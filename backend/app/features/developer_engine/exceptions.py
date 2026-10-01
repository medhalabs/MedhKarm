from app.core.errors import AppError


class IncompatibleSandboxError(AppError):
    code = "incompatible_sandbox"
