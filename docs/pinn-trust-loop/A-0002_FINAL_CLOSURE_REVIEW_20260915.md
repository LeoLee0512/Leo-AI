# A-0002 Final Closure Review 与 PINN Agent 实验准入审计（2026-09-15）

评审人：Claude（队长、宪法维护者）。对象：`governance/AMENDMENTS/A-0002-admissible-matrix-r2.md` 第 3 稿。本轮只解决三项剩余问题并做准入审计，不新增 Gate、状态或协议层；status 保持 `PROPOSED`、effectiveDate 保持 `PENDING`，等用户终审授权。

## 1. A-0002 Final Decision Recommendation

```text
READY FOR USER ACCEPTANCE
```

三项剩余问题全部解决（Issue 1 原为 BLOCKING，已最小修复并有测试），全套 1087 passed / 2 skipped / 0 failed，PRELOCK 七项 PASS，闭合审计没有新的 blocking contradiction。建议用户终审；队长不自行 ACCEPT。

## 2. 三项剩余问题裁决

| Issue | Decision | Evidence | Code/Test impact |
|---|---|---|---|
| 1 运行时版本隔离 | **BLOCKING，已修复**（ACCEPT）。审计结论：修复前 `ADMISSIBLE_ROOT_CAUSES` 是单一全局最新表，`diagnose()` / `validate_diagnosis_record()` 不读宪法版本，文档 = 1.1 而运行时 = 1.2 语义；干预 / 重放义务同样对 1.1 生效（把 1.1 变严也是泄漏）。 | `state_machine.ADMISSIBLE_ROOT_CAUSES_BY_VERSION{"1.1","1.2"}`、`NAMING_OBLIGATIONS_BY_VERSION`、`admissible_root_causes(version)` 只接受 `locking.SUPPORTED_CONSTITUTION_VERSIONS`（现为 1.0/1.1）内的版本；`diagnose(..., constitution_version=)` 与 `discriminating_experiment_errors(..., constitution_version=)` 为必填关键字，无默认；DiagnosisRecord schema 必填 `constitutionVersion`；`amendments.py` R5：PROPOSED 的 newVersion 不得已生效、ACCEPTED 的必须生效；PRELOCK 第七项同时校验登记簿每个版本都有运行时矩阵。 | `pinn/governance/{state_machine,trust_loop,amendments,prelock}.py`、`diagnosis-record.schema.json`；新增 `tests/pinn/test_constitution_version_isolation.py`（Issue 1 部分 21 项：1.1 拒绝八格 ×8、1.2 生效后允许 ×8、PROPOSED 不改 1.1、直接 API 不可绕过、PRELOCK 与运行时一致、真实运行时状态）；既有三角测试改为在"模拟 1.2 生效"夹具下运行 |
| 2 多症状多根因与覆盖不变量 | **ACCEPT_WITH_MODIFICATION**。接受问题：单条记录不得被迫解释全部症状。采用 `explainedSignatures ⊆ observedSignatures`（默认 = 主症状），覆盖不变量放在记录**集合**上；一个症状被两条记录归到不同根因 = 非法（不定义多因归因；分不开就 rUndetermined 停线）。 | `trust_loop.explained_signatures` / `diagnosis_coverage_errors(records)`：同 (problemId, revision, specHash, constitutionVersion, round)、同 observedSignatures、∪explained = observed、每个症状恰好一条记录；单记录的 `excludes` 义务 = 所解释症状候选集的并集；`state_machine.earliest_route` 多记录重入取最小 Gate。 | schema 加 `explainedSignatures`；`validate_diagnosis_record` 去掉"根因须对所有观察症状可接受"的单因规则；4 项新测试（两症状两根因覆盖、漏解释、冲突归因、单记录解释两症状的并集义务与挑症状） |
| 3 sSeedSensitive → rSpecDefect 收窄 | **ACCEPT**。仅当 seed 变化暴露**非预期的**不可识别性 / 未消解的解等价（零空间、规范自由、归一化、分支、对称）且冻结 Claim 需要唯一可评估目标时才是规格缺陷；合法多解不是缺陷；证据不能判定是否有意时不得叫规格缺陷，必须 rUndetermined。 | `state_machine.identifiability_errors`：命名该格必须附 `discriminatingExperiment.identifiability{ambiguityType, claimRequiresUniqueEvaluation = true, specResolvesAmbiguity = false, ambiguityIntent = unintended, nullspaceProjectionFraction?}`；`claimRequiresUniqueEvaluation = false`、`ambiguityIntent = intended`、`specResolvesAmbiguity = true` 各自拒绝；`undecided` 拒绝并指向 rUndetermined。 | schema `$defs/identifiability`；协议汇编 P34 措辞改写；4 项新测试（Neumann + 绝对值 claim + 无规范 → 规格缺陷；分支感知 claim / 有意多解 / 规格已定规范 → 拒绝；undecided → 停线；缺记录 → 拒绝；非 seed 症状不欠该记录） |

