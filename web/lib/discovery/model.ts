// Turns raw artifacts into the nine-stage discovery view. Pure function: same artifacts, same view.
// Readers are tolerant on purpose: the critic, hypothesis, planner and Director artifacts come from different
// tools (local critic tools, Supabase-backed tools, future agents), so each field is looked up under the names
// those producers use. A value that is not in an artifact is shown as missing, never filled in.

import type {
  ArtifactRef,
  ArtifactType,
  AssessmentView,
  CandidateView,
  CritiqueView,
  DecisionView,
  Discovery,
  EstimateRow,
  EvidenceView,
  ExperimentView,
  Fact,
  FollowUp,
  HypothesisView,
  Interval,
  PairView,
  RawArtifact,
  SelectionView,
  Stage,
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

export function outcomeLabel(id: string): string {
  return OUTCOMES[id]?.label ?? id;
}

const str = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v.trim() : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const first = (...vs: unknown[]): string | null => {
  for (const v of vs) {
    const s = str(v);
    if (s) return s;
  }
  return null;
};

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
      if (!body) return [];
      const src = first(o.source, o.source_id, o.passage_id, o.doi, o.url, o.locator);
      return [src ? `${body} (${src})` : body];
    }
    return [];
  });
}

function stem(path: string): string {
  return path.split("/").pop()!.replace(/\.json$/, "");
}

function short(id: string): string {
  return UUID.test(id) ? id.slice(0, 8) : id;
}

/** Display id: the artifact's own readable id when it has one, else a kind prefix plus the short uuid. */
function displayId(prefix: string, ownId: string | null, path: string, code?: string | null): { id: string; full: string | null } {
  const raw = ownId ?? stem(path);
  if (!UUID.test(raw)) return { id: raw, full: null };
  return { id: [prefix, code, short(raw)].filter(Boolean).join(" · "), full: raw };
}

function interval(i: unknown): Interval | null {
  if (!i || typeof i !== "object") return null;
  const o = i as Record<string, unknown>;
  const lower = num(o.lower);
  const upper = num(o.upper);
  if (lower == null || upper == null) return null;
  return { lower, upper, level: num(o.confidence_level), adjustment: str(o.adjustment) };
}

