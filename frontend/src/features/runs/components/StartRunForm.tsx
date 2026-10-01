"use client";

import { useActionState } from "react";

import { startRunAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };

export function StartRunForm() {
  const [state, formAction, pending] = useActionState(startRunAction, initial);

  return (
    <form
      action={formAction}
      className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800"
    >
      <label className="flex flex-col gap-1 text-sm font-medium">
        What should the team build?
        <textarea
          name="request"
          required
          minLength={3}
          maxLength={5000}
          rows={3}
          placeholder="Create slugify.py with slugify(text) and pytest tests in test_slugify.py"
          className="rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-normal dark:border-zinc-700"
        />
      </label>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-1 flex-col gap-1 text-sm font-medium">
          Test command (decides when it&apos;s done)
          <input
            name="test_command"
            defaultValue="python -m pytest -q"
            maxLength={500}
            className="rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-mono text-sm font-normal dark:border-zinc-700"
          />
        </label>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {pending ? "Starting…" : "Start run"}
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
