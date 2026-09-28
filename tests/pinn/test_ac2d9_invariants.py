"""AC2D-9: the label must state what the code computes, and the maths must stay put.

Final Closure Audit issue 1.  The external review derived, correctly, that with any
block partition ``max_j RMS_j(e) / RMS(e) >= 1``; the machine value 1.568e-4 is not
that quotient, because AC2D-9 normalises by the RMS of the REFERENCE SOLUTION, which
makes it a local *relative* error.  These tests pin both readings down so the label
and the implementation cannot drift apart again.
"""

import json
import math
from pathlib import Path

import pytest

from pinn.governance.poisson2d_contract import METRICS as CONTRACT_METRICS
from pinn.governance.poisson2d_contract import THRESHOLD_SOURCES
from pinn.validation.poisson2d import TILES_PER_AXIS

ROOT = Path(__file__).resolve().parents[2]
GATE5B = ROOT / "experiments/poisson2d/runs/exp2d-poisson-calibration-r1/gate5b_external.json"


def blocks(points, values, per_axis):
    out = {}
    for point, value in zip(points, values):
        key = (min(int(point[0] * per_axis), per_axis - 1), min(int(point[1] * per_axis), per_axis - 1))
        out.setdefault(key, []).append(value * value)
    return {key: math.sqrt(math.fsum(v) / len(v)) for key, v in out.items()}


def test_max_block_over_global_error_rms_is_never_below_one():
    """The reviewer's invariant, asserted on many random-ish fields: a weighted mean never exceeds its maximum."""

    per_axis = 4
    points = [((i + 0.5) / 16, (j + 0.5) / 16) for i in range(16) for j in range(16)]
    for seed in range(1, 12):
        errors = [math.sin(seed * 3.1 * x + 1.7 * seed * y) * (1.0 + 4.0 * math.exp(-((x - 0.3) ** 2) * seed))
                  for x, y in points]
        block_rms = blocks(points, errors, per_axis)
        global_rms = math.sqrt(math.fsum(e * e for e in errors) / len(errors))
        assert max(block_rms.values()) >= global_rms - 1e-15
        assert max(block_rms.values()) / global_rms >= 1.0 - 1e-12


def test_the_contract_label_names_the_reference_solution_in_the_denominator():
    formula = CONTRACT_METRICS["AC2D-9"][0]
    assert "mean_tile (u_theta - u*)^2" in formula, formula
    assert "mean_grid (u*)^2" in formula, "the denominator must be the reference solution's RMS, and must say so"
    assert "mean_grid (u_theta - u*)^2" not in formula, "the denominator is NOT the error RMS"


def test_implementation_matches_the_written_formula():
    pytest.importorskip("numpy")
    from pinn.experiments2d import datasets2d as ds
    from pinn.validation import poisson2d as validator

    quadrature, weights = ds.gauss_legendre_square(12)
    pointwise = ds.cgl_interior_square(26)
    boundary, boundary_weights = ds.boundary_nodes(12)
    fixture = validator.Fixture2D("PERTURBED", modes=((1, 1, 1.0), (3, 2, 4e-4)))
    fields = validator.sample_fixture(fixture, quadrature_points=quadrature, quadrature_weights=weights,
                                      pointwise_points=pointwise, boundary_points=boundary,
                                      boundary_weights=boundary_weights)
    result = validator.evaluate_fields(fields, grid_label="formula-check")
    exact = [math.sin(math.pi * x) * math.sin(math.pi * y) for x, y in pointwise]
    errors = [a - b for a, b in zip(fields.u_pointwise, exact)]
    by_hand = max(blocks(pointwise, errors, TILES_PER_AXIS).values()) / math.sqrt(
        math.fsum(e * e for e in exact) / len(exact))
    assert result["metrics"]["AC2D-9"]["value"] == pytest.approx(by_hand, rel=1e-12)
    # and the other reading, computed by hand, is the one that cannot go below 1
    global_error_rms = math.sqrt(math.fsum(e * e for e in errors) / len(errors))
    assert max(blocks(pointwise, errors, TILES_PER_AXIS).values()) / global_error_rms >= 1.0


def test_localized_hotspot_fails_while_a_uniform_low_error_field_passes():
    pytest.importorskip("numpy")
    from pinn.experiments2d import datasets2d as ds
    from pinn.validation import poisson2d as validator

    quadrature, weights = ds.gauss_legendre_square(12)
    pointwise = ds.cgl_interior_square(26)
    boundary, boundary_weights = ds.boundary_nodes(12)
    base = validator.sample_fixture(validator.FIXTURES[0], quadrature_points=quadrature, quadrature_weights=weights,
                                    pointwise_points=pointwise, boundary_points=boundary,
                                    boundary_weights=boundary_weights)
    threshold = validator.THRESHOLDS["AC2D-9"]
    reference_rms = math.sqrt(math.fsum(math.sin(math.pi * x) ** 2 * math.sin(math.pi * y) ** 2
                                        for x, y in pointwise) / len(pointwise))
    # uniform low error: every block sits far below the threshold
    uniform = [value + 0.2 * threshold * reference_rms for value in base.u_pointwise]
    passed = validator.evaluate_fields(validator.Fields2D(**{**base.__dict__, "u_pointwise": uniform}),
                                       grid_label="uniform-low")
    assert "AC2D-9" not in passed["failedMustCriteria"]
    # one block, ten times the threshold: the criterion must catch it
    spike = list(base.u_pointwise)
    touched = 0
    for index, (x, y) in enumerate(pointwise):
        if 0.5 <= x < 0.625 and 0.25 <= y < 0.375:
            spike[index] += 10.0 * threshold * reference_rms
            touched += 1
    assert touched > 0
    caught = validator.evaluate_fields(validator.Fields2D(**{**base.__dict__, "u_pointwise": spike}),
                                       grid_label="hotspot")
    assert "AC2D-9" in caught["failedMustCriteria"]
    assert caught["diagnostics"]["worstTile"]["xRange"] == [0.5, 0.625]


def test_the_stored_artifact_is_the_quotient_of_its_own_components():
    gate = json.loads(GATE5B.read_text(encoding="utf-8"))
    for seed in gate["perSeed"]:
        quotient = seed["diagnostics"]["worstTile"]["rms"] / seed["diagnostics"]["referenceRmsPointwise"]
        assert seed["metrics"]["AC2D-9"] == pytest.approx(quotient, rel=1e-15, abs=0.0)
        # far below one, which is only possible because the denominator is the reference RMS
        assert seed["metrics"]["AC2D-9"] < 1e-3
        assert seed["metrics"]["AC2D-9"] > seed["metrics"]["AC2D-1"], (
            "the per-block criterion must dominate the global one on the same solution")


def test_threshold_source_records_the_dimension_verdict():
    source = THRESHOLD_SOURCES["AC2D-9"]
    assert "DIMENSION-SENSITIVE" in source["dimensionVerdict"]
    assert "protocol rule" in source["source"]
