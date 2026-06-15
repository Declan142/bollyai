# BollyAI — Pre-Existing Attribution Fabrication Audit
**Run:** 2026-06-14 (post-blitz, pre-cleanup)
**Scope:** All committed series in `data/series/*.json` as of HEAD (22a46b9)
**Gate:** `engine/gates/attribution_regex.py` via `validate_series.py` — builds on the honesty
fence from `6c3c63d`. SEASON-level prose licensed only if that specific season carries a
`critic.pull_quotes[].url`; EPISODE-level prose licensed only if that specific episode carries
a `critic_note` or `pull_quote` with a URL.

---

## Summary

| Metric | Count |
|---|---|
| Total series in catalogue | 559 |
| **Passing attribution gate** | **291** (52%) |
| **Failing attribution gate** | **268** (48%) |
| Total attribution flag instances | 518 |

**Critically: every one of the 268 failures is attribution-only.** No other fence (em-dash,
viewing-claim, missing-field, SourceValue envelope) is co-failing. The rest of the content
is clean on all other gates.

---

## Breakdown by field

| Field | Flag count | Notes |
|---|---|---|
| `season.review_body` | 340 | Season-level prose attributing reception without a backed pull_quote on that specific season |
| `episode.spoiler_free` | 130 | Per-episode reviews with unlicensed "Critics noted / Audiences remember" phrasing |
| `season.season_over_season` | 29 | Season-comparison prose with unbacked attribution |
| `episode.the_moment` | 19 | The-moment field with attribution phrasing |
| **Total** | **518** | |

---

## Breakdown by scope

| Scope | Series count |
|---|---|
| Season-level fields only (review_body / season_over_season) | 141 |
| Episode-level fields only (spoiler_free / the_moment) | 78 |
| Both season + episode fields | 49 |
| **Total failing** | **268** |

---

## Severity (flags per file)

| Flags | Series count |
|---|---|
| 1 flag | 138 |
| 2–5 flags | 123 |
| 6–10 flags | 7 |
| >10 flags | 0 |

Max severity: 8 flags (`orange-is-the-new-black`), all in season review_bodies.

---

## Fixability / grounding

The 268 failures split into two cleanup tracks:

### Track A — Sub-grounded (195 series): phrase-rewrite or add season pull_quote
These series have at least one season with a real `critic.pull_quotes[].url`. The fabrication
is in phrases like "Critics noted that..." where BollyAI's editorial voice ("The writing
here...") would be correct and no backing exists at that specific season/episode scope.
- **Fix:** either (a) rewrite the attributed phrase to BollyAI editorial voice (no
  "Critics/Audiences" subject), OR (b) add a real pull_quote with URL to the specific
  season/episode that licenses the claim.
- **Effort:** High but scriptable — a targeted find-replace of the attribution phrase with
  BollyAI voice passes the gate. P2 polish pass with FULL/KIMI can rewrite.

### Track B — Naked (73 series): needs real quotes or full prose rewrite
These series have zero pull_quotes with URLs anywhere. Every attribution claim is purely
fabricated — the phrasing asserts real-world consensus that no source backs.
- **Fix:** either (a) supply real critic pull_quotes with URLs (requires sourcing), OR
  (b) complete rewrite of all attribution phrases to BollyAI's own editorial voice.
- **Effort:** Higher — can't just add a missing URL; the grounding work is real.

---

## Top 20 heaviest failures

