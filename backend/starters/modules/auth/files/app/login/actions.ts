"use server";

import { redirect } from "next/navigation";
import { getAuth } from "@/lib/auth";

export type FormState = { error?: string };

function field(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}

export async function logIn(_: FormState, form: FormData): Promise<FormState> {
  const result = await getAuth().logIn(field(form, "email"), field(form, "password"));
  if ("error" in result) return { error: result.error };
  redirect("/account");
}

export async function signUp(_: FormState, form: FormData): Promise<FormState> {
  const result = await getAuth().signUp(
    field(form, "email"),
    field(form, "password"),
    field(form, "name"),
  );
  if ("error" in result) return { error: result.error };
  redirect("/account");
}

export async function logOut(): Promise<void> {
  await getAuth().logOut();
  redirect("/login");
}
