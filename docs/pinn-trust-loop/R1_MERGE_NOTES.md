# R1 合并说明（队长：Claude）· 2026-09-14

对象：`docs/pinn-trust-loop/inbox/` 下五份 R1 交付物。本文件记录收件核对、各车道摘要、跨车道冲突与队长裁决、与既有宪法 / 代码的衔接计划、以及必须由用户拍板的事项。分歧只记录，不抹平。

## 0. 收件核对（提交 `13dc7ea`，字节原样）

| 文件 | 作者 | SHA-256（前 12 位） | 行数 | 范围声明 |
|---|---|---|---|---|
| `PINN_TRUST_R1_MATH_CORE.md` | DeepSeek | `23dd35179a0a` | 257 | 数学一致性条件、物理一致性公式、误差归因、弱链演算；未越界 |
| `PINN_TRUST_R1_SCHEMAS_STATE_MACHINE.md` | GLM | `4b5693507c9f` | 636 | 三份 JSON Schema、状态机 FAIL 分流、28 条测试用例；未越界 |
| `PINN_TRUST_R1_IMPL_TRAINING.md` | Kimi | `3445b3977df9` | 129 | MMS 协议、T1–T10 单元测试、多 seed 协议、11 篇文献；未越界 |
| `PINN_TRUST_R1_REPORT_AND_WORKFLOW.md` | 豆包 | `4f7523d51e78` | 274 | 六段式模板、两个示例、研究者工作流、术语表；未越界，未画界面 |
| `PINN_TRUST_R1_RED_TEAM.md` | Claude（代 Grok） | `9ca4e288407d` | — | 21 条扰动、三层制、15 条漏洞、对 8 条设计的反驳、20 篇文献 |

五份都按词表写作，都把不确定项写进了"待队长决定"，没有一份猜测仓库路径或输出补丁。

## 1. 各车道一句话摘要

- **DeepSeek**：把 G1 的六类一致性写成机器可判条件；给出 Poisson 1D 与 NS / Oldroyd-B 的守恒、能量、动量、正定、对称、单调、最大值原理、自由能、SPD 的离散公式与容差；误差六项的隔离实验与"症状 → 来源 → 区分实验 → 判定"表；把五态定义为链并证明 claim 等级 = 必需维度逐个 PASS（取最弱），平均是类型错误。
- **GLM**：ProblemDefinition / TrustVector / ClaimGateDecision 三份 draft 2020-12 schema，冻结即哈希（JCS）；提出修正案 A1（G5 拆 G5a/G5b，新增 PHYSICS_CHECKED 状态）；六条诊断分支的路由表、五条不变量、伪代码；T01–T28 测试用例。
- **Kimi**：MMS 五步与 P1/P2/P3、NS1 双 ν 档组合；T1–T10 实现单元测试（float64、阈值明确）；多 seed 协议 N ≥ 10、三因子解耦、中位数 / IQR / 最差 seed、k/N ≥ 0.8；C_train 评级规则。
- **豆包**：六段式模板与硬约束措辞规则；NOT_CHECKED / BLOCKED / PARTIAL 三者的标准措辞；两个填好的示例；研究者"让 PINN 进化"的预注册、冻结 / 可变项、晋升路径、论文方法清单、EXPLORATORY 标签；术语表。
- **Red Team（队长）**：P1–P21 扰动矩阵与降级规则、Tier-0/1/2 执行制；V1–V15 漏洞与对策；对 8 条设计的逐条反驳（不做双重状态机、症状不唯一映射、C_repro 语义、关键证据链需定义、误差不可加、成本分层、输出补 Provenance/Scope、EXPLORATORY 隔离）。

## 2. 跨车道冲突与队长裁决

