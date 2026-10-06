import { describe, expect, it } from "vitest";

import { validationMessage } from "./client";

describe("validationMessage", () => {
  it("gives the first problem in plain words", () => {
    const body = {
      detail: [
        { type: "value_error", msg: "Value error, '/etc/x': use a path inside the project" },
      ],
    };
    expect(validationMessage(body)).toBe("'/etc/x': use a path inside the project");
  });

  it("is undefined for anything else", () => {
    expect(validationMessage({ error: { message: "x" } })).toBeUndefined();
    expect(validationMessage(null)).toBeUndefined();
    expect(validationMessage({ detail: "nope" })).toBeUndefined();
    expect(validationMessage({ detail: [] })).toBeUndefined();
  });
});
