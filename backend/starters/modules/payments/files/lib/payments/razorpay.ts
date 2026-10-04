import { hmacHex, sameHex } from "./signatures";
import type { NewOrder, Order, PaymentProvider } from "./types";

const API = "https://api.razorpay.com/v1";

/** Razorpay: UPI, cards, netbanking and wallets in rupees. */
export class RazorpayPayments implements PaymentProvider {
  readonly name = "razorpay";

  constructor(
    private readonly keyId: string,
    private readonly keySecret: string,
    private readonly webhookSecret?: string,
  ) {}

  async createOrder(order: NewOrder): Promise<Order> {
    const response = await fetch(`${API}/orders`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${Buffer.from(`${this.keyId}:${this.keySecret}`).toString("base64")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: order.amount,
        currency: order.currency ?? "INR",
        receipt: order.receipt.slice(0, 40),
        notes: { description: order.description.slice(0, 250) },
      }),
    });
    if (!response.ok) throw new Error(`Razorpay refused the order (${response.status})`);
    const data = (await response.json()) as { id: string; amount: number; currency: string };
    return {
      provider: this.name,
      orderId: data.id,
      amount: data.amount,
      currency: data.currency,
      checkout: { key: this.keyId, description: order.description },
    };
  }

  verifyPayment(fields: Record<string, string>): boolean {
    const { razorpay_order_id: orderId, razorpay_payment_id: paymentId, razorpay_signature: signature } = fields;
    if (!orderId || !paymentId || !signature) return false;
    return sameHex(hmacHex(this.keySecret, `${orderId}|${paymentId}`), signature);
  }

  paidOrderFromWebhook(rawBody: string, signature: string | null): string | null {
    if (!this.webhookSecret || !signature) return null;
    if (!sameHex(hmacHex(this.webhookSecret, rawBody), signature)) return null;
    const event = JSON.parse(rawBody) as {
      event?: string;
      payload?: { payment?: { entity?: { order_id?: string } }; order?: { entity?: { id?: string } } };
    };
    if (event.event === "order.paid") return event.payload?.order?.entity?.id ?? null;
    if (event.event === "payment.captured") return event.payload?.payment?.entity?.order_id ?? null;
    return null;
  }
}
