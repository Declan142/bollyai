# BollyAI Library Buildout — loop ledger

**Started:** 2026-06-09 · **Baseline:** 183 series
**Target:** 1000 (Aditya 2026-06-16: 6h back-to-back content push, resource-saving Sonnet) · **Stop:** target reached OR Aditya halts OR BUILDOUT_STOP OR 6h wall-clock
**Deep-lane reserved (do NOT author in loop):** i-will-find-you, beef, physical-100, you (subtitle-grounded deep cohort, owned by bolly-deep lane)
**This run:** ticks COMMIT-ONLY (no push/deploy); the Vyom floor runs full pytest then pushes + deploys in throttled waves (IndexNow <=85/wave).
**Velocity policy:** author+gate+commit AGGRESSIVE (reversible/internal); deploy+IndexNow
THROTTLED — site is 1 day old, avoid spam-velocity signal. (confirm cadence with Aditya)

## Pipeline per batch
1. plan disjoint slugs (filter existing) → 6-8 pools
2. dispatch Sonnet authoring agents (brief: scripts/batch/AUTHORING_BRIEF.md)
3. `validate_series.py` over new files → fix/quarantine failures
4. Opus reconcile spot-pass (fence + score sanity)
5. harvest posters (scripts/harvest_series_posters.py)
6. `cd site && npm run build` → must be green
7. commit
8. (throttled) deploy + IndexNow

## Loop-continuation rule (for any future session)
NEVER end a processing turn without either dispatching the next wave OR scheduling a
wakeup - a wave must always be in flight so completions keep waking the orchestrator.
Read this ledger first, then dispatch the next pending batch's pools. Stop at target
or on Aditya's halt. Deploy+IndexNow stays THROTTLED/held until Aditya's velocity call.

## Progress: 985 / 1000   (baseline 183)

### Batch 20 — 2026-06-18 — 30 series — STATUS: DONE (955->985)
- **A K-Drama:** coffee-prince · goong · yong-pal · 100-days-my-prince · tree-with-deep-roots · daejanggeum
- **B Anime:** soul-eater · nagi-no-asukara · magi · claymore · ore-monogatari · yamada-kun-and-the-seven-witches
- **C US Prestige:** criminal-minds · the-mentalist · the-underground-railroad · the-chair · unbelievable · manifest
- **D UK/Euro:** foyle-s-war · hustle · being-human · midsomer-murders · dirilis-ertugrul · dear-child
- **E Indian+World:** chacha-vidhayak-hain-hamare · paranormal-2020 · outer-range · good-girls · the-peripheral · quicksand
- 30/30 validate clean · build green (8556pp) · AggregateRating gate clean · 14/30 posters (16 SVG fallback)
- Commit: 74b42ff

### Batch 19 — 2026-06-18 — 30 series — STATUS: DONE (925->955)
- **A K-Drama:** boys-over-flowers · city-hunter · the-heirs · master-sun · she-was-pretty · tunnel-kdrama
- **B Anime:** hajime-no-ippo · legend-of-galactic-heroes · darling-in-the-franxx · kaichou-wa-maid-sama · eureka-seven · fullmetal-panic
- **C US:** bosch · rick-and-morty · supernatural · nurse-jackie · the-borgias · carnivale
- **D UK/Euro:** spooks · inspector-morse · father-ted · 1983 · the-new-pope · life-on-mars-uk
- **E World:** extracurricular · the-good-detective · wisting · girl-from-nowhere · ray-2021 · black-spot
- 30/30 validate clean · build green (8428pp) · AggregateRating gate clean · 17/30 posters (13 SVG fallback)
- Commit: eca1cb0

### Batch 18 — 2026-06-18 — 30 series — STATUS: DONE (895->925)
- **A K-Drama:** arthdal-chronicles · my-id-is-gangnam-beauty · familiar-wife · mine-kdrama · a-korean-odyssey · oh-my-ghost
- **B Anime:** bakemonogatari · kuroko-no-basket · log-horizon · shiki · the-melancholy-of-haruhi-suzumiya · chuunibyou-demo-koi-ga-shitai
- **C US/Canada:** enlightened · orphan-black · three-pines · godfather-of-harlem · mythic-quest · ghosts-us
- **D UK/Euro:** the-bay · a-very-british-scandal · the-outlaws · dogs-of-berlin · the-law-according-to-lidia-poet · la-fortuna
- **E World/Asian:** nirvana-in-fire · the-untamed · deadloch · the-newsreader · freud · criminal-record
- 30/30 validate clean · build green (8280pp) · AggregateRating gate clean · 12/30 posters (18 SVG fallback)
- Commit: f99c9e7

