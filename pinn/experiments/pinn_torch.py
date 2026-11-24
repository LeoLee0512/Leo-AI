"""The PINN under test: a small MLP trained with Adam, CPU float64, deterministic.

Everything that shapes the result is read from the frozen experiment config
(architecture, optimizer, learning-rate schedule, loss weights, steps, batch
size, collocation count, boundary enforcement).  Three seeds enter a run
(Constitution 10.1): ``init``, ``sample``, ``batch``.  Training never sees D_dev
or D_claim: the dev error is logged for diagnostics only and nothing in the
loop reads it (fixed step count, no early stopping -- protocol L4).

Boundary enforcement (``network.outputParameterization``):
* ``"identity"`` (default) -- u = N(x); the Dirichlet data enters the loss as
  ``lossWeights.bc * mean(u(0)^2, u(1)^2)`` (soft constraint);
* ``"x(1-x)N"`` -- u = x (1 - x) N(x); u(0) = u(1) = 0 by construction (hard
  constraint, a different hypothesis class; the bc loss term is identically 0).

``perturbation`` (Red Team Tier-1, one retrain each; never used by formal runs):
``{"dtype": "float32"}`` (P4), ``{"activation": "sin"}`` (P16),
``{"optimizer": "LBFGS"}`` (P9), ``{"domainScale": L}`` (P8: train on y in
[0, L] for v(y) = u(y / L), map back), ``{"dropFraction": 0.1}`` (P6),
``{"resampleSeed": s}`` (P1: another collocation draw of the same pool).
"""

from __future__ import annotations

import math
import time
from typing import Any, Mapping, Sequence

from pinn.reference import analytic_poisson as reference

ACTIVATIONS = {"tanh", "sin"}
PARAMETERIZATIONS = {"identity", "x(1-x)N"}


def _torch(dtype: str = "float64"):
    import torch  # type: ignore[import-not-found]

    torch.use_deterministic_algorithms(True)
    return torch, (torch.float64 if dtype == "float64" else torch.float32)


class _Sin:  # built lazily so the module imports without torch
    pass


def _activation(torch, name: str):
    if name == "tanh":
        return torch.nn.Tanh()
    if name == "sin":
        class Sin(torch.nn.Module):
            def forward(self, x):
                return torch.sin(x)
        return Sin()
    raise ValueError(f"activation {name!r} is not part of the frozen protocol or its registered perturbations")


def _parameterized(torch, net, parameterization: str, domain_length: float = 1.0):
    if parameterization == "identity":
        return net

    class HardDirichlet(torch.nn.Module):
        """u(y) = y (L - y) N(y): homogeneous Dirichlet data on [0, L] by construction (L = 1 for the frozen spec).

        Tier-1 run 1 (2026-09-16) used the unit-interval form on the P8 rescaled domain [0, 2], which does
        not vanish at y = 2 -- a harness defect, recorded in the attempt's POST_AUDIT_ANNOTATION; the
        equivalent rescaled problem needs the rescaled parameterization.
        """

        def __init__(self, inner, length: float):
            super().__init__()
            self.inner = inner
            self.length = float(length)

        def forward(self, x):
            return x * (self.length - x) * self.inner(x)

    return HardDirichlet(net, domain_length)


def build_model(config: Mapping[str, Any], init_seed: int, *, dtype: str = "float64", activation: str | None = None,
                domain_length: float = 1.0):
    torch, tdtype = _torch(dtype)
    net = config["network"]
    name = activation or net["activation"]
    if name not in ACTIVATIONS:
        raise ValueError(f"activation {name!r} is not part of the frozen protocol")
    parameterization = net.get("outputParameterization", "identity")
    if parameterization not in PARAMETERIZATIONS:
        raise ValueError(f"outputParameterization {parameterization!r} is not registered")
    torch.manual_seed(int(init_seed))
    layers: list[Any] = []
    width_in = 1
    for _ in range(int(net["hiddenLayers"])):
        layers.append(torch.nn.Linear(width_in, int(net["width"]), dtype=tdtype))
        layers.append(_activation(torch, name))
        width_in = int(net["width"])
    layers.append(torch.nn.Linear(width_in, 1, dtype=tdtype))
    return _parameterized(torch, torch.nn.Sequential(*layers), parameterization, domain_length).to(tdtype)


