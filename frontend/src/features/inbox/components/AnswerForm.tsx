"use client";

import { useActionState } from "react";

import { answerAction } from "../api/actions";
import type { FormState, Questions } from "../types";

const initial: FormState = { error: null };

/** Mira's open questions on one project; answers go into every later plan. */
export function AnswerForm({ project }: { project: Questions }) {
  const [state, formAction, pending] = useActionState(
    answerAction.bind(null, project.project_id, project.questions),
    initial,
  );
  return (
    <form action={formAction} className="flex flex-col gap-3">
      {project.questions.map((q, i) => (
        <label key={q} className="flex flex-col gap-1 text-sm">
          <span className="font-medium">{q}</span>
          <input
            name={`answer_${i}`}
            maxLength={2000}
            placeholder="Your answer (leave empty to answer later)"
            className="field"
          />
        </label>
      ))}
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" name="replan" />
          Ask Mira to plan again with these
        </label>
        <button type="submit" disabled={pending} className="btn-primary">
          {pending ? "Saving…" : "Save answers"}
        </button>
        {state.error && (
          <p role="alert" className="text-red-600 dark:text-red-400">
            {state.error}
          </p>
        )}
      </div>
    </form>
  );
}
