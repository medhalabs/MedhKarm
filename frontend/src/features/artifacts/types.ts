// Mirrors backend/app/features/artifacts/schemas.py.

export type Artifact = {
  id: number;
  run_id: string;
  kind: string;
  name: string;
  content_type: string;
  size: number;
  created_at: string;
};
