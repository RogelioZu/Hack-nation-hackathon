// Acceptance checks for the artifact-driven discovery UI (npm run test:discovery).
// Every expectation is read from the canonical artifacts, never typed in: the checks compare the REPLAY bundle with
// the files it was derived from, scan the UI for copied results, and look for secrets in what ships to the browser.
// Set CHECK_URL (e.g. http://localhost:3000) to also check the rendered page.

import { execFileSync } from "node:child_process";
import { cp, mkdtemp, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(webDir, "..");
const bundlePath = path.join(webDir, "data", "discovery-run.json");
const read = async (p) => JSON.parse(await readFile(p, "utf8"));
const results = [];
const check = (id, name, ok, detail = "") => results.push({ id, name, ok: Boolean(ok), detail });

async function walk(dir, filter) {
  const out = [];
  let entries = [];
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...(await walk(p, filter)));
    else if (filter(p)) out.push(p);
  }
  return out;
}

const bundle = await read(bundlePath);
const run = bundle.run;

// A · No scientific number, artifact id or artifact status is written into a UI component.
{
  const STATUS = /\b(UNTESTED|INCONCLUSIVE\w*|SUPPORTED|READY_TO_EXECUTE|WAITING_FOR_\w+|APPROVED_FOR_\w+|EXECUTABLE_NOW|REQUIRES_\w+|NOT_APPLICABLE_\w+|EXPERIMENT_COMPLETED|UNCERTAIN|FORMAL_HETEROGENEITY_TEST|EXPLORATORY_SUBGROUP)\b/;
  const ID = /\b(HYP|PROP|DEC|REV|CRIT|EXP)-\d{3}/;
  const DECIMAL = /(?<![\w.[\-])-?\d+\.\d{2,}(?![\w%])/;
  const files = await walk(path.join(webDir, "app"), (p) => p.endsWith(".tsx"));
  const hits = [];
  for (const f of files) {
    // Comments and presentational props (icon stroke widths) are not content.
    const code = (await readFile(f, "utf8"))
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/(^|[^:])\/\/.*$/gm, "$1")
      .replace(/strokeWidth=\{[\d.]+\}/g, "");
    code.split("\n").forEach((line, i) => {
      for (const [kind, re] of [["status", STATUS], ["id", ID], ["number", DECIMAL]]) {
        const m = line.match(re);
        if (m) hits.push(`${path.relative(webDir, f)}:${i + 1} ${kind} ${m[0]}`);
      }
    });
  }
  check("A", "no hard-coded results, ids or statuses in app/**/*.tsx", hits.length === 0, hits.slice(0, 5).join("; ") || `${files.length} files scanned`);
}

