import { formatNumber, formatTime } from "@/shared/lib/format";

import { actorLabel } from "../describeEvent";
import type { ActivityEvent } from "../types";

const DOTS: Record<string, string> = {
  founder: "bg-violet-500",
  cto: "bg-sky-500",
  developer: "bg-emerald-500",
  qa: "bg-amber-500",
  system: "bg-zinc-400",
};

export function EventRow({ event }: { event: ActivityEvent }) {
  return (
    <li className="flex gap-3 py-2 text-sm">
      <span className="w-16 shrink-0 font-mono text-xs leading-5 text-zinc-500">
        {formatTime(event.occurred_at)}
      </span>
      <span
        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${DOTS[event.actor] ?? "bg-zinc-400"}`}
      />
      <span className="w-28 shrink-0 font-medium">{actorLabel(event)}</span>
      <span className="min-w-0 flex-1 break-words">{event.summary}</span>
      {event.tokens > 0 && (
        <span className="shrink-0 text-xs leading-5 text-zinc-500">
          {formatNumber(event.tokens)} tokens
        </span>
      )}
    </li>
  );
}
