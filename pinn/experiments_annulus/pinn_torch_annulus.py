"""The annulus PINN under test: a tanh MLP on (x, y) with a hard two-component constraint.

Everything that shapes a result is read from the frozen experiment config
(architecture, optimizer, schedule, steps, batch size, collocation count, threads).
Three seeds enter a run (Constitution 10.1): ``init``, ``sample``, ``batch``.
Training never sees D_dev or D_claim -- the dev error is logged for diagnostics and
nothing in the loop reads it (fixed step count, no early stopping, protocol L4).

Boundary enforcement is hard on **both** components by construction:

    u(x, y) = (R^2 - s) (s - a^2) N(x, y),      s = x^2 + y^2

so u vanishes on r = R and on r = a exactly, which is the whole reason a
multiply connected domain does not need a second boundary loss term. The factor
is the same ``h`` the manufactured solution is built from, but it is written here
independently of ``pinn.reference``: the model must not import the answer.

``perturbation`` (Red Team Tier-1, one retrain each; never used by a formal run):
``{"dtype": "float32"}`` (P4), ``{"activation": "sin"}`` (P16),
``{"optimizer": "LBFGS"}`` (P9), ``{"domainScale": L}`` (P8: train on the annulus
with radii (L a, L R) -- the hard factor scales WITH the domain, which is the 1D
harness defect this module must not repeat), ``{"dropFraction": f}`` (P6),
``{"resampleSeed": s}`` (P1), ``{"collocationIndices": [...]}`` (P7/P11: a
preregistered biased draw from the same pool).

``device`` is an EXECUTION parameter and never a method value: the caller passes it
in from the command line and it is NOT read from the frozen config. The config is
inside ``codeHash``, and the G6 reproduction has to run the SAME ``codeHash`` in a
CPU-only environment (Constitution 28.1); a device written into the config would make
that reproduction impossible. The numerics stay float64 on every device and
``torch.use_deterministic_algorithms(True)`` stays on -- under CUDA that requires
``CUBLAS_WORKSPACE_CONFIG=:4096:8``, which is set here rather than by quietly turning
determinism off.

``optimizer.lrPrefixSteps`` decouples the learning-rate schedule from the total budget.
Without it the decay factor is ``(finalLr/lr)**(1/steps)``, so the WHOLE trajectory is
rescaled when the budget changes and two runs of different length never share a prefix --
which is why the retrospective budget-only continuation of the r1 ensemble was impossible
(``docs/pinn-trust-loop/ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md``). With it, the decay
factor is ``(finalLr/lr)**(1/lrPrefixSteps)`` and the scheduler simply stops advancing once
it has taken ``lrPrefixSteps`` of them, so

    lr(t) = lr0 (finalLr/lr0) ** (min(t, lrPrefixSteps) / lrPrefixSteps)

and the budget is no longer an argument of the schedule. Omitting the field keeps the old
budget-coupled behaviour bit for bit, so nothing that ran before changes meaning.

``checkpoint_steps`` / ``checkpoint_sink`` emit the FULL resumable state (model, Adam
moments and step counter, scheduler position, batch generator, order and cursor, RNG
states) at the requested steps, and ``resume_from`` puts one back. Weights alone are not
a continuation: reloading them into a fresh Adam is a different trajectory.
"""

from __future__ import annotations

import os
import time
from typing import Any, Mapping, Sequence

from pinn.experiments.pinn_torch import rel_l2, select_collocation
from . import checkpoint_annulus as ckpt
from pinn.geometry.annulus import INNER_RADIUS, OUTER_RADIUS
from pinn.reference import analytic_annulus as reference

ACTIVATIONS = {"tanh", "sin"}
PARAMETERIZATIONS = {"(R^2-s)(s-a^2)N"}


def _torch(dtype: str = "float64", threads: int = 1, device: str = "cpu"):
    import torch  # type: ignore[import-not-found]

    name = str(device)
    if name.startswith("cuda"):
        # Deterministic algorithms on CUDA need a fixed cuBLAS workspace, and the variable has
        # to be in the environment before the first cuBLAS handle is created. Setting it is the
        # honest option; switching determinism off to make the error go away would not be.
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        if not torch.cuda.is_available():
            raise RuntimeError(f"device {name!r} requested but torch.cuda.is_available() is False")
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(int(threads))
    return torch, (torch.float64 if dtype == "float64" else torch.float32), torch.device(name)


def schedule_of(opt_cfg: Mapping[str, Any], steps: int) -> tuple[float, int]:
    """``(gamma, prefix_steps)`` of the exponential decay.

    ``lrPrefixSteps`` present -> the schedule is a property of the METHOD and the total
    budget is not an argument of it. Absent -> the historical behaviour, where the decay is
    stretched over whatever budget was requested.
    """

    prefix = int(opt_cfg.get("lrPrefixSteps", steps))
    if prefix <= 0:
        raise ValueError("lrPrefixSteps must be positive")
    gamma = (float(opt_cfg["finalLr"]) / float(opt_cfg["lr"])) ** (1.0 / max(prefix, 1))
    return gamma, prefix


