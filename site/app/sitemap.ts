import type { MetadataRoute } from "next";
import { DESKS } from "../lib/desks";
import { getAllFilms, getOttCalendar, getOttPlatforms, platformSlug } from "../lib/data";
import { getAllSeries } from "../lib/series";
import { getAllWatchLists } from "../lib/recommendations";
import { getAllEndings } from "../lib/endings";

const siteUrl = "https://bollyai.in";
const staticPaths = [
  "/",
  "/about/",
  "/privacy/",
  "/disclaimer/",
  "/contact/",
  "/takedown/",
  "/how-bollyai-works/",
  "/series/",
  "/watch/"
];

function asDate(value: string | undefined, fallback: Date): Date {
  if (!value) {
    return fallback;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? fallback : parsed;
}

export default function sitemap(): MetadataRoute.Sitemap {
  const buildTime = new Date();
  const films = getAllFilms();
  const calendar = getOttCalendar();

  const entries: MetadataRoute.Sitemap = [];
  for (const path of staticPaths) {
    entries.push({ url: `${siteUrl}${path}`, lastModified: buildTime });
  }

  for (const desk of DESKS) {
    const deskFilms = films.filter((film) => film.canonical_industry === desk.slug);
    const latestDeskModified = deskFilms.map((film) => film.date_modified).sort().at(-1);
    entries.push({
      url: `${siteUrl}/${desk.slug}/`,
      lastModified: asDate(latestDeskModified, buildTime)
    });
  }

  for (const film of films) {
    const lastModified = asDate(film.date_modified, buildTime);
    entries.push(
      { url: `${siteUrl}/${film.canonical_industry}/reviews/${film.slug}/`, lastModified },
      { url: `${siteUrl}/${film.canonical_industry}/box-office/${film.slug}/`, lastModified },
      { url: `${siteUrl}/${film.canonical_industry}/upcoming/${film.slug}/`, lastModified }
    );
  }

  entries.push({
    url: `${siteUrl}/ott/calendar/`,
    lastModified: asDate(calendar.generated_at, buildTime)
  });

  for (const platform of getOttPlatforms()) {
    const lastModified = calendar.entries
      .filter((entry) => entry.platform === platform)
      .map((entry) => entry.fetched_at)
      .sort()
      .at(-1);
    entries.push({
      url: `${siteUrl}/ott/${platformSlug(platform)}/`,
      lastModified: asDate(lastModified, buildTime)
    });
  }

  for (const series of getAllSeries()) {
    const lastModified = asDate(series.date_modified, buildTime);
    entries.push({ url: `${siteUrl}/series/${series.slug}/`, lastModified });
    for (const season of series.seasons) {
      entries.push({ url: `${siteUrl}/series/${series.slug}/s${season.number}/`, lastModified });
    }
  }

  for (const list of getAllWatchLists()) {
    entries.push({ url: `${siteUrl}/watch/${list.slug}/`, lastModified: asDate(list.updated, buildTime) });
  }

  for (const ending of getAllEndings()) {
    entries.push({
      url: `${siteUrl}/series/${ending.slug}/ending-explained/`,
      lastModified: asDate(ending.date_modified, buildTime)
    });
  }

  return entries;
}
