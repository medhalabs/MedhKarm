import { describe, expect, it } from "vitest";

import { facts, factsLine } from "./summary";

describe("facts", () => {
  it("says what the team did, only what is true", () => {
    const stats = {
      tasks: 3,
      minutes: 7,
      checks_passed: true,
      security_clean: true,
      docs_updated: false,
    };
    expect(facts(stats)).toEqual([
      "3 tasks built",
      "in 7 minutes",
      "tests passed",
      "security checked",
    ]);
    expect(factsLine(stats)).toBe("3 tasks built, in 7 minutes, tests passed, security checked");
  });

  it("is singular for one", () => {
    const stats = {
      tasks: 1,
      minutes: 1,
      checks_passed: false,
      security_clean: false,
      docs_updated: true,
    };
    expect(facts(stats)).toEqual(["1 task built", "in 1 minute", "docs updated"]);
  });
});
