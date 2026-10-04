"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { Play } from "lucide-react";
import type { ArtifactType, ExperimentView, Stage, StatusView } from "@/lib/discovery/types";
import PageHeader from "../_components/PageHeader";
import { StatusTag, TYPE, TypeMark } from "../_components/discovery/primitives";


function Card({ id, title, lead, children }: { id: string; title: string; lead?: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-28 rounded-xl bg-white p-6 md:p-8">
      <h2 id={`${id}-title`} className="text-h3 text-gray-900">
        {title}
      </h2>
      {lead && <p className="mt-2 max-w-[68ch] text-body text-gray-700">{lead}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}

const SECTIONS = [
  { id: "what", label: "What tiemPO is" },
  { id: "use", label: "Running an investigation" },
  { id: "steps", label: "The seven steps" },
  { id: "read", label: "Reading a step" },
  { id: "statuses", label: "Status glossary" },
  { id: "numbers", label: "Reading the numbers" },
  { id: "evidence", label: "Checking the evidence" },
];

const CONTROLS: [string, string, string][] = [
  ["Start investigation", "", "Hands the research question to the agents and starts the run."],
  ["Previous · Next", "← →", "Step back or forward one step. Stepping pauses the run."],
  ["Play · Pause", "Space", "Let the agents continue on their own, or hold the current step."],
  ["Skip to end", "Esc", "Show every step and the final summary at once."],
  ["Home", "", "Return to this landing page; the run starts over."],
];

export default function Guide({
  stages,
  statuses,
  experiments,
  populationN,
}: {
  stages: Stage[];
  statuses: StatusView[];
  experiments: ExperimentView[];
  populationN: number | null;
}) {
  return (
    <>
      <PageHeader title="Reading guide">
        <Link
          href="/?start=1"
          className="flex h-10 items-center gap-2 rounded-full bg-blue-500 pr-5 pl-4 text-body font-semibold whitespace-nowrap text-white transition-colors duration-[120ms] hover:bg-blue-600 active:bg-blue-700"
        >
          <Play aria-hidden size={15} strokeWidth={2.5} />
          <span className="hidden sm:inline">Start investigation</span>
          <span className="sm:hidden">Start</span>
        </Link>
      </PageHeader>
      <main className="px-4 pb-12 md:px-8">
        <div className="grid gap-6 lg:grid-cols-[200px_minmax(0,1fr)]">
          <nav aria-label="Guide sections" className="hidden lg:block">
            <ol className="sticky top-[calc(var(--frame)+92px)] space-y-1">
              {SECTIONS.map((s, i) => (
                <li key={s.id}>
                  <a href={`#${s.id}`} className="flex gap-2 rounded-md px-2 py-1.5 text-body-sm text-gray-700 hover:bg-white hover:text-gray-900">
                    <span className="font-semibold text-blue-700 tabular">{i + 1}</span>
                    {s.label}
                  </a>
                </li>
              ))}
            </ol>
          </nav>

          <div className="max-w-[920px] space-y-6">
            <Card
              id="what"
              title="What tiemPO is"
              lead="An agentic research lab on official Mexican time-use data. Specialist AI agents, orchestrated with Omnigent, examine evidence, name what is uncertain, choose the next experiment and update the lab's scientific state. A deterministic statistics engine is the only component that produces numbers, and a human approves each consequential step."
            >
              <ul className="grid gap-3 sm:grid-cols-3">
                {[
                  ["Data", `INEGI ENUT 2024, ${populationN?.toLocaleString("en-US") ?? "—"} workers aged 18–65 in Mexico City and the State of Mexico.`],
                  ["Question", "Which part of personal time has the strongest negative association with five extra hours of weekday commuting, and does it differ by sex or by children at home?"],
                  ["Claims", "Observational and cross-sectional: every result is an association, never a cause."],
                ].map(([k, v]) => (
                  <li key={k} className="rounded-md bg-gray-50 p-4">
                    <p className="text-body-sm font-semibold text-gray-900">{k}</p>
                    <p className="mt-1 text-body-sm text-gray-700">{v}</p>
                  </li>
                ))}
              </ul>
            </Card>

            <Card
              id="use"
              title="Running an investigation"
              lead="The home page introduces the lab, the data and the question. Start investigation hands the question to the agents. They then take turns: each one shows what it is doing, the checks its tools run, every file it saves and any human approval it waits for, before its result appears. The conclusion arrives only at the end, followed by a summary and the key results."
            >
              <table className="w-full text-left text-body-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-caption text-gray-700">
                    <th className="py-2 pr-4 font-semibold">Control</th>
                    <th className="py-2 pr-4 font-semibold">Key</th>
                    <th className="py-2 font-semibold">What it does</th>
                  </tr>
                </thead>
                <tbody>
                  {CONTROLS.map(([c, k, t]) => (
                    <tr key={c} className="border-b border-gray-100 last:border-0">
                      <td className="py-2.5 pr-4 font-semibold whitespace-nowrap text-gray-900">{c}</td>
                      <td className="py-2.5 pr-4 font-mono text-caption whitespace-nowrap text-gray-700">{k || "—"}</td>
                      <td className="py-2.5 text-gray-700">{t}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-4 text-body-sm text-gray-700">
                What you see replays the recorded Omnigent session from files committed to the repository; the run is not regenerated in
                your browser. Add <code className="font-mono text-caption">?view=full</code> to the address to open the whole record at once.
              </p>
            </Card>

            <Card id="steps" title="The seven steps" lead="Each step is owned by one agent and answers one scientific question. The section bar at the top lets you jump back to any step already shown.">
              <ol className="divide-y divide-gray-100">
                {stages.map((s) => (
                  <li key={s.key} className="grid grid-cols-[2.25rem_minmax(0,1fr)] gap-x-3 py-3">
                    <span className={`flex size-8 items-center justify-center rounded-sm text-body-sm font-bold tabular ${TYPE[s.type].solid}`}>{s.number}</span>
                    <div className="min-w-0">
                      <p className="text-body font-semibold text-gray-900">
                        {s.title}
                        <span className="ml-2 text-caption font-semibold tracking-[0.04em] text-blue-700 uppercase">{s.agent}</span>
                      </p>
                      <p className="mt-0.5 text-body-sm text-gray-700">{s.purpose}</p>
                    </div>
                  </li>
                ))}
              </ol>
              {experiments.length > 0 && (
                <div className="mt-5 rounded-md bg-blue-50 p-4">
                  <p className="text-body-sm font-semibold text-gray-900">About the experiment ids</p>
                  <p className="mt-1 text-body-sm text-gray-700">
                    An experiment is one fixed statistical model the engine runs on the survey data. Each gets an id so later steps can point
                    to it. During the investigation, the &ldquo;what was it?&rdquo; buttons explain each one.
                  </p>
                  <ul className="mt-3 space-y-1.5">
                    {experiments.map((e) => (
                      <li key={e.experimentId} className="text-body-sm text-gray-900">
                        <span className="mr-2 rounded-sm bg-blue-800 px-1.5 py-0.5 font-mono text-caption text-white">{e.experimentId}</span>
                        {e.plain.title}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>

            <Card
              id="read"
              title="Reading a step"
              lead="Every step card has the same parts, so you can skim the first two and open the rest only when you need them."
            >
              <ol className="grid gap-3 sm:grid-cols-2">
                {[
                  ["Agent and purpose", "Who produced the step, and the question it answers."],
                  ["In plain words", "A short summary for readers outside the project, before any technical detail."],
                  ["The result", "Charts, verdicts, hypotheses or decisions, with every figure taken from the artifact."],
                  ["Inspect agent handoff", "The real JSON the agent passed on. Agents exchange structured files, not chat."],
                ].map(([k, v], i) => (
                  <li key={k} className="rounded-md bg-gray-50 p-4">
                    <p className="text-body-sm font-semibold text-gray-900">
                      <span className="mr-2 text-blue-700 tabular">{i + 1}</span>
                      {k}
                    </p>
                    <p className="mt-1 text-body-sm text-gray-700">{v}</p>
                  </li>
                ))}
              </ol>
              <p className="mt-6 text-body-sm font-semibold text-gray-900">Colours and marks</p>
              <ul className="mt-3 grid gap-3 sm:grid-cols-2">
                {(Object.keys(TYPE) as ArtifactType[]).map((t) => (
                  <li key={t} className="flex items-start gap-3">
                    <TypeMark type={t} labelled={false} />
                    <span className="min-w-0 text-body-sm text-gray-700">
                      <span className="font-semibold text-gray-900">{TYPE[t].label}.</span> {TYPE[t].meaning}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card
              id="statuses"
              title="Status glossary"
              lead="Statuses appear in plain words with the exact code the artifact writes beside them. These are all the statuses in the recorded run."
            >
              <ul className="divide-y divide-gray-100">
                {statuses.map((st) => (
                  <li key={st.code} className="grid gap-x-4 gap-y-1 py-2.5 sm:grid-cols-[minmax(0,17rem)_minmax(0,1fr)]">
                    <span>
                      <StatusTag status={st} />
                    </span>
                    <span className="text-body-sm text-gray-700">{st.meaning ?? "Shown as written in the artifact."}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card id="numbers" title="Reading the numbers">
              <ul className="space-y-3 text-body text-gray-700">
                <li>
                  <span className="font-semibold text-gray-900">Units.</span> All times are total Monday–Friday minutes in the survey&rsquo;s
                  reference week. The exposure is five extra hours of weekday commuting (+300 minutes), not one hour a day.
                </li>
                <li>
                  <span className="font-semibold text-gray-900">Estimates and intervals.</span> Each estimate is shown with its 95% interval.
                  In the charts, the dot is the estimate and the line its interval; the vertical line marks zero.
                </li>
                <li>
                  <span className="font-semibold text-gray-900">Interval includes zero.</span> The data are compatible with no association and
                  with a sizeable one. The lab reports this as inconclusive, which is not evidence of no effect.
                </li>
                <li>
                  <span className="font-semibold text-gray-900">Rankings.</span> One outcome only counts as &ldquo;strongest&rdquo; when its
                  difference from every other outcome excludes zero after correcting for multiple comparisons.
                </li>
                <li>
                  <span className="font-semibold text-gray-900">Uncertainty method.</span> Survey weights with PSU-clustered CR1 errors. This
                  approximates, and does not fully reconstruct, ENUT&rsquo;s complex-survey variance.
                </li>
              </ul>
            </Card>

            <Card
              id="evidence"
              title="Checking the evidence"
              lead="Every id on the page is a real file in the repository. Select one to open it in the inspector on the right."
            >
              <ul className="space-y-3 text-body text-gray-700">
                <li>
                  <span className="font-semibold text-gray-900">What this is.</span> The inspector first explains the file in plain words.
                </li>
                <li>
                  <span className="font-semibold text-gray-900">Technical details.</span> Its path, SHA-256 hash, the agent and model that
                  produced it, a link to it on GitHub at the exact commit, and, for experiments, the command that reruns it.
                </li>
                <li>
                  <span className="font-semibold text-gray-900">Reproducibility.</span> The engine runs every experiment twice on a
                  hash-checked dataset and requires identical results before saving them.
                </li>
              </ul>
            </Card>

            <div className="flex justify-center py-2">
              <Link
                href="/?start=1"
                className="flex h-12 items-center gap-2 rounded-full bg-blue-500 pr-6 pl-5 text-[17px] font-semibold text-white transition-colors duration-[120ms] hover:bg-blue-600 active:bg-blue-700"
              >
                <Play aria-hidden size={16} strokeWidth={2.5} />
                Start investigation
              </Link>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
