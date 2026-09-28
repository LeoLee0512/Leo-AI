"""The 2D PINN under test: a tanh MLP on (x, y), trained with Adam, CPU float64, deterministic.

Everything that shapes the result is read from the frozen experiment config
(architecture, optimizer, schedule, steps, batch size, collocation count, thread
count).  Three seeds enter a run (Constitution 10.1): ``init``, ``sample``,
``batch``.  Training never sees D_dev or D_claim: the dev error is logged for
diagnostics only and nothing in the loop reads it (fixed step count, no early
stopping -- protocol L4).

Boundary enforcement is hard by construction (2D preregistration PART 2):

    u(x, y) = x (L - x) y (L - y) N(x, y),   L = 1 for the frozen spec

so u vanishes on all four edges exactly and the loss has a single term

    L = mean( ( -(u_xx + u_yy) - f )^2 ).

``perturbation`` (Red Team Tier-1, one retrain each; never used by formal runs):
``{"dtype": "float32"}`` (P4), ``{"activation": "sin"}`` (P16),
``{"optimizer": "LBFGS"}`` (P9), ``{"domainScale": L}`` (P8: train on the square
(0, L)^2 for v(xi, eta) = u(xi/L, eta/L) -- the hard parameterization is rescaled
with the domain, which is the 1D Tier-1 harness defect this module must not
repeat), ``{"dropFraction": 0.1}`` (P6), ``{"resampleSeed": s}`` (P1).
"""

from __future__ import annotations

import math
import time
from typing import Any, Mapping, Sequence

from pinn.experiments.pinn_torch import rel_l2, select_collocation
from pinn.reference import analytic_poisson2d as reference

ACTIVATIONS = {"tanh", "sin"}
PARAMETERIZATIONS = {"x(1-x)y(1-y)N"}


def _torch(dtype: str = "float64", threads: int = 1):
    import torch  # type: ignore[import-not-found]

    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(int(threads))
    return torch, (torch.float64 if dtype == "float64" else torch.float32)


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
    if parameterization not in PARAMETERIZATIONS:
        raise ValueError(f"outputParameterization {parameterization!r} is not registered for the 2D problem")

    class HardDirichletSquare(torch.nn.Module):
        """u = x (L - x) y (L - y) N(x, y): homogeneous Dirichlet data on all four edges of (0, L)^2 by construction."""

        def __init__(self, inner, length: float):
            super().__init__()
            self.inner = inner
            self.length = float(length)

        def forward(self, xy):
            x = xy[:, 0:1]
            y = xy[:, 1:2]
            return x * (self.length - x) * y * (self.length - y) * self.inner(xy)

    return HardDirichletSquare(net, domain_length)


def build_model(config: Mapping[str, Any], init_seed: int, *, dtype: str = "float64", activation: str | None = None,
                domain_length: float = 1.0, threads: int = 1):
    torch, tdtype = _torch(dtype, threads)
    net = config["network"]
    name = activation or net["activation"]
    if name not in ACTIVATIONS:
        raise ValueError(f"activation {name!r} is not part of the frozen protocol")
    torch.manual_seed(int(init_seed))
    layers: list[Any] = []
    width_in = 2
    for _ in range(int(net["hiddenLayers"])):
        layers.append(torch.nn.Linear(width_in, int(net["width"]), dtype=tdtype))
        layers.append(_activation(torch, name))
        width_in = int(net["width"])
    layers.append(torch.nn.Linear(width_in, 1, dtype=tdtype))
    return _parameterized(torch, torch.nn.Sequential(*layers), net["outputParameterization"], domain_length).to(tdtype)


def model_from_weights(config: Mapping[str, Any], weights: Mapping[str, Sequence[Any]], *, dtype: str = "float64",
                       activation: str | None = None, domain_length: float = 1.0, threads: int = 1):
    torch, tdtype = _torch(dtype, threads)
    model = build_model(config, 0, dtype=dtype, activation=activation, domain_length=domain_length, threads=threads)
    model.load_state_dict({name: torch.tensor(value, dtype=tdtype) for name, value in weights.items()})
    return model


def weights_of(model) -> dict[str, Any]:
    return {name: tensor.detach().cpu().tolist() for name, tensor in model.state_dict().items()}


def _derivatives(torch, model, xy):
    """u, u_x, u_y, u_xx, u_yy through first- and second-order autograd (components separately)."""

    xy = xy.clone().requires_grad_(True)
    u = model(xy)
    (grad,) = torch.autograd.grad(u, xy, grad_outputs=torch.ones_like(u), create_graph=True)
    ux = grad[:, 0:1]
    uy = grad[:, 1:2]
    (gx,) = torch.autograd.grad(ux, xy, grad_outputs=torch.ones_like(ux), create_graph=True)
    (gy,) = torch.autograd.grad(uy, xy, grad_outputs=torch.ones_like(uy), create_graph=True)
    return u, ux, uy, gx[:, 0:1], gy[:, 1:2]


def fields(model, points: Sequence[Sequence[float]], *, dtype: str = "float64", domain_scale: float = 1.0,
           threads: int = 1) -> dict[str, list[float]]:
    """u, u_x, u_y, u_xx, u_yy at physical ``points``.

    With ``domain_scale`` L != 1 the model was trained on (xi, eta) = (L x, L y)
    (P8); the physical derivatives are mapped back: u_x = L v_xi, u_xx = L^2 v_xixi.
    """

    torch, tdtype = _torch(dtype, threads)
    xy = torch.tensor([[float(x) * domain_scale, float(y) * domain_scale] for x, y in points], dtype=tdtype)
    u, ux, uy, uxx, uyy = _derivatives(torch, model, xy)
    L = float(domain_scale)
    flat = lambda t, factor: [float(v) * factor for v in t.detach().flatten().tolist()]
    return {"u": flat(u, 1.0), "ux": flat(ux, L), "uy": flat(uy, L), "uxx": flat(uxx, L * L), "uyy": flat(uyy, L * L)}


