# Annulus Nested Budget Intervention Report（2026-09-20）

执行负责人：Claude（队长）。对象：圆环 Gate 5b 失败（`observedSignatures = ["sLocalizedError"]`）的受控训练预算干预。
预注册：[ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md](../../experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md)（含第 16 节 codeHash 勘误）。
上游：[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)、[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)。

本轮**没有**打开任何 claim set、**没有**写入任何账本事件、**没有**修改 r1 的任何机器证据、**没有**改动阈值 / 架构 / 采样 / 优化器 / 几何 / 损失 / 局部判据合同、**没有**升 revision、**没有**产生 TrustVector 或 ClaimGateDecision、**没有**在 240k 之后继续加预算。

---

## 1. Executive

```text
120k prefix equivalence:  PASS        （10/10 逐位相等）
resume fidelity:          PASS        （11 项检查全部逐位相等）
B*:                       180k
Root Cause:               UNDETERMINED
```

**B\* 存在**：同一 4×64 tanh、同一采样、同一优化器、同一 0–120k 轨迹，仅仅继续优化到 180000 步，就让 **10/10** 个 paired seed 在 D_dev 上同时满足既有的局部验收判据 ACA-9 与既有的 training reliability 条件。这是支持 `rOptimizationFailure`、并反证「capacity 必须增加」的**强判别性证据**。

**但正式 RootCauseClass 仍是 `UNDETERMINED`**，因为 Constitution 1.2 的 DiagnosisRecord 要求尚未满足。`discriminatingExperiment.excludes` 必须为该 signature 下**其余每一个** admissible 根因都指名一个排除实验（schema 原文：a root cause is never chosen, it is what is left），`sLocalizedError` 的 admissible 集合有 7 个成员，本轮只用实验排除了其中 **1 个**（`rCapacityLimit`）。详见第 4 节。按预注册第 13 节 CASE A 的末句，条件未满足即**不得**写入 `rOptimizationFailure`。

