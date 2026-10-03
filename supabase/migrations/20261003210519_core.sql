-- Research state shared by every agent. Agents exchange row IDs, not free prose.
-- No individual microdata rows are ever stored here: only aggregates and provenance.

create table public.projects (
  id                    uuid primary key default gen_random_uuid(),
  title                 text not null,
  question              text not null,
  cohort_definition     text,
  -- Next-decision rules written BEFORE seeing results (pre-registration).
  decision_rules        jsonb not null default '[]'::jsonb,
  status                text not null default 'draft'
                        check (status in ('draft','evidence','planning','running','critique','decided','archived')),
  omnigent_session_url  text,
  is_demo               boolean not null default false,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create table public.hypotheses (
  id                     uuid primary key default gen_random_uuid(),
  project_id             uuid not null references public.projects(id) on delete cascade,
  statement              text not null,
  -- Which agent (or 'human') generated it; agent hypotheses must be labelled in the UI.
  generated_by           text not null default 'human',
  status                 text not null default 'proposed'
                         check (status in ('proposed','testing','supported','not_supported','inconclusive','superseded')),
  supporting_passage_ids uuid[] not null default '{}',
  opposing_passage_ids   uuid[] not null default '{}',
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);
create index hypotheses_project_idx on public.hypotheses(project_id);

create table public.experiment_proposals (
  id                  uuid primary key default gen_random_uuid(),
  project_id          uuid not null references public.projects(id) on delete cascade,
  hypothesis_id       uuid references public.hypotheses(id) on delete set null,
  label               text not null,                 -- 'A', 'B', ...
  title               text not null,
  protocol            text not null,                 -- key of a closed protocol accepted by run_experiment
  description         text,
  learning_value      text,
  feasibility         text,
  cost                text,
  selected            boolean not null default false,
  selection_rationale text,
  created_at          timestamptz not null default now()
);
create index experiment_proposals_project_idx on public.experiment_proposals(project_id);

create table public.experiment_runs (
  id             uuid primary key default gen_random_uuid(),
  project_id     uuid not null references public.projects(id) on delete cascade,
  hypothesis_id  uuid references public.hypotheses(id) on delete set null,
  proposal_id    uuid references public.experiment_proposals(id) on delete set null,
  protocol       text not null,
  dataset_hash   text,
  code_version   text,
  parameters     jsonb not null default '{}'::jsonb,
  sample_sizes   jsonb not null default '{}'::jsonb,
  -- Aggregated output only: estimates, uncertainty, method, chart series.
  results        jsonb not null default '{}'::jsonb,
  artifact_paths jsonb not null default '[]'::jsonb,
  status         text not null default 'pending'
                 check (status in ('pending','running','succeeded','failed')),
  error          text,
  started_at     timestamptz,
  finished_at    timestamptz,
  created_at     timestamptz not null default now()
);
create index experiment_runs_project_idx on public.experiment_runs(project_id);

create table public.decisions (
  id                uuid primary key default gen_random_uuid(),
  project_id        uuid not null references public.projects(id) on delete cascade,
  experiment_run_id uuid references public.experiment_runs(id) on delete set null,
  interpretation    text not null,
  uncertainty       text,
  limitations       text,
  rule_applied      text,   -- which pre-registered decision rule fired
  next_test         text,
  rationale         text,
  decided_by        text not null default 'critic',
  created_at        timestamptz not null default now()
);
create index decisions_project_idx on public.decisions(project_id);

create table public.agent_events (
  id                uuid primary key default gen_random_uuid(),
  project_id        uuid not null references public.projects(id) on delete cascade,
  session_id        text,    -- Omnigent session / run identifier
  experiment_run_id uuid references public.experiment_runs(id) on delete set null,
  agent_name        text not null,
  event_type        text not null
                    check (event_type in ('started','tool_call','handoff','output','decision','approval','error','note')),
  summary           text,
  input_refs        jsonb not null default '{}'::jsonb,
  output_refs       jsonb not null default '{}'::jsonb,
  occurred_at       timestamptz not null default now()
);
create index agent_events_project_time_idx on public.agent_events(project_id, occurred_at);

-- Keep updated_at fresh.
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger projects_touch before update on public.projects
  for each row execute function public.touch_updated_at();
create trigger hypotheses_touch before update on public.hypotheses
  for each row execute function public.touch_updated_at();
