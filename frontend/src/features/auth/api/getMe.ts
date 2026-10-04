import { ApiError, apiGet } from "@/shared/api/client";

import type { Me } from "../types";

/** Who's signed in; null when nobody is (no cookie, or an expired or invalid token). */
export async function getMe(): Promise<Me | null> {
  try {
    return await apiGet<Me>("/auth/me", { cache: "no-store" });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}
