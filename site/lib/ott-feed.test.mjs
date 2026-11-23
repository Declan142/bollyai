import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { parseOttFeed, newerOttEdition } from "./ott-feed.mjs";

const primary = { name: "Netflix Tudum", url: "https://www.netflix.com/tudum/articles/example", type: "press" };
function fixture() {
  const claim = (value) => ({ value, confidence: "verified", sources: [primary] });
  return {
    schema: "ott-calendar/v1", generated_at: "2026-11-23T15:00:00Z",
    window: { start: "2026-11-23", end: "2026-12-06", weeks: 2 },
    entries: [{ _status: "verified", confidence: "verified", id: "film-example", type: "film",
      title: claim("Example"), platform: claim("Netflix"), release_date: claim("2026-12-02"),
      industry: claim("streaming"), sources: [primary], source_url: primary.url,
      verification: "official_source", url: "/series/not-in-this-build/" }]
  };
}

test("verified native feed decodes without trusting a remote internal link", () => {
  const row = parseOttFeed(fixture()).entries[0];
  assert.equal(row.title, "Example");
  assert.equal(row.sources[0].name, "Netflix Tudum");
  assert.equal(row.url, undefined);
  const actual = JSON.parse(readFileSync(new URL("../../data/ott/calendar.json", import.meta.url)));
  assert.ok(parseOttFeed(actual));
});

test("unusable data leaves the entire published edition alone", () => {
  for (const change of [
    (f) => { f.schema = "ott-calendar-week/v1"; },
    (f) => { f.window.start = "2026-11-22"; },
    (f) => { f.window.end = "2026-12-05"; },
    (f) => { f.entries[0].release_date.value = "2026-11-31"; },
    (f) => { f.entries[0].release_date.value = "2026-12-09"; },
    (f) => { f.entries[0].release_date.sources = []; },
    (f) => { f.entries[0].title.confidence = "unverified"; },
    (f) => { f.entries[0].sources = [{ ...primary, url: "http://www.netflix.com/tudum/article" }]; },
    (f) => { f.entries[0].sources = [{ ...primary, url: "https://netflix.com.example.org/news" }]; },
    (f) => { f.entries[0].sources = [{ ...primary, url: "https://www.wikidata.org/wiki/Q1" }]; },
    (f) => { f.entries[0].sources = [{ ...primary, url: "https://abc@netflix.com/news" }]; },
    (f) => { f.entries[0].type = "unknown"; }
  ]) {
    const feed = fixture();
    change(feed);
    assert.equal(parseOttFeed(feed), null);
  }
});

test("promotion requires a strictly newer edition covering today in India", () => {
  const feed = fixture();
  const baseline = { window: feed.window, generated_at: "2026-11-23T14:00:00Z" };
  const time = new Date("2026-11-24T00:00:00Z");
  assert.ok(newerOttEdition(feed, baseline, time));
  assert.equal(newerOttEdition(feed, { ...baseline, generated_at: feed.generated_at }, time), null);
  assert.equal(newerOttEdition(feed, { ...baseline, generated_at: "2026-11-23T16:00:00Z" }, time), null);
  assert.equal(newerOttEdition(feed, baseline, new Date("2026-12-06T19:00:00Z")), null);
  feed.generated_at = "2026-11-24T20:00:00Z";
  assert.equal(newerOttEdition(feed, baseline, time), null);
  feed.generated_at = "2026-11-23T15:00:00Z";
  feed.entries = [];
  assert.deepEqual(newerOttEdition(feed, baseline, time).entries, []);
});

test("two distinct trade publications are both shown; two articles from the same publication do not qualify", () => {
  const feed = fixture();
  const row = feed.entries[0];
  const trade = (name, url) => ({ name, url, type: "trade" });
  const first = trade("Variety", "https://variety.com/release-a");
  const second = trade("Deadline", "https://deadline.com/release-b");
  row.platform.value = "MUBI";
  row.verification = "two_trade_sources";
  row.source_url = first.url;
  const setSources = (sources) => {
    row.sources = sources;
    for (const claim of [row.title, row.platform, row.industry, row.release_date]) claim.sources = sources;
  };
  setSources([first, second]);
  assert.equal(parseOttFeed(feed).entries[0].sources.length, 2);
  setSources([first, trade("Variety", "https://variety.com/release-b")]);
  assert.equal(parseOttFeed(feed), null);
});
