# PINN 可信闭环 · 协议汇编（规范性索引，第 3 稿）

状态：随修正案 A-0001（第 3 稿，PROPOSED）一同；A-0001 ACCEPTED 后本文件的阈值成为预注册起点，正式值在每个规格 SPEC_LOCKED 前冻结进 HASH LOCK（自 1.2 起冻结在 `ProblemDefinition.preregistration`，进入 specHash）。原始交付物在 `docs/pinn-trust-loop/inbox/`，本文件只收录经队长裁决后的规范性部分并指向出处；与原文冲突处以 `docs/pinn-trust-loop/R1_MERGE_NOTES.md`、`R2_MERGE_NOTES.md` 的裁决与 A-0001 reviewLog 为准。

## 1. 可信度向量与弱链演算（DeepSeek §4，代码 `pinn/governance/trust_vector.py`）

| 维度 | 对应 Gate | 说明了什么 |
|---|---|---|
| C_math | G1 | 方程、边界、量纲、无量纲化在纸面上自洽 |
| C_impl | G3 | 算子与装配经独立测试正确 |
| C_train | G4 | 多 seed、多采样下训练行为稳定 |
| C_physics | G5a | 解满足守恒、正定、对称等可采纳性约束 |
| C_external | G5b | 与不同代码路径的独立参考在预注册范数与阈值内一致，且只在 D_claim 上评估才能 PASS（G2 未 PASS 时 BLOCKED） |
| C_repro | G6 | 同规格同代码、独立环境、不同 seed 集的复现落入容差 |

- 维度状态 TrustStatus：PASS / PARTIAL / FAIL / BLOCKED / NOT_CHECKED；只有 PASS 支持 claim；报告序 FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS。
- 检查级别另有 **Applicability**：`CheckResult{checkId, applicability, status?, reason, evidence}`；NOT_APPLICABLE 无 status、必须写理由、不进入 meet；维度状态 = 全部 APPLICABLE 检查的 meet。**INV-A1（第 3 稿）**：没有登记任何检查 = NOT_CHECKED；登记了检查但全部 NOT_APPLICABLE = 非法登记（`NoApplicableCheck`），不是任何状态。适用性在 SPEC_LOCKED 时登记于 `ProblemDefinition.checkApplicability`（每维至少一项 APPLICABLE），之后不得改标；TrustVector 里已执行的维度必须逐项展示注册表的检查，status 不得高于 meet，低于 meet 须 notes 说明。
- 允许等级：C0 需 {math, impl}，C1 需 {math, impl, train}，C2/C3 需六维全 PASS 且证据等级 ≠ D（等级取冻结规格的 primary source）；C3 另需 ≥ 5 个 independently qualified C2 run（同 specHash、同 codeHash、seed 集互异、≥ 2 个执行环境，`c3_run_support`）；EXPLORATORY 封顶 C1。
- 组合算子只有取最弱；TrustStatus 没有算术，平均是类型错误（测试 `tests/pinn/test_trust_vector.py`）。

## 2. 数学一致性条件（DeepSeek §1，对应 G1）

六条机器可判条件：场计数闭合；BC/IC 计数匹配（Neumann-only Poisson 欠定）；量纲齐次性；尺度唯一 + 极限退化（Re→0 → Stokes，Wi→0 → Newtonian，Pe→0 → 纯扩散）；坐标 / 几何 / 外法向绑定；张量阶与符号一致。默认等价容差 1e-14（float64）。

## 3. 物理一致性检查（DeepSeek §2 + Kimi R2 §3，对应 G5a）

每项检查按问题类型在规格里登记 Applicability；下表的 "—" 即 NOT_APPLICABLE（登记时必须写明缺失的物理前提，"节省时间"、"历史上总失败"之类的理由拒绝登记）。全部检查在 float64 下执行；积分 / 求值节点集为 D_phys（确定性 Gauss–Legendre 节点，公开、无 seed、登记为 `evaluationSets.phys`，与训练点互斥）；每项产出一个 CheckResult，证据含实测数值、节点集哈希、代码哈希。

