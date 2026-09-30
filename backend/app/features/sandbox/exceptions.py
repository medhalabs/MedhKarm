from app.core.errors import AppError, NotFoundError


class SandboxError(AppError):
    code = "sandbox_error"


class SandboxNotFoundError(NotFoundError):
    code = "sandbox_not_found"


class UnsafePathError(SandboxError):
    status_code = 400
    code = "unsafe_path"
