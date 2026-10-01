import { describeStatus } from "../describeStatus";
import type { RunStatus } from "../types";

const TONES = {
  neutral: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  busy: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  attention: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
  good: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  bad: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  const look = describeStatus(status);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${TONES[look.tone]}`}
    >
      {look.tone === "busy" && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
      )}
      {look.label}
    </span>
  );
}
