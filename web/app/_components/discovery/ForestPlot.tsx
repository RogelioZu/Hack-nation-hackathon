import type { EstimateRow } from "@/lib/discovery/types";
import { plain, signed } from "./primitives";

function niceStep(span: number): number {
  const raw = span / 5;
  const pow = 10 ** Math.floor(Math.log10(raw));
  return [1, 2, 2.5, 5, 10].map((m) => m * pow).find((s) => s >= raw) ?? 10 * pow;
}

/**
 * Dot-and-whisker plot of adjusted coefficients with their 95% pointwise intervals.
 * One table: the outcome, the interval drawn on a shared axis, and the numbers it is drawn from.
 */
export default function ForestPlot({ rows, highlight, caption }: { rows: EstimateRow[]; highlight: string | null; caption: string }) {
  const lows = rows.map((r) => r.ci?.lower ?? r.coefficient);
  const highs = rows.map((r) => r.ci?.upper ?? r.coefficient);
  const lo = Math.min(0, ...lows);
  const hi = Math.max(0, ...highs);
  const step = niceStep(hi - lo || 1);
  const min = Math.floor(lo / step) * step;
  const max = Math.ceil(hi / step) * step;
  const x = (v: number) => ((v - min) / (max - min)) * 100;
  const ticks: number[] = [];
  for (let t = min; t <= max + 1e-9; t += step) ticks.push(Number(t.toFixed(6)));

  const grid = (
    <>
      {ticks.map((t) => (
        <span
          key={t}
          aria-hidden
          className={`absolute inset-y-0 w-px ${t === 0 ? "bg-gray-400" : "bg-gray-200"}`}
          style={{ left: `${x(t)}%` }}
        />
      ))}
    </>
  );

  return (
    <figure className="mt-5">
      <table className="w-full border-separate border-spacing-0 text-left">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="text-caption text-gray-700">
            <th scope="col" className="w-[30%] pb-2 font-semibold sm:w-[26%]">
              Outcome
            </th>
            <th scope="col" className="relative pb-2 font-normal">
              <span className="sr-only">Interval on a shared axis</span>
              <span aria-hidden className="relative block h-4">
                {ticks.map((t, i) => (
                  <span
                    key={t}
                    // Phones keep every other label (and zero) so the numbers do not collide.
                    className={`absolute -translate-x-1/2 tabular ${t === 0 ? "font-semibold text-gray-900" : i % 2 ? "max-sm:hidden" : ""}`}
                    style={{ left: `${x(t)}%` }}
                  >
                    {plain(t, 0)}
                  </span>
                ))}
              </span>
            </th>
            <th scope="col" className="w-[4.5rem] pb-2 pl-4 text-right font-semibold">
              Estimate
            </th>
            <th scope="col" className="hidden w-[8.5rem] pb-2 pl-3 text-right font-semibold sm:table-cell">
              95% interval
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const strong = r.outcome === highlight;
            const tone = strong ? "bg-blue-500" : "bg-gray-500";
            const ci = r.ci;
            const tip = [
              `${r.label}: ${plain(r.coefficient, 3)} min`,
              ci && `95% [${plain(ci.lower, 3)}, ${plain(ci.upper, 3)}]`,
              r.simultaneous &&
                `${r.simultaneous.adjustment ?? "simultaneous"} [${plain(r.simultaneous.lower, 3)}, ${plain(r.simultaneous.upper, 3)}]`,
              r.standardError != null && `SE ${r.standardError.toFixed(3)}`,
              r.n != null && `n ${r.n.toLocaleString("en-US")}`,
            ]
              .filter(Boolean)
              .join(" · ");
            return (
              <tr key={r.outcome} tabIndex={0} aria-label={tip} className="group">
                <th
                  scope="row"
                  className={`border-t border-gray-200 py-3 pr-3 text-body group-focus-visible:text-blue-700 ${
                    strong ? "font-bold text-gray-900" : "font-medium text-gray-700"
                  }`}
                >
                  {r.label}
                </th>
                <td className="relative border-t border-gray-200 py-3">
                  <span aria-hidden className="absolute inset-0">
                    {grid}
                  </span>
                  <div className="relative h-5">
                    {ci && (
                      <span
                        aria-hidden
                        className={`absolute top-1/2 h-0.5 -translate-y-1/2 rounded-full ${tone}`}
                        style={{ left: `${x(ci.lower)}%`, width: `${x(ci.upper) - x(ci.lower)}%` }}
                      />
                    )}
                    <span
                      aria-hidden
                      className={`absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-white transition-transform duration-[120ms] group-hover:scale-125 group-focus-visible:scale-125 ${tone} ${
                        strong ? "size-3.5" : "size-3"
                      }`}
                      style={{ left: `${x(r.coefficient)}%` }}
                    />
                    <span
                      role="tooltip"
                      className="pointer-events-none absolute bottom-full z-20 mb-2 w-max max-w-[min(22rem,70vw)] -translate-x-1/2 rounded-md bg-gray-900 px-3 py-2 text-caption text-white opacity-0 transition-opacity duration-[120ms] group-hover:opacity-100 group-focus-visible:opacity-100"
                      style={{ left: `${Math.min(80, Math.max(20, x(r.coefficient)))}%` }}
                    >
                      {tip}
                    </span>
                  </div>
                </td>
                <td
                  className={`border-t border-gray-200 py-3 pl-4 text-right text-body tabular ${
                    strong ? "font-bold text-gray-900" : "font-medium text-gray-700"
                  }`}
                >
                  {signed(r.coefficient)}
                </td>
                <td className="hidden border-t border-gray-200 py-3 pl-3 text-right text-body-sm text-gray-700 tabular sm:table-cell">
                  {ci ? `[${plain(ci.lower)}, ${plain(ci.upper)}]` : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot aria-hidden>
          <tr className="text-caption text-gray-700">
            <td />
            <td className="pt-1.5">
              <span className="flex justify-between gap-2 whitespace-nowrap">
                <span>
                  ← fewer<span className="max-sm:hidden"> minutes</span>
                </span>
                <span>
                  more<span className="max-sm:hidden"> minutes</span> →
                </span>
              </span>
            </td>
            <td />
            <td className="hidden sm:table-cell" />
          </tr>
        </tfoot>
      </table>
      {/* The table caption already carries this for screen readers; the visible copy is not read twice. */}
      <figcaption aria-hidden className="mt-3 max-w-[72ch] text-body-sm text-gray-700">
        {caption}
      </figcaption>
    </figure>
  );
}
