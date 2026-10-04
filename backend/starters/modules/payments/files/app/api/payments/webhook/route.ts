import { NextResponse } from "next/server";
import { getPayments, markPaid } from "@/lib/payments";

/** The provider tells us a payment went through. Set this URL in its dashboard. */
export async function POST(request: Request) {
  const provider = getPayments();
  if (!provider) return NextResponse.json({ ok: false }, { status: 503 });
  const signature =
    request.headers.get("x-razorpay-signature") ?? request.headers.get("stripe-signature");
  const orderId = provider.paidOrderFromWebhook(await request.text(), signature);
  if (orderId) await markPaid(orderId);
  return NextResponse.json({ ok: true });
}
