import "server-only";
import { existsSync } from "node:fs";
import path from "node:path";
import { connection } from "next/server";
import snapshot from "@/data/discovery-snapshot.json";
import { collectArtifacts } from "./collect.mjs";
import { buildDiscovery } from "./model";
import type { DiscoveryMode, DiscoveryPayload, RawArtifact } from "./types";

// LIVE reads the repository the agents write into. By default that is the parent of web/;
// DISCOVERY_REPO_ROOT overrides it when the web app runs from somewhere else.
function repoRoot(): string {
  return process.env.DISCOVERY_REPO_ROOT ?? path.resolve(process.cwd(), "..");
}

export async function getDiscovery(mode: DiscoveryMode, session?: string): Promise<DiscoveryPayload> {
  await connection();
  const root = repoRoot();
  const liveReachable = existsSync(path.join(root, "reports", "experiments"));

  let raw: RawArtifact[];
  let source: string;
  let commit: string | null = null;
  if (mode === "live" && liveReachable) {
    raw = (await collectArtifacts(root)) as RawArtifact[];
    source = "reports/ on this machine";
  } else {
    raw = snapshot.artifacts as RawArtifact[];
    commit = snapshot.commit || null;
    source = commit ? `committed artifacts @ ${commit.slice(0, 7)}` : "committed artifacts";
  }
  if (session) raw = raw.filter((a) => a.session == null || a.session === session);

  return {
    discovery: buildDiscovery(raw),
    mode,
    liveUnavailable: mode === "live" && !liveReachable,
    source,
    commit,
    loadedAt: new Date().toISOString(),
  };
}
