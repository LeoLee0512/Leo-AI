# PINN 闭环科研 MVP 计划

**PINN Closed-Loop Scientific MVP Plan**

| 字段 | 值 |
| --- | --- |
| Plan ID | `MVP-PINN-001` |
| Plan Version | **1.3 DRAFT** |
| Status | **DRAFT — P1 治理内核已实现；仅允许 PRELOCK dry run；未 HASH LOCK、未训练、未进入正式 P2** |
| Supersedes | v1.2 draft（未锁定）· v1.1（未提交）· v1.0（PROPOSED，commit `b0151bb`） |
| Constitution Version | 1.0（一字未改） |
| 依据审计 | `AUDIT-2026-09-04-001` |
| Date | 2026-09-05 |

---

## 0. v1.2 → v1.3 锁前修订摘要

| # | lock-blocking 问题 | v1.3 处置 | 机器落点 |
| --- | --- | --- | --- |
| P0-1 | L1 把训练 BC `{0,1}` 与 boundary validation 的合法复用误判为泄漏 | L1 只禁止非边界 holdout（GL512/CGL2000）回流；spec-known boundary 坐标从 identity 比较中豁免，boundary metric 的 L4 反馈仍禁止 | `pinn.governance.leakage` + protocol schema/tests |
| P0-2 | Gate 1 要求 lock、而 lock 又先要求 Gate 1 | 拆为非 Gate 的 `PRELOCK_VALIDATION` 与未来 `POSTLOCK_GATE1`；无 final lock 时 prelock 可 PASS，Gate 1 保持 BLOCKED | `pinn.governance.prelock/state_machine/locking` |
| P0-3 | acceptance criterion 缺失 metric 引用 | 每项强制 `metricRef`，唯一引用 `validationMetrics[].id`；重复、悬空、缺失、类型错误均 FAIL | spec schema + semantic validator |
| P0-4 | “verbatim”与 serializer 规则冲突 | 唯一 canonical bytes 为 `json.dumps(..., ensure_ascii=False, indent=2) + "\n"`；spec/protocol 改用中性的 `lockStatusAuthority` | canonical validator/tests |
| P0-5 | CGL 公式不能唯一确定跨环境字节 | 冻结 `CGL2000.npy`（并一并冻结 GL512 节点/权重）；记录 artifact/data SHA、dtype、shape、endianness、生成器和环境；validation 读取 artifact | `specs/.../assets/` + `pinn.governance.nodes` |
| P0-6 | expected verdict 未被 lock payload 绑定 | 新增纯数据 `adversarial/core_manifest.draft.json`；未来 lock 增加 `adversarialManifestSha256` | manifest/lock schemas + verifier |
| 结构 | calibration component 与正式 workflow 状态混淆 | 增加 `WORKFLOW_E2E / VALIDATOR_COMPONENT / TRAINING_E2E`；component 使用 `NOT_APPLICABLE`，不伪造不可达 workflow/claim | manifest schema + semantic validator |
| 结构 | B1/B9 机器执行计数含糊 | 15 个 conceptual case、18 个 atomic executable scenario；B1a/B1b、B9a/B9b/B9c 各自完整预注册 | adversarial manifest |
| 结构 | 解析 reference 只有自然语言旁路 | 新增 `TRUSTED_ANALYTIC_REFERENCE / ANALYTIC_EVALUATION`，强制 evaluator hash 与 equation/spec binding | provenance policy + validator/tests |

本轮终态固定为：`v1.3 = DRAFT`；`HASH LOCK = NOT EXECUTED`；`TRAINING = NOT EXECUTED`；`P2 = NOT ENTERED`。

### 0.1 v1.1 → v1.2 已原则批准并保留的设计

| # | 审阅意见 | 处置 | 落点 |
| --- | --- | --- | --- |
| 1 | 修复自引用 hash | **已采纳**。`spec.json` / `protocol.json` 不再保存自身 SHA；digest 移入第三份 `lock.json`；冻结 canonicalisation 为 **exact bytes + UTF-8 无 BOM + LF + 单尾换行**（已实测工作区满足） | §14 |
| 2 | Claim-Level Prerequisite Matrix | **已采纳**。并发现第五十五章原文是"只有在**必要的**上游 Gate 全部 PASS"——因此矩阵是对"何谓必要"的解释，**不是 bypass，不需修宪**；例外清单封闭为**恰好一条**（Level D） | §3.5 |
| 3 | 修正 validation leakage 定义 | **已采纳**。删除 $\delta_{\min}=10^{-6}$ 排除区（连续域上几何邻近≠泄漏）。改为 identity / coordinate / generation / consumer 四类 provenance 检查；坐标碰撞用 ULP 级判据。**混叠要求从泄漏中剥离**，独立成协议条款 | §9.6、§9.7 |
| 4 | 全流程统一 float64 / CPU | **已采纳**。canonical executor = CPU + float64（参数、训练、forward、autograd、baseline、validation、metrics）。`DTYPE_WIDEN` 在本 MVP 不再是必要路径 | §9.1 |
| 5 | Provenance trust boundary | **已采纳**。新增 6 个 producer 字段；手工导入默认 `UNTRUSTED_IMPORT`；**拆分 `validationInputEligible` / `claimEvidenceEligible`**，使 ValidationMetric 可作证据但不可回流为模型输入 | §7 |
| 6 | FDM protocol 完整定义 + B11 修正 | **已采纳**。$E(N)$ 改为内点离散最大误差；$p_k=\log_2(E(N_k)/E(2N_k))$；**B11 改判为"缺少 refinement sequence，收敛证据不存在"**——不再声称测到不存在的 $p$；Gate 2a 改用预注册机器容差（`sin(π_f64)=1.2246e-16`，不得要求字面 `==0`） | §10 |
| 7 | 清理 deterministic taxonomy | **已采纳**。四类分级 + 精确计数；B3b → `EMPIRICAL_CHALLENGE_B3`、真实 4 点训练 → `EMPIRICAL_CHALLENGE_B4`，二者移出 core 且**不携带 expected verdict**；**B4 重构为确定性 sparse-collocation null-space 构造**并留在 core；明令禁止"先跑后写 expected verdict" | §8 |
| — | C3 scope 限定 | **已采纳**。5/5 通过也只能声称 Poisson-1D v1.0 + 固定架构/优化器/训练协议 + 5 个预注册 seed | §11.4 |

### 0.2 v1.1 中已由 v1.2 纠正的错误

| 错误 | 纠正 |
| --- | --- |
| `spec.json` 内含 `specSha256`，而锁定流程要求 hash 后写回 → 逻辑上不可能成立 | 移入 `lock.json`，被 hash 的文件锁定后**一个字节都不再改** |
| $\delta_{\min}=10^{-6}$ 被当作 leakage 定义 | 泄漏是**信息流**问题，不是距离问题；已重写 |
| B11 期望写作"收敛阶不落在 $[1.8,2.2]$" | 单一网格根本不存在收敛阶。改判"收敛证据缺失" |
| "13 ANALYTIC + 2 BITWISE" 与表格不符；bad case 实际列了 12 行却标称 11 | 已重新分级并精确计数；`B1′` 归为 B1 的子断言，bad case 恢复为 11 个 ID |
| BITWISE case "期望值 calibration 时录入" | 这正是被禁止的"先跑后写"。已删除；core suite 内所有 expected verdict 均在首次执行前冻结 |
| **逐点网格取 $N=2001$** | 实算节点摘要时发现该网格含 $x=1/2$（偏差 1 ULP），会与 B4 配点集 $\{1/4,1/2,3/4\}$ 碰撞、令 L1 检查误触发。改为 $N=2000$，并新增 §9.3.1 机器可判的反碰撞要求 |

