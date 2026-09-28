---
amendmentId: A-0002
oldVersion: 1.1
newVersion: 1.2
status: ACCEPTED
effectiveDate: 2026-09-15
dependsOn:
  - amendmentId: A-0001
    requiredStatus: ACCEPTED
    requiredConstitutionVersion: "1.1"
proposedBy: Claude（队长）依据 DeepSeek R2 交付物 §1.3、`R2_MERGE_NOTES.md` §7–§8；第 1 稿由用户授权队长裁决 DeepSeek 建议起草；第 2 稿按 2026-09-15 用户复审（PROPOSED / CHANGES REQUIRED）做因果可判定审查后修订；第 3 稿按 2026-09-15 用户 FINAL CLOSURE REVIEW（三项剩余问题 + 准入审计）收口，只做最小修复，不扩张机制
---

## reason

宪法 1.1 第 3.1 条的可接受矩阵（`state_machine.ADMISSIBLE_ROOT_CAUSES`）是封闭表：一个症状只能被命名为表内的根因。封闭表要防两种错误——**假可接受**（不存在或无法识别的根因被允许，Agent 可以挑便宜根因）与**假排除**（真实因果路径因缺格被迫错路由或停线）。第 1 稿依 DeepSeek R2 补了三格；用户复审指出第 1 稿对另外两格的驳回理由不成立、P23 的因果证据不足、rDataDefect 的驳回只是范围决定、以及修正案之间没有机器化的依赖。第 2 稿逐项裁决，并对整张矩阵做了一次闭合审计。

矩阵本身不是越大越安全、越小越严格：它必须等于当前范围内**真实可发生且可被区分实验识别**的因果路径集合，而每增加一个候选，命名任一根因前必须排除的竞争解释同步增加。

## affectedArticles

- 第三章 3.1，可接受矩阵增加八格（第 1 稿三格 + 第 2 稿五格），根因 → Gate 映射不变：
  - `sBcResidual → rCapacityLimit`（G4）：复杂边界数据小网络拟合不到。
  - `sPinnCfd → rCapacityLimit`（G4）：容量不足直接表现为与参考的差距，见 scientificJustification 对残差与误差关系的表述。
  - `sLocalizedError → rSpecDefect`（G1）：源项 / 边界局部位置或强度写错。
  - `sPinnCfd → rSamplingDeficiency`（G4，第 2 稿）：小测度的重要区域欠采样使 QoI 偏移，而按 L2 类范数在评估节点上度量的 PDE 残差可以不越阈。
  - `sSeedSensitive → rImplementationDefect`（G3，第 2 稿）：非确定性实现缺陷（RNG 泄漏、竞态、评估时未关的 dropout、data-loader worker RNG 污染、非确定归约）表现为 seed 敏感。
  - `sSeedSensitive → rSpecDefect`（G1，第 2 稿闭合审计，第 3 稿收窄）：**仅当** seed 变化暴露的是**非预期的**不可识别性或未消解的解等价（零空间 / 规范自由 / 归一化 / 分支 / 对称），且冻结的 Claim 需要唯一可评估目标而规格没有消除它（如 Claim 比较绝对压力、纯 Neumann Poisson 未规定 ∫p = 0）。非线性 PDE 的合法多分支、分岔、对称相关解、规范自由本身不是缺陷；分支感知的 Claim 或已定规范的规格下 seed 落入不同分支不得命名本格；证据不能判定多解是否有意 → rUndetermined 停线。
  - `sPdeResidual → rSingularityTreatment`、`sBcResidual → rSingularityTreatment`（G1，第 2 稿闭合审计）：目标案例的再入角在精确解处导数无界、角点数据不相容，未处理的奇异性可以单独把全局残差或边界残差推过阈值。
