class TempTFError(Exception):
    """Base exception for temptf errors."""


class APIError(TempTFError):
    """Raised when the temp.tf API returns an error status code."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class RateLimitError(APIError):
    """Raised when rate limit (HTTP 429) is exceeded and auto-retry is disabled."""

    def __init__(self, retry_after: int, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        super().__init__(429, message)
