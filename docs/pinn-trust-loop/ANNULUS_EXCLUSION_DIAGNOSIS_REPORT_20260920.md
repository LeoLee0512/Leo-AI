# Annulus Exclusion Diagnosis Report（2026-09-20 / 21）

执行负责人：Claude（队长）。对象：外部评审裁决（2026-09-20）十一项的执行——代码身份补洞，以及 `sLocalizedError` 其余五个 admissible 根因的诊断专用排除实验。

预注册：[ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md](../../experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md)（含第 10 节 S1 勘误，运行前追加）。
上游：[ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md](ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md)、[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)、[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)。

本轮**没有**把「诊断用 Tier-1」当作 Tier-1 阶段、**没有**从「没观察到缺陷」发明排除、**没有**打开任何 claim set、**没有**写入任何账本事件、**没有**改 Gate 4 / geometry schema / Tier-1 语义 / Constitution、**没有**升 revision、**没有**产生 TrustVector 或 ClaimGateDecision。

---

## 1. Executive

```text
Root Cause:            UNDETERMINED
Exclusions:            2 of 5 discharged this round (3 of 6 obligations scientifically met;
                       one of those three has no exp-* identifier and cannot yet be cited)
                       EXCLUDED      rImplementationDefect, rSpecDefect
                       NOT EXCLUDED  rSamplingDeficiency, rReferenceDefect, rSingularityTreatment
DiagnosisRecord:       NOT WRITTEN
Annulus Calibration:   NOT YET PASS
Highest Claim:         BLOCKED
Recommendation:        REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

按裁决 item 5：有原因无法诚实排除，即以 `Root Cause = UNDETERMINED` 停止，**不强行命名** `rOptimizationFailure`。

**本轮最重要的实质发现不是「排除了几项」，而是采样实验的结果反过来削弱了上一轮的因果解读**：把配置点密度提高 2 倍或 2.76 倍，**都把 seed 2 的局部失败修好了**；而失败的那个单元 `2,13` 原本只分到 **5** 个配置点，全域中位数是 **16**。也就是说「多训练」与「多采点」都能压下这个局部误差，两者都不是必要解释（§5）。

---

## 2. 代码身份补洞（裁决 item 3，在任何新诊断执行之前完成）

上一轮发现：`pinn/` 下一个 run 会 import 的新模块可以对整套身份机制隐身——`code_manifest()` 枚举 `git ls-files`，`workspace_dirty_paths()` 传 `--untracked-files=no`，`assert_code_identity_complete()` 无法察觉一个从未被列入的文件。

| 机制 | 处理 |
|---|---|
| `untracked_identity_paths()` | 用 `git ls-files --others` 扫描身份边界，**刻意不加** `--exclude-standard`——一个模块不会因为被写进 `.gitignore` 就离开方法身份。字节码缓存是唯一排除项（它是输出，不是来源） |
| `assert_code_identity_complete()` | 边界内存在未跟踪文件即拒绝 |
| `codeIdentityExtraFiles` | 必须是 git 已跟踪路径；未跟踪的字节无法从仓库恢复，不能标识一个方法 |
| PRELOCK | 新增 `codeIdentityTracked` 检查，**检查数由 7 变 8** |

**对抗测试**（裁决点名要求）：先构造一棵 PRELOCK 确实接受的树作**对照**，再写入一个未跟踪 helper，断言三件事——整体 `FAIL`、`codeIdentityTracked` 是**唯一**状态发生变化的检查、`git add` 之后拒绝解除。对照与「唯一变化」这两条是关键：没有它们，测试可能因夹具本身的毛病而通过。新增 **10** 项测试。

---

## 3. 五项排除实验

每项都标明属于**干预式**还是**正控制式**。判定阈值在运行前冻结于预注册，本节只报结果。

### 3.1 `exp-annulus-dx-implementation` — rImplementationDefect → **EXCLUDED**（正控制式）

| 探针 | 测量 | 判定 |
|---|---|---|
| I1 预言注入：精确解 u\* 经**产生 ACA-9 的同一条流水线** | relL2 `6.055e-18`，ACA-9 `4.437e-17` | ≤ 1e-12 ✓ |
| I2 正控制：在已知单元 `2,5` 注入凸起 | 流水线报告 `2,5`，统计量一致 `0.000e+00` | 位置正确且 ≤ 1e-9 ✓ |
| I3 独立重写的例程重算失败 seed 的 ACA-9 | 生产值 `1.038334942e-03`，独立值 `1.038334942e-03` | 相对差 `0.000e+00` ≤ 1e-12 ✓ |
| I4 AD vs 中心差分（热点单元 16 个点） | 最差相对差 `2.225e-08` | ≤ 1e-6 ✓ |

I1 把 AD 路径、单元划分、归一化、边界与通量代码全部跑了一遍，对着一个**已知精确答案**；I2 证明这条流水线**能**定位一个人为注入的局部缺陷；I3 用一套不 import `diagnostics_annulus`、自行推导等面积分箱的独立例程复算，结果**逐位相同**。这不是「没观察到缺陷」。

### 3.2 `exp-annulus-dx-spec` — rSpecDefect → **EXCLUDED**（正控制式）

规范缺陷**能**产生本信号：网络按 f 训练，若 f 与 u\* 不一致，网络本就不会收敛到 u\*。

| 探针 | 测量 | 判定 |
|---|---|---|
| C1 `-Δu* - f`，**两条独立路径** | 闭式 Laplacian `0.000e+00`；torch 自动微分 `3.553e-15` | 均 ≤ 1e-12 ✓ |
| C2 两条边界组件上的 `max|u*|` | outer `2.115e-16`，inner `2.952e-17` | ≤ 1e-14 ✓ |
| C3 正控制：源项 ×1.000001 | 残差升至 `1.752e-05` | ≥ 1e-6 ✓ |

### 3.3 `exp-annulus-dx-reference` — rReferenceDefect → **NOT EXCLUDED**（路径审计 + 正控制式）

| 探针 | 测量 | 判定 |
|---|---|---|
| R1 路径审计：ACA-9 的调用图能否读到 FDM | `ast` 静态遍历 14 个模块，到达 `scientific_reference` 的模块数 **0** | ✓ |
| R2 独立极坐标 FDM 的收敛阶 | `2.0016 / 2.0004` | 落在 [1.8, 2.2] ✓ |
| **R3** 最细网格（64×256）下 FDM 在热点单元 `2,13` 的自身误差 | 参考 `5.500e-05`，模型 `1.490e-04` | **只低 2.7 倍，预注册要求 10 倍 ✗** |
| **R4** 正控制：去掉极坐标 `1/r` 项的算子 | 观测阶 `[nan]`——迭代**发散**，不是「收敛但掉阶」 | **控制未执行 ✗** |

R1 是一条很强的论证：ACA-9 是对着**解析解**算的，数值参考根本进不了这个统计量，因此它不可能制造该信号。但预注册要求的四条里有两条不成立，按自己定下的规则，**不能**记为已排除。

**R4 的处理（本轮自查出的一个缺陷，见 §6.1）**：最初的实现把 `nan` 读成了「通过」。已改为对非有限证据 fail closed，工件现在如实记录「控制未执行，未证明任何分辨力」。该修正**不可能**改变本项判定——R3 独立地已经不成立。

### 3.4 `exp-annulus-dx-singularity` — rSingularityTreatment → **NOT EXCLUDED**（正控制式）

| 探针 | 测量 | 判定 |
|---|---|---|
| G1 逐单元 `max|Δu*|` 的 max/median | `2.668` | ≤ 10 ✓ |
| **G2** 30 个最差单元中贴边界（bin 0 或 bin 3）的个数 | **1**（seed 1 @240k，单元 `0,15`） | **预注册要求 == 0 ✗** |
| G3 正控制：`r^(-1/3)` 奇异场锚在内圆上 | 机制把热点定位到 `0,1`，即紧贴内孔 | ✓ |

G3 证明这套机制**看得见**贴边界的集中，因此 G2 的观测是有信息量的——而它给出的是 1，不是 0。

这条判定之所以不成立，直接源于我在 Phase II 报告里的一处**事实错误**：原写「30 个最差单元全部在中间两环」，实为 29 / 1 / 0（§6.3）。

### 3.5 `exp-annulus-dx-sampling` — rSamplingDeficiency → **NOT EXCLUDED，且证据反向**（干预式）

全部在 r1 预算 120000 步下，其余一切冻结，只读 D_dev。

| 探针 | 干预 | ACA-9 | 判定 |
|---|---|---|---|
| **S1a** | 已登记池**全部 2048** 点（**2×** 密度，完全配对） | **6.620666e-04** | **PASS —— 修好了** |
| **S1b** | 新池 2823 点（**2.76×** 面积匹配密度，不配对） | **5.766093e-04** | **PASS —— 修好了** |
| S2 | 采样 seed +901 | `2.670052e-04` | PASS |
| S3 | 采样 seed +902 | `6.505030e-04` | PASS |
| S4 | 采样 seed +903 | `3.061673e-04` | PASS |
| **S5** | 热点单元 `2,13` 的配置点计数 | **5**，全域中位数 **16** | **被采稀** |

对照运行前冻结的三条：

```text
(a) 两种加密都救不回来   -> 不成立：两种加密都把 ACA-9 压到阈值以下
(b) 热点单元未被饿着     -> 不成立：5 个点，中位数 16
(c) 失败不随抽样设计重现 -> 成立：3 个替代抽样 0 个失败
```

(a) 与 (b) 都不成立，因此 `rSamplingDeficiency` **未被排除**。按预注册第 3 节写明的那条：若加密确实修好了，采样就是一个**有效杠杆**，该原因与 `rOptimizationFailure` 竞争。

---

## 4. DiagnosisRecord

### 4.1 义务与实际

`discriminating_experiment_errors` 要求：为该 signature 下**其余每一个** admissible 根因指名一个排除实验，`excludes.<cause>.experiment` 必须匹配 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`。`sLocalizedError` 的 admissible 集合共 7 个。