### Batch 17 — 2026-06-18 — 30 series — STATUS: DONE (865->895)
- **A K-Drama:** queen-in-hyuns-man · hot-stove-league · eve-kdrama · poong-the-joseon-psychiatrist · shooting-stars-kdrama · tomorrow-kdrama
- **B Anime:** sailor-moon · paranoia-agent · trigun · hibike-euphonium · chihayafuru · the-dangers-in-my-heart
- **C US Prestige:** damages · american-gods · a-gentleman-in-moscow · ray-donovan · say-nothing · justified-city-primeval
- **D UK/Euro:** prime-suspect · shameless-uk · queer-as-folk-uk · unforgotten · shetland · a-french-village
- **E World:** the-letter-for-the-king · caliphate · the-chestnut-man · sky-rojo · the-mire · the-city-and-the-city
- 30/30 validate clean · build green (8168pp) · AggregateRating gate clean · 16/30 posters (14 SVG fallback)
- Commit: dae46a7

### Batch 16 — 2026-06-18 — 30 series — STATUS: DONE (835->865)
- **A K-Drama:** signal-kdrama · start-up-kdrama · taxi-driver-kdrama · dp-kdrama · moving-kdrama · the-good-bad-mother
- **B Anime:** hunter-x-hunter · demon-slayer · bleach · cowboy-bebop · yu-yu-hakusho · dragon-ball-z
- **C US Prestige:** shogun-2024 · battlestar-galactica · fringe · sense8 · person-of-interest · agatha-all-along
- **D UK/Euro:** call-the-midwife · the-tudors · biohackers · 30-coins · black-sails · vikings-valhalla
- **E Indian+World:** class-2023 · el-reino · broken-but-beautiful · tandav · warrior-nun · dexter-new-blood
- 30/30 validate clean · build green (8027pp) · AggregateRating gate clean · 10/30 posters (20 SVG fallback)
- Commit: 59a669c

### Batch 15 — 2026-06-18 — 30 series — STATUS: DONE (805->835)
- **A K-Drama:** bulgasal-immortal-souls · sungkyunkwan-scandal · designated-survivor-60-days · encounter · one-the-woman · on-the-verge-of-insanity
- **B Anime:** fate-zero · ghost-in-the-shell-stand-alone-complex · durarara · kimi-ni-todoke · black-lagoon · baccano
- **C US Prestige:** masters-of-none · insecure · the-good-fight · the-sinner · homecoming · the-wheel-of-time
- **D UK/Euro:** endeavour · jonathan-strange-and-mr-norrell · kleo · des · quiz · ripper-street
- **E Indian+World:** narcos-mexico · the-house-of-flowers · choona · merli · queen-of-the-south · the-journalist
- 30/30 validate clean · build green (7892pp) · AggregateRating gate clean · 14/30 posters (16 SVG fallback)
- Commit: 5c464be

## VIRAL BROWSE shipped 2026-06-09 (commit 3b80448, pushed, NOT deployed)
Genre data 267/267 (Wikidata P136+P31 via harvest_genres.py + curated seed). /series is
now a faceted browse (genre/platform/country/status/era + sort + title search, SSR cards +
hydrated filters). Recency-first: getSeriesByRecency/seriesRecency/isFreshSeries; home "Just
Dropped" rail. NEW + BollyMeter badges. Fixed --font-mono->--font-number. genres in Series
type + AUTHORING_BRIEF (future waves self-tag). validate baseline now 267/267.

## OPEN: (1) DEPLOY held pending Aditya velocity call (nothing live since launch's 183).
## OPEN: (2) hourly fresh-context cron (Aditya asked) - design pending his go.
## Autonomous wave loop PAUSED at 267 (was Opus-in-session; resumes via cron or manual).

