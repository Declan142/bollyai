#!/usr/bin/env python3
"""Model bake-off for the rich episode review — SAME prompt, SAME dossier, swap the model.
Reuses build_review.py's exact draft+edit prompts. Compares Azure gpt-5.4 vs deepseek-v4-pro.
gpt-5.5 (pilot) is already in data/series/house-of-the-dragon.json for the 3-way compare.
"""
import sys, os, json, subprocess, urllib.request, time
sys.path.insert(0, os.path.dirname(__file__))
import build_review as br

REPO = br.REPO
ENDPOINT = "https://adity-mnuhhdt9-eastus2.cognitiveservices.azure.com"
API_VER = "2024-12-01-preview"

def az_key():
    return subprocess.run(
        ["az","cognitiveservices","account","keys","list","-g","empire-ai",
         "-n","adity-mnuhhdt9-eastus2","--query","key1","-o","tsv"],
        capture_output=True, text=True).stdout.strip()

KEY = az_key()

def azure_chat(deployment, system, user, openai_style, budget=16000, timeout=600):
    url = f"{ENDPOINT}/openai/deployments/{deployment}/chat/completions?api-version={API_VER}"
    body = {"messages":[{"role":"system","content":system},{"role":"user","content":user}]}
    if openai_style:
        body["max_completion_tokens"] = budget          # OpenAI reasoning models
    else:
        body["max_tokens"] = budget; body["temperature"] = 0.7   # DeepSeek/Mistral type
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","api-key":KEY})
    t0=time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    txt = d["choices"][0]["message"]["content"] or ""
    return txt.strip(), round(time.time()-t0,1)

def run(deployment, openai_style):
    house = open(br.HOUSE_STYLE).read()
    dossier = json.load(open(os.path.join(REPO,'data','subtitles','house-of-the-dragon','_dossiers','S01E01.json')))
    dossier.setdefault('title','The Heirs of the Dragon')
    draft_instr, dossier_text = br.build_draft_prompt(house, dossier, 'house-of-the-dragon')
    print(f"[{deployment}] drafting...", flush=True)
    draft, t1 = azure_chat(deployment, draft_instr, dossier_text, openai_style)
    draft = br.strip_fences(draft)
    print(f"[{deployment}] draft {len(draft.split())}w in {t1}s; edit...", flush=True)
    if len(draft.split()) < 200:
        print(f"[{deployment}] DRAFT EMPTY/SHORT — raw: {draft[:200]!r}", flush=True); return
    edited, t2 = azure_chat(deployment, br.EDIT_INSTR, draft, openai_style)
    edited = br.strip_em_dashes(br.strip_fences(edited)) if len(edited.split())>200 else br.strip_em_dashes(draft)
    verdict = br.parse_verdict_json(edited) or br.parse_verdict_json(draft)
    body = br.strip_verdict_line(edited)
    out = f"/tmp/bakeoff_{deployment}.md"
    open(out,'w').write(body)
    print(f"[{deployment}] FINAL {len(body.split())}w | em-dash={br.em_dash_count(body)} | "
          f"verdict={verdict} | {t1+t2}s total -> {out}", flush=True)

if __name__ == '__main__':
    print(f"key len {len(KEY)}", flush=True)
    run("gpt-5-4", openai_style=True)
    run("deepseek-v4-pro", openai_style=False)
    print("BAKEOFF DONE", flush=True)
