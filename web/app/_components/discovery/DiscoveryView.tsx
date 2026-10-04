"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowRight, Check, FastForward, Hourglass, LoaderCircle, Pause, Play, RotateCcw, TriangleAlert, UserCheck } from "lucide-react";
import Wordmark from "../Wordmark";
import type { DiscoveryPayload, DiscoveryRunViewModel as Discovery, EvidenceView, Stage } from "@/lib/discovery/types";
import Inspector from "./Inspector";
import Overview from "./Overview";
import { ArtifactChip, Awaiting, DiscoveryUiContext, StageMarker, TYPE, TypeBadge, TypeMark, VerbatimList } from "./primitives";
import {
  ApprovalBody,
  BaselineBody,
  CapabilityBody,
  CritiqueBody,
  DecisionBody,
  DecisionHistory,
  FollowUpBody,
  HypothesesBody,
  ProposalsBody,
  QuestionBody,
  ReviewPanel,
  StagePartSection,
  UpdateHero,
} from "./stages";
import type { StagePart } from "@/lib/discovery/types";

// Console pacing (milliseconds): the agent "works" while its saved artifacts are listed one by one, then its stage is
// revealed and stays alone on screen for a reading beat before the next agent starts. Space pauses, Esc skips to the end.
const FIRST_LINE_MS = 1100;
const LINE_MS = 650;
const REVEAL_MS = 700;
const READ_MS = 2600;
const MAX_LINES = 6;
const LIVE_REFRESH_MS = 3000;
const FRESH_MS = 8000;

/** Index of the first stage after the last recorded one: from there on, every stage waits for agents. */
function tailStart(stages: Stage[]): number {
  let last = -1;
  stages.forEach((s, i) => {
    if (s.recorded) last = i;
  });
  return last + 1;
}

/** The evidence the lab currently stands on: the latest follow-up with a result, else the first experiment. */
function latestEvidence(d: Discovery): EvidenceView | null {
  return [...d.followUps].reverse().find((f) => f.evidence)?.evidence ?? d.baselineEvidence;
}

/** The headline: the latest scientific update in the critic's words, else the latest evidence, else the question. */
function headlineOf(d: Discovery): { text: string; keys: string[] } | null {
  const u = d.updates.at(-1);
  if (u?.changed) return { text: u.changed, keys: [u.critiqueKey, u.experimentKey].filter((k): k is string => Boolean(k)) };
  const ev = latestEvidence(d);
  const sentence = ev ? [ev.sentences[0], ev.rankingSentence].filter(Boolean).join(" ") : "";
  if (ev && sentence) return { text: sentence, keys: [ev.artifact.key] };
  return d.question.text ? { text: d.question.text, keys: d.question.artifactKey ? [d.question.artifactKey] : [] } : null;
}

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Brings a stage into view once it is laid out (a stage that just revealed has no height on the first frame): centred
 * when it fits, else from its top (below the sticky header, via scroll-margin) so its title and lead are on screen.
 */
function scrollToStage(key: string, smooth = true) {
  let tries = 0;
  const attempt = () => {
    const el = document.getElementById(`stage-${key}`);
    const height = el?.getBoundingClientRect().height ?? 0;
    if (el && height > 0) {
      const fits = height <= window.innerHeight - Number.parseFloat(getComputedStyle(el).scrollMarginTop || "0");
      el.scrollIntoView({ behavior: smooth && !reducedMotion() ? "smooth" : "auto", block: fits ? "center" : "start" });
    } else if (tries++ < 30) {
      requestAnimationFrame(attempt);
    }
  };
  requestAnimationFrame(attempt);
}

function defaultSelection(d: Discovery): string | null {
  const recorded = d.stages.filter((s) => s.recorded);
  return recorded.at(-1)?.artifactKeys[0] ?? null;
}

// --- Stage body routing ------------------------------------------------------

/** The body of one section of a grouped stage. */
function PartBody({ part, d }: { part: StagePart; d: Discovery }) {
  const reviews = d.reviews.filter((r) => part.artifactKeys.includes(r.artifact.key));
  switch (part.key) {
    case "hypotheses":
      return <HypothesesBody hs={d.hypotheses} reviews={[]} />;
    case "review":
      return (
        <>
          {reviews.map((rv) => (
            <ReviewPanel key={rv.artifact.key} rv={rv} labelled={false} />
          ))}
        </>
      );
    case "proposals":
      return <ProposalsBody ps={d.proposals} />;
    case "decision":
      return d.decisions[0] ? <DecisionBody d={d.decisions[0]} /> : null;
    case "capability":
      return <CapabilityBody changes={d.capabilityChanges} />;
    case "history":
      return <DecisionHistory ds={d.decisions} changes={d.capabilityChanges} reviews={d.reviews} />;
    case "approval":
      return <ApprovalBody rvs={reviews} />;
    case "experiment":
      return <FollowUpBody fus={d.followUps} />;
    case "critique": {
      const cs = d.followUps.flatMap((f) => f.critiques);
      return cs[0] ? <CritiqueBody c={cs[0]} earlier={cs.slice(1)} handedOn={false} /> : null;
    }
  }
}

