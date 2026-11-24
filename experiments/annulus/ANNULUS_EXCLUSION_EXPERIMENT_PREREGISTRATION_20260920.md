# ANNULUS EXCLUSION EXPERIMENT PREREGISTRATION（2026-09-20）

本文件在**任何排除实验执行之前**提交。冻结后不得修改：实验设计、判定规则、阈值、正控制（positive control）的通过条件。

授权：外部评审裁决（2026-09-20）item 2 与 item 4。上游：[ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md](../../docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md)。

## 0. 身份与边界

```text
类别        diagnosis-only discriminating experiments（裁决 item 2）
不是        Tier-1（Tier-1 的含义不变：Gate 5 PASS 之后对已接受结果的压力测试）
读取        D_dev / 合成夹具 / 独立参考          不读 D_claim
产生        DiagnosisRecord 的排除证据
不产生      claim、Trust 推进、Tier-1 状态、任何 claim-set 生命周期事件
```

`DAC-M0` 保持 BURNT；`DAC-M1 / M2 / M3` 保持 `NEVER_SEALED` 且不被触碰。每个实验在开始前与结束后各记录账本 sha256 与事件序列并比对。

## 1. 要排除的五个候选

`sLocalizedError` 在 Constitution 1.2 下的 admissible 集合共 7 个。`rOptimizationFailure` 是待命名的根因，`rCapacityLimit` 已由嵌套预算干预（`exp-annulus-nested-budget-r1`）用实验排除。本轮处理其余五个：

```text
rSamplingDeficiency   rImplementationDefect   rSpecDefect   rReferenceDefect   rSingularityTreatment
```

## 2. 排除的标准（贯穿全篇）

**「没有观察到缺陷」不构成排除。** 每个实验必须满足以下之一，并在报告中标明属于哪一类：

* **干预式**：改变该原因所依赖的那个变量；若该原因为真，结果必须改变。
* **正控制式**：先人为注入该原因，证明本实验**能**检出它；再在真实数据上测量，证明它不在。

任何一项若无法诚实排除，该原因保持 viable，Root Cause 保持 `UNDETERMINED`（裁决 item 5）。

## 3. `exp-annulus-dx-sampling` — rSamplingDeficiency（干预式）

待检机制：局部误差可归因于配置点集合（过稀 / 分布有偏 / 遗漏该区域）。

在 **r1 预算 120000 步**下，其余一切冻结，只读 D_dev：

| 探针 | 干预 |
|---|---|
| S1 | 配置点数 1024 → **2823**（按圆环面积匹配密度，2.76×），seed 2 的三元组 |
| S2–S4 | seed 2 的 init / batch 不变，**采样 seed 换成** `sample+901 / +902 / +903` |
| S5 | 观测量：r1 seed-2 的 120k checkpoint，逐 ACA-9 单元的**配置点计数**与逐单元 RMS 误差 |

**判定（事前冻结）**：`rSamplingDeficiency` 被排除，**当且仅当**以下三条同时成立：

```text
(a) S1 的 ACA-9 仍 > 1e-3            —— 2.76 倍密度救不回来，密度不是杠杆
(b) 热点单元的配置点计数 >= 64 个单元计数的中位数   —— 该区域没有被饿着
(c) S2–S4 中失败（ACA-9 > 1e-3）的数量 <= 1        —— 失败不随抽样设计系统性重现
```

若 (a) 不成立（即加密确实修好了），则采样是一个有效杠杆，**不得排除**；该原因与 `rOptimizationFailure` 竞争，按 item 5 报 `UNDETERMINED`。

## 4. `exp-annulus-dx-implementation` — rImplementationDefect（正控制式）

不训练。全部通过**产生 ACA-9 的同一条评估流水线**。

| 探针 | 内容 |
|---|---|
| I1 | **预言注入**：把精确制造解 u\* 当作模型送进同一条流水线（torch 表达、可微，因此 AD 路径、单元划分、归一化、边界与通量代码全部被执行） |
| I2 | **正控制**：在 u\* 上叠加一个**只落在单个已知单元内**的已知凸起，检验流水线是否恰好把该单元报为热点，且统计量等于预测值 |
| I3 | **独立重算**：用第二套独立编写的例程（不 import `diagnostics_annulus`）重算 r1 seed-2 在 120k 处的 ACA-9 |
| I4 | AD 与中心差分在热点单元处的对照 |

