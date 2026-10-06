import { Chip } from "@/shared/ui/Chip";

import type { Brief } from "../types";

const DEFAULTS = "Team picks: Next.js · Supabase · Vercel · Razorpay";
const MODULE_NAMES: Record<string, string> = {
  auth: "Sign-in",
  payments: "Payments",
  reminders: "Reminders",
  dashboards: "Admin dashboard",
};

/** The brief the CTO is ready to start: what, where, which stack. */
export function BriefCard({
  brief,
  pending,
  onPlan,
  onBuildNow,
  onKeepTalking,
}: {
  brief: Brief;
  pending: boolean;
  onPlan: () => void;
  onBuildNow: () => void;
  onKeepTalking: () => void;
}) {
  const chosen = (["frontend", "api", "database", "hosting", "payments"] as const)
    .map((field) => brief.stack[field] && `${field}: ${brief.stack[field]}`)
    .filter(Boolean);
  const small = brief.scale === "small";
  return (
    <div className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5 dark:border-indigo-900 dark:bg-indigo-950/30">
      <p className="text-xs font-semibold tracking-wide text-indigo-700 uppercase dark:text-indigo-300">
        Ready
      </p>
      <p className="mt-2 text-sm leading-relaxed whitespace-pre-line text-zinc-800 dark:text-zinc-200">
        {brief.summary || brief.request.slice(0, 400)}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Chip>
          {brief.repo_url
            ? `Changes ${brief.repo_url.replace("https://github.com/", "")}`
            : brief.create_repo
              ? "New project · private repo when released"
              : "New project · no repo"}
        </Chip>
        {chosen.length ? (
          chosen.map((c) => <Chip key={String(c)}>{c}</Chip>)
        ) : (
          <Chip>{DEFAULTS}</Chip>
        )}
        {brief.stack.modules?.map((m) => (
          <Chip key={m}>{MODULE_NAMES[m] ?? m}</Chip>
        ))}
        {brief.stack.starter === false && <Chip>No starter</Chip>}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {small ? (
          <>
            <button type="button" onClick={onBuildNow} disabled={pending} className="btn-primary">
              {pending ? "One moment…" : "Build it now"}
            </button>
            <button type="button" onClick={onPlan} disabled={pending} className="btn-secondary">
              Plan it first
            </button>
          </>
        ) : (
          <>
            <button type="button" onClick={onPlan} disabled={pending} className="btn-primary">
              {pending ? "One moment…" : "Yes, prepare the plan"}
            </button>
            <button type="button" onClick={onBuildNow} disabled={pending} className="btn-secondary">
              {brief.scale === "big" ? "Build without a plan" : "Skip the plan, build now"}
            </button>
          </>
        )}
        <button type="button" onClick={onKeepTalking} disabled={pending} className="btn-secondary">
          Change something
        </button>
      </div>
      <p className="mt-3 text-xs text-zinc-500">
        {brief.scale === "small"
          ? "Kabir thinks this is a small change you can build straight away."
          : brief.scale === "big"
            ? "Kabir thinks this deserves a plan first: Lekha writes what changes, what could break and the cost."
            : "Lekha, our documentation lead, writes the roadmap, architecture and costs for you to read and approve before any code is written."}
      </p>
    </div>
  );
}
