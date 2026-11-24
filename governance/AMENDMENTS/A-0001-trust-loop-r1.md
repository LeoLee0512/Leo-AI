---
amendmentId: A-0001
oldVersion: 1.0
newVersion: 1.1
status: ACCEPTED
effectiveDate: 2026-09-15
proposedBy: Claude（队长）代表六方团队（DeepSeek、GLM、Kimi、豆包、Claude 代 Grok），依据 docs/pinn-trust-loop/R1_MERGE_NOTES.md 与 R2_MERGE_NOTES.md 的裁决；第 2 稿按 2026-09-14 用户评审（CHANGES REQUIRED）修订；第 3 稿按 2026-09-15 用户复审（MINOR CHANGES REQUIRED）做对抗性治理审查后修订
---

## reason

现行宪法把"结果是否可信"压缩在 Gate 的四个状态与 ClaimStatus 里，缺少四样东西：(1) 一个逐维、不可平均的可信度表达，让用户看到短板在哪一维；(2) 验证 FAIL 之后的**分流**规则——现在只有 FAILURE_RECORDED → DIAGNOSED → REVISED 的骨架，没有规定诊断必须产出什么、回到哪道 Gate、循环多少轮为止；(3) 物理一致性（守恒、正定、对称、自由能）没有独立于"与参考解误差"之外的判定位置；(4) 训练可靠性只要求"字段全记、NaN 终止"，没有多 seed 的统计口径，一次偶然成功可以冒充稳定。R1 的五份交付物给出了这四样的具体形态，本修正案把其中已经裁决的部分条款化。

第 1 稿经用户评审为 **PROPOSED / CHANGES REQUIRED**（五项：症状直接路由、NOT_APPLICABLE 不在类型系统、评估集自适应泄漏、seed 阈值过松、C3 独立性未定义），第 2 稿逐项封死。第 2 稿经用户复审为 **PROPOSED / MINOR CHANGES REQUIRED**（五项：全 NOT_APPLICABLE 的维度语义、哈希不同不证明集合互斥、SEALED → OPENED 必须不可逆、C3 与 G6 的独立环境定义必须统一、IQR/median 的零点行为）。第 3 稿按对抗性治理审查逐项裁决（两项 ACCEPT、三项 ACCEPT_WITH_MODIFICATION，各有部分驳回），并对"形式合法、科学作弊"的路径做了一次闭合审计，新增的封堵见 affectedArticles 与 reviewLog。宪法状态集合与 Gate 状态集合**不变**。

## affectedArticles

