import { apiGet } from "@/shared/api/client";

import type { ActivityEvent } from "../types";

export function listEvents(runId: string): Promise<ActivityEvent[]> {
  return apiGet<ActivityEvent[]>(`/runs/${encodeURIComponent(runId)}/events?limit=1000`, {
    cache: "no-store",
  });
}
