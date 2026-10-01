import Link from "next/link";

import { formatDateTime, formatNumber, isoDay, shiftDay } from "@/shared/lib/format";

import { getStandup } from "../api/getStandup";
import { StandupSection } from "./StandupSection";

/** The daily standup for `day` (default today, IST), with links to the days around it. */
export async function StandupView({ day }: { day: string | null }) {
  const today = isoDay();
  const shownDay = day ?? today;
  const standup = await getStandup(shownDay).catch(() => undefined);
  const next = shiftDay(shownDay, 1);

  return (
    <div className="flex flex-col gap-6">
      <nav className="flex items-center justify-between text-sm">
        <Link href={`/admin/standup?day=${shiftDay(shownDay, -1)}`} className="hover:underline">
          ← {shiftDay(shownDay, -1)}
        </Link>
        <span className="font-medium">{dayLabel(shownDay, today)}</span>
        {next <= shiftDay(today, 1) ? (
          <Link href={`/admin/standup?day=${next}`} className="hover:underline">
            {next === shiftDay(today, 1) ? "Since 09:00 today" : next} →
          </Link>
        ) : (
          <span />
        )}
      </nav>

      {standup === undefined && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          Couldn&apos;t reach the backend.
        </p>
      )}
      {standup === null && (
        <p className="text-sm text-zinc-500">This day hasn&apos;t started yet.</p>
      )}
      {standup && (
        <>
          <header>
            <p className="text-xl font-semibold">{standup.headline}</p>
            <p className="text-sm text-zinc-500">
              {formatDateTime(standup.since)} to {formatDateTime(standup.until)} (IST) ·{" "}
              {formatNumber(standup.tokens)} tokens
              {standup.sent_back > 0 && ` · the CTO sent ${standup.sent_back} back for changes`}
            </p>
          </header>
          <div className="grid gap-4 md:grid-cols-2">
            <StandupSection title="Needs you" items={standup.needs_you} accent="border-amber-500" />
            <StandupSection title="Done" items={standup.done} accent="border-emerald-500" />
            <StandupSection title="Planned today" items={standup.planned} accent="border-sky-500" />
            <StandupSection title="Blocked" items={standup.blocked} accent="border-red-500" />
          </div>
        </>
      )}
    </div>
  );
}

/** A standup for a day covers the 24 hours before 09:00 that morning, so today's work so far
 * is tomorrow's standup: say so instead of showing a bare date. */
function dayLabel(day: string, today: string): string {
  if (day === today) return `This morning's standup · ${day}`;
  if (day === shiftDay(today, 1)) return `Since 09:00 today (tomorrow's standup, so far)`;
  return day;
}
