import Link from "next/link";

import { groupByRun } from "../groupByRun";
import type { StandupItem } from "../types";

export function StandupSection({
  title,
  items,
  accent,
}: {
  title: string;
  items: StandupItem[];
  accent: string;
}) {
  return (
    <section className={`rounded-lg border-l-4 bg-zinc-50 p-4 dark:bg-zinc-900 ${accent}`}>
      <h2 className="mb-2 font-semibold">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-zinc-500">Nothing</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {groupByRun(items).map((group) => (
            <li key={group.runId} className="text-sm">
              <Link href={`/admin/runs/${group.runId}`} className="font-medium hover:underline">
                {group.project}
              </Link>
              <ul className="mt-1 list-disc pl-5 text-zinc-700 dark:text-zinc-300">
                {group.items.map((item, index) => (
                  <li key={index}>{item.text}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