## Batches
### Batch 14 — 2026-06-18 — 28 series — STATUS: DONE (777->805)
- **A K-Drama:** forest-of-secrets · mother-kdrama · miss-hammurabi · lawless-lawyer · go-back-couple · one-spring-night
- **B Anime:** horimiya · welcome-to-the-nhk · the-ancient-magus-bride · little-witch-academia · spice-and-wolf · komi-cant-communicate
- **C US Prestige:** russian-doll · when-they-see-us · glow · the-man-in-the-high-castle · goliath
- **D UK/Euro:** small-axe · penny-dreadful · a-very-english-scandal · pistol · chewing-gum · into-the-night
- **E Indian+World:** paava-kadhaigal · our-boys · call-my-agent-bollywood · the-time-in-between · inspector-montalbano
- 28/28 validate clean · build green (7765pp) · AggregateRating gate clean · 12/28 posters (16 SVG fallback)
- Skipped: the-crown (already existed) · six-suspects (= The Great Indian Murder already in catalogue)
- Commit: a9edbe8

### Batch 13 — 2026-06-18 — 30 series — STATUS: DONE (747->777)
- **A K-Drama:** snowdrop · agency-kdrama · her-private-life · do-you-like-brahms · lovestruck-in-the-city · my-dearest
- **B Anime:** inuyasha · k-on · hyouka · food-wars · astra-lost-in-space · non-non-biyori
- **C US Prestige:** girls-hbo · perry-mason-2020 · lovecraft-country · true-blood · generation-kill · how-to-get-away-with-murder
- **D UK/Euro:** doctor-who · spaced · baptiste · vera · the-pursuit-of-love · capitani
- **E Indian+World:** hatufim · invisible-city · first-love-hatsukoi · the-makanai · queen-sono · ethos-bir-baskadir
- 30/30 validate clean · build green (7676pp) · AggregateRating gate clean · 17/30 posters (13 SVG fallback)

### Batch 12 — 2026-06-18 — 30 series — STATUS: DONE (717->747)
- **A K-Drama:** king-the-land · my-country-the-new-age · mystic-pop-up-bar · search-www · the-school-nurse-files · the-bequeathed
- **B US Prestige:** devs · the-act · under-the-banner-of-heaven · the-staircase · the-plot-against-america · the-gilded-age
- **C Anime Gems:** keep-your-hands-off-eizouken · shirobako · planetes · yuru-camp · heike-story · showa-genroku-rakugo-shinju
- **D UK/Euro/Nordic:** inside-no-9 · grantchester · the-salisbury-poisonings · the-collapse · trapped · midnight-sun
- **E Indian+World:** the-trial · khakee-the-bengal-chapter · valeria · hache · monarca · belascoaran-pi
- 30/30 validate clean · build green (7526pp) · AggregateRating gate clean · 13/30 posters (17 SVG fallback)

### Batch 11 — 2026-06-12 — 30 series — STATUS: DONE (branch agents/bolly-south-0612; 512->542)
- **South Indian (5):** november-story · inspector-rishi · navarasa · victim-who-is-next · loser
- **Prestige/Fantasy:** rings-of-power · bad-sisters · the-great · interview-with-the-vampire · what-we-do-in-the-shadows
- **Thriller/Drama:** jack-ryan · maid · inventing-anna · the-dropout · 1923 · gilmore-girls · black-bird · little-fires-everywhere
- **UK/Intl/Limited:** the-tourist · disclaimer · monarch-legacy-of-monsters · presumed-innocent · tulsa-king · alias-grace
- **Variety/Horror:** physical-100 · the-fall-of-the-house-of-usher · bodkin · a-murder-at-the-end-of-the-world · the-watcher · the-sympathizer
- 30/30 validate clean · 150/150 pytest · build green (EXIT:0) · AggregateRating gate clean

### Batch 10 — 2026-06-09 — 30 series — STATUS: DONE (commit c2dd836 pushed; 482->512) — TARGET REACHED
- **VV** K-drama prestige: chief-detective-1958 · welcome-to-samdal-ri · strong-girl-nam-soon · my-girlfriend-is-a-gumiho · strangers-from-hell · live-up-to-your-name
- **WW** US comedy/drama: only-murders-in-the-building · the-marvelous-mrs-maisel · hacks · shrinking · orange-is-the-new-black · pose
- **XX** Anime: psycho-pass · devilman-crybaby · natsumes-book-of-friends · gintama · trigun-stampede · barakamon
- **YY** UK/Euro: the-it-crowd · its-a-sin · poldark · outlander · les-miserables-bbc · i-may-destroy-you
- **ZZ** Indian+World: tripling · your-honor · queen-charlotte · hijack · one-day · 1883
- 30/30 validate clean · build green (2245 pages) · AggregateRating gate clean · 28/30 posters (shrinking + hijack SVG fallback)

