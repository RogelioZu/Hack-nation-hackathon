import type { Estimate } from "@/lib/types";

const SEX_COLOR: Record<string, string> = {
  women: "var(--women)",
  female: "var(--women)",
  mujer: "var(--women)",
  men: "var(--men)",
  male: "var(--men)",
  hombre: "var(--men)",
};

/** Dot-and-whisker plot: estimate (± interval) per activity, one row per sex. Zero line in the middle. */
export default function EstimatesChart({ estimates, units }: { estimates: Estimate[]; units?: string }) {
  const activities = [...new Set(estimates.map((e) => e.activity))];
  const values = estimates.flatMap((e) => [e.estimate, e.ci_low ?? e.estimate, e.ci_high ?? e.estimate]);
  const max = Math.max(1, ...values.map(Math.abs)) * 1.1;

  const rowH = 18;
  const labelW = 150;
  const plotW = 460;
  const x = (v: number) => labelW + ((v + max) / (2 * max)) * plotW;

  // Group rows by activity, with a small gap between groups.
  const rows: { e: Estimate; cy: number }[] = [];
  let y = 10;
  for (const a of activities) {
    y += 10;
    for (const e of estimates.filter((r) => r.activity === a)) {
      rows.push({ e, cy: y + rowH / 2 });
      y += rowH;
    }
  }
  const height = y + 30;

  return (
    <figure className="space-y-2">
      <svg
        viewBox={`0 0 ${labelW + plotW + 10} ${height}`}
        className="w-full max-w-3xl"
        role="img"
        aria-label="Estimated minutes per activity by sex"
      >
        <line x1={x(0)} x2={x(0)} y1={0} y2={height - 20} stroke="var(--line)" />
        {rows.map(({ e, cy }, i) => {
          const color = SEX_COLOR[e.sex.toLowerCase()] ?? "var(--accent)";
          return (
            <g key={i}>
              <text x={0} y={cy + 4} fontSize={11} fill="var(--foreground)">
                {e.activity} · {e.sex}
              </text>
              {e.ci_low != null && e.ci_high != null && (
                <line x1={x(e.ci_low)} x2={x(e.ci_high)} y1={cy} y2={cy} stroke={color} strokeWidth={2} />
              )}
              <circle cx={x(e.estimate)} cy={cy} r={4} fill={color} />
            </g>
          );
        })}
        <text x={x(-max)} y={height - 4} fontSize={10} fill="var(--muted)">
          {(-max).toFixed(0)}
        </text>
        <text x={x(0)} y={height - 4} fontSize={10} fill="var(--muted)" textAnchor="middle">
          0
        </text>
        <text x={x(max)} y={height - 4} fontSize={10} fill="var(--muted)" textAnchor="end">
          {max.toFixed(0)}
        </text>
      </svg>
      <figcaption className="text-xs text-muted">
        {units ?? "Minutes (Mon–Fri totals)"}. Lines show the reported interval.
      </figcaption>
    </figure>
  );
}