```text
Annulus Calibration:  NOT YET PASS
Highest Claim:        BLOCKED
Recommendation:       REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

---

## 2. 前置门槛

### 2.1 Resume fidelity：PASS

夹具：连续 `0 → 2000` 对照 `0 → 1000` → 存盘 → JSON 往返重载 → `1000 → 2000`，LR prefix 故意设为 1200（落在断点与终点之间），使重载的后半段跨越「停止衰减、开始保持」那一点。合同为 **bitwise**，依据是本机实测的确定性（r1 同 seed 同设备重跑，权重最大绝对差 **0.0**）。

11 项全部 PASS：模型参数 `max|dW| = 0.0`（12752 个值）、Adam 状态 `0.0`（25514 个值）、scheduler 位置、学习率（跨越 prefix 后保持终值）、batch 生成器字节状态、order/cursor、全局 RNG、D_dev 指标、断点处状态、重载后的 loss/lr 历史、`resumedFromStep`。记录：`experiments/annulus/diagnosis/RESUME_FIDELITY.json`。

### 2.2 120k prefix equivalence：PASS（10/10 逐位）

| seed | r1 @120k devRelL2 | 新轨迹 @120k | Δ |
|---|---|---|---|
| 0 | 1.62231774002202404e-04 | 同左 | 0 |
| 1 | 1.87432730527999059e-04 | 同左 | 0 |
| 2 | 3.87396529747795573e-04 | 同左 | 0 |
| 3 | 1.89805321144054332e-04 | 同左 | 0 |
| 4 | 1.57843726300633446e-04 | 同左 | 0 |
| 5 | 1.83257150048191358e-04 | 同左 | 0 |
| 6 | 1.81269058362817876e-04 | 同左 | 0 |
| 7 | 1.73505697022779026e-04 | 同左 | 0 |
| 8 | 2.24073904707458371e-04 | 同左 | 0 |
| 9 | 1.98203746997927286e-04 | 同左 | 0 |

不止全局误差：新轨迹 @120k 的**局部统计量**也与 r1 记录的 D_dev 逐 seed 值完全一致（`4.0045e-04 / 3.7569e-04 / 1.0383e-03 / 4.0672e-04 / 4.9085e-04 / 4.1501e-04 / 3.5692e-04 / 4.9326e-04 / 4.7401e-04 / 3.9996e-04`）。因此「只改了 checkpoint 基础设施与 schedule 表示，方法未变」这一假设**成立**，180k / 240k 的结果可以被作因果解读。

LR schedule 本身的等价性另有机器验证：迭代语义逐位复现 r1 记录的**全部 241 条**学习率，且在总预算 120k / 180k / 240k 下结果相同（第 10 节测试）。

---

## 3. Budget Intervention

每个 paired seed **只启动一次**训练，`0 → 240000`，在三个预算处保存完整 checkpoint 并在 CPU 上评估。180k 是其自身 120k 状态的 exact continuation，240k 是其自身 180k 的 exact continuation。seed identities 为 r1 的原样十组，数据为 r1 的**已登记** D_train / D_dev（逐个以 sha256 对 ProblemDefinition 校验）。用时 9.15 小时（CUDA）。

### 3.1 10 × 3 paired table（D_dev，阈值 ACA-9 = 1e-3，`every-seed`）

| seed | 120k relL2 | 120k ACA-9 | 180k relL2 | 180k ACA-9 | 240k relL2 | 240k ACA-9 |
|---|---|---|---|---|---|---|
| 0 | 1.622e-04 | 4.004e-04 PASS | 1.719e-04 | 4.758e-04 PASS | 8.677e-05 | 2.371e-04 PASS |
| 1 | 1.874e-04 | 3.757e-04 PASS | 3.527e-04 | 6.541e-04 PASS | 9.830e-05 | 2.196e-04 PASS |
| **2** | 3.874e-04 | **1.038e-03 FAIL** | 2.774e-04 | 7.312e-04 PASS | 2.891e-04 | 6.801e-04 PASS |
| 3 | 1.898e-04 | 4.067e-04 PASS | 2.771e-04 | 6.265e-04 PASS | 1.446e-04 | 3.126e-04 PASS |
| 4 | 1.578e-04 | 4.908e-04 PASS | 2.147e-04 | 4.400e-04 PASS | 1.071e-04 | 3.079e-04 PASS |
| 5 | 1.833e-04 | 4.150e-04 PASS | 2.874e-04 | 4.771e-04 PASS | 1.037e-04 | 2.720e-04 PASS |
| 6 | 1.813e-04 | 3.569e-04 PASS | 1.550e-04 | 3.519e-04 PASS | 1.937e-04 | 4.002e-04 PASS |
| 7 | 1.735e-04 | 4.933e-04 PASS | 1.069e-04 | 2.839e-04 PASS | 9.949e-05 | 2.848e-04 PASS |
| 8 | 2.241e-04 | 4.740e-04 PASS | 1.171e-04 | 2.428e-04 PASS | 8.934e-05 | 2.164e-04 PASS |
| 9 | 1.982e-04 | 4.000e-04 PASS | 1.326e-04 | 3.087e-04 PASS | 1.471e-04 | 2.970e-04 PASS |

### 3.2 每预算判定（预注册规则，运行前冻结）

| 预算 | reliability | 成功数 | relL2 median | relL2 worst | relL2 IQR | ACA-9 median | ACA-9 worst | localized | allPass |
|---|---|---|---|---|---|---|---|---|---|
| 120000 | PASS | 10/10 | 1.8534e-04 | 3.8740e-04 | 2.470e-05 | 4.1501e-04 | **1.0383e-03** | 9/10（seed 2 失败） | **False** |
| **180000** | PASS | 10/10 | 1.9329e-04 | 3.5270e-04 | 1.448e-04 | 4.7576e-04 | 7.3121e-04 | **10/10** | **True** |
| 240000 | PASS | 10/10 | 1.0537e-04 | 2.8910e-04 | 4.878e-05 | 2.9701e-04 | 6.8008e-04 | 10/10 | True |

```text
B* = 180000        （最小的、使 10/10 同时满足三项条件的预注册预算）
```

### 3.3 必须如实说明的三点

1. **改善不是单调的，180k 处的 median 反而更差**。全局 median 从 `1.8534e-04`（120k）升到 `1.9329e-04`（180k），到 240k 才降到 `1.0537e-04`；ACA-9 的 median 同样先升（`4.1501e-04 → 4.7576e-04`）后降（`2.9701e-04`）。逐 seed 看，seed 1 / 3 / 5 在 180k 明显变差，seed 6 在 240k 比 180k 差。**「步数越多越好」不成立**；真实形态是在终端学习率 `1e-5` 上继续游走。
2. **180k 通过，靠的是最差 seed 下移，同时离散度上升**。IQR 从 `2.470e-05` 扩大到 `1.448e-04`（5.9 倍），而 worst 从 `1.0383e-03` 降到 `7.3121e-04`。`every-seed` 规则问的正是 worst，所以判定成立——但这意味着 180k 的通过**部分依赖这次游走恰好把 seed 2 带到阈值之下**。240k 的证据更干净：median、worst、IQR 三者同时改善。
3. **余量很薄**。180k 的 worst 对阈值余量 `1.37×`，240k 为 `1.47×`。作为对照，已 CLOSED 的正方形标定在同一判据上有 `6.4×` 余量。

### 3.4 局部热点的位置没有改变

十个 seed、三个预算共 30 个最差单元，**29 个**落在中间两个径向环（bin 1 / bin 2），**1 个**落在紧贴内孔的 bin 0（seed 1 在 240k，单元 `0,15`），**0 个**落在紧贴外圆的 bin 3。这与 r1 的观察一致：双分量硬约束把两条圆周钉在 `~2e-16`，误差被推离两条边界。继续优化没有改变误差的空间结构，只改变了它的大小。

### 3.5 图

`experiments/annulus/diagnosis/nested-budget-r1-paired/plots/` 共 7 张，全部取自已登记的 `DIAGNOSIS.json`，不重算、不加载模型：全局误差逐 seed 轨迹、局部判据逐 seed 轨迹（含阈值与 B\*）、前缀等价性、失败 seed 单独轨迹、median/worst 汇总、残差对预算、离散度对预算。

---

## 4. DiagnosisRecord

### 4.1 候选集合（读自实际 admissible matrix，未缩减）

`pinn.governance.state_machine.admissible_root_causes("1.2")` 对 `sLocalizedError` 给出 **7** 个候选：

```text
rSingularityTreatment  rReferenceDefect  rImplementationDefect  rCapacityLimit
rOptimizationFailure   rSamplingDeficiency  rSpecDefect
```

（另核实 `rDataDefect` **不在**该 signature 的集合内。）

### 4.2 排除义务的实际状态

Constitution 1.2 的 `discriminating_experiment_errors` 要求：**为其余每一个 admissible 根因指名一个排除实验**，且 `excludes.<cause>.experiment` 必须匹配 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`——即一个 Tier-1 扰动编号或一个正式 attempt id。逐项核对：