**未改动：** 宪法 v1.0；AC-1～AC-7 数值；core suite 规模 15（1 good / 11 bad / 3 ambiguous）。

---

## 1. MVP 的目标不是解出 Poisson

$$
\boxed{\text{证明 Leo AI 能够拒绝一个被故意做坏的 PINN}}
$$

| 附录 C 能力 | 测量位置 |
| --- | --- |
| **Accept Good** | G1 在 5 个预注册 seed 上 `ClaimStatus = SUPPORTED @ C2` |
| **Reject Bad** | B1–B11 全部按**首次执行前即冻结**的 verdict 元组被拒 |
| **Abstain When Uncertain** | U1–U3 全部 `ClaimStatus = BLOCKED`，且**不得**为 SUPPORTED / NOT_SUPPORTED / REFUTED |

---

## 2. 范围与非目标

**完整 MVP 做：** D1 domain objects · D2 Poisson spec + protocol + adversarial manifest + lock · D3 解析 primary reference + FDM 子系统验证 · D4 Gate 3 · D5 Run 记录器 · D6 Validation harness · D7 15-case core suite · D8 FailureRecord/Taxonomy/rescue budget · D9 STOP THE LINE 状态 · D10 Artifact provenance 与信任边界 · D11 Evaluation Protocol 冻结。**本轮范围严格收窄为 D1 中的锁前治理内核 + D2 pre-lock draft/dry run，不做正式 lock、baseline execution 或 training。**

**本轮不做：** Maxwell-MHD · 可视化美化 / UI 皮肤 · 第二个 PDE 问题族 · 性能优化 / GPU / 混合精度 · PINN vs FEM 比较 · 删除 `pinns/outputs_*` · 独立 artifact storage

---

## 3. 状态语义与 Claim 依赖

### 3.1 GateStatus（严格照第四条，不扩展）

| 值 | 触发条件 |
| --- | --- |
| `PASS` | 全部 MUST 满足且证据完整 |
| `FAIL` | **已执行**，≥1 MUST 未满足（含"MUST 要求的证据不存在"） |
| `BLOCKED` | 上游 prerequisite 未满足，**未执行** |
| `PARTIAL` | 仅诊断，不推进状态机 |

$$
\boxed{\text{已执行} \wedge \text{MUST 未满足} \Rightarrow \texttt{FAIL}
\qquad \text{未执行} \Rightarrow \texttt{BLOCKED}}
$$

### 3.2 WorkflowStatus

`DRAFT → SPEC_LOCKED → BASELINE_VERIFIED → IMPLEMENTATION_VERIFIED → TRAINING_COMPLETED → VALIDATION → REPRODUCIBILITY_CHECK → ACCEPTED`；支线 `FAILURE_RECORDED → DIAGNOSED → REVISED`；横切 `STOPPED_THE_LINE`。
`EXPLORATORY` 不是状态，是 `evidenceLevel == D` 的推导标记。

### 3.3 ClaimStatus

`SUPPORTED` · `NOT_SUPPORTED`（已检验，证据不足）· `REFUTED`（已检验，证据否证）· `BLOCKED`（无法评估）· `WITHDRAWN`

$$
\boxed{\texttt{BLOCKED} \neq \texttt{NOT\_SUPPORTED} \neq \texttt{REFUTED}}
$$

### 3.4 三者与附录 C 的对应

| 能力 | 测量层级 | **不在**哪一层 |
| --- | --- | --- |
| Accept Good | `ClaimStatus = SUPPORTED` | 不是"Gate 全绿"本身 |
| Reject Bad | 预注册 GateStatus 元组匹配 | — |
| Abstain When Uncertain | **`ClaimStatus = BLOCKED`** | **不是 `GateStatus = BLOCKED`** |

### 3.5 Claim-Level Prerequisite Matrix（新增）

**宪法依据：** 第五十五章原文为"只有在**必要的**上游 Gate 全部 PASS 以后，才允许形成最终 ScientificClaim"。宪法本身已把范围限定在"必要的"，因此本矩阵是对**何谓必要**的解释，**不是 bypass，不需修宪**。

| Claim | 含义 | 必要 Gate | 宪法依据 |
| --- | --- | --- | --- |
| **C0** Implementation | 代码能运行 | `G1 ∧ G3` | 三十六、五十一 |
| **C1** Optimization | 训练收敛/达到指定 loss 行为 | `G1 ∧ G3 ∧ G4`（**G2 不是前置**） | 三十六、五十二 |
| **C2** Numerical Accuracy | 与独立 reference 达到预注册误差标准 | `G1 ∧ G2 ∧ G3 ∧ G4 ∧ G5 ∧ G6` | 三十六、五十、五十三、五十四 |
| **C3** Robustness | 多 seed 稳定 | ≥5 个 `SUPPORTED @ C2` 的 Run + SR-1 协议 | 二十九、三十六 |
| **C4 / C5** | Comparative / Generalization | **out of scope for MVP** | 三十三、三十五 |

**Gate 7 按 claim 分别求值**，不是单一状态：

$$
G7[\text{claim}] =
\begin{cases}
\texttt{PASS} & \text{该 claim 的必要 Gate 全部 PASS}\\
\texttt{BLOCKED} & \text{否则}
\end{cases}
$$

### 3.6 下游操作授权规则（例外清单封闭）

| 操作 | 常规前置 | 授权例外 |
| --- | --- | --- |
| Gate 3 执行 | `G1 = PASS` | 无 |
| Gate 4 执行 | `G1 ∧ G3 = PASS` | 无 |
| Gate 5 执行 | `G1 ∧ G2 ∧ G3 ∧ G4 = PASS` | 无 —— `G2 = FAIL` 时 `G5 = BLOCKED` |
| Gate 6 执行 | `G4 = PASS` | 无 |
| `G7[claim]` 求值 | 该 claim 必要 Gate 全 PASS | 无 |
| **`G2 = FAIL` 时继续 exploratory G3 / G4** | — | **授权，当且仅当已锁定 spec 声明 `evidenceLevel = D`** |

例外的宪法依据是第二章 Level D 与第五十章原文："否则 PINN 可以做 exploratory run，但 `Accuracy Claim = BLOCKED`"。

$$
\boxed{\text{授权例外恰好一条。任何其他"带着失败 Gate 继续"一律 STOP THE LINE。}}
$$

**Gate 失败阻断的是依赖该 Gate 的 claim 与下游操作，不是机械阻断一切计算。** 但 exploratory 计算只能产出 C0/C1，且必须携带 `EXPLORATORY` 标记。

### 3.7 PRELOCK_VALIDATION 与 POSTLOCK_GATE1

`PRELOCK_VALIDATION` 是锁前一致性检查，**不是 GateStatus**，也不产生 `SPEC_LOCKED`。它检查 schema、字段适用性、交叉引用、canonical bytes、节点 artifact、antiCollision、expected-verdict manifest、Constitution binding 与 lock draft 公式；它不得要求 final `lock.json` 已存在。

未来获人工批准并完成正式 HASH LOCK 后，才允许求值：

```text
POSTLOCK_GATE1 =
    PRELOCK_VALIDATION PASS
    AND lock.json exists
    AND verify_lock() PASS
```

fresh repository 只有有效 draft 而无 final `lock.json` 时：`PRELOCK_VALIDATION = PASS`，但 `Gate 1 = BLOCKED`，不得写成 PASS。

### 3.8 Calibration testMode

| testMode | 语义 |
| --- | --- |
| `WORKFLOW_E2E` | 严格遵守正式 Gate prerequisite，断言正式 workflow 与 ClaimStatus。 |
| `VALIDATOR_COMPONENT` | 隔离测试某个 validator 能否拒绝输入；`workflowStatus` 与正式 `ClaimStatus` 必须为 `NOT_APPLICABLE`，不得伪造不可达元组。 |
| `TRAINING_E2E` | 真实 deterministic training 场景；只有 G1 使用。执行仍需未来 P2+批准，本轮不运行。 |

