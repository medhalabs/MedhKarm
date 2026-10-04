import { logOutAction } from "../api/actions";

export function SignOutButton() {
  return (
    <form action={logOutAction}>
      <button type="submit" className="text-zinc-600 hover:underline dark:text-zinc-400">
        Log out
      </button>
    </form>
  );
}
