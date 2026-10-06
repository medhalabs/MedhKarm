"""Priya's project report: how far a project has got, what it has cost in model tokens, and
whether it is moving. Pure: no I/O, so it is the same answer in the API and in a test."""

from datetime import datetime

from pydantic import BaseModel

from app.features.projects.schemas import BacklogItem, ItemStatus, Project, ProjectStatus

QUIET_DAYS = 3  # no activity for this long and work waiting: "stalled"


class ProjectHealth(BaseModel):
    project_id: str
    name: str
    items_total: int  # without skipped ones
    done: int
    in_progress: int  # running, waiting at the gate, or waiting to be merged
    blocked: int
    waiting: int  # in the backlog, not started
    runs: int
    tokens: int  # all the project's runs
    days_since_activity: int | None  # None: nothing has run yet
    state: str  # "not_started" | "moving" | "needs_you" | "stalled" | "done"
    summary: str  # Priya's sentence for the founder


def project_health(
    project: Project,
    items: list[BacklogItem],
    tokens_by_run: dict[str, int],
    last_activity: datetime | None,
    now: datetime,
) -> ProjectHealth:
    counted = [i for i in items if i.status != ItemStatus.SKIPPED]
    done = sum(i.status == ItemStatus.DONE for i in counted)
    busy = sum(i.status in (ItemStatus.IN_PROGRESS, ItemStatus.WAITING_FOR_MERGE) for i in counted)
    blocked = sum(i.status == ItemStatus.BLOCKED for i in counted)
    waiting = len(counted) - done - busy - blocked
    run_ids = {i.run_id for i in items if i.run_id}
    tokens = sum(tokens_by_run.get(run, 0) for run in run_ids)
    quiet = (now - last_activity).days if last_activity else None

    if project.status == ProjectStatus.DONE or (counted and done == len(counted)):
        state = "done"
    elif not run_ids:
        state = "not_started"
    elif blocked or project.status == ProjectStatus.PAUSED or project.questions:
        state = "needs_you"
    elif busy == 0 and waiting and quiet is not None and quiet >= QUIET_DAYS:
        state = "stalled"
    else:
        state = "moving"

    return ProjectHealth(
        project_id=project.id,
        name=project.name,
        items_total=len(counted),
        done=done,
        in_progress=busy,
        blocked=blocked,
        waiting=waiting,
        runs=len(run_ids),
        tokens=tokens,
        days_since_activity=quiet,
        state=state,
        summary=_sentence(state, done, len(counted), blocked, busy, quiet, tokens),
    )


def _sentence(
    state: str, done: int, total: int, blocked: int, busy: int, quiet: int | None, tokens: int
) -> str:
    progress = f"{done} of {total} items done" if total else "No items yet"
    cost = f"{tokens:,} model tokens used so far" if tokens else "nothing spent yet"
    match state:
        case "done":
            return f"All done: {progress}, {cost}."
        case "not_started":
            return f"Not started: {progress}; {cost}."
        case "needs_you":
            why = f"{blocked} blocked" if blocked else "waiting on you for a decision or an answer"
            return f"Needs you: {progress}, {why}; {cost}."
        case "stalled":
            return f"Quiet for {quiet} days with work waiting: {progress}; {cost}."
        case _:
            return f"Moving: {progress}" + (f", {busy} in progress" if busy else "") + f"; {cost}."
