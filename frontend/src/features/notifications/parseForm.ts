/** Checks the update settings form before it's sent to the backend. */

export type SettingsInput = {
  email: string;
  whatsapp: string;
  standup_on: boolean;
  standup_hour: number;
  weekly_on: boolean;
};

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE = /^\+[1-9]\d{7,14}$/;

export function parseSettings(form: FormData): SettingsInput | { error: string } {
  const email = String(form.get("email") ?? "")
    .trim()
    .toLowerCase();
  const whatsapp = String(form.get("whatsapp") ?? "").replace(/[\s()-]/g, "");
  const hour = Number(form.get("standup_hour") ?? 9);
  if (email && !EMAIL.test(email)) return { error: "Enter a valid email address." };
  if (whatsapp && !PHONE.test(whatsapp))
    return { error: "Use the full WhatsApp number with country code, e.g. +919876543210." };
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) return { error: "Pick an hour." };
  return {
    email,
    whatsapp,
    standup_on: form.get("standup_on") === "on",
    standup_hour: hour,
    weekly_on: form.get("weekly_on") === "on",
  };
}
