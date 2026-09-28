# Annulus Budget Diagnosis Report（2026-09-18）

执行负责人：Claude（队长）。对象：`Geometry Lift 1 — Annulus Poisson` 的 Gate 5b 失败（`observedSignatures = ["sLocalizedError"]`）。上游：[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)。

本轮**没有**执行任何训练干预、**没有**修改任何机器证据、**没有**触碰任何 claim set、**没有**改动阈值 / 架构 / 采样 / 优化器 / 几何 / revision、**没有**新增 Gate 或 TrustStatus、**没有**起草 A-0003。

---

## 1. Executive

```text
Root Cause:            UNDETERMINED
Diagnosis:             NOT PERFORMED — blocked before intervention (PART 6)
                       EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE
Annulus Calibration:   NOT YET PASS
Highest Claim:         BLOCKED
State:                 FAILURE_RECORDED   （未进入 DIAGNOSED）
```

按 PART 4 的要求，在任何干预之前先审计了正式 120k run 的 optimizer / scheduler 状态。审计结果是**两条独立的阻塞事实**，任何一条都足以使「只增加训练步数」无法构成单因素干预：

* **B-1 优化器与调度器状态从未被保存。** 正式 run 只保存模型权重。Adam 的一阶/二阶矩 `m_t, v_t`、其 step 计数、`ExponentialLR` 的 `last_epoch`、batch 生成器的 RNG 状态与 shuffle 游标，在 `train_run` 返回时全部丢弃。→ **nested continuation（PART 5）不可执行。**
* **B-2 学习率轨迹依赖总预算。** 实现是 `lr(step, total_steps)`，不是 `lr(step)`。把预算从 120k 改成 180k / 240k 会**重新缩放整条 LR 轨迹，包括本应保持一致的前 120k 步**。→ 这正是 **PART 4.1 明令禁止的混杂**，且它同样污染 PART 6 提到的「from-scratch matched-budget」备选方案。

因此按 **PART 6** 停在干预之前，等待用户裁决。`rOptimizationFailure` **没有**被写成正式 `RootCauseClass`。

---

## 2. Causal Evidence

### 2.0 措辞状态（PART 1）

```text
Before diagnosis:
    training-budget limitation = SUPPORTED HYPOTHESIS
    not yet a formally identified RootCauseClass
```

上游标定报告中「根因不是几何 / 真正的原因是步数预算不足」「局部/全局误差比是几何不变的」等普遍化措辞已按 PART 1 收窄，收窄记录见该报告追加的 §13。允许的措辞是：

> Across the square and annulus calibration cases examined so far, no annulus-specific amplification of the local/global error ratio was observed.

本报告全篇遵守一条规则：**证据的缺席不等于不可能性的证明**。下文任何一处都不使用「证明不存在」。

### 2.1 Evidence against geometry pathology（支持性，非证明）

| 机制 | 机器证据 | 结果 |
|---|---|---|
| 成员判定 | `T11-geometryMembership`、`PH8-geometryMembership` | PASS，0 个非法点 |
| 双分量硬 BC | `T4`、`ACA-3` 十个 seed ≈ `2.116e-16`（阈值 `1e-4`） | PASS |
| 内/外法向朝向 | `T12` 直接断言 + `PH1` 通量恒等式 `1.633e-04` | 双重 PASS |
| 几何原生求积 | `T13`：面积 `2.756747553525` vs 精确值，相对 `6.44e-16` | PASS |
| 独立极坐标 FDM | `G2b`：`3.407e-03 / 8.509e-04 / 2.127e-04`，观测阶 `2.0016 / 2.0004` | PASS |
| 局部误差空间分布 | 十个 seed 的最差单元全部落在中间两个径向环，**从不**紧贴孔或外圆；最差/次差比仅 `1.00–1.66` | 无边界局部热点 |

**可以说**：本轮**没有观察到**明确的几何病理，也没有观察到孔边局部热点。
**不可以说**：几何病理已被排除。`rSingularityTreatment` 与 `rReferenceDefect` 仍是 admissible 集合中的合法候选（第 3 节）。

