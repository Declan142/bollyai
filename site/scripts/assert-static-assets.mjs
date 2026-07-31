import fs from "node:fs";
import path from "node:path";

const outDir = path.resolve(process.cwd(), "out");
const sourceExtensions = new Set([".css", ".html"]);
const staticExtension = /\.(?:avif|css|gif|ico|jpe?g|js|json|png|svg|webmanifest|webp|woff2?)$/i;

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const absolute = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(absolute) : [absolute];
  });
}

if (!fs.existsSync(outDir)) {
  console.error("site/out does not exist; run next build first.");
  process.exit(1);
}

const sources = walk(outDir).filter((file) => sourceExtensions.has(path.extname(file)));
const references = new Map();

function record(rawReference, source) {
  const withoutSuffix = rawReference.split(/[?#]/, 1)[0];
  if (!withoutSuffix.startsWith("/") || withoutSuffix.startsWith("//") || !staticExtension.test(withoutSuffix)) return;
  let reference;
  try {
    reference = decodeURIComponent(withoutSuffix);
  } catch {
    reference = withoutSuffix;
  }
  if (!references.has(reference)) references.set(reference, new Set());
  references.get(reference).add(path.relative(outDir, source));
}

for (const source of sources) {
  const text = fs.readFileSync(source, "utf8");
  if (path.extname(source) === ".html") {
    // Next embeds its component payload in scripts. Those strings include optional source
    // candidates that are not emitted into the DOM, so only inspect real markup attributes.
    const markup = text.replace(/<script\b[\s\S]*?<\/script>/gi, "");
    for (const match of markup.matchAll(/\b(?:content|href|poster|src|srcset)\s*=\s*["']([^"']+)["']/gim)) {
      for (const candidate of match[1].split(",")) record(candidate.trim().split(/\s+/, 1)[0], source);
    }
  } else {
    for (const match of text.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/gim)) record(match[1].trim(), source);
  }
}

const missing = [...references.entries()]
  .filter(([reference]) => !fs.existsSync(path.join(outDir, reference.replace(/^\//, ""))))
  .sort(([left], [right]) => left.localeCompare(right));

if (missing.length > 0) {
  console.error(`Static asset gate failed: ${missing.length} referenced files are missing from site/out.`);
  for (const [reference, owners] of missing.slice(0, 30)) {
    console.error(`- ${reference} <- ${[...owners].slice(0, 3).join(", ")}`);
  }
  if (missing.length > 30) console.error(`- ...and ${missing.length - 30} more`);
  process.exit(1);
}

console.log(`Static asset gate: ${references.size} unique references across ${sources.length} HTML/CSS files, 0 missing.`);
