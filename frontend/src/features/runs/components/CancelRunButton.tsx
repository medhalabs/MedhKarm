import { cancelRunAction } from "../api/actions";

/** Stops the run, whatever it's doing; its work is thrown away. */
export function CancelRunButton({ runId }: { runId: string }) {
  return (
    <form action={cancelRunAction.bind(null, runId)}>
      <button
        type="submit"
        className="btn-secondary w-full text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
      >
        Cancel run
      </button>
    </form>
  );
}
