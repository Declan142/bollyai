import type { Film } from "./data";
import { formatDate } from "./data";
import type { Series, SeriesSeason, EpisodeReview } from "./series";

const siteUrl = "https://bollyai.in";

export function breadcrumbJsonLd(items: Array<{ name: string; url: string }>) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${siteUrl}${item.url}`
    }))
  };
}

export function reviewJsonLd(film: Film) {
  // No Review schema without a real BollyMeter score: a tracking-only film has no review to mark up.
  if (!film.bollymeter) {
    return null;
  }
  const verdictPhrase = film.verdict.ladder_rung ?? "still-tracking";
  return {
    "@context": "https://schema.org",
    "@type": "Review",
    name: `${film.title.value} review: BollyAI verdict`,
    dateModified: film.date_modified,
    author: {
      "@type": "Organization",
      name: "BollyAI",
      url: siteUrl
    },
    publisher: {
      "@type": "Organization",
      name: "BollyAI",
      url: siteUrl
    },
    itemReviewed: {
      "@type": "Movie",
      name: film.title.value,
      datePublished: film.release_date.value,
      identifier: film.qid.value,
      sameAs: `https://www.wikidata.org/wiki/${film.qid.value}`
    },
    reviewRating: {
      "@type": "Rating",
      ratingValue: film.bollymeter.score.toFixed(1),
      bestRating: "10",
      worstRating: "0"
    },
    reviewBody: `${film.title.value} is a BollyAI ${film.bollymeter.score.toFixed(1)}/10 with a ${verdictPhrase} trade verdict.`
  };
}

export function trackerFaqJsonLd(film: Film) {
  const total = film.box_office.totals.india_net_inr_cr?.value ?? null;
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value ?? null;
  const range = total
    ? `Rs ${total.low.toFixed(1)}-${total.high.toFixed(1)} cr`
    : ww
      ? `Rs ${ww.low.toFixed(1)}-${ww.high.toFixed(1)} cr worldwide gross (India nett not yet pair-verified)`
      : "not yet verified across independent sources";

  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: `What is ${film.title.value}'s India nett box office?`,
        acceptedAnswer: {
          "@type": "Answer",
          text: `${film.title.value} is tracked at ${range} India nett as of ${formatDate(film.box_office.totals.as_of)}.`
        }
      },
      {
        "@type": "Question",
        name: `Is ${film.title.value} a hit or flop?`,
        acceptedAnswer: {
          "@type": "Answer",
          text: film.verdict.ladder_rung
            ? `${film.title.value} is currently marked ${film.verdict.ladder_rung}${film.verdict.tracking ? " while tracking continues" : ""}.`
            : `${film.title.value} is still tracking. BollyAI never finalises a verdict mid-run.`
        }
      }
    ]
  };
}

// Visible-FAQ + FAQPage schema for a series hub, built ONLY from real fields
// (renewal note/state, platform, season count, peak verdict). Targets the highest-
// volume Indian-OTT query shapes: "will there be a season N", "release date",
// "where to watch", "is it worth watching". No fabricated dates/numbers.
export function seriesFaq(series: Series, peak: SeriesSeason | undefined): Array<{ q: string; a: string }> {
  const t = series.title.value;
  const faq: Array<{ q: string; a: string }> = [];

  // Renewal / next-season — straight from the sourced renewal note.
  const nextSeasonQ =
    series.renewal.state === "ended" || series.renewal.state === "final-season"
      ? `Will there be another season of ${t}?`
      : `When is ${t}'s next season releasing?`;
  faq.push({ q: nextSeasonQ, a: `${series.renewal.note} (Source: ${series.renewal.source}.)` });

  // Where to watch.
  faq.push({
    q: `Where can I watch ${t} in India?`,
    a: `${t} streams on ${series.platform.value}.`
  });

  // How many seasons.
  faq.push({
    q: `How many seasons of ${t} are there?`,
    a: `${t} has ${series.seasons.length} season${series.seasons.length === 1 ? "" : "s"} so far${
      series.renewal.state === "ended" ? " and has ended" : ""
    }.`
  });

  // Worth watching — peak verdict, honestly framed when unscored.
  faq.push({
    q: `Is ${t} worth watching?`,
    a: peak?.verdict
      ? `BollyAI rates ${t} a ${peak.verdict}${
          peak.bollymeter ? ` at BollyMeter ${peak.bollymeter.score.toFixed(1)}/10` : ""
        }${peak.number ? ` (Season ${peak.number}, its strongest)` : ""}.`
      : `${t} is still being tracked — BollyAI opens a verdict once a season finishes.`
  });

  return faq;
}

