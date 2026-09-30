"""Release gate: pauses the run until the founder approves or rejects.

`interrupt()` saves the run in its checkpoint and stops. The run resumes — possibly in a
different worker process, hours later — when it is invoked again with `Command(resume=...)`.
"""

from typing import Any

from langgraph.types import interrupt

from app.features.workflows.state import BuildState


async def approval(state: BuildState) -> dict[str, Any]:
    dev = state.get("dev_result", {})
    decision = interrupt(
        {
            "gate": "release",
            "question": "Approve this build for release?",
            "summary": dev.get("summary", ""),
            "files_changed": dev.get("files_changed", []),
            "tests": state.get("verify_output", ""),
        }
    )
    if isinstance(decision, dict):
        return {
            "approved": bool(decision.get("approved")),
            "feedback": str(decision.get("feedback", "")),
        }
    return {"approved": bool(decision)}
