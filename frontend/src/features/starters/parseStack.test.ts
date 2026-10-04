import { describe, expect, it } from "vitest";

import { parseStack } from "./parseStack";

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

describe("parseStack", () => {
  it("leaves everything to the team when nothing is filled in", () => {
    expect(parseStack(form({ stack_starter: "auto" }))).toEqual({});
  });

  it("reads the founder's choices, modules and notes", () => {
    expect(
      parseStack(
        form({
          stack_api: " Python ",
          stack_hosting: "AWS",
          stack_payments: "cashfree",
          module_auth: "on",
          module_reminders: "on",
          stack_starter: "yes",
          stack_notes: "Cashfree docs: https://docs.cashfree.com",
        }),
      ),
    ).toEqual({
      api: "Python",
      hosting: "AWS",
      payments: "cashfree",
      modules: ["auth", "reminders"],
      starter: true,
      notes: "Cashfree docs: https://docs.cashfree.com",
    });
  });

  it("refuses long or odd names", () => {
    expect(parseStack(form({ stack_database: "x".repeat(41) }))).toEqual({
      error: "Keep the database choice to a short name.",
    });
  });
});
