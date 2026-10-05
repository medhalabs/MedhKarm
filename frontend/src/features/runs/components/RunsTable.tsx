import Link from "next/link";

import { formatDateTime, timeAgo } from "@/shared/lib/format";

import { titleFrom } from "@/shared/lib/title";
import type { Run } from "../types";
import { RunStatusBadge } from "./RunStatusBadge";

export function RunsTable({ runs }: { runs: Run[] }) {
  if (runs.length === 0) {
    return (
      <p className="card p-8 text-center text-sm text-zinc-500">
        No runs yet. Ask the team for something above.
      </p>
    );
  }
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-zinc-100 text-xs text-zinc-500 dark:border-zinc-800">
          <tr>
            <th className="px-5 py-3 font-medium">Request</th>
            <th className="px-5 py-3 font-medium">Status</th>
            <th className="px-5 py-3 font-medium">Started</th>
            <th className="px-5 py-3 font-medium">Last change</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {runs.map((run) => (
            <tr key={run.id} className="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/40">
              <td className="px-5 py-3.5">
                <Link
                  href={`/admin/runs/${run.id}`}
                  className="font-medium text-zinc-900 hover:text-indigo-600 dark:text-zinc-100 dark:hover:text-indigo-400"
                >
                  {titleFrom(run.request, 90)}
                </Link>
                <div className="font-mono text-xs text-zinc-500">{run.id}</div>
              </td>
              <td className="px-5 py-3.5">
                <RunStatusBadge status={run.status} />
              </td>
              <td className="px-5 py-3.5 whitespace-nowrap text-zinc-600 dark:text-zinc-400">
                {formatDateTime(run.created_at)}
              </td>
              <td className="px-5 py-3.5 whitespace-nowrap text-zinc-600 dark:text-zinc-400">
                {timeAgo(run.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
