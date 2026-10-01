import { describe, expect, it } from "vitest";

import { actorLabel, isFinished, mergeEvents, totalTokens } from "./describeEvent";
import type { ActivityEvent } from "./types";

function event(id: number, extra: Partial<ActivityEvent> = {}): ActivityEvent {
  return {
    id,
    occurred_at: "2026-10-01T12:00:00Z",
    run_id: "r1",
    actor: "system",
    type: "tool.used",
    summary: `step ${id}`,
    data: {},
    tokens: 0,
    ...extra,
  };
}

describe("events", () => {
  it("names developers by their office name", () => {
    expect(actorLabel(event(1, { actor: "developer", data: { member: "Isha" } }))).toBe("Isha");
    expect(actorLabel(event(2, { actor: "cto" }))).toBe("Kabir (CTO)");
  });

  it("merges without duplicates, in order", () => {
    const merged = mergeEvents([event(1), event(3)], [event(3), event(2)]);
    expect(merged.map((e) => e.id)).toEqual([1, 2, 3]);
  });

  it("totals tokens and spots the end of a run", () => {
    const events = [event(1, { tokens: 120 }), event(2, { tokens: 80, type: "run.finished" })];
    expect(totalTokens(events)).toBe(200);
    expect(isFinished(events)).toBe(true);
  });
});
