"use client";

import { useState } from "react";
import { FlaskConical, Hourglass } from "lucide-react";
import type { ExperimentView } from "@/lib/discovery/types";
import { StatusTag, useDiscoveryUi } from "./primitives";

/** One experiment for a reader outside the project: what it asked, what it compared, why it ran, and (once shown) what it found. */
export function ExperimentCard({ exp, compact = false }: { exp: ExperimentView; compact?: boolean }) {
  const { isRevealed } = useDiscoveryUi();
  const shown = isRevealed(exp.experimentId);
  return (
    <div className={compact ? "" : "rounded-lg bg-white p-5 ring-1 ring-gray-200 ring-inset"}>
      <p className="flex flex-wrap items-center gap-2">
        <span className="rounded-sm bg-blue-800 px-2 py-0.5 font-mono text-caption font-semibold text-white">{exp.experimentId}</span>
        <span className="text-body font-semibold text-gray-900">{exp.plain.title}</span>
      </p>
      <dl className="mt-3 space-y-2.5 text-body-sm">
        <div>
          <dt className="font-semibold text-gray-900">What it did</dt>
          <dd className="text-gray-700">{exp.plain.what}</dd>
        </div>
        {exp.plain.why && (
          <div>
            <dt className="font-semibold text-gray-900">Why it ran</dt>
            <dd className="text-gray-700">{exp.plain.why}</dd>
          </div>
        )}
        <div>
          <dt className="font-semibold text-gray-900">What it found</dt>
          <dd className="text-gray-700">
            {shown ? (
              <>
                {exp.plain.finding ?? "No result recorded."}
                <span className="mt-2 flex flex-wrap gap-1.5">
                  <StatusTag status={exp.reviewStatus} code={false} />
                </span>
              </>
            ) : (
              <span className="inline-flex items-center gap-1.5 italic">
                <Hourglass aria-hidden size={14} className="text-gray-500" />
                Appears when the agents reach this experiment.
              </span>
            )}
          </dd>
        </div>
      </dl>
    </div>
  );
}

/** The experiments of the run as buttons; each opens a short explainer. */
export default function ExperimentGuide({ exps, title = "The experiments in this run", initiallyOpen = null }: { exps: ExperimentView[]; title?: string; initiallyOpen?: string | null }) {
  const [open, setOpen] = useState<string | null>(initiallyOpen);
  if (!exps.length) return null;
  const current = exps.find((e) => e.experimentId === open) ?? null;
  return (
    <section aria-label={title} className="rounded-xl bg-white p-5 sm:p-6">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <p className="flex items-center gap-2 text-body font-semibold text-gray-900">
          <FlaskConical aria-hidden size={16} strokeWidth={2} className="text-blue-700" />
          {title}
        </p>
        <div className="flex flex-wrap gap-2">
          {exps.map((e) => (
            <button
              key={e.experimentId}
              type="button"
              onClick={() => setOpen((o) => (o === e.experimentId ? null : e.experimentId))}
              aria-expanded={open === e.experimentId}
              className={`h-8 rounded-full px-3 text-body-sm font-semibold transition-colors duration-[120ms] ${
                open === e.experimentId ? "bg-blue-500 text-white" : "bg-blue-50 text-blue-700 hover:bg-blue-100"
              }`}
            >
              <span className="font-mono">{e.experimentId}</span>
              <span className="ml-1.5 font-normal">· what was it?</span>
            </button>
          ))}
        </div>
      </div>
      {current && (
        <div className="stage-enter mt-4">
          <ExperimentCard exp={current} compact />
        </div>
      )}
    </section>
  );
}
