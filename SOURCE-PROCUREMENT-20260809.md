# Box-office source procurement — decision brief (2026-08-09)

Produced by codex research (Terra@high, live web) on Vyom's brief; citations spot-checked by Vyom
(both load-bearing URLs return HTTP 200). This unblocks the one open item from
`SOL-BOXOFFICE-20260809.md`: the engine is fail-closed and correct, but
`PRODUCTION_ADAPTER_FACTORIES` / `PRODUCTION_SOURCE_GROUPS` are empty, so the board is
permanently empty until a source pairing clears.

## VERDICT

**No currently public, off-the-shelf pair satisfies the two-independent-groups contract at a
small-site budget.** Both realistic candidates are enterprise, contact-sales, and
`PRICING UNPUBLISHED`, so the annual cost cannot even be calculated today.

The only pairing worth an RFP: **Comscore Movies / IBOE + OpusData (The Numbers)**.
Neither is deployable until each supplier contractually grants ad-supported public display and
attests its weekly Worldwide-USD observations are not derived from the same upstream tracker.

## The independence trap (the most useful finding)

The two-group gate is much harder to satisfy than it looks, because the obvious "second sources"
all trace back to Comscore:

- **Gower Street Analytics is NOT independent of Comscore.** Comscore's own 2019 release states
  Gower Street's film-comparison module uses Comscore Box Office Essentials data.
- **BFI is NOT independent of Comscore.** Sector guidance identifies Comscore as the reporting
  system UK cinemas and distributors file into.
- **OpusData independence is UNPROVEN**, not established. It says "studios and other sources",
  which is not evidence of non-overlap with Comscore. Only a supplier-side provenance warranty
  clears this.

So a naive pairing would produce two readings of the same underlying tracker and the "two
independent groups" contract would be satisfied on paper while being meaningless in fact.

## Candidate screen (10 assessed)

| Candidate | Verdict |
|---|---|
| Comscore Movies / IBOE | Strongest primary tracker. Public terms forbid commercial exploitation without express written consent; 2026 product terms separate feed delivery from data rights. `TERMS UNVERIFIED` for our use. `PRICING UNPUBLISHED`. |
| OpusData / The Numbers | Licensed REST feed, names commercial web developers as subscribers. Actual publication licence and provenance are contract-private. `TERMS UNVERIFIED`, `PRICING UNPUBLISHED`. |
| Baseline Syndication API | Fails coverage: documented weekly endpoint is US-only; international is cumulative per-country. No Worldwide Mon-Sun USD series. |
| Boxoffice Co. Pulse | Terms prohibit commercial use/resale/archiving. Its "Source" API is showtimes, not gross. DISQUALIFIED as published. |
| IMDb / Box Office Mojo | POLICY-BLOCKED by this project regardless of licensing. |
| Gower Street | Terms forbid redistribution; and not independent of Comscore. DISQUALIFIED. |
| BFI weekend figures | UK only, GBP, Friday-Sunday. Useful only as a clearly-labelled UK fallback. Not independent of Comscore. |
| LUMIERE (Eur. Audiovisual Obs.) | Annual European admissions, not weekly worldwide USD. |
| KOBIS Open API | Korea only. Could be an independently-collected Korea observation after licence check. |
| MPA THEME | Personal non-commercial use only; aggregate research, not title-level. DISQUALIFIED. |

## If we proceed: the six contract tests to put in the RFP

Require each vendor to confirm in a signed schedule that it supplies:
1. title-level `gross_usd`
2. a closed observation with start/end exactly Monday 00:00 to Sunday 23:59:59 in a stated timezone
3. `territory=Worldwide` with its country/market inclusion definition
4. revision/finality status plus timestamp
5. a perpetual right to publish the attributed figure on an advertising-funded public website
6. a declaration of raw-source classes, affirming whether the feed depends on Comscore,
   OpusData/Nash, Box Office Mojo/IMDb, or any common sublicensor

Then buy a one-week title-level sample before signing anything larger.

## Honest fallback if we do not fund two enterprise licences

Keep the engine fail-closed and do NOT publish a "Weekly Worldwide Theatrical Box Office" board.
Options that do not violate our own contract:
- a separately-labelled **single-source licensed estimate**, only where the supplier grants public display;
- a **territory-specific official board** (e.g. BFI UK, explicitly GBP + Friday-Sunday, never converted
  or presented as worldwide);
- **narrative reporting** citing distributor press releases per film and observation date, without
  presenting disparate reports as a complete worldwide ranking.

None of these should bypass the existing two-group gate; each is a different product.

## Limitations (carried forward honestly)

This is a procurement eligibility screen, not a legal opinion. Enterprise contracts, quotes, API
field dictionaries, correction policy, timezone semantics, FX treatment, and raw-source provenance
are all non-public for Comscore, OpusData, Baseline, and Boxoffice Co. Public product marketing
cannot prove exact closed Mon-Sun Worldwide USD observations or independence. Every such item is
labelled UNVERIFIED above rather than assumed.
