"use server";

import { refresh } from "next/cache";

import { ApiError, apiPost, apiPut } from "@/shared/api/client";

import { parseSettings } from "../parseForm";
import type { Delivery, FormState } from "../types";

export async function saveSettingsAction(_previous: FormState, form: FormData): Promise<FormState> {
  const input = parseSettings(form);
  if ("error" in input) return { error: input.error };
  try {
    await apiPut("/settings/notifications", input);
  } catch (error) {
    return { error: error instanceof ApiError ? error.message : "Couldn't save the settings." };
  }
  refresh();
  return { error: null, saved: true };
}

export async function sendTestAction(): Promise<FormState> {
  try {
    const results = await apiPost<Delivery[]>("/settings/notifications/test", {});
    if (results.length === 0) return { error: "Add an email or WhatsApp number and save first." };
    return { error: null, results };
  } catch (error) {
    return { error: error instanceof ApiError ? error.message : "Couldn't send the test." };
  }
}
