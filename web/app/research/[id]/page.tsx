import { notFound } from "next/navigation";
import { getResearch } from "@/lib/data";
import type { ExperimentRun } from "@/lib/types";
import EstimatesChart from "./EstimatesChart";
import Refresher from "./Refresher";
import PageHeader from "../../_components/PageHeader";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function ResearchPage({ params }: PageProps<"/research/[id]">) {
  const { id } = await params;
  if (!UUID.test(id)) notFound();
  const research = await getResearch(id);
  if (!research) notFound();

  const { project, hypotheses, proposals, runs, decisions, events, sources } = research;
  const latestRun = runs[0];
  const latestDecision = decisions[0];

  return (
    <>
      <PageHeader title="Audit trail" />
      <main className="px-4 pb-10 md:px-8">
        <div className="space-y-10 rounded-lg bg-white p-6 md:p-8">
          <Refresher />

          <section className="space-y-3">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded bg-panel px-2 py-0.5 text-muted">status: {project.status}</span>
              {project.is_demo && (
                <span className="rounded border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 font-medium uppercase tracking-wide text-amber-600">
                  demo data — not findings
                </span>
              )}
              {project.omnigent_session_url ? (
                <a
                  href={project.omnigent_session_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent underline"
                >
                  Open Omnigent session ↗
                </a>
              ) : (
                <span className="text-muted">Omnigent session: pending</span>
              )}
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">{project.title}</h1>
            <p className="max-w-3xl">{project.question}</p>
            {project.cohort_definition && (
              <p className="max-w-3xl text-sm text-muted">
                <strong className="text-foreground">Cohort.</strong> {project.cohort_definition}
              </p>
            )}
          </section>

          <Section title="Pre-registered decision rules" hint="Written before seeing any result.">
            {project.decision_rules.length === 0 ? (
              <Pending />
            ) : (
              <ul className="space-y-1 text-sm">
                {project.decision_rules.map((r) => (
                  <li key={r.id}>
                    <span className="font-mono text-xs text-muted">{r.id}</span> If {r.if.toLowerCase()} →{" "}
                    {r.then.toLowerCase()}.
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Agent timeline">
            {events.length === 0 ? (
              <Pending />
            ) : (
              <ol className="space-y-2 border-l border-line pl-4 text-sm">
                {events.map((e) => (
                  <li key={e.id}>
                    <span className="font-mono text-xs text-muted">
                      {new Date(e.occurred_at).toLocaleTimeString("en-GB")}
                    </span>{" "}
                    <span className="font-medium">{e.agent_name}</span>{" "}
                    <span className="rounded bg-panel px-1.5 py-0.5 text-xs text-muted">{e.event_type}</span>{" "}
                    {e.summary}
                  </li>
                ))}
              </ol>
            )}
          </Section>

          <Section title="Sources">
            {sources.length === 0 ? (
              <Pending />
            ) : (
              <ul className="space-y-1 text-sm">
                {sources.map((s) => (
                  <li key={s.id}>
                    {s.url ? (
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-accent underline">
                        {s.title}
                      </a>
                    ) : (
                      s.title
                    )}{" "}
                    <span className="text-muted">· {[s.publisher, s.year, s.kind].filter(Boolean).join(" · ")}</span>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Hypotheses">
            {hypotheses.length === 0 ? (
              <Pending />
            ) : (
              <ul className="space-y-2 text-sm">
                {hypotheses.map((h) => (
                  <li key={h.id} className="rounded border border-line p-3">
                    <div className="mb-1 flex gap-2 text-xs text-muted">
                      <span>{h.generated_by === "human" ? "human" : `agent-generated · ${h.generated_by}`}</span>
                      <span>· {h.status}</span>
                      <span>
                        · {h.supporting_passage_ids.length} supporting / {h.opposing_passage_ids.length} opposing
                        passages
                      </span>
                    </div>
                    {h.statement}
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Candidate tests">
            {proposals.length === 0 ? (
              <Pending />
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {proposals.map((p) => (
                  <div
                    key={p.id}
                    className={`rounded border p-3 text-sm ${p.selected ? "border-accent" : "border-line"}`}
                  >
                    <div className="mb-1 flex items-center gap-2">
                      <span className="font-mono text-xs">Test {p.label}</span>
                      {p.selected && <span className="rounded bg-accent px-1.5 text-xs text-white">selected</span>}
                    </div>
                    <p className="font-medium">{p.title}</p>
                    {p.description && <p className="mt-1 text-muted">{p.description}</p>}
                    <dl className="mt-2 grid grid-cols-3 gap-2 text-xs">
                      <Field label="Learning" value={p.learning_value} />
                      <Field label="Feasibility" value={p.feasibility} />
                      <Field label="Cost" value={p.cost} />
                    </dl>
                    {p.selected && p.selection_rationale && (
                      <p className="mt-2 text-xs">
                        <strong>Why selected:</strong> {p.selection_rationale}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Section>

          <Section title="Result">{latestRun ? <RunResult run={latestRun} /> : <Pending />}</Section>

          <Section title="Decision and next test">
            {latestDecision ? (
              <div className="space-y-2 text-sm">
                <p>{latestDecision.interpretation}</p>
                {latestDecision.rule_applied && (
                  <p>
                    <strong>Rule applied:</strong> {latestDecision.rule_applied}
                  </p>
                )}
                {latestDecision.uncertainty && (
                  <p>
                    <strong>Uncertainty:</strong> {latestDecision.uncertainty}
                  </p>
                )}
                {latestDecision.limitations && (
                  <p>
                    <strong>Limitations:</strong> {latestDecision.limitations}
                  </p>
                )}
                {latestDecision.next_test && (
                  <p className="rounded border border-accent p-3">
                    <strong>Next test:</strong> {latestDecision.next_test}
                  </p>
                )}
                {latestDecision.rationale && <p className="text-muted">{latestDecision.rationale}</p>}
              </div>
            ) : (
              <Pending />
            )}
          </Section>
        </div>
      </main>
    </>
  );
}

function RunResult({ run }: { run: ExperimentRun }) {
  const r = run.results ?? {};
  const estimates = r.estimates ?? [];
  return (
    <div className="space-y-4 text-sm">
      <div className="flex flex-wrap gap-2 text-xs text-muted">
        <span className="rounded bg-panel px-2 py-0.5">run: {run.status}</span>
        <span className="rounded bg-panel px-2 py-0.5">protocol: {run.protocol}</span>
        {r.label && <span className="rounded bg-panel px-2 py-0.5">{r.label}</span>}
        {run.dataset_hash && <span className="font-mono">dataset {run.dataset_hash.slice(0, 12)}</span>}
        {run.code_version && <span className="font-mono">code {run.code_version.slice(0, 12)}</span>}
      </div>
      {run.status === "failed" && run.error && <p className="text-red-600">{run.error}</p>}
      {estimates.length === 0 ? (
        <Pending label={run.status === "succeeded" ? "No estimates reported." : "Waiting for the experiment run."} />
      ) : (
        <>
          <EstimatesChart estimates={estimates} units={r.units} />
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-line text-muted">
                <tr>
                  <th className="py-1 pr-4">Activity</th>
                  <th className="py-1 pr-4">Sex</th>
                  <th className="py-1 pr-4 text-right">Estimate</th>
                  <th className="py-1 pr-4 text-right">Interval</th>
                  <th className="py-1 text-right">n</th>
                </tr>
              </thead>
              <tbody>
                {estimates.map((e, i) => (
                  <tr key={i} className="border-b border-line">
                    <td className="py-1 pr-4">{e.activity}</td>
                    <td className="py-1 pr-4">{e.sex}</td>
                    <td className="py-1 pr-4 text-right font-mono">{e.estimate.toFixed(1)}</td>
                    <td className="py-1 pr-4 text-right font-mono">
                      {e.ci_low != null && e.ci_high != null ? `${e.ci_low.toFixed(1)} – ${e.ci_high.toFixed(1)}` : "—"}
                    </td>
                    <td className="py-1 text-right font-mono">{e.n ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {r.method && (
        <p>
          <strong>Method:</strong> {r.method}
        </p>
      )}
      {r.uncertainty_method && (
        <p>
          <strong>Uncertainty:</strong> {r.uncertainty_method}
        </p>
      )}
      {Object.keys(run.sample_sizes ?? {}).length > 0 && (
        <p className="text-xs text-muted">
          Sample sizes:{" "}
          {Object.entries(run.sample_sizes)
            .map(([k, v]) => `${k} = ${v}`)
            .join(" · ")}
        </p>
      )}
      {r.notes?.map((n, i) => (
        <p key={i} className="text-xs text-muted">
          {n}
        </p>
      ))}
    </div>
  );
}

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2 border-b border-line pb-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        {hint && <span className="text-xs text-muted">{hint}</span>}
      </div>
      {children}
    </section>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd>{value ?? "—"}</dd>
    </div>
  );
}

function Pending({ label = "Pending." }: { label?: string }) {
  return <p className="text-sm italic text-muted">{label}</p>;
}
