# ANNULUS NESTED BUDGET INTERVENTION PREREGISTRATION（2026-09-19）

本文件在**任何 10-seed 诊断训练之前**提交。冻结后不得修改：预算梯度、LR policy、checkpoint 位置、判定规则、容差、数据防火墙、STOP 条件。

上游：[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](../../docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)、[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](../../docs/pinn-trust-loop/ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)。

## 0. 这不是什么

```text
不是 claim revision          不是 formal scientific attempt
不是新的 D_claim             不产生 TrustVector / ClaimGateDecision
不改 r1 的任何机器证据        不改阈值 / 架构 / 采样 / 优化器 / 几何 / 损失
```

r1 保持原样：`FAILURE_RECORDED`、`DAC-M0 BURNT`、`RootCause UNDETERMINED`、codeHash `8ee9b9236199…`。

本轮是一个**诊断实现身份**（diagnostic implementation identity），目的只有一个：

> 同一 architecture、同一 sampling、同一 optimizer、同一 0–120k 轨迹，仅仅继续优化，能否让 10/10 个 paired seed 在 D_dev 上同时满足既有的局部验收判据？

YES → 强判别性证据支持 `rOptimizationFailure`，并反证「capacity 必须增加」。
NO → 不得把 failure 归为 optimization；`rCapacityLimit` 保持 viable。

## 1. 不再尝试恢复旧 120k optimizer state

r1 的 run record 只保存模型权重，没有 Adam `m_t` / `v_t` / step、没有 scheduler state、没有 batch RNG、没有 shuffle 游标。因此**禁止**「load old weights + fresh Adam + 称之为 continuation」。本轮建立的是**前瞻性**新轨迹。

## 2. 冻结的方法值（与 r1 相同，逐项列出）

```text
architecture            4 x 64 tanh，outputParameterization (R^2-s)(s-a^2)N   不变
collocation             1024（pool 2048，poolSeed 20261330）                   不变
batchSize               512                                                    不变
optimizer               Adam, lr 1e-3, finalLr 1e-5, threads 1                 不变
loss                    单一 pde 项，权重 1.0                                   不变
geometry                annulus-a035-R1-v1, a = 0.35, R = 1                    不变
thresholds              ACA-1..ACA-9 与 PH1..PH8 全部                           不变
localized contract      criterion ACA-9 / statistic maxCellRmsErrorOverReferenceRms
                        normalization globalReferenceRms / partition annulusEqualAreaCells
                        radialBins 4 / angularSectors 16 / operator <= / threshold 1e-3
                        seedPolicy every-seed                                   不变
epsilonSpec             1e-3；worstSeedFactor 3.0；dispersionLimit 1.0          不变
```

相对 r1 只有**两处**改动，且都不是自由参数：

```text
optimizer.steps         120000 -> 240000
optimizer.lrPrefixSteps 新增 = 120000      （把 LR schedule 与总预算解耦）
```

## 3. LR policy（与 total budget 解耦）

```text
lr(t) = lr0 * (lrf / lr0) ** ( min(t, 120000) / 120000 )      lr0 = 1e-3, lrf = 1e-5

0 – 120k    完全复现 r1 的 exponential schedule 1e-3 -> 1e-5
> 120k      保持 lr = 1e-5 直到 240k
```

总预算**不参与** LR 计算：`lr = lr(step)`，不再是 `lr = lr(step, total_steps)`。

**实现语义高于纸面公式（PART 4）**：`torch.optim.lr_scheduler.ExponentialLR.get_lr()` 返回 `group["lr"] * gamma`，即**逐步相乘**，不是求 `lr0 * gamma ** t`。两者在数万次乘法后相差 1–2 ULP。因此等价性以**迭代语义**为准，且 `pinn.experiments_annulus.pinn_torch_annulus.learning_rates()` 也按迭代实现。

