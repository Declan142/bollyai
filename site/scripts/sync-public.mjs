import fs from "node:fs";
import path from "node:path";

const siteRoot = process.cwd();
const repoRoot = path.resolve(siteRoot, "..");
const source = path.join(repoRoot, "public");
const target = path.join(siteRoot, "public");

if (!fs.existsSync(source)) {
  process.exit(0);
}

fs.mkdirSync(target, { recursive: true });
fs.cpSync(source, target, { recursive: true, force: true });
