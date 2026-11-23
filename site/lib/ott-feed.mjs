import publishers from "../../data/ott/publishers.json" with { type: "json" };

export const OTT_FEED_URL = "https://raw.githubusercontent.com/Declan142/bollyai/main/data/ott/calendar.json";
const dayMs = 86_400_000;
const indiaDay = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Kolkata" });
const belongsTo = (host, domain) => host === domain || host.endsWith(`.${domain}`);

function isoDay(value) {
  if (typeof value !== "string" || !/^\d{4}-\d\d-\d\d$/.test(value)) return null;
  const day = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(day.getTime()) && day.toISOString().slice(0, 10) === value ? day : null;
}

function timestamp(value) {
  if (typeof value !== "string" || !/^\d{4}-\d\d-\d\dT(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,3})?(?:Z|[+-]\d\d:\d\d)$/.test(value)) return NaN;
  return isoDay(value.slice(0, 10)) ? Date.parse(value) : NaN;
}

function sourceGroup(source, platform) {
  if (typeof source?.name !== "string" || !source.name.trim() || typeof source?.url !== "string") return null;
  let url;
  try {
    url = new URL(source.url);
  } catch {
    return null;
  }
  if (url.protocol !== "https:" || url.username || url.password || url.port || url.pathname === "/") return null;
  if (source.type === "press" && platform.domains.some((d) => belongsTo(url.hostname, d))) return "official";
  if (source.type === "official_social" && /^(www\.)?(x|twitter)\.com$/.test(url.hostname)) {
    const handle = /^\/([a-z0-9_]+)\/status\/\d+\/?$/.exec(url.pathname.toLowerCase())?.[1];
    if (platform.accounts.includes(handle)) return "official";
  }
  return source.type === "trade" ? publishers.trades.find((d) => belongsTo(url.hostname, d)) ?? null : null;
}

function parseRelease(row, window) {
  if (!row || row.confidence !== "verified" || row._status !== "verified" || !["film", "series"].includes(row.type)) return null;
  const fields = [row.title, row.platform, row.industry, row.release_date];
  if (!fields.every((f) => typeof f?.value === "string" && f.value.trim() && f.confidence === "verified" && Array.isArray(f.sources))) return null;
  const date = row.release_date.value;
  if (!isoDay(date) || date < window.start || date > window.end) return null;
  const platformName = row.platform.value;
  const name = Object.hasOwn(publishers.aliases, platformName) ? publishers.aliases[platformName] : platformName;
  const platform = Object.hasOwn(publishers.platforms, name) ? publishers.platforms[name] : { domains: [], accounts: [] };
  if (!["hollywood", "streaming"].includes(row.industry.value) || !Array.isArray(row.sources)) return null;
  const groups = new Set();
  const sources = [];
  for (const source of row.sources) {
    const group = sourceGroup(source, platform);
    if (!group || groups.has(group)) continue;
    if (!fields.every((f) => f.sources.some((s) => s?.url === source.url && s.type === source.type))) continue;
    groups.add(group);
    sources.push({ name: source.name.trim(), url: source.url });
  }
  const rule = groups.has("official") ? "official_source" : groups.size >= 2 ? "two_trade_sources" : null;
  if (!rule || row.verification !== rule || !sources.some((s) => s.url === row.source_url)) return null;
  return {
    title: row.title.value.trim(), platform: platformName, release_date: date, type: row.type, sources,
    verdict_line: row.verdict_line_basis?.kind === "catalogue_page" && typeof row.verdict_line === "string" ? row.verdict_line.trim() : ""
  };
}

// Parse only fields the public board renders. Internal links come exclusively from the deployed catalogue.
export function parseOttFeed(raw) {
  if (raw?.schema !== "ott-calendar/v1" || raw.window?.weeks !== 2 || !Array.isArray(raw.entries)) return null;
  const start = isoDay(raw.window.start);
  const end = isoDay(raw.window.end);
  const generated = timestamp(raw.generated_at);
  if (!start || !end || start.getUTCDay() !== 1 || end - start !== 13 * dayMs || !Number.isFinite(generated)) return null;
  const window = { start: raw.window.start, end: raw.window.end };
  const entries = raw.entries.map((row) => parseRelease(row, window));
  if (entries.some((row) => row === null)) return null;
  entries.sort((a, b) => a.release_date.localeCompare(b.release_date) || a.title.localeCompare(b.title));
  return { generated_at: raw.generated_at, window, entries };
}

export function newerOttEdition(raw, published, now = new Date()) {
  const edition = parseOttFeed(raw);
  if (!edition) return null;
  const today = indiaDay.format(now);
  const generated = Date.parse(edition.generated_at);
  const issued = indiaDay.format(new Date(generated));
  return edition.window.start >= published.window.start &&
    issued >= edition.window.start && issued <= edition.window.end &&
    generated > Date.parse(published.generated_at) && generated <= now.getTime() &&
    edition.window.start <= today && today <= edition.window.end ? edition : null;
}
