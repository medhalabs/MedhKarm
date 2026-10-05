import { titleFrom } from "@/shared/lib/title";
import { formatDateTime, timeAgo } from "@/shared/lib/format";

import type { Run } from "../types";
import { RunStatusBadge } from "./RunStatusBadge";

/** The run at a glance: status, a readable title from the request, when it happened. */
export function RunHeader({ run }: { run: Run }) {
  return (
    <header className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500">
        <RunStatusBadge status={run.status} />
        <span>started {formatDateTime(run.created_at)}</span>
        <span aria-hidden="true">·</span>
        <span>last change {timeAgo(run.updated_at)}</span>
      </div>
      <h1 className="text-2xl font-semibold tracking-tight text-balance text-zinc-900 dark:text-zinc-50">
        {titleFrom(run.request) || "Untitled run"}
      </h1>
      {run.error && run.status !== "cancelled" && (
        <p
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
        >
          {run.error}
        </p>
      )}
    </header>
  );
}
