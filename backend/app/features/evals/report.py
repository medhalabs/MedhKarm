"""Turns eval outcomes into a Markdown summary and a JSON file."""

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.features.evals.pricing import ModelPrice, PriceTable
from app.features.evals.schemas import EvalReport, TaskOutcome, ValidationOutcome

HISTORY = "history.jsonl"


def summary_markdown(
    report: EvalReport, prices: PriceTable | None = None, previous: dict[str, Any] | None = None
) -> str:
    outcomes = report.outcomes
    scored = report.scored
    lines = [
        f"# Eval run {report.started_at}",
        "",
        f"Engine: **{report.engine}** · Model: **{report.model}** · "
        + (f"Variant: **{report.variant}** · " if report.variant else "")
        +
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
        f"Time: median {statistics.median(seconds) if seconds else 0:.0f}s, "
        f"mean {statistics.mean(seconds) if seconds else 0:.0f}s per task.",
    ]
    if prices:
        lines += _cost_lines(report, prices)
    if previous:
        lines += _change_lines(report, previous)
    lines += [
        "",
        "| Task | Kind | Diff. | Result | Visible | Hidden | Steps | Calls | Tokens in / out "
        "| Time | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for o in sorted(outcomes, key=lambda o: o.task_id):
        note = (o.error or o.summary).replace("|", "/").replace("\n", " ")[:80]
        lines.append(
            f"| {o.task_id} | {o.kind} | {o.difficulty} | {_result(o)} | "
            f"{_mark(o.visible_passed)} | {_mark(o.hidden_passed)} | {o.steps} | "
            f"{o.model_calls} | {o.prompt_tokens:,} / {o.completion_tokens:,} | "
            f"{o.seconds:.0f}s | {note} |"
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


def save(report: EvalReport, results_dir: Path, prices: PriceTable | None = None) -> Path:
    """Writes the run's JSON and Markdown, and appends a line to the history (trend)."""
    results_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{report.started_at.replace(':', '')}-{report.engine}"
    if report.variant:
        stem += f"-{report.variant}"
    previous = last_run(results_dir, report.engine, report.model, report.variant)
    (results_dir / f"{stem}.json").write_text(report.model_dump_json(indent=2))
    path = results_dir / f"{stem}.md"
    path.write_text(summary_markdown(report, prices, previous))
    with (results_dir / HISTORY).open("a", encoding="utf-8") as history:
        history.write(json.dumps(history_line(report, prices)) + "\n")
    return path


def history_line(report: EvalReport, prices: PriceTable | None = None) -> dict[str, Any]:
    scored = report.scored
    seconds = [o.seconds for o in scored]
    line: dict[str, Any] = {
        "started_at": report.started_at,
        "engine": report.engine,
        "model": report.model,
        "variant": report.variant,
        "passed": report.passed,
        "scored": len(scored),
        "errored": len(report.errored),
        "median_seconds": round(statistics.median(seconds), 1) if seconds else 0,
        "prompt_tokens": sum(o.prompt_tokens for o in scored),
        "completion_tokens": sum(o.completion_tokens for o in scored),
    }
    if prices:
        line["usd_per_task"] = {
            m.id: round(_per_task(scored, m), 4) for m in _priced(report, prices)
        }
    return line


def last_run(results_dir: Path, engine: str, model: str, variant: str) -> dict[str, Any] | None:
    """The latest earlier run with the same engine, model and variant, from the history."""
    path = results_dir / HISTORY
    if not path.exists():
        return None
    runs = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    same = [
        r
        for r in runs
        if (r.get("engine"), r.get("model"), r.get("variant", "")) == (engine, model, variant)
    ]
    return same[-1] if same else None


def _priced(report: EvalReport, prices: PriceTable) -> list[ModelPrice]:
    actual = prices.find(report.model)
    return ([actual] if actual else []) + [m for m in prices.references if m is not actual]


def _per_task(outcomes: list[TaskOutcome], price: ModelPrice) -> float:
    if not outcomes:
        return 0.0
    return sum(price.cost_usd(o.prompt_tokens, o.completion_tokens) for o in outcomes) / len(
        outcomes
    )


def _cost_lines(report: EvalReport, prices: PriceTable) -> list[str]:
    scored = report.scored
    passed = [o for o in scored if o.passed]
    lines = [
        "",
        "Cost per task, for the same tokens (prompt caching not applied; reference models are "
        "estimates, since each model uses its own number of tokens):",
        "",
        "| Model | Per task | Per passed task | Whole run |",
        "| --- | --- | --- | --- |",
    ]
    actual = prices.find(report.model)
    for price in _priced(report, prices):
        per_task = _per_task(scored, price)
        total = per_task * len(scored)
        per_pass = total / len(passed) if passed else 0.0
        name = price.label + (" (this run)" if price is actual else "")
        lines.append(
            f"| {name} | {_money(per_task, prices)} | {_money(per_pass, prices)} | "
            f"{_money(total, prices)} |"
        )
    return lines


def _change_lines(report: EvalReport, previous: dict[str, Any]) -> list[str]:
    seconds = [o.seconds for o in report.scored]
    median = statistics.median(seconds) if seconds else 0
    return [
        "",
        f"Since the last run ({previous['started_at']}): passed {previous['passed']}/"
        f"{previous['scored']} → {report.passed}/{len(report.scored)}; median time "
        f"{previous['median_seconds']:.0f}s → {median:.0f}s.",
    ]


def _money(usd: float, prices: PriceTable) -> str:
    return f"₹{usd * prices.usd_to_inr:,.2f} (${usd:,.3f})"


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
