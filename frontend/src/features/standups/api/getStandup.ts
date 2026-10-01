import { ApiError, apiGet } from "@/shared/api/client";

import type { Standup } from "../types";

/** The standup for a day (YYYY-MM-DD), or null if that day hasn't started yet. */
export async function getStandup(day: string): Promise<Standup | null> {
  try {
    return await apiGet<Standup>(`/standups/${day}`, { cache: "no-store" });
  } catch (error) {
    if (error instanceof ApiError && error.status === 400) return null;
    throw error;
  }
}
