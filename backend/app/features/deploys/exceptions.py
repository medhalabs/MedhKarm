class DeployError(Exception):
    """The host refused or failed the deployment (the message is safe to show)."""
