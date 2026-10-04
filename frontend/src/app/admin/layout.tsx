import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { getMe, SignOutButton } from "@/features/auth";

export const metadata: Metadata = { title: "MedhKarm admin" };

export default async function AdminLayout({ children }: LayoutProps<"/admin">) {
  const me = await getMe();
  if (!me) redirect("/login");
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-6">
      <nav className="flex items-center gap-6 border-b border-zinc-200 pb-3 text-sm dark:border-zinc-800">
        <Link href="/admin" className="text-base font-semibold">
          MedhKarm admin
        </Link>
        <Link href="/admin" className="text-zinc-600 hover:underline dark:text-zinc-400">
          Runs
        </Link>
        <Link href="/admin/projects" className="text-zinc-600 hover:underline dark:text-zinc-400">
          Projects
        </Link>
        <Link href="/admin/standup" className="text-zinc-600 hover:underline dark:text-zinc-400">
          Standup
        </Link>
        <span className="ml-auto text-zinc-500">{me.company.name}</span>
        <SignOutButton />
      </nav>
      <main>{children}</main>
    </div>
  );
}
