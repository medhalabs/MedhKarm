import { apiGet } from "@/shared/api/client";

import type { Run } from "../types";

export function listRuns(limit = 50): Promise<Run[]> {
  return apiGet<Run[]>(`/runs?limit=${limit}`, { cache: "no-store" });
}
