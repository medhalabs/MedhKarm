"use client";

import { useActionState } from "react";

import { projectAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };

/** Autopilot on or off, and how many items it may start per day. */
export function AutopilotForm({
  projectId,
  autopilot,
  dailyLimit,
}: {
  projectId: string;
  autopilot: boolean;
  dailyLimit: number;
}) {
  const [state, formAction, pending] = useActionState(projectAction, initial);
  return (
    <form action={formAction} className="flex flex-wrap items-center gap-3 text-sm">
      <input type="hidden" name="op" value="autopilot" />
      <input type="hidden" name="project_id" value={projectId} />
      <label className="flex items-center gap-2">
        <input type="checkbox" name="value" defaultChecked={autopilot} />
        Autopilot
      </label>
      <label className="flex items-center gap-2">
        up to
        <input
          name="daily_limit"
          type="number"
          min={1}
          max={10}
          defaultValue={dailyLimit}
          className="w-14 rounded-md border border-zinc-300 bg-transparent px-2 py-1 dark:border-zinc-700"
        />
        items a day
      </label>
      <button
        type="submit"
        disabled={pending}
        className="rounded-md border border-zinc-300 px-3 py-1 font-medium disabled:opacity-50 dark:border-zinc-700"
      >
        {pending ? "Saving…" : "Save"}
      </button>
      {state.error && (
        <span role="alert" className="text-xs text-red-600 dark:text-red-400">
          {state.error}
        </span>
      )}
    </form>
  );
}
