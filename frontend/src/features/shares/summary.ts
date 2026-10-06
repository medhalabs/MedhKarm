import type { PublicStats } from "./types";

/** The facts about a build as short phrases, for the top of a public page and its link preview. */
export function facts(stats: PublicStats): string[] {
  const out = [
    `${stats.tasks} task${stats.tasks === 1 ? "" : "s"} built`,
    `in ${stats.minutes} minute${stats.minutes === 1 ? "" : "s"}`,
  ];
  if (stats.checks_passed) out.push("tests passed");
  if (stats.security_clean) out.push("security checked");
  if (stats.docs_updated) out.push("docs updated");
  return out;
}

/** "3 tasks built, in 7 minutes, tests passed" */
export function factsLine(stats: PublicStats): string {
  const [built, time, ...rest] = facts(stats);
  return [`${built}`, time, ...rest].join(", ");
}
