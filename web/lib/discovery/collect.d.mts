import type { RawArtifact } from "./types";

export function compactResult(result: unknown): unknown;
export function collectArtifacts(repoRoot: string, options?: { include?: (relPath: string) => boolean }): Promise<RawArtifact[]>;
