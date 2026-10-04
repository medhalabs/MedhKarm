"use server";

// Server actions for the projects pages. They run on the Next.js server and call the backend.
// No sign-in yet: like the API itself, keep the admin page on localhost until auth lands.

import { refresh } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiDelete, apiPatch, apiPost } from "@/shared/api/client";

import { parseNewItem, parseNewProject } from "../parseForms";
import type { FormState, ProjectDetail } from "../types";

export async function createProjectAction(
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  const input = parseNewProject(form);
  if ("error" in input) return { error: input.error };
  let project: ProjectDetail;
  try {
    project = await apiPost<ProjectDetail>("/projects", input);
  } catch (error) {
    return { error: describeError(error) };
  }
  redirect(`/admin/projects/${project.id}`);
}

export async function addItemAction(
  projectId: string,
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  const input = parseNewItem(form);
  if ("error" in input) return { error: input.error };
  return run(() => apiPost(`/projects/${enc(projectId)}/items`, input));
}

/** One button on the project page: `op` names it; item buttons also send `item_id`. */
export async function projectAction(_previous: FormState, form: FormData): Promise<FormState> {
  const projectId = enc(String(form.get("project_id") ?? ""));
  const item = `/projects/${projectId}/items/${enc(String(form.get("item_id") ?? ""))}`;
  const position = Number(form.get("position") ?? 0);
  switch (String(form.get("op"))) {
    case "approve":
      return run(() => apiPost(`/projects/${projectId}/plan/approve`, {}));
    case "replan":
      return run(() => apiPost(`/projects/${projectId}/plan`, {}));
    case "next":
      return run(() => apiPost(`/projects/${projectId}/next`, {}));
    case "pause":
      return run(() => apiPost(`/projects/${projectId}/pause`, {}));
    case "resume":
      return run(() => apiPost(`/projects/${projectId}/resume`, {}));
    case "autopilot":
      return run(() =>
        apiPatch(`/projects/${projectId}`, {
          autopilot: form.get("value") === "on",
          daily_limit: Number(form.get("daily_limit") ?? 2),
        }),
      );
    case "move":
      return run(() => apiPatch(item, { position }));
    case "skip":
      return run(() => apiPost(`${item}/skip`, {}));
    case "retry":
      return run(() => apiPost(`${item}/retry`, {}));
    case "delete":
      return run(() => apiDelete(item));
    default:
      return { error: "Unknown action" };
  }
}

async function run(call: () => Promise<unknown>): Promise<FormState> {
  try {
    await call();
  } catch (error) {
    return { error: describeError(error) };
  }
  refresh();
  return { error: null };
}

function enc(value: string): string {
  return encodeURIComponent(value);
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Couldn't reach the backend. Is it running on port 8000?";
}
