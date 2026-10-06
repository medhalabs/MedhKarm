// Mirrors backend/app/features/shares/schemas.py.

import type { ActivityEvent } from "@/features/events/client";

export type Share = { token: string; run_id: string; views: number; created_at: string };

export type PublicMember = { role: string; title: string; name: string };

export type PublicStats = {
  tasks: number;
  minutes: number;
  checks_passed: boolean;
  security_clean: boolean;
  docs_updated: boolean;
};

export type PublicShare = {
  title: string;
  status: string;
  team: PublicMember[];
  events: ActivityEvent[]; // the safe, whitelisted steps (tokens are 0, run_id is the token)
  stats: PublicStats;
  has_demo: boolean;
  live_url: string;
};
