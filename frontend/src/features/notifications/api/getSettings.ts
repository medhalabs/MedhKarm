import { apiGet } from "@/shared/api/client";

import type { SettingsView } from "../types";

export function getNotificationSettings(): Promise<SettingsView> {
  return apiGet<SettingsView>("/settings/notifications", { cache: "no-store" });
}
