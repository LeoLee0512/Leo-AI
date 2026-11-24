"""Who wrote the tests that carry a gate, and what has not been confirmed yet.

P0-2 rests on 41 adversarial tests. Those tests were *reconstructed* from the
reviewer's written description of the failures; the reviewer's own file was
referenced but never supplied. Those are two different evidentiary situations
and collapsing them would be the quiet way to claim independent confirmation
that has not happened.

``manifests/test-suites.json`` records the distinction. This file makes the
record enforceable:

- the reconstructed suite cannot be renamed into the reviewer's file name;
- it cannot be deleted or shrunk, whatever arrives later;
- a suite that is ABSENT cannot be marked PRESENT without a file to run;
- the outstanding confirmation stays visible as a release caveat.

None of this makes P0-2 fail. It makes P0-2's basis legible.
"""

from __future__ import annotations

import json
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO / "manifests" / "test-suites.json"


def registry() -> dict:
    assert REGISTRY_PATH.is_file(), f"suite registry missing at {REGISTRY_PATH}"
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def suites() -> dict[str, dict]:
    return {entry["id"]: entry for entry in registry()["suites"]}


def _test_names(path: pathlib.Path) -> set[str]:
    """Collect ``def test_*`` names without importing the module."""
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


# ------------------------------------------------------------- the registry


def test_every_declared_suite_has_a_known_provenance_and_status():
    data = registry()
    kinds = set(data["provenance_kinds"])
    statuses = set(data["statuses"])
    for entry in data["suites"]:
        assert entry["provenance"] in kinds, entry
        assert entry["status"] in statuses, entry


def _collected_cases(path: pathlib.Path) -> int:
    """How many cases pytest actually runs for *path*, parametrisation expanded.

    Counted by asking pytest, not by re-implementing parametrise expansion here:
    the headline numbers these suites are quoted by ("41 adversarial tests") are
    collected-case counts, and a count derived a second way would drift.
    """
    import subprocess
    import sys

    done = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q", "--collect-only", "--no-header", "-p", "no:cacheprovider"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert done.returncode == 0, (
        f"collection of {path} failed:\n{done.stdout}\n{done.stderr}"
    )
    return sum(1 for line in done.stdout.splitlines() if "::" in line)


def test_present_suites_exist_and_have_not_shrunk():
    """A declared suite must be on disk with at least the tests it promised."""
    for entry in registry()["suites"]:
        if entry["status"] != "PRESENT":
            continue
        path = REPO / entry["path"]
        assert path.is_file(), f"{entry['id']} declares {entry['path']}, which is not there"
        found = _test_names(path)
        assert len(found) >= entry["minimum_test_functions"], (
            f"{entry['id']} defines {len(found)} test functions, below its declared floor "
            f"of {entry['minimum_test_functions']}. Tests may be added; they may not be removed."
        )


def test_present_suites_still_run_the_number_of_cases_they_are_quoted_by():
    """The collected-case floor, which is the number the reports cite."""
    for entry in registry()["suites"]:
        if entry["status"] != "PRESENT":
            continue
        collected = _collected_cases(REPO / entry["path"])
        assert collected >= entry["minimum_collected_cases"], (
            f"{entry['id']} now collects {collected} cases, below the "
            f"{entry['minimum_collected_cases']} it is cited as providing"
        )


def test_absent_suites_declare_no_file_to_run():
    """ABSENT must mean absent -- not a path that quietly points at something else."""
    for entry in registry()["suites"]:
        if entry["status"] != "ABSENT":
            continue
        assert entry["path"] is None, (
            f"{entry['id']} is ABSENT but names a path; a suite is either supplied or it is not"
        )


# ------------------------------------ the reconstructed suite is load-bearing


