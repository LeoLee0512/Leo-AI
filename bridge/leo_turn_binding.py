"""Pure exact-source edits; the central installer composes other known layers.

Never opens a database or writes active-source. ``edits`` is public so the
central installer can rebuild and reverse the FULL registered composition.
"""
from __future__ import annotations

import hashlib

VERSION = 1
BASE_SHA256 = {
    "openai4s/server/gateway.py": "db33c3e3e7b4d618881e7899646d8de55c9c1794b47f57c5b97c7d2a2227a192",
    "openai4s/store.py": "ebb2ca6ad7ae0b4084f63bbf3b388c23f09a189e614d46b182e54b4583492224",
    "openai4s/storage/frames.py": "75c4bc0ab72c187008edb9898778072e7265eb6000c3a20b9d4db55c0a79f7f0",
}

FRAME_METHOD = '''    def leo_rebind_model(self, frame_id, target, expected, validate_target):
        # LEO_TURN_BINDING_VERSION = 1: one transaction, no nested commits.
        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                row = self._connection.execute(
                    "SELECT frame_id,root_frame_id,model_profile_id,model_profile_revision FROM frames WHERE frame_id=?",
                    (frame_id,),
                ).fetchone()
                if row is None or (row["root_frame_id"] or row["frame_id"]) != frame_id:
                    raise ValueError("MODEL_SESSION_NOT_FOUND")
                current = {"profile_id": row["model_profile_id"] or "", "revision": row["model_profile_revision"] or 0}
                if current != expected:
                    raise ValueError("MODEL_BINDING_CONFLICT")
                config = self._connection.execute("SELECT value FROM settings WHERE key='model_profiles'").fetchone()
                profiles = json.loads(config[0]) if config else []
                if not isinstance(profiles, list):
                    raise ValueError("MODEL_PROFILE_INVALID")
                matching = [p for p in profiles if isinstance(p, dict) and p.get("id") == target["profile_id"]]
                if len(matching) != 1:
                    raise ValueError("MODEL_REVISION_UNAVAILABLE")
                model = validate_target(matching[0])
                changed = self._connection.execute(
                    "UPDATE frames SET model_profile_id=?,model_profile_revision=?,model=?,updated_at=? WHERE frame_id=?",
                    (target["profile_id"], target["revision"], model, self._clock_ms(), frame_id),
                )
                if changed.rowcount != 1:
                    raise ValueError("MODEL_SESSION_NOT_FOUND")
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise

'''

STORE_METHOD = '''    def leo_rebind_model(self, frame_id, target, expected, validate_target):
        # LEO_TURN_BINDING_VERSION = 1
        return self._frames.leo_rebind_model(frame_id, target, expected, validate_target)

'''

_FREEZE_OLD = '''        frozen = self.freeze_model_binding(root_frame_id)

        job = MessageJob(f"job-{uuid.uuid4().hex[:12]}", root_frame_id)
        job.model_profile_id = frozen["model_profile_id"]
        job.model_profile_revision = frozen["model_profile_revision"]
'''
_FREEZE_NEW = '''        job = MessageJob(f"job-{uuid.uuid4().hex[:12]}", root_frame_id)

        def leo_snapshot_factory():
            try:
                return _leo_turn_binding.freeze_job(self, job, reasoning_selection, model_binding)
            except _leo_turn_binding.TurnBindingError as error:
                raise GatewayError(error.status, error.code, error.code) from None
'''

_ROUTE_OLD = '''                frame_id = m.group(1)
                store.unpin_model(frame_id)
                self._json(
                    {"ok": True, "binding": runner.bind_model_revision(frame_id)}
                )
                return
'''
_ROUTE_NEW = '''                frame_id = m.group(1)
                try:
                    result = _leo_turn_binding.rebind_frame(runner, store, frame_id, self._body())
                    self._json(result)
                except _leo_turn_binding.TurnBindingError as error:
                    self._json(error.response(), error.status)
                return
            if m and method == "GET":
                try:
                    self._json(_leo_turn_binding.public_binding(store, m.group(1)))
                except _leo_turn_binding.TurnBindingError as error:
                    self._json(error.response(), error.status)
                return
'''

_PROFILE_GET = '''            if m and method == "GET":
                profile = next((item for item in store.list_model_profiles()
                                if item.get("id") == m.group(1) and not item.get("deleted_at")), None)
                if profile is None:
                    self._json({"ok": False, "code": "MODEL_PROFILE_NOT_FOUND"}, 404)
                else:
                    self._json(model_profiles.public_profile(profile))
                return
'''


