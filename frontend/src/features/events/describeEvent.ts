import type { ActivityEvent, EventType } from "./types";

// Office names from the software team template (backend teams/templates/software.toml).
const ACTORS: Record<string, string> = {
  founder: "You",
  pm: "Mira (PM)",
  cto: "Kabir (CTO)",
  developer: "Developer",
  qa: "Tara (QA)",
  security: "Vikram (security)",
  devops: "Neel (DevOps)",
  system: "System",
};

/** Who did it: the developer's own name when the event says ("Isha"), else the role. */
export function actorLabel(event: ActivityEvent): string {
  const member = event.data.member;
  if (event.actor === "developer" && typeof member === "string") return member;
  return ACTORS[event.actor] ?? event.actor;
}

/** Steps after which the run's status may have changed: refresh the page around the feed. */
export const STATUS_CHANGING: ReadonlySet<EventType> = new Set([
  "approval.requested",
  "approval.decided",
  "run.finished",
  "run.resumed",
  "plan.created",
  "changes.delivered",
]);

/** New events added to the ones shown: no duplicates, in the order they happened. */
export function mergeEvents(shown: ActivityEvent[], incoming: ActivityEvent[]): ActivityEvent[] {
  const byId = new Map(shown.map((event) => [event.id, event]));
  for (const event of incoming) byId.set(event.id, event);
  return [...byId.values()].sort((a, b) => a.id - b.id);
}

export function totalTokens(events: ActivityEvent[]): number {
  return events.reduce((sum, event) => sum + event.tokens, 0);
}

export function isFinished(events: ActivityEvent[]): boolean {
  return events.some((event) => event.type === "run.finished");
}
