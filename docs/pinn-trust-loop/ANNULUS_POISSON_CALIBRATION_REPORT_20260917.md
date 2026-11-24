# Annulus Poisson Calibration Report（Geometry Lift 1，2026-09-17 / 18）

执行负责人：Claude（队长）。对象：圆环制造解 Poisson 的首次正式标定。上游：[CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md](CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md)、[LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md](LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md)。预注册：`experiments/annulus/EXPERIMENT_ANNULUS_PREREGISTRATION_20260917.md`。

本轮**没有**改动任何阈值、**没有**重开已烧毁的 D_claim、**没有**修改任何历史机器证据 / TrustVector / ClaimGateDecision / 账本、**没有**删除失败与中止记录、**没有**新增 Gate 或 TrustStatus、**没有**起草 A-0003、**没有**扩 portability policy、**没有**在 Gate 失败后现场调参数重跑。

---

## 1. Executive

```text
Geometry Lift 1: NOT YET PASS
Highest Claim:   BLOCKED
```

十个 seed 全部训练完成、无 NaN，Gate 1 / 2 / 3 / 4 与 Gate 5a 物理全部 PASS。盲集 DAC-M0 按协议一次性打开，**Gate 5b 验收 FAIL**：十个 seed 中 **一个**（seed 2）在局部误差判据 **ACA-9** 上超标，实测 `1.079e-03` 对阈值 `1.000e-03`，超出 **7.9 %**。其余九个 seed 的 ACA-9 在 `4.196e-04`–`6.537e-04` 之间；**ACA-1..ACA-8 的九个判据对全部十个 seed 全部通过**。

按验收合同的 `seedPolicy = "every-seed"`（与 Gate 5b 对 MUST 判据一贯执行的 `all(...)` 同一规则），一个 seed 失败即 MUST 判据失败，故 `C_external = FAIL`，状态机进入 `FAILURE_RECORDED`。**阈值一个都没有动**（用户 2026-09-17 裁决：达不到就如实写 FAIL）。

**根因尚未正式判定**（见 §13 注解）。几何提升本身是成功的：曲边、内孔、多连通、两条边界组件带来的每一处机制（成员判定、面积均匀采样、双分量硬约束、内法向定向、几何原生求积、等面积局部划分、独立极坐标 FDM）都按设计工作，并有机器证据（第 3 节、第 2 节）；本轮**没有观察到**明确的几何病理。据此，**训练预算不足是一个被现有证据支持的假设（SUPPORTED HYPOTHESIS）**，见 §3.4 的定量对照——它**不是**一个已被正式识别的 `RootCauseClass`。状态仍是 `FAILURE_RECORDED`，尚未进入 `DIAGNOSED`。

---

## 2. Geometry Audit

> **What broke because the domain became curved and multiply connected?**

逐项分类如下。「broke」指**若照搬正方形的做法就会出错**，并给出本轮实测的机器证据。

### 2.1 membership — BROKE

孔**不属于**定义域。制造解的因子 `h = (1 - s)(s - a^2)` 在孔内 `s < a^2` 时变号，因此任何「先算再判断」的写法都会把孔内的值当成解。所有评估集与物理积分点都改为**显式成员判定**。

* 证据 `T11-geometryMembership` PASS：分类器把 interior / hole / exterior / 两条圆周严格分开。
* 证据 `PH8-geometryMembership` PASS：每一个物理评估点都严格落在圆环内部（0 个非法点），恒等式不会跨孔积分。
* 证据 `sets/isolation.json`：四个集合（train 2048 / dev 1024 / phys 5120 / claim 5834）全部通过成员检查。

### 2.2 sampling — BROKE

`r ~ U(a, 1)` **不是**面积均匀：中位半径处的面积分数是 0.38 而不是 0.5，内环被系统性过采样。正确做法是 `r = sqrt(a^2 + (R^2 - a^2) U)`，`theta = 2 pi V`。

