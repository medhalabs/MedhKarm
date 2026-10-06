import type { ProjectHealth } from "../types";

const LOOK: Record<ProjectHealth["state"], { word: string; tone: string }> = {
  moving: {
    word: "Moving",
    tone: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  done: {
    word: "Done",
    tone: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  needs_you: {
    word: "Needs you",
    tone: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  },
  stalled: { word: "Quiet", tone: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300" },
  not_started: {
    word: "Not started",
    tone: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  },
};

/** Priya's update on the project: how far it has got, what it has cost, and whether it moves. */
export function PriyaUpdate({ health }: { health: ProjectHealth }) {
  const look = LOOK[health.state];
  const percent = health.items_total ? Math.round((health.done / health.items_total) * 100) : 0;
  return (
    <section className="card" aria-label="Priya's update">
      <div className="card-header">
        <h2 className="card-title">Priya&apos;s update</h2>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${look.tone}`}>
          {look.word}
        </span>
      </div>
      <div className="flex flex-col gap-3 p-5">
        <p className="text-sm text-zinc-700 dark:text-zinc-300">{health.summary}</p>
        <div
          className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Items done"
        >
          <div className="h-full rounded-full bg-indigo-600" style={{ width: `${percent}%` }} />
        </div>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Fact label="Done" value={`${health.done}/${health.items_total}`} />
          <Fact label="In progress" value={String(health.in_progress)} />
          <Fact label="Model tokens" value={health.tokens.toLocaleString("en-IN")} />
          <Fact
            label="Last activity"
            value={
              health.days_since_activity === null
                ? "none yet"
                : health.days_since_activity === 0
                  ? "today"
                  : `${health.days_since_activity}d ago`
            }
          />
        </dl>
      </div>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
