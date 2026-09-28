"""Human-readable rendering of the machine records (Constitution 13.1: eight sections, no looser than the records)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from pinn.governance.trust_vector import DIMENSIONS
from pinn.reference import analytic_poisson as reference

from .common import load_json
from pinn.research.evidence import read_ref

STATUS_WORDS = {
    "PASS": "PASS", "PARTIAL": "PARTIAL（查了不充分；PARTIAL ≠ PASS）", "FAIL": "FAIL", "BLOCKED": "BLOCKED（不能查：前提未满足）",
    "NOT_CHECKED": "NOT CHECKED（没查：无证据，不构成通过也不构成失败）",
}
MEANING = {
    "math": ("题目在纸面上自洽", "解算得对"), "impl": ("程序算的是这道题", "训练收敛"), "train": ("不是一次偶然成功", "结果准确"),
    "physics": ("物理上可接受", "逼近真值"), "external": ("与独立代码路径的参考在 claim 集上、阈值内一致", "超出参考覆盖范围的行为"),
    "repro": ("不绑定于单次运行、单台机器、单一安装", "独立实现也一致"),
}


def _short(value: str) -> str:
    return value[:12]


def _check_lines(entry: Mapping[str, Any]) -> list[str]:
    lines = []
    for check in entry.get("checks", []):
        if check["applicability"] == "APPLICABLE":
            lines.append(f"- `{check['checkId']}` · APPLICABLE · **{check['status']}** · {check.get('reason', '')}")
        else:
            lines.append(f"- `{check['checkId']}` · **NOT APPLICABLE（不承担）** · 理由：{check['reason']}；无 status，不计入 meet")
    applicable = [c for c in entry.get("checks", []) if c["applicability"] == "APPLICABLE"]
    counts = {}
    for c in applicable:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    total = len(entry.get("checks", []))
    if total:
        lines.append(f"- 维度汇总：登记 {total} 项，APPLICABLE {len(applicable)} 项（{counts}），NOT_APPLICABLE {total - len(applicable)} 项不计；"
                     f"维度状态 = 全部 APPLICABLE 检查的 meet = **{entry['status']}**" + (f"；notes：{entry['notes']}" if entry.get("notes") else ""))
    return lines


#: The 1D wording; the 2D renderer passes its own (2D_REUSE_AUDIT section 3: minimal generalization, 1D output unchanged).
REFERENCE_LINE_1D = ("Reference（参考解）: u*(x) = sin(pi x)，`pinn/reference/analytic_poisson.py`（独立代码路径，不导入任何 PINN 模块）· "
                     "Level A（取自冻结规格 primary source）；数值交叉核对 FDM 二阶 `scientific_reference/poisson_fdm.py` Level B"
                     "（只用于 Gate 2b，不进入任何 AC）")
SCOPE_LINES_1D = (
    "- 结论只对冻结的 Poisson 1D 问题（-u'' = π² sin(πx)，u(0) = u(1) = 0，[0,1]）、本 configId 的架构 / 优化器 / 采样协议、本 seed 集与本执行环境成立。",
    "- 外推禁区：其他 PDE、其他几何、其他架构或训练协议、'PINN 总体可靠'（宪法第三十五章）。",
    "- Red Team 扰动矩阵未执行；C_repro 因无独立执行环境为 BLOCKED，因此 C2 / C3 在任何数值结果下都不可达。",
)


def write_trust_report(attempt_dir: Path, repo_root: Path, *, reference_line: str = REFERENCE_LINE_1D,
                       scope_lines: "Sequence[str]" = SCOPE_LINES_1D, primary_ac: str = "AC-1",
                       should_ac: str = "AC-8") -> Path:
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    pdef = load_json(attempt_dir / "problem_definition.json")
    vector = (read_ref(attempt_dir, summary["currentTrustVectorRef"]) if summary.get("currentTrustVectorRef")
              else load_json(attempt_dir / "trust_vector.json"))
    identity = load_json(attempt_dir / "identity.json")
    transitions = load_json(attempt_dir / "STATE_TRANSITIONS.json")["transitions"]
    manifest = load_json(attempt_dir / "PROVENANCE_MANIFEST.json")["artifacts"]
    decision = (read_ref(attempt_dir, summary["currentDecisionRef"]) if summary.get("currentDecisionRef") else
                (load_json(attempt_dir / "claim_gate_decision.json") if (attempt_dir / "claim_gate_decision.json").exists() else None))
    if summary.get("currentTrustVectorRef") and scope_lines == SCOPE_LINES_1D:
        scope_lines = SCOPE_LINES_1D[:2] + ("- Tier-1 与独立复现状态以本报告的当前机器记录为准；未满足的前提不得由文字解释提升。",)
    sets = pdef["evaluationSets"]
    weakest = (decision.get("weakestLink") if decision else None) or summary.get("weakestLink") or {"dimensions": [d for d in DIMENSIONS if vector["dimensions"][d]["status"] != "PASS"][:1] or ["-"], "status": "-"}
    external = vector["dimensions"]["external"]
    claim_state = sets["claimSetStatus"] + (f"@revision {sets.get('claimSetOpenedAtRevision')}" if sets["claimSetStatus"] == "OPENED" else "")
    lines: list[str] = []
    lines.append("# Trust Report / 可信度报告")
    lines.append(f"Problem spec（冻结问题规格）: {pdef['problemId']} · revision {pdef['revision']} · specHash {_short(pdef['specHash'])}")
    lines.append(reference_line)
    lines.append(f"Evaluation sets / 评估集: D_train {_short(sets['train']['sha256'])} · D_dev {_short(sets['dev']['sha256'])}（诊断/调参/模型选择/扰动）· "
                 f"D_phys {_short(sets['phys']['sha256'])} · D_claim {_short(sets['claim']['sha256'])} {claim_state} · ledger head {_short(summary.get('ledgerHead', '-'))}")
    lines.append(f"C_external evaluated on / 外部一致性评估于: {external.get('evaluationSet', 'n/a（未执行）')}；claim-set consistency: {external['status']}")
    lines.append(f"Report id: tr-{summary['attemptId']}   Generated at: {summary.get('finishedAt', '')}   Gate path: "
                 + " → ".join(f"{t['from']}→{t['to']}[{'G' + str(t['gate']) if t['gate'] else '-'}:{t['result']}]" for t in transitions))
    lines.append(f"Run mode: FORMAL   Code identity: {_short(identity['codeHash'])}   Constitution: {summary['constitutionVersion']}   "
                 f"Environment: {_short(identity['environmentId'])}   git HEAD: {identity['gitHead'][:12]}   workspace dirty: {identity['dirtyCodeIdentityPaths'] or 'no'}")
    lines.append("")
    lines.append(f"> Weakest link / 最弱环节：{', '.join(weakest['dimensions'])} = {weakest['status']}。它限制的结论：{'C2 与 C3（六维全 PASS 才允许）' if weakest['status'] != 'PASS' else '无'}；"
                 "在该维度升为 PASS 之前，任何需要它的 Ck 声称一律阻断（弱链原则，不平均、不抵消）。")
    lines.append("")
    # Result
    lines.append("## Result / 结果")
    lines.append(f"- 最终状态：**{summary['finalState']}**。可信度向量 C = (" + ", ".join(f"{d}={vector['dimensions'][d]['status']}" for d in DIMENSIONS) + ")。")
    training = summary.get("training")
    if training:
        lines.append(f"- 训练可靠性（D_dev {_short(sets['dev']['sha256'])}，相对 L2 对照解析参考 Level A，ε_spec = {pdef['preregistration']['epsilonSpec']}）："
                     f"N = {training['runs']}，k = {training['successes']}（k/N = {training['successRate']}），median = {training['median']:.3e}，IQR = {training['iqr']:.3e}，"
                     f"worst seed = {training['worst']:.3e}，divergent = {training['divergent']}；最好 seed 不进入判定。")
    if (attempt_dir / "gate5b_external.json").exists():
        g5b = load_json(attempt_dir / "gate5b_external.json")
        lines.append(f"- claim 集（{_short(g5b['claimSetSha256'])}，OPENED@revision {g5b['openedAtRevision']}，codeHash {_short(g5b['codeHash'])}）上逐 seed 的 {primary_ac}（相对 L2）："
                     + ", ".join(f"{m['metrics'][primary_ac]:.2e}" for m in g5b["perSeed"]) + f"；MUST 失败：{[m['failedMust'] for m in g5b['perSeed']]}；SHOULD（{should_ac}）失败：{[m['failedShould'] for m in g5b['perSeed']]}。")
    if summary.get("failure"):
        lines.append(f"- 失败记录：Gate 4 FAIL，observedSignatures = {summary['failure']['observedSignatures']}，D_dev 中位量 {json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in summary['failure']['medians'].items()})}。未就地重训。")
    lines.append("")
    # Evidence
    lines.append("## Evidence / 证据")
    for d in DIMENSIONS:
        entry = vector["dimensions"][d]
        says, not_says = MEANING[d]
        lines.append(f"### C_{d} = {STATUS_WORDS[entry['status']]}（说明了什么：{says}；不说明什么：{not_says}）")
        if entry["status"] == "NOT_CHECKED":
            lines.append("- 尚未执行检查，无证据；不构成通过，也不构成失败。")
        else:
            lines.append(f"- 证据指针：{', '.join(p['artifactId'] + '·' + _short(p['sha256']) for p in entry.get('evidencePointers', []))}；评估集：{entry.get('evaluationSet', 'dev/phys' if d in ('train', 'physics') else 'n/a')}")
            lines.extend(_check_lines(entry))
        lines.append("")
    # Uncertainty
    lines.append("## Uncertainty / 不确定性")
    lines.append("- E_model / E_optimization / E_sampling：不单独估计（NOT ESTIMATED）；只报告多 seed 统计（N、median、IQR、最差 seed、k/N）与 D_dev / D_claim 上的实测范数。")
    lines.append("- E_discretization：参考解为解析解，无离散误差；FDM 交叉核对只证明基线子系统正确。")
    lines.append("- E_implementation：G3 的 T1/T3/T4 给出算子精度（见 Evidence）；不排除未测的实现缺陷。")
    lines.append("- 统计含义：N = 10、k ≥ 9 的 PASS 只能以 95% 置信认证 p ≥ 0.55（宪法 10.1）；PASS ≠ 高置信认证。")
    lines.append("")
    # Known failure modes
    lines.append("## Known failure modes / 已知失效模式")
    if (attempt_dir / "diagnosis_record.json").exists():
        dg = load_json(attempt_dir / "diagnosis_record.json")
        ex = dg["discriminatingExperiment"]
        lines.append(f"- 症状 {dg['observedSignatures']} → 根因 **{dg['rootCause']}** → 区分实验 `{ex['experimentId']}`（评估集 {ex['evaluationSet']}；被排除的候选：{sorted(ex['excludes'])}）"
                     + (f" → 回到 Gate {load_json(attempt_dir / 'diagnosis_verdict.json')['route']['gate']}" if (attempt_dir / 'diagnosis_verdict.json').exists() and load_json(attempt_dir / 'diagnosis_verdict.json').get('route') else " → 停线交人工"))
        if "intervention" in ex:
            lines.append("- 受控干预：" + "; ".join(f"{l['level']}: median {l['medianError']:.3e} ({l['seeds']} seeds)" for l in ex["intervention"]["levels"]))
    elif summary.get("failure"):
        lines.append(f"- 症状 {summary['failure']['observedSignatures']} 已登记于 failure_record.json；根因待区分实验（诊断是独立步骤，不在本报告内决定）。")
    elif summary.get("currentTrustVectorRef"):
        lines.append("- 本次 attempt 未登记失败；扰动执行情况与降级结果见当前可信度向量及 Tier-1 记录。未检查的失效模式仍不能排除。")
    else:
        lines.append("- 本次 attempt 没有进入 FAILURE_RECORDED。Red Team 扰动 P1–P21 未在本次校准实验中执行（perturbationsRun 为空）——这是范围限制，不是通过。")
    lines.append("")
    # Allowed / Blocked
    lines.append("## Allowed claims / 允许声称")
    if decision:
        for claim in decision["allowedClaims"]:
            statements = read_ref(attempt_dir, claim["statementRef"])
            lines.append(f"- **{claim['level']}**：{statements[claim['level']]} 成立条件：向量维度不变、冻结规格与代码身份不变。失效条件：{[c['condition'] + ' → ' + c['consequence'] for c in claim['failureConditions']]}")
        if not decision["allowedClaims"]:
            lines.append("- 无。")
    else:
        lines.append("- 无 ClaimGateDecision：状态机停在 FAILURE_RECORDED / STOPPED_THE_LINE，不允许任何声称。")
    lines.append("")
    lines.append("## Blocked claims / 禁止声称")
    if decision:
        for claim in decision["blockedClaims"]:
            lines.append(f"- **{claim['level']}**：{claim['reason']}")
    else:
        lines.append("- C0 / C1 / C2 / C3 全部阻断（无决策文档）。")
    lines.append("")
    # Provenance
    lines.append("## Provenance / 来源")
    lines.append(f"- specHash {pdef['specHash']}；codeHash {identity['codeHash']}；environmentId {identity['environmentId']}；git HEAD {identity['gitHead']}")
    lines.append(f"- 三个评估集 + D_phys：train {sets['train']['sha256']}，dev {sets['dev']['sha256']}，claim {sets['claim']['sha256']}（{claim_state}），phys {sets['phys']['sha256']}；账本头 {summary.get('ledgerHead', '-')}")
    if (attempt_dir / "run_record.json").exists():
        rr = load_json(attempt_dir / "run_record.json")
        lines.append(f"- RunRecord {rr['runId']}：seedSetId {rr['seedSetId']}，seeds {rr['seeds']}，evaluatedOn {rr['evaluatedOn']}")
    lines.append("- Artifact manifest（artifactId · sha256）：")
    for entry in manifest:
        lines.append(f"  - {entry['artifactId']} · {entry['sha256']} · {entry['artifactRole']}")
    lines.append("")
    # Scope
    lines.append("## Scope / 适用范围")
    lines.extend(scope_lines)
    path = attempt_dir / "TRUST_REPORT.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


# ------------------------------------------------------------------ plots

def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plots_experiment1(attempt_dir: Path) -> list[Path]:
    from . import pinn_torch

    plt = _plt()
    out = attempt_dir / "plots"
    out.mkdir(exist_ok=True)
    identity = load_json(attempt_dir / "identity.json")
    config = load_json(Path(identity["configPath"]).resolve() if Path(identity["configPath"]).is_absolute() else attempt_dir.parents[3] / identity["configPath"])
    dev = sorted(s["inputs"][0] for s in load_json(attempt_dir / "sets/dev.json")["samples"])
    runs = sorted(attempt_dir.glob("runs/run-*.json"))
    exact = [reference.solution(x) for x in dev]
    paths = []
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    per_seed_err = []
    for path in runs:
        run = load_json(path)
        model = pinn_torch.model_from_weights(config, run["weights"])
        fld = pinn_torch.fields(model, dev)
        err = [abs(a - b) for a, b in zip(fld["u"], exact)]
        res = [abs(-uxx - reference.forcing(x)) for uxx, x in zip(fld["uxx"], dev)]
        axes[0].plot(dev, fld["u"], lw=0.8, alpha=0.6)
        axes[1].semilogy(dev, err, lw=0.8, alpha=0.6)
        axes[2].semilogy(dev, res, lw=0.8, alpha=0.6)
        per_seed_err.append(run["devRelL2"])
    axes[0].plot(dev, exact, "k--", lw=1.5, label="analytic sin(pi x)")
    axes[0].set_title("PINN (10 seeds) vs analytic on D_dev"); axes[0].legend()
    axes[1].set_title("pointwise |u - u*| on D_dev"); axes[2].set_title("|-u'' - f| on D_dev (holdout residual)")
    fig.tight_layout(); p = out / "exp1_solution_error_residual.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    g4 = load_json(attempt_dir / "gate4_training.json")["detail"]
    claim = load_json(attempt_dir / "gate5b_external.json")["perSeed"] if (attempt_dir / "gate5b_external.json").exists() else None
    fig, ax = plt.subplots(figsize=(7, 4))
    idx = list(range(len(per_seed_err)))
    ax.bar([i - 0.2 for i in idx], per_seed_err, width=0.4, label="dev relative L2")
    if claim:
        ax.bar([i + 0.2 for i in idx], [m["metrics"]["AC-1"] for m in claim], width=0.4, label="claim AC-1 relative L2")
    ax.axhline(g4["seedStatistics"]["median"], color="k", ls=":", label="dev median")
    ax.axhline(1e-3, color="r", ls="--", label="epsilon_spec / AC-1 threshold")
    ax.set_yscale("log"); ax.set_xlabel("seed triplet index"); ax.set_title("multi-seed error distribution (all seeds shown; best seed never judged)"); ax.legend(fontsize=8)
    fig.tight_layout(); p = out / "exp1_multiseed_errors.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    fig, ax = plt.subplots(figsize=(7, 4))
    for path in runs:
        run = load_json(path)
        steps = [h["step"] for h in run["lossHistory"]]
        ax.semilogy(steps, [h["pde"] for h in run["lossHistory"]], color="tab:blue", alpha=0.4, lw=0.8)
        ax.semilogy(steps, [h["devRelL2"] for h in run["lossHistory"]], color="tab:red", alpha=0.4, lw=0.8)
    ax.plot([], [], color="tab:blue", label="pde loss term (training points)"); ax.plot([], [], color="tab:red", label="true dev relative L2 (diagnostic only)")
    ax.set_xlabel("step"); ax.set_title("loss vs true error (loss is not an accuracy metric)"); ax.legend()
    fig.tight_layout(); p = out / "exp1_loss_vs_error.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    return paths


def plots_experiment2(bad_dir: Path, revised_dir: Path | None, baseline_dir: Path | None) -> list[Path]:
    from . import pinn_torch

    plt = _plt()
    out = bad_dir / "plots"
    out.mkdir(exist_ok=True)
    paths = []
    identity = load_json(bad_dir / "identity.json")
    root = bad_dir.parents[3]
    config = load_json(root / identity["configPath"])
    dev = sorted(s["inputs"][0] for s in load_json(bad_dir / "sets/dev.json")["samples"])
    exact = [reference.solution(x) for x in dev]
    pool = [s["inputs"][0] for s in load_json(bad_dir / "sets/train.json")["samples"] if s["kind"] == "interior"]
    runs = sorted(bad_dir.glob("runs/run-*.json"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for path in runs:
        run = load_json(path)
        model = pinn_torch.model_from_weights(config, run["weights"])
        fld = pinn_torch.fields(model, dev)
        axes[0].plot(dev, fld["u"], lw=0.8, alpha=0.6)
        axes[1].semilogy(dev, [abs(a - b) for a, b in zip(fld["u"], exact)], lw=0.8, alpha=0.6)
    axes[0].plot(dev, exact, "k--", label="analytic"); axes[0].legend()
    axes[0].set_title(f"bad sampling (N_train={config['sampling']['collocationCount']}) solution, 10 seeds"); axes[1].set_title("pointwise |u - u*| on D_dev")
    fig.tight_layout(); p = out / "exp2_bad_sampling_solution_error.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    fig, ax = plt.subplots(figsize=(9, 2.5))
    first = load_json(runs[0])
    ax.eventplot([[pool[i] for i in first["collocationIndices"]]], lineoffsets=1, linelengths=0.8, colors="tab:red")
    if baseline_dir is not None:
        base_first = load_json(sorted(baseline_dir.glob("runs/run-*.json"))[0])
        base_pool = [s["inputs"][0] for s in load_json(baseline_dir / "sets/train.json")["samples"] if s["kind"] == "interior"]
        ax.eventplot([[base_pool[i] for i in base_first["collocationIndices"]]], lineoffsets=0, linelengths=0.8, colors="tab:blue")
        ax.set_yticks([0, 1]); ax.set_yticklabels([f"baseline N={len(base_first['collocationIndices'])}", f"bad N={len(first['collocationIndices'])}"])
    ax.set_xlim(0, 1); ax.set_title("collocation locations of seed 0 (sampling seed selects pool points)")
    fig.tight_layout(); p = out / "exp2_sampling_locations.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    if (bad_dir / "intervention.json").exists():
        inter = load_json(bad_dir / "intervention.json")
        fig, ax = plt.subplots(figsize=(6, 4))
        for lvl in inter["levels"]:
            ax.scatter([lvl["collocationCount"]] * len(lvl["errors"]), lvl["errors"], alpha=0.6)
        ax.plot([l["collocationCount"] for l in inter["levels"]], [l["medianError"] for l in inter["levels"]], "k-o", label="median")
        ax.axhline(1e-3, color="r", ls="--", label="epsilon_spec"); ax.set_xscale("log", base=2); ax.set_yscale("log")
        ax.set_xlabel("collocation count (only factor changed)"); ax.set_ylabel("dev relative L2"); ax.set_title("controlled sampling intervention S1 < S2 < S3"); ax.legend()
        fig.tight_layout(); p = out / "exp2_intervention.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    if revised_dir is not None and (revised_dir / "gate4_training.json").exists():
        before = [r["devRelL2"] for r in load_json(bad_dir / "gate4_training.json")["detail"]["perSeed"]]
        after = [r["devRelL2"] for r in load_json(revised_dir / "gate4_training.json")["detail"]["perSeed"]]
        fig, ax = plt.subplots(figsize=(7, 4))
        idx = list(range(len(before)))
        ax.bar([i - 0.2 for i in idx], before, width=0.4, label=f"before revision (N_train={config['sampling']['collocationCount']})")
        ax.bar([i + 0.2 for i in idx], after, width=0.4, label="after revision (sampling only)")
        ax.axhline(1e-3, color="r", ls="--", label="epsilon_spec"); ax.set_yscale("log"); ax.set_xlabel("seed triplet index"); ax.set_ylabel("dev relative L2"); ax.legend(fontsize=8)
        ax.set_title("before vs after revision"); fig.tight_layout(); p = out / "exp2_before_after_revision.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    transitions = load_json(bad_dir / "STATE_TRANSITIONS.json")["transitions"]
    if revised_dir is not None:
        transitions = transitions + load_json(revised_dir / "STATE_TRANSITIONS.json")["transitions"]
    fig, ax = plt.subplots(figsize=(12, 3))
    labels = [t["to"] for t in transitions]
    ax.plot(range(len(labels)), [0] * len(labels), "o-", color="tab:gray")
    for i, t in enumerate(transitions):
        ax.annotate(f"{t['to']}\n{('G' + str(t['gate']) + ':') if t['gate'] else ''}{t['result']}", (i, 0), textcoords="offset points", xytext=(0, 8 if i % 2 == 0 else -28), ha="center", fontsize=7)
    ax.set_yticks([]); ax.set_xticks([]); ax.set_title("state-machine transitions (bad attempt → diagnosis → revision → re-entry)")
    fig.tight_layout(); p = out / "exp2_state_transitions.png"; fig.savefig(p, dpi=120); plt.close(fig); paths.append(p)
    return paths
