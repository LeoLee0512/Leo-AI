"""Audited, request-scoped reasoning capabilities. No credentials or network.

DeepSeek: https://api-docs.deepseek.com/guides/thinking_mode/ (2026-09-09).
Local: llama.cpp 5266f24da, server-common.cpp request thinking_budget_tokens;
the installed Qwen3 template supports enable_thinking. Readiness is separate.
"""
from __future__ import annotations

import copy
import hashlib
import json
from urllib.parse import urlsplit

POLICY_VERSION = 1
CHOICES = ("default", "low", "mid", "high", "xhigh", "extra", "ultra")
LABELS = ("Default", "Low", "Mid", "High", "Xhigh", "Extra", "Ultra")
QWEN_BUDGETS = dict(zip(CHOICES[1:], (128, 256, 512, 1024, 2048, 4096)))
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
            if family == "qwen3_llamacpp":
                available, value = True, QWEN_BUDGETS[choice]
                semantics = (f"Thinking budget {value} tokens per thinking block; forced closing/UTF-8 overhead may occur. "
                             "Total generated tokens are bounded separately; no length or accuracy guarantee.")
            elif family == "deepseek_v4" and choice in DEEPSEEK_LEVELS:
                available, value = True, DEEPSEEK_LEVELS[choice]
                semantics = f"DeepSeek native reasoning_effort={value}; thinking enabled."
            elif family == "deepseek_v4":
                semantics = "DeepSeek exposes only low/high/max; this label does not represent another native strength."
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
    return result
