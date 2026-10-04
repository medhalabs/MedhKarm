/** Settings from the environment. Nothing here is required: without keys the app runs in
 * local mode (data in memory, or in .data/ during development), so tests and previews work. */

export type DataMode = "postgres" | "local";

export function env(name: string): string | undefined {
  const value = process.env[name];
  return value && value.trim() !== "" ? value : undefined;
}

/** Postgres when DATABASE_URL is set (Supabase's connection string works too). */
export function dataMode(): DataMode {
  return env("DATABASE_URL") ? "postgres" : "local";
}

export const isProduction = process.env.NODE_ENV === "production";
