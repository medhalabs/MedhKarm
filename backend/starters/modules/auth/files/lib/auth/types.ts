export type User = { id: string; email: string; name?: string };

export type AuthResult = { user: User } | { error: string };

/** Who's signed in, and how they sign in. Local accounts or Supabase Auth (lib/auth/index.ts). */
export interface AuthProvider {
  currentUser(): Promise<User | null>;
  signUp(email: string, password: string, name?: string): Promise<AuthResult>;
  logIn(email: string, password: string): Promise<AuthResult>;
  logOut(): Promise<void>;
}
