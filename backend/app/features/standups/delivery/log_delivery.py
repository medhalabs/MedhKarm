"""StandupDelivery that writes the standup to the worker's log (until email and WhatsApp)."""

import logging

from app.features.standups.schemas import Standup

logger = logging.getLogger(__name__)


class LogDelivery:
    async def send(self, standup: Standup, text: str) -> str:
        logger.info("Standup for %s\n%s", standup.day, text)
        return "log"
