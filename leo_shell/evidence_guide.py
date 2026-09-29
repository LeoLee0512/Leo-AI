"""A reader's guide to a verified research run, written for scientists rather than engineers.

The guide is a *view* of the evidence, never evidence itself: every number is read from the
run's own records, and nothing here can change what the machine allowed. It lives outside the
research code identity (see ``pinn/research/worker.py`` IDENTITY_EXTRAS), so its wording can be
improved without changing a product run's codeHash or voiding a prepared plan.
"""
from __future__ import annotations

from datetime import datetime
import html
import json
from pathlib import Path
import re

SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

# What each dimension establishes, in the words a mathematician would use.
DIMENSIONS = (
    ("math", "问题本身", "数学",
     "一个二阶方程配两个 Dirichlet 边界条件，问题适定；方程无量纲；参考解确实满足方程与边界。"),
    ("impl", "程序算的是这道题", "实现",
     "把精确解代入程序里的残差算子与边界算子，结果在机器精度量级；自动求导与差分近似一致；"
     "训练、开发、物理、盲测四组点互不重叠；验证程序能识破事先准备的错误样例。"),
    ("train", "训练可靠", "训练",
     "{runs} 次独立训练都跑满固定步数，发散 {divergent} 次；开发集相对 L2 误差中位数 {median}，最差 {worst}，"
     "离散程度在事先规定的范围内。"),
    ("physics", "物理上说得通", "物理",
     "通量平衡、能量恒等式 ∫u′² = ∫f u、正性、关于 x = ½ 的对称性、单调性与最大值原理都在事先规定的阈值内成立。"),
    ("external", "与精确解一致", "外部盲测",
     "在训练时从未见过、事先封存的 {claimPoints} 个检验点上逐个种子比较，所有必须满足的判据都成立；"
     "逐种子相对 L2 误差最大 {maxClaim}，验收线 {epsilon}。"),
    ("repro", "别人也能算出来", "复现",
     "同一份代码、同一个问题，在独立安装的环境中换一组种子重算：误差中位数 {medianB}，"
     "与原结果 {medianA} 相差 {medianDiff}；规定的容差是 {tolerance}。"),
)

# Plain words for individual checks; the raw machine reason is always shown next to it.
CHECKS = {
    "M1-fieldCountClosure": "方程个数与未知函数个数相等",
    "M2-boundaryConditionCount": "边界条件的个数与类型使问题有唯一解",
    "M3-dimensionalHomogeneity": "方程各项量纲一致（无量纲）",
    "M5-geometryBinding": "区间两端分别绑定到两个边界条件",
    "M6-referenceEquationBinding": "参考解对应的正是这道题",
    "T1-autogradVsFiniteDifference": "自动求导与有限差分一致",
    "T3-residualOperatorOnReference": "精确解代入残差算子，残差为机器精度",
    "T4-boundaryOperatorOnReference": "精确解代入边界算子，边界误差为机器精度",
    "T8-lossTermSeparation": "方程残差与边界误差分开记录，权重冻结",
    "T9-collocationDisjointness": "四组计算点互不重叠",
    "T10-validatorControlFixtures": "验证程序能识破事先准备的错误样例",
    "G4-trainingIntegrity": "每次训练都跑满固定步数，没有数值溢出",
    "G4-seedProtocol": "10 个种子的成功率、中位数、最差值与离散度都达标",
    "G4-lossErrorDecoupling": "没有出现「损失下降而误差不降」的假收敛",
    "PH1-fluxBalance": "通量平衡",
    "PH2-energyBalance": "能量恒等式",
    "PH3-positivity": "正性（源项非负时解非负）",
    "PH4-symmetry": "关于 x = ½ 对称",
    "PH5-monotonicity": "单调性",
    "PH6-maximumPrinciple": "最大值原理",
    "PH7-spd": "离散算子正定、能量为正",
    "PH10-momentumBudget": "动量守恒（标量方程不适用）",
    "PH11-freeEnergy": "自由能（稳态椭圆方程不适用）",
    "G5b-acceptanceCriteriaMust": "盲测集上所有必须满足的判据成立",
    "G5b-acceptanceCriteriaShould": "盲测集上建议满足的判据成立",
    "G6-independentReproduction": "独立环境复现一致",
}