| 候选 | 实验 | 科学状态 | 可被 `excludes` 引用？ |
|---|---|---|---|
| `rImplementationDefect` | `exp-annulus-dx-implementation` | **已排除** | 是 |
| `rSpecDefect` | `exp-annulus-dx-spec` | **已排除** | 是 |
| `rCapacityLimit` | Phase II 嵌套预算干预 | **已排除**（干预式，上一轮） | **否 —— 无 `exp-*` 标识** |
| `rSamplingDeficiency` | `exp-annulus-dx-sampling` | **未排除**（证据反向） | — |
| `rReferenceDefect` | `exp-annulus-dx-reference` | **未排除**（R3、R4 不成立） | — |
| `rSingularityTreatment` | `exp-annulus-dx-singularity` | **未排除**（G2 不成立） | — |
| `rOptimizationFailure` | — | 待命名的根因 | — |

**6 项义务中，2 项已备妥可引用的证据，1 项科学上已排除但缺标识，3 项未排除。**

关于 `rCapacityLimit` 的记账细节，必须写清楚而不是含糊带过：上一轮的嵌套预算干预**确实是**一次干预式判别实验，并且**确实**排除了容量限制——同一 4×64 网络在 180k 处 10/10 达到判据。但它的产物没有记录 `experimentId`，其目录名 `nested-budget-r1-paired` **不匹配** `excludes` 要求的 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`。这是**记账缺口**，不是科学缺口；补法是给它指定一个 `exp-*` 标识并登记，而这是一个应当被记录的命名决定，**不应**在写记录时凭空发明。本轮不自行补，登记待裁决。

### 4.2 判定

```text
RootCauseClass:  （未写入）
Formal verdict:  UNDETERMINED
State:           FAILURE_RECORDED（未进入 DIAGNOSED）
```

没有生成 DiagnosisRecord。即便只看形式要求，三项未排除也使记录无法通过 `validate_diagnosis_record`；而更实质的是 §3.5——`rSamplingDeficiency` 不只是「没排除」，它有**支持自己的正面证据**。

---

## 5. 对 Phase II 因果解读的影响

上一轮报告的 `B* = 180k` 是**真实测量**，本轮不回改它的任何机器证据。但它对 `rOptimizationFailure` 的支持强度必须下调：

```text
Phase II 的观察   同一容量、同一采样、同一前 120k 轨迹，继续优化到 180k -> 10/10 通过
本轮的观察        同一容量、同一优化预算 120k，把配置点密度提高 2x 或 2.76x -> 失败 seed 通过
                  且失败单元 2,13 原本只有 5 个配置点，中位数 16
