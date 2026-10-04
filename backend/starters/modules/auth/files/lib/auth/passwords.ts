import { randomBytes, scrypt, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";

const derive = promisify(scrypt) as (password: string, salt: string, length: number) => Promise<Buffer>;

/** "salt:hash", scrypt with a random salt. */
export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const hash = await derive(password, salt, 64);
  return `${salt}:${hash.toString("hex")}`;
}

export async function checkPassword(password: string, stored: string): Promise<boolean> {
  const [salt, hash] = stored.split(":");
  if (!salt || !hash) return false;
  const expected = Buffer.from(hash, "hex");
  const actual = await derive(password, salt, expected.length);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

export function passwordProblem(password: string): string | null {
  return password.length < 8 ? "Use at least 8 characters." : null;
}
