"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight, Hourglass, Pause, Play, TriangleAlert } from "lucide-react";
import Wordmark from "../Wordmark";
import type { DiscoveryPayload, DiscoveryRunViewModel as Discovery, EvidenceView, Stage, StageKey } from "@/lib/discovery/types";
import Inspector from "./Inspector";
import { ArtifactChip, Awaiting, DiscoveryUiContext, StageMarker, TYPE, TypeBadge, VerbatimList } from "./primitives";
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

// Replay clock (docs/DEMO_STORYBOARD.md): how long each recorded stage holds, in seconds. Evidence, the new experiment
// and the scientific update hold longest. Stages still awaiting agents share one beat as the "Next in the loop" band;
// then the whole chain is shown again before the clock stops. Play is optional: ← → step through the same stages.
const HOLD: Record<StageKey, number> = {
  question: 4,
  baseline: 8,
  critique: 6,
  planning: 8,
  decision: 10,
  followup: 8,
  update: 8,
};
const LATER_HOLD = 4;
const BAND_HOLD = 8;
const OVERVIEW_HOLD = 3;
const LIVE_REFRESH_MS = 3000;
const FRESH_MS = 8000;

const clock = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

/** Index of the first stage after the last recorded one: from there on, every stage waits for agents. */
function tailStart(stages: Stage[]): number {
  let last = -1;
  stages.forEach((s, i) => {
    if (s.recorded) last = i;
  });
  return last + 1;
}

