import { apiGet } from "@/shared/api/client";

import type { AutonomyView } from "../types";

export function getAutonomy(projectId?: string): Promise<AutonomyView> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return apiGet<AutonomyView>(`/settings/autonomy${query}`, { cache: "no-store" });
}
