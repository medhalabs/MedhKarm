import { redirect } from "next/navigation";

import { AuthForm, getMe } from "@/features/auth";

export default async function Page() {
  if (await getMe()) redirect("/admin");
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-12">
      <AuthForm mode="login" />
    </main>
  );
}
