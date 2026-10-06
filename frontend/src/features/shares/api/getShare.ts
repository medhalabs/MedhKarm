import { ApiError, apiGet } from "@/shared/api/client";

import type { PublicShare, Share } from "../types";

/** This build's public link, or null when it isn't shared. */
export async function getShare(runId: string): Promise<Share | null> {
  return apiGet<Share | null>(`/runs/${encodeURIComponent(runId)}/share`, { cache: "no-store" });
}

/** What the public sees of a shared build, or null when the link doesn't work (any more). */
export async function getPublicShare(token: string): Promise<PublicShare | null> {
  try {
    return await apiGet<PublicShare>(`/public/shares/${encodeURIComponent(token)}`, {
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
