"use client";

import { useActionState } from "react";

import { projectAction } from "../api/actions";
import type { FormState } from "../types";

const initial: FormState = { error: null };

const LOOKS = {
  primary:
    "rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900",
  secondary:
    "rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium disabled:opacity-50 dark:border-zinc-700",
  small:
    "rounded px-1.5 py-0.5 text-xs text-zinc-600 hover:bg-zinc-100 disabled:opacity-50 dark:text-zinc-400 dark:hover:bg-zinc-800",
};

/** A button that runs one project action (approve, start next, skip an item, ...). */
export function ActionButton({
  op,
  projectId,
  itemId,
  fields,
  label,
  look = "secondary",
  title,
}: {
  op: string;
  projectId: string;
  itemId?: string;
  fields?: Record<string, string | number>;
  label: string;
  look?: keyof typeof LOOKS;
  title?: string;
}) {
  const [state, formAction, pending] = useActionState(projectAction, initial);
  return (
    <form action={formAction} className="inline-flex flex-col">
      <input type="hidden" name="op" value={op} />
      <input type="hidden" name="project_id" value={projectId} />
      {itemId && <input type="hidden" name="item_id" value={itemId} />}
      {Object.entries(fields ?? {}).map(([name, value]) => (
        <input key={name} type="hidden" name={name} value={value} />
      ))}
      <button type="submit" disabled={pending} className={LOOKS[look]} title={title}>
        {pending ? "…" : label}
      </button>
      {state.error && (
        <span role="alert" className="mt-1 max-w-xs text-xs text-red-600 dark:text-red-400">
          {state.error}
        </span>
      )}
    </form>
  );
}
