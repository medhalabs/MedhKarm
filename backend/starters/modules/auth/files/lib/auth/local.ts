import { cookies } from "next/headers";
import { getStore } from "../db";
import { isProduction } from "../config";
import { checkPassword, hashPassword, passwordProblem } from "./passwords";
import { SESSION_COOKIE, SESSION_DAYS, createSessionToken, readSessionToken } from "./session";
import type { AuthProvider, AuthResult, User } from "./types";

type UserDoc = { id: string; createdAt: string; email: string; name?: string; passwordHash: string };

const users = () => getStore().collection<UserDoc>("users");
const publicUser = (doc: UserDoc): User => ({ id: doc.id, email: doc.email, name: doc.name });

async function startSession(userId: string): Promise<void> {
  (await cookies()).set(SESSION_COOKIE, createSessionToken(userId), {
    httpOnly: true,
    sameSite: "lax",
    secure: isProduction,
    path: "/",
    maxAge: SESSION_DAYS * 86_400,
  });
}

/** Accounts in the app's own data store; a signed session cookie. */
export class LocalAuth implements AuthProvider {
  async currentUser(): Promise<User | null> {
    const id = readSessionToken((await cookies()).get(SESSION_COOKIE)?.value);
    const doc = id ? await users().get(id) : null;
    return doc ? publicUser(doc) : null;
  }

  async signUp(email: string, password: string, name?: string): Promise<AuthResult> {
    const normalised = email.trim().toLowerCase();
    const problem = passwordProblem(password);
    if (problem) return { error: problem };
    if (await users().findOne({ email: normalised })) {
      return { error: "An account with this email already exists." };
    }
    const doc = await users().insert({
      email: normalised,
      name: name?.trim() || undefined,
      passwordHash: await hashPassword(password),
    });
    await startSession(doc.id);
    return { user: publicUser(doc) };
  }

  async logIn(email: string, password: string): Promise<AuthResult> {
    const doc = await users().findOne({ email: email.trim().toLowerCase() });
    if (!doc || !(await checkPassword(password, doc.passwordHash))) {
      return { error: "Wrong email or password." };
    }
    await startSession(doc.id);
    return { user: publicUser(doc) };
  }

  async logOut(): Promise<void> {
    (await cookies()).delete(SESSION_COOKIE);
  }
}
