// Mirrors backend/app/features/inbox/schemas.py.

import type { Message } from "@/features/messages";

export type Approval = {
  run_id: string;
  request: string;
  summary: string;
  reasons: string[];
  preview_url: string;
  security: string[];
  waiting_since: string;
};

export type Questions = { project_id: string; project_name: string; questions: string[] };

export type Blocked = {
  project_id: string;
  project_name: string;
  item_id: string;
  title: string;
  note: string;
};

export type Inbox = {
  approvals: Approval[];
  questions: Questions[];
  blocked: Blocked[];
  replies: Message[];
};

export type FormState = { error: string | null };
