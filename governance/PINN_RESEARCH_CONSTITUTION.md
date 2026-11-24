# 《Leo AI PINN 闭环科研宪法》

**Leo AI Constitution for Closed-Loop PINN Research**

| 字段 | 值 |
| --- | --- |
| Version | 1.2 |
| Status | **CONSTITUTIONAL / ACTIVE** |
| Effective Date | 2026-09-04（1.0）；2026-09-15（1.1，修正案 A-0001）；2026-09-15（1.2，修正案 A-0002） |
| Scope | Leo AI 中所有 Physics-Informed Neural Network（PINN）及其衍生科学计算研究流程 |
| Authority | Highest scientific-governance authority within the PINN subsystem |
| Canonical Source | `LeoAIStudio-build/governance/PINN_RESEARCH_CONSTITUTION.md` |
| Amendment Log | `LeoAIStudio-build/governance/AMENDMENTS/` |

---

## 文件元数据（非条款）

以下为本文件自身的存放与副本规则。它描述文件的物理权威性，不是科学条款；但对它的任何修改同样必须走第六十条的修宪程序。

1. **唯一 canonical source** 为 `LeoAIStudio-build/governance/PINN_RESEARCH_CONSTITUTION.md`。该仓库受 git 版本控制，因此第二十六条（不可覆盖证据）与第六十条（修宪留痕）在物理层面可被强制。
2. 成品包 `LeoAIStudio/` 如需展示本宪法，**只允许生成只读副本**。只读副本必须在文件头部标明自己是副本以及 canonical 路径。
3. **禁止从任何副本反向修改 canonical 文件。** 副本与 canonical 冲突时，一律以 canonical 为准，副本按错误处理并重新生成。
4. 成品包由 `assemble.ps1` 重建时会被整体替换，因此副本天然是易失的。任何只存在于副本中的内容视为不存在。
5. **版本 1.1（2026-09-15）由修正案 A-0001（`AMENDMENTS/A-0001-trust-loop-r1.md`，ACCEPTED）修订。** 新增或改写的条款在正文里以 **【A-0001】** 标注；机器可执行形式在 `pinn/governance/`（`trust_vector.py`、`trust_loop.py`、`evaluation_sets.py`、`claim_set_ledger.py`、`state_machine.py` 与七份 schema），协议起点在 `PINN_TRUST_PROTOCOLS_R1.md`。按第六十章，在 1.0 生效期间运行的实验仍按 1.0 审计；1.1 生效时没有任何 run 处于 VALIDATION 之后的状态。
6. **版本 1.2（2026-09-15）由修正案 A-0002（`AMENDMENTS/A-0002-admissible-matrix-r2.md`，ACCEPTED）修订。** 新增或改写的条款以 **【A-0002】** 标注；机器可执行形式在 `state_machine.py`（按版本分表的可接受矩阵与命名义务）、`trust_loop.py`（诊断记录与症状覆盖）、`amendments.py`（登记簿不变量 R1–R5）、`prelock.py`（第七项检查）与 `diagnosis-record.schema.json`。1.2 生效时没有任何 run 处于 FAILURE_RECORDED 之后的状态，没有任何 DiagnosisRecord 存在；绑定 1.1 的 run 仍按 1.1 的矩阵审计。

### 本宪法生效后的效力声明

本文件不是建议，不是 README，不是开发说明，而是 Leo AI 所有 PINN 科研功能、Agent 行为、实验执行、验证、报告和未来扩展都必须遵守的最高级科研规则。

自本文件生效之日起：

- 任何 Implementation Plan、Feature Plan、Prompt、Agent 指令、自动化流程、ScientificSpec、实验代码、训练脚本、报告生成逻辑，如果与本宪法冲突，**本宪法优先**。
- **不得为了让某次实验 PASS 而临时降低本宪法标准。**
- **不得未经明确修宪程序修改本文件。**

---

## 序言

Leo AI 的 PINN 系统不是"训练出一条看起来合理的曲线"的工具，也不是"把 PDE 写进 loss 后让神经网络拟合"的演示系统。

它的目标是：

> 建立一个从科学问题定义、数学规格化、基线构造、PINN 实现、训练、独立验证、失败诊断到科学结论的完整可审计闭环。

因此，Leo AI 对 PINN 结果的基本态度必须始终是：

$$
\boxed{
\text{Optimization success}
\neq
\text{Numerical correctness}
\neq
\text{Scientific validity}
}
$$

尤其：

$$
\boxed{
\text{Low Training Loss}
\not\Rightarrow
\text{Correct PDE Solution}
}
$$

任何 PINN 结果，除非通过独立验证，否则不得被描述为：

- "求解成功"
- "得到正确解"
- "精度较高"
- "优于基线"
- "验证了某物理规律"
- "证明某方法有效"

训练结束仅意味着：

> 一个优化过程已经完成。

它不自动产生科学结论。

---

## 第一章：基本原则

### 第一条：科学问题先于模型

任何 PINN 实验必须先存在明确、版本化、可审计的 ScientificSpec。

禁止先写网络、先训练、再倒推自己到底解了什么问题。

顺序必须是：

$$
\text{Scientific Question}
\rightarrow
\text{Mathematical Specification}
\rightarrow
\text{Reference/Baseline}
\rightarrow
\text{PINN}
\rightarrow
\text{Validation}
\rightarrow
\text{Claim}
$$

而不是：

$$
\text{PINN}
\rightarrow
\text{Loss decreases}
\rightarrow
\text{Find explanation}
$$

### 第二条：规格冻结原则

当一个实验进入正式执行阶段后，以下内容必须冻结：

- 控制方程；
- 定义域；
- 初始条件；
- 边界条件；
- 参数；
- 单位；
- 无量纲定义；
- 输出变量；
- 目标物理量；
- reference solution；
- validation metrics；
- acceptance thresholds。

实验失败后，可以修改这些内容，但修改必须产生新的：

```
ScientificSpec version
```

或新的：

```
ExperimentRun
```

**不得静默修改原实验定义。**

---

## 第二章：证据等级

任何科学结论必须明确其证据等级。

### Level A：Exact / Manufactured Reference

优先级最高。包括：

- 解析解；
- 制造解；
- 可解析 ODE/PDE benchmark；
- 具有严格已知解的问题。

如果某问题可以合理构造制造解，但系统从未通过制造解测试，不得直接声称复杂问题实现可靠。

### Level B：Numerically Converged Reference

没有解析解时，可以采用独立数值方法，例如：

- FDM；
- FEM；
- FVM；
- spectral method；
- verified CFD solver。

但参考解必须至少具有合理的：

- 网格独立性证据；
- 时间步独立性证据（若适用）；
- solver convergence；
- numerical residual information。

未经收敛分析的数值结果不得自动称作"ground truth"。应称为：

```
numerical reference
```

### Level C：Trusted Published Benchmark

如果解析解和独立数值参考均不可获得，可以采用公开 benchmark。但必须记录：

- 文献；
- 方程；
- 参数；
- 几何；
- nondimensionalization；
- boundary conditions；
- comparison quantity。

只有高度一致的 benchmark 才能用于定量验证。

### Level D：No Independent Reference

没有独立参考解时，实验必须明确标记：

