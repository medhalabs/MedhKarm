"""A standup as plain text: for the terminal now, email and WhatsApp later."""

from zoneinfo import ZoneInfo

from app.features.standups.schemas import Standup, StandupItem

SECTIONS = (
    ("needs_you", "Needs you"),
    ("done", "Done"),
    ("planned", "Planned today"),
    ("blocked", "Blocked"),
)


def to_text(standup: Standup) -> str:
    zone = ZoneInfo(standup.timezone)
    since = standup.since.astimezone(zone)
    until = standup.until.astimezone(zone)
    lines = [
        f"Standup for {standup.day:%a %d %b %Y}",
        f"{since:%d %b %H:%M} to {until:%d %b %H:%M} ({standup.timezone})",
        "",
        standup.headline,
    ]
    for key, title in SECTIONS:
        items: list[StandupItem] = getattr(standup, key)
        lines += ["", f"{title}:"]
        if not items:
            lines.append("  Nothing")
        for group in _by_run(items):
            lines.append(f"  {group[0].project}")
            lines += [f"    - {item.text}" for item in group]
    lines.append("")
    if standup.sent_back:
        plural = "s" if standup.sent_back != 1 else ""
        lines.append(f"The CTO sent {standup.sent_back} task{plural} back for changes.")
    lines.append(f"Model use: {standup.tokens:,} tokens.")
    return "\n".join(lines)


def _by_run(items: list[StandupItem]) -> list[list[StandupItem]]:
    """One group per run, in order of first mention (two runs may share a name)."""
    grouped: dict[str, list[StandupItem]] = {}
    for item in items:
        grouped.setdefault(item.run_id, []).append(item)
    return list(grouped.values())
