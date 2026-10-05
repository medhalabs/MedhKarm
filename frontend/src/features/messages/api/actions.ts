"use server";

import { refresh } from "next/cache";

import { ApiError, apiPost } from "@/shared/api/client";

import type { FormState } from "../types";

/** The founder writes to an agent; the reply arrives a little later (a worker writes it). */
export async function sendMessageAction(
  thread: "run" | "project",
  threadId: string,
  _previous: FormState,
  form: FormData,
): Promise<FormState> {
  const body = String(form.get("body") ?? "").trim();
  const to = String(form.get("to") ?? (thread === "run" ? "cto" : "pm"));
  if (!body) return { error: "Write something first." };
  if (body.length > 10000) return { error: "Keep it under 10,000 characters." };
  try {
    await apiPost("/messages", {
      [thread === "run" ? "run_id" : "project_id"]: threadId,
      to,
      body,
    });
  } catch (error) {
    return { error: error instanceof ApiError ? error.message : "Couldn't send the message." };
  }
  refresh();
  return { error: null };
}
