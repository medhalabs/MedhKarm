import { requireUser } from "@/lib/auth";
import { logOut } from "../login/actions";

export const dynamic = "force-dynamic";

export default async function AccountPage() {
  const user = await requireUser();
  return (
    <main>
      <h1>Your account</h1>
      <div className="card">
        <p>
          Signed in as <strong>{user.name ?? user.email}</strong>
        </p>
        <form action={logOut}>
          <button type="submit">Log out</button>
        </form>
      </div>
    </main>
  );
}
