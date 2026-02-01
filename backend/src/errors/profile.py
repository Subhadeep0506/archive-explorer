class ProfileIncompleteError(Exception):
    """Exception raised when a user's profile is incomplete."""

    def __init__(self, message: str = "User profile is incomplete."):
        self.message = message
        super().__init__(self.message)


class FailedToLoadProfileError(Exception):
    """Exception raised when failing to load a user's profile."""

    def __init__(self, message: str = "Failed to load user profile."):
        self.message = message
        super().__init__(self.message)


class FailedToUpdateProfileError(Exception):
    """Exception raised when failing to update a user's profile."""

    def __init__(self, message: str = "Failed to update user profile."):
        self.message = message
        super().__init__(self.message)


class FailedToCreateProfileError(Exception):
    """Exception raised when failing to create a user's profile."""

    def __init__(self, message: str = "Failed to create user profile."):
        self.message = message
        super().__init__(self.message)


class FailedToDeleteProfileError(Exception):
    """Exception raised when failing to delete a user's profile."""

    def __init__(self, message: str = "Failed to delete user profile."):
        self.message = message
        super().__init__(self.message)
