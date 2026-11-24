"""Tier-1 Red Team rules (downgrade only, preregistered thresholds) and the scale-aware hard parameterization."""

import json
from pathlib import Path

import pytest

from pinn.experiments import redteam

ROOT = Path(__file__).resolve().parents[2]


def test_verdicts_follow_the_preregistered_lines_and_never_upgrade():
    base = {"qoi1": 0.6366, "residualMax": 0.05, "e2": 2e-4}
    p1 = {"id": "P1"}
    assert redteam.verdict(p1, base, {"qoi1": 0.6366 * 1.005, "residualMax": 0.05, "e2": 3e-4})["status"] == "PASS"
    assert redteam.verdict(p1, base, {"qoi1": 0.6366 * 1.03, "residualMax": 0.05, "e2": 3e-4})["status"] == "PARTIAL"
    assert redteam.verdict(p1, base, {"qoi1": 0.6366 * 1.10, "residualMax": 0.05, "e2": 3e-4})["status"] == "FAIL"
    p4 = {"id": "P4"}
    assert redteam.verdict(p4, base, {"qoi1": 0.6366, "residualMax": 0.9, "e2": 3e-4})["status"] == "FAIL"   # residual x18 with dtype
    assert redteam.verdict(p4, base, {"qoi1": 0.6366, "residualMax": 0.06, "e2": 3e-4})["status"] == "PASS"
    ids = [e["id"] for e in redteam.TIER1]
    assert ids == ["P1", "P4", "P6", "P7", "P8", "P9", "P11", "P16"]
    assert all(e.get("reason") for e in redteam.TIER1 if e.get("applicable") is False)


def test_hard_parameterization_vanishes_at_both_ends_of_a_rescaled_domain():
    pytest.importorskip("torch")
    from pinn.experiments import pinn_torch

    config = json.loads((ROOT / "experiments/poisson1d/configs/exp3_hard_bc.json").read_text(encoding="utf-8"))
    for L in (1.0, 2.0):
        model = pinn_torch.build_model(config, 3, domain_length=L)
        fld = pinn_torch.fields(model, [0.0, 0.3, 1.0], domain_scale=L)
        assert fld["u"][0] == 0.0 and fld["u"][2] == 0.0 and fld["u"][1] != 0.0