function populationLines(p: unknown, n?: number | null): string[] {
  if (!p || typeof p !== "object") return [];
  const o = p as Record<string, unknown>;
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

function stableJson(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(stableJson).join(",")}]`;
  if (v && typeof v === "object") {
    return `{${Object.keys(v as object)
      .filter((k) => k !== "experiment_id")
      .sort()
      .map((k) => `${JSON.stringify(k)}:${stableJson((v as Record<string, unknown>)[k])}`)
      .join(",")}}`;
  }
  return JSON.stringify(v);
}

function ref(
  a: RawArtifact,
  type: ArtifactType,
  label: string,
  id: { id: string; full: string | null },
  extra: { createdAt?: string | null; producer?: string | null; facts?: Fact[] } = {},
): ArtifactRef {
  return {
    key: a.path,
    id: id.id,
    fullId: id.full,
    type,
    label,
    path: a.path,
    sha256: a.sha256,
    modifiedAt: a.modifiedAt,
    createdAt: extra.createdAt ?? null,
    session: a.session,
    producer: extra.producer ?? null,
    facts: extra.facts ?? [],
    links: [],
  };
}

function link(from: ArtifactRef | null | undefined, to: ArtifactRef | null | undefined) {
  if (!from || !to || from.key === to.key) return;
  if (!from.links.includes(to.key)) from.links.push(to.key);
  if (!to.links.includes(from.key)) to.links.push(from.key);
}

function sortKey(r: ArtifactRef): string {
  return r.createdAt ?? r.modifiedAt ?? r.path;
}

// --- Experiments and evidence ------------------------------------------------

function experimentView(spec: RawArtifact, result: RawArtifact | undefined, validation: RawArtifact | undefined): ExperimentView {
  const s = spec.data ?? {};
  const r = result?.data ?? null;
  const v = validation?.data ?? null;
  const id = str(s.experiment_id) ?? stem(spec.path.replace(/\/spec\.json$/, ""));
  const specRef = ref(spec, "EXPERIMENT", "Experiment spec", { id: `${id} spec`, full: null }, {
    producer: "ExperimentSpec (agents propose, engine validates)",
    facts: [
      { label: "Method", value: str(s.method) ?? "—", mono: true },
      { label: "Exposure", value: str(s.exposure) ?? "—", mono: true },
      { label: "Hypotheses", value: (s.hypothesis_ids ?? []).join(", ") || "—" },
    ],
  });
  const resultRef = result
    ? ref(result, "EVIDENCE", "Experiment result", { id: `${id} result`, full: null }, {
        producer: "Deterministic engine (src/experiments)",
        facts: [
          { label: "Status", value: str(r?.status) ?? "—", mono: true },
          { label: "Review", value: str(r?.review_status) ?? "—", mono: true },
          { label: "Ranking", value: str(r?.ranking?.status) ?? "—", mono: true },
          { label: "Sample", value: num(r?.sample_size) != null ? `n = ${r.sample_size.toLocaleString("en-US")}` : "—" },
        ],
      })
    : null;
  const validationRef = validation
    ? ref(validation, "EVIDENCE", "Reproducibility check", { id: `${id} validation`, full: null }, {
        producer: "scripts/run_experiment.py (two runs)",
        facts: [
          { label: "Status", value: str(v?.status) ?? "—", mono: true },
          { label: "Identical runs", value: v?.identical_spec_identical_result === true ? "yes" : v ? "no" : "—" },
          { label: "Dataset hash", value: v?.analytic_sha256_before && v?.analytic_sha256_before === v?.analytic_sha256_after ? "unchanged" : "—" },
        ],
      })
    : null;
  link(specRef, resultRef);
  link(resultRef, validationRef);
  return {
    experimentId: id,
    spec: specRef,
    result: resultRef,
    validation: validationRef,
    question: str(s.research_question),
    population: populationLines(s.population, num(r?.sample_size)),
    exposure: str(s.exposure) ? EXPOSURES[s.exposure] ?? s.exposure : null,
    outcomes: (s.outcomes ?? []).map(String),
    covariates: (s.covariates ?? []).map((c: string) => COVARIATES[c] ?? c),
    method: str(s.method) ? METHODS[s.method] ?? s.method : null,
    uncertainty: str(s.uncertainty) ? UNCERTAINTY[s.uncertainty] ?? s.uncertainty : null,
    hypothesisIds: (s.hypothesis_ids ?? []).map(String),
    status: str(r?.status),
    reviewStatus: str(r?.review_status),
    reproduced: v ? v.identical_spec_identical_result === true : null,
    datasetUnchanged: v ? Boolean(v.analytic_sha256_before) && v.analytic_sha256_before === v.analytic_sha256_after : null,
    sampleSize: num(r?.sample_size),
    datasetVersion: str(s.dataset_version) ?? str(r?.dataset_version),
  };
}

function evidenceView(exp: ExperimentView, result: RawArtifact): EvidenceView {
  const r = result.data ?? {};
  const adjusted = (r.estimates ?? []).filter(
    (e: Record<string, unknown>) => typeof e.model_id === "string" && (e.model_id as string).startsWith("adjusted:"),
  );
  const rows: EstimateRow[] = adjusted
    .map((e: Record<string, unknown>) => ({
      outcome: String(e.outcome),
      label: outcomeLabel(String(e.outcome)),
      coefficient: num(e.coefficient) ?? 0,
      standardError: num(e.standard_error),
      ci: interval(e.interval),
      simultaneous: interval(e.simultaneous_outcome_interval),
      n: num(e.n),
    }))
    .sort((a: EstimateRow, b: EstimateRow) => a.coefficient - b.coefficient);
  const strongest = rows.length && rows[0].coefficient < 0 ? rows[0] : null;

  const sentences: string[] = [];
  if (strongest) {
    sentences.push(`${strongest.label} had the strongest negative point estimate.`);
    const exposure = adjusted[0]?.exposure;
    if (exposure === "commute_5h") {
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

  const status = str(r.ranking?.status);
  const count = rows.length;
  const countWord = NUMBER_WORDS[count] ?? String(count);
  const rankingSentence =
    status === "INCONCLUSIVE_RANKING"
      ? `The ranking across all ${countWord} outcomes remained inconclusive.`
      : status === "DISTINGUISHABLE_RANKING"
        ? `Every pairwise difference in the ordering of the ${countWord} outcomes excluded zero after Bonferroni adjustment.`
        : null;

  const comparisons = (r.ranking?.paired_comparisons ?? []) as Record<string, unknown>[];
  // Unresolved pairs first: they are the reason a ranking stays inconclusive.
  const pairItems: PairView[] = comparisons
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
  const resolved = pairItems.filter((p) => p.resolved).length;
  const assessments: AssessmentView[] = (["supported", "unsupported", "inconclusive"] as const).flatMap((bucket) =>
    (Array.isArray(r[`${bucket}_hypotheses`]) ? r[`${bucket}_hypotheses`] : [])
      .filter((h: unknown) => h && typeof h === "object" && str((h as Record<string, unknown>).id))
      .map((h: Record<string, unknown>) => ({
        id: String(h.id),
        assessment: str(h.assessment) ?? bucket,
        evidence: str(h.evidence),
        bucket,
      })),
  );

  const first = adjusted[0] as Record<string, unknown> | undefined;
  return {
    experimentId: exp.experimentId,
    artifact: exp.result!,
    rows,
    strongestNegative: strongest,
    sentences,
    rankingStatus: status,
    rankingSentence,
    pairs: comparisons.length
      ? { resolved, total: comparisons.length, adjustment: interval(comparisons[0].interval)?.adjustment ?? null, items: pairItems }
      : null,
    assessments,
    nextDirections: (Array.isArray(r.candidate_next_experiments) ? r.candidate_next_experiments : [])
      .map((c: Record<string, unknown>) => str(c?.question))
      .filter((q: string | null): q is string => Boolean(q)),
    units: str(first?.units),
    sampleSize: num(r.sample_size),
    covariates: exp.covariates,
    covarianceMethod: str(first?.covariance_method),
    sensitivity: (r.sensitivity_results ?? []).map((s: Record<string, unknown>) => ({
      name: String(s.name),
      nAfter: num(s.n_after),
      nExcluded: num(s.n_excluded),
      rankingStatus: str(s.ranking_status),
    })),
    qualityFlags: (r.quality_flags ?? []).map(String),
  };
}

// --- Agent artifacts ---------------------------------------------------------

function critiqueView(a: RawArtifact): CritiqueView {
  const d = a.data ?? {};
  const prov = d.provenance ?? {};
  const verdict = first(d.scientific_status, d.verdict, d.status);
  const experimentId = first(d.experiment_id, prov.source_experiment_id);
  const agent = first(prov.agent, d.agent, d.decided_by) ?? "scientific_critic";
  const model = first(prov.declared_executor?.model, d.model);
  const id = displayId("CRIT", first(d.critique_id, d.id), a.path, experimentId);
  return {
    artifact: ref(a, "UNCERTAINTY", "Scientific critique", id, {
      createdAt: first(prov.created_at, d.created_at),
      producer: [agent, model].filter(Boolean).join(" · "),
      facts: [
        { label: "Verdict", value: verdict ?? "—", mono: true },
        { label: "Experiment", value: experimentId ?? "—", mono: true },
        ...(str(d.evidence_strength) ? [{ label: "Evidence strength", value: d.evidence_strength }] : []),
        ...(str(prov.numbers_policy) ? [{ label: "Numbers", value: prov.numbers_policy }] : []),
        ...(str(prov.source_sha256) ? [{ label: "Source sha256", value: prov.source_sha256, mono: true }] : []),
      ],
    }),
    experimentId,
    verdict,
    rationale: first(d.status_rationale, d.summary),
    evidence: (Array.isArray(d.evidence_summary) ? d.evidence_summary : [])
      .filter((e: unknown) => e && typeof e === "object")
      .map((e: Record<string, unknown>) => ({
        kind: String(e.kind ?? "EVIDENCE"),
        statement: String(e.statement ?? ""),
        source: str(e.source),
      })),
    uncertainties: [...texts(d.uncertainties), ...texts(d.uncertainty), ...texts(d.diagnostics_review)],
    limitations: texts(d.limitations),
    unsupported: [...texts(d.unsupported_claims), ...texts(d.unsupported_interpretations)],
    openQuestions: [...texts(d.untested_questions), ...texts(d.open_questions)].map((q) =>
      q.replace(/^UNTESTED_QUESTION:\s*/i, ""),
    ),
    ruleApplied: str(d.rule_applied),
    recommendedDirection: str(d.recommended_direction),
    agent,
    model,
  };
}

function hypothesisView(a: RawArtifact): HypothesisView {
  const d = a.data ?? {};
  const code = first(d.code, d.hypothesis_code);
  const id = displayId("HYP", first(d.hypothesis_id, d.id), a.path, code);
  const generatedBy = first(d.generated_by, d.agent, d.provenance?.agent);
  return {
    artifact: ref(a, "HYPOTHESIS", "Hypothesis", id, {
      createdAt: first(d.created_at, d.provenance?.created_at),
      producer: generatedBy,
      facts: [
        { label: "Code", value: code ?? "—", mono: true },
        { label: "Status", value: first(d.status) ?? "proposed" },
      ],
    }),
    code,
    statement: first(d.statement, d.claim, d.hypothesis, d.new_hypothesis) ?? "(no statement in artifact)",
    generatedBy,
    status: first(d.status),
    existingEvidence: texts(d.existing_evidence ?? d.evidence),
    inference: texts(d.inference),
    newHypothesis: first(d.new_hypothesis),
    prediction: first(d.prediction, d.falsification, d.falsifiable_prediction, d.test),
    motivatedBy: first(d.motivated_by_critique_id, d.critique_id, d.motivated_by),
    motivatedByLabel: null,
  };
}

function candidateView(a: RawArtifact): CandidateView {
  const d = a.data ?? {};
  const label = first(d.label) ?? stem(a.path);
  const id = displayId("CAND", first(d.proposal_id, d.candidate_id, d.id), a.path, label);
  const check = d.engine_check && typeof d.engine_check === "object" ? d.engine_check : null;
  const feasible = typeof d.contract_feasible === "boolean" ? d.contract_feasible : null;
  return {
    artifact: ref(a, "EXPERIMENT", "Candidate experiment", id, {
      createdAt: first(d.created_at),
      producer: first(d.proposed_by, d.agent) ?? "experiment_planner",
      facts: [
        { label: "Label", value: label },
        { label: "Fits engine contract", value: feasible == null ? "—" : feasible ? "yes" : "no — needs contract revision" },
        ...(check ? [{ label: "Engine dry run", value: check.valid ? `valid${num(check.n) != null ? ` · n = ${check.n}` : ""}` : "invalid" }] : []),
      ],
    }),
    proposalId: first(d.proposal_id, d.candidate_id, d.id),
    label,
    title: first(d.title, d.question) ?? label,
    question: first(d.question),
    hypothesisCodes: (Array.isArray(d.hypothesis_codes) ? d.hypothesis_codes : []).map(String),
    expectedGain: first(d.expected_information_gain, d.learning_value),
    couldChange: first(d.could_change_interpretation, d.decision_relevance),
    feasible,
    feasibility: first(d.feasibility),
    cost: first(d.cost),
    limitations: texts(d.limitations),
    engineCheck: check ? { valid: Boolean(check.valid), n: num(check.n) ?? num(check.sample_size) } : null,
    selected: d.selected === true,
    experimentId: null,
  };
}

function isSelection(d: Record<string, unknown>): boolean {
  return d.type === "candidate_selection" || (d.type == null && d.proposal_id != null && d.experiment_run_id == null);
}

function selectionView(a: RawArtifact): SelectionView {
  const d = a.data ?? {};
  const id = displayId("DEC", first(d.decision_id, d.id), a.path);
  return {
    artifact: ref(a, "DECISION", "Director's selection", id, {
      createdAt: first(d.created_at),
      producer: first(d.decided_by) ?? "discovery_director",
      facts: [
        { label: "Selected", value: first(d.label) ?? "—" },
        { label: "Rule applied", value: first(d.rule_applied) ?? "—", mono: true },
      ],
    }),
    proposalId: first(d.proposal_id),
    candidateKey: null,
    label: first(d.label),
    title: null,
    rationale: first(d.rationale),
    alternatives: first(d.alternatives_considered),
    ruleApplied: first(d.rule_applied),
    basedOnRun: first(d.based_on_run_id),
  };
}

function decisionView(a: RawArtifact): DecisionView {
  const d = a.data ?? {};
  const id = displayId("DEC", first(d.decision_id, d.id), a.path);
  return {
    artifact: ref(a, "DECISION", "Updated decision", id, {
      createdAt: first(d.created_at),
      producer: first(d.decided_by) ?? "discovery_director",
      facts: [
        { label: "Rule applied", value: first(d.rule_applied) ?? "—", mono: true },
        { label: "Hypothesis status", value: first(d.hypothesis_status) ?? "—" },
      ],
    }),
    interpretation: first(d.interpretation, d.summary) ?? "(no interpretation in artifact)",
    ruleApplied: first(d.rule_applied),
    nextTest: first(d.next_test, d.next_action?.description, d.next_action?.type),
    rationale: first(d.rationale),
    uncertainty: first(d.uncertainty),
    limitations: first(d.limitations),
    hypothesisStatus: first(d.hypothesis_status),
    decidedBy: first(d.decided_by),
    runId: first(d.experiment_run_id),
  };
}

// --- Assembly ----------------------------------------------------------------

export function buildDiscovery(raw: RawArtifact[]): Discovery {
  const artifacts: Record<string, ArtifactRef> = {};
  const keep = (r: ArtifactRef | null | undefined) => {
    if (r) artifacts[r.key] = r;
    return r;
  };
  const byKind = (k: RawArtifact["kind"]) => raw.filter((a) => a.kind === k);

  // Question
  const state = byKind("initial_state")[0];
  const s = state?.data ?? {};
  let questionKey: string | null = null;
  if (state) {
    const q = keep(
      ref(state, "QUESTION", "Research question", { id: "initial_state", full: null }, {
        producer: "Shared Research State (Omnigent session input)",
        facts: [{ label: "Dataset", value: str(s.dataset_version) ?? "—", mono: true }],
      }),
    )!;
    questionKey = q.key;
  }

  // Experiments
  const results = new Map(byKind("result").map((a) => [a.path.split("/")[2], a]));
  const validations = new Map(byKind("validation").map((a) => [a.path.split("/")[2], a]));
  const experiments = byKind("spec")
    .map((spec) => {
      const id = str(spec.data?.experiment_id) ?? spec.path.split("/").at(-2)!;
      return { spec, result: results.get(id), validation: validations.get(id), id };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
  const views = experiments.map(({ spec, result, validation }) => {
    const exp = experimentView(spec, result, validation);
    keep(exp.spec);
    keep(exp.result);
    keep(exp.validation);
    if (questionKey) link(artifacts[questionKey], exp.spec);
    const evidence = result && exp.result ? evidenceView(exp, result) : null;
    return { exp, evidence, raw: spec };
  });

  // Critiques
  const critiques = byKind("critique").map(critiqueView);
  critiques.forEach((c) => {
    keep(c.artifact);
    const target = views.find((v) => v.exp.experimentId === c.experimentId);
    link(c.artifact, target?.exp.result ?? target?.exp.spec);
  });
  const critiquesFor = (id: string) =>
    critiques.filter((c) => c.experimentId === id).sort((a, b) => sortKey(b.artifact).localeCompare(sortKey(a.artifact)));

  // Hypotheses (agent-generated)
  const hypotheses = byKind("hypothesis")
    .map(hypothesisView)
    .sort((a, b) => sortKey(a.artifact).localeCompare(sortKey(b.artifact)));
  hypotheses.forEach((h) => {
    keep(h.artifact);
    if (h.motivatedBy) {
      const c = critiques.find((c) => c.artifact.fullId === h.motivatedBy || c.artifact.id === h.motivatedBy);
      if (c) {
        h.motivatedByLabel = c.artifact.id;
        h.motivatedBy = c.artifact.key;
        link(h.artifact, c.artifact);
      } else {
        h.motivatedByLabel = short(h.motivatedBy);
        h.motivatedBy = null;
      }
    }
  });

  // Candidates
  const candidates = byKind("candidate").map((a) => ({ view: candidateView(a), spec: a.data?.spec, hyp: a.data?.hypothesis_id }));
  candidates.forEach(({ view, spec, hyp }) => {
    keep(view.artifact);
    const h = hypotheses.find((h) => h.artifact.fullId === hyp || h.artifact.id === hyp);
    link(view.artifact, h?.artifact);
    if (spec && typeof spec === "object") {
      const fingerprint = stableJson(spec);
      const match = views.find((v) => stableJson(v.raw.data) === fingerprint);
      if (match) {
        view.experimentId = match.exp.experimentId;
        link(view.artifact, match.exp.spec);
      }
    }
  });
  const candidateViews = candidates
    .map((c) => c.view)
    .sort((a, b) => a.label.localeCompare(b.label) || sortKey(a.artifact).localeCompare(sortKey(b.artifact)));

  // Decisions
  const decisionRaws = byKind("decision");
  const selections = decisionRaws.filter((a) => isSelection(a.data ?? {})).map(selectionView);
  selections.forEach((sel) => {
    keep(sel.artifact);
    const c = candidateViews.find((c) => c.proposalId && c.proposalId === sel.proposalId);
    if (c) {
      c.selected = true;
      sel.candidateKey = c.artifact.key;
      sel.title = c.title;
      sel.label = sel.label ?? c.label;
      link(sel.artifact, c.artifact);
    }
  });
  const decisions = decisionRaws
    .filter((a) => !isSelection(a.data ?? {}))
    .map(decisionView)
    .sort((a, b) => sortKey(a.artifact).localeCompare(sortKey(b.artifact)));
  decisions.forEach((d) => keep(d.artifact));

  // Baseline = the first experiment; follow-ups = every later one.
  const [baseline, ...rest] = views;
  const followUps: FollowUp[] = rest.map((v) => ({ experiment: v.exp, evidence: v.evidence, critiques: critiquesFor(v.exp.experimentId) }));
  followUps.forEach((f) => {
    const sel = selections.find((s) => candidateViews.find((c) => c.artifact.key === s.candidateKey)?.experimentId === f.experiment.experimentId);
    link(sel?.artifact, f.experiment.spec);
  });
  const baselineCritiques = baseline ? critiquesFor(baseline.exp.experimentId) : [];

  const session = "reports/discovery/<session>";
  const stage = (
    number: number,
    key: Stage["key"],
    title: string,
    type: ArtifactType,
    keys: (string | null | undefined)[],
    awaiting: Stage["awaiting"],
  ): Stage => {
    const artifactKeys = keys.filter((k): k is string => Boolean(k));
    return { key, number, title, type, recorded: artifactKeys.length > 0, artifactKeys, awaiting };
  };

  const stages: Stage[] = [
    stage(1, "question", "Research question", "QUESTION", [questionKey], {
      what: "the research question",
      producer: "initial_state.json",
      path: "initial_state.json",
    }),
    stage(2, "experiment", "First experiment", "EXPERIMENT", [baseline?.exp.spec.key, baseline?.exp.validation?.key], {
      what: "the first ExperimentSpec",
      producer: "experiment_runner · deterministic engine",
      path: "experiments/EXP-NNN/spec.json",
    }),
    stage(3, "evidence", "Evidence", "EVIDENCE", [baseline?.exp.result?.key], {
      what: "the engine's result",
      producer: "deterministic engine · scripts/run_experiment.py",
      path: "reports/experiments/EXP-NNN/result.json",
    }),
    stage(4, "critique", "Scientific critique", "UNCERTAINTY", baselineCritiques.map((c) => c.artifact.key), {
      what: "a critique of the first result",
      producer: "scientific_critic",
      path: `${session}/critiques/`,
    }),
    stage(5, "hypotheses", "New hypotheses", "HYPOTHESIS", hypotheses.map((h) => h.artifact.key), {
      what: "hypotheses motivated by the critique",
      producer: "hypothesis_agent · save_hypothesis",
      path: `${session}/hypotheses/`,
    }),
    stage(6, "candidates", "Candidate experiments", "EXPERIMENT", candidateViews.map((c) => c.artifact.key), {
      what: "two or more competing candidate experiments",
      producer: "experiment_planner · save_proposals",
      path: `${session}/candidates/`,
    }),
    stage(7, "selection", "Selected experiment", "DECISION", selections.map((s) => s.artifact.key), {
      what: "the Director's choice and its rationale",
      producer: "discovery_director · select_candidate",
      path: `${session}/decisions/`,
    }),
    stage(
      8,
      "new_evidence",
      "New evidence",
      "EVIDENCE",
      followUps.flatMap((f) => [f.experiment.result?.key ?? f.experiment.spec.key, ...f.critiques.map((c) => c.artifact.key)]),
      {
        what: "the selected experiment's result",
        producer: "experiment_runner · run_experiment (approval required)",
        path: "reports/experiments/EXP-NNN/",
      },
    ),
    stage(9, "decision", "Updated scientific decision", "DECISION", [...decisions].reverse().map((d) => d.artifact.key), {
      what: "the decision updated by the new result",
      producer: "discovery_director · record_decision (approval required)",
      path: `${session}/decisions/`,
    }),
  ];

  return {
    question: {
      text: str(s.research_question),
      population: populationLines(s.population),
      datasetVersion: str(s.dataset_version),
      hypotheses: (Array.isArray(s.hypotheses) ? s.hypotheses : []).map((h: Record<string, unknown>) => ({
        code: String(h.code ?? ""),
        claim: String(h.claim ?? ""),
        status: String(h.status ?? ""),
      })),
      artifactKey: questionKey,
    },
    baseline: baseline?.exp ?? null,
    baselineEvidence: baseline?.evidence ?? null,
    baselineCritiques,
    hypotheses,
    candidates: candidateViews,
    selections,
    followUps,
    decisions,
    stages,
    artifacts,
    sessions: [...new Set(raw.map((a) => a.session).filter((x): x is string => Boolean(x)))].sort(),
  };
}
