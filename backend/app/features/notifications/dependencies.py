from functools import cache

from app.core.config import Settings, get_settings
from app.core.database import session_factory
from app.features.notifications.interfaces import Notifier
from app.features.notifications.providers.meta_whatsapp import MetaWhatsApp
from app.features.notifications.providers.resend_email import ResendEmail
from app.features.notifications.providers.smtp_email import SmtpEmail
from app.features.notifications.repository import SqlSettingsRepository
from app.features.notifications.service import NotificationService


def notifiers(settings: Settings) -> list[Notifier]:
    """The providers whose keys are set: Resend (or else SMTP) for email, Meta for WhatsApp."""
    found: list[Notifier] = []
    if settings.resend_api_key:
        found.append(ResendEmail(settings.resend_api_key.get_secret_value(), settings.email_from))
    elif settings.smtp_host:
        password = settings.smtp_password.get_secret_value() if settings.smtp_password else ""
        found.append(
            SmtpEmail(
                settings.smtp_host,
                settings.smtp_port,
                settings.smtp_user,
                password,
                settings.email_from,
            )
        )
    if settings.whatsapp_token and settings.whatsapp_phone_number_id:
        found.append(
            MetaWhatsApp(
                settings.whatsapp_token.get_secret_value(),
                settings.whatsapp_phone_number_id,
                settings.whatsapp_template,
                settings.whatsapp_template_language,
            )
        )
    return found


@cache
def get_notification_service() -> NotificationService:
    settings = get_settings()
    return NotificationService(
        SqlSettingsRepository(session_factory), notifiers(settings), settings.standup_timezone
    )
