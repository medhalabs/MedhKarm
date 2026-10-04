import { ApiError, apiGet } from "@/shared/api/client";

import type { Project, ProjectDetail } from "../types";

export function listProjects(): Promise<Project[]> {
  return apiGet<Project[]>("/projects", { cache: "no-store" });
}

/** The project with its backlog, or null when the backend doesn't know it. */
export async function getProject(projectId: string): Promise<ProjectDetail | null> {
  try {
    return await apiGet<ProjectDetail>(`/projects/${encodeURIComponent(projectId)}`, {
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
