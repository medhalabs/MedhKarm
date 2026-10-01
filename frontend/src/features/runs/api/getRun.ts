import { ApiError, apiGet } from "@/shared/api/client";

import type { Run } from "../types";

/** The run, or null when the backend doesn't know it. */
export async function getRun(runId: string): Promise<Run | null> {
  try {
    return await apiGet<Run>(`/runs/${encodeURIComponent(runId)}`, { cache: "no-store" });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
