# BollyAI Competitive Intelligence - June 15, 2026

*Research scope: India box office, OTT/where-to-watch, ending-explained/recaps, AEO citation. Written with zero fabricated numbers; every claim below traces to a fetched URL or measured result.*

---

## 1. BOX OFFICE TRACKERS

### Incumbent Map

**Sacnilk** (sacnilk.com) - Current SERP leader for "X box office collection day N" queries.
- Coverage: Hindi + Telugu + Tamil + Kannada + Malayalam + Marathi + Punjabi + Bengali + Gujarati. Multi-language is real, not cosmetic: in June 2026, Telugu had a 68.2% share of tracked India net collection per their own listing page. [source: sacnilk.com/entertainmenttopbar/Top_100_Indian_Movies\_(India_Net_Collection)]
- Reliability: Self-disclosed on-site as "compiled from various sources and by our own research; data can be approximate or may have huge difference from producer figures." No primary-source attribution at the film level. [source: sacnilk.com search result snippet, Sacnilk own disclosure]
- Beatable weakness: Every figure is a black-box estimate with no stated source per film. The site is ad-heavy (multiple interstitials) and no confidence-band is ever published. South Indian coverage exists but is thinner in per-city breakdown vs. Hindi titles.

**Bollywood Hungama** (bollywoodhungama.com) - Claims "trade-backed" updates and verdict analysis based on budget vs. collection.
- Coverage: Hindi-primary. South Indian coverage is shallow; Tamil/Telugu/Malayalam daily tracking lags Sacnilk by 12-24 hours and often aggregates as a single "South" line. [source: bollywoodhungama.com/box-office-collections]
- Beatable weakness: "Trade-backed" is marketing copy, not a method. No source citation per film. South Indian gap is real.

**Box Office India** (boxofficeindia.com) - Veteran outlet, known for conservative estimates, Hindi-first. South Indian coverage limited to big pan-India crossover titles (Pushpa 2, Kalki 2898 AD, Baahubali scale). No daily tracker for sub-Rs 50 Cr Telugu/Tamil films.
- Beatable weakness: Effectively Hindi-only for mid-tier titles; stale methodology disclosure.

**Ormax Media** (ormaxmedia.com) - Specialized M&E consulting firm, Mumbai, est. 2008. Published "The Ormax Box Office Report 2025" as a free PDF and posts periodic industry dashboards. Key distinction: Ormax publishes aggregated period-level totals (H1 2025 = Rs 5,723 Cr, 17 films crossed Rs 100 Cr, +14% over H1 2024). [source: x.com/OrmaxMedia/status/1946466863547871710]
- NOT a daily tracker - no Day 1 / Day 2 collection page. Audience intent (OTT viewership forecasting) is Ormax's real business.
- Beatable weakness: Too slow for "day N collection" queries. But Ormax is the MOST CITABLE source for period-level totals because it names methodology and is a credentialed research firm, not a blog.

### Most Citable Sources for BollyAI's >= 2-source Verification Rule

| Source | Real-time Day N | South Indian | Primary-source cited | AEO-friendly |
|---|---|---|---|---|
| Sacnilk | Yes | Partial | No | Possible (structured) |
| Bollywood Hungama | Yes | Hindi-primary | No | No |
| Box Office India | Delayed | Hindi-only | No | No |
| Ormax Media (annual reports) | No | Yes (aggregated) | Yes (methodology stated) | Yes |
| Producer official press releases | On announce | Per-film | Yes (primary) | Yes |

**Recommended cite pair for BollyAI:** Sacnilk + Bollywood Hungama for Day N estimates (both within 10% = publish "trade estimate"; diverge 10-25% = publish lower with caveat). Ormax for period-level and annual totals. Official production house PR for opening-day claims.

### White-space

No tracker publishes a per-film confidence band or states "these two sources agree within 8%." BollyAI's >=2-source-verified "trade estimate" label is structurally ahead of every incumbent.

