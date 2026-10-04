"use client";

import { useState, type ReactNode } from "react";
import { CircleCheck, Database, RefreshCcw, Signpost, TriangleAlert, UserCheck } from "lucide-react";
import { outcomeLabel } from "@/lib/discovery/model";
import type {
  AssessmentView,
  CandidateView,
  CritiqueView,
  DecisionView,
  Discovery,
  EvidenceView,
  ExperimentView,
  HypothesisView,
  SelectionView,
} from "@/lib/discovery/types";
import ForestPlot from "./ForestPlot";
import { ArtifactChip, humanize, Inline, Pill, plain, signed, TypeBadge, VerbatimList } from "./primitives";

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-caption font-semibold text-gray-700">{label}</dt>
      <dd className="mt-1 text-body text-gray-900">{children}</dd>
    </div>
  );
}

const lead = "text-h3 text-balance text-gray-900";
const support = "text-[17px] leading-7 text-gray-700 max-w-[68ch]";

// --- 1 · Research question ---------------------------------------------------

export function QuestionBody({
  q,
  assessments,
  assessedIn,
}: {
  q: Discovery["question"];
  assessments: AssessmentView[];
  assessedIn: string | null;
}) {
  return (
    <>
      <p className="max-w-[68ch] text-[18px] leading-7 font-medium text-gray-900">
        {q.text ?? "The research question is missing from initial_state.json."}
      </p>
      <p className="mt-3 text-body-sm text-gray-700">
        {[...q.population, ...(q.datasetVersion ? [q.datasetVersion] : [])].map((p, i) => (
          <span key={p}>
            {i > 0 && <span className="mx-2 text-gray-300">·</span>}
            <span className={p === q.datasetVersion ? "font-mono" : ""}>{p}</span>
          </span>
        ))}
      </p>
      {q.hypotheses.length > 0 && (
        <dl className="mt-5 grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-1.5 border-t border-gray-200 pt-4 text-body-sm">
          {q.hypotheses.map((h) => {
            const tested = h.status.startsWith("tested");
            const a = assessments.find((x) => x.id === h.code);
            return (
              <div key={h.code} className="contents">
                <dt className={`font-bold tabular ${tested ? "text-gray-900" : "text-gray-700"}`}>{h.code}</dt>
                <dd className="min-w-0 text-gray-900">
                  {h.claim}
                  {/* The engine's own words: an assessment under the model, never a confirmation. */}
                  <span className={`mt-1 block text-body-sm text-gray-700 ${tested || a ? "" : "italic"}`}>
                    {a ? (
                      <>
                        {assessedIn && <span className="font-semibold text-gray-900">{assessedIn}: </span>}
                        {a.assessment}
                        {a.evidence && <span className="text-gray-700"> · {a.evidence}</span>}
                      </>
                    ) : (
                      h.status.replace(/_/g, " ")
                    )}
                  </span>
                </dd>
              </div>
            );
          })}
        </dl>
      )}
    </>
  );
}

// --- 2 · Experiment ----------------------------------------------------------

export function ExperimentBody({ exp }: { exp: ExperimentView }) {
  return (
    <>
      {exp.question && <p className={`${support} text-gray-900`}>&ldquo;{exp.question}&rdquo;</p>}
      <dl className="mt-5 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-3">
        <Field label="Exposure">{exp.exposure ?? "—"}</Field>
        <Field label="Outcomes">{exp.outcomes.map(outcomeLabel).join(", ") || "—"}</Field>
        <Field label="Adjusted for">{exp.covariates.join(", ") || "—"}</Field>
        <Field label="Method">{exp.method ?? "—"}</Field>
        <Field label="Uncertainty">{exp.uncertainty ?? "—"}</Field>
        <Field label="Population">{exp.population.join(" · ") || "—"}</Field>
      </dl>
      <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 border-t border-gray-200 pt-4">
        {exp.status && (
          <Pill tone={exp.status === "EXPERIMENT_COMPLETED" ? "good" : "warn"} icon={exp.status === "EXPERIMENT_COMPLETED" ? CircleCheck : TriangleAlert}>
            {exp.status === "EXPERIMENT_COMPLETED" ? "Completed" : humanize(exp.status)}
          </Pill>
        )}
        {exp.reproduced != null && (
          <Pill tone={exp.reproduced ? "good" : "warn"} icon={RefreshCcw}>
            {exp.reproduced ? "Identical on re-run" : "Re-run differed"}
          </Pill>
        )}
        {exp.datasetUnchanged && (
          <Pill tone="good" icon={Database}>
            Dataset hash unchanged
          </Pill>
        )}
        {exp.reviewStatus && (
          <Pill tone="warn" icon={UserCheck} title={exp.reviewStatus}>
            {exp.reviewStatus === "REQUIRES_HUMAN_REVIEW" ? "Requires human review" : humanize(exp.reviewStatus)}
          </Pill>
        )}
        {exp.hypothesisIds.length > 0 && <Pill>Tests {exp.hypothesisIds.join(", ")}</Pill>}
      </div>
    </>
  );
}