---

## 4. 代码与产物落位

```
LeoAIStudio-build/
├─ governance/   宪法(canonical) · AMENDMENTS/ · 审计 · 本计划 · spec/protocol/lock 三份草案
├─ pinn/         domain/ gates/ verify/ baseline/ model/ validate/ artifacts/ adversarial/
├─ specs/        poisson-1d/v1.0/{spec.json, protocol.json, lock.json}
├─ adversarial/  core_manifest.draft.json；未来批准后为被 lock 绑定的 core_manifest.json
├─ baselines/    poisson-1d/{analytic-v1, fdm-v1}/
├─ runs/         <run_id>/{config,logs,checkpoints,predictions,metrics,figures}/
├─ validation/ · failures/ · claims/ · research_logs/
```

`upstream/OpenAI4S/` 一行不改。不建独立仓库，不建独立 artifact storage。

---

## 5. 七道 Gate 的落地判据

| Gate | PASS 条件 | 失败时 |
| --- | --- | --- |
| **1 SPEC** | §6 | 全部下游 BLOCKED |
| **2 BASELINE** | 2a 解析解验证（§10.1）；2b FDM 子系统收敛检验（§10.2） | G5 BLOCKED；C2 BLOCKED；**Level D 时 G3/G4 仍授权** |
| **3 IMPLEMENTATION** | autograd $<10^{-8}$；$\lVert R[u^*]\rVert_\infty<10^{-6}$；boundary operator 精确；code/config 一致性哈希匹配 | Training BLOCKED |
| **4 TRAINING** | Run 字段全记；**NaN/Inf 立即抛出终止**（禁 `nan_to_num`）；checkpoint 可重载；`terminationReason` 已记 | G5 BLOCKED |
| **5 VALIDATION** | 前置：leakage 四检（§9.6）+ provenance 准入（§7.5）；主体：AC-1～AC-7 全 MUST 通过 | G6 BLOCKED |
| **6 REPRODUCIBILITY** | 重建 run / 重算 metrics / 重绘 figures 三者均成功；环境记录完整 | `G7[C2]` BLOCKED |
| **7 CLAIM** | 按 §3.5 逐 claim 求值 | — |

---

## 6. Gate 1 字段适用性机制

第五章列出 **27 个 key**：**23 个**内容字段携带适用性机制，另 4 个（`specId`、`version`、`createdAt`、`lockedAt`）为恒必填标识与生命周期元数据。
（`lockedAt` 在 v1.2 中移入 `lock.json`，`spec.json` 内保留该 key 但恒为 `null`——见 §14.2。）

**PASS 条件：**

1. 27 个 required key 全部存在。
2. 23 个内容字段各自声明 `applicability ∈ {APPLICABLE, NOT_APPLICABLE}`。
3. `APPLICABLE` → `value` 存在且通过类型 + 语义校验。
4. `NOT_APPLICABLE` → `reason` 存在且通过占位符校验器（拒绝 `n/a`、`none`、`-`、`TBD`、空串、仅复述字段名）。
5. **NEVER_NOT_APPLICABLE 白名单**必须 `APPLICABLE`：`scientificQuestion · equations · dependentVariables · independentVariables · domain · boundaryConditions · parameters · targetQuantities · validationMetrics · acceptanceCriteria · trainingDomain · validationDomain`
6. `referenceSolution` 必须 `APPLICABLE`，**或** spec 显式声明 `evidenceLevel = D` 并给出 reason。
7. `acceptanceCriteria` 非空，每条含 `id / metricRef / threshold / comparator / level`；`metricRef` 必须唯一引用 `validationMetrics[].id`。duplicate metric ID、duplicate acceptance ID、dangling/missing `metricRef` 与错误类型一律 FAIL。
8. 本节属于 `PRELOCK_VALIDATION` 时**不得要求 final `lock.json`**。正式 Gate 1 另按 §3.7 的 `POSTLOCK_GATE1` 求值。

> 为通过完整性检查而伪造 initial condition、dimensional form 或任何不适用字段的取值：**Gate 1 FAIL**；lock 后被发现构成第四十条伪造，立即 STOP THE LINE。

---

## 7. Artifact Provenance 与信任边界

哈希只证明"这份字节没被篡改"，不证明"这份字节是模型输出"。v1.2 补上信任边界：**role / transformation / parents 不得由 artifact 自我声明。**

### 7.1 记录字段

```
artifactId · artifactRole · producerType · producerRunId · checkpointHash
evaluatorCodeHash · captureMethod · registeredBy · parentArtifactIds[]
transformation · path · type · createdAt · hash · source
── 以下为推导值，手写一律忽略并记为篡改尝试 ──
validationInputEligible · claimEvidenceEligible
```

### 7.2 枚举

| 枚举 | 取值 |
| --- | --- |
| `artifactRole` | `RAW_MODEL_PREDICTION` · `REFERENCE` · `VALIDATION_METRIC` · `DISPLAY_ONLY` · `DERIVED_DISPLAY` · `UNTRUSTED_IMPORT` |
| `producerType` | `TRUSTED_RUNNER` · `TRUSTED_VALIDATOR` · `TRUSTED_BASELINE_SOLVER` · `TRUSTED_ANALYTIC_REFERENCE` · `MANUAL_IMPORT` · `UNKNOWN` |
| `captureMethod` | `DIRECT_FORWARD_EVAL` · `SOLVER_OUTPUT` · `ANALYTIC_EVALUATION` · `METRIC_COMPUTATION` · `PLOT_RENDER` · `FILE_IMPORT` |
| `transformation` 保留证据 | `IDENTITY` · `LOSSLESS_SERIALISE` · `DTYPE_WIDEN`（本 MVP 不使用，见 §9.1） |
| `transformation` 摧毁证据（不可逆） | `GAUSSIAN_SMOOTH` · `SAVGOL` · `PCHIP_RESAMPLE` · `ISOTONIC_PROJECTION` · `MONOTONE_CLAMP` · `BOUNDARY_OVERWRITE` · `VALUE_CLIP` · `NAN_FILL` · `MANUAL_EDIT` |

### 7.3 推导规则

$$
\texttt{trusted}(a) := \texttt{producerType}(a)\in\{\text{RUNNER},\text{VALIDATOR},\text{BASELINE\_SOLVER},\text{ANALYTIC\_REFERENCE}\}
\wedge \texttt{registeredBy}(a)\text{ 为可信组件}
\wedge \texttt{evaluatorCodeHash}(a)\text{ 匹配已提交代码对象}
$$

$$
\texttt{lineageClean}(a) := \texttt{transformation}(a)\in\text{PRESERVING}
\wedge \forall p\in\texttt{parents}(a):\ \texttt{lineageClean}(p)\wedge\texttt{trusted}(p)
$$

$$
\texttt{validationInputEligible}(a) := \texttt{trusted}(a)\wedge\texttt{lineageClean}(a)
\wedge \texttt{role}(a)\in\{\text{RAW\_MODEL\_PREDICTION},\text{REFERENCE}\}
$$

$$
\texttt{claimEvidenceEligible}(a) := \texttt{trusted}(a)\wedge\texttt{lineageClean}(a)
\wedge \texttt{role}(a)\in\{\text{RAW\_MODEL\_PREDICTION},\text{REFERENCE},\text{VALIDATION\_METRIC}\}
$$

附加约束：