def edits(relative: str) -> list[tuple[str, str]]:
    if relative == "openai4s/storage/frames.py":
        anchor = "    def unpin_model(self, frame_id: str) -> None:\n"
        return [(anchor, FRAME_METHOD + anchor)]
    if relative == "openai4s/store.py":
        anchor = "    def update_frame(self, frame_id: str, **fields: Any) -> None:\n"
        return [(anchor, STORE_METHOD + anchor)]
    if relative != "openai4s/server/gateway.py":
        raise ValueError("TURN_BINDING_TARGET_INVALID")
    cfg_anchor = '    def _llm_cfg(self, st: "SessionState | None" = None):\n'
    cfg_wrapper = '''    def _llm_cfg(self, st: "SessionState | None" = None):
        return _leo_turn_binding.effective_config(self, st)

    def _leo_original_llm_cfg(self, st: "SessionState | None" = None):
'''
    profile_anchor = '            m = re.fullmatch(r"/model-profiles/([^/]+)", sub)\n            if m and method in ("PUT", "PATCH"):\n'
    return [
        ('from openai4s.agent.finalize import with_finalize_response\n',
         'from openai4s.agent.finalize import with_finalize_response\nfrom openai4s.server import leo_turn_binding as _leo_turn_binding  # LEO_TURN_BINDING_VERSION = 1\n'),
        ('        self.model_profile_revision: int = 0\n',
         '        self.model_profile_revision: int = 0\n        self.leo_turn_snapshot: str | None = None\n'),
        ('        admission_deadline: float | None = None,\n    ):\n',
         '        admission_deadline: float | None = None,\n        snapshot_factory: Callable[[], Mapping[str, Any]] | None = None,\n    ):\n'),
        ('                try:\n                    return self.executions.submit(\n',
         '                try:\n                    snapshot_metadata = snapshot_factory() if snapshot_factory else {}\n                    return self.executions.submit(\n'),
        ('                        metadata={"reason": reason, **dict(metadata or {})},\n',
         '                        metadata={"reason": reason, **dict(metadata or {}), **snapshot_metadata},\n'),
        ('        on_admitted: Callable[[MessageJob], None] | None = None,\n    ) -> MessageJob:\n',
         '        on_admitted: Callable[[MessageJob], None] | None = None,\n        reasoning_selection: dict | None = None,\n        model_binding: dict | None = None,\n    ) -> MessageJob:\n'),
        (_FREEZE_OLD, _FREEZE_NEW),
        ('            owner_id=job.job_id,\n            reason="user message",\n',
         '            owner_id=job.job_id,\n            reason="user message",\n            snapshot_factory=leo_snapshot_factory,\n'),
        ('                            task_mode=task_mode,\n                        )\n                        result.setdefault("job_id", job.job_id)\n',
         '                            task_mode=task_mode,\n                            leo_turn_snapshot=job.leo_turn_snapshot,\n                        )\n                        result.setdefault("job_id", job.job_id)\n'),
        (cfg_anchor, cfg_wrapper),
        ('        frozen_binding: tuple[str, int] | None = None,\n        task_mode: str | None = None,\n',
         '        frozen_binding: tuple[str, int] | None = None,\n        task_mode: str | None = None,\n        leo_turn_snapshot: str | None = None,\n'),
        ('        st = self._state(root_frame_id, project_id)\n        if frozen_binding:\n',
         '        st = self._state(root_frame_id, project_id)\n        frozen_binding = _leo_turn_binding.install_turn(self, st, root_frame_id, frozen_binding, leo_turn_snapshot)\n        if frozen_binding:\n'),
        ('            action_ledger.append_user(user_message)\n',
         '            leo_user_group = action_ledger.append_user(user_message)\n            _leo_turn_binding.record_snapshot(self.store, st, stored_user_message, action_ledger, turn_execution_id, leo_user_group)\n'),
        ('        def _llm_quota_gate() -> None:\n            self.enforce_llm_quota(st.root_frame_id)\n',
         '        def _llm_quota_gate() -> None:\n            _leo_turn_binding.validate_live_profile(self, st)\n            self.enforce_llm_quota(st.root_frame_id)\n'),
        (_ROUTE_OLD, _ROUTE_NEW),
        ('                    self._json(model_profiles.create(self._body()), 201)\n',
         '                    leo_body = self._body()\n                    if "leo_registration_id" in leo_body:\n                        self._json(_leo_turn_binding.create_managed_profile(store, cfg, leo_body), 201)\n                    else:\n                        self._json(model_profiles.create(leo_body), 201)\n                except _leo_turn_binding.TurnBindingError as error:\n                    self._json(error.response(), error.status)\n'),
        ('                model_profiles.delete(m.group(1))\n',
         '                if m.group(1).startswith("mp-leo-"):\n                    try:\n                        _leo_turn_binding.delete_managed_profile(store, cfg, m.group(1))\n                    except _leo_turn_binding.TurnBindingError as error:\n                        self._json(error.response(), error.status)\n                        return\n                else:\n                    model_profiles.delete(m.group(1))\n'),
        (profile_anchor, '            m = re.fullmatch(r"/model-profiles/([^/]+)", sub)\n' + _PROFILE_GET + '            if m and method in ("PUT", "PATCH"):\n'),
        ('                        on_admitted=_persist_correlation,\n',
         '                        on_admitted=_persist_correlation,\n                        reasoning_selection=b.get("reasoning_selection"),\n                        model_binding=b.get("model_binding"),\n'),
    ]


def transform(relative: str, original: bytes) -> bytes:
    if relative not in BASE_SHA256 or hashlib.sha256(original).hexdigest() != BASE_SHA256[relative]:
        raise ValueError("TURN_BINDING_SOURCE_UNKNOWN")
    source = original.decode("utf-8")
    for before, after in edits(relative):
        if source.count(before) != 1:
            raise ValueError("TURN_BINDING_LAYOUT_CHANGED")
        source = source.replace(before, after, 1)
    result = source.encode("utf-8")
    compile(result, relative, "exec")
    return result


def reverse(relative: str, modified: bytes) -> bytes:
    source = modified.decode("utf-8")
    for before, after in reversed(edits(relative)):
        if source.count(after) != 1:
            raise ValueError("TURN_BINDING_LAYER_CONFLICT")
        source = source.replace(after, before, 1)
    original = source.encode("utf-8")
    if transform(relative, original) != modified:
        raise ValueError("TURN_BINDING_LAYER_CONFLICT")
    return original