- 第三章 闭环状态机：诊断分两层。观察到的 **FailureSignature**（sPdeResidual、sBcResidual、sConservation、sPinnCfd、sSeedSensitive、sLocalizedError）只是证据，不决定路由；FAILURE_RECORDED → DIAGNOSED 必须命名一个对该症状**可接受的 RootCauseClass**（rSpecDefect、rDataDefect、rSingularityTreatment、rReferenceDefect、rImplementationDefect、rCapacityLimit、rOptimizationFailure、rSamplingDeficiency、rUndetermined），并附症状证据与**区分实验**；由根因决定重入 Gate：规格 / 数据 / 奇异性处理 → G1，参考解 → G2，实现 → G3，容量 / 优化 / 采样 → G4；rUndetermined 直接 STOPPED_THE_LINE 交人工。可接受矩阵为封闭表。**第 3 稿：根因是排除后剩下的，不是挑选的**——区分实验记录 `discriminatingExperiment{experimentId, evaluationSet = dev, excludes{根因: {experiment, observed}}, evidencePointers}` 必须对该症状的**每一个其它可接受根因**给出排除记录，否则不得命名根因（`state_machine.discriminating_experiment_errors`、`DiagnosisRecord` 契约）；rUndetermined 只需 experimentId。重入 Gate k 时 k 及下游维度重置为 NOT_CHECKED（含 BLOCKED），下游 Gate 按顺序重跑；同一规格的诊断循环最多 3 轮，第 4 次 FAIL 直接 STOPPED_THE_LINE；轮次的键是 (problemId, specHash)，而 specHash 不含 revision，空升版不重置轮次。
- 第四章 Gate 状态：四个 Gate 状态不变。新增"可信度向量维度状态"TrustStatus = {PASS, PARTIAL, FAIL, BLOCKED, NOT_CHECKED}，其中 NOT_CHECKED 只表示"该维度对应的检查尚未执行"，**不是 Gate 状态**。新增独立类型 **Applicability = {APPLICABLE, NOT_APPLICABLE}** 与 **CheckResult{checkId, applicability, status?, reason, evidence}**：NOT_APPLICABLE 表示该问题不承担这项检查义务，必须写明理由，**没有 status**，不进入 meet；维度状态 = 其全部 APPLICABLE 检查的 meet。**第 3 稿 INV-A1：每个维度至少承担一项 APPLICABLE 检查**——"检查清单非空但全部 NOT_APPLICABLE"不是一种维度状态，而是非法登记（规格的检查注册表不完整），校验器拒绝；没有登记任何检查才是 NOT_CHECKED。适用性在 SPEC_LOCKED 时随规格登记（`ProblemDefinition.checkApplicability`，进入 specHash），TrustVector 里已执行维度展示的检查必须与注册表**逐项一致**：不得漏列、不得多列、不得改标；维度 status 不得高于其 APPLICABLE 检查的 meet，低于 meet 必须在 notes 说明（人工只能压低）。Gate 结果为 PARTIAL 或 BLOCKED 时状态机不推进；FAIL 一律进入 FAILURE_RECORDED，禁止就地重训。
- 第五章 ScientificSpec：ProblemDefinition 契约升到 1.2（`pinn/governance/schemas/problem-definition.schema.json` + `trust_loop.validate_problem_definition`）：新增 `checkApplicability`（检查注册表）、`preregistration{errorNorm, epsilonSpec, seedRuns, seedFactors, worstSeedFactor, dispersionLimit, qoiBand?}`、`evaluationSets.phys?`、`evaluationSets.minSeparation?`。**specHash = 方法身份** = 除 specHash、revision 与 claim 集状态（evaluationSets.claim / claimSetStatus / claimSetOpenedAtRevision / claimSetHistory）之外全部字段的规范化哈希：打开 claim 集不改变 specHash（否则同 specHash 的 C2 run 全部作废，C3 永远无法达成），train / dev 集、阈值、seed 协议、适用性、参考解等级都在哈希内。FROZEN 后任何在哈希内的字段变更即哈希失配，旧哈希的全部下游 artifact 标记 stale。
- 第九章 训练数据与验证数据隔离：数据分三份——**D_train** 训练用（含内部配点、边界点、初值点，全部是训练可见样本）；**D_dev** 诊断、调参、失败分析、模型与架构选择、早停、扰动实验都只准看它；**D_claim** 预注册后密封（SEALED），只在本版本的最终独立验证时打开（OPENED，记录版本号）。**第 3 稿：互斥是样本级的，哈希不同不是证据。** 每个评估集是一份样本清单（`evaluation-set.schema.json`）：样本身份 = 规范化哈希({inputs: 全部网络输入坐标（含参数化输入 μ）float64 精确值, quantity: 观测量或 null})，−0.0 折入 0.0，NaN / Inf 拒绝；`trust_loop.validate_problem_definition(evaluation_sets=…)` 复算清单哈希 = 规格登记的 artifact 哈希，并要求 训练可见样本 ∩ (D_dev ∪ D_claim ∪ D_phys) = ∅、D_dev ∩ D_claim = ∅；"坐标几乎相同"不是身份问题，而由预注册的 `minSeparation`（进入 specHash）以欧氏距离机械判定。**claim 集状态由账本推导，不由文档声明**：`ClaimSetEvent` 账本（`claim-set-event.schema.json`、`claim_set_ledger.py`）是哈希链，eventId = 除 eventId 外全部字段（含 prevEventId）的规范化哈希；不变量 L1–L7：链完整、时间单调、SEALED 先于 OPENED 且 specHash 一致、OPENED 必记 codeHash、同一 claim 集**终身只 OPENED 一次**（跨版本、跨问题）、同一 (problemId, revision) 只 OPENED 一次、OPENED 后永不再 SEALED。文档的 claimSetStatus / claimSetOpenedAtRevision / claimSetHistory 必须等于账本推导值。C_external 只有在 D_claim 上评估才能 PASS，判定必须写明 claimSetSha256 且等于规格登记的 claim 集；在 D_dev 上最多 PARTIAL。
- 第十章 Training Gate：多 seed 协议——1D 案例 N ≥ 10；2D 过渡期允许 N = 5 但 C_train 封顶 PARTIAL；N < 5 视为协议未执行（BLOCKED）；seed 拆为初始化 / 采样 / batch 顺序三因子；报告中位数、IQR、**最差 seed**，最好 seed 永不进入判定。达标次数 k：**k/N < 0.8 → FAIL；0.8 ≤ k/N < 0.9 → PARTIAL；k/N ≥ 0.9 → PASS**；最差 seed > 3ε_spec → 封顶 PARTIAL；中位数 > ε_spec → FAIL；分项 loss 下降而误差不降判优化假象 FAIL。**第 3 稿：离散度规则写成 `IQR > dispersionLimit × median`（乘法比较，全程无除法）**：median = 0 且 IQR = 0 不封顶，median = 0 且 IQR > 0 封顶 PARTIAL，近零中位数不需要机器容差规则，也不引入预注册的分母下限；NaN / Inf 的 run 是发散 run，计入 N、不计入 k、使最差 seed 发散；负误差是调用方错误，拒绝（`trust_vector.seed_statistics`）。
- 第十三章 ValidationReport：Claim Gate 的人读输出固定为 Result / Evidence / Uncertainty / Known failure modes / Allowed claims / Blocked claims / Provenance / Scope 八段；可信度向量六维逐维展示；每条检查按 CheckResult 展示，NOT_APPLICABLE（不承担）、NOT_CHECKED（没查）、BLOCKED（不能查）、PARTIAL（查了不充分）四者措辞必须区分；Known failure modes 必须写出 症状 → 根因 → 区分实验（含被排除的候选） → 回到的 Gate；报告必须披露 C_external 用的是 dev 还是 claim 集、claim 集哈希与状态（SEALED / OPENED@revision）、C3 的 run 数 / seed 集数 / 环境数；禁止单一百分比、"基本通过"、"总体可信"、"平均等级"、"待验证"等措辞。报告是机器判定的只读渲染，冲突以机器记录为准。
- 第三十六章 Claim Levels：弱链演算——六维向量 C = (C_math, C_impl, C_train, C_physics, C_external, C_repro)，每维取 TrustStatus；C0 需 math、impl 全 PASS，C1 再加 train，C2 与 C3 需六维全 PASS 且参考解证据等级 ≠ D；**参考解证据等级取自冻结规格的 primary source，决策文档不得重新标注**；**C3 另需 ≥ 5 个 independently qualified 的 SUPPORTED @ C2 run：同一 specHash、同一 codeHash（这是"同一个方法"的定义），seed 集两两不同，执行环境至少 2 个不同**；复制的 run 不计数。**第 3 稿：seedSetId = 排序去重后 seed 值的哈希，environmentId = 环境指纹强字段的哈希，codeHash = 排序后代码清单的哈希，三者都由校验器复算，手填即拒**；ClaimGateDecision 1.2 必须携带 revision、claimSetSha256、ledgerHead，与规格、向量、账本逐项绑定：external 在 claim 集上判定过 ⇒ 账本有本版本的 OPENED 事件，且决策的 codeHash = OPENED 事件记录的 codeHash（打开 claim 集之后改代码而不升版本 = 拒绝）。组合算子只有取最弱（meet），TrustStatus 无算术结构，平均是类型错误；最弱环节报告序 FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS。
- Gate 5：拆为 G5a 物理一致性 MUST 组与 G5b 独立数值验证；两者都在 VALIDATION 内执行，G5 PASS ⇔ G5a ∧ G5b PASS；C_physics ↔ G5a，C_external ↔ G5b；G2 未 PASS 时 C_external 记 BLOCKED。G5a 的每项检查按问题类型在规格里登记 Applicability。
- 第六章 复现性（对应 G6）与 C3 的独立环境**共用一个定义**（第 3 稿）：`EnvironmentFingerprint` 的强字段 = {machineId, osFamily, acceleratorClass, frameworkVersion(major.minor), blasBackend, dependencyLockHash, installationId}，弱字段 = {osVersion, pythonVersion(patch), acceleratorDriver}；**两个环境独立 ⇔ 至少一个强字段不同 ⇔ environmentId 不同**；仅弱字段不同是同一环境。裁定的案例：同机不同独立安装（installationId 不同）→ 独立（最弱的可接受形式）；同机同镜像两个容器 → 同一环境；不同机器同 lockfile → 独立；集群两节点 → machineId 不同即独立；不同 OS / 加速器 → 独立。C_repro PASS = 同规格同代码、独立环境、不同 seed 集的复现落入预注册容差（`reproduction_status`）；同环境或同 seed 集的"复现"是协议未执行 → BLOCKED；落在容差外 → FAIL。独立性的目的是排除单一安装 / 单一执行环境的偶然性，不是追求可移植性。
- 第二十七 / 二十八章 Run 记录：新增 `RunRecord` 契约（`run-record.schema.json`）：runId、problemId、revision、specHash、codeHash + codeManifest、environment + environmentId、seeds + seedSetId、evaluatedOn、时间与执行者；三个派生哈希由校验器复算。ClaimGateDecision 的 qualifiedC2Runs 携带同样的材料字段，可选地与 RunRecord 注册表逐项核对。
- 新增 revision 规则（第 3 稿，对抗审计项 2）："新 revision"由哈希机械定义：specHash 或 codeHash 任一改变都必须 revision + 1；架构、优化器、采样、loss 权重、依赖版本在 codeHash（代码清单含配置与依赖锁文件）内，PDE、BC、参考解、阈值、seed 协议、适用性、D_train / D_dev 在 specHash 内；"改了代码但语义相同"不可机器判定，因此按字节判定——codeHash 变即新版本。纯文档 / 报告改动不在任一哈希内，不需要升版。打开过的 claim 集在新版本禁用（账本 L4）；burnt 的集可以在新版本重新登记为 D_dev 或并入 D_train（那会改变 specHash），永远不能再任 claim 集。
- 新增 Red Team 条款：扰动实验分三层，Tier-0（只评估）在任何 Claim 之前必跑，Tier-1（单次重训）在 C2 之前必跑，Tier-2（多次重训）在 C3 之前必跑；扰动只能降级或维持，且只降级矩阵指定的那一维（P12 越线 → C_physics）；未跑的层对应维度记 NOT_CHECKED；跑了扰动的维度必须记 worstCase；扰动实验与区分实验只准看 D_dev（DiagnosisRecord.discriminatingExperiment.evaluationSet 固定为 dev）。
- 新增 EXPLORATORY 第二来源：除既有的 evidenceLevel = D 推导标记外，研究者可将一次 run 登记为 EXPLORATORY（假设生成实验）；两种来源都把 Claim 封顶在 C1，产物不进入 ACCEPTED；晋升必须在冻结规格下重新走完整闭环。

