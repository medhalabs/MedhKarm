"""Checks a finished run against Gate 1 (docs/03-roadmap.md), from what was recorded.

    uv run python -m app.workers.gate_check <run_id>

Gate 1: a team defined in config finishes a 10-step task, pauses at an approval, survives a
worker restart, logs every step and its cost, and produces a standup.

Everything is read back from the database (events, the run, its jobs, the LangGraph
checkpoint, the standup), so the answer doesn't depend on anyone's say-so. The worker restart
itself is done by hand during the run (see docs/09-gate-1-report.md).
"""

import argparse
import asyncio
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import session_factory
from app.core.logging import configure_logging
from app.features.events.schemas import Actor, Event, EventType
from app.features.events.stores.sql_store import SqlEventStore
from app.features.jobs.models import JobRow
from app.features.runs.repository import SqlRunRepository
from app.features.standups.dependencies import get_standup_service
from app.features.teams.loader import load_templates
from app.workers.wiring import workflow_service

MIN_STEPS = 10


@dataclass
class Check:
    name: str
    passed: bool
    evidence: str


async def check_run(run_id: str) -> list[Check]:
    events = await SqlEventStore(session_factory).list_for_run(run_id, limit=5000)
    run = await SqlRunRepository(session_factory).get(run_id)
    async with workflow_service(get_settings()) as workflows:
        state = (await workflows.get(run_id)).state
    async with session_factory() as session:
        jobs = (
            await session.scalars(
                select(JobRow).where(JobRow.payload["run_id"].astext == run_id).order_by(JobRow.id)
            )
        ).all()
    types = Counter(e.type for e in events)
    return [
        _team_from_config(events),
        _ten_steps(events, state),
        _paused_at_approval(events, run.status if run else None),
        _survived_restart(types, jobs),
        _every_step_logged(events, types, state),
        _cost_logged(events, state),
        await _standup(run_id, events),
    ]


def _team_from_config(events: list[Event]) -> Check:
    template = load_templates()[get_settings().team_template]
    names = {n for role in template.roles if role.active for n in role.display_names}
    members = {str(e.data["member"]) for e in events if e.data.get("member")}
    actors = {e.actor for e in events}
    ok = bool(members) and members <= names and {Actor.CTO, Actor.DEVELOPER, Actor.QA} <= actors
    return Check(
        "A team defined in config",
        ok,
        f"template '{template.id}'; agents seen: CTO, QA, developers {', '.join(sorted(members))}"
        f" (all named in {template.id}.toml)",
    )


def _ten_steps(events: list[Event], state: dict[str, object]) -> Check:
    steps = sum(1 for e in events if e.type == EventType.MODEL_USED and e.actor == Actor.DEVELOPER)
    tools = sum(1 for e in events if e.type == EventType.TOOL_USED)
    tasks = state.get("tasks", [])
    finished = state.get("status") == "released"
    return Check(
        f"Finishes a task of {MIN_STEPS}+ steps",
        finished and steps >= MIN_STEPS,
        f"{steps} developer steps, {tools} tool uses, "
        f"{len(tasks) if isinstance(tasks, list) else 0} tasks; run {state.get('status')}",
    )


def _paused_at_approval(events: list[Event], status: str | None) -> Check:
    asked = next((e for e in events if e.type == EventType.APPROVAL_REQUESTED), None)
    decided = next(
        (e for e in events if e.type == EventType.APPROVAL_DECIDED and e.actor == Actor.FOUNDER),
        None,
    )
    ok = bool(asked and decided and decided.occurred_at > asked.occurred_at)
    waited = (decided.occurred_at - asked.occurred_at) if (asked and decided) else None
    return Check(
        "Pauses at an approval",
        ok,
        f"paused at the release gate, decided by the founder {waited} later; run now {status}"
        if ok
        else "no founder decision after an approval request",
    )


