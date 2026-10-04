"use client";

import { useState } from "react";
import { Check, CircleCheck, Copy, ExternalLink, TriangleAlert } from "lucide-react";
import { ArtifactChip, TYPE, TypeMark, useDiscoveryUi } from "./primitives";

function CopyButton({ value, label }: { value: string; label: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setDone(true);
          setTimeout(() => setDone(false), 2000);
        } catch {}
      }}
      aria-label={done ? `${label} copied` : `Copy ${label}`}
      className="flex size-7 shrink-0 items-center justify-center rounded-full text-gray-700 transition-colors duration-[120ms] hover:bg-blue-50 hover:text-blue-600"
    >
      {done ? <Check aria-hidden size={14} strokeWidth={2.5} className="text-green-600" /> : <Copy aria-hidden size={14} strokeWidth={1.75} />}
    </button>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[6.5rem_minmax(0,1fr)] gap-3 border-t border-gray-200 py-2.5 first:border-t-0">
      <dt className="text-caption font-semibold text-gray-700">{label}</dt>
      <dd className="min-w-0 text-body-sm text-gray-900">{children}</dd>
    </div>
  );
}

/** Lets long repo paths wrap at their slashes instead of mid-word. */
function PathText({ path }: { path: string }) {
  const parts = path.split("/");
  return (
    <>
      {parts.map((p, i) => (
        <span key={i}>
          {p}
          {i < parts.length - 1 && (
            <>
              /<wbr />
            </>
          )}
        </span>
      ))}
    </>
  );
}

const HASH = /^[0-9a-f]{40,64}$/i;
const REPO = "https://github.com/RogelioZu/Hack-nation-hackathon";

function when(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC";
}

