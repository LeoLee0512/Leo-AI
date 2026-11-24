"""3.2.11 · 「用量」: per-model temperature and the local model's latest request (owner, 2026-09-30).

Both live in WSL next to the daemon's data: the temperatures are read by ``leo_reasoning.apply_request``
on every chat request (so a change applies to the next message, no restart), and the local relay keeps
its latest main-loop request. Leo runs the two bridge scripts' small commands; nothing else is touched.
Token counts and cache hits come from the daemon's own timeline, and the context estimate from its
``/frames/{id}/context`` (see ``workbench.py``).
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from .bridge_client import WslBridge, windows_path_to_wsl

TEMPERATURE_MIN, TEMPERATURE_MAX = 0.0, 1.5


def _model(value):
    if not isinstance(value, str) or not 0 < len(value) <= 200 or any(ord(c) < 32 for c in value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


def _temperature(value):
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or not TEMPERATURE_MIN <= value <= TEMPERATURE_MAX:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return round(float(value), 2)


class ModelUsage:
    OPERATIONS = ("model_temperatures", "model_temperature_set", "local_last_request")

    def __init__(self, bridge_dir, distro=None, *, runner=subprocess.run):
        self._bridge_dir = Path(bridge_dir) if bridge_dir else None
        self._distro = distro
        self._runner = runner

    def _run(self, script, args, limit):
        if self._bridge_dir is None:
            raise ValueError("WORKBENCH_USAGE_UNAVAILABLE")
        argv = ["wsl.exe"] + (["-d", self._distro] if self._distro else [])
        # The relay imports leo_reasoning from its own folder (as when Leo starts it), so it is not run
        # isolated; leo_reasoning needs only the standard library.
        flags = ["-B"] if script == "leo_local_relay.py" else ["-I", "-B"]
        argv += ["-e", "/usr/bin/python3", *flags, windows_path_to_wsl(self._bridge_dir / script)] + list(args)
        try:
            completed = self._runner(argv, capture_output=True, timeout=30, shell=False,
                                     creationflags=WslBridge._creationflags(), startupinfo=WslBridge._startupinfo())
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError("WORKBENCH_USAGE_UNAVAILABLE") from None
        stdout = completed.stdout if isinstance(completed.stdout, bytes) else b""
        if len(stdout) > limit:
            raise ValueError("WORKBENCH_USAGE_UNAVAILABLE")
        lines = [line for line in stdout.decode("utf-8", "replace").splitlines() if line.strip()]
        try:
            payload = json.loads(lines[-1])
        except (IndexError, ValueError):
            raise ValueError("WORKBENCH_USAGE_UNAVAILABLE") from None
        if not isinstance(payload, dict) or payload.get("ok") is not True or not isinstance(payload.get("data"), dict):
            raise ValueError("WORKBENCH_USAGE_UNAVAILABLE")
        return payload["data"]

    def handle(self, payload):
        op = payload.get("operation")
        if op == "model_temperatures":
            return self._shape_temperatures(self._run("leo_reasoning.py", ["temperatures"], 65536))
        if op == "model_temperature_set":
            model, value = _model(payload.get("model")), _temperature(payload.get("value"))
            args = ["clear-temperature", model] if value is None else ["set-temperature", model, repr(value)]
            return self._shape_temperatures(self._run("leo_reasoning.py", args, 65536))
        return {"request": self._shape_request(
            self._run("leo_local_relay.py", ["last-request"], 2_000_000).get("request"),
            payload.get("promptTokens"))}

    @staticmethod
    def _shape_temperatures(data):
        raw = data.get("temperatures") if isinstance(data.get("temperatures"), dict) else {}
        temperatures = {}
        for model, value in raw.items():
            try:
                temperatures[_model(model)] = _temperature(value)
            except ValueError:
                continue
        default = data.get("default")
        return {"temperatures": temperatures,
                "default": default if type(default) in (int, float) and math.isfinite(default) else 0.7,
                "min": TEMPERATURE_MIN, "max": TEMPERATURE_MAX}

    @staticmethod
    def _shape_request(record, prompt_tokens=None):
        if not isinstance(record, dict) or not record:
            return None

        def count(value):
            return value if type(value) is int and value >= 0 else None
        parts = record.get("parts") if isinstance(record.get("parts"), dict) else {}
        recorded = count(record.get("prompt_tokens"))
        # The relay keeps one request for the whole process. The text is returned only
        # when this conversation's latest call has the same input size, so another
        # conversation's prompt is not shown here.
        same = (type(prompt_tokens) is int and recorded is not None
                and abs(recorded - prompt_tokens) <= 8)
        raw = record.get("text") if same and isinstance(record.get("text"), str) else ""
        text = raw[:400_000]
        return {"at": count(record.get("at")), "context": count(record.get("context")),
                "promptTokens": recorded, "maxTokens": count(record.get("max_tokens")),
                "parts": {key: count(parts.get(key)) for key in ("system", "history", "question")},
                "text": text, "sameConversation": same,
                "truncated": bool(same and (record.get("truncated") is True or len(raw) > 400_000))}
