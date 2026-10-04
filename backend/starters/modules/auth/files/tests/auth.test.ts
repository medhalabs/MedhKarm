import { describe, expect, it } from "vitest";
import { checkPassword, hashPassword, passwordProblem } from "@/lib/auth/passwords";
import { createSessionToken, readSessionToken } from "@/lib/auth/session";

describe("passwords", () => {
  it("checks a password against its hash, never storing it", async () => {
    const stored = await hashPassword("correct horse");
    expect(stored).not.toContain("correct horse");
    expect(await checkPassword("correct horse", stored)).toBe(true);
    expect(await checkPassword("wrong horse", stored)).toBe(false);
  });

  it("asks for at least 8 characters", () => {
    expect(passwordProblem("short")).not.toBeNull();
    expect(passwordProblem("long enough")).toBeNull();
  });
});

describe("session tokens", () => {
  it("round-trips the user id", () => {
    expect(readSessionToken(createSessionToken("user-1"))).toBe("user-1");
  });

  it("rejects tampered and expired tokens", () => {
    const token = createSessionToken("user-1");
    const [payload, signature] = token.split(".");
    const forged = Buffer.from(JSON.stringify({ sub: "admin", exp: Date.now() + 1e9 })).toString(
      "base64url",
    );
    expect(readSessionToken(`${forged}.${signature}`)).toBeNull();
    expect(readSessionToken(`${payload}.x`)).toBeNull();
    expect(readSessionToken(createSessionToken("user-1", Date.now() - 31 * 86_400_000))).toBeNull();
  });
});
