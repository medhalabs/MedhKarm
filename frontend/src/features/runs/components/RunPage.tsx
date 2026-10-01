import Link from "next/link";
import { notFound } from "next/navigation";

import { ActivityFeed, listEvents } from "@/features/events";
import { AutoRefresh } from "@/shared/ui/AutoRefresh";

import { getRun } from "../api/getRun";
import { describeStatus } from "../describeStatus";
import { ApprovalPanel } from "./ApprovalPanel";
import { RunHeader } from "./RunHeader";

/** One run: where it stands, the release decision when it's waiting, and its live activity. */
export async function RunPage({ runId }: { runId: string }) {
  const [run, events] = await Promise.all([getRun(runId), listEvents(runId).catch(() => [])]);
  if (!run) notFound();

  return (
    <div className="flex flex-col gap-6">
      <Link href="/admin" className="text-sm text-zinc-500 hover:underline">
        ← All runs
      </Link>
      <RunHeader run={run} />
      {run.status === "waiting_for_approval" && run.gate && (
        <ApprovalPanel runId={run.id} gate={run.gate} />
      )}
      <ActivityFeed key={run.id} runId={run.id} initialEvents={events} />
      {/* Status changes are also caught from the feed; this covers queued → running. */}
      <AutoRefresh active={describeStatus(run.status).active} seconds={10} />
    </div>
  );
}
