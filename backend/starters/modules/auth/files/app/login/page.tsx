import Link from "next/link";
import AuthForm from "./AuthForm";
import { logIn } from "./actions";

export default function LoginPage() {
  return (
    <main>
      <h1>Log in</h1>
      <AuthForm action={logIn} submit="Log in" />
      <p className="muted">
        New here? <Link href="/signup">Create an account</Link>
      </p>
    </main>
  );
}
