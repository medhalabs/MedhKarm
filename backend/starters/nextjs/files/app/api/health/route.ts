import { NextResponse } from "next/server";
import { dataMode } from "@/lib/config";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({ ok: true, data: dataMode() });
}
