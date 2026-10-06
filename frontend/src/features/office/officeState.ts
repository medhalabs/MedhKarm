import type { ActivityEvent } from "@/features/events/client";

import type { AgentState, Doing, Member, OfficeState, Place } from "./types";

const BUBBLE_MAX = 70;

function short(text: string): string {
  const line = text.trim().split("\n")[0] ?? "";
  return line.length <= BUBBLE_MAX ? line : `${line.slice(0, BUBBLE_MAX - 1).trimEnd()}…`;
}

const desk = (of: string): Place => ({ kind: "desk", of });

export function initialOffice(team: Member[]): OfficeState {
  const agents: Record<string, AgentState> = {};
  for (const member of team) {
    agents[member.name] = {
      member,
      place: desk(member.name),
      doing: "idle",
      bubble: null,
      bubbleId: 0,
    };
  }
  return { agents, founderWaiting: false, finished: null, lastEventId: 0 };
}

/** The office after `events`, in order. Every move comes from a real event. */
export function officeState(team: Member[], events: ActivityEvent[]): OfficeState {
  return events.reduce((state, event) => applyEvent(state, event), initialOffice(team));
}

export function applyEvent(state: OfficeState, event: ActivityEvent): OfficeState {
  const next: OfficeState = {
    ...state,
    agents: { ...state.agents },
    lastEventId: event.id,
  };
  const byRole = (role: string): string | undefined =>
    Object.values(next.agents).find((a) => a.member.role === role)?.member.name;
  const member = typeof event.data.member === "string" ? event.data.member : undefined;
  const actor = (member && next.agents[member] ? member : undefined) ?? byRole(event.actor);
  const cto = byRole("cto");

  const set = (name: string | undefined, change: Partial<Omit<AgentState, "member">>) => {
    if (!name || !next.agents[name]) return;
    next.agents[name] = { ...next.agents[name], ...change };
  };
  const say = (name: string | undefined, text: string, doing: Doing, place?: Place) =>
    set(name, { bubble: short(text), bubbleId: event.id, doing, ...(place ? { place } : {}) });
  const home = (name: string | undefined) => name && set(name, { place: desk(name) });
  const target = typeof event.data.member === "string" ? event.data.member : undefined;

  switch (event.type) {
    case "run.started":
      next.finished = null;
      say(cto, event.summary.replace(/^Asked for: /, "New request: "), "thinking", desk(cto ?? ""));
      break;
    case "codebase.mapped":
      say(cto, "Reading the project", "thinking");
      break;
    case "project.scaffolded":
      say(byRole("devops"), event.summary, "working");
      break;
    case "plan.created": {
      const tasks = Array.isArray(event.data.tasks) ? event.data.tasks : [];
      const owners = new Set(
        tasks
          .map((t) => (t as { owner?: unknown }).owner)
          .filter((o): o is string => typeof o === "string"),
      );
      say(cto, event.summary, "talking", { kind: "meeting" });
      for (const owner of owners) set(owner, { place: { kind: "meeting" }, doing: "talking" });
      break;
    }
    case "task.assigned": {
      // The CTO, QA or the security engineer walks over to whoever gets the task
      const from = byRole(event.actor) ?? cto;
      say(from, event.summary, "talking", target ? desk(target) : undefined);
      if (target) set(target, { place: desk(target) });
      break;
    }
    case "work.started":
      home(cto);
      for (const a of Object.values(next.agents))
        if (a.place.kind === "meeting") home(a.member.name);
      say(actor, event.summary.replace(/^[^:]+ started: /, ""), "working", desk(actor ?? ""));
      break;
    case "model.used":
      set(actor, { doing: "thinking" });
      break;
    case "tool.used":
      say(actor, event.summary, /test/i.test(event.summary) ? "testing" : "working");
      break;
    case "work.finished":
      say(actor, event.summary.replace(/^[^:]+: /, ""), "idle");
      break;
    case "review.finished":
      say(cto, event.summary, "reviewing", target ? desk(target) : undefined);
      break;
    case "check.finished":
      say(byRole("qa"), event.summary, "testing", desk(byRole("qa") ?? ""));
      break;
    case "security.finished":
      say(byRole("security"), event.summary, "testing", desk(byRole("security") ?? ""));
      break;
    case "deploy.finished":
    case "changes.delivered":
      say(byRole("devops"), event.summary, "working");
      break;
    case "demo.recorded":
      say(byRole("qa"), "Recorded a demo of the app", "testing", desk(byRole("qa") ?? ""));
      break;
    case "docs.updated":
      say(byRole("docs"), event.summary.replace(/^[^:]+: /, ""), "working");
      break;
    case "approval.requested":
      next.founderWaiting = true;
      say(cto, "Waiting for your approval", "waiting", { kind: "door" });
      break;
    case "approval.decided":
      next.founderWaiting = false;
      say(cto, event.summary, "talking", desk(cto ?? ""));
      break;
    case "message.posted":
      if (event.actor !== "founder") say(actor, event.summary.replace(/^[^:]+: /, ""), "talking");
      break;
    case "run.finished":
      next.finished = typeof event.data.status === "string" ? event.data.status : "finished";
      next.founderWaiting = false;
      for (const a of Object.values(next.agents)) {
        set(a.member.name, { place: desk(a.member.name), doing: "idle" });
      }
      say(cto, event.summary, "idle");
      break;
    default:
      break;
  }
  return next;
}
