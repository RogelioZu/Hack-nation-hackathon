import "server-only";
import { connection } from "next/server";
import { supabase } from "./supabase";
import type {
  AgentEvent,
  Decision,
  ExperimentProposal,
  ExperimentRun,
  Hypothesis,
  Project,
  Source,
} from "./types";

function unwrap<T>(res: { data: T | null; error: { message: string } | null }, what: string): T {
  if (res.error) throw new Error(`Failed to load ${what}: ${res.error.message}`);
  return res.data as T;
}

export async function getProjects(): Promise<Project[]> {
  await connection();
  const res = await supabase().from("projects").select("*").order("created_at", { ascending: false });
  return unwrap(res, "projects") ?? [];
}

export interface Research {
  project: Project;
  hypotheses: Hypothesis[];
  proposals: ExperimentProposal[];
  runs: ExperimentRun[];
  decisions: Decision[];
  events: AgentEvent[];
  sources: Source[];
}

export async function getResearch(id: string): Promise<Research | null> {
  await connection();
  const db = supabase();
  const project = unwrap(await db.from("projects").select("*").eq("id", id).maybeSingle(), "project");
  if (!project) return null;

  const [hypotheses, proposals, runs, decisions, events, sources] = await Promise.all([
    db.from("hypotheses").select("*").eq("project_id", id).order("created_at"),
    db.from("experiment_proposals").select("*").eq("project_id", id).order("label"),
    db.from("experiment_runs").select("*").eq("project_id", id).order("created_at", { ascending: false }),
    db.from("decisions").select("*").eq("project_id", id).order("created_at", { ascending: false }),
    db.from("agent_events").select("*").eq("project_id", id).order("occurred_at"),
    // Sources are shared across projects; the corpus is small.
    db.from("sources").select("*").order("retrieved_at"),
  ]);

  return {
    project: project as Project,
    hypotheses: unwrap(hypotheses, "hypotheses") ?? [],
    proposals: unwrap(proposals, "proposals") ?? [],
    runs: unwrap(runs, "runs") ?? [],
    decisions: unwrap(decisions, "decisions") ?? [],
    events: unwrap(events, "agent events") ?? [],
    sources: unwrap(sources, "sources") ?? [],
  };
}
