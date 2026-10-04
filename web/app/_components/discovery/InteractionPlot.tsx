import type { InteractionView, SlopeView } from "@/lib/discovery/types";
import { niceStep } from "./ForestPlot";
import { plain, signed, StatusTag } from "./primitives";

interface Row {
  key: string;
  label: string;
  detail: string;
  slope: SlopeView;
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/**
 * A binary-moderator interaction on one shared axis. The two group slopes are shown as context; the interaction —
 * the difference between them — is set apart as the formal test, so nobody has to infer heterogeneity by eye.
 */
export default function InteractionPlot({ i }: { i: InteractionView }) {
  const groups: Row[] = [
    i.referenceSlope && { key: "ref", label: `${cap(i.moderator)}: ${i.referenceLevel}`, detail: "reference group slope", slope: i.referenceSlope },
    i.comparisonSlope && { key: "cmp", label: `${cap(i.moderator)}: ${i.comparisonLevel}`, detail: "comparison group slope", slope: i.comparisonSlope },
  ].filter((r): r is Row => Boolean(r));
  const formal: Row | null = i.interaction
    ? { key: "int", label: "Difference in slopes", detail: `${i.comparisonLevel} − ${i.referenceLevel}`, slope: i.interaction }
    : null;
  const all = formal ? [...groups, formal] : groups;
  if (!all.length) return null;

  const lo = Math.min(0, ...all.map((r) => r.slope.ci?.lower ?? r.slope.estimate));
  const hi = Math.max(0, ...all.map((r) => r.slope.ci?.upper ?? r.slope.estimate));
  const step = niceStep(hi - lo || 1);
  const min = Math.floor(lo / step) * step;
  const max = Math.ceil(hi / step) * step;
  const x = (v: number) => ((v - min) / (max - min)) * 100;
  const ticks: number[] = [];
  for (let t = min; t <= max + 1e-9; t += step) ticks.push(Number(t.toFixed(6)));

  const grid = (
    <span aria-hidden className="absolute inset-0">
      {ticks.map((t) => (
        <span key={t} className={`absolute inset-y-0 w-px ${t === 0 ? "bg-gray-400" : "bg-gray-200"}`} style={{ left: `${x(t)}%` }} />
      ))}
    </span>
  );

  const row = (r: Row, emphasis: boolean) => {
    const ci = r.slope.ci;
    const tone = emphasis ? "bg-blue-800" : "bg-gray-500";
    return (
      <tr key={r.key} className={emphasis ? "bg-blue-50" : ""}>
        <th scope="row" className={`border-t border-gray-200 py-3 pr-3 pl-2 text-left align-middle ${emphasis ? "font-bold text-gray-900" : "font-medium text-gray-700"}`}>
          <span className="block text-body">{r.label}</span>
          <span className="block text-caption font-normal text-gray-700">{r.detail}</span>
        </th>
        {/* Phones keep the numbers and drop the drawn axis, which has no room to be read there. */}
        <td className="relative hidden border-t border-gray-200 py-3 sm:table-cell">
          {grid}
          <div className="relative h-6">
            {ci && (
              <span
                aria-hidden
                className={`absolute top-1/2 -translate-y-1/2 rounded-full ${tone} ${emphasis ? "h-1" : "h-0.5"}`}
                style={{ left: `${x(ci.lower)}%`, width: `${x(ci.upper) - x(ci.lower)}%` }}
              />
            )}
            <span
              aria-hidden
              className={`absolute top-1/2 -translate-x-1/2 -translate-y-1/2 ring-2 ring-white ${tone} ${emphasis ? "size-4 rotate-45 rounded-[3px]" : "size-3 rounded-full"}`}
              style={{ left: `${x(r.slope.estimate)}%` }}
            />
          </div>
        </td>
        <td className={`border-t border-gray-200 py-3 pl-3 text-right text-body tabular ${emphasis ? "font-bold text-gray-900" : "font-medium text-gray-700"}`}>
          {signed(r.slope.estimate)}
          {ci && (
            <span className="block text-body-sm font-normal whitespace-nowrap text-gray-700">
              [{plain(ci.lower)}, {plain(ci.upper)}]
            </span>
          )}
        </td>
      </tr>
    );
  };

  return (
    <figure className="mt-5">
      <table className="w-full table-fixed border-separate border-spacing-0 text-left">
        <caption className="sr-only">
          Commute slopes for each {i.moderator} group, and the formal interaction test (difference in slopes), with 95% intervals
        </caption>
        <thead>
          <tr className="text-caption text-gray-700">
            <th scope="col" className="pb-2 pl-2 font-semibold sm:w-[30%]">
              Slope of {i.outcomeLabel.toLowerCase()} on commuting
            </th>
            <th scope="col" className="relative hidden pb-2 font-normal sm:table-cell">
              <span className="sr-only">Interval on a shared axis</span>
              <span aria-hidden className="relative block h-4">
                {ticks.map((t, k) => (
                  <span
                    key={t}
                    className={`absolute tabular ${k === 0 ? "" : k === ticks.length - 1 ? "-translate-x-full" : "-translate-x-1/2"} ${
                      t === 0 ? "font-semibold text-gray-900" : k % 2 ? "max-sm:hidden" : ""
                    }`}
                    style={{ left: `${x(t)}%` }}
                  >
                    {plain(t, 0)}
                  </span>
                ))}
              </span>
            </th>
            <th scope="col" className="w-[7.5rem] pb-2 pl-3 text-right font-semibold">
              Estimate · 95%
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={3} className="pt-2 pb-1.5 pl-2 text-body-sm font-semibold text-gray-700">
              Group slopes · descriptive, not a test
            </td>
          </tr>
          {groups.map((r) => row(r, false))}
        </tbody>
        {formal && (
          <tbody>
            <tr>
              <td colSpan={3} className="pt-5 pb-1.5 pl-2">
                <span className="flex flex-wrap items-center gap-x-3 gap-y-2 text-body-sm font-semibold text-gray-900">
                  Formal test · interaction
                  <StatusTag status={i.status} />
                </span>
              </td>
            </tr>
            {row(formal, true)}
          </tbody>
        )}
      </table>
      {i.units && (
        <figcaption className="mt-3 max-w-[72ch] text-body-sm text-gray-700">
          {cap(i.units)}. Reference level: {i.referenceLevel}; comparison level: {i.comparisonLevel}.
        </figcaption>
      )}
    </figure>
  );
}
