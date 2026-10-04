import { getStore } from "../db";
import { getNotifier, type Notifier } from "./notify";

export type ReminderDoc = {
  id: string;
  createdAt: string;
  to: string;
  subject: string;
  message: string;
  sendAt: string; // ISO time
  status: "pending" | "sent" | "failed";
  sentAt?: string;
  error?: string;
  userId?: string;
};

export const reminders = () => getStore().collection<ReminderDoc>("reminders");

export async function scheduleReminder(input: {
  to: string;
  subject: string;
  message: string;
  sendAt: Date;
  userId?: string;
}): Promise<ReminderDoc> {
  return reminders().insert({
    to: input.to,
    subject: input.subject,
    message: input.message,
    sendAt: input.sendAt.toISOString(),
    status: "pending",
    userId: input.userId,
  });
}

export function isDue(reminder: ReminderDoc, now: Date): boolean {
  return reminder.status === "pending" && new Date(reminder.sendAt) <= now;
}

/** Sends every reminder that's due; one failure doesn't stop the rest. */
export async function sendDueReminders(
  now = new Date(),
  notifier: Notifier = getNotifier(),
): Promise<{ sent: number; failed: number }> {
  const pending = await reminders().find({ status: "pending" }, 500);
  let sent = 0;
  let failed = 0;
  for (const reminder of pending.filter((r) => isDue(r, now))) {
    try {
      await notifier.send({ to: reminder.to, subject: reminder.subject, text: reminder.message });
      await reminders().update(reminder.id, { status: "sent", sentAt: now.toISOString() });
      sent += 1;
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      await reminders().update(reminder.id, { status: "failed", error: reason });
      failed += 1;
    }
  }
  return { sent, failed };
}
