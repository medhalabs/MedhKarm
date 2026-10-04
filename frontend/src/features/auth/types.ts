// Mirrors backend/app/features/auth/schemas.py.

export type Company = { id: string; name: string; created_at: string };

export type User = {
  id: string;
  email: string;
  name: string;
  company_id: string;
  created_at: string;
};

export type Session = { token: string; user: User; company: Company };

export type Me = { user: User; company: Company };

export type FormState = { error: string | null };