function StageBody({ stage, d, listening }: { stage: Stage; d: Discovery; listening: boolean }) {
  if (stage.parts.length) {
    return (
      <>
        {stage.parts.map((p, i) => (
          <StagePartSection key={p.key} part={p} first={i === 0} listening={listening}>
            <PartBody part={p} d={d} />
          </StagePartSection>
        ))}
      </>
    );
  }
  switch (stage.key) {
    case "question":
      return <QuestionBody q={d.question} />;
    case "baseline":
      return d.baseline ? <BaselineBody exp={d.baseline} ev={d.baselineEvidence} /> : null;
    case "critique":
      return d.baselineCritiques[0] ? (
        <CritiqueBody c={d.baselineCritiques[0]} earlier={d.baselineCritiques.slice(1)} handedOn={d.hypotheses.length > 0} />
      ) : null;
    case "update":
      return <UpdateHero us={d.updates} />;
    default:
      return null;
  }
}

// Stages whose few artifacts read best as header chips; the rest carry chips per item in the body.
const HEADER_CHIPS: Stage["key"][] = ["question", "baseline", "critique", "followup", "update"];

function StageItem({
  stage,
  d,
  shown,
  active,
  fresh,
  animate,
  lineFilled,
  last,
  listening,
}: {
  stage: Stage;
  d: Discovery;
  shown: boolean;
  active: boolean;
  fresh: boolean;
  animate: boolean;
  lineFilled: boolean;
  last: boolean;
  listening: boolean;
}) {
  const headerKeys = HEADER_CHIPS.includes(stage.key) ? stage.artifactKeys.slice(0, /critique|update|followup/.test(stage.key) ? 1 : 2) : [];
  // The scientific update is the closing moment of the run: it sits on the update role's ink, not on white.
  const dark = stage.key === "update" && stage.recorded;
  return (
    <li className="relative grid grid-cols-[32px_minmax(0,1fr)] gap-x-3 pb-5 sm:gap-x-5">
      {!last && (
        <span
          aria-hidden
          className={`absolute top-[50px] -bottom-[18px] left-[15px] sm:top-[58px] sm:-bottom-[26px] ${
            lineFilled ? "w-0.5 bg-blue-500" : "w-0 border-l-2 border-dashed border-gray-300"
          }`}
        />
      )}
      <div className="pt-[18px] sm:pt-[26px]">
        <StageMarker number={stage.number} type={stage.type} recorded={stage.recorded && shown} active={active} />
      </div>

      {shown ? (
        <article
          key={`${stage.key}-shown`}
          id={`stage-${stage.key}`}
          aria-labelledby={`stage-${stage.key}-title`}
          className={`scroll-mt-28 rounded-lg p-5 sm:p-7 ${
            dark ? "bg-blue-900 text-white" : stage.recorded ? "bg-white" : "bg-gray-50 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-gray-300"
          } ${animate ? "stage-enter" : ""} ${fresh ? "fresh" : ""} ${active ? "ring-2 ring-blue-300" : ""}`}
        >
          <p className={`mb-3 text-caption font-semibold tracking-[0.04em] uppercase ${dark ? "text-blue-100" : "text-blue-700"}`}>{stage.agent}</p>
          <header className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-3">
            <span className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
              <h2 id={`stage-${stage.key}-title`} className={`text-h4 sm:text-h3 ${dark ? "text-white" : "text-gray-900"}`}>
                {stage.title}
              </h2>
              {/* A title that already names its role ("Initial evidence", "Scientific update") keeps only the swatch. */}
              <TypeBadge
                type={stage.type}
                className={dark ? "text-blue-100" : ""}
                compact={stage.title.toLowerCase().includes(TYPE[stage.type].label.toLowerCase().slice(0, -2))}
              />
            </span>
            {fresh && <span className="rounded-sm bg-blue-500 px-2 py-0.5 text-micro text-white uppercase">New</span>}
            {stage.recorded && (
              <span className="flex w-full flex-wrap items-center gap-2 sm:ml-auto sm:w-auto">
                {headerKeys.map((k) => (
                  <ArtifactChip key={k} artifactKey={k} />
                ))}
                {!headerKeys.length && (
                  <span className={`text-caption font-medium tabular ${dark ? "text-blue-100" : "text-gray-700"}`}>
                    {stage.artifactKeys.length} artifact{stage.artifactKeys.length === 1 ? "" : "s"}
                  </span>
                )}
              </span>
            )}
            <p className={`w-full max-w-[64ch] text-body-sm ${dark ? "text-blue-100" : "text-gray-700"}`}>{stage.purpose}</p>
          </header>
          {stage.recorded ? <StageBody stage={stage} d={d} listening={listening} /> : <Awaiting {...stage.awaiting} listening={listening} />}
        </article>
      ) : (
        <div id={`stage-${stage.key}`} className="flex min-h-[68px] items-center gap-3 rounded-lg px-1 sm:min-h-[84px]">
          <h2 className="text-h4 text-gray-700">{stage.title}</h2>
          <span className="text-caption text-gray-700">upcoming</span>
        </div>
      )}
    </li>
  );
}

