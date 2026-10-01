import { formatDateTime, timeAgo } from "@/shared/lib/format";

import type { Run } from "../types";
import { RunStatusBadge } from "./RunStatusBadge";

export function RunHeader({ run }: { run: Run }) {
  return (
    <header className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <RunStatusBadge status={run.status} />
        <span className="font-mono text-xs text-zinc-500">run {run.id}</span>
        <span className="text-xs text-zinc-500">
          started {formatDateTime(run.created_at)} · last change {timeAgo(run.updated_at)}
        </span>
      </div>
      <p className="text-lg leading-snug font-medium whitespace-pre-line">{run.request}</p>
      <p className="text-sm text-zinc-500">
        Done when <code className="font-mono">{run.test_command}</code> passes.
      </p>
      {run.error && (
        <p
          role="alert"
          className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300"
        >
          {run.error}
        </p>
      )}
    </header>
  );
}
