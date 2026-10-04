"use client";

import { TriangleAlert } from "lucide-react";
import type { DiscoveryRunViewModel as Discovery, StatusView } from "@/lib/discovery/types";
import { ArtifactChip, Inline, StatusTag, useDiscoveryUi } from "./primitives";

/** The artifact key behind an id an artifact cites ("EXP-001", "CRIT-EXP-002-002"), when the run has it. */
function useKeyForId() {
  const { artifacts } = useDiscoveryUi();
  return (id: string | null | undefined): string | null => {
    if (!id) return null;
    const all = Object.values(artifacts);
    return (all.find((a) => a.id === id || a.fullId === id) ?? all.find((a) => a.id === `${id} result`))?.key ?? null;
  };
}

function Panel({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  return (
    <section className="min-w-0 border-t border-gray-200 pt-4">
      <h2 className="flex items-baseline gap-2 text-body font-semibold text-gray-900">
        {title}
        {count != null && <span className="text-caption font-medium text-gray-700 tabular">{count}</span>}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function IdOrText({ id }: { id: string }) {
  const keyFor = useKeyForId();
  const k = keyFor(id);
  return k ? <ArtifactChip artifactKey={k} /> : <span className="font-mono text-caption text-gray-700">{id}</span>;
}

/**
 * Where the investigation stands, at a glance: the latest finding in the artifact's words, the status of every protocol
 * hypothesis with the artifact that set it, each experiment with its result and review state, and what is still open.
 * Everything is read from the view model; the stages below hold the detail.
 */
export default function Overview({
  d,
  headline,
  source,
  sampleSize,
  errors,
}: {
  d: Discovery;
  headline: { text: string; keys: string[] } | null;
  source: string;
  sampleSize: number | null;
  errors: string[];
}) {
  const experiments = [
    ...(d.baseline ? [{ exp: d.baseline, result: d.baselineEvidence?.rankingStatus ?? null }] : []),
    ...d.followUps.map((f) => ({ exp: f.experiment, result: (f.interactions[0]?.status ?? f.evidence?.rankingStatus ?? null) as StatusView | null })),
  ];
  const latestCritique = [...d.followUps].reverse().find((f) => f.critiques.length)?.critiques[0] ?? d.baselineCritiques[0] ?? null;
  const open = latestCritique?.openQuestions ?? [];
  const pendingReview = experiments.filter((e) => /REVIEW/i.test(e.exp.reviewStatus?.code ?? ""));

  return (
    <section id="overview" aria-labelledby="overview-title" className="scroll-mt-28 rounded-xl bg-white p-6 md:p-8">
      <p className="text-caption font-semibold tracking-[0.04em] text-blue-700 uppercase">Where the investigation stands</p>
      <h1 id="overview-title" className="mt-2 max-w-[48ch] text-[24px] leading-[30px] font-extrabold tracking-[-0.02em] text-balance text-gray-900 sm:text-[28px] sm:leading-[34px]">
        {headline?.text ?? "No research question has been recorded yet."}
      </h1>
      <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-body-sm text-gray-700">
        {headline?.keys.map((k) => (
          <ArtifactChip key={k} artifactKey={k} />
        ))}
        {sampleSize != null && <span className="tabular">n = {sampleSize.toLocaleString("en-US")}</span>}
        <span aria-hidden className="text-gray-300">
          ·
        </span>
        <span>{source}</span>
      </p>
      {errors.length > 0 && (
        <p role="alert" className="mt-3 flex items-start gap-2 text-body-sm font-semibold text-gray-900">
          <TriangleAlert aria-hidden size={16} className="mt-0.5 shrink-0 text-yellow-700" />
          {errors.length} artifact problem{errors.length === 1 ? "" : "s"}: {errors[0]}
        </p>
      )}

      <div className="mt-6 grid gap-x-8 gap-y-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)_minmax(0,0.9fr)]">
        <Panel title="Hypotheses" count={d.question.hypotheses.length}>
          <ul className="divide-y divide-gray-100">
            {d.question.hypotheses.map((h) => (
              <li key={h.code} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-x-2 py-2 first:pt-0">
                <span className="pt-0.5 text-body-sm font-bold text-gray-900 tabular">{h.code}</span>
                <div className="min-w-0">
                  <p className="text-body-sm font-medium text-gray-900">{h.title ?? h.claim}</p>
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-caption text-gray-700">
                    <StatusTag status={h.status} code={false} />
                    {h.statusSource ? (
                      <>
                        <span>by</span>
                        <IdOrText id={h.statusSource} />
                      </>
                    ) : (
                      <span>no experiment yet</span>
                    )}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Experiments" count={experiments.length}>
          <ul className="divide-y divide-gray-100">
            {experiments.map(({ exp, result }) => (
              <li key={exp.experimentId} className="py-2 first:pt-0">
                <div className="flex flex-wrap items-center gap-2">
                  <IdOrText id={exp.experimentId} />
                  {exp.hypothesisIds.length > 0 && <span className="text-caption text-gray-700">tests {exp.hypothesisIds.join(", ")}</span>}
                </div>
                {exp.question && <p className="mt-1 line-clamp-2 text-body-sm text-gray-900">{exp.question}</p>}
                <p className="mt-1.5 flex flex-wrap gap-1.5">
                  <StatusTag status={result} code={false} />
                  <StatusTag status={exp.reviewStatus} code={false} />
                </p>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Still open" count={open.length || undefined}>
          {open.length > 0 ? (
            <ul className="space-y-2">
              {open.slice(0, 3).map((q, i) => (
                <li key={i} className="text-body-sm text-gray-900">
                  <Inline text={q} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-body-sm text-gray-700">No open questions recorded.</p>
          )}
          {latestCritique && (
            <p className="mt-2 flex flex-wrap items-center gap-2 text-caption text-gray-700">
              Raised by <ArtifactChip artifactKey={latestCritique.artifact.key} />
              {open.length > 3 && <span>· {open.length - 3} more in the critique</span>}
            </p>
          )}
          {pendingReview.length > 0 && (
            <p className="mt-4 text-body-sm text-gray-700">
              <span className="font-semibold text-gray-900">Awaiting expert review:</span> {pendingReview.map((e) => e.exp.experimentId).join(", ")}
            </p>
          )}
        </Panel>
      </div>

      <p className="mt-6 max-w-[80ch] border-t border-gray-200 pt-4 text-body-sm text-gray-700">
        Figures come only from the deterministic engine; agents interpret them and humans approve each consequential step. All
        results are observational associations. Uncertainty uses PSU-clustered CR1 errors, an approximation of ENUT&rsquo;s
        complex-survey variance. Select any id to inspect its source file.
      </p>
    </section>
  );
}
