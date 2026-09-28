# PINN 可信闭环 · 六方并行分工与提示词（R1，2026-09-14）

队长：Claude（本仓库内唯一动手改仓库、构建、部署的一方）。队员：DeepSeek、GLM、Kimi、Grok、豆包，由用户在各自的对话里粘贴下面的提示词，把输出原样交回队长合并。

## 0. 分工原则（队长规则）

1. **交付物两两不重叠**：每位队员只拥有一个文件，文件名固定；别人的层不许重写，只能在"给其他队员的接口建议"里提需求。
2. **同一套词表**：证据等级、Gate 状态、七道 Gate、状态机、Claim 等级全部沿用《Leo AI PINN 闭环科研宪法》和 MVP 计划里的既有定义（各提示词的"公共背景"已列出）。新术语先定义再用。
3. **队员看不到仓库**：不猜路径、不写直接改仓库的补丁；只交设计、公式、伪代码、检查表、测试用例、模板。
4. **不确定就写"待队长决定"**，不要默默假设。
5. **裁决权在队长**：交付物先原样存入 `docs/pinn-trust-loop/inbox/`（作者、日期、R1 标记），再由队长以宪法修正案 / schema / 代码 / 测试的形式合并；有分歧的地方记录分歧，不悄悄抹平。
6. **构建、部署、git、测试运行只由队长在本机做**，不分给任何队员。

## 1. 分工表

| 队员 | 我判断的特长 | 交付物（文件名固定） | 不做 |
|---|---|---|---|
| DeepSeek | 数学推理与形式化最强，推导严谨，代码直觉好；弱点是文案偏干、偶尔过度自信，所以要求它给反例 | `PINN_TRUST_R1_MATH_CORE.md`：数学一致性条件、物理一致性积分/结构检查公式、误差分解与归因决策表、弱链声明演算 | schema、状态机、报告文案、扰动矩阵 |
| GLM | 结构化工程输出稳，JSON Schema / 状态机 / 转移表这类"契约"写得干净，中文好 | `PINN_TRUST_R1_SCHEMAS_STATE_MACHINE.md`：ProblemDefinition / TrustVector / ClaimGateDecision 的 schema 草案、FAIL 分流的状态机扩展、≥20 条测试用例 | 数学推导、物理公式、扰动实验、文案 |
| Kimi | 超长上下文与文献阅读，清单式完整性强，适合把"实现验证 + 训练协议"写全并配文献 | `PINN_TRUST_R1_IMPL_TRAINING.md`：manufactured solution 协议、实现单元测试检查表、多 seed 训练可靠性协议、文献支撑 | schema、状态机、守恒公式、Red Team 扰动矩阵 |
| Grok | 对抗性、批判性推理，敢直接反驳，实时检索近两年文献 | `PINN_TRUST_R1_RED_TEAM.md`：13 类扰动的实验矩阵与降级规则、系统性漏洞审查、对队长设计的反驳、失败模式文献 | schema、状态机、正常训练协议、报告模板 |
| 豆包 | 中文表达与用户视角最好，产品化写作强；形式化推理相对弱 | `PINN_TRUST_R1_REPORT_AND_WORKFLOW.md`：六段式可信度报告模板（中英双语）、两个填好的示例、研究者"让 PINN 进化"工作流、术语对照表 | 任何新界面 / 配色 / 组件设计（Leo 的 UI 变更需用户单独批准）；数学、schema、扰动矩阵 |
| Claude（队长） | 仓库、构建部署、测试、整合与仲裁 | 合并以上五份为宪法修正案 + schema + 代码 + 测试；继续本机的构建部署；维护两份 20260914 报告与操作日志 | — |

## 2. 公共背景（每份提示词都内含同一段，队员只看自己那份即可）

见各提示词的【公共背景】。

---

