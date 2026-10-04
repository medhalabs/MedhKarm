"use client";

import { useActionState } from "react";

import { addItemAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };
const field =
  "rounded-md border border-zinc-300 bg-transparent px-3 py-1.5 text-sm dark:border-zinc-700";

export function AddItemForm({ projectId }: { projectId: string }) {
  const [state, formAction, pending] = useActionState(addItemAction.bind(null, projectId), initial);
  return (
    <details className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
      <summary className="cursor-pointer text-sm font-medium">Add an item</summary>
      <form action={formAction} className="mt-3 flex flex-col gap-2">
        <input
          name="title"
          required
          minLength={3}
          maxLength={120}
          placeholder="Title"
          className={field}
        />
        <textarea
          name="description"
          rows={2}
          placeholder="What and why (optional)"
          className={field}
        />
        <textarea
          name="acceptance"
          rows={2}
          placeholder="Done when… (one check per line)"
          className={field}
        />
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={pending}
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {pending ? "Adding…" : "Add to the end"}
          </button>
          {state.error && (
            <span role="alert" className="text-xs text-red-600 dark:text-red-400">
              {state.error}
            </span>
          )}
        </div>
      </form>
    </details>
  );
}
