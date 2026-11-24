"""3.2.2: the annulus as the third verified product template (r3's method, 8 product blind grids).

Pure-Python checks run everywhere; the ones that build the train / dev sets need numpy and run under
the science interpreter (like the other 2D and annulus tests).
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from leo_shell.research import ResearchService
from leo_shell.research_draft import (PROMPT, TEMPLATE_ANNULUS, TEMPLATE_METHOD_ANNULUS, TEMPLATES,
                                      validate_draft)
from pinn.research import worker
from pinn.research.context import RunContext, using
from pinn.research.quota import CAPACITY, annulus_grid, claim_grid_candidates, quota

ROOT = Path(__file__).resolve().parents[2]
CALIBRATION = {  # DAC-M0..M3 (experiments/annulus/CALIBRATION_CLAIM_REGISTRATION_20260929.json)
    "radial": {34, 36, 38, 42}, "angular": {125, 127, 129, 131}, "cgl": {50, 54, 56, 60},
    "pointwiseAngular": {33, 35, 37, 39}, "offsets": {0.011, 0.013, 0.017, 0.019, 0.007, 0.009}}


def raw(**extra):
    base = {"objective": "环形域校准", "equation": TEMPLATE_ANNULUS["equation"], "domain": {"annulus": [0.35, 1]},
            "boundary": {"inner": 0, "outer": 0}, "assumptions": [], "missing": [], "conflicts": []}
    base.update(extra)
    return base


# -- blind grids ----------------------------------------------------------------------------

def test_there_are_eight_annulus_grids_apart_from_the_calibration_pool():
    grids = list(claim_grid_candidates("annulus"))
    assert CAPACITY["annulus"] == 8 and len(grids) == 8
    assert [name for name, _, _ in grids][:2] == ["ANN-Q44-A137", "ANN-Q46-A139"]
    specs = [grid for _, grid, _ in grids]
    for key, used in (("quadratureRadialOrder", CALIBRATION["radial"] | {40}),
                      ("quadratureAngularCount", CALIBRATION["angular"] | {128}),
                      ("pointwiseCglCount", CALIBRATION["cgl"]),
                      ("pointwiseAngularCount", CALIBRATION["pointwiseAngular"])):
        values = [g[key] for g in specs]
        assert len(set(values)) == 8 and not set(values) & used, key
    offsets = [g["angularOffset"] for g in specs] + [g["pointwiseAngularOffset"] for g in specs]
    assert len(set(offsets)) == 16 and not set(offsets) & CALIBRATION["offsets"]
    assert annulus_grid(7)["quadratureRadialOrder"] == 58


def test_the_annulus_quota_counts_its_own_grids_only(tmp_path):
    # A fresh install already counts the grid the 3.2.2 smoke burnt (registered in the repository).
    fresh = quota(tmp_path, ROOT, "annulus")
    assert fresh == {"capacity": 8, "used": 1, "remaining": 7, "family": "annulus"}
    problems = tmp_path / "tasks/research-x/work/experiments/annulus/problems"
    problems.mkdir(parents=True)
    (problems / "pdef-research-x-claim-ANN-Q46-A139.json").write_text("{}", encoding="utf-8")
    (problems / "pdef-research-x-claim-DAC-M3.json").write_text("{}", encoding="utf-8")
    # A product grid counts; a calibration (DAC) grid does not.
    assert quota(tmp_path, ROOT, "annulus")["used"] == 2
    # The other families keep their own 32.
    assert quota(tmp_path, ROOT, "poisson2d")["capacity"] == 32


def test_the_calibration_grids_are_registered_and_match_their_recorded_hashes():
    from pinn.experiments_annulus import datasets_annulus as ds
    from pinn.governance.canonical import canonical_sha256
    from pinn.governance.evaluation_sets import sample_set_hash
    note = json.loads((ROOT / "experiments/annulus/CALIBRATION_CLAIM_REGISTRATION_20260929.json").read_text("utf-8"))
    assert sorted(note["members"]) == ["DAC-M0", "DAC-M1", "DAC-M2", "DAC-M3"]
    for name, record in note["members"].items():
        document = json.loads((ROOT / record["claimFile"]).read_text("utf-8"))
        assert canonical_sha256(document) == record["artifactHash"] and sample_set_hash(document) == record["sampleSetHash"]
        regenerated = ds.claim_pool_manifests({name: record["grid"]}, label="pdef-annulus-poisson-v1")[name]
        assert canonical_sha256(regenerated) == record["artifactHash"]
    identities, history = worker.historical_claims(ROOT, ROOT / "no-such-research-root", "annulus")
    # The four calibration grids plus the 3.2.2 smoke grid (ANN-Q44-A137, registered 2026-09-30).
    smoke = json.loads((ROOT / "experiments/annulus/SMOKE_3_2_2_CLAIM_REGISTRATION_20260930.json").read_text("utf-8"))
    assert len(history) == 5 and any(key.endswith(Path(smoke["claimFile"]).name) for key in history)
    assert len(identities) > sum(r["sampleCount"] for r in note["members"].values())


def test_no_product_grid_shares_a_sample_with_another_or_with_the_calibration_pool():
    from pinn.experiments_annulus import datasets_annulus as ds
    identities, _ = worker.historical_claims(ROOT, ROOT / "no-such-research-root", "annulus")
    seen = set(identities)
    for name, grid, _ in claim_grid_candidates("annulus"):
        points = set(ds.claim_member_points(grid))
        assert not points & seen, name
        seen |= points


# -- product configuration ------------------------------------------------------------------

def test_the_product_configuration_is_r3s_method():
    config = json.loads((ROOT / worker.CONFIG_ANNULUS).read_text("utf-8"))
    assert worker.CONFIG_ANNULUS in worker.IDENTITY_EXTRAS and worker.FAMILIES["annulus"]["config"] == worker.CONFIG_ANNULUS
    assert config["optimizer"]["steps"] == 240000 and config["optimizer"]["lrPrefixSteps"] == 120000
    assert (config["seedProtocol"]["initBase"], config["seedProtocol"]["sampleBase"], config["seedProtocol"]["batchBase"]) == (
        20263500, 20263600, 20263700)
    assert config["network"]["hiddenLayers"] == 4 and config["network"]["width"] == 64
    assert config["preregistration"]["epsilonSpec"] == 1e-3
    assert config["reproduction"]["devRelL2MedianAbsDiff"] == 1e-4 and config["reproduction"]["devRelL2MedianRelDiff"] == 0.5
    assert "claimPool" not in config and "codeIdentityExtraFiles" not in config
    # The r3 run this method was accepted on, as recorded in the repository.
    summary = json.loads((ROOT / "experiments/annulus/runs/exp-geometry1-annulus-poisson-r3/RUN_SUMMARY.json").read_text("utf-8"))
    assert summary["configId"] == "annulus-poisson-hard-bc-v1-r3-240k" and "C2" in summary["allowedClaimsFinal"]
    # What the person confirms restates the same numbers.
    method = TEMPLATE_METHOD_ANNULUS
    assert method["configId"] == config["configId"] and "24 万步" in method["training"] and "12 万步" in method["training"]
    assert "20263500" in method["seeds"] and "1.31" in method["acceptance"]
    assert worker.FAMILIES["annulus"]["budgetSeconds"] == 57600 and worker.FAMILIES["annulus"]["workers"] == 10


# -- drafts ---------------------------------------------------------------------------------

def test_the_annulus_draft_is_recognized_only_exactly():
    assert "annulus-v1" in TEMPLATES and '{"annulus": [0.35, 1]}' in PROMPT and "exactly three verified problems" in PROMPT
    assert validate_draft(raw(), "p")["templateId"] == "annulus-v1"
    spelled = "-Δu = f, u* = (1-x^2-y^2)(x^2+y^2-0.1225)(1+0.2 sin(πx) cos(2πy)+0.1x-0.1y)"
    assert validate_draft(raw(equation=spelled), "p")["templateId"] == "annulus-v1"
    for change in ({"domain": {"annulus": [0.3, 1]}}, {"boundary": {"inner": 0, "outer": 1}},
                   {"equation": "-(u_xx+u_yy)=1"}, {"missing": ["源项"]}, {"domain": {"annulus": [True, 1]}}):
        draft = validate_draft(raw(**change), "p")
        assert draft["templateId"] is None and draft["unsupportedReasons"], change
    assert "环形" in validate_draft(raw(domain={"annulus": [0.3, 1]}), "p")["unsupportedReasons"][0]


def make(tmp_path, draft_raw):
    paths = SimpleNamespace(root=tmp_path, user=tmp_path / "user")
    for name in ("code", "python-a", "python-b"):
        (tmp_path / name).mkdir(exist_ok=True)
    return ResearchService(paths, confirm=lambda *_: True, background=False,
                           draft_provider=lambda frame, prompt: validate_draft(draft_raw, prompt),
                           runtime={"codeRoot": str(tmp_path / "code"), "pythonA": str(tmp_path / "python-a"),
                                    "pythonB": str(tmp_path / "python-b")})


def test_an_annulus_task_shows_its_quota_family_and_timings(tmp_path):
    service = make(tmp_path, raw())
    task = service.dispatch("create", {"prompt": "环形域", "frameId": "f", "projectId": "p"})["task"]
    task = service.dispatch("draft", {"taskId": task["taskId"], "expectedVersion": task["version"]})["task"]
    view = service.dispatch("get", {"taskId": task["taskId"]})
    assert view["family"] == "annulus" and view["quota"]["capacity"] == 8 and view["prepareLimitMinutes"] == 30
    listed = service.dispatch("list", {"frameId": "f"})["tasks"][0]
    assert listed["family"] == "annulus" and listed["hasDraft"] is True
    from leo_shell.research_estimates import ESTIMATE_MINUTES
    # Measured by the 3.2.2 sandbox smoke: 341 minutes from the run confirmation to COMPLETED.
    assert 330 <= ESTIMATE_MINUTES["leo-annulus-poisson-hard-bc-v1"] <= 360


# -- product mode of the runner ---------------------------------------------------------------

def test_in_product_mode_the_annulus_runner_keeps_everything_in_the_task(tmp_path):
    from pinn.experiments_annulus import runner_annulus as runner
    outside = runner.pool_members("pdef-nowhere")
    with using(RunContext(ROOT, tmp_path / "work")):
        assert runner.repo_root() == ROOT.resolve()
        problems = tmp_path / "work" / runner.PROBLEMS_DIR
        problems.mkdir(parents=True)
        (problems / "pdef-x-claim-pool.json").write_text(json.dumps({"members": {"ANN-Q44-A137": {"grid": {}}}}), "utf-8")
        assert list(runner.pool_members("pdef-x")["members"]) == ["ANN-Q44-A137"]
        assert runner.load_registry() == {}
        attempt = runner.AttemptAnnulus(config_path=ROOT / worker.CONFIG_ANNULUS, attempt_id="main", problem_id="pdef-x",
                                        revision=1, out_root=tmp_path / "work/attempts")
        assert attempt.ledger_path == tmp_path / "work" / runner.LEDGER_DIR / "pdef-x.json"
        assert attempt.summary["constitutionVersion"] == runner.CONSTITUTION_VERSION
        assert attempt.summary["startedAt"].endswith("Z")
    assert outside == {"members": {}}
    historical = runner.AttemptAnnulus(config_path=ROOT / worker.CONFIG_ANNULUS, attempt_id="h", problem_id="pdef-y",
                                       revision=1, out_root=tmp_path / "h")
    assert historical.ledger_path == runner.LEDGER_DIR / "pdef-y.json" and "constitutionVersion" not in historical.summary


def test_the_worker_builds_an_annulus_attempt_the_way_the_product_runs_it(tmp_path):
    attempt = worker._attempt("annulus", ROOT, tmp_path / "work", "pdef-t", attempt_id="reproduction",
                              claim_member="ANN-Q44-A137", seed_offset=10000,
                              reproduction_of=tmp_path / "work/attempts/main", workers=3)
    assert attempt.reproduction_of == "main" and attempt.stop_after_gate == 4 and attempt.device == "cpu"
    assert attempt.workers == 3 and attempt.seed_offset == 10000
    main = worker._attempt("annulus", ROOT, tmp_path / "work", "pdef-t", attempt_id="main", claim_member="ANN-Q44-A137")
    assert main.reproduction_of is None and main.stop_after_gate is None


def test_the_annulus_trust_report_names_the_binding_criterion():
    from pinn.experiments_annulus import report_annulus
    assert "ACA-9" in "".join(report_annulus.SCOPE_LINES_ANNULUS) and "1.31" in "".join(report_annulus.SCOPE_LINES_ANNULUS)
    assert "analytic_annulus.py" in report_annulus.REFERENCE_LINE_ANNULUS


# -- preparation (needs numpy for the area-uniform train and dev sets) -------------------------

def test_the_annulus_base_sets_and_first_candidate_are_isolated():
    pytest.importorskip("numpy")
    from pinn.experiments_annulus import datasets_annulus as ds
    config = json.loads((ROOT / worker.CONFIG_ANNULUS).read_text("utf-8"))
    base = worker._base_sets("annulus", config, ROOT, "t")
    name, grid, _ = next(claim_grid_candidates("annulus"))
    base["claim"] = ds.claim_pool_manifests({name: grid}, label="pdef-t")[name]
    assert ds.isolation_report(base, min_separation=config["sets"]["minSeparation"])["errors"] == []
