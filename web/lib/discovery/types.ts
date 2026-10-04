// DiscoveryRunViewModel: the normalized view of the discovery artifacts that every UI component reads.
// Everything here is read from files under reports/, experiments/ and metadata/ by lib/discovery/model.ts;
// nothing is computed by a model, no scientific value is typed in by hand, and components never see raw artifacts.

export type RawKind =
  | "initial_state"
  | "research_state"
  | "capabilities"
  | "spec"
  | "experiment_provenance"
  | "result"
  | "validation"
  | "critique"
  | "hypothesis"
  | "candidate"
  | "decision"
  | "review";

export interface RawArtifact {
  kind: RawKind;
  path: string;
  sha256: string;
  modifiedAt: string | null;
  session: string | null;
  // Artifact JSON as written by the engine or the agents (shapes vary by producer and version).
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
}

/** The visual roles a viewer must tell apart. Each carries a word and an icon, never color alone. */
export type ArtifactType =
  | "QUESTION"
  | "EVIDENCE"
  | "UNCERTAINTY"
  | "HYPOTHESIS"
  | "REVIEW"
  | "PROPOSAL"
  | "DECISION"
  | "CAPABILITY"
  | "EXPERIMENT"
  | "UPDATE";

/** A status exactly as an artifact writes it, plus the tone the adapter assigned to it. */
export type Tone = "good" | "warn" | "uncertain" | "neutral";
export interface StatusView {
  code: string; // exactly as the artifact writes it
  tone: Tone;
  label: string; // plain-language reading of the code, from the adapter's glossary
  meaning: string | null; // one sentence on what the code means for a researcher
}

export interface Fact {
  label: string;
  value: string;
  mono?: boolean;
}

export interface ArtifactRef {
  key: string; // repo path, unique
  id: string; // display id from the artifact: EXP-001 result, CRIT-EXP-001-001, HYP-005
  fullId: string | null; // full artifact id when the display id is shortened
  type: ArtifactType;
  label: string; // "Experiment result", "Scientific critique", …
  path: string;
  sha256: string;
  expectedSha256: string | null; // what research_state.json recorded for this file, when it lists it
  modifiedAt: string | null;
  createdAt: string | null;
  session: string | null;
  producer: string | null;
  codeVersion: string | null;
  datasetVersion: string | null;
  sourceExperiment: string | null;
  facts: Fact[];
  links: string[]; // keys of linked artifacts
  handoff: unknown; // an excerpt of the artifact's own JSON (long lists and text shortened, local paths removed)
}

export interface Interval {
  lower: number;
  upper: number;
  level: number | null;
  adjustment: string | null;
}

export interface EstimateRow {
  outcome: string;
  label: string;
  coefficient: number;
  standardError: number | null;
  ci: Interval | null;
  simultaneous: Interval | null;
  n: number | null;
}

/** One Bonferroni-adjusted paired difference between two outcomes, as written in result.json. */
export interface PairView {
  a: string; // outcome label
  b: string;
  difference: number;
  interval: Interval | null;
  resolved: boolean; // the interval excludes zero
}

/** The engine's own assessment of a protocol hypothesis (result.json supported/unsupported/inconclusive lists). */
export interface AssessmentView {
  id: string;
  assessment: string;
  evidence: string | null;
  status: StatusView; // SUPPORTED / UNSUPPORTED / INCONCLUSIVE, the list the engine put it in
}

export interface EvidenceView {
  experimentId: string;
  artifact: ArtifactRef;
  rows: EstimateRow[]; // adjusted primary models, ordered by point estimate
  strongestNegative: EstimateRow | null; // only when two or more outcomes can be compared
  sentences: string[]; // scientifically safe statements derived from the rows and the ranking status
  rankingStatus: StatusView | null;
  rankingSentence: string | null;
  rankingRule: string | null;
  pairs: { resolved: number; total: number; adjustment: string | null; items: PairView[] } | null;
  assessments: AssessmentView[];
  nextDirections: string[]; // result.json candidate_next_experiments[].question, verbatim; never a selection
  units: string | null;
  sampleSize: number | null;
  covariates: string[];
  covarianceMethod: string | null;
  sensitivity: { name: string; nAfter: number | null; nExcluded: number | null; rankingStatus: string | null }[];
  qualityFlags: string[];
}