def model_from_weights(config: Mapping[str, Any], weights: Mapping[str, Sequence[Any]], *, dtype: str = "float64",
                       activation: str | None = None, domain_length: float = 1.0):
    torch, tdtype = _torch(dtype)
    model = build_model(config, 0, dtype=dtype, activation=activation, domain_length=domain_length)
    state = {name: torch.tensor(value, dtype=tdtype) for name, value in weights.items()}
    model.load_state_dict(state)
    return model


def weights_of(model) -> dict[str, Any]:
    return {name: tensor.detach().cpu().tolist() for name, tensor in model.state_dict().items()}


def _derivatives(torch, model, x):
    x = x.clone().requires_grad_(True)
    u = model(x)
    (ux,) = torch.autograd.grad(u, x, grad_outputs=torch.ones_like(u), create_graph=True)
    (uxx,) = torch.autograd.grad(ux, x, grad_outputs=torch.ones_like(ux), create_graph=True)
    return u, ux, uxx


def fields(model, points: Sequence[float], *, dtype: str = "float64", domain_scale: float = 1.0) -> dict[str, list[float]]:
    """u, u', u'' at physical ``points`` through first- and second-order autograd (no finite differences).

    With ``domain_scale`` L != 1 the model was trained on y = L x (P8); the
    physical derivatives are mapped back: u'(x) = L v'(y), u''(x) = L^2 v''(y).
    """

    torch, tdtype = _torch(dtype)
    x = torch.tensor([[float(p) * domain_scale] for p in points], dtype=tdtype)
    u, ux, uxx = _derivatives(torch, model, x)
    L = float(domain_scale)
    return {
        "u": [float(v) for v in u.detach().flatten().tolist()],
        "ux": [float(v) * L for v in ux.detach().flatten().tolist()],
        "uxx": [float(v) * L * L for v in uxx.detach().flatten().tolist()],
    }


def rel_l2(values: Sequence[float], exact: Sequence[float]) -> float:
    num = math.fsum((a - b) ** 2 for a, b in zip(values, exact))
    den = math.fsum(b * b for b in exact)
    return math.sqrt(num / den)


def select_collocation(pool_size: int, count: int, sample_seed: int) -> list[int]:
    """The run's collocation subset of the preregistered pool: ``count`` distinct indices from ``sample_seed``."""

    import numpy as np

    if count > pool_size:
        raise ValueError("collocationCount exceeds the preregistered pool")
    rng = np.random.default_rng(int(sample_seed))
    return sorted(int(i) for i in rng.choice(pool_size, size=int(count), replace=False))