def values(model, points: Sequence[Sequence[float]], *, dtype: str = "float64", domain_scale: float = 1.0,
           threads: int = 1) -> list[float]:
    """u only (no autograd graph): used for boundary values and plots."""

    torch, tdtype = _torch(dtype, threads)
    with torch.no_grad():
        xy = torch.tensor([[float(x) * domain_scale, float(y) * domain_scale] for x, y in points], dtype=tdtype)
        return [float(v) for v in model(xy).flatten().tolist()]


def normal_derivatives(model, boundary_points: Sequence[Sequence[float]], *, dtype: str = "float64",
                       domain_scale: float = 1.0, threads: int = 1) -> list[float]:
    """Outward normal derivative of the model on the four edges of the unit square."""

    fld = fields(model, boundary_points, dtype=dtype, domain_scale=domain_scale, threads=threads)
    out: list[float] = []
    for (x, y), ux, uy in zip(boundary_points, fld["ux"], fld["uy"]):
        if x == 0.0:
            out.append(-ux)
        elif x == 1.0:
            out.append(ux)
        elif y == 0.0:
            out.append(-uy)
        elif y == 1.0:
            out.append(uy)
        else:
            raise ValueError("normal derivatives are defined on the boundary only")
    return out


def train_run(config: Mapping[str, Any], pool: Sequence[Sequence[float]], dev_points: Sequence[Sequence[float]],
              seeds: Mapping[str, int], *, collocation_count: int, log_every: int = 500,
              perturbation: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One training run.  Returns the full record (history, weights, integrity flags)."""

    pert = dict(perturbation or {})
    dtype = pert.get("dtype", "float64")
    threads = int(config["optimizer"].get("threads", 1))
    torch, tdtype = _torch(dtype, threads)
    opt_cfg = config["optimizer"]
    weights_cfg = config["lossWeights"]
    if set(weights_cfg) != {"pde"}:
        raise ValueError("the 2D loss has a single pde term; the hard parameterization enforces the boundary data")
    steps = int(opt_cfg["steps"])
    batch_size = int(opt_cfg["batchSize"])
    L = float(pert.get("domainScale", 1.0))
    indices = select_collocation(len(pool), collocation_count, pert.get("resampleSeed", seeds["sample"]))
    if pert.get("dropFraction"):
        import numpy as np

        keep = max(1, int(round(len(indices) * (1.0 - float(pert["dropFraction"])))))
        rng = np.random.default_rng(int(seeds["sample"]) + 7)
        indices = sorted(int(i) for i in rng.choice(indices, size=keep, replace=False))
    if pert.get("collocationIndices") is not None:        # P7: a preregistered biased draw from the same pool
        indices = sorted(int(i) for i in pert["collocationIndices"])
    collocation = [pool[i] for i in indices]
    # Scaled problem for P8: (xi, eta) = (L x, L y), v(xi, eta) = u(x, y), -(v_xixi + v_etaeta) = f(x, y) / L^2.
    xy_col = torch.tensor([[x * L, y * L] for x, y in collocation], dtype=tdtype)
    f_col = torch.tensor([[reference.forcing(x, y) / (L * L)] for x, y in collocation], dtype=tdtype)
    dev_exact = [reference.solution(x, y) for x, y in dev_points]
    dev_tensor = torch.tensor([[x * L, y * L] for x, y in dev_points], dtype=tdtype)

    model = build_model(config, seeds["init"], dtype=dtype, activation=pert.get("activation"), domain_length=L, threads=threads)
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
            u_dev = model(dev_tensor).flatten().tolist()
        return rel_l2(u_dev, dev_exact)

    def loss_terms(xb, fb):
        _, _, _, uxx, uyy = _derivatives(torch, model, xb)
        residual = -(uxx + uyy) - fb
        loss_pde = torch.mean(residual ** 2)
        return float(weights_cfg["pde"]) * loss_pde, loss_pde

    for step in range(1, steps + 1):
        if cursor + batch_size > n_col:
            order = torch.randperm(n_col, generator=batch_gen)
            cursor = 0
        batch = order[cursor:cursor + batch_size] if batch_size < n_col else order
        cursor += batch_size
        xb, fb = xy_col[batch], f_col[batch]
        if optimizer_name == "LBFGS":
            def closure():
                optimizer.zero_grad()
                total, _ = loss_terms(xb, fb)
                total.backward()
                return total
            optimizer.step(closure)
            with torch.enable_grad():
                loss, loss_pde = loss_terms(xb, fb)
        else:
            optimizer.zero_grad()
            loss, loss_pde = loss_terms(xb, fb)
        if not torch.isfinite(loss):
            nan_encountered = True
            history.append({"step": step, "total": float("nan"), "pde": float("nan"), "devRelL2": float("nan")})
            break
        if optimizer_name == "Adam":
            loss.backward()
            optimizer.step()
            scheduler.step()
        if step % log_every == 0 or step == steps or step == 1:
            entry = {"step": step, "total": float(loss.detach()), "pde": float(loss_pde.detach()), "devRelL2": dev_error()}
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
        "finalLoss": {k: history[-1][k] for k in ("total", "pde")} if history else None,
        "devRelL2": final_dev,
        "elapsedSeconds": elapsed,
        "determinism": {"useDeterministicAlgorithms": True, "threads": threads, "dtype": dtype, "device": "cpu"},
        "outputParameterization": config["network"]["outputParameterization"],
        "hardBoundary": True,
        "perturbation": pert or None,
        "weights": weights_of(model),
    }