| Slug | Total flags | Season flags | Episode flags | Track |
|---|---|---|---|---|
| orange-is-the-new-black | 8 | 8 | 0 | A |
| this-is-us | 7 | 4 | 3 | A |
| billions | 6 | 6 | 0 | A |
| friday-night-lights | 6 | 5 | 1 | A |
| mad-men | 6 | 6 | 0 | A |
| the-office-us | 6 | 6 | 0 | A |
| the-shield | 6 | 5 | 1 | A |
| brooklyn-nine-nine | 5 | 5 | 0 | A |
| gilmore-girls | 5 | 5 | 0 | A |
| hacks | 5 | 4 | 1 | A |
| luther | 5 | 4 | 1 | A |
| my-hero-academia | 5 | 4 | 1 | A |
| six-feet-under | 5 | 5 | 0 | A |
| skins | 5 | 5 | 0 | B |
| stranger-things | 5 | 5 | 0 | A |
| the-marvelous-mrs-maisel | 5 | 5 | 0 | A |
| what-we-do-in-the-shadows | 5 | 5 | 0 | B |
| abbott-elementary | 4 | 4 | 0 | A |
| beef | 4 | 1 | 3 | A |
| boardwalk-empire | 4 | 4 | 0 | A |

---

## All 268 failing slugs

Format: `slug: Nf (S:season_flags, E:episode_flags) [track]`

