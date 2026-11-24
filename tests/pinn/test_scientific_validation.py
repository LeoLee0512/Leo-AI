"""Diagnostic-only scientific, adversarial and independent-reference checks."""

import ast
from dataclasses import replace
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from pinn.validation.fixtures import FIXTURES
from pinn.validation.poisson import (
    THRESHOLDS, ValidationInputError, check_metric_values, evaluate_samples,
    load_candidate_protocol, sample_callable_fixture,
)
from scientific_reference.poisson_fdm import refinement_diagnostic, solve_poisson


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def protocol():
    return load_candidate_protocol(ROOT)


@pytest.fixture
def analytic_samples(protocol):
    fixture = FIXTURES[0]
    return sample_callable_fixture(protocol, fixture.solution, fixture.first_derivative, fixture.second_derivative)


def test_analytic_control_is_accurate_but_cannot_mint_a_claim(protocol, analytic_samples):
    result = evaluate_samples(protocol, analytic_samples)
    assert result["componentCriteriaSatisfied"] is True
    assert result["failedMustCriteria"] == result["failedShouldCriteria"] == []
    assert result["evaluationScope"] == "VALIDATOR_COMPONENT"
    assert result["workflowStatus"] == result["claimStatus"] == "NOT_APPLICABLE"
    assert result["trainingApplicable"] is False
    assert result["lockStatus"] == "NOT_EXECUTED"
    assert all(metric["value"] < 1e-12 for metric in result["metrics"].values())
    assert "PASS" not in json.dumps(result)


def test_protocol_reads_exact_assets_without_generating_nodes(protocol, monkeypatch):
    import pinn.governance.nodes as nodes
    def forbidden(*args, **kwargs):
        raise AssertionError("runtime node regeneration is forbidden")
    monkeypatch.setattr(nodes, "generate_cgl2000", forbidden)
    monkeypatch.setattr(nodes, "generate_gl512", forbidden)
    assert load_candidate_protocol(ROOT) == protocol


def test_deterministic_sampling_has_no_seed_and_is_repeatable(protocol, analytic_samples):
    first = evaluate_samples(protocol, analytic_samples)
    second = evaluate_samples(load_candidate_protocol(ROOT), analytic_samples)
    assert first == second
    assert first["sampling"]["evaluationSeed"] == "NOT_APPLICABLE"
    assert protocol.quadrature_nodes[0] > 0.0 and protocol.quadrature_nodes[-1] < 1.0
    assert protocol.pointwise_nodes[0] == 0.0 and protocol.pointwise_nodes[-1] == 1.0


@pytest.mark.parametrize("fixture_id,relative_l2,residual", [
    ("B1b", 2.0, 2.0), ("B3", math.sqrt(2.0) * 0.3, 0.0),
    ("B4", 0.002, 0.032), ("B6", 0.2, 5.0), ("ZERO_FIELD_CONTROL", 1.0, 1.0),
])
def test_known_bad_fields_rejected(protocol, fixture_id, relative_l2, residual):
    fixture = next(item for item in FIXTURES if item.fixture_id == fixture_id)
    samples = sample_callable_fixture(protocol, fixture.solution, fixture.first_derivative, fixture.second_derivative)
    result = evaluate_samples(protocol, samples)
    assert result["componentCriteriaSatisfied"] is False
    assert result["metrics"]["AC-1"]["value"] == pytest.approx(relative_l2, rel=1e-12, abs=1e-14)
    assert result["metrics"]["AC-4"]["value"] == pytest.approx(residual, rel=1e-12, abs=1e-14)
    if fixture_id == "B3":
        assert "AC-3" in result["failedMustCriteria"]
        assert result["metrics"]["AC-3"]["value"] == pytest.approx(0.3)
        assert result["diagnostics"]["unweightedBoundaryMeanSquare"] == pytest.approx(0.09)
    if fixture_id in {"B4", "B6"}:
        assert {"AC-1", "AC-4"}.issubset(result["failedMustCriteria"])
        assert max(abs(-fixture.second_derivative(i / fixture.mode)
                       - math.pi**2 * math.sin(math.pi * i / fixture.mode))
                   for i in range(1, fixture.mode)) < 1e-12
        assert result["metrics"]["AC-3"]["value"] < 1e-14


