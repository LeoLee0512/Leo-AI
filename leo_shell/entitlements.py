"""Entitlement checkpoint for research-task operations that will become a paid feature.

The research service calls :func:`check` before every operation in :data:`COSTLY`. The decision
lives here, outside the research code identity (see ``pinn/research/worker.py`` IDENTITY_EXTRAS),
so wiring a real entitlement later never changes a product run's codeHash or invalidates a
prepared plan. Today every operation is allowed.
"""
from __future__ import annotations

from typing import Any, Mapping

#: Operations that spend model calls, a blind claim grid or an hour of compute. ``fork`` is
#: listed as well as ``create`` because it starts a new task without going through ``create``.
COSTLY = frozenset({"create", "fork", "draft", "prepare", "approve_run"})

#: The refusal code the desktop panel explains to the user.
REFUSAL = "ENTITLEMENT_REQUIRED"


def check(operation: str, context: Mapping[str, Any]) -> None:
    """Allow ``operation`` or raise ``ValueError(REFUSAL)``.

    ``context`` carries the public task identifiers (``taskId``, ``frameId``) and never a
    prompt, draft or credential. Nothing is refused yet.
    """
    return None
