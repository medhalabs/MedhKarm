import { apiGet } from "@/shared/api/client";

import type { Signoff } from "../types";

export function getSignoffs(runId: string): Promise<Signoff[]> {
  return apiGet<Signoff[]>(`/runs/${encodeURIComponent(runId)}/signoffs`, { cache: "no-store" });
}