- `RAW_MODEL_PREDICTION` 仅可由 `TRUSTED_RUNNER` 注册，且必须记录 `checkpointHash` 且 `captureMethod == DIRECT_FORWARD_EVAL`。
- `VALIDATION_METRIC` 仅可由 `TRUSTED_VALIDATOR` 注册，且其**全部 parent 必须 `validationInputEligible`**。
- 解析 primary reference 只能使用 `artifactRole=REFERENCE`、`producerType=TRUSTED_ANALYTIC_REFERENCE`、`captureMethod=ANALYTIC_EVALUATION`，并同时绑定 `evaluatorSourcePath + evaluatorCodeSha256 + equationBinding + specBinding`。缺一即不可信；不得再通过“或解析解”自然语言旁路进入。

### 7.4 资格矩阵

| role | 必需 producerType | `validationInputEligible` | `claimEvidenceEligible` |
| --- | --- | --- | --- |
| `RAW_MODEL_PREDICTION` | TRUSTED_RUNNER | **true** | **true** |
| `REFERENCE`（数值） | TRUSTED_BASELINE_SOLVER + SOLVER_OUTPUT | **true** | **true** |
| `REFERENCE`（解析） | TRUSTED_ANALYTIC_REFERENCE + ANALYTIC_EVALUATION + evaluator/equation/spec binding | **true** | **true** |
| `VALIDATION_METRIC` | TRUSTED_VALIDATOR | **false** | **true** |
| `DISPLAY_ONLY` | 任意 | false | false |
| `DERIVED_DISPLAY` | 任意 | false | false |
| `UNTRUSTED_IMPORT` | MANUAL_IMPORT / UNKNOWN | false | false |

> ValidationMetric 可以成为科学证据，但**不能反过来当模型原始预测输入**——这正是审计中"后处理产物回流成结论依据"那条路径的封堵点。

### 7.5 Gate 5 准入与晋升路径

Gate 5 只接受 `validationInputEligible == true` 的 artifact。

- 用户手工导入默认 `UNTRUSTED_IMPORT` / `validationInputEligible = false`，**即使文件内容完全正确**。
- **唯一晋升路径**：由 `TRUSTED_RUNNER` 从匹配 `checkpointHash` 的 checkpoint、用匹配 `evaluatorCodeHash` 的 evaluator 重新生成，且重生成字节与导入件一致。除此之外无路径。
- provenance 记录缺失 → Gate 5 前置 MUST 未满足 → **Gate 5 = FAIL**（已执行），`ClaimStatus = BLOCKED`。

污染沿 lineage 传播的原则保留：任何以 DISPLAY_ONLY / DERIVED_DISPLAY / UNTRUSTED_IMPORT 为父的 artifact 永久失去两项资格。

---

## 8. Adversarial Calibration Suite

### 8.1 确定性分级（四类，计数不含糊）

| 类别 | 定义 | 可否 gate `suite_passes` |
| --- | --- | --- |
| `ANALYTIC` | verdict 由闭式数值证明，执行前已知 | ✅ |
| `STRUCTURAL/PROVENANCE` | verdict 由结构 / provenance / hash / 集合检查决定，不含数值 | ✅ |
| `BITWISE_TRAINING` | 真实训练，device/dtype/seed/kernel 全冻结；**expected verdict 仍在首次执行前声明** | ✅ |
| `EMPIRICAL_CHALLENGE` | 真实训练，结果不可预先证明 | ❌ **不入 core suite，不携带 expected verdict** |

$$
\boxed{\text{禁止先运行真实训练看到结果、再据结果写 expected verdict}}
$$

`EMPIRICAL_CHALLENGE` 只**记录**结果，不**断言**结果，因此不存在事后写 verdict 的空间。

### 8.2 Core Constitutional Calibration Suite（15）

#### Good（1）

| ID | 构造 | 类别 | expected（执行前冻结） |
| --- | --- | --- | --- |
| **G1** | 正确实现，5 个预注册 seed 各自独立 | `BITWISE_TRAINING` | 每 seed `G1–G7 = PASS`，`SUPPORTED @ C2` |

#### Bad（11）

| ID | 故意做错 | 类别 | 闭式事实（已数值核验） | 决定性 expected |
| --- | --- | --- | --- | --- |
| **B1** | PDE 符号翻转。**B1a** 隔离测试 Gate 3；**B1b** 隔离测试 Gate 5 对翻转方程精确解 $-\sin\pi x$ 的拒绝能力 | `ANALYTIC` | B1a $\lVert R[u^*]\rVert_\infty=2\pi^2=19.739208802$；B1b $E_{L_2}=2$ | 两者均为 `VALIDATOR_COMPONENT`：B1a **G3 = FAIL**；B1b **G5 = FAIL**；workflow/ClaimStatus 均 `NOT_APPLICABLE`，不得伪装成绕过 G3 的正式 workflow |
| **B2** | BC 错误：实现 $u(1)=1$，spec 写 $u(1)=0$ | `STRUCTURAL` | 备用解析靶 $u=\sin\pi x+x$：$E_{BC}=1$，$E_{L_2}=\sqrt{2/3}=0.816496580928$ | **G3 = FAIL**（code/config 哈希不一致） |
| **B3** | 边界权重饿死，解析控制件 $u=\sin\pi x+0.3$ | `ANALYTIC` | PDE residual $\equiv0$；$E_{BC}=0.3$；$E_{L_2}=0.424264068712$ | **G5 = FAIL**（AC-3），且**未加权** $L_b$ 必须单独落盘<br><sub>不断言"$L_b$ 未下降"</sub> |
| **B4** | **Sparse-collocation null-space（重构）**：3 内点 $\{1/4,1/2,3/4\}$，模 $\sin 4\pi x$，$A_4=2\times10^{-3}$ | `ANALYTIC` | 配点 residual $=1.16\text{e-}16$；$E_{BC}=1.22\text{e-}16$；$E_{L_2}=2.0\text{e-}3$（AC-1 的 **2×**）；AC-4 $=16A_4=3.2\text{e-}2$（AC-4 的 **3.2×**） | **G5 = FAIL**（AC-1 **且** AC-4） |
| **B5** | 错误 scaling：按 $\xi=x/2$ 求二阶导，缺链式因子 4 | `ANALYTIC` | $\lVert R[u^*]\rVert_\infty=3\pi^2=29.608813203$ | **G3 = FAIL** |
| **B6** | **Collocation Aliasing Trap**：4 内点 $\{i/5\}$，模 $\sin5\pi x$，$A=0.2$ | `ANALYTIC` | 配点 residual $=2.4\text{e-}14$；$E_{L_2}=0.2$；AC-4 $=25A=5.0$ | **G5 = FAIL**（AC-1 **且** AC-4） |
| **B7** | 显式把 final validation 样本注入 training | `STRUCTURAL` | identity 检查命中 | **G5 = FAIL** + STOP THE LINE |
| **B8** | 事后改阈值：验证后把 AC-1 从 $10^{-3}$ 改成 $2\times10^{-3}$ | `STRUCTURAL` | `lock.json` 校验失败 | **STOP THE LINE**，`BLOCKED` |
| **B9** | **a** 平滑+边界改写件，hash 正确、role 手写 RAW；**b** provenance 缺失；**c** 内容**正确**但为手工导入无 producer 记录 | `PROVENANCE` | 推导得 `validationInputEligible = false` | 三者均 **G5 = FAIL**，`BLOCKED` |
| **B10** | 在已知 step 注入 NaN residual | `STRUCTURAL` | 必须抛出并终止 | **G4 = FAIL**，Taxonomy `NUMERICAL` |
| **B11** | Strawman baseline：只跑 $N=4$ 单一网格，据此声称 PINN 更准 | `STRUCTURAL` | — | **G2 = FAIL：required refinement sequence 缺失，收敛证据不存在**<br><sub>**不得**声称测得 $p$ 不在 $[1.8,2.2]$——单一网格根本没有收敛阶</sub> |