```
EXPLORATORY
```

此时可以研究：

- residual behavior；
- stability；
- conservation；
- parameter trend；
- qualitative structure。

但不得声称：

> "PINN 得到了正确解。"

---

## 第三章：闭环状态机

任何正式 PINN 项目必须进入统一状态机。

```
DRAFT
  │
  ▼
SPEC_LOCKED
  │
  ▼
BASELINE_VERIFIED
  │
  ▼
IMPLEMENTATION_VERIFIED
  │
  ▼
TRAINING_COMPLETED
  │
  ▼
VALIDATION
  │
  ├──────── PASS ───────► REPRODUCIBILITY_CHECK
  │                              │
  │                              ▼
  │                           ACCEPTED
  │
  └──────── FAIL ───────► FAILURE_RECORDED
                                  │
                                  ▼
                              DIAGNOSED
                                  │
                                  ▼
                               REVISED
                                  │
                                  └────► 回到对应上游 Gate
```

禁止：

```
TRAINING_COMPLETED
        ↓
      ACCEPTED
```

训练结果不得绕过 Validation。

### 3.1 失败分流分两层【A-0001】

状态集合不变。FAILURE_RECORDED → DIAGNOSED 必须产出一份 DiagnosisRecord，分两层：

1. **FailureSignature**（观察到什么，只是证据，不决定路由）：`sPdeResidual`、`sBcResidual`、`sConservation`、`sPinnCfd`、`sSeedSensitive`、`sLocalizedError`。
2. **RootCauseClass**（区分实验找到什么，决定重入的 Gate）：`rSpecDefect`、`rDataDefect`、`rSingularityTreatment` → G1；`rReferenceDefect` → G2；`rImplementationDefect` → G3；`rCapacityLimit`、`rOptimizationFailure`、`rSamplingDeficiency` → G4；`rUndetermined` → STOPPED_THE_LINE，交人工。

每个症状可以被命名的根因是一张**封闭的可接受矩阵**（`state_machine.admissible_root_causes(constitutionVersion)`，按宪法版本分表；例如 `sLocalizedError` 在 1.2 下可诊断为奇异性处理、参考解局部失真、实现、容量、优化、采样、规格七类之一【A-0002】，不得默认为实现）。**根因是排除后剩下的，不是挑选的**：诊断必须附症状证据与区分实验记录 `discriminatingExperiment{experimentId, evaluationSet = dev, excludes{其它每一个可接受根因: 排除它的实验与观察}}`；任何可接受的其它根因没有排除记录，就不得命名根因。`rUndetermined` 只需 experimentId。重入 Gate k 时，k 及其下游的可信度向量维度（含 BLOCKED）全部重置为 NOT_CHECKED，下游 Gate 按顺序重跑，不得跳过。同一规格的诊断循环最多 3 轮，第 4 次 FAIL 直接 STOPPED_THE_LINE；轮次的键是 (problemId, specHash)，specHash 不含 revision，空升版不重置轮次。第二十二章的 Failure Taxonomy 继续作为描述性分类使用；路由只按 RootCauseClass。

### 3.2 可接受矩阵的扩展、命名义务、症状覆盖与版本隔离【A-0002】

1. **八格扩展**（1.1 → 1.2）：`sBcResidual → rCapacityLimit`、`sPinnCfd → rCapacityLimit`、`sLocalizedError → rSpecDefect`、`sPinnCfd → rSamplingDeficiency`、`sSeedSensitive → rImplementationDefect`、`sSeedSensitive → rSpecDefect`、`sPdeResidual → rSingularityTreatment`、`sBcResidual → rSingularityTreatment`。根因 → Gate 映射不变。矩阵范围是 **forward-problem MVP**（`state_machine.MATRIX_SCOPE`，`DiagnosisRecord.problemClass = forward`）：正向问题里观测数据不进入 PDE 算子，`sPdeResidual / sConservation → rDataDefect` 不可接受是范围决定；逆问题需要自己的修正案与矩阵。空格分类：IMPOSSIBLE（不涉及参考解计算的四个症状 → 参考解）、OUT_OF_SCOPE（正向 → 数据）、UNSUPPORTED（sConservation / sSeedSensitive → 奇异性）。
2. **结构化命名义务**（`discriminatingExperiment`）：命名 `rCapacityLimit` 或 `rSamplingDeficiency` 必须附**受控干预** `intervention{factor, changed = [唯一允许改动的控制项], heldFixed ⊇ 其余全部控制项, levels ≥ 3 档、每档 ≥ 3 seed、逐档中位误差严格下降}`，容量另需 `optimizationDiagnosticsClean = true`——单次加大网络或加密采样后变好不是因果证据。命名 `sSeedSensitive → rImplementationDefect` 必须附 **P33 同 seed 确定性重放** `determinismReplay{sameSeedRuns ≥ 2, maxDivergence > epsilonDet, defectLocated}`；重放一致则实现非确定性被排除。命名 `sSeedSensitive → rSpecDefect` 必须附 **P34 可识别性记录** `identifiability{ambiguityType, claimRequiresUniqueEvaluation = true, specResolvesAmbiguity = false, ambiguityIntent = unintended}`：仅当 seed 变化暴露的是**非预期的**不可识别性或未消解的解等价，且冻结 Claim 需要唯一可评估目标而规格没有消除它，才是规格缺陷；合法多解（分支感知 Claim、有意多解研究、已定规范的规格）不是缺陷，证据不能判定是否有意 → `rUndetermined` 停线。`excludes` 义务随矩阵扩张：命名任一根因必须排除所解释症状的**每一个**其它可接受根因。
3. **症状覆盖不变量**：DiagnosisRecord 列出 `observedSignatures`（全部观察到的症状，含主症状）与 `explainedSignatures ⊆ observedSignatures`（本条记录解释的症状，默认 = 主症状）；`excludes` 覆盖所解释症状候选集的并集。一个失败可以有多条记录（不同症状归于不同根因），记录集合必须满足（`trust_loop.diagnosis_coverage_errors`）：同属一个失败、列出相同的 observedSignatures、解释集合的并集等于观察集合、每个症状恰好被一条记录解释。同一症状被两个根因同时声称是矛盾——排除纪律下两个都成立就谁都不能命名，记 `rUndetermined` 并停线；本版本不定义单症状的多因归因。多条 DIAGNOSED 记录重入取最小的 Gate（`earliest_route`），下游全部重跑。"只登记候选集最小的症状"由覆盖不变量封住。
4. **运行时版本隔离**：治理语义是宪法版本的函数，不是仓库最新代码。矩阵与命名义务按版本分表（`ADMISSIBLE_ROOT_CAUSES_BY_VERSION`、`NAMING_OBLIGATIONS_BY_VERSION`），入口只接受 `SUPPORTED_CONSTITUTION_VERSIONS` 内的版本；`diagnose`、`discriminating_experiment_errors`、`validate_diagnosis_record` 必须声明宪法版本，DiagnosisRecord 必填 `constitutionVersion`。PROPOSED 修正案的格与义务在其版本生效前对任何入口不可达；旧版本的运行时行为不因新修正案的起草而改变。

---

## 第四章：Gate 状态定义

Gate 状态只能使用：

