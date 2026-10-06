"""The release sign-off card: what each member of the team says about a release, worked out
from the run's activity log. Nothing is stored: the card is always what the log says."""

from typing import Protocol

from app.features.events.schemas import Actor, Event, EventType
from app.features.signoffs.schemas import Signoff, State

TITLES = {
    "developer": "Developers",
    "cto": "CTO",
    "qa": "QA engineer",
    "security": "Security engineer",
    "devops": "DevOps",
    "docs": "Documentation",
    "founder": "You",
}
READY_PREFIXES = ("Preview ready", "Live at")


class Card(Protocol):
    def __call__(
        self, role: str, state: State, headline: str, details: list[str], url: str = ""
    ) -> Signoff: ...


def build(events: list[Event], names: dict[str, str]) -> list[Signoff]:
    """The sign-offs in the order the work happens. `names`: role id -> the member's name."""

    def of(type_: EventType, actor: Actor | None = None) -> list[Event]:
        return [e for e in events if e.type == type_ and (actor is None or e.actor == actor)]

    def card(role: str, state: State, headline: str, details: list[str], url: str = "") -> Signoff:
        return Signoff(
            role=role,
            name=names.get(role, TITLES[role]),
            title=TITLES[role],
            state=state,
            headline=headline,
            details=details,
            url=url,
        )

    # Steps a run never reaches show as "not part of this run" only once it's at the gate or over
    over = bool(of(EventType.APPROVAL_REQUESTED) or of(EventType.RUN_FINISHED))
    return [
        _developers(of(EventType.WORK_FINISHED), card),
        _cto(of(EventType.REVIEW_FINISHED), card),
        _qa(of(EventType.CHECK_FINISHED, Actor.QA), card),
        _security(of(EventType.SECURITY_FINISHED), over, card),
        _devops(of(EventType.DEPLOY_FINISHED), of(EventType.CHANGES_DELIVERED), over, card),
        _docs(of(EventType.DOCS_UPDATED), over, card),
        _founder(of(EventType.APPROVAL_DECIDED), card),
    ]


def _developers(finished: list[Event], card: Card) -> Signoff:
    tasks = {e.data.get("task_id"): e for e in finished}
    if not tasks:
        return card("developer", State.WAITING, "Haven't finished anything yet", [])
    who = sorted({str(e.data.get("member", "")) for e in finished if e.data.get("member")})
    details = [e.summary for e in tasks.values()]
    return card(
        "developer",
        State.OK,
        f"Built {len(tasks)} task{'s' if len(tasks) != 1 else ''}"
        + (f" ({', '.join(who)})" if who else ""),
        details,
    )


def _cto(reviews: list[Event], card: Card) -> Signoff:
    if not reviews:
        return card("cto", State.WAITING, "Hasn't reviewed anything yet", [])
    last: dict[str, Event] = {}
    for e in reviews:
        last[str(e.data.get("task_id"))] = e
    sent_back = sum(1 for e in reviews if e.data.get("decision") == "revise")
    issues = [e for e in last.values() if e.data.get("accepted_with_issues")]
    headline = f"Reviewed {len(last)} task{'s' if len(last) != 1 else ''}"
    if sent_back:
        headline += f", sent {sent_back} back for changes"
    if issues:
        return card(
            "cto",
            State.WARN,
            headline + f"; moved on from {len(issues)} with open comments",
            [e.summary for e in issues],
        )
    return card("cto", State.OK, headline + ", all approved", [])


def _qa(checks: list[Event], card: Card) -> Signoff:
    tests = [e for e in checks if not e.data.get("browser")]
    browser = [e for e in checks if e.data.get("browser")]
    if not checks:
        return card("qa", State.WAITING, "Hasn't tested anything yet", [])
    latest = [tests[-1]] if tests else []
    latest += [browser[-1]] if browser else []
    failed = [e for e in latest if not e.data.get("passed")]
    details = [e.summary for e in latest]
    if failed:
        return card("qa", State.FAIL, failed[0].summary, details)
    return card("qa", State.OK, " · ".join(details), [])


def _not_here(over: bool) -> State:
    return State.SKIPPED if over else State.WAITING


def _security(reports: list[Event], over: bool, card: Card) -> Signoff:
    if not reports:
        text = "No security scan on this run" if over else "Hasn't scanned yet"
        return card("security", _not_here(over), text, [])
    last = reports[-1]
    blocking = int(last.data.get("blocking", 0))
    warnings = int(last.data.get("warnings", 0))
    if blocking:
        return card("security", State.FAIL, last.summary, [])
    state = State.WARN if warnings else State.OK
    return card("security", state, last.summary, [])


def _devops(deploys: list[Event], delivered: list[Event], over: bool, card: Card) -> Signoff:
    details = [e.summary for e in delivered]
    pull = next((e.data.get("pull_request_url") or e.data.get("repo_url") for e in delivered), "")
    if not deploys:
        text = "No preview was set up for this run" if over else "Hasn't put a preview online yet"
        return card("devops", _not_here(over), text, details, str(pull or ""))
    last = deploys[-1]
    ok = last.summary.startswith(READY_PREFIXES)
    return card(
        "devops",
        State.OK if ok else State.FAIL,
        last.summary.split(":")[0] if ok else last.summary,
        details,
        str(last.data.get("url", "") if ok else pull or ""),
    )


def _docs(updates: list[Event], over: bool, card: Card) -> Signoff:
    if not updates:
        text = "No docs folder in this project to update" if over else "Hasn't updated the docs yet"
        return card("docs", _not_here(over), text, [])
    entry = str(updates[-1].data.get("entry", ""))
    return card("docs", State.OK, "Added to the changelog", entry.splitlines())


def _founder(decisions: list[Event], card: Card) -> Signoff:
    if not decisions:
        return card("founder", State.WAITING, "Waiting for your approval", [])
    last = decisions[-1]
    approved = bool(last.data.get("approved"))
    by_rules = last.data.get("by") == "rules"
    if approved:
        return card(
            "founder",
            State.OK,
            "Approved by your rules" if by_rules else "You approved the release",
            [],
        )
    return card("founder", State.FAIL, "Not approved", [last.summary])
