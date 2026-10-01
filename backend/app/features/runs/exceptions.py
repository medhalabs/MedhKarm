from app.core.errors import ConflictError, NotFoundError


class RunNotFoundError(NotFoundError):
    code = "run_not_found"


class RunNotWaitingError(ConflictError):
    code = "run_not_waiting_for_approval"
