// Normalized view of the discovery artifacts. Everything here is read from files under reports/ and experiments/;
// nothing is computed by a model and no value is typed in by hand.

export type RawKind =
  | "initial_state"
  | "spec"
  | "result"
  | "validation"
  | "critique"
  | "hypothesis"
  | "candidate"
  | "decision";

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

/** The five visual roles a judge must tell apart, plus the neutral research question. */
export type ArtifactType = "QUESTION" | "EVIDENCE" | "HYPOTHESIS" | "EXPERIMENT" | "UNCERTAINTY" | "DECISION";

export interface Fact {
  label: string;
  value: string;
  mono?: boolean;
}

export interface ArtifactRef {
  key: string; // repo path, unique
  id: string; // display id: EXP-001, CRIT-EXP-001-001, H5 · 3f2a91c0
  fullId: string | null; // full artifact id when the display id is shortened
  type: ArtifactType;
  label: string; // "Experiment result", "Scientific critique", …
  path: string;
  sha256: string;
  modifiedAt: string | null;
  createdAt: string | null;
  session: string | null;
  producer: string | null;
  facts: Fact[];
  links: string[]; // keys of linked artifacts
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
  bucket: "supported" | "unsupported" | "inconclusive";
}

export interface EvidenceView {
  experimentId: string;
  artifact: ArtifactRef;
  rows: EstimateRow[]; // adjusted primary models, ordered by point estimate
  strongestNegative: EstimateRow | null;
  sentences: string[]; // scientifically safe statements derived from the rows and the ranking status
  rankingStatus: string | null;
  rankingSentence: string | null;
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
  status: string | null;
  reviewStatus: string | null;
  reproduced: boolean | null;
  datasetUnchanged: boolean | null;
  sampleSize: number | null;
  datasetVersion: string | null;
}

export interface CritiqueView {
  artifact: ArtifactRef;
  experimentId: string | null;
  verdict: string | null;
  rationale: string | null;
  evidence: { kind: string; statement: string; source: string | null }[];
  uncertainties: string[];
  limitations: string[];
  unsupported: string[];
  openQuestions: string[];
  ruleApplied: string | null;
  recommendedDirection: string | null;
  agent: string | null;
  model: string | null;
}

export interface HypothesisView {
  artifact: ArtifactRef;
  code: string | null;
  statement: string;
  generatedBy: string | null;
  status: string | null;
  existingEvidence: string[];
  inference: string[];
  newHypothesis: string | null;
  prediction: string | null;
  motivatedBy: string | null; // key of the critique artifact when found, else the raw id
  motivatedByLabel: string | null;
}

export interface CandidateView {
  artifact: ArtifactRef;
  proposalId: string | null;
  label: string;
  title: string;
  question: string | null;
  hypothesisCodes: string[];
  expectedGain: string | null;
  couldChange: string | null;
  feasible: boolean | null;
  feasibility: string | null;
  cost: string | null;
  limitations: string[];
  engineCheck: { valid: boolean; n: number | null } | null;
  selected: boolean;
  experimentId: string | null; // experiment whose spec matches this candidate's spec
}

export interface SelectionView {
  artifact: ArtifactRef;
  proposalId: string | null;
  candidateKey: string | null;
  label: string | null;
  title: string | null;
  rationale: string | null;
  alternatives: string | null;
  ruleApplied: string | null;
  basedOnRun: string | null;
}

export interface DecisionView {
  artifact: ArtifactRef;
  interpretation: string;
  ruleApplied: string | null;
  nextTest: string | null;
  rationale: string | null;
  uncertainty: string | null;
  limitations: string | null;
  hypothesisStatus: string | null;
  decidedBy: string | null;
  runId: string | null;
}

export type StageKey =
  | "question"
  | "experiment"
  | "evidence"
  | "critique"
  | "hypotheses"
  | "candidates"
  | "selection"
  | "new_evidence"
  | "decision";

export interface Stage {
  key: StageKey;
  number: number;
  title: string;
  type: ArtifactType;
  recorded: boolean;
  artifactKeys: string[]; // primary artifact first
  awaiting: { what: string; producer: string; path: string };
}

export interface FollowUp {
  experiment: ExperimentView;
  evidence: EvidenceView | null;
  critiques: CritiqueView[];
}

export interface Discovery {
  question: {
    text: string | null;
    population: string[];
    datasetVersion: string | null;
    hypotheses: { code: string; claim: string; status: string }[];
    artifactKey: string | null;
  };
  baseline: ExperimentView | null;
  baselineEvidence: EvidenceView | null;
  baselineCritiques: CritiqueView[];
  hypotheses: HypothesisView[];
  candidates: CandidateView[];
  selections: SelectionView[];
  followUps: FollowUp[];
  decisions: DecisionView[];
  stages: Stage[];
  artifacts: Record<string, ArtifactRef>;
  sessions: string[];
}

export type DiscoveryMode = "replay" | "live";

export interface DiscoveryPayload {
  discovery: Discovery;
  mode: DiscoveryMode;
  liveUnavailable: boolean; // live requested but the repo files are not reachable (e.g. on Vercel)
  source: string; // "Committed snapshot @ ca6c7d7" or "reports/ on this machine"
  commit: string | null; // full commit of the REPLAY snapshot; null in LIVE
  loadedAt: string;
}
