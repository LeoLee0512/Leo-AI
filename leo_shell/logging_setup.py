"""Redacting rotating log for the Leo AI Studio shell.

One process-wide logger (``leo_shell``) writes to ``user/logs/leo-shell.log``
with rotation.  A filter scrubs credential-shaped text (``sk-...`` keys,
``token=`` query values, ``Bearer`` headers, JSON ``api_key``/``password``/
``secret`` values) plus any literal secret registered at runtime via
:func:`register_redaction`.  Logs carry phase codes, error codes, request ids
and durations only — never keys or full token URLs.
"""

from __future__ import annotations

import logging
import re
import threading
from logging.handlers import RotatingFileHandler

from .paths import AppPaths

__all__ = ["register_redaction", "setup_logging"]

_LOGGER_NAME = "leo_shell"
_LOG_FILENAME = "leo-shell.log"
_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_MAX_BYTES = 1024 * 1024
_BACKUP_COUNT = 3
_REDACTED = "<redacted>"

_SK_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
_TOKEN_QUERY_PATTERN = re.compile(r"([?&]token=)[^\s&\"']+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)
_JSON_SECRET_PATTERN = re.compile(
    r"(\"(?:api_key|password|secret)\"\s*:\s*\")[^\"]*(\")",
    re.IGNORECASE,
)

_REGISTRY_LOCK = threading.Lock()
_REGISTERED_SECRETS: set[str] = set()


def register_redaction(secret: str) -> None:
    """Register a literal value (e.g. an API key) that logs must never show."""
    if not isinstance(secret, str) or not secret:
        return
    with _REGISTRY_LOCK:
        _REGISTERED_SECRETS.add(secret)


def _redact_text(text: str) -> str:
    text = _SK_PATTERN.sub(_REDACTED, text)
    text = _TOKEN_QUERY_PATTERN.sub(r"\1" + _REDACTED, text)
    text = _BEARER_PATTERN.sub(r"\1" + _REDACTED, text)
    text = _JSON_SECRET_PATTERN.sub(r"\1" + _REDACTED + r"\2", text)
    with _REGISTRY_LOCK:
        literals = sorted(_REGISTERED_SECRETS, key=len, reverse=True)
    for literal in literals:
        if literal in text:
            text = text.replace(literal, _REDACTED)
    return text


class _RedactionFilter(logging.Filter):
    """Rewrite the rendered message with all known secrets scrubbed."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - formatting failure must not kill logging
            return True
        redacted = _redact_text(message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def setup_logging(paths: AppPaths, *, verbose: bool = False) -> logging.Logger:
    """Configure the process-wide ``leo_shell`` logger and return it.

    Repeated calls replace the previous handlers so tests and re-entry do not
    duplicate output.
    """
    paths.logs.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False
    for existing in list(logger.handlers):
        logger.removeHandler(existing)
        try:
            existing.close()
        except Exception:  # pragma: no cover - closing a dead handler
            pass
    handler = RotatingFileHandler(
        paths.logs / _LOG_FILENAME,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(_RedactionFilter())
    logger.addHandler(handler)
    return logger
