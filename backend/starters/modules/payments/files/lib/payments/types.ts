export type Order = {
  provider: string;
  orderId: string;
  amount: number; // in paise (₹1 = 100)
  currency: string;
  /** What the browser needs to pay: Razorpay's public key, or Stripe's checkout URL. */
  checkout: Record<string, string>;
};

export type NewOrder = { amount: number; currency?: string; description: string; receipt: string };

/** A payment provider. Every check uses the provider's signature, never the browser's word. */
export interface PaymentProvider {
  readonly name: string;
  createOrder(order: NewOrder): Promise<Order>;
  /** Razorpay Checkout's callback fields; Stripe confirms through the webhook instead. */
  verifyPayment(fields: Record<string, string>): boolean;
  /** The order id a genuine "paid" webhook is about, or null (bad signature or another event). */
  paidOrderFromWebhook(rawBody: string, signature: string | null): string | null;
}
