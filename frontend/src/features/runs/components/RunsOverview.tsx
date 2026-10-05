import { AutoRefresh } from "@/shared/ui/AutoRefresh";
import { PageHeader, Stat } from "@/shared/ui/PageHeader";

import { listRuns } from "../api/listRuns";
import { describeStatus } from "../describeStatus";
import { RunsTable } from "./RunsTable";
import { IntakeChat } from "./IntakeChat";

/** The admin home: start a run, and every run with its status (refreshes while work is going on). */
export async function RunsOverview() {
  const runs = await listRuns().catch(() => null);
  const busy = runs?.some((run) => describeStatus(run.status).active) ?? false;
  const waiting = runs?.filter((run) => run.status === "waiting_for_approval").length ?? 0;

  const working = runs?.filter((run) => describeStatus(run.status).active).length ?? 0;
  const released = runs?.filter((run) => run.status === "released").length ?? 0;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Runs" description="Ask your team for something, and follow every build.">
        <div className="flex gap-3">
          <Stat value={working} label="Working" tone="sky" />
          <Stat value={waiting} label="Waiting for you" tone="amber" />
          <Stat value={released} label="Released" tone="emerald" />
        </div>
      </PageHeader>
      <IntakeChat />
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-zinc-500">All runs</h2>
        {runs ? (
          <RunsTable runs={runs} />
        ) : (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            Couldn&apos;t reach the backend. Start it with `uv run uvicorn app.main:app --port
            8000`.
          </p>
        )}
      </section>
      <AutoRefresh active={busy} />
    </div>
  );
}
