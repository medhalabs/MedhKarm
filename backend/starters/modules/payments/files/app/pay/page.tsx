import PayButton from "@/components/PayButton";
import { getPayments } from "@/lib/payments";

export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ status?: string }> };

export default async function PayPage({ searchParams }: Props) {
  const { status } = await searchParams;
  const connected = getPayments() !== null;
  return (
    <main>
      <h1>Pay</h1>
      {status === "paid" && <p role="status">Payment received. Thank you!</p>}
      {status === "cancelled" && <p role="status">Payment cancelled.</p>}
      {connected ? (
        <PayButton amount={49900} description="Example payment" />
      ) : (
        <p className="muted">Payments aren&apos;t connected yet: add the provider&apos;s keys to the settings.</p>
      )}
    </main>
  );
}
