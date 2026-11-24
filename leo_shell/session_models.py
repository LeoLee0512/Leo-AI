"""Native profile selection without daemon restart or secrets in browser state.

The encrypted mapping is the ownership ledger for profiles created by this
service. Existing upstream profiles are never adopted by model-name matching.
"""
from __future__ import annotations

import atexit
import base64
import hashlib
import json
import logging
import os
import re
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_MAGIC = b"LEOSESSIONMAP1\n"
_MAX_BYTES = 2 * 1024 * 1024


class SessionModelError(ValueError):
    def __init__(self, code: str, status: int = 400, binding: dict | None = None):
        super().__init__(code)
        self.code, self.status, self.binding = code, status, binding

    def response(self) -> dict:
        result = {"ok": False, "message": self.code, "code": self.code, "status": self.status}
        if self.binding is not None:
            result["binding"] = self.binding
        return result


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise SessionModelError("MODEL_SELECTION_INVALID")
    return value


def _binding(value: Any) -> dict:
    if not isinstance(value, dict):
        raise SessionModelError("MODEL_BINDING_INVALID")
    profile = value.get("profile_id")
    revision = value.get("revision")
    if type(profile) is not str or type(revision) is not int or revision < 0 or bool(profile) != (revision > 0):
        raise SessionModelError("MODEL_BINDING_INVALID")
    if profile:
        _identifier(profile)
    return {"profile_id": profile, "revision": revision}


