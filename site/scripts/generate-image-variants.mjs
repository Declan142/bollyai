import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const siteRoot = process.cwd();
const publicDir = path.join(siteRoot, "public");
const seriesRoot = path.join(publicDir, "img", "series");
const widths = [185, 342, 500];
const only = new Set(process.argv.slice(2).filter((arg) => !arg.startsWith("--")));
const all = process.argv.includes("--all");

function publicPath(filePath) {
  return `/${path.relative(publicDir, filePath).split(path.sep).join("/")}`;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, payload) {
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`);
}

function candidateDirs() {
  if (!fs.existsSync(seriesRoot)) return [];
  return fs
    .readdirSync(seriesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(seriesRoot, entry.name))
    .filter((dir) => only.size === 0 || only.has(path.basename(dir)))
    .filter((dir) => all || fs.existsSync(path.join(dir, "manifest.json")));
}

async function writeVariant(source, dir, width, format) {
  const height = Math.round(width * 1.5);
  const output = path.join(dir, `w${width}.${format}`);
  const sourceStat = fs.statSync(source);
  if (fs.existsSync(output)) {
    const stat = fs.statSync(output);
    if (stat.mtimeMs >= sourceStat.mtimeMs) {
      return {
        variant: {
          width,
          height,
          format,
          path: publicPath(output),
          bytes: stat.size
        },
        wrote: false
      };
    }
  }
  let pipeline = sharp(source).resize(width, height, { fit: "cover", position: "attention" });
  if (format === "avif") {
    pipeline = pipeline.avif({ quality: 58, effort: 4 });
  } else {
    pipeline = pipeline.webp({ quality: 78, effort: 4 });
  }
  await pipeline.toFile(output);
  const stat = fs.statSync(output);
  return {
    variant: {
      width,
      height,
      format,
      path: publicPath(output),
      bytes: stat.size
    },
    wrote: true
  };
}

async function run() {
  let processed = 0;
  let skipped = 0;
  for (const dir of candidateDirs()) {
    const source = path.join(dir, "poster.jpg");
    const manifestPath = path.join(dir, "manifest.json");
    if (!fs.existsSync(source)) {
      skipped += 1;
      continue;
    }
    const variants = [];
    let wroteVariant = false;
    for (const width of widths) {
      // avif dropped 2026-06-21: 1008 avif files pushed the build over CF Pages' 20k-file
      // cap; avif had 0 <img>/<source> usages (webp+jpg serve all images). webp-only now.
      const webp = await writeVariant(source, dir, width, "webp");
      variants.push(webp.variant);
      wroteVariant = wroteVariant || webp.wrote;
    }
    const originalManifest = fs.existsSync(manifestPath) ? fs.readFileSync(manifestPath, "utf8") : "";
    const manifest = fs.existsSync(manifestPath)
      ? readJson(manifestPath)
      : {
          schema: "bollyai-image-harvest/v2",
          slug: path.basename(dir),
          kind: "series-poster",
          source: null,
          attribution: null
        };
    manifest.variant_tool = "site/scripts/generate-image-variants.mjs";
    if (wroteVariant || !manifest.variant_generated_at) {
      manifest.variant_generated_at = new Date().toISOString();
    }
    manifest.variants = variants;
    const nextManifest = `${JSON.stringify(manifest, null, 2)}\n`;
    if (nextManifest !== originalManifest) {
      writeJson(manifestPath, manifest);
    }
    processed += 1;
  }
  console.log(`image variants: processed=${processed} skipped=${skipped}`);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
