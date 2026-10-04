import type { BacklogItem, ItemStatus, ProjectDetail, ProjectStatus } from "./types";

type Tone = "neutral" | "busy" | "attention" | "good" | "bad";

const PROJECT: Record<ProjectStatus, { label: string; tone: Tone }> = {
  planning: { label: "Mira is planning", tone: "busy" },
  plan_ready: { label: "Plan ready for you", tone: "attention" },
  active: { label: "Active", tone: "good" },
  paused: { label: "Paused", tone: "neutral" },
  done: { label: "Done", tone: "good" },
};

const ITEM: Record<ItemStatus, { label: string; tone: Tone }> = {
  proposed: { label: "Proposed", tone: "neutral" },
  todo: { label: "To do", tone: "neutral" },
  in_progress: { label: "In progress", tone: "busy" },
  waiting_for_merge: { label: "Merge on GitHub", tone: "attention" },
  done: { label: "Done", tone: "good" },
  blocked: { label: "Blocked", tone: "bad" },
  skipped: { label: "Skipped", tone: "neutral" },
};

export function describeProject(status: ProjectStatus) {
  return PROJECT[status] ?? { label: status, tone: "neutral" as Tone };
}

export function describeItem(status: ItemStatus) {
  return ITEM[status] ?? { label: status, tone: "neutral" as Tone };
}

/** Done of total, leaving skipped items out of both. */
export function progress(items: BacklogItem[]): { done: number; total: number } {
  const counted = items.filter((i) => i.status !== "skipped");
  return { done: counted.filter((i) => i.status === "done").length, total: counted.length };
}

/** Worth refreshing the page: the PM is planning, or an item is being built. */
export function isBusy(project: ProjectDetail): boolean {
  return (
    project.status === "planning" ||
    project.items.some((i) => i.status === "in_progress" || i.status === "waiting_for_merge")
  );
}

/** What the founder can do with an item, by its status. */
export function itemActions(item: BacklogItem): Array<"up" | "down" | "delete" | "skip" | "retry"> {
  if (item.status === "proposed" || item.status === "todo") return ["up", "down", "skip", "delete"];
  if (item.status === "blocked") return ["retry", "skip"];
  return [];
}

export const TONES: Record<Tone, string> = {
  neutral: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  busy: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  attention: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
  good: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  bad: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};
