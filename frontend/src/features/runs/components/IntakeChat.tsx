"use client";

import { ChatIntake } from "@/shared/ui/ChatIntake";

import { intakeAction, startFromBriefAction } from "../api/actions";
import type { Brief } from "../types";
import { BriefCard } from "./BriefCard";

const EXAMPLES = [
  "A booking page for my yoga classes where students pick a slot and pay ₹499",
  "Add a CSV export of orders to my shop: https://github.com/you/shop",
  "A landing page for my bakery with a WhatsApp order button",
];

/** Start a run by talking to the CTO: he asks what he needs, then hands over a brief. */
export function IntakeChat() {
  return (
    <ChatIntake<Brief>
      agent={{ name: "Kabir", initial: "K" }}
      title="New run"
      subtitle="Tell Kabir, your CTO, what you need. He'll ask anything that's unclear."
      greeting="Hi! What would you like the team to build? A sentence is fine, or paste a full spec. If it's a change to an existing project, include the GitHub link."
      examples={EXAMPLES}
      placeholder="Describe what you want built…"
      skipLabel="Skip the questions, start now"
      ask={async (turns) => {
        const result = await intakeAction(turns);
        return "error" in result ? result : { text: result.reply.text, brief: result.reply.brief };
      }}
      start={startFromBriefAction}
      skip={(request) =>
        startFromBriefAction({
          request,
          summary: "",
          repo_url: null,
          branch: null,
          create_repo: true,
          new_repo_name: null,
          stack: {},
          test_command: null,
        })
      }
      renderBrief={(brief, c) => (
        <BriefCard
          brief={brief}
          pending={c.pending}
          onStart={c.start}
          onKeepTalking={c.keepTalking}
        />
      )}
    />
  );
}