### PASS

全部 MUST 条件均已满足，并存在完整证据。

### FAIL

Gate 已执行，但至少一个 MUST 条件未满足。

### BLOCKED

上游 prerequisite 未满足，因此当前 Gate 不得执行。

### PARTIAL

仅用于内部诊断信息。PARTIAL 不具有推进状态机的权限。

因此：

$$
\boxed{
PARTIAL \neq PASS
}
$$

任何关键 Gate 为 PARTIAL 时，下游正式科学 Gate 必须保持 BLOCKED。

禁止使用：

- basically passed；
- mostly passed；
- almost passed；
- seems okay；
- visually correct；

代替正式 PASS。

### 4.1 可信度向量维度状态与检查适用性【A-0001】

四个 Gate 状态不变。在 Gate 状态之外，另设**可信度向量维度状态** `TrustStatus = {PASS, PARTIAL, FAIL, BLOCKED, NOT_CHECKED}`：NOT_CHECKED 只表示"该维度对应的检查尚未执行"，它**不是 Gate 状态**。维度下的每项检查是一条 `CheckResult{checkId, applicability, status?, reason, evidence}`，其中 `Applicability = {APPLICABLE, NOT_APPLICABLE}` 是独立类型：NOT_APPLICABLE 表示该问题不承担这项检查义务，必须写明缺失的物理或数学前提，**没有 status**，不进入 meet。维度状态 = 其全部 APPLICABLE 检查的 meet（取最弱）。

**INV-A1**：每个维度至少承担一项 APPLICABLE 检查。"检查清单非空但全部 NOT_APPLICABLE"不是一种维度状态，而是非法登记（规格的检查注册表不完整），校验器拒绝；没有登记任何检查才是 NOT_CHECKED。适用性在 SPEC_LOCKED 时随规格登记（第五章 `checkApplicability`，进入 specHash），之后不得按结果改标；TrustVector 中已执行的维度必须与注册表**逐项一致**展示检查，不得漏列、多列或改标。维度 status 不得高于其 APPLICABLE 检查的 meet；低于 meet 必须在 notes 说明（人工只能压低）。Gate 结果为 PARTIAL 或 BLOCKED 时状态机不推进；FAIL 一律进入 FAILURE_RECORDED，禁止就地重训。

---

## 第五章：ScientificSpec

每个研究问题必须产生唯一且版本化的：

```
ScientificSpec
```

至少包含：

```
specId
version
title

scientificQuestion

equations
dependentVariables
independentVariables

domain
geometry

initialConditions
boundaryConditions

parameters
units

dimensionalForm
nondimensionalForm

referenceScales

assumptions

targetQuantities

referenceSolution

trainingDomain
validationDomain

validationMetrics

acceptanceCriteria

knownSingularities
knownNumericalRisks

createdAt
lockedAt
```

### 5.1 ProblemDefinition 契约与方法身份【A-0001】

层 1 的机器契约是 `ProblemDefinition`（`pinn/governance/schemas/problem-definition.schema.json` 1.2，校验 `trust_loop.validate_problem_definition`），在上表之外至少还包含：`revision`（文档版次）、`checkApplicability`（检查注册表，见 4.1）、`preregistration{errorNorm, epsilonSpec, seedRuns, seedFactors, worstSeedFactor, dispersionLimit, qoiBand?}`、`evaluationSets{train, dev, claim, phys?, minSeparation?, claimSetStatus, claimSetOpenedAtRevision?, claimSetHistory}`。

**specHash 是方法身份**：除 `specHash`、`revision` 与 claim 集状态字段（`evaluationSets.claim`、`claimSetStatus`、`claimSetOpenedAtRevision`、`claimSetHistory`）之外全部字段的规范化哈希（序列化沿用 `canonical.py` 的唯一规则）。打开 claim 集不改变 specHash；train / dev 集、阈值、seed 协议、适用性、参考解等级都在哈希内。FROZEN 后任何在哈希内的字段变更即哈希失配，旧哈希的全部下游 artifact 标记 stale。claim 集通过第九章的账本绑定到 (problemId, revision, specHash)。

---

## 第六章：数学一致性 Gate

在任何训练开始前，Leo AI 必须完成数学审计。至少检查：

### 1. 方程数量与未知量数量

避免欠定或过定问题。

### 2. Boundary / Initial Conditions 完整性

不得因为神经网络"好像能学出来"而允许数学上不完整的问题。

### 3. 单位一致性

每一个有量纲方程必须通过 dimensional consistency check。

### 4. 无量纲化一致性

任何：

$$
Re,\ Pe,\ Wi,\ Pr,\ Ma,\ Ra,\dots
$$

必须明确采用什么 characteristic scale。

禁止出现两个模块分别采用不同：

$$
U,\ L,\ T
$$

却仍称为同一参数。

### 5. 坐标与几何约定

坐标原点、方向、domain extent、reference length 必须冻结。

### 6. 符号一致性

例如：

$$
\tau_{xy}
$$

不能在不同模块分别表示不同应力定义。

---

## 第七章：Baseline 原则

PINN 不能自己证明自己。因此：

$$
\boxed{
PINN \text{ output cannot be its own reference}
}
$$

正式定量验证必须尽可能存在独立计算路径。例如：

```
ScientificSpec
       │
       ├──── PINN implementation
       │
       └──── Independent reference solver
```

两者最终只在 validation 层相遇。

### Reference Independence Rule

不得使用 PINN 输出：

- 调整 reference solver；
- 修正 baseline；
- 选择 reference timestep；
- 调整 reference mesh；

从而让 baseline 更接近 PINN。反之亦然。

---

## 第八章：Implementation Verification

在训练复杂 PDE 之前，PINN implementation 必须通过最低实现验证。至少验证：

### Autograd

导数计算符合预期。

### Residual

PDE residual 的符号、系数、变量对应正确。

### Boundary Operator

Dirichlet / Neumann / Robin / periodic / traction 等边界实现正确。

### Coordinate Mapping

物理坐标与网络坐标一致。

### Scaling

输入、输出、residual scaling 明确。

### Manufactured Solution

如果可行，将已知解析解代入 residual。应满足：

$$
R[u^*] \approx 0
$$

若解析解代入 residual 都不能得到接近零的值：

$$
\boxed{
\text{TRAINING MUST NOT START}
}
$$

---

## 第九章：训练数据与验证数据隔离

PINN 虽然通常不是传统监督学习，但仍必须实行数据隔离。至少定义：

```
training collocation set
training boundary set
adaptive sampling pool
diagnostic set
final validation set
```

Final validation points 不得用于：

- optimizer；
- adaptive sampling；
- early stopping；
- loss weighting；
- architecture selection；
- hyperparameter tuning。

否则发生：

```
validation leakage
```

### 9.1 三分评估集、样本级互斥与 claim 集账本【A-0001】

数据分三份：**D_train**（训练可见样本：内部配点 ∪ 边界点 ∪ 初值点）；**D_dev**（诊断、调参、失败分析、模型与架构选择、早停、扰动实验、区分实验都只准看它）；**D_claim**（预注册后密封 SEALED，只在本版本最终独立验证时打开 OPENED，记录版本号）。物理检查的求值节点 **D_phys** 可选登记，与训练点互斥。