def test_ac2_uses_discrete_cgl_reference_maximum(protocol, analytic_samples):
    altered = replace(analytic_samples, u_pointwise=tuple(u + 0.02 for u in analytic_samples.u_pointwise),
                      u_boundary=tuple(u + 0.02 for u in analytic_samples.u_boundary))
    result = evaluate_samples(protocol, altered)
    denominator = max(abs(math.sin(math.pi * x)) for x in protocol.pointwise_nodes)
    assert denominator < 1.0  # This grid has no midpoint; exact-one shortcut is wrong.
    assert result["metrics"]["AC-2"]["value"] == pytest.approx(0.02 / denominator, abs=1e-15)
    assert result["diagnostics"]["absoluteLinf"] == pytest.approx(0.02, abs=1e-15)


def test_absolute_l2_is_quadrature_norm_not_training_loss(protocol, analytic_samples):
    altered = replace(analytic_samples, u_quadrature=tuple(u + 0.3 for u in analytic_samples.u_quadrature))
    result = evaluate_samples(protocol, altered)
    assert result["diagnostics"]["absoluteL2"] == pytest.approx(0.3, abs=1e-14)
    assert result["metrics"]["AC-1"]["value"] == pytest.approx(0.3 * math.sqrt(2), abs=1e-14)


@pytest.mark.parametrize("i,threshold", list(enumerate(THRESHOLDS, 1)))
def test_strict_threshold_never_accepts_equality(i, threshold):
    metrics = {f"AC-{j}": 0.0 for j in range(1, 9)}
    metrics[f"AC-{i}"] = threshold
    assert check_metric_values(metrics)[f"AC-{i}"] is False
    metrics[f"AC-{i}"] = math.nextafter(threshold, 0.0)
    assert check_metric_values(metrics)[f"AC-{i}"] is True


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, -0.01, "0", True, 0])
def test_invalid_metric_rejected(invalid):
    metrics = {f"AC-{j}": 0.0 for j in range(1, 9)}
    metrics["AC-1"] = invalid
    with pytest.raises(ValidationInputError):
        check_metric_values(metrics)


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_metric_set_must_be_complete_and_exact(mutation):
    metrics = {f"AC-{j}": 0.0 for j in range(1, 9)}
    if mutation == "missing":
        del metrics["AC-8"]
    else:
        metrics["training_loss"] = 0.0
    with pytest.raises(ValidationInputError, match="exactly"):
        check_metric_values(metrics)


@pytest.mark.parametrize("field", ["u_quadrature", "du_quadrature", "d2u_quadrature",
                                  "u_pointwise", "u_boundary", "du_boundary", "forcing_quadrature"])
@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
def test_every_raw_field_rejects_nonfinite(protocol, analytic_samples, field, invalid):
    values = list(getattr(analytic_samples, field))
    values[0] = invalid
    with pytest.raises(ValidationInputError, match="finite"):
        evaluate_samples(protocol, replace(analytic_samples, **{field: values}))


@pytest.mark.parametrize("mutation,expected", [
    ({"domain": (0.0, 2.0)}, "domain"),
    ({"boundary_values": (0.0, 0.3)}, "boundary"),
    ({"equation_binding": "u'' = f"}, "equation"),
    ({"derivative_method": "FINITE_DIFFERENCE"}, "derivative"),
    ({"device": "cuda"}, "CPU"),
    ({"boundary_coordinates": (1e-12, 1.0)}, "exact protocol"),
    ({"u_boundary": (0.0,)}, "shape"),
    ({"u_boundary": ((0.0,), (0.0,))}, "float64"),
    ({"u_boundary": ("0.0", 0.0)}, "float64"),
])
def test_wrong_domain_bc_shape_or_metadata_rejected(protocol, analytic_samples, mutation, expected):
    with pytest.raises(ValidationInputError, match=expected):
        evaluate_samples(protocol, replace(analytic_samples, **mutation))


