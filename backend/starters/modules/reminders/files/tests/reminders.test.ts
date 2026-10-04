import { beforeEach, describe, expect, it } from "vitest";
import { resetStore } from "@/lib/db";
import { reminders, scheduleReminder, sendDueReminders } from "@/lib/reminders";
import type { Message, Notifier } from "@/lib/reminders/notify";

class Recorder implements Notifier {
  sent: Message[] = [];
  async send(message: Message) {
    if (message.to === "broken@example.com") throw new Error("mailbox full");
    this.sent.push(message);
  }
}

describe("reminders", () => {
  beforeEach(() => resetStore());

  it("sends only what's due, once, and records failures", async () => {
    const now = new Date("2026-10-05T09:00:00Z");
    await scheduleReminder({ to: "a@example.com", subject: "Due", message: "m", sendAt: new Date("2026-10-05T08:00:00Z") });
    await scheduleReminder({ to: "b@example.com", subject: "Later", message: "m", sendAt: new Date("2026-10-06T08:00:00Z") });
    await scheduleReminder({ to: "broken@example.com", subject: "Due", message: "m", sendAt: now });
    const notifier = new Recorder();

    expect(await sendDueReminders(now, notifier)).toEqual({ sent: 1, failed: 1 });
    expect(notifier.sent.map((m) => m.to)).toEqual(["a@example.com"]);
    expect(await sendDueReminders(now, notifier)).toEqual({ sent: 0, failed: 0 });
    expect((await reminders().findOne({ status: "failed" }))?.error).toBe("mailbox full");
  });
});