## scientificJustification

- 可信度不是一维量：五个 PASS 加一个 FAIL 不是 83% 可信，而是"该 FAIL 所在的证据链不成立"。弱链原则把这一点变成可判定的规则（取最弱），并让报告指出短板所在维度。
- 症状到原因不是一一映射：PDE residual 异常可能来自方程、AD、缩放、容量或优化；再入角附近的局部误差可能来自边界实现、几何离散、角点奇异性、容量、采样、loss 权重或参考解自身的局部失真。若看到症状就固定回某道 Gate，诊断系统本身会产生错误路由。因此路由必须由区分实验确定的根因决定，症状只限定候选根因的范围；而"区分"意味着其余候选被排除——只挑一个合意的根因回到最便宜的 Gate，是第 2 稿留下的可钻路径。无法区分时停线交人。
- NOT_APPLICABLE 与 NOT_CHECKED 语义不同：前者是"不承担该检查义务"，后者是"应查未查"。把前者塞进 TrustStatus 会让"没有检查义务"与"没有查"混在一起。第 2 稿把"全部 NOT_APPLICABLE"折算成 NOT_CHECKED，复审指出这是语义回流；第 3 稿的回答是：这不是一种状态，而是非法登记——六个维度各自是一道 MUST Gate 的对象，一道执行了的 Gate 至少产生一项适用检查；若某类问题真的对某维度一项检查都不承担，缺的是规格的检查注册表，应立新修正案补检查，而不是给 run 一个整维豁免。整维豁免（无论放在 DimensionResult 还是 ClaimPrerequisite）恰恰是 Agent 最想要的开关。
- 独立评估集会被自适应地污染：train / dev / claim 三分与"打开即失盲、换版本必须换集"是经典的 holdout 纪律（Dwork 等 2015 的可重用 holdout 问题）。但三分只有在样本层面互斥时才成立：H(A) ≠ H(B) 不蕴含 A ∩ B = ∅。样本身份用精确 float64，是因为身份必须是判定性的；"几乎相同"是分布重叠问题，用预注册的最小间距判定，两者不混。
- 状态字段不能自证：claimSetStatus 若是普通可写字段，SEALED → OPENED → SEALED 在文档上不可见。账本把每个事件承诺到它的全部历史（哈希链）；JSON 文件不是密码学意义上的不可变存储，本修正案给的保证是**可检测性**：删除、重排、改写任一事件都使后续 eventId 失配，而 ClaimGateDecision 必须引用账本头，篡改账本就必须同时伪造决策——决策正是人工终审阅读的对象。
- seed 阈值：十次有两次直接炸掉不应得到完整 PASS。0.8 作为 FAIL 线、0.9 作为 PASS 线，把"偶然性不能被平均掉"落到数字上；最差 seed 与 IQR 仍能把维度压在 PARTIAL。离散度写成乘法比较是因为除法在中位数为零时没有定义，而分母下限是一个没有物理意义的预注册数字，会在"误差全部极小"的情形下把噪声比放大成判定。
- C3 的独立性：五个 run 若共享同一机器、同一环境、同一 seed 集，信息增益很有限，Agent 也可以合法地"复制五次"。要求 seed 集互不相同、至少两个执行环境，才是对同一方法的鲁棒性证据；而 spec 与代码相同不是弱点，是"同一方法"的定义。独立环境如果在 C3 与 G6 各有一套定义，两者必然漂移；第 3 稿只保留一个函数，两处调用它。身份必须从材料派生（seed 值、强字段、代码清单），否则 seedSetId / environmentId 只是可以随意填写的字符串。
- 多 seed 与最差 seed 口径：seed 方差足以翻转结论（Henderson 等 2018；Picard 2021；Bouthillier 等 2021），"跑三次取最好"是有偏统计量。
- 本修正案不是为了让任何一次已有实验通过：当前没有任何 Poisson 1D run 处于 VALIDATION 之后的状态，PRELOCK_VALIDATION 的结论不受影响。

