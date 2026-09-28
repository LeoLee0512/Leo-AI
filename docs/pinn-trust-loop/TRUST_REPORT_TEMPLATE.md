# Trust Report 模板（Claim Gate 的人读输出，第 3 稿）

来源：豆包 `PINN_TRUST_R1_REPORT_AND_WORKFLOW.md` §1 与 `PINN_TRUST_R2_REPORT_AND_WORKFLOW.md` §1–§4，按 `R1_MERGE_NOTES.md` 裁决 C4、C10、C11，`R2_MERGE_NOTES.md` 裁决 R2-30 ～ R2-35 与 A-0001 第 3 稿修订；Red Team 第 7 条补 Provenance 与 Scope。报告是第 7 层的只读渲染：机器判定（TrustVector、ClaimGateDecision、DiagnosisRecord、账本）在前，文本不得比机器判定更宽松，不一致时以机器记录为准并视为生成错误。

## 0. 措辞硬约束

1. 不出现单一百分比式总分；禁用词："可信度 xx%"、"总体可信"、"基本通过"、"平均等级"、"待验证"、"大致符合"、"初步通过"、"N/A 略过"。
2. 可信度向量逐维展示，每维一句"说明了什么 / 不说明什么"；维度下的检查按 CheckResult 逐条展示，并给一句维度汇总句。
3. 最弱环节必须高亮，写明它限制了哪条结论；并列时列出全部并列维度。
4. 允许 / 禁止声称只用 §3 固定句式，每条带 Claim 等级、成立条件与失效条件。
5. 数值三要素：范数（或口径）、单位、参考解来源与证据等级；loss 只能以分项出现在 Evidence 的训练日志一栏，禁止称作误差或精度。
6. 状态词只取 PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；检查级别另有 NOT_APPLICABLE（不承担）；英文展示 "NOT CHECKED" / "NOT APPLICABLE"（不用 "NOT VALIDATED"）。适用性在 SPEC_LOCKED 时由规格登记，报告不得按结果事后改标；一个维度不可能"全部不承担"（INV-A1）。
7. 必须披露三个评估集的哈希、C_external 是在 dev 集还是 claim 集上评估、claim 集哈希与状态（SEALED / OPENED@revision）、账本头。

## 1. 抬头与八段

```
# Trust Report / 可信度报告
Problem spec（冻结问题规格）: <problemId · revision · specHash 前 12 位>
Reference（参考解）: <来源 · 独立代码路径声明 · Level A/B/C/D（取自冻结规格）>
Evaluation sets / 评估集: D_train <sha12> · D_dev <sha12>（诊断/调参/模型选择/扰动）· D_claim <sha12> <SEALED | OPENED@revision> · ledger head <eventId 前 12 位>
C_external evaluated on / 外部一致性评估于: <D_dev | D_claim>；claim-set consistency / claim 集一致性: <PASS|PARTIAL|…>
Report id / 报告编号: <id>   Generated at / 生成时间: <UTC>   Gate path / 经过 Gate: G1…G7 状态序列
Run mode / 运行模式: FORMAL | EXPLORATORY   Code identity / 代码身份: <codeHash 前 12 位>

> Weakest link / 最弱环节：<维度（并列全列）> = <状态>。它限制的结论：<被压住的声称>；
> 在该维度升为 PASS 之前，任何需要它的 Ck 声称一律阻断（弱链原则，不平均、不抵消）。

## Result / 结果
## Evidence / 证据
## Uncertainty / 不确定性
## Known failure modes / 已知失效模式
## Allowed claims / 允许声称
## Blocked claims / 禁止声称
## Provenance / 来源
## Scope / 适用范围
```

抬头规则：三集哈希两两不同（样本级互斥由规格校验保证）；OPENED 必带 @revision 且与账本一致；若本报告写于 claim 集打开且 revision 已升之后，抬头必须同时显示旧集 burnt 记录（§4.1 句式）；C_external 只有 evaluationSet = claim 才允许 PASS，写在 D_dev 上的一致性最多 PARTIAL 且只能称"开发集一致性观察"，不得称 accuracy。

