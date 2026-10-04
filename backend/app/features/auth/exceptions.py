from app.core.errors import ConflictError, UnauthorizedError


class InvalidCredentialsError(UnauthorizedError):
    code = "invalid_credentials"


class NotSignedInError(UnauthorizedError):
    code = "not_signed_in"


class EmailTakenError(ConflictError):
    code = "email_taken"