#### Ambiguous（3）—— expected `ClaimStatus = BLOCKED`

| ID | 构造 | 类别 | expected 元组 |
| --- | --- | --- | --- |
| **U1** | spec 诚实声明 `evidenceLevel = D`，无解析解亦无独立数值参考 | `STRUCTURAL` | `G1=PASS, G2=FAIL, G3=PASS, G4=PASS, G5=BLOCKED, G6=PASS`；`G7[C1]=PASS → C1 SUPPORTED`；`G7[C2]=BLOCKED → C2 BLOCKED`；`EXPLORATORY` |
| **U2** | 复刻 `outputs/run_6/model.pt` 事故：G1–G5 正常通过后删除 checkpoint，再跑 Gate 6 | `PROVENANCE` | `G1–G5=PASS, G6=FAIL, G7[C2]=BLOCKED`；`C1 SUPPORTED`、**`C2 BLOCKED`**（非 NOT_SUPPORTED，非 REFUTED）；`REPRODUCIBILITY_LIMITED`；Taxonomy `INFRASTRUCTURE` |
| **U3** | 无 commit hash、无环境记录 | `STRUCTURAL` | 同 U2 的 Gate 形态；`C1 SUPPORTED`、`C2 BLOCKED`；`REPRODUCIBILITY_LIMITED` |

### 8.3 精确计数

| 类别 | 数量 | Case |
| --- | --- | --- |
| `ANALYTIC` | **5** | B1, B3, B4, B5, B6 |
| `STRUCTURAL/PROVENANCE` | **9** | B2, B7, B8, B9, B10, B11, U1, U2, U3 |
| `BITWISE_TRAINING` | **1** | G1 |
| **Core suite 合计** | **15** | 1 good + 11 bad + 3 ambiguous |
| `EMPIRICAL_CHALLENGE`（**core 之外**） | **2** | `EMPIRICAL_CHALLENGE_B3`（$\lambda_b=10^{-8}$ 真实训练）· `EMPIRICAL_CHALLENGE_B4`（4 点真实训练） |

`B1a/B1b`、`B9a/B9b/B9c` 是各自 case ID 下的原子 subcase。概念计数仍为 **15**；按每个原子 subcase 执行断言时，`executableScenarioCount = 18`。G1 的 5 个 seed 是一个预注册 scenario 内的 5 个 Run，不把 case/scenario 计数混成 Run 计数。

### 8.3.1 Case → testMode 机器映射

| testMode | Case / subcase |
| --- | --- |
| `TRAINING_E2E` | G1（未来批准后才可执行真实训练） |
| `WORKFLOW_E2E` | B8、U1、U2、U3 |
| `VALIDATOR_COMPONENT` | B1a、B1b、B2、B3、B4、B5、B6、B7、B9a、B9b、B9c、B10、B11 |

该映射不改变科学意图，只阻止 component calibration 伪造正式 workflow：component 可断言某个 validator 的局部 Gate decision，但其 `workflowStatus` 与 `ClaimStatus` 必须为 `NOT_APPLICABLE`。

### 8.4 B4 / B6 的构造与核验

两者同属 sparse-collocation null-space 族，但考核点不同：**B6 考核毛误差能否被抓住，B4 考核阈值附近的灵敏度。**

设 $u_{\text{bad}}(x)=\sin(\pi x)+A\sin(m\pi x)$，配点取 $x_i=i/m$。则 $\sin(m\pi x_i)=0$，故

$$
R[u_{\text{bad}}](x_i)=m^2A\pi^2\sin(m\pi x_i)=0,
\qquad u_{\text{bad}}(0)=u_{\text{bad}}(1)=0
$$

$$
E_{L_2}=|A|,
\qquad
\frac{E_R}{\lVert f\rVert_{rms}}=m^2|A|
$$

| Case | $m$ | 配点 | $A$ | $E_{L_2}$ | AC-4 | 相对阈值裕度 |
| --- | --- | --- | --- | --- | --- | --- |
| **B6** | 5 | $\{1/5,2/5,3/5,4/5\}$ | $0.2$ | `0.200000000000` | `5.000000000000` | 200× / 500× |
| **B4** | 4 | $\{1/4,1/2,3/4\}$ | $2\times10^{-3}$ | `2.000000000000e-03` | `3.200000000000e-02` | **2× / 3.2×** |

$$
\boxed{\text{Low training residual} + \text{exact BC} \;\not\Rightarrow\; \text{correct solution}}
$$

**执行方式：** B1b / B2 靶 / B3 / B4 / B6 以 `VALIDATOR_COMPONENT` 的 closed-form predictor fixture 执行。fixture 的 source hash 与构造参数必须记录；`trainingApplicable=false`。它不是 `ExperimentRun`，不得伪造 `TRUSTED_RUNNER` checkpoint 或正式 workflow 状态（第三十九、四十条）。

### 8.5 Suite 判据

```
suite_passes ⟺ ∀ atomic scenario ∈ core manifest:
      actual.gates == expected.gates
    ∧ actual.workflow == expected.workflow
    ∧ actual.claims == expected.claims
```

附加 MUST：

1. PARTIAL 不得推进状态机。
2. 11 个 bad case 各生成 Taxonomy 分类正确的 FailureRecord。
3. **U1–U3 的 `claim.status` 必须为 `BLOCKED`**；出现 SUPPORTED / NOT_SUPPORTED / REFUTED 任一 → suite FAIL。
4. core suite 中 `EMPIRICAL_CHALLENGE` 数为 0。
5. 全部 expected verdict 在 suite 首次执行前写入 `adversarial/core_manifest.json`；未来 `lock.json.adversarialManifestSha256` 对其完整字节绑定。

---

## 9. Evaluation Protocol

### 9.1 Canonical Executor（统一 float64 / CPU）

| 项 | 值 |
| --- | --- |
| device | **CPU** |
| dtype | **float64 全程**：model parameters · training · forward · autograd · baseline · validation · metrics |
| 理由 | 该问题极小，无性能必要性；统一 float64 消除 `DTYPE_WIDEN` 与导数精度的语义争议 |
| 确定性 | `torch.use_deterministic_algorithms(True)`；线程数固定并记录 |
| `DTYPE_WIDEN` | **本 MVP 不使用**（枚举保留，供未来 protocol） |

未来复杂 PINN 可重新允许 float32 / 混合精度，那属于**另一个 protocol 版本**，不属于本 MVP。

### 9.2 求积（AC-1 / AC-4 / AC-5 / AC-7 / AC-8）

Gauss–Legendre，**512 节点**，映射 $[-1,1]\to[0,1]$。锁前生成器为 `numpy.polynomial.legendre.leggauss(512)`（float64）；运行时读取冻结的 `GL512_nodes.npy` / `GL512_weights.npy`，不重新调用生成器。protocol 同时记录两个 artifact SHA 与 nodes+weights 原始 `<f8` payload 的组合 SHA。

采用连续（求积）范数而非裸离散和——离散和随网格密度漂移，等于把测法留成活口。

### 9.3 逐点网格（AC-2）

Chebyshev–Gauss–Lobatto，$N_{\text{validation}}=\mathbf{2000}$，

$$
x_j=\tfrac12\!\left(1-\cos\tfrac{j\pi}{1999}\right),\qquad j=0,\dots,1999
$$

端点精确为 $0$ 与 $1$。

由于不同但数学等价的浮点求值路径可产生不同末位，本协议不把“公式 + float64”当成未来字节来源。采用的 2000 个节点冻结为 `specs/poisson-1d/v1.0/assets/CGL2000.npy`（NPY v1.0、`<f8`、shape `[2000]`、C order）。protocol 记录 artifact SHA、16000-byte data payload SHA、Python/NumPy 调查环境、生成器源码路径与 SHA。正式 validation **读取 artifact 本身**；公式仅作为可读 provenance，不作为重新生成 authority。

