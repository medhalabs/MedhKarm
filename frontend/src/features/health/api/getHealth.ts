import { apiGet } from "@/shared/api/client";

import type { HealthStatus } from "../types";

export function getHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>("/health", { cache: "no-store" });
}
