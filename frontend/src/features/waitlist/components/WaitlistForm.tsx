"use client";

import { useActionState } from "react";

import { joinWaitlistAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };

/** Join the waitlist: an email and, if they like, what they want to build. `source` says where
 * they came from (e.g. "share"). The hidden `website` field is for bots. */
export function WaitlistForm({ source = "" }: { source?: string }) {
  const [state, join, joining] = useActionState(joinWaitlistAction, initial);
  if (state.joined) {
    return (
      <p
        role="status"
        className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200"
      >
        You&apos;re on the list{state.count ? ` (one of ${state.count})` : ""}. We&apos;ll write to
        you when your invite is ready.
      </p>
    );
  }
  return (
    <form action={join} className="flex flex-col gap-3">
      <input type="hidden" name="source" value={source} />
      <div aria-hidden="true" className="absolute -left-[9999px]">
        <label>
          Website
          <input name="website" tabIndex={-1} autoComplete="off" />
        </label>
      </div>
      <label className="flex flex-col gap-1 text-sm font-medium">
        Your email
        <input name="email" type="email" required autoComplete="email" className="field" />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium">
        What would you like to build? <span className="font-normal text-zinc-500">(optional)</span>
        <textarea
          name="building"
          rows={2}
          maxLength={600}
          placeholder="e.g. an ordering app for my coffee shop"
          className="field"
        />
      </label>
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" disabled={joining} className="btn-primary">
          {joining ? "Joining…" : "Join the waitlist"}
        </button>
        {state.error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {state.error}
          </p>
        )}
      </div>
    </form>
  );
}
