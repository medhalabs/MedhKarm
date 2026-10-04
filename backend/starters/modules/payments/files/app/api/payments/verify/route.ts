import { NextResponse } from "next/server";
import { getPayments, markPaid } from "@/lib/payments";

/** Razorpay Checkout's success callback: paid only if the signature checks out. */
export async function POST(request: Request) {
  const provider = getPayments();
  const fields = (await request.json().catch(() => ({}))) as Record<string, string>;
  if (!provider || !provider.verifyPayment(fields)) {
    return NextResponse.json({ paid: false }, { status: 400 });
  }
  return NextResponse.json({ paid: await markPaid(fields.razorpay_order_id) });
}