- **Result**：只陈述事实性数值与 Gate 状态。句式 `<QoI> = <值> <单位>，<范数/口径>，评估位置 <…>，评估集 <dev|claim>，对照参考 <来源·等级>`。EN: `<QoI> = <value> <unit> in <norm> at <location> on the <dev|claim> set, versus <reference, level>.`
- **Evidence**：每条 证据内容 → 证据等级 → 来源与独立代码路径声明 → artifactId + sha256 → 支撑的 Gate 与维度。每个维度下逐检查一行（§2.1）；训练统计栏用 seed 展示串（§2.2）。
- **Uncertainty**：误差六项逐项给已知界或 NOT ESTIMATED；多 seed 只报 N、中位数、IQR、最差 seed、k/N。
- **Known failure modes**：逐条按 §2.3 六槽位句式；必须列出实际执行过的 Red Team P 编号与结果，不写泛泛的"可能存在"；rUndetermined 的条目用停线句式。
- **Allowed / Blocked claims**：见 §3。C3 条目必须按 §3 披露 run 数、seed 集数与 environmentId 列表。
- **Provenance**：规格、代码、参考解、模型、三个评估集的哈希；账本头；C2 run 的 runId / environmentId / seedSetId 表（与 RunRecord 一致）。
- **Scope**：结论成立的参数范围与几何；外推禁区。

## 2. 可信度向量展示

`C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)`，一行六元组加逐维明细，禁止折叠成一个数。

| 维度 | 说明了什么 | 不说明什么 |
|---|---|---|
| C_math | 题目在纸面上自洽 | 解算得对 |
| C_impl | 程序算的是这道题 | 训练收敛 |
| C_train | 不是一次偶然成功 | 结果准确 |
| C_physics | 物理上可接受 | 逼近真值 |
| C_external | 与独立代码路径的参考在 claim 集上、阈值内一致 | 超出参考覆盖范围的行为 |
| C_repro | 不绑定于单次运行、单台机器、单一安装 | 独立实现也一致（那是 C_external） |

### 2.1 CheckResult 逐条写法

槽位固定：`<checkId> · <applicability> · <status，仅 APPLICABLE 有> · 证据指针 <artifactId·sha12> · 评估集 <train|dev|claim|phys|n/a> · 一句事实结论`。

- APPLICABLE 行示例：`PH1-fluxBalance · APPLICABLE · PASS · art#2041·a31c9f0d7b21 · phys · 通量平衡相对差 6.2e-9，优于预注册容差（示例数据）。`
- NOT_APPLICABLE 标准句（检查级专用）：
  - 中："〈checkId〉：**NOT APPLICABLE（不承担）**——本问题类型不承担此项检查，理由：〈规格登记的物理 / 数学理由〉；该项**无 status**，不计入本维度 meet。"
  - EN: "〈checkId〉: **NOT APPLICABLE** — this problem type does not owe this check (reason: 〈…〉); it carries **no status** and does not enter the dimension's meet."
- 维度汇总句（每维一条，必写）："本维度登记检查 〈n〉 项，其中 APPLICABLE 〈m〉 项：PASS/PARTIAL/FAIL/BLOCKED/NOT_CHECKED 各若干，NOT_APPLICABLE 〈n−m〉 项不计；维度状态 = 全部 APPLICABLE 检查的 meet = 〈状态〉〈若人工压低：'，人工压至 〈状态〉，理由：〈notes〉'〉。"（每个维度至少一项 APPLICABLE；没有登记任何检查的维度写 NOT_CHECKED，不写汇总句。）

四种"非通过"严格区分，禁止互换：

