class DatabaseConnectionError(Exception):
    """Raised when the DB connection fails (e.g. psycopg2 OperationalError).

    Routes can catch this and return 503 / log as needed.
    """

    def __init__(self, message: str = "Database connection error occurred."):
        self.message = message
        super().__init__(self.message)
