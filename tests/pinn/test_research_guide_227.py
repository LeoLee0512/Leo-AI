"""2.2.7: a finished run is verified once and read quickly, re-checked on demand, and explained.

No training: a completed task is assembled from the files a real run leaves behind, and the
full verifier is replaced by a counting fake, so each rule the desktop depends on is pinned
without a formal run.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import leo_shell.research as research
from leo_shell import evidence_guide
from leo_shell.research import ResearchService
from leo_shell.research_draft import PROMPT, TEMPLATE, validate_draft
from pinn.governance.trust_loop import code_hash_from_manifest
from pinn.research.evidence import tree_hashes
from pinn.research.storage import digest, read, write

VERIFIED = {"scientificState": "ACCEPTED", "verified": True, "allowedClaims": ["C0", "C1", "C2"],
            "blockedClaims": [{"level": "C3", "reason": "no independently qualified C2 runs supplied"}],
            "dimensions": {k: {"status": "PASS", "checks": [{"checkId": "T9-collocationDisjointness", "status": "PASS",
                                                             "reason": "train | dev | phys | claim pairwise sample-disjoint: yes"}]}
                           for k in ("math", "impl", "train", "physics", "external", "repro")},
            "codeHash": "c" * 64}
SOURCE = b"print('method')\n"
MANIFEST = [{"path": "pinn/a.py", "sha256": hashlib.sha256(SOURCE).hexdigest()}]


def raw(**change):
    return {"objective": "验证基准", "equation": TEMPLATE["equation"], "domain": [0, 1],
            "boundary": {"left": 0, "right": 0}, "assumptions": [], "missing": [], "conflicts": [], **change}


def completed(tmp_path, monkeypatch):
    """A COMPLETED task whose evidence looks like a real run's, with a counting verifier."""
    paths = SimpleNamespace(root=tmp_path, user=tmp_path / "user")
    for name in ("code", "python-a", "python-b"):
        (tmp_path / name).mkdir(exist_ok=True)
    (tmp_path / "code/pinn").mkdir()
    (tmp_path / "code/pinn/a.py").write_bytes(SOURCE)
    (tmp_path / "code/.gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
    service = ResearchService(paths, confirm=lambda *_: True, background=False,
                              draft_provider=lambda frame, prompt: validate_draft(raw(), prompt),
                              runtime={"codeRoot": str(tmp_path / "code"), "pythonA": str(tmp_path / "python-a"),
                                       "pythonB": str(tmp_path / "python-b")})
    task = service.dispatch("create", {"prompt": "验证基准", "frameId": "f-a", "projectId": "p-a"})["task"]
    directory = service._directory(task["taskId"])
    main = directory / "work/attempts/main"
    code_hash = code_hash_from_manifest(MANIFEST)
    write(directory / "execution-plan.json", {"taskId": task["taskId"], "codeManifest": MANIFEST,
          "context": {"codeRoot": str(tmp_path / "code")}, "codeHash": code_hash,
          "createdAt": "2026-09-29T03:52:15Z", "budgetSeconds": 3600, "expectedTolerance": {"devRelL2MedianAbsDiff": 1e-4},
          "solverConfiguration": {"configId": "leo-poisson1d-hard-bc-v1", "preregistration": {"epsilonSpec": 1e-3}}})
    write(main / "identity.json", {"codeHash": code_hash, "codeManifest": MANIFEST})
    write(main / "claim_set_ledger.json", [{"event": "SEALED", "at": "2026-09-29T03:52:09Z"},
                                           {"event": "OPENED", "at": "2026-09-29T04:36:28Z"}])
    write(main / "RUN_SUMMARY.json", {"startedAt": "2026-09-29T04:33:50Z", "finalState": "ACCEPTED",
          "training": {"runs": 10, "divergent": 0, "median": 1.99e-4, "worst": 2.48e-4, "successRate": "10/10"},
          "claimEvaluation": {"perSeedAC1": [7.1e-5, 2.519e-4, 1.5e-4]},
          "g6": {"report": {"medianA": 1.99e-4, "medianB": 2.55e-4, "medianAbsDiff": 5.6e-5}}})
    write(directory / "work/experiments/poisson1d/problems/pdef-x-claim-GL1056-CGL4004.json", {"samples": [{}] * 5058})
    write(directory / "run-approval.json", {"at": "2026-09-29T04:33:45Z"})
    receipt = {"state": "COMPLETED", "at": "2026-09-29T04:41:11Z", "evidenceHashes": tree_hashes(directory / "work", exclude=())}
    write(directory / "completion.json", receipt)
    task = read(directory / "state.json")
    task.update({"state": "COMPLETED", "completionHash": digest(receipt)})
    service._save(directory, task, "WORKER_FINISHED")
    calls = []

    def fake_verify(root):
        calls.append(root)
        return json.loads(json.dumps(VERIFIED))

    monkeypatch.setattr(research, "verify_attempt", fake_verify)
    return service, read(directory / "state.json"), directory, calls


# -- drafts ------------------------------------------------------------------------------------

def test_the_prompt_keeps_domain_and_boundary_out_of_the_equation_field():
    assert "equation holds the differential equation alone" in PROMPT


def test_an_equation_carrying_its_domain_and_boundary_is_explained_not_accepted():
    draft = validate_draft(raw(equation="-u''(x)=pi^2*sin(pi*x), 0<x<1, u(0)=u(1)=0"), "p")
    assert not draft["supported"]
    assert len(draft["unsupportedReasons"]) == 1 and "夹带了区间或边界条件" in draft["unsupportedReasons"][0]


@pytest.mark.parametrize("change,fragment", [
    ({"equation": "-u''(x)=x"}, "方程不是"),
    ({"domain": [0, 2]}, "求解区域"),
    ({"domain": [False, True]}, "求解区域"),
    ({"boundary": {"left": 0, "right": 1}}, "边界条件"),
    ({"boundary": None}, "缺少边界条件"),
    ({"missing": ["系数"]}, "待补充"),
    ({"conflicts": ["两个方程"]}, "冲突"),
])
def test_each_mismatching_field_gets_its_own_reason(change, fragment):
    draft = validate_draft(raw(**change), "p")
    assert not draft["supported"] and any(fragment in r for r in draft["unsupportedReasons"])


def test_a_supported_draft_has_no_reasons_and_the_match_stays_exact():
    assert validate_draft(raw(), "p")["unsupportedReasons"] == []
    assert not validate_draft(raw(equation="-u''(x)=pi^2*sin(pi*x) on (0,1)"), "p")["supported"]


# -- verification is cached, never trusted blindly --------------------------------------------

def test_a_finished_run_is_fully_verified_once_then_read_from_the_cache(tmp_path, monkeypatch):
    service, task, _, calls = completed(tmp_path, monkeypatch)
    for _ in range(3):
        view = service.dispatch("get", {"taskId": task["taskId"]})
        assert view["verification"]["verified"] and view["guide"]
    assert len(calls) == 1


def test_changed_evidence_is_caught_without_the_cache(tmp_path, monkeypatch):
    service, task, directory, calls = completed(tmp_path, monkeypatch)
    service.dispatch("get", {"taskId": task["taskId"]})
    (directory / "work/attempts/main/RUN_SUMMARY.json").write_text("{}", encoding="utf-8")
    view = service.dispatch("get", {"taskId": task["taskId"]})
    assert view["verification"] == {"verified": False, "allowedClaims": [], "reason": "EVIDENCE_HASH_MISMATCH"}
    assert "guide" not in view


def test_an_upgrade_or_a_forged_cache_forces_a_full_verification(tmp_path, monkeypatch):
    service, task, _, calls = completed(tmp_path, monkeypatch)
    service.dispatch("get", {"taskId": task["taskId"]})
    monkeypatch.setattr(research, "__version__", "9.9.9")
    service.dispatch("get", {"taskId": task["taskId"]})
    assert len(calls) == 2
    cache = tmp_path / "user/research/cache" / (task["taskId"] + ".json")
    forged = read(cache)
    forged["key"] = "0" * 64
    write(cache, forged)
    service.dispatch("get", {"taskId": task["taskId"]})
    assert len(calls) == 3


def test_export_always_verifies_in_full_and_ships_the_guide_inside_the_package(tmp_path, monkeypatch):
    service, task, _, calls = completed(tmp_path, monkeypatch)
    service.dispatch("get", {"taskId": task["taskId"]})
    path = Path(service.dispatch("export", {"taskId": task["taskId"], "expectedVersion": task["version"]})["path"])
    assert len(calls) == 2
    manifest = json.loads((path / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))["fileHashes"]
    assert "证据说明书.html" in manifest
    assert "2.52 × 10⁻⁴" in (path / "证据说明书.html").read_text(encoding="utf-8")


# -- re-check ------------------------------------------------------------------------------------

def test_recheck_reports_each_step_and_passes_on_intact_evidence(tmp_path, monkeypatch):
    service, task, _, calls = completed(tmp_path, monkeypatch)
    result = service.dispatch("recheck", {"taskId": task["taskId"]})
    assert result["passed"] and len(result["steps"]) == 4 and all(s["passed"] for s in result["steps"])
    assert len(calls) == 1, "the re-check runs the full verifier, not the cache"


def test_recheck_fails_the_seal_step_when_the_blind_set_was_opened_twice(tmp_path, monkeypatch):
    service, task, directory, _ = completed(tmp_path, monkeypatch)
    ledger = directory / "work/attempts/main/claim_set_ledger.json"
    write(ledger, read(ledger) + [{"event": "OPENED", "at": "2026-09-29T05:00:00Z"}])
    steps = service.dispatch("recheck", {"taskId": task["taskId"]})["steps"]
    assert not steps[0]["passed"], "the ledger edit also changes the evidence hashes"
    assert not steps[2]["passed"]


def test_recheck_fails_the_code_step_when_the_recorded_manifest_differs(tmp_path, monkeypatch):
    service, task, directory, _ = completed(tmp_path, monkeypatch)
    identity = directory / "work/attempts/main/identity.json"
    write(identity, {**read(identity), "codeManifest": [{"path": "pinn/a.py", "sha256": "2" * 64}]})
    steps = service.dispatch("recheck", {"taskId": task["taskId"]})["steps"]
    assert not steps[1]["passed"]


def test_recheck_is_only_for_finished_runs(tmp_path, monkeypatch):
    service, _, _, _ = completed(tmp_path, monkeypatch)
    fresh = service.dispatch("create", {"prompt": "p", "frameId": "f-a", "projectId": "p-a"})["task"]
    with pytest.raises(ValueError, match="RECHECK_REQUIRES_COMPLETED"):
        service.dispatch("recheck", {"taskId": fresh["taskId"]})


# -- the guide explains, it never vouches beyond the evidence ----------------------------------

def test_the_guide_reads_its_numbers_from_the_records(tmp_path, monkeypatch):
    service, task, _, _ = completed(tmp_path, monkeypatch)
    guide = service.dispatch("get", {"taskId": task["taskId"]})["guide"]
    assert "2.52 × 10⁻⁴" in guide["headline"] and "C2" in guide["headline"]
    labels = {n["label"]: n for n in guide["numbers"]}
    assert labels["最大误差"]["value"] == "2.52 × 10⁻⁴" and "5058" in labels["最大误差"]["text"]
    assert labels["用时"]["value"] == "7 分 26 秒"
    assert [c["proof"] for c in guide["chain"]][2] == "台账：打开 1 次"
    assert any("C3" in x for x in guide["cannot"])


def test_no_guide_is_built_for_unverified_evidence():
    assert evidence_guide.build_guide(Path("."), {"taskId": "t"}, {"verified": False}) is None


def test_a_failed_reproduction_is_not_described_as_consistent(tmp_path, monkeypatch):
    service, task, directory, _ = completed(tmp_path, monkeypatch)
    verification = json.loads(json.dumps(VERIFIED))
    verification["dimensions"]["repro"]["status"] = "FAIL"
    verification["allowedClaims"] = ["C0", "C1"]
    guide = evidence_guide.build_guide(directory, task, verification)
    repro = next(n for n in guide["numbers"] if n["label"] == "独立复现")
    assert "没有通过" in repro["text"] and "C2" not in guide["headline"] and guide["can"] == []
    assert guide["chain"][4]["proof"] == "复现未通过"


def test_the_exported_page_is_static_and_escapes_what_it_quotes(tmp_path, monkeypatch):
    service, task, directory, _ = completed(tmp_path, monkeypatch)
    guide = evidence_guide.build_guide(directory, {**task, "prompt": "<script>alert(1)</script>"}, VERIFIED)
    page = evidence_guide.render_html(guide)
    assert "<script" not in page and "&lt;script&gt;" in page


def test_the_run_confirmation_states_the_estimate_and_the_limit(tmp_path, monkeypatch):
    service, task, _, _ = completed(tmp_path, monkeypatch)
    seen = []
    service.confirm = lambda title, text: seen.append(text) or True
    service._approval(task, "RUN", {"budgetSeconds": 3600, "solverConfiguration": {"configId": "leo-poisson1d-hard-bc-v1"}})
    service._approval(task, "RUN", {"budgetSeconds": 1800, "solverConfiguration": {"configId": "other"}})
    assert "预计约 8 分钟，上限 60 分钟" in seen[0] and "上限 30 分钟" in seen[1] and "预计" not in seen[1]
