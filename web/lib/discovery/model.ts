// normalizeDiscoveryRun: raw discovery artifacts → DiscoveryRunViewModel. Pure function: same artifacts, same view.
// research_state.json is the primary contract (which artifacts exist, their order, relations and expected hashes);
// every value is then read from the canonical artifact it points to. Readers are tolerant on purpose so LIVE mode keeps
// working while agents write; a value that is not in an artifact is shown as missing, never filled in.
// Labels for contract variables live here (and only here) so components never carry scientific vocabulary.

import type {
  ArtifactRef,
  ArtifactType,
  AssessmentView,
  CapabilityChangeView,
  CritiqueView,
  DecisionView,
  DiscoveryIssue,
  DiscoveryRunViewModel,
  EstimateRow,
  EvidenceView,
  ExperimentView,
  Fact,
  FollowUpView,
  HypothesisView,
  InteractionView,
  Interval,
  PairView,
  ProposalView,
  ProtocolHypothesisView,
  RawArtifact,
  ReviewView,
  ScientificUpdateView,
  SlopeView,
  Awaiting,
  Stage,
  StagePart,
  StatusView,
  Tone,
} from "./types";

// Variable names from docs/DATA_CONTRACT.md → reader-facing labels. Labels only; no values.
const OUTCOMES: Record<string, { label: string; noun: string }> = {
  sleep_weekday_min: { label: "Sleep", noun: "sleep" },
  leisure_weekday_min: { label: "Leisure", noun: "leisure" },
  household_conversation_weekday_min: { label: "Household conversation", noun: "household-conversation" },
  personal_hygiene_weekday_min: { label: "Personal hygiene", noun: "personal-hygiene" },
};
const COVARIATES: Record<string, string> = { work_weekday_min: "work time", age: "age", sex: "sex", state: "state" };
const EXPOSURES: Record<string, string> = { commute_5h: "+5 h weekday commuting (300 min Mon–Fri)" };
const METHODS: Record<string, string> = { weighted_linear_regression: "Weighted linear regression" };
const UNCERTAINTY: Record<string, string> = { psu_cluster_CR1_t: "PSU-cluster CR1, t (approximation)" };
const STATES: Record<string, string> = { "09": "CDMX", "15": "Edomex" };
const NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Generic copy for a hypothesis status change, keyed by the new status the critique recorded (no numbers, no ids).
const UPDATE_EXPLAINER: Record<string, string> = {
  INCONCLUSIVE:
    "The experiment formally tested the hypothesis, but its uncertainty interval did not allow the lab to resolve it. The state now records an open, tested question instead of a certainty it does not have.",
  SUPPORTED: "The formal test produced evidence consistent with the hypothesis under the specified model. It remains an observational association.",
  NOT_SUPPORTED: "The formal test produced evidence that does not support the hypothesis under the specified model. It remains an observational association.",
};

export function outcomeLabel(id: string): string {
  return OUTCOMES[id]?.label ?? id;
}

const str = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v.trim() : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const obj = (v: unknown): Record<string, unknown> => (v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {});
const first = (...vs: unknown[]): string | null => {
  for (const v of vs) {
    const s = str(v);
    if (s) return s;
  }
  return null;
};

/** A status exactly as written, with the tone the UI uses for it. Components never decide tones themselves. */
export function statusOf(code: unknown): StatusView | null {
  const c = str(code);
  if (!c) return null;
  const u = c.toUpperCase();
  const tone: Tone = /UNSUPPORTED|NOT_SUPPORTED|NOT_APPLICABLE/.test(u)
    ? "neutral"
    : /INCONCLUSIVE|UNCERTAIN|INCLUDES_ZERO/.test(u)
      ? "uncertain"
      : /WAITING|REQUIRES|BLOCKED|FAILED|INVALID|REJECT/.test(u)
        ? "warn"
        : /READY|APPROVED|EXECUTABLE|COMPLETED|SUPPORTED|VALID|PASS/.test(u)
          ? "good"
          : "neutral";
  return { code: c, tone };
}
const status = (code: unknown, fallback: string): StatusView => statusOf(code) ?? { code: fallback, tone: "neutral" };

/** Strings, or objects carrying a statement under one of the usual keys, flattened to text. */
function texts(v: unknown): string[] {
  if (v == null) return [];
  if (typeof v === "string") return v.trim() ? [v.trim()] : [];
  if (!Array.isArray(v)) return texts([v]);
  return v.flatMap((item) => {
    if (typeof item === "string") return item.trim() ? [item.trim()] : [];
    if (item && typeof item === "object") {
      const o = item as Record<string, unknown>;
      const body = first(o.statement, o.claim, o.question, o.quote, o.text, o.summary, o.description);
      return body ? [body] : [];
    }
    return [];
  });
}

const stripKind = (s: string) => s.replace(/^[A-Z_]+:\s*/, "");

function stem(path: string): string {
  return path.split("/").pop()!.replace(/\.json$/, "");
}

function short(id: string): string {
  return UUID.test(id) ? id.slice(0, 8) : id;
}

/** Display id: the artifact's own readable id when it has one, else a kind prefix plus the short uuid. */
function displayId(prefix: string, ownId: string | null, path: string): { id: string; full: string | null } {
  const raw = ownId ?? stem(path);
  if (!UUID.test(raw)) return { id: raw, full: null };
  return { id: `${prefix} · ${short(raw)}`, full: raw };
}

function interval(i: unknown): Interval | null {
  const o = obj(i);
  const lower = num(o.lower);
  const upper = num(o.upper);
  if (lower == null || upper == null) return null;
  return { lower, upper, level: num(o.confidence_level), adjustment: str(o.adjustment) };
}

function slope(v: unknown): SlopeView | null {
  const o = obj(v);
  const estimate = num(o.estimate);
  return estimate == null ? null : { estimate, standardError: num(o.standard_error), ci: interval(o.interval) };
}

function populationLines(p: unknown, n?: number | null): string[] {
  const o = obj(p);
  const lines: string[] = [];
  const ageMin = num(o.age_min);
  const ageMax = num(o.age_max);
  if (ageMin != null && ageMax != null) lines.push(`Workers aged ${ageMin}–${ageMax}`);
  if (Array.isArray(o.states)) lines.push(o.states.map((s) => STATES[String(s)] ?? String(s)).join(" + "));
  if (Array.isArray(o.sexes)) {
    const s = o.sexes.map(String);
    lines.push(s.includes("male") && s.includes("female") ? "Women and men" : s.includes("female") ? "Women only" : "Men only");
  }
  const count = n ?? num(o.expected_n);
  if (count != null) lines.push(`n = ${count.toLocaleString("en-US")}`);
  return lines;
}

