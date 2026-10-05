import type { Member, OfficeState } from "../types";
import { DOOR, FLOOR, MEETING, desks, positions } from "../layout";
import { roleColor } from "../colors";
import { Character } from "./Character";

/** The office, drawn from its state: desks, meeting room, the founder's door, characters. */
export function OfficeFloor({ team, state }: { team: Member[]; state: OfficeState }) {
  const deskOf = desks(team);
  const agents = team.map((m) => state.agents[m.name]).filter(Boolean);
  const at = positions(agents, deskOf);
  return (
    <svg
      viewBox={`0 0 ${FLOOR.width} ${FLOOR.height}`}
      className="h-auto w-full rounded-xl border border-zinc-200 bg-stone-50 dark:border-zinc-800 dark:bg-zinc-950"
      role="img"
      aria-label="The team's office"
    >
      {team.map((m) => {
        const d = deskOf[m.name];
        return (
          <g key={m.name}>
            <rect
              x={d.x - 44}
              y={d.y - 22}
              width={88}
              height={30}
              rx={6}
              className="fill-amber-100 stroke-amber-300 dark:fill-zinc-800 dark:stroke-zinc-700"
            />
            <rect
              x={d.x - 14}
              y={d.y - 18}
              width={28}
              height={16}
              rx={2}
              fill={roleColor(m.role)}
              opacity={0.25}
            />
            <text x={d.x} y={d.y - 30} textAnchor="middle" fontSize={10} className="fill-zinc-500">
              {m.title}
            </text>
          </g>
        );
      })}
      <rect
        {...MEETING}
        rx={12}
        className="fill-sky-50 stroke-sky-200 dark:fill-sky-950/40 dark:stroke-sky-900"
      />
      <text
        x={MEETING.x + 14}
        y={MEETING.y + 22}
        fontSize={12}
        fontWeight={600}
        className="fill-sky-800 dark:fill-sky-300"
      >
        Meeting room
      </text>
      <ellipse
        cx={MEETING.x + 125}
        cy={MEETING.y + 130}
        rx={60}
        ry={42}
        className="fill-amber-100 stroke-amber-300 dark:fill-zinc-800 dark:stroke-zinc-700"
      />
      <rect
        {...DOOR}
        rx={12}
        className={
          state.founderWaiting
            ? "fill-amber-50 stroke-amber-400 dark:fill-amber-950/40 dark:stroke-amber-600"
            : "fill-zinc-100 stroke-zinc-200 dark:fill-zinc-900 dark:stroke-zinc-800"
        }
        strokeWidth={state.founderWaiting ? 2 : 1}
      />
      <text
        x={DOOR.x + 14}
        y={DOOR.y + 22}
        fontSize={12}
        fontWeight={600}
        className="fill-zinc-700 dark:fill-zinc-300"
      >
        Your office
      </text>
      <text x={DOOR.x + 14} y={DOOR.y + 40} fontSize={11} className="fill-zinc-500">
        {state.founderWaiting
          ? "A release is waiting for you"
          : state.finished
            ? `Run ${state.finished}`
            : "Inbox is clear"}
      </text>
      <rect
        x={DOOR.x + 150}
        y={DOOR.y + 90}
        width={70}
        height={100}
        rx={4}
        className="fill-amber-200 stroke-amber-400 dark:fill-amber-900 dark:stroke-amber-700"
      />
      <circle cx={DOOR.x + 208} cy={DOOR.y + 140} r={3} className="fill-amber-600" />
      {agents.map((agent) => (
        <Character key={agent.member.name} agent={agent} at={at[agent.member.name]} />
      ))}
    </svg>
  );
}