* 冻结配置 `sampling.rule` 明确写死该公式；`pinn/experiments_annulus/datasets_annulus.area_uniform_interior` 是唯一实现。
* 训练解释器下的回归测试 `test_the_sampler_is_uniform_in_area_not_in_radius` PASS（7 项之一）。
* 顺带否证了一个似是而非的猜想：把配置点数按面积匹配（1024 → 2823）**并不**改善误差（EXPLORATORY：10k 步 1.05e-02 vs 9.94e-03，40k 步 2.358e-03 vs 2.230e-03），所以配置点数按正方形原值冻结，未做任何架构搜索。

### 2.3 boundary components — BROKE

边界不再是一条连通曲线的四条边，而是**两条互不连通的组件**。所有边界量都必须**按组件**分别计算并分别报告，而不是在一个「边界集合」上取最大值。

* 证据 `T4-hardBoundaryBothComponents` PASS：outer `1.69e-17`、inner 独立报告。
* 证据 `ACA-3`（两组件上 `|u|` 的最大值）在 D_claim 上十个 seed 全部 `≈ 2.116e-16`，对阈值 `1e-4` 有 **12 个数量级**的余量。
* 证据 `gate5b` 的 `diagnostics.boundary` 对 inner / outer 分别记录 `flux`、`maxAbsU`、`maxNormalError`、`nodes`（各 64 个节点）。

### 2.4 normal orientation — BROKE（本几何最危险的一处）

内边界的**外法向指向孔内**，即 `-(x, y) / a`，与外边界的 `+(x, y) / R` 相反。写反不会崩溃，只会给出一个看似合理、符号错误的数——预注册记录：写反时解析通量恒等式会从 `~1e-15` 劣化到 `O(1)`。

* 证据 `T12-boundaryNormalOrientation` PASS：直接断言外法向背离原点、内法向指向孔内，单位长度到 `1e-15`。
* 证据 `PH1-fluxBalance` PASS：`|∮ ∂u/∂n ds + ∫ f dA| / |∫ f dA| = 1.633e-04`（worst seed，阈值 `1e-2`），**按组件各用自己的外法向求和**。这是第二重、独立于 T12 的验证。
* 证据 `ACA-6`（按组件的法向导数误差）worst `9.950e-04`，阈值 `5e-3`，PASS。

### 2.5 hard constraint — NOT BROKEN（设计成立，如实记录）

双分量硬 Dirichlet 参数化 `u = (R^2 - s)(s - a^2) N(x, y)` 在两条圆周上**构造性**为零，因此多连通域并不需要第二个边界损失项，损失里只有一个 pde 项。

* 证据 `T8-lossTermSeparation` PASS：损失只有一个 pde 项、权重冻结、无边界罚项。
* 证据 ACA-3 ≈ `2.1e-16`（见 2.3）——这是机器精度，不是「训练得好」。
* 该因子在模型侧**独立于** `pinn.reference` 重写，模型不得 import 答案。

### 2.6 quadrature — BROKE

笛卡尔张量积求积不适用。改为几何原生求积：面积分数 `t` 上的 Gauss–Legendre × `theta` 上的梯形，雅可比必须正确。

* 证据 `T13-quadratureJacobian` PASS：求积面积 `2.756747553525` vs 精确值 `pi (1 - a^2) = 2.756747553525`，相对误差 `6.44e-16`；`∫ u* dA` 亦对上解析值。
* 证据 `ACA-5`（积分泛函）worst `1.798e-04`、`ACA-7`（能量恒等式）worst `1.674e-04`，阈值分别 `1e-3` / `1e-2`。

### 2.7 localized validation — BROKE

正方形用的 8×8 笛卡尔分块在圆环上**跨越孔**，且单元面积不等，统计量失去意义。改为几何原生的**等面积**划分：4 个等面积径向环 × 16 个扇区 = **64 个单元**（ACA-9）。

* 证据 `sLocalizedError` 合同：`partitionKind = annulusEqualAreaCells`、`radialBins = 4`、`angularSectors = 16`、`normalization = globalReferenceRms`、`operator = <=`、`threshold = 1e-3`、`seedPolicy = every-seed`、`statisticId = maxCellRmsErrorOverReferenceRms`，九个字段逐项与冻结合同比对通过。
* **这正是本轮失败的判据**（第 3、5 节）。但失败**不是**划分方式造成的：失败单元并不在孔边，见 §3.3。

