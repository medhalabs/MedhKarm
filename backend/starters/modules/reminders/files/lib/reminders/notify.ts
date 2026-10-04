import { env } from "../config";

export type Message = { to: string; subject: string; text: string };

/** Delivers a message. Email (Resend) or the log; SMS/WhatsApp would be another class. */
export interface Notifier {
  send(message: Message): Promise<void>;
}

export class LogNotifier implements Notifier {
  async send(message: Message): Promise<void> {
    console.info(`[reminder] to ${message.to}: ${message.subject} — ${message.text}`);
  }
}

export class ResendNotifier implements Notifier {
  constructor(
    private readonly apiKey: string,
    private readonly from: string,
  ) {}

  async send(message: Message): Promise<void> {
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: this.from, to: [message.to], subject: message.subject, text: message.text }),
    });
    if (!response.ok) throw new Error(`Resend refused the email (${response.status})`);
  }
}

export function getNotifier(): Notifier {
  const key = env("RESEND_API_KEY");
  return key
    ? new ResendNotifier(key, env("EMAIL_FROM") ?? "App <onboarding@resend.dev>")
    : new LogNotifier();
}