def _endpoint(value: str) -> str:
    try:
        parts = urlsplit(value.strip())
        if (parts.scheme not in {"https", "http"} or not parts.hostname
                or parts.username is not None or parts.password is not None or parts.query or parts.fragment):
            raise ValueError
        host = parts.hostname + (":" + str(parts.port) if parts.port else "")
        return urlunsplit((parts.scheme, host, parts.path.rstrip("/"), "", ""))
    except ValueError:
        raise SessionModelError("MODEL_ENDPOINT_INVALID") from None


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LocalDaemonTransport:
    """Only authenticated fixed-loopback requests; never log request payloads."""
    def __init__(self, client_url, *, opener=None):
        self._client_url = client_url
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        from .bridge_client import WslBridge
        url = self._client_url()
        if not WslBridge._is_valid_client_url(url):
            raise SessionModelError("MODEL_RUNTIME_UNAVAILABLE", 503)
        parts = urlsplit(url)
        tokens = parse_qs(parts.query, keep_blank_values=True).get("token", [])
        if len(tokens) != 1 or not tokens[0] or any(ord(c) < 33 for c in tokens[0]):
            raise SessionModelError("MODEL_RUNTIME_AUTH_UNAVAILABLE", 503)
        if not re.fullmatch(r"/api/v1/(?:frames/[A-Za-z0-9_-]+(?:/model-binding)?|model-profiles(?:/[A-Za-z0-9_-]+)?)", path):
            raise SessionModelError("MODEL_SELECTION_INVALID")
        headers = {"Authorization": "Bearer " + tokens[0], "Accept": "application/json"}
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(f"http://{parts.netloc}{path}", data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read(_MAX_BYTES + 1)
        except HTTPError as error:
            status = error.code
            code = None
            if status == 409:
                try:
                    body = json.loads(error.read(4097))
                    if body.get("code") in {"MODEL_REGISTRATION_EXISTS", "MODEL_REGISTRATION_ID_CONFLICT"}:
                        code = body["code"]
                except Exception:
                    pass
            # Do not reflect provider/internal error bodies into the browser.
            raise SessionModelError(
                code or "MODEL_BINDING_CONFLICT" if status == 409 else
                "MODEL_PROFILE_NOT_FOUND" if status == 404 else "MODEL_RUNTIME_REQUEST_FAILED", status
            ) from None
        except Exception:
            raise SessionModelError("MODEL_RUNTIME_UNAVAILABLE", 503) from None
        if len(raw) > _MAX_BYTES:
            raise SessionModelError("MODEL_RUNTIME_RESPONSE_INVALID", 502)
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise SessionModelError("MODEL_RUNTIME_RESPONSE_INVALID", 502) from None
        if not isinstance(value, dict):
            raise SessionModelError("MODEL_RUNTIME_RESPONSE_INVALID", 502)
        return value


class SessionModelService:
    def __init__(self, settings, paths, coordinator, *, transport=None, protect=None,
                 unprotect=None, local_factory=None, reasoning_describe=None):
        from .secrets_store import _protect, _unprotect
        self._settings, self._paths, self._coordinator = settings, paths, coordinator
        self._transport = transport
        self._protect, self._unprotect = protect or _protect, unprotect or _unprotect
        self._local_factory, self._describe = local_factory, reasoning_describe
        self._path = Path(paths.user) / "session-model-bindings.dpapi"
        self._lock = threading.RLock()
        self._local = None
        self._local_configuration = None
        self._local_identity = None
        self._closed = False
        atexit.register(self.close)

    def _client(self):
        if self._transport is None:
            bridge = getattr(self._coordinator, "_bridge", None)
            if bridge is None:
                raise SessionModelError("MODEL_RUNTIME_UNAVAILABLE", 503)
            self._transport = LocalDaemonTransport(bridge.client_url)
        return self._transport

    def _runtime_allowed(self) -> None:
        state = self._coordinator.runtime_state()
        if (self._closed or not isinstance(state, dict) or state.get("status") != "ready"
                or state.get("mode") not in {"cloud", "local"}):
            raise SessionModelError("MODEL_CONNECT_BEFORE_SELECTION", 409)

    def _read(self) -> dict:
        if not self._path.exists():
            return {"version": 1, "entries": {}, "managed": {}, "revoking": [], "pending": {}}
        try:
            if self._path.is_symlink() or self._path.stat().st_size > _MAX_BYTES:
                raise ValueError
            raw = self._path.read_bytes()
            if not raw.startswith(_MAGIC):
                raise ValueError
            value = json.loads(self._unprotect(base64.b64decode(raw[len(_MAGIC):], validate=True)))
            if (not isinstance(value, dict) or type(value.get("version")) is not int or value.get("version") != 1
                    or not isinstance(value.get("entries"), dict)
                    or not isinstance(value.get("managed"), dict)
                    or not isinstance(value.get("revoking"), list)):
                raise ValueError
            for native, ids in value["managed"].items():
                _identifier(native)
                if not isinstance(ids, list):
                    raise ValueError
                for item in ids:
                    _identifier(item)
            for native, entry in value["entries"].items():
                _identifier(native)
                if not isinstance(entry, dict) or not re.fullmatch(r"[0-9a-f]{64}", entry.get("fingerprint", "")):
                    raise ValueError
                _binding(entry)
                if entry["profile_id"] not in value["managed"].get(native, []):
                    raise ValueError
                identity = entry.get("identity")
                if (not isinstance(identity, dict) or set(identity) != {"provider", "model", "base_url"}
                        or any(type(v) is not str for v in identity.values())):
                    raise ValueError
            for native in value["revoking"]:
                _identifier(native)
            pending = value.setdefault("pending", {})
            if not isinstance(pending, dict):
                raise ValueError
            for native, item in pending.items():
                _identifier(native)
                if (not isinstance(item, dict) or not re.fullmatch(r"mp-leo-[0-9a-f]{32}", item.get("profile_id", ""))
                        or item["profile_id"] not in value["managed"].get(native, [])
                        or not re.fullmatch(r"[0-9a-f]{64}", item.get("fingerprint", ""))):
                    raise ValueError
            return value
        except Exception:
            raise SessionModelError("MODEL_MAPPING_UNAVAILABLE", 503) from None

    def _write(self, value: dict) -> None:
        plain = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
        encoded = _MAGIC + base64.b64encode(self._protect(plain))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.is_symlink():
            raise SessionModelError("MODEL_MAPPING_UNAVAILABLE", 503)
        fd, temporary = tempfile.mkstemp(prefix=".session-model-", suffix=".tmp", dir=self._path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _profiles(self) -> list[dict]:
        from .settings_store import PRESETS
        by_preset = {item["id"]: item for item in PRESETS}
        value = self._settings.state_for_shell()
        if not isinstance(value, dict) or not isinstance(value.get("profiles"), list):
            raise SessionModelError("MODEL_SETTINGS_UNAVAILABLE", 503)
        profiles = []
        for source in value["profiles"]:
            if not isinstance(source, dict) or source.get("preset") not in by_preset:
                raise SessionModelError("MODEL_SETTINGS_INVALID")
            preset = by_preset[source["preset"]]
            profiles.append({"id": _identifier(source.get("id")), "name": str(source.get("name") or ""),
                "provider": preset["provider"], "model": str(source.get("model") or ""),
                "base_url": _endpoint(str(source.get("base_url") or "")),
                "local": preset.get("requires_key") is False, "has_key": source.get("has_key") is True})
        return profiles

    def _public_binding(self, frame_id: str, document: dict) -> dict:
        frame = self._client().request("GET", "/api/v1/frames/" + quote(frame_id) + "/model-binding")
        if frame.get("ok") is not True or frame.get("frame_id") != frame_id:
            raise SessionModelError("MODEL_SESSION_NOT_FOUND", 404)
        binding = _binding(frame.get("binding"))
        binding["native_profile_id"] = next((native for native, ids in document["managed"].items()
                                             if binding["profile_id"] in ids), None)
        binding["reasoning"] = frame.get("reasoning")
        binding["credential_ready"] = frame.get("credential_ready") is True
        return binding

    def list(self, payload: Any) -> dict:
        if not isinstance(payload, dict):
            raise SessionModelError("MODEL_SELECTION_INVALID")
        frame_id = _identifier(payload.get("frame_id"))
        with self._lock:
            document = self._read()
            binding = self._public_binding(frame_id, document)
            models = []
            if self._describe is None:
                from bridge.leo_reasoning import describe
                self._describe = describe
            for profile in self._profiles():
                allowed = profile["local"] or profile["has_key"]
                model = {key: profile[key] for key in ("id", "name", "provider", "model", "has_key", "local")}
                model["available"] = allowed and profile["id"] not in document["revoking"]
                identity = {"provider": "chatgpt" if profile["local"] else profile["provider"],
                            "model": profile["model"], "base_url": profile["base_url"]}
                entry = document["entries"].get(profile["id"])
                if profile["local"] and entry and isinstance(entry.get("identity"), dict):
                    identity = entry["identity"]
                model["reasoning"] = self._describe(**identity)
                models.append(model)
            state = self._settings.state_for_shell()
            active = state.get("active_profile_id")
            if active not in {item["id"] for item in models}:
                active = None
            return {"ok": True, "frame_id": frame_id, "binding": binding, "models": models,
                    "active_native_profile_id": active}

    def select(self, payload: Any) -> dict:
        if not isinstance(payload, dict):
            raise SessionModelError("MODEL_SELECTION_INVALID")
        frame_id, native_id = _identifier(payload.get("frame_id")), _identifier(payload.get("native_profile_id"))
        expected = _binding(payload.get("expected_binding"))
        with self._lock:
            self._runtime_allowed()
            document = self._read()
            if native_id in document["revoking"]:
                raise SessionModelError("MODEL_PROFILE_REVOKING", 409)
            current = self._public_binding(frame_id, document)
            if _binding(current) != expected:
                raise SessionModelError("MODEL_BINDING_CONFLICT", 409, current)
            profile = next((p for p in self._profiles() if p["id"] == native_id), None)
            if profile is None:
                raise SessionModelError("MODEL_PROFILE_NOT_FOUND", 404)
            key = None
            try:
                if profile["local"]:
                    if self._local is None:
                        from .local_model import LocalModelSession
                        self._local = (self._local_factory or LocalModelSession)(self._paths)
                    if self._local_configuration is None:
                        self._local_configuration = self._local.start()
                        self._local_identity = self._local._inspect_model()
                    else:
                        identity = self._local._inspect_model()
                        if not self._local._same_identity(self._local_identity, identity):
                            raise SessionModelError("LOCAL_MODEL_IDENTITY_CHANGED", 409)
                        self._local._verify_health(identity)
                        relay = getattr(self._local, "_relay", None)
                        if relay is None or relay.poll() is not None:
                            raise SessionModelError("LOCAL_RELAY_UNAVAILABLE", 503)
                    endpoint, key = self._local_configuration
                    effective = {"provider": "chatgpt", "model": profile["model"], "base_url": endpoint}
                else:
                    key = self._settings.api_key_for(native_id)
                    if not isinstance(key, str) or not key.strip():
                        raise SessionModelError("MODEL_KEY_UNAVAILABLE", 409)
                    effective = {k: profile[k] for k in ("provider", "model", "base_url")}
                fingerprint = hashlib.sha256(json.dumps({**effective, "credential": key}, sort_keys=True,
                    ensure_ascii=False).encode("utf-8")).hexdigest()
                entry = document["entries"].get(native_id)
                if entry and entry["fingerprint"] == fingerprint:
                    try:
                        public = self._client().request("GET", "/api/v1/model-profiles/" + entry["profile_id"])
                        if (public.get("id") != entry["profile_id"] or public.get("revision") != entry["revision"]
                                or any(public.get(k) != v for k, v in effective.items())):
                            entry = None
                        elif public.get("has_api_key") is not True:
                            # The daemon's managed credential transport is
                            # process-only. Re-inject the exact saved operation
                            # after restart instead of inventing a new profile.
                            document["pending"][native_id] = {"profile_id": entry["profile_id"], "fingerprint": fingerprint}
                            self._write(document)
                            entry = None
                    except SessionModelError as error:
                        if error.status != 404:
                            raise
                        entry = None
                else:
                    entry = None
                if entry is None:
                    intent = document["pending"].get(native_id)
                    if intent is None:
                        intent = {"profile_id": "mp-leo-" + uuid.uuid4().hex, "fingerprint": fingerprint}
                        document["managed"].setdefault(native_id, []).append(intent["profile_id"])
                        document["pending"][native_id] = intent
                        # Ownership and retry identity MUST be durable before
                        # any remote write. No credential is in this intent.
                        self._write(document)
                    elif intent["fingerprint"] != fingerprint:
                        raise SessionModelError("MODEL_REGISTRATION_PENDING", 409)
                    try:
                        public = self._client().request("POST", "/api/v1/model-profiles",
                            {**effective, "name": profile["name"], "api_key": key,
                             "leo_registration_id": intent["profile_id"], "leo_native_profile_id": native_id})
                    except SessionModelError as error:
                        if error.code != "MODEL_REGISTRATION_EXISTS":
                            raise
                        # Server returns this code only for this exact prior
                        # operation and credential. An arbitrary 409 is failure.
                        public = self._client().request("GET", "/api/v1/model-profiles/" + intent["profile_id"])
                    if (public.get("id") != intent["profile_id"] or public.get("has_api_key") is not True
                            or any(public.get(k) != v for k, v in effective.items())):
                        raise SessionModelError("MODEL_REGISTRATION_UNCONFIRMED", 502)
                    entry = {**_binding({"profile_id": public.get("id"), "revision": public.get("revision")}),
                             "fingerprint": fingerprint, "identity": effective}
                    document["entries"][native_id] = entry
                    document["pending"].pop(native_id)
                    try:
                        self._write(document)
                    except Exception:
                        # The original intent is still durable. A new process
                        # retries the same ID or explicitly revokes that ID.
                        raise SessionModelError("MODEL_MAPPING_UNAVAILABLE", 503) from None
                try:
                    result = self._client().request("POST", "/api/v1/frames/" + frame_id + "/model-binding",
                        {"profile_id": entry["profile_id"], "revision": entry["revision"], "expected_binding": expected})
                except SessionModelError as error:
                    if error.status == 409:
                        raise SessionModelError("MODEL_BINDING_CONFLICT", 409,
                                                self._public_binding(frame_id, document)) from None
                    raise
                binding = _binding(result.get("binding"))
                if result.get("ok") is not True or binding != _binding(entry):
                    raise SessionModelError("MODEL_BINDING_UNCONFIRMED", 502)
                if self._describe is None:
                    from bridge.leo_reasoning import describe
                    self._describe = describe
                descriptor = self._describe(**effective)
                return {"ok": True, "frame_id": frame_id, "binding": {**binding, "native_profile_id": native_id,
                        "reasoning": descriptor, "credential_ready": True}, "reasoning": descriptor,
                        "applies_to": "next_unadmitted_turn"}
            finally:
                key = None

    def revoke(self, native_id: str) -> None:
        """Revoke only this service's copies before deleting a native profile."""
        native_id = _identifier(native_id)
        with self._lock:
            document = self._read()
            managed = document["managed"].get(native_id, [])
            if not managed:
                return
            if native_id not in document["revoking"]:
                document["revoking"].append(native_id)
                self._write(document)
            for profile_id in list(managed):
                try:
                    receipt = self._client().request("DELETE", "/api/v1/model-profiles/" + profile_id)
                    if receipt.get("ok") is not True:
                        raise SessionModelError("MODEL_REVOCATION_PENDING", 503)
                except SessionModelError as error:
                    # The managed runtime returns an explicit success receipt
                    # for a known intent with no remote registration. A bare
                    # 404 may instead mean an unavailable/unauthorized route.
                    raise SessionModelError("MODEL_REVOCATION_PENDING", 503) from None
                managed.remove(profile_id)
                if document["pending"].get(native_id, {}).get("profile_id") == profile_id:
                    document["pending"].pop(native_id, None)
                if document["entries"].get(native_id, {}).get("profile_id") == profile_id:
                    document["entries"].pop(native_id, None)
                self._write(document)
            document["entries"].pop(native_id, None)
            document["pending"].pop(native_id, None)
            document["managed"].pop(native_id, None)
            document["revoking"].remove(native_id)
            self._write(document)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            local, self._local = self._local, None
            if local is not None:
                try:
                    local.stop()
                except Exception:
                    logging.getLogger(__name__).error("LOCAL_SESSION_CLEANUP_FAILED")
