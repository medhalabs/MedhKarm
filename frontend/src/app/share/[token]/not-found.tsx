import Link from "next/link";

export default function ShareNotFound() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-3 px-6 text-center">
      <h1 className="text-2xl font-semibold">This link doesn&apos;t work</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        It may have been turned off by its owner, or the address is wrong.
      </p>
      <Link href="/" className="text-sm font-medium text-indigo-600 underline dark:text-indigo-400">
        What is MedhKarm?
      </Link>
    </main>
  );
}