## impactOnExistingRuns

- 已有 Run：只有 Poisson 1D v1.0 的 PRELOCK 草案与组件诊断（42 项 exact-byte 复核、PRELOCK PASS），没有 ACCEPTED 的 run，没有 C2 及以上的结论；无需重新审计、无旧结论降级。没有任何 1.1 版本的 ProblemDefinition / TrustVector / ClaimGateDecision 文档存在于仓库中，schema 升到 1.2 不使任何真实文档失效；1.1 文档被校验器拒绝是有意的（旧契约不得成为绕过新规则的通道）。
- 已有代码：`pinn/governance/state_machine.py` 的四个 Gate 状态与前提矩阵函数不变；`trust_vector.py`（TrustStatus、Applicability、CheckResult、INV-A1、seed_statistics、EnvironmentFingerprint / environment_id / independent_environments、seed_set_id、RunQualification.from_record、c3_run_support、reproduction_status、弱链演算）、`trust_loop.py`（七类文档的交叉校验）、新增 `evaluation_sets.py`（样本身份与互斥）、`claim_set_ledger.py`（账本）、schema 1.2 三份 + 新契约四份（evaluation-set、claim-set-event、run-record、diagnosis-record）与状态机扩展（discriminating_experiment_errors）。既有 839 项基线测试全部保留；第 1 稿 91 项、第 2 稿 31 项的 1.1 测试夹具改为 1.2 形态（改写，未删除）；第 3 稿新增 70 项（含对抗闭合审计 23 项），pinn 子集 447 项。
- 已有文档：宪法正文在本修正案 ACCEPTED 之前不改；`docs/pinn-trust-loop/inbox/` 八份交付物原样保留，合并裁决见 `R1_MERGE_NOTES.md`、`R2_MERGE_NOTES.md`；协议汇编 `governance/PINN_TRUST_PROTOCOLS_R1.md` 与报告模板同步到第 3 稿。