**互斥是样本级的，哈希不同不是证据。** 每个评估集是一份样本清单（`evaluation-set.schema.json`），其规范化哈希就是规格登记的 artifact 哈希。样本身份 = 规范化哈希({inputs: 全部网络输入坐标（含参数化输入）的 float64 精确值, quantity: 观测量或 null})，−0.0 折入 0.0，NaN / Inf 拒绝；kind（interior / boundary / initial / observation）是元数据不是身份。要求 训练可见样本 ∩ (D_dev ∪ D_claim ∪ D_phys) = ∅，D_dev ∩ D_claim = ∅。"坐标几乎相同"不是身份问题，由预注册的 `minSeparation`（进 specHash，欧氏距离，全输入空间）机械判定。

**claim 集状态由账本推导，不由文档声明。** 账本 `ClaimSetEvent` 是哈希链：eventId = 除 eventId 外全部字段（含 prevEventId）的规范化哈希。不变量：链完整；时间单调；SEALED 先于 OPENED 且 specHash 一致；OPENED 必记 codeHash；同一 claim 集**终身只 OPENED 一次**（跨版本、跨问题）；同一 (problemId, revision) 只 OPENED 一次；OPENED 后永不再 SEALED。文档的 claimSetStatus / claimSetOpenedAtRevision / claimSetHistory 必须等于账本推导值；ClaimGateDecision 必须引用账本头。账本给出的保证是**可检测性**（删除、重排、改写任一事件都使后续 eventId 失配，篡改账本就必须同时伪造人工终审阅读的决策），不是密码学不可篡改。打开过的 claim 集在任何版本不得再密封、不得再任 claim 集；可在新版本降级为 dev 或并入 train。**C_external 只有在 D_claim 上评估才能 PASS**，判定必须写明 claimSetSha256；在 D_dev 上最多 PARTIAL。"打开"包括在 D_claim 上计算任何聚合统计，以及人看了结果再做决定。

---

## 第十章：Training Gate

Training Gate 只能证明：

> 优化过程完成。

它不得证明：

> PDE 解正确。

每次正式 Run 至少记录：

```
runId
specId
codeVersion
commitHash

architecture
activation

optimizer
learningRate
scheduler

lossDefinition
lossWeights

samplingStrategy

nInterior
nBoundary
nInitial

randomSeed

epochs
iterations

hardware
softwareEnvironment

wallTime

lossHistory

gradientDiagnostics

terminationReason
```

### 10.1 多 seed 协议【A-0001】

1D 案例 N ≥ 10；2D 过渡期允许 N = 5 但 C_train 封顶 PARTIAL；N < 5 视为协议未执行（BLOCKED）；N 与 ε_spec 预注册，事后不得改。seed 拆为初始化 / 采样 / batch 顺序三因子，三元组先入 append-only 账簿再启动 run；seedSetId = 排序去重后 seed 值的哈希，改名不改身份。报告中位数、IQR、**最差 seed**，最好 seed 永不进入判定。达标次数 k（在 D_dev 上、预注册范数与 ε_spec）：k/N < 0.8 → FAIL；0.8 ≤ k/N < 0.9 → PARTIAL；k/N ≥ 0.9 → PASS；最差 seed > 3ε_spec → 封顶 PARTIAL；中位数 > ε_spec → FAIL；分项 loss 下降而误差不降判优化假象 FAIL。离散度规则写成 **IQR > dispersionLimit × median**（乘法比较，全程无除法）：median = 0 且 IQR = 0 不封顶，median = 0 且 IQR > 0 封顶 PARTIAL，不引入分母下限。NaN / Inf 的 run 是发散 run：计入 N、不计入 k、使最差 seed 发散；负误差是调用方错误。这些线认证的是"大概率可靠"，PASS 不是对 p ≥ 0.9 的高置信认证（N = 10、k = 9 只能以 95% 置信认证 p ≥ 0.55）；提高置信只能在预注册时声明更大的 N。

---

## 第十一章：禁止单一 Total Loss

任何多项 PINN loss：

$$
\mathcal L
=
\lambda_f L_f
+
\lambda_b L_b
+
\lambda_i L_i
+\cdots
$$

必须分别保存：

$$
L_f,\quad L_b,\quad L_i,\quad \dots
$$

禁止只记录：

$$
\mathcal L
$$

因为 total loss 可能掩盖某一约束完全失败。

---

## 第十二章：Loss 不是精度指标

以下语句在 Leo AI 中属于非法科学推断：

> "Loss 已降到 $10^{-6}$，所以结果非常准确。"

Training loss 仅用于优化诊断。数值正确性必须来自独立 validation metrics。

---

## 第十三章：ValidationReport

每一次正式训练完成后，必须生成：

```
ValidationReport
```

至少包含：

```
validationId
runId
specId

referenceType
referenceVersion

evaluationGrid
evaluationSeed

metrics

boundaryValidation
initialConditionValidation
pdeResidualValidation

conservationValidation

quantityOfInterestValidation

fieldwiseErrors

visualComparisons

passCriteria

failedCriteria

finalStatus
```

### 13.1 Claim Gate 的人读输出【A-0001】

Claim Gate 的人读报告固定为八段：Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims / Provenance / Scope（模板 `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`）。可信度向量六维逐维展示；每条检查按 CheckResult 逐条展示，NOT_APPLICABLE（不承担）、NOT_CHECKED（没查）、BLOCKED（不能查）、PARTIAL（查了不充分）四者措辞必须区分；Known failure modes 必须写出 症状 → 根因 → 区分实验（含被排除的候选） → 回到的 Gate；必须披露三个评估集的哈希、C_external 用的是 dev 还是 claim 集、claim 集哈希与状态（SEALED / OPENED@revision）、账本头、C3 的 run 数 / seed 集数 / 环境数。禁止单一百分比、"基本通过"、"总体可信"、"平均等级"、"待验证"等措辞。报告是机器判定（TrustVector、ClaimGateDecision、DiagnosisRecord、账本）的只读渲染，文本不得比机器判定更宽松，冲突以机器记录为准。

---

## 第十四章：默认数值误差指标

对于参考解：

$$
u^*(x_i)
$$

PINN：

$$
u_\theta(x_i)
$$

至少建议计算：

### Relative $L_2$

$$
E_{L_2}
=
\sqrt{
\frac{
\sum_{i=1}^{N}
|u_\theta(x_i)-u^*(x_i)|^2
}{
\sum_{i=1}^{N}
|u^*(x_i)|^2+\epsilon
}
}
$$

### Absolute $L_\infty$

$$
E_\infty
=
\max_i
|u_\theta(x_i)-u^*(x_i)|
$$

必要时计算相对：

$$
E_{\infty,\mathrm{rel}}
=
\frac{
\max_i |u_\theta-u^*|
}{
\max_i|u^*|+\epsilon
}
$$

---

## 第十五章：多物理变量不得被 aggregate error 掩盖

例如网络输出：

$$
u,v,p,T,\tau_{xx},\tau_{xy},\tau_{yy}
$$

必须分别报告误差：

$$
E_u,
E_v,
E_p,
E_T,
E_{\tau_{xx}},
E_{\tau_{xy}},
E_{\tau_{yy}}
$$