- 第三章 3.1，命名根因的证据义务升级为结构化、机器可判（`state_machine.intervention_errors` / `determinism_replay_errors`，契约 `diagnosis-record.schema.json`）：
  - 命名 `rCapacityLimit` 或 `rSamplingDeficiency` 必须附**受控干预** `discriminatingExperiment.intervention{factor, changed, heldFixed, levels, optimizationDiagnosticsClean?}`：只改一个控制项（capacity → architecture，sampling → sampling），其余控制项（architecture / sampling / optimizer / lrSchedule / lossWeights / trainingBudget / spec / reference / seedProtocol）全部固定，≥ 3 档、每档 ≥ 3 seed、逐档中位误差**严格下降**；容量另需 `optimizationDiagnosticsClean = true`。单次加大网络或加密采样后变好不是因果证据，它同时改变了优化景观。
  - 命名 `sSeedSensitive → rImplementationDefect` 必须附 **P33 同 seed 确定性重放** `discriminatingExperiment.determinismReplay{sameSeedRuns ≥ 2, maxDivergence, epsilonDet, defectLocated}`，且 maxDivergence > epsilonDet、缺陷已定位；重放一致则实现非确定性被排除、不得命名。
  - `excludes` 义务随矩阵扩张：命名任一根因必须排除该症状的**每一个**其它可接受根因（含新格）。
  - 命名 `sSeedSensitive → rSpecDefect` 必须附 **P34 可识别性记录** `discriminatingExperiment.identifiability{ambiguityType ∈ nullspace / gauge / normalization / branch / symmetry, claimRequiresUniqueEvaluation = true, specResolvesAmbiguity = false, ambiguityIntent = unintended, nullspaceProjectionFraction?}`（`state_machine.identifiability_errors`，第 3 稿）：`claimRequiresUniqueEvaluation = false`、`ambiguityIntent = intended`、`specResolvesAmbiguity = true` 各自拒绝命名（合法多解不是缺陷），`ambiguityIntent = undecided` 拒绝并指向 rUndetermined。P34 检验的不是"是否多解"，而是"这种多解是否违反冻结 Claim 要求的可识别性"。
  - DiagnosisRecord 可选 `observedSignatures`（必须含主症状）与 `explainedSignatures ⊆ observedSignatures`（默认 = 主症状；第 3 稿）：一条记录 R_j : explainedSignatures_j → rootCause_j，`excludes` 覆盖所解释症状候选集的**并集**；一个失败可以有多条记录（sPdeResidual ← 优化、sLocalizedError ← 奇异性），**症状覆盖不变量**（`trust_loop.diagnosis_coverage_errors`）要求记录集合同属一个失败、列出相同的 observedSignatures、⋃explained = observed（漏解释非法）、每个症状恰好一条记录（同一症状被两个根因同时声称非法——MVP 不定义单症状多因归因，分不开就 rUndetermined）。第 2 稿"根因必须对每个观察症状可接受，否则另立记录"的单因规则被此取代——它会错误强迫单因果解释，且"另立记录"只停留在文字。
- 第三章 3.1 与第六十章，**运行时版本隔离**（第 3 稿，Issue 1，BLOCKING 已修复）：治理语义 = f(constitutionVersion)，不是 master 上最新代码。`state_machine.ADMISSIBLE_ROOT_CAUSES_BY_VERSION{"1.1": A-0001 矩阵, "1.2": 本修正案矩阵}` 与 `NAMING_OBLIGATIONS_BY_VERSION{"1.1": ∅, "1.2": {intervention, determinismReplay, identifiability}}`；唯一入口 `admissible_root_causes(version)` / `naming_obligations(version)` 只接受 `locking.SUPPORTED_CONSTITUTION_VERSIONS` 内的版本（运行时读取），因此本修正案 PROPOSED 期间 "1.2" 不可选、绑定 1.1 的任何 run / DiagnosisRecord / PRELOCK / claim 流程都不能使用八个新格，也不欠 1.2 的干预 / 重放 / 可识别性义务；`diagnose(..., constitution_version=)`、`discriminating_experiment_errors(..., constitution_version=)`、DiagnosisRecord 必填 `constitutionVersion`——直接调用没有默认版本，不可能自动获得未来修正案的能力。登记簿不变量 R5：PROPOSED / REJECTED 的 newVersion 不得出现在 SUPPORTED 中（泄漏），ACCEPTED 的必须出现；PRELOCK 第七项同时要求登记簿每个版本与宪法声明版本都有运行时矩阵。生效配方不变：把 "1.2" 加入 SUPPORTED 的那一步即解锁 1.2 矩阵。
- 第三章 3.1，矩阵范围：**forward-problem MVP**（`state_machine.MATRIX_SCOPE`，`DiagnosisRecord.problemClass` 常量 `forward`）。正向问题里观测数据不进入 PDE 算子，`sPdeResidual / sConservation → rDataDefect` 不可接受是范围决定，不是永久科学命题；逆问题（θ = θ(D_obs) 或系数由数据识别）需要自己的修正案与矩阵，schema 在此之前拒绝 `problemClass ≠ forward`。
- 第六十章 修宪制度，机器化依赖（`pinn/governance/amendments.py`，PRELOCK 第七项检查 `amendmentRegister`）：修正案 frontmatter 可声明 `dependsOn[{amendmentId, requiredStatus, requiredConstitutionVersion}]`；不变量——ACCEPTED 修正案构成从 1.0 出发的单链，每个 ACCEPTED 的 oldVersion 等于前一个 ACCEPTED 的 newVersion，宪法元数据声明的版本等于链尾；ACCEPTED 修正案的每个依赖目标必须存在且处于要求的状态与版本；ACCEPTED 必有日期、PROPOSED 必为 PENDING。因此 `Constitution = 1.0, A-0001 = PROPOSED, A-0002 = ACCEPTED` 被拒绝。通用 `dependsOn` 比为 A-0002 特判更小：一个解析器、一个循环，之后每个修正案都用它。
- 协议汇编 §4：三格判定规则升级为受控干预；P33 确定性重放；P34 改为可识别性检验（合法多解 vs 非预期不可识别性）；explainedSignatures 与症状覆盖不变量；版本隔离；空格分类表。

