"""QA's browser test (Tara): for runs that changed a web page, QA writes one end-to-end test
with Playwright (a real headless browser), and we run it ourselves. A failure goes back to the
frontend developer once ("fix the app, not the test"); if it still fails, the release stops
without asking the founder. Runs without web UI changes pass straight through."""

import base64
import logging
import shlex
from pathlib import PurePosixPath
from typing import Any

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.developer_engine.schemas import DevTask
from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.sandbox.interfaces import Sandbox, SandboxProvider
from app.features.workflows.interfaces import ArtifactSink
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

logger = logging.getLogger(__name__)
E2E_DIR = "tests/e2e"
VIDEO_DIR = "/tmp/medhkarm-demo"  # outside the project, so the video isn't committed
MAX_VIDEO_BYTES = 6 * 1024 * 1024
SLOWMO_MS = 300  # a pause after each browser action, so a person can follow the video
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
    artifacts: ArtifactSink | None = None,
) -> BuildNode:
    """`tester` is QA's engine (QA role: instructions, tools); None = no browser tests.
    `fixer` is who gets the fix task (the frontend developer). `artifacts`: where the demo video
    of a passing test is kept (None: not recorded)."""

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
        rounds = state.get("browser_rounds", 0)
        video_dir = f"{VIDEO_DIR}-{rounds}"
        flags = (
            f" --video on --slowmo {SLOWMO_MS} --output {shlex.quote(video_dir)}"
            if artifacts
            else ""
        )
        run = await sandbox.run(E2E_COMMAND + flags + " " + " ".join(shlex.quote(t) for t in tests))
        app_bug = qa_summary.strip().upper().startswith(APP_BUG)
        passed = bool(tests) and run.ok and not app_bug
        output = run.output[-2000:] if tests else "QA didn't write a browser test."
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
        if passed and artifacts is not None:
            demo = await _keep_demo(sandbox, artifacts, state.get("run_id", ""), video_dir)
            if demo:
                update["browser"]["demo"] = demo
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


async def _keep_demo(
    sandbox: Sandbox, artifacts: ArtifactSink, run_id: str, video_dir: str
) -> dict[str, Any] | None:
    """The recording of the passing test, kept for the founder. Never fails the run: a missing
    or oversized video just means there's no demo."""
    try:
        found = await sandbox.run(
            f"find {shlex.quote(video_dir)} -name '*.webm' -printf '%s %p\\n' | sort -rn | head -1"
        )
        size_text, _, path = found.output.strip().partition(" ")
        size = int(size_text) if size_text.isdigit() else 0
        if not found.ok or not path or not 0 < size <= MAX_VIDEO_BYTES:
            return None
        encoded = await sandbox.run(f"base64 -w0 {shlex.quote(path)}")
        if not encoded.ok:
            return None
        data = base64.b64decode(encoded.output.strip(), validate=True)
        saved = await artifacts.save(run_id, "demo", "browser-test.webm", "video/webm", data)
    except Exception as error:  # a demo is a bonus: whatever goes wrong, the run carries on
        logger.warning("Couldn't keep the demo video for %s: %s", run_id, error)
        return None
    return {"artifact_id": saved.id, "bytes": len(data)}
