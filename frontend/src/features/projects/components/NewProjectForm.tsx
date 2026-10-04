"use client";

import { useActionState } from "react";

import { StackFields } from "@/features/starters";

import { createProjectAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };
const field =
  "rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-normal dark:border-zinc-700";

export function NewProjectForm() {
  const [state, formAction, pending] = useActionState(createProjectAction, initial);

  return (
    <form
      action={formAction}
      className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800"
    >
      <h2 className="font-semibold">New project</h2>
      <label className="flex flex-col gap-1 text-sm font-medium">
        Name
        <input
          name="name"
          required
          minLength={2}
          maxLength={80}
          placeholder="Clinic booking"
          className={field}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium">
        Goal: what should it do, in your words?
        <textarea
          name="goal"
          required
          minLength={10}
          maxLength={5000}
          rows={3}
          placeholder="Patients book a slot with a doctor, get a reminder the day before, and the clinic sees today's bookings."
          className={field}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium">
        Existing GitHub repository (optional; leave empty for a new project)
        <input
          name="repo_url"
          placeholder="https://github.com/you/your-app"
          className={`${field} font-mono text-sm`}
        />
      </label>
      <StackFields />
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" name="autopilot" />
          Autopilot: work through the backlog on its own
        </label>
        <label className="flex items-center gap-2">
          Items per day
          <input
            name="daily_limit"
            type="number"
            min={1}
            max={10}
            defaultValue={2}
            className={`${field} w-16 py-1`}
          />
        </label>
        <button
          type="submit"
          disabled={pending}
          className="ml-auto rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {pending ? "Creating…" : "Create and plan"}
        </button>
      </div>
      {state.error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {state.error}
        </p>
      )}
    </form>
  );
}