| 级别 | 词 | 含义 | 标准措辞（中） | EN |
|---|---|---|---|---|
| 仅检查级 | NOT_APPLICABLE | **不承担**：此题无此检查义务，SPEC_LOCKED 时随问题类型登记 | 见上标准句；无 status、不进 meet | 见上 |
| 两级 | NOT_CHECKED | **没查**：义务存在、未执行、无证据 | "尚未执行检查，无证据；不构成通过，也不构成失败。" | Not checked: no evidence yet; neither pass nor failure. |
| 两级 | BLOCKED | **不能查**：上游 Gate / 前提未 PASS，当前无定义 | "因上游〈Gate/前提〉未 PASS 而无法执行；须先解除上游阻断。" | Blocked: undefined until upstream 〈…〉 is PASS. |
| 两级 | PARTIAL | **查了不充分**：覆盖不全，仅诊断用 | "已检查但不充分：已覆盖〈…〉，未覆盖〈…〉；PARTIAL ≠ PASS。" | Partial: checked but insufficient; PARTIAL ≠ PASS. |

### 2.2 seed 判定展示串（Evidence 训练统计栏）

"seed 协议：N=〈n〉、k=〈达标 run 数〉、发散=〈d〉、k/N=〈值〉→〈<0.8 FAIL｜0.8≤·<0.9 PARTIAL｜≥0.9 PASS〉；median=〈值〉、IQR=〈值〉、最差 seed〈id〉=〈值〉照报；封顶：最差 seed>3ε 或 IQR>〈dispersionLimit〉×median 封顶 PARTIAL、median>ε FAIL、2D 过渡 N=5 封顶 PARTIAL、N<5 BLOCKED；seedSetId 〈sha12〉。"

### 2.3 Known failure modes：两层诊断固定句式

每条失效模式六槽位齐全，缺一不可：

- 中："**症状**〈FailureSignature 枚举名 + 证据位置与数值〉→ **根因**〈RootCauseClass 封闭枚举名；区分实验未完成时写'根因待定，候选集 {…}'，禁止只凭症状命名〉→ **区分实验**〈experimentId；逐个候选：〈根因〉被〈P 编号 / exp-id〉排除，观察到〈…〉；仅用 D_dev〉→ **回到的 Gate**〈根因对应 G1/G2/G3/G4〉→ **缓解状态**〈未缓解 / 已缓解：动作 + 重跑结果 + 诊断轮次 x/3〉→ **压住的维度**〈维度 = 状态〉。"
- EN: "**Signature** 〈enum, location, value〉 → **root cause** 〈closed enum, or 'undetermined; candidates {…}'〉 → **discriminating experiment** 〈id; per candidate: 〈cause〉 excluded by 〈experiment〉, observed 〈…〉; dev-only〉 → **Gate returned to** 〈Gk〉 → **mitigation** 〈open/closed: action, re-run result, round x/3〉 → **dimension held down** 〈dim=status〉."

硬规则：① 症状只是证据，不得直接路由（sLocalizedError 的可接受根因有六类，不得默认为实现缺陷）；② 根因只有在其余可接受候选全部被排除后才能写出（DiagnosisRecord.excludes 全覆盖），否则写"待定 + 候选集 + 已做 / 计划的区分实验"；③ 必须写实际执行过的 P 编号与结果；④ 扰动与区分实验只准看 D_dev；⑤ 重入 Gate k 后，k 及其下游维度重置 NOT_CHECKED，写入缓解状态槽；⑥ 一个扰动只压矩阵指定的那一维。

停线句式（rUndetermined）：

