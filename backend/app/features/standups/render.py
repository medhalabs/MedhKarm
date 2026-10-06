"""A standup as plain text (email, the terminal) and as one line (WhatsApp)."""

from zoneinfo import ZoneInfo

from app.features.standups.schemas import Standup, StandupItem

SECTIONS = (
    ("needs_you", "Needs you"),
    ("done", "Done"),
    ("planned", "Planned today"),
    ("blocked", "Blocked"),
)


def to_text(standup: Standup, by: str = "") -> str:
    """The standup as plain text. `by` is who speaks (Priya): she greets and signs off."""
    zone = ZoneInfo(standup.timezone)
    since = standup.since.astimezone(zone)
    until = standup.until.astimezone(zone)
    lines = [f"Good morning, it's {by}. Here is your standup.", ""] if by else []
    lines += [
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
    if by:
        lines += ["", by]
    return "\n".join(lines)


def _by_run(items: list[StandupItem]) -> list[list[StandupItem]]:
    """One group per run, in order of first mention (two runs may share a name)."""
    grouped: dict[str, list[StandupItem]] = {}
    for item in items:
        grouped.setdefault(item.run_id, []).append(item)
    return list(grouped.values())


def to_short(standup: Standup, link: str = "", by: str = "") -> str:
    """One line for WhatsApp: the headline, what needs the founder, and the counts."""
    voice = f"{by}: " if by else ""
    parts = [f"{voice}Standup {standup.day:%a %d %b}: {standup.headline}"]
    if standup.needs_you:
        names = list(dict.fromkeys(item.project for item in standup.needs_you))
        parts.append(f"Needs you: {', '.join(names[:3])}" + (" and more" if len(names) > 3 else ""))
    parts.append(
        f"Done {len(standup.done)}, planned {len(standup.planned)}, blocked {len(standup.blocked)}"
    )
    if link:
        parts.append(f"Open: {link}")
    return ". ".join(parts)