**判定（事前冻结）**：被排除，当且仅当

```text
I1  relL2 <= 1e-12 且 ACA-9 <= 1e-12          （预言应当给出机器精度的零）
I2  热点单元 == 注入单元，且统计量相对误差 <= 1e-9
I3  与生产值相对差 <= 1e-12
I4  AD 与中心差分相对差 <= 1e-6               （差分截断误差量级）
```

## 5. `exp-annulus-dx-spec` — rSpecDefect（正控制式）

待检机制：规范（PDE / 源项 / 边界条件 / 定义域）自相矛盾，于是「误差」是规范错误的产物。注意这**能**产生本信号：网络是按 f 训练的，若 f 与 u\* 不一致，网络本就不会收敛到 u\*。

| 探针 | 内容 |
|---|---|
| C1 | `-Δu* - f = 0`，在 D_dev 与**热点单元节点**上，用**两条独立路径**各算一次：(α) torch 自动微分作用于 torch 表达的 u\*；(β) `analytic_annulus` 的闭式 Laplacian |
| C2 | u\* 在**两条**边界组件上为零 |
| C3 | **正控制**：对 f 注入一个刻意的偏差，确认 C1 能检出 |

**判定（事前冻结）**：被排除，当且仅当

```text
C1  两条路径的 max |-Δu* - f| 均 <= 1e-12
C2  两条组件上的 max |u*| 均 <= 1e-14
C3  注入偏差后 C1 的残差 >= 1e-6            （证明该检查确实有分辨力）
```

## 6. `exp-annulus-dx-reference` — rReferenceDefect（路径审计 + 正控制式）

在本问题中「独立参考」指 `scientific_reference/annulus_polar_fdm.py`（只用 numpy、不含 autograd、不复用 PINN 残差算子）。解析对 (u\*, f) 的正确性由第 5 节覆盖，此处覆盖数值参考。

| 探针 | 内容 |
|---|---|
| R1 | **路径审计**：机器证明 ACA-9 的计算路径**从不读取** FDM —— 若参考进不了统计量，它就不可能制造该信号 |
| R2 | **收敛阶**：独立极坐标 FDM 三级网格对解析解的相对 L2，观测阶 |
| R3 | **局部一致性**：最细网格下 FDM 与解析解的**逐 ACA-9 单元**误差，特别是热点单元 |
| R4 | **正控制**：破坏 FDM 算子（去掉极坐标 Jacobian 的一项），确认 R2 检出二阶的丧失 |

**判定（事前冻结）**：被排除，当且仅当

```text
R1  ACA-9 的调用路径不含 scientific_reference（机器断言）
R2  观测阶落在 [1.8, 2.2]
R3  FDM 在热点单元的自身误差 <= 模型在该单元误差的 1/10
R4  破坏后观测阶落在 [1.8, 2.2] 之外       （证明该检查确实有分辨力）
```

## 7. `exp-annulus-dx-singularity` — rSingularityTreatment（正控制式）

| 探针 | 内容 |
|---|---|
| G1 | **正则性**：u\*、\|∇u\*\|、\|Δu\*\| 在 D_dev 与逐单元上的最大值 |
| G2 | **空间特征**：10 seed × 3 预算共 30 个最差单元中，落在紧贴边界的径向环（bin 0 或 bin 3）的个数 |
| G3 | **正控制**：合成一个在内圆上某点具有真实 r^(2/3) 角点型奇异的误差场，确认 ACA-9 机制把它定位到**紧贴边界**的单元 |

**判定（事前冻结）**：被排除，当且仅当

```text
G1  逐单元 max |Δu*| <= 10 × 全域中位数     （无向边界的增长）
G2  30 个最差单元中落在 bin 0 或 bin 3 的个数 == 0
G3  正控制的热点落在 bin 0（紧贴内圆）      （证明该机制确实能定位奇异）
```

## 8. 产物与记录

每个实验写出一份 `exp-*` 证据工件（JSON），含其 `experimentId`、全部探针的原始测量、逐条判定、以及**该实验所属的类别（干预式 / 正控制式）**。这些工件被 DiagnosisRecord 的 `discriminatingExperiment.excludes` 与 `evidencePointers` 引用。

