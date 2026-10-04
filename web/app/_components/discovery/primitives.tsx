"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import {
  ChartScatter,
  CircleCheck,
  CircleDashed,
  CircleHelp,
  ClipboardList,
  Cpu,
  FlaskConical,
  GitCompareArrows,
  Hourglass,
  Signpost,
  TriangleAlert,
  UserCheck,
  type LucideIcon,
} from "lucide-react";
import type { ArtifactRef, ArtifactType, StatusView } from "@/lib/discovery/types";

// --- Selection context: which artifact the inspector shows, and which ones just arrived (LIVE). ---

interface DiscoveryUi {
  selectedKey: string | null;
  select: (key: string) => void;
  fresh: Set<string>;
  artifacts: Record<string, ArtifactRef>;
  commit: string | null; // REPLAY snapshot commit, for "open at commit" links
  // Console replay: whether an artifact (key, id or experiment id) has appeared yet. Later results stay hidden until then.
  isRevealed: (idOrKey: string) => boolean;
}

export const DiscoveryUiContext = createContext<DiscoveryUi>({
  selectedKey: null,
  select: () => {},
  fresh: new Set(),
  artifacts: {},
  commit: null,
  isRevealed: () => true,
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
    meaning: "Figures computed by the deterministic engine that the loop starts from.",
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
    meaning: "A falsifiable explanation to be tested; never a finding.",
  },
  REVIEW: {
    label: "Human review",
    icon: UserCheck,
    solid: "bg-white text-gray-900 ring-[1.5px] ring-inset ring-gray-900",
    meaning: "A human approval that gates a consequential scientific step.",
  },
  PROPOSAL: {
    label: "Experiment proposal",
    icon: ClipboardList,
    solid: "bg-white text-blue-800 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-blue-800",
    meaning: "A candidate experiment the planner proposed; not run.",
  },
  DECISION: {
    label: "Decision",
    icon: Signpost,
    solid: "bg-gray-900 text-white",
    meaning: "A recorded choice by the Discovery Director.",
  },
  CAPABILITY: {
    label: "Engine capability",
    icon: Cpu,
    solid: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-300",
    meaning: "What the deterministic engine can compute, and when that changed.",
  },
  EXPERIMENT: {
    label: "Experiment result",
    icon: FlaskConical,
    solid: "bg-blue-800 text-white",
    meaning: "A new run of the deterministic engine, approved before it ran.",
  },
  UPDATE: {
    label: "Scientific update",
    icon: GitCompareArrows,
    solid: "bg-blue-900 text-white",
    meaning: "A hypothesis status the lab changed because of a result.",
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
export function TypeMark({ type, labelled = true }: { type: ArtifactType; labelled?: boolean }) {
  const Icon = TYPE[type].icon;
  return (
    <span className={`flex size-7 shrink-0 items-center justify-center rounded-sm ${TYPE[type].solid}`}>
      <Icon aria-hidden size={15} strokeWidth={2.25} />
      {/* Unlabelled when the text beside it already names the role. */}
      {labelled && <span className="sr-only">{TYPE[type].label}:</span>}
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
    : "bg-gray-100 text-gray-700 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-gray-400";
  return (
    <span
      className={`relative z-10 flex size-8 items-center justify-center rounded-sm text-body-sm font-bold tabular transition-[box-shadow] duration-200 ${fill} ${
        active ? "shadow-[0_0_0_4px_var(--color-blue-300)]" : ""
      }`}
    >
      {number}
    </span>
  );
}

const TONE: Record<StatusView["tone"], { box: string; icon: LucideIcon | null; iconClass: string }> = {
  good: { box: "bg-gray-50 text-gray-900", icon: CircleCheck, iconClass: "text-green-600" },
  warn: { box: "bg-gray-50 text-gray-900", icon: TriangleAlert, iconClass: "text-yellow-700" },
  uncertain: { box: "bg-yellow-400 text-gray-900", icon: TriangleAlert, iconClass: "text-gray-900" },
  neutral: { box: "bg-gray-50 text-gray-700", icon: null, iconClass: "" },
};

/**
 * A status in plain words, with the artifact's exact code beside it. The adapter sets the tone (icon), label and the
 * one-line meaning shown on hover; `code={false}` keeps the code for screen readers and the tooltip only.
 */
export function StatusTag({
  status,
  large = false,
  code = true,
  className = "",
}: {
  status: StatusView | null;
  large?: boolean;
  code?: boolean;
  className?: string;
}) {
  if (!status) return null;
  const t = TONE[status.tone];
  const Icon = t.icon;
  // A one-word code whose label is the same word ("Supported") is shown once; every other code stays visible beside its label.
  const same = status.label.toUpperCase() === status.code.toUpperCase();
  return (
    <span
      title={[status.code, status.meaning].filter(Boolean).join(" · ")}
      className={`inline-flex max-w-full shrink-0 flex-wrap items-center gap-x-1.5 gap-y-0.5 rounded-sm ${
        large ? "min-h-10 px-3.5 py-1 text-body font-semibold" : "min-h-7 px-2 py-0.5 text-caption font-semibold"
      } ${t.box} ${className}`}
    >
      {Icon && <Icon aria-hidden size={large ? 17 : 13} strokeWidth={2.25} className={`shrink-0 ${t.iconClass}`} />}
      <span className="min-w-0 [overflow-wrap:anywhere]">{status.label}</span>
      {!same && (
        <span className={`min-w-0 font-mono font-normal opacity-70 [overflow-wrap:anywhere] ${large ? "text-caption" : "text-micro"} ${code ? "" : "sr-only"}`}>
          {status.code}
        </span>
      )}
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
      onClick={() => {
        select(artifactKey);
        // Where the inspector sits beside the spine (lg+), move focus to it so keyboard and screen-reader users land on the details.
        if (window.matchMedia("(min-width: 1024px)").matches) {
          requestAnimationFrame(() => document.getElementById("inspector-title")?.focus({ preventScroll: true }));
        }
      }}
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
  const iconTone = { neutral: "text-gray-500", good: "text-green-600", warn: "text-yellow-700", brand: "text-blue-600" };
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
          <li key={i} className={`text-body-sm [overflow-wrap:anywhere] text-gray-700 ${clamp && !open ? "line-clamp-3" : ""}`}>
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

export function Awaiting({
  state,
  what,
  producer,
  path,
  listening,
}: {
  state: string;
  what: string;
  producer: string;
  path: string;
  listening: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <Hourglass aria-hidden size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-gray-500" />
      <div className="min-w-0">
        <p className="text-h4 text-gray-700">{state}</p>
        <p className="mt-1 text-body-sm text-gray-700">Awaiting {what}</p>
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
