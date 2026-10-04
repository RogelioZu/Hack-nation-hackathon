import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { getProjects } from "@/lib/data";
import PageHeader from "../_components/PageHeader";

export const metadata = { title: "Audit trail · tiemPO" };

export default async function AuditPage() {
  let projects: Awaited<ReturnType<typeof getProjects>> = [];
  let error: string | null = null;
  try {
    projects = await getProjects();
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <>
      <PageHeader title="Audit trail" />
      <main className="space-y-6 px-4 pb-10 md:px-8">
        <section className="rounded-lg bg-white p-6">
          <h1 className="text-h1 text-gray-900">Research cases in the database</h1>
          <p className="mt-2 max-w-[70ch] text-[15px] leading-6 text-gray-700">
            Every agent tool call, proposal, run and decision that the Omnigent tools persist in Supabase. The discovery spine reads the JSON
            artifacts in the repository; this view is the database side of the same audit trail. All times are total Monday–Friday minutes,
            and every result is an observational association.
          </p>
        </section>

        {error ? (
          <p className="rounded-lg bg-white p-6 text-body text-gray-700">
            The database is not reachable from this deployment: {error}
          </p>
        ) : projects.length === 0 ? (
          <p className="rounded-lg bg-white p-6 text-body text-gray-700">No research cases yet.</p>
        ) : (
          <ul className="space-y-2">
            {projects.map((p) => (
              <li key={p.id}>
                <Link
                  href={`/research/${p.id}`}
                  className="flex items-center gap-4 rounded-md bg-white p-4 transition-colors duration-[120ms] hover:bg-blue-50"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-title-card text-gray-900">{p.title}</span>
                      {p.is_demo && (
                        <span className="rounded-sm bg-yellow-400 px-2 py-0.5 text-micro text-gray-900 uppercase">Demo data</span>
                      )}
                      <span className="rounded-sm bg-gray-50 px-2 py-0.5 font-mono text-caption text-gray-700">
                        {p.status}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-body-sm text-gray-700">{p.question}</p>
                  </div>
                  <ChevronRight aria-hidden size={18} className="shrink-0 text-gray-500" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
