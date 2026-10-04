// Reads the discovery artifacts the agents and the engine write into the repo.
// Plain Node ESM so the same code serves the server (LIVE mode) and scripts/snapshot-discovery.mjs (REPLAY bundle).
// It only copies and compacts JSON; it never computes or edits scientific values.

import { createHash } from "node:crypto";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

/** @typedef {"initial_state"|"research_state"|"capabilities"|"spec"|"experiment_provenance"|"result"|"validation"|"critique"|"hypothesis"|"candidate"|"decision"|"review"} RawKind */
/** @typedef {{kind: RawKind, path: string, sha256: string, modifiedAt: string|null, session: string|null, data: any}} RawArtifact */

// Only the top level of each folder: superseded/ holds retired artifacts kept as a record, not part of the run.
const DISCOVERY_KINDS = {
  critiques: "critique",
  hypotheses: "hypothesis",
  candidates: "candidate",
  decisions: "decision",
  reviews: "review",
};
const EXPERIMENT_ID = /^EXP-\d{3,}$/;

async function exists(p) {
  try {
    await stat(p);
    return true;
  } catch {
    return false;
  }
}

async function dirs(p) {
  try {
    return (await readdir(p, { withFileTypes: true })).filter((d) => d.isDirectory()).map((d) => d.name).sort();
  } catch {
    return [];
  }
}

async function jsonFiles(p) {
  try {
    return (await readdir(p, { withFileTypes: true }))
      .filter((d) => d.isFile() && d.name.endsWith(".json"))
      .map((d) => d.name)
      .sort();
  } catch {
    return [];
  }
}

/** Drops covariance matrices and per-term coefficients; keeps every field the panel shows, values untouched. */
export function compactResult(r) {
  const interval = (i) => i && { lower: i.lower, upper: i.upper, confidence_level: i.confidence_level, adjustment: i.adjustment };
  const ranking = (k) =>
    k && {
      status: k.status,
      point_estimate_order: (k.point_estimate_order ?? []).map((o) => ({
        rank: o.rank,
        outcome: o.outcome,
        coefficient: o.coefficient,
        interval: interval(o.interval),
      })),
      paired_comparisons: (k.paired_comparisons ?? []).map((c) => ({
        outcome_a: c.outcome_a,
        outcome_b: c.outcome_b,
        difference_a_minus_b: c.difference_a_minus_b,
        interval: interval(c.interval),
      })),
      rule: k.rule,
      limitation: k.limitation,
    };
  const slope = (s) => s && { estimate: s.estimate, standard_error: s.standard_error, interval: interval(s.interval) };
  return {
    experiment_id: r.experiment_id,
    status: r.status,
    review_status: r.review_status,
    dataset_version: r.dataset_version,
    sample_size: r.sample_size,
    weighted_population: r.weighted_population,
    estimates: (r.estimates ?? []).map((e) => ({
      model_id: e.model_id,
      variant: e.variant,
      outcome: e.outcome,
      exposure: e.exposure,
      coefficient: e.coefficient,
      standard_error: e.standard_error,
      interval: interval(e.interval),
      simultaneous_outcome_interval: interval(e.simultaneous_outcome_interval),
      units: e.units,
      n: e.n,
      formula: e.provenance?.formula,
      covariance_method: e.provenance?.covariance_method,
      dataset_sha256: e.provenance?.dataset_sha256,
    })),
    ranking: ranking(r.ranking),
    sensitivity_results: (r.sensitivity_results ?? []).map((s) => ({
      name: s.name,
      rule: s.rule,
      n_before: s.n_before,
      n_excluded: s.n_excluded,
      n_after: s.n_after,
      ranking_status: s.ranking?.status ?? null,
    })),
    population_counts: r.population_counts ?? [],
    quality_flags: r.quality_flags ?? [],
    limitations: r.limitations ?? [],
    supported_hypotheses: r.supported_hypotheses ?? [],
    unsupported_hypotheses: r.unsupported_hypotheses ?? [],
    inconclusive_hypotheses: r.inconclusive_hypotheses ?? [],
    // Binary-moderator interactions: group slopes and the formal interaction term, without covariance matrices.
    interactions: (r.interactions ?? []).map((i) => ({
      model_id: i.model_id,
      outcome: i.outcome,
      exposure: i.exposure,
      moderator: i.moderator,
      reference_level: i.reference_level,
      comparison_level: i.comparison_level,
      coding: i.coding,
      reference_group_slope: slope(i.reference_group_slope),
      comparison_group_slope: slope(i.comparison_group_slope),
      interaction: slope(i.interaction),
      interpretation_status: i.interpretation_status,
      interpretation: i.interpretation,
    })),
    // Directions the engine lists for later work; shown verbatim as "not selected", never as a choice.
    candidate_next_experiments: (r.candidate_next_experiments ?? []).map((c) => ({
      question: c.question,
      feasibility: c.feasibility,
    })),
  };
}

function compactInitialState(s) {
  return {
    research_question: s.research_question,
    dataset_version: s.dataset_version,
    population: s.population,
    hypotheses: s.hypotheses,
  };
}

/**
 * Collects every discovery artifact under repoRoot.
 * @param {string} repoRoot absolute path of the repository root
 * @param {{include?: (relPath: string) => boolean}} [options] include: e.g. only git-tracked files for the replay snapshot
 * @returns {Promise<RawArtifact[]>}
 */
export async function collectArtifacts(repoRoot, options = {}) {
  const include = options.include ?? (() => true);
  /** @type {RawArtifact[]} */
  const out = [];

  async function add(kind, rel, session, transform) {
    if (!include(rel)) return;
    const abs = path.join(repoRoot, rel);
    let bytes;
    try {
      bytes = await readFile(abs);
    } catch {
      return;
    }
    let data;
    try {
      data = JSON.parse(bytes.toString("utf8"));
    } catch {
      return; // a half-written file during a live session; the next refresh picks it up
    }
    const { mtime } = await stat(abs);
    out.push({
      kind,
      path: rel,
      sha256: createHash("sha256").update(bytes).digest("hex"),
      modifiedAt: mtime.toISOString(),
      session,
      data: transform ? transform(data) : data,
    });
  }

  await add("initial_state", "initial_state.json", null, compactInitialState);
  await add("capabilities", "metadata/experiment_engine_capabilities.json", null);

  const specIds = new Set((await dirs(path.join(repoRoot, "experiments"))).filter((d) => EXPERIMENT_ID.test(d)));
  const reportIds = new Set((await dirs(path.join(repoRoot, "reports/experiments"))).filter((d) => EXPERIMENT_ID.test(d)));
  for (const id of [...new Set([...specIds, ...reportIds])].sort()) {
    const specRel = (await exists(path.join(repoRoot, "experiments", id, "spec.json")))
      ? `experiments/${id}/spec.json`
      : `reports/experiments/${id}/spec.json`;
    await add("spec", specRel, null);
    await add("experiment_provenance", `experiments/${id}/provenance.json`, null);
    await add("result", `reports/experiments/${id}/result.json`, null, compactResult);
    await add("validation", `reports/experiments/${id}/validation.json`, null);
  }

  for (const session of await dirs(path.join(repoRoot, "reports/discovery"))) {
    await add("research_state", `reports/discovery/${session}/research_state.json`, session);
    for (const [folder, kind] of Object.entries(DISCOVERY_KINDS)) {
      for (const file of await jsonFiles(path.join(repoRoot, "reports/discovery", session, folder))) {
        await add(kind, `reports/discovery/${session}/${folder}/${file}`, session);
      }
    }
  }
  return out;
}
