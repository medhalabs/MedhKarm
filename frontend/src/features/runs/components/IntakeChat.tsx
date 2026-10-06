"use client";

import { askForPlanAction } from "@/features/blueprints/client";
import { ChatIntake } from "@/shared/ui/ChatIntake";

import { intakeAction, startFromBriefAction } from "../api/actions";
import { briefBody } from "../briefBody";
import type { About, Brief } from "../types";
import { BriefCard } from "./BriefCard";

const EXAMPLES = [
  "A booking page for my yoga classes where students pick a slot and pay ₹499",
  "Add a CSV export of orders to my shop: https://github.com/you/shop",
  "A landing page for my bakery with a WhatsApp order button",
];

const CHANGE_EXAMPLES = [
  "Add an optional tip at checkout",
  "Change the button colours to match my logo",
  "Let customers see their past orders",
];

/** Start a run by talking to the CTO: he asks what he needs, then hands over a brief. With
 * `about`, it is a change to that live project. */
export function IntakeChat({ about }: { about?: About }) {
  return (
    <ChatIntake<Brief>
      agent={{ name: "Kabir", initial: "K" }}
      title={about ? "What should change?" : "New run"}
      subtitle="Tell Kabir, your CTO, what you need. He'll ask anything that's unclear."
      greeting={
        about
          ? "Hi! What would you like to change? A sentence is fine. I'll tell you if it's a quick fix or worth a plan first."
          : "Hi! What would you like the team to build? A sentence is fine, or paste a full spec. If it's a change to an existing project, include the GitHub link."
      }
      examples={about ? CHANGE_EXAMPLES : EXAMPLES}
      placeholder="Describe what you want built…"
      skipLabel="Skip the questions, start now"
      ask={async (turns) => {
        const result = await intakeAction(turns, about);
        return "error" in result ? result : { text: result.reply.text, brief: result.reply.brief };
      }}
      start={(brief) => askForPlanAction(briefBody(brief))}
      skip={(request) =>
        startFromBriefAction({
          request,
          summary: "",
          repo_url: about?.repo_url ?? null,
          branch: null,
          create_repo: !about,
          new_repo_name: null,
          stack: {},
          test_command: null,
        })
      }
      renderBrief={(brief, c) => (
        <BriefCard
          brief={brief}
          pending={c.pending}
          onPlan={c.start}
          onBuildNow={() => void startFromBriefAction(brief)}
          onKeepTalking={c.keepTalking}
        />
      )}
    />
  );
}
