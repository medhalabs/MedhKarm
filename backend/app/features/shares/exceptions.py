from app.core.errors import NotFoundError


class ShareNotFoundError(NotFoundError):
    """No such link, or it was turned off."""

    code = "share_not_found"
