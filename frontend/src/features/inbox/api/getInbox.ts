import { ApiError, apiGet } from "@/shared/api/client";

import type { Inbox } from "../types";

export function getInbox(): Promise<Inbox> {
  return apiGet<Inbox>("/inbox", { cache: "no-store" });
}

/** How many things need the founder; 0 when the backend can't say (never breaks the nav). */
export async function getInboxCount(): Promise<number> {
  try {
    return (await apiGet<{ count: number }>("/inbox/count", { cache: "no-store" })).count;
  } catch (error) {
    if (error instanceof ApiError) return 0;
    return 0;
  }
}
