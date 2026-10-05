// The office: who is where, doing what, worked out from a run's activity log.

export type Member = { role: string; title: string; name: string };

export type Place = { kind: "desk"; of: string } | { kind: "meeting" } | { kind: "door" };

export type Doing =
  "idle" | "thinking" | "working" | "testing" | "reviewing" | "talking" | "waiting";

export type AgentState = {
  member: Member;
  place: Place;
  doing: Doing;
  bubble: string | null; // what they're saying or doing, shortened
  bubbleId: number; // the event behind the bubble (to restart its animation)
};

export type OfficeState = {
  agents: Record<string, AgentState>; // by name
  founderWaiting: boolean; // a release waits for the founder at the door
  finished: string | null; // the run's final status, once it ends
  lastEventId: number;
};

export type Column = "todo" | "working" | "review" | "done";

export type BoardTask = {
  id: string;
  title: string;
  owner: string;
  column: Column;
  rounds: number; // times sent back
};