| 候选 | 现有证据 | 是否满足排除义务 |
|---|---|---|
| `rCapacityLimit` | **本轮干预**：同一容量在 180k 处 10/10 满足判据 | **满足** |
| `rSamplingDeficiency` | EXPLORATORY 密度探针（2.76× 配置点无改善） | **不满足**：EXPLORATORY 非正式实验；Tier-1 的 P1 / P6 / P7 / P11 未跑 |
| `rImplementationDefect` | Gate 3 十项 + 可信校验器 10 个负面控制全 PASS | **不满足**：Gate 不是 discriminating experiment；P4（float32）未跑 |
| `rSpecDefect` | Gate 1 / Gate 2 PASS，解析自验残差恒为 0 | **不满足**：无 P 编号或 exp id 可指 |
| `rReferenceDefect` | 独立极坐标 FDM 观测阶 2.0016 / 2.0004，与解析解一致 | **不满足**：同上 |
| `rSingularityTreatment` | 无角点 / 再入角；热点不在任一边界附近（§3.4） | **不满足**：观察，不是实验 |

**6 项义务中满足 1 项。** 因此无法生成通过校验的 DiagnosisRecord。这不是形式主义：其余五项的证据全部是「没有观察到缺陷」，而**证据的缺席不是排除**。

（以上不是推理，是对 `pinn.governance.trust_loop.validate_diagnosis_record` 的实测：构造候选记录后逐条读取它返回的错误。）

