import os
import threading
import sys
import logging
import logfire
from loguru import logger


# Filter class to suppress specific SSE parsing errors from Cohere SDK
class SSEErrorFilter(logging.Filter):
    def filter(self, record):
        # Suppress the "[DONE]" JSON parsing error from httpx-sse/cohere
        if (
            "Failed to parse SSE data field as JSON" in record.getMessage()
            and "[DONE]" in record.getMessage()
        ):
            return False
        return True


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

        # Filter function for loguru to suppress SSE [DONE] parsing errors
        def filter_sse_errors(record):
            message = record.get("message", "")
            if (
                "Failed to parse SSE data field as JSON" in message
                and "[DONE]" in message
            ):
                return False
            return True

        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            backtrace=True,
            filter=filter_sse_errors,
        )

        # Apply SSE error filter to suppress Cohere's [DONE] parsing warnings
        sse_filter = SSEErrorFilter()

        # Apply filter to httpx-sse and cohere loggers
        for logger_name in ["httpx_sse", "cohere", "httpx"]:
            lib_logger = logging.getLogger(logger_name)
            lib_logger.addFilter(sse_filter)

        # Also apply to root logger to catch any other instances
        logging.getLogger().addFilter(sse_filter)

        self.logger = logger

    def get_logger(self):
        return self.logger
