import type { SignoffState } from "./types";

/** How a state reads and looks: a word, an icon character and colours (light and dark). */
export const STATE_LOOK: Record<SignoffState, { word: string; mark: string; tone: string }> = {
  ok: {
    word: "Signed off",
    mark: "✓",
    tone: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  warn: {
    word: "Signed off, with notes",
    mark: "!",
    tone: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  },
  fail: {
    word: "Problem",
    mark: "✕",
    tone: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  },
  waiting: {
    word: "Not yet",
    mark: "…",
    tone: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
  },
  skipped: {
    word: "Not part of this run",
    mark: "–",
    tone: "bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500",
  },
};

/** One line for the top of the card: how many signed off, and what needs a look. */
export function overall(states: SignoffState[]): string {
  const applies = states.filter((s) => s !== "skipped");
  const done = applies.filter((s) => s === "ok" || s === "warn").length;
  const problems = applies.filter((s) => s === "fail").length;
  if (problems) return `${problems} problem${problems === 1 ? "" : "s"} to look at`;
  return `${done} of ${applies.length} signed off`;
}
