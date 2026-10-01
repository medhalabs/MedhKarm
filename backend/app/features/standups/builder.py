"""Builds a standup from runs' events. Pure: no database, no model, no clock.

Each run's full history up to the end of the window is replayed to find where every task and
the run itself stand; only what happened *inside* the window counts as done or sent back.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app.features.events.schemas import Event, EventType
from app.features.standups.schemas import (
    ProjectStatus,
    ProjectSummary,
    Standup,
    StandupItem,
)

NAME_LENGTH = 50
FINISHED = {
    "released": ProjectStatus.RELEASED,
    "rejected": ProjectStatus.REJECTED,
    "error": ProjectStatus.ERROR,
}


@dataclass
class _Task:
    title: str
    owner: str
    state: str = (
        "to do"  # to do | working | in review | changes requested | done | done_with_issues
    )
    attempts: int = 0


@dataclass
class _Report:
    done: list[StandupItem] = field(default_factory=list)
    planned: list[StandupItem] = field(default_factory=list)
    blocked: list[StandupItem] = field(default_factory=list)
    needs_you: list[StandupItem] = field(default_factory=list)
    sent_back: int = 0
    tasks_done: int = 0


def build_standup(
    histories: dict[str, list[Event]],
    day: date,
    timezone: str,
    since: datetime,
    until: datetime,
    stall_after: timedelta,
) -> Standup:
    report = _Report()
    projects = [
        _replay(run_id, events, since, until, stall_after, report)
        for run_id, events in histories.items()
        if events
    ]
    return Standup(
        day=day,
        timezone=timezone,
        since=since,
        until=until,
        headline=_headline(report, projects),
        done=report.done,
        planned=report.planned,
        blocked=report.blocked,
        needs_you=report.needs_you,
        projects=projects,
        sent_back=report.sent_back,
        tokens=sum(p.tokens for p in projects),
    )


def _replay(
    run_id: str,
    events: list[Event],
    since: datetime,
    until: datetime,
    stall_after: timedelta,
    report: _Report,
) -> ProjectSummary:
    project = _project_name(run_id, events)
    tasks: dict[str, _Task] = {}
    tokens = 0

    def item(text: str, event: Event, member: str | None = None) -> StandupItem:
        return StandupItem(
            run_id=run_id, project=project, text=text, member=member, at=event.occurred_at
        )

    for event in events:
        in_window = since <= event.occurred_at < until
        data = event.data
        task = tasks.get(str(data.get("task_id", "")))
        if in_window:
            tokens += event.tokens

        if event.type == EventType.TASK_ASSIGNED:
            tasks[data["task_id"]] = _Task(title=data["title"], owner=data["member"])
        elif event.type == EventType.WORK_STARTED and task:
            task.state = "working"
        elif event.type == EventType.WORK_FINISHED and task:
            task.state, task.attempts = "in review", task.attempts + 1
        elif event.type == EventType.REVIEW_FINISHED and task:
            if data.get("decision") != "approve":
                task.state = "changes requested"
                report.sent_back += in_window
            elif data.get("accepted_with_issues"):
                task.state = "done_with_issues"
                if in_window:
                    report.blocked.append(
                        item(
                            f"“{task.title}” was accepted with review comments still "
                            f"open: {str(data.get('feedback', ''))[:200]}",
                            event,
                            task.owner,
                        )
                    )
            else:
                task.state = "done"
                if in_window:
                    report.tasks_done += 1
                    report.done.append(
                        item(f"{task.owner} finished “{task.title}”", event, task.owner)
                    )
        elif event.type == EventType.RUN_FINISHED and in_window:
            status = str(data.get("status", ""))
            if status == "released":
                report.done.append(item("Released", event))
            elif status == "rejected":
                report.done.append(item("Stopped at your request", event))
            elif status == "error":
                report.blocked.append(item("Stopped: something went wrong", event))
            else:
                report.blocked.append(item("Stopped: the final checks did not pass", event))

    status = _status(events[-1], until, stall_after)
    last = events[-1]
    if status == ProjectStatus.WAITING_FOR_APPROVAL:
        gate = last.data.get("gate", {})
        why = " ".join(gate.get("reasons", [])) if gate.get("rules") else ""
        report.needs_you.append(item("Approve the release" + (f": {why}" if why else ""), last))
    elif status == ProjectStatus.STALLED:
        report.blocked.append(item("No activity for a while: check the worker", last))
    if status in (ProjectStatus.IN_PROGRESS, ProjectStatus.STALLED):
        for open_task in tasks.values():
            if not open_task.state.startswith("done"):
                report.planned.append(
                    StandupItem(
                        run_id=run_id,
                        project=project,
                        text=f"{open_task.owner}: “{open_task.title}” ({open_task.state})",
                        member=open_task.owner,
                    )
                )

    return ProjectSummary(
        run_id=run_id,
        project=project,
        status=status,
        tasks_done=sum(t.state.startswith("done") for t in tasks.values()),
        tasks_total=len(tasks),
        tokens=tokens,
    )


def _status(last: Event, until: datetime, stall_after: timedelta) -> ProjectStatus:
    if last.type == EventType.RUN_FINISHED:
        return FINISHED.get(str(last.data.get("status")), ProjectStatus.FAILED)
    if last.type == EventType.APPROVAL_REQUESTED:
        return ProjectStatus.WAITING_FOR_APPROVAL
    if until - last.occurred_at > stall_after:
        return ProjectStatus.STALLED
    return ProjectStatus.IN_PROGRESS


def _project_name(run_id: str, events: list[Event]) -> str:
    """A short name from the founder's request: its first clause, at most ~50 characters."""
    started = next((e for e in events if e.type == EventType.RUN_STARTED), None)
    request = " ".join(str(started.data.get("request", "")).split()) if started else ""
    name = re.split(r":|\. |\(\d\)", request, maxsplit=1)[0].strip(" ,;")
    if not name:
        return run_id
    if len(name) <= NAME_LENGTH:
        return name
    return name[:NAME_LENGTH].rsplit(" ", 1)[0].rstrip(" ,;") + "\u2026"


def _headline(report: _Report, projects: list[ProjectSummary]) -> str:
    if not projects:
        return "A quiet day: no work in progress."
    done = report.tasks_done
    parts = [f"{done} task{'s' if done != 1 else ''} done"]
    if report.needs_you:
        parts.append(f"{len(report.needs_you)} waiting for your approval")
    parts.append(f"{len(report.blocked)} blocked" if report.blocked else "nothing blocked")
    return ", ".join(parts) + "."
