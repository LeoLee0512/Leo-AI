"""Installed as openai4s.server.leo_turn_binding; no startup mutations."""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
import threading
from dataclasses import replace

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


class TurnBindingError(ValueError):
    def __init__(self, code, status=400, binding=None):
        super().__init__(code)
        self.code, self.status, self.binding = code, status, binding
        self.error_code = code

    def response(self):
        result = {"ok": False, "code": self.code, "message": self.code, "status": self.status}
        if self.binding is not None:
            result["binding"] = self.binding
        return result


class ManagedSecretBroker:
    """Process-only native credentials; all other secrets keep their backend.

    The installed daemon deliberately uses a read-only environment broker.
    Managed credentials therefore need explicit re-injection after restart;
    they never become environment variables or plaintext database values.
    """
    def __init__(self, delegate):
        self._delegate = delegate
        self._namespace = delegate.namespace
        self._lock = threading.RLock()
        self._allowed = set()
        self._values = {}

    def __getattr__(self, name):
        return getattr(self._delegate, name)

    def _managed(self, ref):
        from openai4s.security.secret_broker import parse_ref
        version, namespace, scope, name = parse_ref(ref)
        return version == 2 and namespace == self._namespace and scope == "model_profile" and re.fullmatch(r"mp-leo-[0-9a-f]{32}", name)

    def authorize(self, ref):
        if not self._managed(ref):
            raise TurnBindingError("MODEL_REGISTRATION_JOURNAL_INVALID", 503)
        with self._lock:
            self._allowed.add(ref)

    def put(self, scope, name, secret):
        from openai4s.security.secret_broker import make_ref
        ref = make_ref(scope, name, self._namespace)
        if not self._managed(ref):
            return self._delegate.put(scope, name, secret)
        with self._lock:
            if (ref not in self._allowed or type(secret) is not str or not secret
                    or (ref in self._values and self._values[ref] != secret)):
                raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
            self._values[ref] = secret
        return ref

    def get(self, ref):
        if not self._managed(ref):
            return self._delegate.get(ref)
        with self._lock:
            return self._values.get(ref)

    def delete(self, ref):
        if not self._managed(ref):
            return self._delegate.delete(ref)
        with self._lock:
            self._values.pop(ref, None)
            self._allowed.discard(ref)

    def describe(self, ref):
        if not self._managed(ref):
            return self._delegate.describe(ref)
        from openai4s.security.secret_broker import parse_ref
        _, _, scope, name = parse_ref(ref)
        configured = self.get(ref) is not None
        return {"ref": ref, "scope": scope, "name": name, "configured": configured,
                "backend": "leo-native-process", "persistent": False, "reentry_required": not configured}


def _managed_broker(store):
    with store._lock:
        broker = store.secrets
        if not isinstance(broker, ManagedSecretBroker):
            broker = ManagedSecretBroker(broker)
            store._secret_broker = broker
        return broker


def _credential_digest(profile_id, credential):
    return hmac.new(credential.encode("utf-8"), ("leo-registration-v1:" + profile_id).encode("ascii"), hashlib.sha256).hexdigest()


def binding(value):
    if not isinstance(value, dict):
        raise TurnBindingError("MODEL_BINDING_INVALID")
    identity, revision = value.get("profile_id"), value.get("revision")
    if (type(identity) is not str or type(revision) is not int or revision < 0
            or bool(identity) != (revision > 0) or (identity and not _ID.fullmatch(identity))):
        raise TurnBindingError("MODEL_BINDING_INVALID")
    return {"profile_id": identity, "revision": revision}


def _profile(store, pair):
    from openai4s.server.model_profiles import ModelProfileService
    matching = [p for p in store.list_model_profiles() if p.get("id") == pair["profile_id"]]
    if len(matching) != 1 or matching[0].get("deleted_at"):
        raise TurnBindingError("MODEL_REVISION_UNAVAILABLE", 409)
    profile = matching[0]
    try:
        recorded = ModelProfileService.revision_config(profile, pair["revision"])
    except (TypeError, ValueError):
        recorded = None
    if recorded is None:
        raise TurnBindingError("MODEL_REVISION_UNAVAILABLE", 409)
    _validate_managed_identity(store, profile, recorded)
    return profile, recorded