## 3. Runtime Version Isolation Evidence

| 场景 | 行为（当前仓库状态：宪法 1.1，A-0002 PROPOSED，`SUPPORTED_CONSTITUTION_VERSIONS = (1.0, 1.1)`） | 测试 |
|---|---|---|
| 1.1 behavior | `admissible_root_causes("1.1")` 返回冻结的 A-0001 矩阵（26 格，与 a94c138 逐格一致）；命名义务集合为空（无干预 / 重放 / 可识别性义务）；八个 A-0002 格 `diagnose` 抛 `IllegalTransition("... under Constitution 1.1")`，文档校验报 `not admissible ... under Constitution 1.1`；sPinnCfd → 规格的排除义务是 1.1 的 5 个候选，不是 1.2 的 7 个 | `test_1_1_rejects_every_a0002_only_admissible_cell[8]`、`test_proposed_a0002_does_not_change_1_1_behavior` |
| 1.2 behavior | 只有 `"1.2" ∈ SUPPORTED_CONSTITUTION_VERSIONS` 时可选（终审配方里加 "1.2" 的那一步即解锁）；此时八格路由到派生 Gate、文档校验通过、登记簿 R5 通过（A-0002 ACCEPTED + 宪法 1.2 + effective 含 1.2） | `test_1_2_allows_a0002_cells_after_dependency_and_effective_checks[8]`（monkeypatch 模拟生效） |
| PROPOSED amendment behavior | 代码里 1.2 表存在但不可达：`admissible_root_causes("1.2")` 抛 `ConstitutionVersionError("Constitution 1.2 is not effective ...")`；`validate_diagnosis_record` 对 constitutionVersion = 1.2 的记录返回同一错误；1.1 矩阵与义务与 A-0002 起草前逐字节相同 | `test_direct_diagnosis_api_cannot_bypass_version_gating`、`test_the_real_runtime_has_1_1_effective_and_1_2_proposed` |
| direct API behavior | `diagnose()` 无 `constitution_version` → `TypeError`；"1.0" → 无矩阵；"9.9" / 非字符串 → 拒绝；`discriminating_experiment_errors` 同样返回版本错误；`validate_diagnosis_record(record, constitution_version=run 的版本)` 记录与 run 版本不一致 → 错误；schema 缺 constitutionVersion → 错误 | 同上 |
| PRELOCK behavior | 第一项：宪法声明版本 ∈ SUPPORTED；第七项：ACCEPTED 链尾 = 声明版本，PROPOSED 的 newVersion ∉ SUPPORTED（否则报 "leaked"），ACCEPTED 的 newVersion ∈ SUPPORTED，登记簿每个 newVersion（≥ 1.1）与声明版本都有运行时矩阵。实跑 7/7 PASS | `test_prelock_version_and_runtime_matrix_agree`、`test_amendments.py::test_prelock_runs_the_register_check` |

结论：GovernanceSemantics = f(constitutionVersion)，单一事实来源是 `locking.SUPPORTED_CONSTITUTION_VERSIONS`（运行时读取，不在导入期固化）。不存在 PROPOSED 修正案泄漏到有效运行时的路径；不需要重构。

