import { describe, expect, it } from "vitest";

import { groupByRun, validDay } from "./groupByRun";
import type { StandupItem } from "./types";

const item = (run_id: string, text: string): StandupItem => ({
  run_id,
  project: "Expense tracker",
  text,
  member: null,
  at: null,
});

describe("groupByRun", () => {
  it("keeps runs with the same name apart", () => {
    const groups = groupByRun([item("a", "1"), item("b", "2"), item("a", "3")]);
    expect(groups.map((g) => [g.runId, g.items.map((i) => i.text)])).toEqual([
      ["a", ["1", "3"]],
      ["b", ["2"]],
    ]);
  });
});

describe("validDay", () => {
  it("accepts only YYYY-MM-DD", () => {
    expect(validDay("2026-10-01")).toBe("2026-10-01");
    expect(validDay("tomorrow")).toBeNull();
    expect(validDay(["2026-10-01"])).toBeNull();
  });
});