| # | 议题 | 各方立场 | 裁决 | 状态 |
|---|---|---|---|---|
| C1 | 五态在"最弱环节"排序中的位置 | DeepSeek：FAIL ⊏ BLOCKED ⊏ NOT_CHECKED ⊏ PARTIAL ⊏ PASS；GLM §3.1-6：FAIL < BLOCKED < PARTIAL < NOT_CHECKED < PASS；Red Team：NOT_CHECKED 不高于 PARTIAL | 采纳 DeepSeek 序：**FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS**（没查的证据比查了不充分的更弱）。对 claim gate 无影响（非 PASS 一律阻断）；GLM schema 的 weakestLink 推导序按此修正 | 已裁决 |
| C2 | C_external 绑定哪几道 Gate | DeepSeek、豆包：G2 + G5；GLM：只绑 G5b，参考解证据等级由 `referenceEvidenceLevel` 单独携带 | 采纳 GLM：**C_external ↔ G5b（独立数值验证）**；G2 不单独成维，`referenceEvidenceLevel` 是 ClaimGateDecision 的独立前提；G2 未 PASS 时 C_external 记 BLOCKED | 已裁决 |
| C3 | 物理一致性怎么拆出 G5 | GLM A1：新增 PHYSICS_CHECKED 状态；GLM 备选：不新增状态，作为 VALIDATION 内前置子检查；Red Team 第 1 条：不做双重记账 | 采纳 **GLM 备选**：G5 = G5a（物理一致性 MUST 组）+ G5b（独立数值验证），都在 VALIDATION 内执行，VALIDATION PASS ⇔ G5a ∧ G5b PASS；宪法状态机的状态集合不变；dConservation 分流重入 VALIDATION 并重跑 G5a | 已裁决 |
| C4 | 示例 (b)"Accuracy claim ALLOWED" | 用户原例：ALLOWED；豆包按弱链：5 seed → C_train PARTIAL、corner PARTIAL、repro NOT_CHECKED → C2 应阻断；Kimi：2D 过渡期 N=5 封顶 PARTIAL | 采 **(ii) C1 + 受限一致陈述**（"在该工作点、该 QoI 上与 Level B 参考在阈值内一致"），不开 scoped C2 口子；弱链原则是宪法级，示例不能例外 | 已裁决（用户 2026-09-14 选 (ii)） |
| C5 | seed 数与 C_train 封顶 | Kimi：N ≥ 10（1D），2D 过渡 N = 5 封顶 PARTIAL；Red Team P2：以最差 seed 判定 | 采纳两者；写入修正案 | 已裁决 |
| C6 | 阈值 | 各方给的都是"建议默认值" | 全部作为**预注册起点**：ε_spec = 1e-3（相对 L2）、最差 seed ≤ 3ε_spec、k/N ≥ 0.8、IQR/median ≤ 1、Δq 1% / 5% 两档、DeepSeek §2 各容差；正式值在 SPEC_LOCKED 前冻结进 HASH LOCK | 已裁决（数值待预注册） |
| C7 | Red Team 结果怎么进向量 | Red Team：TrustVector 每维加 `perturbationsRun`、`worstCase`；GLM：以 `supersedesRecordId` 新版本写入 | 两者都要：新版本记录 + 每维扩展字段；schema 下一版补 | 已裁决 |
| C8 | EXPLORATORY | 豆包 §3.5 与 Red Team 第 8 条一致：探索性只允许 C0/C1 | 采纳；作为 run 级 `mode` 枚举进 schema（GLM 下一版），claim 封顶 C1，不进 ACCEPTED | 已裁决 |
| C9 | 诊断循环上限 | Red Team 第 2 条：3 轮后 BLOCKED 升级人工 | 采纳；状态机加计数（GLM 下一版） | 已裁决 |
| C10 | weakestLink 并列 | GLM D4 | 记录全部并列维度，展示按固定序 | 已裁决 |
| C11 | "NOT VALIDATED" 展示词 | 豆包 D2 | 英文展示统一为 "NOT CHECKED"，枚举不变 | 已裁决 |
| C12 | C_repro 定义 | Red Team 第 3 条 / V15；豆包 D3 | **PASS = 同规格、独立环境（不同机器或独立安装）+ 不同 seed 集的复现落入预注册容差**；同机同 seed 只证明确定性，不计 | 已裁决 |
| C13 | 配点互斥（Kimi T10）升宪法级 | Kimi 待决 ③ | 采纳为宪法级禁令 | 已裁决 |
| C14 | specHash 规范化用 JCS（RFC 8785） | GLM A3 | 已核对：既有 `canonical.py` 的唯一规范化是 `json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + LF`，PRELOCK / HASH LOCK 都用它；specHash 沿用该序列化，不引入 JCS | 已裁决 |
| C15 | 报告禁用词表升为自动校验 | 豆包 D6 | 采纳，作为 ClaimGateDecision 生成时的文本校验 | 已裁决 |
| C16 | 完整英文版报告 | 豆包 D4 | R1 不做；标题、句式、术语双语即可 | 已裁决 |

