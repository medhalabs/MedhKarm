// Mirrors backend/app/features/notifications/schemas.py.

export type Channel = "email" | "whatsapp";

export type NotificationSettings = {
  company_id: string;
  email: string;
  whatsapp: string;
  standup_on: boolean;
  standup_hour: number;
  weekly_on: boolean;
  nudge_on: boolean;
};

export type SettingsView = { settings: NotificationSettings; available: Channel[] };

export type Delivery = { channel: Channel; to: string; ok: boolean; error: string };

export type FormState = { error: string | null; saved?: boolean; results?: Delivery[] };