### 4.3 正式判定

```text
RootCauseClass:  （未写入）
Formal verdict:  UNDETERMINED
Evidence:        rOptimizationFailure 获强判别性支持；rCapacityLimit 已被实验排除；
                 其余五个候选未被排除，仍然 viable
```

状态仍为 `FAILURE_RECORDED`，**未进入 `DIAGNOSED`**。

### 4.4 一个结构性发现（登记为 AMENDMENT CANDIDATE，本轮不实施）

上述五项排除义务实际上要求 **Tier-1 扰动集合**（P1 / P4 / P6 / P7 / P11 / P16 等），而协议规定 Tier-1 **只在 Gate 5 PASS 之后**执行。于是出现一个闭环：

> 一次**失败** run 的正式诊断，需要协议只在**成功** run 之后才安排的实验。

这不是本轮造成的，也不该由本轮单方面解决——它要么需要一条「诊断用 Tier-1」的通路，要么需要承认失败 run 的 DiagnosisRecord 在 MVP 下通常只能落到 `rUndetermined`。登记待审。

---

## 5. Revision

**未执行。** `revision` 仍为 1，`specHash` 仍为 `4c8dfbc7238d…`，冻结配置 `exp_annulus_baseline.json` 一字未改（`steps` 仍为 `120000`，无 `lrPrefixSteps`）。按 PART 16，只有正式 DiagnosisRecord 确认 `rOptimizationFailure` 才允许 `revision 1 -> revision 2`，该前提不成立。

预注册第 15.4 条的事前记录仍然有效，供将来使用：若日后获授权进入 revision 2，方法变更**不应**被描述为「only changed field = steps」。相对 r1 它实际包含 ① 延长的训练预算 B\*；② 显式的 120k 之后 LR continuation policy。准确的定义是 **optimization-trajectory extension**（保留原 0–120k 前缀 + 额外的 terminal-LR 优化至 B\*）。

```text
r1 codeHash          8ee9b9236199996fe95684b42bb6a247717f07bb5845437ac7c85ff7978b550e （未变）
诊断 codeHash        b7f9fe73e0b1ae9b17da74c8260ce638f7fcf0e97524ba39017ceccb0f2e01f3
诊断配置             experiments/annulus/diagnosis/config_nested_budget.json
```

诊断身份**不是** claim revision：它没有打开 claim set，不产生 claim。

## 6. Blind Validation

**未执行，且未触碰。** driver 在开始前与结束后各记录账本 sha256 与事件序列并比对，结果 `unchanged = True`：

```text
DAC-M0   SEALED -> OPENED -> BURNT     （历史，永久保留，不得重开）
DAC-M1   NEVER_SEALED                   未触碰
DAC-M2   NEVER_SEALED                   未触碰
DAC-M3   NEVER_SEALED                   未触碰
账本事件  ['SEALED', 'OPENED']           本轮无新增
```

局部判据合同自身也拒绝 `evaluationSet != "dev"`；测试另钉死 driver 源码中不得出现 `claim_grids` / `claim_quadrature` / `claim_pointwise` / `make_event` / `write_ledger` / `claim_evaluation` 等标识。

## 7. Tier-1

**未执行。** 只在 Gate 5 PASS 之后进行。参见 §4.4：这正是排除义务无法满足的原因。

## 8. G6

**未执行。** `C_repro` 仍为 `BLOCKED`。Environment B 本轮未被访问。

## 9. Trust Vector / Claim

本轮**未产生**新的 TrustVector 或 ClaimGateDecision。r1 的实际值保持不变：

