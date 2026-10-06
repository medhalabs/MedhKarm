import Link from "next/link";
import { notFound } from "next/navigation";

import { DemoCard } from "@/features/artifacts";
import { ActivityFeed, listEvents } from "@/features/events";
import { MessageThread } from "@/features/messages";
import { ShareCard } from "@/features/shares";
import { SignoffCard } from "@/features/signoffs";
import { AutoRefresh } from "@/shared/ui/AutoRefresh";

import { getRun } from "../api/getRun";
import { describeStatus } from "../describeStatus";
import { ApprovalPanel } from "./ApprovalPanel";
import { RequestCard } from "./RequestCard";
import { RunHeader } from "./RunHeader";
import { RunSidebar } from "./RunSidebar";

const SHOW_SIGNOFFS = ["waiting_for_approval", "released", "rejected", "failed"];

/** One run: where it stands, the release decision when it's waiting, the request, its live
 * activity and messages, with the office and the run's facts alongside. */
export async function RunPage({ runId }: { runId: string }) {
  const [run, events] = await Promise.all([getRun(runId), listEvents(runId).catch(() => [])]);
  if (!run) notFound();

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/admin"
        className="w-fit text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
      >
        ← All runs
      </Link>
      <RunHeader run={run} />
      {run.status === "waiting_for_approval" && run.gate && (
        <ApprovalPanel runId={run.id} gate={run.gate} />
      )}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="flex min-w-0 flex-col gap-6">
          <RequestCard request={run.request} />
          {SHOW_SIGNOFFS.includes(run.status) && <DemoCard runId={run.id} />}
          {SHOW_SIGNOFFS.includes(run.status) && <SignoffCard runId={run.id} />}
          <div className="card p-5">
            <ActivityFeed key={run.id} runId={run.id} initialEvents={events} />
          </div>
          <MessageThread thread="run" threadId={run.id} />
        </div>
        <RunSidebar run={run} share={<ShareCard runId={run.id} />} />
      </div>
      {/* Status changes are also caught from the feed; this covers queued → running. */}
      <AutoRefresh active={describeStatus(run.status).active} seconds={10} />
    </div>
  );
}