禁止用一个 aggregate score 掩盖某一个场完全错误。

---

## 第十六章：PDE Residual Holdout

必须在未参与训练的点上重新计算 PDE residual。例如：

$$
E_R
=
\sqrt{
\frac1N
\sum_{i=1}^{N}
R(x_i)^2
}
$$

Training residual 和 holdout residual 必须分开记录。

---

## 第十七章：Boundary Validation

所有边界必须单独验证。

例如 Dirichlet：

$$
E_{BC}
=
\max_{x\in\partial\Omega}
|u_\theta(x)-g(x)|
$$

Neumann：

$$
E_N
=
\max_{x\in\partial\Omega}
\left|
\frac{\partial u_\theta}{\partial n}
-
q
\right|
$$

复杂问题不得只报告 interior error。

---

## 第十八章：物理守恒优先

如果问题存在守恒律，则 Validation 必须尽可能验证。

例如不可压缩流：

$$
\nabla\cdot \mathbf u =0
$$

以及控制体质量守恒：

$$
\dot m_{in}
-
\dot m_{out}
\approx0
$$

热问题：

$$
Q_{in}
-
Q_{out}
-
Q_{stored}
\approx0
$$

若局部误差很低但关键守恒严重违反：**不得判定 ACCEPTED。**

---

## 第十九章：Quantity of Interest

最终科学目标往往不是全场误差，而是某些 QoI。例如：

- pressure drop；
- drag；
- wall shear stress；
- reattachment length；
- Nusselt number；
- maximum temperature；
- stress integral；
- flow rate。

因此 ScientificSpec 必须提前声明：

```
targetQuantities
```

不得训练结束后只挑"看起来效果最好"的指标进行报告。

---

## 第二十章：Acceptance Criteria 必须事前声明

每个正式实验必须在训练之前确定 acceptance criteria。例如：

```
relative_L2(u) < threshold_A
boundary_error < threshold_B
mass_conservation_error < threshold_C
QoI_error < threshold_D
```

阈值根据问题特点设定。本宪法不规定所有 PDE 使用同一个数值阈值。但规定：

$$
\boxed{
\text{Thresholds must be declared before final validation.}
}
$$

禁止：先得到误差 4.7%，然后把 PASS 标准改成 5%。

这种行为属于：

```
post-hoc acceptance manipulation
```

---

## 第二十一章：失败必须显式存在

失败不是需要隐藏的数据。失败是研究证据。

任何正式失败 Run：

- 不得删除。
- 不得覆盖。
- 不得把失败文件换成成功版本。

必须生成：

```
FailureRecord
```

至少包括：

```
failureId
runId
gate

observedFailure

evidence

suspectedCause

alternativeHypotheses

diagnosticTests

rootCauseStatus

proposedChange

changeScope

nextRunId

createdAt
```

---

## 第二十二章：Failure Taxonomy

失败至少分为：

| 类别 | 含义 |
| --- | --- |
| `SPEC` | 数学问题或规格错误。 |
| `BASELINE` | 参考解不可靠。 |
| `IMPLEMENTATION` | PDE、BC、autograd、坐标等代码错误。 |
| `SCALING` | 尺度或无量纲化问题。 |
| `SAMPLING` | collocation 分布不足。 |
| `OPTIMIZATION` | optimizer、learning rate、gradient 等问题。 |
| `LOSS_BALANCE` | 各约束 loss 竞争失衡。 |
| `MODEL_CAPACITY` | 网络表达能力不足。 |
| `NUMERICAL` | overflow、underflow、NaN、精度等问题。 |
| `VALIDATION` | 验证协议或 metric 不充分。 |
| `INFRASTRUCTURE` | GPU、依赖、文件系统等基础设施问题。 |
| `UNKNOWN` | 证据不足，尚不能确定。 |

如果根因未知：**必须写 `UNKNOWN`。** 禁止凭直觉制造确定性。

---

## 第二十三章：失败诊断必须可证伪

禁止：

> "可能网络太小，所以我加大网络。"

作为完整诊断。

应写成：

> 假设 H1：网络容量不足。

并定义可证伪测试。例如增加容量后，如果：

$$
E_{L_2}
$$

没有显著改善，则 H1 证据减弱。

科研 Agent 必须区分：

- hypothesis；
- test；
- result；
- conclusion。

---

## 第二十四章：避免同时修改多个变量

进行 root-cause diagnosis 时，原则上每个 rescue run 应尽量只修改一个主要因素。否则：

```
change optimizer
change network
change sampling
change loss weight
```

同时发生后，即使成功，也无法判断原因。

必要时允许多项修改，但必须明确标记：

```
compound intervention
```

此类 Run 不允许用于强因果归因。

---

## 第二十五章：不可静默修复

任何 Agent 如果：

- 修改 PDE；
- 改 BC；
- 改 loss；
- 改 reference；
- 改 sampling；
- 改 network；
- 改 threshold；

必须记录。禁止：

```
silent repair
```

---

## 第二十六章：不可覆盖证据

以下内容原则上必须 immutable：

- raw stdout/stderr；
- training logs；
- checkpoints used for report；
- reference outputs；
- validation outputs；
- failure evidence；
- generated metrics；
- scientific decisions。

允许生成新版本。禁止覆盖原证据后继续声称是同一个 Run。

---

## 第二十七章：唯一 Run ID

每一次正式计算必须有唯一：

```
runId
```

任何图、表、checkpoint、report 都必须能够追溯到：

$$
\text{runId}
\rightarrow
\text{code}
\rightarrow
\text{spec}
\rightarrow
\text{environment}
\rightarrow
\text{data}
\rightarrow
\text{validation}
$$

---

## 第二十八章：环境可复现性

每个正式 Run 必须记录至少：

- OS；
- Python；
- framework；
- CUDA；
- cuDNN；
- GPU；
- dependency versions；
- git commit；
- random seed。

如果不能复现环境，结果应明确标记：

```
REPRODUCIBILITY LIMITED
```

### 28.1 RunRecord 与执行环境身份【A-0001】

正式 run 的机器契约是 `RunRecord`（`run-record.schema.json`）：runId、problemId、revision、specHash、codeHash + codeManifest、environment + environmentId、seeds + seedSetId、evaluatedOn、时间与执行者。三个身份都是**派生**的，由校验器复算，手填即拒：codeHash = 按 path 排序的代码清单（含配置与依赖锁文件）的规范化哈希；seedSetId = 排序去重后 seed 值的哈希；environmentId = 环境指纹**强字段**的规范化哈希。强字段 = {machineId, osFamily, acceleratorClass, frameworkVersion(major.minor), blasBackend, dependencyLockHash, installationId}；弱字段 = {osVersion, pythonVersion(patch), acceleratorDriver}；hostname、用户名、路径不是身份。**两个执行环境独立 ⇔ 至少一个强字段不同 ⇔ environmentId 不同**；仅弱字段不同是同一环境。同机不同独立安装 → 独立（最弱的可接受形式）；同机同镜像两容器 → 同一环境；不同机器同 lockfile → 独立；集群两节点 → machineId 不同即独立；不同 OS / 加速器 → 独立。这一个定义同时供第三十六章的 C3 与第五十四章的 Gate 6 使用。工作区有未提交改动的 run 没有有效 codeHash，不得计为合格 run。