## consequence

**被禁止**：把可信度写成单一百分比或平均值；PARTIAL、NOT_CHECKED 或 NOT_APPLICABLE 冒充 PASS；把 NOT_APPLICABLE 写进任何 status 字段；登记一个全部 NOT_APPLICABLE 的检查清单，或在 SPEC_LOCKED 之后改动任何检查的适用性；已执行的维度不展示检查、漏列或多列注册表之外的检查；把维度 status 写得高于其检查的 meet；只凭症状决定重入 Gate，或不排除其余可接受根因就命名根因；带失败 Gate 就地重训而不走 FAILURE_RECORDED → DIAGNOSED → REVISED；用 D_claim 做诊断、调参、选模型、早停、扰动或区分实验；把与训练可见样本有交集的集合登记为 dev / claim / phys；打开过的 claim 集在任何版本再次密封或再任 claim 集；同一版本二次打开；打开 claim 集之后改代码而不升版本；在 D_dev 上宣称 C_external PASS；只报最好 seed；训练点、边界点、评估集有交集；把 loss 当精度指标；用 IQR/median 的除法实现离散度判定；用同一 seed 值集（改名亦同）、同一环境（改 hostname、patch 版本亦同）的复制 run 凑 C3 或 G6；手填 seedSetId / environmentId / codeHash；在决策里重新标注参考解证据等级；EXPLORATORY 产物进入 ACCEPTED 或支持 C2；同一规格第 4 轮诊断继续自动循环；用空升版重置诊断轮次。