```
1899: 2f (S:1, E:1) [B]
1923: 1f (S:1) [B]
aarya: 1f (S:1) [A]
abbott-elementary: 4f (S:4) [A]
american-horror-story: 1f (S:1) [A]
anohana: 2f (S:1, E:1) [B]
aranyak: 1f (E:1) [A]
aspirants: 1f (S:1) [A]
atlanta: 3f (S:2, E:1) [A]
babylon-berlin: 1f (S:1) [A]
bad-and-crazy: 1f (E:1) [A]
band-of-brothers: 1f (E:1) [A]
bard-of-blood: 1f (S:1) [B]
barry: 1f (E:1) [A]
be-melodramatic: 3f (S:1, E:2) [B]
beastars: 1f (S:1) [B]
beef: 4f (S:1, E:3) [A]
berlin: 1f (S:1) [A]
berserk-1997: 1f (E:1) [A]
beyond-evil: 1f (E:1) [A]
big-little-lies: 1f (E:1) [A]
billions: 6f (S:6) [A]
bleach-thousand-year-blood-war: 1f (S:1) [B]
blood-and-water: 1f (S:1) [A]
blue-period: 2f (S:1, E:1) [B]
boardwalk-empire: 4f (S:4) [A]
bocchi-the-rock: 1f (E:1) [A]
borgen: 2f (S:2) [A]
breathe-into-the-shadows: 1f (S:1) [B]
broadchurch: 1f (S:1) [A]
brooklyn-nine-nine: 5f (S:5) [A]
brown: 1f (E:1) [A]
call-my-agent: 1f (S:1) [A]
catastrophe: 1f (S:1) [A]
clannad: 2f (S:1, E:1) [A]
class: 1f (S:1) [B]
cobra-kai: 3f (S:3) [A]
college-romance: 1f (S:1) [A]
community: 2f (S:2) [A]
crash-course-in-romance: 1f (E:1) [A]
criminal-justice: 1f (S:1) [A]
daredevil: 2f (S:2) [A]
dark-desire: 1f (S:1) [A]
deaths-game: 1f (E:1) [A]
demon-slayer-kimetsu-no-yaiba: 2f (S:2) [A]
derry-girls: 1f (S:1) [A]
dexter: 2f (S:2) [A]
doom-at-your-service: 1f (E:1) [B]
dopesick: 1f (E:1) [A]
downton-abbey: 1f (S:1) [A]
dr-stone: 2f (S:2) [A]
elite: 2f (S:2) [A]
emily-in-paris: 2f (S:2) [A]
erased: 2f (S:1, E:1) [B]
every-year-after: 1f (S:1) [B]
fauda: 1f (S:1) [A]
fight-my-way: 2f (E:2) [A]
for-all-mankind: 1f (E:1) [A]
forecasting-love-and-weather: 2f (S:1, E:1) [B]
four-more-shots-please: 3f (S:3) [A]
friday-night-lights: 6f (S:5, E:1) [A]
gen-v: 1f (S:1) [A]
gilmore-girls: 5f (S:5) [A]
gintama: 1f (S:1) [A]
gomorrah: 2f (S:2) [A]
great-pretender: 1f (E:1) [A]
greys-anatomy: 3f (S:2, E:1) [A]
grid: 1f (E:1) [A]
gurren-lagann: 1f (E:1) [A]
gyeongseong-creature: 2f (S:1, E:1) [A]
hacks: 5f (S:4, E:1) [A]
haikyu: 2f (S:1, E:1) [A]
halt-and-catch-fire: 4f (S:3, E:1) [A]
happy-valley: 1f (S:1) [A]
heeramandi: 1f (E:1) [A]
homeland: 4f (S:4) [A]
hometown-cha-cha-cha: 1f (E:1) [A]
hostel-daze: 3f (S:3) [A]
hotel-del-luna: 2f (S:1, E:1) [B]
house-md: 4f (S:4) [A]
humans: 3f (S:3) [A]
i-may-destroy-you: 1f (E:1) [A]
inside-edge: 1f (S:1) [A]
inspector-koo: 1f (S:1) [B]
interview-with-the-vampire: 2f (S:2) [B]
itaewon-class: 1f (S:1) [B]
its-a-sin: 1f (E:1) [A]
jack-ryan: 3f (S:3) [B]
justified: 4f (S:4) [A]
kill-me-heal-me: 3f (S:1, E:2) [B]
killing-eve: 1f (E:1) [A]
kingdom: 1f (E:1) [A]
land-of-the-lustrous: 1f (E:1) [B]
landman: 1f (S:1) [B]
line-of-duty: 4f (S:4) [A]
little-things: 1f (S:1) [A]
little-women-2022: 3f (S:1, E:2) [B]
lost: 3f (S:3) [A]
love-alarm: 2f (S:2) [B]
lovely-runner: 2f (S:1, E:1) [B]
luther: 5f (S:4, E:1) [A]
mad-men: 6f (S:6) [A]
made-in-abyss: 1f (S:1) [A]
madoka-magica: 1f (E:1) [A]
marry-my-husband: 1f (E:1) [A]
mask-girl: 2f (S:1, E:1) [B]
maxton-hall: 1f (S:1) [B]
mayor-of-kingstown: 2f (S:2) [B]
mismatched: 1f (S:1) [A]
mob-psycho-100: 2f (S:2) [B]
money-heist: 1f (S:1) [A]
monster-2004: 1f (S:1) [B]
moon-lovers-scarlet-heart-ryeo: 1f (S:1) [B]
mouse: 1f (E:1) [A]
moving: 2f (E:2) [A]
mumbai-diaries: 1f (E:1) [A]
mushishi: 3f (S:2, E:1) [B]
my-brilliant-friend: 2f (S:2) [A]
my-demon: 1f (E:1) [A]
my-hero-academia: 5f (S:4, E:1) [A]
my-liberation-notes: 1f (E:1) [A]
my-name: 1f (E:1) [A]
nana: 1f (E:1) [A]
natsumes-book-of-friends: 3f (S:3) [A]
never-have-i-ever: 3f (S:3) [A]
no-game-no-life: 1f (E:1) [A]
noragami: 1f (S:1) [A]
normal-people: 2f (E:2) [A]
november-story: 1f (S:1) [B]
odd-taxi: 1f (E:1) [B]
one-punch-man: 1f (S:1) [A]
only-murders-in-the-building: 4f (S:4) [A]
orange-is-the-new-black: 8f (S:8) [A]
our-beloved-summer: 3f (S:1, E:2) [B]
our-blues: 2f (S:1, E:1) [B]
outer-banks: 2f (S:2) [A]
outlander: 3f (S:3) [A]
overlord: 2f (S:2) [A]
panchayat: 2f (S:2) [A]
parasyte-the-maxim: 1f (S:1) [B]
parks-and-recreation: 3f (S:1, E:2) [A]
peep-show: 4f (S:4) [B]
permanent-roommates: 1f (S:1) [B]
physical-100: 1f (S:1) [B]
pluto-2023: 1f (E:1) [A]
poldark: 1f (S:1) [A]
pose: 3f (S:2, E:1) [A]
prison-break: 2f (S:2) [A]
psycho-pass: 1f (S:1) [A]
ragnarok-2020: 1f (S:1) [A]
ranking-of-kings: 1f (E:1) [A]
re-zero: 2f (S:1, E:1) [A]
reacher: 2f (S:2) [A]
reborn-rich: 2f (E:2) [A]
rectify: 2f (S:1, E:1) [A]
rings-of-power: 3f (S:3) [B]
rome: 1f (S:1) [A]
samurai-champloo: 1f (E:1) [A]
save-the-tigers: 1f (S:1) [B]
secret-garden: 1f (E:1) [A]
sex-education: 2f (S:2) [A]
sherlock: 1f (S:1) [A]
shogun: 1f (E:1) [A]
shrinking: 1f (S:1) [A]
six-feet-under: 5f (S:5) [A]
skam: 1f (E:1) [A]
skins: 5f (S:5) [B]
slow-horses: 1f (S:1) [A]
solo-leveling: 1f (S:1) [A]
sons-of-anarchy: 4f (S:4) [A]
special-ops: 1f (S:1) [A]
spiral: 3f (S:3) [B]
spy-x-family: 1f (S:1) [A]
station-eleven: 2f (E:2) [A]
stranger-things: 5f (S:5) [A]
strangers-from-hell: 1f (E:1) [B]
strong-girl-nam-soon: 2f (S:1, E:1) [B]
suburra: 1f (S:1) [A]
suits: 2f (S:2) [B]
sweet-home: 2f (S:1, E:1) [A]
sword-art-online: 2f (S:2) [A]
tanaav: 1f (E:1) [A]
tehran: 2f (S:2) [A]
that-time-i-got-reincarnated-as-a-slime: 2f (S:1, E:1) [A]
the-americans: 2f (S:1, E:1) [A]
the-art-of-sarah: 1f (E:1) [A]
the-atypical-family: 2f (S:1, E:1) [B]
the-boys: 2f (S:2) [A]
the-bridge: 1f (S:1) [B]
the-bureau: 4f (S:4) [A]
the-crown: 3f (S:3) [A]
the-devil-judge: 2f (E:2) [A]
the-diplomat: 1f (E:1) [A]
the-empress: 2f (S:2) [A]
the-end-of-the-f-ing-world: 2f (S:1, E:1) [B]
the-fall: 1f (S:1) [A]
the-frog: 2f (S:1, E:1) [B]
the-good-place: 2f (S:1, E:1) [A]
the-great: 3f (S:3) [B]
the-handmaids-tale: 2f (S:2) [A]
the-haunting-of-hill-house: 1f (E:1) [A]
the-it-crowd: 3f (S:2, E:1) [B]
the-killing: 1f (S:1) [A]
the-knick: 1f (E:1) [A]
the-last-kingdom: 3f (S:3) [B]
the-last-of-us: 1f (E:1) [A]
the-leftovers: 1f (E:1) [A]
the-marvelous-mrs-maisel: 5f (S:5) [A]
the-missing: 1f (S:1) [A]
the-night-of: 1f (E:1) [A]
the-office-uk: 1f (S:1) [A]
the-office-us: 6f (S:6) [A]
the-pacific: 1f (E:1) [A]
the-penthouse-war-in-life: 2f (S:2) [B]
the-perfect-couple: 2f (S:1, E:1) [B]
the-protector: 2f (S:2) [B]
the-queens-gambit: 1f (E:1) [A]
the-red-sleeve: 3f (S:1, E:2) [B]
the-sandman: 1f (E:1) [A]
the-shield: 6f (S:5, E:1) [A]
the-sopranos: 3f (S:3) [A]
the-terror: 2f (S:1, E:1) [A]
the-thick-of-it: 1f (S:1) [A]
the-trauma-code: 2f (E:2) [A]
the-uncanny-counter: 1f (E:1) [A]
the-young-pope: 1f (E:1) [A]
thirty-nine: 1f (E:1) [A]
this-is-us: 7f (S:4, E:3) [A]
thukra-ke-mera-pyaar: 1f (E:1) [A]
to-your-eternity: 3f (S:2, E:1) [B]
tokyo-ghoul: 3f (S:1, E:2) [A]
tokyo-revengers: 2f (S:2) [A]
top-boy: 1f (S:1) [A]
top-of-the-lake: 1f (S:1) [A]
toradora: 1f (E:1) [A]
trigun-stampede: 1f (S:1) [A]
tripling: 3f (S:3) [B]
tvf-cubicles: 3f (S:3) [B]
tvf-pitchers: 1f (S:1) [B]
twenty-five-twenty-one: 1f (E:1) [A]
twin-peaks: 1f (S:1) [A]
undekhi: 1f (S:1) [B]
vadhandhi-the-fable-of-velonie: 1f (E:1) [A]
vigilante: 2f (S:1, E:1) [B]
vikings: 2f (S:2) [A]
vincenzo: 1f (E:1) [A]
violet-evergarden: 1f (E:1) [A]
vis-a-vis: 3f (S:3) [B]
voice-kdrama: 2f (S:2) [B]
w-two-worlds: 1f (E:1) [A]
watchmen: 1f (E:1) [A]
weak-hero-class-1: 2f (E:2) [A]
weightlifting-fairy-kim-bok-joo: 1f (E:1) [A]
welcome-to-samdal-ri: 1f (S:1) [B]
wentworth: 3f (S:3) [B]
what-we-do-in-the-shadows: 5f (S:5) [B]
when-life-gives-you-tangerines: 3f (E:3) [A]
when-the-phone-rings: 3f (S:1, E:2) [B]
while-you-were-sleeping: 1f (E:1) [B]
wolf-hall: 1f (E:1) [A]
wonder-egg-priority: 1f (S:1) [B]
years-and-years: 1f (E:1) [A]
yeh-kaali-kaali-ankhein: 3f (S:2, E:1) [A]
yeh-meri-family: 1f (E:1) [A]
you: 2f (S:2) [A]
young-royals: 1f (S:1) [A]
your-lie-in-april: 1f (E:1) [A]
yuri-on-ice: 2f (S:1, E:1) [B]
```

