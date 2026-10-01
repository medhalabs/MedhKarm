import Link from "next/link";

import { formatDateTime, timeAgo } from "@/shared/lib/format";

import { shortRequest } from "../describeStatus";
import type { Run } from "../types";
import { RunStatusBadge } from "./RunStatusBadge";

export function RunsTable({ runs }: { runs: Run[] }) {
  if (runs.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-500 dark:border-zinc-700">
        No runs yet. Ask the team for something above.
      </p>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-zinc-50 text-xs text-zinc-500 uppercase dark:bg-zinc-900">
          <tr>
            <th className="px-4 py-2 font-medium">Request</th>
            <th className="px-4 py-2 font-medium">Status</th>
            <th className="px-4 py-2 font-medium">Started</th>
            <th className="px-4 py-2 font-medium">Last change</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {runs.map((run) => (
            <tr key={run.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-900/50">
              <td className="px-4 py-3">
                <Link href={`/admin/runs/${run.id}`} className="font-medium hover:underline">
                  {shortRequest(run.request)}
                </Link>
                <div className="font-mono text-xs text-zinc-500">{run.id}</div>
              </td>
              <td className="px-4 py-3">
                <RunStatusBadge status={run.status} />
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-zinc-600 dark:text-zinc-400">
                {formatDateTime(run.created_at)}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-zinc-600 dark:text-zinc-400">
                {timeAgo(run.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