**被允许**：在 ClaimGateDecision 中给出比演算更严（不更松）的允许等级；把维度 status 判得低于检查的 meet，只要在 notes 说明；2D 昂贵案例以 N = 5 起步但 C_train 封顶 PARTIAL；研究者登记探索性实验并在 C0/C1 级表述其观察；把某项物理检查在规格里登记为 NOT_APPLICABLE，只要写明理由、该维度仍有其它 APPLICABLE 检查、并接受它不参与 meet；burnt 的 claim 集在新版本降级为 D_dev 或并入 D_train；同一台机器上的独立安装作为第二个执行环境（最弱的可接受形式）；纯文档改动不升版本。

**生效前提**：status 改为 ACCEPTED 并填 effectiveDate 之后，宪法正文按 affectedArticles 更新为 1.1；在此之前本修正案与配套代码只作为草案与测试存在，不改变任何 Gate 的判定。

## reviewLog

| 稿 | 日期 | 评审 | 结论 |
|---|---|---|---|
| 第 1 稿 | 2026-09-14 | 用户 | PROPOSED / CHANGES REQUIRED，五项 |
| 第 2 稿 | 2026-09-14 | 队长修订 | 待用户复审 |
| 第 2 稿 | 2026-09-15 | 用户 | PROPOSED / MINOR CHANGES REQUIRED，五项 + 要求对抗性闭合审计 |
| 第 3 稿 | 2026-09-15 | 队长修订 | 待用户终审 |
| 第 3 稿 | 2026-09-15 | 用户终审 | **ACCEPTED**（"通过"）；status 与 effectiveDate 已填。宪法正文按 affectedArticles 更新为 1.1（用户选方案一，2026-09-15）：正文各章加【A-0001】条款与第六十四～六十六章；`locking.py` / `prelock.py` 的版本引脚放宽为 {1.0, 1.1} 且草案绑定的版本必须等于宪法元数据声明的版本；Poisson 1D v1.0 三份草案重绑定到 1.1（constitutionSha256 943484850d64…）；新增证据文件 `PINN_V1.3_PRELOCK_DRY_RUN_A0001.json`（2026-09-05 的旧文件保留）；全套 1033 passed / 2 skipped |

