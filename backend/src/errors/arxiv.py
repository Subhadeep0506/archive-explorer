class ArxivRateLimitError(Exception):
    """Exception raised when arXiv API rate limit (429) is exceeded."""

    def __init__(
        self,
        message: str = "arXiv API rate limit exceeded. Please try again in a few seconds.",
        retry_after: int | None = None,
    ):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class ArxivAPIError(Exception):
    """Exception raised for general arXiv API errors."""

    def __init__(
        self, message: str = "arXiv API error occurred.", status_code: int | None = None
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
