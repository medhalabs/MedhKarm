import { createHmac, timingSafeEqual } from "node:crypto";
import { env, isProduction } from "../config";

export const SESSION_COOKIE = "session";
export const SESSION_DAYS = 30;

function secret(): string {
  const value = env("SESSION_SECRET");
  if (value) return value;
  if (isProduction && process.env.NEXT_PHASE !== "phase-production-build") {
    console.warn("SESSION_SECRET is not set: sessions use a development secret.");
  }
  return "development-only-secret-change-me";
}

function sign(payload: string): string {
  return createHmac("sha256", secret()).update(payload).digest("base64url");
}

/** A signed token: user id and expiry, readable but not forgeable. */
export function createSessionToken(userId: string, now = Date.now()): string {
  const payload = Buffer.from(
    JSON.stringify({ sub: userId, exp: now + SESSION_DAYS * 86_400_000 }),
  ).toString("base64url");
  return `${payload}.${sign(payload)}`;
}

/** The user id in a valid, unexpired token; null otherwise. */
export function readSessionToken(token: string | undefined, now = Date.now()): string | null {
  if (!token) return null;
  const [payload, signature] = token.split(".");
  if (!payload || !signature) return null;
  const expected = Buffer.from(sign(payload));
  const given = Buffer.from(signature);
  if (expected.length !== given.length || !timingSafeEqual(expected, given)) return null;
  try {
    const { sub, exp } = JSON.parse(Buffer.from(payload, "base64url").toString()) as {
      sub: string;
      exp: number;
    };
    return exp > now ? sub : null;
  } catch {
    return null;
  }
}
