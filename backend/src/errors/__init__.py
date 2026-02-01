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
]
