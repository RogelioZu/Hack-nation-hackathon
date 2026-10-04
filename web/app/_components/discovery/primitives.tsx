"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import {
  ChartScatter,
  CircleDashed,
  CircleHelp,
  FlaskConical,
  Hourglass,
  Signpost,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import type { ArtifactRef, ArtifactType } from "@/lib/discovery/types";

// --- Selection context: which artifact the inspector shows, and which ones just arrived (LIVE). ---

interface DiscoveryUi {
  selectedKey: string | null;
  select: (key: string) => void;
  fresh: Set<string>;
  artifacts: Record<string, ArtifactRef>;
}

export const DiscoveryUiContext = createContext<DiscoveryUi>({
  selectedKey: null,
  select: () => {},
  fresh: new Set(),
  artifacts: {},
});

export const useDiscoveryUi = () => useContext(DiscoveryUiContext);

// --- Artifact roles ---

export const TYPE: Record<ArtifactType, { label: string; icon: LucideIcon; solid: string; meaning: string }> = {
  QUESTION: {
    label: "Question",
    icon: CircleHelp,
    solid: "bg-white text-gray-900 ring-1 ring-inset ring-gray-300",
    meaning: "What the lab set out to learn.",
  },
  EVIDENCE: {
    label: "Evidence",
    icon: ChartScatter,
    solid: "bg-blue-500 text-white",
    meaning: "Figures computed by the deterministic engine.",
  },
  UNCERTAINTY: {
    label: "Uncertainty",
    icon: TriangleAlert,
    solid: "bg-yellow-400 text-gray-900",
    meaning: "What the critic says the evidence cannot settle.",
  },
  HYPOTHESIS: {
    label: "Hypothesis",
    icon: CircleDashed,
    solid: "bg-white text-blue-600 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-blue-500",
    meaning: "A falsifiable explanation, proposed and not yet tested.",
  },
  EXPERIMENT: {
    label: "Experiment",
    icon: FlaskConical,
    solid: "bg-blue-800 text-white",
    meaning: "An ExperimentSpec, proposed or run on analytic_v1.",
  },
  DECISION: {
    label: "Decision",
    icon: Signpost,
    solid: "bg-gray-900 text-white",
    meaning: "A recorded choice of what to investigate next.",
  },
};