def train_run(config: Mapping[str, Any], pool: Sequence[float], dev_points: Sequence[float],
              seeds: Mapping[str, int], *, collocation_count: int, log_every: int = 200,
              perturbation: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One training run.  Returns the full record (history, weights, integrity flags)."""

    pert = dict(perturbation or {})
    dtype = pert.get("dtype", "float64")
    torch, tdtype = _torch(dtype)
    torch.set_num_threads(1)
    opt_cfg = config["optimizer"]
    weights_cfg = config["lossWeights"]
    steps = int(opt_cfg["steps"])
    batch_size = int(opt_cfg["batchSize"])
    L = float(pert.get("domainScale", 1.0))
    indices = select_collocation(len(pool), collocation_count, pert.get("resampleSeed", seeds["sample"]))
    if pert.get("dropFraction"):
        import numpy as np

        keep = max(1, int(round(len(indices) * (1.0 - float(pert["dropFraction"])))))
        rng = np.random.default_rng(int(seeds["sample"]) + 7)
        indices = sorted(int(i) for i in rng.choice(indices, size=keep, replace=False))
    collocation = [pool[i] for i in indices]
    # Scaled problem for P8: y = L x, v(y) = u(x), -v''(y) = (pi^2 / L^2) sin(pi y / L).
    x_col = torch.tensor([[v * L] for v in collocation], dtype=tdtype)
    f_col = torch.tensor([[reference.forcing(v) / (L * L)] for v in collocation], dtype=tdtype)
    x_bc = torch.tensor([[0.0], [L]], dtype=tdtype)
    dev_exact = [reference.solution(v) for v in dev_points]
    hard = config["network"].get("outputParameterization", "identity") != "identity"

    model = build_model(config, seeds["init"], dtype=dtype, activation=pert.get("activation"), domain_length=L)
    optimizer_name = pert.get("optimizer", opt_cfg["name"])
    if optimizer_name == "Adam":
        optimizer = torch.optim.Adam(model.parameters(), lr=float(opt_cfg["lr"]))
        gamma = (float(opt_cfg["finalLr"]) / float(opt_cfg["lr"])) ** (1.0 / max(steps, 1))
        scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=gamma)
    elif optimizer_name == "LBFGS":
        optimizer = torch.optim.LBFGS(model.parameters(), lr=1.0, max_iter=20, history_size=50, line_search_fn="strong_wolfe")
        scheduler = None
        steps = max(1, steps // 20)          # 20 inner iterations per outer step: same budget of function evaluations
        batch_size = len(collocation)        # L-BFGS is full-batch by construction
    else:
        raise ValueError(f"optimizer {optimizer_name!r} is not registered")
    batch_gen = torch.Generator().manual_seed(int(seeds["batch"]))
    n_col = len(collocation)
    order = torch.randperm(n_col, generator=batch_gen)
    cursor = 0
    history: list[dict[str, float]] = []
    nan_encountered = False
    started = time.perf_counter()

    def dev_error() -> float:
        with torch.no_grad():
            u_dev = model(torch.tensor([[v * L] for v in dev_points], dtype=tdtype)).flatten().tolist()
        return rel_l2(u_dev, dev_exact)

    def loss_terms(xb, fb):
        u, ux, uxx = _derivatives(torch, model, xb)
        residual = -uxx - fb
        loss_pde = torch.mean(residual ** 2)
        loss_bc = torch.mean(model(x_bc) ** 2)
        total = float(weights_cfg["pde"]) * loss_pde + float(weights_cfg["bc"]) * loss_bc
        return total, loss_pde, loss_bc

    for step in range(1, steps + 1):
        if cursor + batch_size > n_col:
            order = torch.randperm(n_col, generator=batch_gen)
            cursor = 0
        batch = order[cursor:cursor + batch_size] if batch_size < n_col else order
        cursor += batch_size
        xb, fb = x_col[batch], f_col[batch]
        if optimizer_name == "LBFGS":
            def closure():
                optimizer.zero_grad()
                total, _, _ = loss_terms(xb, fb)
                total.backward()
                return total
            optimizer.step(closure)
            with torch.enable_grad():
                loss, loss_pde, loss_bc = loss_terms(xb, fb)
        else:
            optimizer.zero_grad()
            loss, loss_pde, loss_bc = loss_terms(xb, fb)
        if not torch.isfinite(loss):
            nan_encountered = True
            history.append({"step": step, "total": float("nan"), "pde": float("nan"), "bc": float("nan"), "devRelL2": float("nan")})
            break
        if optimizer_name == "Adam":
            loss.backward()
            optimizer.step()
            scheduler.step()
        if step % log_every == 0 or step == steps or step == 1:
            entry = {"step": step, "total": float(loss.detach()), "pde": float(loss_pde.detach()), "bc": float(loss_bc.detach()),
                     "devRelL2": dev_error()}
            if scheduler is not None:
                entry["lr"] = float(scheduler.get_last_lr()[0])
            history.append(entry)
    elapsed = time.perf_counter() - started
    final_dev = float("nan") if nan_encountered else dev_error()
    return {
        "seeds": dict(seeds),
        "collocationCount": collocation_count,
        "collocationIndices": indices,
        "stepsRequested": steps,
        "stepsCompleted": history[-1]["step"] if history else 0,
        "batchSize": batch_size,
        "nanEncountered": nan_encountered,
        "completed": (not nan_encountered) and bool(history) and history[-1]["step"] == steps,
        "lossHistory": history,
        "finalLoss": {k: history[-1][k] for k in ("total", "pde", "bc")} if history else None,
        "devRelL2": final_dev,
        "elapsedSeconds": elapsed,
        "determinism": {"useDeterministicAlgorithms": True, "threads": 1, "dtype": dtype, "device": "cpu"},
        "outputParameterization": config["network"].get("outputParameterization", "identity"),
        "hardBoundary": hard,
        "perturbation": pert or None,
        "weights": weights_of(model),
    }
