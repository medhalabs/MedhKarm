import { redirect } from "next/navigation";
import { env } from "../config";
import { LocalAuth } from "./local";
import { SupabaseAuth } from "./supabase";
import type { AuthProvider, User } from "./types";

export type { AuthProvider, AuthResult, User } from "./types";

/** Supabase Auth when its keys are set, otherwise local accounts. */
export function getAuth(): AuthProvider {
  return env("NEXT_PUBLIC_SUPABASE_URL") && env("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    ? new SupabaseAuth()
    : new LocalAuth();
}

export function currentUser(): Promise<User | null> {
  return getAuth().currentUser();
}

/** The signed-in user; sends everyone else to /login. */
export async function requireUser(): Promise<User> {
  const user = await currentUser();
  if (!user) redirect("/login");
  return user;
}
