# R2 合并说明（队长：Claude）· 2026-09-15

对象：`docs/pinn-trust-loop/inbox/` 下的 R2 交付物，以及用户 2026-09-15 对 A-0001 第 2 稿的复审（PROPOSED / MINOR CHANGES REQUIRED，五项 + 对抗性闭合审计要求）。本文件记录收件核对、各车道摘要、逐项裁决（含驳回及其论证）、落地位置。分歧只记录，不抹平。

## 0. 收件核对（字节原样入库）

| 文件 | 作者 | SHA-256（前 12 位） | 行数 | 来源与范围 |
|---|---|---|---|---|
| `PINN_TRUST_R2_SCHEMAS_STATE_MACHINE.md` | GLM | `6edec0c24f5b` | 541 | 用户放在桌面（`C:\Users\user\Desktop\`），队长 `cp` 入库并 `cmp` 复核；1.1 契约审核、三份新契约、状态机第 2 版、T29–T60；未越界 |
| `PINN_TRUST_R2_IMPL_TRAINING.md` | Kimi | `6497bb9b8ea1` | 220 | 用户放入收件箱；评估集操作协议、seed 协议第 2 版、物理检查实现清单、C3 登记清单；未越界 |
| `PINN_TRUST_R2_REPORT_AND_WORKFLOW.md` | 豆包 | `2792e505d932` | 174 | 用户放入收件箱；报告模板第 3 稿写法、示例 (b) 第 2 版、失盲处置流程、术语表；未越界 |
| `PINN_TRUST_R2_MATH_CORE.md` | DeepSeek | `3332850a6ce3` | 241 | 第 3 稿合并时未找到；用户 2026-09-15 终审同日告知位置 `C:\Users\user\PINN_TRUST_R2_MATH_CORE.md`，队长 `cp` 入库并 `cmp` 复核（原件未动）；逐格区分实验 P22–P32、seed 阈值统计论证、泄漏信息流不变量、Applicability 表；未越界。裁决见 §7 |

三份都按词表写作，都把不确定项写进了"待队长决定"，没有一份猜测仓库路径或输出补丁。GLM 的 schema 片段只用了校验器支持的关键字子集。

## 1. 各车道一句话摘要

- **GLM**：对 1.1 三份契约提出 P1–P7、V1–V8、C1–C7、D1–D4 共 26 条漏洞与修订；补 DiagnosisRecord、ClaimSetEvent（哈希链、六条不变量）、RunRecord（environmentId / codeHash / seedSetId 派生规则）；状态机第 2 版 17 行转移表与伪代码；T29–T60（16 条对抗）。
- **Kimi**：D_train / D_dev / D_claim（+ D_phys）的生成、位级互斥、哈希登记、密封持有、"打开"的操作清单、失盲五步处置、日志最小字段；seed 协议第 2 版八步判定、k 的定义、三因子账簿、N 的折中、F1–F8 禁止清单；PH1–PH10 实现级检查表；环境强 / 弱字段、codeHash 覆盖范围、seed 集去重、run 登记表。
- **豆包**：抬头评估集披露行、CheckResult 逐条写法与 NOT_APPLICABLE 标准句、Known failure modes 六槽位句式与停线句式、C3 独立性披露句式；示例 (b) 第 2 版；失盲处置流程、失败条目"症状 / 诊断"分块、EXPLORATORY 三条；术语表 16 条。
- **DeepSeek**（补交）：P22–P32 隔离式诊断实验库与六症状逐格 (a)(b)(c) 表，建议增 3 格、不加 3 格；Clopper–Pearson 与似然比论证 0.9 / 0.8 线与 N = 5 只能 PARTIAL，算力换置信表；"看过即失盲"的信息流不变量与五条可判定检查项；三类问题的 Applicability 表。

## 2. 用户复审五项的裁决（对抗性治理审查）

裁决标准：类型一致性、科学有效性、状态机封闭性、可机器判定性、可复现性、防 Agent 绕过。不因为是评审意见就默认正确，也不因为现有测试通过就默认现有设计正确。

### Issue 1 — 全 NOT_APPLICABLE 时的维度语义

**A. 是否存在语义冲突？** 是。第 2 稿把"检查清单非空且全部 NOT_APPLICABLE"折算成 NOT_CHECKED；前者是"适用性评估已执行、该问题不承担这些检查"，后者是"应查未查"，两者不同，折算是语义回流。

**B. 方案取舍。**

- 方案 1（DimensionResult 加 applicability，整维无 TrustStatus、不进 meet）：**REJECT**。它把"整维豁免"做成一个合法开关。六个维度各对应一道 MUST Gate（G1、G3、G4、G5a、G5b、G6），一个不承担任何检查的维度等价于"这道 Gate 对该问题不存在"，这不是 run 级可以声明的事。Agent 最想要的就是这个开关。
- 方案 2（ScientificSpec / ClaimPrerequisite 显式豁免）：**REJECT**。把开关从 run 挪到规格，Agent 写规格时同样能打开它；且它引入第二套前提矩阵，与 REQUIRED_DIMENSIONS 并存必然漂移。
- 方案 C（不变量禁止全 N/A）：**ACCEPT**，写成 INV-A1 并落代码与测试。

**C. 落地。**

- `trust_vector.dimension_status_from_checks`：空清单 → NOT_CHECKED；非空但无 APPLICABLE → 抛 `NoApplicableCheck`（ValueError 子类）。
- `ProblemDefinition 1.2.checkApplicability`：适用性在 SPEC_LOCKED 时随规格登记（进 specHash），每个维度至少一项 APPLICABLE（规格级 INV-A1），NOT_APPLICABLE 必须写理由。
- `validate_trust_vector(document, problem_definition)`：已执行维度（PASS / PARTIAL / FAIL）必须展示检查；检查集合必须等于注册表（不漏、不多、不改标）；status ≤ meet，低于 meet 必须 notes 说明。
- 若将来某类问题对某维度确实一项检查都不承担：那是宪法级缺口，立新修正案补检查；不给 run 豁免。

测试：`test_trust_vector.py::test_all_not_applicable_is_an_illegal_registration_not_a_weak_not_checked`、`test_trust_loop_adversarial.py` 前六条。

### Issue 2 — 哈希不同不能证明集合互斥

**ACCEPT。** 审查结论：第 2 稿 `_evaluation_set_errors` 只比较三个 sha256，**没有**任何样本级校验；修正案文字"两两互斥升为 MUST"没有机器落点。

落地（`pinn/governance/evaluation_sets.py` + `evaluation-set.schema.json`）：

- 评估集是一份样本清单 `{schemaVersion, artifactId, role, inputNames, generator?, samples[{inputs, kind, quantity?}]}`；清单的规范化哈希就是规格登记的 artifact 哈希，因此互斥证明绑定的正是规格指定的集合。
- 样本身份 = `canonical_sha256({"inputs": [float64…], "quantity": quantity|null})`。浮点按 float64 精确值（规范化 JSON 的 shortest-roundtrip repr 与 float64 位模式一一对应），−0.0 折入 0.0，整数 1 与 1.0 同一，NaN / Inf 拒绝。**"几乎相同"不是身份问题**：由预注册的 `evaluationSets.minSeparation`（进 specHash）以欧氏距离机械判定，缺省不检查。
- 参数化 PDE：(x, t, μ) 是网络输入，μ 不同即不同样本；μ 相近的泄漏由 minSeparation 在全输入空间上判定。逆问题：观测身份 = (坐标, 观测量名)；同坐标不同量是不同观测，但同坐标的位置泄漏仍由 minSeparation 捕获。
- kind（interior / boundary / initial / observation）是元数据不是身份：边界点、初值点都是训练可见样本。规则：训练可见样本 ∩ (dev ∪ claim ∪ phys) = ∅，dev ∩ claim = ∅。
- Kimi 的 D_phys 采纳为可选集 `evaluationSets.phys`：物理检查节点若与训练点重合，残差检查不是证据。
- 复杂度：O(N·M) 纯 Python（.venv 无 numpy），每个冻结规格跑一次，MVP 点数可接受；大规模 2D 集需要空间索引，记为后续工程项。

测试：`test_evaluation_sets.py`（9 项，含评审的 {1,2,3,4,5} vs {1,2,3,4,6}）、`test_trust_loop_adversarial.py` 数据隔离三条。

### Issue 3 — SEALED → OPENED 必须不可逆

**ACCEPT_WITH_MODIFICATION。** 审查结论：第 2 稿的 claimSetStatus 是普通可写字段；状态 SEALED + 历史里有本版本的 OPENED 记录，校验器**不报错**（burnt 只看更早版本）——SEALED → OPENED → SEALED 在同一版本内确实可以伪装成从未打开。GLM P2 同时指出 claimSetHistory 内嵌于文档、可随文档重写。

- 方案 A（append-only 事件历史）与方案 B（status 由历史推导）**同时采纳**：`claim_set_ledger.py` 的哈希链账本（eventId = 除 eventId 外全部字段含 prevEventId 的规范化哈希）+ `derive_claim_set_state`；文档的 claimSetStatus / claimSetOpenedAtRevision / claimSetHistory 必须等于推导值。
- 账本不变量 L1–L7：链完整、时间单调、SEALED 先于 OPENED 且 specHash 一致、OPENED 必记 codeHash、同一哈希终身只 OPENED 一次（GLM 的"全局永久烧毁"）、同一 (problemId, revision) 只 OPENED 一次、OPENED 后永不再 SEALED。
- **驳回"必须实现真正 append-only 存储"**：JSON 文件在本项目层级做不到密码学不可变；给出的等价治理保障是可检测性——任何删除 / 重排 / 改写使后续 eventId 失配，且 ClaimGateDecision 必须引用 `ledgerHead`，篡改账本就必须同时伪造人工终审阅读的决策。
- 附带修正（GLM P5，队长采纳）：specHash 排除 revision 与 claim 集状态字段，否则打开 claim 集即改变 specHash，同 specHash 的 C2 run 全部作废、C3 永远无法达成。claim 集改由账本的 SEALED 事件绑定到 (problemId, revision, specHash)。

测试：`test_claim_set_ledger.py`（6 项）、`test_trust_loop_documents.py::test_claim_set_state_is_derived_from_the_ledger`、`test_trust_loop_adversarial.py` claim sealing 三条。

### Issue 4 — C3 与 G6 的独立环境定义必须统一

**ACCEPT_WITH_MODIFICATION。** 审查结论：第 2 稿 `RunQualification.environment_id` 是不透明字符串，G6 没有任何环境代码——两处都没有定义，谈不上一致，但也说明"漂移"是必然的。

- 统一为 `EnvironmentFingerprint` + `environment_id`（强字段哈希）+ `independent_environments`；`c3_run_support` 与新的 `reproduction_status`（G6）都通过 environment_id 判独立性，只有一个规则。
- 强字段（任一不同即独立）：machineId、osFamily、acceleratorClass、frameworkVersion(major.minor)、blasBackend、dependencyLockHash、installationId。弱字段（单独不同不构成新环境）：osVersion、pythonVersion(patch)、acceleratorDriver。采纳 Kimi §4.1 的强 / 弱分法；hostname、用户名、路径不是身份（传入即拒）。
- 五个案例的裁定：A 同机不同独立安装 → 独立（最弱的可接受形式，检验结果不绑定于单一安装状态，与 R1 裁决 C12"不同机器或独立安装"一致）；B 同机同镜像两容器 → 同一环境（installationId = 镜像摘要相同）；C 不同机器同 lockfile → 独立；D 集群两节点 → machineId 不同即独立；E 不同 OS / 加速器 → 独立。
- **驳回"机械要求所有字段都不同"**与 GLM 提议把内存容量 / CPU 核数纳入身份：独立性的目的是排除单一安装 / 单一执行环境的偶然性，不是可移植性；字段越多，"刷环境数"越容易。
- G6 语义：同环境或同 seed 集的"复现"只证明确定性 → 协议未执行 → BLOCKED；执行了但落在容差外 → FAIL。

测试：`test_trust_vector.py` 案例 A–E 与 `test_reproduction_uses_the_same_environment_rule_as_c3`、`test_trust_loop_adversarial.py::test_same_machine_same_installation_with_a_new_hostname_is_one_environment`。

### Issue 5 — IQR / median 的零点与近零行为

**ACCEPT_WITH_MODIFICATION。** 审查结论：第 2 稿 `training_reliability_status` 只接收 `iqr_ok` 布尔值，除法在治理代码之外——正是评审说的"隐式实现细节"。

- 新增 `seed_statistics(errors, epsilon_spec, …)` 从逐 seed 误差计算 k、median、IQR（Tukey hinges）、worst。离散度规则写成 **`IQR > dispersionLimit × median`**：乘法比较，全程无除法。语义等于方案 A（median = 0 ∧ IQR = 0 → 不封顶；median = 0 ∧ IQR > 0 → 封顶 PARTIAL），但不产生 inf，也不需要"median ≈ 0"的机器容差规则（没有除法就没有放大）。
- **驳回方案 B（预注册分母下限 ε_floor）**：它是一个没有物理意义的数字，进了 ScientificSpec 也仍是人为的；在"误差全部极小"的情形下它把噪声比放大成判定，而在"误差全部为零"的情形下它反而把 0/ε_floor 判成正常——两头都错。
- NaN / Inf 的 run：发散 run，计入 N、不计入 k、worst = ∞ → worst_ok False；中位数落在发散 run 上 → FAIL。负误差：误差范数非负，负值是调用方错误，拒绝。Kimi 的"发散率 > 20% → FAIL"不单列：k/N < 0.8 已蕴含。

测试：`test_trust_vector.py` seed statistics 五条（median = 0 / IQR = 0、median = 0 / IQR > 0、近零、NaN、Inf、负值）。

## 3. 复审建议中被驳回的部分（完整论证）

```text
Decision: REJECT
Claim being rejected: Issue 1 方案 1 —— DimensionResult 增加 applicability，整维 NOT_APPLICABLE 时无 TrustStatus、不进 claim 的 weak-link meet。
Reason: 它创造了"一个必需维度可以合法地不存在"的状态，而必需维度 = MUST Gate 的对象。整维豁免正是最大化 Claim 等级的 Agent 想要的形式合法路径。
Existing protection: 第 2 稿已无此路径（全 N/A 折成 NOT_CHECKED 会阻断一切 claim，方向是安全的，只是语义错）。
Why the proposed change is unnecessary or harmful: 增加一种类型、一条前提矩阵之外的分支，且把"不承担"这个规格事实放到 run 级记录里。
Evidence: trust_vector.py: NoApplicableCheck / dimension_status_from_checks; trust_loop.py: _check_registry_errors; tests: test_all_not_applicable_is_an_illegal_registration_not_a_weak_not_checked, test_all_not_applicable_is_refused_at_spec_level_too.
Residual risk: 某类未来问题对某维度确无适用检查时需要立新修正案（这是设计意图）。
Alternative: INV-A1 + 规格级注册表（已采纳）。
```

```text
Decision: REJECT
Claim being rejected: Issue 1 方案 2 —— 由 ScientificSpec / ClaimPrerequisite 显式豁免整维。
Reason: 与方案 1 同一个开关，只是挪到规格里；写规格的仍是 Agent；且与 REQUIRED_DIMENSIONS 并存两套前提矩阵必然漂移。
Existing protection: REQUIRED_DIMENSIONS 是封闭常量，无豁免入口。
Why harmful: 引入第二真源。
Evidence: trust_vector.py: REQUIRED_DIMENSIONS; tests: test_example_* 系列。
Residual risk: 无新增。
Alternative: 同上。
```

```text
Decision: REJECT
Claim being rejected: Issue 3 中"必须实现真正 append-only / immutable 存储"。
Reason: 本项目层级是单机 JSON 文档，没有可信第三方或不可变介质；声称做到了就是假保证。
Existing protection / Alternative: 哈希链账本 + 决策必须引用 ledgerHead + 文档状态必须等于账本推导值，给出的是可检测性而非不可篡改性，并如实写进修正案。
Evidence: claim_set_ledger.py: validate_claim_set_ledger（L1 chain）; trust_loop.py: ledgerHead 校验; tests: test_history_deletion_reordering_and_rewriting_break_the_chain, test_deleting_the_opened_event_from_the_ledger_is_detected, test_a_decision_must_cite_the_ledger_head_and_an_opened_claim_set.
Residual risk: 攻击者同时重写账本与决策并让人工终审看假决策——这超出机器治理范围，属于宪法第三十九 / 四十章（不得伪造执行 / 文件）的人工审计对象。
```

```text
Decision: REJECT
Claim being rejected: Issue 4 中"environmentFingerprint 字段越全越好 / 都必须不同"（含 GLM 的内存容量、CPU 核数）。
Reason: 独立性检验的是"结果不依赖单一安装 / 单一执行环境的偶然性"，不是可移植性；字段越多，同一台机器"刷"出不同环境越容易，而真正的独立性并没有增加。
Existing protection / Alternative: 强 / 弱字段二分，environmentId 只哈希强字段，独立 ⇔ 强字段有一项不同。
Evidence: trust_vector.py: ENVIRONMENT_STRONG_FIELDS / ENVIRONMENT_WEAK_FIELDS / independent_environments; tests: test_case_a … test_case_e, test_patch_level_differences_never_make_a_new_environment.
Residual risk: installationId 的采集方式（venv 前缀 id / 镜像摘要）由 runner 工具决定，工具尚未实现（R3）。
```

```text
Decision: REJECT
Claim being rejected: Issue 5 方案 B —— 预注册分母下限 ε_floor。
Reason: 见 §2 Issue 5；一个无物理意义的数字，两头都错。
Existing protection / Alternative: IQR > limit × median 的乘法比较。
Evidence: trust_vector.py: seed_statistics; tests: test_dispersion_rule_has_no_division_and_no_floor.
Residual risk: 极小误差下 IQR 略大于 median 会封顶 PARTIAL——这是 fail-closed 的方向，可接受。
```

## 4. 队员建议的裁决（采纳 / 部分采纳 / 驳回）

| # | 来源 | 建议 | 裁决 | 说明 |
|---|---|---|---|---|
| R2-1 | GLM P1 | revision 严格递增按事件日志校验 | 部分采纳 | 账本的 (problemId, revision) 单次 OPENED + 决策 revision 必须等于规格与向量的 revision；"严格递增"的跨文档校验留给 RunRecord 注册表（R3） |
| R2-2 | GLM P2 | 烧毁自 OPENED 起全局永久；历史只认账本 | 采纳 | L4、L7；文档 history = 账本投影 |
| R2-3 | GLM P3 / P4 | claimSetHistory uniqueItems；OPENED ⇒ 字段条件 | 采纳 | schema uniqueItems；交叉校验 |
| R2-4 | GLM P5 | specHash 排除 claimSet\*，revision 不入哈希 | 采纳 | 见 Issue 3 |
| R2-5 | GLM P6 / Kimi §1.2 | 样本级指纹交叉校验 | 采纳并加强 | 见 Issue 2；不用"重叠率阈值"（互斥就是零重叠），用最小间距处理近重复 |
| R2-6 | GLM P7 | 三契约 additionalProperties:false | 已是 | 1.1 已声明 |
| R2-7 | GLM V1 / V3 | CheckResult 条件字段；external ∧ dev ⇒ status ∈ {NOT_CHECKED, BLOCKED} | 部分采纳 | 条件字段已在 1.1；**驳回** external 在 dev 上不得 PARTIAL / FAIL：dev 上的一致性观察是合法的诊断证据，PARTIAL 正是"查了不充分"的准确措辞；FAIL 进 FAILURE_RECORDED 是正确行为（dev 上都不一致更该停下） |
| R2-8 | GLM V2 / Kimi §3.3 | 适用性由注册表推导 | 采纳 | checkApplicability 进规格并进 specHash |
| R2-9 | GLM V4 | judgedBy 走 actor 注册表；OPENED-actor 污染集 | **驳回** | 打开 claim 集的人就是做最终验证的人，污染集会禁止同一研究者再做任何验证，不可维护；它想封的泄漏（把 claim 集内容带进下一版本）已由"打开即烧毁、新版本换新集"在数据层封死，新 claim 集是未见过的样本 |
| R2-10 | GLM V5 | perturbationsRun 引用 runId；PASS ⇒ worstCase 必填 | 部分采纳 | worstCase 在有扰动时必填（不限 PASS）；perturbationsRun 保留 P 编号（Red Team 矩阵编号是协议的一部分） |
| R2-11 | GLM V6 | 检查级 status 一律由通过率分档复算 | **驳回** | 通过率分档是 C_train 多 seed 协议的规则；物理检查、实现单测是确定性单次判定，套用 0.9 / 0.8 分档是语义错配（"90% 的通量平衡检查通过"没有意义） |
| R2-12 | GLM V7 | evidencePointers 内容寻址 | 已是 | artifactRef{artifactId, sha256} |
| R2-13 | GLM V8 | claim 上的 judgedAt ≥ OPENED.at | 部分采纳 | 用 claimSetSha256 + 账本 OPENED 事件绑定代替时间比较（时间戳可填，事件不可无） |
| R2-14 | GLM C1–C4 | qualifiedC2Runs 必须解析到 RunRecord、seedSetId / environmentId 派生、minItems 5 | 采纳（minItems 除外） | 派生 + 复算；RunRecord 注册表为可选参数；**驳回 minItems 5**：少于 5 个 run 的决策是合法的（它只是不许 C3），schema 不应把 C3 前提写成文档存在条件 |
| R2-15 | GLM C5 / C6 | 演算封闭、weakestLink 集合相等 | 已是 | claim_gate 是唯一演算；weakestLink 集合相等 1.1 已有 |
| R2-16 | GLM C7 / Kimi §4.2 | codeHash = 封闭清单的规范化哈希 | 采纳 | RunRecord.codeManifest；testHash 是否并入：**不并入**（测试代码不改变方法，但清单可包含 tests/ 目录，由规格的清单范围决定） |
| R2-17 | GLM D1 | 路由键 (rootCause, gate) | 已是 | ROOT_CAUSE_GATE 由根因唯一决定 gate，DiagnosisRecord.gate 只可选且必须等于派生值 |
| R2-18 | GLM D2 | 3 轮键 = (problemId, specHash)，revision 不入哈希 | 采纳 | 见 Issue 3 |
| R2-19 | GLM D3 | STOPPED_THE_LINE 出口：ABANDONED 终态、换 problemId 回 DRAFT | **驳回** | 新状态违反本修正案"状态集合不变"的承诺；宪法第五十八章已把 Negative Result 定为合法终点，停线的出口是人工裁决记录（DecisionRecord），不是状态机转移 |
| R2-20 | GLM 复发升级 | 跨 specHash 同 (rootCause, gate) ≥ 2 次自动停线评审 | **采纳**（用户 2026-09-15 同意） | 触发停线评审而非直接终止；需要跨规格的诊断注册表，实现 R3；写入协议汇编 §8 |
| R2-21 | GLM 枚举 / ID 改名 | S1–S6、rSpecAmbiguity 等、`sha256:` 前缀、`actor_`、`pinn_` | **驳回** | 仓库已定名（六症状、九根因、pdef- / tv- / cgd- / hex64），改名无保护增益、破坏既有测试 |
| R2-22 | GLM T29–T60 | 32 条用例 | 采纳可落地者 | T45 seed 改名、T46 环境伪造、T47 不升版重开、T48 N/A 藏 FAIL、T49 缺区分实验、T50 根因越界、T51 external dev PASS、T52 history 与 status 不一致、T53 weakestLink 少列、T54 混入其它 codeHash、T55 旧哈希复用、T56 条件字段、T58 空升版不重置、T59 账本篡改、T60 宽于演算 → 对应 `test_trust_loop_adversarial.py`、`test_claim_set_ledger.py`、`test_trust_loop_documents.py`；T57（污染 actor）随 R2-9 驳回 |
| R2-23 | Kimi §1.1 | D_phys 辅助集 | 采纳 | evaluationSets.phys 可选，与训练点互斥 |
| R2-24 | Kimi §1.4 | "打开"的操作清单、治理侧持有 | 采纳为协议 | 单机场景存储形态：用户 2026-09-15 同意由队长选型，选**权限目录**（治理账户独占可读、研究者账户无权限），不选加密文件（密钥与数据同机，只增管理不增保证）；写入协议汇编 §10 |
| R2-25 | Kimi §1.6 / 豆包 §3.1 | burnt 集可否降级为 D_dev | 裁决：**可以** | 它不再是盲的，这正是 dev 的定义；须以新哈希登记为 dev（或并入 train，改 specHash），永不再任 claim；账本烧毁只针对 claim 角色 |
| R2-26 | Kimi §2.1 | 发散率 > 20% 单列 FAIL | 不单列 | k/N < 0.8 已蕴含 |
| R2-27 | Kimi §2.3 | A 段归因扫描不计入 k/N | 采纳为协议 | 写入协议汇编 §6 |
| R2-28 | Kimi §4.1 | 强 / 弱字段；"仅 patch 差异判同一环境" | 采纳 | 见 Issue 4；不算过宽 |
| R2-29 | Kimi §6 ③ | 2D 点数与 PH9 阈值默认值 | 待预注册 | 协议汇编写区间，正式值 SPEC_LOCKED 前冻结 |
| R2-30 | 豆包 §5.2-1 | P12 越线压 C_physics 还是 C_external | 裁决：**只压 C_physics** | Red Team 矩阵 P12 列写的是 C_physics；一个扰动只降级矩阵指定的那一维，每个维度反映自己的证据；示例 (b) 的 C_external 由 claim 集一致性与网格无关性决定 |
| R2-31 | 豆包 §5.2-3 | 纯文字改动不升 revision 由谁判定 | 裁决 | 由哈希判定：specHash 与 codeHash 都不变即不升版（文档不在任一哈希内） |
| R2-32 | 豆包 §5.2-4 | C3 披露是否逐一列 environmentId | 裁决 | 列 environmentId（强字段哈希），不列原始指纹 |
| R2-33 | 豆包 §5.2-5 | 报告与 DiagnosisRecord 冲突 | 裁决 | 以机器记录为准，报告是只读渲染 |
| R2-34 | 豆包 §5.2-6 | 停线句式与禁用词自动校验 | 采纳原则 | 文本 lint 的实现是 R3（C15 延伸） |
| R2-35 | 豆包 §1.2 | 维度汇总句"没有 APPLICABLE 检查时维度 = NOT_CHECKED" | **改口径** | 按 INV-A1：没有登记检查 = NOT_CHECKED；登记了但全 N/A = 非法 |

## 5. 分歧记录（不抹平）

- GLM 的六症状 / 九根因 / ID 模式与仓库不同，原文保留，整合按仓库定名。
- GLM 提出的 ABANDONED 状态与 actor 污染集未采纳，原文保留，理由见 §4。
- Kimi 从严执行"burnt 集禁止降级为 D_dev"，队长裁决为允许；Kimi 原文保留。
- 豆包示例 (b) 第 2 版把 FM-1 同时压 C_physics 与 C_external，队长裁决只压 C_physics；豆包原文保留，模板第 3 稿示例按裁决改。
- DeepSeek R2 在第 3 稿终审同日补交，其建议的三个新矩阵格未进入已终审的 A-0001，作为 A-0002 候选保留；原文保留。

## 7. DeepSeek R2 的裁决（终审同日补交，2026-09-15）

| # | 建议 | 裁决 | 落点 |
|---|---|---|---|
| R2-36 | 诊断实验库 P22–P32，与 P1–P21 是否合并编号 | 不合并：P1–P21 对抗式加压，P22–P32 隔离式诊断，语义不同；编号不冲突，`DiagnosisRecord.excludes[].experiment` 的模式 `P[0-9]+` 两类都接受，无需改代码 | 协议汇编 §4 |
| R2-37 | 逐格 (a)(b)(c) 表 | 采纳为 `excludes` 的 observed 写法与数值约定 | 协议汇编 §4 |
| R2-38 | 矩阵增 3 格（sBcResidual → 容量、sPinnCfd → 容量、sLocalizedError → 规格） | **采纳，起草 A-0002（PROPOSED）**：用户 2026-09-15 授权队长裁决；三格理由成立（低容量同样导致 BC 欠拟合与 PINN–CFD 差距；源项 / 边界位置写错是局部误差的直接来源）且各有正交的区分实验；`ADMISSIBLE_ROOT_CAUSES` 与测试已同步，宪法 1.2 落笔待用户终审 | `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md` |
| R2-39 | 倾向不加的三格（sPinnCfd → 采样、sPdeResidual / sConservation → 数据、sSeedSensitive → 实现） | **A-0002 第 2 稿改判**：sPinnCfd → 采样与 sSeedSensitive → 实现改为采纳（用户复审反例成立，见 §8）；数据两格维持不加但范围写死为 forward-problem MVP | `A-0002` 第 2 稿 |
| R2-40 | seed 阈值统计论证；建议宪法写明"PASS ≠ 高置信认证 p ≥ 0.9" | 采纳为协议说明与升级路径（N ≥ 30 / 50 为预注册时可选，不是补救）；宪法正文措辞随 1.1 落笔一并处理 | 协议汇编 §6 |
| R2-41 | 泄漏信息流不变量与五条检查项 | 采纳；检查项 ② ④ 已由账本实现，⑤ 与既有规则不冲突而是补充（打开须既在 claim 集上又在 VALIDATION 阶段），① ③ 运行期断言为 R3 | 协议汇编 §10 |
| R2-42 | Applicability 表（Poisson / NS / Oldroyd-B） | 采纳；三列各至少一项 APPLICABLE，与 INV-A1 一致；NS 的正定性 / 对称性 / 极值原理 / SPD 全部 NOT_APPLICABLE 的理由可直接填入 reason | 协议汇编 §3 |

## 6. 落地位置

| 产物 | 位置 |
|---|---|
| 修正案第 3 稿 | `governance/AMENDMENTS/A-0001-trust-loop-r1.md`（status 仍 PROPOSED，effectiveDate PENDING） |
| 弱链演算 / seed 统计 / 环境身份 / G6 | `pinn/governance/trust_vector.py` |
| 评估集样本级互斥 | `pinn/governance/evaluation_sets.py`、`schemas/evaluation-set.schema.json` |
| claim 集账本 | `pinn/governance/claim_set_ledger.py`、`schemas/claim-set-event.schema.json` |
| 文档交叉校验 | `pinn/governance/trust_loop.py`；schema 1.2 三份；`schemas/run-record.schema.json`、`schemas/diagnosis-record.schema.json` |
| 状态机 | `pinn/governance/state_machine.py`（`discriminating_experiment_errors`，`diagnose` 调用它） |
| 测试 | `tests/pinn/test_trust_vector.py`（65）、`test_trust_loop_documents.py`（50）、`test_state_machine_triage.py`（39）、`test_trust_loop_adversarial.py`（23，新）、`test_evaluation_sets.py`（9，新）、`test_claim_set_ledger.py`（6，新） |
| 协议汇编第 3 稿 | `governance/PINN_TRUST_PROTOCOLS_R1.md` |
| 报告模板第 3 稿 | `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` |


## 8. A-0002 第 2 稿：用户复审六项的因果可判定裁决（2026-09-15）

| # | 复审意见 | 裁决 | 要点 |
|---|---|---|---|
| 1 | sPinnCfd → 容量的"弱 / 强范数"措辞 | ACCEPT | 改为稳定性估计表述：‖u_θ − u*‖_X ≤ C_stab‖R(u_θ)‖_Y 只在匹配的稳定性估计存在时成立；ε_R 与 ε_E 无条款关联；残差在 D_phys 节点按离散 L2，差距在 claim 集按 QoI |
| 2 | sPinnCfd → 采样应采纳 | ACCEPT_WITH_MODIFICATION | 复审命题 A（采样不足必先触发 sPdeResidual）不成立：小测度关键区域欠采样时 L2 平均残差可不越阈而 QoI 偏移；"中介"是混淆了可干预根因、因果链中间量与症状。采纳该格，干预实验比复审建议更严并机器化 |
| 3 | sSeedSensitive → 实现应采纳 | ACCEPT_WITH_MODIFICATION | "实现缺陷是确定性的"不成立（RNG 泄漏、竞态、评估时未关 dropout、worker RNG 污染、非确定归约）；G3 的 T1–T10 与 P4 都不是确定性审计。采纳该格，命名前提为 P33 同 seed 重放发散且定位缺陷；矩阵是理论候选、记录逐个排除 |
| 4 | rDataDefect 两格驳回须限定范围 | ACCEPT | `MATRIX_SCOPE = forward-problem-mvp`、`DiagnosisRecord.problemClass = forward`；逆问题另立修正案 |
| 5 | P23 单调下降不足 | ACCEPT | 受控干预：单因子、其余控制项固定、≥ 3 档 × ≥ 3 seed、中位误差严格下降、容量另需优化诊断干净；同样适用于 P25 采样 |
| 6 | 修正案依赖须机器化 | ACCEPT | 通用 `dependsOn`（`amendments.py`）：ACCEPTED 单链、宪法版本 = 链尾、依赖目标状态与版本；挂进 PRELOCK 第七项 `amendmentRegister`；比特判 A-0002 更小 |

对复审两问的直接回答：A. 采样不足能否直接解释 sPinnCfd——**YES**（干预意义上的因果，反例机制成立）。B. 实现缺陷能否解释 sSeedSensitive——**YES**（非确定性实现缺陷）。驳回的复审意见：无。

闭合审计（6 症状 × 8 根因）：IMPOSSIBLE 4 格（sPdeResidual / sBcResidual / sConservation / sSeedSensitive → 参考解）；OUT_OF_SCOPE 5 格（→ 数据，正向）；UNSUPPORTED 2 格（sConservation → 奇异性、sSeedSensitive → 奇异性）；被遗漏的 ADMISSIBLE 3 格补入（sPdeResidual → 奇异性、sBcResidual → 奇异性、sSeedSensitive → 规格 / 非唯一解，P34 零空间投影）。新发现风险：**挑症状**（只登记候选集最小的症状以缩小排除义务）——NON-BLOCKING，以 `observedSignatures`（根因须对每个观察到的症状可接受）封住；"漏报症状"不可机器判定，留给人工审计（宪法第三十九 / 四十章）。

矩阵第 2 稿后各症状的候选数：sPdeResidual 6、sBcResidual 7、sConservation 5、sPinnCfd 8、sSeedSensitive 5、sLocalizedError 7（rUndetermined 之外）。

## 9. A-0002 第 3 稿：Final Closure Review 三项剩余问题的裁决（2026-09-15）

| # | 剩余问题 | 裁决 | 要点 |
|---|---|---|---|
| 1 | PROPOSED 修正案不得提前改变有效宪法的运行时行为 | **BLOCKING，已修复** | 审计：`ADMISSIBLE_ROOT_CAUSES` 是单一全局最新表，`diagnose` 不读版本——文档 1.1 / 运行时 1.2 语义，且干预 / 重放义务也对 1.1 生效。修复：矩阵与义务按版本分表，`admissible_root_causes(version)` 只认 `SUPPORTED_CONSTITUTION_VERSIONS`（运行时读取），API 与 schema 必填版本，登记簿 R5（PROPOSED 版本不得已生效），PRELOCK 校验运行时矩阵。1.1 矩阵在测试里逐格冻结。不重构 |
| 2 | observedSignatures 必须支持多个独立根因并满足覆盖不变量 | ACCEPT_WITH_MODIFICATION | 接受问题：单因规则会错误强迫单因果解释。采用 `explainedSignatures ⊆ observedSignatures` + 集合级 `diagnosis_coverage_errors`（同一失败、同 observed、∪explained = observed、每症状恰好一条记录）；单症状多因归因不定义——排除纪律下两个都成立就谁都命名不了，rUndetermined 停线；多记录重入取最小 Gate |
| 3 | sSeedSensitive → rSpecDefect 限定为非预期不可识别性 | ACCEPT | 非唯一解 ≠ 规格缺陷。`identifiability` 记录：Claim 需要唯一目标、规格未消除歧义、歧义非有意三者同时成立才可命名；分支感知 Claim / 有意多解 / 已定规范 → 拒绝；undecided → rUndetermined。P34 改为可识别性检验 |

Final Decision Recommendation：**READY FOR USER ACCEPTANCE**（status 仍 PROPOSED）。准入审计 `PINN_AGENT_EXPERIMENT_READINESS: NOT_READY`，只有三个 blocker：A-0002 等用户终审；Poisson 1D 校准实验尚未实跑（草案 lockedAt = null，无 ProblemDefinition / 评估集清单 / RunRecord / TrustVector / ClaimGateDecision，runner 工具 R3 未实现）；失败路径实验尚未实跑。完整报告 `docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md`。测试 1058 → **1087 passed / 2 skipped**（+29），PRELOCK 7/7 PASS。停止设计新治理规则：终审后进入 Poisson 1D 校准实验。