```

两者都能把这个局部误差压下去，因此**两者都不是必要解释**。一个自洽的替代叙事是：seed 2 的配置点抽样在该单元偏稀，PDE 在那里约束不足，于是局部误差偏大；继续优化只是让网络在别处的约束把该区域「带」得更好一些，而加密则直接补上了约束。本轮的证据无法在这两者之间做出判别。

这正是裁决要求做真排除实验、而不是接受「没观察到缺陷」的理由。若上一轮就据 `B*` 命名根因，这条竞争解释会被整个错过。

---

## 6. 本轮自查出的三个自身缺陷

### 6.1 R4 正控制把 `nan` 读成通过（已修，已加回归测试）

判据写成「观测阶落在 [1.8, 2.2] 之外即算检出」，而 `1.8 <= nan` 为 False，于是**发散**被当成了成功的正控制。这与 2026-09-16 那轮硬化定下的规则（非有限证据必须 fail closed）是同一类缺陷，只不过这次出现在我自己本轮写的代码里。

`control_verdict()` 现在返回 `(executed, detected)`，对非有限或空证据一律 fail closed；工件记录 `controlExecuted` 并写明「控制未执行，未证明任何分辨力」。4 项回归测试钉死。

**该修正是在看到结果之后做的，必须说明为什么这不是钓结果**：`rReferenceDefect` 因 R3 独立不成立而本就未被排除，修 R4 不可能改变判定；而把一个已知的「非有限证据当通过」留在代码里，下一次就会悄悄放行。

### 6.2 driver 的探针标签 off-by-one（已修，五次训练白跑）

`f"S{offset - 899 + 1}"` 把三个替代抽样标成 S3/S4/S5，与计数探针 S5 撞名，判定查表抛 `KeyError`，工件没写成——**五次 120k 训练白跑了约 1.8 小时**。测量本身无误，错的只是标签。

**没有**把日志里的数字誊进工件（那不算证据）。已修为 S2/S3/S4，重跑得到完全相同的数（训练是确定性的）。

### 6.3 Phase II 报告的一处事实错误（已就地更正 + 追加勘误）

原写「30 个最差单元**全部**在中间两环、**没有一个**贴边界」，逐条核对 `DIAGNOSIS.json` 后实为 **29 / 1 / 0**（seed 1 @240k 的 `0,15` 贴内孔）。来源：我在一次进度汇报里打印过那份清单，写报告时**按印象概括**而未逐条复核。

机器证据一直是对的，错的只是散文。**这条更正直接决定了 §3.4 的 G2 判定**——按真实数据 G2 不成立，`rSingularityTreatment` 未被排除。

r1 标定报告与预算诊断报告中关于「**十个** seed 的最差单元全部在中间两环」的说法**是正确的**，未改。

---

## 7. Blind Validation Firewall

每次调用前后各记录账本 sha256 与事件序列并比对，全部 `unchanged = True`：

```text
DAC-M0   SEALED -> OPENED -> BURNT      （历史，永久保留，不得重开）
DAC-M1 / M2 / M3   NEVER_SEALED          一次未触碰
账本事件  ['SEALED', 'OPENED']            本轮无新增
```

所有实验只读 D_dev、合成夹具与独立参考。局部判据合同自身拒绝 `evaluationSet != "dev"`；测试另钉死 driver 源码中不得出现 `claim_grids` / `claim_quadrature` / `claim_pointwise` / `make_event` / `write_ledger` / `claim_evaluation`。

**本轮不具 Tier-1 状态**：Tier-1 含义不变（Gate 5 PASS 之后对已接受结果的压力测试）；这些是 `exp-*` 身份下的 diagnosis-only discriminating experiments，不产生 claim、不推进 Trust、不产生任何 claim-set 生命周期事件。

## 8. Trust Vector / Claim

本轮**未产生**新的 TrustVector 或 ClaimGateDecision。r1 的实际值不变：

```text
math PASS   impl PASS   train PASS   physics PASS   external FAIL   repro BLOCKED
Highest Claim: BLOCKED
```

## 9. Tests / PRELOCK / Portability

| 项目 | 治理虚拟环境 `.venv` | 训练解释器（mamba） |
|---|---|---|
| 全套 pytest | **1426 passed / 0 failed / 26 skipped** | — |
| annulus 补跑 | — | **24 passed / 0 failed** |
| poisson2d 补跑 | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，8/8**（新增 `codeIdentityTracked`，检查数由 7 变 8） | — |
| portability | **0 hard binding / 1 configurable / 8 historical** | — |

上轮基线 1414 / 26 与 PRELOCK 7/7；本轮净增 **12** 项（10 项身份对抗测试 + 2 项正控制 fail-closed 测试）。

## 10. Newly Discovered

### BLOCKING

**无。** 三项未排除是**预注册判定规则如实执行的结果**，不是新缺陷。

### NON-BLOCKING

1. **采样是一个有效杠杆**：2× 与 2.76× 密度都修好了失败 seed（§3.5）。
2. **失败单元被采稀**：`2,13` 只有 5 个配置点，中位数 16。
3. **`B* = 180k` 的因果解读被削弱**：多训练与多采点都能压下该误差，两者都不是必要解释（§5）。
4. **数值参考在热点单元并不「远低于」模型**：64×256 网格下只低 2.7 倍。若将来要用 R3 这类判据，需要更细的网格或换一条论证路线。
5. **R1 是一条强论证且已机器化**：ACA-9 的调用图（14 个模块）中无一能到达 `scientific_reference`。

### AMENDMENT CANDIDATE

1. **（承前，本轮已部分回应）失败 run 的诊断与 Tier-1 的时序闭环**——裁决 item 2 以「`exp-*` 身份下的 diagnosis-only discriminating experiments」解决了通路问题；是否把这条通路写进协议正文，待审。
2. **（承前，本轮已修）未跟踪文件静默落在代码身份之外** —— 已补洞并加对抗测试；是否把 `codeIdentityTracked` 写进协议正文，待审。
3. **（承前）Gate 4 不筛查局部判据**，尽管 D_dev 有能力测量它。
4. **（承前）`ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`**。
5. **（承前）训练记录应保存 optimizer / scheduler / batch RNG 状态**——诊断路径已实现，尚未成为正式 attempt 的要求。
6. **（承前）LR 调度与总预算耦合**——已提供 `lrPrefixSteps` 解耦，缺省行为仍耦合（为不改变历史含义而刻意保留）。
7. **（新）正控制的执行有效性应当是一等判据**。R4 的教训是：一个「控制」必须先证明自己**跑起来了**，才谈得上它有没有检出。建议把 `controlExecuted` 作为所有正控制式排除的必填字段。

### NONE

其余未发现新问题。

## 11. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

按裁决 item 5，本轮以 `Root Cause = UNDETERMINED` 停止，**不写** `rOptimizationFailure`，**不进** revision 2，**不碰** DAC-M1。

需要用户与外部评审裁决的是：

1. **`rSamplingDeficiency` 现在是一个有正面证据的竞争假设**。下一步若要判别它与 `rOptimizationFailure`，需要一个能同时固定两者的设计——例如在**相同**的配置点集合下比较预算，以及在**相同**预算下比较密度，构成 2×2；本轮没有这样的设计，也不自行开始。
2. **`rReferenceDefect` 的 R3 判据**：是在更细网格上重做，还是改用 R1 那条「参考进不了统计量」的论证路线并相应修订判据？两者都需要事前裁决，不能在看到结果后选。
3. **`rSingularityTreatment` 的 G2 判据**：1/30 贴边界是否构成实质的奇异性证据？G2 的 `== 0` 是本轮冻结的严格形式；若要改，必须是**事前**修订，并说明理由。
4. **`rCapacityLimit` 的 `exp-*` 标识**：上一轮的嵌套预算干预在科学上已排除容量限制，但其产物没有 `experimentId`，目录名不匹配 `excludes` 所要求的模式。是否给它指定并登记一个 `exp-*` 标识（例如 `exp-annulus-nested-budget-r1`），需要裁决——这是一个命名决定，不应在写 DiagnosisRecord 时凭空发明（§4.1）。
5. 六条既有 + 一条新增的 AMENDMENT CANDIDATE 的统一审议。

在裁决之前，本轮**停止**：不做 capacity sweep、不做架构搜索、不做优化器搜索、不做更高预算 sweep、不开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热。

---

## 12. 四项裁决与随之查出的四个自身缺陷（2026-09-21，追加不改写）

本节是**追加**。第 1–11 节、全部 `exp-*` 工件、`EXCLUSIONS.json`、2026-09-20 预注册、r1 与 Phase II 的一切机器证据，一字未改。用户把四项悬而未决的问题委托给执行者裁决（2026-09-21），以下是裁决、理由，以及裁决过程中查出的、**属于我自己**的四个缺陷。

**裁决后的总账（比裁决前更差）：**

```text
rImplementationDefect   EXCLUDED
rSpecDefect             EXCLUDED
rSamplingDeficiency     NOT EXCLUDED   （证据反向）
rReferenceDefect        NOT EXCLUDED   （R1 与 R3 均不成立；R4 修好后通过）
rSingularityTreatment   NOT EXCLUDED   （G2 不成立；且 G3 未按冻结规格执行）
rCapacityLimit          NOT EXCLUDED   ← 由「已排除」改记，见 §12.4
                        未排除由 3 项改为 4 项