export interface ExperimentView {
  experimentId: string;
  spec: ArtifactRef;
  result: ArtifactRef | null;
  validation: ArtifactRef | null;
  question: string | null;
  population: string[];
  exposure: string | null;
  outcomes: string[];
  covariates: string[];
  method: string | null;
  uncertainty: string | null;
  hypothesisIds: string[];
  status: StatusView | null;
  reviewStatus: StatusView | null;
  reproduced: boolean | null;
  datasetUnchanged: boolean | null;
  sampleSize: number | null;
  datasetVersion: string | null;
  // The experiment for a reader outside the project, built from the spec, the decision that chose it and its result.
  plain: { title: string; what: string; why: string | null; finding: string | null };
}

export interface SlopeView {
  estimate: number;
  standardError: number | null;
  ci: Interval | null;
}

/** A binary-moderator interaction exactly as result.json reports it. */
export interface InteractionView {
  outcome: string;
  outcomeLabel: string;
  exposure: string;
  moderator: string;
  referenceLevel: string;
  comparisonLevel: string;
  coding: string | null;
  referenceSlope: SlopeView | null;
  comparisonSlope: SlopeView | null;
  interaction: SlopeView | null;
  status: StatusView | null;
  interpretation: string | null;
  units: string | null;
}

export interface CritiqueView {
  artifact: ArtifactRef;
  experimentId: string | null;
  verdict: StatusView | null;
  rationale: string | null;
  evidence: { kind: string; label: string; statement: string; source: string | null }[];
  uncertainties: string[];
  limitations: string[];
  unsupported: string[];
  openQuestions: string[];
  pointEstimateObservations: string[];
  formalInference: string[];
  agent: string | null;
  model: string | null;
  plain: string; // what this critique is and what it concluded, in plain words
}

/** H1–H4 as pre-registered, with the latest status the artifacts give them. */
export interface ProtocolHypothesisView {
  code: string;
  title: string | null;
  claim: string;
  status: StatusView;
  statusSource: string | null; // experiment or critique id that set the status
  assessment: string | null;
}

/** A hypothesis written by the Hypothesis Agent: to be tested, never a finding. */
export interface HypothesisView {
  artifact: ArtifactRef;
  id: string;
  question: string | null;
  claim: string | null;
  observed: string[];
  inference: string[];
  unresolved: string[];
  expectedDirection: string | null;
  supportIf: string | null;
  contradictIf: string | null;
  requiredVariables: string[];
  status: StatusView; // as the artifact recorded it when written
  assessedLater: { status: StatusView; critiqueKey: string } | null; // a later critique's assessment
  approvedIn: string[]; // review artifact keys
  limitations: string[];
}

export interface ReviewView {
  artifact: ArtifactRef;
  id: string;
  type: string;
  decision: StatusView;
  scope: string | null;
  constraints: string[];
  notEndorsed: { text: string; reason: string | null }[];
  approves: string[]; // artifact keys
  authorizes: string[]; // experiment ids the review authorizes
  approvedHypotheses: { id: string; question: string | null; expectedDirection: string | null }[];
  approvedExperiment: { experimentId: string | null; model: string | null; engine: string | null } | null;
  reviewer: string | null;
  recordedBy: string | null;
  recordedAt: string | null;
}

export interface ProposalView {
  artifact: ArtifactRef;
  id: string;
  hypothesisIds: string[];
  question: string | null;
  test: string | null;
  estimand: string | null;
  role: StatusView | null; // analysis_role: FORMAL_HETEROGENEITY_TEST / EXPLORATORY_SUBGROUP
  formal: boolean;
  infoGain: { level: string; reason: string | null } | null;
  scientificValue: string | null;
  feasibilityAtPlanning: StatusView | null;
  feasibilityReason: string | null;
  requiredCapabilities: string[];
  current: { executable: boolean; missing: string[]; asOf: string } | null; // from the latest decision's audit
  limitations: string[];
  ranAs: string | null; // experiment id
}

export interface DecisionView {
  artifact: ArtifactRef;
  id: string;
  status: StatusView;
  createdAt: string | null;
  codeVersion: string | null;
  model: string | null;
  preferred: { id: string; key: string | null } | null;
  bestExecutable: { id: string; key: string | null } | null;
  rationale: string | null;
  expectedLearning: string | null;
  alternatives: { id: string; key: string | null; reason: string }[];
  executable: boolean | null;
  missing: string[];
  uncertainties: string[];
  nextAction: string | null;
  approvedBy: string[]; // review keys
}