def _survived_restart(types: Counter[EventType], jobs: Sequence[JobRow]) -> Check:
    takeovers = [j for j in jobs if j.attempts > 1]
    ok = (
        types[EventType.RUN_RESUMED] >= 1
        and types[EventType.RUN_STARTED] == 1
        and types[EventType.PLAN_CREATED] == 1
        and bool(takeovers)
    )
    workers = ", ".join(f"{j.kind} took {j.attempts} attempt(s)" for j in jobs)
    return Check(
        "Survives a worker restart",
        ok,
        f"{types[EventType.RUN_RESUMED]} pick-up(s) after an interruption; started once, planned "
        f"once; jobs: {workers}",
    )


def _every_step_logged(
    events: list[Event], types: Counter[EventType], state: dict[str, object]
) -> Check:
    tasks = state.get("tasks", [])
    attempts = sum(int(t.get("attempts", 0)) for t in tasks) if isinstance(tasks, list) else 0
    expected = {
        EventType.RUN_STARTED: 1,
        EventType.PLAN_CREATED: 1,
        EventType.TASK_ASSIGNED: len(tasks) if isinstance(tasks, list) else 0,
        EventType.WORK_FINISHED: attempts,
        EventType.REVIEW_FINISHED: attempts,
        EventType.CHECK_FINISHED: 1,
        EventType.APPROVAL_REQUESTED: 1,
        EventType.APPROVAL_DECIDED: 1,
        EventType.RUN_FINISHED: 1,
    }
    missing = {t.value: (types[t], n) for t, n in expected.items() if types[t] < n}
    return Check(
        "Logs every step",
        not missing,
        f"{len(events)} events; every plan, task attempt ({attempts}), review, check, approval "
        "and finish recorded"
        if not missing
        else f"missing (seen, expected): {missing}",
    )


def _cost_logged(events: list[Event], state: dict[str, object]) -> Check:
    model_calls = [e for e in events if e.type == EventType.MODEL_USED]
    logged = sum(e.tokens for e in events)
    dev = state.get("dev_result", {})
    kept = int(dev.get("total_tokens", 0) if isinstance(dev, dict) else 0)
    kept += int(state.get("cto_tokens_total", 0) or 0)  # type: ignore[call-overload]
    ok = bool(model_calls) and all(e.tokens > 0 for e in model_calls) and logged >= kept
    return Check(
        "Logs every step's cost",
        ok,
        f"{len(model_calls)} model calls, each with its tokens; {logged:,} tokens logged "
        f"(the run's own totals: {kept:,})"
        + (
            f"; the {logged - kept:,} extra is work a restart interrupted: paid for, logged, redone"
            if logged > kept
            else ""
        ),
    )


async def _standup(run_id: str, events: list[Event]) -> Check:
    settings = get_settings()
    finished = events[-1].occurred_at.astimezone(ZoneInfo(settings.standup_timezone))
    # A day's standup covers the 24 hours before its 09:00: work after 09:00 is the next day's.
    day = finished.date() + timedelta(days=1 if finished.hour >= settings.standup_hour else 0)
    standup = await get_standup_service().for_day(day)
    project = next((p for p in standup.projects if p.run_id == run_id), None)
    done = [i.text for i in standup.done if i.run_id == run_id]
    ok = project is not None and "Released" in done
    return Check(
        "Produces a standup",
        ok,
        f"standup for {day}: '{project.project}' {project.status}, {project.tasks_done}/"
        f"{project.tasks_total} tasks done; Done lists: {'; '.join(done)}"
        if project
        else f"run not in the standup for {day}",
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Check a run against Gate 1.")
    parser.add_argument("run_id")
    args = parser.parse_args()
    configure_logging("WARNING")
    checks = await check_run(args.run_id)
    for check in checks:
        print(f"{'PASS' if check.passed else 'FAIL'}  {check.name}\n      {check.evidence}")
    passed = sum(c.passed for c in checks)
    print(
        f"\nGate 1: {passed}/{len(checks)} checks passed"
        + (" — PASSED" if passed == len(checks) else "")
    )


if __name__ == "__main__":
    asyncio.run(main())