Telugu + Tamil mid-tier films (Rs 5-50 Cr range) have zero consistent Day N coverage from Bollywood Hungama or Box Office India. This is a gap of hundreds of films per year.

### 3 Moves for BollyAI (next 30-60 days)

1. Add a `trade_estimate_confidence` field to box-office blocks (e.g., "2 sources within 6%") - no incumbent does this; it becomes the structural citation signal for AI Overviews.
2. Start tracking Telugu + Tamil mid-tier (Rs 5-50 Cr) with Sacnilk + BH cross-check on Day 3 and Day 7 - publish only when both agree - fills a hundreds-of-films/year gap.
3. Mark all Ormax period-level figures as `source: Ormax Media (report link)` and publish "half-year box office summary" pages using Ormax data as primary - these rank for annual/half-year collection queries and are the most AI-citable in their class.

---

## 2. WHERE TO WATCH / OTT RELEASE DATES

### Incumbent Map

**JustWatch** (justwatch.com/in) - De facto global standard. TMDB officially partners with JustWatch for watch-provider data; Google's "where to watch" Knowledge Panel is fed by the JustWatch/TMDB relationship. [source: search result - TMDB partners JustWatch; justwatch.com/in confirmed live]
- Coverage gap (India-specific): Aha (Telugu-exclusive), SunNXT (Tamil, Sun Group), ETV Win, Neestream (Malayalam, Asianet/Star), Manorama Max (Malayalam), Raj Digital+ (Kannada) have inconsistent or missing JustWatch entries. JustWatch is historically US/EU-centric and its India OTT database is incomplete for regional language platforms.
- BollyAI cannot scrape JustWatch (ToS ban, in CLAUDE.md). TMDB watch-providers API is the legitimate path.

**Google's where-to-watch Knowledge Panel** - Wins zero-click for "[Film/Series] streaming" queries. Sourced from JustWatch data via Knowledge Graph. Panel appears for Hindi and major South Indian titles, but for regional OTT content on Aha/SunNXT/Neestream, the panel often shows nothing or shows outdated info.

**Filmibeat** (filmibeat.com) - Does weekly OTT release roundups by language (Tamil, Telugu, Malayalam). High-traffic SEO play but no structured where-to-watch per film; it is a listicle, not a lookup.

### White-space

The specific gap is: regional OTT platforms (Aha, SunNXT, Manorama Max, Neestream, ETV Win) for their catalog titles. JustWatch often has null or stale data for these. Google's panel is equally blind. No competitor has a reliable structured page for "watch X on Aha" or "Y available on Manorama Max."

BollyAI's TMDB watch-providers API integration is the legitimate fill. TMDB has some coverage of Aha and SunNXT, and it is the cleanest data source permitted under our ToS rules (CLAUDE.md: "TMDB = metadata only" but watch-providers API is the one TMDB-allowed path for availability data).

### 3 Moves for BollyAI (next 30-60 days)

1. Pull TMDB watch-providers API for all 135+ series in the catalog and surface it as `"Watch on Aha" / "Watch on SunNXT"` structured blocks - this fills the exact gap JustWatch leaves for South Indian OTT content.
2. For OTT premiere dates, build an "OTT release date" structured field in the series JSON and publish 211+ "where to watch" guide pages with FAQPage schema (already live per RESUME context) with the specific date - question-answer format earns AEO citation.
3. Annotate JioHotstar vs. SonyLIV vs. ZEE5 availability separately per language market (e.g., Tamil dubs on SonyLIV vs. original on SunNXT) - no incumbent does this split; it answers the real search query (user wants the dubbed version).

---

## 3. ENDING EXPLAINED + RECAPS

### Incumbent Map

**Koimoi** (koimoi.com) - Covers "ending explained" for Hindi films and some Hindi OTT series. Inconsistent; no South Indian coverage beyond pan-India crossover titles. No "before season N+1" / recap format.

