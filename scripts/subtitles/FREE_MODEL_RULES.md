# FREE-MODEL QUALITY CONTRACT — BollyAI subtitle intelligence engine
<!-- v1 2026-06-12. Owner: Vyom. Consumers: extract_dossier.py, season_crosspass.py,
     judge prompts, and the (next-stage) review-draft generator.
     Extends DOSSIER_SPEC.md; inherits every honesty fence in ~/bollyai/CLAUDE.md. -->

## Why this exists

Free/cheap models produce review-GRADE material only under a contract that makes
fabrication mechanically impossible and opinion evidence-bound. The contract has two
halves: rules the model must follow IN the prompt, and gates OUTSIDE the prompt that
verify it did. A claim that survives both is publishable fuel. A claim that fails
either is stripped, never argued with.

## The four gates (every artifact passes ALL, in order)

| # | Gate | Tool | Fail action |
|---|------|------|-------------|
| G1 | Schema | strict JSON, required keys, enums | re-ask same model once with parse error |
| G2 | Grounding | verify_grounding.py — every timestamp exists in the SRT, every quote is verbatim | 1 repair round with error list, then mechanical strip |
| G3 | Judge | different model FAMILY scores vs rubric (below), >= 7/10 to pass | regenerate once on the next lane model, else flag for Fable |
| G4 | Adjudication | Fable/Opus spot-audit (>= 2 dossiers per series) + full pass on anything G3-flagged | human-grade fix or discard |

## PART 1 — Dossier extraction rules (per episode)

The model receives: episode dialogue doc (`MM:SS|speaker-or-blank|line`), stats hints
(top silences, recurring phrases, name mentions), and the DOSSIER_SPEC.md JSON shape.

Hard rules (in-prompt, all G2-verifiable):
1. **Anchor or omit.** Every `t`, `evidence_t`, `line_t` is COPIED from the dialogue
   doc. If you cannot point at a timestamp, the claim does not exist.
2. **Verbatim means verbatim.** `key_lines.line` is a character-exact substring of the
   line at that timestamp (max 15 words, max 6 lines, max 80 quoted words total).
   Trimming is allowed; paraphrase is not.
3. **Null beats guess.** Unknown speaker = null. Unknown title = null. No episode-title,
   actor, air-date, or production fact from training memory — the dialogue doc is the
   ONLY source. (Reviews add real-world context LATER from cited sources, not here.)
4. **Contradiction spine is mandatory**: the character whose want-vs-do gap drives the
   hour, with `line_t` evidence. No contradiction found = pick the closest tension and
   say why in `tone_notes`; never leave it null.
5. **Specificity bar**: a beat that could describe any episode of any show is banned.
   "Tension rises between the leads" = FAIL. "Meera exposes the court order as forged
   because the judge retired two days before its date (19:08)" = PASS.
6. **Open loops are questions, not summaries** — phrased as the question the viewer is
   left holding.
7. **Translated-subtitle discipline**: for non-English originals the quotes are the
   English subtitle rendering. Set `"quote_lang": "en-sub"` so the review stage cites
   them as "as the English subtitles render it" — never as the actor's spoken line.
8. **Self-check block is part of the output** (G1-required):
   `"self_check": {"every_t_exists": true, "quotes_verbatim": true, "quote_words_total": <n>, "no_training_facts": true}`
   — emit only after actually re-checking. A false self-check found by G2 marks the
   model lane as dishonest for the run (lane demoted for the rest of the series).

## PART 2 — Season/series cross-pass rules (the easter-egg stage)

The model receives ALL episodes' dialogue in one context (1M lane) + the recurring-
phrase index from Stage B.

1. **A callback needs BOTH ends**: `setup` (ep + t) and `payoff` (ep + t), each
   independently G2-verified. One-ended "this feels related" = banned.
2. **Phrase-anchored first**: start from Stage-B `recurring_phrases` (deterministic),
   then add what statistics can't see (visual-cue dialogue references, prophecy→
   fulfillment, object handoffs, planted lies).
3. **Confidence is consensus**: the pass runs on two model families. A callback both
   find (same eps, t within 20s) = `"confidence": "high"`. Single-family finds =
   `"candidate"` — publishable only after G4 (Fable) confirms against the dialogue.
