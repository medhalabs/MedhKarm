from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

TaskKind = Literal["new", "feature", "bug", "refactor"]


class EvalTask(BaseModel):
    """One eval task, loaded from `evals/tasks/<id>/task.toml`."""

    id: str
    title: str
    kind: TaskKind
    difficulty: int = Field(ge=1, le=3)
    language: str
    request: str
    test_command: str  # visible: the team runs it while working
    check_command: str  # hidden: run by us afterwards, with the files from checks/
    repo: str | None = None  # starting project in evals/repos/, or None for a new module
    solution_delete: list[str] = Field(default_factory=list)  # files the solution removes
    task_dir: Path
    repo_dir: Path | None = None


class TaskOutcome(BaseModel):
    task_id: str
    kind: TaskKind
    difficulty: int
    language: str
    passed: bool
    visible_passed: bool = False
    hidden_passed: bool = False
    steps: int = 0
    total_tokens: int = 0  # every agent's tokens in the task (CTO, developers, QA)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model_calls: int = 0
    seconds: float = 0.0
    summary: str = ""
    files_changed: list[str] = Field(default_factory=list)
    hidden_output: str = ""
    error: str | None = None
    errored: bool = False  # model or sandbox failure, not the team's fault: rerun, don't score


class EvalReport(BaseModel):
    started_at: str
    engine: str
    model: str
    outcomes: list[TaskOutcome]
    variant: str = ""  # what this run tries, e.g. "code-graph" (in the file name and summary)

    @property
    def passed(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.passed)

    @property
    def scored(self) -> list[TaskOutcome]:
        """Tasks that actually ran. Errored tasks say nothing about the team's quality."""
        return [outcome for outcome in self.outcomes if not outcome.errored]

    @property
    def errored(self) -> list[TaskOutcome]:
        return [outcome for outcome in self.outcomes if outcome.errored]


class ValidationOutcome(BaseModel):
    """Whether a task is fair (solvable) and not already solved."""

    task_id: str
    fixture_fails_checks: bool  # the starting project must NOT already pass the hidden checks
    solution_passes: bool  # the reference solution must pass visible tests and hidden checks
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.fixture_fails_checks and self.solution_passes
