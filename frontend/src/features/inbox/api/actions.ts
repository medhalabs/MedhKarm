"use server";

// Acting on inbox items: the same backend endpoints as the run and project pages.

import { refresh } from "next/cache";

import { ApiError, apiPost } from "@/shared/api/client";

import type { FormState } from "../types";

const enc = encodeURIComponent;

export async function decideAction(runId: string, approved: boolean): Promise<void> {
  await apiPost(`/runs/${enc(runId)}/approval`, { approved, feedback: "" });
  refresh();
}

export async function itemAction(
  projectId: string,
  itemId: string,
  op: "retry" | "skip",
): Promise<void> {
  await apiPost(`/projects/${enc(projectId)}/items/${enc(itemId)}/${op}`, {});
  refresh();
}

/** Answers to the PM's questions; empty answers are left for later. */
export async function answerAction(
  projectId: string,
  questions: string[],
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  const answers = questions
    .map((question, i) => ({ question, answer: String(form.get(`answer_${i}`) ?? "").trim() }))
    .filter((a) => a.answer);
  if (answers.length === 0) return { error: "Answer at least one question." };
  try {
    await apiPost(`/projects/${enc(projectId)}/answers`, {
      answers,
      replan: form.get("replan") === "on",
    });
  } catch (error) {
    return { error: error instanceof ApiError ? error.message : "Couldn't save the answers." };
  }
  refresh();
  return { error: null };
}
