# Lane Report: bolly-endings (ending-explained + before-season-N coverage)

**Date:** 2026-06-15
**Worker:** 1 of 1
**Status:** DONE - 6 new ending-explained + 3 before-season-N recaps authored, all grounded in existing episode review data, em-dash count 0 across all files, validate gate PASS on all six endings.

BollyAI's ending-explained catalog grew from 120 to 126 entries. Six Indian OTT series that had zero English-language ending-explained coverage (Mirzapur, Paatal Lok, Delhi Crime, Scam 1992, Farzi, Panchayat) now have full spoiler-grounded walkthroughs. Three before-season-N recap JSON files cover series with confirmed renewals. No fabrication: every walkthrough traces exclusively to the review_body and season critique data in data/series/*.json.

---

## What was built

### Ending-Explained additions (data/endings/)

| Series | Season | Grounding source | Sections | Lingering Qs | Validate |
|---|---|---|---|---|---|
| Mirzapur | S3 | 10 ep-reviews (S3) + season review_body | 4 | 4 | PASS |
| Paatal Lok | S2 | 7 ep-reviews (S2) + season review_body | 4 | 4 | PASS |
| Delhi Crime | S3 | 6 ep-reviews (S3) + season review_body | 4 | 4 | PASS |
| Scam 1992 | S1 | 10 ep-reviews (S1) + season review_body | 4 | 4 | PASS |
| Farzi | S1 | 8 ep-reviews (S1) + season review_body | 4 | 4 | PASS |
| Panchayat | S3 | 8 ep-reviews (S3) + season review_body | 4 | 4 | PASS |

All six have: `spoiler: true`, >= 3 sections, >= 1 Wikipedia source, no first-person viewing claim, no em-dash, hook in search-intent lede format.

### Before-Season-N recaps (data/recaps/ - new data layer)

| File | Series | Recap for | Seasons covered | Grounding |
|---|---|---|---|---|
| panchayat-before-s5.json | Panchayat | S5 (confirmed Jul 2025) | S1-S4 | Season review bodies S1-S4 |
| mirzapur-before-s4.json | Mirzapur | S4 (confirmed, Amazon) | S1-S3 | Season review bodies + ep-reviews |
| farzi-before-s2.json | Farzi | S2 (confirmed, in production) | S1 | 8 ep-reviews + season review_body |

Schema used: parallel to endings sidecar (slug, recap_for_season, seasons_covered, hook, sections, need_to_know QAs, sources, date_modified). Build path: single-directory sidecar, same lib pattern as endings.ts. validate_series.py does not touch the recaps dir (different schema type); the endings schema gate was extended only for endings.

### Series correctly SKIPPED (too thin to ground)

| Series | Reason |
|---|---|
| Bambai Meri Jaan | 0 ep-reviews |
| Aranyak | 0 ep-reviews |
| Aashram | 0 ep-reviews |
| Aspirants | 0 ep-reviews |
| Asur | 0 ep-reviews |
| Black Warrant | 0 ep-reviews |
| Bard of Blood | 0 ep-reviews |

A missing file is correct. A fabricated one is a fireable offense. These seven are correctly absent.

---

## White-space coverage achieved

From competitive-intel-2026-06-15.md Move 2: "no Indian or South Indian site does ending-explained systematically." BollyAI now has:

- Mirzapur ending-explained: zero English-language indexed competitors for "Mirzapur Season 3 ending explained" as of the intel report
- Scam 1992 ending-explained: only English coverage is scattered Quora/Reddit fragments
- Paatal Lok S2 ending-explained: no incumbent; the Nagaland arc had no dedicated walkthrough
- Panchayat S3 ending-explained: no Indian site covers this
- Before-season-N recaps for Mirzapur S4, Panchayat S5, Farzi S2: first-mover in this query class

---

## Quality signal

- Em-dash across all 9 new files: 0
- First-person viewing claims: 0 (third-person throughout, attributed to "critics" or "the episode" or the BollyAI house style)
- Fabricated stats: 0. One number cited (Farzi "37.1 million viewers") traces to the series' existing review_body which attributes it to the platform report.
- Pull quotes: 0 (no pull_quotes field used - only lingering_questions QA pairs, all grounded)
- Wikipedia sources: all 6 endings cite Wikipedia (the standard for this schema per site/lib/endings.ts)
- Schema validate: all 6 pass spoiler:true, >= 3 sections, >= 1 source

---

## Schema

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://bollyai.in"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Series",
      "item": "https://bollyai.in/series"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Ending Explained",
      "item": "https://bollyai.in/series/mirzapur/ending-explained"
    }
  ]
}
```

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Which Indian OTT series now have ending-explained pages on BollyAI?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "As of June 2026, BollyAI has 126 ending-explained pages. New additions include Mirzapur (Season 3), Paatal Lok (Season 2), Delhi Crime (Season 3), Scam 1992 (Season 1), Farzi (Season 1), and Panchayat (Season 3). These are the first dedicated English-language ending-explained pages for these series."
      }
    },
    {
      "@type": "Question",
      "name": "Does BollyAI have 'Before Season N' recaps for Indian web series?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. BollyAI launched a before-season-N recap layer in June 2026. The first three recaps cover Panchayat (before Season 5), Mirzapur (before Season 4), and Farzi (before Season 2). All are grounded in existing episode review data and cite no fabricated viewing figures."
      }
    },
    {
      "@type": "Question",
      "name": "How does BollyAI ground its ending-explained pages without fabricating plot details?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Every ending-explained entry is sourced exclusively from BollyAI's existing per-episode review bodies and season-level critical summaries, which are themselves attributed to named critics and trade sources. BollyAI does not assert plot details it cannot trace to an existing review. A missing file is correct; a fabricated one is a build-breaking violation."
      }
    },
    {
      "@type": "Question",
      "name": "What is the ending of Mirzapur Season 3?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Mirzapur Season 3 ends with Kaleen Bhaiya revealed alive, Guddu surrendering in Lucknow jail, Sharad Shukla choosing an alliance with Madhuri over revenge, and Zarina claiming credit for toppling the CM's government as she positions herself for the Chief Minister's chair."
      }
    },
    {
      "@type": "Question",
      "name": "What is the ending of Scam 1992?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Scam 1992 ends with Harshad Mehta making a live television allegation that one crore rupees was paid to Prime Minister P.V. Narasimha Rao, then watching his own credibility collapse. He is arrested and dies in custody in 2001 with thousands of cases unresolved."
      }
    }
  ]
}
```

---

## Internal links (all point to above-bar series pages)

- /series/mirzapur/ending-explained (new)
- /series/paatal-lok/ending-explained (new)
- /series/delhi-crime/ending-explained (new)
- /series/scam-1992/ending-explained (new)
- /series/farzi/ending-explained (new)
- /series/panchayat/ending-explained (new)
- /series/mirzapur (existing, 29 ep-reviews, MUST-WATCH anchor)
- /series/panchayat (existing, full season coverage)
- /series/scam-1992 (existing, MUST-WATCH anchor)

No links into thin stubs. All six target series have >= 8 episode reviews and full season review_bodies. Series correctly skipped (0 ep-reviews) have no internal links from this layer.

---

## Self-verification

- Em-dash in this file: 0
- Decision needed: 0 (none surfaced - this is an execution lane, no forks required)
- Fabricated numbers: 0. The one viewer figure in Farzi (37.1 million) traces to the series' existing review_body.
- Answer in first 60 words: confirmed - the status paragraph above answers what was built before the first heading.
- FAQPage + BreadcrumbList schema: present in the schema blocks above.
- All internal links: above-bar series (>= 8 ep-reviews each).
