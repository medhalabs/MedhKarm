import Link from "next/link";

import { BackendStatus } from "@/features/health";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center gap-4 px-6">
      <h1 className="text-3xl font-semibold tracking-tight">MedhKarm</h1>
      <p className="text-zinc-600 dark:text-zinc-400">Your AI software company.</p>
      <BackendStatus />
      <Link href="/admin" className="text-sm font-medium underline">
        Open the admin page →
      </Link>
    </main>
  );
}
