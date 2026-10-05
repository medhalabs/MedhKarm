"""Email through any SMTP server (e.g. Gmail with an app password), with STARTTLS."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.features.notifications.exceptions import NotificationError
from app.features.notifications.schemas import Channel


class SmtpEmail:
    channel = Channel.EMAIL

    def __init__(self, host: str, port: int, user: str, password: str, sender: str) -> None:
        self._host, self._port = host, port
        self._user, self._password = user, password
        self._sender = sender

    async def send(self, to: str, subject: str, text: str) -> None:
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = self._sender, to, subject
        message.set_content(text)
        try:
            await asyncio.to_thread(self._send, message)
        except (smtplib.SMTPException, OSError) as error:
            raise NotificationError(f"The mail server refused the email: {error}") from error

    def _send(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port, timeout=20) as server:
            server.starttls(context=ssl.create_default_context())
            if self._user:
                server.login(self._user, self._password)
            server.send_message(message)
