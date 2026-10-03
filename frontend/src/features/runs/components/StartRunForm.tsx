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
      <div className="flex flex-wrap gap-3">
        <label className="flex min-w-60 flex-[3] flex-col gap-1 text-sm font-medium">
          Existing GitHub repo (optional)
          <input
            name="repo_url"
            type="url"
            maxLength={300}
            placeholder="https://github.com/you/your-project"
            className="rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-mono text-sm font-normal dark:border-zinc-700"
          />
        </label>
        <label className="flex min-w-32 flex-1 flex-col gap-1 text-sm font-medium">
          Branch
          <input
            name="repo_branch"
            maxLength={200}
            placeholder="default"
            className="rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-mono text-sm font-normal dark:border-zinc-700"
          />
        </label>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" name="create_repo" defaultChecked />
          No repo above? Create a private GitHub repo when released
        </label>
        <label className="flex min-w-48 flex-1 flex-col gap-1 text-sm font-medium">
          New repo name
          <input
            name="new_repo_name"
            maxLength={100}
            placeholder="made from the request"
            className="rounded-md border border-zinc-300 bg-transparent px-3 py-2 font-mono text-sm font-normal dark:border-zinc-700"
          />
        </label>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-1 flex-col gap-1 text-sm font-medium">
          Test command (decides when it&apos;s done; detected for a repo if empty)
          <input
            name="test_command"
            placeholder="python -m pytest -q"
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
