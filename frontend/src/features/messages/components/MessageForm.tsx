"use client";

import { useActionState } from "react";

import { sendMessageAction } from "../api/actions";
import { AGENTS, type FormState } from "../types";

const initial: FormState = { error: null };

export function MessageForm({ thread, threadId }: { thread: "run" | "project"; threadId: string }) {
  const [state, formAction, pending] = useActionState(
    sendMessageAction.bind(null, thread, threadId),
    initial,
  );
  return (
    <form action={formAction} className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label htmlFor={`to-${threadId}`} className="font-medium">
          To
        </label>
        <select
          id={`to-${threadId}`}
          name="to"
          defaultValue={thread === "run" ? "cto" : "pm"}
          className="field"
        >
          {AGENTS.map((a) => (
            <option key={a.role} value={a.role}>
              {a.label}
            </option>
          ))}
        </select>
      </div>
      <textarea
        name="body"
        rows={2}
        maxLength={10000}
        required
        aria-label="Message"
        placeholder={
          thread === "run"
            ? "A note for the team: it goes into their next task"
            : "A note for the PM: it goes into the next backlog plan"
        }
        className="rounded-md border border-zinc-300 bg-transparent px-3 py-2 text-sm dark:border-zinc-700"
      />
      <div className="flex items-center gap-3">
        <button type="submit" disabled={pending} className="btn-primary">
          {pending ? "Sending…" : "Send"}
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
