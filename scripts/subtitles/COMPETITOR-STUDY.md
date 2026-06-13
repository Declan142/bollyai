# WHAT THE BEST REVIEW SHOPS DO - distilled for BollyAI
Vyom, 2026-06-13. Source study for the REVIEW-HOUSE-STYLE upgrade.
Read this to understand WHY the house style says what it says. The contract is in
`REVIEW-HOUSE-STYLE.md`; this is the reasoning behind it.

> We are not copying anyone. We are stealing the *moves* that make a review land and
> leaving behind everything that would break a BollyAI honesty fence (no first-person
> viewing, no invented numbers, no em-dash). The goal: competitor-grade voice on a
> disclosed-AI critic that has read everyone and watched no one.

---

## The eleven shops, one line each

| Shop | The signature move worth stealing |
|---|---|
| **Vulture** | Recap-with-a-spine: never neutral, always has a take on the week's hour. Letter grade + "the week's best/worst" callouts. Gossipy intelligence. |
| **The Ringer** | Thesis-driven. Starts from a cultural question, the episode is the evidence. "Specificity to universality." |
| **The A.V. Club** | Letter grade up top + sharp, specific headline + "Stray Observations" bullet coda. Judgement is concrete, never vague. |
| **Decider** | "Stream It or Skip It." A scannable verdict box and a single decisive call. Built for the reader-deciding-right-now. |
| **IGN** | Numeric score with a one-line "verdict" summary. Genre-fluent, fan-forward, structured. |
| **Rolling Stone** | Swagger and authority. A strong first sentence that plants a flag. Cultural weight. |
| **Polygon** | Fandom-native. Assumes love for the thing, talks craft and lore without condescension. Warm, propulsive. |
| **Film Companion** | Comparative pop-cultural framing ("DDLJ, but make it gory") + grounded lyricism. Indian cinema literacy as default. |
| **Film Companion South** | Treats Telugu/Tamil/Malayalam/Kannada as a primary canon, not a footnote. Star-text and regional craft fluency. |
| **FirstPost** | Brisk, opinionated, culture-plugged. Lands the take fast. |
| **The Hindu** | Measured authority, context-rich, respects the reader's intelligence. The grown-up in the room. |

---

## The moves we are stealing (and how they map to our fences)

### 1. A THESIS, not a recap (The Ringer)
The best reviews *argue something*. The Ringer opens "'The Pitt' Is a Warning About
Optimization Culture" and the whole piece is evidence for that claim. The episode is the
case study, not the subject.
**Our version:** every review states what this hour is *about* under the plot, early, and
spends its body proving it. We already have dossier beats and a central contradiction. Use
them as evidence for a claim, not as a list to summarize.

### 2. Specificity to universality (The Ringer, again)
Move from one concrete detail to a larger point, then back. "A single character arc becomes
a lens." Concrete beats abstract, always, but the concrete is in *service* of an idea.
**Our version:** anchor every abstract claim to a named character and a physical beat from
the dossier. Never float.

### 3. The verdict box (Decider, IGN, A.V. Club)
A scannable, decisive payoff. Decider's "Stream It or Skip It," A.V. Club's letter grade,
IGN's score-plus-one-liner. The reader who scrolls to the bottom still gets the call.
**Our version:** the `bollymeter` score + the `one_liner` verdict already do this. Sharpen
the one_liner into a genuine flag-plant, not a summary. The Verdict section earns the score.

### 4. The headline that promises a specific take (A.V. Club)
"A sublime Nicola Walker elevates Hulu's so-so 'Alice And Steve'." The headline already has
a POV and a specific reason. Not "Episode 4 Review."
**Our version:** the cold-open does this job. Lead with the specific charged thing, not a
neutral frame.

### 5. Comparative pop-cultural framing (Film Companion)
"DDLJ, But Make it Gory, Gruesome and Awesome." A familiar reference instantly locates the
reader and shows wit. Film Companion does this with Indian touchstones the audience lives in.
**Our version:** use sparingly and ONLY when the comparison is factually true (shared genre
lineage, an actual influence, a verifiable echo). One earned comparison can do the work of a
paragraph. A fabricated one breaks the grounding fence. Indian touchstones welcome and
preferred for an Indian readership.

### 6. The "Stray Observations" energy (A.V. Club)
The main review carries the argument; a coda catches the small sharp things that did not fit.
It is where the wit breathes.
**Our version:** we do NOT add a bullet coda (keeps the prose clean and the schema stable),
but we carry that energy *into* the act-blocks: the precise, slightly wicked, specific
observation is the wit. Earn it through accuracy, not adjectives.

### 7. Season-arc awareness (Vulture recaps, all the prestige-TV shops)
A great recap knows where the hour sits in the season. It calls back three episodes and sets
up the finale. It treats the season as one organism.
**Our version:** THIS is the "whole series taken into effect" directive. Every episode review
must place the hour in the season's arc: what it pays off, what it plants, whether it earns
its slot. This is safe linking (internal, factual) and it is the single biggest upgrade.

### 8. Linking that recommends without lying
Polygon and The Ringer constantly connect a show to its neighbors, its lineage, its
creator's other work. It makes the reader feel held inside a map.
**Our version, fenced:** prose linking is allowed ONLY when factual:
  - intra-series: callbacks across episodes/seasons of the SAME show (always safe).
  - cross-series: shared creator / shared cast / same universe / genuine genre lineage,
    framed as craft comparison, never as an invented "if you liked X watch Y" claim.
The structural watch-next mesh (the chips/rails) is computed centrally in
`series-links.json` and wired at render. The prose gestures; the render layer recommends.
Do not hardcode cross-series recommendations the mesh has not verified.

### 9. Voice with a spine (Vulture, Rolling Stone, FirstPost)
None of these are neutral. They have opinions and a personality. The entertainment IS the
point of view. A flat, balanced, both-sides recap is the failure mode.
**Our version:** BollyAI has strong opinions about craft. It is a front-row fan with taste
and swagger. "Entertaining" means propulsive and opinionated, NOT slop. See the restraint
rule in the house style: restraint kills *fake* profundity, it does not mean flat.

### 10. Authority and context (The Hindu, Film Companion South)
The grown-up shops earn trust by knowing the canon: the director's prior films, the genre's
history, the star's text. Context is a flex.
**Our version:** lean on grounded context when the dossier or well-established fact supports
it (a creator's known preoccupations, a genre's conventions). Never invent a "fact" to sound
smart. Unsure equals omit.

---

## The anti-patterns we are NOT stealing (the slop tells)

- The neutral both-sides recap with no take (the death of every bad recap).
- The "in this episode, we see..." throat-clear.
- The aphoristic fortune-cookie paragraph-closer (AI's favourite tic).
- The "not just X, but Y" / "X is both A and B" profundity couplet.
- Manufactured stakes ("everything changes in this game-changing hour").
- The five-paragraph plot retell with a one-line opinion stapled on.
- Star-rating inflation. We score craft honestly; a 6 is a real 6.

---

## The synthesis (what the house style now demands)

A BollyAI episode review is **a Ringer thesis** delivered in **a Vulture recap's
season-aware, opinionated voice**, with **Film Companion's Indian-cinema literacy and
comparative wit**, paying off in **a Decider/IGN-grade scannable verdict**, and connected to
its neighbors with **Polygon's map-sense** - all of it grounded to the dossier and clean of
every honesty fence. Entertaining through precision and point of view, never through reach.

The contract that operationalizes this is `REVIEW-HOUSE-STYLE.md`.