### 2.8 numerical reference — BROKE

五点差分贴不了曲边界。独立参考改为**极坐标有限差分**，只用 numpy，不 import 任何 `pinn` 模块、不使用 autograd、不复用 PINN 的残差算子，只共享冻结的源项。

* 证据 `G2b-fdmRefinement` PASS：三级网格 (16×64 / 32×128 / 64×256) 的相对 L2 为 `3.407e-03 / 8.509e-04 / 2.127e-04`，比值 `4.004` 与 `4.001`，**观测阶 2.0016 / 2.0004**。
* 证据 `test_the_finite_difference_solver_shares_no_code_with_the_model` PASS。

### 2.9 governance — BROKE（登记为 AMENDMENT CANDIDATE，未改 schema）

`ProblemDefinition` schema 的 `domainType` 词汇是 `{interval, rectangle, disk, mesh, other}`，**没有 `annulus`**，且 `geometry` 对象不接受额外字段。

处理方式：用 schema **自带的** `regions[].params` 承载圆环几何，`domainType = "other"`，**没有修改治理 schema**。这是一个真实的表达力缺口，登记为 AMENDMENT CANDIDATE（第 11 节），本轮不动它——在一次几何提升的当口改治理词汇，等于一边跑实验一边改尺子。

### 2.10 acceptance-set blind spot — BROKE（已用其他手段覆盖）

纯粹的**导数分量互换**（`u_x ↔ u_y`）不会被 MUST 的积分型判据看见：能量对互换不变，H1 半范 ACA-8 只是 SHOULD。

覆盖手段：边界法向导数 ACA-6（按组件，见 2.4）与 Gate 3 的 AD 分量检查 `T2-secondDerivativeComponentSeparation`（非对称探针 `w = sin(2πx) cos(πy)`，`|w_xx + 4π² w| = 7.11e-15`、`|w_yy + π² w| = 1.78e-15`）。两者本轮均 PASS。

### 2.11 process — BROKE（上一轮沙箱冒烟抓到，已修，本轮验证）

旧写法在 Gate 4 返回 `BLOCKED` 时会**继续打开 claim 集**。修复后：任何非干净 PASS（FAIL / PARTIAL / BLOCKED 一律）都停在失败路径且**不打开** claim 集。

* 本轮沙箱冒烟（CUDA，150 步 × 3 seed）实测：Gate 4 `BLOCKED` → 走失败路径 → `finalState = IMPLEMENTATION_VERIFIED`，沙箱账本**未出现 OPENED**，真账本一字未动。

### 2.12 none — 未因几何而破的部分

架构、优化器、batch、dtype、seed 协议、代码身份机制、PRELOCK、账本生命周期、状态机分流、局部误差触发器的**判定逻辑**（只换了划分方式，判定规则原样沿用）。步数预算是唯一与正方形标定不同的方法值，理由在预注册 5.2 事前写定。

### 2.13 本轮新增的一条（一条尚未被否证的观察）

在**迄今考察的正方形与圆环两个标定案例中**，**没有观察到**圆环特有的局部/全局误差比放大。两个几何不足以证明普遍的 geometry invariance，因此下表只作为观察记录，不作为不变性的证明：

| | 全局（ACA-1 / AC2D-1）median | 局部（ACA-9 / AC2D-9）median | 比值 |
|---|---|---|---|
| 正方形 2D（已 CLOSED @ C2） | `3.600e-05` | `1.151e-04` | **3.20** |
| 圆环（本轮） | `1.860e-04` | `5.545e-04` | **2.98** |

圆环十个 seed 的逐 seed 比值为 `2.61 / 2.77 / 2.90 / 3.02 / 3.95 / 2.62 / 2.46 / 3.76 / 2.63 / 2.58`，均值 **2.93**、标准差 0.52 —— 与正方形的 3.20 在同一水平。

