# PINN 可信闭环 · R2 分工与提示词（2026-09-15）

队长：Claude。队员：DeepSeek、GLM、Kimi、豆包（Grok 车道已撤销，其 Red Team 交付物由队长维护）。用户在各自对话里粘贴下面的提示词，把输出原样交回队长合并。R2 的目的不是重新设计，而是把 A-0001 第 2 稿里队长已经落成机器规则的五项修订**审核、补全、落到可执行的协议与测试**，让修正案能够进入 ACCEPTED。

## 0. 队长规则（与 R1 相同）

1. 交付物两两不重叠；文件名固定；别人的层不许重写，只能在"给其他队员的接口建议"里提需求。
2. 术语沿用既有词表与 A-0001 第 2 稿；新术语先定义。
3. 队员看不到仓库，不猜路径、不写补丁；只交设计、公式、伪代码、检查表、测试用例、模板。
4. 不确定写"待队长决定"，不要默默假设。
5. 裁决权在队长；交付物原样存入 `docs/pinn-trust-loop/inbox/`，合并记入 `R2_MERGE_NOTES.md`。
6. 构建、部署、git、测试运行只由队长在本机做。

## 1. 分工表

| 队员 | 交付物 | 核心任务 |
|---|---|---|
| DeepSeek | `PINN_TRUST_R2_MATH_CORE.md` | 症状 × 根因可接受矩阵的逐格区分实验与判定；seed 阈值的统计论证；自适应泄漏规则的信息流形式化；物理检查的 Applicability 表 |
| GLM | `PINN_TRUST_R2_SCHEMAS_STATE_MACHINE.md` | 审核队长的 1.1 契约；补 DiagnosisRecord、ClaimSetEvent、RunRecord（环境身份定义）契约；状态机第 2 版转移表；T29–T60 对抗性测试用例 |
| Kimi | `PINN_TRUST_R2_IMPL_TRAINING.md` | D_train / D_dev / D_claim 的操作协议；seed 协议第 2 版；物理检查的实现级清单；C3 合格 run 登记清单 |
| 豆包 | `PINN_TRUST_R2_REPORT_AND_WORKFLOW.md` | 报告模板第 3 稿（NOT_APPLICABLE、两层诊断、评估集与 C3 独立性披露）；研究者工作流第 2 版；术语表更新 |
| Claude（队长） | 合并、A-0001 第 3 稿、代码与测试 | — |

---

## 2. 提示词一：DeepSeek（数学核心 R2）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"数学核心"队员，本轮是 R2。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手。其中的 PINN（物理信息神经网络）科研治理有《Leo AI PINN 闭环科研宪法》与《PINN 闭环科研 MVP 计划》。R1（2026-09-14）五份交付物已合并为宪法修正案 A-0001 第 2 稿（PROPOSED），配套代码与 122 项测试已落地。你在 R1 交付的数学一致性条件、物理检查公式、归因决策表与弱链演算已被采纳。
- 既有词表（必须沿用）：证据等级 Level A/B/C/D；Gate 状态 PASS / FAIL / BLOCKED / PARTIAL（PARTIAL ≠ PASS，不推进）；七道 Gate G1 规格与数学一致性、G2 参考解、G3 实现正确性、G4 训练、G5 验证（G5a 物理一致性 + G5b 独立数值验证）、G6 复现性、G7 声明；状态机 DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION → REPRODUCIBILITY_CHECK → ACCEPTED，FAIL → FAILURE_RECORDED → DIAGNOSED → REVISED → 回上游 Gate，横切 STOPPED_THE_LINE；Claim 等级 C0/C1/C2/C3。
- 队长已落成的机器规则（A-0001 第 2 稿，请在此基础上工作，不要重新发明）：
  · 可信度向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，维度状态 TrustStatus = {PASS, PARTIAL, FAIL, BLOCKED, NOT_CHECKED}，报告序 FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS，组合只有取最弱；C0 需 math、impl；C1 加 train；C2/C3 需六维全 PASS 且证据等级 ≠ D；EXPLORATORY 封顶 C1。
  · 检查级别有独立类型 Applicability = {APPLICABLE, NOT_APPLICABLE}；CheckResult{checkId, applicability, status?, reason, evidence}；NOT_APPLICABLE 无 status、必须写理由、不进入 meet；维度状态 = 全部 APPLICABLE 检查的 meet，没有 APPLICABLE 检查时为 NOT_CHECKED。
  · 两层诊断：FailureSignature = {sPdeResidual, sBcResidual, sConservation, sPinnCfd, sSeedSensitive, sLocalizedError} 只是证据；RootCauseClass = {rSpecDefect, rDataDefect, rSingularityTreatment → G1; rReferenceDefect → G2; rImplementationDefect → G3; rCapacityLimit, rOptimizationFailure, rSamplingDeficiency → G4; rUndetermined → STOPPED_THE_LINE}。可接受矩阵：sPdeResidual→{规格, 实现, 容量, 优化, 采样}；sBcResidual→{规格, 数据, 实现, 优化, 采样}；sConservation→{规格, 实现, 容量, 优化, 采样}；sPinnCfd→{规格, 数据, 奇异性, 参考解, 实现, 优化}；sSeedSensitive→{容量, 优化, 采样}；sLocalizedError→{奇异性, 参考解, 实现, 容量, 优化, 采样}。诊断必须附区分实验（discriminatingExperiment）。
  · 评估集三分：D_train 训练；D_dev 诊断 / 调参 / 模型选择 / 早停 / 扰动实验；D_claim 预注册密封，只在本版本最终验证时打开，打开过的哈希在后续版本禁用；C_external 只在 D_claim 上可 PASS。
  · seed 协议：N ≥ 10（1D），2D 过渡 N = 5 封顶 PARTIAL，N < 5 BLOCKED；k/N < 0.8 FAIL，0.8 ≤ k/N < 0.9 PARTIAL，≥ 0.9 PASS；最差 seed > 3ε 或 IQR/median > 1 封顶 PARTIAL；中位数 > ε FAIL。
  · C3：≥ 5 个 independently qualified 的 SUPPORTED @ C2 run——同 specHash、同代码哈希、seed 集两两不同、执行环境至少 2 个不同。
  · Red Team 扰动 P1–P21 分三层（Tier-0 任何 claim 前，Tier-1 C2 前，Tier-2 C3 前）。