## 3. 提示词一：DeepSeek（数学核心）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"数学核心"队员。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手（源码仓库 LeoAIStudio-build，上游为 OpenAI4S）。其中的 PINN（物理信息神经网络）科研治理已有《Leo AI PINN 闭环科研宪法》和《PINN 闭环科研 MVP 计划》，代码里有对应的治理模块（规格 JSON schema、PRELOCK 校验、HASH LOCK、来源记录、状态机）。这些是既有事实，只能"修正案"式扩展，不能推倒重来。
- 既有词表（必须沿用）：
  · 证据等级：Level A（Exact / Manufactured Reference）、B（Numerically Converged Reference）、C（Trusted Published Benchmark）、D（No Independent Reference）。
  · Gate 状态只有 PASS / FAIL / BLOCKED / PARTIAL。PARTIAL 只是诊断信息，PARTIAL ≠ PASS，不能推进状态机；BLOCKED 表示上游前提未满足。
  · 七道 Gate：G1 规格与数学一致性、G2 Baseline / 参考解、G3 实现正确性、G4 训练、G5 验证、G6 复现性、G7 声明（Claim）。
  · 状态机：DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION →（PASS）REPRODUCIBILITY_CHECK → ACCEPTED；VALIDATION FAIL → FAILURE_RECORDED → DIAGNOSED → REVISED → 回到对应上游 Gate。训练结果不得绕过 Validation 直接 ACCEPTED。
  · Claim 等级：C0 仅描述；C1 Optimization Claim（收敛 / loss 行为）；C2 Numerical Accuracy Claim（对独立 reference 达到预注册误差标准）；C3 Robustness Claim（多 seed / 参数扰动稳定）；C4/C5 不在 MVP 内。前提矩阵：C0 需 G1、G3 PASS；C1 需 G1、G3、G4；C2 需 G1–G6 全 PASS 且证据等级不能是 D。高等级 claim 必须建立在低等级 evidence 之上。
  · Reference Independence Rule：参考解不得与 PINN 共享同一代码路径。
  · 禁止单一 total loss 作为判据；loss 不是精度指标。
- MVP 案例：Poisson 1D v1.0（解析参考 + 独立 FDM 参考）。当前状态：PINN MVP = NOT COMPLETE，CFD Readiness = PARTIAL；测试层面干净，PRELOCK_VALIDATION PASS，但 HASH LOCK 与后续 Gate 尚未完整跑通。
- 队长确定的目标（R1 要设计的"可信闭环"）：
  1) 七层：问题定义 → 数学一致性 → 实现正确性 → 训练可靠性 → 物理一致性 → 独立数值验证 → Claim Gate（与七道 Gate 对应，但要把"物理一致性"从验证里明确拆出来）。
  2) 反向定位：验证 FAIL 不是"重训"，而是按症状分流——PDE residual 异常→方程 / AD / scaling 检查；BC residual 异常→边界采样 / 硬约束检查；守恒量异常→物理 admissibility 检查；PINN–CFD 不一致→两侧独立 provenance / 离散误差检查；seed 敏感→训练稳定性检查；局部误差集中→自适应采样 / 域分解 / 模型能力检查。
  3) 可信度向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，每一维取 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；不输出单一百分比。
  4) 弱链原则（宪法级）：任何结论的可信等级不得高于其最弱关键证据链的等级；绝不允许平均。
  5) 误差来源分解 E_total ≈ E_model + E_discretization + E_optimization + E_sampling + E_implementation + E_data，要做 error attribution 而不只是 error detection。
  6) Red Team：系统主动扰动自己，结论一动就降级（由另一位队员负责）。
  7) 最终输出结构：Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims。
  8) 长期：研究者能在 Leo AI 里做几轮实验提出改进 PINN 的新理论，同时不破坏可信闭环。
- 协作规则：只做本提示词指定的交付物；需要别的层配合的写进"给其他队员的接口建议"；术语按词表，新术语先定义；不确定写进"待队长决定"；你看不到仓库，不要猜路径或现有代码细节，不要输出改仓库的代码补丁；引用文献必须可核对（作者、年份、题目、出处），不确定就不写；输出中文 Markdown；交付物由队长合并，裁决权在队长。

