import { apiGet } from "@/shared/api/client";

import type { Artifact } from "../types";

export function listArtifacts(runId: string, kind?: string): Promise<Artifact[]> {
  const query = kind ? `?kind=${encodeURIComponent(kind)}` : "";
  return apiGet<Artifact[]>(`/runs/${encodeURIComponent(runId)}/artifacts${query}`, {
    cache: "no-store",
  });
}
