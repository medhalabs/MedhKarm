import { cancelRunAction } from "../api/actions";

/** Stops the run, whatever it's doing; its work is thrown away. */
export function CancelRunButton({ runId }: { runId: string }) {
  return (
    <form action={cancelRunAction.bind(null, runId)}>
      <button
        type="submit"
        className="rounded-md border border-zinc-300 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
      >
        Cancel run
      </button>
    </form>
  );
}