/** A change in engine capability, derived by comparing the audits two consecutive decisions recorded. */
export interface CapabilityChangeView {
  from: { id: string; key: string };
  to: { id: string; key: string };
  gained: string[];
  lost: string[];
  schemaBefore: string | null;
  schemaAfter: string | null;
  // False when both audits hash the same engine files (schema, method registry, capability export): only the audit changed.
  engineChanged: boolean;
  capabilitiesKey: string | null; // metadata/experiment_engine_capabilities.json
  supported: { name: string; supported: boolean }[];
  humanReview: string | null; // review key, when an artifact records one
}

export interface FollowUpView {
  experiment: ExperimentView;
  evidence: EvidenceView | null;
  interactions: InteractionView[];
  critiques: CritiqueView[];
  authorizedBy: string[]; // review keys
  decisionKey: string | null;
  proposalKey: string | null;
}

/** A hypothesis status change recorded by a critique: the closing moment of a discovery run. */
export interface ScientificUpdateView {
  hypothesisId: string | null;
  hypothesisKey: string | null;
  protocolId: string | null;
  title: string | null;
  question: string | null;
  previous: StatusView;
  next: StatusView;
  reason: string | null;
  statusSource: string | null;
  explainer: string | null;
  experimentId: string | null;
  experimentKey: string | null;
  critiqueKey: string;
  before: string | null;
  tested: string | null;
  changed: string | null;
  unresolved: string | null;
}

export type StageKey = "question" | "baseline" | "critique" | "planning" | "decision" | "followup" | "update";

/** A grouped stage's sections, in reading order; a part without artifacts renders as pending, never as filler. */
export type StagePartKey = "hypotheses" | "review" | "proposals" | "decision" | "capability" | "history" | "approval" | "experiment" | "critique";

export interface Awaiting {
  state: string; // "Not generated yet", "Awaiting human review", "Experiment not executed"
  what: string;
  producer: string;
  path: string;
}

export interface StagePart {
  key: StagePartKey;
  title: string;
  type: ArtifactType;
  recorded: boolean;
  artifactKeys: string[];
  awaiting: Awaiting;
}

export interface Stage {
  key: StageKey;
  number: number;
  title: string;
  shortTitle: string; // for the section navigation
  purpose: string; // the scientific question this stage answers
  agent: string; // who produced the stage, as the run's console names it
  working: string; // what that agent was doing, shown while the stage is being revealed
  checks: string[]; // the validations its tools run before saving, as listed in the console
  type: ArtifactType;
  recorded: boolean;
  artifactKeys: string[]; // primary artifact first
  awaiting: Awaiting;
  parts: StagePart[]; // empty for single-artifact stages
}

export interface DiscoveryIssue {
  level: "error" | "warning";
  message: string;
  path: string | null;
}

export interface DiscoveryRunViewModel {
  schemaVersion: 1;
  question: {
    text: string | null;
    population: string[];
    datasetVersion: string | null;
    hypotheses: ProtocolHypothesisView[];
    artifactKey: string | null;
  };
  dataset: { version: string | null; populationN: number | null; sha256: string | null; approval: string | null } | null;
  baseline: ExperimentView | null;
  baselineEvidence: EvidenceView | null;
  baselineCritiques: CritiqueView[];
  hypotheses: HypothesisView[];
  reviews: ReviewView[];
  proposals: ProposalView[];
  decisions: DecisionView[];
  capabilityChanges: CapabilityChangeView[];
  followUps: FollowUpView[];
  updates: ScientificUpdateView[];
  stages: Stage[];
  artifacts: Record<string, ArtifactRef>;
  sessions: string[];
  researchState: { key: string; valid: boolean | null; note: string | null; numbersPolicy: string | null } | null;
  issues: DiscoveryIssue[];
}

export type DiscoveryMode = "replay" | "live";

export interface DiscoveryPayload {
  run: DiscoveryRunViewModel;
  mode: DiscoveryMode;
  liveUnavailable: boolean; // live requested but the repo files are not reachable (e.g. on Vercel)
  source: string; // "committed artifacts @ ca6c7d7" or "reports/ on this machine"
  commit: string | null; // full commit of the REPLAY bundle; null in LIVE
  loadedAt: string;
}

/** The REPLAY bundle written by scripts/snapshot-discovery.mjs: a derived UI view, never a scientific source. */
export interface ReplayBundle {
  note: string;
  commit: string | null;
  sources: { kind: RawKind; path: string; sha256: string }[];
  run: DiscoveryRunViewModel;
}
