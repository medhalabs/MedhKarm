import { describe, expect, it } from "vitest";

import { formatNumber, formatTime, isoDay, shiftDay, timeAgo } from "./format";

describe("format", () => {
  it("shows times in IST", () => {
    expect(formatTime("2026-10-01T12:35:43Z")).toBe("18:05:43");
  });

  it("groups numbers the Indian way", () => {
    expect(formatNumber(384095)).toBe("3,84,095");
  });

  it("says how long ago", () => {
    const now = new Date("2026-10-01T12:00:00Z");
    expect(timeAgo("2026-10-01T11:59:30Z", now)).toBe("just now");
    expect(timeAgo("2026-10-01T11:55:00Z", now)).toBe("5 min ago");
    expect(timeAgo("2026-10-01T09:00:00Z", now)).toBe("3 h ago");
    expect(timeAgo("2026-09-29T12:00:00Z", now)).toBe("2 days ago");
  });

  it("works out IST days", () => {
    expect(isoDay(new Date("2026-10-01T20:00:00Z"))).toBe("2026-10-02"); // 01:30 IST next day
    expect(shiftDay("2026-10-01", -1)).toBe("2026-09-30");
    expect(shiftDay("2026-12-31", 1)).toBe("2027-01-01");
  });
});
