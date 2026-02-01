import os
import threading
import sys
import logfire
from loguru import logger


class SingletonLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_file="app.log"):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SingletonLogger, cls).__new__(cls)
                    cls._instance._init_logger(log_file)
        return cls._instance

    def _init_logger(self, log_file):
        logger.remove()  # Remove default console handler
        send_to_logfire = os.getenv("SEND_TO_LOGFIRE", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        logfire.configure(
            token=os.getenv("LOGFIRE_TOKEN"),
            send_to_logfire=send_to_logfire,
            service_name=os.getenv("OTEL_SERVICE_NAME", "arxiver-backend"),
            service_version=os.getenv("OTEL_SERVICE_VERSION", "0.0.1"),
            environment=os.getenv("ENVIRONMENT", "development"),
        )
        if send_to_logfire:
            logger.configure(handlers=[logfire.loguru_handler()])
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            backtrace=True,
        )
        self.logger = logger

    def get_logger(self):
        return self.logger
