"use client";

import { useState, type ReactNode } from "react";
import { ArrowDown, ArrowRight, CircleCheck, Cpu, Database, RefreshCcw, TriangleAlert, UserCheck } from "lucide-react";
import type {
  StagePart,
  CapabilityChangeView,
  CritiqueView,
  DecisionView,
  DiscoveryRunViewModel,
  EvidenceView,
  ExperimentView,
  FollowUpView,
  HypothesisView,
  ProposalView,
  ReviewView,
  ScientificUpdateView,
} from "@/lib/discovery/types";
import ForestPlot from "./ForestPlot";
import InteractionPlot from "./InteractionPlot";
import { ArtifactChip, Awaiting, Inline, Pill, plain, signed, StatusTag, TypeMark, useDiscoveryUi, VerbatimList } from "./primitives";

// Every value below comes from the DiscoveryRunViewModel; components carry layout and connective copy only.

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-caption font-semibold text-gray-700">{label}</dt>
      <dd className="mt-1 text-body [overflow-wrap:anywhere] text-gray-900">{children}</dd>
    </div>
  );
}

function Section({ label, count, children, className = "" }: { label: string; count?: number; children: ReactNode; className?: string }) {
  return (
    <div className={`min-w-0 border-t border-gray-200 pt-4 ${className}`}>
      <p className="mb-2 flex items-baseline gap-2 text-body-sm font-semibold text-gray-900">
        {label}
        {count != null && <span className="text-caption font-medium text-gray-700 tabular">{count}</span>}
      </p>
      {children}
    </div>
  );
}

function Details({ summary, children }: { summary: string; children: ReactNode }) {
  return (
    <details className="group mt-5 border-t border-gray-200 pt-4">
      <summary className="cursor-pointer list-none text-body-sm font-semibold text-blue-600 hover:text-blue-700 [&::-webkit-details-marker]:hidden">
        <span className="group-open:hidden">Show {summary}</span>
        <span className="hidden group-open:inline">Hide {summary}</span>
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  );
}

const lead = "text-h3 text-balance text-gray-900";
const support = "text-[17px] leading-7 text-gray-700 max-w-[68ch]";
const when = (iso: string | null) => {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC";
};

/** One section of a grouped stage (e.g. decision · engine capability · human approval), or its pending state. */
export function StagePartSection({
  part,
  first,
  listening,
  children,
}: {
  part: StagePart;
  first: boolean;
  listening: boolean;
  children: ReactNode;
}) {
  return (
    <section aria-label={part.title} className={first ? "" : "mt-8 border-t border-gray-200 pt-6"}>
      <h3 className="mb-4 flex items-center gap-2.5 text-h4 text-gray-900">
        <TypeMark type={part.type} />
        {part.title}
      </h3>
      {part.recorded ? children : <Awaiting {...part.awaiting} listening={listening} />}
    </section>
  );
}

// --- 1 · Research question ---------------------------------------------------

