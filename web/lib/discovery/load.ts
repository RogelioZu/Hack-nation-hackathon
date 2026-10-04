import "server-only";
import { existsSync } from "node:fs";
import path from "node:path";
import { connection } from "next/server";
import bundle from "@/data/discovery-run.json";
import { collectArtifacts } from "./collect.mjs";
import { normalizeDiscoveryRun } from "./model";
import type { DiscoveryMode, DiscoveryPayload, RawArtifact, ReplayBundle } from "./types";

// Two data sources, one view model:
//   REPLAY reads the bundle scripts/snapshot-discovery.mjs built from committed artifacts. It is part of the server
//          build, needs no filesystem, Omnigent or Databricks, and is what Vercel serves.
//   LIVE   reads the repository the agents write into and normalizes it on each request (local only).
// LIVE reads DISCOVERY_REPO_ROOT when set, else the parent of web/.
function repoRoot(): string {
  return process.env.DISCOVERY_REPO_ROOT ?? path.resolve(process.cwd(), "..");
}

const replay = bundle as unknown as ReplayBundle;

export async function getDiscovery(mode: DiscoveryMode, session?: string): Promise<DiscoveryPayload> {
  await connection();
  const loadedAt = new Date().toISOString();
  const root = repoRoot();
  // LIVE is the lab machine reading what the agents write. A deployment only carries files traced at build time (on
  // Vercel these paths get bundled), so it never counts as live; locally LIVE needs the whole layout the agents write
  // into. Otherwise it falls back to the replay bundle and says so.
  const deployed = Boolean(process.env.VERCEL);
  const liveReachable =
    !deployed && ["initial_state.json", "reports/experiments", "reports/discovery"].every((p) => existsSync(path.join(root, p)));

  if (mode === "live" && liveReachable) {
    let raw = (await collectArtifacts(root)) as RawArtifact[];
    if (session) raw = raw.filter((a) => a.session == null || a.session === session);
    return { run: normalizeDiscoveryRun(raw), mode, liveUnavailable: false, source: "reports/ on this machine", commit: null, loadedAt };
  }

  return {
    run: replay.run,
    mode,
    liveUnavailable: mode === "live",
    source: replay.commit ? `committed artifacts @ ${replay.commit.slice(0, 7)}` : "committed artifacts",
    commit: replay.commit,
    loadedAt,
  };
}
