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
    <details className="card p-4">
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
          <button type="submit" disabled={pending} className="btn-primary">
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