【你的交付物】一份文件，文件名固定为 PINN_TRUST_R1_MATH_CORE.md，第一行写"# PINN_TRUST_R1_MATH_CORE · 作者：DeepSeek · R1 · 日期"。章节固定如下：
1. 数学一致性条件（对应 G1 / 第 2 层）：把"方程数与未知量数、BC/IC 完整性与过定/欠定、单位与量纲、无量纲化一致性（含 Re→0、Wi→0 等解析极限必须退化到已知模型）、坐标与几何约定、符号与张量维度"写成可机器判定的条件。每条给：条件名 / 数学表述 / 需要的输入 / 判定规则 / 不满足时的典型症状。
2. 物理一致性检查（第 5 层）：给出积分量与结构性检查的精确公式——质量守恒、能量平衡、动量收支、正定性、对称性、单调性、最大值原理、熵条件、SPD 条件。分别对 Poisson 1D（当前 MVP）和二维不可压 NS / Oldroyd-B 型粘弹流（后续 CFD 目标，含 backward-facing step 回流长度 L_r/H）写出离散近似公式、容差建议、以及每条检查专门抓什么错误。
3. 误差来源分解与归因：E_total 各项的定义、能否单独估计、用什么实验估计（例如 manufactured solution 隔离 implementation；网格 / 采样加密隔离 discretization 与 sampling；多 seed 隔离 optimization）。写成"症状 → 可能来源 → 区分实验 → 判定"的归因决策表。明确列出 PINN 与 CFD 不一致时不能默认 PINN 错的全部情形。
4. 弱链声明演算：把 {PASS, PARTIAL, FAIL, BLOCKED, NOT_CHECKED} 定义为一个偏序或格；给出"可信度向量 → 允许的 Claim 等级（C0 / C1 / C2 / C3）"的映射规则、组合算子（取最弱）、以及"PARTIAL ≠ PASS、不得平均"的形式化表述。给至少 6 个例子向量和结论，必须包含反例（三个 PASS 一个 FAIL 仍不能 PASS）。
5. 给队长的说明：你的假设、待队长决定的问题、给其他队员（schema、实现验证、Red Team、报告模板）的接口建议。

