"""P0-3: nothing the user can click may be backed by an unimplemented API.

The failure this prevents is the one that damages trust fastest in a beta: the
page renders a control, the user clicks it, and the shell answers
"此功能暂未在新版壳中提供". Eleven such controls shipped — custom themes, the
whole data-lifecycle pane, and project persona.

They are not deleted, because the features are wanted later. They are gated on
``LEO_FEATURE_FLAGS`` in ``stage/leo-inject.js`` and the markup is not emitted at
all while a flag is false.

That alone was not enough, and the Gate review proved it: appending an ungated
``window.pywebview.api.list_entity_states({})`` to the file left all five of the
original tests green. They checked that a flag held the value ``false``, not that
the call sites were actually behind it.

The injection layer that carried those gated controls (``leo-inject.js`` and its
``leoBridge`` with ``LEO_FEATURE_FLAGS``) was removed on 2026-09-26 together with
the upstream page it decorated. Every document the user sees is now Leo's own,
and none of them may call an unimplemented method at all -- there is no gate
left to hide behind. ``test_mutation_an_unimplemented_call_is_detected`` proves
the scan would notice one.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

FRONTEND_SOURCES = (
    REPO / "stage" / "workbench.js",
    REPO / "stage" / "research-panel.js",
    REPO / "stage" / "shell.html",
)

API_CALL = re.compile(
    r"(?:window\.)?pywebview\s*(?:\?\.)?\.?\s*api\s*(?:\?\.)?\.\s*(\w+)"
)
#: The workbench reaches the shell through its own ``native('<method>', ...)`` helper.
NATIVE_CALL = re.compile(r"\bnative\(\s*['\"](\w+)['\"]")

#: Which feature flag governs each unimplemented ShellApi method. Adding a name
#: to ``_UNIMPLEMENTED_EXTENSIONS`` without deciding which flag hides it is
#: itself a failure: the decision is the point.
FEATURE_OF = {
    "choose_theme_file": "customThemes",
    "stage_theme_preview": "customThemes",
    "confirm_theme_preview": "customThemes",
    "discard_theme_preview": "customThemes",
    "delete_custom_theme": "customThemes",
    "list_entity_states": "entityLifecycle",
    "mark_entity": "entityLifecycle",
    "restore_entity": "entityLifecycle",
    "forget_entity": "entityLifecycle",
    "get_project_persona": "projectPersona",
    "save_project_persona": "projectPersona",
}


def _api_source() -> str:
    return (REPO / "leo_shell" / "api.py").read_text(encoding="utf-8")


def implemented_methods() -> set[str]:
    tree = ast.parse(_api_source())
    shell_api = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "ShellApi"
    )
    return {
        node.name
        for node in shell_api.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }


def unimplemented_methods() -> set[str]:
    source = _api_source()
    block = source.split("_UNIMPLEMENTED_EXTENSIONS", 1)[1].split(")", 1)[0]
    return set(re.findall(r'"(\w+)"', block))


def called_methods() -> dict[str, set[str]]:
    calls: dict[str, set[str]] = {}
    for path in FRONTEND_SOURCES:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        for match in [*API_CALL.finditer(source), *NATIVE_CALL.finditer(source)]:
            calls.setdefault(match.group(1), set()).add(path.name)
    return calls


def test_every_called_api_exists_somewhere():
    """A call to a method the shell has never heard of is a typo, not a feature."""
    known = implemented_methods() | unimplemented_methods()
    unknown = {name: sorted(src) for name, src in called_methods().items() if name not in known}
    assert not unknown, f"front end calls pywebview.api methods ShellApi does not define: {unknown}"


def test_no_frontend_calls_an_unimplemented_method():
    """No user-visible control may reach an unimplemented backend; there is no gate any more."""
    unimplemented = unimplemented_methods()
    offenders = {name: sorted(src) for name, src in called_methods().items() if name in unimplemented}
    assert not offenders, f"these documents call unimplemented ShellApi methods: {offenders}"


def test_the_scan_sees_the_workbench_call_style():
    """If the contract missed native('...') calls it would be checking nothing in the workbench."""
    calls = called_methods()
    for name in ("workbench_request", "save_profile", "purge_entity", "return_to_start", "list_session_models"):
        assert "workbench.js" in calls.get(name, set()), name
    assert "workbench.js" not in calls.get("open_model_settings", set())


def test_mutation_an_unimplemented_call_is_detected(monkeypatch, tmp_path):
    """Insert a call to an unimplemented method and the scan must fail on it."""
    mutated = tmp_path / "workbench.js"
    mutated.write_text((REPO / "stage" / "workbench.js").read_text(encoding="utf-8")
                       + "\nnative('save_project_persona',{});\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "FRONTEND_SOURCES", (mutated,))
    assert "save_project_persona" in called_methods()
    assert "save_project_persona" in unimplemented_methods()


def test_every_unimplemented_method_has_a_declared_owner():
    """Adding to _UNIMPLEMENTED_EXTENSIONS forces a decision about the UI."""
    missing = sorted(unimplemented_methods() - set(FEATURE_OF))
    assert not missing, (
        f"{missing} were declared unimplemented but no feature flag was assigned. "
        "Add them to FEATURE_OF and gate their UI, or implement them."
    )


def test_shell_html_calls_only_implemented_methods():
    """The splash page has no gated features, so it may call the API directly --
    but only methods that really exist."""
    text = (REPO / "stage" / "shell.html").read_text(encoding="utf-8")
    unimplemented = unimplemented_methods()
    offenders = sorted({name for name in API_CALL.findall(text) if name in unimplemented})
    assert not offenders, f"shell.html calls unimplemented methods: {offenders}"
