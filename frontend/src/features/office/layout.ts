import type { AgentState, Member, Place } from "./types";

/** The floor plan, in SVG units (viewBox 960 × 560). */
export const FLOOR = { width: 960, height: 560 };
export const MEETING = { x: 690, y: 30, width: 250, height: 250 };
export const DOOR = { x: 690, y: 310, width: 250, height: 220 };

const ROWS: Record<string, number> = { pm: 0, cto: 0, developer: 1, qa: 2, security: 2, devops: 2 };
const ROW_Y = [120, 290, 460];
const FIRST_X = 110;
const STEP_X = 200;

export type Point = { x: number; y: number };

/** Each member's desk: leadership on top, developers in the middle, specialists below. */
export function desks(team: Member[]): Record<string, Point> {
  const used = [0, 0, 0];
  const out: Record<string, Point> = {};
  for (const member of team) {
    const row = ROWS[member.role] ?? 2;
    out[member.name] = { x: FIRST_X + STEP_X * used[row], y: ROW_Y[row] };
    used[row] += 1;
  }
  return out;
}

const SEATS: Point[] = [
  { x: 755, y: 105 },
  { x: 875, y: 105 },
  { x: 755, y: 215 },
  { x: 875, y: 215 },
  { x: 815, y: 75 },
  { x: 815, y: 245 },
];

/** Where each character stands: at their chair, beside a colleague's desk, at a meeting seat
 * or at the founder's door. Visitors to the same spot stand side by side. */
export function positions(
  agents: AgentState[],
  deskOf: Record<string, Point>,
): Record<string, Point> {
  const out: Record<string, Point> = {};
  const crowd = new Map<string, number>();
  let seat = 0;
  for (const agent of agents) {
    const name = agent.member.name;
    out[name] = spot(agent.place, name, deskOf, () => SEATS[seat++ % SEATS.length]);
    const key = `${Math.round(out[name].x)}:${Math.round(out[name].y)}`;
    const n = crowd.get(key) ?? 0;
    crowd.set(key, n + 1);
    out[name] = { x: out[name].x + n * 34, y: out[name].y };
  }
  return out;
}

function spot(
  place: Place,
  name: string,
  deskOf: Record<string, Point>,
  nextSeat: () => Point,
): Point {
  if (place.kind === "meeting") return nextSeat();
  if (place.kind === "door") return { x: DOOR.x + 70, y: DOOR.y + 150 };
  const desk = deskOf[place.of] ?? deskOf[name];
  if (!desk) return { x: 40, y: 40 };
  return place.of === name ? { x: desk.x, y: desk.y + 34 } : { x: desk.x + 52, y: desk.y + 30 };
}
