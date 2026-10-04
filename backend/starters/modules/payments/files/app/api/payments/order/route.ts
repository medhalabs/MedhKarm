import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";
import { getPayments, payments } from "@/lib/payments";

/** Creates an order for the amount (in paise) and records it as `created`. Decide prices on
 * the server: replace the body's amount with your product's price before going live. */
export async function POST(request: Request) {
  const provider = getPayments();
  if (!provider) {
    return NextResponse.json({ error: "Payments aren't connected yet." }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { amount?: number; description?: string };
  const amount = Math.round(Number(body.amount));
  if (!Number.isFinite(amount) || amount < 100) {
    return NextResponse.json({ error: "The amount must be at least ₹1 (100 paise)." }, { status: 400 });
  }
  const description = String(body.description ?? "Payment").slice(0, 250);
  const order = await provider.createOrder({ amount, description, receipt: randomUUID() });
  await payments().insert({
    provider: order.provider,
    orderId: order.orderId,
    amount: order.amount,
    currency: order.currency,
    description,
    userId: null,
    status: "created",
  });
  return NextResponse.json(order);
}