function timeline(stages: Stage[]) {
  const tail = tailStart(stages);
  const cues: number[] = [];
  let t = 0;
  stages.forEach((s, i) => {
    cues.push(t);
    if (i < tail) t += HOLD[s.key] ?? LATER_HOLD; // every awaiting stage shares the band's cue
  });
  const overview = tail < stages.length ? t + BAND_HOLD : t;
  return { cues, overview, end: overview + OVERVIEW_HOLD, tail };
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

/** Centres a stage once it is laid out (a stage that just revealed has no height on the first frame). */
function scrollToStage(key: string, smooth = true) {
  let tries = 0;
  const attempt = () => {
    const el = document.getElementById(`stage-${key}`);
    if (el && el.getBoundingClientRect().height > 0) {
      el.scrollIntoView({ behavior: smooth && !reducedMotion() ? "smooth" : "auto", block: "center" });
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
      return <DecisionHistory ds={d.decisions} changes={d.capabilityChanges} />;
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

// --- Top bar -----------------------------------------------------------------

function GhostButton({ label, onClick, children }: { label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="flex size-9 shrink-0 items-center justify-center rounded-full text-gray-900 transition-colors duration-[120ms] hover:bg-white active:bg-gray-200"
    >
      {children}
    </button>
  );
}

// --- View --------------------------------------------------------------------

export default function DiscoveryView({
  payload,
  session,
  initialStage,
}: {
  payload: DiscoveryPayload;
  session?: string;
  initialStage?: number; // 0-based; opens the replay paused at that stage (?stage=N)
}) {
  const { run: d, mode, liveUnavailable } = payload;
  const router = useRouter();
  const live = mode === "live" && !liveUnavailable;
  const total = d.stages.length;
  const { cues, overview, end, tail } = useMemo(() => timeline(d.stages), [d.stages]);
  // The band is one replay step: its cursor is the last stage, so every awaiting stage shows together.
  const units = useMemo(() => [...Array(tail).keys(), ...(tail < total ? [total - 1] : [])], [tail, total]);
  const toCursor = useCallback((i: number) => (i >= tail ? total - 1 : i), [tail, total]);

  const [selectedKey, setSelectedKey] = useState<string | null>(() =>
    initialStage != null ? (d.stages[initialStage]?.artifactKeys[0] ?? defaultSelection(d)) : defaultSelection(d),
  );
  const [cursor, setCursor] = useState<number | null>(initialStage != null ? toCursor(initialStage) : null); // null = whole chain
  const [playing, setPlaying] = useState(false);
  const [pausedMid, setPausedMid] = useState(false);
  const [elapsed, setElapsed] = useState(initialStage != null ? (cues[initialStage] ?? 0) : 0);
  const [now, setNow] = useState(() => Date.parse(payload.loadedAt));
  const started = useRef(0);
  const cursorRef = useRef<number | null>(null);
  useEffect(() => {
    cursorRef.current = cursor;
  }, [cursor]);

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
    if (initialStage != null) scrollToStage(initialStage >= tail ? "band" : d.stages[initialStage].key, false);
    // Only on first mount: later changes come from the replay controls.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const goTo = useCallback(
    (i: number | null, scrollKey?: string) => {
      if (i == null) {
        setCursor(null);
        setSelectedKey(defaultSelection(d));
        setTimeout(() => window.scrollTo({ top: 0, behavior: reducedMotion() ? "auto" : "smooth" }), 60);
        return;
      }
      setCursor(toCursor(i));
      const stage = d.stages[i];
      if (stage.artifactKeys[0]) setSelectedKey(stage.artifactKeys[0]);
      scrollToStage(scrollKey ?? (i >= tail ? "band" : stage.key));
    },
    [d, tail, toCursor],
  );

  // REPLAY clock: reveal stages on their cues.
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      const t = (performance.now() - started.current) / 1000;
      setElapsed(t);
      if (t >= end) {
        setPlaying(false);
        return;
      }
      const target = t >= overview ? null : toCursor(cues.reduce((acc, c, i) => (t >= c ? i : acc), 0));
      if (cursorRef.current !== target) {
        cursorRef.current = target;
        goTo(target);
      }
    }, 250);
    return () => clearInterval(id);
  }, [playing, goTo, cues, overview, end, toCursor]);

  const play = useCallback(() => {
    if (playing) {
      setPlaying(false);
      setPausedMid(true);
      return;
    }
    const from = elapsed > 0 && elapsed < end ? elapsed : 0;
    started.current = performance.now() - from * 1000;
    if (from === 0) goTo(0);
    setElapsed(from);
    setPausedMid(false);
    setPlaying(true);
  }, [playing, elapsed, end, goTo]);

  const step = useCallback(
    (delta: number) => {
      setPlaying(false);
      setPausedMid(false);
      const pos = cursor == null ? (delta > 0 ? -1 : units.length) : units.indexOf(toCursor(cursor));
      const next = units[Math.min(units.length - 1, Math.max(0, pos + delta))];
      setElapsed(cues[next] ?? 0);
      goTo(next);
    },
    [cursor, units, cues, goTo, toCursor],
  );

  const restart = useCallback(() => {
    setPlaying(false);
    setPausedMid(false);
    setElapsed(0);
    goTo(0);
  }, [goTo]);

  useEffect(() => {
    if (mode !== "replay") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement;
      // Text fields and the inspector keep their own keys; the replay shortcuts work everywhere else.
      if (el.closest("input, textarea, select, [contenteditable=true], #inspector")) return;
      if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === " " && !el.closest("button, a")) {
        e.preventDefault();
        play();
      } else if (e.key === "Home") restart();
      else if (e.key === "Escape") {
        setPlaying(false);
        setPausedMid(false);
        goTo(null);
      } else return;
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, step, play, restart, goTo]);

  const recorded = d.stages.filter((s) => s.recorded).length;
  const ago = Math.max(0, Math.round((now - Date.parse(payload.loadedAt)) / 1000));
  const evidence = latestEvidence(d);
  const headline = headlineOf(d);
  const errors = d.issues.filter((i) => i.level === "error");
  const position = cursor == null ? "Overview" : cursor >= tail ? "Next in the loop" : `Stage ${cursor + 1} of ${total}`;

  const ui = useMemo(
    () => ({ selectedKey, select: setSelectedKey, fresh, artifacts: d.artifacts, commit: payload.commit }),
    [selectedKey, fresh, d.artifacts, payload.commit],
  );

  return (
    <DiscoveryUiContext.Provider value={ui}>
      <a
        href="#stages"
        className="sr-only rounded-full bg-white px-4 py-2 text-body font-semibold text-blue-700 focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[60]"
      >
        Skip to discovery stages
      </a>
      <header className="sticky top-0 z-40 flex h-20 items-center gap-4 bg-gray-100 px-4 md:gap-6 md:px-8 lg:top-[var(--frame)] lg:rounded-tr-2xl">
        {/* Replay is the only mode with a control; LIVE stays reachable for the team at /?mode=live. */}
        <Link href="/" className="mr-auto rounded-sm text-gray-900" aria-label="tiemPO, replay from the start">
          <Wordmark className="text-[26px] leading-none sm:text-[30px]" />
        </Link>
        {mode === "replay" ? (
          <div className="flex items-center gap-1" role="group" aria-label="Replay controls">
            <span className="hidden sm:contents">
              <GhostButton label="Previous stage (←)" onClick={() => step(-1)}>
                <ChevronLeft aria-hidden size={18} strokeWidth={2} />
              </GhostButton>
            </span>
            <button
              type="button"
              onClick={play}
              title={playing ? "Pause the discovery replay (Space)" : "Start the discovery replay (Space)"}
              className="flex h-10 items-center gap-2 rounded-full bg-blue-500 pr-5 pl-4 text-body font-semibold whitespace-nowrap text-white transition-colors duration-[120ms] hover:bg-blue-600 active:bg-blue-700"
            >
              {playing ? <Pause aria-hidden size={15} strokeWidth={2.5} /> : <Play aria-hidden size={15} strokeWidth={2.5} />}
              {playing ? "Pause" : pausedMid ? "Resume" : "Start discovery"}
            </button>
            <GhostButton label="Next stage (→)" onClick={() => step(1)}>
              <ChevronRight aria-hidden size={18} strokeWidth={2} />
            </GhostButton>
            <span className="ml-3 hidden min-w-[9.5rem] text-body-sm font-semibold text-gray-900 tabular md:block">
              {/* Only the stage is announced; the ticking clock stays silent. */}
              <span aria-live="polite">{position}</span>
              {(playing || elapsed > 0) && cursor != null && (
                <span className="block text-caption font-medium text-gray-700">
                  {clock(elapsed)} / {clock(end)}
                </span>
              )}
            </span>
          </div>
        ) : (
          <span className="hidden items-center gap-2 text-body-sm font-semibold text-gray-900 sm:flex">
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

      <main className="space-y-8 px-4 pb-12 md:px-8">
        <section
          aria-labelledby="thesis"
          className="grid gap-6 rounded-xl bg-white p-6 md:p-8 xl:grid-cols-[minmax(0,1fr)_300px] xl:items-center xl:gap-10"
        >
          <div>
            {/* The headline is the latest evidence in the engine's own words, so it updates when a new result lands. */}
            {/* The headline is the latest scientific update in the artifact's own words, so it changes when a new result lands. */}
            <h1 id="thesis" className="text-[26px] leading-[32px] font-extrabold sm:text-[30px] sm:leading-[36px] tracking-[-0.02em] text-balance text-gray-900">
              {headline?.text ?? "No research question has been recorded yet."}
            </h1>
            {headline && (
              <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-body-sm text-gray-700">
                {headline.keys.map((k) => (
                  <ArtifactChip key={k} artifactKey={k} />
                ))}
                {evidence?.sampleSize != null && <span className="tabular">n = {evidence.sampleSize.toLocaleString("en-US")}</span>}
                <span aria-hidden className="text-gray-300">
                  ·
                </span>
                <span>{payload.source}</span>
              </p>
            )}
            {errors.length > 0 && (
              <p role="alert" className="mt-3 flex items-start gap-2 text-body-sm font-semibold text-gray-900">
                <TriangleAlert aria-hidden size={16} className="mt-0.5 shrink-0 text-yellow-700" />
                {errors.length} artifact problem{errors.length === 1 ? "" : "s"}: {errors[0].message}
              </p>
            )}
            <p className="mt-4 max-w-[64ch] text-[17px] leading-7 text-gray-700">
              Agents examine the evidence, name what is uncertain, decide what is worth testing next; a deterministic engine runs the
              experiment and humans approve each consequential step. Every stage below is read from a real artifact; any stage still
              missing waits, named, for the agent that produces it.
            </p>
          </div>

          <div className="border-t border-gray-200 pt-5 xl:border-t-0 xl:border-l xl:pt-0 xl:pl-10">
            <div className="flex items-baseline justify-between gap-3">
              <p className="text-title-card text-gray-900">Discovery loop</p>
              <p className="text-body-sm font-semibold text-gray-900 tabular">
                {recorded} of {total} recorded
              </p>
            </div>
            <ol aria-label="Stages" className="mt-3 grid grid-cols-7 gap-1">
              {d.stages.map((s, i) => (
                <li key={s.key}>
                  <button
                    type="button"
                    onClick={() => {
                      setPlaying(false);
                      setPausedMid(false);
                      if (mode === "replay" && cursor != null) {
                        setElapsed(cues[i] ?? 0);
                        goTo(i, s.key);
                      } else {
                        if (s.artifactKeys[0]) setSelectedKey(s.artifactKeys[0]);
                        scrollToStage(s.key);
                      }
                    }}
                    aria-label={`Stage ${s.number}, ${s.title}: ${s.recorded ? "recorded" : "awaiting agents"}`}
                    title={`${s.number} · ${s.title}`}
                    className={`flex h-7 w-full items-center justify-center rounded-sm text-caption font-bold tabular transition-transform duration-[120ms] hover:-translate-y-0.5 ${
                      s.recorded ? TYPE[s.type].solid : "bg-gray-50 text-gray-700 outline-1 outline-dashed -outline-offset-1 outline-gray-400"
                    } ${cursor === i || (cursor != null && cursor >= tail && i >= tail) ? "shadow-[0_0_0_3px_var(--color-blue-300)]" : ""}`}
                  >
                    {s.number}
                  </button>
                </li>
              ))}
            </ol>
          </div>
        </section>

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
          <section id="stages" tabIndex={-1} aria-label="Discovery stages" className="focus:outline-none">
            <ol>
              {d.stages.slice(0, tail).map((s, i) => {
                const shown = cursor == null || i <= cursor;
                const next = d.stages[i + 1];
                const nextShown = cursor == null || i + 1 <= cursor;
                return (
                  <StageItem
                    key={s.key}
                    stage={s}
                    d={d}
                    shown={shown}
                    active={cursor === i}
                    fresh={s.artifactKeys.some((k) => fresh.has(k))}
                    animate={cursor === i}
                    lineFilled={Boolean(next && nextShown && next.recorded && s.recorded)}
                    last={i === total - 1}
                    listening={live}
                  />
                );
              })}
              {tail < total && (
                <NextInLoop
                  stages={d.stages.slice(tail)}
                  d={d}
                  evidence={evidence}
                  shown={cursor == null || cursor >= tail}
                  active={cursor != null && cursor >= tail}
                  listening={live}
                />
              )}
            </ol>
          </section>
          <div
            id="inspector"
            className="lg:sticky lg:top-[calc(var(--frame)+92px)] lg:max-h-[calc(100dvh-2*var(--frame)-92px)] lg:self-start lg:overflow-y-auto lg:pb-3"
          >
            <Inspector />
          </div>
        </div>
      </main>
    </DiscoveryUiContext.Provider>
  );
}
