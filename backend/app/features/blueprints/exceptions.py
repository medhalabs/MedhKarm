from app.core.errors import ConflictError, NotFoundError


class BlueprintNotFoundError(NotFoundError):
    code = "blueprint_not_found"


class BlueprintNotReadyError(ConflictError):
    """Approving or commenting needs a blueprint that is ready."""

    code = "blueprint_not_ready"