def learning_rates(opt_cfg: Mapping[str, Any], steps: int, at: Sequence[int], *, logged: bool = False
                   ) -> list[float]:
    """The learning rate at each 1-based step in ``at``, computed the way the code computes it.

    ``torch.optim.lr_scheduler.ExponentialLR.get_lr()`` returns ``group["lr"] * gamma``: it
    multiplies the CURRENT rate, step after step. It does not evaluate ``lr0 * gamma ** t``.
    The two differ in the last one or two ULP after tens of thousands of multiplications, so a
    prefix-equivalence check written against the closed form compares against something the
    training loop never computed. This helper therefore iterates, and reproduces all 241
    learning rates logged by the r1 ensemble bit for bit.

    ``logged=False`` gives the rate in force DURING step t (the loop calls ``scheduler.step()``
    after ``optimizer.step()``); ``logged=True`` gives what ``get_last_lr()`` reports after it.
    """

    gamma, prefix = schedule_of(opt_cfg, steps)
    wanted = {int(s) for s in at}
    if not wanted:
        return []
    applied: dict[int, float] = {}
    reported: dict[int, float] = {}
    lr = float(opt_cfg["lr"])
    advances = 0
    for step in range(1, max(wanted) + 1):
        if step in wanted:
            applied[step] = lr
        if advances < prefix:                  # past the prefix the rate is held, not decayed further
            lr = lr * gamma
            advances += 1
        if step in wanted:
            reported[step] = lr
    source = reported if logged else applied
    return [source[int(s)] for s in at]


def _activation(torch, name: str):
    if name == "tanh":
        return torch.nn.Tanh()
    if name == "sin":
        class Sin(torch.nn.Module):
            def forward(self, x):
                return torch.sin(x)
        return Sin()
    raise ValueError(f"activation {name!r} is not part of the frozen protocol or its registered perturbations")


def _parameterized(torch, net, parameterization: str, inner: float, outer: float):
    if parameterization not in PARAMETERIZATIONS:
        raise ValueError(f"outputParameterization {parameterization!r} is not registered for the annulus problem")

    class HardDirichletAnnulus(torch.nn.Module):
        """u = (R^2 - s)(s - a^2) N(x, y): zero on BOTH circles by construction."""

        def __init__(self, inner_net, inner_radius: float, outer_radius: float):
            super().__init__()
            self.inner = inner_net
            self.inner_radius = float(inner_radius)
            self.outer_radius = float(outer_radius)

        def forward(self, xy):
            s = xy[:, 0:1] ** 2 + xy[:, 1:2] ** 2
            factor = (self.outer_radius ** 2 - s) * (s - self.inner_radius ** 2)
            return factor * self.inner(xy)

    return HardDirichletAnnulus(net, inner, outer)


def build_model(config: Mapping[str, Any], init_seed: int, *, dtype: str = "float64", activation: str | None = None,
                domain_scale: float = 1.0, threads: int = 1, device: str = "cpu"):
    torch, tdtype, tdev = _torch(dtype, threads, device)
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
    scale = float(domain_scale)
    model = _parameterized(torch, torch.nn.Sequential(*layers), net["outputParameterization"],
                           INNER_RADIUS * scale, OUTER_RADIUS * scale)
    # the parameters are drawn on the CPU under the init seed and only then moved, so the
    # initial weights are bit-identical whatever device the run trains on
    return model.to(device=tdev, dtype=tdtype)


def model_from_weights(config: Mapping[str, Any], weights: Mapping[str, Sequence[Any]], *, dtype: str = "float64",
                       activation: str | None = None, domain_scale: float = 1.0, threads: int = 1,
                       device: str = "cpu"):
    torch, tdtype, tdev = _torch(dtype, threads, device)
    model = build_model(config, 0, dtype=dtype, activation=activation, domain_scale=domain_scale, threads=threads,
                        device=device)
    model.load_state_dict({name: torch.tensor(value, dtype=tdtype, device=tdev) for name, value in weights.items()})
    return model


def weights_of(model) -> dict[str, Any]:
    return {name: tensor.detach().cpu().tolist() for name, tensor in model.state_dict().items()}


def _derivatives(torch, model, xy):
    """u, u_x, u_y, u_xx, u_yy through first- and second-order autograd, components kept apart."""

    xy = xy.clone().requires_grad_(True)
    u = model(xy)
    (grad,) = torch.autograd.grad(u, xy, grad_outputs=torch.ones_like(u), create_graph=True)
    ux = grad[:, 0:1]
    uy = grad[:, 1:2]
    (gx,) = torch.autograd.grad(ux, xy, grad_outputs=torch.ones_like(ux), create_graph=True)
    (gy,) = torch.autograd.grad(uy, xy, grad_outputs=torch.ones_like(uy), create_graph=True)
    return u, ux, uy, gx[:, 0:1], gy[:, 1:2]


