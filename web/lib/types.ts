// Row shapes for supabase/migrations. Replace with generated types
// (`supabase gen types typescript`) once the project is linked.

export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };

export interface DecisionRule {
  id: string;
  if: string;
  then: string;
}

export interface Project {
  id: string;
  title: string;
  question: string;
  cohort_definition: string | null;
  decision_rules: DecisionRule[];
  status: string;
  omnigent_session_url: string | null;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface Hypothesis {
  id: string;
  project_id: string;
  statement: string;
  generated_by: string;
  status: string;
  supporting_passage_ids: string[];
  opposing_passage_ids: string[];
  created_at: string;
}

export interface ExperimentProposal {
  id: string;
  project_id: string;
  hypothesis_id: string | null;
  label: string;
  title: string;
  protocol: string;
  description: string | null;
  learning_value: string | null;
  feasibility: string | null;
  cost: string | null;
  selected: boolean;
  selection_rationale: string | null;
  created_at: string;
}

/** One estimate row. Contract documented in AGENTS.md ("Experiment results contract"). */
export interface Estimate {
  activity: string;
  sex: string;
  estimate: number;
  ci_low?: number | null;
  ci_high?: number | null;
  n?: number | null;
}

export interface RunResults {
  label?: string;
  method?: string;
  units?: string;
  uncertainty_method?: string;
  estimates?: Estimate[];
  notes?: string[];
}

export interface ExperimentRun {
  id: string;
  project_id: string;
  proposal_id: string | null;
  protocol: string;
  dataset_hash: string | null;
  code_version: string | null;
  parameters: Json;
  sample_sizes: Record<string, number>;
  results: RunResults;
  status: "pending" | "running" | "succeeded" | "failed";
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface Decision {
  id: string;
  project_id: string;
  experiment_run_id: string | null;
  interpretation: string;
  uncertainty: string | null;
  limitations: string | null;
  rule_applied: string | null;
  next_test: string | null;
  rationale: string | null;
  decided_by: string;
  created_at: string;
}

export interface AgentEvent {
  id: string;
  project_id: string;
  session_id: string | null;
  agent_name: string;
  event_type: string;
  summary: string | null;
  occurred_at: string;
}

export interface Source {
  id: string;
  kind: string;
  title: string;
  url: string | null;
  doi: string | null;
  publisher: string | null;
  year: number | null;
  is_demo: boolean;
}
