"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight, Pause, Play, TriangleAlert } from "lucide-react";
import Wordmark from "../Wordmark";
import type { Discovery, DiscoveryPayload, Stage } from "@/lib/discovery/types";
import Inspector from "./Inspector";
import { ArtifactChip, Awaiting, DiscoveryUiContext, StageMarker, TYPE, TypeBadge } from "./primitives";
import {
  CandidatesBody,
  CritiqueBody,
  DecisionBody,
  EvidenceBody,
  ExperimentBody,
  HypothesesBody,
  NewEvidenceBody,
  QuestionBody,
  SelectionBody,
} from "./stages";

// Replay clock, in seconds, for stages 1–9 (docs/DEMO_STORYBOARD.md): a 40-second tour in which the recorded
// evidence (0:08) and critique (0:16) hold longest. At OVERVIEW (0:37) the whole chain is shown again.
const CUES = [0, 4, 8, 16, 22, 25, 28, 31, 34];
const OVERVIEW = 37;
const END = 40;
const LIVE_REFRESH_MS = 3000;
const FRESH_MS = 8000;

const clock = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

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

function StageBody({ stage, d }: { stage: Stage; d: Discovery }) {
  const experimentKeys = Object.fromEntries(
    [d.baseline, ...d.followUps.map((f) => f.experiment)].filter(Boolean).map((e) => [e!.experimentId, e!.spec.key]),
  );
  switch (stage.key) {
    case "question":
      return <QuestionBody q={d.question} />;
    case "experiment":
      return d.baseline ? <ExperimentBody exp={d.baseline} /> : null;
    case "evidence":
      return d.baselineEvidence ? <EvidenceBody ev={d.baselineEvidence} /> : null;
    case "critique":
      return d.baselineCritiques[0] ? <CritiqueBody c={d.baselineCritiques[0]} earlier={d.baselineCritiques.slice(1)} /> : null;
    case "hypotheses":
      return <HypothesesBody hs={d.hypotheses} />;
    case "candidates":
      return <CandidatesBody cs={d.candidates} experimentKeys={experimentKeys} />;
    case "selection":
      return <SelectionBody sels={d.selections} />;
    case "new_evidence":
      return <NewEvidenceBody followUps={d.followUps} />;
    case "decision":
      return <DecisionBody ds={d.decisions} />;
  }
}

