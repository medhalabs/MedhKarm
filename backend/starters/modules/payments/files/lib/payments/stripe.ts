import { hmacHex, sameHex } from "./signatures";
import type { NewOrder, Order, PaymentProvider } from "./types";

const API = "https://api.stripe.com/v1";
const TOLERANCE_SECONDS = 300;

/** Stripe Checkout: Stripe hosts the payment page; the webhook confirms payment. */
export class StripePayments implements PaymentProvider {
  readonly name = "stripe";

  constructor(
    private readonly secretKey: string,
    private readonly webhookSecret: string | undefined,
    private readonly siteUrl: string,
  ) {}

  async createOrder(order: NewOrder): Promise<Order> {
    const currency = (order.currency ?? "INR").toLowerCase();
    const form = new URLSearchParams({
      mode: "payment",
      "line_items[0][quantity]": "1",
      "line_items[0][price_data][currency]": currency,
      "line_items[0][price_data][unit_amount]": String(order.amount),
      "line_items[0][price_data][product_data][name]": order.description.slice(0, 250),
      client_reference_id: order.receipt,
      success_url: `${this.siteUrl}/pay?status=paid`,
      cancel_url: `${this.siteUrl}/pay?status=cancelled`,
    });
    const response = await fetch(`${API}/checkout/sessions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.secretKey}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form,
    });
    if (!response.ok) throw new Error(`Stripe refused the checkout (${response.status})`);
    const data = (await response.json()) as { id: string; url: string; amount_total: number };
    return {
      provider: this.name,
      orderId: data.id,
      amount: data.amount_total,
      currency: currency.toUpperCase(),
      checkout: { url: data.url },
    };
  }

  verifyPayment(): boolean {
    return false; // Stripe confirms through the webhook
  }

  paidOrderFromWebhook(rawBody: string, signature: string | null, now = Date.now()): string | null {
    if (!this.webhookSecret || !signature) return null;
    const parts = Object.fromEntries(
      signature.split(",").map((part) => part.split("=", 2) as [string, string]),
    );
    const timestamp = Number(parts.t);
    if (!parts.v1 || !timestamp || Math.abs(now / 1000 - timestamp) > TOLERANCE_SECONDS) return null;
    if (!sameHex(hmacHex(this.webhookSecret, `${parts.t}.${rawBody}`), parts.v1)) return null;
    const event = JSON.parse(rawBody) as {
      type?: string;
      data?: { object?: { id?: string; payment_status?: string } };
    };
    const session = event.data?.object;
    return event.type === "checkout.session.completed" && session?.payment_status === "paid"
      ? (session.id ?? null)
      : null;
  }
}
