"""The weekly report: what the team shipped, what stopped and what it cost, over the 7 days
before the report's day. Built from the company's runs and their activity."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.features.standups.interfaces import ActivityLog, RunLister

PAGE = 1000
OUTCOMES = ("released", "failed", "rejected", "cancelled", "error")


class WeeklyReport(BaseModel):
    day: date  # the report's day (a Monday): covers the 7 days before it
    timezone: str
    started: int  # runs started in the week
    outcomes: dict[str, list[str]] = Field(default_factory=dict)  # status -> requests
    waiting: list[str] = Field(default_factory=list)  # at the gate now
    tokens: int = 0


async def build_weekly(
    runs: RunLister, log: ActivityLog, company_id: str, day: date, timezone: str
) -> WeeklyReport:
    zone = ZoneInfo(timezone)
    until = datetime.combine(day, time(0), zone)
    since = until - timedelta(days=7)
    report = WeeklyReport(day=day, timezone=timezone, started=0)
    for run in await runs.list(500, company_id):
        if not since <= run.updated_at < until and run.status != "waiting_for_approval":
            continue
        title = run.request.strip().splitlines()[0][:80] if run.request.strip() else run.id
        if since <= run.created_at < until:
            report.started += 1
        if run.status in OUTCOMES and since <= run.updated_at < until:
            report.outcomes.setdefault(str(run.status), []).append(title)
        elif run.status == "waiting_for_approval":
            report.waiting.append(title)
        report.tokens += await _tokens(log, run.id, since, until)
    return report


async def _tokens(log: ActivityLog, run_id: str, since: datetime, until: datetime) -> int:
    total, after = 0, 0
    while True:
        page = await log.list_for_run(run_id, after, PAGE)
        total += sum(e.tokens for e in page if since <= e.occurred_at < until)
        if len(page) < PAGE:
            return total
        after = page[-1].id


LABELS = {
    "released": "Released",
    "failed": "Checks failed",
    "rejected": "Not approved",
    "cancelled": "Cancelled",
    "error": "Something broke",
}


def weekly_text(report: WeeklyReport, link: str = "") -> str:
    released = len(report.outcomes.get("released", []))
    lines = [
        f"Your week up to {report.day:%a %d %b %Y}",
        "",
        f"{report.started} run{'s' if report.started != 1 else ''} started, "
        f"{released} released, {len(report.waiting)} waiting for you.",
    ]
    for status, label in LABELS.items():
        titles = report.outcomes.get(status, [])
        if titles:
            lines += ["", f"{label}:"] + [f"  - {t}" for t in titles]
    if report.waiting:
        lines += ["", "Waiting for your approval:"] + [f"  - {t}" for t in report.waiting]
    lines += ["", f"Model use: {report.tokens:,} tokens."]
    if link:
        lines += ["", f"Open your inbox: {link}"]
    return "\n".join(lines)


def weekly_short(report: WeeklyReport, link: str = "") -> str:
    released = len(report.outcomes.get("released", []))
    stopped = sum(len(report.outcomes.get(s, [])) for s in ("failed", "rejected", "error"))
    text = (
        f"Your week: {report.started} runs started, {released} released, {stopped} stopped, "
        f"{len(report.waiting)} waiting for you. {report.tokens:,} tokens"
    )
    return f"{text}. Open: {link}" if link else text
