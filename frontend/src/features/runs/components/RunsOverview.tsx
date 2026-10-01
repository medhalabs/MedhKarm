import { AutoRefresh } from "@/shared/ui/AutoRefresh";

import { listRuns } from "../api/listRuns";
import { describeStatus } from "../describeStatus";
import { RunsTable } from "./RunsTable";
import { StartRunForm } from "./StartRunForm";

/** The admin home: start a run, and every run with its status (refreshes while work is going on). */
export async function RunsOverview() {
  const runs = await listRuns().catch(() => null);
  const busy = runs?.some((run) => describeStatus(run.status).active) ?? false;
  const waiting = runs?.filter((run) => run.status === "waiting_for_approval").length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <StartRunForm />
      <section className="flex flex-col gap-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Runs</h2>
          {waiting > 0 && (
            <span className="text-sm text-amber-700 dark:text-amber-400">
              {waiting} waiting for your approval
            </span>
          )}
        </div>
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
