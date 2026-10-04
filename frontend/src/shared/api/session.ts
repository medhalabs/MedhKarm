import { cookies } from "next/headers";

/** The signed-in founder's session token, kept in an httpOnly cookie (server side only). */
export const SESSION_COOKIE = "medhkarm_session";
export const SESSION_DAYS = 30;

export async function sessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}
