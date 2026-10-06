"""From the founder's plain settings to the approval rules the release gate evaluates, and the
same settings as plain sentences. Pure: no I/O."""

from app.features.approvals.schemas import Action, ApprovalPolicy, ApprovalRule, Condition
from app.features.autonomy.schemas import AutonomySettings, Level

TOGGLES = {  # the template's rule id -> the setting that switches it on or off
    "sensitive_files": "ask_sensitive_files",
    "open_review_comments": "ask_open_comments",
    "security_warnings": "ask_security_warnings",
    "preview_failed": "ask_preview_failed",
    "large_change": "ask_large_change",
    "expensive_run": "ask_expensive",
}


def build_policy(base: ApprovalPolicy, settings: AutonomySettings) -> ApprovalPolicy:
    """The team template's policy, adjusted by the founder's settings. The strictest matching
    rule still wins, so "release on its own" never overrides a rule that says ask."""
    rules: list[ApprovalRule] = []
    for original in base.rules:
        rule = original.model_copy(deep=True)
        if rule.id in TOGGLES:
            rule.enabled = bool(getattr(settings, TOGGLES[rule.id]))
        if rule.id == "large_change":
            rule.when[0].value = settings.large_files
            rule.reason = f"It changes more than {settings.large_files} files."
        elif rule.id == "expensive_run":
            rule.when[0].value = settings.max_tokens
            rule.reason = f"It used more than {settings.max_tokens:,} model tokens."
        elif rule.id == "small_clean_change":
            rule.enabled = settings.level == Level.SMALL
            rule.when[0].value = settings.small_files
            rule.reason = (
                f"A small change ({settings.small_files} files or fewer) with passing tests "
                "and no open review comments."
            )
        rules.append(rule)
    if settings.level == Level.CHECKS:
        rules.append(
            ApprovalRule(
                id="checks_pass",
                action=Action.APPROVE,
                reason="Every check passed and nothing needs a look: released on its own.",
                when=[Condition(fact="tests_passed", op="eq", value=True)],
            )
        )
    for number, pattern in enumerate(settings.never_touch, start=1):
        rules.append(
            ApprovalRule(
                id=f"never_touch_{number}",
                action=Action.REJECT,
                reason=f"You told the team never to change {pattern}.",
                when=[Condition(fact="files_changed", op="matches_any", value=[pattern])],
            )
        )
    return ApprovalPolicy(default=Action.ASK, default_reason=base.default_reason, rules=rules)


def describe(settings: AutonomySettings) -> list[str]:
    """What the settings mean, in plain sentences for the founder."""
    lines: list[str]
    if settings.level == Level.EVERY:
        lines = ["Every release waits for your approval."]
    elif settings.level == Level.SMALL:
        lines = [
            f"Small, clean changes ({settings.small_files} files or fewer, passing checks, no open "
            "comments) are released on their own. Everything else waits for you."
        ]
    else:
        lines = ["A release goes out on its own once every check passes."]
    if settings.level != Level.EVERY:
        asks = _asks(settings)
        lines.append(
            "It still stops to ask you when " + _join(asks) + "."
            if asks
            else "Nothing else will stop it to ask you."
        )
    if settings.never_touch:
        lines.append("It stops without asking if it changes " + _join(settings.never_touch) + ".")
    lines.append(
        "After a release it publishes to the internet."
        if settings.go_live
        else "After a release it delivers the code but doesn't publish: you do that yourself."
    )
    return lines


def _asks(s: AutonomySettings) -> list[str]:
    wanted = [
        (s.ask_sensitive_files, "it changes secrets, dependencies, the database or deployment"),
        (s.ask_open_comments, "the CTO left review comments open"),
        (s.ask_security_warnings, "the security engineer has warnings"),
        (s.ask_preview_failed, "the preview doesn't build"),
        (s.ask_large_change, f"it changes more than {s.large_files} files"),
        (s.ask_expensive, f"it uses more than {s.max_tokens:,} model tokens"),
    ]
    return [text for on, text in wanted if on]


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " or " + items[-1]