- 中："症状〈…〉经〈n〉轮区分实验（已做：〈P 编号与结果〉）仍无法在可接受矩阵内命名唯一根因（候选 {…}：各被哪条证据排除 / 保留）。**未能判定，已停线（rUndetermined → STOPPED_THE_LINE）**：本规格冻结一切 claim 晋升与下游重训，移交人工；同一规格诊断满 3 轮后再次 FAIL 同样停线。解除条件：人工裁决记录，或修订规格（新 specHash）后从对应 Gate 重走。"
- EN: "Signature 〈…〉 cannot be assigned a single acceptable root cause after 〈n〉 rounds (experiments: 〈…〉; candidates retained/rejected: 〈…〉). **Undetermined — line stopped (rUndetermined → STOPPED_THE_LINE):** all claim promotion frozen and handed to a human; a fourth FAIL on the same spec stops the line likewise. Resume only after a human ruling or a spec revision re-entering the responsible Gate."

## 3. 允许 / 禁止声称的固定句式

**允许（Allowed）**
- 中："在冻结规格〈problemId·revision·哈希〉与预注册判据〈范数+阈值〉下，〈QoI=值 单位〉在 claim 集〈sha12，OPENED@revision〉上相对〈参考解来源·证据等级〉达到〈阈值〉；本声称为 **Ck** 级，以可信度向量必需维度全部 PASS 为成立条件；若〈失效条件〉发生，本声称自动撤销。"
- EN: "Under frozen spec 〈id·revision·hash〉 and the preregistered criterion 〈norm, threshold〉, 〈QoI = value unit〉 agrees on the claim set 〈sha12, OPENED@revision〉 with 〈reference, evidence level〉 to within 〈threshold〉. This is a **Ck** claim, conditional on every required TrustVector dimension being PASS; it is automatically withdrawn if 〈invalidation condition〉 occurs."

**C3 独立性披露（C3 条目尾部必加）**
- 中："……本声称为 **C3（Robustness）**。独立性披露：independently qualified C2 runs = 〈m〉 个（要求 ≥ 5），互异 seed 集 = 〈s〉 个（seedSetId 由 seed 值派生），执行环境 = 〈e〉 个 environmentId（要求 ≥ 2；逐一列出哈希前 12 位：〈…〉）；全部 run 同 specHash〈sha12〉、同 codeHash〈sha12〉，复制 run 不计数。任一 run 被撤销、seed 集出现交集、或环境 / 哈希独立性被破坏，本声称自动撤销。"
- EN: "...This is a **C3 (robustness)** claim. Independence disclosure: independently qualified C2 runs = 〈m〉 (≥5 required), disjoint seed sets = 〈s〉 (seedSetId derived from the seed values), environments = 〈e〉 distinct environmentIds (≥2 required; listed: 〈…〉); all runs share specHash 〈…〉 and codeHash 〈…〉; duplicated runs do not count. It is automatically withdrawn if any run is retracted, seed sets intersect, or hash/environment independence breaks."

m / s / e 任一不达标，C3 条目不得出现，改写进 Blocked claims 并注明缺项。裁决 (ii) 的受限一致陈述不是 C2：措辞必须含"C1 级受限一致陈述"与 claim 集状态。

**禁止（Blocked）**
- 中："**不得声称**〈被阻断的结论〉，因为〈最弱维度〉=〈状态〉：该维度仅证明〈它实际说明的事〉，未达到 Ck 所必需的 PASS；补齐路径为〈动作 + 重走的 Gate〉，在此之前相关表述只能停留在 Cj（j<k）并标注探索性。"
- EN: "**No claim of** 〈blocked conclusion〉 **is permitted**, because 〈dimension〉 = 〈status〉: it establishes only 〈what it shows〉, short of the PASS required for Ck. Remedy: 〈action, Gate to re-run〉; until then wording must remain at Cj (j<k) and be labelled exploratory."

## 4. 研究者工作流补充（豆包 R2 §3，按裁决 R2-25 修订）

### 4.1 "我看了 claim 集之后怎么办"

D_claim 一旦 OPENED（账本事件），研究者对该集永久失盲，重新密封同一哈希不恢复盲态（账本 L4 / L7 拒绝）。看完结果后：

