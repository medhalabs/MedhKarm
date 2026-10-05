from app.core.errors import NotFoundError


class ThreadNotFoundError(NotFoundError):
    code = "thread_not_found"