def test_the_reconstructed_adversarial_suite_is_intact():
    """Its test functions are named in the registry and every one must still exist."""
    entry = suites()["research-sop-adversarial-reconstructed"]
    path = REPO / entry["path"]
    found = _test_names(path)
    locked = set(entry["locked_test_functions"])
    assert entry["reconstructed_cases_at_registration"] == 41, (
        "the reconstructed suite is cited as 41 cases; the registry must say so"
    )
    assert len(locked) == entry["minimum_test_functions"]
    missing = sorted(locked - found)
    assert not missing, (
        "reconstructed adversarial tests were removed or renamed:\n  "
        + "\n  ".join(missing)
        + "\n\nThis suite is evidence for P0-2 and is kept even after the reviewer's "
        "own file arrives. Add tests beside it; do not replace it."
    )


def test_the_reconstructed_suite_says_so_in_its_own_docstring():
    """Someone opening the file must learn its provenance from the file.

    A registry entry nobody reads is not a safeguard. The word has to be in the
    module that would otherwise be mistaken for the reviewer's own.
    """
    entry = suites()["research-sop-adversarial-reconstructed"]
    header = (REPO / entry["path"]).read_text(encoding="utf-8")[:2000].lower()
    assert "reconstruct" in header, "the file must say it is a reconstruction"
    assert "not supplied" in header or "not provided" in header, (
        "the file must say the reviewer's original was not supplied"
    )


def test_the_reviewer_original_slot_is_recorded_as_not_provided():
    """The outstanding item stays visible rather than being forgotten."""
    entry = suites()["research-sop-adversarial-reviewer-original"]
    assert entry["status"] == "ABSENT"
    assert entry["provenance"] == "reviewer-original"
    assert entry["reserved_path"] != suites()["research-sop-adversarial-reconstructed"]["path"], (
        "the reviewer's file must land at its own path, not overwrite the reconstruction"
    )
    pending = {item["id"]: item for item in registry()["pending_confirmations"]}
    outstanding = pending["reviewer-original-adversarial-tests"]
    assert outstanding["state"] == "NOT PROVIDED"
    assert outstanding["gate"] == "P0-2"
    assert outstanding["effect_on_gate"].strip(), (
        "a pending confirmation must say what it does and does not change about the gate"
    )


def test_the_reviewer_file_if_it_arrives_runs_alongside_not_instead():
    """When the reserved path appears, both suites must be present and run.

    Skipping is not an option here: this either checks a real coexistence or it
    checks that the file is absent, and both are useful. What it must never do
    is pass because the reconstruction was replaced.
    """
    reconstructed = REPO / suites()["research-sop-adversarial-reconstructed"]["path"]
    reserved = REPO / suites()["research-sop-adversarial-reviewer-original"]["reserved_path"]
    assert reconstructed.is_file(), "the reconstructed suite must always be present"
    if not reserved.is_file():
        registered = suites()["research-sop-adversarial-reviewer-original"]["status"]
        assert registered == "ABSENT", (
            "the registry says the reviewer's suite is present, but there is no file at "
            f"{reserved}"
        )
        return
    assert suites()["research-sop-adversarial-reviewer-original"]["status"] == "PRESENT", (
        f"{reserved} exists but the registry still says ABSENT -- update the registry "
        "and record that the independent confirmation has now happened"
    )
    assert _test_names(reserved), "the reviewer's suite declares no tests"


# ------------------------------------------------- honesty about the wording


@pytest.mark.parametrize(
    "path",
    [
        "docs/P0_RELEASE_CANDIDATE.md",
        "docs/P0_FINAL_CLOSURE_REPORT.md",
    ],
)
def test_reports_do_not_call_the_reconstruction_the_reviewers_tests(path):
    """A report may cite the 41 tests; it may not attribute them to the reviewer."""
    from tools.report_archive import read_report
    text = read_report(path, REPO)
    assert "41" in text, f"{path} should state the size of the suite it relies on"
    lowered = text.lower()
    assert "reconstruct" in lowered or "独立重建" in text, (
        f"{path} cites the adversarial suite without saying it is a reconstruction"
    )
