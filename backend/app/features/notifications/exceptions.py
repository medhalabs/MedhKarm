from app.core.errors import AppError


class NotificationError(AppError):
    """A provider refused or couldn't be reached."""

    status_code = 502
    code = "notification_failed"
