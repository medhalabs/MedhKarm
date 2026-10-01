class PermanentJobError(Exception):
    """Raised by a handler when retrying can't help (bad payload, missing run): fail at once."""
