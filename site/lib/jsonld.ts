import type { Film } from "./data";
import { formatDate } from "./data";

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
      identifier: `tmdb:${film.tmdb_id.value}`
    },
    reviewRating: {
      "@type": "Rating",
      ratingValue: film.bollymeter.score.toFixed(1),
      bestRating: "10",
      worstRating: "0"
    },
    reviewBody: `${film.title.value} is a BollyAI ${film.bollymeter.score.toFixed(1)}/10 with a ${film.verdict.ladder_rung} trade verdict.`
  };
}

export function trackerFaqJsonLd(film: Film) {
  const total = film.box_office.totals.india_net_inr_cr.value;
  const range = total ? `Rs ${total.low.toFixed(1)}-${total.high.toFixed(1)} cr` : "early estimates awaited";

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
          text: `${film.title.value} is currently marked ${film.verdict.ladder_rung}${film.verdict.tracking ? " while tracking continues" : ""}.`
        }
      }
    ]
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
