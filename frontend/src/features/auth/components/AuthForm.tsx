"use client";

import Link from "next/link";
import { useActionState } from "react";

import { logInAction, signUpAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };
const field =
  "rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-normal dark:border-zinc-700";

/** Log in, or create an account (and the founder's company). */
export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const signup = mode === "signup";
  const [state, formAction, pending] = useActionState(signup ? signUpAction : logInAction, initial);

  return (
    <form
      action={formAction}
      className="flex w-full max-w-sm flex-col gap-3 rounded-lg border border-zinc-200 p-6 dark:border-zinc-800"
    >
      <h1 className="text-xl font-semibold">{signup ? "Create your account" : "Log in"}</h1>
      {signup && (
        <>
          <label className="flex flex-col gap-1 text-sm font-medium">
            Your name
            <input name="name" autoComplete="name" maxLength={80} className={field} />
          </label>
          <label className="flex flex-col gap-1 text-sm font-medium">
            Company or project name
            <input name="company_name" required minLength={2} maxLength={120} className={field} />
          </label>
        </>
      )}
      <label className="flex flex-col gap-1 text-sm font-medium">
        Email
        <input name="email" type="email" required autoComplete="email" className={field} />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium">
        Password
        <input
          name="password"
          type="password"
          required
          minLength={signup ? 8 : undefined}
          autoComplete={signup ? "new-password" : "current-password"}
          className={field}
        />
      </label>
      {state.error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {state.error}
        </p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {pending ? "Please wait…" : signup ? "Create account" : "Log in"}
      </button>
      <p className="text-sm text-zinc-500">
        {signup ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="underline">
              Log in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link href="/signup" className="underline">
              Create an account
            </Link>
          </>
        )}
      </p>
    </form>
  );
}
