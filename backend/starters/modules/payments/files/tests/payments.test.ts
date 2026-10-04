import { describe, expect, it } from "vitest";
import { RazorpayPayments } from "@/lib/payments/razorpay";
import { hmacHex } from "@/lib/payments/signatures";
import { StripePayments } from "@/lib/payments/stripe";

describe("Razorpay", () => {
  const razorpay = new RazorpayPayments("rzp_test_key", "key-secret", "hook-secret");

  it("accepts a payment only with the right signature", () => {
    const fields = {
      razorpay_order_id: "order_1",
      razorpay_payment_id: "pay_1",
      razorpay_signature: hmacHex("key-secret", "order_1|pay_1"),
    };
    expect(razorpay.verifyPayment(fields)).toBe(true);
    expect(razorpay.verifyPayment({ ...fields, razorpay_payment_id: "pay_2" })).toBe(false);
    expect(razorpay.verifyPayment({})).toBe(false);
  });

  it("reads the paid order from a genuine webhook only", () => {
    const body = JSON.stringify({
      event: "payment.captured",
      payload: { payment: { entity: { order_id: "order_1" } } },
    });
    expect(razorpay.paidOrderFromWebhook(body, hmacHex("hook-secret", body))).toBe("order_1");
    expect(razorpay.paidOrderFromWebhook(body, hmacHex("other", body))).toBeNull();
    expect(razorpay.paidOrderFromWebhook(body, null)).toBeNull();
  });
});

describe("Stripe", () => {
  const stripe = new StripePayments("sk_test", "whsec", "http://localhost:3000");
  const body = JSON.stringify({
    type: "checkout.session.completed",
    data: { object: { id: "cs_1", payment_status: "paid" } },
  });

  it("reads the paid session from a signed, recent webhook", () => {
    const now = 1_700_000_000_000;
    const t = String(now / 1000);
    const header = `t=${t},v1=${hmacHex("whsec", `${t}.${body}`)}`;
    expect(stripe.paidOrderFromWebhook(body, header, now)).toBe("cs_1");
    expect(stripe.paidOrderFromWebhook(body, header, now + 10 * 60_000)).toBeNull(); // too old
    expect(stripe.paidOrderFromWebhook(body, `t=${t},v1=bad`, now)).toBeNull();
  });
});
