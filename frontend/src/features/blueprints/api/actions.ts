"use server";

import { refresh } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiPost } from "@/shared/api/client";

import type { Blueprint, FormState } from "../types";

function message(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

/** Ask Lekha for the plan. `brief` is the agreed brief in the shape of starting a run. */
export async function askForPlanAction(brief: object): Promise<{ error: string }> {
  let blueprint: Blueprint;
  try {
    blueprint = await apiPost<Blueprint>("/blueprints", { brief });
  } catch (error) {
    return { error: message(error, "Couldn't ask for the plan.") };
  }
  redirect(`/admin/blueprints/${blueprint.id}`);
}

export async function commentAction(
  blueprintId: string,
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  const text = String(form.get("text") ?? "").trim();
  if (!text) return { error: "Write what you'd like changed." };
  try {
    await apiPost(`/blueprints/${encodeURIComponent(blueprintId)}/comments`, { text });
  } catch (error) {
    return { error: message(error, "Couldn't send your comment.") };
  }
  refresh();
  return { error: null };
}

/** Approve the plan: the team starts building, and we go to the run. */
export async function approveAction(blueprintId: string): Promise<{ error: string }> {
  let blueprint: Blueprint;
  try {
    blueprint = await apiPost<Blueprint>(
      `/blueprints/${encodeURIComponent(blueprintId)}/approve`,
      {},
    );
  } catch (error) {
    return { error: message(error, "Couldn't start the build.") };
  }
  redirect(blueprint.run_id ? `/admin/runs/${blueprint.run_id}` : "/admin");
}

export async function retryAction(blueprintId: string): Promise<void> {
  await apiPost(`/blueprints/${encodeURIComponent(blueprintId)}/retry`, {});
  refresh();
}