## scientificJustification

- **sPinnCfd → rCapacityLimit 的表述（复审 Issue 1）**：第 1 稿写"残差是弱范数、差距是强范数"，这是过度泛化。准确的表述：‖R(u_θ)‖_Y ≪ 1 只有在存在与问题、边界条件和范数相匹配的稳定性估计 ‖u_θ − u*‖_X ≤ C_stab ‖R(u_θ)‖_Y 时才蕴含 ‖u_θ − u*‖_X ≪ 1；预注册的残差阈值 ε_R 与差距阈值 ε_E 是两个独立数字，没有任何条款保证 C_stab ε_R ≤ ε_E。对流占优、高 Re / Wi 的目标案例 C_stab 很大，而且残差在 D_phys 节点上按离散 L2 度量，差距按 claim 集上的 QoI 度量——两者的评估集与范数都不同。因此容量不足可以先表现为差距而残差不越阈。
- **sPinnCfd → rSamplingDeficiency（复审 Issue 2）**：命题"采样不足若造成 sPinnCfd 则必先触发 sPdeResidual"**不成立**。反例（复审给出，队长核实其机制）：残差按 L2 类范数在评估节点上平均，一个测度很小但对 QoI 决定性的区域（再入角下游的回流长度）欠采样时，残差的全局范数可以停在 9.8 × 10⁻⁴ < ε_R = 10⁻³，而 QoI 差距 4.1% > ε_E = 2%；固定架构、优化器、日程、权重、初始化协议、参考解与规格，只把采样密度 10⁴ → 5 × 10⁴，差距降到 1.1%。这是干预意义上的因果：可操纵变量、其余固定、症状随之消失。第 1 稿把采样叫"中介"混淆了三件事——因果根因（可干预的变量）、中介（因果链上的中间量，如"重要区域表示不足"）、可观测症状（残差、差距）。根因经由中介产生症状是常态，不是把它降级为中介的理由。
- **sSeedSensitive → rImplementationDefect（复审 Issue 3）**："实现缺陷是确定性的"**不成立**。未初始化状态、竞态、随机状态泄漏、错误的 RNG 处理、评估时未关闭的 dropout、data-loader worker 的 RNG 污染、非确定 kernel、依赖顺序的归约、异步状态修改，都是实现缺陷且直接表现为 seed 敏感。G3 的 T1–T10 是算子单元测试，P4 是精度扰动，都不是确定性审计；G3 PASS 不排除非确定性缺陷。层次划分：可接受矩阵描述**理论候选**（状态无关的封闭表），DiagnosisRecord 用证据逐个**排除**——G3 的产物可以作为排除 rImplementationDefect 的证据，但只有 P33 重放一致才是排除非确定实现的证据；重放发散且定位到缺陷，才能命名它。
- **受控干预（复审 Issue 5）**：E(C₂) < E(C₁) 不能单独证明容量不足，因为加大网络同时改变优化景观、条件数、梯度流与隐式正则化。P23 与 P25 升级为受控干预：三档以上、每档多 seed、其余控制项固定、中位误差沿档严格下降；容量另需优化诊断（分项 loss 收敛、梯度无病态）干净。仍然不是充分因果证明，但排除了"单次巧合"与"改了别的东西"两类混淆，且是机器可判的最低要求。
- **rDataDefect 的两格（复审 Issue 4）**：正向 MVP 下 observation data 不进入待求 PDE 算子或参数，data defect 无法传播到 PDE 残差 / 守恒失衡——这是范围内的事实，写进 `MATRIX_SCOPE` 与 `problemClass`，不写成永久命题。
- **闭合审计（复审 Issue 7）**：对 6 × 8 格逐格分类——IMPOSSIBLE：四个不涉及参考解计算的症状 → rReferenceDefect；OUT_OF_SCOPE：五个症状 → rDataDefect（正向）；UNSUPPORTED：sConservation → rSingularityTreatment（全局积分对小测度角点不敏感，没有案例证据）、sSeedSensitive → rSingularityTreatment；被遗漏的 ADMISSIBLE：sPdeResidual / sBcResidual → rSingularityTreatment（目标案例的再入角与角点不相容数据），sSeedSensitive → rSpecDefect（非唯一解）。三格补入，各有区分实验（P29 局部加密不收敛；P34 零空间投影）。
- **防挑便宜根因（复审 Issue 8）**：每加一个候选，`excludes` 的义务自动多一项（测试 `test_every_added_candidate_adds_an_exclusion_duty`）；容量与采样必须干预、非确定实现必须重放；`observedSignatures` 封住挑症状。
- **运行时版本隔离（Final Closure Review Issue 1）**：可执行治理要求文档版本与运行时语义一致。修复前矩阵是单一全局最新表，A-0002 起草的那一刻 1.1 的运行时就已经是 1.2 语义（多了八格，也多了干预 / 重放义务）——这正是"PROPOSED 修正案提前改变有效宪法行为"。修复是把表按版本分开并让选择版本的入口只认已生效版本，不重构状态机；1.1 的表在测试里逐格冻结（`FROZEN_1_1`），以后改运行时表不会悄悄改 1.1。
- **多症状多根因（Issue 2）**：真实失败常常是 s₁ ← r_A 且 s₂ ← r_B，强迫一个根因解释全部症状会制造假排除。正确的不变量在记录集合上：覆盖 100%、每症状一条记录；"挑症状"由覆盖封住而不是由单因规则封住。单症状多因归因 MVP 不定义：排除纪律下两个都成立就谁都命名不了，停线交人。
- **sSeedSensitive → rSpecDefect 收窄（Issue 3）**：非唯一解不等于规格缺陷——分岔、多分支、对称相关解、规范自由都可以是研究对象本身。缺陷只在"Claim 需要唯一可评估目标而冻结规格没有消除本应消除的不可识别性"时成立；P34 因此检验的是可识别性与 Claim 的关系，判定不了意图时不得默认为缺陷。
- 本修正案不是为了让任何实验通过：当前没有任何处于 FAILURE_RECORDED 之后的 run，没有任何 DiagnosisRecord 存在。

