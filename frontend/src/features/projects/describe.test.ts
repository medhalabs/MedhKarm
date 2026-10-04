import { describe, expect, it } from "vitest";

import { describeItem, isBusy, itemActions, progress } from "./describe";
import type { BacklogItem, ProjectDetail } from "./types";

function item(status: BacklogItem["status"]): BacklogItem {
  return {
    id: status,
    project_id: "p1",
    position: 1,
    title: "t",
    description: "",
    acceptance: [],
    size: "M",
    status,
    run_id: null,
    attempts: 0,
    note: "",
    pull_request_url: "",
    started_at: null,
    done_at: null,
  };
}

describe("projects", () => {
  it("counts progress without skipped items", () => {
    expect(progress([item("done"), item("todo"), item("skipped")])).toEqual({ done: 1, total: 2 });
  });

  it("offers actions by status", () => {
    expect(itemActions(item("todo"))).toContain("delete");
    expect(itemActions(item("blocked"))).toEqual(["retry", "skip"]);
    expect(itemActions(item("in_progress"))).toEqual([]);
    expect(describeItem("waiting_for_merge").label).toBe("Merge on GitHub");
  });

  it("is busy while planning or building", () => {
    const base = { status: "active", items: [item("todo")] } as unknown as ProjectDetail;
    expect(isBusy(base)).toBe(false);
    expect(isBusy({ ...base, items: [item("in_progress")] })).toBe(true);
    expect(isBusy({ ...base, status: "planning" })).toBe(true);
  });
});
