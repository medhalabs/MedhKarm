import pytest

from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.repos.schemas import RepoSource
from app.features.runs.exceptions import RunNotFoundError, RunNotWaitingError
from app.features.runs.memory_repository import InMemoryRunRepository
from app.features.runs.schemas import ApprovalDecision, RunStatus, StartRun
from app.features.runs.service import RESUME_JOB, START_JOB, RunService


def service() -> tuple[RunService, InMemoryRunRepository, InMemoryJobQueue]:
    repo, queue = InMemoryRunRepository(), InMemoryJobQueue()
    return RunService(repo, queue, max_attempts=2), repo, queue


async def test_start_records_the_run_and_queues_a_job() -> None:
    runs, _, queue = service()

    run = await runs.start(StartRun(request="Build a calculator"))

    assert (run.status, run.test_command) == (RunStatus.QUEUED, "pytest -q")
    [job] = queue.jobs
    assert (job.kind, job.payload, job.max_attempts) == (START_JOB, {"run_id": run.id}, 2)


async def test_approval_only_when_waiting_and_only_once() -> None:
    runs, repo, queue = service()
    run = await runs.start(StartRun(request="Build a calculator"))

    with pytest.raises(RunNotWaitingError):
        await runs.decide(run.id, ApprovalDecision(approved=True))

    await repo.set_status(run.id, RunStatus.WAITING_FOR_APPROVAL, gate={"question": "Ship?"})
    decided = await runs.decide(run.id, ApprovalDecision(approved=False, feedback="Not yet"))

    assert decided.status == RunStatus.QUEUED
    assert queue.jobs[-1].kind == RESUME_JOB
    assert queue.jobs[-1].payload == {"run_id": run.id, "approved": False, "feedback": "Not yet"}
    with pytest.raises(RunNotWaitingError):  # a double click doesn't queue a second decision
        await runs.decide(run.id, ApprovalDecision(approved=True))


async def test_unknown_run() -> None:
    runs, _, _ = service()

    with pytest.raises(RunNotFoundError):
        await runs.get("nope")


async def test_repo_runs_keep_the_repo_and_detect_their_test_command() -> None:
    runs, _, _ = service()

    run = await runs.start(
        StartRun(request="Add search", repo=RepoSource(url="https://github.com/a/notes"))
    )
    given = await runs.start(
        StartRun(
            request="Add search",
            test_command="npm test",
            repo=RepoSource(url="https://github.com/a/notes"),
        )
    )

    assert run.repo is not None and run.repo.name == "notes"
    assert run.test_command == ""  # detected when the run starts
    assert given.test_command == "npm test"


async def test_workers_record_the_delivery_and_keep_it() -> None:
    runs, _, _ = service()
    run = await runs.start(StartRun(request="Add search"))

    await runs.set_status(run.id, RunStatus.RELEASED, delivery={"pull_request_url": "u"})
    await runs.set_status(run.id, RunStatus.RELEASED)

    assert (await runs.get(run.id)).delivery == {"pull_request_url": "u"}
