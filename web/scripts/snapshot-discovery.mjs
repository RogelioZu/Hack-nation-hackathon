// Builds the REPLAY bundle (web/data/discovery-snapshot.json) from git-tracked discovery artifacts only,
// so replay shows exactly what is committed. Run from web/: `npm run snapshot`.
// Outside a git checkout (e.g. a Vercel upload of web/ alone) it keeps the committed snapshot untouched.

import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { collectArtifacts } from "../lib/discovery/collect.mjs";

const webDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(webDir, "..");
const outFile = path.join(webDir, "data", "discovery-snapshot.json");

let tracked;
try {
  const ls = execFileSync("git", ["ls-files", "--", "initial_state.json", "experiments", "reports/experiments", "reports/discovery"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  tracked = new Set(ls.split("\n").filter(Boolean));
} catch {
  console.log("snapshot-discovery: no git checkout found; keeping the committed snapshot.");
  process.exit(0);
}
if (tracked.size === 0) {
  console.log("snapshot-discovery: no tracked artifacts found; keeping the committed snapshot.");
  process.exit(0);
}

const artifacts = await collectArtifacts(repoRoot, { include: (rel) => tracked.has(rel) });
let commit = null;
try {
  commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: repoRoot, encoding: "utf8" }).trim();
} catch {}

await mkdir(path.dirname(outFile), { recursive: true });
await writeFile(
  outFile,
  // modifiedAt depends on the checkout, not the artifact; drop it so the bundle is reproducible.
  JSON.stringify({ source: "git-tracked artifacts", commit, artifacts: artifacts.map((a) => ({ ...a, modifiedAt: null })) }, null, 2) + "\n",
  "utf8",
);
console.log(`snapshot-discovery: ${artifacts.length} artifacts → ${path.relative(repoRoot, outFile)}`);
