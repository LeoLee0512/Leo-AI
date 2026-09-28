"""Human-readable rendering and the 2D plots (PART 17, PART 21).

The trust report itself is dimension-independent (it renders the machine records),
so ``pinn.experiments.report.write_trust_report`` is reused; only its single
1D-specific scope sentence is replaced with the 2D one, explicitly and in one
place.  All plots are computed from stored evidence: the registered D_phys tensor
grid, the stored per-seed weights, the stored FDM diagnostic and the stored Red
Team report.  No new evaluation surface is introduced for plotting.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence

from pinn.experiments.common import load_json
from pinn.experiments.report import write_trust_report as _write_trust_report_1d
from pinn.reference import analytic_poisson2d as reference

from . import datasets2d as ds
from . import pinn_torch2d as pinn2d

REFERENCE_LINE_2D = ("Reference（参考解）: u*(x,y) = sin(pi x) sin(pi y)，`pinn/reference/analytic_poisson2d.py`（独立代码路径，不导入任何 PINN 模块）· "
                     "Level A（取自冻结规格 primary source）；数值交叉核对五点 FDM 二阶 `scientific_reference/poisson2d_fdm.py` Level B"
                     "（只用于 Gate 2b，不进入任何 AC）")
SCOPE_LINES_2D = (
    "- 结论只对冻结的 Poisson 2D 问题（-(u_xx + u_yy) = 2π² sin(πx) sin(πy)，u = 0 于 (0,1)² 的四条边）、本 configId 的架构 / 优化器 / "
    "采样协议、本 seed 集与本执行环境成立。",
    "- 外推禁区：其他 PDE、其他几何（本问题是单位正方形，不含角奇性、不规则边界）、其他架构或训练协议、'PINN 总体可靠'（宪法第三十五章）。",
    "- 对称的制造解无法判别残差算子中的 x/y 互换；该能力由 Gate 3 的 T2 非对称探针承担，claim 层判据不提供这一保证。",
)


def write_trust_report(attempt_dir: Path, repo_root: Path) -> Path:
    return _write_trust_report_1d(attempt_dir, repo_root, reference_line=REFERENCE_LINE_2D,
                                  scope_lines=SCOPE_LINES_2D, primary_ac="AC2D-1", should_ac="AC2D-8")


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _square(values: Sequence[float], n: int):
    """Tensor-grid values (x-major) as an (n, n) array indexed [iy][ix] for imshow."""

    return [[values[ix * n + iy] for ix in range(n)] for iy in range(n)]


def _median_index(errors: Sequence[float]) -> int:
    order = sorted(range(len(errors)), key=lambda i: errors[i])
    return order[len(order) // 2]


def plots(attempt_dir: Path) -> list[Path]:
    plt = _plt()
    out = attempt_dir / "plots"
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    identity = load_json(attempt_dir / "identity.json")
    config = load_json(Path(identity["configPath"]))
    threads = int(config["optimizer"].get("threads", 1))
    order = int(config["sets"]["physOrder"])
    phys_points, _ = ds.gauss_legendre_square(order)
    xs = sorted({p[0] for p in phys_points})
    ys = sorted({p[1] for p in phys_points})
    extent = [min(xs), max(xs), min(ys), max(ys)]
    runs = [load_json(p) for p in sorted(attempt_dir.glob("runs/run-*.json"))]
    errors = [r["devRelL2"] for r in runs]
    worst_index = max(range(len(errors)), key=lambda i: errors[i])
    median_index = _median_index(errors)

    def field(run: Any) -> dict[str, list[float]]:
        model = pinn2d.model_from_weights(config, run["weights"], threads=threads)
        return pinn2d.fields(model, phys_points, threads=threads)

    exact = [reference.solution(x, y) for x, y in phys_points]
    median_fields = field(runs[median_index])
    worst_fields = field(runs[worst_index])
    residual = [-(xx + yy) - reference.forcing(x, y) for xx, yy, (x, y) in zip(median_fields["uxx"], median_fields["uyy"], phys_points)]
    abs_error = [abs(a - b) for a, b in zip(median_fields["u"], exact)]
    worst_error = [abs(a - b) for a, b in zip(worst_fields["u"], exact)]

    def heatmap(values: Sequence[float], title: str, filename: str, *, cmap: str = "viridis", log: bool = False) -> None:
        fig, ax = plt.subplots(figsize=(5.2, 4.2))
        data = _square([math.log10(max(v, 1e-18)) if log else v for v in values], order)
        image = ax.imshow(data, origin="lower", extent=extent, cmap=cmap, aspect="equal")
        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_title(title)
        fig.colorbar(image, ax=ax, shrink=0.85)
        fig.tight_layout()
        target = out / filename
        fig.savefig(target, dpi=130)
        plt.close(fig)
        paths.append(target)

    heatmap(exact, "analytic  u*(x,y) = sin(pi x) sin(pi y)", "p1_analytic_solution.png")
    heatmap(median_fields["u"], f"PINN u_theta (median seed, run {median_index:02d})", "p2_pinn_solution.png")
    heatmap(abs_error, f"log10 |u_theta - u*| (median seed, run {median_index:02d})", "p3_absolute_error.png", cmap="magma", log=True)
    heatmap(residual, f"PDE residual -(u_xx+u_yy) - f (median seed, run {median_index:02d})", "p4_pde_residual.png", cmap="coolwarm")
    heatmap(worst_error, f"log10 |u_theta - u*| (worst seed, run {worst_index:02d})", "p7_worst_seed_error.png", cmap="magma", log=True)

    # collocation distribution of the seed-0 run
    train = load_json(attempt_dir / "sets/train.json")
    pool = ds.points_of(train)
    chosen = [pool[i] for i in runs[0]["collocationIndices"]]
    fig, ax = plt.subplots(figsize=(5.0, 4.6))
    ax.scatter([p[0] for p in pool], [p[1] for p in pool], s=3, c="#cccccc", label=f"pool ({len(pool)})")
    ax.scatter([p[0] for p in chosen], [p[1] for p in chosen], s=5, c="#1f77b4", label=f"collocation ({len(chosen)})")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_title("training collocation distribution (run 00)")
    ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout(); target = out / "p5_collocation_distribution.png"; fig.savefig(target, dpi=130); plt.close(fig); paths.append(target)

    # multi-seed distribution
    stats = load_json(attempt_dir / "gate4_training.json")["detail"]["seedStatistics"]
    epsilon = load_json(attempt_dir / "problem_definition.json")["preregistration"]["epsilonSpec"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.bar(range(len(errors)), errors, color="#4c72b0")
    ax.axhline(stats["median"], color="#dd8452", label=f"median {stats['median']:.2e}")
    ax.axhline(epsilon, color="#c44e52", linestyle="--", label=f"epsilon_spec {epsilon:.0e}")
    ax.set_yscale("log"); ax.set_xlabel("seed triplet index"); ax.set_ylabel("dev relative L2")
    ax.set_title(f"multi-seed dev error (k/N = {stats['successRate']})")
    ax.legend(fontsize=8)
    fig.tight_layout(); target = out / "p6_multiseed_errors.png"; fig.savefig(target, dpi=130); plt.close(fig); paths.append(target)

    # FDM convergence
    fdm = load_json(attempt_dir / "gate2_baseline.json")["detail"]
    solutions = fdm.get("fdmSolutions", [])
    if solutions:
        h = [s["h"] for s in solutions]
        err = [s["interior_max_error"] for s in solutions]
        fig, ax = plt.subplots(figsize=(5.4, 4.0))
        ax.loglog(h, err, "o-", label="five-point FDM, interior max error")
        ax.loglog(h, [err[0] * (v / h[0]) ** 2 for v in h], "k--", label="slope 2 reference")
        ax.set_xlabel("h"); ax.set_ylabel("max |u_h - u*|"); ax.set_title("independent FDM grid refinement")
        ax.legend(fontsize=8); ax.grid(True, which="both", alpha=0.3)
        fig.tight_layout(); target = out / "p8_fdm_convergence.png"; fig.savefig(target, dpi=130); plt.close(fig); paths.append(target)

    # Red Team summary
    tier_path = next((p for p in (attempt_dir / "tier1_redteam.json", attempt_dir / "tier1v2_redteam.json") if p.exists()), None)
    if tier_path is not None:
        tier = load_json(tier_path)
        applicable = [r for r in tier["results"] if r.get("applicability") == "APPLICABLE"]
        fig, ax = plt.subplots(figsize=(6.6, 3.8))
        colors = {"PASS": "#55a868", "PARTIAL": "#dd8452", "FAIL": "#c44e52"}
        ax.bar([r["id"] for r in applicable], [max(r["deltaQ"], 1e-12) for r in applicable],
               color=[colors[r["status"]] for r in applicable])
        ax.axhline(0.01, color="#dd8452", linestyle="--", label="1 % maintain")
        ax.axhline(0.05, color="#c44e52", linestyle="--", label="5 % FAIL")
        ax.set_yscale("log"); ax.set_ylabel("delta_q"); ax.set_title("Tier-1 Red Team (2D): QoI drift per perturbation")
        ax.legend(fontsize=8)
        fig.tight_layout(); target = out / "p9_redteam_summary.png"; fig.savefig(target, dpi=130); plt.close(fig); paths.append(target)

    (out / "PLOTS_INDEX.json").write_text(json.dumps({
        "generatedFrom": {"attempt": attempt_dir.name, "physOrder": order, "medianSeedRun": median_index, "worstSeedRun": worst_index},
        "note": "every field is evaluated on the registered D_phys tensor grid from the stored per-seed weights; no new evaluation "
                "surface and no claim data are used for plotting",
        "files": [p.name for p in paths],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return paths
