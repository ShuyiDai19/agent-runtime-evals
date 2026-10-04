class RetryableToolError(Exception):
    """A transient tool failure that may succeed if retried."""