`signatureEvidence` 的两项必填字段由本轮覆盖：`errorSpatialDistribution`（逐单元误差场）与 `samplingConfigDiff`（第 3 节的采样干预）。

## 9. 事前披露

1. 第 3 节需要 4 次 120k 训练，约 2 小时（CUDA）。其余四个实验不训练，分钟级。
2. 判定阈值取自既有合同与机器精度量级，**不是**看到结果后选的。`1e-3` 是 ACA-9 的既有阈值；`1e-12 / 1e-14` 是 float64 机器精度量级；`[1.8, 2.2]` 是二阶格式的常规接受带；正控制的通过条件要求检查具备分辨力。
3. 若任何一个原因无法诚实排除，本轮以 `Root Cause = UNDETERMINED` 停止，**不强行**命名 `rOptimizationFailure`（裁决 item 5）。
4. 即使五项全部排除、DiagnosisRecord 成立，本轮仍在形式诊断完成后**停止并报告**，不消耗 DAC-M1（裁决 item 11）。

---

## 10. 追加勘误：S1 的可执行形式（2026-09-20，**在任何排除实验执行之前**追加）

本节是追加。第 0–9 节一字未改。这里更正的是第 3 节 S1 的一个**实现层面不可执行的写法**，并且把更正写在运行之前，而不是看到结果之后。

第 3 节写 S1 为「配置点数 1024 → 2823，seed 2 的三元组」。这在配对设计下**无法执行**：r1 的已登记 D_train 池只有 **2048** 个点，2823 个配置点无法从中抽出。（2823 这个数来自更早的 EXPLORATORY 探针，它当时用的是一个 4096 点的池。）

因此 S1 拆成两个探针，并且把判定改得**更严**而不是更松：

| 探针 | 干预 | 是否配对 |
|---|---|---|
| **S1a** | 从 r1 的**已登记**池中取**全部 2048** 个点作配置点（相对 1024 是 **2×** 密度） | **是**，与 r1 同一池、同一 seed 三元组 |
| **S1b** | 从一个新生成的 4096 点面积均匀池中取 **2823** 个点（相对正方形标定的 **2.76×** 面积匹配密度） | 否，池不同（这是 2823 唯一可执行的方式，如实标明） |

**更正后的判定 (a)**：`rSamplingDeficiency` 的第一项条件成立，当且仅当

```text
S1a 的 ACA-9 > 1e-3  且  S1b 的 ACA-9 > 1e-3      —— 两种加密都救不回来
```

只要**任意一个**把 ACA-9 压到阈值以下，(a) 即不成立，采样就是一个有效杠杆，**不得排除**，按裁决 item 5 报 `UNDETERMINED`。

(b) 与 (c) 不变。S2–S4 仍在 r1 的已登记池上、以 1024 个配置点、只更换采样 seed 执行，完全配对。

---

## 11. 追加勘误：§1 关于 rCapacityLimit 的那句话不被本文件 §2 授权（2026-09-21，追加不改写）

本节是**追加**，§0–§10 一字未改，判定规则与阈值全部保持冻结。

本文件 §1 写道：「`rCapacityLimit` 已由嵌套预算干预（`exp-annulus-nested-budget-r1`）用实验排除。」这句话有两处问题：

1. **它不被本文件自己的 §2 授权。** §2 原文：「干预式：改变该原因所依赖的那个变量；若该原因为真，结果必须改变。」`state_machine.FACTOR_CONTROL` 把容量所依赖的变量定为 **architecture**；嵌套预算干预把架构钉死在 4×64、只改 `optimizer.steps`，从未改变过那个变量。
2. **它与更早冻结的 2026-09-19 预注册 §13 CASE A 冲突。** 后者原文是「`rCapacityLimit` **不再是必要解释**」，并把它逐字列入六项不得跳过的记录义务。以更早冻结的那份为准。

此外 §1 用的 `exp-annulus-nested-budget-r1` 这个标识**从未存在**：该干预的产物没有 `experimentId`，目录名为 `nested-budget-r1-paired`。

更正：`rCapacityLimit` **未被排除**。本文件处理的五个原因不变；未排除的原因总数由 3 项改为 4 项。见
`docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md` §12.4。
