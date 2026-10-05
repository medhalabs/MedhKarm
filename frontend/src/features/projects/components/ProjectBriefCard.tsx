import { Chip } from "@/shared/ui/Chip";

import type { ProjectBrief } from "../types";

const MODULE_NAMES: Record<string, string> = {
  auth: "Sign-in",
  payments: "Payments",
  reminders: "Reminders",
  dashboards: "Admin dashboard",
};

/** The project Mira is ready to plan: name, summary, where, stack, how fast. */
export function ProjectBriefCard({
  brief,
  pending,
  onStart,
  onKeepTalking,
}: {
  brief: ProjectBrief;
  pending: boolean;
  onStart: () => void;
  onKeepTalking: () => void;
}) {
  const chosen = (["frontend", "api", "database", "hosting", "payments"] as const)
    .map((field) => brief.stack[field] && `${field}: ${brief.stack[field]}`)
    .filter(Boolean);
  return (
    <div className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5 dark:border-indigo-900 dark:bg-indigo-950/30">
      <p className="text-xs font-semibold tracking-wide text-indigo-700 uppercase dark:text-indigo-300">
        Ready to plan
      </p>
      <p className="mt-1 text-lg font-semibold text-zinc-900 dark:text-zinc-50">{brief.name}</p>
      <p className="mt-1 text-sm leading-relaxed whitespace-pre-line text-zinc-800 dark:text-zinc-200">
        {brief.summary || brief.goal.slice(0, 400)}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Chip>
          {brief.repo_url
            ? `Changes ${brief.repo_url.replace("https://github.com/", "")}`
            : "New project"}
        </Chip>
        {chosen.length ? (
          chosen.map((c) => <Chip key={String(c)}>{c}</Chip>)
        ) : (
          <Chip>Team picks: Next.js · Supabase · Vercel · Razorpay</Chip>
        )}
        {brief.stack.modules?.map((m) => (
          <Chip key={m}>{MODULE_NAMES[m] ?? m}</Chip>
        ))}
        <Chip>
          {brief.autopilot
            ? `Works on its own · ${brief.daily_limit} item${brief.daily_limit === 1 ? "" : "s"} a day`
            : "Waits for you to start each item"}
        </Chip>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={onStart} disabled={pending} className="btn-primary">
          {pending ? "Creating…" : "Create and plan"}
        </button>
        <button type="button" onClick={onKeepTalking} disabled={pending} className="btn-secondary">
          Change something
        </button>
      </div>
    </div>
  );
}
