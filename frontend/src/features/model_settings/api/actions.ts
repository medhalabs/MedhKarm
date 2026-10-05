"use server";

import { refresh } from "next/cache";

import { ApiError, apiDelete, apiPost, apiPut } from "@/shared/api/client";

import { parseChoices } from "../parseChoices";
import type { FormState, KeyCheck, Provider } from "../types";

function message(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export async function saveChoicesAction(_previous: FormState, form: FormData): Promise<FormState> {
  const roles = String(form.get("roles") ?? "")
    .split(",")
    .filter(Boolean);
  try {
    await apiPut("/settings/models", parseChoices(form, roles));
  } catch (error) {
    return { error: message(error, "Couldn't save the models.") };
  }
  refresh();
  return { error: null, saved: true };
}

export async function addKeyAction(_previous: FormState, form: FormData): Promise<FormState> {
  const provider = String(form.get("provider") ?? "") as Provider;
  const key = String(form.get("key") ?? "").trim();
  if (key.length < 8) return { error: "Paste the whole key." };
  try {
    await apiPost("/settings/models/keys", { provider, key });
    const check = await apiPost<KeyCheck>(`/settings/models/keys/${provider}/check`, {});
    refresh();
    return { error: null, saved: true, check };
  } catch (error) {
    return { error: message(error, "Couldn't save the key.") };
  }
}

export async function checkKeyAction(_previous: FormState, form: FormData): Promise<FormState> {
  const provider = String(form.get("provider") ?? "") as Provider;
  try {
    const check = await apiPost<KeyCheck>(`/settings/models/keys/${provider}/check`, {});
    return { error: null, check };
  } catch (error) {
    return { error: message(error, "Couldn't check the key.") };
  }
}

export async function removeKeyAction(_previous: FormState, form: FormData): Promise<FormState> {
  const provider = String(form.get("provider") ?? "") as Provider;
  try {
    await apiDelete(`/settings/models/keys/${provider}`);
  } catch (error) {
    return { error: message(error, "Couldn't remove the key.") };
  }
  refresh();
  return { error: null };
}