结论（详见 §3.4）：**局部判据一直就在全局误差的约 3 倍处**；正方形把全局误差压到 `3.6e-05`（对 `1e-3` 有 28 倍余量），所以 AC2D-9 从未构成威胁；圆环只压到 `1.86e-04`（5.4 倍余量），于是 ACA-9 成为**首先触顶**的判据。这是**预算问题，不是几何问题**。

---

## 3. Numerical

### 3.1 训练（D_dev，诊断口径，不是验收）

| 量 | 值 |
|---|---|
| seed 数 N | 10（init 20261400+i / sample 20261500+i / batch 20261600+i） |
| 完成率 k/N | **10/10**（全部跑满 120000 步，NaN/Inf 0 个，发散 0 个） |
| median devRelL2 | **1.853e-04** |
| IQR | **2.470e-05** |
| worst seed | **3.874e-04**（seed 2）；worst/median = 2.09，上限 3.0 |
| 训练设备 | cuda（每 seed 1849–2571 s，共约 5.9 h） |
| 评估设备 | cpu（全部 Gate 数值） |

Gate 4 三项检查全 PASS：训练完整性、seed 协议（`median_ok / worst_ok / dispersion_ok` 全 True）、loss–error 解耦（无 run 出现 loss 掉两个数量级而 dev 误差不降）。

D_dev 上的诊断中位数：残差 `normalizedResidualRms = 1.034e-03`、边界 `maxBoundaryAbs = 2.116e-16`、通量亏损 `fluxBalance = 9.212e-05`、局部统计量 `maxCellRmsErrorOverReferenceRms = 4.109e-04`、局部/全局比 `3.119`。

### 3.2 验收（D_claim = DAC-M0，5834 个样本，一次性打开）

| 判据 | 含义 | median | worst | 阈值 | 判定 |
|---|---|---|---|---|---|
| ACA-1 | 相对 L2 | `1.860e-04` | `3.722e-04` | `1e-3` | PASS |
| ACA-2 | 相对 L∞（逐点网格） | `3.539e-04` | `7.443e-04` | `5e-3` | PASS |
| ACA-3 | 两组件边界 \|u\| 最大值 | `2.116e-16` | `2.117e-16` | `1e-4` | PASS |
| ACA-4 | 归一化残差 RMS | `9.797e-04` | `1.426e-03` | `1e-2` | PASS |
| ACA-5 | 积分泛函相对误差 | `1.350e-04` | `1.798e-04` | `1e-3` | PASS |
| ACA-6 | 按组件法向导数误差 | `5.828e-04` | `9.950e-04` | `5e-3` | PASS |
| ACA-7 | 能量恒等式亏损 | `1.106e-04` | `1.674e-04` | `1e-2` | PASS |
| ACA-8（SHOULD） | 相对 H1 半范 | `3.166e-04` | `5.601e-04` | `5e-3` | PASS |
| **ACA-9** | **等面积单元局部误差** | `5.545e-04` | **`1.079e-03`** | **`1e-3`** | **FAIL（seed 2）** |

逐 seed ACA-9：`4.196e-04 / 5.207e-04 / ` **`1.079e-03`** ` / 5.884e-04 / 5.961e-04 / 4.825e-04 / 4.429e-04 / 6.537e-04 / 5.994e-04 / 5.153e-04`。

### 3.3 失败单元在哪里（回答「是不是孔边的病理」——不是）

| seed | ACA-9 | 最差单元 (径向环, 扇区) | 该单元 RMS | 与次差单元之比 |
|---|---|---|---|---|
| 0 | 4.196e-04 | (2, 11) | 5.033e-05 | 1.17 |
| 1 | 5.207e-04 | (1, 14) | 6.246e-05 | 1.15 |
| **2** | **1.079e-03** | **(2, 13)** | **1.294e-04** | **1.04** |
| 3 | 5.884e-04 | (2, 9) | 7.059e-05 | 1.10 |
| 4 | 5.961e-04 | (2, 4) | 7.151e-05 | 1.38 |
| 5 | 4.825e-04 | (2, 0) | 5.788e-05 | 1.00 |
| 6 | 4.429e-04 | (2, 8) | 5.313e-05 | 1.06 |
| 7 | 6.537e-04 | (2, 13) | 7.842e-05 | 1.66 |
| 8 | 5.994e-04 | (1, 10) | 7.191e-05 | 1.03 |
| 9 | 5.153e-04 | (1, 1) | 6.181e-05 | 1.16 |

