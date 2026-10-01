import { describe, expect, it } from "vitest";

import { describeStatus, shortRequest } from "./describeStatus";

describe("describeStatus", () => {
  it("marks runs the team is working on as active", () => {
    expect(describeStatus("running")).toMatchObject({ label: "Working", active: true });
    expect(describeStatus("queued").active).toBe(true);
    expect(describeStatus("waiting_for_approval")).toMatchObject({
      label: "Needs you",
      tone: "attention",
      active: false,
    });
  });
});

describe("shortRequest", () => {
  it("keeps the first line and cuts long ones", () => {
    expect(shortRequest("Build a calculator\nwith tests")).toBe("Build a calculator");
    expect(shortRequest("x".repeat(100), 10)).toBe("xxxxxxxxx…");
  });
});
