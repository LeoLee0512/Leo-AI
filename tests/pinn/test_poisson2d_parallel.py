"""2.2.11: parallel 2D training must be the sequential training, bit for bit.

Needs torch: the governance virtualenv skips it; it runs under the training interpreter
(the installed science-a environment) before a release.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from pinn.experiments2d import datasets2d as ds                  # noqa: E402
from pinn.experiments2d import parallel2d as parallel            # noqa: E402
from pinn.experiments2d import redteam2d                         # noqa: E402

CONFIG = {
    "configId": "poisson2d-parallel-test",
    "network": {"hiddenLayers": 2, "width": 16, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "x(1-x)y(1-y)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": 60, "batchSize": 16, "threads": 1},
    "lossWeights": {"pde": 1.0},
    "sampling": {"poolSize": 64, "poolSeed": 20261230, "collocationCount": 32},
}


def _jobs(perturbation=None):
    pool, dev = ds.uniform_interior(64, 20261230), ds.uniform_interior(48, 20261240)
    return [{"config": CONFIG, "pool": pool, "dev_points": dev, "collocation_count": 32,
             "seeds": {"init": 20261200 + i, "sample": 20261210 + i, "batch": 20261220 + i},
             **({"perturbation": perturbation} if perturbation else {})}
            for i in range(3)]


def test_parallel_results_equal_sequential_bit_for_bit_and_keep_job_order():
    jobs = _jobs()
    sequential = parallel.train_many(jobs, workers=1, log=lambda _m: None)
    side_by_side = parallel.train_many(jobs, workers=3, log=lambda _m: None)
    assert len(side_by_side) == len(sequential) == 3
    for a, b in zip(sequential, side_by_side):
        assert a["seeds"] == b["seeds"]
        assert (a["weights"], a["devRelL2"], a["completed"]) == (b["weights"], b["devRelL2"], b["completed"])
    assert sequential[0]["weights"] != sequential[1]["weights"], "different seeds must differ"


def test_the_parallel_job_is_the_function_the_runner_called_before():
    """One job through the pool equals a direct call of the training function the runner used."""
    from pinn.experiments2d import pinn_torch2d as pinn2d

    job = _jobs()[0]
    direct = pinn2d.train_run(job["config"], job["pool"], job["dev_points"], job["seeds"],
                              collocation_count=job["collocation_count"])
    pooled = parallel.train_many([job, _jobs()[1]], workers=2, log=lambda _m: None)[0]
    assert direct["weights"] == pooled["weights"] and direct["devRelL2"] == pooled["devRelL2"]


def test_tier1_measures_the_same_retrains_whether_they_ran_side_by_side_or_not(monkeypatch):
    """Tier-1 trains its perturbations first, then measures them in the fixed order."""
    seen = []

    def fake_train_many(jobs, workers=1, log=print):
        seen.append((workers, [job["perturbation"] for job in jobs]))
        return [{"weights": None, "completed": True, "nanEncountered": False, "elapsedSeconds": 0.0} for _ in jobs]

    monkeypatch.setattr(parallel, "train_many", fake_train_many)
    monkeypatch.setattr(redteam2d.pinn2d, "model_from_weights", lambda *a, **k: None)
    monkeypatch.setattr(redteam2d, "measure", lambda *a, **k: {"e2": 1e-4, "q": 1.0})
    monkeypatch.setattr(redteam2d, "verdict", lambda entry, base, pert: {"status": "PASS", "deltaQ": 0.0, "notes": ""})
    job = _jobs()[0]
    report = redteam2d.run_tier1(CONFIG, job["pool"], job["dev_points"], [], [], {"seeds": job["seeds"], "weights": None},
                                 log=lambda _m: None, workers=7)
    applicable = [e for e in redteam2d.TIER1 if e.get("applicable", True) is not False]
    assert seen[0][0] == 7 and len(seen[0][1]) == len(applicable)
    assert [r["id"] for r in report["results"]] == [e["id"] for e in redteam2d.TIER1]
    assert report["passed"] is True
