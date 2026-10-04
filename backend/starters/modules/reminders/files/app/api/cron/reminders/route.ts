import { NextResponse } from "next/server";
import { env } from "@/lib/config";
import { sendDueReminders } from "@/lib/reminders";

export const dynamic = "force-dynamic";

/** Sends due reminders. Called by Vercel Cron or the docker-compose `cron` service. */
export async function GET(request: Request) {
  const secret = env("CRON_SECRET");
  if (!secret || request.headers.get("authorization") !== `Bearer ${secret}`) {
    return NextResponse.json({ error: "Not allowed" }, { status: 401 });
  }
  return NextResponse.json(await sendDueReminders());
}
