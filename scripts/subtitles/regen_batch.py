#!/usr/bin/env python3
"""regen_batch — mass-regenerate rich episode reviews via build_review (gpt-5.4-Azure).

Parallel ACROSS series (each series owns its JSON file, processed serially within)
so there is never a same-file write race. Per-episode robustness: a failure is
logged and the batch continues. Re-runnable: skips episodes that already have review_body.

Usage:
  python3 scripts/subtitles/regen_batch.py farzi scam-1992 crash-landing-on-you ...
  python3 scripts/subtitles/regen_batch.py --force <slugs>   # redo even if review_body exists
"""
import sys, os, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LEDGER = os.path.join(REPO, 'data', 'subtitles', '_engine', 'regen-batch.jsonl')
BUILD = os.path.join(os.path.dirname(__file__), 'build_review.py')


def log(rec):
    rec['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    with open(LEDGER, 'a') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f"  [{rec.get('event')}] {rec.get('slug','')} {rec.get('ep','')} {rec.get('detail','')}", flush=True)


def episodes_for(slug, force):
    d = json.load(open(os.path.join(REPO, 'data', 'series', f'{slug}.json')))
    dossdir = os.path.join(REPO, 'data', 'subtitles', slug, '_dossiers')
    doss = set(os.listdir(dossdir)) if os.path.isdir(dossdir) else set()
    out = []
    for s in d.get('seasons', []):
        for r in s.get('episode_reviews', []):
            tag = f"S{s['number']:02d}E{r['number']:02d}.json"
            if tag in doss and (force or not r.get('review_body')):
                out.append((s['number'], r['number']))
    return out


def do_series(slug, force):
    eps = episodes_for(slug, force)
    log({'event': 'series_start', 'slug': slug, 'detail': f'{len(eps)} episodes'})
    ok = fail = 0
    for (sn, en) in eps:
        for attempt in (1, 2):  # one retry on transient failure
            p = subprocess.run(['python3', BUILD, slug, str(sn), str(en)],
                               capture_output=True, text=True, timeout=900)
            if p.returncode == 0 and 'DONE:' in p.stdout:
                ok += 1
                wc = next((l for l in p.stdout.splitlines() if 'DONE:' in l), '')
                log({'event': 'ep_ok', 'slug': slug, 'ep': f'S{sn}E{en}', 'detail': wc.split('|',1)[-1].strip()})
                break
            elif attempt == 2:
                fail += 1
                log({'event': 'ep_FAIL', 'slug': slug, 'ep': f'S{sn}E{en}',
                     'detail': (p.stderr or p.stdout)[-160:]})
            else:
                time.sleep(5)
    # validate the series after its episodes are done
    v = subprocess.run(['python3', os.path.join(REPO, 'scripts', 'batch', 'validate_series.py'), slug],
                       capture_output=True, text=True)
    log({'event': 'series_done', 'slug': slug,
         'detail': f'ok={ok} fail={fail} validate={"PASS" if "PASS" in v.stdout else "FAIL"}'})
    return slug, ok, fail


def main():
    args = sys.argv[1:]
    force = '--force' in args
    slugs = [a for a in args if not a.startswith('--')]
    if not slugs:
        print("usage: regen_batch.py [--force] <slug> [<slug>...]", file=sys.stderr); sys.exit(1)
    log({'event': 'batch_start', 'detail': f'{len(slugs)} series, force={force}'})
    results = []
    with ThreadPoolExecutor(max_workers=1) as ex:  # serial: gpt-5-4 deployment is capacity-3 (429s above this)
        futs = {ex.submit(do_series, s, force): s for s in slugs}
        for fu in as_completed(futs):
            results.append(fu.result())
    tot_ok = sum(r[1] for r in results); tot_fail = sum(r[2] for r in results)
    log({'event': 'batch_end', 'detail': f'ok={tot_ok} fail={tot_fail}'})
    print(f"\nBATCH DONE: ok={tot_ok} fail={tot_fail}", flush=True)
    for s, ok, fail in sorted(results):
        print(f"  {s}: ok={ok} fail={fail}", flush=True)


if __name__ == '__main__':
    main()