> **v1.1 用 $N=2001$ 是错的。** 计算节点摘要时发现：$N=2001$（2000 个区间，偶数）在 $j=1000$ 处给出 $\cos(\pi/2)$，节点落在 $x=1/2$，实测与 $1/2$ 的偏差仅 `5.551e-17`（约 1 ULP）。而 B4 的配点集为 $\{1/4,1/2,3/4\}$，于是 §9.6 的 L1 identity 检查会在 B4 上误触发，把一个混叠失败误判成 leakage，verdict 全错。$N=1999$ 同样含 $x=1/2$。
>
> 取 $N=2000$（**1999 个区间，奇数**）后不再命中任何低阶有理点。这是协议设计缺陷，不是 B4 的问题，因此**修网格、不动 case**。

### 9.3.1 节点集的反碰撞要求（机器可判）

两个验证节点集必须与所有低阶有理格不相交：

$$
\min_{v\in V}\ \min_{2\le d\le D_{\max}}\ \min_{1\le i<d}\ \left|v-\tfrac{i}{d}\right| \ >\ 10^{-12},
\qquad D_{\max}=64
$$

实测：

| 节点集 | $d\le12$ 最小距离 | $d\le64$ 最小距离 | 结论 |
| --- | --- | --- | --- |
| CGL $N=2001$（已废弃） | `5.551e-17`（$d=2$） | — | **COLLIDES** |
| CGL $N=1999$（已废弃） | `5.551e-17`（$d=2$） | — | **COLLIDES** |
| **CGL $N=2000$（采用）** | `2.471e-05`（$d=5$） | `2.269e-08`（$d=45$） | OK |
| **GL $n=512$（采用）** | `6.075e-05`（$d=11$） | `4.285e-06`（$d=19$） | OK |

该检查是 Gate 1 锁定前的 MUST：任何未来协议改网格都必须重跑它。

### 9.4 边界集（AC-3）

$\partial\Omega=\{0,1\}$，**精确取值**，不用邻近网格点代替。

### 9.5 Holdout residual 集（AC-4）

即 §9.2 的 512 个 Gauss–Legendre 节点。

### 9.6 Validation Leakage 定义（重写）

**删除 $\delta_{\min}=10^{-6}$ 排除区。** PINN 位于连续域，training point 在几何上接近 validation point **不构成** data leakage；人为的排除区既无理论依据，也会扭曲采样。

泄漏是**信息流**问题。四类 provenance 检查：

| 检查 | 内容 | 判据 |
| --- | --- | --- |
| **L1 sample identity** | 非边界 holdout（GL512、CGL2000 去除 spec-known `{0,1}`）是否出现在 training collocation / adaptivePool / diagnostic | canonical float64 位模式相等，或 `ulp_distance ≤ 8`（仅吸收良性再序列化）；training BC `{0,1}` 与 boundary validation 合法重用 |
| **L2 coordinate provenance** | validation 坐标是否来自本 protocol 的确定性生成器 | `generatorId` 必须为 protocol 声明者，不得来自任何 training 侧生成器 |
| **L3 generation provenance** | validation 集合是否由 training artifact 派生 | validation 集合的 `parentArtifactIds` 不得含任何 training 侧 artifact |
| **L4 consumer provenance** | 谁读过 validation 集合 / 指标 | 禁止读取者：optimizer · adaptive sampler · early-stopping controller · loss-weight scheduler · architecture selector · hyperparameter tuner |

泄漏成立的充分条件（任一）：

- GL512/CGL2000 的**非边界 holdout** 坐标被加入训练侧集合（L1）
- validation artifact 被 optimizer / adaptive sampler 读取（L4）
- **validation metric 影响 early stopping（L4）**
- validation 结果影响 loss weighting / architecture / hyperparameter selection（L4）

BOUNDARY `{0,1}` 是方程规格公开且训练必须使用的约束，不是 holdout secret。它可以同时用于 training BC 与 AC-3/AC-6；即使 CGL2000 本身含端点，L1 也先排除这两个 spec-known boundary 坐标。但任何由 boundary validation 得到的 metric 若回流 optimizer、adaptive sampler、early stopping、loss weighting、architecture selection 或 hyperparameter tuning，仍由 L4 判定为 leakage。

> L4 的第三条正是审计在 `pinns/main.py:1036-1040` 抓到的那条：`should_stop()` 依赖出图网格上的 `profile_ok`。新定义能抓住它，而旧的距离定义抓不住。

B7 保留：显式注入 → **Gate 5 FAIL + STOP THE LINE**。

### 9.7 混叠分辨要求（从 leakage 中剥离）

这是**协议充分性**问题，与泄漏无关：

1. validation 节点集不得与任何 training 配点格碰撞——由 §9.3.1 的反碰撞检查强制。**不能靠"GL/CGL 节点是无理数"这种直觉**：$N=2001$ 的 CGL 就恰好含 $x=1/2$。
2. 求积与逐点网格必须分辨到 `minResolvedMode = 64`。core suite 的对抗模为 $m\in\{4,5\}$，余量充分。

§9.6 与 §9.7 检查的是两件不同的事，不得混为一谈：前者问"信息有没有从验证侧流回训练侧"，后者问"验证网格看不看得见误差"。

### 9.8 导数求值

`AUTOGRAD_FIRST_ORDER`（网络精确解析导数）；`SYNTHETIC` 预测器用闭式符号导数。**禁止有限差分**——会把离散误差混进 AC-6 / AC-7 / AC-8。

### 9.9 epsilon 与端点

$\epsilon=10^{-30}$（float64），仅防除零。附断言 `denominator > 1e6·ε`。GL 为开型求积（不含端点），对积分正确；端点由 AC-3 单独精确检查。

### 9.10 随机性

`evaluationSeed = NOT_APPLICABLE`，reason："所有评估网格均为确定性求积/插值节点，评估阶段不执行任何采样。"

### 9.11 冻结的 Acceptance Criteria

