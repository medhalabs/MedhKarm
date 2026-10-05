import { Collapsible } from "@/shared/ui/Collapsible";
import { Markdown } from "@/shared/ui/Markdown";

const LONG = 700; // characters: longer requests start folded

/** What the founder asked for, formatted, folded when it's a long spec. */
export function RequestCard({ request }: { request: string }) {
  return (
    <section className="card">
      <div className="card-header">
        <h2 className="card-title">Request</h2>
        <span className="text-xs text-zinc-500">
          {request.length.toLocaleString("en-IN")} characters
        </span>
      </div>
      <div className="px-5 py-4">
        <Collapsible long={request.length > LONG}>
          <Markdown>{request}</Markdown>
        </Collapsible>
      </div>
    </section>
  );
}