三点如实观察：

1. 最差单元**从不落在径向环 0（紧贴孔）或环 3（紧贴外圆）**，十个 seed 全部落在中间两环。这与双分量硬约束把两条圆周精确钉死（ACA-3 ≈ 2e-16）一致——误差被推离两条边界。**孔没有制造局部病理**。
2. 最差单元与次差单元之比只有 1.00–1.66，说明误差是**一片平缓抬高的区域**，不是某个奇异单元。
3. seed 2 的最差单元 `1.294e-04` 是其余九个 seed 最差单元（`5.03e-05`–`7.84e-05`）的 1.65 倍；而 seed 2 的全局 ACA-1（`3.722e-04`）同样是中位数的 2.00 倍。**seed 2 是整体更差，不是局部更差。**

### 3.4 定量线索：指向训练预算的支持性证据（假设，非判定）

局部/全局比值 `2.93 ± 0.52`（§2.13）意味着：只要 ACA-9 与 ACA-1 共用同一个 `1e-3` 阈值，**ACA-9 就会先触顶**，其对 ACA-1 的隐含预算是

```text
ACA-1 隐含上限 = 1e-3 / 2.93 ≈ 3.414e-04
```

而预注册 5.2 的步数外推只针对 ACA-1：120000 步被选为「外推到约 7e-04，对 ε_spec = 1e-3 约 1.4 倍余量」，并且当时就**如实记录了这比正方形标定的 23 倍余量小得多**。实际跑出来 median ACA-1 = `1.860e-04`（比外推的 7e-04 还好），但 worst seed `3.722e-04` **恰好越过了 `3.414e-04` 这条隐含线**——于是 ACA-9 在该 seed 上给出 `1.079e-03`。

换句话说：预算是按**一个**判据外推的，而验收是按**九个**判据、且按 **every-seed** 判定的。这一条写在这里作为观察与算术，**不作为本轮的行动**——改步数是方法变更，必须走新 revision、新盲集成员，由用户决定（第 12 节）。

---

## 4. Blind Validation

盲集生命周期，全部来自账本 `experiments/annulus/ledger/pdef-annulus-poisson-v1.json`（唯一真相源，从不读 manifest 的静态 status 字段）：

```text
事件 1  SEALED   claimSet 84877d8b1eec   samples cb3a15010f91   （2026-09-17，正式 run 之前）
事件 2  OPENED   claimSet 84877d8b1eec   samples cb3a15010f91   codeHash 8ee9b9236199
                 -> 随即 BURNT
ledgerHead  df1b1c5004e9...
```

* 打开发生在 **Gate 5a 物理 PASS 之后**、Gate 5b 之前，一次性，不可撤销。
* 打开**之前**的早期护栏实测生效：run 启动时账本派生状态为 `SEALED`（`claimSetLedgerStatusAtStart = "SEALED"`），若为 `OPENED` / `BURNT` 则拒绝启动。
* 被中断的两次 attempt（`stopped-cpu-r1-c5a3e12e018e`、`stopped-gpu-r1-sleep-8ee9b9236199`）**从未打开**盲集，所以 DAC-M0 才能留到本轮；两份记录都完整保留、未删除。
* 盲集池四个成员两两共享样本数为 0；**DAC-M1 / M2 / M3 仍为 NEVER_SEALED**，本轮一次也没有触碰。
* **DAC-M0 现已 BURNT，不得重开**。

---

## 5. Failure Path

```text
IMPLEMENTATION_VERIFIED -> TRAINING_COMPLETED   (gate 4, PASS)
TRAINING_COMPLETED      -> VALIDATION           (ENTER_VALIDATION)
claim set 84877d8b1eec OPENED -> BURNT
VALIDATION              -> FAILURE_RECORDED     (gate 5, FAIL)
```

