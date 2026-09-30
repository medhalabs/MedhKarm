from app.core.errors import AppError


class ModelCallError(AppError):
    status_code = 502
    code = "model_call_failed"