// Stages whose few artifacts read best as header chips; the rest carry chips per item in the body.
const HEADER_CHIPS: Stage["key"][] = ["question", "experiment", "evidence", "critique"];

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
  const headerKeys = HEADER_CHIPS.includes(stage.key) ? stage.artifactKeys.slice(0, stage.key === "critique" ? 1 : 2) : [];
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
            stage.recorded ? "bg-white" : "bg-gray-50 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-gray-300"
          } ${animate ? "stage-enter" : ""} ${fresh ? "fresh" : ""} ${active ? "ring-2 ring-blue-200" : ""}`}
        >
          <header className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-3">
            <span className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
              <h3 id={`stage-${stage.key}-title`} className="text-h4 text-gray-900 sm:text-h3">
                {stage.title}
              </h3>
              {/* A title that already names its role ("Evidence", "First experiment") keeps only the swatch. */}
              <TypeBadge type={stage.type} compact={stage.title.toLowerCase().includes(TYPE[stage.type].label.toLowerCase().slice(0, -2))} />
            </span>
            {fresh && <span className="rounded-sm bg-blue-500 px-2 py-0.5 text-micro text-white uppercase">New</span>}
            {stage.recorded && (
              <span className="flex w-full flex-wrap items-center gap-2 sm:ml-auto sm:w-auto">
                {headerKeys.map((k) => (
                  <ArtifactChip key={k} artifactKey={k} />
                ))}
                {!headerKeys.length && (
                  <span className="text-caption font-medium text-gray-700 tabular">
                    {stage.artifactKeys.length} artifact{stage.artifactKeys.length === 1 ? "" : "s"}
                  </span>
                )}
              </span>
            )}
          </header>
          {stage.recorded ? <StageBody stage={stage} d={d} /> : <Awaiting {...stage.awaiting} listening={listening} />}
        </article>
      ) : (
        <div id={`stage-${stage.key}`} className="flex min-h-[68px] items-center gap-3 rounded-lg px-1 sm:min-h-[84px]">
          <h3 className="text-h4 text-gray-700">{stage.title}</h3>
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
  const { discovery: d, mode, liveUnavailable } = payload;
  const router = useRouter();
  const live = mode === "live" && !liveUnavailable;

  const [selectedKey, setSelectedKey] = useState<string | null>(() =>
    initialStage != null ? (d.stages[initialStage]?.artifactKeys[0] ?? defaultSelection(d)) : defaultSelection(d),
  );
  const [cursor, setCursor] = useState<number | null>(initialStage ?? null); // null = whole chain
  const [playing, setPlaying] = useState(false);
  const [elapsed, setElapsed] = useState(initialStage != null ? (CUES[initialStage] ?? 0) : 0);
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
    if (initialStage != null) scrollToStage(d.stages[initialStage].key, false);
    // Only on first mount: later changes come from the replay controls.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const goTo = useCallback(
    (i: number | null) => {
      setCursor(i);
      if (i == null) {
        setSelectedKey(defaultSelection(d));
        setTimeout(() => window.scrollTo({ top: 0, behavior: reducedMotion() ? "auto" : "smooth" }), 60);
        return;
      }
      const stage = d.stages[i];
      if (stage.artifactKeys[0]) setSelectedKey(stage.artifactKeys[0]);
      scrollToStage(stage.key);
    },
    [d],
  );

  // REPLAY clock: reveal stages on the storyboard cues.
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      const t = (performance.now() - started.current) / 1000;
      setElapsed(t);
      if (t >= END) {
        setPlaying(false);
        return;
      }
      const target = t >= OVERVIEW ? null : CUES.reduce((acc, c, i) => (t >= c ? i : acc), 0);
      if (cursorRef.current !== target) {
        cursorRef.current = target;
        goTo(target);
      }
    }, 250);
    return () => clearInterval(id);
  }, [playing, goTo]);

  const play = useCallback(() => {
    if (playing) {
      setPlaying(false);
      return;
    }
    const from = elapsed > 0 && elapsed < END ? elapsed : 0;
    started.current = performance.now() - from * 1000;
    if (from === 0) goTo(0);
    setElapsed(from);
    setPlaying(true);
  }, [playing, elapsed, goTo]);

  const step = useCallback(
    (delta: number) => {
      setPlaying(false);
      const base = cursor ?? (delta > 0 ? -1 : d.stages.length);
      const next = Math.min(d.stages.length - 1, Math.max(0, base + delta));
      setElapsed(CUES[next] ?? 0);
      goTo(next);
    },
    [cursor, d.stages.length, goTo],
  );

  const restart = useCallback(() => {
    setPlaying(false);
    setElapsed(0);
    goTo(0);
  }, [goTo]);

  useEffect(() => {
    if (mode !== "replay") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement;
      if (el.closest("input, textarea, select, [contenteditable=true]")) return;
      if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === " " && !el.closest("button, a")) {
        e.preventDefault();
        play();
      } else if (e.key === "Home") restart();
      else if (e.key === "Escape") {
        setPlaying(false);
        goTo(null);
      } else return;
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, step, play, restart, goTo]);

  const recorded = d.stages.filter((s) => s.recorded).length;
  const total = d.stages.length;
  const ago = Math.max(0, Math.round((now - Date.parse(payload.loadedAt)) / 1000));

  const ui = useMemo(
    () => ({ selectedKey, select: setSelectedKey, fresh, artifacts: d.artifacts }),
    [selectedKey, fresh, d.artifacts],
  );

  return (
    <DiscoveryUiContext.Provider value={ui}>
      <header className="sticky top-0 z-40 flex h-20 items-center gap-4 bg-gray-100 px-4 md:gap-6 md:px-8 lg:top-[var(--frame)] lg:rounded-tr-2xl">
        {/* Replay is the only mode with a control; LIVE stays reachable for the team at /?mode=live. */}
        <Link href="/" className="mr-auto rounded-sm text-gray-900" aria-label="tiemPO, replay from the start">
          <Wordmark className="text-[26px] leading-none sm:text-[30px]" />
        </Link>
        {mode === "replay" ? (
          <div className="flex items-center gap-1" role="group" aria-label="Replay controls (← → Space, Home restarts, Esc shows all)">
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
              {playing ? "Pause" : elapsed > 0 && elapsed < END && cursor != null ? "Resume" : "Start discovery"}
            </button>
            <GhostButton label="Next stage (→)" onClick={() => step(1)}>
              <ChevronRight aria-hidden size={18} strokeWidth={2} />
            </GhostButton>
            <span className="ml-3 hidden min-w-[9.5rem] text-body-sm font-semibold text-gray-900 tabular md:block" aria-live="polite">
              {cursor == null ? `Overview · ${recorded} of ${total} recorded` : `Stage ${cursor + 1} of ${total}`}
              {(playing || elapsed > 0) && cursor != null && (
                <span className="block text-caption font-medium text-gray-700">
                  {clock(elapsed)} / {clock(END)}
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
                <TriangleAlert aria-hidden size={16} className="text-yellow-600" />
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
            <h1 id="thesis" className="text-[26px] leading-[32px] font-extrabold sm:text-[30px] sm:leading-[36px] tracking-[-0.02em] text-balance text-gray-900">
              A discovery loop that turns uncertainty into the next experiment.
            </h1>
            <p className="mt-3 max-w-[64ch] text-[15px] leading-6 text-gray-700">
              Agents examine the evidence, name what is uncertain, decide what is worth testing next, run a reproducible experiment and
              update the scientific decision. Every recorded stage is read from a real artifact; the rest wait, named, for the agent that
              produces them.
            </p>
          </div>

          <div className="border-t border-gray-200 pt-5 xl:border-t-0 xl:border-l xl:pt-0 xl:pl-10">
            <div className="flex items-baseline justify-between gap-3">
              <p className="text-title-card text-gray-900">Discovery loop</p>
              <p className="text-body-sm font-semibold text-gray-900 tabular">
                {recorded} of {total} stages
              </p>
            </div>
            <ol aria-label="Stages" className="mt-3 grid grid-cols-9 gap-1">
              {d.stages.map((s, i) => (
                <li key={s.key}>
                  <button
                    type="button"
                    onClick={() => {
                      setPlaying(false);
                      if (mode === "replay" && cursor != null) setElapsed(CUES[i] ?? 0);
                      if (mode === "replay" && cursor != null) goTo(i);
                      else {
                        if (s.artifactKeys[0]) setSelectedKey(s.artifactKeys[0]);
                        scrollToStage(s.key);
                      }
                    }}
                    aria-label={`Stage ${s.number}, ${s.title}: ${s.recorded ? "recorded" : "awaiting agents"}`}
                    title={`${s.number} · ${s.title}`}
                    className={`flex h-7 w-full items-center justify-center rounded-sm text-caption font-bold tabular transition-transform duration-[120ms] hover:-translate-y-0.5 ${
                      s.recorded ? TYPE[s.type].solid : "bg-gray-50 text-gray-500 outline-1 outline-dashed -outline-offset-1 outline-gray-400"
                    } ${cursor === i ? "shadow-[0_0_0_3px_var(--color-blue-200)]" : ""}`}
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
          <section aria-label="Discovery stages">
            <ol>
              {d.stages.map((s, i) => {
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
                    last={i === d.stages.length - 1}
                    listening={live}
                  />
                );
              })}
            </ol>
          </section>
          <div className="lg:sticky lg:top-[calc(var(--frame)+92px)] lg:max-h-[calc(100dvh-2*var(--frame)-92px)] lg:self-start lg:overflow-y-auto lg:pb-3">
            <Inspector />
          </div>
        </div>
      </main>
    </DiscoveryUiContext.Provider>
  );
}
