class UserNotVerifiedError(Exception):
    """Exception raised when a user is not verified."""

    def __init__(self, message: str = "User is not verified."):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(Exception):
    """Exception raised for invalid authentication credentials."""

    def __init__(self, message: str = "Invalid credentials provided."):
        self.message = message
        super().__init__(self.message)


class TokenExpiredError(Exception):
    """Exception raised when an authentication token has expired."""

    def __init__(self, message: str = "Authentication token has expired."):
        self.message = message
        super().__init__(self.message)


class PermissionDeniedError(Exception):
    """Exception raised when a user does not have permission to access a resource."""

    def __init__(self, message: str = "Permission denied."):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsError(Exception):
    """Exception raised when trying to create a user that already exists."""

    def __init__(self, message: str = "User already exists."):
        self.message = message
        super().__init__(self.message)


class InvalidTokenError(Exception):
    """Exception raised for invalid authentication tokens."""

    def __init__(self, message: str = "Invalid authentication token."):
        self.message = message
        super().__init__(self.message)

class LoginError(Exception):
    """Exception raised for login related errors."""

    def __init__(self, message: str = "Login error occurred."):
        self.message = message
        super().__init__(self.message)