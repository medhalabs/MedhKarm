"use client";

import { useActionState } from "react";
import type { FormState } from "./actions";

type Props = {
  action: (state: FormState, form: FormData) => Promise<FormState>;
  submit: string;
  withName?: boolean;
};

export default function AuthForm({ action, submit, withName = false }: Props) {
  const [state, formAction, pending] = useActionState(action, {});
  return (
    <form action={formAction} className="stack">
      {withName && (
        <label>
          Name
          <input name="name" autoComplete="name" />
        </label>
      )}
      <label>
        Email
        <input name="email" type="email" required autoComplete="email" />
      </label>
      <label>
        Password
        <input
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete={withName ? "new-password" : "current-password"}
        />
      </label>
      {state.error && (
        <p role="alert" className="error">
          {state.error}
        </p>
      )}
      <button type="submit" disabled={pending}>
        {pending ? "Please wait…" : submit}
      </button>
    </form>
  );
}
