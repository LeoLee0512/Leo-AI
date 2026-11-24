"""Redacted diagnostics report for support escalation.

``run_diagnostics`` drives the bridge's read-only steps (``preflight`` /
``status``, plus ``doctor`` when a runtime is installed) and writes the
combined outcome to ``user/logs/diagnostics-<yyyymmdd-HHMMSS>.json``.  Errors
are captured per step as ``code``/``message``/``guidance``; the report is
scrubbed recursively so it can never contain an API key or token.

The module only uses duck-typed access to the bridge error shape
(``code``/``message``/``guidance`` attributes), keeping it importable without
the sibling runtime modules.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = ["run_diagnostics"]


_REDACTED = "<redacted>"
_SECRET_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key|password|secret|token|authorization)")
_SK_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
_BEARER_PATTERN = re.compile(r"(?i)Bearer\s+\S+")
_TOKEN_QUERY_PATTERN = re.compile(r"(?i)(token=)[^&\s]+")


def _scrub_text(text: str) -> str:
    text = _SK_PATTERN.sub(_REDACTED, text)
    text = _BEARER_PATTERN.sub("Bearer " + _REDACTED, text)
    return _TOKEN_QUERY_PATTERN.sub(r"\1" + _REDACTED, text)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            text_key = str(key)
            cleaned[text_key] = _REDACTED if _SECRET_KEY_PATTERN.search(text_key) else _scrub(item)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _describe_error(exc: Exception) -> dict:
    code = getattr(exc, "code", None)
    message = getattr(exc, "message", None) or str(exc) or type(exc).__name__
    guidance = getattr(exc, "guidance", None)
    error: dict[str, Any] = {
        "code": str(code) if code else type(exc).__name__,
        "message": _scrub_text(str(message)),
    }
    if guidance:
        items = guidance if isinstance(guidance, (list, tuple)) else [guidance]
        error["guidance"] = [_scrub_text(str(item)) for item in items]
    return error


def _capture_step(bridge: Any, method: str, logger: logging.Logger) -> dict:
    func = getattr(bridge, method, None)
    if not callable(func):
        return {
            "ok": False,
            "error": {
                "code": "BRIDGE_STEP_UNAVAILABLE",
                "message": f"bridge does not provide a {method} step",
            },
        }
    try:
        result = func()
    except Exception as exc:
        code = getattr(exc, "code", None)
        logger.info("diagnostics step %s failed: %s", method, code or type(exc).__name__)
        return {"ok": False, "error": _describe_error(exc)}
    if isinstance(result, dict):
        scrubbed = _scrub(result)
        return scrubbed if isinstance(scrubbed, dict) else {"ok": True}
    return {"ok": True, "result": _scrub(result)}


def run_diagnostics(paths: Any, bridge: Any, logger: logging.Logger) -> Path:
    """Capture preflight/status/doctor into a timestamped JSON report."""

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    report["preflight"] = _capture_step(bridge, "preflight", logger)
    status = _capture_step(bridge, "status", logger)
    report["status"] = status
    if status.get("ok") and status.get("installed"):
        report["doctor"] = _capture_step(bridge, "doctor", logger)
    else:
        report["doctor"] = {"ok": False, "skipped": "runtime not installed"}

    logs_dir = Path(paths.logs)
    logs_dir.mkdir(parents=True, exist_ok=True)
    target = logs_dir / f"diagnostics-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    target.write_text(payload + "\n", encoding="utf-8")
    logger.info("diagnostics report written to %s", target)
    return target