---

## Cleanup sizing (for Aditya's morning)

**Track A (195 series, 73% of failures):** phrase-level fix
- Pattern: "Critics noted that..." / "widely praised" / "Audiences remember..." in
  review_body or spoiler_free, with no backing URL at that scope
- Fix path: targeted rewrite to BollyAI editorial voice (remove the attributed subject,
  own the sentence). Example: "Critics noted the pacing falters" → "The pacing falters."
- Script-assisted: attribution_regex can locate exact matches; a FULL/KIMI polish pass
  can rewrite. Estimated: 1–2 hours of coordinated batch work.

**Track B (73 series, 27% of failures):** heavier lift
- These have zero pull_quotes. Attribution phrases have no grounding anchor at all.
- Fix path: (a) add real critic pull_quotes with URLs to each failing season, OR
  (b) full prose rewrite to BollyAI voice with no third-party attribution claims.
- Estimated: several hours; requires real sourcing for the quote path.

**Not a blitz artifact:** This is distinct from the ~14,700 blitz-generated NANO episode
drafts (which have been reverted). These 268 failures are in content authored by earlier
Claude sessions before the attribution gate existed. The root cause is the same pattern
(writing "Critics noted..." without sourcing) but these are older files, not the NANO batch.

---

*Audit is read-only. Fix NOTHING. Floor decides cleanup strategy.*