| ID | 指标 | 精确参考值 | 阈值 | 级别 |
| --- | --- | --- | --- | --- |
| AC-1 | relative $L_2(u)$ | — | $<10^{-3}$ | MUST |
| AC-2 | relative $L_\infty(u)$ | $\max\lvert u^*\rvert=1$ | $<5\times10^{-3}$ | MUST |
| AC-3 | $E_{BC}$ | $g\equiv0$ | $<10^{-4}$ | MUST |
| AC-4 | $E_R/\lVert f\rVert_{rms}$ | $\lVert f\rVert_{rms}=\pi^2/\sqrt2=6.978864199639$ | $<10^{-2}$ | MUST |
| AC-5 | $\int_0^1u\,dx$ 相对误差 | $2/\pi=0.636619772367581$ | $<10^{-3}$ | MUST |
| AC-6 | $u'(0)$ 相对误差 | $\pi=3.141592653589793$ | $<5\times10^{-3}$ | MUST |
| AC-7 | 能量恒等式违反 | 两侧同为 $\pi^2/2=4.934802200545$ | $<10^{-2}$ | MUST |
| AC-8 | relative $L_2(u')$ | $u^{*\prime}=\pi\cos\pi x$ | $<5\times10^{-3}$ | SHOULD |

---

## 10. Reference 与 Baseline

| 角色 | 对象 | 作用 |
| --- | --- | --- |
| **Primary reference** | 解析解 $u^*=\sin(\pi x)$ | **AC-1～AC-8 全部对它计算** |
| **Independent numerical baseline** | 二阶 FDM | **验证 baseline 子系统本身**，不参与任何 AC |

$$
\boxed{\text{不得用带离散误差的 FDM 替代已有的解析真解}}
$$

### 10.1 Gate 2a — Primary reference 验证（预注册机器容差）

| 检查 | 容差 | 依据 |
| --- | --- | --- |
| $\lVert -u^{*\prime\prime}-f\rVert_\infty$ 在 512 GL 节点上 | $<10^{-12}$ | `tol_residual` |
| $\lvert u^*(0)\rvert,\ \lvert u^*(1)\rvert$ | $<10^{-14}$ | `tol_bc` |

**不得要求 `sin(pi_float64) == 0`。** 实测 $\sin(\pi_{\text{f64}})=1.224647\times10^{-16}$，`tol_bc = 1e-14` 留 81.7× 余量。数学上 $u^*(0)=u^*(1)=0$ 精确成立；浮点实现按预注册容差判定。

### 10.2 Gate 2b — FDM 子系统验证（完整定义，预注册）

**离散化**

$$
N := \text{均匀子区间数},\qquad h:=1/N
$$

$$
\text{内点}\quad x_i=i/N,\quad i=1,\dots,N-1
$$

$$
\frac{-u_{i-1}+2u_i-u_{i+1}}{h^2}=f(x_i),\qquad u_0=u_N=0
$$

**误差（内点离散最大误差）**

$$
E(N)=\max_{1\le i\le N-1}\bigl|u_i-u^*(x_i)\bigr|
$$

**观测收敛阶**

$$
p_k=\log_2\frac{E(N_k)}{E(2N_k)}
$$

**$N$ 序列**：$\{32,64,128,256,512,1024,2048\}$ → 6 个 refinement pair，取**最后 $K=4$ 对**：$(128,256),(256,512),(512,1024),(1024,2048)$。

**MUST**

1. 全部 $E(N)$ **严格单调下降**；
2. 最后 $K=4$ 对满足 $1.8\le p_k\le 2.2$。

$N\le2048$ 时 float64 舍入下限远未触及，$p_k$ 估计不受舍入污染。

**Independence**：baseline 模块不得 import 任何 PINN 模块，由 CI 依赖方向检查强制（第七条）。

### 10.3 B11 的正确判定（修正 v1.1）

单一网格 $N=4$ **根本不存在收敛阶**。因此：

$$
\boxed{
\text{B11 判定为 Gate 2 FAIL：required refinement sequence 缺失，convergence evidence 不存在}
}
$$

**不得**表述为"实测 $p$ 不在 $[1.8,2.2]$"——那是在报告一个从未计算过的量，违反第三十九、四十条。

区间 $[1.8,2.2]$ 与 $K=4$ 已批准；随 `lock.json` 冻结后不得调整。

---

## 11. 多 seed 与 Claim 分级

### 11.1 Run 级（Gate 5）

每个 seed **独立**执行 Gate 5，判据仅为 AC-1～AC-7（MUST）+ AC-8（SHOULD）。

### 11.2 Suite 级

`SR-1`：5 个预注册 seed 全部 Gate 5 PASS。
seed 预注册规则：$\text{seed}_i=20260904+i,\ i\in\{0..4\}$ → `{20260904, 20260905, 20260906, 20260907, 20260908}`。

### 11.3 部分通过时的处置（例：4/5）

| 对象 | 结论 |
| --- | --- |
| 4 个通过的 Run | **各自仍达 `SUPPORTED @ C2`** |
| 1 个失败的 Run | `G5 = FAIL`，生成 FailureRecord |
| C3 robustness | **`NOT_SUPPORTED`**（已检验、证据不足；非 REFUTED） |
| core suite | **FAIL** |

$$
\boxed{\text{一个 seed 失败，不得把其余已达独立参考精度的 C2 Run 降为 C1}}
$$

同时报告 mean / std / best / worst（第二十九条）与独立实验总数 $N$（第三十条）。

### 11.4 C3 的 scope 限定（新增）

即使 5/5 全部 PASS，C3 claim 的 `scope` **必须**逐项写明：

```
Poisson-1D v1.0（本 spec，本 protocol）
fixed architecture（该 Run 记录的架构）
fixed optimizer（该 Run 记录的优化器与调度）
fixed training protocol
five preregistered seeds 20260904..20260908
```

$$
\boxed{\text{不得泛化为 “PINN generally robust”}}
$$

依据第三十五条：验证单问题不得声称一般问题族；验证 5 个 seed 不得声称种子无关。

---

## 12. 失败治理与 rescue budget

```yaml
rescue_policy:
  max_rescue_runs: 3
  modification_policy: one_primary_factor_per_run     # 第二十四条
  compound_intervention: 允许但必须标记，不得用于因果归因
  termination: 超预算 → STOP，生成 FailureRecord，rootCauseStatus 可为 UNKNOWN
  forbidden: 自动"再多训练一点"
```

回流按第五十六条依次考察 `Spec → Baseline → Implementation → Scaling → Sampling → Optimization → Loss balance → Architecture → Numerical stability → Validation design`。

Negative result 是合法终点（第五十八条）：3 次 rescue 后仍不通过，正确输出是 `ClaimStatus = NOT_SUPPORTED` 的 ScientificClaim。

可复用 `user/user-skills/research-sop/kernel.py` 的 `max_rollbacks` 与 `unresolved` 终态。

---

## 13. 旧 `Desktop/pinns` 产出的登记方案

### 13.1 顶层标记（已批准）

$$
\texttt{LEGACY\_NONVALIDATED}
$$

### 13.2 原件处置

**冻结。不删除、不覆盖、不重写。** 登记通过**新增**旁置的 `legacy_register.json` 完成，不修改任何既有文件字节（第二十六、五十九条）。

### 13.3 逐 Run / 逐 artifact 分级

| 标签 | 适用 | 本案例 |
| --- | --- | --- |
| `FAIL` | **已检验且已证实**违反某条 MUST | 显示序投影存在于代码；early stopping 读出图网格；NaN 被吞；无 validation 层；无 spec |
| `BLOCKED` | 无法评估 | `复现/outputs_aligned*`：checkpoint 已丢失 |
| `UNVERIFIED` | 无证据支持，**亦无证据否定** | **Maxwell-MHD 场本身是否物理正确——无人验证过** |
| `REPRODUCIBILITY_LIMITED` | 环境/版本不可复现 | 全部 Run（无 commit、无 env 记录） |

### 13.4 必须写进登记簿的界定

> 审计确立的是：**当时的流程不足以支撑那些结论**。
> 审计**没有**确立：那些物理场是错的。
>
> $$\boxed{\text{证据不足以证明正确} \;\neq\; \text{已经证明错误}}$$
>
> 因此 Maxwell-MHD 结果的科学正确性标 `UNVERIFIED`，`ClaimStatus` 标 `BLOCKED`——**不是 `REFUTED`**。

### 13.5 执行时机

登记会写入 `pinns/` 旁置文件，属实施动作，**待批准后执行**。

---

## 14. HASH LOCK 程序（非自引用）

### 14.1 三个 hash input + 一个 lock

```text
specs/poisson-1d/v1.0/
    spec.json                         ← hash input
    protocol.json                     ← hash input
adversarial/core_manifest.json        ← hash input（预注册 expected verdict）
specs/poisson-1d/v1.0/lock.json       ← 承载三者 digest + Constitution digest
```

$$
\boxed{\text{禁止"hash 完文件后又修改被 hash 文件"}}
$$

### 14.2 被 hash 文件的约束

- 三个 hash input 不得包含 `specSha256` / `protocolSha256` / `adversarialManifestSha256` / 任何自身摘要。
- `lockedAt` 在 `spec.json` 中保留 key 但**恒为 `null`**（生命周期时间戳只存在于 `lock.json`）。
- spec/protocol/manifest 内只保存中性 `lockStatusAuthority = "lock.json"`；禁止永久 hash 入 `DRAFT — NOT HASH-LOCKED` 这类锁后失真的文本。

### 14.3 Canonicalisation（exact bytes）

| 规则 | 值 |
| --- | --- |
| 编码 | UTF-8，**无 BOM** |
| 行尾 | **LF only**，文件以**恰好一个** LF 结尾 |
| 强制 | `.gitattributes` 现有 `* text=auto eol=lf`，且 v1.3 已最小追加显式规则（§14.6） |
| 唯一序列化 | `(json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")` |
| 摘要对象 | **磁盘上的最终字节**（任何人可用 `sha256sum` 复核） |

已实测：`governance/PINN_RESEARCH_CONSTITUTION.md` 在 Windows 工作区为 `CRLF=0 / LF=1996 / 无 BOM / 单尾换行`，规则可行。

> 未采用 RFC 8785（JCS）：exact-bytes 用标准工具即可复核，更易审计。若将来需要跨序列化器可复现，走修宪/协议升版，不在本 MVP 改。

锁前必须同时满足 `actual_bytes == canonical_bytes`。因此不存在“verbatim 保存”第二条路径；BOM、CRLF、零尾换行、双尾换行、键/缩进布局不同，即使 JSON 语义相同也一律 FAIL。

### 14.4 两阶段算法（消除循环依赖）

```python
LOCK_VERSION = "1"
LOCK_FIELD_ORDER = (
    "specSha256",
    "protocolSha256",
    "adversarialManifestSha256",
    "constitutionSha256",
    "constitutionVersion",
    "lockVersion",
    "lockedAt",
)

# ---------- Phase A: PRELOCK_VALIDATION（不要求 lock.json） ----------
for path in (SPEC, PROTOCOL, ADVERSARIAL_MANIFEST):
    b = read_bytes(path)
    obj = json.loads(validate_utf8_lf_single_trailing_lf_no_bom(b))
    assert b == canonical_bytes(obj)
validate_spec_schema_and_semantics(SPEC)
validate_protocol_schema_assets_anticollision_and_leakage(PROTOCOL)
validate_expected_manifest_schema_counts_and_verdicts(ADVERSARIAL_MANIFEST)
validate_lock_draft_nulls_formula_and_constitution_binding(LOCK_DRAFT)
assert constitution_sha256 == LOCK_DRAFT["constitutionSha256"]
PRELOCK_VALIDATION = PASS

# 本轮到此停止。下列 Phase B 仅描述未来经人工批准的 P2：
assert human_approval_recorded()
assert PRELOCK_VALIDATION == PASS
spec_sha = sha256(read_bytes(SPEC)).hexdigest()
protocol_sha = sha256(read_bytes(PROTOCOL)).hexdigest()
manifest_sha = sha256(read_bytes(ADVERSARIAL_MANIFEST)).hexdigest()
locked_at = utc_now_iso8601()
fields = [spec_sha, protocol_sha, manifest_sha, constitution_sha256,
          "1.0", LOCK_VERSION, locked_at]
lock_sha = sha256(("\n".join(fields) + "\n").encode("utf-8")).hexdigest()
write_new_lock_without_overwrite(...)

# ---------- Phase C: POSTLOCK_GATE1 ----------
Gate1 = PASS iff PRELOCK_VALIDATION == PASS and lock.json.exists() and verify_lock()
```

`python -m pinn.governance.prelock` 只执行 Phase A；输出 candidate SHA 与使用显眼 sentinel 的 `candidateLockPayloadSha256`，均标记 `DRY-RUN ONLY — NOT A LOCK`，不写回任何 draft。`pinn.governance.locking.write_lock` 不由该 CLI 暴露、拒绝覆盖、并要求外部显式提供已通过的 prelock validator；本轮不调用。

未来命令行等价复核 payload：

```bash
sha256sum specs/poisson-1d/v1.0/spec.json specs/poisson-1d/v1.0/protocol.json adversarial/core_manifest.json governance/PINN_RESEARCH_CONSTITUTION.md
printf '%s\n%s\n%s\n%s\n%s\n%s\n%s\n' "$SPEC_SHA" "$PROTO_SHA" "$MANIFEST_SHA" "$CONSTITUTION_SHA" "1.0" "1" "$LOCKED_AT" | sha256sum
```

### 14.5 锁后变更

任何对 `spec.json` / `protocol.json` / `adversarial/core_manifest.json` 的修改都必须产生**新版本 artifact set**，并写新的 `lock.json`。**不得原地编辑后重算 hash**（第二、五十九条）。B8 与 manifest tamper regression test 检验此路径。

### 14.6 `.gitattributes` 现场状态与 v1.3 最小合并

```gitattributes
specs/**/spec.json      text eol=lf
specs/**/protocol.json  text eol=lf
specs/**/lock.json      text eol=lf
adversarial/**/core_manifest.json text eol=lf
*.npy binary
```

现场核验显示：任务开始时 `.gitattributes` **无未提交 diff**，并已有 `* text=auto eol=lf`。v1.3 因而采用最小 append，保留全部原规则并加入以上显式加固；没有覆盖用户改动。若未来现场不同，仍必须先读 diff 再 merge。

---

## 15. 实施顺序

| 阶段 | 内容 | 依赖 |
| --- | --- | --- |
| P1 | domain objects + 目录契约 + **artifact provenance 与信任边界** | —；v1.3 锁前治理子集已实现并测试 |
| P2-prelock | schema + canonical bytes + frozen nodes + expected manifest + lock draft dry run | P1；**本轮只到这里** |
| P2-formal | final spec/protocol/manifest 落位并 HASH LOCK | P2-prelock PASS + **人工最终批准**；本轮禁止进入 |
| P3 | Gate 2a 解析 reference + Gate 2b FDM 子系统 | P2 |
| P4 | verify/ + Gate 3 | P2 |
| P5 | PINN 实现 + Run 记录器 + Gate 4 | P4 |
| P6 | validate/ + Gate 5（leakage 四检 + provenance 准入） | P3, P5 |
| P7 | **15-case core suite** | P6 |
| P8 | FailureRecord / Taxonomy / rescue budget | P7 |
| P9 | Gate 6/7 + claim ledger + SR-1 | P8 |
| P10 | STOP THE LINE 状态 + legacy register 落地 | P9 |

**P7 不得压缩。**

顺序硬约束：`P1 → P2-prelock → STOP / HUMAN REVIEW → P2-formal`。禁止先 HASH LOCK 再补 P1，也禁止把 prelock candidate digest 称为 locked digest。

---

## 16. 完成定义

1. G1 在 5 个预注册 seed 上各自 G1–G7 PASS，`SUPPORTED @ C2`；SR-1 满足则 C3 `SUPPORTED`，且 scope 按 §11.4 限定。
2. B1–B11 全部按**首次执行前冻结**的三层元组被拒，各生成分类正确的 FailureRecord。
3. U1–U3 全部 `ClaimStatus = BLOCKED`，无一被判 SUPPORTED / NOT_SUPPORTED / REFUTED。
4. 任一 Run 可从 `runId` 追溯到 code → spec → environment → data → validation。
5. 全部主图由脚本从 `claimEvidenceEligible = true` 的 artifact 重绘，不含任何平滑、边界改写、保序投影。
6. `research_logs/` 记录每一次失败与每一个被推翻的判断。
7. core suite 中 `EMPIRICAL_CHALLENGE` 数为 0；`verify_lock()` 通过。

在 1–7 全部成立前：

$$
\boxed{\text{PINN scientific closed-loop MVP} = \text{NOT ESTABLISHED}}
$$

---

*本计划遵守宪法第六十一条优先级链。若本计划任一条与宪法冲突，以宪法为准。宪法 v1.0 一字未改。*
