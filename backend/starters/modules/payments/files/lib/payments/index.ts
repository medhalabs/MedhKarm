import { env } from "../config";
import { getStore } from "../db";
import { RazorpayPayments } from "./razorpay";
import { StripePayments } from "./stripe";
import type { PaymentProvider } from "./types";

export type { NewOrder, Order, PaymentProvider } from "./types";

export type PaymentDoc = {
  id: string;
  createdAt: string;
  provider: string;
  orderId: string;
  amount: number;
  currency: string;
  description: string;
  userId: string | null;
  status: "created" | "paid" | "failed";
  paidAt?: string;
};

export const payments = () => getStore().collection<PaymentDoc>("payments");

/** The provider chosen by PAYMENTS_PROVIDER (Razorpay by default); null until its keys are set. */
export function getPayments(): PaymentProvider | null {
  const provider = (env("PAYMENTS_PROVIDER") ?? "razorpay").toLowerCase();
  if (provider === "stripe") {
    const key = env("STRIPE_SECRET_KEY");
    return key
      ? new StripePayments(key, env("STRIPE_WEBHOOK_SECRET"), env("NEXT_PUBLIC_SITE_URL") ?? "http://localhost:3000")
      : null;
  }
  const keyId = env("RAZORPAY_KEY_ID");
  const keySecret = env("RAZORPAY_KEY_SECRET");
  return keyId && keySecret
    ? new RazorpayPayments(keyId, keySecret, env("RAZORPAY_WEBHOOK_SECRET"))
    : null;
}

/** Marks an order paid once (webhooks can arrive more than once). */
export async function markPaid(orderId: string): Promise<boolean> {
  const record = await payments().findOne({ orderId });
  if (!record) return false;
  if (record.status !== "paid") {
    await payments().update(record.id, { status: "paid", paidAt: new Date().toISOString() });
  }
  return true;
}
