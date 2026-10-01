from app.core.errors import AppError


class StandupDayInFutureError(AppError):
    status_code = 400
    code = "standup_day_in_future"