## impactOnExistingRuns

- 已有 Run：Poisson 1D v1.0 只有 PRELOCK 草案（宪法 1.1 绑定），没有诊断记录；无旧结论受影响。
- 代码：`state_machine.py`（`ADMISSIBLE_ROOT_CAUSES_BY_VERSION` 1.1 / 1.2 两表、`NAMING_OBLIGATIONS_BY_VERSION`、`admissible_root_causes` / `naming_obligations` / `effective_constitution_versions`、`ConstitutionVersionError`；`MATRIX_SCOPE`；`INTERVENTION_FACTORS` / `INTERVENTION_CONTROLS` / `FACTOR_CONTROL`；`intervention_errors`、`determinism_replay_errors`、`replay_diverged`、`identifiability_errors`，由带版本与 explained 参数的 `discriminating_experiment_errors` 调用；`diagnose(..., constitution_version=)`；`earliest_route`）；`diagnosis-record.schema.json`（必填 `constitutionVersion`；`problemClass`、`observedSignatures`、`explainedSignatures`、`intervention`、`determinismReplay`、`identifiability`）；`trust_loop.validate_diagnosis_record(document, constitution_version=None)`、`explained_signatures`、`diagnosis_coverage_errors`；`amendments.py`（R1–R5）；`prelock.py` 第七项检查含 R5 与运行时矩阵一致性。在 ACCEPTED 之前，1.2 的表存在于代码中但不可达：`admissible_root_causes("1.2")` 被拒绝，1.1 的运行时行为与 A-0002 起草前逐格相同。
- 测试：新增 `test_constitution_version_isolation.py`（29 项：1.1 拒绝每个 A-0002 格、1.2 在生效检查后允许、PROPOSED 不改 1.1 行为、直接 API 不可绕过版本门、PRELOCK 版本与运行时矩阵一致；多症状多根因覆盖、漏解释、冲突归因、单记录并集义务；Neumann + 绝对值 claim 判规格缺陷、合法多解不判、undecided 停线）；`test_state_machine_triage.py`（在模拟 1.2 生效的夹具下运行；反例改用仍不可接受的组合；八格可接受与排除义务；采样干预五种不足证据；容量干预与优化诊断；重放发散 / 一致 / 未定位；每加候选即加排除义务）；`test_trust_loop_adversarial.py`（constitutionVersion、problemClass、observedSignatures / explainedSignatures、文档级干预与重放）；新增 `test_amendments.py`（A-0002 不能在 A-0001 PROPOSED 时生效、不能对宪法 1.0 生效、A-0001 ACCEPTED 且宪法 1.1 时可以；依赖目标与版本；状态 / 日期纪律；真实登记簿；PRELOCK 第七项）。
- 文档：协议汇编 §4；`R2_MERGE_NOTES.md` §8；登记簿。生效时宪法正文 3.1 改 1.2，`SUPPORTED_CONSTITUTION_VERSIONS` 与三份 schema 枚举加 "1.2"，Poisson 草案重绑定，写新证据文件（与 A-0001 同一流程）。

