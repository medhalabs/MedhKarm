from pathlib import Path

from app.features.evals.report import save, summary_markdown
from app.features.evals.schemas import EvalReport, TaskKind, TaskOutcome


def outcome(task_id: str, passed: bool, kind: TaskKind = "bug") -> TaskOutcome:
    return TaskOutcome(
        task_id=task_id,
        kind=kind,
        difficulty=1,
        language="python",
        passed=passed,
        visible_passed=True,
        hidden_passed=passed,
        total_tokens=1000,
        seconds=10,
    )


def report() -> EvalReport:
    return EvalReport(
        started_at="2026-10-01T00:00:00Z",
        engine="builtin",
        model="m",
        outcomes=[outcome("a", True), outcome("b", False, "feature")],
    )


def test_summary_counts_and_groups() -> None:
    text = summary_markdown(report())

    assert "Passed: **1/2**" in text
    assert "| kind: bug | 1/1 |" in text
    assert "| kind: feature | 0/1 |" in text
    assert "| b | feature | 1 | FAIL |" in text


def test_save_writes_json_and_markdown(tmp_path: Path) -> None:
    path = save(report(), tmp_path)

    assert path.suffix == ".md"
    assert path.with_suffix(".json").exists()


def test_errored_tasks_are_not_scored() -> None:
    errored = outcome("c", False)
    errored.errored = True
    errored.error = "ModelCallError: down"
    rep = report()
    rep.outcomes.append(errored)

    text = summary_markdown(rep)

    assert "Passed: **1/2** of the tasks that ran" in text
    assert "**1 errored**" in text
    assert "--tasks c" in text
    assert "| c | bug | 1 | ERROR |" in text