GLOSSARY = (
    ("PINN", "物理信息神经网络：用神经网络表示解 u(x)，训练目标是让方程残差和边界误差尽量小。"),
    ("硬边界", "把解写成 u = x(1−x)·N(x)，边界条件自然精确满足。"),
    ("随机种子", "决定网络初始值与采样点的随机数起点；换种子重训可以检验结果是不是碰巧。"),
    ("相对 L2 误差", "‖u − u*‖₂ / ‖u*‖₂，用高阶求积在检验点上计算；u* 为精确解。"),
    ("盲测集", "训练前生成并封存的一批检验点，训练过程碰不到，只允许打开一次。"),
    ("Tier-1 扰动检验", "对实现、数学设定与训练做一组小扰动，检查结论是否稳定。"),
    ("G6", "复现判定：独立环境、不同种子重算的结果必须在容差内一致。"),
    ("C0 / C1 / C2 / C3", "结论等级。C2 是在给定问题上的精度声明；C3 还需要其他独立完成的合格运行。"),
    ("代码指纹（codeHash）", "参与计算的全部源文件的内容哈希；任何一个字节改动，指纹都会变。"),
)

# 2.2.11 · The 2D template differs only in words: the equation, the boundary, the physics checks
# and where its blind points live. Everything numeric is still read from the run's own records.
FAMILY_TEXT = {
    "poisson1d": {
        "math": DIMENSIONS[0][3], "physics": DIMENSIONS[3][3],
        "solution": "sin(πx)", "problem": "这道一维 Poisson 问题",
        "equation": "−u″(x) = π² sin(πx)，0 < x < 1，u(0) = u(1) = 0",
        "hardBoundary": "把解写成 u = x(1−x)·N(x)，边界条件自然精确满足。",
        "claimDir": "work/experiments/poisson1d/problems", "claimGlob": "*-claim-GL*.json",
        "cannot": "这个方法对其他方程、其他区间或其他边界条件同样准确。", "checks": {},
    },
    "poisson2d": {
        "math": "一个二阶椭圆方程配四条边上的 Dirichlet 边界条件，问题适定；方程无量纲；参考解确实满足方程与四条边界。",
        "physics": "通量平衡、能量恒等式 ∬|∇u|² = ∬f u、正性、关于对角线 x = y 的交换对称、单调性与最大值原理都在事先规定的阈值内成立。",
        "solution": "sin(πx)·sin(πy)", "problem": "这道二维 Poisson 问题（单位正方形）",
        "equation": "−(u_xx + u_yy) = 2π² sin(πx) sin(πy)，0 < x, y < 1，四条边上 u = 0",
        "hardBoundary": "把解写成 u = x(1−x)y(1−y)·N(x, y)，四条边上的边界条件自然精确满足。",
        "claimDir": "work/experiments/poisson2d/problems", "claimGlob": "*-claim-D2C-*.json",
        "cannot": "这个方法对其他方程、其他区域形状（如带孔、带角点）或其他边界条件同样准确。",
        "checks": {"M5-geometryBinding": "正方形的四条边分别绑定到四个边界条件",
                   "T2-secondDerivativeComponentSeparation": "u_xx 与 u_yy 分开求导（非对称探针能识破 x、y 混淆）",
                   "T4-boundaryOperatorFourEdges": "精确解代入四条边的边界算子，边界误差为机器精度",
                   "PH4-symmetry": "关于对角线 x = y 交换对称"},
    },
}