/** The role as a small swatch plus its word: calm enough to sit beside a heading on every card. */
export function TypeBadge({ type, compact = false, className = "" }: { type: ArtifactType; compact?: boolean; className?: string }) {
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 text-caption font-semibold text-gray-700 ${className}`}>
      {/* The question's white swatch alone would read as an empty checkbox. */}
      {!(compact && type === "QUESTION") && <span aria-hidden className={`size-2.5 shrink-0 rounded-[3px] ${TYPE[type].solid}`} />}
      <span className={compact ? "sr-only" : ""}>{TYPE[type].label}</span>
    </span>
  );
}

/** The role as a square mark (spine marker grammar), so the heading stays the dominant first line. */
export function TypeMark({ type }: { type: ArtifactType }) {
  const Icon = TYPE[type].icon;
  return (
    <span className={`flex size-7 shrink-0 items-center justify-center rounded-sm ${TYPE[type].solid}`}>
      <Icon aria-hidden size={15} strokeWidth={2.25} />
      <span className="sr-only">{TYPE[type].label}:</span>
    </span>
  );
}

/** Square stage number on the spine (the system's ModuleNumber), filled with the stage's role once recorded. */
export function StageMarker({
  number,
  type,
  recorded,
  active,
}: {
  number: number;
  type: ArtifactType;
  recorded: boolean;
  active: boolean;
}) {
  const fill = recorded
    ? TYPE[type].solid
    : "bg-gray-100 text-gray-500 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-gray-400";
  return (
    <span
      className={`relative z-10 flex size-8 items-center justify-center rounded-sm text-body-sm font-bold tabular transition-[box-shadow] duration-200 ${fill} ${
        active ? "shadow-[0_0_0_4px_var(--color-blue-200)]" : ""
      }`}
    >
      {number}
    </span>
  );
}

/** A real artifact id. Clicking it opens the artifact in the inspector. */
export function ArtifactChip({ artifactKey, className = "" }: { artifactKey: string; className?: string }) {
  const { selectedKey, select, fresh, artifacts } = useDiscoveryUi();
  const a = artifacts[artifactKey];
  if (!a) return null;
  const selected = selectedKey === artifactKey;
  return (
    <button
      type="button"
      onClick={() => select(artifactKey)}
      aria-pressed={selected}
      title={`${a.label} · ${a.path}`}
      className={`inline-flex h-7 max-w-full shrink-0 items-center rounded-sm px-2 font-mono text-caption transition-colors duration-[120ms] ${
        selected ? "bg-blue-50 text-blue-700 ring-1 ring-blue-300" : "bg-gray-50 text-gray-700 hover:bg-blue-50 hover:text-blue-700"
      } ${fresh.has(artifactKey) ? "fresh" : ""} ${className}`}
    >
      <span className="truncate">{a.id}</span>
    </button>
  );
}

export function Pill({
  tone = "neutral",
  icon: Icon,
  children,
  title,
}: {
  tone?: "neutral" | "good" | "warn" | "brand";
  icon?: LucideIcon;
  children: ReactNode;
  title?: string;
}) {
  const text = { neutral: "text-gray-700", good: "text-gray-900", warn: "text-gray-900", brand: "text-blue-700" };
  const iconTone = { neutral: "text-gray-500", good: "text-green-600", warn: "text-yellow-600", brand: "text-blue-600" };
  return (
    <span title={title} className={`inline-flex items-center gap-1.5 text-body-sm ${text[tone]}`}>
      {Icon && <Icon aria-hidden size={15} strokeWidth={2} className={`shrink-0 ${iconTone[tone]}`} />}
      {children}
    </span>
  );
}

/** Renders the *emphasis* and **strong** markers agents sometimes write, instead of showing raw asterisks. */
export function Inline({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g);
  return (
    <>
      {parts.map((p, i) =>
        /^\*\*[^*]+\*\*$/.test(p) ? (
          <strong key={i}>{p.slice(2, -2)}</strong>
        ) : /^\*[^*]+\*$/.test(p) ? (
          <em key={i}>{p.slice(1, -1)}</em>
        ) : (
          p
        ),
      )}
    </>
  );
}

/** First items verbatim; the rest one click away. Artifact text is never rewritten. */
export function VerbatimList({
  items,
  clamp = true,
  initial = 1,
  empty = "Not stated in the artifact.",
}: {
  items: string[];
  clamp?: boolean;
  initial?: number;
  empty?: string;
}) {
  const [open, setOpen] = useState(false);
  if (items.length === 0) return <p className="text-body-sm text-gray-700 italic">{empty}</p>;
  const shown = open ? items : items.slice(0, initial);
  return (
    <div>
      <ul className="space-y-2">
        {shown.map((t, i) => (
          <li key={i} className={`text-body-sm text-gray-700 ${clamp && !open ? "line-clamp-3" : ""}`}>
            <Inline text={t} />
          </li>
        ))}
      </ul>
      {items.length > initial && (
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

export function Awaiting({ what, producer, path, listening }: { what: string; producer: string; path: string; listening: boolean }) {
  return (
    <div className="flex items-start gap-3">
      <Hourglass aria-hidden size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-gray-500" />
      <div className="min-w-0">
        <p className="text-h4 text-gray-700">Awaiting {what}</p>
        <p className="mt-1 text-body-sm text-gray-700">
          Produced by <span className="font-semibold">{producer}</span>
        </p>
        <p className="mt-1 font-mono text-caption break-all text-gray-700">{path}</p>
        {listening && (
          <p className="mt-2 inline-flex items-center gap-2 text-caption font-medium text-blue-700">
            <span aria-hidden className="size-2 animate-pulse rounded-full bg-blue-500" />
            Listening for new files
          </p>
        )}
      </div>
    </div>
  );
}

const MINUS = "−";

/** Signed number with a true minus sign; positives carry a plus so direction is never implied by color alone. */
export function signed(n: number, digits = 1): string {
  const v = Number(n.toFixed(digits));
  if (v === 0) return (0).toFixed(digits);
  return v < 0 ? `${MINUS}${Math.abs(v).toFixed(digits)}` : `+${v.toFixed(digits)}`;
}

export function plain(n: number, digits = 1): string {
  const v = Number(n.toFixed(digits));
  return v < 0 ? `${MINUS}${Math.abs(v).toFixed(digits)}` : v.toFixed(digits);
}

export function humanize(code: string): string {
  return code.replace(/_/g, " ").toLowerCase();
}
