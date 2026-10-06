"use server";

import { refresh } from "next/cache";

import { ApiError, apiDelete, apiPut } from "@/shared/api/client";

import { parseSettings } from "../parseSettings";
import type { FormState } from "../types";

function query(projectId: string): string {
  return projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
}

export async function saveAutonomyAction(
  projectId: string,
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  try {
    await apiPut(`/settings/autonomy${query(projectId)}`, parseSettings(form));
  } catch (error) {
    return { error: error instanceof ApiError ? error.message : "Couldn't save the settings." };
  }
  refresh();
  return { error: null, saved: true };
}

/** A project goes back to the company's settings. */
export async function resetAutonomyAction(projectId: string): Promise<void> {
  await apiDelete(`/settings/autonomy${query(projectId)}`);
  refresh();
}
