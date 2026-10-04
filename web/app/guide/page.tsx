import bundle from "@/data/discovery-run.json";
import type { ReplayBundle, StatusView } from "@/lib/discovery/types";
import Guide from "./Guide";

export const metadata = { title: "Reading guide · tiemPO" };

const run = (bundle as unknown as ReplayBundle).run;

/** Every status the recorded run uses, once each: the glossary is read from the artifacts, never typed in. */
function statusesInRun(): StatusView[] {
  const seen = new Map<string, StatusView>();
  JSON.stringify(run, (_k, v) => {
    if (v && typeof v === "object" && typeof v.code === "string" && typeof v.label === "string" && "tone" in v && !seen.has(v.code)) {
      seen.set(v.code, v as StatusView);
    }
    return v;
  });
  return [...seen.values()];
}

// Only what the guide shows goes to the browser: stages, statuses and the experiments' plain summaries.
export default function GuidePage() {
  return (
    <Guide
      stages={run.stages}
      statuses={statusesInRun()}
      experiments={[...(run.baseline ? [run.baseline] : []), ...run.followUps.map((f) => f.experiment)]}
      populationN={run.dataset?.populationN ?? null}
    />
  );
}
