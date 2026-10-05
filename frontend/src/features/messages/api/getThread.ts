import { apiGet } from "@/shared/api/client";

import type { Message } from "../types";

export function getThread(thread: "run" | "project", id: string): Promise<Message[]> {
  const key = thread === "run" ? "run_id" : "project_id";
  return apiGet<Message[]>(`/messages?${key}=${encodeURIComponent(id)}`, { cache: "no-store" });
}