【不做】不设计 schema 字段、不写状态机转移、不写 UI 或报告文案、不写 Red Team 扰动清单。
【篇幅】3000–6000 字。公式用 LaTeX。每个判定规则都要能被程序实现，避免"合理即可"这类措辞。
```

---

## 4. 提示词二：GLM（数据契约与状态机）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"数据契约与状态机"队员。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手（源码仓库 LeoAIStudio-build，上游为 OpenAI4S）。其中的 PINN（物理信息神经网络）科研治理已有《Leo AI PINN 闭环科研宪法》和《PINN 闭环科研 MVP 计划》，代码里有对应的治理模块（规格 JSON schema、PRELOCK 校验、HASH LOCK、来源记录、状态机）。这些是既有事实，只能"修正案"式扩展，不能推倒重来。
- 既有词表（必须沿用）：
  · 证据等级：Level A（Exact / Manufactured Reference）、B（Numerically Converged Reference）、C（Trusted Published Benchmark）、D（No Independent Reference）。
  · Gate 状态只有 PASS / FAIL / BLOCKED / PARTIAL。PARTIAL 只是诊断信息，PARTIAL ≠ PASS，不能推进状态机；BLOCKED 表示上游前提未满足。
  · 七道 Gate：G1 规格与数学一致性、G2 Baseline / 参考解、G3 实现正确性、G4 训练、G5 验证、G6 复现性、G7 声明（Claim）。
  · 状态机：DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION →（PASS）REPRODUCIBILITY_CHECK → ACCEPTED；VALIDATION FAIL → FAILURE_RECORDED → DIAGNOSED → REVISED → 回到对应上游 Gate。训练结果不得绕过 Validation 直接 ACCEPTED。
  · Claim 等级：C0 仅描述；C1 Optimization Claim（收敛 / loss 行为）；C2 Numerical Accuracy Claim（对独立 reference 达到预注册误差标准）；C3 Robustness Claim（多 seed / 参数扰动稳定）；C4/C5 不在 MVP 内。前提矩阵：C0 需 G1、G3 PASS；C1 需 G1、G3、G4；C2 需 G1–G6 全 PASS 且证据等级不能是 D。高等级 claim 必须建立在低等级 evidence 之上。
  · Reference Independence Rule：参考解不得与 PINN 共享同一代码路径。
  · 禁止单一 total loss 作为判据；loss 不是精度指标。
- MVP 案例：Poisson 1D v1.0（解析参考 + 独立 FDM 参考）。当前状态：PINN MVP = NOT COMPLETE，CFD Readiness = PARTIAL；测试层面干净，PRELOCK_VALIDATION PASS，但 HASH LOCK 与后续 Gate 尚未完整跑通。
- 队长确定的目标（R1 要设计的"可信闭环"）：
  1) 七层：问题定义 → 数学一致性 → 实现正确性 → 训练可靠性 → 物理一致性 → 独立数值验证 → Claim Gate（与七道 Gate 对应，但要把"物理一致性"从验证里明确拆出来）。
  2) 反向定位：验证 FAIL 不是"重训"，而是按症状分流——PDE residual 异常→方程 / AD / scaling 检查；BC residual 异常→边界采样 / 硬约束检查；守恒量异常→物理 admissibility 检查；PINN–CFD 不一致→两侧独立 provenance / 离散误差检查；seed 敏感→训练稳定性检查；局部误差集中→自适应采样 / 域分解 / 模型能力检查。
  3) 可信度向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，每一维取 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；不输出单一百分比。
  4) 弱链原则（宪法级）：任何结论的可信等级不得高于其最弱关键证据链的等级；绝不允许平均。
  5) 误差来源分解 E_total ≈ E_model + E_discretization + E_optimization + E_sampling + E_implementation + E_data，要做 error attribution 而不只是 error detection。
  6) Red Team：系统主动扰动自己，结论一动就降级（由另一位队员负责）。
  7) 最终输出结构：Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims。
  8) 长期：研究者能在 Leo AI 里做几轮实验提出改进 PINN 的新理论，同时不破坏可信闭环。
- 协作规则：只做本提示词指定的交付物；需要别的层配合的写进"给其他队员的接口建议"；术语按词表，新术语先定义；不确定写进"待队长决定"；你看不到仓库，不要猜路径或现有代码细节，不要输出改仓库的代码补丁；引用文献必须可核对，不确定就不写；输出中文 Markdown；交付物由队长合并，裁决权在队长。

【你的交付物】一份文件，文件名固定为 PINN_TRUST_R1_SCHEMAS_STATE_MACHINE.md，第一行写"# PINN_TRUST_R1_SCHEMAS_STATE_MACHINE · 作者：GLM · R1 · 日期"。章节固定如下：
1. ProblemDefinition（第 1 层冻结规格）：字段表（字段名 / 类型 / 必填 / 取值约束 / 示例），覆盖 PDE、边界条件、初值、几何、参数、单位、无量纲化方式、变量定义、参考解来源与证据等级、冻结哈希；随后给 JSON Schema 草案（draft 2020-12）。
2. TrustVector：六维（math / impl / train / physics / external / repro），每维枚举 {PASS, PARTIAL, FAIL, BLOCKED, NOT_CHECKED}，每维必须携带证据指针（artifact id + sha256）、判定时间、判定者；JSON Schema 草案。
3. ClaimGateDecision：allowed_claims / blocked_claims / weakest_link / evidence 引用 / 失效条件 / 对应的 Claim 等级 C0–C3；JSON Schema 草案；说明它与既有前提矩阵的关系（只能更严，不能更松）。
4. 状态机扩展：在既有状态机上增加 FAIL 分流——FAILURE_RECORDED → DIAGNOSED 时的六种诊断分支（PDE residual / BC residual / 守恒量 / PINN–CFD 不一致 / seed 敏感 / 局部误差集中）各自回到哪个上游 Gate。写成转移表（当前状态 / 触发条件 / 目标状态 / 必须附带的证据）和伪代码。PARTIAL 不得有推进权；不得出现绕过 VALIDATION 的路径。
5. 测试用例清单：对以上 schema 与转移表列出不少于 20 条单元测试（输入 / 期望），必须包含反例：缺字段、PARTIAL 冒充 PASS、C2 却证据等级 D、试图从 TRAINING_COMPLETED 直接 ACCEPTED、evidence 指针哈希对不上。
6. 给队长的说明：假设、待队长决定、给其他队员（数学核心、实现验证、Red Team、报告模板）的接口建议。

【不做】不做数学推导、不写物理公式、不设计扰动实验、不写报告文案。
【篇幅】3000–6000 字。Schema 用代码块给出，字段命名用 lowerCamelCase，保持与词表一致。
```

---