### 2.2 Evidence against sampling deficiency（支持性，非证明）

已有 EXPLORATORY 证据（D_dev only，claim pool 当时尚未封存）：

| 配置点数 | 步数 | devRelL2 |
|---|---|---|
| 1024 | 10k | `9.94e-03` |
| 2823（面积密度匹配，2.76×） | 10k | `1.05e-02` |
| 2823 | 40k | `2.358e-03` |
| 1024 | 40k | `2.230e-03` |

把配置点密度提高 **2.76 倍**没有带来实质改善（在两个步数预算下都略**更差**）。

**可以说**：这是**反对** `rSamplingDeficiency` 的一项证据。
**不可以说**：这是数学证明。它是两个密度、两个预算、一个 seed 三元组的探索性观察，且是 EXPLORATORY 标记、不构成正式证据。

### 2.3 Evidence for / against capacity limit

**目前两侧都没有决定性证据。**

* 反对 `rCapacityLimit` 的间接线索：同一 `4×64 tanh` 架构在正方形上达到 `AC2D-1 = 3.600e-05`（比圆环好 5.2 倍），说明该容量**在另一几何上**有余量；十个 seed 中 **9 个**已经满足 ACA-9，失败者超出阈值仅 **7.9 %**。
* 支持 `rCapacityLimit` 的可能性未被排除：圆环面积是单位正方形的 `2.757` 倍，同样的参数量覆盖更大的定义域；「9/10 已通过」同样可以由「容量恰好处在边缘」解释。
* **判别这两者正是本轮预定干预的目的**（PART 2 的核心问题：同一架构是否仅靠更多优化预算就能稳定满足已有局部判据）。该干预**未能执行**，因此该问题**仍然悬空**。

### 2.4 Evidence for / against optimization budget

支持（全部为 EXPLORATORY，非正式诊断）：

| 步数 | devRelL2 |
|---|---|
| 10k | `~9.94e-03` |
| 20k | `~5.43e-03` |
| 40k | `~2.23e-03` |
| 120k（正式） | median `1.853e-04` |

显示明显的 budget response（每倍增步数误差约降 2.1 倍）。正式 run 的定量线索：局部/全局比 `2.93 ± 0.52` 使 ACA-9 对 ACA-1 的隐含上限为 `1e-3 / 2.93 ≈ 3.414e-04`，而 worst-seed ACA-1 为 `3.722e-04`——**差距很小**，与「再多一点优化预算即可」相符。

**但**：
* `exploratory trend != formal diagnosis`；上表来自 D_dev 的探索性探针，不是受控干预。
* 上表的每一行都是**独立的 from-scratch run，且各自带着被重新缩放的 LR 轨迹**（见 §4.2）——所以它们之间的差异**本来就不是**纯粹的「步数」差异。这一点此前没有被写明，本报告予以更正。
* 因此现有 budget response 证据**比原先以为的更弱**：它混合了「更多步数」与「更慢的 LR 衰减」两个因素。

---

## 3. Candidate Root Causes（PART 2，读自实际 admissible matrix）

从 `pinn.governance.state_machine.admissible_root_causes("1.2")` 直接读取，**未按任何外部提示词缩减**：

```text
sLocalizedError -> rSingularityTreatment, rReferenceDefect, rImplementationDefect,
                   rCapacityLimit, rOptimizationFailure, rSamplingDeficiency, rSpecDefect
```

共 **7** 个候选。附带核实：`rDataDefect` **不在** `sLocalizedError` 的 admissible 集合内（它只对 `sBcResidual` 与 `sPinnCfd` 可用），因此本轮不将其列为候选；`rUndetermined` 是 `RootCauseClass` 的合法成员，作为 PART 12 Case B 的兜底。