版本中性、记录为 DEFERRED / NON-BLOCKING：DiagnosisRecord schema 的 `problemClass = forward` 与可选 `observedSignatures` 字段对 1.1 记录同样存在。它们只增加信息、不改变任何可命名的根因或义务（1.1 本就只有正向 MVP），故不按版本拆 schema。

## 4. Signature Coverage Evidence

记录语义：一条 DiagnosisRecord = `R_j : explainedSignatures_j → rootCause_j`，`signature`（主症状）∈ `explainedSignatures_j` ⊆ `observedSignatures`。不变量（`diagnosis_coverage_errors`）：

- 所有记录属于同一失败（problemId, revision, specHash, constitutionVersion, round）且列出相同的 observedSignatures；
- ⋃_j explainedSignatures_j = observedSignatures（漏解释 → INVALID，错误文本给出漏掉的症状）；
- 每个症状恰好被一条记录解释（`s1 → rA` 与 `s1 → rB` 同时存在 → INVALID；MVP 不定义单症状多因归因，因为按排除纪律命名 rA 就必须排除 rB，两者同时成立时谁都不能命名 → rUndetermined 停线）；
- rUndetermined 记录也算覆盖（该症状的处置是停线）。

单条记录解释多个症状时，`excludes` 必须覆盖所解释症状候选集的**并集**；只登记便宜症状则另一症状无人解释，被覆盖不变量拒绝——"挑症状"在集合层面封住，同时不强迫单因。多条 DIAGNOSED 记录重入时取最小 Gate（`earliest_route`），下游全部重跑。

测试：`test_two_signatures_two_root_causes_are_two_records_that_cover_everything`、`test_a_signature_no_record_explains_is_a_coverage_failure`、`test_conflicting_attribution_of_one_signature_is_refused`、`test_one_record_may_explain_several_signatures_but_owes_the_union_of_exclusions`。

## 5. P34 / rSpecDefect Final Semantics

```text
sSeedSensitive -> rSpecDefect is admissible only when seed variation reveals
unintended non-identifiability or unresolved solution equivalence that prevents
the registered Claim from being uniquely evaluated under the frozen ScientificSpec.
```

| | legitimate multiplicity | unintended non-identifiability |
|---|---|---|
| 例 | 非线性 PDE 的多分支 / 分岔 / 对称相关解 / 规范自由，且 Claim 是分支感知或集合值的；或规格已给出规范条件 | 纯 Neumann Poisson `-Δp = f`，`p ~ p + C`，Claim 要比较绝对压力，规格未规定 ∫p = 0 或参考压力 |
| identifiability 记录 | `claimRequiresUniqueEvaluation = false` 或 `ambiguityIntent = intended` 或 `specResolvesAmbiguity = true` | `claimRequiresUniqueEvaluation = true`、`specResolvesAmbiguity = false`、`ambiguityIntent = unintended` |
| 裁决 | 不得命名 rSpecDefect（不是缺陷）；seed 落入不同分支要在其它候选里排除 | rSpecDefect → G1 |
| 证据不能判定是否有意 | `ambiguityIntent = undecided` → 拒绝命名，指向 rUndetermined 停线 | |

P34 检验的是"这种多解 / 零空间 / 等价关系是否违反冻结 Claim 要求的可识别性"，`nullspaceProjectionFraction` 只是可选证据（差投影到零空间的占比），不是判据本身。

## 6. Test Evidence

| 项 | 值 |
|---|---|
| previous baseline | 1058 passed / 2 skipped |
| new tests | 29（`test_constitution_version_isolation.py`：Issue 1 21 项、Issue 2 4 项、Issue 3 4 项（其中一项参数化 3）） |
| 修改的既有测试 | `test_state_machine_triage.py`（在模拟 1.2 生效夹具下运行、seed → 规格夹具补 identifiability）、`test_trust_loop_adversarial.py`（记录加 constitutionVersion；单因规则的断言改为 explainedSignatures 语义） |
| total passed | **1087** |
| failed | 0 |
| skipped | 2 |
| PRELOCK | `python -m pinn.governance.prelock` 7/7 PASS（constitutionBinding、spec、protocol、adversarialManifest、lockDraft、repository、amendmentRegister） |

