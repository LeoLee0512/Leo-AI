"""P0-2 regression tests: research-sop must never hand one study another's evidence.

The defect these lock down was real and silent. ``sop_stage_path`` used a single
fixed ``research-sop/NN-role.json`` layout with no task binding, and
``orchestrate_research(resume=True)`` — the default — returned any stage it found
marked ``complete``. Running question B after question A therefore reported A's
literature survey, modelling and validation as B's own results, with no delegate
call and no warning. The same function also ended with an unconditional
``{"status": "complete", "validator": "pass", "paper": <path>}``, so a one-role
smoke test claimed a validated paper that was never written.

The skill's kernel is loaded the way the daemon loads it — as a module with a
``host`` object injected — so these tests exercise the shipped file, not a copy.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]

TASK_A = "Does the residual L2 norm bound the L2 error for a 1D Poisson problem?"
TASK_B = "How does mesh anisotropy affect convergence of a 2D heat equation solver?"


def _skill_root() -> pathlib.Path:
    """Locate the canonical research-sop skill.

    The canonical copy is the one in this repository. It is deliberately NOT the
    deployed copy under the user data directory: testing whatever happens to be
    deployed would mean the suite passes or fails depending on machine state
    rather than on the source under review. Whether the deployed and daemon
    copies match canonical is a separate question, checked by
    ``tools/sync_skills.py --check``.
    """
    override = os.environ.get("LEO_SKILLS_ROOT")
    root = pathlib.Path(override) if override else REPO / "skills"
    return root / "research-sop"


#: The orchestrator now validates each role's output against ROLE_OUTPUT_SCHEMA
#: locally, so a fake returning only {"summary": ...} is correctly rejected.
#: These are the minimum shapes a real child would have to submit.
ROLE_REQUIRED = {
    "literature-surveyor": ("summary", "citations", "gaps"),
    "modeler": ("summary", "equations", "assumptions"),
    "numerical-experimenter": ("summary", "method", "results", "convergence"),
    "validator": ("summary", "verdict", "findings"),
    "paper-writer": ("summary", "sections"),
}


def schema_valid_output(role, **overrides):
    """A minimal output that satisfies *role*'s required keys."""
    output = {key: f"{role} {key}" for key in ROLE_REQUIRED.get(role, ("summary",))}
    if role == "validator":
        output["verdict"] = "pass"
        output["findings"] = []
    output["document"] = f"# {role}\n\nbody\n"
    output.update(overrides)
    return output