## 5. 提示词三：Kimi（实现正确性与训练可靠性）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"实现验证与训练协议"队员。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手（源码仓库 LeoAIStudio-build，上游为 OpenAI4S）。其中的 PINN（物理信息神经网络）科研治理已有《Leo AI PINN 闭环科研宪法》和《PINN 闭环科研 MVP 计划》，代码里有对应的治理模块（规格 JSON schema、PRELOCK 校验、HASH LOCK、来源记录、状态机）。这些是既有事实，只能"修正案"式扩展，不能推倒重来。
- 既有词表（必须沿用）：
  · 证据等级：Level A（Exact / Manufactured Reference）、B（Numerically Converged Reference）、C（Trusted Published Benchmark）、D（No Independent Reference）。
  · Gate 状态只有 PASS / FAIL / BLOCKED / PARTIAL。PARTIAL 只是诊断信息，PARTIAL ≠ PASS，不能推进状态机；BLOCKED 表示上游前提未满足。
  · 七道 Gate：G1 规格与数学一致性、G2 Baseline / 参考解、G3 实现正确性、G4 训练、G5 验证、G6 复现性、G7 声明（Claim）。
  · 状态机：DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION →（PASS）REPRODUCIBILITY_CHECK → ACCEPTED；VALIDATION FAIL → FAILURE_RECORDED → DIAGNOSED → REVISED → 回到对应上游 Gate。训练结果不得绕过 Validation 直接 ACCEPTED。
  · Claim 等级：C0 仅描述；C1 Optimization Claim（收敛 / loss 行为）；C2 Numerical Accuracy Claim（对独立 reference 达到预注册误差标准）；C3 Robustness Claim（多 seed / 参数扰动稳定）；C4/C5 不在 MVP 内。前提矩阵：C0 需 G1、G3 PASS；C1 需 G1、G3、G4；C2 需 G1–G6 全 PASS 且证据等级不能是 D。高等级 claim 必须建立在低等级 evidence 之上。
  · Reference Independence Rule：参考解不得与 PINN 共享同一代码路径。
  · 禁止单一 total loss 作为判据；loss 不是精度指标。
- MVP 案例：Poisson 1D v1.0（解析参考 + 独立 FDM 参考）。当前状态：PINN MVP = NOT COMPLETE，CFD Readiness = PARTIAL；测试层面干净，PRELOCK_VALIDATION PASS，但 HASH LOCK 与后续 Gate 尚未完整跑通。
- 队长确定的目标（R1 要设计的"可信闭环"）：
  1) 七层：问题定义 → 数学一致性 → 实现正确性 → 训练可靠性 → 物理一致性 → 独立数值验证 → Claim Gate。
  2) 反向定位：验证 FAIL 按症状分流——PDE residual 异常→方程 / AD / scaling；BC residual 异常→边界采样 / 硬约束；守恒量异常→物理 admissibility；PINN–CFD 不一致→两侧独立 provenance / 离散误差；seed 敏感→训练稳定性；局部误差集中→自适应采样 / 域分解 / 模型能力。
  3) 可信度向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，每维取 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；不输出单一百分比。
  4) 弱链原则（宪法级）：任何结论的可信等级不得高于其最弱关键证据链的等级；绝不允许平均。
  5) 误差来源分解 E_total ≈ E_model + E_discretization + E_optimization + E_sampling + E_implementation + E_data，做 error attribution。
  6) Red Team：系统主动扰动自己，结论一动就降级（由另一位队员负责，你不做）。
  7) 最终输出结构：Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims。
  8) 长期：研究者能在 Leo AI 里做几轮实验提出改进 PINN 的新理论，同时不破坏可信闭环。
- 协作规则：只做本提示词指定的交付物；需要别的层配合的写进"给其他队员的接口建议"；术语按词表，新术语先定义；不确定写进"待队长决定"；你看不到仓库，不要猜路径或现有代码细节，不要输出改仓库的代码补丁；引用文献必须可核对（作者、年份、题目、出处），不确定就不写；输出中文 Markdown；交付物由队长合并，裁决权在队长。

【你的交付物】一份文件，文件名固定为 PINN_TRUST_R1_IMPL_TRAINING.md，第一行写"# PINN_TRUST_R1_IMPL_TRAINING · 作者：Kimi · R1 · 日期"。章节固定如下：
1. Manufactured Solution 协议（第 3 层 / G3）：如何构造已知真解 u*、推导源项 f* 与相容的边界条件；对 Poisson 1D 与二维不可压 NS 各给至少一个具体的 (u*, p*) 组合；验收判据（误差随网络容量、采样数、训练步数的预期收敛行为，用什么范数）；什么情况下 manufactured solution 会给出假阳性（例如 u* 太光滑、与网络激活函数同族）。
2. 实现单元测试检查表：自动微分（与有限差分 / 解析导数对照，含二阶导）、残差实现、几何掩码、边界采样覆盖率、法向量方向、坐标缩放与输出反缩放、loss 各项分离记录。每条给：测试名 / 构造方法 / 通过判据（数值阈值）/ 失败含义。
3. 训练可靠性协议（第 4 层 / G4）：多 seed（给出建议的 N 及理由）、不同初始化、不同采样集、不同 batch 顺序；必须记录的量 {L^(s), E^(s)}_{s=1..N}、统计口径（中位数、IQR、最差 seed，而不是最好 seed）、稳定性阈值建议；"五次只有一次好"如何判定为偶然成功；训练日志的最小字段集；何时 C_train 只能是 PARTIAL 或 FAIL。
4. 文献支撑：用可核对的文献支撑上述判据（Method of Manufactured Solutions；PINN 训练病态、梯度病态与失败模式；多 seed 报告规范）。每条给作者、年份、题目、出处。不确定的不写。
5. 给队长的说明：假设、待队长决定、给其他队员（数学核心、schema、Red Team、报告模板）的接口建议。