## consequence

**被禁止**：绑定 1.1 的 run 或记录引用本修正案的任何格或义务；调用诊断 API 而不声明宪法版本；PROPOSED 修正案的版本出现在 `SUPPORTED_CONSTITUTION_VERSIONS`；一条记录解释它没有观察到的症状；观察到的症状没有任何记录解释；同一症状被两条记录归到不同根因；把合法多解（分支感知 Claim、有意多解研究、已定规范的规格）命名为规格缺陷；判定不了多解是否有意就命名规格缺陷；不做受控干预就命名容量或采样；干预时同时改动第二个控制项；只有一档改进就命名；优化诊断不干净时命名容量；重放一致或未定位缺陷就把 seed 敏感归为实现；命名任一根因而不排除该症状的其它每一个可接受根因；只登记候选集最小的症状而不列其它观察到的症状；把 sPinnCfd 归为参考解之外的 IMPOSSIBLE 格或把正向问题的残差 / 守恒失衡归为数据；把 A-0002 在 A-0001 未 ACCEPTED 或宪法不是 1.1 时置为 ACCEPTED。

**被允许**：八个新格在各自的区分实验支持下回到对应 Gate；把 G3 产物作为排除 rImplementationDefect 的证据（但排除非确定性实现只能靠 P33）；逆问题在未来修正案里重开 rDataDefect 的两格。

**生效前提**：用户终审 status 改 ACCEPTED 并填 effectiveDate 后，宪法正文 3.1 改为 1.2（"六类之一"改为对应的候选数，加入受控干预、重放、可识别性、范围、observedSignatures / explainedSignatures 与覆盖不变量、版本隔离条款，第六十章加 dependsOn 与 R5），`SUPPORTED_CONSTITUTION_VERSIONS` 与三份 schema 枚举加 "1.2"（这一步同时解锁运行时 1.2 矩阵；DiagnosisRecord schema 的 constitutionVersion 枚举已含 1.2），Poisson v1.0 草案重绑定，新证据文件；`amendments.py` 的链校验会拒绝任何越过 A-0001 的生效顺序，R5 会拒绝 ACCEPTED 却未加入 SUPPORTED 的半生效状态。

## reviewLog

