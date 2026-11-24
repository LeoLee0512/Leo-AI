"""The manual-acceptance collectors must not be able to pass a checklist item.

``tools/manual_acceptance/`` exists to make the 27 items in
``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`` easier to run: collect the facts, run
what is decidable, save the evidence. The obvious way for that to go wrong is for
a collector to start deciding rows -- a tool that prints PASS for "installs under
a fresh Windows account" while running under the account that built the product
would be a fabricated acceptance result, and worse than no tool at all.

These tests are the guard. They check that:

- no collector writes to the checklist;
- every collector covers rows that exist;
- suggestions are labelled as suggestions and carry no authority;
- the verdict vocabulary has no way to spell a simulated pass;
- the classifier that names live-run failures actually distinguishes them,
  including the two shapes matching the 2026-09-03 failures.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib
import re
import sys

import pytest
from tools.report_archive import read_report

REPO = pathlib.Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools" / "manual_acceptance"
CHECKLIST = REPO / "docs" / "P0_MANUAL_ACCEPTANCE_CHECKLIST.md"

COLLECTORS = (
    "collect_windows_account_env.py",
    "verify_webview2_runtime.py",
    "verify_wsl_environment.py",
    "verify_lean_real_toolchain.py",
    "verify_research_sop_live.py",
    "verify_clean_build.py",
)


def _load(name: str):
    path = TOOLS / name
    sys.path.insert(0, str(TOOLS))
    try:
        spec = importlib.util.spec_from_file_location(f"leo_ma_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(TOOLS))


def _checklist_items() -> set[str]:
    text = read_report(CHECKLIST.relative_to(REPO).as_posix(), REPO)
    return set(re.findall(r"^\|\s*([A-F]\d)\s*\|", text, flags=re.MULTILINE))


# ------------------------------------------------------- they exist and cover


def test_every_collector_exists():
    for name in COLLECTORS:
        assert (TOOLS / name).is_file(), f"{name} is missing"
    assert (TOOLS / "run_all.py").is_file()
    assert (TOOLS / "_common.py").is_file()


def test_the_collectors_between_them_cover_all_27_items():
    """A collector for a block that skips rows would leave a silent gap."""
    covered: set[str] = set()
    for name in COLLECTORS:
        covered |= set(_load(name).COVERS)
    items = _checklist_items()
    assert len(items) == 27, f"the checklist has {len(items)} rows, expected 27"
    assert items - covered == set(), f"no collector covers: {sorted(items - covered)}"
    assert covered - items == set(), f"collectors claim rows that do not exist: {sorted(covered - items)}"


# ----------------------------------------------------- they cannot self-certify


def test_no_collector_writes_to_the_checklist():
    """Statically: nothing under tools/manual_acceptance may open the checklist for writing."""
    for path in sorted(TOOLS.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "P0_MANUAL_ACCEPTANCE_CHECKLIST" not in source or "write" not in source.lower() or (
            "write_text(" not in source.split("P0_MANUAL_ACCEPTANCE_CHECKLIST")[0][-400:]
        ), f"{path.name} looks like it writes near the checklist path"
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = getattr(node.func, "attr", None)
            if target not in ("write_text", "write_bytes", "open"):
                continue
            rendered = ast.unparse(node)
            assert "CHECKLIST" not in rendered and "P0_MANUAL" not in rendered, (
                f"{path.name} writes to the checklist: {rendered}"
            )


def test_the_verdict_vocabulary_cannot_spell_a_simulated_pass():
    common = _load("_common.py")
    assert set(common.VERDICTS) == {"PASS", "FAIL", "UNDETERMINED", "NOT APPLICABLE"}
    with pytest.raises(AssertionError):
        common.Report("t", "A", ["A1"]).check("x", "SIMULATED PASS", "no")
    with pytest.raises(AssertionError):
        common.Report("t", "A", ["A1"]).suggestion("A1", "PROBABLY PASS", "no")


def test_a_suggestion_says_it_is_only_a_suggestion():
    """The word "suggested" is not enough; the record must state its own limits."""
    common = _load("_common.py")
    report = common.Report("t", "A", ["A1"])
    entry = report.suggestion("A1", common.PASS, "because")
    assert entry["suggested_verdict"] == "PASS"
    assert "suggestion only" in entry["authority"]
    assert "NOT TESTED" in entry["authority"]
    assert "checklist_item" in entry


def test_the_saved_evidence_disclaims_authority():
    common = _load("_common.py")
    payload = common.Report("t", "A", ["A1"]).as_dict()
    assert "does not change any status" in payload["authority"]
    assert "P0_MANUAL_ACCEPTANCE_CHECKLIST" in payload["authority"]


def test_evidence_records_where_it_was_collected():
    """A result with no environment attached cannot be evaluated later."""
    common = _load("_common.py")
    environment = common.Report("t", "A", ["A1"]).as_dict()["environment"]
    for field in ("hostname", "platform", "user", "repo"):
        assert environment[field], f"environment.{field} is empty"


def test_no_collector_advertises_a_pass_it_did_not_observe():
    common = _load("_common.py")
    for path in sorted(TOOLS.glob("*.py")):
        lowered = path.read_text(encoding="utf-8").lower()
        for phrase in common.FORBIDDEN_CLAIMS:
            # The list itself lives in _common.py, which is why it is excluded.
            if path.name == "_common.py":
                continue
            assert phrase not in lowered, f"{path.name} contains {phrase!r}"


def test_run_all_states_that_nothing_was_accepted():
    source = (TOOLS / "run_all.py").read_text(encoding="utf-8")
    assert "remain NOT TESTED" in source
    assert "cannot pass a single row" in source or "cannot execute" in source


# ------------------------------------------------ the live-failure classifier


def _parser_api():
    """The shipped upstream parser, or a skip when the checkout is not here."""
    live = _load("verify_research_sop_live.py")
    common = _load("_common.py")
    report = common.Report("probe", "E", ["E1"])
    api = live._load_upstream_parser(report, live.UPSTREAM_DEFAULT)
    if api is None:
        pytest.skip("the pinned upstream checkout is not available on this machine")
    return live, api


@pytest.mark.parametrize(
    "reply, expected",
    [
        ("```python\nprint(1)\n```\n", "ok"),
        ("```\nprint(1)\n```\n", "ok"),
        # The flash symptom: a second labelled fence before the first closes.
        ("```python\nx=1\n```python\ny=2\n```\n", "unclosed-cell"),
        # Closing with a labelled fence has the same effect.
        ("```python\nprint(1)\n```python\n", "unclosed-cell"),
        # The common near-miss info string.
        ("```python3\nprint(1)\n```\n", "unexecutable-info-string"),
        ("no code at all, just prose\n", "no-action-in-reply"),
    ],
)
def test_the_classifier_names_the_failure(reply, expected):
    """Against the real shipped parser, not a reimplementation of it.

    A classifier built on a second copy of the fence rules would drift from the
    harness it is supposed to explain, and would then confidently misattribute
    failures.
    """
    live, api = _parser_api()
    assert live.classify_reply(reply, api)["classification"] == expected


def test_the_classifier_detects_repetition():
    live, api = _parser_api()
    reply = ("I will reconsider the previous approach more carefully now.\n" * 8)
    assert live.classify_reply(reply, api)["classification"] == "repetition"


def test_the_classifier_is_provider_neutral():
    """No vendor or model name may be baked into the runner."""
    source = (TOOLS / "verify_research_sop_live.py").read_text(encoding="utf-8")
    code = "\n".join(
        line for line in source.splitlines()
        if not line.strip().startswith("#")
    )
    body = code.split('"""', 2)[-1]  # everything after the module docstring
    for vendor in ("deepseek", "openai/", "anthropic", "gpt-", "claude-", "qwen"):
        assert vendor not in body.lower(), (
            f"{vendor!r} appears in the runner's code. A workaround for one model "
            "moves the failure rather than removing it, and rots when that model changes"
        )
    assert "--provider" in source and "--model" in source


def test_the_live_runner_does_not_go_looking_for_credentials():
    """A live run costs money and calls an external service."""
    source = (TOOLS / "verify_research_sop_live.py").read_text(encoding="utf-8")
    assert "key_env" in source, "the credential variable must be named, not discovered"
    assert "never goes looking for a key" in source


def test_the_live_runner_refuses_to_modify_upstream():
    """Upstream must stay byte-clean; verify_release.py fails on drift."""
    source = (TOOLS / "verify_research_sop_live.py").read_text(encoding="utf-8")
    assert "byte-clean" in source
    # Normalised: the sentence is wrapped in the docstring.
    flattened = " ".join(source.lower().split())
    assert "upstream is not modified here" in flattened
    live = _load("verify_research_sop_live.py")
    assert set(live.FAILURE_CLASSES) >= {
        "no-action-in-reply", "unclosed-cell", "unexecutable-info-string",
        "repetition", "orchestration",
    }