4. **Motifs need 3+ occurrences** with timestamps, else they're listed as `weak_motifs`.
5. **Arcs are dialogue-derivable only** — describe what characters SAY and DO in text,
   never staging/cinematography (we have no video).
6. **No mythology imports**: cultural/mythological references may be NOTED as
   `external_ref_candidates` (for the review stage to verify via real sources) but
   never asserted as fact from training memory.

## PART 3 — Review-draft rules (free models drafting publishable reviews)

A free model may draft `EpisodeReview` / season-body prose ONLY from a G2-verified
dossier + crosspass. The draft inherits every BollyAI CLAUDE.md fence. Non-negotiables:

1. **Third person, disclosed-AI**: BollyAI reads, BollyAI weighs; it never watches.
   Zero first-person viewing claims in any language (gate test exists, 0 tolerance).
2. **Evidence chain**: every factual sentence traces to a dossier field. A sentence
   with no dossier anchor is opinion — opinion is allowed only as a VERDICT on cited
   evidence, never as new information. Fact not in dossier = page capped at 2.0
   (WRITER-GENOME Dimension-0).
3. **Quote budget**: max 40 quoted words per review, each quote <= 25 words, cited
   ("as the English subtitles render it" for en-sub). Subtitle text is fuel, NEVER
   cargo.
4. **bollymeter**: `{"score": x.x, "basis": "<grounded 1-2 sentences>"}` or null.
   Basis must cite the dossier evidence (the 116s silence, the density spike, the
   contradiction) — "great episode" is not a basis.
5. **spoiler_free field is actually spoiler-free**: tease the question, never the
   answer. `the_moment` names the beat people remember WITHOUT resolving it.
6. **Structure** (mirror squid-game.json gold): hook (<= 25 words, concrete, no
   clickbait-question openers) → what the hour does → what elevates it (evidence) →
   what drags (evidence; mandatory — a review with zero negatives FAILS) → verdict.
7. **Banned register** (G3 auto-fail): "delve", "tapestry", "rollercoaster", "must-
   watch", "edge of your seat", "masterclass", "elevates the narrative", "a testament
   to", "binge-worthy", rhetorical-question openers, em-dash (auto-stripped anyway),
   emoji, any sentence over 35 words.
8. **Hinglish flavor allowed, English spine** (BollyAI voice): Devanagari only as
   accent words, never full sentences.
9. **Length bands**: episode review 110-160 words; season body 220-320; ending-
   explained 350-500. Over/under = G3 fail.
10. **Self-check block** mirrors Part 1 (`viewing_claims: 0, quoted_words: <n>,
    every_fact_dossier_anchored: true`).

## PART 4 — Judge rubric (G3, run on a different family than the writer)

Score 0-10, average of five 0-2 dimensions; pass >= 7 (i.e. 1.4 avg):
- **Grounding**: spot-check 3 random claims against the dossier/dialogue provided.
- **Specificity**: would this text be false for a different episode? (generic = 0)
- **Honesty fences**: viewing claims / invented numbers / uncited quotes = instant 0
  overall, not just this dimension.
- **Register**: banned-phrase scan + sentence-length + hook quality.
- **Verdict courage**: does it actually SAY something falsifiable about quality, with
  the evidence to back it (2), hedge-everything mush (0)?

Judge returns `{"scores": {...}, "overall": x.x, "verdict": "pass|revise|fail",
"worst_sentence": "...", "fix": "one line"}`.

## Engine defaults

- temperature 0.2 extraction / 0.55 review drafts / 0.1 judge
- Nemotron-3 family: `"thinking": {"type":"enabled","effort":"low"}` ALWAYS
  (default reasoning = 240s+ timeouts). Nex: thinking disabled. NEVER a `reasoning`
  param on `:free` ids (silently routes to paid).
- Staggered hedge: fire lane-1; +75s fire lane-2; +150s fire DeepSeek-paid backstop.
  First G1-valid response wins. ~1.15 requests/episode average, 1000 req/day quota.
- Every call logged to `data/subtitles/_engine/orfree-log.jsonl`; batch halts at 900
  requests/day (QUOTA_HALT marker) and resumes next day.
- Subtitle corpus is PRIVATE (gitignored). Dossiers/crosspass are internal fuel —
  only review-stage output ever ships, and only through G1-G4.
