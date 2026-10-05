"use client";

import { ChatIntake } from "@/shared/ui/ChatIntake";

import { createFromBriefAction, projectIntakeAction } from "../api/actions";
import type { ProjectBrief } from "../types";
import { ProjectBriefCard } from "./ProjectBriefCard";

const EXAMPLES = [
  "An app for my yoga studio: class schedule, bookings with payment, and reminders",
  "A simple CRM for my interior design clients, with quotes and follow-ups",
  "Keep improving my shop: https://github.com/you/shop",
];

/** Start a project by talking to Mira: she asks about the product, then plans its backlog. */
export function ProjectIntake() {
  return (
    <ChatIntake<ProjectBrief>
      agent={{ name: "Mira", initial: "M" }}
      title="New project"
      subtitle="Tell Mira, your product manager, about the product. She'll ask what she needs, then plan the backlog."
      greeting="Hi, I'm Mira. What are you building, and who is it for? Rough ideas are fine; I'll ask about the rest. For an existing project, share the GitHub link."
      examples={EXAMPLES}
      placeholder="Describe your product…"
      skipLabel="Skip the questions, plan it now"
      ask={projectIntakeAction}
      start={createFromBriefAction}
      skip={(goal) => {
        const firstLine = goal
          .split("\n")[0]
          .replace(/[#*>`]/g, "")
          .trim();
        return createFromBriefAction({
          name: (firstLine.length > 60 ? `${firstLine.slice(0, 57)}…` : firstLine) || "New project",
          goal: goal.length >= 10 ? goal : `${goal} (as described)`,
          summary: "",
          repo_url: null,
          stack: {},
          autopilot: false,
          daily_limit: 2,
        });
      }}
      renderBrief={(brief, c) => (
        <ProjectBriefCard
          brief={brief}
          pending={c.pending}
          onStart={c.start}
          onKeepTalking={c.keepTalking}
        />
      )}
    />
  );
}
