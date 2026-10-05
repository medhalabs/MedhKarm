import { apiGet } from "@/shared/api/client";

import type { ModelsView } from "../types";

export function getModelSettings(): Promise<ModelsView> {
  return apiGet<ModelsView>("/settings/models", { cache: "no-store" });
}