# The package, file by file, for readers who want to open the records themselves.
EVIDENCE_MAP = (
    ("证据说明书.html", "你正在读的这份说明书；由证据生成，本身不是证据。"),
    ("execution-plan.json", "运行确认包：问题、方法、验收阈值与代码指纹，在计算之前冻结。"),
    ("run-approval.json", "你确认正式运行的记录（时间、确认的内容哈希）。"),
    ("completion.json", "运行结束的回执，列出全部证据文件的哈希。"),
    ("work/attempts/main/TRUST_REPORT.md", "机器生成的完整可信度报告（技术版）。"),
    ("work/attempts/main/RUN_SUMMARY.json", "主实验摘要：最终状态、训练统计、盲测结果。"),
    ("work/attempts/main/gate1_math.json", "问题本身的检查记录。"),
    ("work/attempts/main/gate3_implementation.json", "程序实现的检查记录。"),
    ("work/attempts/main/gate4_training.json", "训练可靠性的检查记录。"),
    ("work/attempts/main/gate5a_physics.json", "物理检查记录。"),
    ("work/attempts/main/gate5b_external.json", "盲测集上的比较记录。"),
    ("work/attempts/main/tier1_redteam.json", "Tier-1 扰动检验记录。"),
    ("work/attempts/main/gate6_reproducibility_executed.json", "独立复现判定记录。"),
    ("work/attempts/main/claim_set_ledger.json", "盲测集台账：封存与打开的时间，只允许打开一次。"),
    ("work/attempts/main/claim_gate_decision_g6.json", "最终结论判定：允许与被阻断的结论等级。"),
    ("work/attempts/main/identity.json", "代码指纹与运行环境。"),
    ("work/attempts/reproduction/", "独立环境复现的完整记录。"),
    ("source/", "运行所用的全部源代码副本，可按 REPRODUCE.md 独立重算。"),
)


def sci(value, digits=3):
    """2.519e-04 -> '2.52 × 10⁻⁴'."""
    if not isinstance(value, (int, float)) or value != value:
        return "—"
    if value == 0:
        return "0"
    mantissa, exponent = f"{value:.{digits - 1}e}".split("e")
    exponent = int(exponent)
    if exponent == 0:
        return mantissa
    return f"{mantissa} × 10{str(exponent).translate(SUPERSCRIPT)}"


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _minutes(start, end):
    try:
        a = datetime.fromisoformat(start.replace("Z", "+00:00"))
        b = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    seconds = int((b - a).total_seconds())
    return f"{seconds // 60} 分 {seconds % 60:02d} 秒" if seconds >= 0 else None


def _clock(stamp):
    """UTC timestamp -> local wall-clock HH:MM, as the person saw it."""
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone().strftime("%m-%d %H:%M")
    except (AttributeError, ValueError):
        return "—"