class FakeHost:
    """In-memory stand-in for the host SDK the kernel talks to.

    Records every delegate call so a test can assert that a stage was actually
    re-run rather than silently inherited.
    """

    def __init__(self, outputs=None):
        self.files: dict[str, str] = {}
        self.delegate_calls: list[dict] = []
        self.outputs = outputs or {}

    # -- filesystem ------------------------------------------------------

    def read_file(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return {"content": self.files[path]}

    def write_file(self, path, content):
        self.files[path] = content
        return {"path": path, "bytes": len(content)}

    def list_dir(self, path):
        prefix = path.rstrip("/") + "/"
        names = {
            key[len(prefix):].split("/")[0]
            for key in self.files
            if key.startswith(prefix)
        }
        return {"entries": [{"name": name} for name in sorted(names)]}

    # -- delegation ------------------------------------------------------

    def delegate(self, request, **kwargs):
        role = kwargs.get("name")
        self.delegate_calls.append({"role": role, "request": request})
        output = self.outputs.get(role)
        if output is None:
            output = schema_valid_output(role)
        return {
            "output": output,
            "task_status": "completed",
            "turns": 1,
            "child_id": f"child-{role}",
        }


def _load_kernel(host):
    """Import the shipped kernel.py with *host* injected, as the daemon does."""
    path = _skill_root() / "kernel.py"
    # Fail, never skip: a missing canonical skill means this repo is not the
    # source of truth it claims to be, and a green skip would hide exactly that.
    assert path.is_file(), f"canonical research-sop kernel not found at {path}"
    sys.modules["host"] = host
    spec = importlib.util.spec_from_file_location("leo_research_sop_kernel", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _passing_outputs():
    return {role: schema_valid_output(role) for role in ROLE_REQUIRED}


@pytest.fixture
def host():
    fake = FakeHost(outputs=_passing_outputs())
    yield fake
    sys.modules.pop("host", None)


@pytest.fixture
def kernel(host):
    return _load_kernel(host)


# ---------------------------------------------------------------- Case A


def test_case_a_second_task_never_reads_the_first_tasks_stages(kernel, host):
    """Task A completes; task B resumes; B must not inherit a single A stage."""
    first = kernel.orchestrate_research(TASK_A)
    assert first["status"] == "complete", first
    a_run = first["run_id"]
    assert host.delegate_calls, "task A should have delegated"

    host.delegate_calls.clear()
    second = kernel.orchestrate_research(TASK_B, resume=True)

    b_run = second["run_id"]
    assert b_run != a_run, "a different question must get a different run"
    assert second["task_sha256"] == kernel.sop_task_sha256(TASK_B)
    assert second["resumed"] is False, "task B is not a resume of anything"

    # Every role ran for B in its own right.
    roles_run = [call["role"] for call in host.delegate_calls]
    assert set(roles_run) == set(kernel.ROLE_ORDER), roles_run

    # And nothing B reports points into A's directory.
    for stage in second["stages"]:
        assert a_run not in stage["document"], stage
    assert a_run not in (second["paper"] or "")

    # A's evidence is still on disk, untouched — a new run must not delete it.
    assert kernel.sop_read_stage(a_run, "validator", kernel.sop_task_sha256(TASK_A)) is not None


# ---------------------------------------------------------------- Case B


def test_case_b_partial_role_subset_is_not_complete(kernel, host):
    """Running a subset of roles must report partial, never complete."""
    result = kernel.orchestrate_research(
        TASK_A, roles=["literature-surveyor", "modeler"]
    )
    assert result["status"] == "partial", result
    assert result["pipeline"] == ["literature-surveyor", "modeler"]
    ran = [call["role"] for call in host.delegate_calls]
    assert ran == ["literature-surveyor", "modeler"], ran


# ---------------------------------------------------------------- Case C


def test_case_c_without_validator_there_is_no_pass(kernel, host):
    """A pipeline that never ran the validator must not report validator=pass."""
    result = kernel.orchestrate_research(
        TASK_A,
        roles=["literature-surveyor", "modeler", "numerical-experimenter"],
    )
    assert result["validator"] is None, result
    assert result["status"] != "complete"
    assert "validator" not in [call["role"] for call in host.delegate_calls]


def test_validator_failure_is_not_reported_as_pass(host):
    """A validator that fails twice must end unresolved, not complete."""
    host.outputs = {
        "validator": {
            "summary": "no",
            "verdict": "fail",
            "findings": ["boundary condition unverified"],
            "send_back_to": "modeler",
            "document": "# validator\n",
        }
    }
    kernel = _load_kernel(host)
    result = kernel.orchestrate_research(TASK_A, max_rollbacks=1)
    assert result["status"] == "unresolved", result
    assert result["validator"] == "fail"
    assert result["paper"] is None
    assert result["findings"] == ["boundary condition unverified"]


# ---------------------------------------------------------------- Case D


def test_case_d_without_paper_writer_no_paper_path(kernel, host):
    """No paper-writer means no paper path — not a path to a file that is absent."""
    result = kernel.orchestrate_research(
        TASK_A,
        roles=["literature-surveyor", "modeler", "numerical-experimenter", "validator"],
    )
    assert result["paper"] is None, result
    assert result["status"] == "partial"
    # Nothing was written for a stage that never ran.
    assert kernel.sop_stage_path(result["run_id"], "paper-writer", "md") not in host.files


# ---------------------------------------------------------------- Case E


def test_case_e_same_task_resumes_in_place(kernel, host):
    """A legitimate resume of the same question continues instead of re-running."""
    first = kernel.orchestrate_research(TASK_A)
    assert first["status"] == "complete"
    run_id = first["run_id"]

    host.delegate_calls.clear()
    second = kernel.orchestrate_research(TASK_A, resume=True)

    assert second["run_id"] == run_id, "same question must reuse its own run"
    assert second["resumed"] is True
    assert host.delegate_calls == [], "completed stages must not be re-delegated"
    assert second["status"] == "complete"


def test_rework_forks_a_new_run_and_keeps_the_old_evidence(kernel, host):
    """resume=False is a rework: new run, recorded lineage, old run preserved."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]

    second = kernel.orchestrate_research(TASK_A, resume=False)
    assert second["run_id"] != original
    assert second["parent_run_id"] == original, second
    # The earlier attempt is still readable; a rework must not erase evidence.
    assert kernel.sop_read_stage(original, "paper-writer", kernel.sop_task_sha256(TASK_A)) is not None


# ------------------------------------------------------------- manifest


def test_manifest_binds_the_run_to_its_task_and_pipeline(kernel, host):
    """The manifest must carry every field the audit requires."""
    result = kernel.orchestrate_research(TASK_A)
    manifest = kernel.sop_read_manifest(result["run_id"])
    assert manifest is not None
    for field in (
        "schema_version",
        "run_id",
        "task_text",
        "task_sha256",
        "pipeline_version",
        "role_prompt_hashes",
        "model_fingerprint",
        "created_at",
        "parent_run_id",
    ):
        assert field in manifest, f"manifest is missing {field}"
    expected = hashlib.sha256(" ".join(TASK_A.split()).encode("utf-8")).hexdigest()
    assert manifest["task_sha256"] == expected
    assert set(manifest["role_prompt_hashes"]) == set(kernel.ROLE_ORDER)
    # An unknown model must say so rather than invent an identifier.
    assert manifest["model_fingerprint"]["model"] == "unknown"


def test_stage_records_are_stamped_and_cross_task_reads_are_refused(kernel, host):
    """A stage carrying another task's hash must not be readable as evidence."""
    result = kernel.orchestrate_research(TASK_A)
    run_id = result["run_id"]
    path = kernel.sop_stage_path(run_id, "modeler")
    record = json.loads(host.files[path])
    assert record["run_id"] == run_id
    assert record["task_sha256"] == kernel.sop_task_sha256(TASK_A)

    # Same file, wrong task: refused.
    assert kernel.sop_read_stage(run_id, "modeler", "deadbeef") is None
    # Right task: still readable.
    assert (
        kernel.sop_read_stage(run_id, "modeler", record["task_sha256"])
        is not None
    )


def test_task_hash_ignores_whitespace_but_not_wording(kernel):
    """Re-wrapping a question resumes; changing a word does not."""
    assert kernel.sop_task_sha256(TASK_A) == kernel.sop_task_sha256(
        TASK_A.replace(" ", "\n  ")
    )
    assert kernel.sop_task_sha256(TASK_A) != kernel.sop_task_sha256(TASK_A + " Really?")


def test_manifest_with_a_mismatched_task_is_refused(kernel, host):
    """A hand-edited or corrupted manifest must not be silently reused."""
    result = kernel.orchestrate_research(TASK_A)
    run_id = result["run_id"]
    manifest = kernel.sop_read_manifest(run_id)
    manifest["task_sha256"] = "0" * 64
    kernel.sop_write_manifest(run_id, manifest)
    with pytest.raises(ValueError, match="does not match this task"):
        kernel.orchestrate_research(TASK_A)


def test_blocked_stage_reports_blocked_not_complete(host):
    """A stage that fails to complete must block the run."""
    host.outputs = {"modeler": {}}  # no output, no document -> incomplete

    class Silent(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "modeler":
                return {"output": None, "final_message": ""}
            return super().delegate(request, **kwargs)

    silent = Silent(outputs=_passing_outputs())
    kernel = _load_kernel(silent)
    result = kernel.orchestrate_research(TASK_A)
    assert result["status"] == "blocked", result
    assert result["paper"] is None
    assert result["validator"] is None
