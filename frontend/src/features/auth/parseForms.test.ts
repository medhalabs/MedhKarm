import { describe, expect, it } from "vitest";

import { parseLogIn, parseSignUp } from "./parseForms";

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

describe("auth forms", () => {
  it("reads a log-in", () => {
    expect(parseLogIn(form({ email: " Pavan@Example.com ", password: "secret123" }))).toEqual({
      email: "pavan@example.com",
      password: "secret123",
    });
    expect(parseLogIn(form({ email: "nope", password: "x" }))).toEqual({
      error: "Enter your email address.",
    });
  });

  it("checks a sign-up", () => {
    expect(
      parseSignUp(
        form({ email: "a@b.co", password: "long enough", name: " Pavan ", company_name: "Labs" }),
      ),
    ).toEqual({ email: "a@b.co", password: "long enough", name: "Pavan", company_name: "Labs" });
    expect(parseSignUp(form({ email: "a@b.co", password: "short", company_name: "Labs" }))).toEqual(
      { error: "Use at least 8 characters for the password." },
    );
  });
});