/** Provenance of the selected artifact: where it lives, its bytes, who produced it, what it links to. */
export default function Inspector({ explain }: { explain?: (key: string) => string | null }) {
  const { selectedKey, artifacts, commit } = useDiscoveryUi();
  const a = selectedKey ? artifacts[selectedKey] : null;
  // Experiments reproduce from their spec: the spec itself, or the spec linked to a result (one hop) or validation (two hops).
  const isSpec = (k: string) => k.startsWith("experiments/") && k.endsWith("/spec.json");
  const specPath = a
    ? isSpec(a.path)
      ? a.path
      : a.path.startsWith("reports/experiments/")
        ? (a.links.find(isSpec) ?? a.links.flatMap((k) => artifacts[k]?.links ?? []).find(isSpec) ?? null)
        : null
    : null;
  const reproduce = specPath ? `python scripts/run_experiment.py ${specPath}` : null;

  return (
    <aside aria-label="Scientific provenance" className="space-y-4">
      <section className="rounded-lg bg-white p-5">
        {a ? (
          <>
            <h2 id="inspector-title" tabIndex={-1} className="flex items-center gap-2.5 rounded-sm text-h2 text-gray-900">
              <TypeMark type={a.type} />
              {a.label}
            </h2>
            <p className="mt-1 font-mono text-body font-semibold [overflow-wrap:anywhere] text-gray-900">{a.id}</p>
            {a.fullId && <p className="mt-1 font-mono text-caption break-all text-gray-700">{a.fullId}</p>}
            <div className="mt-4 rounded-md bg-blue-50 p-4">
              <p className="text-caption font-semibold tracking-[0.04em] text-blue-700 uppercase">What this is</p>
              <p className="mt-1 text-body-sm text-gray-900">{TYPE[a.type].meaning}</p>
              {explain?.(a.key) && <p className="mt-2 text-body-sm text-gray-900">{explain(a.key)}</p>}
            </div>
            <details className="group mt-4">
              <summary className="cursor-pointer list-none text-body-sm font-semibold text-blue-600 hover:text-blue-700">
                <span className="group-open:hidden">Show technical details</span>
                <span className="hidden group-open:inline">Hide technical details</span>
                <span className="ml-1 font-normal text-gray-700">file, hash, producer, reproduction</span>
              </summary>
            <dl className="mt-3">
              <Row label="File">
                <span className="flex items-start gap-1">
                  <span className="min-w-0 font-mono text-caption [overflow-wrap:anywhere]">
                    <PathText path={a.path} />
                  </span>
                  <CopyButton value={a.path} label="path" />
                </span>
              </Row>
              {commit && (
                <Row label="Source">
                  <a
                    href={`${REPO}/blob/${commit}/${a.path}`}
                    title={`Open ${a.path} on GitHub at commit ${commit}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 font-medium text-blue-600 underline-offset-2 hover:text-blue-700 hover:underline"
                  >
                    GitHub at <span className="font-mono text-caption">{commit.slice(0, 7)}</span>
                    <ExternalLink aria-hidden size={13} strokeWidth={2} />
                  </a>
                </Row>
              )}
              <Row label="SHA-256">
                <span className="flex items-start gap-1">
                  <span className="min-w-0 font-mono text-caption break-all" title={a.sha256}>
                    {a.sha256.slice(0, 16)}…
                  </span>
                  <CopyButton value={a.sha256} label="SHA-256" />
                </span>
                {a.expectedSha256 && (
                  <span className="mt-1 flex items-center gap-1.5 text-caption text-gray-700">
                    {a.expectedSha256 === a.sha256 ? (
                      <CircleCheck aria-hidden size={13} className="text-green-600" />
                    ) : (
                      <TriangleAlert aria-hidden size={13} className="text-yellow-700" />
                    )}
                    {a.expectedSha256 === a.sha256 ? "matches research_state.json" : "differs from research_state.json"}
                  </span>
                )}
              </Row>
              {a.producer && <Row label="Produced by">{a.producer}</Row>}
              {a.sourceExperiment && (
                <Row label="Source experiment">
                  <span className="font-mono text-caption">{a.sourceExperiment}</span>
                </Row>
              )}
              {a.datasetVersion && (
                <Row label="Dataset">
                  <span className="font-mono text-caption">{a.datasetVersion}</span>
                </Row>
              )}
              {a.codeVersion && (
                <Row label="Code version">
                  <span className="font-mono text-caption" title={a.codeVersion}>
                    {a.codeVersion.slice(0, 12)}
                  </span>
                </Row>
              )}
              {when(a.createdAt) && <Row label="Created">{when(a.createdAt)}</Row>}
              {!a.createdAt && when(a.modifiedAt) && <Row label="Written">{when(a.modifiedAt)}</Row>}
              {a.session && (
                <Row label="Session">
                  <span className="font-mono text-caption">{a.session}</span>
                </Row>
              )}
              {reproduce && (
                <Row label="Reproduce">
                  <span className="flex items-start gap-1">
                    <code className="min-w-0 font-mono text-caption [overflow-wrap:anywhere]">{reproduce}</code>
                    <CopyButton value={reproduce} label="reproduce command" />
                  </span>
                  <span className="mt-1 block text-caption text-gray-700">Runs the spec twice and requires identical results.</span>
                </Row>
              )}
              {a.facts.map((f) => (
                <Row key={f.label} label={f.label}>
                  <span className={f.mono ? "font-mono text-caption [overflow-wrap:anywhere]" : ""} title={HASH.test(f.value) ? f.value : undefined}>
                    {HASH.test(f.value) ? `${f.value.slice(0, 16)}…` : f.value}
                  </span>
                </Row>
              ))}
            </dl>
            </details>
            {a.links.length > 0 && (
              <div className="mt-4 border-t border-gray-200 pt-4">
                <p className="mb-2 text-caption font-semibold text-gray-700">Related</p>
                <div className="flex flex-wrap gap-2">
                  {a.links.map((k) => (
                    <ArtifactChip key={k} artifactKey={k} />
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-body-sm text-gray-700">Select an artifact id to see its scientific provenance: where it lives, its hash, and what produced it.</p>
        )}
      </section>

    </aside>
  );
}
