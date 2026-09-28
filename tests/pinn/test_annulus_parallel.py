"""Parallel training must be the sequential training, bit for bit.

Needs torch: the governance virtualenv skips it, and
``experiments/annulus/verify_tests_under_torch.py`` executes it under the training interpreter.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from pinn.experiments_annulus import datasets_annulus as ds              # noqa: E402
from pinn.experiments_annulus import parallel_annulus as parallel        # noqa: E402

CONFIG = {
    "configId": "annulus-parallel-test",
    "network": {"hiddenLayers": 2, "width": 16, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "(R^2-s)(s-a^2)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": 60, "batchSize": 16,
                  "threads": 1, "lrPrefixSteps": 40},
    "lossWeights": {"pde": 1.0},
}


def _jobs():
    pool, dev = ds.area_uniform_interior(64, 20261230), ds.area_uniform_interior(48, 20261240)
    return [{"config": CONFIG, "pool": pool, "dev_points": dev, "collocation_count": 32, "device": "cpu",
             "seeds": {"init": 20261200 + i, "sample": 20261210 + i, "batch": 20261220 + i}}
            for i in range(3)]


def _fingerprint(run):
    return (run["weights"], run["devRelL2"] if "devRelL2" in run else None, run["completed"])


def test_parallel_results_equal_sequential_bit_for_bit_and_keep_job_order():
    jobs = _jobs()
    sequential = parallel.train_many(jobs, workers=1, log=lambda _m: None)
    side_by_side = parallel.train_many(jobs, workers=3, log=lambda _m: None)
    assert len(side_by_side) == len(sequential) == 3
    for a, b in zip(sequential, side_by_side):
        assert a["seeds"] == b["seeds"]
        assert _fingerprint(a) == _fingerprint(b)
    assert sequential[0]["weights"] != sequential[1]["weights"], "different seeds must differ"


def test_parallel_refuses_a_shared_gpu():
    jobs = [dict(job, device="cuda") for job in _jobs()[:2]]
    with pytest.raises(ValueError):
        parallel.train_many(jobs, workers=2)