| checkId | 检查 | Poisson 1D（MVP） | NS / Oldroyd-B（CFD 目标） |
|---|---|---|---|
| PH1 / PH8 | 质量守恒 / 通量平衡 | \|(u'(0) − u'(1)) − Σ w_i f(x_i)\| / 2π < 1e-8 | 四边 GL 边界积分，\|Σ_e Q_e\| / Σ_e Σ w \|û·n\| < 1e-6 且 ‖∇·û‖₂ ≤ 1e-3 |
| PH2 / PH9 | 能量平衡 | \|Σ w_i (u')² − Σ w_i f u\| / (π²/2) < 1e-8（齐次 Dirichlet；非齐次时预注册含边界项的替代式） | 边界净流入 + 耗散 − forcing 功，以耗散量级归一，相对 1e-4～1e-3（默认值待预注册） |
| PH10 | 动量收支 | —（标量方程无动量变量） | 分量式边界积分减体积力，每分量相对残差 < 1e-3 |
| PH3 | 正定性 | min û ≥ −1e-12（前置 f ≥ 0） | det C > ε，C_xx > ε |
| PH4 | 对称性 | GL 节点关于 ½ 配对，max\|û(x_j) − û(1−x_j)\| < 1e-10（前置：域 / f / BC 对称） | C = Cᵀ：max\|C_xy − C_yx\| < 1e-12；台阶流全域对称 — |
| PH5 | 单调性 | (0,½) 增、(½,1) 减，前向差分容差 1e-8，违例数 = 0 | —（回流区） |
| PH6 | 最大值原理 | max û ≤ 0.9999992382（CGL2000 离散界，不用理想值 1；界的出处由数学核心维护） | —（纯 NS 无最大值原理） |
| — | 自由能 / 熵 | —（已被能量恒等式覆盖，须引用 PH2 并由数学核心签署） | tr C − ln det C − 2 ≥ −1e-10 |
| PH7 | SPD | 独立路径装配 FDM 三对角矩阵（n = 1024），λ_min > 0 且 ∫(u')² > 1e-14 | C 对称正定 |

Applicability 表（DeepSeek R2 §4，理由可直接填入 `CheckResult.reason`，登记于 `ProblemDefinition.checkApplicability`）：

| 检查项 | Poisson 1D | 二维稳态不可压 NS | Oldroyd-B 粘弹流 |
|---|---|---|---|
| 质量守恒 / 通量平衡 | ✓（兼容条件 ∫f = u′(b) − u′(a)） | ✓（∇·u = 0 即约束本身） | ✓（∇·u = 0） |
| 能量平衡 | ✓（∫(u′)² = ∫ f u） | ✓（ν∫\|∇u\|² = ∫ u·f + 边界功率） | ✓（动能 + 弹性势能总收支） |
| 动量收支 | ✗ 标量方程无动量变量 | ✓ | ✓（含 ∇·τ） |
| 正定性 | ✓（−d²/dx² 强制） | ✗ 无必须恒正的物理标量场：压力为规范量可为负 | ✓（构象张量 c ≻ 0，否则 HWNP 失稳） |
| 对称性 | ✓（自伴算子，对称数据 ⇒ 对称解） | ✗ NS 允许对称破缺分岔 | ✓（τ = τᵀ、c = cᵀ） |
| 单调性 / 比较原理 | ✓ | ✗ 无比较原理，速度 / 压力可超调 | ✗ 粘弹流无比较原理 |
| 最大值原理 | ✓ | ✗ 向量耦合 + 压力 Poisson 耦合破坏极值原理 | ✗ 上随体导数 + 对流无极值原理 |
| 自由能 / 熵 | ✗ 稳态椭圆方程无耗散结构（由能量恒等式覆盖） | ✗ 不可压等温无自由能结构 | ✓（F = (η_p/2λ)∫tr(c − ln c − I) 沿流非增） |
| SPD | ✓（FEM 刚度矩阵） | ✗ 对流项使线性化算子非对称 | ✗ 非 SPD |

每列都至少有一项 ✓（INV-A1 成立）。归一化常数（2π、π²/2）按 MVP 问题数据给出，换问题数据时由数学核心重新给出并预注册。回流长度 L_r/H 的可执行定义：台阶下游壁面剪应力 τ_w 由负变正的零点横坐标除以台阶高 H；须预注册，依赖回流区存在、唯一符号翻转、质量守恒通过。

## 4. 误差归因与两层诊断（DeepSeek §3 + 评审意见 1 + 第 3 稿审计项 1，代码 `state_machine.py`、契约 `diagnosis-record.schema.json`）

E_total ≈ E_model + E_discretization + E_optimization + E_sampling + E_implementation + E_data；不可线性相加。诊断分两层：

1. **FailureSignature**（观察到什么）：sPdeResidual、sBcResidual、sConservation、sPinnCfd、sSeedSensitive、sLocalizedError。
2. **RootCauseClass**（区分实验找到什么）：rSpecDefect、rDataDefect、rSingularityTreatment → G1；rReferenceDefect → G2；rImplementationDefect → G3；rCapacityLimit、rOptimizationFailure、rSamplingDeficiency → G4；rUndetermined → STOPPED_THE_LINE。

可接受矩阵（症状 → 允许的根因）：

| 症状 | 可接受根因 |
|---|---|
| sPdeResidual | 规格、实现、容量、优化、采样、奇异性（A-0002 第 2 稿） |
| sBcResidual | 规格、数据、实现、优化（loss 平衡）、采样、容量（A-0002）、奇异性（A-0002 第 2 稿） |
| sConservation | 规格、实现、容量、优化、采样 |
| sPinnCfd | 规格（两侧不是同一方程）、数据（参数不一致）、奇异性、参考解、实现、优化、容量（A-0002）、采样（A-0002 第 2 稿） |
| sSeedSensitive | 容量、优化、采样、实现（非确定性缺陷，A-0002 第 2 稿）、规格（非唯一解，A-0002 第 2 稿） |
| sLocalizedError | 奇异性、参考解局部失真、实现、容量、优化（权重）、采样、规格（A-0002） |

矩阵范围：**forward-problem MVP**（`state_machine.MATRIX_SCOPE`，`DiagnosisRecord.problemClass = forward`）。正向问题里观测数据不进入 PDE 算子，所以 sPdeResidual / sConservation → 数据不可接受；逆问题（参数由数据识别）需要自己的修正案与矩阵。空格分类（A-0002 第 2 稿闭合审计）：IMPOSSIBLE——sPdeResidual / sBcResidual / sConservation / sSeedSensitive → 参考解（这些症状的计算不涉及参考解）；OUT_OF_SCOPE——五个症状 → 数据（正向问题）；UNSUPPORTED——sConservation → 奇异性（全局积分对小测度角点不敏感，待 CFD 案例给出证据）、sSeedSensitive → 奇异性；其余为 ADMISSIBLE。

**根因是排除后剩下的，不是挑选的**：`DiagnosisRecord{diagnosisId, problemId, revision, specHash, signature, signatureEvidence, rootCause, gate?, discriminatingExperiment{experimentId, evaluationSet = dev, excludes{根因: {experiment: P 编号或 exp-id, observed}}, evidencePointers}, round ≤ 3, decidedBy, decidedAt}`；`excludes` 必须覆盖该症状的**每一个其它可接受根因**，否则 `diagnose` 拒绝；rUndetermined 只需 experimentId 并直接停线；gate 若写出必须等于根因派生值。诊断轮次的键是 (problemId, specHash)，specHash 不含 revision，空升版不重置。PINN–CFD 不一致时不得默认 PINN 错的十种情形见 DeepSeek 原文 §3.2。

**诊断实验库 P22–P32（DeepSeek R2 §1.1；与 Red Team 的 P1–P21 分工：P1–P21 是对抗式加压，P22–P32 是隔离式诊断；编号不合并，`DiagnosisRecord.excludes[].experiment` 两类都接受）**：P22 制造解 MMS（实现 / 容量 vs 规格 / 优化）、P23 容量扫描、P24 优化器 / 迭代消融、P25 采样加密、P26 损失分项分解、P27 数据消融、P28 硬约束切换、P29 局部加密收敛性（奇异性 vs 采样 / 容量）、P30 参考解交叉验证、P31 独立重实现（实现 vs 规格）、P32 种子方差分解。数值约定：「下降 ≥ 1 个量级」= log₁₀(前/后) ≥ 1；「显著下降」= 后/前 < 0.5；「两实现一致」= 相对差 ≤ 1%（→ 规格）；「纠正」= 重实现相对差 ≤ 1% 且与 PINN 相对差 > 10×（→ 实现）；「加密不收敛」= 残差不减反增或下降率 < 2×/倍（→ 奇异性）。

逐格判定规则（每格 = 该根因的排除 / 保留实验，写进 `excludes` 的 observed 字段）：sPdeResidual：规格 P31+P22（重实现残差结构一致）、实现 P22+P31（大容量 MMS 仍 > ε）、容量 P23（残差(大)/残差(小) < 0.5 且仍在下降）、优化 P24+P26（换优化器降 ≥ 1 量级）、采样 P25（加密后降 > 50%）。sBcResidual：规格 P31+P22（BC 算子与规格文档不符）、数据 P27（消融该数据后 BC 残差改变）、实现 P31+P28（重实现纠正）、优化 P28+P24（增权重 / 硬约束后 BC 残差消失且 PDE 残差可接受）、采样 P25（加密 BC 配点后下降）。sConservation：规格 P31（重实现得同错）、实现 P31（重实现纠正）、容量 P23、优化 P24、采样 P25。sPinnCfd：规格（两套 spec 对照不一致）、数据 P27（换正确参数后 gap 缩小）、奇异性 P29（加密不收敛）、参考解 P30（更细网格 / 第二求解器下参考间不一致）、实现 P22+P31、优化 P24。sSeedSensitive：容量 P23+P32（容量↑ → seed IQR↓）、优化 P24+P32（更稳优化器后方差↓）、采样 P25+P32（固定配点后方差↓）。sLocalizedError：奇异性 P29、参考解 P30、实现 P31、容量 P23+P29、优化 P24、采样 P25+P29（局部加密误差↓且收敛）。

**受控干预与确定性重放（A-0002 第 2 稿，`state_machine.intervention_errors` / `determinism_replay_errors`）**：命名 rCapacityLimit 或 rSamplingDeficiency 必须附 `intervention{factor, changed = [唯一允许改动的控制项], heldFixed ⊇ 其余全部控制项（architecture / sampling / optimizer / lrSchedule / lossWeights / trainingBudget / spec / reference / seedProtocol）, levels ≥ 3 档、每档 ≥ 3 seed、逐档中位误差严格下降}`；容量另需 `optimizationDiagnosticsClean = true`——单次加大网络或加密采样后变好不是因果证据，它同时改变了优化景观。命名 sSeedSensitive → rImplementationDefect 必须附 P33 确定性重放 `determinismReplay{sameSeedRuns ≥ 2, maxDivergence, epsilonDet, defectLocated}` 且 maxDivergence > epsilonDet；重放一致则实现非确定性被排除，不得命名。P33：固定初始化 / 采样 / batch 三 seed、环境、规格、代码配置做同 seed 重放，输出差 > ε_det 即实现非确定性候选。P34：**可识别性检验**（A-0002 第 3 稿）——不同 seed 解的差投影到算子零空间（如 Neumann Poisson 的常数模）上的占比只是证据；判据是这种多解 / 零空间 / 等价关系是否违反当前冻结 Claim 要求的可识别性。命名 sSeedSensitive → rSpecDefect 必须附 `identifiability{ambiguityType ∈ nullspace / gauge / normalization / branch / symmetry, claimRequiresUniqueEvaluation = true, specResolvesAmbiguity = false, ambiguityIntent = unintended, nullspaceProjectionFraction?}`（`state_machine.identifiability_errors`）：Claim 不需要唯一目标（分支感知 / 集合值）、多解是规格有意的、规格已定规范条件——都是合法多解，不得命名规格缺陷；证据判定不了是否有意（`undecided`）→ rUndetermined 停线。

**版本隔离与症状覆盖（A-0002 第 3 稿）**：可接受矩阵与命名义务按宪法版本分表（`state_machine.ADMISSIBLE_ROOT_CAUSES_BY_VERSION` / `NAMING_OBLIGATIONS_BY_VERSION`），入口 `admissible_root_causes(version)` 只接受 `locking.SUPPORTED_CONSTITUTION_VERSIONS` 内的版本；`diagnose` 与 `validate_diagnosis_record` 都要求 DiagnosisRecord 的 `constitutionVersion`，PROPOSED 修正案的格在其版本生效前不可达。`observedSignatures`：诊断记录列出全部观察到的症状；`explainedSignatures ⊆ observedSignatures`（默认 = 主症状）是本条记录解释的症状，`excludes` 覆盖所解释症状候选集的并集；一个失败可有多条记录（sPdeResidual ← 优化、sLocalizedError ← 奇异性），**症状覆盖不变量**（`trust_loop.diagnosis_coverage_errors`）：记录集合同属一个失败、observedSignatures 相同、⋃explained = observed、每个症状恰好一条记录；同一症状被两个根因同时声称 = 非法（分不开就 rUndetermined）；多条记录重入取最小 Gate（`earliest_route`）。挑便宜症状的绕过由覆盖不变量封住，而不再由"一个根因解释全部症状"封住。

DeepSeek 建议增加三格（sBcResidual → 容量、sPinnCfd → 容量、sLocalizedError → 规格）：队长采纳，起草 **A-0002**（`governance/AMENDMENTS/A-0002-admissible-matrix-r2.md`，PROPOSED），代码矩阵与测试已同步；判定规则——sBcResidual → 容量：P23，BC 残差随容量单调下降 → 容量；sPinnCfd → 容量：P23，容量 ↑ → gap ↓ → 容量；sLocalizedError → 规格：P31 + P22，对照规格文档源项 / 边界位置错 → 规格。倾向不加的 sPinnCfd → 采样（中介而非直接根因）、sPdeResidual / sConservation → 数据（正向问题数据不进算子；逆问题不在 MVP 范围）、sSeedSensitive → 实现（实现缺陷应是确定性的；非确定算子由 P4 精度 / 确定性检查排除）：采纳"不加"。

## 5. 实现正确性（Kimi §1–§2，对应 G3）

- MMS 五步：选解 u*（不得与网络同族）→ CAS 推源项 f*（脚本归档，不与训练代码共享路径）→ 推边界 / 初值 → 求解 → 在 D_dev 上对照（G3 阶段），claim 集不开。
- Poisson 1D 组合：P1 光滑基线 u* = sin(2πx)；P2 应力测试 u* = sin(2πx) + 0.05 sin(32πx)（主判据）；P3 非对称备查 u* = x(1−x)eˣ。NS：流函数 ψ = sin(πx)sin(πy) 构造 NS1，ν = 1 与 0.01 双档。
- 验收：相对 L2 为主、L∞ 为辅（NS 加散度范数），评估网格 ≥ 4096 点且与训练配点零重叠（样本级，见 §10）；平台期高于 ε_spec 不得 PASS。
- 单元测试 T1–T10（float64）：AD 一阶 / 二阶导对 FD、AD 对解析导数、残差符号、几何掩码、边界采样覆盖率、法向量方向、缩放 / 反缩放回路、loss 分项分离、配点互斥（宪法级，四集合版本：D_train 含边界子集、D_phys、D_dev、D_claim）。任一 FAIL 全量重跑；缺一项视同 NOT_CHECKED。
- 假阳性清单（Kimi §1.5）逐条排查记录归档，否则 PARTIAL。

## 6. 训练可靠性（Kimi §3 + Kimi R2 §2 + 评审意见 4 + 复审 Issue 5，代码 `seed_statistics` / `training_reliability_status`）

- N ≥ 10（1D）；2D 过渡 N = 5 封顶 PARTIAL；N < 5 为协议未执行（BLOCKED）；N 与 ε_spec 在 `preregistration` 里冻结，事后不得改；三因子解耦 (s_init, s_sample, s_batch)，三元组先入 append-only 的 seed 账簿再启动 run（登记时间戳早于 run 启动）；seedSetId = 排序去重后 seed 值的哈希（改名、重排不改变身份）。
- k 的定义：相对 L2，E^(s) = ‖û − u_ref‖₂ / ‖u_ref‖₂，在 D_dev 上（整个 G4 期间固定不变），阈值 ε_spec；只在同 specHash + 同 codeHash 的 run 内统计。A 段单因子归因扫描（每因子 5 组）不计入 k/N；B 段 N 组全随机组合计入。
- 判定顺序（全部比较显式，**无除法**）：日志完整性（缺项 run 记 BLOCKED 剔除并注明，N 不改）→ loss–error 解耦（分项 loss 降两个数量级而 E 不降 → FAIL）→ 中位数 > ε_spec → FAIL → k/N < 0.8 → FAIL；0.8 ≤ k/N < 0.9 → PARTIAL；≥ 0.9 → 进入封顶 → 最差 seed > 3ε_spec 或 **IQR > dispersionLimit × median** → 封顶 PARTIAL → N 封顶（5 ≤ N < 10 → PARTIAL）→ PASS。NaN / Inf 的 run 是发散 run：计入 N、不计入 k、最差 seed 为发散；负误差是调用方错误。median = 0 且 IQR = 0 不封顶；median = 0 且 IQR > 0 封顶；没有分母下限，没有近零容差规则。
- 报告 {N, k, k/N, median, IQR, max, seedSetId, D_dev 哈希, 剔除 run 清单}；最好 seed 永不进入判定。
- **阈值的统计含义（DeepSeek R2 §2，写明以免误读）**：在 seed i.i.d.、无重尾的二项模型下，N = 10、k = 9 的 PASS 只能以 95% 置信认证 p ≥ 0.55（Clopper–Pearson），似然比 LR(p=0.9 : p=0.5) ≈ 40；k = 8 的 PARTIAL 只有 LR ≈ 4.4；N = 5 即使 5/5 也只有 p_L ≈ 0.55、LR ≈ 19，无法把"可靠"与"抛硬币"区分开，所以 2D 过渡期 N = 5 在任何 k 下不得 PASS。**PASS ≠ 高置信认证 p ≥ 0.9**：0.9 / 0.8 两条线是"以可承受算力换取中等置信下限"的折中；median、最差 seed、IQR 三条稳健规则与 k/N 正交，专门打击幸运 seed 与重尾。算力换置信（PASS 线 k ≥ ⌈0.9N⌉，坏方法 p = 0.7 的错误接受率）：N = 10 → 15%、20 → 3.5%、30 → 0.9%、50 → 0.2%、100 → 0.001%。升级路径（预注册时声明，不作补救）：2D 稳定期建议 N ≥ 30，1D 的 C2 / C3 阶段建议 N ≥ 50。
- 禁止（Kimi F1–F8）：报最好 seed；事后改 N / ε_spec / k 口径；用 D_claim 或训练配点算 seed 统计；复用三元组或 C3 各 run 间 seed 集有交集；静默删除发散 run；A 段 run 凑 k/N；扫描期间改架构 / 超参 / 配点数；以补跑最好 seed 复现报告数字替代协议。

## 7. Red Team（Claude 代 Grok §1–§2）

- P1–P21 扰动矩阵与降级规则见原文 §1；分层：Tier-0（P10、P12、P13、P18、P19 哈希交集、P20、P21）任何 claim 前必跑；Tier-1（P1、P4、P6、P7、P8、P9、P11、P16）C2 前必跑；Tier-2（P2、P3、P5、P14、P15、P17）C3 前必跑。扰动实验与区分实验只准看 D_dev（`DiagnosisRecord.discriminatingExperiment.evaluationSet` 固定为 dev）。
- 扰动结果以新版本 TrustVector 记录（supersedesRecordId），每维携带 perturbationsRun 与 worstCase（有扰动必有 worstCase）；只能降级或维持，且只降级矩阵指定的那一维（P12 越线 → C_physics PARTIAL，不连带 C_external）。
- 15 条系统性漏洞与对策（§2）中，V1 共同 bug 一致、V2 参考泄漏、V3 验证集过拟合（现由 D_claim 纪律与账本封死）、V4 挑 seed（现由 seedSetId 派生封死）、V5 Gate gaming、V11 硬约束假 PASS、V13 参考未收敛为必查项。
- 第 3 稿新增建议挂接（Kimi R2 §6）：模拟训练进程读取 claim 文件（应被权限挡下并留痕）；seed 账簿时间戳后补（应被 append-only 拒绝）；environmentId 伪造（改 hostname 不改强字段，应判同一环境——已有测试）。

## 8. 数据契约与状态机（GLM §1–§5、GLM R2 + 评审意见 1/2/3/5 + 复审五项，代码 `schemas/*.schema.json`、`trust_loop.py`、`claim_set_ledger.py`、`evaluation_sets.py`、`state_machine.py`）

- 七份契约，全部只用 `jsonschema_lite` 的关键字子集；条件约束由 Python 交叉校验执行并失败关闭：
  - `problem-definition 1.2`：+ `checkApplicability`、`preregistration{errorNorm, epsilonSpec, seedRuns, seedFactors, worstSeedFactor, dispersionLimit, qoiBand?}`、`evaluationSets.phys?`、`evaluationSets.minSeparation?`；specHash = 除 specHash、revision、claim 集状态字段外全部字段的规范化哈希。
  - `evaluation-set 1.0`：样本清单（见 §10）。
  - `claim-set-event 1.0`：账本事件（见 §10）。
  - `trust-vector 1.2`：+ `revision`、维度 `claimSetSha256`；已执行维度必须有 checks 且与注册表一致；status ≤ meet；有 perturbationsRun 必有 worstCase。
  - `run-record 1.0`：runId、problemId、revision、specHash、codeHash + codeManifest、environment + environmentId、seeds + seedSetId、evaluatedOn、时间、执行者；三个派生哈希复算。
  - `diagnosis-record 1.0`：见 §4。
  - `claim-gate-decision 1.2`：+ `revision`、`claimSetSha256`、`ledgerHead`；qualifiedC2Runs 携带 environment 与 seeds，environmentId / seedSetId 复算；referenceEvidenceLevel 必须等于规格 primary source；external 在 claim 集上判定过 ⇒ 账本有本版本 OPENED 且 codeHash 相等；可选 RunRecord 注册表逐项核对。
- 未采纳：新增 PHYSICS_CHECKED 状态（裁决 C3）；weakestLink 排序（裁决 C1）；BLOCKED 进 FAILURE_RECORDED；ABANDONED 新状态（R2-19）；actor 污染集（R2-9）；检查级通过率分档泛化（R2-11）；枚举 / ID 改名（R2-21）；qualifiedC2Runs minItems 5（R2-14）。
- 重入规则按"宁严勿松"：重入 Gate k 后，k 及下游全部（含 BLOCKED）重置 NOT_CHECKED 并重跑；如需放宽，另立修正案。
- 复发升级（GLM R2 §3，用户 2026-09-15 同意采纳）：同一 problemId 跨 specHash 出现同一 (rootCause, gate) 的诊断 ≥ 2 次，自动触发停线评审（STOPPED_THE_LINE，交队长裁决），不是直接终止；需要跨规格的诊断注册表，实现为 R3。

## 9. 报告模板（豆包 §1 + 豆包 R2 §1–§4，`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` 第 3 稿）

八段固定；措辞硬约束；NOT_APPLICABLE / NOT_CHECKED / BLOCKED / PARTIAL 四种标准措辞；CheckResult 逐条写法与维度汇总句；抬头评估集披露行（三集哈希、claim 集状态、C_external 评估集）；Known failure modes 六槽位句式（含被排除的候选）与停线句式；C3 独立性披露句式（run 数、seed 集数、environmentId 列表）；示例 (b) 第 2 版按裁决 C4 与 R2-30。

## 10. 评估集纪律（评审意见 3 + 复审 Issue 2 / 3 + Kimi R2 §1，代码 `evaluation_sets.py`、`claim_set_ledger.py`、`trust_loop._evaluation_set_errors`）

| 集 | 用途 | 规则 |
|---|---|---|
| D_train | 训练（内部配点 ∪ 边界点 ∪ 初值点，全部是训练可见样本） | 与 dev / claim / phys **样本级**互斥；在 specHash 内 |
| D_dev | 诊断、调参、失败分析、模型 / 架构选择、早停、扰动实验、区分实验 | 可以反复看；在它上面的一致性只能支撑 C_external ≤ PARTIAL；在 specHash 内 |
| D_phys | 物理检查的积分 / 求值节点（确定性 GL 节点，公开） | 与训练点互斥；dev 级，不密封 |
| D_claim | 本版本的最终独立验证 | 预注册后由治理侧生成即 SEALED（账本事件，绑定 problemId / revision / specHash）；只在 VALIDATION 内、每版本一次 OPENED（账本事件，记 codeHash）；打开过的哈希终身不得再任 claim 集（可在新版本降级为 dev 或并入 train）；只有它上面的一致性能让 C_external PASS，且判定必须写明 claimSetSha256 |

- **样本身份**：`canonical_sha256({inputs: 全部网络输入（含参数化输入）float64 精确值, quantity: 观测量或 null})`；−0.0 折入 0.0；NaN / Inf 拒绝；kind 是元数据不是身份。"几乎相同"由预注册 `minSeparation`（欧氏距离，全输入空间）判定。
- **claim 集身份按样本（2026-09-16 协议澄清，实验 2 暴露）**：`artifactHash = canonical_sha256(清单文档)` 描述字节与元数据；`sampleSetHash = canonical_sha256(sorted(sampleId))`（`evaluation_sets.sample_set_hash`）只描述真正被评估的样本集合，对 artifactId、generator 元数据、顺序不敏感。账本事件携带 `sampleSetHash`（旧事件由持有清单者提供 `{claimSetSha256: sampleSetHash}` 解析）；OPENED 即按 sampleSetHash 烧毁（L4s），同样本换 artifactId / 换字节再 SEALED 或 OPENED 一律拒绝（L6/L7 按样本身份），一个 artifactHash 只能绑定一个 sampleSetHash（L8）；`validate_problem_definition(..., evaluation_sets, claim_set_events)` 拒绝 claim 样本已在别的 artifact 下打开过的规格。这是宪法 9.1"打开过的 claim 集"的实现修正，不改变宪法语义。**claim pool**：规格冻结前预注册多套两两样本互斥、与 train / dev / phys 互斥的 claim 集（D_claim_0…k），全部 SEALED；revision r 只能消费下一套仍 SEALED 的集，G5 FAIL 后该集 BURNT，下一次 G5 必须用下一套；不得看着 D_claim 调参。
- **"打开"的操作**（Kimi R2 §1.4，任一即 OPENED）：在 D_claim 坐标上评估任何模型输出 / 残差 / 导数；把 D_claim 坐标载入任何训练 / 诊断 / 绘图 / 统计进程；以模型在 D_claim 上输出的任何函数作为任何决策的输入；解封 / 导出 claim artifact。不构成打开：哈希比对、账本追加、生成期互斥证明。
- **账本**（L1–L7）：eventId = 除 eventId 外全部字段（含 prevEventId）的规范化哈希；链完整；时间单调；SEALED 先于 OPENED 且 specHash 一致；OPENED 必记 codeHash；同一哈希终身只 OPENED 一次；同一 (problemId, revision) 只 OPENED 一次；OPENED 后永不再 SEALED。文档的 claimSetStatus / claimSetOpenedAtRevision / claimSetHistory 必须等于账本推导值；ClaimGateDecision 必须引用 ledgerHead。保证的是可检测性，不是不可篡改性。
- **信息流不变量**（DeepSeek R2 §3）：对任何发生在本版本最终验证之前、且影响本版本 claim 或模型 / 规格 / 超参选择的决策 f，cond(f) ∩ D_claim = ∅；唯一合法以 D_claim 为条件的决策是 C_external 的最终判定，且只发生一次。在 D_claim 上计算任何聚合统计（均值、通过率）也算打开；"人看了报告再做决定"也是一条信息路径。可判定检查项：① 数据血缘（训练 / 诊断进程引用的 setId 不含当前 D_claim）；② 密封台账（即账本，OPENED 的集合在下一版本预注册前必须已 burnt）；③ 决策审计（每个 Gate / claim 决策记录 inputsHashes，盲有效 ⇔ 与已打开 claim 哈希无交集）；④ 时序（预注册时间戳先于任何 OPENED 事件，账本 L2 / L3）；⑤ 若当前 D_claim 曾以任何理由被提前打开（账本上 OPENED 事件不在 VALIDATION 阶段），本版本 C_external 不得 PASS——与"只在 D_claim 上可 PASS"不冲突，是它的补充：打开必须既在 claim 集上、又在正确阶段。①③ 的运行期断言为 R3。
- **单机场景的密封存储**（Kimi R2 §1.4，用户 2026-09-15 同意队长选型）：claim 集坐标文件放在工作区之外的治理目录，由治理账户持有、仅该账户可读，写一次；训练与诊断进程以研究者账户运行、无读权限；研究者侧只持有 {claimSetSha256, n_points, 分布族描述}。不采用加密文件：单机上密钥与数据同处一机，加密只增加密钥管理而不增加治理保证；权限目录的每次读取可留审计痕迹。
- **需要再改实现时**（Kimi §1.6 五步）：revision + 1 → 旧哈希在账本上已 burnt → 治理侧重新抽取新 claim 集并 SEALED → 按状态机重跑受影响 Gate → 新版本最终验证时再 OPEN 新集。触发条件由哈希机械定义：specHash 或 codeHash 任一改变。

## 11. 执行环境身份与 Gate 6（复审 Issue 4 + Kimi R2 §4，代码 `EnvironmentFingerprint` / `environment_id` / `independent_environments` / `reproduction_status`）

- 强字段（任一不同 ⇒ 独立环境）：machineId（硬件身份指纹，不是 hostname）、osFamily、acceleratorClass（cpu-only 或 GPU 型号）、frameworkVersion（major.minor）、blasBackend、dependencyLockHash、installationId（venv / conda 前缀 id，或容器镜像摘要）。弱字段（单独不同不构成新环境）：osVersion、pythonVersion（patch）、acceleratorDriver。不入身份：hostname、用户名、工作目录、wall-clock、并发数、GPU 序列号、内存容量、CPU 核数。
- environmentId = 强字段的规范化哈希；独立 ⇔ environmentId 不同。C3 的"≥ 2 个环境"与 G6 的"独立环境"用同一个函数。
- 案例裁定：同机不同独立安装 → 独立（最弱可接受形式）；同机同镜像两容器 → 同一环境；不同机器同 lockfile → 独立；集群两节点 → machineId 不同即独立；不同 OS / 加速器 → 独立。
- codeHash = 按 path 排序的 codeManifest[{path, sha256}] 的规范化哈希；清单范围随规格预注册（残差装配、AD 封装、缩放、采样器、边界 / 法向、几何掩码、网络结构、优化器与日程、loss 权重、评估与物理检查代码、依赖锁文件；文档 / 报告 / 资产不入）；工作区脏（未提交改动）→ 无有效 codeHash → 不得计为 qualified run。
- G6：C_repro PASS = 同 specHash 同 codeHash、独立环境、不同 seed 集的复现落入预注册容差；同环境或同 seed 集 → BLOCKED（协议未执行）；执行了但落在容差外 → FAIL。
- run 登记表（Kimi §4.4）：runId · problemId@revision · specHash / codeHash · environmentId + 强字段摘要 · seedSetId + N + 账簿引用 · D_dev 哈希 / claimSetSha256 · T1–T10 引用 · G4 统计 · 物理检查引用 · C_external · Gate 结论 · 日志与 artifact 指针。