1. **改动影响数值输出或模型选择**（实现、超参、网络、采样、loss 权重、早停选择等，即 codeHash 或 specHash 会变）→ 升版五步：① 停止在旧 D_claim 上的一切判定与调参；② revision + 1，按冻结 / 可变项表确定重入 Gate，k 及下游维度重置 NOT_CHECKED；③ 重新预注册：判据 / 阈值 / QoI 若要改必须在看到新 claim 集之前写死（进 specHash）；治理侧生成新 D_claim，SEALED 事件入账本，哈希不得是账本上任何 OPENED 过的哈希；④ 旧集在账本上已 burnt，可以新哈希重新登记为 D_dev（或并入 D_train，那会改变 specHash）；⑤ 履行告知义务，固定句：
   - 中："D_claim〈sha12〉已于 revision〈r〉最终验证 OPENED（账本事件〈id 前 12 位〉）；其后因〈具体改动〉升至 revision〈r+1〉，该集对 r+1 及以后版本 **burnt（失盲不可恢复）**；新 D_claim〈sha12〉已重新预注册并 SEALED。"
   - EN: "D_claim 〈…〉 was OPENED at revision 〈r〉 (ledger event 〈…〉); a subsequent 〈change〉 forced revision 〈r+1〉, on which that set is **burnt (blindness unrecoverable)**; a new D_claim 〈…〉 is preregistered and SEALED."
2. **纯文字 / 元数据改动**（排版、错别字、不触数值产物的描述）→ specHash 与 codeHash 都不变即不升 revision；Provenance 列改动清单并声明两个哈希不变。拿不准算哪类，看哈希：任一变了就是第 1 类。
3. **禁止**：打开后假装没看过；旧集重新密封冒充新集；只往旧集补样本；按 claim 结果回调后在同一集复测；打开 claim 集后改代码而不升版本（决策校验器按 OPENED 事件的 codeHash 拒绝）；把 burnt 集的"好结果"当验证证据写进论文。

### 4.2 失败实验写入论文附录：症状与根因分两块

- **块 A · 症状（只写事实，禁用因果词）**：FailureSignature 枚举名；完整配置与全部 seed（含失败 seed）；观测数值、位置、当时 Gate 状态与 k/N；证据指针。不得出现"由于 / 因为 / 源于"。
- **块 B · 诊断**：候选 RootCauseClass 全集；每个候选对应什么区分实验、排除还是保留（与 DiagnosisRecord.excludes 一致）；最终根因、回到的 Gate、缓解动作与重跑结果；rUndetermined 原样写停线与人工裁决记录，不补编根因。

失败 run 不删除、不挑除，附录给全量清单；缓解成功的失败也保留——它是 C_train 与 C3 证据链的组成部分。

### 4.3 EXPLORATORY 标注

① 凡在 D_dev 上产生的观察默认 EXPLORATORY，展示串带 evaluationSet=dev，封顶 C1；② 看过 D_claim 结果后萌生的新假设，本 revision 内一律 EXPLORATORY，其正式验证只能用下一 revision 的新 claim 集；③ Run mode=EXPLORATORY 的报告不进 ACCEPTED，Allowed claims 最多到 C1。探索只能靠补做对应 Gate 晋升，不能靠改写措辞晋升。

## 5. 示例 (b) 第 2 版（backward-facing step，L_r/H = 6.42；数值均为自拟示例数据；按裁决 C4 与 R2-30）

抬头评估集披露：`D_train a1b2c3d4e5f6 · D_dev b2c3d4e5f6a7（P11/P12/P13 等扰动只在此集）· D_claim c3d4e5f6a7b8 OPENED@r1（账本事件 9f0e…）· C_external evaluated on: D_claim；P12 角点排查执行于 D_dev。`

