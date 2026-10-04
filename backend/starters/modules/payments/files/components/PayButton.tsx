"use client";

import { useState } from "react";

type Props = { amount: number; description: string; label?: string };

type RazorpayOptions = Record<string, unknown> & { handler: (r: Record<string, string>) => void };
declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => { open(): void };
  }
}

function loadRazorpay(): Promise<void> {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Couldn't load Razorpay"));
    document.body.appendChild(script);
  });
}

/** Pays `amount` (paise) with the project's provider; shows what happened. */
export default function PayButton({ amount, description, label = "Pay" }: Props) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function pay() {
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch("/api/payments/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount, description }),
      });
      const order = await response.json();
      if (!response.ok) throw new Error(order.error ?? "Couldn't start the payment.");
      if (order.provider === "stripe") {
        window.location.href = order.checkout.url;
        return;
      }
      await loadRazorpay();
      new window.Razorpay!({
        key: order.checkout.key,
        order_id: order.orderId,
        amount: order.amount,
        currency: order.currency,
        description,
        handler: async (result) => {
          const verified = await fetch("/api/payments/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(result),
          });
          setMessage(verified.ok ? "Payment received. Thank you!" : "We couldn't confirm the payment.");
        },
      }).open();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button type="button" onClick={pay} disabled={busy}>
        {busy ? "Starting…" : `${label} ₹${(amount / 100).toLocaleString("en-IN")}`}
      </button>
      {message && <p role="status">{message}</p>}
    </div>
  );
}
