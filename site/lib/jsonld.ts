import type { Film } from "./data";
import { formatDate } from "./data";
import type { Series, SeriesSeason } from "./series";

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
