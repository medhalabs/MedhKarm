import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { env } from "../config";
import type { AuthProvider, AuthResult, User } from "./types";

async function client() {
  const store = await cookies();
  return createServerClient(env("NEXT_PUBLIC_SUPABASE_URL")!, env("NEXT_PUBLIC_SUPABASE_ANON_KEY")!, {
    cookies: {
      getAll: () => store.getAll(),
      setAll: (list) => {
        try {
          list.forEach(({ name, value, options }) => store.set(name, value, options));
        } catch {
          // Called from a server component: the session refreshes on the next action.
        }
      },
    },
  });
}

function toUser(user: { id: string; email?: string; user_metadata?: Record<string, unknown> }): User {
  const name = user.user_metadata?.name;
  return { id: user.id, email: user.email ?? "", name: typeof name === "string" ? name : undefined };
}

/** Supabase Auth: accounts live in the founder's Supabase project. */
export class SupabaseAuth implements AuthProvider {
  async currentUser(): Promise<User | null> {
    const { data } = await (await client()).auth.getUser();
    return data.user ? toUser(data.user) : null;
  }

  async signUp(email: string, password: string, name?: string): Promise<AuthResult> {
    const { data, error } = await (await client()).auth.signUp({
      email,
      password,
      options: { data: name ? { name } : {} },
    });
    if (error || !data.user) return { error: error?.message ?? "Couldn't create the account." };
    return { user: toUser(data.user) };
  }

  async logIn(email: string, password: string): Promise<AuthResult> {
    const { data, error } = await (await client()).auth.signInWithPassword({ email, password });
    if (error || !data.user) return { error: "Wrong email or password." };
    return { user: toUser(data.user) };
  }

  async logOut(): Promise<void> {
    await (await client()).auth.signOut();
  }
}
