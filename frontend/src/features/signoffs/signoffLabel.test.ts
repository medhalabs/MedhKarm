import { describe, expect, it } from "vitest";

import { overall } from "./signoffLabel";

describe("overall", () => {
  it("counts those that signed off, leaving out what isn't part of the run", () => {
    expect(overall(["ok", "ok", "warn", "waiting", "skipped"])).toBe("3 of 4 signed off");
  });

  it("says when something needs a look", () => {
    expect(overall(["ok", "fail", "fail"])).toBe("2 problems to look at");
    expect(overall(["fail"])).toBe("1 problem to look at");
  });

  it("copes with nothing to count", () => {
    expect(overall([])).toBe("0 of 0 signed off");
  });
});