## 3. 与既有宪法 / 代码的衔接计划（R1 → 仓库）

| 产物 | 来源 | 落位 | 备注 |
|---|---|---|---|
| 宪法修正案草案 | C1–C13 裁决 + 各方条款 | `governance/AMENDMENTS/A-20260914-R1-trust-loop.md` | 条款化：可信度向量、弱链演算、G5a/G5b、EXPLORATORY、seed 协议、配点互斥、Red Team 三层制、诊断循环上限 |
| 三份 schema | GLM §1–§3（按 C1/C2/C7/C8 修正） | `pinn/governance/schemas/problem-definition.schema.json`、`trust-vector.schema.json`、`claim-gate-decision.schema.json` | 先核对 `jsonschema_lite.py` 支持哪些 2020-12 关键字（if/then、contains、prefixItems）；不支持的交叉规则放进 PRELOCK |
| 弱链演算 | DeepSeek §4 + Red Team NOT_CHECKED 语义 | `pinn/governance/trust_vector.py`（新） | 纯函数：向量 → allowed / blocked / weakestLink；DeepSeek 4.4 七个例子直接成测试 |
| 状态机扩展 | GLM §4（按 C3/C9 修正） | `pinn/governance/state_machine.py` | 六条 branchId 封闭枚举、INV1–INV5、循环计数 |
| 测试 | GLM T01–T28、DeepSeek 4.4、Kimi 阈值 | `tests/pinn/test_trust_loop_schemas.py`、`test_trust_vector.py`、`test_state_machine_triage.py` | 全部保留现有 839 项，只增不减 |
| 报告模板 | 豆包 §1 | `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` | 双语标题与句式；禁用词表 |
| 协议文档 | Kimi §1–§3、DeepSeek §2、Red Team §1 | `governance/PINN_TRUST_PROTOCOLS_R1.md` | MMS 组合、T1–T10、seed 协议、物理检查公式、P1–P21 |
| 物理检查代码 | DeepSeek §2 | `pinn/validation/`（R2） | Poisson 1D 的通量 / 能量 / 正定 / 对称 / 单调 / 最大值 / SPD 检查可直接实现；NS 部分等 CFD 案例 |

顺序建议：修正案草案 → schema + 弱链演算 + 测试 → 状态机扩展 → 模板与协议文档 → R2 出题。

## 4. 需要用户拍板

1. C4：用户已选 (ii)（2026-09-14）。
2. 用户已选"现在开始实现"（2026-09-14）；实现记录见操作日志。

## 5. 分歧记录（不抹平）

- GLM 的 weakestLink 排序与 DeepSeek 相反（C1），已裁决为 DeepSeek 序；GLM 文件原文保留。
- DeepSeek、豆包写的 "C_external ↔ G2 + G5" 与裁决（C2）不同；原文保留，整合时改口径。
- GLM 修正案 A1 的新状态未采纳（C3），采纳其备选；原文保留。
- 豆包示例 (b) 与弱链原则的冲突（C4）已由用户裁决为 (ii)；豆包原文两说并存，保留不改。
