"""Background worker entry point.

Long-running work (LangGraph runs, sandbox jobs, evals) runs here, never inside an API request.
The job queue (arq on Redis, or a Postgres job table) is chosen in Phase 1; until then this
only proves the entry point starts.
"""

import logging

from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    settings = get_settings()
    logger.info(
        "Worker started (environment=%s). No job queue configured yet.", settings.environment
    )


if __name__ == "__main__":
    main()
