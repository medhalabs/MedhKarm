from app.core.errors import AppError, NotFoundError


class ArtifactNotFoundError(NotFoundError):
    code = "artifact_not_found"


class RangeNotSatisfiableError(AppError):
    status_code = 416
    code = "range_not_satisfiable"


class ArtifactTooLargeError(AppError):
    status_code = 413
    code = "artifact_too_large"
