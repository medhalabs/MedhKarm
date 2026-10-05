import { getMe } from "@/features/auth";
import { PageHeader } from "@/shared/ui/PageHeader";

import { getNotificationSettings } from "../api/getSettings";
import { SettingsForm } from "./SettingsForm";

export async function SettingsPage() {
  const [view, me] = await Promise.all([getNotificationSettings(), getMe()]);
  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Settings"
        description="Your morning standup and Monday report: done, planned, blocked and what needs you. Nothing is sent until you save an address."
      />
      <SettingsForm view={view} suggestedEmail={me?.user.email ?? ""} />
    </div>
  );
}