`failure_record.json` 实录：

* `gate = 5`
* `observedSignatures = ["sLocalizedError"]`（**只有这一个**；`sPdeResidual`、`sBcResidual`、`sConservation`、`sPinnCfd`、`sSeedSensitive` 均未触发）
* `claimSetVerdict.failedMustPerSeed = [[], [], ["ACA-9"], [], [], [], [], [], [], []]`
* `retrainedInPlace = false` —— **没有现场调参数、没有重训**

**上一轮局部误差触发器硬化的直接验证**（这是本轮一个独立的正面结果）：

```text
fired            true
firedBy          "1/10 seed(s) fail ACA-9"
seedPolicy       every-seed
failingSeedIndices [2]      failureFraction 0.1
ensembleStatistic  best 3.569e-04   median 4.109e-04   worst 1.038e-03
```

注意 **median = 4.109e-04 远低于阈值**。硬化之前的 median 口径会把这个少数派失败整个吞掉、报告「没有失败」；硬化之后它按验收合同自己的 `every-seed` 策略正确触发。该机制上一轮是在正方形上修的，本轮在**一个新几何、一次真实失败**上得到验证。

---

## 6. Tier-1 Red Team

**未执行。** 依协议，Tier-1 只在 Gate 5 PASS 之后进行——红队是对**已被接受**结果的压力测试，不是被拒结果的第二次机会。本轮 `C_external = FAIL`，故八项（P1 / P4 / P6 / P7 / P8 / P9 / P11 / P16）**一项未跑**。

驱动入口已在正式 run **之前**进入代码身份（`runner_annulus.run_tier1_for_attempt`、`run_formal_annulus.py --tier1`、`runner_annulus tier1`），并已实测其拒绝路径：对 Gate 5 未 PASS 的 attempt 拒绝启动，对未完成的 attempt 给出明确拒绝而非堆栈。它只读已登记产物，从不触碰 D_claim、账本或历史判定。

放在跑之前而不是跑之后，是因为跑完再加 driver 会再次改变 `codeHash`，红队就无法与它所检验的 attempt 处在同一代码身份下。

---

## 7. G6 Reproduction

**未执行。** `C_repro = BLOCKED`，`gate6_reproducibility.json` 记录的理由是「Gate 5 did not pass; reproduction is not attempted」。复现一个被拒的结果不会产生任何可信度。

Environment B 已只读核验、**未做任何安装、未污染**：

```text
C:\Users\user\LeoAI-envB2D-20260916\venv
Python 3.12.9   torch 2.12.1+cpu   numpy 2.4.5   torch.cuda.is_available() = False
```

预注册的 G6 容差（`|Δmedian| ≤ 1e-4` 且 `≤ 0.5 × median_A`、k/N 判定一致、seedOffset 10000）保持冻结，本轮未使用、未修改。

附带说明（本轮的 device 设计要点）：主 run 在 GPU、复现在 CPU，两者 `acceleratorClass` 不同，这只会增强环境独立性；而 `codeHash` 必须相同——这正是 `device` 被做成命令行参数、**绝不写进冻结配置**的原因。

---

## 8. Trust Vector

| 维度 | 状态 | 依据 |
|---|---|---|
| `math` | **PASS** | Gate 1（几何合同、两条边界组件）+ Gate 2（解析自验 `max\|-Δu* - f\| = 0`、独立极坐标 FDM 观测阶 2.0016 / 2.0004） |
| `impl` | **PASS** | Gate 3 十项全 PASS，含 T11 成员判定、T12 内外法向朝向、T13 求积雅可比、T10 可信校验器的控制夹具 |
| `train` | **PASS** | Gate 4：10/10 完成，median 1.853e-04，IQR 2.470e-05，worst 3.874e-04，发散 0，loss–error 未解耦 |
| `physics` | **PASS** | Gate 5a：PH1 通量 1.633e-04、PH2 能量 1.674e-04、PH3 正性 0 违例、PH6 极值 1.000303、PH7 SPD（能量 1.639，独立极算子最小特征值 22.7262 > 0）、PH8 成员；PH4 / PH5 登记 NOT_APPLICABLE 并附理由 |
| `external` | **FAIL** | Gate 5b：D_claim 上 seed 2 的 ACA-9 = 1.079e-03 > 1e-3（every-seed 策略） |
| `repro` | **BLOCKED** | Gate 6 未尝试（Gate 5 未通过） |

