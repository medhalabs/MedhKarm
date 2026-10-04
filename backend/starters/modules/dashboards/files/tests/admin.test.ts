import { afterEach, describe, expect, it } from "vitest";
import { isAdmin, perDay, preview } from "@/lib/admin/stats";

describe("admin", () => {
  afterEach(() => {
    delete process.env.ADMIN_EMAILS;
  });

  it("lets in only listed emails", () => {
    process.env.ADMIN_EMAILS = "Owner@Example.com, ops@example.com";
    expect(isAdmin("owner@example.com")).toBe(true);
    expect(isAdmin("someone@example.com")).toBe(false);
    expect(isAdmin(undefined)).toBe(false);
  });

  it("counts records per day, including empty days", () => {
    const now = new Date("2026-10-05T12:00:00Z");
    const days = perDay(
      [{ createdAt: "2026-10-05T01:00:00Z" }, { createdAt: "2026-10-05T02:00:00Z" }, { createdAt: "2026-10-03T09:00:00Z" }, { createdAt: "2026-01-01T00:00:00Z" }],
      3,
      now,
    );
    expect(days).toEqual([
      { day: "2026-10-03", count: 1 },
      { day: "2026-10-04", count: 0 },
      { day: "2026-10-05", count: 2 },
    ]);
  });

  it("never shows password hashes", () => {
    expect(preview({ id: "1", createdAt: "x", email: "a@b.c", passwordHash: "s:h" })).toBe("email: a@b.c");
  });
});
