"""Turns eval outcomes into a Markdown summary and a JSON file."""

import statistics
from collections import defaultdict
from pathlib import Path

from app.features.evals.schemas import EvalReport, TaskOutcome, ValidationOutcome


def summary_markdown(report: EvalReport) -> str:
    outcomes = report.outcomes
    scored = report.scored
    lines = [
        f"# Eval run {report.started_at}",
        "",
        f"Engine: **{report.engine}** · Model: **{report.model}** · "
        f"Passed: **{report.passed}/{len(scored)}** of the tasks that ran",
    ]
    if report.errored:
        ids = ",".join(o.task_id for o in report.errored)
        lines += [
            "",
            f"**{len(report.errored)} errored** (model or sandbox failure, not scored). Rerun with:",
            f"`uv run python -m app.workers.run_evals run --tasks {ids}`",
        ]
    lines += ["", "| Group (scored tasks) | Passed |", "| --- | --- |"]
    for label, group in _groups(scored).items():
        lines.append(f"| {label} | {sum(o.passed for o in group)}/{len(group)} |")

    tokens = [o.total_tokens for o in scored if o.total_tokens]
    seconds = [o.seconds for o in scored]
    lines += [
        "",
        f"Tokens: total {sum(tokens):,}, median per task "
        f"{int(statistics.median(tokens)) if tokens else 0:,}. "
        f"Time: median {statistics.median(seconds) if seconds else 0:.0f}s per task.",
        "",
        "| Task | Kind | Diff. | Result | Visible | Hidden | Steps | Tokens | Time | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for o in sorted(outcomes, key=lambda o: o.task_id):
        note = (o.error or o.summary).replace("|", "/").replace("\n", " ")[:80]
        lines.append(
            f"| {o.task_id} | {o.kind} | {o.difficulty} | {_result(o)} | "
            f"{_mark(o.visible_passed)} | {_mark(o.hidden_passed)} | {o.steps} | "
            f"{o.total_tokens:,} | {o.seconds:.0f}s | {note} |"
        )
    return "\n".join(lines) + "\n"


def validation_markdown(results: list[ValidationOutcome]) -> str:
    ok = sum(r.ok for r in results)
    lines = [f"Validated {ok}/{len(results)} tasks", ""]
    for r in sorted(results, key=lambda r: r.task_id):
        lines.append(
            f"{'OK  ' if r.ok else 'FAIL'} {r.task_id}" + (f"  {r.detail}" if r.detail else "")
        )
    return "\n".join(lines) + "\n"


def save(report: EvalReport, results_dir: Path) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{report.started_at.replace(':', '')}-{report.engine}"
    (results_dir / f"{stem}.json").write_text(report.model_dump_json(indent=2))
    path = results_dir / f"{stem}.md"
    path.write_text(summary_markdown(report))
    return path


def _groups(outcomes: list[TaskOutcome]) -> dict[str, list[TaskOutcome]]:
    groups: dict[str, list[TaskOutcome]] = defaultdict(list)
    for o in outcomes:
        groups[f"kind: {o.kind}"].append(o)
        groups[f"language: {o.language}"].append(o)
        groups[f"difficulty: {o.difficulty}"].append(o)
    return dict(sorted(groups.items()))


def _result(outcome: TaskOutcome) -> str:
    if outcome.errored:
        return "ERROR"
    return "PASS" if outcome.passed else "FAIL"


def _mark(value: bool) -> str:
    return "yes" if value else "no"