---

## 第二十九章：随机性原则

存在随机初始化或随机采样时：单一 seed 的成功不得自动解释为算法稳定。

工程 smoke test 可以使用单 seed。但任何关于：

- robustness；
- stability；
- superiority；
- reliability；

的科学结论原则上需要多 seed 支撑。

必须同时报告：

- mean；
- standard deviation；
- best；
- worst；

并禁止只展示 best seed。**【A-0001】** 判定按 10.1 的协议：进入判定的统计量只有 k/N、中位数、IQR 与最差 seed；best 只作展示，永不进入判定。

---

## 第三十章：不得 Cherry-Pick

禁止只保留：

- 最好看的曲线；
- 最低 loss；
- 最优 seed；
- 最漂亮 checkpoint；

而隐藏失败结果。

若进行了 $N$ 次独立正式实验，报告中必须能知道：

$$
N
$$

是多少。

---

## 第三十一章：Figure 不等于 Evidence

图像是证据的表达方式，不是证据本身。

> "看起来差不多"

不得替代误差计算。

所有主要图应尽可能由可复现脚本从原始数据生成。禁止手工修改：

- 曲线位置；
- 数值点；
- axis scale；

来改善视觉结果。

---

## 第三十二章：Baseline 不得成为 Strawman

如果声称：

> PINN 优于传统方法

传统方法必须采用合理设置。禁止故意：

- 使用粗劣网格；
- 不收敛 solver；
- 错误参数；
- 不合理 timestep；

从而制造一个弱 baseline。

---

## 第三十三章：比较实验公平性

比较：

```
PINN A vs PINN B
```

或：

```
PINN vs FEM/FVM
```

必须明确：

- compute budget；
- hardware；
- stopping criterion；
- accuracy target；
- runtime definition；
- preprocessing cost。

否则只能称为：

```
descriptive comparison
```

不得称为严格 performance superiority。

---

## 第三十四章：Scientific Claim Ledger

任何最终研究结论应登记为：

```
ScientificClaim
```

至少包括：

```
claimId
statement

scope

supportingRuns
supportingEvidence

limitations

confidenceLevel

status
```

---

## 第三十五章：结论必须有限定域

任何结论都只能在已验证范围内成立。

例如实验验证：

$$
Wi \in [0,0.5]
$$

不得自动扩展为：

> "该方法适用于高 Wi 粘弹性流动。"

- 验证二维：不得自动声称三维。
- 验证层流：不得自动声称湍流。
- 验证单几何：不得自动声称一般复杂几何。

---

## 第三十六章：Claim Levels

Leo AI 应至少区分：

| 等级 | 名称 | 含义 |
| --- | --- | --- |
| **C0** | Implementation Claim | 代码能够运行。 |
| **C1** | Optimization Claim | 训练能够收敛或达到指定 loss 行为。 |
| **C2** | Numerical Accuracy Claim | 与独立 reference 在指定问题上达到预注册误差标准。 |
| **C3** | Robustness Claim | 多 seed / 参数扰动下稳定。 |
| **C4** | Comparative Claim | 对竞争方法存在公平比较证据。 |
| **C5** | Generalization Claim | 多个问题族、参数域或几何证明存在合理泛化。 |

高等级 claim 必须建立在低等级 evidence 之上。

### 36.1 可信度向量与弱链演算【A-0001】

六维向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，分别对应 G1、G3、G4、G5a、G5b、G6，每维取 TrustStatus（4.1）。只有 PASS 支持 claim：C0 需 math、impl 全 PASS；C1 再加 train；C2 与 C3 需六维全 PASS 且参考解证据等级 ≠ D，**证据等级取自冻结规格的 primary source，决策文档不得重新标注**；EXPLORATORY run 封顶 C1。**C3 另需 ≥ 5 个 independently qualified 的 SUPPORTED @ C2 run**：同一 specHash、同一 codeHash（这是"同一个方法"的定义），seed 集两两不同，执行环境至少 2 个不同（按 28.1 的同一规则）；复制的 run 不计数；seedSetId 与 environmentId 由校验器从材料复算。组合算子只有取最弱（meet）；TrustStatus 无算术结构，平均是类型错误；最弱环节报告序 FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS，并列时全部列出。ClaimGateDecision（`claim-gate-decision.schema.json` 1.2）必须携带 revision、claimSetSha256、ledgerHead，与规格、向量、账本逐项绑定：external 在 claim 集上判定过 ⇒ 账本有本版本的 OPENED 事件，且决策的 codeHash = OPENED 事件记录的 codeHash（打开 claim 集之后改代码而不升版本 = 拒绝）。allowedClaims 只能比演算更严，不能更松；weakestLink 由向量推导，不由声明。本演算只收紧 MVP 计划 §3.5 的前提矩阵，不放松。

---

## 第三十七章：Builder 与 Auditor 分离

负责实现或修改算法的 Agent 不得直接根据自己的主观判断宣布科研成功。

流程上必须区分：

| 角色 | 职责 |
| --- | --- |
| **Builder** | 负责实现。 |
| **Runner** | 负责执行。 |
| **Validator** | 负责验证。 |
| **Auditor** | 负责检查证据与 Gate。 |

这些角色可以由同一个底层 AI 模型在不同阶段承担，但逻辑职责必须分离。

**Auditor 不得为了让 Builder 的结果通过而降低标准。**

---

## 第三十八章：验证阶段禁止修改实现

进入 VALIDATION 后：Validator 只验证。

如果发现问题需要修改代码：

1. 当前 Run 判定完成。
2. 返回对应 Gate。
3. 创建新 Run。

禁止：

```
validation → 偷改代码 → 继续 validation → PASS
```

然后仍声称是原 Run。

---

## 第三十九章：Agent 不得伪造执行

如果 Leo AI 没有真正运行某条命令，不得说：

> "测试已经通过。"

如果没有实际读取某文件，不得说：

> "该文件内容正确。"

如果无法获取某证据，必须写：

```
UNVERIFIED
```

禁止根据预期结果模拟执行结果。

---

## 第四十章：Agent 不得伪造文件与指标

不得编造：

- 文件路径；
- checkpoint；
- metric；
- log；
- commit；
- hardware result；
- solver output；
- experiment result。

科研系统宁可：

```
BLOCKED
```

也不得伪造完整闭环。

---

## 第四十一章：科研日志属于正式证据

每次重要操作应进入 Research Log，包括：

- 今天做什么；
- 为什么这样做；
- 哪个假设被测试；
- 发生什么失败；
- 哪个判断被推翻；
- 修改了什么；
- 下一步为什么这么做。

日志不是宣传材料。失败、错误判断和无效尝试不得被清洗掉。

---

## 第四十二章：Result ≠ Interpretation

报告必须区分：

| 类别 | 含义 |
| --- | --- |
| **Observation** | 实际观测。 |
| **Interpretation** | 对现象的解释。 |
| **Hypothesis** | 尚未验证的猜想。 |
| **Conclusion** | 当前证据支持的结论。 |

例如 Observation：

