"""Priya's nudge: a short, kind reminder of what is waiting for the founder, once it has waited a
day. It speaks about releases to approve and plans to read (the things that have a time), and
mentions Mira's questions and blocked work alongside. It stops after four days: the inbox and the
standup still show everything, and nagging helps nobody."""

from datetime import datetime, timedelta

from app.features.inbox.schemas import Inbox
from app.features.notifications.schemas import Update

NUDGE_AFTER = timedelta(hours=24)
NUDGE_UNTIL = timedelta(hours=96)  # after four days she stops


def _ago(delta: timedelta) -> str:
    days = delta.days
    if days >= 1:
        return f"{days} day{'s' if days != 1 else ''}"
    hours = max(int(delta.total_seconds() // 3600), 1)
    return f"{hours} hour{'s' if hours != 1 else ''}"


def _title(text: str, limit: int = 60) -> str:
    line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "your project")
    line = line.lstrip("#> ").replace("**", "")
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"


def nudge(inbox: Inbox, now: datetime, link: str, by: str = "Priya") -> Update | None:
    """The reminder to send, or None when nothing has waited a day (or it has waited too long)."""
    waiting = [
        (now - a.waiting_since, f"A release to approve: {_title(a.request)}")
        for a in inbox.approvals
    ] + [(now - p.waiting_since, f"A plan to read: {_title(p.title)}") for p in inbox.plans]
    ages = [age for age, _ in waiting]
    if not ages or not (NUDGE_AFTER <= max(ages) < NUDGE_UNTIL):
        return None
    lines = [f"- {line} (waiting {_ago(age)})" for age, line in sorted(waiting, reverse=True)]
    questions = sum(len(q.questions) for q in inbox.questions)
    if questions:
        lines.append(f"- {questions} question{'s' if questions != 1 else ''} from Mira")
    if inbox.blocked:
        lines.append(f"- {len(inbox.blocked)} blocked item{'s' if len(inbox.blocked) != 1 else ''}")
    count = len(lines)
    noun = "thing is" if count == 1 else "things are"
    tail = f"\n\nOpen your inbox: {link}" if link else ""
    return Update(
        subject=f"{by}: {count} {noun} waiting for you",
        text=f"Hi, it's {by}. {count} {noun} waiting for you:\n" + "\n".join(lines) + tail,
        short=f"{by}: {count} {noun} waiting for you. "
        + "; ".join(line.removeprefix("- ") for line in lines[:3])
        + (f". Open: {link}" if link else ""),
    )
