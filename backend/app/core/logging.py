"""Logging setup. Never log secrets or API keys."""

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # LiteLLM logs every model call at INFO; our activity log already records them.
    for noisy in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