| 候选 | 当前证据状态 |
|---|---|
| `rOptimizationFailure` | **SUPPORTED HYPOTHESIS**，待受控干预检验；干预被阻塞 |
| `rCapacityLimit` | **VIABLE**，未被排除；与 `rOptimizationFailure` 的判别正是被阻塞的那一步 |
| `rSamplingDeficiency` | 有一项反对证据（§2.2，EXPLORATORY），**未排除** |
| `rImplementationDefect` | Gate 3 十项 + 可信校验器的 10 个负面控制全 PASS，**未观察到**缺陷；未排除 |
| `rSpecDefect` | Gate 1/2 PASS，解析自验残差恒为 0，**未观察到**缺陷；未排除 |
| `rReferenceDefect` | 独立极坐标 FDM 观测阶 2.00、与解析解一致，**未观察到**缺陷；未排除 |
| `rSingularityTreatment` | 圆环无角点、无再入角；局部误差不集中在任一边界附近，**未观察到**奇异性问题；未排除 |

**没有任何一个候选被正式排除。** 正式排除需要 `DiagnosisRecord` 按 admissible matrix / excludes 规则逐项给出排除证据，而这要以受控干预为前提。

---

## 4. Optimizer / Scheduler State Audit（PART 4）

### 4.1 B-1：checkpoint 内容 — 只有权重

`experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu/runs/run-00.json` 的全部顶层字段：

```text
batchSize, collocationCount, collocationIndices, completed, determinism, devRelL2,
elapsedSeconds, finalLoss, hardBoundary, lossHistory, nanEncountered,
outputParameterization, perturbation, runIndex, seeds, stepsCompleted, stepsRequested,
weights
```

`weights` 是**模型** `state_dict` 的逐元素列表（`inner.{0,2,4,6,8}.{weight,bias}`）。全仓库 `pinn/experiments_annulus/` 与 `experiments/annulus/` 中，`state_dict()` 只出现一次——`pinn_torch_annulus.weights_of()`，取的是模型；`load_state_dict` 只出现一次——`model_from_weights()`。**没有** `optimizer.state_dict()`、**没有** `scheduler.state_dict()`、**没有** checkpoint 文件、**没有** resume 代码路径。

因此以下优化状态在 `train_run` 返回时被丢弃：

```text
Adam:        m_t, v_t, step 计数（偏差校正用）
Scheduler:   ExponentialLR.last_epoch
Batch:       torch.Generator 的 RNG 状态、shuffle 后的 order、cursor
```

PART 6 明确：`load weights + fresh Adam` **不得**冒充「只是多训练几步」，因为 `m_t, v_t` 也是优化状态的一部分。据此：

```text
EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE
```

### 4.2 B-2：学习率是 `lr(step, total_steps)`，不是 `lr(step)` —— PART 4 问题 A 的回答

实现（`pinn/experiments_annulus/pinn_torch_annulus.py`）：

```python
optimizer = torch.optim.Adam(model.parameters(), lr=float(opt_cfg["lr"]))
gamma = (float(opt_cfg["finalLr"]) / float(opt_cfg["lr"])) ** (1.0 / max(steps, 1))
scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=gamma)
```

`gamma` 由**总预算** `steps` 计算，于是

```text
lr(step) = lr0 * (finalLr / lr0) ** (step / steps_total)
```

**答案：`lr(step, total_steps)`——会随最终训练预算重新缩放。**

同一 step 在不同总预算下的学习率（`lr0 = 1e-3`，`finalLr = 1e-5`）：

| step | S = 120k | S = 180k | S = 240k |
|---|---|---|---|
| 1 | `9.9996e-04` | `9.9997e-04` | `9.9998e-04` |
| 30 000 | `3.1623e-04` | `4.6416e-04` | `5.6234e-04` |
| 60 000 | `1.0000e-04` | `2.1544e-04` | `3.1623e-04` |
| 90 000 | `3.1623e-05` | `1.0000e-04` | `1.7783e-04` |
| 120 000 | `1.0000e-05` | `4.6416e-05` | `1.0000e-04` |