def fields(model, points: Sequence[Sequence[float]], *, dtype: str = "float64", domain_scale: float = 1.0,
           threads: int = 1, device: str = "cpu") -> dict[str, list[float]]:
    """u, u_x, u_y, u_xx, u_yy at physical ``points``.

    With ``domain_scale`` L != 1 the model was trained on the annulus of radii
    (L a, L R) (P8); the physical derivatives are mapped back: u_x = L v_xi and
    u_xx = L^2 v_xixi.
    """

    torch, tdtype, tdev = _torch(dtype, threads, device)
    xy = torch.tensor([[float(x) * domain_scale, float(y) * domain_scale] for x, y in points], dtype=tdtype,
                      device=tdev)
    u, ux, uy, uxx, uyy = _derivatives(torch, model, xy)
    L = float(domain_scale)
    flat = lambda t, factor: [float(v) * factor for v in t.detach().flatten().tolist()]
    return {"u": flat(u, 1.0), "ux": flat(ux, L), "uy": flat(uy, L), "uxx": flat(uxx, L * L), "uyy": flat(uyy, L * L)}


def values(model, points: Sequence[Sequence[float]], *, dtype: str = "float64", domain_scale: float = 1.0,
           threads: int = 1, device: str = "cpu") -> list[float]:
    """u only (no autograd graph): boundary values and plots."""

    torch, tdtype, tdev = _torch(dtype, threads, device)
    with torch.no_grad():
        xy = torch.tensor([[float(x) * domain_scale, float(y) * domain_scale] for x, y in points], dtype=tdtype,
                          device=tdev)
        return [float(v) for v in model(xy).flatten().tolist()]


def normal_derivatives(model, boundary_points: Sequence[Sequence[float]], component: str, *,
                       dtype: str = "float64", domain_scale: float = 1.0, threads: int = 1,
                       device: str = "cpu") -> list[float]:
    """Outward normal derivative on ONE named boundary component.

    The component is an argument rather than something inferred from the point,
    because that is exactly the decision a multiply connected domain adds: the same
    radius formula with the wrong component gives a plausible number with the wrong
    sign. ``pinn.geometry.annulus.outward_normal`` owns the sign.
    """

    from pinn.geometry.annulus import outward_normal

    fld = fields(model, boundary_points, dtype=dtype, domain_scale=domain_scale, threads=threads, device=device)
    out: list[float] = []
    for point, ux, uy in zip(boundary_points, fld["ux"], fld["uy"]):
        nx, ny = outward_normal(point, component)
        out.append(ux * nx + uy * ny)
    return out


