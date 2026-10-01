"use client";

import { useActionState } from "react";

import { formatNumber } from "@/shared/lib/format";

import { decideAction } from "../api/actions";
import type { FormState, Gate } from "../types";

const initial: FormState = { error: null };

/** The release gate: why the founder is asked, what changed, and approve / reject. */
export function ApprovalPanel({ runId, gate }: { runId: string; gate: Gate }) {
  const [state, formAction, pending] = useActionState(decideAction.bind(null, runId), initial);
  const byRule = gate.rules.length > 0;

  return (
    <section className="flex flex-col gap-4 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/40">
      <div>
        <h2 className="text-lg font-semibold">{gate.question}</h2>
        <ul className="mt-1 list-disc pl-5 text-sm">
          {gate.reasons.map((reason) => (
            <li
              key={reason}
              className={byRule ? "font-medium text-amber-900 dark:text-amber-300" : ""}
            >
              {reason}
            </li>
          ))}
        </ul>
      </div>
      {gate.summary && <p className="text-sm">{gate.summary}</p>}
      <div className="text-sm">
        <span className="font-medium">Files changed:</span>{" "}
        <span className="font-mono">{gate.files_changed.join(", ") || "none"}</span>
        {gate.tokens !== undefined && (
          <span className="text-zinc-500"> · {formatNumber(gate.tokens)} tokens</span>
        )}
      </div>
      {gate.tests && (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium">QA&apos;s test output</summary>
          <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-zinc-900 p-3 text-xs text-zinc-100">
            {gate.tests}
          </pre>
        </details>
      )}
      <form action={formAction} className="flex flex-col gap-2">
        <textarea
          name="feedback"
          rows={2}
          maxLength={2000}
          placeholder="A note for the team (optional)"
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            name="decision"
            value="approve"
            disabled={pending}
            className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Approve release
          </button>
          <button
            type="submit"
            name="decision"
            value="reject"
            disabled={pending}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium disabled:opacity-50 dark:border-zinc-700"
          >
            Reject
          </button>
        </div>
        {state.error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {state.error}
          </p>
        )}
      </form>
    </section>
  );
}
