"use server";

import { ApiError, apiPost } from "@/shared/api/client";

import type { FormState, Joined } from "../types";

export async function joinWaitlistAction(_previous: FormState, form: FormData): Promise<FormState> {
  const email = String(form.get("email") ?? "").trim();
  if (!email.includes("@")) return { error: "Enter your email so we can write to you." };
  try {
    const joined = await apiPost<Joined>("/public/waitlist", {
      email,
      name: String(form.get("name") ?? ""),
      building: String(form.get("building") ?? ""),
      source: String(form.get("source") ?? ""),
      website: String(form.get("website") ?? ""), // the hidden field: only bots fill it in
    });
    return { error: null, joined: true, count: joined.count };
  } catch (error) {
    if (error instanceof ApiError && error.status === 429) {
      return { error: "That's a lot of sign-ups from here. Try again in a while." };
    }
    return { error: error instanceof ApiError ? error.message : "Couldn't join. Try again?" };
  }
}
