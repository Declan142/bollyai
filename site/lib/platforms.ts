// India streaming context for the Where-to-Watch surface: the free-vs-paid answer and a
// one-line "how this platform works in India" note - real India-specific information the
// global guides (JustWatch/OTTplay) carry and our series hub does NOT. Categorical and
// durable on purpose: no volatile rupee price numbers we can't keep accurate (same
// integrity line as the no-AggregateRating rule). Always defer to the platform for current
// pricing. Reflects the 2025 Jio + Hotstar merger.

type Access = "paid" | "free-ad";
type PlatformInfo = { access: Access; note: string };

// Keyed by lowercased platform token. A combined string like "JTBC / Netflix" is tokenised
// and the first known token wins.
const PLATFORMS: Record<string, PlatformInfo> = {
  netflix: { access: "paid", note: "Netflix needs a paid subscription in India." },
  "prime video": { access: "paid", note: "Included with an Amazon Prime membership in India." },
  "amazon prime video": { access: "paid", note: "Included with an Amazon Prime membership in India." },
  "disney+ hotstar": { access: "paid", note: "Now part of JioHotstar in India; most originals need a paid plan." },
  jiohotstar: { access: "paid", note: "JioHotstar (the 2025 Jio + Hotstar merger) needs a paid plan for most originals." },
  hotstar: { access: "paid", note: "Now part of JioHotstar in India; most originals need a paid plan." },
  sonyliv: { access: "paid", note: "SonyLIV needs a paid subscription in India." },
  zee5: { access: "paid", note: "ZEE5 needs a paid subscription in India." },
  "apple tv+": { access: "paid", note: "Apple TV+ needs a paid subscription in India." },
  "apple tv": { access: "paid", note: "Apple TV+ needs a paid subscription in India." },
  jiocinema: { access: "paid", note: "JioCinema content now sits under JioHotstar in India." },
  "mx player": { access: "free-ad", note: "Streams free with ads in India - no subscription needed." },
  "amazon mx player": { access: "free-ad", note: "Streams free with ads in India - no subscription needed." },
  youtube: { access: "free-ad", note: "Available free with ads on YouTube in India." }
};

function tokenise(platformString: string): string[] {
  return platformString
    .split(/[/,&]|\band\b/i)
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);
}

export function platformInfo(platformString: string): PlatformInfo {
  for (const t of tokenise(platformString)) {
    if (PLATFORMS[t]) return PLATFORMS[t];
  }
  return { access: "paid", note: `${platformString} needs a paid subscription in India.` };
}

// Is this title free to stream in India (ad-supported) or does it need a subscription?
export function isFreeInIndia(platformString: string): boolean {
  return platformInfo(platformString).access === "free-ad";
}