def train_run(config: Mapping[str, Any], pool: Sequence[Sequence[float]], dev_points: Sequence[Sequence[float]],
              seeds: Mapping[str, int], *, collocation_count: int, log_every: int = 500,
              device: str = "cpu", perturbation: Mapping[str, Any] | None = None,
              checkpoint_steps: Sequence[int] = (), checkpoint_sink=None,
              resume_from: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One training run. Returns the full record (history, weights, integrity flags)."""

    pert = dict(perturbation or {})
    dtype = pert.get("dtype", "float64")
    threads = int(config["optimizer"].get("threads", 1))
    torch, tdtype, tdev = _torch(dtype, threads, device)
    opt_cfg = config["optimizer"]
    weights_cfg = config["lossWeights"]
    if set(weights_cfg) != {"pde"}:
        raise ValueError("the annulus loss has a single pde term; the hard parameterization enforces both boundaries")
    steps = int(opt_cfg["steps"])
    batch_size = int(opt_cfg["batchSize"])
    L = float(pert.get("domainScale", 1.0))
    indices = select_collocation(len(pool), collocation_count, pert.get("resampleSeed", seeds["sample"]))
    if pert.get("dropFraction"):
        import numpy as np

        keep = max(1, int(round(len(indices) * (1.0 - float(pert["dropFraction"])))))
        rng = np.random.default_rng(int(seeds["sample"]) + 7)
        indices = sorted(int(i) for i in rng.choice(indices, size=keep, replace=False))
    if pert.get("collocationIndices") is not None:        # P7 / P11: a preregistered biased draw from the same pool
        indices = sorted(int(i) for i in pert["collocationIndices"])
    collocation = [pool[i] for i in indices]
    # Scaled problem for P8: (xi, eta) = (L x, L y) on the annulus of radii (L a, L R),
    # v(xi, eta) = u(x, y), -(v_xixi + v_etaeta) = f(x, y) / L^2.
    xy_col = torch.tensor([[x * L, y * L] for x, y in collocation], dtype=tdtype, device=tdev)
    f_col = torch.tensor([[reference.forcing(x, y) / (L * L)] for x, y in collocation], dtype=tdtype, device=tdev)
    dev_exact = [reference.solution(x, y) for x, y in dev_points]
    dev_tensor = torch.tensor([[x * L, y * L] for x, y in dev_points], dtype=tdtype, device=tdev)

    model = build_model(config, seeds["init"], dtype=dtype, activation=pert.get("activation"),
                        domain_scale=L, threads=threads, device=device)
    optimizer_name = pert.get("optimizer", opt_cfg["name"])
    if optimizer_name == "Adam":
        optimizer = torch.optim.Adam(model.parameters(), lr=float(opt_cfg["lr"]))
        gamma, prefix_steps = schedule_of(opt_cfg, steps)
        scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=gamma)
    elif optimizer_name == "LBFGS":
        optimizer = torch.optim.LBFGS(model.parameters(), lr=1.0, max_iter=20, history_size=50,
                                      line_search_fn="strong_wolfe")
        scheduler = None
        prefix_steps = steps
        steps = max(1, steps // 20)          # 20 inner iterations per outer step: the same evaluation budget
        batch_size = len(collocation)        # L-BFGS is full-batch by construction
    else:
        raise ValueError(f"optimizer {optimizer_name!r} is not registered")
    batch_gen = torch.Generator().manual_seed(int(seeds["batch"]))
    n_col = len(collocation)
    order = torch.randperm(n_col, generator=batch_gen).to(tdev)
    cursor = 0
    first_step = 1
    if resume_from is not None:
        if dict(resume_from["seeds"]) != dict(seeds):
            raise ValueError(f"checkpoint belongs to seeds {resume_from['seeds']}, not {dict(seeds)}")
        state = ckpt.restore(torch, resume_from, model, optimizer, scheduler, device=tdev)
        if state["prefixSteps"] != prefix_steps:
            raise ValueError(f"checkpoint carries LR prefix {state['prefixSteps']}, this run uses {prefix_steps}")
        order, cursor, batch_gen = state["order"], state["cursor"], state["batchGenerator"]
        first_step = state["step"] + 1
    checkpoint_at = {int(s) for s in checkpoint_steps}
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

    for step in range(first_step, steps + 1):
        if cursor + batch_size > n_col:
            order = torch.randperm(n_col, generator=batch_gen).to(tdev)
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
            if scheduler.last_epoch < prefix_steps:      # past the prefix the rate is HELD, not decayed further
                scheduler.step()
        if step % log_every == 0 or step == steps or step == first_step:
            entry = {"step": step, "total": float(loss.detach()), "pde": float(loss_pde.detach()),
                     "devRelL2": dev_error()}
            if scheduler is not None:
                entry["lr"] = float(scheduler.get_last_lr()[0])
            history.append(entry)
        if step in checkpoint_at and checkpoint_sink is not None:
            checkpoint_sink(step, ckpt.capture(torch, model, optimizer, scheduler, step=step,
                                               prefix_steps=prefix_steps, order=order, cursor=cursor,
                                               batch_generator=batch_gen, device=tdev, seeds=seeds,
                                               extra={"devRelL2": dev_error(),
                                                      "appliedLrNextStep": float(optimizer.param_groups[0]["lr"]),
                                                      "collocationCount": collocation_count}))
    if tdev.type == "cuda":
        torch.cuda.synchronize(tdev)     # the kernels are asynchronous; an unsynchronised timing would lie
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
        "lrSchedule": {"gamma": gamma if optimizer_name == "Adam" else None, "prefixSteps": prefix_steps,
                       "budgetCoupled": "lrPrefixSteps" not in opt_cfg,
                       "rule": "lr(t) = lr0 * (finalLr/lr0) ** (min(t, prefix) / prefix); applied rate at step t "
                               "is lr0 * gamma ** min(t-1, prefix)"},
        "resumedFromStep": (int(resume_from["currentStep"]) if resume_from is not None else None),
        "checkpointSteps": sorted(checkpoint_at),
        "determinism": {"useDeterministicAlgorithms": True, "threads": threads, "dtype": dtype,
                        "device": str(tdev), "deviceRequested": str(device),
                        "deviceName": torch.cuda.get_device_name(tdev) if tdev.type == "cuda" else "cpu",
                        "cublasWorkspaceConfig": os.environ.get("CUBLAS_WORKSPACE_CONFIG", "")},
        "outputParameterization": config["network"]["outputParameterization"],
        "hardBoundary": {"components": ["outer", "inner"], "factor": "(R^2 - s)(s - a^2)", "domainScale": L},
        "perturbation": pert or None,
        "weights": weights_of(model),
    }
