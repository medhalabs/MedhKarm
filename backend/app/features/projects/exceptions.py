from app.core.errors import ConflictError, NotFoundError


class ProjectNotFoundError(NotFoundError):
    code = "project_not_found"


class ItemNotFoundError(NotFoundError):
    code = "backlog_item_not_found"


class BacklogConflictError(ConflictError):
    """The change doesn't fit where the project or item stands (e.g. editing started work)."""

    code = "backlog_conflict"
