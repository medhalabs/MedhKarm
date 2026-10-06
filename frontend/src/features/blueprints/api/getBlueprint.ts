import { apiGet } from "@/shared/api/client";

import type { Blueprint } from "../types";

export function getBlueprint(id: string): Promise<Blueprint> {
  return apiGet<Blueprint>(`/blueprints/${encodeURIComponent(id)}`, { cache: "no-store" });
}
