import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { getMe, SignOutButton } from "@/features/auth";
import { getInboxCount } from "@/features/inbox";
import {
  InboxIcon,
  ModelsIcon,
  ProjectsIcon,
  RunsIcon,
  SettingsIcon,
  StandupIcon,
} from "@/shared/ui/icons";
import { NavLink } from "@/shared/ui/NavLink";

export const metadata: Metadata = { title: "MedhKarm" };

export default async function AdminLayout({ children }: LayoutProps<"/admin">) {
  const me = await getMe();
  if (!me) redirect("/login");
  const waiting = await getInboxCount();

  const nav = (
    <>
      <NavLink href="/admin/inbox">
        <InboxIcon />
        Inbox
        {waiting > 0 && (
          <span className="ml-auto rounded-full bg-amber-500 px-1.5 py-0.5 text-[11px] leading-none font-semibold text-white">
            {waiting}
          </span>
        )}
      </NavLink>
      <NavLink href="/admin" exact>
        <RunsIcon />
        Runs
      </NavLink>
      <NavLink href="/admin/projects">
        <ProjectsIcon />
        Projects
      </NavLink>
      <NavLink href="/admin/standup">
        <StandupIcon />
        Standup
      </NavLink>
      <NavLink href="/admin/models">
        <ModelsIcon />
        Models
      </NavLink>
      <NavLink href="/admin/settings">
        <SettingsIcon />
        Settings
      </NavLink>
    </>
  );

  return (
    <div className="flex min-h-full flex-1 bg-zinc-50 dark:bg-zinc-950">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col gap-6 border-r border-zinc-200 bg-zinc-100/60 px-3 py-5 md:flex dark:border-zinc-800 dark:bg-zinc-900/40">
        <Link href="/admin" className="flex items-center gap-2.5 px-3">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
            M
          </span>
          <span className="leading-tight">
            <span className="block text-sm font-semibold tracking-tight">MedhKarm</span>
            <span className="block text-xs text-zinc-500">AI software team</span>
          </span>
        </Link>
        <nav className="flex flex-col gap-1" aria-label="Main">
          {nav}
        </nav>
        <div className="mt-auto flex flex-col gap-1 border-t border-zinc-200 pt-4 dark:border-zinc-800">
          <p className="truncate px-3 text-xs text-zinc-500">Signed in to</p>
          <p className="truncate px-3 pb-1 text-sm font-medium">{me.company.name}</p>
          <SignOutButton />
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 overflow-x-auto border-b border-zinc-200 bg-white px-4 py-2 md:hidden dark:border-zinc-800 dark:bg-zinc-900">
          <span className="mr-2 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-xs font-bold text-white">
            M
          </span>
          <nav className="flex gap-1" aria-label="Main">
            {nav}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8 md:py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