// B · Changing a source artifact and rebuilding changes the UI payload (on a temporary copy; originals untouched).
{
  const tmp = await mkdtemp(path.join(tmpdir(), "discovery-check-"));
  try {
    for (const rel of ["initial_state.json", "metadata/experiment_engine_capabilities.json", "experiments", "reports/experiments", "reports/discovery"]) {
      await cp(path.join(repoRoot, rel), path.join(tmp, rel), { recursive: true }).catch(() => {});
    }
    const followUp = run.followUps[0];
    const resultRel = followUp?.experiment.result?.path;
    const before = followUp?.interactions[0]?.interaction?.estimate;
    let after = null;
    if (resultRel && before != null) {
      const resultPath = path.join(tmp, resultRel);
      const r = await read(resultPath);
      r.interactions[0].interaction.estimate = before + 1;
      await writeFile(resultPath, JSON.stringify(r));
      const out = path.join(tmp, "bundle.json");
      execFileSync(process.execPath, ["--no-warnings", path.join(webDir, "scripts/snapshot-discovery.mjs"), "--root", tmp, "--out", out], {
        stdio: "ignore",
      });
      after = (await read(out)).run.followUps[0].interactions[0].interaction.estimate;
    }
    check("B", "a changed artifact changes the rebuilt payload", after != null && after !== before && after === before + 1, `interaction estimate ${before} → ${after}`);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

// C · Replay needs no agents, model provider or network: the replay path reads only the committed bundle.
{
  // The replay path: the home page, its components and the discovery adapter (the Supabase audit pages are separate).
  const load = await readFile(path.join(webDir, "lib/discovery/load.ts"), "utf8");
  const sources = [path.join(webDir, "app/page.tsx")];
  sources.push(...(await walk(path.join(webDir, "app/_components"), (p) => /\.(tsx?|mjs)$/.test(p))));
  sources.push(...(await walk(path.join(webDir, "lib/discovery"), (p) => /\.(tsx?|mjs)$/.test(p))));
  const external = [];
  for (const f of sources) {
    const t = (await readFile(f, "utf8")).replace(/\/\/.*$/gm, "");
    if (/fetch\(|DATABRICKS|serving-endpoints|localhost:6767|from ["']omnigent|supabase/i.test(t)) external.push(path.relative(webDir, f));
  }
  check("C", "replay reads the bundle; no agent, Databricks or network call", load.includes('from "@/data/discovery-run.json"') && external.length === 0, external.join(", ") || "bundle import only");
}

// D · The first experiment shows its ranking status as the result artifact records it.
{
  const src = await read(path.join(repoRoot, run.baseline.result.path));
  check("D", "first experiment ranking status matches result.json", run.baselineEvidence?.rankingStatus?.code === src.ranking?.status, run.baselineEvidence?.rankingStatus?.code);
}

// E · The follow-up experiment shows its ranking status as recorded.
{
  const f = run.followUps[0];
  const src = f ? await read(path.join(repoRoot, f.experiment.result.path)) : null;
  check("E", "follow-up ranking status matches result.json", f && f.evidence?.rankingStatus?.code === src?.ranking?.status, f?.evidence?.rankingStatus?.code);
}

// F · The formal interaction is separate from the two group slopes, with the artifact's values.
{
  const f = run.followUps[0];
  const i = f?.interactions[0];
  const src = f ? (await read(path.join(repoRoot, f.experiment.result.path))).interactions?.[0] : null;
  const same = i && src && i.interaction.estimate === src.interaction.estimate && i.referenceSlope.estimate === src.reference_group_slope.estimate && i.comparisonSlope.estimate === src.comparison_group_slope.estimate && i.status?.code === src.interpretation_status;
  const ui = await readFile(path.join(webDir, "app/_components/discovery/InteractionPlot.tsx"), "utf8");
  check("F", "interaction shown as its own formal test, values from result.json", same && ui.includes("Formal test") && ui.includes("descriptive, not a test"), i?.status?.code);
}

// G · The hypothesis status change comes from the critique's hypothesis_assessments.
{
  const u = run.updates.at(-1);
  const src = u ? (await read(path.join(repoRoot, u.critiqueKey))).hypothesis_assessments?.find((h) => h.hypothesis_id === u.hypothesisId) : null;
  check("G", "scientific update matches the critique", u && src && u.previous.code === src.previous_status && u.next.code === src.new_status, u ? `${u.protocolId} ${u.previous.code} → ${u.next.code}` : "no update");
}

// H · Decision history keeps every decision artifact, in the order the Director made them.
{
  const dir = path.join(repoRoot, "reports/discovery");
  const files = (await walk(dir, (p) => /\/decisions\/[^/]+\.json$/.test(p))).filter((p) => !p.includes("/superseded/"));
  const times = run.decisions.map((d) => d.createdAt ?? "");
  const ordered = times.every((t, k) => k === 0 || t >= times[k - 1]);
  check("H", "all decisions kept and ordered", run.decisions.length === files.length && ordered, run.decisions.map((d) => `${d.id}:${d.status.code}`).join(" → "));
}

// I · Human reviews are present and linked to what they approve.
{
  const files = (await walk(path.join(repoRoot, "reports/discovery"), (p) => /\/reviews\/[^/]+\.json$/.test(p))).filter((p) => !p.includes("/superseded/"));
  const linked = run.reviews.every((r) => r.approves.length > 0);
  check("I", "human reviews visible and linked", files.length > 0 && run.reviews.length === files.length && linked, run.reviews.map((r) => `${r.id}:${r.decision.code}`).join(", "));
}

// K · The bundle is part of the build: no filesystem access is needed to serve replay.
{
  const s = await stat(bundlePath);
  check("K", "replay bundle committed under web/data and imported at build time", s.size > 0 && run.stages.length > 0, `${Math.round(s.size / 1024)} KB, ${run.stages.filter((x) => x.recorded).length}/${run.stages.length} stages`);
}

// L · No secrets or local paths in the bundle or in what ships to the browser.
{
  const SECRET = /(dapi[0-9a-f]{20,}|sk-[A-Za-z0-9_-]{20,}|sb_secret_|service_role|DATABRICKS_TOKEN|OPENAI_API_KEY|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.|\/home\/[A-Za-z]|\/Users\/[A-Za-z]|[A-Z]:\\\\Users)/;
  const targets = [bundlePath, ...(await walk(path.join(webDir, ".next/static"), (p) => /\.(js|json|html|css)$/.test(p)))];
  const hits = [];
  for (const f of targets) {
    const m = (await readFile(f, "utf8")).match(SECRET);
    if (m) hits.push(`${path.relative(webDir, f)}: ${m[0].slice(0, 24)}`);
  }
  check("L", "no secrets or local paths in bundle or .next/static", hits.length === 0, hits.slice(0, 3).join("; ") || `${targets.length} files scanned`);
}

// Rendered page (optional): the story reads end to end.
if (process.env.CHECK_URL) {
  const html = await (await fetch(process.env.CHECK_URL)).text();
  const text = html.replace(/<script[\s\S]*?<\/script>/g, "").replace(/<!-- -->/g, "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
  const u = run.updates.at(-1);
  const want = [run.baselineEvidence?.rankingStatus?.code, run.followUps[0]?.evidence?.rankingStatus?.code, "Formal test · interaction", u?.previous.code, u?.next.code, ...run.reviews.map((r) => r.decision.code)].filter(Boolean);
  const missing = want.filter((w) => !text.includes(w));
  check("R", `rendered page at ${process.env.CHECK_URL}`, missing.length === 0, missing.join(", ") || "story present");
}

for (const r of results) console.log(`${r.ok ? "PASS" : "FAIL"} ${r.id} ${r.name}${r.detail ? ` — ${r.detail}` : ""}`);
const failed = results.filter((r) => !r.ok);
console.log(failed.length ? `\n${failed.length} check(s) failed.` : `\nAll ${results.length} checks passed.`);
process.exit(failed.length ? 1 : 0);
