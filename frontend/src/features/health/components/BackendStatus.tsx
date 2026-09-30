import { getHealth } from "../api/getHealth";
import { describeHealth } from "../describeHealth";

/** Server component: shows whether the backend API is reachable. */
export async function BackendStatus() {
  const health = await getHealth().catch(() => null);
  const { label, healthy } = describeHealth(health);

  return (
    <p className="flex items-center gap-2 text-sm">
      <span className={`h-2 w-2 rounded-full ${healthy ? "bg-green-500" : "bg-red-500"}`} />
      {label}
    </p>
  );
}