**DeepSeek R2 补交后的说明（2026-09-15，终审同日）**：`PINN_TRUST_R2_MATH_CORE.md` 建议可接受矩阵增加三格（sBcResidual → 容量、sPinnCfd → 容量、sLocalizedError → 规格）。本修正案已由用户按第 3 稿文本终审，矩阵不在终审后改动；三格作为 A-0002 候选记入 `R2_MERGE_NOTES.md` §7。DeepSeek 的诊断实验库 P22–P32、seed 阈值统计论证、泄漏不变量与 Applicability 表进入协议汇编 §3 / §4 / §6 / §10（阈值与实验是预注册起点，不改变本修正案条款）。

第 2 稿对第 1 稿五项的处理（保留）：

| # | 评审意见 | 处理 | 落点 |
|---|---|---|---|
| 1 | 症状直接映射 Gate 与论证矛盾 | 拆为 FailureSignature → RootCauseClass → Gate；可接受矩阵封闭；区分实验必填；rUndetermined 停线 | 第三章；`state_machine.py` |
| 2 | NOT_APPLICABLE 不在类型系统 | 独立 Applicability 类型 + CheckResult；不进入 meet；维度状态 = APPLICABLE 检查的 meet | 第四章；`trust_vector.py` |
| 3 | 独立评估集未防自适应泄漏 | D_train / D_dev / D_claim；claimSetStatus 与 claimSetHistory；打开即失盲、换版本必须换集 | 第九章 |
| 4 | seed 阈值 0.8 过松 | 0.8 FAIL 线、0.9 PASS 线、中间 PARTIAL；最差 seed 与 IQR 封顶 PARTIAL；N < 5 BLOCKED | 第十章 |
| 5 | C3 五个 run 未定义独立性 | independently qualified：同 specHash、同代码哈希、seed 集互异、≥ 2 个环境；驳回一半：同规格同代码是"同一方法"的定义 | 第三十六章 |

第 3 稿对第 2 稿复审五项的裁决：