- 协作规则：只做本提示词指定的交付物；需要别的层配合的写进"给其他队员的接口建议"；术语按词表；不确定写进"待队长决定"；你看不到仓库，不要猜路径或代码细节，不要输出改仓库的补丁；引用文献必须可核对（作者、年份、题目、出处），不确定就不写；输出中文 Markdown；交付物由队长合并，裁决权在队长。

【你的交付物】一份文件，文件名固定为 PINN_TRUST_R2_MATH_CORE.md，第一行写"# PINN_TRUST_R2_MATH_CORE · 作者：DeepSeek · R2 · 日期"。章节固定：
1. 可接受矩阵逐格审核与区分实验：对上面六个症状 × 各自可接受根因的每一格，给出（a）该根因成立时的预期症状形态，（b）把它与同一症状下其它根因区分开的实验（引用 P1–P21 的编号，或定义新实验并编号 P22 起），（c）判定规则（数值化）。指出矩阵里你认为应增删的格并说明理由。
2. seed 阈值的统计论证：在 N = 10、k ≥ 9 与 N = 5 两种情形下，对"真实成功概率 p"给出置信区间或似然比说明；论证 0.9 / 0.8 两条线是否合理，2D 过渡期 N = 5 为什么只能 PARTIAL；给出"若算力允许，N 取多少可以把 PASS 线的错误接受率压到多少"的表。
3. 自适应泄漏规则的形式化：把"看过 D_claim 即失盲"写成一个信息流不变量（哪些决策不得以 D_claim 为条件；哪些操作构成"打开"；打开后为什么必须换集而不是只加密封）；给出可判定的检查项。
4. 物理检查的 Applicability 表：对 Poisson 1D、二维稳态不可压 NS、Oldroyd-B 型粘弹流三类问题，逐项（质量守恒 / 通量平衡、能量平衡、动量收支、正定性、对称性、单调性、最大值原理、自由能 / 熵条件、SPD）给出 APPLICABLE 或 NOT_APPLICABLE，NOT_APPLICABLE 的一句理由必须能直接填进 CheckResult.reason。
5. 给队长的说明：假设、待队长决定、给其他队员的接口建议。