弱链：`external = FAIL`。

---

## 9. Claim Decision

```text
Highest Claim: BLOCKED
```

`finalState = FAILURE_RECORDED`，runner 以 `decision = False` 收尾，因此**没有生成 `claim_gate_decision.json`**——这是正确行为：一次 Gate 5 FAIL 的 attempt 不产生任何 claim 等级。C0 / C1 / C2 **一律未被授予**。

圆环几何目前的可信状态是「已实现、已验证实现正确性与物理一致性，但**未通过验收**」。

**已 CLOSED 的 Poisson 1D 与 Poisson 2D 正方形标定不受本轮任何影响**：本轮未触碰它们的证据、账本、TrustVector 或 ClaimGateDecision。

---

## 10. Tests / PRELOCK / Portability

两个解释器的真实数字：

| 项目 | 治理虚拟环境 `.venv`（无 torch / numpy） | 训练解释器（mamba，torch 2.12.1+cu126） |
|---|---|---|
| 全套 pytest | **1391 passed / 0 failed / 25 skipped** | — |
| 被跳过项的补跑（annulus） | — | **7 passed / 0 failed** |
| 被跳过项的补跑（poisson2d） | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，7/7** | — |
| portability | **0 hard binding / 1 configurable default / 8 historical evidence** | — |

与上一轮基线完全一致（1391 / 0 / 25、7/7、0-1-8），本轮的 device 改动没有引入任何回归。

沙箱冒烟（CUDA，150 步 × 3 seed）另跑一次，整条流水线含失败路径通过；沙箱自建自删。

---

## 11. Newly Discovered

### BLOCKING

**无。**（Gate 5b FAIL 是**预期内的判定结果**，不是新发现的缺陷：判据、阈值、seed 策略都在预注册里事前写定，机器如约执行。）

### NON-BLOCKING

1. **在迄今考察的正方形与圆环两个标定案例中，没有观察到圆环特有的局部/全局误差比放大**（3.20 与 2.93 ± 0.52）。在这两个案例内，ACA-9 触顶与全局误差水平高出 5.2 倍相符；两个几何不足以证明普遍的 geometry invariance，也不足以排除其它候选根因。见 §2.13、§3.4、§13。
2. **误差被硬约束推离两条边界**。十个 seed 的最差局部单元全部落在中间两个径向环，从不在紧贴孔或紧贴外圆的环上。多连通域**没有**在孔边制造局部病理。见 §3.3。
3. **GPU 在此工作负载上是更慢的设备**。事前 EXPLORATORY 基准（CPU 16.6–21.6 ms/步 vs CUDA 17.6–19.3 ms/步）与正式 run 实测（CUDA 1849–2571 s/seed vs 归档 CPU attempt 1407 s/seed）一致。原因是网络极小且宪法要求 float64，而 RTX 4060 的 FP64 吞吐是 FP32 的 1/64。用户在看到数字后仍选择 GPU，代价已记录。
4. **CPU 与 CUDA 在 float64 + 确定性算法下给出同一答案**。同 seed 2000 步后权重最大绝对差 `4.441e-16`；seed 0 跑满 120000 步在 CUDA 上两次、CPU 上一次都得到 devRelL2 = `1.622e-04`。
5. **局部误差触发器硬化在一次真实的少数派失败上得到验证**（1/10，median 远低于阈值）。见第 5 节。

### AMENDMENT CANDIDATE

