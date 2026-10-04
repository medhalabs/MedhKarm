/** Checks the sign-up and log-in forms before anything is sent to the backend. */

export type SignUpInput = { email: string; password: string; name: string; company_name: string };
export type LogInInput = { email: string; password: string };

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function text(form: FormData, name: string): string {
  return String(form.get(name) ?? "").trim();
}

export function parseLogIn(form: FormData): LogInInput | { error: string } {
  const email = text(form, "email").toLowerCase();
  const password = String(form.get("password") ?? "");
  if (!EMAIL.test(email)) return { error: "Enter your email address." };
  if (!password) return { error: "Enter your password." };
  return { email, password };
}

export function parseSignUp(form: FormData): SignUpInput | { error: string } {
  const login = parseLogIn(form);
  if ("error" in login) return login;
  if (login.password.length < 8) return { error: "Use at least 8 characters for the password." };
  const company_name = text(form, "company_name");
  if (company_name.length < 2) return { error: "Give your company or project a name." };
  return { ...login, name: text(form, "name"), company_name };
}