def test_wrong_forcing_is_rejected_even_with_correct_solution(protocol, analytic_samples):
    altered = replace(analytic_samples, forcing_quadrature=tuple(-f for f in analytic_samples.forcing_quadrature))
    with pytest.raises(ValidationInputError, match="forcing"):
        evaluate_samples(protocol, altered)


def test_boundary_and_pointwise_outputs_cannot_disagree(protocol, analytic_samples):
    with pytest.raises(ValidationInputError, match="outputs disagree"):
        evaluate_samples(protocol, replace(analytic_samples, u_boundary=(0.1, 0.1)))


def test_validation_coordinate_reordering_is_rejected(protocol, analytic_samples):
    with pytest.raises(ValidationInputError, match="exact protocol"):
        evaluate_samples(protocol, replace(analytic_samples, quadrature_coordinates=protocol.quadrature_nodes[::-1]))


def test_finite_inputs_that_overflow_cannot_produce_metrics(protocol, analytic_samples):
    with pytest.raises(ValidationInputError, match="overflow|invalid|finite"):
        evaluate_samples(protocol, replace(analytic_samples, u_quadrature=(1e308,) * 512))


def test_finite_criteria_do_not_hide_overflowed_auxiliary_diagnostic(protocol, analytic_samples):
    values = list(analytic_samples.u_pointwise)
    values[0] = values[-1] = 1e308
    with pytest.raises(ValidationInputError, match="finite"):
        evaluate_samples(protocol, replace(analytic_samples, u_pointwise=values, u_boundary=(1e308, 1e308)))


def test_mutating_protocol_in_memory_cannot_bypass_asset_binding(protocol, analytic_samples):
    altered = replace(protocol, quadrature_weights=(1.0 / 512.0,) * 512)
    with pytest.raises(ValidationInputError, match="payload"):
        evaluate_samples(altered, analytic_samples)


@pytest.mark.parametrize("field", ["spec_sha256", "protocol_sha256", "reference_sha256"])
def test_fabricated_candidate_metadata_cannot_be_echoed_as_provenance(protocol, analytic_samples, field):
    with pytest.raises(ValidationInputError, match="metadata hash"):
        evaluate_samples(replace(protocol, **{field: "a" * 64}), analytic_samples)


def _candidate_copy(destination):
    for name in ("governance/POISSON_1D_V1.0_spec.draft.json", "governance/POISSON_1D_V1.0_protocol.draft.json",
                 "pinn/reference/analytic_poisson.py", "specs/poisson-1d/v1.0/assets/GL512_nodes.npy",
                 "specs/poisson-1d/v1.0/assets/GL512_weights.npy", "specs/poisson-1d/v1.0/assets/CGL2000.npy"):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)


@pytest.mark.parametrize("mutation", ["hash", "missing", "reference", "threshold", "formula", "domain", "duplicate", "line_endings"])
def test_tampered_or_missing_candidate_inputs_rejected(tmp_path, mutation):
    _candidate_copy(tmp_path)
    if mutation == "missing":
        (tmp_path / "specs/poisson-1d/v1.0/assets/CGL2000.npy").unlink()
    elif mutation == "hash":
        path = tmp_path / "specs/poisson-1d/v1.0/assets/GL512_nodes.npy"
        path.write_bytes(path.read_bytes()[:-1] + b"\xff")
    elif mutation == "reference":
        path = tmp_path / "pinn/reference/analytic_poisson.py"
        path.write_bytes(path.read_bytes() + b"\n# changed\n")
    else:
        path = tmp_path / "governance/POISSON_1D_V1.0_spec.draft.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "threshold":
            document["acceptanceCriteria"]["value"][0]["threshold"] = 0.9
        elif mutation == "formula":
            document["validationMetrics"]["value"][1]["definition"] = "max error divided by 1"
        elif mutation == "domain":
            document["domain"]["value"]["closure"] = "[0,2]"
        raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if mutation == "duplicate":
            raw = raw.replace(b'"specId":', b'"specId": "duplicate-value",\n  "specId":', 1)
        elif mutation == "line_endings":
            raw = raw.replace(b"\n", b"\r\n")
        path.write_bytes(raw)
    with pytest.raises(ValidationInputError):
        load_candidate_protocol(tmp_path)


