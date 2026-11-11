"""Structured rotating logging setup for Math Mayhem."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.config import Settings, get_settings


class JsonLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for auditability."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event_type"):
            payload["event_type"] = getattr(record, "event_type")
        if hasattr(record, "context"):
            payload["context"] = getattr(record, "context")
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging(
    settings: Optional[Settings] = None,
    log_filename: str = "math_mayhem.log",
) -> logging.Logger:
    """Configure and return the math_mayhem application logger."""
    cfg = settings or get_settings()
    cfg.MM_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path: Path = cfg.MM_LOGS_DIR / log_filename

    logger = logging.getLogger("math_mayhem")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Avoid duplicate handlers on repeated initialization
    for h in list(logger.handlers):
        h.close()
        logger.removeHandler(h)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonLogFormatter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(console_handler)

    return logger
