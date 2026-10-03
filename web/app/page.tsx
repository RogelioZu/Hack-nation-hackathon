import Link from "next/link";
import { getProjects } from "@/lib/data";

export default async function Home() {
  const projects = await getProjects();

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">
          How does work commuting relate to the rest of people&rsquo;s week?
        </h1>
        <p className="max-w-3xl text-muted">
          Many residents of Mexico City and Estado de México spend hours each week travelling to work.
          This lab runs an auditable, agent-orchestrated research loop on INEGI&rsquo;s time-use survey (ENUT):
          question → cited evidence → hypotheses → two candidate tests → a reproducible run → critique → the next decision.
        </p>
        <p className="max-w-3xl text-sm text-muted">
          ENUT is observational and cross-sectional: results describe <strong>associations</strong>, not causes.
          All time figures are <strong>weekly</strong> minutes from the survey&rsquo;s reference week.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Research cases</h2>
        {projects.length === 0 ? (
          <p className="text-muted">No research cases yet.</p>
        ) : (
          <ul className="divide-y divide-line rounded-lg border border-line">
            {projects.map((p) => (
              <li key={p.id}>
                <Link href={`/research/${p.id}`} className="block px-4 py-4 hover:bg-panel">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{p.title}</span>
                    {p.is_demo && <DemoBadge />}
                    <span className="ml-auto rounded bg-panel px-2 py-0.5 text-xs text-muted">{p.status}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{p.question}</p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function DemoBadge() {
  return (
    <span className="rounded border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-600">
      demo data
    </span>
  );
}
