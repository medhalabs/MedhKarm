"use server";

// Server actions for the admin forms. They run on the Next.js server and call the backend API
// as the signed-in founder (the API client adds their session token).

import { refresh } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiPost } from "@/shared/api/client";

import { briefBody } from "../briefBody";
import { parseDecision, parseStartRun } from "../parseForms";
import type { Brief, FormState, IntakeReply, Run, Turn } from "../types";

export async function startRunAction(_previous: FormState, form: FormData): Promise<FormState> {
  const input = parseStartRun(form);
  if ("error" in input) return { error: input.error };
  let run: Run;
  try {
    run = await apiPost<Run>("/runs", input);
  } catch (error) {
    return { error: describeError(error) };
  }
  redirect(`/admin/runs/${run.id}`);
}

/** One turn of the conversation with the CTO (the conversation itself lives in the browser). */
export async function intakeAction(
  turns: Turn[],
): Promise<{ reply: IntakeReply } | { error: string }> {
  try {
    return { reply: await apiPost<IntakeReply>("/intake", { turns }) };
  } catch (error) {
    return { error: describeError(error) };
  }
}

/** Start the run the conversation agreed on. */
export async function startFromBriefAction(brief: Brief): Promise<{ error: string }> {
  let run: Run;
  try {
    run = await apiPost<Run>("/runs", briefBody(brief));
  } catch (error) {
    return { error: describeError(error) };
  }
  redirect(`/admin/runs/${run.id}`);
}

export async function decideAction(
  runId: string,
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  const input = parseDecision(form);
  if ("error" in input) return { error: input.error };
  try {
    await apiPost<Run>(`/runs/${encodeURIComponent(runId)}/approval`, input);
  } catch (error) {
    return { error: describeError(error) };
  }
  refresh();
  return { error: null };
}

export async function cancelRunAction(runId: string): Promise<void> {
  await apiPost<Run>(`/runs/${encodeURIComponent(runId)}/cancel`, {});
  refresh();
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Couldn't reach the backend. Is it running on port 8000?";
}
