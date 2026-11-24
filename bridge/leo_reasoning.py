"""Audited, request-scoped reasoning capabilities. No credentials or network.

DeepSeek: https://api-docs.deepseek.com/guides/thinking_mode/ (2026-09-09).
Local: llama.cpp 5266f24da, server-common.cpp request thinking_budget_tokens;
the installed Qwen3 template supports enable_thinking. Readiness is separate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

POLICY_VERSION = 1
CHOICES = ("default", "low", "mid", "high", "xhigh", "extra", "ultra")
LABELS = ("Default", "Low", "Mid", "High", "Xhigh", "Extra", "Ultra")
# 3.2.6 · The local model offers the same levels as DeepSeek (owner, 2026-09-30): low / high / ultra,
# as thinking budgets in tokens. The other choice ids stay defined but unavailable.
QWEN_BUDGETS = {"low": 256, "high": 1024, "ultra": 4096}
DEEPSEEK_LEVELS = {"low": "low", "high": "high", "ultra": "max"}
DEEPSEEK_MODELS = frozenset({"deepseek-v4-flash", "deepseek-v4-pro"})


class ReasoningError(ValueError):
    """Stable public code; never echo arbitrary endpoints or credentials."""

    def __init__(self, code: str):
        self.code = self.error_code = code
        self.status = 400
        self.retryable = False
        super().__init__(code)


def _identity(provider: str, model: str, base_url: str) -> tuple[str, str, str, str]:
    if any(type(value) is not str or len(value) > 4096 for value in (provider, model, base_url)):
        raise ReasoningError("REASONING_IDENTITY_INVALID")
    provider, model = provider.strip().lower(), model.strip()
    if not provider or not model or any(ord(c) < 32 for c in provider + model + base_url):
        raise ReasoningError("REASONING_IDENTITY_INVALID")
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError:
        raise ReasoningError("REASONING_ENDPOINT_INVALID") from None
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        raise ReasoningError("REASONING_ENDPOINT_INVALID")
    path = parsed.path.rstrip("/")
    host = parsed.hostname.lower()
    endpoint = f"{parsed.scheme}://{host}:{port or (443 if parsed.scheme == 'https' else 80)}{path}"
    family = "provider_default"
    if (provider in {"chatgpt", "openai", "deepseek"} and host == "api.deepseek.com"
            and parsed.scheme == "https" and port in {None, 443}
            and path in {"", "/v1"} and model in DEEPSEEK_MODELS):
        family = "deepseek_v4"
    elif (provider in {"chatgpt", "openai", "local", "llamacpp"} and model == "local-qwen3-4b"
          and parsed.scheme == "http" and host == "127.0.0.1"
          and port is not None and 1 <= port <= 65535 and path == "/v1"):
        family = "qwen3_llamacpp"
    return provider, model, endpoint, family


def describe(provider: str, model: str, base_url: str) -> dict:
    provider, model, endpoint, family = _identity(provider, model, base_url)
    choices = []
    for choice, label in zip(CHOICES, LABELS):
        available, value = choice == "default", None
        semantics = "Provider default; no explicit reasoning override."
        if choice != "default":
            semantics = "This endpoint/model has no audited independent support for this choice."
            if family == "qwen3_llamacpp" and choice in QWEN_BUDGETS:
                available, value = True, QWEN_BUDGETS[choice]
                semantics = (f"Thinking budget {value} tokens per thinking block; forced closing/UTF-8 overhead may occur. "
                             "Total generated tokens are bounded separately; no length or accuracy guarantee.")
            elif family == "deepseek_v4" and choice in DEEPSEEK_LEVELS:
                available, value = True, DEEPSEEK_LEVELS[choice]
                semantics = f"DeepSeek native reasoning_effort={value}; thinking enabled."
            elif family == "deepseek_v4":
                semantics = "DeepSeek exposes only low/high/max; this label does not represent another native strength."
            elif family == "qwen3_llamacpp":
                semantics = "The local model offers low/high/ultra, the same levels as DeepSeek."
        elif family == "qwen3_llamacpp":
            semantics = "Existing local default: thinking disabled; ordinary output budget remains separate."
        elif family == "deepseek_v4":
            semantics = "DeepSeek provider default: thinking enabled with native high; no explicit override."
        choices.append({"id": choice, "label": label, "available": available,
                        "semantics": semantics, "native_value": value})
    contract = {"policy_version": POLICY_VERSION, "provider": provider, "model": model,
                "endpoint": endpoint, "family": family, "choices": choices}
    revision = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True).encode("utf-8")).hexdigest()
    # No endpoint is returned; identity is bound by the revision without
    # exposing arbitrary endpoint strings in API responses or diagnostics.
    return {"revision": revision, "family": family, "choices": choices}


def resolve(provider: str, model: str, base_url: str, choice: str,
            capability_revision: str) -> dict:
    descriptor = describe(provider, model, base_url)
    if type(capability_revision) is not str or capability_revision != descriptor["revision"]:
        raise ReasoningError("REASONING_CAPABILITY_REVISION_MISMATCH")
    if type(choice) is not str or choice not in CHOICES:
        raise ReasoningError("REASONING_CHOICE_INVALID")
    selected = next(row for row in descriptor["choices"] if row["id"] == choice)
    if not selected["available"]:
        raise ReasoningError("REASONING_CHOICE_UNAVAILABLE")
    payload, remove_fields = {}, []
    if choice != "default" and descriptor["family"] == "qwen3_llamacpp":
        payload = {"chat_template_kwargs": {"enable_thinking": True},
                   "thinking_budget_tokens": selected["native_value"]}
        remove_fields = ["reasoning_effort", "reasoning_budget_tokens"]
    elif choice != "default" and descriptor["family"] == "deepseek_v4":
        payload = {"thinking": {"type": "enabled"}, "reasoning_effort": selected["native_value"]}
    return {"choice": choice, "capability_revision": descriptor["revision"],
            "family": descriptor["family"], "semantics": selected["semantics"],
            "native_value": selected["native_value"], "payload": payload, "remove_fields": remove_fields}


def validate_snapshot(provider: str, model: str, base_url: str, snapshot: dict) -> dict:
    if type(snapshot) is not dict:
        raise ReasoningError("REASONING_SNAPSHOT_INVALID")
    expected = resolve(provider, model, base_url, snapshot.get("choice"),
                       snapshot.get("capability_revision"))
    # JSON comparison is type strict (True must not pass as integer 1).
    try:
        same = (json.dumps(snapshot, sort_keys=True, allow_nan=False)
                == json.dumps(expected, sort_keys=True, allow_nan=False))
    except (TypeError, ValueError):
        same = False
    if not same:
        raise ReasoningError("REASONING_SNAPSHOT_MISMATCH")
    return copy.deepcopy(expected)


def apply_request(payload: dict, cfg, base: str, model: str) -> dict:
    """Consume the admission snapshot; internal callers use audited default.

    This never consults process-global reasoning effort and never places the
    capability snapshot or provider credentials into the model payload.
    """
    snapshot = getattr(cfg, "reasoning_snapshot", None)
    if snapshot is None:
        choice = getattr(cfg, "reasoning_choice", "default")
        revision = getattr(cfg, "reasoning_capability_revision", None)
        if revision is None and choice == "default":
            revision = describe(cfg.provider, model, base)["revision"]
        snapshot = resolve(cfg.provider, model, base, choice, revision)
    else:
        snapshot = validate_snapshot(cfg.provider, model, base, snapshot)
        if (getattr(cfg, "reasoning_choice", "default") != snapshot["choice"]
                or getattr(cfg, "reasoning_capability_revision", None) != snapshot["capability_revision"]):
            raise ReasoningError("REASONING_SNAPSHOT_MISMATCH")
    result = copy.deepcopy(payload)
    for field in snapshot["remove_fields"]:
        result.pop(field, None)
    result.update(copy.deepcopy(snapshot["payload"]))
    if snapshot["family"] == "qwen3_llamacpp":
        # The local relay revalidates this choice using the same policy. Its
        # Windows endpoint differs from the daemon-side relay endpoint, so a
        # second endpoint revision must not masquerade as the admitted one.
        result["leo_reasoning_level"] = snapshot["choice"]
    # 3.2.11 · A temperature the person set for this model replaces only the daemon's default one;
    # callers that ask for their own (titles 0.3, compaction 0.2) keep it.
    chosen = model_temperature(model)
    if chosen is not None and "temperature" in result and result["temperature"] == getattr(cfg, "temperature", None):
        result["temperature"] = chosen
    return result


# 3.2.11 · Temperature per model, set from Leo's 「用量」 panel (owner, 2026-09-30). The daemon has one
# global temperature (OPENAI4S_LLM_TEMPERATURE, default 0.7); every chat request passes apply_request,
# so a small file next to the daemon's data holds the per-model values. A missing or unreadable file
# means "use the default"; it never blocks a request.
TEMPERATURE_FILE = "leo-model-temperatures.json"
DEFAULT_TEMPERATURE = 0.7
TEMPERATURE_MIN, TEMPERATURE_MAX = 0.0, 1.5


def _temperature_path() -> Path:
    data = os.environ.get("OPENAI4S_DATA_DIR") or str(Path.home() / ".local/share/leo-ai-studio/data")
    return Path(data) / TEMPERATURE_FILE


def _valid_model(model: object) -> bool:
    return type(model) is str and 0 < len(model) <= 200 and not any(ord(c) < 32 for c in model)


def _valid_temperature(value: object) -> bool:
    return (type(value) in (int, float) and math.isfinite(value)
            and TEMPERATURE_MIN <= value <= TEMPERATURE_MAX)


def model_temperatures() -> dict:
    try:
        data = json.loads(_temperature_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    models = data.get("models") if isinstance(data, dict) and data.get("version") == 1 else None
    if not isinstance(models, dict):
        return {}
    return {model: float(value) for model, value in models.items()
            if _valid_model(model) and _valid_temperature(value)}


def model_temperature(model: str) -> float | None:
    return model_temperatures().get(model)


def set_model_temperature(model: str, value: float | None) -> dict:
    """Set (or with None, clear) one model's temperature; the file is replaced atomically."""
    if not _valid_model(model) or (value is not None and not _valid_temperature(value)):
        raise ReasoningError("TEMPERATURE_INVALID")
    models = model_temperatures()
    if value is None:
        models.pop(model, None)
    else:
        models[model] = round(float(value), 2)
    path = _temperature_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".leo-temperatures-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"version": 1, "models": models}, handle, sort_keys=True)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return models


def main(argv=None) -> int:
    """``temperatures`` | ``set-temperature MODEL VALUE`` | ``clear-temperature MODEL`` (run by Leo in WSL)."""
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args == ["temperatures"]:
            models = model_temperatures()
        elif len(args) == 3 and args[0] == "set-temperature":
            try:
                value = float(args[2])
            except ValueError:
                raise ReasoningError("TEMPERATURE_INVALID") from None
            models = set_model_temperature(args[1], value)
        elif len(args) == 2 and args[0] == "clear-temperature":
            models = set_model_temperature(args[1], None)
        else:
            raise ReasoningError("TEMPERATURE_COMMAND_INVALID")
    except (ReasoningError, OSError) as exc:
        code = exc.code if isinstance(exc, ReasoningError) else "TEMPERATURE_STORE_UNAVAILABLE"
        print(json.dumps({"ok": False, "error": {"code": code, "message": "Model temperature was not changed."}}))
        return 1
    print(json.dumps({"ok": True, "data": {"temperatures": models, "default": DEFAULT_TEMPERATURE,
                                           "range": [TEMPERATURE_MIN, TEMPERATURE_MAX]}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
