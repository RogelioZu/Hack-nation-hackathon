import { getDiscovery } from "@/lib/discovery/load";
import DiscoveryView from "./_components/discovery/DiscoveryView";

export default async function DiscoveryPage({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const mode = params.mode === "live" ? "live" : "replay";
  const session = typeof params.session === "string" && /^[\w-]+$/.test(params.session) ? params.session : undefined;
  const stage = typeof params.stage === "string" ? Number.parseInt(params.stage, 10) : NaN;
  const payload = await getDiscovery(mode, session);
  const initialStage = mode === "replay" && stage >= 1 && stage <= payload.run.stages.length ? stage - 1 : undefined;
  // ?view=full opens the whole record at once; otherwise replay starts from the question composer.
  const full = params.view === "full";
  // ?start=1 (the reading guide's buttons) opens the page with the investigation already running.
  const autostart = params.start === "1";
  return <DiscoveryView payload={payload} session={session} initialStage={initialStage} full={full} autostart={autostart} />;
}