$$
E_{L_2}
$$

在 Wi=0.5 明显增加。

不能直接改写为：

> 高 Wi 导致 PINN 必然失效。

后者需要进一步验证。

---

## 第四十三章：复杂问题必须逐级升级

从简单到复杂：

$$
\text{Exact benchmark}
\rightarrow
\text{simple PDE}
\rightarrow
\text{simple geometry}
\rightarrow
\text{complex geometry}
\rightarrow
\text{multiphysics}
$$

上一级核心实现尚未验证：不得依靠更复杂问题掩盖问题。

---

## 第四十四章：最小可验证闭环优先

新功能首先回答：

> 是否增强科学闭环？

如果一个功能：

- 更漂亮；
- 更智能；
- 更自动化；

但不能提高：

- specification；
- validation；
- reproducibility；
- auditability；
- diagnosis；

优先级不得高于闭环基础设施。

---

## 第四十五章：核心科研对象

Leo AI PINN subsystem 的核心 domain objects 至少包括：

```
ScientificSpec
BaselineRecord
ExperimentRun
ValidationReport
FailureRecord
ScientificClaim
ArtifactManifest
DecisionRecord
```

UI、Agent、自动化工作流都应围绕这些 domain object 构建。

**不得把科研状态只存在页面 DOM 或聊天历史中。**

---

## 第四十六章：ArtifactManifest

每个 Run 必须拥有 artifact manifest。例如：

```
runId

spec
sourceCode
config

trainingLog

checkpoint

prediction

referenceData

metrics

figures

validationReport

failureRecord
```

每一个 artifact 至少记录：

```
path
type
createdAt
hash
source
```

---

## 第四十七章：DecisionRecord

任何影响科学结论的重要人为或 Agent 决策，应能记录：

```
decisionId
time

question

availableEvidence

decision

reason

alternatives

consequence
```

这样未来才能回答：

> 为什么当时选这个方法？

而不是只剩最终代码。

---

## 第四十八章：推荐目录契约

建议：

```
governance/
    PINN_RESEARCH_CONSTITUTION.md
    AMENDMENTS/

specs/

baselines/

runs/
    <run_id>/
        config/
        logs/
        checkpoints/
        predictions/
        metrics/
        figures/

validation/

failures/

claims/

research_logs/
```

具体目录可以调整。但必须保持：规格、运行、验证、失败、结论相互可追溯。

---

## 第四十九章：Gate 1 — SPEC

PASS 条件：

- 方程明确；
- BC/IC 明确；
- domain 明确；
- parameter 明确；
- units 明确；
- nondimensionalization 明确；
- reference strategy 明确；
- validation metric 明确；
- acceptance criteria 明确。

否则：`FAIL`。所有下游：`BLOCKED`。

---

## 第五十章：Gate 2 — BASELINE

PASS 条件：存在可信 reference，并完成必要验证。

否则 PINN 可以做 exploratory run，但：

```
Accuracy Claim = BLOCKED
```

---

## 第五十一章：Gate 3 — IMPLEMENTATION

PASS 条件至少包括：

- autograd check；
- residual check；
- boundary operator check；
- known/manufactured solution test；
- code/config consistency。

否则：

```
Training = BLOCKED
```

---

## 第五十二章：Gate 4 — TRAINING

PASS 仅表示：训练完整执行，没有违反 execution protocol。

它可以包括：

- 正常结束；
- loss history 完整；
- 无静默 NaN；
- checkpoint 可恢复；
- logs 完整。

它不包含："结果正确"。

---

## 第五十三章：Gate 5 — VALIDATION

这是数值正确性的核心 Gate。必须至少根据问题类型检查：

- field error；
- boundary error；
- PDE holdout residual；
- conservation；
- QoI；
- comparison to reference。

所有预注册 MUST 指标通过：`PASS`。否则：`FAIL`。

**【A-0001】** Gate 5 拆为 **G5a 物理一致性 MUST 组**（守恒 / 通量平衡、能量平衡、动量收支、正定性、对称性、单调性、最大值原理、自由能 / 熵、SPD，每项按问题类型在规格里登记 Applicability）与 **G5b 独立数值验证**（与不同代码路径的独立参考在预注册范数与阈值内一致，只在 D_claim 上评估才能 PASS）。两者都在 VALIDATION 内执行，G5 PASS ⇔ G5a ∧ G5b PASS；C_physics ↔ G5a，C_external ↔ G5b；G2 未 PASS 时 C_external 记 BLOCKED。状态集合不变，不新增 PHYSICS_CHECKED 状态。

---

## 第五十四章：Gate 6 — REPRODUCIBILITY

对于正式科研结果，至少应能够：

- 从保存环境重新执行；
- 从 config 重建 run；
- 重算 metrics；
- 重绘 figures。

如果关键结果只能依赖已经遗失的运行状态：不得标记完整 reproducible。

**【A-0001】** C_repro PASS = 同 specHash 同 codeHash、**独立执行环境**（28.1 的同一规则）、不同 seed 集的复现落入预注册容差。同环境或同 seed 集的"复现"只证明确定性，是协议未执行 → BLOCKED；执行了但落在容差外 → FAIL。独立性的目的是排除单一安装 / 单一执行环境的偶然性，不是可移植性。

---

## 第五十五章：Gate 7 — SCIENTIFIC CLAIM

只有在必要的上游 Gate 全部 PASS 以后，才允许形成最终 ScientificClaim。

报告必须同时展示：

- evidence；
- scope；
- limitations；
- failures；
- uncertainty。

---

## 第五十六章：失败回流规则

如果 `Validation FAIL`，不得默认："再多训练一点"。

首先进入：

```
Failure Diagnosis
```

依次考虑：

```
Spec
Baseline
Implementation
Scaling
Sampling
Optimization
Loss balance
Architecture
Numerical stability
Validation design
```

修复哪个层级，状态机就返回哪个层级。**【A-0001】** 层级由 3.1 的 RootCauseClass 决定，根因必须以区分实验排除其余可接受候选后命名；症状不得直接路由。

---

## 第五十七章：禁止自动无限重试

Agent 不得：

```
失败 → 改参数 → 重跑 → 改参数 → 重跑
```

无限循环直到偶然出现成功结果。

任何自动 rescue 必须存在明确：

- rescue budget；
- modification policy；
- termination criterion。

超过预算：`STOP`。并生成 FailureRecord。

---

## 第五十八章：Negative Result 也是合法终点

Leo AI 必须允许最终结论为：

> 在当前条件下，该 PINN 方法没有达到预先定义的验证要求。

这是完整科研结果。

**不得因为产品想展示"成功"而继续自动调参直到得到好看的结果。**

---

## 第五十九章：禁止修改历史以制造成功

如果实验失败，不得：

- 删除失败日志；
- 改写旧报告；
- 覆盖旧 checkpoint；
- 修改旧 acceptance threshold；
- 修改旧 ScientificSpec；

来让历史记录显示为成功。

新认识必须产生：**新版本**。

---

## 第六十章：修宪制度

本宪法可以改。但只能通过正式：

```
Constitutional Amendment
```

每次修改必须产生：

```
amendmentId
oldVersion
newVersion
reason
affectedArticles
scientificJustification
effectiveDate
```

