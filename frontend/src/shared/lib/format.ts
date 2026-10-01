/**
 * Formatting for people in India: times in IST and numbers with Indian grouping (3,84,000).
 * Fixed locale and time zone, so the server and the browser render the same text.
 */

const TIME_ZONE = "Asia/Kolkata";

const timeFormat = new Intl.DateTimeFormat("en-IN", {
  timeZone: TIME_ZONE,
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

const dateTimeFormat = new Intl.DateTimeFormat("en-IN", {
  timeZone: TIME_ZONE,
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const numberFormat = new Intl.NumberFormat("en-IN");

export function formatTime(iso: string): string {
  return timeFormat.format(new Date(iso));
}

export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso));
}

export function formatNumber(value: number): string {
  return numberFormat.format(value);
}

/** "just now", "5 min ago", "3 h ago", "2 days ago". */
export function timeAgo(iso: string, now: Date = new Date()): string {
  const seconds = Math.max(0, Math.round((now.getTime() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

/** Today's date in IST as YYYY-MM-DD, and days around it. */
export function isoDay(date: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE }).format(date);
}

export function shiftDay(day: string, days: number): string {
  const date = new Date(`${day}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
