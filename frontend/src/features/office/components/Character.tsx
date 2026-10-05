import type { AgentState } from "../types";
import { roleColor } from "../colors";
import type { Point } from "../layout";

const DOING_LABEL: Record<string, string> = {
  thinking: "thinking",
  working: "working",
  testing: "testing",
  reviewing: "reviewing",
  talking: "talking",
  waiting: "waiting for you",
  idle: "",
};

/** One agent: a simple figure that glides to where the activity log puts them. */
export function Character({ agent, at }: { agent: AgentState; at: Point }) {
  const color = roleColor(agent.member.role);
  const busy = agent.doing !== "idle";
  const doing = DOING_LABEL[agent.doing];
  const label = `${agent.member.name}, ${agent.member.title}${doing ? `: ${doing}` : ""}`;
  return (
    <g
      style={{ transform: `translate(${at.x}px, ${at.y}px)` }}
      className="transition-transform duration-1000 ease-in-out motion-reduce:transition-none"
    >
      <title>{label}</title>
      {busy && (
        <circle
          r={22}
          cy={-6}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeDasharray={agent.doing === "thinking" ? "4 4" : undefined}
          className={
            agent.doing === "thinking"
              ? "origin-center animate-spin [animation-duration:4s] motion-reduce:animate-none"
              : "opacity-60"
          }
          style={{ transformBox: "fill-box" }}
        />
      )}
      <rect x={-12} y={4} width={24} height={20} rx={8} fill={color} opacity={0.85} />
      <circle cy={-6} r={12} fill={color} />
      <text y={-2} textAnchor="middle" fontSize={11} fontWeight={600} fill="#fff">
        {agent.member.name[0]}
      </text>
      <text y={40} textAnchor="middle" fontSize={11} className="fill-zinc-700 dark:fill-zinc-300">
        {agent.member.name}
      </text>
      {agent.bubble && (
        <foreignObject x={-90} y={-78} width={180} height={56} key={agent.bubbleId}>
          <div className="flex h-full items-end justify-center">
            <p className="animate-[fadein_300ms_ease-out] rounded-lg border border-zinc-200 bg-white px-2 py-1 text-[10px] leading-tight text-zinc-800 shadow-sm motion-reduce:animate-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200">
              {agent.bubble}
            </p>
          </div>
        </foreignObject>
      )}
    </g>
  );
}