【不做】不设计 schema、不写状态机、不推导守恒公式、不写 Red Team 扰动矩阵（你只负责"正常协议"，扰动攻击归另一位队员）。
【篇幅】3000–6000 字。检查表用表格。
```

---

## 6. 提示词四：Grok（Red Team）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"Red Team"队员，任务是攻击我们自己的设计。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。允许直言不讳，允许说"这条不成立"。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手（源码仓库 LeoAIStudio-build，上游为 OpenAI4S）。其中的 PINN（物理信息神经网络）科研治理已有《Leo AI PINN 闭环科研宪法》和《PINN 闭环科研 MVP 计划》，代码里有对应的治理模块（规格 JSON schema、PRELOCK 校验、HASH LOCK、来源记录、状态机）。这些是既有事实，只能"修正案"式扩展，不能推倒重来。
- 既有词表（必须沿用）：
  · 证据等级：Level A（Exact / Manufactured Reference）、B（Numerically Converged Reference）、C（Trusted Published Benchmark）、D（No Independent Reference）。
  · Gate 状态只有 PASS / FAIL / BLOCKED / PARTIAL。PARTIAL 只是诊断信息，PARTIAL ≠ PASS，不能推进状态机；BLOCKED 表示上游前提未满足。
  · 七道 Gate：G1 规格与数学一致性、G2 Baseline / 参考解、G3 实现正确性、G4 训练、G5 验证、G6 复现性、G7 声明（Claim）。
  · 状态机：DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION →（PASS）REPRODUCIBILITY_CHECK → ACCEPTED；VALIDATION FAIL → FAILURE_RECORDED → DIAGNOSED → REVISED → 回到对应上游 Gate。训练结果不得绕过 Validation 直接 ACCEPTED。
  · Claim 等级：C0 仅描述；C1 Optimization Claim；C2 Numerical Accuracy Claim（对独立 reference 达到预注册误差标准）；C3 Robustness Claim（多 seed / 参数扰动稳定）；C4/C5 不在 MVP 内。前提矩阵：C0 需 G1、G3 PASS；C1 需 G1、G3、G4；C2 需 G1–G6 全 PASS 且证据等级不能是 D。
  · Reference Independence Rule：参考解不得与 PINN 共享同一代码路径。
  · 禁止单一 total loss 作为判据；loss 不是精度指标。
- MVP 案例：Poisson 1D v1.0（解析参考 + 独立 FDM 参考）。当前状态：PINN MVP = NOT COMPLETE，CFD Readiness = PARTIAL；测试层面干净，PRELOCK_VALIDATION PASS，但 HASH LOCK 与后续 Gate 尚未完整跑通。
- 队长确定的目标（R1 要设计的"可信闭环"）：
  1) 七层：问题定义 → 数学一致性 → 实现正确性 → 训练可靠性 → 物理一致性 → 独立数值验证 → Claim Gate。
  2) 反向定位：验证 FAIL 按症状分流——PDE residual 异常→方程 / AD / scaling；BC residual 异常→边界采样 / 硬约束；守恒量异常→物理 admissibility；PINN–CFD 不一致→两侧独立 provenance / 离散误差；seed 敏感→训练稳定性；局部误差集中→自适应采样 / 域分解 / 模型能力。
  3) 可信度向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，每维取 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；不输出单一百分比。
  4) 弱链原则（宪法级）：任何结论的可信等级不得高于其最弱关键证据链的等级；绝不允许平均。
  5) 误差来源分解 E_total ≈ E_model + E_discretization + E_optimization + E_sampling + E_implementation + E_data，做 error attribution。
  6) Red Team：系统主动扰动自己——换 collocation points、改 seed、扩大 / 缩小网络、改 precision、改采样密度、删除 10% 训练点、加密边界附近采样、改无量纲化、换 optimizer、检查梯度爆炸 / 消失、局部网格加密、检查 corner singularity、检查 out-of-domain extrapolation——结论一动就降级。
  7) 最终输出结构：Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims。
  8) 长期：研究者能在 Leo AI 里做几轮实验提出改进 PINN 的新理论，同时不破坏可信闭环。
- 协作规则：只做本提示词指定的交付物；需要别的层配合的写进"给其他队员的接口建议"；术语按词表；不确定写进"待队长决定"；你看不到仓库，不要猜路径或现有代码细节，不要输出改仓库的代码补丁；引用文献必须可核对（作者、年份、题目、出处），不确定就不写；输出中文 Markdown（文献题目保留原文）；交付物由队长合并，裁决权在队长。

【你的交付物】一份文件，文件名固定为 PINN_TRUST_R1_RED_TEAM.md，第一行写"# PINN_TRUST_R1_RED_TEAM · 作者：Grok · R1 · 日期"。章节固定如下：
1. 扰动实验矩阵：对上面第 6) 条的 13 类扰动逐条写：测什么 / 怎么做（步骤）/ 度量 / 触发降级的规则（影响可信度向量的哪一维、降到什么状态、阈值）/ 计算成本；再补充你认为遗漏的攻击（至少 5 条）。
2. 系统性漏洞审查：如何骗过这套闭环——PINN 与 CFD 共享代码路径导致"共同 bug 一致"、参考解泄漏进训练、验证集过拟合、挑 seed 报告、Gate gaming（把 FAIL 拆成多个 PARTIAL）、报告措辞漂移、无量纲化不一致导致两边比较的不是同一个量。每条给：攻击方法 / 检测方法 / 对策 / 应落在哪一层。
3. 对队长 8 条设计的逐条反驳与修订建议：哪些站得住、哪些有漏洞、哪些在工程上做不到，给替代方案。
4. 失败模式文献：近两年（含更早的经典）关于 PINN 失败模式、谱偏置、刚性 PDE、训练病态、验证方法学的可核对文献，每条一句话说明它支持或反驳我们哪一条设计。
5. 给队长的说明：假设、待队长决定、给其他队员（数学核心、schema、实现验证、报告模板）的接口建议。

【不做】不设计 schema、不写状态机、不写正常训练协议、不写报告模板。
【篇幅】3000–6000 字。反驳要有理由和可执行的替代方案，不要泛泛而谈。
```

