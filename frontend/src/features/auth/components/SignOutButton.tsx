import { LogoutIcon } from "@/shared/ui/icons";

import { logOutAction } from "../api/actions";

export function SignOutButton() {
  return (
    <form action={logOutAction}>
      <button
        type="submit"
        className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-zinc-600 transition hover:bg-zinc-200/60 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/60 dark:hover:text-zinc-100"
      >
        <LogoutIcon />
        Log out
      </button>
    </form>
  );
}