### Batch 09 — 2026-06-09 — 30 series — STATUS: DONE (commit bba76e5 pushed; 452->482)
- **QQ** K-drama romance/historical: forecasting-love-and-weather · defendant · when-the-camellia-blooms · law-school · love-in-the-moonlight · my-perfect-stranger
- **RR** US prestige drama: twin-peaks · friday-night-lights · american-horror-story · yellowstone · billions · the-outsider
- **SS** Anime: noragami · kill-la-kill · tokyo-revengers · wonder-egg-priority · dororo · yuri-on-ice
- **TT** UK/Euro/Scandinavian: vikings · wolf-hall · the-missing · catastrophe · humans · emily-in-paris
- **UU** Indian + World: college-romance · the-fame-game · rudra-the-edge-of-darkness · ripley · all-the-light-we-cannot-see · bodies

### Batch 08 — 2026-06-09 — 30 series — STATUS: DONE (commit cb25f3c pushed; 422->452)
- **LL** K-drama romance/supernatural: memories-of-the-alhambra · doom-at-your-service · the-penthouse-war-in-life · romantic-doctor-teacher-kim · sisyphus-the-myth · under-the-queen-umbrella
- **MM** US prestige drama: halt-and-catch-fire · rome · the-shield · sharp-objects · the-knick · rectify
- **NN** Anime: ping-pong-the-animation · land-of-the-lustrous · vivy-fluorite-eyes-song · to-your-eternity · lycoris-recoil · summertime-rendering
- **OO** UK/Euro/Scandinavian: the-night-manager · the-office-uk · the-inbetweeners · the-killing · skam · spiral
- **PP** Indian + World: breathe-into-the-shadows · guilty-minds · a-suitable-boy · wentworth · top-of-the-lake · tvf-cubicles

### Batch 07 — 2026-06-09 — 30 series — STATUS: DONE (commit a44f436 pushed; 392->422)
- **GG** K-drama romance/historical: reply-1994 · navillera · weightlifting-fairy-kim-bok-joo · moon-lovers-scarlet-heart-ryeo · inspector-koo · our-blues
- **HH** US prestige: band-of-brothers · deadwood · abbott-elementary · blue-eye-samurai · gen-v · the-pacific
- **II** Anime: assassination-classroom · erased · parasyte-the-maxim · beastars · blue-period · mushishi
- **JJ** UK/Euro: the-last-kingdom · peep-show · ragnarok-2020 · the-returned · afterlife · ganglands
- **KK** Indian+World: khakee-the-bihar-chapter · mai-2022 · yeh-kaali-kaali-ankhein · taaza-khabar · blood-and-water · katla

### Batch 06 — 2026-06-09 — 30 series — STATUS: DONE (commit cfb2a9d pushed; 362->392)
- **BB** K-drama crime/thriller: voice-kdrama · one-ordinary-day · thirty-nine · divorce-attorney-shin · bad-and-crazy · grid
- **CC** US prestige drama/comedy: station-eleven · this-is-us · dopesick · the-terror · greys-anatomy · community
- **DD** Anime: madoka-magica · clannad · gurren-lagann · tokyo-ghoul · no-game-no-life · anohana
- **EE** UK/Euro prestige: years-and-years · skins · utopia-uk · the-thick-of-it · taboo · derry-girls
- **FF** Indian + World: aranyak · permanent-roommates · tanaav · human-india · aashram · yeh-meri-family

### Batch 05 — 2026-06-09 — 30 series — STATUS: DONE (commit 30512cc pushed; 332->362)
- **W** K-drama romance/slice-of-life: the-world-of-the-married · reply-1997 · nevertheless · romance-is-a-bonus-book · be-melodramatic · love-alarm
- **X** US drama/comedy classics: the-office-us · parks-and-recreation · homeland · the-good-place · arrested-development · american-crime-story
- **Y** Anime: samurai-champloo · great-pretender · odd-taxi · pluto-2023 · ranking-of-kings · nana
- **Z** UK/Europe prestige: the-young-pope · my-brilliant-friend · deutschland-83 · the-end-of-the-f-ing-world · giri-haji · the-fall
- **AA** Indian + World: she · little-things · 3-percent · who-killed-sara · cable-girls · dark-desire

