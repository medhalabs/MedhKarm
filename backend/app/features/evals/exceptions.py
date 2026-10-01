from app.core.errors import AppError


class EvalTaskError(AppError):
    status_code = 400
    code = "invalid_eval_task"
