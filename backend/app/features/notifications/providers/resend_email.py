"""Email through Resend (resend.com): one HTTPS call. A sender on your own verified domain
(EMAIL_FROM); Resend's onboarding sender only delivers to the account's own address."""

import httpx

from app.features.notifications.exceptions import NotificationError
from app.features.notifications.schemas import Channel

API = "https://api.resend.com/emails"


class ResendEmail:
    channel = Channel.EMAIL

    def __init__(self, api_key: str, sender: str, client: httpx.AsyncClient | None = None) -> None:
        self._key = api_key
        self._sender = sender
        self._client = client

    async def send(self, to: str, subject: str, text: str) -> None:
        payload = {"from": self._sender, "to": [to], "subject": subject, "text": text}
        headers = {"Authorization": f"Bearer {self._key}"}
        try:
            if self._client:
                response = await self._client.post(API, json=payload, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(API, json=payload, headers=headers)
        except httpx.HTTPError as error:
            raise NotificationError(f"Couldn't reach Resend: {error}") from error
        if response.status_code >= 400:
            raise NotificationError(
                f"Resend refused the email ({response.status_code}): {response.text[:200]}"
            )
