"use client";

import { useActionState } from "react";

import { saveSettingsAction, sendTestAction } from "../api/actions";
import type { FormState, SettingsView } from "../types";

const initial: FormState = { error: null };
const field = "field";

/** Where the daily standup and the Monday report go, and when. */
export function SettingsForm({
  view,
  suggestedEmail,
}: {
  view: SettingsView;
  suggestedEmail: string;
}) {
  const [saved, save, saving] = useActionState(saveSettingsAction, initial);
  const [test, sendTest, testing] = useActionState(sendTestAction, initial);
  const s = view.settings;
  const missing = (["email", "whatsapp"] as const).filter((c) => !view.available.includes(c));

  return (
    <div className="flex flex-col gap-4">
      <form action={save} className="flex max-w-lg flex-col gap-3 card p-5">
        <label className="flex flex-col gap-1 text-sm font-medium">
          Email
          <input
            name="email"
            type="email"
            defaultValue={s.email || suggestedEmail}
            className={field}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          WhatsApp number (with country code)
          <input
            name="whatsapp"
            defaultValue={s.whatsapp}
            placeholder="+919876543210"
            className={field}
          />
        </label>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" name="standup_on" defaultChecked={s.standup_on} />
            Daily standup at
          </label>
          <select name="standup_hour" defaultValue={s.standup_hour} className={`${field} py-1`}>
            {Array.from({ length: 24 }, (_, h) => (
              <option key={h} value={h}>
                {String(h).padStart(2, "0")}:00
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2">
            <input type="checkbox" name="weekly_on" defaultChecked={s.weekly_on} />
            Weekly report on Mondays
          </label>
        </div>
        {missing.length > 0 && (
          <p className="text-xs text-amber-700 dark:text-amber-400">
            Not set up on the server yet: {missing.join(" and ")} (see the setup guide). You can
            still save the address.
          </p>
        )}
        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Saving…" : "Save"}
          </button>
          {saved.saved && (
            <span className="text-sm text-emerald-700 dark:text-emerald-400">Saved.</span>
          )}
          {saved.error && (
            <p role="alert" className="text-sm text-red-600 dark:text-red-400">
              {saved.error}
            </p>
          )}
        </div>
      </form>
      <form action={sendTest} className="flex flex-col gap-2">
        <button
          type="submit"
          disabled={testing}
          className="w-fit rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium dark:border-zinc-700"
        >
          {testing ? "Sending…" : "Send me a test"}
        </button>
        {test.error && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {test.error}
          </p>
        )}
        {test.results?.map((r) => (
          <p
            key={r.channel}
            className={`text-sm ${r.ok ? "text-emerald-700 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}
          >
            {r.channel === "email" ? "Email" : "WhatsApp"} to {r.to}: {r.ok ? "sent" : r.error}
          </p>
        ))}
      </form>
    </div>
  );
}