/**
 * Every stage after the last recorded one, as one compact band: what the critique hands to the next agent, the
 * directions the engine listed (never a selection), and each awaiting stage with the agent and path that will fill it.
 * A stage leaves the band the moment its artifact exists and becomes a full card again.
 */
function NextInLoop({
  stages,
  d,
  evidence,
  shown,
  active,
  listening,
}: {
  stages: Stage[];
  d: Discovery;
  evidence: EvidenceView | null;
  shown: boolean;
  active: boolean;
  listening: boolean;
}) {
  const critique = [...d.followUps].reverse().find((f) => f.critiques.length)?.critiques[0] ?? d.baselineCritiques[0] ?? null;
  const questions = critique?.openQuestions ?? [];
  const directions = evidence?.nextDirections ?? [];
  return (
    <li className="relative grid grid-cols-[32px_minmax(0,1fr)] gap-x-3 pb-5 sm:gap-x-5">
      <div className="pt-[18px] sm:pt-[26px]">
        <span
          className={`relative z-10 flex size-8 items-center justify-center rounded-sm bg-gray-100 text-gray-700 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-gray-400 transition-[box-shadow] duration-200 ${
            active ? "shadow-[0_0_0_4px_var(--color-blue-300)]" : ""
          }`}
        >
          <Hourglass aria-hidden size={16} strokeWidth={1.75} />
        </span>
      </div>

      {shown ? (
        <article
          id="stage-band"
          aria-labelledby="stage-band-title"
          className={`scroll-mt-28 rounded-lg bg-gray-50 p-5 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-gray-300 sm:p-7 ${
            active ? "stage-enter ring-2 ring-blue-300" : ""
          }`}
        >
          <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h2 id="stage-band-title" className="text-h4 text-gray-900 sm:text-h3">
              Next in the loop
            </h2>
            <span className="text-caption font-medium text-gray-700 tabular">
              {stages.length} stage{stages.length === 1 ? "" : "s"} awaiting agents
            </span>
            {listening && (
              <span className="inline-flex items-center gap-2 text-caption font-medium text-blue-700 sm:ml-auto">
                <span aria-hidden className="size-2 animate-pulse rounded-full bg-blue-500" />
                Listening for new files
              </span>
            )}
          </header>

          {(questions.length > 0 || directions.length > 0) && (
            <div className="mt-5 grid gap-x-8 gap-y-5 sm:grid-cols-2">
              {critique && questions.length > 0 && (
                <div className="min-w-0">
                  <p className="mb-2 flex flex-wrap items-center gap-2 text-body-sm font-semibold text-gray-900">
                    {questions.length} untested question{questions.length === 1 ? "" : "s"} handed on by
                    <ArtifactChip artifactKey={critique.artifact.key} />
                  </p>
                  <VerbatimList items={questions} initial={2} />
                </div>
              )}
              {evidence && directions.length > 0 && (
                <div className="min-w-0">
                  <p className="mb-2 flex flex-wrap items-center gap-2 text-body-sm font-semibold text-gray-900">
                    Directions listed by
                    <ArtifactChip artifactKey={evidence.artifact.key} />
                  </p>
                  <VerbatimList items={directions} initial={directions.length} />
                  <p className="mt-2 text-body-sm text-gray-700">
                    Listed by the engine, not selected. The Director chooses after the planner proposes at least two candidates.
                  </p>
                </div>
              )}
            </div>
          )}

          <ol className="mt-5 border-t border-gray-200">
            {stages.map((s) => (
              <li
                key={s.key}
                id={`stage-${s.key}`}
                className="grid scroll-mt-28 grid-cols-[2rem_minmax(0,1fr)] gap-x-3 border-b border-gray-200 py-3 last:border-b-0"
              >
                <span className="pt-px text-body-sm font-bold text-gray-700 tabular">{s.number}</span>
                <div className="min-w-0">
                  <h3 className="text-body font-semibold text-gray-900">{s.title}</h3>
                  <p className="mt-0.5 text-body-sm text-gray-700">
                    <span className="font-semibold text-gray-900">{s.awaiting.state}</span> · awaiting {s.awaiting.what} ·{" "}
                    <span className="font-semibold">{s.awaiting.producer}</span>
                  </p>
                  <p className="mt-0.5 font-mono text-caption break-all text-gray-700">{s.awaiting.path}</p>
                </div>
              </li>
            ))}
          </ol>
        </article>
      ) : (
        <div id="stage-band" className="flex min-h-[68px] items-center gap-3 rounded-lg px-1 sm:min-h-[84px]">
          <h2 className="text-h4 text-gray-700">Next in the loop</h2>
          <span className="text-caption text-gray-700">upcoming</span>
        </div>
      )}
    </li>
  );
}

