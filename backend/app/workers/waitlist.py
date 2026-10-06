"""Read the waitlist and invite people (the emails are never served over HTTP).

uv run python -m app.workers.waitlist list
uv run python -m app.workers.waitlist export > waitlist.csv
uv run python -m app.workers.waitlist invite someone@example.com
"""

import argparse
import asyncio
import csv
import sys

from app.features.waitlist.dependencies import get_waitlist_service


async def main(args: argparse.Namespace) -> int:
    service = get_waitlist_service()
    if args.command == "invite":
        found = await service.invite(args.email)
        print("Marked as invited." if found else "That email isn't on the list.")
        return 0 if found else 1
    entries = await service.export()
    if args.command == "export":
        writer = csv.writer(sys.stdout)
        writer.writerow(["email", "name", "building", "source", "joined", "invited"])
        for e in entries:
            writer.writerow(
                [
                    e.email,
                    e.name,
                    e.building,
                    e.source,
                    e.created_at.isoformat(),
                    e.invited_at or "",
                ]
            )
        return 0
    print(f"{len(entries)} on the list, {sum(1 for e in entries if e.invited_at)} invited")
    for e in entries:
        mark = "invited" if e.invited_at else "waiting"
        print(f"{e.created_at:%d %b} {mark:8} {e.email}  {e.building[:70]}")
    return 0


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="Who is waiting")
    commands.add_parser("export", help="Everyone, as CSV")
    invite = commands.add_parser("invite", help="Mark someone as invited")
    invite.add_argument("email")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse())))