def build_guide(task_dir, task, verification):
    """The guide's content for a COMPLETED, verified task; ``None`` when there is nothing to vouch for."""
    if not verification or not verification.get("verified"):
        return None
    task_dir = Path(task_dir)
    main = task_dir / "work/attempts/main"
    summary = _read(main / "RUN_SUMMARY.json") or {}
    plan = _read(task_dir / "execution-plan.json") or {}
    approval = _read(task_dir / "run-approval.json") or {}
    completion = _read(task_dir / "completion.json") or {}
    ledger = _read(main / "claim_set_ledger.json") or []
    config = plan.get("solverConfiguration") or {}
    family = plan.get("family") if plan.get("family") in FAMILY_TEXT else "poisson1d"
    words = FAMILY_TEXT[family]
    epsilon = (config.get("preregistration") or {}).get("epsilonSpec")
    training = summary.get("training") or {}
    evaluation = summary.get("claimEvaluation") or {}
    if family == "poisson2d":
        per_seed = [row.get("AC2D-1") for row in evaluation.get("perSeed") or [] if isinstance(row, dict)]
        per_seed = [v for v in per_seed if isinstance(v, (int, float))]
    else:
        per_seed = evaluation.get("perSeedAC1") or []
    max_claim = max(per_seed) if per_seed else None
    report = (summary.get("g6") or {}).get("report") or {}
    tolerance = (plan.get("expectedTolerance") or {}).get("devRelL2MedianAbsDiff")
    claim_points = None
    for path in (task_dir / words["claimDir"]).glob(words["claimGlob"]):
        doc = _read(path)
        if doc and isinstance(doc.get("samples"), list):
            claim_points = len(doc["samples"])
    opened = [e for e in ledger if e.get("event") == "OPENED"]
    sealed = [e for e in ledger if e.get("event") == "SEALED"]
    allowed = list(verification.get("allowedClaims") or [])
    top = allowed[-1] if allowed else None
    values = {"runs": training.get("runs", "—"), "divergent": training.get("divergent", "—"),
              "median": sci(training.get("median")), "worst": sci(training.get("worst")),
              "claimPoints": claim_points or "—", "maxClaim": sci(max_claim), "epsilon": sci(epsilon, 1),
              "medianA": sci(report.get("medianA")), "medianB": sci(report.get("medianB")),
              "medianDiff": sci(report.get("medianAbsDiff")), "tolerance": sci(tolerance, 1)}

    headline = (f"在这道题上，Leo 算出的解与精确解 {words['solution']} 的相对 L2 误差最大为 {values['maxClaim']}，"
                f"低于事先规定的 {values['epsilon']}，可以作为精度声明（{top}）。" if top == "C2" else
                f"这次运行的证据核验通过，机器允许的最高结论等级是 {top or '无'}。")
    margin = (epsilon / max_claim) if isinstance(epsilon, (int, float)) and max_claim else None
    repro_passed = ((verification.get("dimensions") or {}).get("repro") or {}).get("status") == "PASS"
    numbers = [
        {"label": "最大误差", "value": values["maxClaim"],
         "text": f"{values['runs']} 次独立训练里最差的一次，在事先封存的 {values['claimPoints']} 个检验点上的相对 L2 误差。"
                 f"验收线是 {values['epsilon']}" + (f"，还有约 {margin:.1f} 倍余量。" if margin and margin > 1 else "。")},
        {"label": "成功率", "value": str(training.get("successRate", "—")).replace("/", " / "),
         "text": f"用 {values['runs']} 组不同的随机种子各训练一次，全部达标才算通过，不是碰巧一次成功。"},
        {"label": "独立复现", "value": values["medianB"],
         "text": f"在另一套独立安装的环境、另一组种子上重算的误差中位数；与原结果 {values['medianA']} 的差"
                 + ("在规定的容差之内。" if repro_passed else "没有通过复现判定。")},
    ]
    elapsed = _minutes(approval.get("at"), completion.get("at"))
    if elapsed:
        numbers.append({"label": "用时", "value": elapsed, "text": "从你确认正式运行到全部检查完成。"})

    can, cannot = [], [words["cannot"]]
    if top == "C2":
        can.append(f"用硬边界 PINN 求解{words['problem']}，相对 L2 误差 ≤ {values['epsilon']}（实测最大 {values['maxClaim']}）。")
        can.append("这一结果对随机种子稳健，并在独立环境中复现。")
    for blocked in verification.get("blockedClaims") or []:
        level = blocked.get("level")
        cannot.append(f"更高一级的结论（{level}）：还需要其他独立完成的合格运行。" if level == "C3"
                      else f"{level}：{blocked.get('reason', '被阻断')}")

    dimensions = []
    for key, name, short, text in DIMENSIONS:
        text = words.get(key, text)
        record = (verification.get("dimensions") or {}).get(key) or {}
        checks = []
        for check in record.get("checks") or []:
            check_id = check.get("checkId", "")
            status = check.get("status") or ("不适用" if check.get("applicability") == "NOT_APPLICABLE" else "—")
            plain = words["checks"].get(check_id) or CHECKS.get(check_id, check_id)
            checks.append({"id": check_id, "plain": plain, "status": status,
                           "reason": check.get("reason") or check.get("notApplicableReason") or ""})
        dimensions.append({"key": key, "name": name, "short": short, "status": record.get("status", "NOT_CHECKED"),
                           "text": text.format(**values), "checks": checks})

    chain = [
        {"title": "标准先定", "text": "验收阈值在计算之前冻结进运行确认包，算完之后不能再调。",
         "proof": "冻结于 " + _clock(plan.get("createdAt"))},
        {"title": "考题封存", "text": "检验点在训练前生成并封存，训练过程碰不到。",
         "proof": "封存于 " + _clock(sealed[0].get("at")) if sealed else "封存记录缺失"},
        {"title": "只拆一次", "text": "封存的检验点只允许打开一次，台账记录打开时间，不能反复试到满意为止。",
         "proof": f"台账：打开 {len(opened)} 次"},
        {"title": "代码有指纹", "text": "参与计算的每个文件都有指纹，改动一个字节指纹就会变。",
         "proof": "指纹 " + str(verification.get("codeHash") or plan.get("codeHash") or "—")[:8] + "…"},
        {"title": "独立复算", "text": "另一套独立环境、另一组种子重算，结果一致才算通过。",
         "proof": "复现" + ("通过" if (verification.get("dimensions") or {}).get("repro", {}).get("status") == "PASS" else "未通过")},
    ]
    return {"schemaVersion": "leo.evidenceGuide/1", "taskId": task.get("taskId"), "headline": headline,
            "subline": "六个方面的检查全部通过；换一套独立的计算环境、换一组随机种子重算，结果一致。"
            if all(d["status"] == "PASS" for d in dimensions) else "部分检查没有全部通过，详见下方各项。",
            "numbers": numbers, "can": can, "cannot": cannot, "dimensions": dimensions, "chain": chain,
            "glossary": [[term, words["hardBoundary"] if term == "硬边界" else text] for term, text in GLOSSARY],
            "map": [list(m) for m in EVIDENCE_MAP],
            "problem": {"prompt": task.get("prompt", ""), "equation": words["equation"]}}