def test_independent_fdm_has_no_pinn_imports():
    for source in (ROOT / "scientific_reference").glob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("pinn") for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("pinn")


def test_independent_fdm_refinement_is_second_order():
    result = refinement_diagnostic()
    assert result["componentCriteriaSatisfied"] is True
    assert result["observedSequence"] == [32, 64, 128, 256, 512, 1024, 2048]
    assert len(result["orders"]) == 6
    assert all(1.8 <= row["order"] <= 2.2 for row in result["orders"][-4:])
    assert result["solutions"][-1]["interior_max_error"] < 2e-7
    assert all(row["discrete_residual_max"] < 1e-8 for row in result["solutions"])
    assert result["claimStatus"] == "NOT_APPLICABLE"
    assert result["acceptanceReference"] is False


def test_single_grid_b11_reports_absent_orders_without_fabricating_a_measurement():
    result = refinement_diagnostic((4,))
    assert result["componentCriteriaSatisfied"] is False
    assert result["orders"] == []
    assert any("sequence absent" in text for text in result["findings"])
    assert not any("outside" in text for text in result["findings"])


@pytest.mark.parametrize("bad", [True, 0, 1, 3.5])
def test_fdm_malformed_resolution_rejected(bad):
    with pytest.raises(ValueError):
        solve_poisson(bad)


@pytest.mark.parametrize("forcing", [lambda x: math.nan, lambda x: math.inf])
def test_fdm_nonfinite_source_rejected(forcing):
    with pytest.raises(ValueError, match="non-finite"):
        solve_poisson(32, forcing=forcing)


def test_fdm_finite_solution_with_overflowed_residual_is_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        solve_poisson(32, forcing=lambda x: 1e308, boundary=(8e307, 8e307))


def test_fdm_wrong_sign_and_boundary_disagree_with_analytic_reference():
    assert solve_poisson(64, forcing=lambda x: -math.pi**2 * math.sin(math.pi * x)).interior_max_error > 1.9
    assert solve_poisson(64, boundary=(0.3, 0.3)).interior_max_error > 0.3


def test_manual_derivation_checked_by_independent_finite_differences():
    # Separate arithmetic path: evaluate u only, approximate u'', and compare f.
    # This is a reference diagnostic, never a finite-difference AC derivative.
    h = 1e-4
    errors = []
    for i in range(1, 100):
        x = i / 100.0
        second = (math.sin(math.pi * (x + h)) - 2.0 * math.sin(math.pi * x)
                  + math.sin(math.pi * (x - h))) / h**2
        errors.append(abs(-second - math.pi**2 * math.sin(math.pi * x)))
    assert max(errors) < 1e-6
    assert abs(math.sin(math.pi)) < 1e-14


def test_diagnostic_evidence_command_refuses_overwrite(tmp_path):
    output = tmp_path / "new-component-evidence"
    command = [sys.executable, "-m", "pinn.validation.diagnose", "--output", str(output)]
    first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert first.returncode == 0, first.stderr
    saved = {path.name: path.read_bytes() for path in output.iterdir() if path.is_file()}
    metadata = json.loads(saved["metadata.json"])
    assert metadata["evaluationScope"] == "VALIDATOR_COMPONENT"
    assert metadata["formalGatesExecuted"] == []
    second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert second.returncode != 0
    assert "FileExistsError" in second.stderr
    assert saved == {path.name: path.read_bytes() for path in output.iterdir() if path.is_file()}