正式 run 记录的实测 LR 与该式一致：step 1 为 `9.999616e-04`，step 120000 为 `1.000000e-05`。

在 step 60000 处，180k 预算的 LR 是 120k 预算的 **2.15 倍**；在 step 120000 处是 **4.64 倍**（240k 则为 **10.00 倍**）。也就是说，一次 180k 的 from-scratch run 与正式 120k run **在整个前 120k 步都不是同一条优化轨迹**。这正是 PART 4.1 描述的禁止混杂：

```text
120k run:  lr 1e-3 -> 1e-5 over 120k
180k run:  lr 1e-3 -> 1e-5 over 180k
→ 不能声称 "only training budget changed"
```

### 4.3 对备选方案的影响（如实说明，未自行设计）

PART 6 提到的备选是「a new from-scratch matched-budget intervention」。必须指出：**在当前代码下，from-scratch 的 180k / 240k run 同样不是 budget-only 干预**——因为 B-2 使 LR 轨迹随预算重新缩放。要让 from-scratch 干预成为单因素干预，需要一个**事前预注册的统一 continuation policy**（PART 5.1 已给出优先形式：前 120k 步走原 LR 轨迹，此后把 LR 保持在已达到的终值 `1e-5`），而这需要改动训练代码，从而改变 `codeHash`。

**本轮不实施、不设计、不预注册该方案**（PART 6：不要自行扩大设计）。上述仅为让用户的裁决建立在完整事实上。

---

## 5. Budget Intervention

**未执行。** 无 10-seed paired 表格可报告。

按 PART 7 预定的预算梯度 `B0 = 120000, B1 = 180000, B2 = 240000`（原预算的 1 / 1.5 / 2 倍，**不是**由 DAC-M0 的 `1.079e-03` 倒推）**未被预注册**——PART 7 以 exact continuation 可行为前提，该前提不成立。

## 6. DiagnosisRecord

**未生成。** 状态仍为 `FAILURE_RECORDED`，未进入 `DIAGNOSED`。

```text
RootCauseClass:  （未写入）
Formal verdict:  UNDETERMINED
```

7 个 admissible 候选**一个都未被正式排除**（第 3 节）。

## 7. Revision

**未执行。** `revision` 仍为 1，`specHash` 仍为 `4c8dfbc7238d…`，冻结配置一字未改（`steps` 仍为 `120000`）。PART 14 规定只有正式 `DiagnosisRecord` 支持 `rOptimizationFailure` 才允许 `DIAGNOSED -> REVISED`，该前提不成立。

## 8. Blind Validation

**未执行，且未触碰。** 账本状态复核（PART 13）：

```text
DAC-M0   SEALED -> OPENED -> BURNT      （历史，永久保留，不得重开）
DAC-M1   NEVER_SEALED                    未触碰
DAC-M2   NEVER_SEALED                    未触碰
DAC-M3   NEVER_SEALED                    未触碰
```

本轮**没有任何** claim set 生命周期事件写入；账本文件自上一轮提交以来未被修改。

## 9. Tier-1 / G6

**均未执行。** Tier-1 只在 Gate 5 PASS 之后进行；G6 的 `C_repro` 仍为 `BLOCKED`。Environment B 本轮未被访问。

## 10. Trust Vector / Claim

沿用上一轮的**实际值**，本轮未产生新的 TrustVector 或 ClaimGateDecision：

```text
math PASS   impl PASS   train PASS   physics PASS   external FAIL   repro BLOCKED
Highest Claim: BLOCKED
```

## 11. Tests / PRELOCK / Portability

本轮未改动 `pinn/`、`scientific_reference/`、`specs/` 下任何文件，也未改动冻结配置与正式驱动脚本，因此 `codeHash` 仍为 `8ee9b9236199…`。改动只落在报告 / 日志 / CHANGELOG / 记忆文件（均不在代码身份内）。