### Batch 04 — 2026-06-09 — 30 series — STATUS: DONE (commit af8550b pushed; 302->332)
- **R** K-drama romance/fantasy: my-love-from-the-star · secret-garden · pinocchio-kdrama · fight-my-way · vagabond-kdrama · suspicious-partner
- **S** US prestige/FX/HBO: the-americans · atlanta · the-handmaids-tale · boardwalk-empire · justified · six-feet-under
- **T** Anime: violet-evergarden · toradora · 86-eighty-six · fruits-basket-2019 · your-lie-in-april · berserk-1997
- **U** UK/Euro/HBO limited: unorthodox · mare-of-easttown · the-night-of · misfits · downton-abbey · doctor-foster
- **V** Indian OTT: four-more-shots-please · bombay-begums · mismatched · scam-2003-the-telgi-story · sunflower · hostel-daze

### Batch 03 — 2026-06-09 — 30 series — STATUS: DONE (commit 77c64c8 pushed; 267->297)
- **M** K-drama recent/crime: juvenile-justice · through-the-darkness · happiness-kdrama · jirisan · the-silent-sea · celebrity
- **N** Netflix/Western: the-haunting-of-hill-house · midnight-mass · never-have-i-ever · daredevil · outer-banks · suits
- **O** Anime: neon-genesis-evangelion · sword-art-online · that-time-i-got-reincarnated-as-a-slime · golden-kamuy · banana-fish · overlord
- **P** European/British: killing-eve · luther · borgen · the-bureau · the-bridge · vis-a-vis
- **Q** Indian: jamtara · leila · ghoul · ic-814-the-kandahar-hijack · bard-of-blood · undekhi

### Batch 02 — 2026-06-09 — 42 series — STATUS: DONE (commit 7ee927d pushed; 225->267)
### Batch 02 (orig plan) — authoring
- **G** K-drama action: vigilante · song-of-the-bandits · bloodhounds · chicago-typewriter · kill-me-heal-me · the-atypical-family · a-shop-for-killers
- **H** K-drama recent/romance: w-two-worlds · while-you-were-sleeping · doctor-slump · weak-hero-class-2 · light-shop · the-frog · crash-course-in-romance
- **I** Netflix Western: you · cobra-kai · the-lincoln-lawyer · the-sandman · griselda · kaos · the-residence
- **J** HBO/Apple prestige: big-little-lies · the-leftovers · watchmen · barry · euphoria · the-morning-show · for-all-mankind
- **K** Anime: bocchi-the-rock · kaguya-sama-love-is-war · dr-stone · the-promised-neverland · haikyu · mushoku-tensei · delicious-in-dungeon
- **L** Indian/World: bambai-meri-jaan · rana-naidu · inside-edge · the-empress · maxton-hall · 1670 · call-my-agent

### Batch 01 — 2026-06-09 — 42 series — STATUS: DONE (commit 26c8ac6 pushed; 183->225; validate 42/42, build green, 150 pytest)
- **A** K-drama recent: when-life-gives-you-tangerines · the-trauma-code · weak-hero-class-1 · reborn-rich · little-women-2022 · the-devil-judge · my-demon
- **B** K-drama prestige: my-liberation-notes · beyond-evil · flower-of-evil · hotel-del-luna · the-uncanny-counter · the-red-sleeve · our-beloved-summer
- **C** Netflix/Western: the-queens-gambit · beef · the-diplomat · the-night-agent · 3-body-problem · bridgerton · the-gentlemen
- **D** Anime: my-hero-academia · blue-lock · oshi-no-ko · jojos-bizarre-adventure · made-in-abyss · re-zero · the-apothecary-diaries
- **E** UK/Euro: sex-education · line-of-duty · happy-valley · normal-people · 1899 · the-day-of-the-jackal · broadchurch
- **F** Indian/World: heeramandi · mumbai-diaries · tvf-pitchers · poacher · money-heist-korea · suburra · shtisel