实现方式：`gamma = (lrf/lr0) ** (1/120000)`（与 r1 逐位相同的浮点数），scheduler 在推进满 120000 次后**停止推进**，学习率就停在它已经到达的终值。

**已完成的事前验证**：新 schedule 逐位复现 r1 seed 0 记录的**全部 241 条**学习率，包含 step 1 = `9.99961624318148777e-04` 与 step 120000 = `9.99999999996725452e-06`，在总预算 120k / 180k / 240k 下结果完全相同。

## 4. 预算梯度与 checkpoint

```text
B0 = 120000      B1 = 180000      B2 = 240000
```

即 r1 预算的 1 / 1.5 / 2 倍。**不是**由 DAC-M0 的 seed 2 值 `1.079e-03` 倒推。

```text
最大诊断预算 = 240000
```

看到 240k 结果后**不得**继续 300k / 360k / 480k。driver 中不存在任何提升预算的代码路径（有测试钉死）。

每个 paired seed **只启动一次训练**，`0 -> 240000`，在三个预算处保存完整 checkpoint 并评估。因此 180k 是其自身 120k 状态的 exact continuation，240k 是其自身 180k 的 exact continuation；**不分别初始化三次网络**。

## 5. Checkpoint 内容

```text
modelState                model.state_dict()
optimizerState            Adam m_t, v_t, step 计数, param_groups（含 lr）
scheduler                 gamma, lastEpoch, prefixSteps, currentLr
currentStep
batchGeneratorState       torch.Generator 字节状态
order / cursor            当前置换与游标
rngStates                 全局 CPU（及 CUDA）RNG 状态
seeds / device / schemaVersion
```

全部以 JSON 存储：需要特定库版本才能读的证据，是会悄悄失效的证据。

## 6. Resume fidelity（已在本预注册之前完成并 PASS）

夹具：连续 `0 -> 2000` 对照 `0 -> 1000` → 存盘 → 经 JSON 往返重载 → `1000 -> 2000`；LR prefix 故意设为 1200，落在断点与终点之间，使重载的后半段跨越「停止衰减、开始保持」的那一点。

合同为 **bitwise**，依据是本机已实测的确定性：r1 集合在同一设备、同一 seed 下重跑，权重最大绝对差 **0.0**、dev 误差完全相同。接受更松的容差等于接受比代码已证明的更少。

结果 **PASS（11 项全部逐位相同）**：参数、Adam 状态、scheduler 位置与学习率、batch 生成器、order/cursor、RNG、D_dev 指标、断点处状态、重载后的 loss/lr 历史。记录见 `experiments/annulus/diagnosis/RESUME_FIDELITY.json`。

## 7. Paired seed 设计

使用 r1 正式 attempt 的 **10 个 seed identities**，不改一个：

```text
init   = 20261400 + i        sample = 20261500 + i        batch = 20261600 + i,  i = 0..9
```

目的不是再做 claim，而是 **within-seed causal comparison**。数据同样是 r1 的**已登记** D_train / D_dev，逐个用记录的 sha256 对 ProblemDefinition 校验；不是「另取一份相似的点集」。

## 8. PART 10 基线等价性（前置门槛）

新轨迹在 120k 处必须与 r1 同一 seed 在 D_dev 上一致。记录

```text
ΔE_i = E_new(i, 120k) - E_old(i, 120k)
```

**容差（事前写定）**：主判据为 **bitwise 相等**；备用相对容差 `|ΔE_i| / |E_old| <= 1e-12`，仅为将来在非逐位可复现的主机上仍可判定而保留。依据同第 6 节的实测确定性，不是临时发明的宽容差。

不一致即说明「只改了 checkpoint 基础设施与 schedule 表示」这一假设不成立：

```text
DIAGNOSTIC INVALID -> STOP
```

不得继续用 180k / 240k 做因果解释。

## 9. 测量（每 seed × 每预算，全部在 D_dev 上、CPU 评估）