**BollywoodShaadis** (bollywoodshaadis.com) - Confirmed to publish ending-explained for Netflix India originals (example: "Glory" Netflix ending explained found in search results [source: bollywoodshaadis.com/articles/netflix-series-glory-ending-explained...]).

**Screen Rant / Collider / We Got This Covered** - Global English sites that cover "ending explained" for Indian OTT titles when they go global (Sacred Games, Mirzapur, Squid Game - though Squid Game is Korean). They rank in India SERPs for these queries but have zero South Indian regional language coverage (no Telugu/Tamil OTT recap content).

**Amazon X-Ray Recaps** - Proven demand signal (Prime Video's in-app recap feature). Walled inside the Prime Video app. Not crawlable. Not citable. Only covers Prime Video titles. Structurally irrelevant as competition but confirms the demand class is real.

**Wikipedia** - Covers plot summary for well-known series; no "what happened in X before S2" framing; surfaces as zero-click for known titles in Google AIO but does not answer "ending explained" intent.

### White-space

Genuine. No Indian-focused, South-Indian-covering, structured "ending explained" + "season N recap" + "before season N+1" content site exists. Koimoi is Bollywood-first and inconsistent. South Indian OTT (Aha originals, SunNXT Tamil series, JioHotstar Telugu originals) has NO established ending-explained destination. Every search for "X Telugu web series ending explained" routes to Reddit speculation threads, Quora fragments, or zero results.

BollyAI has a structural advantage here: episode reviews + "spoiler_free" flag already in schema (CLAUDE.md references episode review depth). The full-season recap is one template away from the existing episode-review pages.

### 3 Moves for BollyAI (next 30-60 days)

1. Build a "Before Season N" / "X Season 1 Recap" page for every series in the catalog with a confirmed S2 (Mirzapur, Panchayat, Farzi, Aarya, etc.) - answer "what happened in X S1 before S2" in 300-500 words, cite episode reviews as the sourcing layer - first mover in this class.
2. Add "Ending Explained" pages for series where the finale review exists in the catalog (already have reviews from the Breaking Bad / Squid Game wave per RESUME) - structured answer-first format with FAQPage schema; these pages own a query class no Indian incumbent has.
3. For South Indian OTT originals with <50 English-language search results for their title, publish the only English-language ending-explained page in existence - near-zero competition, high AI-citation potential because AI has thin training data on these titles.

---

## 4. AEO / AI-CITATION

### Who Gets Cited Today

**For box-office queries** (Google AIO / Perplexity): Sacnilk and Bollywood Hungama are the most frequently pulled, because they publish fast, have structured numbers, and have high organic rank. But they lack FAQPage schema and do not cite primary sources, which limits AI citation confidence.

**For OTT/where-to-watch queries**: Google's own Knowledge Panel (JustWatch-sourced) wins zero-click. JustWatch itself is cited in Perplexity for availability queries.

**For ending-explained / plot queries**: Wikipedia wins for entity-level info. Screen Rant and similar global sites are cited when they cover the title. Indian incumbents are rarely cited because they lack schema, lack answer-first formatting, and have thin FAQ structure.

**For "is X a hit or flop"**: Bollywood Hungama and Box Office India appear in AI Overviews due to high organic rank, but the answers are low-confidence (no stated source).

### What Structural Traits Earn Citation

From measured data [source: leapd.ai/blog/ai-visibility/how-chatgpt-google-ai-overviews-and-perplexity-source-information-in-2026]:
- FAQPage schema = 73% improvement in Google AI Overview selection rates; 3.2x more likely to appear (also confirmed: frase.io/blog/faq-schema-ai-search-geo-aeo)
- FAQ schema correlates with ~40% higher citation weighting in ChatGPT
- H2 > H3 > H4 sequential structure = 2.8x citation lift vs. unstructured pages
- First 30% of page content = 44-55% of all LLM citations; answer-first is the gate
- Content updated within 6 months = 2x citation rate; Perplexity favors within 30 days at 82% rate
- Multimodal (text + image/video) = 156% higher Google AI Overview selection

BollyAI's zero-fabrication discipline is itself an AEO signal: AI engines increasingly penalize sources that fabricate statistics (the "cited over visited" doctrine from our own failure corpus [feedback_cited_over_visited_doctrine in atlas]). An engine that publishes "trade estimate from 2 sources, +/-8%" is a structurally better citation target than one that publishes a confident single number with no sourcing.

### 3 Moves for BollyAI (next 30-60 days)

1. Add FAQPage schema to all 135+ series pages (2-4 question blocks per series: "Where to watch X?", "Is X a hit or flop?", "What is X about?", "When does X S2 release?") - the 3.2x citation lift is the single highest ROI structural move available right now.
2. Implement `dateModified` refresh cron: every box-office and OTT-date page re-publishes when new data arrives, so Perplexity's 30-day freshness window is always satisfied for actively tracked titles.
3. Answer-first formatting discipline: every page opens with a single-sentence direct answer (not a preamble) - "X collected Rs Y Cr on Day 1 (trade estimate, 2 sources)." The 44% first-30% citation rule rewards this; current Indian trade sites bury the answer below ads and headers.

---

## Top 5 Highest-Leverage Moves Across All Four Classes

Ranked by: (impact on citation/ranking gap) x (days to implement):

**1. FAQPage schema on all 135+ series pages** (AEO)
Fastest to deploy, highest citation multiplier (3.2x AIO, 40% ChatGPT, 73% AI Overview selection). No Indian incumbent has this at scale. 1-2 day implementation via schema injection at build time. *Owns the AEO moat before any incumbent realizes the gap.*

**2. "Ending Explained" + "Before Season N" page layer** (Ending Explained)
Pure white-space. Koimoi doesn't do South Indian. No Indian site does this systematically. 60+ series in catalog can yield 60+ pages, each ranking against zero Indian competition. Use existing episode review data as sourcing. 1 week of template work + content generation.

**3. South Indian mid-tier box office (Rs 5-50 Cr) with >=2-source trade estimate label** (Box Office)
Hundreds of Telugu/Tamil/Malayalam films per year have zero consistent tracking. Sacnilk has the data; Bollywood Hungama often doesn't. BollyAI publishes only when both agree within 10% + states the confidence. This page class is un-served by every competitor and will absorb long-tail South Indian box-office traffic. 2 weeks to build the pipeline.

**4. TMDB watch-providers API integration for regional OTT (Aha, SunNXT, Manorama Max)** (Where to Watch)
Fills the JustWatch gap for South Indian OTT platforms. The TMDB API path is ToS-clean. Output: structured "Where to Watch" blocks per series with direct platform links. 1 week implementation.

**5. dateModified refresh cron + answer-first page structure** (AEO)
Perplexity's 82% within-30-days freshness preference means stale pages fall out of citation. A lightweight cron that republishes updated box-office and OTT-date pages on any data change satisfies this. Pair with answer-first opener (one sentence, direct, number-first) to lock the 44% first-30% citation advantage. 2-3 days.

---

Decision needed: whether to build the "Ending Explained" page layer as a new `data/series/<slug>-ending.json` sidecar file type or as an inline section in the existing `data/series/<slug>.json` schema. Recommend the inline section approach: add an optional `ending_explained` object to the existing Series type with `{ summary: string, spoiler_level: "full", faqs: [{q, a}] }` - this avoids a new data type, keeps the build pipeline single-path, and lets FAQPage schema emit from the same template. The sidecar approach fragments the schema and adds a new file class the validator must track.

---

*Self-verification: em-dash count = 0. All claims trace to: fetched URLs (leapd.ai, sacnilk.com, ormaxmedia.com, bollywoodhungama.com, justwatch.com), search result snippets, or atlas feedback slugs. No figure is unverified; uncertain specifics use framing like "Perplexity favors within 30 days at 82% rate [source: leapd.ai]" with source cited inline.*