向量 **C = (PASS, PASS, PARTIAL, PARTIAL, PASS, NOT_CHECKED)**：
- C_math = PASS：规格、量纲、Wi→0 退化、几何约定一致。
- C_impl = PASS：T1–T10 与 NS manufactured 双 ν 档通过。
- C_train = **PARTIAL**：N = 5（2D 过渡，规则封顶 PARTIAL）；"k/N = 5/5 = 1.0 仍封顶 PARTIAL；最差 seed #3：L_r/H = 6.38；IQR 未超 median"。
- C_physics = **PARTIAL**：PH8 质量通量 PASS；P12 越线，按 Red Team 矩阵降级 C_physics，必写 **"corner treatment not validated"**（FM-1）。
- C_external = **PASS**：claim 集上 CFD agreement PASS（6.42 对收敛 CFD 6.41，在预注册阈值内）、grid independence PASS；P12 不压这一维（R2-30：一个扰动只压矩阵指定的那一维）。
- C_repro = **NOT_CHECKED**：无独立环境复现 run（没查，非上游阻断）。

> Weakest link：C_repro = NOT_CHECKED；其次 C_train = C_physics = PARTIAL。限制的结论：六维未全 PASS，C2 Accuracy、C3 Robustness 与高 Wi 外推一律阻断；只放行 C1 级受限一致陈述。

Known failure modes：
- **FM-1**：症状 sLocalizedError（再入角邻域，回零点定位随角点局部处理漂移，三半径极差 0.08H，越 Δq = 0.05H 带）→ 根因：**第 1/3 轮，待定，候选集 {rSingularityTreatment→G1, rSamplingDeficiency→G4, rReferenceDefect→G2, rImplementationDefect→G3, rCapacityLimit→G4, rOptimizationFailure→G4}** → 区分实验 exp-bfs-01：P12（三半径只评估、D_dev）已做，结果 6.39 / 6.42 / 6.47 越线；rSamplingDeficiency 待 P11 局部加密重训排除或保留；rReferenceDefect 待 CFD 角点收敛序列；rImplementationDefect 待 T4/T6 角点掩码复核；rCapacityLimit 待 P3；rOptimizationFailure 待 P8——六个候选未全部排除前不命名根因 → 回到的 Gate：视最终根因而定 → 缓解状态：未缓解（round 1/3）→ 压住维度：C_physics = PARTIAL。

Allowed claims：
- C0："该网络在冻结工作点输出带再循环区的定常近似流场。"
- **C1 受限一致陈述（裁决 ii）**："在冻结规格〈id·r1·hash〉与预注册阈值下，L_r/H = 6.42（无量纲）在 D_claim（c3d4e5f6a7b8，OPENED@r1）上与收敛 CFD 参考（Level B）阈值内一致；本陈述为 **C1 级受限一致陈述**，仅限该 QoI 与该 Re/Wi 工作点；失效条件：FM-1 根因闭合前保持受限、seed 补齐前不得升 C2、任何重训使 claim 集 burnt 后本陈述随旧集一并撤销。"

Blocked claims：
- C2："不得声称'数值精度达标'：C_repro = NOT_CHECKED（没查）、C_train 受 N = 5 封顶 PARTIAL、C_physics 受 FM-1 压在 PARTIAL；补齐：seed 补至 N ≥ 10 且 k/N ≥ 0.9、闭合 FM-1（排除其余五个候选或命名根因并重走对应 Gate）、独立环境复现，重走 G4/G5/G6。"
- C3："不得声称鲁棒 / 可推广：qualified C2 runs = 0/5、互异 seed 集 0、environmentId 0/2；高 Wi 外推 = NOT_CHECKED（P13 未跑），域外声明没资格。"

这与用户原始示例中的 "Accuracy claim ALLOWED" 不同，是弱链原则的直接后果（裁决 C4，用户已确认）。与第 2 稿模板示例的差异：C_physics 由 PASS 改为 PARTIAL（假设 P12 已执行且越线），C_external 由 PARTIAL 改为 PASS（P12 不再连带压它）；豆包 R2 原稿把 FM-1 同时压两维，队长裁决只压 C_physics（R2-30），原文保留在收件箱。
