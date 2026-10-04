import json
from pathlib import Path

from app.features.evals.pricing import ModelPrice, PriceTable, load_prices
from app.features.evals.report import last_run, save, summary_markdown
from app.features.evals.schemas import EvalReport, TaskOutcome

BACKEND = Path(__file__).resolve().parents[4]


def outcome(task_id: str, passed: bool, prompt: int, completion: int) -> TaskOutcome:
    return TaskOutcome(
        task_id=task_id, kind="feature", difficulty=1, language="python", passed=passed,
        visible_passed=passed, hidden_passed=passed, prompt_tokens=prompt,
        completion_tokens=completion, total_tokens=prompt + completion, model_calls=3,
        seconds=60,
    )


PRICES = PriceTable(
    usd_to_inr=88,
    models=[
        ModelPrice(id="ollama_chat/gpt-oss:20b", label="gpt-oss:20b", input_usd=0, output_usd=0),
        ModelPrice(id="claude-sonnet-5-5", label="Sonnet", input_usd=2, output_usd=10,
                   reference=True),
    ],
)


def report(started: str, passed: bool = True) -> EvalReport:
    return EvalReport(
        started_at=started, engine="builtin", model="ollama_chat/gpt-oss:20b",
        outcomes=[outcome("a", passed, 1_000_000, 100_000), outcome("b", False, 0, 0)],
    )


def test_shipped_prices_have_the_free_model_and_references() -> None:
    prices = load_prices(BACKEND / "evals" / "prices.toml")

    assert prices.find("ollama_chat/gpt-oss:20b") is not None
    assert {m.id for m in prices.references} >= {"claude-sonnet-5-5", "claude-haiku-4-5"}
    assert prices.find("anthropic/claude-sonnet-5-5") is prices.find("claude-sonnet-5-5")


def test_cost_per_task_at_this_and_reference_models() -> None:
    text = summary_markdown(report("t1"), PRICES)

    # Sonnet: (1M × $2 + 0.1M × $10) / 1M = $3 for task a, $0 for b: $1.50 per task
    assert "| gpt-oss:20b (this run) | ₹0.00 ($0.000) |" in text
    assert "| Sonnet | ₹132.00 ($1.500) | ₹264.00 ($3.000) | ₹264.00 ($3.000) |" in text
    assert "| a | feature | 1 | PASS | yes | yes | 0 | 3 | 1,000,000 / 100,000 | 60s |" in text


def test_history_and_comparison_with_the_last_run(tmp_path: Path) -> None:
    save(report("2026-10-04T020000Z", passed=False), tmp_path, PRICES)
    path = save(report("2026-10-05T020000Z"), tmp_path, PRICES)

    lines = (tmp_path / "history.jsonl").read_text().splitlines()
    assert [json.loads(line)["passed"] for line in lines] == [0, 1]
    assert json.loads(lines[1])["usd_per_task"]["claude-sonnet-5-5"] == 1.5
    assert "passed 0/2 → 1/2" in path.read_text()
    assert last_run(tmp_path, "builtin", "other-model", "") is None
