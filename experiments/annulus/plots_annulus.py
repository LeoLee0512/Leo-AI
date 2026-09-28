"""Figures of the annular Poisson experiment (Geometry Lift 1 section 30).

Rendering only: every number plotted here comes from a registered evaluation set or
a stored artifact of the attempt, and nothing in this file can change a verdict --
which is why it is NOT declared in ``codeIdentityExtraFiles`` (the code-identity
audit's rule: the manifest covers what can change a decision; a picture cannot).

    PYTHONPATH=. python experiments/annulus/plots_annulus.py --attempt experiments/annulus/runs/<id>
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

from pinn.experiments_annulus import datasets_annulus as ds          # noqa: E402
from pinn.experiments_annulus import pinn_torch_annulus as pinn      # noqa: E402
from pinn.geometry import annulus as geo                             # noqa: E402
from pinn.governance import annulus_contract as contract             # noqa: E402
from pinn.reference import analytic_annulus as ref                   # noqa: E402

FIGSIZE = (5.4, 4.8)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def annulus_mask(nx: int = 400):
    grid = np.linspace(-1.05, 1.05, nx)
    X, Y = np.meshgrid(grid, grid)
    S = X ** 2 + Y ** 2
    inside = (S > geo.INNER_RADIUS ** 2) & (S < geo.OUTER_RADIUS ** 2)
    return X, Y, inside


def field_figure(values, title: str, path: Path, *, cmap="viridis", symmetric=False):
    X, Y, inside = annulus_mask()
    masked = np.where(inside, values, np.nan)
    figure, axes = plt.subplots(figsize=FIGSIZE)
    limit = np.nanmax(np.abs(masked)) if symmetric else None
    mesh = axes.pcolormesh(X, Y, masked, shading="auto", cmap=cmap,
                           vmin=-limit if symmetric else None, vmax=limit if symmetric else None)
    for radius, style in ((geo.OUTER_RADIUS, "-"), (geo.INNER_RADIUS, "--")):
        theta = np.linspace(0, 2 * math.pi, 400)
        axes.plot(radius * np.cos(theta), radius * np.sin(theta), style, color="black", linewidth=1.0)
    axes.set_aspect("equal")
    axes.set_title(title, fontsize=10)
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    figure.colorbar(mesh, ax=axes, shrink=0.85)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def evaluate_on_grid(model, threads: int = 1):
    X, Y, inside = annulus_mask()
    points = [(float(x), float(y)) for x, y in zip(X[inside], Y[inside])]
    values = pinn.values(model, points, threads=threads)
    out = np.full(X.shape, np.nan)
    out[inside] = values
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    attempt = args.attempt
    out = args.out or (attempt / "plots")
    out.mkdir(parents=True, exist_ok=True)

    identity = load(attempt / "identity.json")
    config = load(Path(identity["configPath"]))
    threads = int(config["optimizer"].get("threads", 1))
    dev = ds.points_of(load(attempt / "sets/dev.json"))
    train = ds.points_of(load(attempt / "sets/train.json"))
    boundary = load(attempt / "sets/boundary.json")["components"]
    runs = sorted((attempt / "runs").glob("run-*.json"))
    records = [load(path) for path in runs]
    worst = max(records, key=lambda record: record["devRelL2"])
    best = min(records, key=lambda record: record["devRelL2"])
    model = pinn.model_from_weights(config, best["weights"], threads=threads)
    worst_model = pinn.model_from_weights(config, worst["weights"], threads=threads)
    X, Y, inside = annulus_mask()

    # 1. geometry and its two boundary components
    figure, axes = plt.subplots(figsize=FIGSIZE)
    theta = np.linspace(0, 2 * math.pi, 400)
    axes.fill(np.concatenate([np.cos(theta), 0.35 * np.cos(theta[::-1])]),
              np.concatenate([np.sin(theta), 0.35 * np.sin(theta[::-1])]), color="#cfe3ff", linewidth=0)
    axes.plot(np.cos(theta), np.sin(theta), "-", color="black", label="outer boundary (n = (x,y))")
    axes.plot(0.35 * np.cos(theta), 0.35 * np.sin(theta), "--", color="crimson",
              label="inner boundary (n = -(x,y)/a)")
    for component, colour in (("outer", "black"), ("inner", "crimson")):
        points = np.array(boundary[component]["points"])
        normals = np.array(boundary[component]["normals"])
        step = max(1, len(points) // 24)
        axes.quiver(points[::step, 0], points[::step, 1], normals[::step, 0], normals[::step, 1],
                    color=colour, scale=12, width=0.004)
    axes.set_aspect("equal")
    axes.legend(fontsize=7, loc="upper right")
    axes.set_title("annulus geometry: two boundary components, outward normals", fontsize=10)
    figure.tight_layout()
    figure.savefig(out / "01_geometry.png", dpi=150)
    plt.close(figure)

    # 2-5 fields
    exact = np.full(X.shape, np.nan)
    exact[inside] = [ref.solution(float(x), float(y)) for x, y in zip(X[inside], Y[inside])]
    field_figure(exact, "analytic solution u*", out / "02_analytic_solution.png")
    predicted = evaluate_on_grid(model, threads)
    field_figure(predicted, "PINN solution (best seed)", out / "03_pinn_solution.png")
    field_figure(np.abs(predicted - exact), "|u_theta - u*| (best seed)", out / "04_absolute_error.png",
                 cmap="magma")
    dev_fields = pinn.fields(model, dev, threads=threads)
    residuals = [abs(-(xx + yy) - ref.forcing(x, y))
                 for xx, yy, (x, y) in zip(dev_fields["uxx"], dev_fields["uyy"], dev)]
    figure, axes = plt.subplots(figsize=FIGSIZE)
    scatter = axes.scatter([p[0] for p in dev], [p[1] for p in dev], c=residuals, s=6, cmap="magma")
    axes.set_aspect("equal")
    axes.set_title("PDE residual on D_dev (best seed)", fontsize=10)
    figure.colorbar(scatter, ax=axes, shrink=0.85)
    figure.tight_layout()
    figure.savefig(out / "05_residual.png", dpi=150)
    plt.close(figure)

    # 6. collocation distribution
    indices = best["collocationIndices"]
    figure, axes = plt.subplots(figsize=FIGSIZE)
    axes.scatter([train[i][0] for i in indices], [train[i][1] for i in indices], s=4, color="#1f77b4")
    axes.plot(np.cos(theta), np.sin(theta), "-", color="black", linewidth=1)
    axes.plot(0.35 * np.cos(theta), 0.35 * np.sin(theta), "--", color="crimson", linewidth=1)
    axes.set_aspect("equal")
    axes.set_title(f"collocation points of the best seed ({len(indices)})", fontsize=10)
    figure.tight_layout()
    figure.savefig(out / "06_collocation.png", dpi=150)
    plt.close(figure)

    # 7. geometry-native localized cells
    diagnostics_path = attempt / "dev_diagnostics.json"
    figure, axes = plt.subplots(figsize=FIGSIZE, subplot_kw={"projection": "polar"})
    bins, sectors = contract.RADIAL_BINS, contract.ANGULAR_SECTORS
    cell_values = np.zeros((bins, sectors))
    if diagnostics_path.exists():
        cells = load(diagnostics_path)["perSeedFields"][0]["cellRms"]
        for key, value in cells.items():
            i, j = (int(part) for part in key.split(","))
            cell_values[i, j] = value
    else:
        errors = [abs(a - ref.solution(x, y)) for a, (x, y) in zip(dev_fields["u"], dev)]
        buckets: dict[tuple[int, int], list[float]] = {}
        for point, error in zip(dev, errors):
            buckets.setdefault(geo.cell_index(point, bins, sectors), []).append(error * error)
        for (i, j), values in buckets.items():
            cell_values[i, j] = math.sqrt(sum(values) / len(values))
    radii = [geo.radius_of_area_fraction(i / bins) for i in range(bins + 1)]
    angles = np.linspace(0, 2 * math.pi, sectors + 1)
    mesh = axes.pcolormesh(angles, radii, cell_values, shading="auto", cmap="magma")
    axes.set_rmin(0.0)
    axes.set_title(f"per-cell RMS error, {bins} equal-area rings x {sectors} sectors", fontsize=9)
    figure.colorbar(mesh, ax=axes, shrink=0.7)
    figure.tight_layout()
    figure.savefig(out / "07_localized_cells.png", dpi=150)
    plt.close(figure)

    # 8. multi-seed error distribution
    errors = [record["devRelL2"] for record in records]
    figure, axes = plt.subplots(figsize=FIGSIZE)
    axes.plot(range(len(errors)), errors, "o-", color="#1f77b4")
    axes.axhline(float(config["preregistration"]["epsilonSpec"]), color="crimson", linestyle="--",
                 label="epsilon_spec")
    axes.set_yscale("log")
    axes.set_xlabel("seed index")
    axes.set_ylabel("dev relative L2")
    axes.set_title("multi-seed error distribution", fontsize=10)
    axes.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(out / "08_seed_distribution.png", dpi=150)
    plt.close(figure)

    # 9. worst-seed field
    field_figure(np.abs(evaluate_on_grid(worst_model, threads) - exact),
                 f"|u_theta - u*| (worst seed, {worst['devRelL2']:.2e})", out / "09_worst_seed_error.png", cmap="magma")

    # 10. polar FDM convergence
    gate2 = attempt / "gate2_baseline.json"
    if gate2.exists():
        levels = load(gate2)["detail"]["fdm"]["levels"]
        h = [1.0 / level["radialCells"] for level in levels]
        errors = [level["relL2"] for level in levels]
        figure, axes = plt.subplots(figsize=FIGSIZE)
        axes.loglog(h, errors, "o-", label="polar FDM")
        axes.loglog(h, [errors[0] * (value / h[0]) ** 2 for value in h], "--", label="order 2")
        axes.set_xlabel("dr")
        axes.set_ylabel("relative L2")
        axes.set_title("independent polar FDM refinement", fontsize=10)
        axes.legend(fontsize=8)
        figure.tight_layout()
        figure.savefig(out / "10_fdm_convergence.png", dpi=150)
        plt.close(figure)

    # 11. Red Team summary
    tier1 = attempt / "tier1_redteam.json"
    if tier1.exists():
        results = load(tier1)["results"]
        figure, axes = plt.subplots(figsize=FIGSIZE)
        ids = [r["id"] for r in results]
        drifts = [r["deltaQ"] for r in results]
        axes.bar(ids, drifts, color=["#2ca02c" if r["status"] == "PASS" else "#d62728" for r in results])
        axes.axhline(0.01, color="black", linestyle="--", label="maintain 1 %")
        axes.set_yscale("log")
        axes.set_ylabel("delta_q")
        axes.set_title("Tier-1 Red Team", fontsize=10)
        axes.legend(fontsize=8)
        figure.tight_layout()
        figure.savefig(out / "11_redteam.png", dpi=150)
        plt.close(figure)

    print(f"wrote figures to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
