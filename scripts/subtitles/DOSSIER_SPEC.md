# BollyAI Episode Evidence Dossier — spec (Stage C)

Input:  `data/subtitles/<slug>/_stats/SxxExx.json` — full dialogue doc + stats from Stage B.
Output: `data/subtitles/<slug>/_dossiers/SxxExx.json`

The dossier is the ONLY thing the review writer may rely on for in-episode facts
(WRITER-GENOME Dimension-0: any fact not in the dossier caps the page at 2.0).
The dialogue corpus itself is PRIVATE — never published, never quoted beyond caps below.

## Output JSON shape

```json
{
  "episode": "S01E03",
  "title": "<from episode list>",
  "beats": [
    {"t": "14:32", "what": "one-line event, grounded in the dialogue at that timestamp"}
  ],
  "character_beats": [
    {"who": "Boyd", "beat": "what he wants vs what he does in this hour", "evidence_t": "21:04"}
  ],
  "key_lines": [
    {"t": "14:32", "speaker": "Sara", "line": "verbatim line, <= 15 words", "why": "why this line is load-bearing"}
  ],
  "open_loops": ["question this episode plants and does NOT answer"],
  "payoffs": [
    {"plants_from": "S01E01 04:10", "pays_here": "32:55", "what": "the callback"}
  ],
  "contradiction": {"who": "<character>", "wants": "...", "does": "...", "line_t": "..."},
  "tone_notes": "pacing observations grounded in the stats (silences, density spikes)",
  "speaker_attribution_confidence": "high|medium|low"
}
```

## Hard rules
1. Every `t` timestamp must exist in the dialogue doc (copy it, don't invent).
2. `key_lines` max 6 per episode; each verbatim line <= 15 words. TOTAL quoted words
   across the dossier <= 80 (downstream review quotes <= 40 of those).
3. Subtitles here are non-SDH: speakers are INFERRED from context. Mark inference
   quality in `speaker_attribution_confidence`. If unsure of a speaker, use null —
   never guess a name for a quoted line.
4. No facts from memory/training about the show: ONLY what's in this dialogue doc.
   (Episode title + season context comes from the brief, not from you.)
5. `contradiction` is mandatory — it's the spine of the review. Pick the character
   whose want-vs-do gap drives the hour.
6. No em-dashes anywhere.
