"use client";

import { useEffect, useState } from "react";
import { newerOttEdition, OTT_FEED_URL, type OttEdition } from "../lib/ott-feed.mjs";
import { SectionHero } from "./SectionHero";
import { JsonLd } from "./JsonLd";
import { OttCalendarBoard } from "./OttCalendarBoard";

const compactDate = new Intl.DateTimeFormat("en-GB", { month: "short", day: "numeric", year: "numeric", timeZone: "Asia/Kolkata" });
const editionDate = new Intl.DateTimeFormat("en-GB", { month: "long", day: "numeric", year: "numeric", timeZone: "Asia/Kolkata" });

export function CurrentOttCalendar({ published, catalogueLinks }: {
  published: OttEdition;
  catalogueLinks: Record<string, string>;
}) {
  const [calendar, setCalendar] = useState(published);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    let mounted = true;
    const timeout = window.setTimeout(() => controller.abort(), 6000);
    async function refresh() {
      try {
        const response = await fetch(OTT_FEED_URL, {
          signal: controller.signal, credentials: "omit", referrerPolicy: "no-referrer", redirect: "error"
        });
        if (!response.ok) throw new Error("Calendar feed unavailable");
        const raw: unknown = await response.json();
        const latest = newerOttEdition(raw, published);
        if (latest && mounted) setCalendar(latest);
      } catch {
        if (mounted) setUnavailable(true);
      } finally {
        window.clearTimeout(timeout);
      }
    }
    void refresh();
    return () => {
      mounted = false;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [published]);

  const range = compactDate.formatRange(new Date(calendar.window.start), new Date(calendar.window.end)).replace(/\s*[\u2013\u2014]\s*/g, " to ");
  const platforms = new Set(calendar.entries.map((row) => row.platform)).size;
  return (
    <>
      <JsonLd data={{
        "@context": "https://schema.org", "@type": "ItemList", name: `BollyAI streaming releases for ${range}`,
        numberOfItems: calendar.entries.length,
        itemListElement: calendar.entries.map((row, index) => ({
          "@type": "ListItem", position: index + 1,
          item: { "@type": row.type === "film" ? "Movie" : "TVSeries", name: row.title }
        }))
      }} />
      <SectionHero
        eyebrow="Streaming desk"
        title="Streaming release calendar"
        lede="Streaming dates for Western films and series. Open each announcement to check its release region."
        stats={[
          { value: String(calendar.entries.length), label: calendar.entries.length === 1 ? "Verified release" : "Verified releases" },
          { value: String(platforms), label: platforms === 1 ? "Platform" : "Platforms" },
          { value: range, label: "Calendar window" }
        ]}
      >
        <p className="date-modified">
          {unavailable ? "Showing the saved edition of " : "Edition of "}
          <time dateTime={calendar.generated_at}>{editionDate.format(new Date(calendar.generated_at))}</time>
        </p>
      </SectionHero>
      <OttCalendarBoard entries={calendar.entries} catalogueLinks={catalogueLinks} />
    </>
  );
}