Root Cause              UNDETERMINED   （不变）
```

### 12.1 裁决一：rSamplingDeficiency 与 rOptimizationFailure 本轮**不可分离**，不跑新实验（0 GPU）

**路由在看到数据之前就已冻结。** 2026-09-20 预注册 §3 结尾写着：「若 (a) 不成立（即加密确实修好了），则采样是一个**有效杠杆**，不得排除；该原因与 `rOptimizationFailure` 竞争，按 item 5 报 `UNDETERMINED`。」§10 勘误（**在任何排除实验执行之前**追加）写得更严：「只要**任意一个**把 ACA-9 压到阈值以下，(a) 即不成立。」工件记 `a_densityDoesNotRescue.satisfied = false`。路由已经触发；现在再委托一个新判别器去分开这两个**事前已被判定为「竞争即 UNDETERMINED」**的原因，结构上就是在判据判否之后重开一个事前已裁决的归宿。

**定义层重叠，不是功效不足。** `state_machine.py` 把 `rOptimizationFailure` 定义为「not converged, gradient pathology, **loss weighting**」，把 `rSamplingDeficiency` 定义为「collocation density or **distribution**」。本实验是等权单损失（`lossWeights.pde = 1.0`，硬边界参数化），于是「`2,13` 只有 5 点」与「`2,13` 只拿到 0.49% 而非 1.6% 的梯度权重」是**同一句话**，落在两个类定义的交集里。一切**增加资源**的设计（2×2 析因、密度阶梯）两个假设都预测 PASS，天然分不开。

**§3.5 与 §5 的机理叙事必须收窄（重要）。** 我原写「失败单元被采稀……把密度提上去就修好了」，把观测读成了「饥饿 → 补点 → 痊愈」。逐条复核工件后，这个读法**不成立**：

| 探针 | 干预 | ACA-9 | 热点单元 |
|---|---|---|---|
| r1 seed 2 | 基线 1024 点 | 1.038335e-03 | `2,13` |
| **S1a** | **2× 密度**（整池 2048 点） | **6.620666e-04** | **仍是 `2,13`** |
| S1b | 2.76× 密度（新池 2823 点） | 5.766093e-04 | `2,8` |
| S2 | 只换抽样 seed | 2.670052e-04 | `1,12` |
| S3 | 只换抽样 seed | 6.505030e-04 | `1,1` |
| S4 | 只换抽样 seed | 3.061673e-04 | `1,4` |

实测复核：S1a 把 `2,13` 的配置点数从 5 提到 18，相对中位数由 **0.31× 升到 0.58×**（饥饿被**部分缓解**），而热点**纹丝不动**，且其 ACA-9（6.6207e-04）比只换抽签的 S3（6.5050e-04）**还差**。反之，只换抽签的三次**每一次**都把热点挪走了，散布 2.44×（2.670e-04 – 6.505e-04），量级盖过任何密度效应。

**可如实记录的结论**：在这批探针下，可靠改变局部误差位置的操作变量是**抽签**，不是**密度**；「该单元被饿瘦、补点即愈」这一机理**未获支持**。判据 (a)/(b) 的 `satisfied = false` 是已记录的机器事实、不可改写，但它们支撑的机理读法降一档。

**前瞻性设计（写入下一份预注册，本轮不跑）**：`S6-R 等总量重分配`——总配置点数固定 1024、预算固定 120000、init/batch/sample 沿用 r1 配对，只把点从计数最高的格迁到最低的格直至全部 ≥ 中位数；目标格必须写成**机械规则**（「该 seed 配置点数最少的格」），**绝不写死 `2,13`**。这是唯一在固定资源总量下只改**分布**的设计，因而是唯一可能有识别力的那个。

### 12.2 裁决二：R3 整族前瞻性退役；R4 只修我自己的仪器 bug，判据一字不改

**R4 的失败是我的 bug，不是控制太狠。** `exclusion_annulus.py` 原写 `u = u + residual / diagonal`，而 `residual = -(urr + utt) - rhs` 即 `A·u − b`；Jacobi 应为**减**。按原写法**无论是否腐蚀算子都会发散**，控制从未真正测试过腐蚀。另一缺陷：固定 4000 扫本身不够——实测真算子在 4000 扫后 `max|residual|` 仍约 `1.3e-01`，迭代误差会混进离散误差。

修复后（符号改正 + 改为按残差容差迭代到 `1e-10`）实测：

```text
16x64    relL2 1.161905e-01   iterations 1587   finalMaxResidual 1.579e-09
32x128   relL2 1.153873e-01   iterations 6342   finalMaxResidual 1.700e-09
观测阶   0.0100
```

**预注册的 R4 原判据（观测阶落在 [1.8, 2.2] 之外）现在直接通过**，判据一个字没改。丢掉 `1/r` 项使格式**不相容**而非掉阶，误差停滞在 0.115，refinement study 照样看得见。在一个字符的仪器 bug 足以完全解释失败时去替换设计，才是「看到失败才改设计」。

**R1 的根集合是手挑的——这是更重的一条。** 原实现的根集合只含「计算」统计量的模块，**恰好不含 `gates_annulus`**；而 `gates_annulus.py:31` 在模块层 `from scientific_reference.annulus_polar_fdm import min_eigenvalue, refinement_diagnostic`，且 `gates_annulus.py:439` 的 `external_checks` 正是**裁决 ACA-9 MUST 判定**的地方。所以原工件的 `modulesReachingTheNumericalReference: []` 不是「查出来没有」，是「根集合选得没有」。另两处缺陷：包节点（如 `pinn.governance`）被当叶子静默截断；相对导入 `from .x import Y` 把 `Y` 当成了模块。

修复后（根集合补入裁决模块、包节点回落到 `__init__.py`、相对导入取 `node.module`），审计图由 14 个模块扩到 **43** 个，结果是：

```text
modulesReachingTheNumericalReference: ['pinn.experiments.gates', 'pinn.experiments_annulus.gates_annulus']
statisticCanReadTheNumericalReference: True        ->  R1 现在 FAIL
```

**两句话都要说**：FDM 实际只用在 Gate 2（`gates_annulus.py:143`）与 PH7（`:353`），**不**参与 ACA-9 的计算，所以「ACA-9 的数值读不到 FDM」这一**实质结论很可能仍然成立**；但**我原来的审计没有立住它**，而按 R1 写下的判据，修复后的审计给出的是 FAIL。原工件保留于 `superseded/exp-annulus-dx-reference.as-first-run.json`，修正后的工件覆盖同名文件。

修正后四条：**R1 FAIL、R2 PASS、R3 FAIL、R4 PASS**。判定不变：`rReferenceDefect` **NOT EXCLUDED**，且理由比原先更扎实。

**R3 退役的理由是规范缺陷，不是阈值松紧**：R3 的阈值是**被诊断对象自身**（模型在该单元的误差）的函数，因此没有固定分辨力——被诊断对象越差，判据越容易通过。这条陈述不依赖任何已看到的结果，可以事前写进下一份预注册；替代仪器必须是一台**能失败**的。

### 12.3 裁决三：G2 维持，`rSingularityTreatment` 保持 NOT EXCLUDED——而且成立两次

**其一，G2 是我写错的。** 等面积划分下贴边界的单元（bin 0 与 bin 3）恰好是 **32/64，整整一半**。于是在面积均匀零假设下

```text
P(G2 通过) = 0.5^30 = 9.3132e-10        期望的贴边界个数 = 15
```

它要求的不是「没有奇异性集中」，而是一种任何随机过程都几乎不可能满足的近乎确定性；更糟的是 `P(通过) = (1−π)^n` 对 n 严格递减——**证据收得越多越难通过**，这是构造性错误。

**可入档的只有上面这一类「运行前即可算出」的规格性质。** 我另算过的 `P(X≤1)=2.887e-08`（n=30）与 `1.074e-02`（按 seed 计 n=10）是**事后统计量**——它们是在一个已被判过的冻结样本上算出的新统计量，一旦写进工件就会变成影子判定。它们只能出现在本节这样的动机叙述与将来某份预注册里，**不得作为证据被引用**。

**其二，也是更重的一条：G3 没有按冻结规格执行。** 预注册 §7 冻结的是「具有真实 **r^(2/3)** 角点型奇异的误差场」，而 `exclusion_annulus.py` 实际用的是 `exponent = -1/3`。这不是参数差异。实测（同一 D_dev、同一独立统计量）：

```text
d^(-1/3)   实际运行的        热点 0,1    在 bin 0 ✓
d^(+2/3)   预注册冻结的文本  热点 3,8    在 bin 0 ✗（落在贴外圆的 bin 3）
```

字面的 `r^(2/3)` 场在锚点处趋零、最大值在离锚点最远处，**根本通不过预注册自己写的「热点落在 bin 0」条件**。也就是说冻结文本的「场」与「通过条件」**自相矛盾**，而实现静默地选了能通过的那一侧。

据此记入一条机器事实：该实验标称的 `kind: "positive-controlled"` 在执行层面**不成立**，它实为**观察式**。按预注册 §2，观察式在**任一方向**都不构成排除。因此 `rSingularityTreatment` 的 NOT EXCLUDED 成立两次：一次因 G2 不成立，一次因该实验本就没有排除的资格。

报告第 93 行原写「G3 证明机制看得见贴边界集中，因此 G2 的观测是有信息量的」——这句话现在两头都站不住：G3 未按规格执行，而「==0」是否有信息量取决于零假设发生率（=1/2，本轮从未计算）。记为本轮第四条散文缺陷。

**「最差单元位置」这一族判据整体退役。** 理由是设计事实：α=0.01 单侧精确二项检验对 H0: p ≥ 0.5 的拒绝域，n≤6 为**空集**、n=10 恰为 `{0}`、n=20 为 k≤4、n=30 为 k≤8。也就是说「前瞻性写一个 G2′ 二项检验」在数学上**就是 G2**，只是换了个 n。将来真要排除奇异性，必须走**干预式**设计（同域、同流水线、同预算、**同配置点集**，A 臂现解析 u\*，B 臂 u\* 加事前冻结幅度阶梯的真 `r^(2/3)` 内圆奇异项、f 重算并过 C1），产出检出下限并给出有界结论。**该设计本轮不冻结、不预注册**——在不知道哪个命名动作需要它之前就冻结，又是一次在压力下造判据。

### 12.4 裁决四：`rCapacityLimit` 从未被排除——问题不成立，且总账变差

这是四项里最重的一条，因为它**让情况变坏**。

`state_machine.py` 的 `FACTOR_CONTROL = {"capacity": "architecture", "sampling": "sampling"}`，且 `MIN_INTERVENTION_LEVELS = 3`、`MIN_INTERVENTION_SEEDS = 3`：一次**容量**干预必须改变**架构**，至少三档、每档至少三个 seed。而嵌套预算干预全程把架构钉死在 `4×64 tanh`（诊断配置的 `network` 块与 r1 逐字相同），改变的是 `optimizer.steps`——**容量档位数 = 0**。

我自己在 2026-09-19 预注册 §13 CASE A 里写的原文是：

> 构成支持 `rOptimizationFailure` 的**强判别性**证据，因为同一 representational capacity 已实证达到判据，`rCapacityLimit` **不再是必要解释**。但**不得**因为 B\* 存在就跳过其余六个 admissible candidate 的记录义务——……`rCapacityLimit`……

它把 `rCapacityLimit` **逐字列进**那六项不得跳过的义务里。**「不再是必要解释」≠「已排除」。** 我在 Phase II 报告与本报告 §4.1 里把它写成了后者，这是越权。

**裁决**：不发任何用于 `excludes.rCapacityLimit` 的 `exp-*` 标识，不建注册表，不重跑。改记 `rCapacityLimit` 为**未排除**，未排除原因由 3 项改为 **4 项**。§4.1 的表格与「6 项义务中 2 项备妥、1 项缺标识、3 项未排除」这一行据此更正为：**6 项义务中 2 项备妥可引用证据，4 项未排除**。

嵌套预算干预并未白跑：那 9.15 小时买到了 `B* = 180k`、三档预算的配对结构、以及 120k 前缀在十个 seed 上逐位复现 r1，它仍是本项目迄今最干净的干预式实验之一，将来作为 **B\* 证据**经 `evidencePointers`（`artifactRef` 本就强制 `artifactId + sha256`）进入记录。它唯一不能做的事，是排除一个**它从未改变过的变量**。

### 12.5 一个本节新发现的可执行事实：`rUndetermined` 的 DiagnosisRecord 是写得出来的

本报告 §4.2 原写「三项未排除也使记录无法通过 `validate_diagnosis_record`」。这句话只对**命名 `rOptimizationFailure`** 成立。实测：`state_machine.discriminating_experiment_errors` 在 `root_cause is RootCauseClass.UNDETERMINED` 时校验完 `experimentId` 即 `return errors`，`excludes` 可为空；`SIGNATURE_EVIDENCE[sLocalizedError]` 只要 `errorSpatialDistribution` 与 `samplingConfigDiff`，两项本轮均已产出；唯一额外要求是不得带 `gate` 字段。构造的候选记录经 `validate_diagnosis_record` 返回**零错误**。

但它的后果不轻：`triage` 在 `rUndetermined` 下返回的不是 `DIAGNOSED` 而是 **`STOPPED_THE_LINE`**——「the line stops for a human」。这是一次真实的状态迁移，且 `MAX_DIAGNOSIS_ROUNDS = 3`。**本轮不写、不迁移**：它超出用户委托的四项，留给用户与外部评审裁决（见本报告新的 §13 建议）。
