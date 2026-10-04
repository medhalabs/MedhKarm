"use server";

// Sign-up, log-in and log-out. The session token from the backend lives in an httpOnly cookie,
// so the browser's scripts never see it; the API client adds it to every backend call.

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ApiError, apiPost } from "@/shared/api/client";
import { SESSION_COOKIE, SESSION_DAYS } from "@/shared/api/session";

import { parseLogIn, parseSignUp } from "../parseForms";
import type { FormState, Session } from "../types";

async function keep(session: Session): Promise<void> {
  (await cookies()).set(SESSION_COOKIE, session.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_DAYS * 86_400,
  });
}

export async function signUpAction(_previous: FormState, form: FormData): Promise<FormState> {
  const input = parseSignUp(form);
  if ("error" in input) return { error: input.error };
  try {
    await keep(await apiPost<Session>("/auth/signup", input));
  } catch (error) {
    return { error: describe(error) };
  }
  redirect("/admin");
}

export async function logInAction(_previous: FormState, form: FormData): Promise<FormState> {
  const input = parseLogIn(form);
  if ("error" in input) return { error: input.error };
  try {
    await keep(await apiPost<Session>("/auth/login", input));
  } catch (error) {
    return { error: describe(error) };
  }
  redirect("/admin");
}

export async function logOutAction(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/login");
}

function describe(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Couldn't reach the backend. Is it running on port 8000?";
}
