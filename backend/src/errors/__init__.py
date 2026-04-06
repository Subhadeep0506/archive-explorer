from .auth import (
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserNotVerifiedError,
)
from .profile import (
    FailedToCreateProfileError,
    FailedToDeleteProfileError,
    FailedToLoadProfileError,
    FailedToUpdateProfileError,
    ProfileIncompleteError,
)
from .database import DatabaseConnectionError
from .arxiv import ArxivRateLimitError, ArxivAPIError

__all__ = [
    # auth
    "InvalidCredentialsError",
    "InvalidTokenError",
    "PermissionDeniedError",
    "TokenExpiredError",
    "UserAlreadyExistsError",
    "UserNotVerifiedError",
    # profile
    "FailedToCreateProfileError",
    "FailedToDeleteProfileError",
    "FailedToLoadProfileError",
    "FailedToUpdateProfileError",
    "ProfileIncompleteError",
    # database
    "DatabaseConnectionError",
    # arxiv
    "ArxivRateLimitError",
    "ArxivAPIError",
]
