"use server";

import { refresh } from "next/cache";

import { apiDelete, apiPost } from "@/shared/api/client";

import type { Share } from "../types";

export async function shareAction(runId: string): Promise<void> {
  await apiPost<Share>(`/runs/${encodeURIComponent(runId)}/share`, {});
  refresh();
}

export async function stopSharingAction(runId: string): Promise<void> {
  await apiDelete(`/runs/${encodeURIComponent(runId)}/share`);
  refresh();
}
