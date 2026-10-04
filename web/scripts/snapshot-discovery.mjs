// Builds the REPLAY bundle web/data/discovery-run.json from the committed discovery artifacts:
//   git-tracked artifacts → collectArtifacts() → normalizeDiscoveryRun() → DiscoveryRunViewModel.
// The bundle is a derived UI view, not a scientific source: it keeps each source's path and SHA-256, and the
// canonical JSON files stay where they are. Runs before every `next build` (prebuild) and with `npm run snapshot`.
//
// Exits 1 when a required artifact is missing or malformed, so a broken bundle never ships.
// Outside a git checkout (e.g. a Vercel upload of web/ alone) it keeps the committed bundle untouched.
//
// Options (used by scripts/check-discovery.mjs): --root <dir> reads artifacts from another directory (all files,
// no git filter); --out <file> writes the bundle elsewhere.

import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const arg = (name) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : null;
};
const customRoot = arg("--root");
const repoRoot = customRoot ? path.resolve(customRoot) : path.resolve(webDir, "..");
const outFile = path.resolve(arg("--out") ?? path.join(webDir, "data", "discovery-run.json"));

let include = () => true;
let commit = null;
if (!customRoot) {
  let tracked;
  try {
    const ls = execFileSync(
      "git",
      ["ls-files", "--", "initial_state.json", "metadata", "experiments", "reports/experiments", "reports/discovery"],
      { cwd: repoRoot, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
    );
    tracked = new Set(ls.split("\n").filter(Boolean));
  } catch {
    console.log("snapshot-discovery: no git checkout found; keeping the committed bundle.");
    process.exit(0);
  }
  if (tracked.size === 0) {
    console.log("snapshot-discovery: no tracked artifacts found; keeping the committed bundle.");
    process.exit(0);
  }
  include = (rel) => tracked.has(rel);
  // The last commit that changed the artifacts, not HEAD: the bundle stays byte-identical across unrelated commits
  // (so a build never dirties the tree), and "open at commit" links point to a commit that holds these exact files.
  try {
    commit = execFileSync(
      "git",
      ["log", "-1", "--format=%H", "--", "initial_state.json", "metadata", "experiments", "reports/experiments", "reports/discovery"],
      { cwd: repoRoot, encoding: "utf8" },
    ).trim() || null;
  } catch {}
}

// Imported only after the git check, so a Vercel build never needs to load the adapter here.
const { collectArtifacts } = await import("../lib/discovery/collect.mjs");
const { normalizeDiscoveryRun } = await import("../lib/discovery/model.ts");

// modifiedAt depends on the checkout, not the artifact; drop it so the bundle is reproducible.
const artifacts = (await collectArtifacts(repoRoot, { include })).map((a) => ({ ...a, modifiedAt: null }));
const run = normalizeDiscoveryRun(artifacts);

for (const issue of run.issues) console.warn(`snapshot-discovery: ${issue.level}: ${issue.message}`);
const errors = run.issues.filter((i) => i.level === "error");
if (errors.length) {
  console.error(`snapshot-discovery: ${errors.length} error(s) in the source artifacts; the bundle was not written.`);
  process.exit(1);
}

const bundle = {
  note: "Derived UI bundle for REPLAY mode. Not a scientific source: the canonical artifacts are the files listed in sources.",
  commit,
  sources: artifacts.map((a) => ({ kind: a.kind, path: a.path, sha256: a.sha256 })),
  run,
};
await mkdir(path.dirname(outFile), { recursive: true });
await writeFile(outFile, JSON.stringify(bundle, null, 2) + "\n", "utf8");
const recorded = run.stages.filter((s) => s.recorded).length;
console.log(
  `snapshot-discovery: ${artifacts.length} artifacts → ${recorded} of ${run.stages.length} stages → ${path.relative(process.cwd(), outFile)}`,
);
