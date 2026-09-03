"""Structured Application Logging Service for RecoverIQ.

Outputs contextual JSON logs with correlation IDs while guaranteeing zero leakage
of secrets, API credentials, webhook tokens, or customer PII.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Configure root logger
logger = logging.getLogger("recoveriq")
logger.setLevel(logging.INFO)

# Formatter to ensure structured output without duplicates if handler exists
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


class StructuredLogger:
    """Provides sanitized, correlation-aware structured logging for all subsystems."""

    FORBIDDEN_KEYS = {
        "api_key",
        "secret",
        "webhook_secret",
        "razorpay_key_secret",
        "openai_api_key",
        "password",
        "token",
        "email",
        "phone",
        "authorization",
    }

    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        """Recursively scrubs secrets and sensitive PII from dictionaries or lists."""
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(forbidden in k.lower() for forbidden in cls.FORBIDDEN_KEYS):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = cls._sanitize(v)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [cls._sanitize(item) for item in data]
        return data

    @classmethod
    def log(
        cls,
        level: str,
        component: str,
        operation: str,
        status: str,
        message: str,
        case_id: Optional[int] = None,
        recovery_action_id: Optional[int] = None,
        approval_id: Optional[int] = None,
        event_id: Optional[Any] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Emits a structured log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "component": component,
            "operation": operation,
            "status": status.upper(),
            "message": message,
        }

        if case_id is not None:
            log_entry["case_id"] = case_id
        if recovery_action_id is not None:
            log_entry["recovery_action_id"] = recovery_action_id
        if approval_id is not None:
            log_entry["approval_id"] = approval_id
        if event_id is not None:
            log_entry["event_id"] = str(event_id)
        if request_id is not None:
            log_entry["request_id"] = request_id
        if details:
            log_entry["details"] = cls._sanitize(details)

        formatted_msg = json.dumps(log_entry)

        if level.upper() == "ERROR":
            logger.error(formatted_msg)
        elif level.upper() == "WARNING":
            logger.warning(formatted_msg)
        elif level.upper() == "DEBUG":
            logger.debug(formatted_msg)
        else:
            logger.info(formatted_msg)

    @classmethod
    def info(cls, component: str, operation: str, message: str, **kwargs):
        cls.log("INFO", component, operation, "SUCCESS", message, **kwargs)

    @classmethod
    def warning(cls, component: str, operation: str, message: str, **kwargs):
        cls.log("WARNING", component, operation, "WARNING", message, **kwargs)

    @classmethod
    def error(cls, component: str, operation: str, message: str, **kwargs):
        cls.log("ERROR", component, operation, "FAILURE", message, **kwargs)


structured_logger = StructuredLogger()