// --- 3 · Evidence (also reused for every follow-up experiment) ---------------

export function EvidenceBody({ ev }: { ev: EvidenceView }) {
  const [headline, ...rest] = ev.sentences;
  const caption = [
    ev.units ? `${ev.units[0].toUpperCase()}${ev.units.slice(1)} (Mon–Fri totals)` : null,
    ev.covariates.length ? `adjusted for ${ev.covariates.join(", ")}` : null,
    ev.sampleSize != null ? `n = ${ev.sampleSize.toLocaleString("en-US")}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
  return (
    <>
      {headline && <p className={lead}>{headline}</p>}
      {rest.map((s) => (
        <p key={s} className={`mt-1 ${support}`}>
          {s}
        </p>
      ))}
      {ev.rows.length > 0 ? (
        <ForestPlot rows={ev.rows} highlight={ev.strongestNegative?.outcome ?? null} caption={`${caption}.`} />
      ) : (
        <p className="mt-4 text-body-sm text-gray-700 italic">The result has no adjusted estimates to plot.</p>
      )}

      {ev.rankingStatus && (
        <div className="mt-6 flex gap-3 rounded-md bg-gray-50 p-4">
          <span className="flex size-6 shrink-0 items-center justify-center rounded-sm bg-yellow-400 text-gray-900">
            <TriangleAlert aria-hidden size={14} strokeWidth={2.25} />
          </span>
          <div className="min-w-0">
            <p className="text-h4 text-gray-900">{ev.rankingSentence ?? `Ranking status: ${ev.rankingStatus}`}</p>
            <p className="mt-1 text-body-sm text-gray-700">
              {ev.pairs && (
                <>
                  {ev.pairs.resolved} of {ev.pairs.total} paired differences exclude zero
                  {ev.pairs.adjustment ? ` (${ev.pairs.adjustment})` : ""}.{" "}
                </>
              )}
              <span className="font-mono text-caption">{ev.rankingStatus}</span>
            </p>
            {ev.pairs && ev.pairs.items.length > 0 && (
              <table className="mt-3 w-full text-left text-body-sm">
                <caption className="sr-only">Paired differences between outcomes, in weekday minutes, with adjusted intervals</caption>
                <thead className="sr-only">
                  <tr>
                    <th scope="col">Pair</th>
                    <th scope="col">Difference and interval</th>
                    <th scope="col" className="hidden sm:table-cell">Zero</th>
                  </tr>
                </thead>
                <tbody>
                  {ev.pairs.items.map((p) => (
                    <tr key={`${p.a}-${p.b}`} className="border-t border-gray-200 first:border-t-0">
                      <th scope="row" className={`py-1.5 pr-3 font-normal ${p.resolved ? "text-gray-700" : "font-semibold text-gray-900"}`}>
                        {p.a} − {p.b}
                      </th>
                      <td className="py-1.5 pr-3 text-right text-gray-700 tabular">
                        <span className="whitespace-nowrap">{signed(p.difference)}</span>
                        {p.interval && (
                          <span className="block whitespace-nowrap sm:inline">
                            <span className="max-sm:hidden"> </span>[{plain(p.interval.lower)}, {plain(p.interval.upper)}]
                          </span>
                        )}
                        {/* Phones: the zero status sits under the interval instead of in a third column. */}
                        <span className={`block text-caption sm:hidden ${p.resolved ? "" : "font-semibold text-gray-900"}`}>
                          {p.resolved ? "excludes zero" : "includes zero"}
                        </span>
                      </td>
                      <td
                        className={`hidden w-[7.5rem] py-1.5 text-right text-caption whitespace-nowrap sm:table-cell ${p.resolved ? "text-gray-700" : "font-semibold text-gray-900"}`}
                      >
                        {p.resolved ? "excludes zero" : "includes zero"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      <div className="mt-4 max-w-[72ch] space-y-1.5 text-body-sm text-gray-700">
        <p>
          95% pointwise intervals{ev.covarianceMethod ? ` · ${ev.covarianceMethod}` : ""}: an approximation, not the full ENUT
          complex-survey variance.
        </p>
        {ev.sensitivity.map((s) => (
          <p key={s.name}>
            Sensitivity <span className="font-mono">{s.name}</span>
            {s.nAfter != null ? `: n = ${s.nAfter.toLocaleString("en-US")}` : ""}
            {s.nExcluded != null ? ` (${s.nExcluded} excluded)` : ""}
            {s.rankingStatus ? `, ranking ${s.rankingStatus}` : ""}.
          </p>
        ))}
      </div>
    </>
  );
}

// --- 4 · Scientific critique -------------------------------------------------

function FindingGroup({ label, items, initial }: { label: string; items: string[]; initial?: number }) {
  return (
    <div className="border-t border-gray-200 pt-4">
      <p className="mb-2 flex items-baseline gap-2 text-body-sm font-semibold text-gray-900">
        {label}
        <span className="text-caption font-medium text-gray-700 tabular">{items.length}</span>
      </p>
      <VerbatimList items={items} initial={initial} />
    </div>
  );
}

const EVIDENCE_KIND: Record<string, string> = { OBSERVED_EVIDENCE: "Observed", INFERENCE: "Inference" };

function EvidenceCited({ items }: { items: CritiqueView["evidence"] }) {
  const [open, setOpen] = useState(false);
  const shown = open ? items : items.slice(0, 2);
  return (
    <div className="border-t border-gray-200 pt-4">
      <p className="mb-2 flex items-baseline gap-2 text-body-sm font-semibold text-gray-900">
        Evidence cited
        <span className="text-caption font-medium text-gray-700 tabular">{items.length}</span>
      </p>
      <ul className="space-y-2.5">
        {shown.map((e, i) => (
          <li key={i} className="text-body-sm text-gray-700">
            <span className="mr-2 font-semibold text-gray-900">{EVIDENCE_KIND[e.kind] ?? humanize(e.kind)}</span>
            <Inline text={e.statement} />
            {e.source && <span className="mt-0.5 block font-mono text-caption [overflow-wrap:anywhere] text-gray-700">{e.source}</span>}
          </li>
        ))}
      </ul>
      {items.length > 2 && (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className="mt-2 rounded-full text-caption font-semibold text-blue-600 hover:text-blue-700"
        >
          {open ? "Show less" : `Show all ${items.length}`}
        </button>
      )}
    </div>
  );
}

export function CritiqueBody({ c, earlier }: { c: CritiqueView; earlier: CritiqueView[] }) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex h-8 items-center gap-2 rounded-sm bg-yellow-400 px-3 text-body font-bold tracking-[0.04em] text-gray-900">
          <TriangleAlert aria-hidden size={16} strokeWidth={2.25} />
          {c.verdict ?? "No verdict"}
        </span>
        <span className="text-body-sm text-gray-700">
          Verdict by <span className="font-semibold text-gray-900">{c.agent}</span>
          {c.model && <> · {c.model}</>}
        </span>
      </div>
      {c.rationale && (
        <p className={`mt-3 ${support}`}>
          <Inline text={c.rationale} />
        </p>
      )}
      <div className="mt-6 grid gap-x-8 gap-y-5 sm:grid-cols-2">
        {c.evidence.length > 0 && (
          <div className="sm:col-span-2">
            <EvidenceCited items={c.evidence} />
          </div>
        )}
        <FindingGroup label="Limitations" items={c.limitations} />
        <FindingGroup label="Uncertainties" items={c.uncertainties} />
        <div className="sm:col-span-2">
          <FindingGroup label="Unsupported claims" items={c.unsupported} />
        </div>
        <div className="sm:col-span-2">
          <FindingGroup label="Untested questions" items={c.openQuestions} initial={c.openQuestions.length} />
        </div>
      </div>
      {(c.ruleApplied || c.recommendedDirection) && (
        <p className="mt-2 text-body-sm text-gray-700">
          {c.ruleApplied && <span className="mr-2 font-mono font-semibold text-gray-900">{c.ruleApplied}</span>}
          {c.recommendedDirection}
        </p>
      )}
      {earlier.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-caption text-gray-700">
          Earlier critiques of the same experiment:
          {earlier.map((e) => (
            <ArtifactChip key={e.artifact.key} artifactKey={e.artifact.key} />
          ))}
        </div>
      )}
    </>
  );
}

// --- 5 · Hypotheses ----------------------------------------------------------

function Part({ label, items, text }: { label: string; items?: string[]; text?: string | null }) {
  const list = items ?? (text ? [text] : []);
  return (
    <div className="min-w-0">
      <dt className="mb-1 text-caption font-semibold text-gray-700">{label}</dt>
      <dd>
        <VerbatimList items={list} />
      </dd>
    </div>
  );
}

export function HypothesesBody({ hs }: { hs: HypothesisView[] }) {
  return (
    <ol className="divide-y divide-gray-200">
      {hs.map((h) => (
        <li key={h.artifact.key} className="py-5 first:pt-0 last:pb-0">
          <div className="flex flex-wrap items-center gap-2">
            {h.code && (
              <span className="inline-flex h-7 items-center rounded-sm px-2.5 text-body-sm font-bold text-blue-600 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-blue-500">
                {h.code}
              </span>
            )}
            <ArtifactChip artifactKey={h.artifact.key} />
            <span className="text-caption text-gray-700">
              {h.generatedBy ? `by ${h.generatedBy}` : ""}
              {h.status ? ` · ${h.status}` : ""}
            </span>
          </div>
          <p className="mt-3 text-h4 text-balance text-gray-900">{h.statement}</p>
          <dl className="mt-4 grid gap-4 sm:grid-cols-3">
            <Part label="Existing evidence" items={h.existingEvidence} />
            <Part label="Inference" items={h.inference} />
            <Part label="New hypothesis" text={h.newHypothesis} />
          </dl>
          {h.prediction && (
            <p className="mt-3 text-body-sm text-gray-700">
              <span className="font-semibold text-gray-900">Would be contradicted if: </span>
              {h.prediction}
            </p>
          )}
          {h.motivatedByLabel && (
            <p className="mt-3 flex flex-wrap items-center gap-2 text-caption text-gray-700">
              Motivated by
              {h.motivatedBy ? <ArtifactChip artifactKey={h.motivatedBy} /> : <span className="font-mono">{h.motivatedByLabel}</span>}
            </p>
          )}
        </li>
      ))}
    </ol>
  );
}

// --- 6 · Candidates ----------------------------------------------------------

export function CandidatesBody({ cs, experimentKeys }: { cs: CandidateView[]; experimentKeys: Record<string, string> }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {cs.map((c) => (
        <section
          key={c.artifact.key}
          aria-label={`Candidate ${c.label}`}
          className={`flex flex-col rounded-md p-4 ${c.selected ? "bg-white ring-2 ring-blue-500" : "bg-gray-50 ring-1 ring-gray-200"}`}
        >
          <div className="flex items-start gap-3">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-sm bg-blue-800 text-body font-bold text-white">{c.label}</span>
            <div className="min-w-0 flex-1">
              <p className="text-title-card text-gray-900">{c.title}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <ArtifactChip artifactKey={c.artifact.key} />
                {c.selected && (
                  <span className="inline-flex h-7 items-center gap-1.5 rounded-sm bg-gray-900 px-2.5 text-caption font-semibold text-white">
                    <Signpost aria-hidden size={13} strokeWidth={2.25} />
                    Selected by the Director
                  </span>
                )}
              </div>
            </div>
          </div>
          {c.question && c.question !== c.title && <p className="mt-3 text-body-sm text-gray-700">{c.question}</p>}
          <dl className="mt-4 space-y-3">
            <Part label="Expected information gain" text={c.expectedGain} />
            <Part label="Could change the interpretation because" text={c.couldChange} />
          </dl>
          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 border-t border-gray-200 pt-3">
            {c.feasible != null && (
              <Pill tone={c.feasible ? "good" : "warn"} icon={c.feasible ? CircleCheck : TriangleAlert}>
                {c.feasible ? "Fits the current engine contract" : "Needs a contract revision (human approval)"}
              </Pill>
            )}
            {c.engineCheck && (
              <Pill tone={c.engineCheck.valid ? "good" : "warn"}>
                Dry run {c.engineCheck.valid ? "valid" : "invalid"}
                {c.engineCheck.n != null ? ` · n = ${c.engineCheck.n.toLocaleString("en-US")}` : ""}
              </Pill>
            )}
            {c.hypothesisCodes.length > 0 && <Pill>Tests {c.hypothesisCodes.join(", ")}</Pill>}
            {c.cost && <Pill>Cost: {c.cost}</Pill>}
          </div>
          {c.experimentId && experimentKeys[c.experimentId] && (
            <p className="mt-3 flex flex-wrap items-center gap-2 text-caption text-gray-700">
              Ran as <ArtifactChip artifactKey={experimentKeys[c.experimentId]} />
            </p>
          )}
        </section>
      ))}
      {cs.length === 1 && (
        <p className="self-center rounded-md p-4 text-body-sm text-gray-700 outline-1 outline-dashed outline-gray-300">
          Only one candidate so far. The planner must propose at least two before the Director can choose.
        </p>
      )}
    </div>
  );
}

// --- 7 · Selection -----------------------------------------------------------

export function SelectionBody({ sels }: { sels: SelectionView[] }) {
  return (
    <ol className="divide-y divide-gray-200">
      {sels.map((s) => (
        <li key={s.artifact.key} className="py-5 first:pt-0 last:pb-0">
          <p className={lead}>
            {s.label ? `Candidate ${s.label}` : "A candidate"}
            {s.title ? `: ${s.title}` : " was selected"}
          </p>
          {s.rationale && <p className={`mt-2 ${support}`}>{s.rationale}</p>}
          <dl className="mt-4 grid gap-4 sm:grid-cols-[2fr_1fr]">
            <Field label="Alternatives considered">
              <span className="text-body-sm text-gray-700">{s.alternatives ?? "Not stated in the artifact."}</span>
            </Field>
            <Field label="Rule and evidence">
              <span className="flex flex-wrap items-center gap-2">
                {s.ruleApplied && <span className="font-mono font-semibold">{s.ruleApplied}</span>}
                {s.candidateKey && <ArtifactChip artifactKey={s.candidateKey} />}
                {s.basedOnRun && <span className="font-mono text-caption text-gray-700">run {s.basedOnRun.slice(0, 8)}</span>}
              </span>
            </Field>
          </dl>
        </li>
      ))}
    </ol>
  );
}

// --- 8 · New evidence --------------------------------------------------------

export function NewEvidenceBody({ followUps }: { followUps: Discovery["followUps"] }) {
  return (
    <ol className="divide-y divide-gray-200">
      {followUps.map(({ experiment: e, evidence, critiques }) => (
        <li key={e.experimentId} className="py-6 first:pt-0 last:pb-0">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <ArtifactChip artifactKey={e.spec.key} />
            <span className="text-body-sm text-gray-700">{e.population.join(" · ")}</span>
          </div>
          {e.question && <p className={`${support} mb-4 text-gray-900`}>&ldquo;{e.question}&rdquo;</p>}
          {evidence ? (
            <EvidenceBody ev={evidence} />
          ) : (
            <p className="text-body-sm text-gray-700 italic">
              The spec exists but there is no result.json yet: the run is in progress, awaiting approval, or failed.
            </p>
          )}
          {critiques.map((c) => (
            <div key={c.artifact.key} className="mt-5 flex flex-wrap items-start gap-3 rounded-md bg-gray-50 p-4">
              <TypeBadge type="UNCERTAINTY" />
              <div className="min-w-0 flex-1">
                <p className="text-body font-semibold text-gray-900">
                  Critic verdict: <span className="font-mono">{c.verdict ?? "—"}</span>
                </p>
                {c.rationale && <p className="mt-1 line-clamp-3 text-body-sm text-gray-700">{c.rationale}</p>}
              </div>
              <ArtifactChip artifactKey={c.artifact.key} />
            </div>
          ))}
        </li>
      ))}
    </ol>
  );
}

// --- 9 · Updated decision ----------------------------------------------------

export function DecisionBody({ ds }: { ds: DecisionView[] }) {
  const [latest, ...earlier] = [...ds].reverse();
  if (!latest) return null;
  return (
    <>
      <p className={lead}>{latest.interpretation}</p>
      {latest.nextTest && (
        <div className="mt-4 rounded-md bg-gray-900 p-5 text-white">
          <p className="text-caption font-semibold text-gray-300">Next test{latest.ruleApplied ? ` · rule ${latest.ruleApplied}` : ""}</p>
          <p className="mt-1 text-h4 text-white">{latest.nextTest}</p>
        </div>
      )}
      <dl className="mt-5 grid gap-4 sm:grid-cols-2">
        {latest.rationale && <Part label="Rationale" text={latest.rationale} />}
        {latest.uncertainty && <Part label="Uncertainty" text={latest.uncertainty} />}
        {latest.limitations && <Part label="Limitations" items={latest.limitations.split("\n").filter(Boolean)} />}
        {latest.hypothesisStatus && (
          <Field label="Hypothesis status">
            <span className="font-mono">{latest.hypothesisStatus}</span>
          </Field>
        )}
      </dl>
      {earlier.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-caption text-gray-700">
          Earlier decisions:
          {earlier.map((d) => (
            <ArtifactChip key={d.artifact.key} artifactKey={d.artifact.key} />
          ))}
        </div>
      )}
    </>
  );
}
