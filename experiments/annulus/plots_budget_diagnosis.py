"""Figures of the nested budget intervention (PART 23). Every point comes from DIAGNOSIS.json.

Nothing is recomputed here and no model is loaded: the plots render the registered
diagnostic record, so a figure cannot disagree with the evidence it illustrates.

    PYTHONPATH=. <mamba python> -B experiments/annulus/plots_budget_diagnosis.py \
        --diagnosis experiments/annulus/diagnosis/nested-budget-r1-paired
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

STAT = "maxCellRmsErrorOverReferenceRms"
FIGSIZE = (6.0, 4.4)


def series(document, key):
    budgets = document["budgets"]
    return budgets, [[s["budgets"][str(b)][key] for b in budgets] for s in document["perSeed"]]


def _finish(ax, out, name, *, legend=False):
    ax.set_xlabel("optimization steps")
    ax.grid(alpha=0.3, linewidth=0.5)
    if legend:
        ax.legend(fontsize=7, ncol=2)
    ax.figure.tight_layout()
    ax.figure.savefig(out / name, dpi=150)
    plt.close(ax.figure)
    print("  ", name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--diagnosis", type=Path, required=True)
    args = parser.parse_args()

    document = json.loads((args.diagnosis / "DIAGNOSIS.json").read_text(encoding="utf-8"))
    out = args.diagnosis / "plots"
    out.mkdir(parents=True, exist_ok=True)
    budgets = document["budgets"]
    threshold = float(document["localizedCriterion"]["threshold"])
    epsilon = float(document["epsilonSpec"])
    b_star = document["bStar"]
    print(f"figures -> {out}")

    # 1 + 3. every paired seed's global error, one line per seed
    _, rel = series(document, "relL2")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for index, values in enumerate(rel):
        ax.plot(budgets, values, marker="o", linewidth=1.0, markersize=3.5, alpha=0.85, label=f"seed {index}")
    ax.axhline(epsilon, color="crimson", linestyle="--", linewidth=1.0, label=f"epsilon_spec {epsilon:g}")
    ax.set_yscale("log")
    ax.set_ylabel("dev relative L2")
    ax.set_title("Global dev error of the ten paired seeds")
    _finish(ax, out, "01_global_relL2_per_seed.png", legend=True)

    # 2. the localized criterion, one line per seed, against its threshold
    _, loc = series(document, STAT)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for index, values in enumerate(loc):
        ax.plot(budgets, values, marker="o", linewidth=1.0, markersize=3.5, alpha=0.85, label=f"seed {index}")
    ax.axhline(threshold, color="crimson", linestyle="--", linewidth=1.2, label=f"ACA-9 threshold {threshold:g}")
    if b_star:
        ax.axvline(b_star, color="seagreen", linestyle=":", linewidth=1.2, label=f"B* = {b_star}")
    ax.set_yscale("log")
    ax.set_ylabel(STAT)
    ax.set_title("Localized acceptance criterion on D_dev (every-seed)")
    _finish(ax, out, "02_localized_criterion_per_seed.png", legend=True)

    # 4. the seed that failed r1, on its own
    failing = document["budgetVerdicts"][0]["localized"]["failingSeedIndices"]
    worst_index = failing[0] if failing else max(range(len(loc)), key=lambda i: loc[i][0])
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(budgets, loc[worst_index], marker="o", color="darkorange", linewidth=1.6, label=f"seed {worst_index} ACA-9")
    ax.plot(budgets, rel[worst_index], marker="s", color="steelblue", linewidth=1.2, label=f"seed {worst_index} relL2")
    ax.axhline(threshold, color="crimson", linestyle="--", linewidth=1.2, label=f"ACA-9 threshold {threshold:g}")
    for x, y in zip(budgets, loc[worst_index]):
        ax.annotate(f"{y:.3e}", (x, y), textcoords="offset points", xytext=(0, 8), fontsize=7, ha="center")
    ax.set_yscale("log")
    ax.set_ylabel("value on D_dev")
    ax.set_title(f"The seed that failed Gate 5b in r1 (seed {worst_index})")
    _finish(ax, out, "04_failing_seed_trajectory.png", legend=True)

    # 5. median and worst of both metrics -- the summary the decision rule does NOT use
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for values, name, style in ((rel, "relL2", "-"), (loc, STAT, "--")):
        medians = [statistics.median(v[i] for v in values) for i in range(len(budgets))]
        worsts = [max(v[i] for v in values) for i in range(len(budgets))]
        ax.plot(budgets, medians, style, marker="o", linewidth=1.3, label=f"{name} median")
        ax.plot(budgets, worsts, style, marker="^", linewidth=1.3, alpha=0.7, label=f"{name} worst")
    ax.axhline(threshold, color="crimson", linestyle=":", linewidth=1.0, label=f"ACA-9 threshold {threshold:g}")
    ax.set_yscale("log")
    ax.set_ylabel("value on D_dev")
    ax.set_title("Median and worst seed -- the median is not the verdict")
    _finish(ax, out, "05_median_and_worst_summary.png", legend=True)

    # 6. residual against budget
    _, residual = series(document, "normalizedResidualRms")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for index, values in enumerate(residual):
        ax.plot(budgets, values, marker="o", linewidth=1.0, markersize=3.5, alpha=0.85, label=f"seed {index}")
    ax.set_yscale("log")
    ax.set_ylabel("normalized residual RMS")
    ax.set_title("PDE residual against optimization budget")
    _finish(ax, out, "06_residual_vs_budget.png", legend=True)

    # 7. dispersion: the part of the story the every-seed rule makes visible
    fig, ax = plt.subplots(figsize=FIGSIZE)
    iqr = [v["reliability"]["iqr"] for v in document["budgetVerdicts"]]
    spread = [max(v[i] for v in loc) - min(v[i] for v in loc) for i in range(len(budgets))]
    ax.plot(budgets, iqr, marker="o", linewidth=1.4, label="relL2 IQR")
    ax.plot(budgets, spread, marker="s", linewidth=1.4, label="ACA-9 max - min")
    ax.set_yscale("log")
    ax.set_ylabel("spread across seeds")
    ax.set_title("Continuing optimization also moves the dispersion")
    _finish(ax, out, "07_dispersion_vs_budget.png", legend=True)

    # 3b. the paired prefix check, as a picture
    fig, ax = plt.subplots(figsize=FIGSIZE)
    deltas = [abs(p["delta"]) for p in document["prefixEquivalence"]["perSeed"]]
    ax.bar(range(len(deltas)), [d if d > 0 else 1e-20 for d in deltas], color="seagreen")
    ax.set_yscale("log")
    ax.set_ylim(1e-21, 1e-3)
    ax.set_xlabel("paired seed")
    ax.set_ylabel("|new - r1| at 120000 steps")
    ax.set_title("Prefix equivalence against r1: every seed bitwise identical")
    ax.grid(alpha=0.3, linewidth=0.5)
    fig.tight_layout()
    fig.savefig(out / "03_prefix_equivalence.png", dpi=150)
    plt.close(fig)
    print("   03_prefix_equivalence.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
