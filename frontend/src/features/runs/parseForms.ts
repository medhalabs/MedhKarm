/** Reads and checks the admin forms before anything is sent to the backend. */

export type StartRunInput = { request: string; test_command: string };
export type DecisionInput = { approved: boolean; feedback: string };

export function parseStartRun(form: FormData): StartRunInput | { error: string } {
  const request = String(form.get("request") ?? "").trim();
  const testCommand = String(form.get("test_command") ?? "").trim() || "pytest -q";
  if (request.length < 3) return { error: "Say what the team should build." };
  if (request.length > 5000) return { error: "Keep the request under 5,000 characters." };
  if (testCommand.length > 500) return { error: "Keep the test command under 500 characters." };
  return { request, test_command: testCommand };
}

export function parseDecision(form: FormData): DecisionInput | { error: string } {
  const decision = form.get("decision");
  if (decision !== "approve" && decision !== "reject")
    return { error: "Choose approve or reject." };
  const feedback = String(form.get("feedback") ?? "").trim();
  if (feedback.length > 2000) return { error: "Keep the note under 2,000 characters." };
  return { approved: decision === "approve", feedback };
}