| # | 复审意见 | 裁决 | 处理 | 落点 |
|---|---|---|---|---|
| 1 | 全 NOT_APPLICABLE 的维度折算成 NOT_CHECKED 是语义回流 | ACCEPT_WITH_MODIFICATION：冲突成立；但 DimensionResult.applicability（方案 1）与 ClaimPrerequisite 豁免（方案 2）都被驳回 | INV-A1：非空检查清单必须含 APPLICABLE 检查，否则 `NoApplicableCheck`；适用性登记进规格并进 specHash；向量检查与注册表逐项一致 | 第四章、第五章；`dimension_status_from_checks`、`checkApplicability`、`validate_trust_vector` |
| 2 | 哈希不同不证明集合互斥 | ACCEPT：第 2 稿确实只比较了三个哈希 | 样本清单契约、样本身份、成对互斥、预注册最小间距、边界点属训练可见样本、D_phys 也不得与训练点重合 | 第九章；`evaluation_sets.py`、`validate_problem_definition(evaluation_sets=)` |
| 3 | SEALED → OPENED 必须不可逆 | ACCEPT_WITH_MODIFICATION：方案 A（append-only 事件）与方案 B（状态由历史推导）同时采纳；驳回"必须做到真正不可变存储"，改为可检测性保证 | 哈希链账本 L1–L7；文档状态必须等于推导值；决策引用账本头；specHash 排除 claim 集状态 | 第九章、第三十六章；`claim_set_ledger.py` |
| 4 | C3 与 G6 的独立环境必须统一 | ACCEPT_WITH_MODIFICATION：统一为一个函数；驳回"所有字段都必须不同"与"字段清单越长越好" | 强 / 弱字段、environmentId = 强字段哈希、`independent_environments`、`reproduction_status`；五个案例逐一裁定 | 第六章、第三十六章；`trust_vector.py` |
| 5 | IQR / median 的零点行为 | ACCEPT_WITH_MODIFICATION：方案 A 的语义、但不产生 inf；驳回方案 B（分母下限） | `seed_statistics` 全程无除法；NaN / Inf 为发散 run；负值拒绝 | 第十章；`trust_vector.py` |

第 3 稿对抗性闭合审计（"形式合法、科学作弊"的路径）：

| 项 | 发现 | 级别 | 封堵 |
|---|---|---|---|
| 1 根因挑选 | 第 2 稿的 discriminatingExperiment 是自由文本，可挑一个回到最便宜 Gate 的根因 | BLOCKING（已封） | excludes 必须覆盖症状的全部其它可接受根因；DiagnosisRecord 契约 |
| 2 revision 规避 | "新 revision"无机械定义；打开 claim 集后改代码不升版即可继续 | BLOCKING（已封） | OPENED 事件记 codeHash，决策 codeHash 必须相等；revision 由 specHash / codeHash 变化机械定义 |
| 3 specHash 覆盖 | 阈值、seed 协议、适用性不在规格里，因而不在哈希内；打开 claim 集反而改变哈希 | BLOCKING（已封） | preregistration、checkApplicability 入规格；specHash 排除 revision 与 claim 集状态 |
| 4 evidenceLevel 重标 | 决策的 referenceEvidenceLevel 与规格无绑定 | BLOCKING（已封） | 必须等于冻结规格 primary source 的等级 |
| 5 C3 计数 | seedSetId / environmentId 是自报字符串 | BLOCKING（已封） | 从 seed 值 / 强字段派生并复算；可选 RunRecord 注册表核对 |
| 6 Red Team 泄漏 | 扰动只准看 dev 只是一句话 | NON-BLOCKING（已封可封部分） | 区分实验 evaluationSet 固定 dev；claim 集打开后改代码需升版（封住基于 claim 结果的调参回流）；"看了 claim 结果后只改扰动选择"不可由文档校验器判定，靠账本 + 升版纪律 |
| 7 Gate 重置 | 已由 `reenter` 的 INV4 覆盖；补 BLOCKED 残留用例 | NONE | 测试 `test_reentry_leaves_no_stale_downstream_pass` |
| 8 人工向上覆盖 | 无检查的维度可直接写 PASS；改适用性可间接升级 | BLOCKING（已封） | 已执行维度必须展示检查；status ≤ meet；适用性冻结在规格里 |

驳回记录（第 3 稿）：见 `docs/pinn-trust-loop/R2_MERGE_NOTES.md` §3（复审建议中被驳回的部分）与 §4（队员建议中被驳回的部分：GLM 的枚举改名、ABANDONED 新状态、actor 污染集、检查级通过率分档泛化、ID 模式改写；豆包的 P12 双维降级）。