```text
global rel L2
localized criterion value (maxCellRmsErrorOverReferenceRms) 与其 PASS/FAIL
normalized residual RMS
worst local cell（单元编号与其 RMS 误差）
loss / pde loss
learning rate
```

输出 10 × 3 paired table。局部判据继续使用**已硬化的同一份合同**，不新造标准。

## 10. B* 判定规则（运行前冻结）

候选预算 `{180000, 240000}`。`B*` 定义为其中**第一个**使 10/10 paired seed 在 D_dev 上**同时**满足以下三条的最小预算：

1. 既有 global training reliability 条件（Constitution 10.1 的 `seed_statistics`，epsilonSpec 1e-3、worstFactor 3.0、dispersionLimit 1.0，status 必须为 PASS）；
2. 既有 localized acceptance criterion（ACA-9，阈值 1e-3，`every-seed`）；
3. 无 divergence、无 invalid evidence（全部 finite、全部训练完成、divergent = 0）。

```text
180k all-pass                      -> B* = 180k
180k not all-pass 且 240k all-pass -> B* = 240k
240k 仍不 all-pass                 -> no B*
```

**不得以平均数替代 every-seed。** 另须报告 120k / 180k / 240k 上 global 与 local 的 median 与 worst 变化，不另造「改善百分比阈值」。

## 11. 数据防火墙

```text
DAC-M0 = BURNT（永久）    DAC-M1 / M2 / M3 = NEVER_SEALED
```

诊断期间不得发生任何 claim ledger event。driver 在开始前与结束后各记录账本文件的 sha256 与事件序列并比对。禁止读 D_claim 来选择 `B*` / schedule / architecture / optimizer。DAC-M0 仅可用于解释**为什么要做诊断**，不用于调参。局部判据合同自身也拒绝 `evaluationSet != "dev"`。

## 12. 代码身份

本轮允许修改 checkpoint / resume 基础设施、fixed-prefix schedule 实现、诊断 driver 与测试；这会改变 `codeHash`，属预期行为。

```text
r1（不变）           codeHash 8ee9b9236199996fe95684b42bb6a247717f07bb5845437ac7c85ff7978b550e
诊断（本轮）         codeHash 124c31eb46aeee6c0e8f0c1232f3e49f9b24f2f41a5869e783527668d2525e3b
诊断配置             experiments/annulus/diagnosis/config_nested_budget.json
                     sha256 f6a89e1df181342d6adb4e2f8ec1741e57155db7b63ae920de4d83fad49014ba
声明的 driver        experiments/annulus/run_nested_budget_diagnosis.py
```

## 13. 根因解释规则

**CASE A — B\* 存在**：构成支持 `rOptimizationFailure` 的**强判别性**证据，因为同一 representational capacity 已实证达到判据，`rCapacityLimit` 不再是必要解释。但**不得**因为 B\* 存在就跳过其余六个 admissible candidate 的记录义务——`sLocalizedError` 在 Constitution 1.2 下的 admissible 集合是 `rSingularityTreatment / rReferenceDefect / rImplementationDefect / rCapacityLimit / rOptimizationFailure / rSamplingDeficiency / rSpecDefect`。只有满足正式 DiagnosisRecord 的全部要求后，才能写入 `RootCauseClass = rOptimizationFailure`。

**CASE B — 240k 仍无 B\***：立即 STOP。Root Cause 保持 `UNDETERMINED`，`rCapacityLimit` 保持 viable。不得自行加大网络、换激活、换优化器或提高预算。

## 14. STOP 条件

任一条成立立即停止，不得绕过：

```text
resume fidelity 失败
120k prefix 等价性失败
claim set 被触碰
invalid evidence
240k 仍无 B*
unexpected regression
```

**即使 B\* 存在且 DiagnosisRecord 成立，也先 STOP 并报告**，不自行启动 revision 2 正式 run，不消耗 DAC-M1。

## 15. 事前披露