_CSS = """
:root{--paper:#F2E8D8;--surface:#FAF4E9;--ink:#30271F;--ink-2:#594B3C;--muted:#736451;--line:rgba(105,78,43,.16);
--accent:#9C3A28;--bamboo:#56784C;--bamboo-wash:#E1E8D3;--bamboo-ink:#3B5231;--slate-wash:#E4DDD4;--slate-ink:#463E36;
--indigo:#3E5E70;--serif:"Noto Serif SC","Songti SC","SimSun",Georgia,serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.8 "Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:980px;margin:0 auto;padding:40px 28px 60px}
h1{font:500 28px/1.3 var(--serif);margin:0 0 6px}.sub{color:var(--muted);margin:0 0 24px;font-size:13px}
.verdict{border-left:4px solid var(--bamboo);background:var(--bamboo-wash);color:var(--bamboo-ink);border-radius:0 12px 12px 0;padding:18px 24px;margin:18px 0}
.verdict h2{font:500 21px/1.55 var(--serif);margin:0 0 6px}.verdict p{margin:0;font-size:13px}
.layer{font-size:11px;letter-spacing:.2em;color:var(--muted);font-weight:600;margin:34px 0 12px;display:flex;gap:10px;align-items:center}
.layer:after{content:"";flex:1;height:1px;background:var(--line)}
.nums{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.num,.dim,.step,details{background:var(--surface);border:1px solid var(--line);border-radius:12px}
.num{padding:16px 18px}.num small{display:block;color:var(--muted);font-size:11px;letter-spacing:.08em}.num b{display:block;font:500 24px var(--serif);margin:4px 0}
.num p{margin:0;font-size:12.5px;color:var(--ink-2)}
.say{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.say div{border-radius:10px;padding:14px 18px}
.can{background:var(--bamboo-wash);color:var(--bamboo-ink)}.cannot{background:var(--slate-wash);color:var(--slate-ink)}
.say h3{margin:0 0 4px;font-size:13px}.say ul{margin:0;padding-left:18px}
.dim{padding:14px 20px;margin-bottom:8px}.dim h3{font:500 16px var(--serif);margin:0}.dim .tag{font-size:11px;color:var(--muted)}
.dim p{margin:6px 0 4px;color:var(--ink-2)}.dim ul{margin:6px 0 0;padding-left:18px;font-size:12.5px;color:var(--ink-2)}
.dim code{font:11.5px Consolas,monospace;color:var(--muted)}
.chain{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}.step{padding:14px 16px}
.step b{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px}
.step h3{margin:8px 0 4px;font-size:14px}.step p{margin:0;font-size:12.5px;color:var(--ink-2)}.proof{display:inline-block;margin-top:6px;font-size:11px;background:var(--bamboo-wash);color:var(--bamboo-ink);border-radius:999px;padding:2px 9px}
details{padding:12px 18px;margin-top:10px}summary{cursor:pointer}dl{display:grid;grid-template-columns:190px 1fr;gap:6px 16px;font-size:13px}dt{font-weight:600}dd{margin:0;color:var(--ink-2)}
.how{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 20px;font-size:13px;color:var(--ink-2)}
footer{margin-top:30px;color:var(--muted);font-size:12px}
@media print{body{background:#fff}.num,.dim,.step,details{break-inside:avoid}}
"""


