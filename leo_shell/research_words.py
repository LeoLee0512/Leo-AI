"""3.2.0 · Plain words for the research panel.

The panel renders structure; the sentences a person reads come from here. Like ``evidence_guide``
this module lives outside the research code identity (see ``pinn/research/worker.py``
IDENTITY_EXTRAS), so wording can be improved later without changing a product run's codeHash.
Nothing here decides anything: every value is read from the task's own records, raw codes are
passed through next to the words, and a missing or unreadable record only makes a sentence shorter.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

# Claim levels, lowest first; each needs the one before it (Constitution, claim calculus).
CLAIM_LADDER = (
    ("C0", "代码能正确运行", "数学设定与实现两项检查通过"),
    ("C1", "训练收敛", "每个种子都按规定跑完并收敛"),
    ("C2", "精度声明", "这道题上的误差低于事先约定的值"),
    ("C3", "可推广结论", "还需要至少 5 次独立完成的合格运行"),
)

# The six checks in execution order: name, raw gate, what it establishes in one line.
DIMENSIONS = (
    ("math", "数学设定", "G1", "方程、区域与边界条件互相一致，精确解代回去成立。"),
    ("impl", "实现", "G3", "程序算的就是这道题，并能识破事先准备的错误样例。"),
    ("train", "训练", "G4", "每个种子都按规定跑完，开发集上的误差达标。"),
    ("physics", "物理", "G5a", "守恒、对称、最大值原理等物理检查都在容差内。"),
    ("external", "与精确解一致", "G5b", "在训练碰不到的盲测集上，所有必须满足的判据都成立。"),
    ("repro", "独立复现", "G6", "换一个环境、换一组种子重算，结果在容差内一致。"),
)
GATE_DIMENSION = {1: "math", 3: "impl", 4: "train", 5: "external", 6: "repro"}

STATUS = {"PASS": "通过", "PARTIAL": "部分通过", "FAIL": "未通过", "BLOCKED": "受阻", "NOT_CHECKED": "未检查",
          "NOT_RUN": "未进行", "NOT_APPLICABLE": "不适用"}

PHASES = {
    "main": ("主实验", "{runs} 个种子训练，在开发集上评估，再打开封存的盲测集逐条核对判据。"),
    "tier1": ("扰动检验", "对实现、数学设定和训练各做一组小改动，看结论是否依然成立。"),
    "reproduction": ("独立复现", "在另一个科学环境里、用另一组种子重算。"),
    "g6": ("复现判定", "比较两次结果是否在容差内一致。"),
    "supervisor": ("运行前核对", "开始计算前核对代码、环境与确认包是否一致。"),
}

PREPARATION_STEPS = (
    ("identity", "核对代码身份", "代码与发布时一致"),
    ("environments", "检查两个科学环境", "主环境负责计算，复现环境负责独立重算，两者必须互相独立"),
    ("claim", "预留盲测集", "取 1 个训练碰不到的盲测集并封存"),
    ("plan", "生成运行确认包", "冻结问题、方法与验收规则"),
)

SIGNATURES = {
    "sLocalizedError": "局部误差超标：某一小块区域的误差超过了约定值",
    "sPdeResidual": "方程残差偏大：解没有很好地满足方程",
    "sBcResidual": "边界误差偏大：解没有很好地满足边界条件",
    "sConservation": "守恒量有偏差",
    "sSeedSensitive": "对随机种子敏感：不同种子的结果差别过大",
    "sPinnCfd": "与参考数值解不一致",
}

FINAL_STATES = {
    "FAILURE_RECORDED": "失败已如实记录",
    "STOPPED_THE_LINE": "停线：原因未定，不自动重试，交由人判断",
    "DIAGNOSED": "已诊断出原因",
    "ACCEPTED": "已通过",
}

END_REASONS = {
    "WORKER_LOST": "计算进程意外退出（可能是应用被关闭或电脑睡眠）",
    "RUN_CODE_CHANGED": "运行期间代码发生了变化",
    "PLAN_CODE_CHANGED": "代码与运行确认包不一致",
    "PREPARED_EVIDENCE_CHANGED": "准备好的数据被改动",
    "PLAN_ENVIRONMENT_CHANGED": "科学环境与运行确认包不一致",
    "RUN_APPROVAL_STALE": "运行确认与确认包不一致",
    "RESOURCE_BUSY": "另一项计算正在占用",
    "RUN_NOT_ADMITTED": "任务不处于已确认运行的状态",
    "APP_CLOSED": "应用被关闭",
}

# Acceptance criteria by number; 1D is AC-n, 2D is AC2D-n, same meaning.
CRITERIA = {
    "1": "整体相对误差（L2）", "2": "最大逐点误差", "3": "边界上的误差", "4": "方程残差",
    "5": "解的积分量误差", "6": "边界处导数的误差", "7": "能量恒等式误差", "8": "梯度误差",
    "9": "局部误差（最差一小块区域）",
}

BLOCKED_REASONS = (
    (re.compile(r"no independently qualified C2 runs", re.I), "还需要至少 5 次独立完成的合格运行，目前只有这 1 次"),
    (re.compile(r"reference.*evidence level", re.I), "参考解的证据等级不够"),
    (re.compile(r"EXPLORATORY", re.I), "这是一次探索性运行，最高只允许描述性结论"),
)


def criterion_name(criterion_id):
    number = str(criterion_id).rsplit("-", 1)[-1]
    return CRITERIA.get(number, str(criterion_id))


def sci(value):
    """1.079e-03 -> '1.08 × 10⁻³' (display only)."""
    try:
        mantissa, exponent = f"{float(value):.2e}".split("e")
    except (TypeError, ValueError):
        return str(value)
    mantissa = mantissa.rstrip("0").rstrip(".")
    return f"{mantissa} × 10{str(int(exponent)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


def panel_words(family=None):
    """Everything the panel needs to explain itself, as plain data."""
    return {
        "claimLadder": [{"level": level, "name": name, "text": text} for level, name, text in CLAIM_LADDER],
        "dimensions": [{"key": key, "name": name, "gate": gate, "text": text} for key, name, gate, text in DIMENSIONS],
        "status": STATUS,
        "phases": {key: {"name": name, "text": text} for key, (name, text) in PHASES.items()},
        "preparationSteps": [{"key": key, "name": name, "text": text} for key, name, text in PREPARATION_STEPS],
        "signatures": SIGNATURES,
        "finalStates": FINAL_STATES,
        "endReasons": END_REASONS,
        "family": {"poisson1d": "一维", "poisson2d": "二维", "annulus": "环形"}.get(family or "", ""),
    }


def blocked_reason(reason):
    for pattern, text in BLOCKED_REASONS:
        if reason and pattern.search(str(reason)):
            return text
    return None


def annotate_verification(verification):
    """Add plain words next to machine reasons; the machine fields are left exactly as they are."""
    for claim in verification.get("blockedClaims") or []:
        if isinstance(claim, dict):
            plain = blocked_reason(claim.get("reason"))
            if plain:
                claim["plain"] = plain
    return verification


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _failed_criteria(directory):
    """Which MUST criteria failed on how many seeds, with the worst value and the line."""
    record = _read(Path(directory) / "work/attempts/main/gate5b_external.json")
    if not isinstance(record, dict) or not isinstance(record.get("perSeed"), list):
        return []
    thresholds = record.get("thresholds") or {}
    seeds = record["perSeed"]
    found = {}
    for seed in seeds:
        if not isinstance(seed, dict):
            continue
        for criterion in seed.get("failedMust") or []:
            entry = found.setdefault(criterion, {"criterion": criterion, "seeds": 0, "worst": None})
            entry["seeds"] += 1
            value = (seed.get("metrics") or {}).get(criterion)
            if isinstance(value, (int, float)) and (entry["worst"] is None or value > entry["worst"]):
                entry["worst"] = value
    out = []
    for criterion, entry in sorted(found.items()):
        entry.update({"name": criterion_name(criterion), "threshold": thresholds.get(criterion), "total": len(seeds)})
        out.append(entry)
    return out


def failure_story(directory, task, failure):
    """What happened, what it means and what the person can do, for a run that ended without a claim."""
    failure = failure or {}
    completion = failure.get("completion") or task.get("completion") or {}
    state = task.get("state")
    facts = []
    phase = completion.get("phase")
    if phase:
        name = PHASES.get(phase, (phase, ""))[0]
        how = END_REASONS.get(completion.get("reason")) if completion.get("reason") else (
            "这一阶段没有通过" if completion.get("exitCode") is not None else "")
        raw = f"phase {phase}" + (f" · {completion['reason']}" if completion.get("reason") else "") + (
            f" · exit {completion['exitCode']}" if completion.get("exitCode") is not None else "")
        facts.append({"plain": f"在「{name}」阶段结束" + (f"：{how}" if how else ""), "raw": raw})
    gate = failure.get("gate")
    if gate is not None:
        dimension = GATE_DIMENSION.get(gate)
        label = next((name for key, name, _, _ in DIMENSIONS if key == dimension), None)
        facts.append({"plain": f"没通过的是第 {gate} 关" + (f"「{label}」" if label else ""), "raw": f"Gate {gate}"})
    for signature in failure.get("observedSignatures") or []:
        facts.append({"plain": "观察到的问题：" + SIGNATURES.get(signature, signature), "raw": signature})
    if failure.get("tier1Passed") is False:
        facts.append({"plain": "扰动检验没有通过", "raw": "Tier-1 FAIL"})
    final = failure.get("finalState")
    if final:
        facts.append({"plain": "记录状态：" + FINAL_STATES.get(final, final), "raw": final})

    criteria = _failed_criteria(directory)
    if criteria:
        parts = []
        for c in criteria:
            line = f"{c['total']} 个种子里有 {c['seeds']} 个没有满足「{c['name']}」"
            if c["worst"] is not None and isinstance(c["threshold"], (int, float)):
                line += f"（最差 {sci(c['worst'])}，约定上限 {sci(c['threshold'])}）"
            parts.append(line)
        happened = "打开封存的盲测集核对时，" + "；".join(parts) + "。"
        means = ("按规则，只要有一个种子不满足必须满足的判据，就不能声明精度。"
                 "原因还没有查清，系统不会自己猜，交给你判断。")
    elif state == "CANCELLED":
        happened, means = "计算在完成前被停止了。", "没有跑完的计算不能下结论；已有的记录全部保留。"
    elif state == "TIMED_OUT":
        happened, means = "计算用完了时间上限，没有跑完。", "没有跑完的计算不能下结论；已有的记录全部保留。"
    elif state == "INTERRUPTED":
        happened = "计算中途中断：" + END_REASONS.get(completion.get("reason"), "计算进程意外退出") + "。"
        means = "没有跑完的计算不能下结论；中断不能接着算，因为接着算会改变代码身份，已完成的部分就不作数了。"
    elif facts:
        happened = "；".join(f["plain"] for f in facts[:2]) + "。"
        means = "这次运行没有通过全部检查，按规则不下结论。失败本身也是结果，记录都原样保留。"
    else:
        happened, means = "这次计算没有正常结束。", "按规则不下结论；记录都原样保留。"
    return {"happened": happened, "means": means,
            "next": "可以以此草案新建任务再试一次（准备时会用掉 1 个新的盲测集），或先修改模型设定。",
            "facts": facts, "criteria": criteria}