export function QuestionBody({ q }: { q: DiscoveryRunViewModel["question"] }) {
  const { isRevealed } = useDiscoveryUi();
  return (
    <>
      <p className="max-w-[68ch] text-[18px] leading-7 font-medium text-gray-900">{q.text ?? "The research question is missing from the artifacts."}</p>
      <p className="mt-3 text-body-sm text-gray-700">
        {[...q.population, ...(q.datasetVersion ? [q.datasetVersion] : [])].map((p, i) => (
          <span key={p}>
            {i > 0 && <span className="mx-2 text-gray-300">·</span>}
            <span className={p === q.datasetVersion ? "font-mono" : ""}>{p}</span>
          </span>
        ))}
      </p>
      {q.hypotheses.length > 0 && (
        <dl className="mt-5 space-y-3 border-t border-gray-200 pt-4">
          {q.hypotheses.map((h) => (
            <div key={h.code} className="grid grid-cols-[2.5rem_minmax(0,1fr)] gap-x-3">
              <dt className="pt-0.5 text-body font-bold text-gray-900 tabular">{h.code}</dt>
              <dd className="min-w-0">
                <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="text-body text-gray-900">{h.title ? `${h.title}: ` : ""}{h.claim}</span>
                </span>
                <span className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-body-sm text-gray-700">
                  {/* A status set by a later artifact appears only once that artifact has. */}
                  {!h.statusSource || isRevealed(h.statusSource) ? (
                    <>
                      <StatusTag status={h.status} />
                      {h.statusSource && <span>in {h.statusSource}</span>}
                      {h.assessment && <span className="basis-full">{h.assessment}</span>}
                    </>
                  ) : (
                    <span className="italic">Pre-registered · not yet evaluated in this run</span>
                  )}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      )}
    </>
  );
}

// --- 2 · Initial evidence (first experiment) -----------------------------------

export function ExperimentSpec({ exp }: { exp: ExperimentView }) {
  return (
    <>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-3">
        <Field label="Exposure">{exp.exposure ?? "—"}</Field>
        <Field label="Outcomes">{exp.outcomes.join(", ") || "—"}</Field>
        <Field label="Adjusted for">{exp.covariates.join(", ") || "—"}</Field>
        <Field label="Method">{exp.method ?? "—"}</Field>
        <Field label="Uncertainty">{exp.uncertainty ?? "—"}</Field>
        <Field label="Population">{exp.population.join(" · ") || "—"}</Field>
      </dl>
      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-gray-200 pt-4">
        <StatusTag status={exp.status} />
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
        <StatusTag status={exp.reviewStatus} />
        {exp.hypothesisIds.length > 0 && <Pill>Tests {exp.hypothesisIds.join(", ")}</Pill>}
      </div>
    </>
  );
}

export function BaselineBody({ exp, ev }: { exp: ExperimentView; ev: EvidenceView | null }) {
  return (
    <>
      {exp.question && <p className={`${support} mb-2 text-gray-900`}>&ldquo;{exp.question}&rdquo;</p>}
      <p className="text-body-sm text-gray-700">
        {[exp.exposure, exp.population.join(" · "), exp.method].filter(Boolean).join("  ·  ")}
      </p>
      {ev ? <EvidenceBody ev={ev} /> : <p className="mt-4 text-body-sm text-gray-700 italic">The experiment has no result yet.</p>}
      <Details summary="specification and reproducibility">
        <ExperimentSpec exp={exp} />
      </Details>
    </>
  );
}

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
      {headline && <p className={`mt-5 ${lead}`}>{headline}</p>}
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
        <div className="mt-6 rounded-md bg-gray-50 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <StatusTag status={ev.rankingStatus} />
            {ev.rankingSentence && <p className="text-h4 text-gray-900">{ev.rankingSentence}</p>}
          </div>
          {ev.pairs ? (
            <>
              <p className="mt-2 text-body-sm text-gray-700">
                {ev.pairs.resolved} of {ev.pairs.total} paired differences exclude zero{ev.pairs.adjustment ? ` (${ev.pairs.adjustment})` : ""}.
              </p>
              <table className="mt-3 w-full text-left text-body-sm">
                <caption className="sr-only">Paired differences between outcomes, in weekday minutes, with adjusted intervals</caption>
                <thead className="sr-only">
                  <tr>
                    <th scope="col">Pair</th>
                    <th scope="col">Difference and interval</th>
                    <th scope="col" className="hidden sm:table-cell">
                      Zero
                    </th>
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
            </>
          ) : (
            ev.rankingRule && <p className="mt-2 text-body-sm text-gray-700">{ev.rankingRule}.</p>
          )}
        </div>
      )}

      <div className="mt-4 max-w-[72ch] space-y-1.5 text-body-sm text-gray-700">
        <p>
          95% pointwise intervals{ev.covarianceMethod ? ` · ${ev.covarianceMethod}` : ""}: an approximation, not the full ENUT complex-survey variance.
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

// --- 3 / 11 · Scientific critique ----------------------------------------------

function EvidenceCited({ items }: { items: CritiqueView["evidence"] }) {
  const [open, setOpen] = useState(false);
  const shown = open ? items : items.slice(0, 2);
  return (
    <Section label="Evidence cited" count={items.length}>
      <ul className="space-y-2.5">
        {shown.map((e, i) => (
          <li key={i} className="text-body-sm text-gray-700">
            <span className={`mr-2 font-semibold ${/INFERENCE/.test(e.kind) ? "text-blue-700" : "text-gray-900"}`}>{e.label}</span>
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
    </Section>
  );
}

export function CritiqueBody({ c, earlier, handedOn }: { c: CritiqueView; earlier: CritiqueView[]; handedOn: boolean }) {
  // The verdict, its reason and the open questions carry the story; the critic's full review stays one click away.
  const [full, setFull] = useState(false);
  const details = c.pointEstimateObservations.length + c.formalInference.length + c.evidence.length + c.limitations.length + c.uncertainties.length + c.unsupported.length;
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <StatusTag status={c.verdict} large />
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
      <Section label="What it leaves open" count={c.openQuestions.length} className="mt-5">
        <VerbatimList items={c.openQuestions} initial={c.openQuestions.length} />
        {handedOn && c.openQuestions.length > 0 && (
          <p className="mt-3 inline-flex items-center gap-2 text-body-sm font-semibold text-blue-700">
            <ArrowDown aria-hidden size={15} strokeWidth={2.25} />
            These open questions are the input of the next stage.
          </p>
        )}
      </Section>
      {details > 0 && (
        <button
          type="button"
          onClick={() => setFull((v) => !v)}
          aria-expanded={full}
          className="mt-5 text-body-sm font-semibold text-blue-600 hover:text-blue-700"
        >
          {full ? "Hide the critic's full review" : "Show the critic's full review"}
          <span className="ml-1 font-normal text-gray-700">evidence cited, limitations, uncertainties, claims it rejects</span>
        </button>
      )}
      {full && (
        <div className="stage-enter">
          {(c.pointEstimateObservations.length > 0 || c.formalInference.length > 0) && (
            <div className="mt-5 grid gap-x-8 gap-y-4 sm:grid-cols-2">
              <Section label="Point-estimate observations">
                <VerbatimList items={c.pointEstimateObservations} initial={c.pointEstimateObservations.length} clamp={false} />
              </Section>
              <Section label="Formal inference">
                <VerbatimList items={c.formalInference} initial={c.formalInference.length} clamp={false} />
              </Section>
            </div>
          )}
          <div className="mt-5 grid gap-x-8 gap-y-5 sm:grid-cols-2">
            {c.evidence.length > 0 && (
              <div className="sm:col-span-2">
                <EvidenceCited items={c.evidence} />
              </div>
            )}
            <Section label="Limitations" count={c.limitations.length}>
              <VerbatimList items={c.limitations} />
            </Section>
            <Section label="Uncertainties" count={c.uncertainties.length}>
              <VerbatimList items={c.uncertainties} />
            </Section>
            <Section label="Interpretations the critic rejects" count={c.unsupported.length} className="sm:col-span-2">
              <VerbatimList items={c.unsupported} />
            </Section>
          </div>
        </div>
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

// --- 4 · Hypotheses + human review --------------------------------------------

export function ReviewPanel({ rv, labelled = true }: { rv: ReviewView; labelled?: boolean }) {
  return (
    <section aria-label={`Human review ${rv.id}`} className={`${labelled ? "mt-5" : ""} rounded-md p-4 ring-[1.5px] ring-gray-900 ring-inset`}>
      <div className="flex flex-wrap items-center gap-3">
        {labelled && (
          <span className="inline-flex items-center gap-2 text-body font-semibold text-gray-900">
            <UserCheck aria-hidden size={18} strokeWidth={2} />
            Human review
          </span>
        )}
        <StatusTag status={rv.decision} />
        <ArtifactChip artifactKey={rv.artifact.key} />
      </div>
      <p className="mt-2 text-body-sm text-gray-700">
        {[rv.reviewer, when(rv.recordedAt), rv.recordedBy].filter(Boolean).join(" · ")}
      </p>
      {rv.scope && <p className="mt-2 max-w-[72ch] text-body-sm text-gray-900">{rv.scope}</p>}
      {rv.constraints.length > 0 && (
        <Section label="Constraints set by the reviewer" count={rv.constraints.length} className="mt-4">
          <VerbatimList items={rv.constraints} initial={rv.constraints.length} clamp={false} />
        </Section>
      )}
      {rv.notEndorsed.length > 0 && (
        <Section label="Not endorsed by the reviewer" count={rv.notEndorsed.length} className="mt-4">
          <ul className="space-y-2.5">
            {rv.notEndorsed.map((n, i) => (
              <li key={i} className="text-body-sm text-gray-700">
                &ldquo;{n.text}&rdquo;
                {n.reason && <span className="mt-0.5 block font-semibold text-gray-900">{n.reason}</span>}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </section>
  );
}

export function HypothesesBody({ hs, reviews }: { hs: HypothesisView[]; reviews: ReviewView[] }) {
  return (
    <>
      <p className={`${support} mb-4`}>Falsifiable explanations proposed from the critique. They are to be tested, not findings.</p>
      <ol className="grid gap-3 lg:grid-cols-1">
        {hs.map((h) => (
          <li key={h.artifact.key} className="rounded-md p-4 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-blue-500">
            <div className="flex flex-wrap items-center gap-2">
              <ArtifactChip artifactKey={h.artifact.key} />
              <StatusTag status={h.status} />
              <span className="text-caption font-semibold text-blue-700">To be tested</span>
            </div>
            {h.question && <p className="mt-3 text-h4 text-balance text-gray-900">{h.question}</p>}
            {h.claim && <p className="mt-1 max-w-[72ch] text-body text-gray-700">{h.claim}</p>}
            <dl className="mt-4 grid gap-4 sm:grid-cols-2">
              {h.expectedDirection && (
                <Field label="Expected direction (a hypothesis, not evidence)">
                  <span className="font-mono text-body-sm">{h.expectedDirection}</span>
                </Field>
              )}
              {h.requiredVariables.length > 0 && (
                <Field label="Required variables">
                  <span className="flex flex-wrap gap-1.5">
                    {h.requiredVariables.map((v) => (
                      <span key={v} className="rounded-sm bg-gray-50 px-1.5 font-mono text-caption text-gray-700">
                        {v}
                      </span>
                    ))}
                  </span>
                </Field>
              )}
            </dl>
            {(h.supportIf || h.contradictIf || h.observed.length > 0 || h.inference.length > 0) && (
              <Details summary="test criteria and motivation">
                <dl className="grid gap-4 sm:grid-cols-2">
                  {h.supportIf && <Field label="Would be supported if">{<span className="text-body-sm">{h.supportIf}</span>}</Field>}
                  {h.contradictIf && <Field label="Would be contradicted if">{<span className="text-body-sm">{h.contradictIf}</span>}</Field>}
                  <Field label="Observed evidence">
                    <VerbatimList items={h.observed} clamp={false} initial={h.observed.length} />
                  </Field>
                  <Field label="Scientific inference">
                    <VerbatimList items={h.inference} clamp={false} initial={h.inference.length} />
                  </Field>
                </dl>
              </Details>
            )}
          </li>
        ))}
      </ol>
      {reviews.map((rv) => (
        <ReviewPanel key={rv.artifact.key} rv={rv} />
      ))}
    </>
  );
}

// --- 5 · Candidate experiments --------------------------------------------------

function ProposalCard({ p }: { p: ProposalView }) {
  const { isRevealed } = useDiscoveryUi();
  const ranAs = p.ranAs && isRevealed(p.ranAs) ? p.ranAs : null;
  const current = p.current && isRevealed(p.current.asOf) ? p.current : null;
  return (
    <li className={`flex flex-col rounded-md p-4 ${p.formal ? "bg-white ring-1 ring-blue-800 ring-inset" : "bg-gray-50 ring-1 ring-gray-200 ring-inset"}`}>
      <div className="flex flex-wrap items-center gap-2">
        <ArtifactChip artifactKey={p.artifact.key} />
        <StatusTag status={p.role} />
        {ranAs && <span className="text-caption font-semibold text-blue-800">Ran as {ranAs}</span>}
      </div>
      {p.question && <p className="mt-3 text-title-card text-gray-900">{p.question}</p>}
      {p.estimand && (
        <p className="mt-1 text-body-sm text-gray-700">
          <span className="font-semibold text-gray-900">Estimand: </span>
          {p.estimand}
        </p>
      )}
      <dl className="mt-3 space-y-3">
        {p.infoGain && (
          <Field label={`Expected information gain · ${p.infoGain.level}`}>
            <span className="text-body-sm text-gray-700">{p.infoGain.reason}</span>
          </Field>
        )}
        <Field label="Feasibility">
          <span className="flex flex-wrap items-center gap-2 text-body-sm">
            <span className="text-gray-700">At planning</span>
            <StatusTag status={p.feasibilityAtPlanning} />
            {current && (
              <>
                <ArrowRight aria-hidden size={14} className="text-gray-500" />
                <span className="text-gray-700">{current.asOf} audit</span>
                <span className="inline-flex items-center gap-1 font-semibold text-gray-900">
                  {current.executable ? (
                    <CircleCheck aria-hidden size={14} className="text-green-600" />
                  ) : (
                    <TriangleAlert aria-hidden size={14} className="text-yellow-700" />
                  )}
                  {current.executable ? "executable" : `missing ${current.missing.join(", ")}`}
                </span>
              </>
            )}
          </span>
        </Field>
      </dl>
      {p.limitations.length > 0 && (
        <div className="mt-3 border-t border-gray-200 pt-3">
          <VerbatimList items={p.limitations} initial={p.formal ? 1 : p.limitations.length} />
        </div>
      )}
    </li>
  );
}

export function ProposalsBody({ ps }: { ps: ProposalView[] }) {
  const formal = ps.filter((p) => p.formal);
  const other = ps.filter((p) => !p.formal);
  return (
    <>
      <p className={`${support} mb-4`}>
        A formal test estimates the difference between groups with its own interval. A separate subgroup model only describes one group and
        cannot establish a difference.
      </p>
      {formal.length > 0 && (
        <Section label="Formal tests" count={formal.length}>
          <ul className="grid gap-3 md:grid-cols-2">
            {formal.map((p) => (
              <ProposalCard key={p.artifact.key} p={p} />
            ))}
          </ul>
        </Section>
      )}
      {other.length > 0 && (
        <Section label="Exploratory" count={other.length} className="mt-5">
          <ul className="grid gap-3 md:grid-cols-2">
            {other.map((p) => (
              <ProposalCard key={p.artifact.key} p={p} />
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}

// --- 6 · Director decision ------------------------------------------------------

export function DecisionBody({ d }: { d: DecisionView }) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <StatusTag status={d.status} large />
        <ArtifactChip artifactKey={d.artifact.key} />
        <span className="text-body-sm text-gray-700">{[when(d.createdAt), d.model].filter(Boolean).join(" · ")}</span>
      </div>
      <dl className="mt-5 grid gap-4 sm:grid-cols-2">
        <Field label="Preferred (most to learn)">
          <span className="flex flex-wrap items-center gap-2">{d.preferred?.key ? <ArtifactChip artifactKey={d.preferred.key} /> : (d.preferred?.id ?? "—")}</span>
        </Field>
        <Field label="Best executable now">
          <span className="flex flex-wrap items-center gap-2">
            {d.bestExecutable?.key ? <ArtifactChip artifactKey={d.bestExecutable.key} /> : (d.bestExecutable?.id ?? "—")}
          </span>
        </Field>
      </dl>
      {d.missing.length > 0 && (
        <p className="mt-4 inline-flex flex-wrap items-center gap-2 text-body-sm text-gray-900">
          <Cpu aria-hidden size={16} className="text-blue-700" />
          Blocked by missing engine capability:
          {d.missing.map((m) => (
            <span key={m} className="rounded-sm bg-blue-50 px-1.5 font-mono text-caption text-blue-700">
              {m}
            </span>
          ))}
        </p>
      )}
      {d.rationale && <p className={`mt-4 ${support}`}>{d.rationale}</p>}
      {d.nextAction && (
        <div className="mt-4 rounded-md bg-gray-900 p-4 text-white">
          <p className="text-caption font-semibold text-gray-300">Next action recorded by the Director</p>
          <p className="mt-1 text-body text-white">{d.nextAction}</p>
        </div>
      )}
      {d.alternatives.length > 0 && (
        <Details summary={`${d.alternatives.length} alternatives considered`}>
          <ul className="space-y-3">
            {d.alternatives.map((a) => (
              <li key={a.id} className="text-body-sm text-gray-700">
                {a.key ? <ArtifactChip artifactKey={a.key} className="mr-2" /> : <span className="mr-2 font-mono">{a.id}</span>}
                {a.reason}
              </li>
            ))}
          </ul>
        </Details>
      )}
    </>
  );
}

// --- 7 · Engine capability change -------------------------------------------------

export function CapabilityBody({ changes }: { changes: CapabilityChangeView[] }) {
  const supported = changes.find((c) => c.supported.length)?.supported ?? [];
  return (
    <>
      <p className={`${support} mb-4`}>
        The Director&rsquo;s preferred experiment needed a capability the engine did not have. The capability audits recorded by consecutive
        decisions show when it changed.
      </p>
      <ul className="space-y-3">
        {changes.map((c) => (
          <li key={`${c.from.id}-${c.to.id}`} className="rounded-md bg-blue-50 p-4">
            <p className="flex flex-wrap items-center gap-2 text-body-sm text-gray-900">
              Between <ArtifactChip artifactKey={c.from.key} /> and <ArtifactChip artifactKey={c.to.key} />
            </p>
            <ul className="mt-2 space-y-1">
              {c.gained.map((g) => (
                <li key={g} className="flex flex-wrap items-center gap-2 text-body text-gray-900">
                  <span className="font-mono text-body-sm">{g}</span>
                  <span className="text-gray-700">not supported</span>
                  <ArrowRight aria-hidden size={15} className="text-blue-700" />
                  <span className="font-semibold">supported</span>
                </li>
              ))}
              {c.lost.map((g) => (
                <li key={g} className="flex flex-wrap items-center gap-2 text-body text-gray-900">
                  <span className="font-mono text-body-sm">{g}</span>
                  <span className="text-gray-700">supported</span>
                  <ArrowRight aria-hidden size={15} className="text-blue-700" />
                  <span className="font-semibold">not supported</span>
                </li>
              ))}
            </ul>
            {c.schemaBefore && c.schemaAfter && (
              <p className="mt-2 font-mono text-caption text-gray-700">
                schema sha256 {c.schemaBefore.slice(0, 12)}… → {c.schemaAfter.slice(0, 12)}…
              </p>
            )}
            {!c.engineChanged && (
              <p className="mt-2 text-body-sm text-gray-900">
                The engine files hash the same in both audits (schema, method registry, capability export): the capability audit changed,
                not the engine.
              </p>
            )}
            <p className="mt-2 text-body-sm text-gray-700">
              {c.humanReview ? (
                <>
                  Human review: <ArtifactChip artifactKey={c.humanReview} />
                </>
              ) : (
                `No human review artifact records this ${c.engineChanged ? "engine" : "audit"} change.`
              )}
            </p>
          </li>
        ))}
      </ul>
      {supported.length > 0 && (
        <Details summary="current engine capabilities">
          <ul className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
            {supported.map((s) => (
              <li key={s.name} className="flex items-center gap-2 text-body-sm text-gray-700">
                {s.supported ? (
                  <CircleCheck aria-hidden size={14} className="shrink-0 text-green-600" />
                ) : (
                  <span aria-hidden className="size-3.5 shrink-0 rounded-full border border-gray-400" />
                )}
                <span className="font-mono text-caption">{s.name}</span>
                <span className="sr-only">{s.supported ? "supported" : "not supported"}</span>
              </li>
            ))}
          </ul>
        </Details>
      )}
    </>
  );
}

// --- 8 · Decision history ---------------------------------------------------------

export function DecisionHistory({ ds, changes, reviews = [] }: { ds: DecisionView[]; changes: CapabilityChangeView[]; reviews?: ReviewView[] }) {
  return (
    <>
      <p className={`${support} mb-4`}>Every decision is kept. Each re-run is a new artifact; none replaces the one before it.</p>
      <ol className="relative space-y-0">
        {ds.map((d, i) => {
          const change = changes.find((c) => c.to.id === d.id);
          return (
            <li key={d.artifact.key}>
              {change && (
                <p className="my-2 ml-[7px] flex flex-wrap items-center gap-2 border-l-2 border-dashed border-blue-300 py-1 pl-5 text-body-sm text-blue-700">
                  <Cpu aria-hidden size={15} />
                  {change.engineChanged ? "Engine capability changed" : "Capability audit changed (engine unchanged)"}:{" "}
                  <span className="font-mono">{[...change.gained, ...change.lost].join(", ")}</span>
                </p>
              )}
              <div className={`grid grid-cols-[1rem_minmax(0,1fr)] gap-x-4 py-2.5 ${i > 0 ? "border-t border-gray-200" : ""}`}>
                <span aria-hidden className={`mt-1.5 size-3 rounded-full ${i === ds.length - 1 ? "bg-gray-900" : "border-2 border-gray-900 bg-white"}`} />
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <ArtifactChip artifactKey={d.artifact.key} />
                    <StatusTag status={d.status} />
                    <span className="text-body-sm text-gray-700 tabular">{when(d.createdAt)}</span>
                  </div>
                  <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-body-sm text-gray-700">
                    Preferred <span className="font-mono text-gray-900">{d.preferred?.id ?? "—"}</span>
                    <span className="text-gray-300">·</span>
                    best executable <span className="font-mono text-gray-900">{d.bestExecutable?.id ?? "—"}</span>
                    {d.codeVersion && (
                      <>
                        <span className="text-gray-300">·</span>
                        code <span className="font-mono">{d.codeVersion.slice(0, 7)}</span>
                      </>
                    )}
                  </p>
                  {d.approvedBy.map((k) => (
                    <p key={k} className="mt-1.5 flex flex-wrap items-center gap-2 text-body-sm font-semibold text-gray-900">
                      <UserCheck aria-hidden size={15} />
                      Approved by
                      <ArtifactChip artifactKey={k} />
                    </p>
                  ))}
                  {/* The first decision's rationale is shown in full above; each reassessment keeps its own, in the Director's words. */}
                  {i > 0 && (d.rationale || d.alternatives.length > 0) && (
                    <details className="group mt-1.5">
                      <summary className="cursor-pointer list-none text-body-sm font-semibold text-blue-600 hover:text-blue-700 [&::-webkit-details-marker]:hidden">
                        <span className="group-open:hidden">Show the Director&rsquo;s rationale</span>
                        <span className="hidden group-open:inline">Hide the Director&rsquo;s rationale</span>
                      </summary>
                      {d.rationale && <p className={`mt-2 ${support}`}>{d.rationale}</p>}
                      {reviews
                        .filter((rv) => d.approvedBy.includes(rv.artifact.key) && rv.notEndorsed.length > 0)
                        .map((rv) => (
                          <p key={rv.artifact.key} className="mt-2 flex flex-wrap items-center gap-2 text-body-sm font-semibold text-gray-900">
                            <TriangleAlert aria-hidden size={15} className="text-yellow-700" />
                            Parts of this rationale are not endorsed by
                            <ArtifactChip artifactKey={rv.artifact.key} />
                            (see Human approval below).
                          </p>
                        ))}
                      {d.alternatives.length > 0 && (
                        <ul className="mt-2 space-y-2">
                          {d.alternatives.map((a) => (
                            <li key={a.id} className="text-body-sm text-gray-700">
                              {a.key ? <ArtifactChip artifactKey={a.key} className="mr-2" /> : <span className="mr-2 font-mono">{a.id}</span>}
                              {a.reason}
                            </li>
                          ))}
                        </ul>
                      )}
                    </details>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </>
  );
}

// --- 9 · Human approval -------------------------------------------------------------

export function ApprovalBody({ rvs }: { rvs: ReviewView[] }) {
  return (
    <>
      {rvs.map((rv) => (
        <div key={rv.artifact.key}>
          <div className="flex flex-wrap items-center gap-3">
            <StatusTag status={rv.decision} large />
            <ArtifactChip artifactKey={rv.artifact.key} />
          </div>
          <p className="mt-2 text-body-sm text-gray-700">{[rv.reviewer, when(rv.recordedAt), rv.recordedBy].filter(Boolean).join(" · ")}</p>
          {rv.approvedExperiment && (
            <dl className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Authorized experiment">{rv.approvedExperiment.experimentId ?? "—"}</Field>
              <Field label="Engine">{rv.approvedExperiment.engine ?? "—"}</Field>
              {rv.approvedExperiment.model && (
                <div className="sm:col-span-2">
                  <Field label="Model">
                    <span className="font-mono text-body-sm">{rv.approvedExperiment.model}</span>
                  </Field>
                </div>
              )}
            </dl>
          )}
          {rv.scope && <p className={`mt-4 ${support}`}>{rv.scope}</p>}
          {rv.constraints.length > 0 && (
            <Section label="Interpretation constraints" count={rv.constraints.length} className="mt-4">
              <VerbatimList items={rv.constraints} initial={rv.constraints.length} clamp={false} />
            </Section>
          )}
          {rv.notEndorsed.length > 0 && (
            <Section label="Not endorsed by the reviewer" count={rv.notEndorsed.length} className="mt-4">
              <ul className="space-y-2.5">
                {rv.notEndorsed.map((n, i) => (
                  <li key={i} className="text-body-sm text-gray-700">
                    &ldquo;{n.text}&rdquo;
                    {n.reason && <span className="mt-0.5 block font-semibold text-gray-900">{n.reason}</span>}
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </div>
      ))}
    </>
  );
}

// --- 10 · New experiment --------------------------------------------------------------

export function FollowUpBody({ fus }: { fus: FollowUpView[] }) {
  return (
    <ol className="divide-y divide-gray-200">
      {fus.map((f) => {
        const e = f.experiment;
        return (
          <li key={e.experimentId} className="py-6 first:pt-0 last:pb-0">
            {e.question && <p className={`${support} mb-2 text-gray-900`}>&ldquo;{e.question}&rdquo;</p>}
            <div className="flex flex-wrap items-center gap-2 text-body-sm text-gray-700">
              {f.authorizedBy.map((k) => (
                <span key={k} className="inline-flex items-center gap-2">
                  Authorized by <ArtifactChip artifactKey={k} />
                </span>
              ))}
              {f.proposalKey && (
                <span className="inline-flex items-center gap-2">
                  from <ArtifactChip artifactKey={f.proposalKey} />
                </span>
              )}
            </div>
            {f.interactions.map((i) => (
              <div key={`${i.outcome}-${i.moderator}`}>
                <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
                  <Field label="Outcome">
                    <span className="font-mono text-body-sm">{i.outcome}</span>
                  </Field>
                  <Field label="Exposure">
                    <span className="font-mono text-body-sm">{i.exposure}</span>
                  </Field>
                  <Field label="Moderator">
                    <span className="font-mono text-body-sm">{i.moderator}</span>
                  </Field>
                  <Field label="Reference group">{i.referenceLevel}</Field>
                  <Field label="Comparison group">{i.comparisonLevel}</Field>
                  <Field label="Analysis n">{e.sampleSize != null ? e.sampleSize.toLocaleString("en-US") : "—"}</Field>
                </dl>
                <InteractionPlot i={i} />
                {i.interpretation && <p className={`mt-4 ${support} text-gray-900`}>{i.interpretation}</p>}
              </div>
            ))}
            {f.evidence?.rankingStatus && (
              <p className="mt-4 flex flex-wrap items-center gap-2 text-body-sm text-gray-700">
                Ranking <StatusTag status={f.evidence.rankingStatus} />
                {f.evidence.rankingRule && <span>{f.evidence.rankingRule}.</span>}
              </p>
            )}
            {!f.interactions.length && f.evidence && <EvidenceBody ev={f.evidence} />}
            {!f.evidence && <p className="mt-4 text-body-sm text-gray-700 italic">Experiment not executed: the spec exists but there is no result yet.</p>}
            <Details summary="specification and reproducibility">
              <ExperimentSpec exp={e} />
            </Details>
          </li>
        );
      })}
    </ol>
  );
}

// --- 12 · Scientific update (the closing moment) ----------------------------------------

export function UpdateHero({ us }: { us: ScientificUpdateView[] }) {
  return (
    <div className="space-y-8">
      {us.map((u) => (
        <div key={`${u.critiqueKey}-${u.hypothesisId}`}>
          <p className="text-body text-blue-100">
            {u.protocolId && <span className="font-semibold text-white">{u.protocolId}</span>}
            {u.title && <span className="text-white"> · {u.title}</span>}
            {u.hypothesisId && <span> · {u.hypothesisId}</span>}
          </p>
          {u.question && <p className="mt-1 max-w-[60ch] text-h3 text-balance text-white">{u.question}</p>}
          <div className="mt-6 grid items-center gap-4 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
            <div className="rounded-md p-4 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-blue-300">
              <p className="text-caption font-semibold text-blue-100">Before {u.experimentId ?? "the experiment"}</p>
              <p className="mt-2 font-mono text-[32px] leading-10 font-semibold tracking-[-0.01em] [overflow-wrap:anywhere] text-white">{u.previous.code}</p>
            </div>
            <div className="flex items-center justify-center gap-2 text-body-sm font-semibold text-blue-100">
              <span className="max-sm:hidden">
                <ArrowRight aria-hidden size={22} strokeWidth={2} />
              </span>
              <span className="sm:hidden">
                <ArrowDown aria-hidden size={22} strokeWidth={2} />
              </span>
              {u.experimentId}
            </div>
            <div className="rounded-md bg-yellow-400 p-4 text-gray-900">
              <p className="text-caption font-semibold">After {u.experimentId ?? "the experiment"}</p>
              <p className="mt-2 font-mono text-[32px] leading-10 font-semibold tracking-[-0.01em] [overflow-wrap:anywhere]">{u.next.code}</p>
            </div>
          </div>
          {u.reason && <p className="mt-6 max-w-[68ch] text-[18px] leading-7 font-medium text-white">{u.reason}</p>}
          {u.explainer && <p className="mt-2 max-w-[68ch] text-[17px] leading-7 text-blue-100">{u.explainer}</p>}
          <dl className="mt-6 grid gap-x-8 gap-y-4 border-t border-blue-800 pt-5 sm:grid-cols-2">
            {u.tested && (
              <div>
                <dt className="text-caption font-semibold text-blue-100">What was tested</dt>
                <dd className="mt-1 text-body text-white">{u.tested}</dd>
              </div>
            )}
            {u.unresolved && (
              <div>
                <dt className="text-caption font-semibold text-blue-100">What remains unresolved</dt>
                <dd className="mt-1 text-body text-white">{u.unresolved}</dd>
              </div>
            )}
          </dl>
          {u.statusSource && <p className="mt-4 text-caption text-blue-100">Status source: {u.statusSource}</p>}
        </div>
      ))}
    </div>
  );
}
