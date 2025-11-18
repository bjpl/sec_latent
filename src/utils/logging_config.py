"""
Logging and Monitoring Configuration
Centralized logging setup with multiple handlers
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: str = "./logs",
    enable_json: bool = False
) -> logging.Logger:
    """
    Setup comprehensive logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_json: Use JSON formatting

    Returns:
        Configured root logger
    """
    # Get settings
    settings = get_settings().monitoring

    if log_level is None:
        log_level = settings.log_level

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    if enable_json:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_formatter = logging.Formatter(
            settings.log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    # File handler - general log
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "sec_analysis.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    if enable_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_formatter = logging.Formatter(
            settings.log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        JSONFormatter() if enable_json else logging.Formatter(settings.log_format)
    )
    logger.addHandler(error_handler)

    # Performance log handler
    perf_handler = logging.handlers.RotatingFileHandler(
        log_path / "performance.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.addFilter(lambda record: "performance" in record.name.lower())
    perf_handler.setFormatter(
        JSONFormatter() if enable_json else logging.Formatter(settings.log_format)
    )
    logger.addHandler(perf_handler)

    logger.info(f"Logging configured: level={log_level}, dir={log_dir}, json={enable_json}")
    return logger


class PerformanceLogger:
    """Logger for tracking performance metrics"""

    def __init__(self):
        self.logger = logging.getLogger("performance")

    def log_task_performance(
        self,
        task_name: str,
        duration: float,
        success: bool,
        **metadata
    ):
        """Log task performance metrics"""
        self.logger.info(
            f"Task: {task_name} | Duration: {duration:.2f}s | Success: {success}",
            extra={
                "task_name": task_name,
                "duration_seconds": duration,
                "success": success,
                **metadata
            }
        )

    def log_api_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration: float
    ):
        """Log API call metrics"""
        self.logger.info(
            f"API Call: {model} | Tokens: {input_tokens + output_tokens} | Duration: {duration:.2f}s",
            extra={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "duration_seconds": duration
            }
        )


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger by name"""
    return logging.getLogger(name)
