"""QA's browser test (Tara): for runs that changed a web page, QA writes one end-to-end test
with Playwright (a real headless browser), and we run it ourselves. A failure goes back to the
frontend developer once ("fix the app, not the test"); if it still fails, the release stops
without asking the founder. Runs without web UI changes pass straight through."""

import shlex
from pathlib import PurePosixPath
from typing import Any

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.developer_engine.schemas import DevTask
from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

E2E_DIR = "tests/e2e"
E2E_COMMAND = f"python -m pytest {E2E_DIR} -q -p no:cacheprovider"
WEB_SUFFIXES = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte"}
WEB_FOLDERS = {"templates", "static", "public", "pages", "components"}
APP_BUG = "APP BUG:"
FIX_TITLE = "Make the browser test pass"

QA_BRIEF = """The developers built this:

{request}

Files they changed: {files}

Write ONE end-to-end browser test for it in {e2e_dir}/test_<short_name>.py with
pytest-playwright (use its `page` fixture). In the test, start the app the way it really
runs (for example `python -m uvicorn app:app --port <a free port>` with subprocess,
`python -m http.server` for plain pages, or for Next.js `npm run build` once and then
`npx next start -p <a free port>`), wait until it answers, then use the page like a
person: open it, fill in forms, click, and check what appears. Cover the main journey the
request describes. Stop the server at the end.
Run `{command}`. Fix the TEST until it reflects the request. If the app itself is broken,
stop and call finish with a summary that starts with "{app_bug}" and says what's wrong."""


def needs_browser_test(changed: list[str]) -> bool:
    """Did the run change something a user sees in a browser?"""
    for path in changed:
        parts = PurePosixPath(path)
        if parts.suffix.lower() in WEB_SUFFIXES or WEB_FOLDERS & set(parts.parts[:-1]):
            return True
    return False


def make_browser_qa_node(
    sandboxes: SandboxProvider,
    tester: DeveloperEngine | None,
    events: EventStore | None = None,
    qa_name: str = "QA",
    fixer: str = "Developer",
    max_fix_rounds: int = 1,
) -> BuildNode:
    """`tester` is QA's engine (QA role: instructions, tools); None = no browser tests.
    `fixer` is who gets the fix task (the frontend developer)."""

    async def browser_qa(state: BuildState) -> dict[str, Any]:
        changed = list(state.get("dev_result", {}).get("files_changed", []))
        previous = state.get("browser", {})
        if tester is None or not (previous.get("needed") or needs_browser_test(changed)):
            return {"browser": {"needed": False}, "browser_passed": True}
        sandbox = await sandboxes.attach(state["sandbox_id"])
        recorder = RunRecorder(events, state.get("run_id", "unknown")).with_context(member=qa_name)
        qa_summary = previous.get("qa_summary", "")
        tests = previous.get("test_files", [])
        if not tests:  # QA writes the test once; a fix round re-runs the same test
            await recorder.record(
                Actor.QA, EventType.WORK_STARTED, f"{qa_name} started: a browser test"
            )
            result = await tester.run_task(
                DevTask(
                    description=QA_BRIEF.format(
                        request=state["request"],
                        files=", ".join(changed) or "none",
                        e2e_dir=E2E_DIR,
                        command=E2E_COMMAND,
                        app_bug=APP_BUG,
                    ),
                    test_command=E2E_COMMAND,
                ),
                sandbox,
                recorder,
            )
            qa_summary = result.summary
            tests = [f for f in result.files_changed if f.startswith(f"{E2E_DIR}/")]
        run = await sandbox.run(E2E_COMMAND + " " + " ".join(shlex.quote(t) for t in tests))
        app_bug = qa_summary.strip().upper().startswith(APP_BUG)
        passed = bool(tests) and run.ok and not app_bug
        output = run.output[-2000:] if tests else "QA didn't write a browser test."
        rounds = state.get("browser_rounds", 0)
        update: dict[str, Any] = {
            "browser": {
                "needed": True,
                "passed": passed,
                "test_files": tests,
                "qa_summary": qa_summary,
                "output": output,
                "round": rounds,
            },
            "browser_passed": passed,
        }
        if not passed and tests and rounds < max_fix_rounds:
            tasks = [dict(t) for t in state.get("tasks", [])]
            tasks.append(_fix_task(fixer, tests, qa_summary if app_bug else "", output, rounds))
            update |= {
                "tasks": tasks,
                "current_task": len(tasks) - 1,
                "browser_rounds": rounds + 1,
            }
        return update

    return browser_qa


def after_browser_qa(state: BuildState) -> str:
    if state.get("current_task", 0) < len(state.get("tasks", [])):
        return "develop"
    return "security" if state.get("browser_passed", True) else "finish"


def _fix_task(owner: str, tests: list[str], bug: str, output: str, round_: int) -> dict[str, Any]:
    found = bug or "The browser test fails:\n" + output[-1200:]
    return {
        "id": f"ui{round_ + 1}",
        "title": FIX_TITLE,
        "description": (
            f"QA's browser test ({', '.join(tests)}) uses the app like a person would. "
            f"{found}\nFix the app so the test passes. Change the test only if it gets the "
            "request wrong, and never weaken what it checks. Run it with "
            f"`{E2E_COMMAND}`."
        ),
        "owner": owner,
        "specialty": "frontend",
        "status": "todo",
        "attempts": 0,
        "feedback": "",
        "summary": "",
        "files_changed": [],
        "success": False,
    }
