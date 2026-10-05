import type { ActivityEvent } from "@/features/events/client";

import type { BoardTask } from "./types";

type TaskData = { id?: unknown; title?: unknown; owner?: unknown };

/** The CTO's tasks and where each one is, from the plan, work and review events. */
export function taskBoard(events: ActivityEvent[]): BoardTask[] {
  const tasks = new Map<string, BoardTask>();
  const id = (event: ActivityEvent): string | undefined =>
    typeof event.data.task_id === "string" ? event.data.task_id : undefined;

  for (const event of events) {
    if (event.type === "plan.created" && Array.isArray(event.data.tasks)) {
      for (const raw of event.data.tasks as TaskData[]) {
        if (typeof raw.id !== "string") continue;
        tasks.set(raw.id, {
          id: raw.id,
          title: String(raw.title ?? raw.id),
          owner: String(raw.owner ?? ""),
          column: "todo",
          rounds: 0,
        });
      }
    }
    const taskId = id(event);
    if (!taskId) continue;
    if (event.type === "task.assigned" && !tasks.has(taskId)) {
      // fix tasks from QA, security or the browser test join the board when assigned
      tasks.set(taskId, {
        id: taskId,
        title: String(event.data.title ?? taskId),
        owner: String(event.data.member ?? ""),
        column: "todo",
        rounds: 0,
      });
    }
    const task = tasks.get(taskId);
    if (!task) continue;
    if (event.type === "work.started") task.column = "working";
    if (event.type === "work.finished") task.column = "review";
    if (event.type === "review.finished") {
      if (event.data.decision === "approve") task.column = "done";
      else {
        task.column = "todo";
        task.rounds += 1;
      }
    }
  }
  return [...tasks.values()];
}