// --- Console pieces ------------------------------------------------------------

/** What an agent saved during its stage, in order, as the console lists it while the agent works. */
function workLines(stage: Stage, d: Discovery) {
  const seen = new Set<string>();
  return stage.artifactKeys
    .map((k) => d.artifacts[k])
    .filter((a) => a && !seen.has(a.id) && seen.add(a.id))
    .slice(0, MAX_LINES)
    .map((a) => ({ key: a.key, id: a.id, path: a.path, human: a.type === "REVIEW" }));
}

/** The agent at work: who, what it is doing, and each artifact as it lands. Never shows a result before the stage does. */
function AgentWorking({ stage, d, lines, paused }: { stage: Stage; d: Discovery; lines: number; paused: boolean }) {
  const all = workLines(stage, d);
  return (
    <li id="agent-working" className="relative grid scroll-mt-28 grid-cols-[32px_minmax(0,1fr)] gap-x-3 pb-5 sm:gap-x-5">
      <div className="pt-[18px] sm:pt-[22px]">
        <span className="relative z-10 flex size-8 items-center justify-center rounded-sm bg-white text-blue-600 ring-1 ring-inset ring-blue-300">
          <LoaderCircle aria-hidden size={16} strokeWidth={2.25} className={paused ? "" : "animate-spin"} />
        </span>
      </div>
      <div className="rounded-lg bg-white/70 p-5 ring-1 ring-gray-200 sm:p-6" aria-live="polite">
        <p className="flex flex-wrap items-center gap-2 text-body font-semibold text-gray-900">
          <TypeMark type={stage.type} />
          {stage.agent}
          <span className="text-body-sm font-medium text-gray-700">· step {stage.number} of {d.stages.length}</span>
        </p>
        <p className="mt-2 text-body text-gray-700">
          {stage.working}
          {!paused && <span aria-hidden className="thinking-dots" />}
          {paused && <span className="ml-2 text-body-sm font-semibold text-gray-900">Paused</span>}
        </p>
        {lines > 0 && (
          <ul className="mt-4 space-y-1.5 border-t border-gray-200 pt-3">
            {all.slice(0, lines).map((l) => (
              <li key={l.key} className="stage-enter flex min-w-0 items-center gap-2 text-body-sm text-gray-700">
                {l.human ? (
                  <UserCheck aria-hidden size={15} strokeWidth={2} className="shrink-0 text-gray-900" />
                ) : (
                  <Check aria-hidden size={15} strokeWidth={2.5} className="shrink-0 text-green-600" />
                )}
                <span className="shrink-0 font-semibold text-gray-900">{l.human ? "Human approval" : "Saved"}</span>
                <span className="shrink-0 font-mono text-caption text-gray-900">{l.id}</span>
                <span className="min-w-0 truncate font-mono text-caption text-gray-500">{l.path}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </li>
  );
}

/** The opening screen: the approved question loaded into a composer, ready to hand to the agents. */
function Composer({ d, source, onRun, onFull }: { d: Discovery; source: string; onRun: () => void; onFull: () => void }) {
  return (
    <section aria-labelledby="composer-title" className="mx-auto flex min-h-[calc(100dvh-12rem)] max-w-3xl flex-col justify-center py-8">
      <p className="text-caption font-semibold tracking-[0.04em] text-blue-700 uppercase">Agentic discovery lab · ENUT 2024</p>
      <h1 id="composer-title" className="mt-2 text-[30px] leading-[36px] font-extrabold tracking-[-0.02em] text-balance text-gray-900 sm:text-[36px] sm:leading-[42px]">
        What should the lab investigate?
      </h1>
      <form
        className="mt-6 rounded-xl bg-white p-4 shadow-[0_1px_0_var(--color-gray-200)] ring-1 ring-gray-200 focus-within:ring-2 focus-within:ring-blue-300 sm:p-5"
        onSubmit={(e) => {
          e.preventDefault();
          onRun();
        }}
      >
        <label htmlFor="question" className="text-body-sm font-semibold text-gray-900">
          Research question
        </label>
        <textarea
          id="question"
          readOnly
          rows={5}
          value={d.question.text ?? ""}
          className="mt-2 w-full resize-none bg-transparent text-body text-gray-900 outline-none"
        />
        <div className="mt-3 flex flex-wrap items-end justify-between gap-3 border-t border-gray-200 pt-3">
          <ul className="flex flex-wrap gap-1.5">
            {d.question.population.map((p) => (
              <li key={p} className="rounded-sm bg-gray-50 px-2 py-1 text-caption text-gray-700">
                {p}
              </li>
            ))}
          </ul>
          <button
            type="submit"
            autoFocus
            className="flex h-11 items-center gap-2 rounded-full bg-blue-500 pr-5 pl-4 text-body font-semibold text-white transition-colors duration-[120ms] hover:bg-blue-600 active:bg-blue-700"
          >
            <Play aria-hidden size={15} strokeWidth={2.5} />
            Run discovery
          </button>
        </div>
      </form>
      <p className="mt-4 text-body-sm text-gray-700">
        Seven agents take turns: they examine the evidence, name what is uncertain, choose the next experiment and update the
        lab&rsquo;s state. Figures come only from the deterministic engine. This replays the recorded Omnigent session from{" "}
        {source}.
      </p>
      <button type="button" onClick={onFull} className="mt-3 self-start text-body-sm font-semibold text-blue-600 hover:text-blue-700">
        Skip to the full record <ArrowRight aria-hidden size={14} className="inline" />
      </button>
    </section>
  );
}

function GhostButton({ label, onClick, children }: { label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      className="flex h-9 shrink-0 items-center gap-2 rounded-full px-3 text-body-sm font-semibold whitespace-nowrap text-gray-900 transition-colors duration-[120ms] hover:bg-white active:bg-gray-200"
    >
      {children}
    </button>
  );
}

// --- View --------------------------------------------------------------------

type Phase = "idle" | "running" | "done";
type Step = "think" | "read";

export default function DiscoveryView({
  payload,
  session,
  initialStage,
  full = false,
}: {
  payload: DiscoveryPayload;
  session?: string;
  initialStage?: number; // 0-based; opens the run paused after that stage (?stage=N)
  full?: boolean; // ?view=full: the whole record at once
}) {
  const { run: d, mode, liveUnavailable } = payload;
  const router = useRouter();
  const live = mode === "live" && !liveUnavailable;
  const total = d.stages.length;
  const tail = useMemo(() => tailStart(d.stages), [d.stages]);
  // Console units: each recorded stage, then (when some still await agents) one "Next in the loop" band.
  const units = tail + (tail < total ? 1 : 0);

  const startDone = full || mode === "live";
  const [phase, setPhase] = useState<Phase>(startDone ? "done" : initialStage != null ? "running" : "idle");
  const [revealed, setRevealed] = useState(startDone ? units : initialStage != null ? Math.min(units, initialStage + 1) : 0);
  const [step, setStep] = useState<Step>("read");
  const [lines, setLines] = useState(0);
  const [paused, setPaused] = useState(initialStage != null && !startDone);
  const [selectedKey, setSelectedKey] = useState<string | null>(() =>
    initialStage != null ? (d.stages[initialStage]?.artifactKeys[0] ?? defaultSelection(d)) : defaultSelection(d),
  );
  const [now, setNow] = useState(() => Date.parse(payload.loadedAt));

  // LIVE: artifacts that were not in the previous payload are marked fresh for a few seconds.
  const [arrivals, setArrivals] = useState<{ seen: Record<string, true>; at: Record<string, number> }>(() => ({
    seen: Object.fromEntries(Object.keys(d.artifacts).map((k) => [k, true] as const)),
    at: {},
  }));
  const added = Object.keys(d.artifacts).filter((k) => !arrivals.seen[k]);
  const [follow, setFollow] = useState<string | null>(null);
  if (added.length) {
    const at = { ...arrivals.at };
    added.forEach((k) => (at[k] = Date.parse(payload.loadedAt)));
    setArrivals({ seen: { ...arrivals.seen, ...Object.fromEntries(added.map((k) => [k, true] as const)) }, at });
    setSelectedKey(added.at(-1)!);
    setFollow(d.stages.find((s) => s.artifactKeys.includes(added.at(-1)!))?.key ?? null);
  }
  useEffect(() => {
    if (follow) scrollToStage(follow);
  }, [follow, arrivals]);
  const fresh = useMemo(
    () => new Set(Object.entries(arrivals.at).filter(([, t]) => now - t < FRESH_MS).map(([k]) => k)),
    [arrivals.at, now],
  );

  useEffect(() => {
    if (!live) return;
    const refresh = setInterval(() => router.refresh(), LIVE_REFRESH_MS);
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => {
      clearInterval(refresh);
      clearInterval(tick);
    };
  }, [live, router]);

  useEffect(() => {
    if (initialStage != null && !startDone) scrollToStage(initialStage >= tail ? "band" : d.stages[initialStage].key, false);
    // Only on first mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const unitStage = (i: number): Stage => d.stages[Math.min(i, total - 1)];
  const unitKey = (i: number) => (i >= tail ? "band" : d.stages[i].key);
  const linesFor = useCallback((i: number) => (i >= tail ? [] : workLines(d.stages[i], d)), [d, tail]);

  // The console clock: think (list what the agent saved) → reveal the stage → read → next agent.
  useEffect(() => {
    if (phase !== "running" || paused) return;
    let t: ReturnType<typeof setTimeout>;
    if (revealed >= units) {
      t = setTimeout(() => {
        setPhase("done");
        scrollToStage("summary");
      }, READ_MS);
    } else if (step === "read") {
      t = setTimeout(() => {
        setStep("think");
        setLines(0);
        requestAnimationFrame(() => document.getElementById("agent-working")?.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "nearest" }));
      }, revealed === 0 ? 300 : READ_MS);
    } else if (lines < linesFor(revealed).length) {
      t = setTimeout(() => setLines((l) => l + 1), lines === 0 ? FIRST_LINE_MS : LINE_MS);
    } else {
      t = setTimeout(() => {
        const i = revealed;
        setRevealed(i + 1);
        setStep("read");
        const k = unitStage(i).artifactKeys[0];
        if (k && i < tail) setSelectedKey(k);
        scrollToStage(unitKey(i));
      }, lines === 0 ? FIRST_LINE_MS + REVEAL_MS : REVEAL_MS);
    }
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, paused, revealed, step, lines, units, linesFor]);

  const run = useCallback(() => {
    setPhase("running");
    setRevealed(0);
    setStep("read");
    setLines(0);
    setPaused(false);
    setSelectedKey(null);
    window.scrollTo({ top: 0 });
  }, []);

  const skip = useCallback(() => {
    setPhase("done");
    setRevealed(units);
    setPaused(false);
    setSelectedKey(defaultSelection(d));
    scrollToStage("summary");
  }, [units, d]);

  useEffect(() => {
    if (mode !== "replay") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement;
      if (el.closest("input, textarea, select, button, a, [contenteditable=true], #inspector")) return;
      if (e.key === " " && phase === "running") {
        e.preventDefault();
        setPaused((p) => !p);
      } else if (e.key === "Escape" && phase === "running") skip();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, phase, skip]);

  // Scroll spy for the section bar.
  const [inView, setInView] = useState<string>("");
  useEffect(() => {
    const ids = [...d.stages.slice(0, Math.min(revealed, tail)).map((s) => `stage-${s.key}`), ...(revealed > tail ? ["stage-band"] : []), "overview"];
    const els = ids.map((id) => document.getElementById(id)).filter((el): el is HTMLElement => Boolean(el));
    const io = new IntersectionObserver(
      (entries) => {
        const hit = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (hit) setInView(hit.target.id);
      },
      { rootMargin: "-25% 0px -65% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [d.stages, tail, revealed, phase]);

  const ago = Math.max(0, Math.round((now - Date.parse(payload.loadedAt)) / 1000));
  const evidence = latestEvidence(d);
  const headline = headlineOf(d);
  const errors = d.issues.filter((i) => i.level === "error");
  const working = phase === "running" && step === "think" && revealed < units;

  // Everything the console has shown so far, by key, display id, full id and experiment id ("EXP-001 result" → "EXP-001").
  const revealedIds = useMemo(() => {
    const ids = new Set<string>();
    d.stages.slice(0, Math.min(revealed, tail)).forEach((s) =>
      s.artifactKeys.forEach((k) => {
        const a = d.artifacts[k];
        ids.add(k);
        if (!a) return;
        ids.add(a.id);
        if (a.fullId) ids.add(a.fullId);
        ids.add(a.id.split(" ")[0]);
      }),
    );
    return ids;
  }, [d, revealed, tail]);
  const done = phase === "done";
  const isRevealed = useCallback((id: string) => done || revealedIds.has(id), [done, revealedIds]);

  const ui = useMemo(
    () => ({ selectedKey, select: setSelectedKey, fresh, artifacts: d.artifacts, commit: payload.commit, isRevealed }),
    [selectedKey, fresh, d.artifacts, payload.commit, isRevealed],
  );

  const navItem = (current: boolean) =>
    `flex h-9 items-center gap-2 rounded-full pr-3 pl-1.5 text-body-sm font-semibold whitespace-nowrap transition-colors duration-[120ms] ${
      current ? "bg-white text-gray-900 shadow-[0_0_0_1px_var(--color-gray-200)]" : "text-gray-700 hover:bg-white/70 hover:text-gray-900"
    }`;

  return (
    <DiscoveryUiContext.Provider value={ui}>
      <a
        href="#stages"
        className="sr-only rounded-full bg-white px-4 py-2 text-body font-semibold text-blue-700 focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[60]"
      >
        Skip to discovery stages
      </a>
      <header className="sticky top-0 z-40 flex min-h-20 flex-wrap items-center gap-x-4 gap-y-2 bg-gray-100 px-4 py-3 md:gap-x-6 md:px-8 lg:top-[var(--frame)] lg:rounded-tr-2xl">
        {/* On desktop the sidebar carries the wordmark; the bar is for moving through the run. */}
        <Link href="/" className="rounded-sm text-gray-900 lg:hidden" aria-label="tiemPO, new discovery run">
          <Wordmark className="text-[26px] leading-none" />
        </Link>
        {phase !== "idle" && (
          <nav aria-label="Sections" className="order-last -mx-1 w-full overflow-x-auto md:order-none md:mx-0 md:w-auto md:flex-1">
            <ol className="flex items-center gap-1 px-1 py-1 md:px-0">
              {d.stages.map((s, i) => {
                const unit = Math.min(i, tail);
                const available = unit < revealed;
                const target = i >= tail ? "stage-band" : `stage-${s.key}`;
                const current = available && inView === target && i <= tail;
                return (
                  <li key={s.key}>
                    {available ? (
                      <a
                        href={`#${target}`}
                        aria-current={current ? "location" : undefined}
                        title={`${s.number} · ${s.title}`}
                        onClick={(e) => {
                          e.preventDefault();
                          if (s.artifactKeys[0]) setSelectedKey(s.artifactKeys[0]);
                          scrollToStage(i >= tail ? "band" : s.key);
                        }}
                        className={navItem(current)}
                      >
                        <span
                          aria-hidden
                          className={`flex size-6 items-center justify-center rounded-[5px] text-caption font-bold tabular ${
                            s.recorded ? TYPE[s.type].solid : "bg-gray-50 text-gray-700 outline-1 outline-dashed -outline-offset-1 outline-gray-400"
                          }`}
                        >
                          {s.number}
                        </span>
                        {s.shortTitle}
                      </a>
                    ) : (
                      <span className="flex h-9 items-center gap-2 rounded-full pr-3 pl-1.5 text-body-sm font-semibold whitespace-nowrap text-gray-400" aria-disabled>
                        <span aria-hidden className="flex size-6 items-center justify-center rounded-[5px] text-caption font-bold tabular outline-1 outline-dashed -outline-offset-1 outline-gray-300">
                          {s.number}
                        </span>
                        {s.shortTitle}
                      </span>
                    )}
                  </li>
                );
              })}
              {phase === "done" && (
                <li>
                  <a
                    href="#overview"
                    aria-current={inView === "overview" ? "location" : undefined}
                    onClick={(e) => {
                      e.preventDefault();
                      scrollToStage("summary");
                    }}
                    className={`${navItem(inView === "overview")} pl-3`}
                  >
                    Summary
                  </a>
                </li>
              )}
            </ol>
          </nav>
        )}
        {mode === "replay" ? (
          <div className="ml-auto flex items-center gap-1" role="group" aria-label="Run controls">
            {phase === "running" && (
              <>
                <GhostButton label={paused ? "Resume (Space)" : "Pause (Space)"} onClick={() => setPaused((p) => !p)}>
                  {paused ? <Play aria-hidden size={14} strokeWidth={2.5} /> : <Pause aria-hidden size={14} strokeWidth={2.5} />}
                  {paused ? "Resume" : "Pause"}
                </GhostButton>
                <GhostButton label="Show the full record (Esc)" onClick={skip}>
                  <FastForward aria-hidden size={14} strokeWidth={2.5} />
                  Skip to end
                </GhostButton>
              </>
            )}
            {phase === "done" && (
              <button
                type="button"
                onClick={run}
                className="flex h-9 items-center gap-2 rounded-full bg-white pr-4 pl-3 text-body-sm font-semibold whitespace-nowrap text-blue-700 ring-1 ring-blue-300 transition-colors duration-[120ms] hover:bg-blue-50 active:bg-blue-100"
              >
                <RotateCcw aria-hidden size={14} strokeWidth={2.5} />
                Run again
              </button>
            )}
          </div>
        ) : (
          <span className="ml-auto hidden items-center gap-2 text-body-sm font-semibold text-gray-900 sm:flex">
            {live ? (
              <>
                <span aria-hidden className="size-2 animate-pulse rounded-full bg-green-500" />
                Reading reports/ every {LIVE_REFRESH_MS / 1000} s
                <span className="font-medium text-gray-700 tabular">· {ago}s ago</span>
              </>
            ) : (
              <>
                <TriangleAlert aria-hidden size={16} className="text-yellow-700" />
                Live needs the local lab server
              </>
            )}
          </span>
        )}
      </header>

      <main className="px-4 pb-12 md:px-8">
        {phase === "idle" ? (
          <Composer d={d} source={payload.source} onRun={run} onFull={skip} />
        ) : (
          <div className="space-y-6">
            {d.sessions.length > 1 && (
              <nav aria-label="Discovery sessions" className="flex flex-wrap items-center gap-2 text-caption text-gray-700">
                Session:
                {[undefined, ...d.sessions].map((s) => (
                  <Link
                    key={s ?? "all"}
                    href={`/?${new URLSearchParams({ ...(mode === "live" ? { mode: "live" } : {}), ...(s ? { session: s } : {}) })}`}
                    aria-current={session === s ? "page" : undefined}
                    className={`rounded-full px-3 py-1 font-mono ${session === s ? "bg-blue-500 text-white" : "bg-white text-blue-600 ring-1 ring-blue-500 hover:bg-blue-50"}`}
                  >
                    {s ?? "all"}
                  </Link>
                ))}
              </nav>
            )}

            <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] 2xl:grid-cols-[minmax(0,1fr)_380px]">
              <div className="min-w-0 space-y-5">
                {/* The researcher's prompt, as a console turn. */}
                <section aria-label="Your question" className="ml-auto max-w-[44rem] rounded-xl bg-blue-500 p-5 text-white sm:p-6">
                  <p className="text-caption font-semibold tracking-[0.04em] text-blue-100 uppercase">You asked</p>
                  <p className="mt-2 text-body">{d.question.text}</p>
                  <p className="mt-3 text-caption text-blue-100">
                    {mode === "replay" ? `Replaying the recorded session · ${payload.source}` : payload.source}
                  </p>
                </section>

                <section id="stages" tabIndex={-1} aria-label="Discovery stages" className="focus:outline-none">
                  <ol>
                    {d.stages.slice(0, Math.min(revealed, tail)).map((s, i, shownStages) => {
                      const isLast = i === shownStages.length - 1;
                      return (
                        <StageItem
                          key={s.key}
                          stage={s}
                          d={d}
                          shown
                          active={phase === "running" && isLast && step === "read"}
                          fresh={s.artifactKeys.some((k) => fresh.has(k))}
                          animate={phase === "running" && isLast}
                          lineFilled={!isLast || working}
                          last={isLast && !working && revealed <= tail}
                          listening={live}
                        />
                      );
                    })}
                    {revealed > tail && tail < total && (
                      <NextInLoop stages={d.stages.slice(tail)} d={d} evidence={evidence} shown active={false} listening={live} />
                    )}
                    {working && <AgentWorking stage={unitStage(revealed)} d={d} lines={lines} paused={paused} />}
                  </ol>
                </section>

                {phase === "done" && (
                  <div id="stage-summary" className="stage-enter scroll-mt-28">
                    <Overview
                      d={d}
                      headline={headline}
                      source={payload.source}
                      sampleSize={evidence?.sampleSize ?? null}
                      errors={errors.map((e) => e.message)}
                    />
                  </div>
                )}
              </div>
              <div
                id="inspector"
                className="lg:sticky lg:top-[calc(var(--frame)+92px)] lg:max-h-[calc(100dvh-2*var(--frame)-92px)] lg:self-start lg:overflow-y-auto lg:pb-3"
              >
                {selectedKey ? (
                  <Inspector />
                ) : (
                  <p className="hidden rounded-lg bg-white/60 p-5 text-body-sm text-gray-700 ring-1 ring-gray-200 lg:block">
                    Every artifact the agents save appears here with its file, hash and producer. Select any id to inspect it.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </DiscoveryUiContext.Provider>
  );
}