| 项目 | 治理虚拟环境 `.venv` | 训练解释器（mamba） |
|---|---|---|
| 全套 pytest | **1391 passed / 0 failed / 25 skipped** | — |
| annulus 补跑 | — | **7 passed / 0 failed** |
| poisson2d 补跑 | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，7/7** | — |
| portability | **0 hard binding / 1 configurable / 8 historical** | — |

PART 24 所列的十一项新测试**未新增**：其中十项针对尚未获授权、也尚不可执行的干预与 revision 流程；在干预设计被批准之前写测试，等于先固化一个未经批准的设计。

## 12. Newly Discovered

### BLOCKING

1. **B-1：正式训练不保存 optimizer / scheduler / batch-generator 状态**，只保存模型权重。→ nested continuation 不可执行，`EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE`。
2. **B-2：LR 调度依赖总预算**（`gamma` 由 `steps` 算出），因此 `lr = lr(step, total_steps)`。→ 任何「只改步数」的 from-scratch 对比都自带 LR 混杂；在 step 60000 处 180k 与 120k 的 LR 相差 2.15 倍。

两条合起来使本轮预定的受控干预**在当前代码下无法以单因素形式执行**。

### NON-BLOCKING

1. 既有 EXPLORATORY 的 budget response 趋势（10k / 20k / 40k）**比原先以为的更弱**：那三次是各自独立的 from-scratch run，各带被重新缩放的 LR 轨迹，因此混合了「更多步数」与「更慢衰减」两个因素。此前未写明，本报告更正。
2. 十个 seed 的最差局部单元全部位于中间两个径向环，最差/次差比 `1.00–1.66`：误差是平缓抬高的一片，不是奇异单元；**未观察到**孔边病理。
3. 失败 seed（seed 2）的局部与全局误差同步抬高（ACA-9 为中位数的 1.95 倍，ACA-1 为 2.00 倍）：整体更差，不是局部更差。

### AMENDMENT CANDIDATE

1. **（PART 21，登记不实施）** `D_dev` 在盲集被打开之前已含有足以预测局部验收失败的信息：本轮 D_dev 上局部统计量 worst 为 `1.038e-03`（> `1e-3`），与 D_claim 上的 `1.079e-03` 指向同一个 seed。**本轮不改 Gate 4、不改 TrustStatus、不改 claim 前置条件、不新增 Gate**——不能一边诊断 failure，一边修改「failure 应该在哪里被抓住」。待 annulus calibration 结束后再审。
2. **（PART 22，登记不实施）** `ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`；继续使用 `domainType = "other"` + `regions[].params`，不改 Constitution / schema，留待 L-shape 时统一处理。
3. **（本轮新增）** 训练记录**应当**保存 optimizer / scheduler / batch-generator 状态，否则任何「延长训练」类的受控干预在事后都不可能做成单因素干预。这是一个可复现性与可诊断性的结构缺口，不只影响圆环。登记为提案，**本轮不实施**（它会改变 `codeHash`）。
4. **（本轮新增）** LR 调度与总预算耦合（`gamma = (finalLr/lr0)^(1/steps)`）使「步数」不是一个可独立操纵的变量。若未来要把训练预算当作受控变量，需要一个事前预注册的、与总预算解耦的 schedule 定义。登记为提案，**本轮不实施**。

### NONE

其余未发现新问题。

## 13. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

并按 **PART 6** 停在干预之前，等待用户裁决：

```text
EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE
```

需要用户决定的是：是否授权一次 **from-scratch matched-budget intervention**，以及——因为 B-2——是否同时授权为其定义一个**与总预算解耦、事前预注册**的 LR continuation policy（PART 5.1 给出的优先形式是：前 120k 步走原 LR 轨迹，其后把 LR 保持在 `1e-5`）。该改动会改变 `codeHash`，属于方法基础设施的变更，不在本轮授权范围内。

在用户裁决之前，本轮**停止**：不做 capacity sweep、不做架构搜索、不做优化器搜索、不做更高预算 sweep、不开始 L-shape / BFS / Navier–Stokes / UCM / 传热，也不把 `rOptimizationFailure` 写成正式 `RootCauseClass`。
