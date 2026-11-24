"""3.2.2 · The human-readable trust report of a product annulus attempt.

As in ``pinn/experiments2d/report2d.py``: the trust report itself is dimension-independent (it renders
the machine records), so ``pinn.experiments.report.write_trust_report`` is reused; only the reference
line and the scope sentences are the annulus ones, written here in one place.
"""

from __future__ import annotations

from pathlib import Path

from pinn.experiments.report import write_trust_report as _write_trust_report_1d

REFERENCE_LINE_ANNULUS = (
    "Reference（参考解）: u* = (1 - s)(s - a²)·g(x,y)，s = x² + y²，a = 0.35，g = 1 + 0.2 sin(πx) cos(2πy) + 0.1x - 0.1y，"
    "`pinn/reference/analytic_annulus.py`（独立代码路径，不导入任何 PINN 模块）· Level A（取自冻结规格 primary source）；"
    "数值交叉核对极坐标 FDM `scientific_reference/annulus_polar_fdm.py` Level B（只用于 Gate 2 与 PH7，不进入任何 ACA）")
SCOPE_LINES_ANNULUS = (
    "- 结论只对冻结的环形域 Poisson 问题（a² < x² + y² < 1，a = 0.35，内外两圈上 u = 0，源项由上面的制造解给出）、本 configId 的"
    "架构 / 优化器 / 采样协议（与已接受的 r3 相同）、本 seed 集与本执行环境成立。",
    "- 外推禁区：其他 PDE、其他几何（其他内径、带角点或不规则边界的区域）、其他架构或训练协议、'PINN 总体可靠'（宪法第三十五章）。",
    "- 局部误差判据 ACA-9 是绑定判据：已接受的 r3 在它上面的余量只有约 1.31 倍，结论应连同这一余量一起引用。",
)


def write_trust_report(attempt_dir: Path, repo_root: Path) -> Path:
    return _write_trust_report_1d(attempt_dir, repo_root, reference_line=REFERENCE_LINE_ANNULUS,
                                  scope_lines=SCOPE_LINES_ANNULUS, primary_ac="ACA-1", should_ac="ACA-8")
