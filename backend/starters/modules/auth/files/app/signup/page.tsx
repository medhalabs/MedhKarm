import Link from "next/link";
import AuthForm from "../login/AuthForm";
import { signUp } from "../login/actions";

export default function SignupPage() {
  return (
    <main>
      <h1>Create an account</h1>
      <AuthForm action={signUp} submit="Sign up" withName />
      <p className="muted">
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </main>
  );
}