def render_html(guide):
    """A self-contained page (no scripts, no network) that reads well on screen and on paper."""
    e = html.escape
    parts = [f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>证据说明书 · {e(guide['taskId'] or '')}</title>",
             f"<style>{_CSS}</style></head><body><main>",
             "<h1>证据说明书</h1>",
             f"<p class='sub'>研究问题：{e(guide['problem']['prompt'])}<br>任务 {e(guide['taskId'] or '')} · 本说明书由证据自动生成，本身不是证据。</p>",
             f"<section class='verdict'><h2>{e(guide['headline'])}</h2><p>{e(guide['subline'])}</p></section>",
             "<div class='layer'>第一层 · 一页看懂</div><div class='nums'>"]
    for n in guide["numbers"]:
        parts.append(f"<div class='num'><small>{e(n['label'])}</small><b>{e(n['value'])}</b><p>{e(n['text'])}</p></div>")
    parts.append("</div><div class='say'><div class='can'><h3>可以这样说</h3><ul>")
    parts += [f"<li>{e(x)}</li>" for x in guide["can"]] or ["<li>—</li>"]
    parts.append("</ul></div><div class='cannot'><h3>不能这样说</h3><ul>")
    parts += [f"<li>{e(x)}</li>" for x in guide["cannot"]]
    parts.append("</ul></div></div><div class='layer'>第二层 · 用数学语言看六项检查</div>")
    for d in guide["dimensions"]:
        parts.append(f"<section class='dim'><h3>{e(d['name'])} <span class='tag'>{e(d['short'])} · {e(d['status'])}</span></h3>"
                     f"<p>{e(d['text'])}</p><ul>")
        for c in d["checks"]:
            parts.append(f"<li>{e(c['plain'])}：{e(c['status'])} <code>{e(c['id'])}</code><br><code>{e(c['reason'])}</code></li>")
        parts.append("</ul></section>")
    parts.append("<div class='layer'>第三层 · 凭什么说这是证据</div><div class='chain'>")
    for i, s in enumerate(guide["chain"], 1):
        parts.append(f"<div class='step'><b>{i}</b><h3>{e(s['title'])}</h3><p>{e(s['text'])}</p><span class='proof'>{e(s['proof'])}</span></div>")
    parts.append("</div><div class='layer'>自己核对</div><p class='how'>不必逐个阅读文件。在 Leo AI 的「证据」页点「一键重新核对」，"
                 "会逐项重算指纹并复核结论；没有 Leo AI 时，可按证据包里 REPRODUCE.md 的步骤，用任意 Python 验证证据，"
                 "或在独立环境中重新计算。</p>")
    parts.append("<details open><summary>术语表</summary><dl>")
    parts += [f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in guide["glossary"]]
    parts.append("</dl></details><details><summary>证据地图：每个文件是什么</summary><dl>")
    parts += [f"<dt><code>{e(f)}</code></dt><dd>{e(w)}</dd>" for f, w in guide["map"]]
    parts.append("</dl></details><footer>Leo AI · 数字均取自本次运行的记录；结论等级以机器判定为准，人的解释不能提升它。</footer></main></body></html>")
    return "".join(parts)


_SAFE = re.compile(r"^research-[0-9a-f]{32}$")


def write_guide(task_dir, guide):
    """Place the guide in the task folder so the export carries it inside the hashed package."""
    task_dir = Path(task_dir)
    if not _SAFE.fullmatch(task_dir.name):
        raise ValueError("TASK_ID_INVALID")
    target = task_dir / "证据说明书.html"
    target.write_text(render_html(guide), encoding="utf-8")
    return target
