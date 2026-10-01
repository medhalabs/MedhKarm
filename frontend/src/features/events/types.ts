// Mirrors backend/app/features/events/schemas.py.

export const EVENT_TYPES = [
  "run.started",
  "run.resumed",
  "run.finished",
  "plan.created",
  "task.assigned",
  "review.finished",
  "work.started",
  "tool.used",
  "model.used",
  "work.finished",
  "check.finished",
  "approval.requested",
  "approval.decided",
] as const;

export type EventType = (typeof EVENT_TYPES)[number];

export type Actor = "founder" | "pm" | "cto" | "developer" | "qa" | "devops" | "system";

export type ActivityEvent = {
  id: number;
  occurred_at: string;
  run_id: string;
  actor: Actor;
  type: EventType;
  summary: string;
  data: Record<string, unknown>;
  tokens: number;
};