---

## 7. 提示词五：豆包（报告模板与研究者工作流）

```
【你的角色】你是 Leo AI Studio 六方 AI 团队里的"报告模板与研究者工作流"队员。队长是 Claude，负责分工与合并；你只交付下面指定的一份文件，不越界。

【公共背景】
- 项目：Leo AI Studio 是一款 Windows 桌面科研助手（源码仓库 LeoAIStudio-build，上游为 OpenAI4S）。其中的 PINN（物理信息神经网络）科研治理已有《Leo AI PINN 闭环科研宪法》和《PINN 闭环科研 MVP 计划》，代码里有对应的治理模块。这些是既有事实，只能"修正案"式扩展，不能推倒重来。
- 既有词表（必须沿用）：
  · 证据等级：Level A（Exact / Manufactured Reference）、B（Numerically Converged Reference）、C（Trusted Published Benchmark）、D（No Independent Reference）。
  · Gate 状态只有 PASS / FAIL / BLOCKED / PARTIAL。PARTIAL 只是诊断信息，PARTIAL ≠ PASS；BLOCKED 表示上游前提未满足。
  · 七道 Gate：G1 规格与数学一致性、G2 Baseline / 参考解、G3 实现正确性、G4 训练、G5 验证、G6 复现性、G7 声明（Claim）。
  · Claim 等级：C0 仅描述；C1 Optimization Claim（收敛 / loss 行为）；C2 Numerical Accuracy Claim（对独立 reference 达到预注册误差标准）；C3 Robustness Claim（多 seed / 参数扰动稳定）。高等级 claim 必须建立在低等级 evidence 之上。
  · 禁止单一 total loss 作为判据；loss 不是精度指标。
- MVP 案例：Poisson 1D v1.0（解析参考 + 独立 FDM 参考）。当前状态：PINN MVP = NOT COMPLETE，CFD Readiness = PARTIAL。
- 队长确定的目标（R1 要设计的"可信闭环"）：
  1) 七层：问题定义 → 数学一致性 → 实现正确性 → 训练可靠性 → 物理一致性 → 独立数值验证 → Claim Gate。
  2) 验证 FAIL 后按症状分流反向定位，而不是简单重训。
  3) 可信度向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，每维取 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；绝不输出"可信度 92%"这种单一数字。
  4) 弱链原则（宪法级）：任何结论的可信等级不得高于其最弱关键证据链的等级；绝不允许平均（不是 GPA）。
  5) 误差来源要分解、要归因（model / discretization / optimization / sampling / implementation / data）。
  6) Red Team：系统主动扰动自己，结论一动就降级（另一位队员负责）。
  7) 最终输出结构固定六段：Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims。示例：Numerical recirculation length L_r/H = 6.42；CFD agreement PASS；Mass conservation PASS；Grid independence PASS；5-seed PINN variance 0.7%；Corner singularity sensitivity PARTIAL；High-Wi continuation robustness NOT VALIDATED → Accuracy claim ALLOWED；Generalization to higher Wi BLOCKED。
  8) 长期：研究者（例如想写一篇新的 PINN 论文的用户 A）能在 Leo AI 里做几轮实验提出改进 PINN 的新理论，同时不破坏可信闭环。
- 协作规则：只做本提示词指定的交付物；需要别的层配合的写进"给其他队员的接口建议"；术语按词表；不确定写进"待队长决定"；你看不到仓库和界面，不要猜；不输出代码；输出中文 Markdown；交付物由队长合并，裁决权在队长。

【你的交付物】一份文件，文件名固定为 PINN_TRUST_R1_REPORT_AND_WORKFLOW.md，第一行写"# PINN_TRUST_R1_REPORT_AND_WORKFLOW · 作者：豆包 · R1 · 日期"。章节固定如下：
1. 可信度报告模板（第 7 层的输出）：中英双语，固定六段 Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims。给措辞规则：不出现单一百分比；可信度向量逐维展示并给每维一句"这一维说明了什么"；最弱环节必须高亮并写明它限制了什么结论；"允许声称 / 禁止声称"的固定句式；NOT_CHECKED（没查）与 BLOCKED（前提不满足不能查）与 PARTIAL（查了但不充分）三者的措辞区别；数值必须带范数、单位与参考解来源。
2. 两个填好的示例：(a) Poisson 1D MVP，数据自拟但每个数字旁标注"示例数据"；(b) backward-facing step 回流长度 L_r/H = 6.42，按第 7) 条给的状态填写。两份都要写出对应的可信度向量和最弱环节。
3. 研究者工作流"让 PINN 进化"：用户 A 想写一篇新的 PINN 论文时，在 Leo AI 里如何登记实验假设、区分冻结项（问题定义、参考解、验证标准）与可变项（网络、采样、loss 权重、优化器等）、几轮实验的结果如何变成证据、哪些可以写进论文方法部分（给一份清单）、探索性结果如何标注才不与可信闭环冲突（例如只允许 C0/C1 级表述）。
4. 术语中英对照表（覆盖本文件用到的全部术语）。
5. 给队长的说明：假设、待队长决定、给其他队员（数学核心、schema、实现验证、Red Team）的接口建议。

【不做】不要设计任何新的界面、配色、按钮或组件——Leo 的界面变更需要用户单独批准，你只做文本结构与文案；不做数学推导、schema、扰动矩阵。
【篇幅】2500–5000 字。语言面向研究者，准确优先于华丽。
```

---

## 8. 回传与合并流程

1. 用户把每位队员的输出原样交给队长（粘贴或存为文件）。队长存入 `docs/pinn-trust-loop/inbox/<文件名>`，首行保留作者与日期，不改一字。
2. 队长逐份审读：与词表冲突的、越界的、与其它队员矛盾的，记入 `docs/pinn-trust-loop/R1_MERGE_NOTES.md`（分歧不抹平）。
3. 合并产物：宪法修正案草案（`governance/AMENDMENTS/`）、schema 草案（`pinn/governance/schemas/`）、状态机与测试（`pinn/governance/`、`tests/pinn/`）、报告模板（`docs/`）。每一步写进操作日志与 20260914 报告。
4. R2 由队长根据合并结果重新出题；队员不自行进入 R2。