```text
math PASS   impl PASS   train PASS   physics PASS   external FAIL   repro BLOCKED
Highest Claim: BLOCKED
```

## 10. Tests / PRELOCK / Portability

| 项目 | 治理虚拟环境 `.venv` | 训练解释器（mamba，torch 2.12.1+cu126） |
|---|---|---|
| 全套 pytest | **1414 passed / 0 failed / 26 skipped** | — |
| annulus 补跑 | — | **24 passed / 0 failed** |
| poisson2d 补跑 | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，7/7** | — |
| portability | **0 hard binding / 1 configurable / 8 historical** | — |

上轮基线为 1391 / 25 与 annulus 7 项；本轮净增 **23** 项治理测试（schedule 等价性、预算独立性、B\* 规则、无升级路径、防火墙、配对 seed、r1 证据不变）与 **17** 项训练解释器测试（checkpoint 内容、JSON 往返、resume 逐位一致、拒绝异种 checkpoint、LR 保持）。

## 11. Newly Discovered

### BLOCKING

**无。** `B*` 存在且前置门槛全部 PASS；阻止正式判定的是排除义务未满足（§4.2），这是**已知的协议要求**，不是新缺陷。

### NON-BLOCKING

1. **继续优化不单调改善**：180k 的 median 比 120k 更差，IQR 扩大 5.9 倍，240k 才三项同时改善（§3.3）。`B* = 180k` 的通过部分依赖最差 seed 恰好下移。
2. **误差的空间结构基本不随预算改变，但不是「一个都没有」**：30 个最差单元中 29 个在中间两个径向环，1 个（seed 1 @240k，单元 `0,15`）紧贴内孔（§3.4）。
3. **余量很薄**：180k `1.37×`、240k `1.47×`，对比正方形标定的 `6.4×`。
4. **既有 budget response 证据的强度已更正**：10k / 20k / 40k 三次探针是各自独立的 from-scratch run 且 LR 轨迹随预算重新缩放，混合了「更多步数」与「更慢衰减」——上一轮已记录，本轮的固定前缀设计正是为消除该混杂。

### AMENDMENT CANDIDATE

1. **（新）失败 run 的诊断与 Tier-1 的时序闭环**：正式 DiagnosisRecord 的排除义务需要 Tier-1 扰动，而 Tier-1 只在 Gate 5 PASS 后执行（§4.4）。
2. **（新）未跟踪文件静默落在代码身份之外**：`code_manifest()` 只枚举 git 已跟踪文件，`workspace_dirty_paths()` 用 `--untracked-files=no`，`assert_code_identity_complete()` 无法察觉从未被列入的文件。本轮预注册记录的 codeHash 因此一度写错（已在预注册第 16 节追加勘误并机器坐实因果）。r1 不受影响。
3. **（承前）Gate 4 不筛查局部判据**，尽管 D_dev 有能力测量它。
4. **（承前）`ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`**。
5. **（承前）训练记录应保存 optimizer / scheduler / batch RNG 状态** —— 本轮已对诊断路径实现，但尚未成为正式 attempt 的要求。
6. **（承前）LR 调度与总预算耦合** —— 本轮已提供 `lrPrefixSteps` 解耦，但缺省行为仍是耦合的（为不改变历史含义而刻意保留）。

### NONE

其余未发现新问题。

## 12. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

`B*` 存在是一个实质进展：它以配对、逐位可核验的方式证明**同一容量确实能达到既有判据**，从而把 `rCapacityLimit` 排除在必要解释之外。但根因尚未正式判定，圆环标定仍未通过，Highest Claim 仍为 BLOCKED。

按 PART 21 与 PART 26：**即使 B\* 存在且证据指向 `rOptimizationFailure`，本轮到此停止**。不自行启动 revision 2 正式 run、不消耗 DAC-M1、不做 capacity sweep / 架构搜索 / 优化器搜索 / 更高预算 sweep、不开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热。

需要用户与外部评审裁决的是：

