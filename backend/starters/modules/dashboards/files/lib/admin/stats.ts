import { env } from "../config";
import type { Doc } from "../db";

/** Collections shown on /admin. Add yours here. */
export const ADMIN_COLLECTIONS = ["users", "payments", "reminders"];

export function isAdmin(email: string | undefined): boolean {
  if (!email) return false;
  const admins = (env("ADMIN_EMAILS") ?? "")
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
  return admins.includes(email.toLowerCase());
}

export type DayCount = { day: string; count: number };

/** New records per day for the last `days` days, oldest first (days with none count 0). */
export function perDay(docs: Pick<Doc, "createdAt">[], days = 14, now = new Date()): DayCount[] {
  const counts = new Map<string, number>();
  for (let i = days - 1; i >= 0; i -= 1) {
    const day = new Date(now.getTime() - i * 86_400_000).toISOString().slice(0, 10);
    counts.set(day, 0);
  }
  for (const doc of docs) {
    const day = doc.createdAt.slice(0, 10);
    if (counts.has(day)) counts.set(day, (counts.get(day) ?? 0) + 1);
  }
  return [...counts].map(([day, count]) => ({ day, count }));
}

/** A record's fields as short text for a table, without secrets. */
export function preview(doc: Doc): string {
  return Object.entries(doc)
    .filter(([key]) => !["id", "createdAt"].includes(key) && !/password|secret|token|hash/i.test(key))
    .map(([key, value]) => `${key}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`)
    .join(" · ")
    .slice(0, 160);
}
