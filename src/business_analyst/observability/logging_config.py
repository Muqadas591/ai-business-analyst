"""Safe operational logging configuration."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any


_STANDARD_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys()) | {
    "message",
    "asctime",
}


class JsonFormatter(logging.Formatter):
    """Render structured JSON logs without arbitrary extra fields."""

    ALLOWED_EXTRA_FIELDS = {
        "event",
        "request_id",
        "workspace_id",
        "user_id",
        "duration_ms",
        "status_code",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in self.ALLOWED_EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            # Avoid logging exception messages that might contain user data.
            payload["exception_type"] = record.exc_info[0].__name__

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure one application-level structured logging handler."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def log_security_event(
    logger: logging.Logger,
    *,
    event: str,
    status_code: int,
    user_id: str | None = None,
    workspace_id: str | None = None,
    dataset_id: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log a security event using explicitly allowlisted fields."""

    safe_fields: dict[str, Any] = {
        "event": event,
        "status_code": status_code,
    }

    optional_fields = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "dataset_id": dataset_id,
        "request_id": request_id,
    }

    for field, value in optional_fields.items():
        if value is not None:
            safe_fields[field] = value

    logger.info(
        "security_event %s",
        json.dumps(safe_fields, sort_keys=True),
        extra=safe_fields,
    )