1. 本轮 GPU 训练约需 12 小时（r1 的 10 × 120k 用了 5.9 小时）。事前设备基准已如实记录 GPU 在本负载上并不更快；仍使用 CUDA，是为了让 120k prefix 与 r1 的比较落在同一设备上，从而可以用逐位判据。
2. 30 个完整 checkpoint 约 27.4 MB。这是本轮的核心证据——r1 之所以无法回溯续跑，正是因为没有它们。
3. 诊断的 `steps = 240000` 不是一个「调出来让它通过」的值：候选集合、最大值与 B\* 规则都在看到任何诊断结果之前写定于本文件。
4. 若最终确认 `rOptimizationFailure` 并获授权进入 revision 2，方法变更**不应**再被描述为「only changed field = steps」。相对 r1，它实际包含：① 延长的训练预算 B\*；② 显式的 120k 之后 LR continuation policy。更准确的定义是 **optimization-trajectory extension**（保留原 0–120k 前缀 + 额外的 terminal-LR 优化至 B\*），一个受控的 revision package。

---

## 16. 追加勘误：第 12 节记录的诊断 codeHash 有误（2026-09-19，追加不改写）

本节是**追加**。第 0–15 节一字未改：方法、预算梯度、LR policy、checkpoint 位置、B\* 规则、容差、防火墙、STOP 条件全部保持冻结。这里更正的是一条**被记录的事实**。

第 12 节写的诊断 codeHash

```text
124c31eb46aeee6c0e8f0c1232f3e49f9b24f2f41a5869e783527668d2525e3b      （错误）
```

正确值是正式诊断 run 在 `identity.json` 中记录的

```text
b7f9fe73e0b1ae9b17da74c8260ce638f7fcf0e97524ba39017ceccb0f2e01f3      （正确，manifest 91 项）
```

**原因（已机器复核，不是猜测）**：第 12 节的值是在**提交之前**算的，而 `code_manifest()` 枚举的是 **git 已跟踪**的文件（`git ls-files`）。当时新模块 `pinn/experiments_annulus/checkpoint_annulus.py` 还是 untracked，于是**根本没有进入清单**。把它从当前清单中移除后重算，得到的正是 `124c31eb46ae…` —— 逐位吻合，因果确定。

真实的诊断代码身份是 `b7f9fe73e0b1…`，它包含 `checkpoint_annulus.py`；正式诊断 run 全程使用的就是这一个，`identity.json` 与 `DIAGNOSIS.json` 记录的也是它。**没有任何训练在错误的身份下进行**。

### 这是一个真实的治理缺口，登记为 AMENDMENT CANDIDATE（本轮不实施）

1. `code_manifest()` 只看 git 已跟踪文件，因此**一个全新的、未跟踪的 `pinn/` 下模块会静默地落在代码身份之外**；
2. `workspace_dirty_paths()` 用的是 `git status --porcelain --untracked-files=no`，因此**也不会**把它报成脏；
3. `assert_code_identity_complete()` 校验的是声明的 extra 文件存在、以及清单与磁盘字节一致——它无法注意到一个**从未被列入**的文件。

三者叠加的后果是：若在一棵含有「新增但未提交的 `pinn/` 模块、且该模块确实被 run 导入」的树上启动正式 attempt，记录下来的 `codeHash` 会遗漏它，而**没有任何机制会报警**。本轮之所以被发现，只是因为提交之后重算了一次。

**对历史证据无影响**：r1 正式 attempt 在 `gitHead 400f13d` 的干净树上启动（`git status --porcelain` 为空，该命令**包含**未跟踪文件），`workspaceDirty = false`，其 codeHash `8ee9b9236199…` 不受此缺口影响。

**本轮不修**：修它要动 `pinn/experiments/common.py`，会改变代码身份，而现在正有一个诊断 run 在这个身份下运行；且在诊断进行当中修改「身份是怎么算的」本身就不当。与此前登记的其余提案一并待审。