【不做】不设计 schema 字段、不写状态机转移表、不写操作协议、不写报告文案。
【篇幅】3000–6000 字。每条判定规则要能被程序实现。
```

---

## 3. 提示词二：GLM（数据契约与状态机 R2）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"数据契约与状态机"队员，本轮是 R2。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手。其中的 PINN 科研治理有《Leo AI PINN 闭环科研宪法》与《PINN 闭环科研 MVP 计划》。R1（2026-09-14）你交付的三份 schema、状态机扩展与 T01–T28 已被采纳并改写为仓库自带校验器支持的关键字子集（它只支持 type / required / properties / additionalProperties / items / minItems / maxItems / uniqueItems / enum / const / pattern / minLength / minimum / maximum / anyOf / allOf / $ref / $defs；if/then、contains、prefixItems、exclusiveMinimum、format、not 一律改由 Python 交叉校验）。未采纳：新增 PHYSICS_CHECKED 状态（G5 拆成 G5a/G5b 但都在 VALIDATION 内执行）、weakestLink 排序改为 FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS、BLOCKED 的 Gate 结果不进 FAILURE_RECORDED（状态不变）。
- 既有词表：证据等级 A/B/C/D；Gate 状态 PASS / FAIL / BLOCKED / PARTIAL；七道 Gate G1–G7（G5 = G5a 物理一致性 + G5b 独立数值验证）；状态机 DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION → REPRODUCIBILITY_CHECK → ACCEPTED，FAIL → FAILURE_RECORDED → DIAGNOSED → REVISED，横切 STOPPED_THE_LINE；Claim 等级 C0–C3。
- 队长已落成的 1.1 契约（在此基础上工作）：
  · ProblemDefinition 1.1：新增 revision（整数 ≥ 1）与 evaluationSets{train, dev, claim（三个 artifactRef，哈希两两不同）, claimSetStatus ∈ {SEALED, OPENED}, claimSetOpenedAtRevision（OPENED 时必填且 = revision）, claimSetHistory[{sha256, openedAtRevision}]}；规则：打开过的 claim 集哈希在更高 revision 禁用；specHash 用仓库既有的规范化序列化。
  · TrustVector 1.1：每维 {status, evidencePointers, judgedAt, judgedBy, notes, perturbationsRun, worstCase, evaluationSet ∈ {dev, claim}, checks[CheckResult]}；CheckResult{checkId, applicability ∈ {APPLICABLE, NOT_APPLICABLE}, status?（仅 APPLICABLE）, reason（NOT_APPLICABLE 必填）, evidencePointers}；维度 status 必须等于 APPLICABLE 检查的 meet（无 APPLICABLE → NOT_CHECKED）；external 只有 evaluationSet = claim 才能 PASS。
  · ClaimGateDecision 1.1：新增 codeHash；supportedC2Runs 整数改为 qualifiedC2Runs[{runId, specHash, codeHash, environmentId, seedSetId}]；校验器按"同 specHash、同 codeHash、seed 集互异、≥ 2 个环境、≥ 5 个"重算 C3 资格；allowedClaims 只能比演算更严；weakestLink 由向量推导（dimensions 列出全部并列维度）。
  · 状态机：FailureSignature（六症状）→ RootCauseClass（九类，含 rUndetermined → STOPPED_THE_LINE）→ Gate；可接受矩阵封闭；诊断必须附症状证据与 discriminatingExperiment；重入 Gate k 后 k 及下游维度重置 NOT_CHECKED；同一规格诊断最多 3 轮。
- 评审意见（用户，2026-09-14）要求在生效前封死：症状不得直接路由；NOT_APPLICABLE 不是状态；D_claim 的盲态；seed 阈值 0.9/0.8；C3 独立性。上述契约是队长对这五项的第一版实现，你的任务是审核与补全。
- 协作规则：同 R1（只做本交付物；接口建议单列；不猜仓库；不输出补丁；中文 Markdown；裁决权在队长）。

【你的交付物】文件名固定 PINN_TRUST_R2_SCHEMAS_STATE_MACHINE.md，第一行"# PINN_TRUST_R2_SCHEMAS_STATE_MACHINE · 作者：GLM · R2 · 日期"。章节固定：
1. 对队长 1.1 契约的审核：逐字段指出漏洞（能被绕过的地方、缺失的约束、可被伪造的字段），每条给修订建议；只用上面列出的关键字子集写 schema 片段。
2. 补全三份新契约（字段表 + 子集 schema）：DiagnosisRecord{signature, rootCause, discriminatingExperiment, signatureEvidence, round, decidedBy, decidedAt}；ClaimSetEvent{problemId, revision, claimSetSha256, event ∈ {SEALED, OPENED}, actor, at}（append-only）；RunRecord（供 qualifiedC2Runs 引用）——重点定义 environmentId 的构成（操作系统、机器指纹、Python / 框架 / GPU 驱动版本、容器镜像…哪些字段进入身份哈希）与 codeHash 的构成（哪些文件参与）。
3. 状态机第 2 版转移表：把两层诊断、claim 集事件（SEALED → OPENED 只能发生在 VALIDATION 内且只能一次 / 版本）、rUndetermined 停线、3 轮上限写成 当前状态 / 触发 / 目标 / 必须证据 / 不变量 的表，加伪代码。
4. 测试用例 T29–T60：至少 32 条，其中对抗性用例不少于 12 条：同一 seed 集改名冒充新 run、environmentId 伪造、claim 集在不升 revision 的情况下重开、用 NOT_APPLICABLE 隐藏一条本应 APPLICABLE 且 FAIL 的检查、症状证据齐全但缺 discriminatingExperiment、根因不在可接受矩阵内、external 在 dev 上声明 PASS、claimSetHistory 与 status 不一致、weakestLink 少列并列维度、qualifiedC2Runs 混入其它 codeHash 的 run。
5. 给队长的说明：假设、待队长决定、给其他队员的接口建议。

【不做】不做数学推导、不写操作协议、不写报告文案。
【篇幅】3500–7000 字。
```

