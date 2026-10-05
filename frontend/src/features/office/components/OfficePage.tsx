import { listEvents } from "@/features/events";

import { getTeam } from "../api/getTeam";
import { OfficeView } from "./OfficeView";

export async function OfficePage({ runId }: { runId: string }) {
  const [team, events] = await Promise.all([getTeam(), listEvents(runId).catch(() => [])]);
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-xl font-semibold">The office</h1>
      <OfficeView runId={runId} team={team} initialEvents={events} />
    </div>
  );
}
