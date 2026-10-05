import { getMe } from "@/features/auth";

import { getNotificationSettings } from "../api/getSettings";
import { SettingsForm } from "./SettingsForm";

export async function SettingsPage() {
  const [view, me] = await Promise.all([getNotificationSettings(), getMe()]);
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">Settings</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Your morning standup and Monday report: what was done, what&apos;s planned, what&apos;s
        blocked and what needs you. Nothing is sent until you save an address.
      </p>
      <SettingsForm view={view} suggestedEmail={me?.user.email ?? ""} />
    </div>
  );
}