---

## 4. 提示词三：Kimi（实现与训练协议 R2）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"实现验证与训练协议"队员，本轮是 R2。队长是 Claude；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手。其中的 PINN 科研治理有《Leo AI PINN 闭环科研宪法》与《PINN 闭环科研 MVP 计划》。R1（2026-09-14）你交付的 MMS 协议、T1–T10 单元测试、多 seed 协议已被采纳并写入修正案 A-0001；用户评审后把 seed 判定改为 k/N < 0.8 FAIL、0.8 ≤ k/N < 0.9 PARTIAL、≥ 0.9 PASS（最差 seed 与 IQR 仍封顶 PARTIAL；N ≥ 10；2D 过渡 N = 5 封顶 PARTIAL；N < 5 BLOCKED），并新增三条治理规则：评估集三分 D_train / D_dev / D_claim；检查级别的 Applicability（NOT_APPLICABLE 不是状态）；C3 需 ≥ 5 个 independently qualified C2 run（同 specHash、同代码哈希、seed 集互异、≥ 2 个执行环境）。
- 既有词表：证据等级 A/B/C/D；Gate 状态 PASS / FAIL / BLOCKED / PARTIAL；G1–G7（G5 = G5a 物理一致性 + G5b 独立数值验证）；可信度向量 (C_math, C_impl, C_train, C_physics, C_external, C_repro)，维度状态 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；两层诊断 FailureSignature → RootCauseClass → Gate；Red Team 扰动 P1–P21 三层制。
- 评估集规则（队长已落成）：三集哈希两两不同；D_dev 用于诊断、调参、模型 / 架构选择、早停、扰动实验；D_claim 预注册后 SEALED，只在本版本最终验证时 OPENED 并记录版本号；打开过的哈希在更高 revision 禁用；C_external 只在 D_claim 上可 PASS，在 D_dev 上最多 PARTIAL；训练配点、边界点、评估集两两互斥（宪法级）。
- 协作规则：同 R1（只做本交付物；接口建议单列；不猜仓库；不输出补丁；文献必须可核对；中文 Markdown；裁决权在队长）。

【你的交付物】文件名固定 PINN_TRUST_R2_IMPL_TRAINING.md，第一行"# PINN_TRUST_R2_IMPL_TRAINING · 作者：Kimi · R2 · 日期"。章节固定：
1. D_train / D_dev / D_claim 操作协议：三集如何生成（分布、点数建议、与训练配点互斥的机械保证）、如何哈希与登记、谁持有 D_claim 的密封、什么操作算"打开"、打开后的记录、发现需要再改实现时的处置（升 revision、重新预注册新 claim 集、旧集标 burnt）、日志最小字段。
2. seed 协议第 2 版：按新阈值重写判定流程；三因子解耦（初始化 / 采样 / batch 顺序）的具体登记方式；k 的定义（哪个误差、哪个集、哪个阈值）；N 的取法与算力折中；禁止事项清单。
3. 物理检查的实现级清单：对 Poisson 1D 的每项 APPLICABLE 检查（通量平衡、能量恒等式、正定性、对称性、单调性、最大值原理、SPD）给出计算步骤、需要保存的证据（数值、节点集、哈希）、通过阈值；对二维 NS 给出质量守恒、能量收支、动量收支的实现步骤；NOT_APPLICABLE 项如何登记理由。
4. C3 合格 run 登记清单：什么使两个执行环境"不同"（列出必须不同的字段与可以相同的字段）；代码身份哈希覆盖哪些文件；seed 集的登记与去重；一份 run 登记表模板。
5. 文献支撑（仅新增内容需要，可核对出处）。
6. 给队长的说明：假设、待队长决定、给其他队员的接口建议。

