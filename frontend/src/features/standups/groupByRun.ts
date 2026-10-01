import type { StandupItem } from "./types";

export type RunGroup = { runId: string; project: string; items: StandupItem[] };

/** Items grouped per run, in order of first mention (two runs can share a name). */
export function groupByRun(items: StandupItem[]): RunGroup[] {
  const groups = new Map<string, RunGroup>();
  for (const item of items) {
    const group = groups.get(item.run_id) ?? {
      runId: item.run_id,
      project: item.project,
      items: [],
    };
    group.items.push(item);
    groups.set(item.run_id, group);
  }
  return [...groups.values()];
}

/** A `?day=` value we can use: YYYY-MM-DD, or null. */
export function validDay(value: string | string[] | undefined): string | null {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : null;
}
