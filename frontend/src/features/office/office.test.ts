import { describe, expect, it } from "vitest";

import type { ActivityEvent } from "@/features/events/client";

import { officeState } from "./officeState";
import { taskBoard } from "./taskBoard";
import type { Member } from "./types";

const TEAM: Member[] = [
  { role: "cto", title: "CTO", name: "Kabir" },
  { role: "developer", title: "Developer", name: "Isha" },
  { role: "developer", title: "Developer", name: "Arjun" },
  { role: "qa", title: "QA engineer", name: "Tara" },
];

let next = 0;
function event(
  type: ActivityEvent["type"],
  actor: ActivityEvent["actor"],
  summary: string,
  data = {},
): ActivityEvent {
  next += 1;
  return {
    id: next,
    occurred_at: "2026-10-05T10:00:00Z",
    run_id: "r1",
    actor,
    type,
    summary,
    data,
    tokens: 0,
  };
}

const PLAN = event("plan.created", "cto", "Split the work into 2 tasks for Arjun, Isha", {
  tasks: [
    { id: "t1", title: "Message API", owner: "Isha" },
    { id: "t2", title: "Home page", owner: "Arjun" },
  ],
});

describe("the office follows the activity log", () => {
  it("gathers the team for planning, then sends everyone to work", () => {
    const planning = officeState(TEAM, [PLAN]);
    expect(planning.agents.Kabir.place).toEqual({ kind: "meeting" });
    expect(planning.agents.Isha.place).toEqual({ kind: "meeting" });
    expect(planning.agents.Tara.place).toEqual({ kind: "desk", of: "Tara" });

    const working = officeState(TEAM, [
      PLAN,
      event("task.assigned", "cto", "Assigned “Message API” to Isha", {
        task_id: "t1",
        member: "Isha",
      }),
      event("work.started", "developer", "Isha started: Message API", {
        task_id: "t1",
        member: "Isha",
      }),
      event("tool.used", "developer", "Ran the tests", { member: "Isha" }),
    ]);
    expect(working.agents.Isha).toMatchObject({
      place: { kind: "desk", of: "Isha" },
      doing: "testing",
      bubble: "Ran the tests",
    });
    expect(working.agents.Kabir.place).toEqual({ kind: "desk", of: "Kabir" });
    expect(working.agents.Arjun.place).toEqual({ kind: "desk", of: "Arjun" });
  });

  it("walks the CTO to a desk to review, and to the door for approval", () => {
    const review = officeState(TEAM, [
      PLAN,
      event("review.finished", "cto", "Sent “Home page” back to Arjun: use rupees", {
        task_id: "t2",
        member: "Arjun",
        decision: "revise",
      }),
    ]);
    expect(review.agents.Kabir).toMatchObject({
      place: { kind: "desk", of: "Arjun" },
      doing: "reviewing",
    });

    const gate = officeState(TEAM, [
      PLAN,
      event("approval.requested", "cto", "Waiting for your approval"),
    ]);
    expect(gate.founderWaiting).toBe(true);
    expect(gate.agents.Kabir.place).toEqual({ kind: "door" });
  });

  it("sends QA to the developer who gets a fix task", () => {
    const state = officeState(TEAM, [
      PLAN,
      event("check.finished", "qa", "Checks failed: sent to Isha to fix"),
      event("task.assigned", "qa", "Assigned “Make QA's checks pass” to Isha", {
        task_id: "qa1",
        member: "Isha",
      }),
    ]);
    expect(state.agents.Tara.place).toEqual({ kind: "desk", of: "Isha" });
  });

  it("sends everyone home when the run ends", () => {
    const state = officeState(TEAM, [
      PLAN,
      event("run.finished", "system", "Released", { status: "released" }),
    ]);
    expect(state.finished).toBe("released");
    expect(
      Object.values(state.agents).every(
        (a) => a.place.kind === "desk" && a.place.of === a.member.name,
      ),
    ).toBe(true);
  });
});

describe("the task board", () => {
  it("moves tasks through the columns and counts send-backs", () => {
    const board = taskBoard([
      PLAN,
      event("work.started", "developer", "Isha started", { task_id: "t1", member: "Isha" }),
      event("work.finished", "developer", "Isha: done", { task_id: "t1", member: "Isha" }),
      event("review.finished", "cto", "Approved", { task_id: "t1", decision: "approve" }),
      event("work.started", "developer", "Arjun started", { task_id: "t2", member: "Arjun" }),
      event("work.finished", "developer", "Arjun: done", { task_id: "t2", member: "Arjun" }),
      event("review.finished", "cto", "Sent back", { task_id: "t2", decision: "revise" }),
      event("task.assigned", "qa", "Assigned fix", {
        task_id: "qa1",
        member: "Isha",
        title: "Make QA's checks pass",
      }),
    ]);
    expect(board.map((t) => [t.id, t.column, t.rounds])).toEqual([
      ["t1", "done", 0],
      ["t2", "todo", 1],
      ["qa1", "todo", 0],
    ]);
  });
});

describe("Lekha in the office", () => {
  it("shows what she added to the changelog, at her desk", () => {
    const team: Member[] = [...TEAM, { role: "docs", title: "Documentation", name: "Lekha" }];
    const state = officeState(team, [
      event("docs.updated", "docs", "Lekha added to the changelog: Customers can add a tip"),
    ]);
    expect(state.agents.Lekha.bubble).toBe("Customers can add a tip");
    expect(state.agents.Lekha.doing).toBe("working");
  });
});

describe("the floor plan", () => {
  it("keeps every desk clear of the meeting room, even with four on the top row", async () => {
    const { desks, MEETING } = await import("./layout");
    const team: Member[] = [
      { role: "pm", title: "PM", name: "Mira" },
      { role: "cto", title: "CTO", name: "Kabir" },
      { role: "docs", title: "Documentation", name: "Lekha" },
      { role: "design", title: "Designer", name: "Anaya" },
    ];
    const places = desks(team);
    const xs = Object.values(places).map((p) => p.x);
    expect(new Set(xs).size).toBe(4); // no two on the same spot
    expect(Math.max(...xs)).toBeLessThan(MEETING.x - 60);
  });
});