【不做】不设计 schema、不写状态机、不写报告模板、不做数学推导。
【篇幅】3000–6000 字。检查表用表格。
```

---

## 5. 提示词四：豆包（报告模板与研究者工作流 R2）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"报告模板与研究者工作流"队员，本轮是 R2。队长是 Claude；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手。其中的 PINN 科研治理有《Leo AI PINN 闭环科研宪法》与《PINN 闭环科研 MVP 计划》。R1（2026-09-14）你交付的六段式模板、措辞规则、两个示例与研究者工作流已被采纳；用户裁决示例 (b) 采 (ii)：C1 + 受限一致陈述，不开 scoped C2。队长已把模板扩为八段（加 Provenance 与 Scope）。
- 用户评审后新增的规则（你需要把它们写进报告与工作流）：
  · 两层诊断：FailureSignature（症状：sPdeResidual、sBcResidual、sConservation、sPinnCfd、sSeedSensitive、sLocalizedError）→ RootCauseClass（根因：规格缺陷、数据缺陷、奇异性处理、参考解缺陷、实现缺陷、容量不足、优化失败、采样不足、未能判定）→ 回到的 Gate；诊断必须写明区分实验；未能判定就停线交人。
  · 检查级别的 Applicability：NOT_APPLICABLE（不承担）与 NOT_CHECKED（没查）、BLOCKED（不能查）、PARTIAL（查了不充分）四者措辞必须区分；NOT_APPLICABLE 不计入维度。
  · 评估集三分：D_train / D_dev / D_claim；报告必须披露 C_external 是在 dev 还是 claim 集上评估、claim 集状态（SEALED / OPENED@版本）；只有 claim 集上的一致性能让 C_external PASS。
  · seed 判定：k/N < 0.8 FAIL、0.8–0.9 PARTIAL、≥ 0.9 PASS，仍报最差 seed；2D 过渡 N = 5 封顶 PARTIAL。
  · C3：≥ 5 个 independently qualified C2 run（同规格、同代码、seed 集互异、≥ 2 个环境）；报告必须披露 run 数、seed 集数、环境数。
- 既有词表：Gate 状态 PASS / FAIL / BLOCKED / PARTIAL；维度状态另加 NOT_CHECKED；Claim 等级 C0–C3；弱链原则；禁止单一百分比。
- 协作规则：同 R1（只做本交付物；不设计任何界面 / 配色 / 组件；不做数学、schema、协议；不猜仓库；中文 Markdown；裁决权在队长）。

【你的交付物】文件名固定 PINN_TRUST_R2_REPORT_AND_WORKFLOW.md，第一行"# PINN_TRUST_R2_REPORT_AND_WORKFLOW · 作者：豆包 · R2 · 日期"。章节固定：
1. 报告模板第 3 稿（在八段基础上）：Evidence 段里 CheckResult 的逐条写法（含 NOT_APPLICABLE 的标准句）；Known failure modes 段里"症状 → 根因 → 区分实验 → 回到的 Gate → 缓解状态 → 压住的维度"的固定句式，以及"未能判定，已停线"的句式；抬头里评估集披露行；Allowed claims 里 C3 的独立性披露句式；中英双语。
2. 示例 (b) 第 2 版：按裁决 (ii) 与新规则重写 backward-facing step 示例，给出诊断条目（假设角点敏感性的区分实验是 P12）与评估集披露。
3. 研究者工作流第 2 版："我看了 claim 集之后怎么办"的处置流程（升 revision、重新预注册、旧集 burnt 的告知）；失败实验如何写入论文附录（症状与根因分开写）；EXPLORATORY 结果的标注。
4. 术语中英对照表更新：新增 FailureSignature、RootCauseClass、Applicability、NOT_APPLICABLE、D_train / D_dev / D_claim、SEALED / OPENED、burnt claim set、independently qualified run、environmentId、codeHash 等。
5. 给队长的说明：假设、待队长决定、给其他队员的接口建议。

【不做】不设计界面；不做数学、schema、协议。
【篇幅】2500–5000 字。准确优先于华丽。
```

---

## 6. 回传与合并流程

1. 用户把每位队员的输出原样交给队长；队长存入 `docs/pinn-trust-loop/inbox/<文件名>`，首行保留作者与日期。
2. 队长审读并记入 `docs/pinn-trust-loop/R2_MERGE_NOTES.md`；分歧不抹平。
3. 合并产物：A-0001 第 3 稿（含 DiagnosisRecord / ClaimSetEvent / RunRecord 契约与状态机第 2 版）、代码与测试、协议汇编第 3 稿、报告模板第 3 稿；每一步写进操作日志。
4. 第 3 稿提交用户复审；用户裁决 ACCEPTED 后队长更新宪法正文到 1.1。
