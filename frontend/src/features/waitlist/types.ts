// Mirrors backend/app/features/waitlist/schemas.py.

export type Joined = { ok: boolean; count: number };

export type FormState = { error: string | null; joined?: boolean; count?: number };
