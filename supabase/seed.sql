-- DEMO SEED — placeholder state so the web panel renders before the real loop runs.
-- Nothing here is a finding. The run stays 'pending' and has no results.
-- Fixed IDs so the demo URL is stable: /research/00000000-0000-0000-0000-000000000001

insert into public.projects (id, title, question, cohort_definition, decision_rules, status, is_demo)
values (
  '00000000-0000-0000-0000-000000000001',
  'Commuting and time poverty in Mexico City and Estado de México',
  'Among workers living in Mexico City and Estado de México, how are 60 additional weekly minutes of work commuting associated with weekly time spent on sleep, family/social time, caring for household members, leisure and personal care? Does the association differ by sex?',
  'Tentative: people aged 18+ living in CDMX or Edomex, who worked last week and reported work-commute time. To be confirmed against the ENUT data dictionary.',
  '[
    {"id":"R1","if":"Sex difference is sufficiently supported and subgroup sizes are adequate","then":"Propose a test on household composition / presence of children"},
    {"id":"R2","if":"No sex difference appears","then":"Propose sensitivity to long commutes or a non-linear relationship"},
    {"id":"R3","if":"Data quality or sample size prevents a conclusion","then":"Revise variables, cohort and measurement before continuing"}
  ]'::jsonb,
  'planning',
  true
)
on conflict (id) do nothing;

insert into public.sources (id, kind, title, url, publisher, year, is_demo)
values
  ('00000000-0000-0000-0000-0000000000a1', 'official_doc',
   'ENUT 2024 — Microdata (INEGI)', 'https://www.inegi.org.mx/programas/enut/2024/#Microdatos',
   'INEGI', 2024, true),
  ('00000000-0000-0000-0000-0000000000a2', 'data_dictionary',
   'ENUT 2024 — Data dictionary, TMODULO', 'https://www.inegi.org.mx/rnm/index.php/catalog/1127/data-dictionary/F22',
   'INEGI', 2024, true)
on conflict (id) do nothing;

insert into public.hypotheses (id, project_id, statement, generated_by, status)
values (
  '00000000-0000-0000-0000-0000000000b1',
  '00000000-0000-0000-0000-000000000001',
  '[DEMO] Longer weekly work commutes are associated with fewer weekly minutes of sleep and family/social time, and the association differs by sex.',
  'method_agent',
  'proposed'
)
on conflict (id) do nothing;

insert into public.experiment_proposals
  (id, project_id, hypothesis_id, label, title, protocol, description, learning_value, feasibility, cost, selected, selection_rationale)
values
  ('00000000-0000-0000-0000-0000000000c1', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-0000000000b1',
   'A', 'Weighted means by commute group and sex', 'weighted_means_by_group',
   'Weighted means/distributions of each activity for commute-time groups, split by sex.',
   'Medium: shows patterns and subgroup sizes', 'High', 'Low', false, null),
  ('00000000-0000-0000-0000-0000000000c2', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-0000000000b1',
   'B', 'Adjusted exploratory regression with commute × sex', 'wls_commute_by_sex',
   'Activity minutes ~ weekly commute hours × sex + age + hours worked + state, weighted by FAC_PER. Associational only.',
   'High: directly estimates minutes per +60 weekly commute minutes by sex', 'Medium', 'Medium',
   true, '[DEMO] Placeholder rationale — the coordinator will overwrite this with the real selection.')
on conflict (id) do nothing;

insert into public.experiment_runs (id, project_id, hypothesis_id, proposal_id, protocol, status)
values (
  '00000000-0000-0000-0000-0000000000d1',
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-0000000000b1',
  '00000000-0000-0000-0000-0000000000c2',
  'wls_commute_by_sex',
  'pending'
)
on conflict (id) do nothing;

insert into public.agent_events (project_id, session_id, agent_name, event_type, summary, occurred_at)
values
  ('00000000-0000-0000-0000-000000000001', 'demo', 'coordinator', 'started',
   '[DEMO] Research session opened for the commute question.', now() - interval '4 minutes'),
  ('00000000-0000-0000-0000-000000000001', 'demo', 'evidence_agent', 'tool_call',
   '[DEMO] search_evidence("ENUT commute variables weekly reference")', now() - interval '3 minutes'),
  ('00000000-0000-0000-0000-000000000001', 'demo', 'method_agent', 'output',
   '[DEMO] Proposed tests A and B.', now() - interval '2 minutes'),
  ('00000000-0000-0000-0000-000000000001', 'demo', 'coordinator', 'handoff',
   '[DEMO] Selected test B; waiting for run_experiment.', now() - interval '1 minute');