修宪必须**先于**受新规则影响的实验。

禁止在看到实验失败后，通过修宪 retroactively 将失败变成 PASS。

旧实验仍按其运行时生效的宪法版本审计。

**【A-0002】** 修正案之间的依赖机器化（`pinn/governance/amendments.py`，PRELOCK 第七项检查 `amendmentRegister`）：修正案 frontmatter 可声明 `dependsOn[{amendmentId, requiredStatus, requiredConstitutionVersion}]`。登记簿不变量：R1 编号唯一、状态 ∈ {PROPOSED, ACCEPTED, REJECTED}、版本 x.y；R2 ACCEPTED 必有日期、PROPOSED 必为 PENDING；R3 ACCEPTED 修正案构成从 1.0 出发的单链，每个 ACCEPTED 的 oldVersion 等于前一个 ACCEPTED 的 newVersion，宪法元数据声明的版本等于链尾；R4 ACCEPTED 修正案的每个依赖目标必须存在且处于要求的状态与版本；R5 ACCEPTED 的 newVersion 必须在运行时 `SUPPORTED_CONSTITUTION_VERSIONS` 内、PROPOSED / REJECTED 的不得在内——PROPOSED 修正案的语义不得泄漏到有效运行时，ACCEPTED 的必须可达。因此 `Constitution = 1.0, A-0001 = PROPOSED, A-0002 = ACCEPTED` 与"ACCEPTED 却未加入 SUPPORTED"都被拒绝。生效配方：版本行、`SUPPORTED_CONSTITUTION_VERSIONS`、三份 schema 枚举、草案重绑定、新证据文件，缺一即 PRELOCK FAIL。

---

## 第六十一章：规则优先级

如果发生冲突，优先级为：

1. PINN Research Constitution
2. Locked ScientificSpec
3. Validation Protocol
4. Experiment Plan
5. Agent Plan
6. Feature implementation
7. UI preference

低等级规则不得覆盖高等级规则。

---

## 第六十二章：Stop-the-Line Principle

当以下情况发生时：

- ScientificSpec 不完整；
- baseline 不可信；
- evidence 缺失；
- implementation verification 失败；
- validation leakage；
- artifact 丢失；
- acceptance criteria 被事后修改；
- 无法判断数据来源；
- 发现潜在科研完整性问题；

Agent 必须拥有并使用：

$$
\boxed{\text{STOP THE LINE}}
$$

即：停止继续推进下游实验。

状态：`BLOCKED`，直到问题被解决。

---

## 第六十三章：最重要的最终原则

Leo AI 的科研价值不得由：

> "它能自动跑多少实验"

衡量。而应由：

> 它能否阻止错误实验被误认为正确科学结果。

衡量。

因此，本系统永久遵守：

$$
\boxed{
\text{Correctness before Automation}
}
$$

$$
\boxed{
\text{Evidence before Conclusion}
}
$$

$$
\boxed{
\text{Validation before Acceptance}
}
$$

$$
\boxed{
\text{Reproducibility before Trust}
}
$$

$$
\boxed{
\text{Failure must remain visible}
}
$$

以及最核心的一条：

$$
\boxed{
\text{Low Loss} \neq \text{Correct Solution}
}
$$

---

## 第六十四章：Red Team 扰动三层制【A-0001】

扰动实验（协议汇编 §7 的 P1–P21）分三层：Tier-0（只评估，不重训）在任何 Claim 之前必跑；Tier-1（单次重训）在 C2 之前必跑；Tier-2（多次重训）在 C3 之前必跑。扰动只能降级或维持，且只降级矩阵指定的那一维；未跑的层对应维度记 NOT_CHECKED；跑了扰动的维度必须记录 worstCase；扰动实验与诊断的区分实验只准看 D_dev。

---

## 第六十五章：EXPLORATORY 的第二来源【A-0001】

除既有的 evidenceLevel = D 推导标记外，研究者可以把一次 run 登记为 EXPLORATORY（假设生成实验）。两种来源都把 Claim 封顶在 C1，产物不进入 ACCEPTED；在 D_dev 上产生的观察默认 EXPLORATORY；看过 D_claim 结果后萌生的新假设，本 revision 内一律 EXPLORATORY，其正式验证只能用下一 revision 的新 claim 集。晋升必须在冻结规格下重新走完整闭环，不能靠改写措辞。

---

## 第六十六章：revision 与方法身份【A-0001】

"新 revision"由哈希机械定义：specHash（方法的规格身份，5.1）或 codeHash（方法的代码身份，28.1）任一改变，revision 必须 + 1。架构、优化器、采样、loss 权重、依赖版本在 codeHash 内；PDE、BC、参考解、阈值、seed 协议、适用性、D_train / D_dev 在 specHash 内。"改了代码但语义相同"不可机器判定，因此按字节判定：codeHash 变即新版本。纯文档 / 报告改动不在任一哈希内，不需要升版。升版后：打开过的 claim 集在账本上已 burnt，必须重新预注册新 claim 集；同一 problemId 跨 specHash 出现同一 (rootCause, gate) 的诊断 ≥ 2 次，触发停线评审交人工。

---

## 附录 A：最小闭环定义

任何 Leo AI PINN 功能若要被称为：

```
Closed Loop
```

至少必须实现：

```
ScientificSpec
      ↓
Independent Baseline
      ↓
PINN Implementation
      ↓
Training
      ↓
Independent Validation
      ↓
PASS / FAIL
      ↓
Failure Diagnosis
      ↓
Revision
      ↓
Re-validation
```

少任何一个关键环节：只能叫 **pipeline**。不得叫**科研闭环**。

---

## 附录 B：MVP 基准问题

Leo AI 第一个完整闭环不使用复杂流体问题。首先使用一个具有解析解的简单 PDE，例如：

$$
-u''(x)
=
\pi^2\sin(\pi x),
\qquad
x\in[0,1]
$$

边界：

$$
u(0)=0,
\qquad
u(1)=0
$$

解析解：

$$
u^*(x)=\sin(\pi x)
$$

使用该问题完整测试：

```
Spec
Baseline
Residual
Autograd
Training
Validation
Failure injection
Diagnosis
Revision
Acceptance
Artifact tracing
```

必须主动构造错误版本，例如：

- 错 PDE 符号；
- 错 BC；
- 极低边界权重；
- 严重采样不足；
- 错误 scaling；
- 低 loss 但高 solution error；

验证 Leo AI 是否能够：**拒绝错误结果。**

只有系统能够稳定拒绝人为制造的坏解之后，才允许宣布：

> PINN scientific closed-loop MVP established.

---

## 附录 C：宪法成功标准

这套系统真正成功的标志不是：

> 一个好 PINN 被判定成功。

而是同时满足：

### Good Case

正确实现能够 **PASS**。

### Bad Case

故意制造的错误实现能够 **FAIL**。

### Ambiguous Case

证据不足时能够 **BLOCKED**，而不是猜。

即：

$$
\boxed{
\text{Accept Good}
+
\text{Reject Bad}
+
\text{Abstain When Uncertain}
}
$$

三者缺一不可。

---

*END OF CONSTITUTION v1.2（v1.0 + A-0001 + A-0002）*
