"use client";

import type { ArtifactType } from "@/lib/discovery/types";
import { TYPE, TypeMark } from "./primitives";

/** How to read the discovery spine: the five artifact roles and the honesty note. */
export default function SpineGuide() {
  return (
    <section className="max-w-[720px] rounded-lg bg-white p-6 md:p-8" aria-labelledby="legend-title">
      <h1 id="legend-title" className="text-h2 text-gray-900">
        Reading the spine
      </h1>
      <ul className="mt-5 space-y-4">
        {(Object.keys(TYPE) as ArtifactType[]).map((t) => (
          <li key={t} className="flex items-start gap-3">
            <TypeMark type={t} labelled={false} />
            <span className="min-w-0 text-body text-gray-700">
              <span className="font-semibold text-gray-900">{TYPE[t].label}.</span> {TYPE[t].meaning}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-6 border-t border-gray-200 pt-4 text-body text-gray-700">
        ENUT 2024 is observational and cross-sectional. Every figure here is an association, never a cause.
      </p>
    </section>
  );
}