1. **`ProblemDefinition` schema 的 `domainType` 词汇缺少 `annulus`**，且 `geometry` 对象不收额外字段。本轮用 schema 自带的 `regions[].params` 承载圆环几何、`domainType = "other"`，**未改治理 schema**。再入角、L 形等后续几何会重复遇到同一问题，建议作为一次性的词汇扩展提案单独处理。
2. **Gate 4 不筛查局部判据，尽管 D_dev 有能力测量它**。本轮 D_dev 上的局部统计量 worst 已经是 `1.038e-03`（> 1e-3），即**在盲集被打开之前，同一个 seed 的同一个问题已经在开放集上可见**；但 Gate 4 只按 Constitution 10.1 的 seed 规则检查 `devRelL2`，于是盲集仍被消耗。一个 Gate-4 层面的 D_dev 侧局部判据预筛，可以在不消耗盲集的前提下拦下这类 attempt。**本轮没有实现它**——新增 Gate 是被明令禁止的，且在失败当口改判定结构本身就是不当行为。仅作为提案登记。

### NONE

其余部分未发现新问题。

---

## 12. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

理由：验收未通过，圆环几何尚未取得任何 claim 等级；在未通过的几何上继续向再入角推进，等于把一个未结清的债务带进更难的问题。

同时如实记录：**几何提升本身是成功的**。第 2 节逐项列出的十处「因为域变成曲边且多连通而必须改变的东西」全部按设计工作并有机器证据，且本轮**没有观察到**明确的几何病理。失败的解释目前只是一个受支持的假设（训练预算，§3.4），**尚未经过受控干预检验**，见 §13 与诊断报告。

后续可能的走向属于**用户与外部评审的决定，本轮不自行开始**。仅列出与之相关的既成事实：

* **DAC-M0 已 BURNT，不得重开**；盲集池中 **DAC-M1 / M2 / M3 仍为 NEVER_SEALED**。
* 任何方法值变更（含步数）都是方法变更，必须走**新 revision + 新预注册注解 + 新盲集成员**，并重新冻结代码身份。
* §3.4 给出的算术是：在当前局部/全局比 `2.93` 下，要让 ACA-9 对全部十个 seed 通过，worst-seed 的 ACA-1 需低于约 `3.414e-04`（本轮为 `3.722e-04`）。这是一个观察，不是一个已获授权的计划。

本轮到此**停止**：不自行开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热，等用户与外部评审。

---

## 13. 追加注解：因果措辞收窄（2026-09-18，追加而非改写机器证据）

本节是**追加**。它只修正本报告自身的**散文措辞**；任何机器证据（RunRecord、账本、Gate 结果、`failure_record.json`、TrustVector、状态转移、seed 账本、阈值、ScientificSpec revision 1）**一字未动**。

收窄的内容，以及为什么：

1. **「根因不是几何 / 真正的原因是步数预算不足」→「训练预算不足是一个受支持的假设」**。
   状态机当前仍停在 `FAILURE_RECORDED`，**尚未进入 `DIAGNOSED`**。在受控干预完成之前，`rOptimizationFailure`
   不得被写成正式的 `RootCauseClass`。原措辞把一个尚未检验的假设说成了结论。
2. **「局部/全局误差比是几何不变的」→「在迄今考察的正方形与圆环两个标定案例中，没有观察到圆环特有的
   局部/全局误差比放大」**。两个几何不足以证明普遍的 geometry invariance。
3. **「失败落在一个与几何无关的量上」→「本轮没有观察到明确的几何病理」**。
   证据的缺席不等于不可能性的证明（`absence of evidence != proof of impossibility`）。

被收窄的判断所依据的**数字本身没有变**：正方形 3.20、圆环 2.93 ± 0.52、隐含 ACA-1 上限 `≈ 3.414e-04`、
worst-seed `3.722e-04`。变的只是这些数字被允许支撑的结论强度。

同一收窄同步应用于 CHANGELOG、根目录软件修改报告与记忆文件；操作日志 §5.32 以**追加**方式记录本次收窄，
不改写原有条目。

后续：`sLocalizedError` 在 Constitution 1.2 下的完整候选根因集合、既有证据清点，以及为什么
「只增加步数」的受控干预在当前代码下**无法**做成单因素干预，见
[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)。
