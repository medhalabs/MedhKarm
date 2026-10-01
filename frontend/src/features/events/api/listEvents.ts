import { apiGet, apiUrl } from "@/shared/api/client";

import type { ActivityEvent } from "../types";

export function listEvents(runId: string): Promise<ActivityEvent[]> {
  return apiGet<ActivityEvent[]>(`/runs/${encodeURIComponent(runId)}/events?limit=1000`, {
    cache: "no-store",
  });
}

/** Server-sent events: everything after `afterId`, live (backend events/router.py). */
export function eventStreamUrl(runId: string, afterId: number): string {
  return apiUrl(`/runs/${encodeURIComponent(runId)}/events/stream?after_id=${afterId}`);
}
