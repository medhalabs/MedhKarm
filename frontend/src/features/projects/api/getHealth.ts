import { apiGet } from "@/shared/api/client";

import type { ProjectHealth } from "../types";

/** Priya's report on a project: progress, model tokens used, and whether it is moving. */
export async function getProjectHealth(projectId: string): Promise<ProjectHealth | null> {
  try {
    return await apiGet<ProjectHealth>(`/projects/${encodeURIComponent(projectId)}/health`, {
      cache: "no-store",
    });
  } catch {
    return null; // the report is a bonus: the page works without it
  }
}