| 稿 | 日期 | 评审 | 结论 |
|---|---|---|---|
| 第 1 稿 | 2026-09-15 | 队长起草（DeepSeek R2 §1.3 三格采纳、三格驳回） | 待用户终审 |
| 第 1 稿 | 2026-09-15 | 用户复审 | PROPOSED / CHANGES REQUIRED，六项 + 闭合审计要求 |
| 第 2 稿 | 2026-09-15 | 队长修订 | 待用户终审 |
| 第 2 稿 | 2026-09-15 | 用户 FINAL CLOSURE REVIEW | 三项剩余问题（运行时版本隔离、多症状多根因覆盖、sSeedSensitive → rSpecDefect 收窄）+ 闭合审计 + 实验准入审计 |
| 第 3 稿 | 2026-09-15 | 队长收口（`docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md`） | **READY FOR USER ACCEPTANCE**；status 仍 PROPOSED，等用户终审授权 |
| 第 3 稿 | 2026-09-15 | 用户终审（实验授权指令："A-0002 已通过用户终审，需先按既定依赖顺序完成正式生效"） | **ACCEPTED**，effectiveDate 2026-09-15；宪法正文更新为 1.2（3.2、第六十章【A-0002】），`SUPPORTED_CONSTITUTION_VERSIONS` 与三份 schema 枚举加 1.2，Poisson v1.0 草案重绑定，新证据文件 `PINN_V1.3_PRELOCK_DRY_RUN_A0002.json`（操作日志 §5.21） |

第 2 稿对复审六项的裁决：

| # | 复审意见 | 裁决 | 落点 |
|---|---|---|---|
| 1 | sPinnCfd → rCapacityLimit 的弱 / 强范数措辞过度泛化 | ACCEPT：改为稳定性估计表述，并指出 ε_R 与 ε_E 无条款关联、评估集与范数不同 | scientificJustification |
| 2 | sPinnCfd → rSamplingDeficiency 应采纳 | ACCEPT_WITH_MODIFICATION：采纳；干预实验比复审建议更严（单因子、其余固定、≥ 3 档 × ≥ 3 seed、中位严格下降）并机器化 | 第三章 3.1；`intervention_errors` |
| 3 | sSeedSensitive → rImplementationDefect 应采纳 | ACCEPT_WITH_MODIFICATION：采纳；命名前提为 P33 重放发散且定位缺陷；矩阵为理论候选、记录逐个排除的层次写明 | 第三章 3.1；`determinism_replay_errors` |
| 4 | rDataDefect 两格的驳回须限定范围 | ACCEPT：`MATRIX_SCOPE`、`problemClass = forward` | 第三章 3.1；schema |
| 5 | P23 单调下降不足以判容量 | ACCEPT：受控多档多 seed 干预 + 优化诊断干净 | 协议汇编 §4；`intervention_errors` |
| 6 | A-0002 对 A-0001 的依赖须机器化 | ACCEPT：通用 `dependsOn` + 链不变量 + PRELOCK 检查（优于特判） | 第六十章；`amendments.py` |

第 3 稿对 Final Closure Review 三项的裁决：

| # | 剩余问题 | 裁决 | 落点 |
|---|---|---|---|
| 1 | PROPOSED 修正案不得提前改变有效宪法的运行时行为 | **BLOCKING，已修复**：矩阵与命名义务按版本分表，入口只认已生效版本，API 必填版本，schema 必填 constitutionVersion，登记簿 R5，PRELOCK 一致性 | `state_machine` / `trust_loop` / `amendments` / `prelock` / schema；21 项测试 |
| 2 | observedSignatures 必须支持多个独立根因并满足覆盖不变量 | ACCEPT_WITH_MODIFICATION：`explainedSignatures` + 集合级 `diagnosis_coverage_errors`；单症状多因归因不定义（→ rUndetermined） | `trust_loop`；schema；4 项测试 |
| 3 | sSeedSensitive → rSpecDefect 限定为非预期不可识别性 | ACCEPT：`identifiability` 记录与 `identifiability_errors`；P34 改为可识别性检验 | `state_machine`；schema；协议 §4；4 项测试 |

驳回记录：无（复审六项全部成立；第 1 稿被驳回的是队长自己的两条理由；第 3 稿三项全部成立，其中第 2 项按"接受问题、不机械接受实现"改为集合级不变量）。DEFERRED / NON-BLOCKING：单症状多因归因、schema 字段按版本拆分、逆问题矩阵、nullspaceProjectionFraction 阈值。闭合审计新增：sPdeResidual / sBcResidual → rSingularityTreatment、sSeedSensitive → rSpecDefect（ADMISSIBLE，补入）；observedSignatures（NON-BLOCKING 风险"挑症状"，已封）。
