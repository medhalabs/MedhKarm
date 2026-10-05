"""WhatsApp through Meta's WhatsApp Cloud API. Messages a business starts must use an
approved template: ours (WHATSAPP_TEMPLATE, default `medhkarm_update`) has one body variable,
{{1}}, which gets the one-line update (Meta allows no line breaks in variables)."""

import re

import httpx

from app.features.notifications.exceptions import NotificationError
from app.features.notifications.schemas import Channel

GRAPH = "https://graph.facebook.com/v21.0"
MAX_VARIABLE = 1000


def template_text(text: str) -> str:
    """Meta's rules for a template variable: no newlines or tabs, no 4+ spaces in a row."""
    flat = re.sub(r"[\r\n\t]+", " • ", text)
    flat = re.sub(r" {4,}", "   ", flat).strip()
    return flat if len(flat) <= MAX_VARIABLE else flat[: MAX_VARIABLE - 1] + "…"


class MetaWhatsApp:
    channel = Channel.WHATSAPP

    def __init__(
        self,
        token: str,
        phone_number_id: str,
        template: str = "medhkarm_update",
        language: str = "en",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token
        self._url = f"{GRAPH}/{phone_number_id}/messages"
        self._template = template
        self._language = language
        self._client = client

    async def send(self, to: str, subject: str, text: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "to": to.lstrip("+"),
            "type": "template",
            "template": {
                "name": self._template,
                "language": {"code": self._language},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": template_text(text)}]}
                ],
            },
        }
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            if self._client:
                response = await self._client.post(self._url, json=payload, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(self._url, json=payload, headers=headers)
        except httpx.HTTPError as error:
            raise NotificationError(f"Couldn't reach WhatsApp: {error}") from error
        if response.status_code >= 400:
            raise NotificationError(
                f"WhatsApp refused the message ({response.status_code}): {response.text[:200]}"
            )