1. **五项未满足的排除义务如何处理**——是授权一次「诊断用 Tier-1」（在 Gate 5 未 PASS 的前提下执行扰动集合，仅用于排除、不产生 claim），还是接受失败 run 的 DiagnosisRecord 在当前 MVP 下只能落到 `rUndetermined`。
2. **若要进入 revision 2，B\* 取 180k 还是 240k**。180k 是预注册规则给出的答案（最小预算）；240k 的证据更干净（median / worst / IQR 三者同时改善，余量 1.47× 对 1.37×），但选它等于偏离预注册的最小性规则。这是一个需要明确裁决的取舍，**不应由执行者单方面决定**。


---

## 13. 追加勘误：一处事实错误（2026-09-20，追加不改写）

本节是追加。机器证据 `DIAGNOSIS.json` 一字未动——它从一开始就记录着正确的数据；错的是本报告的散文。

§3.4 与 §11 NON-BLOCKING 2 原写「30 个最差单元**全部**落在中间两个径向环，**没有一个**紧贴内孔或外圆」。这是错的。逐条核对 `DIAGNOSIS.json`：

```text
30 个最差单元中
  29 个在 bin 1 / bin 2
   1 个在 bin 0（紧贴内孔）：seed 1 @ 240000，单元 0,15
   0 个在 bin 3（紧贴外圆）
```

错误的来源：我在一次进度汇报里打印过这 30 个单元的清单，随后写报告时按印象概括为「全部」，**没有逐条复核**那份清单。正文两处已就地更正为 29 / 1 / 0。

**这不是无关紧要的更正**。该说法正是「圆环几何没有制造孔边病理」这一论断的证据，而本轮 `exp-annulus-dx-singularity` 的预注册判定 G2 要求「30 个最差单元中落在 bin 0 或 bin 3 的个数 == 0」。按真实数据，G2 **不成立**（1 ≠ 0），因此 `rSingularityTreatment` **未被排除**。详见
[ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md](ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md)。

需要说明的是，r1 标定报告与预算诊断报告中关于「**十个** seed 的最差单元全部在中间两环」的说法**是正确的**——r1 的十个 seed 在 120k 处确实全部落在 bin 1 / bin 2。出错的只是 Phase II 中覆盖 30 个单元的那句概括。

---

## 14. 追加勘误：本报告把「不再是必要解释」写成了「已排除」（2026-09-21，追加不改写）

本节是**追加**。机器证据（`DIAGNOSIS.json`、checkpoint、`B* = 180k`、逐位相等的 120k 前缀）一字未动——它们都是真实测量。错的是本报告对它们的**形式定性**。

§1 与 §4.2 写道嵌套预算干预「把 `rCapacityLimit` 排除在必要解释之外」「已排除（干预式，上一轮）」，§4.1 的表格把它记为**科学状态：已排除**。这是越权。

`pinn/governance/state_machine.py` 的 `FACTOR_CONTROL = {"capacity": "architecture", "sampling": "sampling"}`，配合 `MIN_INTERVENTION_LEVELS = 3` 与 `MIN_INTERVENTION_SEEDS = 3`：一次**容量**干预必须改变**架构**，至少三档、每档至少三个 seed。本干预全程把架构钉死在 `4×64 tanh`，改变的是 `optimizer.steps`——**容量档位数 = 0**。它从未改变过容量这个变量，因此不可能排除它。

而 2026-09-19 预注册 §13 CASE A 的原文恰恰是准确的：「同一 representational capacity 已实证达到判据，`rCapacityLimit` **不再是必要解释**」，并把 `rCapacityLimit` **逐字列进**六项不得跳过的记录义务中。**「不再是必要解释」≠「已排除」**——前者说的是它不再被逼着为观测负责，后者说的是实验把它排除掉了。本报告把前者写成了后者。

更正：`rCapacityLimit` **未被排除**，保持 viable。`B* = 180k` 仍是支持 `rOptimizationFailure` 的强证据，本干预仍是本项目迄今最干净的干预式实验之一；它唯一不能做的事，是排除一个它从未改变过的变量。逐条见
[ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md](ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md) §12.4。
