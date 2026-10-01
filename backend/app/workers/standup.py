"""Prints the daily standup from the activity log.

    uv run python -m app.workers.standup                 (today's)
    uv run python -m app.workers.standup --day 2026-10-01

Sending it every morning (email, WhatsApp) comes with the job queue.
"""

import argparse
import asyncio
from datetime import date

from app.core.logging import configure_logging
from app.features.standups.dependencies import get_standup_service
from app.features.standups.render import to_text


async def main() -> None:
    parser = argparse.ArgumentParser(description="Print the daily standup.")
    parser.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    configure_logging("WARNING")
    print(to_text(await get_standup_service().for_day(args.day)))


if __name__ == "__main__":
    asyncio.run(main())