export function seriesFaqJsonLd(faq: Array<{ q: string; a: string }>) {
  if (faq.length === 0) return null;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a }
    }))
  };
}

export function seriesJsonLd(series: Series) {
  return {
    "@context": "https://schema.org",
    "@type": "TVSeries",
    name: series.title.value,
    inLanguage: series.original_language.value,
    countryOfOrigin: series.origin,
    numberOfSeasons: series.seasons.length,
    ...(series.qid ? { sameAs: `https://www.wikidata.org/wiki/${series.qid.value}` } : {}),
    url: `${siteUrl}/series/${series.slug}/`
  };
}

// Review schema ONLY when there's a real BollyMeter score; never AggregateRating (single critic).
export function seasonReviewJsonLd(series: Series, season: SeriesSeason) {
  if (!season.bollymeter) return null;
  return {
    "@context": "https://schema.org",
    "@type": "Review",
    name: `${series.title.value} Season ${season.number} review: BollyAI verdict`,
    dateModified: series.date_modified,
    author: { "@type": "Organization", name: "BollyAI", url: siteUrl },
    publisher: { "@type": "Organization", name: "BollyAI", url: siteUrl },
    itemReviewed: {
      "@type": "TVSeason",
      name: `${series.title.value} Season ${season.number}`,
      seasonNumber: season.number,
      numberOfEpisodes: season.episodes,
      partOfSeries: { "@type": "TVSeries", name: series.title.value, url: `${siteUrl}/series/${series.slug}/` }
    },
    reviewRating: {
      "@type": "Rating",
      ratingValue: season.bollymeter.score.toFixed(1),
      bestRating: "10",
      worstRating: "0"
    },
    reviewBody: `${series.title.value} Season ${season.number} is a BollyAI ${season.bollymeter.score.toFixed(1)}/10${season.verdict ? `, ${season.verdict}` : ""}.`
  };
}

// TVEpisode + Review per standout episode. Review block only when a per-episode
// BollyMeter exists (same rule as season/film — never mark up an unscored hour).
export function episodeReviewsJsonLd(series: Series, season: SeriesSeason) {
  const eps = season.episode_reviews ?? [];
  if (eps.length === 0) return null;
  return eps.map((ep: EpisodeReview) => {
    const episode: Record<string, unknown> = {
      "@type": "TVEpisode",
      name: ep.title,
      episodeNumber: ep.number,
      ...(ep.air_date ? { datePublished: ep.air_date } : {}),
      partOfSeason: {
        "@type": "TVSeason",
        seasonNumber: season.number,
        partOfSeries: { "@type": "TVSeries", name: series.title.value, url: `${siteUrl}/series/${series.slug}/` }
      }
    };
    if (ep.bollymeter != null) {
      episode.review = {
        "@type": "Review",
        author: { "@type": "Organization", name: "BollyAI", url: siteUrl },
        publisher: { "@type": "Organization", name: "BollyAI", url: siteUrl },
        reviewRating: {
          "@type": "Rating",
          ratingValue: ep.bollymeter.toFixed(1),
          bestRating: "10",
          worstRating: "0"
        },
        reviewBody: ep.spoiler_free
      };
    }
    return { "@context": "https://schema.org", ...episode };
  });
}

// ItemList for a curated watch list — the AEO-friendly shape for "best X to watch".
export function watchListJsonLd(list: {
  slug: string;
  title: string;
  intro: string;
  updated: string;
  picks: Array<{ title: string; one_line: string }>;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: list.title,
    description: list.intro,
    dateModified: list.updated,
    url: `${siteUrl}/watch/${list.slug}/`,
    numberOfItems: list.picks.length,
    itemListOrder: "https://schema.org/ItemListOrderAscending",
    itemListElement: list.picks.map((p, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: p.title,
      description: p.one_line
    }))
  };
}

export function watchListFaqJsonLd(list: { faq?: Array<{ q: string; a: string }> }) {
  if (!list.faq || list.faq.length === 0) return null;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: list.faq.map((f) => ({
      "@type": "Question",
      name: f.q,
      acceptedAnswer: { "@type": "Answer", text: f.a }
    }))
  };
}

export function webSiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "BollyAI",
    url: siteUrl,
    potentialAction: {
      "@type": "SearchAction",
      target: `${siteUrl}/search/?q={search_term_string}`,
      "query-input": "required name=search_term_string"
    }
  };
}
