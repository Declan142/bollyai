#!/usr/bin/env python3
"""orfree.py — staggered-hedge caller for the BollyAI subtitle engine.

Free OpenRouter lanes first, DeepSeek-v4-flash PAID as the never-congested
backstop. First G1-valid (parses + required keys) response wins. Quota-guarded:
counts every fired request in the daily log, halts the batch at REQ_BUDGET.

Lanes (per FREE_MODEL_RULES.md "Engine defaults"):
  json:  gpt-oss-120b (t0) -> nemotron-super thinking-low (+75s) -> deepseek paid (+150s)
  mega:  nemotron-super thinking-low (t0, 1M ctx) -> deepseek paid (+240s, 1M ctx)

Nemotron thinking-low is mandatory (default reasoning = 240s+ dead air).
NEVER a `reasoning` param on :free ids (silent paid-routing).
"""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
ENGINE_DIR = Path.home() / "bollyai" / "data" / "subtitles" / "_engine"
ENGINE_DIR.mkdir(parents=True, exist_ok=True)
LOG = ENGINE_DIR / "orfree-log.jsonl"
URL = "https://openrouter.ai/api/v1/chat/completions"
REQ_BUDGET = 900  # of the 1000/day account-wide free quota


class QuotaExhausted(RuntimeError):
    pass


def _key() -> str:
    env = os.environ.get("OPENROUTER_API_KEY")
    if env:
        return env.strip()
    txt = (Path.home() / ".claude" / "vault" / "openrouter.md").read_text()
    m = re.search(r"sk-or-v1-[a-f0-9]+", txt)
    if not m:
        raise RuntimeError("no OpenRouter key in vault")
    return m.group(0)


LANES = {
    "json": [
        # (label, model_id, extra_body, stagger_s, per_call_timeout_s)
        ("gpt_oss", "openai/gpt-oss-120b:free", {}, 0, 180),
        ("nemotron_super", "nvidia/nemotron-3-super-120b-a12b:free",
         {"thinking": {"type": "enabled", "effort": "low"}}, 75, 180),
        ("deepseek_paid", "deepseek/deepseek-v4-flash", {}, 150, 180),
    ],
    "mega": [
        ("nemotron_super", "nvidia/nemotron-3-super-120b-a12b:free",
         {"thinking": {"type": "enabled", "effort": "low"}}, 0, 420),
        ("deepseek_paid", "deepseek/deepseek-v4-flash", {}, 240, 420),
    ],
    # consensus partner for the cross-pass: a DIFFERENT family than nemotron
    "mega_alt": [
        ("deepseek_paid", "deepseek/deepseek-v4-flash", {}, 0, 420),
        ("owl_alpha", "openrouter/owl-alpha", {}, 240, 420),
    ],
}

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _log(rec: dict) -> None:
    rec["ts"] = datetime.now(IST).isoformat()
    with LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def requests_today() -> int:
    if not LOG.exists():
        return 0
    today = datetime.now(IST).strftime("%Y-%m-%d")
    n = 0
    with LOG.open() as f:
        for line in f:
            if f'"ts": "{today}' in line or f'"ts":"{today}' in line:
                n += 1
    return n


def coerce_json(raw: str) -> dict | None:
    txt = (raw or "").strip()
    for cand in (txt, *( [m.group(1)] if (m := _FENCE_RE.search(txt)) else [] )):
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    start = txt.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(txt)):
            if txt[i] == "{":
                depth += 1
            elif txt[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(txt[start:i + 1])
                        return obj if isinstance(obj, dict) else None
                    except Exception:
                        return None
    return None


def _one_call(label, model_id, extra_body, timeout, system, user, max_tokens, temperature, out_q, ctx):
    payload = {
        "model": model_id,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        **extra_body,
    }
    if label != "owl_alpha":  # owl alpha rejects response_format intermittently
        payload["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/Declan142", "X-Title": "bollyai-subtext",
                 "User-Agent": "empire-cron/1.0"},
        method="POST")
    t0 = time.time()
    rec = {"lane_label": label, "model": model_id, "ctx": ctx}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        rec["latency_s"] = round(time.time() - t0, 1)
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
        usage = data.get("usage", {})
        rec["usage"] = {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "cost")}
        if not content or not content.strip():
            rec["ok"] = False
            rec["reason"] = "empty_content"
            _log(rec)
            out_q.put((False, label, None, rec))
            return
        rec["ok"] = True
        _log(rec)
        out_q.put((True, label, content, rec))
    except urllib.error.HTTPError as e:
        rec.update(ok=False, code=e.code, body=e.read().decode("utf-8", "replace")[:200],
                   latency_s=round(time.time() - t0, 1))
        _log(rec)
        out_q.put((False, label, None, rec))
    except Exception as e:
        rec.update(ok=False, reason=f"{type(e).__name__}: {e}"[:150], latency_s=round(time.time() - t0, 1))
        _log(rec)
        out_q.put((False, label, None, rec))


def call(system: str, user: str, *, lane: str = "json", max_tokens: int = 6000,
         temperature: float = 0.2, required_keys: tuple[str, ...] = (),
         total_timeout: int = 600, ctx: str = "") -> tuple[dict, dict]:
    """Staggered hedge. Returns (parsed_json, meta). Raises on total failure."""
    if requests_today() >= REQ_BUDGET:
        raise QuotaExhausted(f"daily request budget {REQ_BUDGET} reached")
    spec = LANES[lane]
    out_q: queue.Queue = queue.Queue()
    threads = []
    fired = []
    t_start = time.time()
    next_i = 0
    failures = []
    winner = None
    while True:
        elapsed = time.time() - t_start
        # fire next lane when its stagger arrives, or early if every fired lane already failed
        while next_i < len(spec) and (elapsed >= spec[next_i][3] or len(failures) == len(fired)):
            label, model_id, extra, _stag, tmo = spec[next_i]
            th = threading.Thread(target=_one_call,
                                  args=(label, model_id, extra, tmo, system, user,
                                        max_tokens, temperature, out_q, ctx), daemon=True)
            th.start()
            threads.append(th)
            fired.append(label)
            next_i += 1
        try:
            ok, label, content, rec = out_q.get(timeout=2.0)
        except queue.Empty:
            if elapsed > total_timeout:
                break
            continue
        if not ok:
            failures.append(rec)
            if next_i >= len(spec) and len(failures) >= len(fired):
                break  # every fired lane has failed and nothing left to fire
            continue
        obj = coerce_json(content)
        if obj is None or any(k not in obj for k in required_keys):
            rec2 = {**rec, "ok": False, "reason": "g1_schema_fail",
                    "missing": [k for k in required_keys if not obj or k not in obj]}
            _log(rec2)
            failures.append(rec2)
            if next_i >= len(spec) and len(failures) >= len(fired):
                break
            continue
        winner = (obj, {**rec, "winner": True, "hedge_fired": len(fired)})
        break
    if winner:
        _log({"event": "winner", "lane_label": winner[1]["lane_label"], "ctx": ctx,
              "hedge_fired": winner[1]["hedge_fired"]})
        return winner
    raise RuntimeError(f"orfree: all lanes failed for ctx={ctx}: {json.dumps(failures)[:500]}")
