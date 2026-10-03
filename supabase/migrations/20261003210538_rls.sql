-- Public read of aggregated demo data; writes only through service_role
-- (Python host / Omnigent tools / Next.js Route Handlers). No write policies on purpose.

do $$
declare
  t text;
begin
  foreach t in array array[
    'projects','hypotheses','experiment_proposals','experiment_runs',
    'decisions','agent_events','sources','passages'
  ] loop
    execute format('alter table public.%I enable row level security', t);
    execute format(
      'create policy %I on public.%I for select to anon, authenticated using (true)',
      t || '_public_read', t
    );
    execute format('grant select on public.%I to anon, authenticated', t);
    execute format('grant all on public.%I to service_role', t);
  end loop;
end
$$;

grant execute on function public.hybrid_search(text, extensions.vector, int, float, float, int)
  to anon, authenticated, service_role;