const byTime = (a: string | null, b: string | null) => (a ?? "").localeCompare(b ?? "");

// --- Normalizer --------------------------------------------------------------

export function normalizeDiscoveryRun(raw: RawArtifact[]): DiscoveryRunViewModel {
  const issues: DiscoveryIssue[] = [];
  const artifacts: Record<string, ArtifactRef> = {};
  const byKind = (k: RawArtifact["kind"]) => raw.filter((a) => a.kind === k);

  // research_state.json: the index of what exists, how it relates and which bytes were recorded.
  const rsRaw = byKind("research_state")[0] ?? null;
  const rs = obj(rsRaw?.data);
  const expected = obj(obj(rs.provenance).inputs) as Record<string, string>;
  const rsValidation = obj(rs.validation);
  if (rsRaw && rsValidation.valid === false) {
    issues.push({ level: "error", message: "research_state.json reports validation errors", path: rsRaw.path });
  }
  const session = rsRaw?.session ?? raw.find((a) => a.session)?.session ?? "<session>";
  const discoveryDir = `reports/discovery/${session}`;

  const ref = (
    a: RawArtifact,
    type: ArtifactType,
    label: string,
    id: { id: string; full: string | null },
    extra: Partial<Pick<ArtifactRef, "createdAt" | "producer" | "codeVersion" | "datasetVersion" | "sourceExperiment">> & {
      facts?: Fact[];
    } = {},
  ): ArtifactRef => {
    const expectedSha = str(expected[a.path]);
    if (expectedSha && expectedSha !== a.sha256) {
      issues.push({ level: "warning", message: `SHA-256 differs from research_state.json (${a.path})`, path: a.path });
    }
    const r: ArtifactRef = {
      key: a.path,
      id: id.id,
      fullId: id.full,
      type,
      label,
      path: a.path,
      sha256: a.sha256,
      expectedSha256: expectedSha,
      modifiedAt: a.modifiedAt,
      createdAt: extra.createdAt ?? null,
      session: a.session,
      producer: extra.producer ?? null,
      codeVersion: extra.codeVersion ?? null,
      datasetVersion: extra.datasetVersion ?? null,
      sourceExperiment: extra.sourceExperiment ?? null,
      facts: extra.facts ?? [],
      links: [],
    };
    artifacts[r.key] = r;
    return r;
  };
  const link = (from: ArtifactRef | null | undefined, to: ArtifactRef | null | undefined) => {
    if (!from || !to || from.key === to.key) return;
    if (!from.links.includes(to.key)) from.links.push(to.key);
    if (!to.links.includes(from.key)) to.links.push(from.key);
  };

  // Every artifact research_state.json points to must exist; otherwise the bundle would silently drop part of the run.
  const collected = new Set(raw.map((a) => a.path));
  const listed = [
    ...arr(rs.critiques),
    ...arr(rs.hypotheses).filter((h) => str(obj(h).artifact)?.endsWith(".json")),
    ...arr(rs.candidate_experiments),
    ...arr(rs.decisions),
    ...arr(rs.reviews),
  ].map((e) => str(obj(e).artifact));
  arr(rs.experiments).forEach((e) => listed.push(...Object.values(obj(obj(e).artifacts)).map(str)));
  // A spec is read from experiments/<id>/ when that copy exists; the reports/ copy is the same spec.
  const specAlias = (p: string) => p.replace(/^reports\/experiments\/([^/]+)\/spec\.json$/, "experiments/$1/spec.json");
  for (const p of listed) {
    if (p && !collected.has(p) && !collected.has(specAlias(p))) {
      issues.push({ level: "error", message: `research_state.json lists ${p}, which was not found`, path: p });
    }
  }

  // --- Question and dataset
  const state = byKind("initial_state")[0];
  const s = obj(state?.data);
  const questionText = first(rs.research_question, s.research_question);
  if (!questionText) issues.push({ level: "error", message: "No research question in initial_state.json or research_state.json", path: null });
  const questionRef = state
    ? ref(state, "QUESTION", "Research question", { id: "initial_state", full: null }, {
        producer: "Shared Research State (Omnigent session input)",
        datasetVersion: str(s.dataset_version),
        facts: [{ label: "Dataset", value: str(s.dataset_version) ?? "—", mono: true }],
      })
    : null;
  const rsRef = rsRaw
    ? ref(rsRaw, "QUESTION", "Research state index", { id: "research_state", full: null }, {
        producer: str(obj(rs._generated).generator) ?? "scripts/build_research_state.py",
        datasetVersion: str(obj(rs.dataset).version),
        facts: [
          { label: "Validation", value: rsValidation.valid === true ? "valid" : rsValidation.valid === false ? "invalid" : "—" },
          { label: "Inputs sha256", value: str(obj(rs.provenance).inputs_sha256) ?? "—", mono: true },
        ],
      })
    : null;
  link(questionRef, rsRef);
  const ds = obj(rs.dataset);
  const protocolTitles = new Map(
    arr(rs.hypotheses)
      .map(obj)
      .filter((h) => h.source === "protocol")
      .map((h) => [String(h.hypothesis_id), str(h.title)] as const),
  );

  // --- Experiments (spec + result + validation + provenance)
  const results = new Map(byKind("result").map((a) => [a.path.split("/")[2], a]));
  const validations = new Map(byKind("validation").map((a) => [a.path.split("/")[2], a]));
  const provenances = new Map(byKind("experiment_provenance").map((a) => [a.path.split("/")[1], a]));
  const experiments = byKind("spec")
    .map((spec) => {
      const id = str(spec.data?.experiment_id) ?? spec.path.split("/").at(-2)!;
      return { spec, result: results.get(id), validation: validations.get(id), provenance: provenances.get(id), id };
    })
    .sort((a, b) => a.id.localeCompare(b.id));

  const experimentView = (spec: RawArtifact, result?: RawArtifact, validation?: RawArtifact, prov?: RawArtifact): ExperimentView => {
    const sp = obj(spec.data);
    const r = result ? obj(result.data) : null;
    const v = validation ? obj(validation.data) : null;
    const id = str(sp.experiment_id) ?? stem(spec.path.replace(/\/spec\.json$/, ""));
    if (result && !Array.isArray(r?.estimates)) {
      issues.push({ level: "error", message: `${result.path} has no estimates array`, path: result.path });
    }
    const pv = prov ? obj(prov.data) : null;
    const specRef = ref(spec, "EXPERIMENT", "Experiment spec", { id: `${id} spec`, full: null }, {
      producer: pv ? `ExperimentSpec from ${first(pv.proposal_id) ?? "an approved proposal"} (engine validates)` : "ExperimentSpec (agents propose, engine validates)",
      createdAt: pv ? first(pv.created_at) : null,
      codeVersion: pv ? first(pv.spec_translation_code_version, pv.code_version) : null,
      datasetVersion: str(sp.dataset_version),
      facts: [
        { label: "Method", value: str(sp.method) ?? "—", mono: true },
        { label: "Exposure", value: str(sp.exposure) ?? "—", mono: true },
        { label: "Hypotheses", value: arr(sp.hypothesis_ids).join(", ") || "—" },
        ...(obj(sp.interaction).moderator ? [{ label: "Moderator", value: String(obj(sp.interaction).moderator), mono: true }] : []),
      ],
    });
    const rp = r ? obj(r.provenance) : {};
    const resultRef = result
      ? ref(result, followUpIds.has(id) ? "EXPERIMENT" : "EVIDENCE", "Experiment result", { id: `${id} result`, full: null }, {
          producer: "Deterministic engine (src/experiments)",
          codeVersion: first(rp.code_sha256, rp.code_version),
          datasetVersion: str(r?.dataset_version),
          sourceExperiment: id,
          facts: [
            { label: "Status", value: str(r?.status) ?? "—", mono: true },
            { label: "Review", value: str(r?.review_status) ?? "—", mono: true },
            { label: "Ranking", value: str(obj(r?.ranking).status) ?? "—", mono: true },
            { label: "Sample", value: num(r?.sample_size) != null ? `n = ${(r!.sample_size as number).toLocaleString("en-US")}` : "—" },
          ],
        })
      : null;
    const validationRef = validation
      ? ref(validation, "EVIDENCE", "Reproducibility check", { id: `${id} validation`, full: null }, {
          producer: "scripts/run_experiment.py (two runs)",
          sourceExperiment: id,
          facts: [
            { label: "Status", value: str(v?.status) ?? "—", mono: true },
            { label: "Identical runs", value: v?.identical_spec_identical_result === true ? "yes" : v ? "no" : "—" },
            {
              label: "Dataset hash",
              value: v?.analytic_sha256_before && v?.analytic_sha256_before === v?.analytic_sha256_after ? "unchanged" : "—",
            },
          ],
        })
      : null;
    const provRef = prov
      ? ref(prov, "EXPERIMENT", "Experiment provenance", { id: `${id} provenance`, full: null }, {
          producer: first(pv?.created_by) ?? "experiment_runner",
          createdAt: first(pv?.created_at),
          codeVersion: first(pv?.code_version),
          datasetVersion: first(pv?.dataset_version),
          sourceExperiment: first(pv?.source_experiment_id),
          facts: [
            { label: "Decision", value: first(pv?.decision_id) ?? "—", mono: true },
            { label: "Approval", value: first(pv?.decision_approval_id) ?? "—", mono: true },
            { label: "Proposal", value: first(pv?.proposal_id) ?? "—", mono: true },
          ],
        })
      : null;
    link(specRef, resultRef);
    link(resultRef, validationRef);
    link(specRef, provRef);
    if (questionRef && !followUpIds.has(id)) link(questionRef, specRef);
    return {
      experimentId: id,
      spec: specRef,
      result: resultRef,
      validation: validationRef,
      question: str(sp.research_question),
      population: populationLines(sp.population, num(r?.sample_size)),
      exposure: str(sp.exposure) ? (EXPOSURES[sp.exposure as string] ?? (sp.exposure as string)) : null,
      outcomes: arr(sp.outcomes).map(String),
      covariates: arr(sp.covariates).map((c) => COVARIATES[String(c)] ?? String(c)),
      method: str(sp.method) ? (METHODS[sp.method as string] ?? (sp.method as string)) : null,
      uncertainty: str(sp.uncertainty) ? (UNCERTAINTY[sp.uncertainty as string] ?? (sp.uncertainty as string)) : null,
      hypothesisIds: arr(sp.hypothesis_ids).map(String),
      status: statusOf(r?.status),
      reviewStatus: statusOf(r?.review_status),
      reproduced: v ? v.identical_spec_identical_result === true : null,
      datasetUnchanged: v ? Boolean(v.analytic_sha256_before) && v.analytic_sha256_before === v.analytic_sha256_after : null,
      sampleSize: num(r?.sample_size),
      datasetVersion: str(sp.dataset_version) ?? str(r?.dataset_version),
    };
  };

  const evidenceView = (exp: ExperimentView, result: RawArtifact): EvidenceView => {
    const r = obj(result.data);
    const adjusted = arr(r.estimates)
      .map(obj)
      .filter((e) => typeof e.model_id === "string" && (e.model_id as string).startsWith("adjusted:"));
    const rows: EstimateRow[] = adjusted
      .map((e) => ({
        outcome: String(e.outcome),
        label: outcomeLabel(String(e.outcome)),
        coefficient: num(e.coefficient) ?? 0,
        standardError: num(e.standard_error),
        ci: interval(e.interval),
        simultaneous: interval(e.simultaneous_outcome_interval),
        n: num(e.n),
      }))
      .sort((a, b) => a.coefficient - b.coefficient);
    // "Strongest" only means something when two or more outcomes share the model.
    const strongest = rows.length > 1 && rows[0].coefficient < 0 ? rows[0] : null;

    const sentences: string[] = [];
    if (strongest) {
      sentences.push(`${strongest.label} had the strongest negative point estimate.`);
      if (adjusted[0]?.exposure === "commute_5h") {
        const minutes = Math.round(Math.abs(strongest.coefficient));
        const noun = OUTCOMES[strongest.outcome]?.noun ?? strongest.label.toLowerCase();
        const crossesZero = strongest.ci ? strongest.ci.lower <= 0 && strongest.ci.upper >= 0 : false;
        sentences.push(
          `Five additional weekday commuting hours were associated with about ${minutes} fewer weekday ${noun} minutes in the adjusted model${
            crossesZero ? ", with a 95% interval that includes zero" : ""
          }.`,
        );
      }
    }

    const ranking = obj(r.ranking);
    const rankingCode = str(ranking.status);
    const countWord = NUMBER_WORDS[rows.length] ?? String(rows.length);
    const rankingSentence =
      rankingCode === "INCONCLUSIVE_RANKING"
        ? `The ranking across all ${countWord} outcomes remained inconclusive.`
        : rankingCode === "DISTINGUISHABLE_RANKING"
          ? `Every pairwise difference in the ordering of the ${countWord} outcomes excluded zero after Bonferroni adjustment.`
          : null;

    // Unresolved pairs first: they are the reason a ranking stays inconclusive.
    const pairItems: PairView[] = arr(ranking.paired_comparisons)
      .map(obj)
      .map((c) => {
        const i = interval(c.interval);
        return {
          a: outcomeLabel(String(c.outcome_a)),
          b: outcomeLabel(String(c.outcome_b)),
          difference: num(c.difference_a_minus_b) ?? 0,
          interval: i,
          resolved: i ? i.lower > 0 || i.upper < 0 : false,
        };
      })
      .sort((x, y) => Number(x.resolved) - Number(y.resolved));
    const assessments: AssessmentView[] = (["supported", "unsupported", "inconclusive"] as const).flatMap((bucket) =>
      arr(r[`${bucket}_hypotheses`])
        .map(obj)
        .filter((h) => str(h.id))
        .map((h) => ({ id: String(h.id), assessment: str(h.assessment) ?? bucket, evidence: str(h.evidence), status: status(bucket.toUpperCase(), bucket) })),
    );
    const head = adjusted[0];
    return {
      experimentId: exp.experimentId,
      artifact: exp.result!,
      rows,
      strongestNegative: strongest,
      sentences,
      rankingStatus: statusOf(rankingCode),
      rankingSentence,
      rankingRule: str(ranking.rule),
      pairs: pairItems.length
        ? {
            resolved: pairItems.filter((p) => p.resolved).length,
            total: pairItems.length,
            adjustment: pairItems[0].interval?.adjustment ?? null,
            items: pairItems,
          }
        : null,
      assessments,
      nextDirections: arr(r.candidate_next_experiments)
        .map((c) => str(obj(c).question))
        .filter((q): q is string => Boolean(q)),
      units: str(head?.units),
      sampleSize: num(r.sample_size),
      covariates: exp.covariates,
      covarianceMethod: str(head?.covariance_method),
      sensitivity: arr(r.sensitivity_results)
        .map(obj)
        .map((x) => ({ name: String(x.name), nAfter: num(x.n_after), nExcluded: num(x.n_excluded), rankingStatus: str(x.ranking_status) })),
      qualityFlags: arr(r.quality_flags).map(String),
    };
  };

  const interactionViews = (result: RawArtifact): InteractionView[] =>
    arr(obj(result.data).interactions)
      .map(obj)
      .filter((i) => str(i.moderator))
      .map((i) => ({
        outcome: String(i.outcome),
        outcomeLabel: outcomeLabel(String(i.outcome)),
        exposure: String(i.exposure),
        moderator: String(i.moderator),
        referenceLevel: String(i.reference_level),
        comparisonLevel: String(i.comparison_level),
        coding: str(i.coding),
        referenceSlope: slope(i.reference_group_slope),
        comparisonSlope: slope(i.comparison_group_slope),
        interaction: slope(i.interaction),
        status: statusOf(i.interpretation_status),
        interpretation: str(i.interpretation),
        units: str(i.units) ?? str(obj(arr(obj(result.data).estimates)[0]).units),
      }));

  // Experiments that an approval review authorized (or whose provenance names a decision) are follow-ups.
  const followUpIds = new Set<string>();
  experiments.forEach(({ id, provenance }) => {
    if (provenance && str(obj(provenance.data).decision_id)) followUpIds.add(id);
  });
  arr(rs.experiments)
    .map(obj)
    .forEach((e) => {
      if (arr(e.authorized_by).length) followUpIds.add(String(e.experiment_id));
    });
  // The first experiment is the baseline even when nothing marks it.
  const views = experiments.map(({ spec, result, validation, provenance, id }) => {
    const exp = experimentView(spec, result, validation, provenance);
    return { id, exp, evidence: result && exp.result ? evidenceView(exp, result) : null, interactions: result ? interactionViews(result) : [], provenance };
  });
  const baselineEntry = views.find((v) => !followUpIds.has(v.id)) ?? views[0] ?? null;

  // --- Critiques
  const critiqueView = (a: RawArtifact): CritiqueView => {
    const d = obj(a.data);
    const prov = obj(d.provenance);
    const experimentId = first(d.experiment_id, prov.source_experiment_id);
    if (!experimentId) issues.push({ level: "error", message: `${a.path} names no experiment`, path: a.path });
    const agent = first(prov.agent, d.agent, d.decided_by) ?? "scientific_critic";
    const model = first(obj(prov.declared_executor).model, d.model);
    const verdict = first(d.scientific_status, d.verdict, d.status);
    const r = ref(a, "UNCERTAINTY", "Scientific critique", displayId("CRIT", first(d.critique_id, d.id), a.path), {
      createdAt: first(prov.created_at, d.created_at),
      producer: [agent, model].filter(Boolean).join(" · "),
      codeVersion: first(prov.code_version),
      datasetVersion: first(prov.dataset_version),
      sourceExperiment: experimentId,
      facts: [
        { label: "Verdict", value: verdict ?? "—", mono: true },
        ...(str(prov.numbers_policy) ? [{ label: "Numbers", value: prov.numbers_policy as string }] : []),
        ...(str(prov.source_sha256) ? [{ label: "Source sha256", value: prov.source_sha256 as string, mono: true }] : []),
      ],
    });
    const KIND_LABEL: Record<string, string> = { OBSERVED_EVIDENCE: "Observed evidence", INFERENCE: "Scientific inference" };
    return {
      artifact: r,
      experimentId,
      verdict: statusOf(verdict),
      rationale: first(d.status_rationale, d.summary),
      evidence: arr(d.evidence_summary)
        .map(obj)
        .filter((e) => str(e.statement))
        .map((e) => {
          const kind = String(e.kind ?? "EVIDENCE");
          return { kind, label: KIND_LABEL[kind] ?? kind.replace(/_/g, " ").toLowerCase(), statement: String(e.statement), source: str(e.source) };
        }),
      uncertainties: [...texts(d.uncertainties), ...texts(d.uncertainty), ...texts(d.diagnostics_review)],
      limitations: texts(d.limitations),
      unsupported: [...texts(d.unsupported_claims), ...texts(d.unsupported_interpretations)],
      openQuestions: [...texts(d.untested_questions), ...texts(d.open_questions)].map(stripKind),
      pointEstimateObservations: texts(d.point_estimate_observations),
      formalInference: texts(d.formal_inference),
      agent,
      model,
    };
  };
  const critiqueRaws = byKind("critique");
  const critiques = critiqueRaws.map(critiqueView);
  critiques.forEach((c) => {
    const target = views.find((v) => v.id === c.experimentId);
    link(c.artifact, target?.exp.result ?? target?.exp.spec);
  });
  const critiquesFor = (id: string) =>
    critiques.filter((c) => c.experimentId === id).sort((a, b) => byTime(b.artifact.createdAt, a.artifact.createdAt));

  // --- Reviews (human)
  const reviewView = (a: RawArtifact): ReviewView => {
    const d = obj(a.data);
    const type = first(d.review_type) ?? "REVIEW";
    if (!str(d.review_type) || !str(d.decision)) issues.push({ level: "error", message: `${a.path} lacks review_type or decision`, path: a.path });
    const id = first(d.review_id) ?? stem(a.path);
    const approvedExp = obj(d.approved_experiment);
    const r = ref(a, "REVIEW", "Human review", { id, full: null }, {
      createdAt: first(d.recorded_at),
      producer: first(d.reviewer) ?? "human reviewer",
      facts: [
        { label: "Type", value: type, mono: true },
        { label: "Decision", value: first(d.decision) ?? "—", mono: true },
        ...(str(d.recorded_by) ? [{ label: "Recorded by", value: d.recorded_by as string }] : []),
      ],
    });
    return {
      artifact: r,
      id,
      type,
      decision: status(d.decision, "—"),
      scope: str(d.scope),
      constraints: texts(d.constraints),
      notEndorsed: arr(d.not_endorsed)
        .map(obj)
        .filter((n) => str(n.text))
        .map((n) => ({ text: String(n.text), reason: str(n.reason) })),
      approves: [
        ...arr(d.approved_hypotheses).map((h) => str(obj(h).hypothesis_id)),
        str(d.approved_decision_id),
      ].filter((x): x is string => Boolean(x)),
      authorizes: [str(approvedExp.experiment_id_to_assign)].filter((x): x is string => Boolean(x)),
      approvedHypotheses: arr(d.approved_hypotheses)
        .map(obj)
        .map((h) => ({ id: String(h.hypothesis_id), question: str(h.question), expectedDirection: str(h.expected_direction_as_hypothesis) })),
      approvedExperiment: Object.keys(approvedExp).length
        ? { experimentId: str(approvedExp.experiment_id_to_assign), model: str(approvedExp.model), engine: str(approvedExp.engine) }
        : null,
      reviewer: str(d.reviewer),
      recordedBy: str(d.recorded_by),
      recordedAt: str(d.recorded_at),
    };
  };
  const reviews = byKind("review")
    .map(reviewView)
    .sort((a, b) => byTime(a.recordedAt, b.recordedAt));

  // --- Hypotheses (agent)
  const hypothesisView = (a: RawArtifact): HypothesisView => {
    const d = obj(a.data);
    const prov = obj(d.provenance);
    const mot = obj(d.motivation);
    const id = first(d.hypothesis_id, d.id) ?? stem(a.path);
    const r = ref(a, "HYPOTHESIS", "Hypothesis", displayId("HYP", id, a.path), {
      createdAt: first(prov.timestamp, prov.created_at, d.created_at),
      producer: [first(prov.agent, d.generated_by) ?? "hypothesis_agent", first(prov.model)].filter(Boolean).join(" · "),
      codeVersion: first(prov.code_version),
      datasetVersion: first(prov.dataset_version),
      sourceExperiment: arr(d.source_experiment_ids).map(String).join(", ") || null,
      facts: [
        { label: "Status", value: first(d.current_evidence_status, d.status) ?? "—", mono: true },
        { label: "Kind", value: first(d.kind) ?? "—", mono: true },
      ],
    });
    return {
      artifact: r,
      id,
      question: first(d.scientific_question, d.question),
      claim: first(d.falsifiable_claim, d.statement, d.claim),
      observed: texts(mot.observed_evidence),
      inference: texts(mot.scientific_inference),
      unresolved: texts(mot.unresolved_uncertainty),
      expectedDirection: first(d.expected_direction),
      supportIf: first(d.supporting_observation),
      contradictIf: first(d.contradicting_observation),
      requiredVariables: arr(d.required_variables).map(String),
      status: status(first(d.current_evidence_status, d.status), "UNTESTED"),
      assessedLater: null,
      approvedIn: [],
      limitations: texts(d.limitations),
    };
  };
  const hypotheses = byKind("hypothesis")
    .map(hypothesisView)
    .sort((a, b) => a.id.localeCompare(b.id));
  const hypothesisById = new Map(hypotheses.map((h) => [h.id, h]));
  hypotheses.forEach((h) => {
    const d = obj(raw.find((x) => x.path === h.artifact.key)?.data);
    arr(d.source_critique_ids).forEach((cid) => link(h.artifact, critiques.find((c) => c.artifact.id === String(cid))?.artifact));
  });

  // --- Proposals
  const decisionRaws = byKind("decision");
  decisionRaws.forEach((a) => {
    if (!str(obj(a.data).decision_status)) issues.push({ level: "error", message: `${a.path} has no decision_status`, path: a.path });
  });
  const latestDecisionRaw = [...decisionRaws].sort((a, b) =>
    byTime(str(obj(obj(a.data).provenance).created_at), str(obj(obj(b.data).provenance).created_at)),
  ).at(-1);
  const latestExecutability = obj(obj(obj(latestDecisionRaw?.data).provenance).proposal_executability);
  const latestDecisionId = first(obj(latestDecisionRaw?.data).decision_id);

  const proposalView = (a: RawArtifact): ProposalView => {
    const d = obj(a.data);
    const prov = obj(d.provenance);
    const id = first(d.proposal_id, d.candidate_id, d.id) ?? stem(a.path);
    const role = statusOf(d.analysis_role);
    const feas = obj(d.feasibility);
    const gain = obj(d.expected_information_gain);
    const exec = obj(latestExecutability[id]);
    const r = ref(a, "PROPOSAL", "Candidate experiment", displayId("PROP", id, a.path), {
      createdAt: first(prov.timestamp, prov.created_at),
      producer: [first(prov.agent) ?? "experiment_planner", first(prov.model)].filter(Boolean).join(" · "),
      codeVersion: first(prov.code_version),
      datasetVersion: arr(prov.dataset_version).map(String).join(", ") || first(prov.dataset_version),
      sourceExperiment: arr(prov.experiment_ids).map(String).join(", ") || null,
      facts: [
        { label: "Analysis role", value: first(d.analysis_role) ?? "—", mono: true },
        { label: "Feasibility at planning", value: first(feas.status) ?? "—", mono: true },
      ],
    });
    return {
      artifact: r,
      id,
      hypothesisIds: arr(d.hypothesis_ids).map(String),
      question: first(d.scientific_question, d.question, d.title),
      test: first(d.experimental_test),
      estimand: first(d.comparison_or_estimand),
      role,
      formal: /FORMAL/i.test(first(d.analysis_role) ?? ""),
      infoGain: str(gain.level) ? { level: String(gain.level), reason: str(gain.reason) } : null,
      scientificValue: str(d.scientific_value),
      feasibilityAtPlanning: statusOf(feas.status),
      feasibilityReason: str(feas.reason),
      requiredCapabilities: arr(d.required_engine_capabilities).map(String),
      current:
        typeof exec.currently_executable === "boolean" && latestDecisionId
          ? { executable: exec.currently_executable, missing: arr(exec.missing_capabilities).map(String), asOf: latestDecisionId }
          : null,
      limitations: texts(d.limitations),
      ranAs: null,
    };
  };
  const proposals = byKind("candidate")
    .map(proposalView)
    .sort((a, b) => a.id.localeCompare(b.id));
  const proposalById = new Map(proposals.map((p) => [p.id, p]));
  proposals.forEach((p) => p.hypothesisIds.forEach((h) => link(p.artifact, hypothesisById.get(h)?.artifact)));

  // --- Decisions, in the order the Director made them
  const decisionView = (a: RawArtifact): DecisionView => {
    const d = obj(a.data);
    const prov = obj(d.provenance);
    const id = first(d.decision_id, d.id) ?? stem(a.path);
    const cap = obj(d.capability_check);
    const r = ref(a, "DECISION", "Director decision", displayId("DEC", id, a.path), {
      createdAt: first(prov.created_at, d.created_at),
      producer: [first(prov.agent, d.decided_by) ?? "discovery_director", first(prov.model)].filter(Boolean).join(" · "),
      codeVersion: first(prov.code_version),
      facts: [
        { label: "Status", value: first(d.decision_status) ?? "—", mono: true },
        { label: "Preferred", value: first(d.preferred_proposal_id) ?? "—", mono: true },
        { label: "Best executable", value: first(d.best_executable_proposal_id) ?? "—", mono: true },
        ...(str(prov.policy) ? [{ label: "Policy", value: prov.policy as string }] : []),
      ],
    });
    const pick = (pid: string | null) => (pid ? { id: pid, key: proposalById.get(pid)?.artifact.key ?? null } : null);
    return {
      artifact: r,
      id,
      status: status(d.decision_status, "—"),
      createdAt: first(prov.created_at, d.created_at),
      codeVersion: first(prov.code_version),
      model: first(prov.model),
      preferred: pick(first(d.preferred_proposal_id)),
      bestExecutable: pick(first(d.best_executable_proposal_id)),
      rationale: str(d.scientific_rationale),
      expectedLearning: str(d.expected_learning),
      alternatives: arr(d.alternatives)
        .map(obj)
        .filter((x) => str(x.proposal_id))
        .map((x) => ({ id: String(x.proposal_id), key: proposalById.get(String(x.proposal_id))?.artifact.key ?? null, reason: str(x.reason_not_selected) ?? "" })),
      executable: typeof cap.currently_executable === "boolean" ? cap.currently_executable : null,
      missing: arr(cap.missing_capabilities).map(String),
      uncertainties: texts(d.uncertainties),
      nextAction: str(d.next_action),
      approvedBy: [],
    };
  };
  const decisions = decisionRaws.map(decisionView).sort((a, b) => byTime(a.createdAt, b.createdAt) || a.id.localeCompare(b.id));
  const decisionById = new Map(decisions.map((d) => [d.id, d]));
  decisions.forEach((d) => {
    link(d.artifact, d.preferred?.key ? artifacts[d.preferred.key] : null);
    link(d.artifact, d.bestExecutable?.key ? artifacts[d.bestExecutable.key] : null);
    const raw = obj(decisionRaws.find((x) => x.path === d.artifact.key)?.data);
    arr(raw.based_on_ids).forEach((bid) => {
      const c = critiques.find((x) => x.artifact.id === String(bid));
      link(d.artifact, c?.artifact);
    });
  });

  // Reviews → what they approve
  reviews.forEach((rv) => {
    rv.approves.forEach((target) => {
      const h = hypothesisById.get(target);
      if (h) {
        h.approvedIn.push(rv.artifact.key);
        link(rv.artifact, h.artifact);
      }
      const dec = decisionById.get(target);
      if (dec) {
        dec.approvedBy.push(rv.artifact.key);
        link(rv.artifact, dec.artifact);
      }
    });
  });

  // --- Engine capability changes: compare the audits recorded by consecutive decisions.
  const capabilitiesRaw = byKind("capabilities")[0] ?? null;
  const capabilitiesRef = capabilitiesRaw
    ? ref(capabilitiesRaw, "CAPABILITY", "Engine capabilities", { id: "engine capabilities", full: null }, {
        producer: "src/experiments/capabilities.py (exported, validated against the schema)",
        facts: [{ label: "Methods", value: arr(obj(capabilitiesRaw.data).methods).join(", ") || "—", mono: true }],
      })
    : null;
  const audit = (dec: DecisionView) => obj(obj(obj(decisionRaws.find((x) => x.path === dec.artifact.key)?.data).provenance).engine_capability_audit);
  const capabilityChanges: CapabilityChangeView[] = [];
  for (let i = 1; i < decisions.length; i++) {
    const before = audit(decisions[i - 1]);
    const after = audit(decisions[i]);
    const sb = obj(before.supported);
    const sa = obj(after.supported);
    const names = [...new Set([...Object.keys(sb), ...Object.keys(sa)])];
    const gained = names.filter((n) => sb[n] === false && sa[n] === true);
    const lost = names.filter((n) => sb[n] === true && sa[n] === false);
    if (!gained.length && !lost.length) continue;
    const engineReview = reviews.find((rv) => /CAPABILITY|ENGINE/i.test(rv.type));
    capabilityChanges.push({
      from: { id: decisions[i - 1].id, key: decisions[i - 1].artifact.key },
      to: { id: decisions[i].id, key: decisions[i].artifact.key },
      gained,
      lost,
      schemaBefore: str(before.schema_sha256),
      schemaAfter: str(after.schema_sha256),
      capabilitiesKey: capabilitiesRef?.key ?? null,
      supported: Object.entries(obj(obj(capabilitiesRaw?.data).supported)).map(([name, v]) => ({ name, supported: v === true })),
      humanReview: engineReview?.artifact.key ?? null,
    });
    link(capabilitiesRef, decisions[i].artifact);
  }

  // --- Follow-up experiments and their critiques
  const followUps: FollowUpView[] = views
    .filter((v) => v !== baselineEntry)
    .map((v) => {
      const pv = v.provenance ? obj(v.provenance.data) : {};
      const decisionKey = decisionById.get(first(pv.decision_id) ?? "")?.artifact.key ?? null;
      const proposal = proposalById.get(first(pv.proposal_id) ?? "") ?? null;
      if (proposal) {
        proposal.ranAs = v.id;
        link(proposal.artifact, v.exp.spec);
      }
      const authorizedBy = reviews.filter((rv) => rv.authorizes.includes(v.id) || rv.id === first(pv.decision_approval_id)).map((rv) => rv.artifact.key);
      authorizedBy.forEach((k) => link(artifacts[k], v.exp.spec));
      if (decisionKey) link(artifacts[decisionKey], v.exp.spec);
      return {
        experiment: v.exp,
        evidence: v.evidence,
        interactions: v.interactions,
        critiques: critiquesFor(v.id),
        authorizedBy,
        decisionKey,
        proposalKey: proposal?.artifact.key ?? null,
      };
    });

  // --- Scientific updates: hypothesis status changes recorded by critiques of follow-up experiments.
  const updates: ScientificUpdateView[] = followUps.flatMap((f) =>
    f.critiques.flatMap((c) => {
      const d = obj(critiqueRaws.find((x) => x.path === c.artifact.key)?.data);
      const su = obj(d.scientific_update);
      return arr(d.hypothesis_assessments)
        .map(obj)
        .filter((h) => str(h.new_status))
        .map((h) => {
          const hypothesisId = str(h.hypothesis_id);
          const hyp = hypothesisId ? hypothesisById.get(hypothesisId) : undefined;
          const next = status(h.new_status, "—");
          if (hyp) {
            hyp.assessedLater = { status: next, critiqueKey: c.artifact.key };
            link(hyp.artifact, c.artifact);
          }
          const protocolId = str(h.protocol_hypothesis_id);
          return {
            hypothesisId,
            hypothesisKey: hyp?.artifact.key ?? null,
            protocolId,
            title: protocolId ? (protocolTitles.get(protocolId) ?? null) : null,
            question: hyp?.question ?? null,
            previous: status(h.previous_status, "—"),
            next,
            reason: str(h.reason),
            statusSource: str(h.status_source),
            explainer: UPDATE_EXPLAINER[next.code.toUpperCase()] ?? null,
            experimentId: f.experiment.experimentId,
            experimentKey: f.experiment.result?.key ?? f.experiment.spec.key,
            critiqueKey: c.artifact.key,
            before: str(su.what_was_known_before),
            tested: str(su.what_was_tested),
            changed: str(su.what_changed),
            unresolved: str(su.what_remains_unresolved),
          };
        });
    }),
  );

  // --- Protocol hypotheses H1–H4 with their latest status: critique assessment > engine assessment > initial state.
  const protocolHypotheses: ProtocolHypothesisView[] = arr(s.hypotheses)
    .map(obj)
    .filter((h) => str(h.code))
    .map((h) => {
      const code = String(h.code);
      let st = status(String(h.status ?? "").toUpperCase().replace(/^TESTED_IN_.*/, "TESTED"), "UNTESTED");
      let source: string | null = null;
      let assessment: string | null = null;
      views.forEach((v) => {
        const a = v.evidence?.assessments.find((x) => x.id === code);
        if (a) {
          st = a.status;
          source = v.id;
          assessment = a.assessment;
        }
      });
      updates
        .filter((u) => u.protocolId === code)
        .forEach((u) => {
          st = u.next;
          source = artifacts[u.critiqueKey]?.id ?? null;
          assessment = u.reason ?? assessment;
        });
      return { code, title: protocolTitles.get(code) ?? null, claim: String(h.claim ?? ""), status: st, statusSource: source, assessment };
    });

  // --- Stages, derived by role (never by id). Seven stages; the grouped ones keep their parts as sections.
  const baseline = baselineEntry?.exp ?? null;
  const baselineEvidence = baselineEntry?.evidence ?? null;
  const baselineCritiques = baseline ? critiquesFor(baseline.experimentId) : [];
  const hypothesisReviews = reviews.filter((rv) => /HYPOTHESIS/i.test(rv.type));
  const approvalReviews = reviews.filter((rv) => /DECISION|APPROVAL/i.test(rv.type) && !/HYPOTHESIS/i.test(rv.type));
  const keys = (...ks: (string | null | undefined)[]) => ks.filter((k): k is string => Boolean(k));
  const NOT_YET = "Not generated yet";
  const part = (key: StagePart["key"], title: string, type: ArtifactType, artifactKeys: string[], awaiting: Awaiting): StagePart => ({
    key,
    title,
    type,
    recorded: artifactKeys.length > 0,
    artifactKeys,
    awaiting,
  });
  const stage = (number: number, key: Stage["key"], title: string, type: ArtifactType, awaiting: Awaiting, own: string[], parts: StagePart[] = []): Stage => {
    const artifactKeys = [...new Set([...own, ...parts.flatMap((p) => p.artifactKeys)])];
    return { key, number, title, type, recorded: artifactKeys.length > 0, artifactKeys, awaiting, parts };
  };

  const planningParts = [
    part("hypotheses", "Hypotheses", "HYPOTHESIS", hypotheses.map((h) => h.artifact.key), {
      state: NOT_YET,
      what: "hypotheses motivated by the critique",
      producer: "hypothesis_agent · save_hypothesis",
      path: `${discoveryDir}/hypotheses/`,
    }),
    part("review", "Human review", "REVIEW", hypothesisReviews.map((r) => r.artifact.key), {
      state: "Awaiting human review",
      what: "a human review of the hypotheses",
      producer: "human project lead",
      path: `${discoveryDir}/reviews/`,
    }),
    part("proposals", "Experiment planning", "PROPOSAL", proposals.map((p) => p.artifact.key), {
      state: NOT_YET,
      what: "competing candidate experiments",
      producer: "experiment_planner · save_proposal",
      path: `${discoveryDir}/candidates/`,
    }),
  ];
  // A capability section only when the first decision waited for one, or when the audits show a change.
  const capabilityRelevant = capabilityChanges.length > 0 || decisions[0]?.executable === false;
  const decisionParts = [
    part("decision", "Director decision", "DECISION", keys(decisions[0]?.artifact.key), {
      state: NOT_YET,
      what: "the Director's decision",
      producer: "discovery_director",
      path: `${discoveryDir}/decisions/`,
    }),
    ...(capabilityRelevant
      ? [
          part("capability", "Engine capability", "CAPABILITY", capabilityChanges.length ? keys(capabilityChanges[0].capabilitiesKey) : [], {
            state: NOT_YET,
            what: "the engine capability the decision is waiting for",
            producer: "engine extension (code change) · recorded in the decision audits",
            path: "metadata/experiment_engine_capabilities.json",
          }),
        ]
      : []),
    ...(decisions.length > 1
      ? [
          part("history", "Decision history", "DECISION", decisions.slice(1).map((d) => d.artifact.key), {
            state: NOT_YET,
            what: "the Director's reassessment",
            producer: "discovery_director",
            path: `${discoveryDir}/decisions/`,
          }),
        ]
      : []),
    part("approval", "Human approval", "REVIEW", approvalReviews.map((r) => r.artifact.key), {
      state: "Awaiting human review",
      what: "a human approval of the decision",
      producer: "human project lead",
      path: `${discoveryDir}/reviews/`,
    }),
  ];
  const followUpParts = [
    part("experiment", "Formal test", "EXPERIMENT", followUps.flatMap((f) => keys(f.experiment.result?.key ?? f.experiment.spec.key)), {
      state: "Experiment not executed",
      what: "the approved experiment's result",
      producer: "experiment_runner · deterministic engine",
      path: "reports/experiments/EXP-NNN/",
    }),
    part("critique", "Scientific critic", "UNCERTAINTY", followUps.flatMap((f) => f.critiques.map((c) => c.artifact.key)), {
      state: NOT_YET,
      what: "a critique of the new result",
      producer: "scientific_critic",
      path: `${discoveryDir}/critiques/`,
    }),
  ];
  const followUpId = followUps[0]?.experiment.experimentId ?? null;

  const stages: Stage[] = [
    stage(1, "question", "Research question", "QUESTION", { state: NOT_YET, what: "the research question", producer: "initial_state.json", path: "initial_state.json" }, keys(questionRef?.key, rsRef?.key)),
    stage(
      2,
      "baseline",
      baseline ? `${baseline.experimentId} evidence` : "Initial evidence",
      "EVIDENCE",
      { state: "Experiment not executed", what: "the first experiment's result", producer: "experiment_runner · deterministic engine", path: "reports/experiments/EXP-NNN/" },
      keys(baseline?.result?.key, baseline?.spec.key, baseline?.validation?.key),
    ),
    stage(
      3,
      "critique",
      "Scientific critic",
      "UNCERTAINTY",
      { state: NOT_YET, what: "a critique of the first result", producer: "scientific_critic", path: `${discoveryDir}/critiques/` },
      baselineCritiques.map((c) => c.artifact.key),
    ),
    stage(
      4,
      "planning",
      "Hypotheses and experiment planning",
      "HYPOTHESIS",
      { state: NOT_YET, what: "hypotheses and candidate experiments", producer: "hypothesis_agent · experiment_planner", path: `${discoveryDir}/` },
      [],
      planningParts,
    ),
    stage(
      5,
      "decision",
      "Discovery decision",
      "DECISION",
      { state: NOT_YET, what: "the Director's decision", producer: "discovery_director", path: `${discoveryDir}/decisions/` },
      [],
      decisionParts,
    ),
    stage(
      6,
      "followup",
      followUpId ?? "New experiment",
      "EXPERIMENT",
      { state: "Experiment not executed", what: "the approved experiment's result", producer: "experiment_runner · deterministic engine", path: "reports/experiments/EXP-NNN/" },
      [],
      followUpParts,
    ),
    stage(
      7,
      "update",
      "Updated scientific state",
      "UPDATE",
      { state: NOT_YET, what: "the updated hypothesis status", producer: "scientific_critic · hypothesis_assessments", path: `${discoveryDir}/critiques/` },
      [...new Set(updates.map((u) => u.critiqueKey))],
    ),
  ];

  return {
    schemaVersion: 1,
    question: {
      text: questionText,
      population: populationLines(s.population),
      datasetVersion: str(ds.version) ?? str(s.dataset_version),
      hypotheses: protocolHypotheses,
      artifactKey: questionRef?.key ?? null,
    },
    dataset: rsRaw
      ? { version: str(ds.version), populationN: num(ds.population_n), sha256: str(ds.dataset_sha256), approval: str(ds.approval_status) }
      : null,
    baseline,
    baselineEvidence,
    baselineCritiques,
    hypotheses,
    reviews,
    proposals,
    decisions,
    capabilityChanges,
    followUps,
    updates,
    stages,
    artifacts,
    sessions: [...new Set(raw.map((a) => a.session).filter((x): x is string => Boolean(x)))].sort(),
    researchState: rsRef
      ? {
          key: rsRef.key,
          valid: typeof rsValidation.valid === "boolean" ? rsValidation.valid : null,
          note: str(obj(rs._generated).note),
          numbersPolicy: str(obj(rs.provenance).numbers_policy),
        }
      : null,
    issues,
  };
}