def _identity(recorded):
    return {name: str(recorded.get(name) or "") for name in ("provider", "model", "base_url")}


def _service(store, cfg):
    from openai4s.server.model_profiles import ModelProfileService
    from openai4s.llm import PROVIDERS
    return ModelProfileService(store, cfg, providers=lambda: PROVIDERS)


def _registration(store, profile_id):
    if not isinstance(profile_id, str) or not re.fullmatch(r"mp-leo-[0-9a-f]{32}", profile_id):
        raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
    key = "leo_model_registration." + profile_id
    raw = store.get_setting(key)
    if not raw:
        return key, None
    try:
        from openai4s.security.secret_broker import make_ref
        item = json.loads(raw)
        namespace = store.secrets.namespace
        if (type(item.get("version")) is not int or item.get("version") != 1 or item.get("profile_id") != profile_id
                or not isinstance(item.get("native_id"), str) or not _ID.fullmatch(item["native_id"])
                or not isinstance(item.get("identity"), dict) or set(item["identity"]) != {"provider", "model", "base_url"}
                or any(type(v) is not str for v in item["identity"].values())
                or not namespace or item.get("secret_ref") != make_ref("model_profile", profile_id, namespace)
                or not isinstance(item.get("credential_digest"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", item["credential_digest"])
                or item.get("state") not in {"pending", "created", "revoking", "revoked"}):
            raise ValueError
    except (TypeError, ValueError, AttributeError):
        raise TurnBindingError("MODEL_REGISTRATION_JOURNAL_INVALID", 503) from None
    return key, item


def _validate_managed_identity(store, profile, recorded=None, *, deleting=False):
    """A managed ID cannot silently adopt another profile's credential ref."""
    profile_id = str(profile.get("id") or "")
    if not profile_id.startswith("mp-leo-"):
        return
    _, intent = _registration(store, profile_id)
    raw_ref = profile.get("api_key")
    permitted_ref = raw_ref == intent["secret_ref"] if intent else False
    if deleting and profile.get("deleted_at") and raw_ref == "":
        permitted_ref = True
    if (intent is None or not permitted_ref or _identity(profile) != intent["identity"]
            or (recorded is not None and _identity(recorded) != intent["identity"])
            or (not deleting and intent["state"] != "created")):
        raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
    if not deleting:
        from openai4s.server.model_profiles import resolve_profile_key
        credential = resolve_profile_key(store, profile)
        if credential and not hmac.compare_digest(intent["credential_digest"], _credential_digest(profile_id, credential)):
            raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)


def create_managed_profile(store, cfg, body):
    """Durable registration intent precedes broker writes; never overwrites."""
    from openai4s.endpoint_identity import normalize_endpoint
    from openai4s.security.secret_broker import make_ref
    from openai4s.server.model_profiles import ModelProfileService, clean_api_key
    from openai4s.llm import PROVIDERS
    if not isinstance(body, dict):
        raise TurnBindingError("MODEL_SELECTION_INVALID")
    profile_id, native_id = body.get("leo_registration_id"), body.get("leo_native_profile_id")
    if not isinstance(native_id, str) or not _ID.fullmatch(native_id):
        raise TurnBindingError("MODEL_SELECTION_INVALID")
    service = ModelProfileService(store, cfg, providers=lambda: PROVIDERS, id_factory=lambda: profile_id)
    identity = {"provider": str(body.get("provider") or ""), "model": str(body.get("model") or "").strip(),
                "base_url": normalize_endpoint(body.get("base_url"))}
    credential = clean_api_key(body.get("api_key"))
    if not credential:
        raise TurnBindingError("MODEL_KEY_UNAVAILABLE", 409)
    with store._lock:
        broker = _managed_broker(store)
        journal_key, intent = _registration(store, profile_id)
        existing = [p for p in store.list_model_profiles() if p.get("id") == profile_id]
        if intent is None:
            if existing:
                raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
            namespace = store.secrets.namespace
            if not namespace:
                raise TurnBindingError("MODEL_REGISTRATION_JOURNAL_INVALID", 503)
            intent = {"version": 1, "profile_id": profile_id, "native_id": native_id,
                      "identity": identity, "state": "pending",
                      "credential_digest": _credential_digest(profile_id, credential),
                      "secret_ref": make_ref("model_profile", profile_id, namespace)}
            store.set_setting(journal_key, json.dumps(intent, sort_keys=True))
        elif (intent.get("native_id") != native_id or intent.get("identity") != identity
              or not hmac.compare_digest(intent["credential_digest"], _credential_digest(profile_id, credential))
              or intent.get("state") in {"revoking", "revoked"}):
            raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
        broker.authorize(intent["secret_ref"])
        if existing:
            if (len(existing) != 1 or existing[0].get("deleted_at")
                    or _identity(existing[0]) != identity
                    or existing[0].get("api_key") != intent["secret_ref"]):
                raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
            # Exact operation+credential verifier allows process restart
            # recovery without changing profile or its immutable revision.
            broker.put("model_profile", profile_id, credential)
            if intent["state"] != "created":
                intent["state"] = "created"
                store.set_setting(journal_key, json.dumps(intent, sort_keys=True))
            raise TurnBindingError("MODEL_REGISTRATION_EXISTS", 409)
        # An earlier broker write may have succeeded before the profile write.
        # A retry must be byte-identical and may not replace its credential.
        prior = store.secrets.get(intent["secret_ref"])
        if prior and prior != credential:
            raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
        public = service.create(body)
        intent["state"] = "created"
        store.set_setting(journal_key, json.dumps(intent, sort_keys=True))
        return public


def delete_managed_profile(store, cfg, profile_id):
    with store._lock:
        _managed_broker(store)
        journal_key, intent = _registration(store, profile_id)
        existing = [p for p in store.list_model_profiles() if p.get("id") == profile_id]
        if intent is None:
            if existing:
                raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
            # The native intent was written but never reached this server.
            return
        if len(existing) > 1:
            raise TurnBindingError("MODEL_REGISTRATION_ID_CONFLICT", 409)
        if existing:
            # Generic deletion also deletes the reference in the profile row.
            # Refuse a corrupted row before that code can revoke another key.
            _validate_managed_identity(store, existing[0], deleting=True)
        intent["state"] = "revoking"
        store.set_setting(journal_key, json.dumps(intent, sort_keys=True))
        _service(store, cfg).delete(profile_id)
        # Existing deletion suppresses broker errors. Managed deletion verifies
        # revocation explicitly, including registration interrupted pre-profile.
        try:
            store.secrets.delete(intent["secret_ref"])
            if store.secrets.get(intent["secret_ref"]):
                raise ValueError
        except Exception:
            raise TurnBindingError("MODEL_REVOCATION_PENDING", 503) from None
        intent["state"] = "revoked"
        store.set_setting(journal_key, json.dumps(intent, sort_keys=True))


def public_binding(store, frame_id):
    frame = store.get_frame(frame_id)
    if frame is None or (frame.get("root_frame_id") or frame_id) != frame_id:
        raise TurnBindingError("MODEL_SESSION_NOT_FOUND", 404)
    pair = binding({"profile_id": frame.get("model_profile_id") or "",
                    "revision": frame.get("model_profile_revision") or 0})
    descriptor = None
    credential_ready = False
    if pair["profile_id"]:
        try:
            from openai4s.leo_reasoning import describe
            profile, recorded = _profile(store, pair)
            descriptor = describe(**_identity(recorded))
            from openai4s.server.model_profiles import resolve_profile_key
            credential_ready = bool(resolve_profile_key(store, profile))
        except (ValueError, TypeError):
            pass  # A stale pin remains visible; never substitute another one.
    return {"ok": True, "frame_id": frame_id, "binding": pair, "reasoning": descriptor,
            "credential_ready": credential_ready}


def rebind_frame(runner, store, frame_id, body):
    from openai4s.server.model_profiles import ModelProfileService
    if not isinstance(body, dict):
        raise TurnBindingError("MODEL_SELECTION_INVALID")
    target = binding({"profile_id": body.get("profile_id"), "revision": body.get("revision")})
    expected = binding(body.get("expected_binding"))
    if not target["profile_id"]:
        raise TurnBindingError("MODEL_SELECTION_INVALID")
    frame = store.get_frame(frame_id)
    if frame is None or (frame.get("root_frame_id") or frame_id) != frame_id:
        raise TurnBindingError("MODEL_SESSION_NOT_FOUND", 404)
    st = runner._state(frame_id, frame["project_id"])
    service = _service(store, runner.cfg)

    def validate(profile):
        if profile.get("deleted_at") or not service.resolve_key(profile):
            raise TurnBindingError("MODEL_REVISION_UNAVAILABLE", 409)
        recorded = ModelProfileService.revision_config(profile, target["revision"])
        if not recorded:
            raise TurnBindingError("MODEL_REVISION_UNAVAILABLE", 409)
        _validate_managed_identity(store, profile, recorded)
        return str(recorded.get("model") or "")

    # This is the same lock the queue owns while snapshot_factory executes.
    with st.admission_lock:
        try:
            store.leo_rebind_model(frame_id, target, expected, validate)
        except ValueError as error:
            if isinstance(error, TurnBindingError):
                raise
            code = str(error)
            if code == "MODEL_BINDING_CONFLICT":
                raise TurnBindingError(code, 409, public_binding(store, frame_id)["binding"]) from None
            raise TurnBindingError("MODEL_REVISION_UNAVAILABLE", 409) from None
    return {"ok": True, "frame_id": frame_id, "binding": target,
            "applies_to": "next_unadmitted_turn"}


def freeze_turn(runner, frame_id, selection=None, expected=None):
    """Called ONLY inside the existing admission lock, before queue submit."""
    from openai4s.leo_reasoning import describe, resolve
    controlled = selection is not None or expected is not None
    if controlled:
        if not isinstance(selection, dict) or expected is None:
            raise TurnBindingError("MODEL_SELECTION_INVALID")
        pair = public_binding(runner.store, frame_id)["binding"]
        if pair != binding(expected):
            raise TurnBindingError("MODEL_BINDING_CONFLICT", 409, pair)
        if not pair["profile_id"]:
            raise TurnBindingError("MODEL_SELECTION_REQUIRED", 409)
    else:
        frozen = runner.freeze_model_binding(frame_id)
        pair = binding({"profile_id": frozen["model_profile_id"], "revision": frozen["model_profile_revision"]})
    if not pair["profile_id"]:
        # Preserve legacy internal/CLI callers that intentionally have no pin.
        # New controlled Web requests may never enter this fallback.
        return {"binding": pair, "reasoning": None, "identity": None, "controlled": False}
    profile, recorded = _profile(runner.store, pair)
    from openai4s.server.model_profiles import ModelProfileService
    if not _service(runner.store, runner.cfg).resolve_key(profile):
        raise TurnBindingError("MODEL_REVISION_UNAVAILABLE", 409)
    identity = _identity(recorded)
    if selection is None:
        selection = {"choice": "default", "capability_revision": describe(**identity)["revision"]}
    if set(selection) != {"choice", "capability_revision"}:
        raise TurnBindingError("REASONING_SELECTION_INVALID")
    try:
        reasoning = resolve(**identity, choice=selection["choice"], capability_revision=selection["capability_revision"])
    except ValueError as error:
        code = getattr(error, "code", "REASONING_SELECTION_INVALID")
        raise TurnBindingError(code, 400) from None
    return {"binding": pair, "reasoning": reasoning, "identity": identity, "controlled": controlled}


def freeze_job(runner, job, selection, expected):
    snapshot = freeze_turn(runner, job.root_frame_id, selection, expected)
    job.model_profile_id = snapshot["binding"]["profile_id"]
    job.model_profile_revision = snapshot["binding"]["revision"]
    # Immutable serialized value; no nested mutable dict can alter the ticket.
    job.leo_turn_snapshot = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {"model_profile_id": job.model_profile_id, "model_profile_revision": job.model_profile_revision,
            "reasoning_snapshot": copy.deepcopy(snapshot["reasoning"])}


def install_turn(runner, st, frame_id, frozen_pair, encoded):
    if encoded is None:
        with st.admission_lock:
            snapshot = freeze_turn(runner, frame_id)
    else:
        try:
            snapshot = json.loads(encoded)
            pair = binding(snapshot["binding"])
            if (pair["profile_id"], pair["revision"]) != (frozen_pair or ("", 0)):
                raise ValueError
        except (ValueError, TypeError, KeyError):
            raise TurnBindingError("MODEL_SNAPSHOT_INVALID", 409) from None
    pair = snapshot["binding"]
    st.leo_turn_snapshot = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return (pair["profile_id"], pair["revision"]) if pair["profile_id"] else None


def apply_reasoning(cfg, st):
    encoded = getattr(st, "leo_turn_snapshot", None) if st is not None else None
    if encoded is None:
        return cfg
    snapshot = json.loads(encoded)
    reasoning = snapshot["reasoning"]
    if reasoning is None:
        return cfg
    identity = snapshot["identity"]
    if any(str(getattr(cfg, name, "") or "") != identity[name] for name in identity):
        raise TurnBindingError("MODEL_SNAPSHOT_MISMATCH", 409)
    from openai4s.leo_reasoning import validate_snapshot
    validated = validate_snapshot(**identity, snapshot=reasoning)
    return replace(cfg, reasoning_choice=validated["choice"],
                   reasoning_capability_revision=validated["capability_revision"], reasoning_snapshot=validated)


def effective_config(runner, st):
    encoded = getattr(st, "leo_turn_snapshot", None) if st is not None else None
    controlled = bool(encoded and json.loads(encoded).get("controlled") is True)
    if controlled:
        # Explicit native selection includes the credential. The legacy team
        # owner-key override must not silently substitute another credential.
        cfg = runner._pinned_llm_config(st)
        if cfg is None:
            raise TurnBindingError("MODEL_SNAPSHOT_MISMATCH", 409)
    else:
        cfg = runner._leo_original_llm_cfg(st)
    return apply_reasoning(cfg, st)


def validate_live_profile(runner, st):
    """Revocation prevents the next primary model dispatch, even within a turn."""
    encoded = getattr(st, "leo_turn_snapshot", None)
    if encoded is None:
        return
    snapshot = json.loads(encoded)
    if not snapshot["binding"]["profile_id"]:
        return
    profile, recorded = _profile(runner.store, snapshot["binding"])
    from openai4s.server.model_profiles import ModelProfileService
    if not _service(runner.store, runner.cfg).resolve_key(profile):
        raise TurnBindingError("MODEL_PROFILE_REVOKED", 409)
    if _identity(recorded) != snapshot["identity"]:
        raise TurnBindingError("MODEL_SNAPSHOT_MISMATCH", 409)


def record_snapshot(store, st, user_message, ledger, execution_id, user_group):
    encoded = getattr(st, "leo_turn_snapshot", None)
    if not encoded:
        return
    snapshot = json.loads(encoded)
    metadata = {"turn_id": ledger.turn_id, "execution_id": execution_id,
                "model_binding": snapshot["binding"], "reasoning_snapshot": snapshot["reasoning"]}
    if store.update_message_metadata(user_message["message_id"], metadata) is None:
        raise TurnBindingError("MODEL_SNAPSHOT_NOT_RECORDED", 500)
    store.append_action_event(group_id=user_group["group_id"], type="leo_turn_configuration", result=metadata)