## 7. A-0002 Final Closure Audit（有限检查）

1. runtime / version mismatch：无（§3）。
2. signature 未覆盖：无（§4）。
3. 某格科学含义明显过宽：sSeedSensitive → rSpecDefect 已收窄（§5）；其余七格的命名前提（干预 / 重放 / 排除并集）未变，未发现过宽。
4. 已知 Agent bypass：挑症状（集合覆盖封住）、挑便宜根因（排除并集）、单次改进冒充因果（受控干预）、把合法多解叫规格缺陷（identifiability）、把 1.2 格写进 1.1 记录（版本隔离）——均有测试。"漏报症状"不可机器判定，留人工审计（宪法第三十九 / 四十章）——DEFERRED / NON-BLOCKING。
5. amendment dependency bypass：R1–R5 + PRELOCK 第七项；ACCEPTED 未生效 / PROPOSED 已生效两向都拒绝。

DEFERRED / NON-BLOCKING（不扩张 1.2）：单症状多因归因的定义；schema 字段按版本拆分；逆问题矩阵；`nullspaceProjectionFraction` 的预注册阈值。

## 8. PINN Agent Experiment Readiness

```text
PINN_AGENT_EXPERIMENT_READINESS:
NOT_READY
```

| 类别 | 条件 | 状态 |
|---|---|---|
| Governance | A-0001 终审完成 | ✓ ACCEPTED 2026-09-15 |
| | A-0002 终审完成 | ✗ **BLOCKER 1**：队长已收口（READY FOR USER ACCEPTANCE），等用户终审"通过"并执行 1.2 配方（宪法正文 3.1 / 第六十章、SUPPORTED 加 1.2、三份 schema 枚举、Poisson 草案重绑定、新证据文件） |
| | 依赖顺序有效 | ✓ dependsOn A-0001 ACCEPTED @ 1.1，R1–R5 通过 |
| | Constitution / schema / runtime 版本一致 | ✓ 宪法 1.1 = 链尾 = SUPPORTED 内 = 有运行时矩阵 |
| | 无 PROPOSED 泄漏 | ✓ §3 |
| Implementation | full suite PASS | ✓ 1087 / 0 failed |
| | PRELOCK PASS | ✓ 7/7 |
| | no blocking TODO | ✓（R3 项：runner 工具、报告文本 lint、跨规格复发升级，均不阻塞 A-0002；runner 是 BLOCKER 2 的一部分） |
| | tree clean | ✓ 本轮提交后干净 |
| | evidence / version pins 一致 | ✓ `PINN_V1.3_PRELOCK_DRY_RUN_A0001.json` 绑 1.1 |
| Calibration experiment（Poisson 1D） | Frozen ScientificSpec / ProblemDefinition / D_train·D_dev·D_claim / multi-seed / 独立评估 / Trust Vector / Gate 执行 / ValidationReport / ClaimGateDecision / provenance / 复现证据 | ✗ **BLOCKER 2**：只有三份 PRELOCK 草案（lockedAt = null），没有 ProblemDefinition 实例、评估集清单、RunRecord、TrustVector、ClaimGateDecision、账本事件；捕获环境指纹与清单的 runner 工具未实现（R3） |
| Failure-path experiment | 至少一个已知失败案例走完 FAILURE_RECORDED → DIAGNOSED → REVISED → 重入 Gate | ✗ **BLOCKER 3**：状态机路径只有单元测试覆盖，尚无真实 run 走过 |

Blocker 1 是用户动作；Blocker 2、3 是下一阶段工作本身（Poisson 1D calibration + 一个人为失败案例，建议欠采样或错误 BC）。除此之外没有 blocker；不再新增治理规则，A-0002 终审后即进入 Poisson 1D 校准实验，由真实实验暴露下一轮问题。
