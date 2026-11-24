# Poisson 1D 正式校准实验 · 预注册协议（2026-09-15，宪法 1.2）

本文件在任何正式 run 之前写定并提交（codeHash 含它引用的两份配置）。实验由 `pinn/experiments/runner.py`（R3 最小 runner）执行；所有阈值、架构、优化器、采样、seed 协议在 D_claim 密封前冻结，之后不得为结果而改。

## 0. 问题（不改 PDE）

-u''(x) = π² sin(πx)，x ∈ (0,1)，u(0) = u(1) = 0；解析解 u*(x) = sin(πx)（Level A，`pinn/reference/analytic_poisson.py`，独立代码路径）。FDM 二阶（`scientific_reference/poisson_fdm.py`，N 序列 32…2048）只作 Gate 2b 基线子系统核对，不进入任何 AC。规格与阈值来源：`governance/POISSON_1D_V1.0_spec.draft.json` / `_protocol.draft.json`（已重绑定宪法 1.2）。

## 1. 两个实验共享的冻结项（`experiments/poisson1d/configs/exp1_baseline.json`）

| 项 | 值 | 来源 |
|---|---|---|
| 架构 | MLP 1 → 32 → 32 → 32 → 1，tanh，torch 默认初始化 | 仓库没有冻结的基线架构，按授权指令取"简单、保守"的 3×32 tanh |
| 优化器 | Adam，lr 1e-3 指数衰减到 1e-5，6000 步，mini-batch 128，无早停 | D_dev 上的 pilot（一次 3 seed 试跑，见操作日志 §5.22）选定，在密封 D_claim 前冻结 |
| loss | mean(−u'' − f)² + 10 · mean(u(0)², u(1)²)，分项记录 | 第十一章：分项 loss |
| 训练可见样本 D_train | 1024 个 (0,1) 均匀随机点（numpy default_rng(20260915)）∪ {0, 1}；每个 run 由采样 seed 抽 256 个池点做配点 | 9.1 |
| D_dev | 1000 个均匀随机点（default_rng(20260916)） | 9.1 |
| D_phys | Gauss–Legendre 256 阶节点（公开、确定性） | 协议 §3 |
| D_claim | 协议冻结网格 GL512 ∪ CGL2000 去掉端点 {0,1}（端点是规格已知的边界坐标，按协议 L1 boundaryIdentityExempt 作为边界值评估，不作 claim 样本） | 协议 leakageProtocol L1 |
| 互斥 | 样本级身份（canonical_sha256 of float64 坐标），train ∩ (dev ∪ claim ∪ phys) = ∅，dev ∩ claim = ∅，minSeparation 1e-9 | `evaluation_sets.py` |
| seed 协议 | N = 10 三元组：init = 20260900 + i，sample = 20261000 + i，batch = 20261100 + i；先写 seed_ledger 再启动 | 10.1 |
| ε_spec | 1e-3（= AC-1，D_dev 上相对 L2 对照解析解）；worstSeedFactor 3；dispersionLimit 1 | 10.1 |
| k/N 判定 | < 0.8 FAIL；0.8–0.9 PARTIAL；≥ 0.9 PASS；median > ε FAIL；worst > 3ε 或 IQR > median 封顶 PARTIAL；NaN 计入 N 不计入 k | `seed_statistics` |
| G5b（C_external） | 每个 seed 模型都在 OPENED 的 D_claim 上算 AC-1..AC-8（可信校验器 `pinn.validation.poisson.evaluate_samples`，冻结 GL512/CGL2000）；维度状态 = 各 seed 判定的 meet（最差 seed）；AC-8 SHOULD 未达 → PARTIAL 不是 FAIL | 规格 AC 表 |
| G5a（C_physics） | PH1–PH7 在 D_phys 上逐 seed，取 meet；PH10、自由能 NOT_APPLICABLE（理由见注册表）；阈值 PH1 1e-2、PH2 1e-2、PH3 1e-3、PH4 5e-3、PH5 1e-3、PH6 5e-3、PH7 λ_min > 0 且 ∫u'² > 1e-14 | 协议 §3 的 1e-8/1e-10 是解析夹具默认值，"正式值在 SPEC_LOCKED 前冻结"；此处按 AC 量级冻结，来源写入 config.thresholdSources |
| G6（C_repro） | 本机没有第二个装有训练框架的独立安装（唯一 torch 解释器是 mamba 前缀），同环境复现只证明确定性 → 协议未执行 → BLOCKED（不是 PASS，也不是 FAIL） | 第五十四章【A-0001】 |
| 执行环境 | mamba Python 3.12.9，torch 2.12.1（CPU float64，deterministic algorithms，1 线程），numpy 2.4.5；`.venv` 无 torch/numpy，只跑治理测试 | 28.1 |

## 2. 实验 1：Formal Calibration（happy path）

流程：PRELOCK → 建四个集并证明互斥 → ProblemDefinition FROZEN（specHash）→ 账本 SEALED → G1 → G2 → G3 → seed 账簿 → 10 个 run → RunRecord → G4（D_dev）→ VALIDATION：G5a（D_phys）→ 账本 OPENED（记 codeHash）→ G5b（D_claim）→ G6 → TrustVector → ClaimGateDecision → Trust Report + 图。成功标准即授权指令 1.10 的八条；不要求达到 C3；C_repro BLOCKED 已知使 C2/C3 不可达，最高可能 C1。

## 3. 实验 2：Controlled Sampling Deficiency（failure-recovery path）

- 干预（事前登记）：方案 A，`sampling.collocationCount` 256 → 8（`exp2_bad_sampling.json`），其余一切与实验 1 相同；D_dev、D_claim、PDE、BC、参考解、架构均不改。problemId 用 `pdef-poisson1d-cal-v1-exp2`（与实验 1 同一规格内容；claim 样本相同、artifactId 不同因此哈希不同——见第 5 节披露）。
- 症状：不预设。FAILURE_RECORDED 后按 `signatureCriteria` 在 D_dev / D_phys 上判定 observedSignatures（sPinnCfd：median 相对 L2 > ε_spec；sPdeResidual：median 归一化 holdout 残差 RMS > 1e-2；sBcResidual：median max|u(0)|,|u(1)| > 1e-4；sLocalizedError：10 段 bin RMS 最大/中位 > 3；sConservation：median PH1 > 1e-2；sSeedSensitive：10.1 的离散度 / 最差 seed / 发散规则）。主症状选择规则：sPinnCfd 若触发，否则 sLocalizedError，否则首个触发者；记录同时列出全部 observedSignatures 并解释全部（explainedSignatures = observedSignatures，排除义务取候选并集）。
- 区分实验：受控采样干预 S1 < S2 < S3 = 4 / 8 / 16 配点，每档 5 seed（seed 与正式 run 不同），其余控制项全部固定，只看 D_dev；命名 rSamplingDeficiency 的前提是逐档中位误差严格下降且每个观察症状的其它候选都有排除记录（引用 G2a/G2b/G3 与干预的实测数字）；否则 rUndetermined 并 STOP_THE_LINE。
- 修订：只把 collocationCount 改回 256（`run_revise` 机械校验差异只在该字段）；重入按根因路由到 Gate 4（`reenter`，train 及下游重置 NOT_CHECKED，math/impl 保留），再跑训练 → 验证 → 决策。
- 成功定义按授权指令 2.8 的 A/B/C/D 四种情况。

## 4. 证据

每个 attempt 目录（`experiments/poisson1d/runs/<attemptId>/`）含：identity（codeHash、清单、环境指纹、git HEAD、脏文件）、prelock、sets/ 四份清单 + isolation、problem_definition、claim_set_ledger 引用（账本文件在 `experiments/poisson1d/ledger/`）、gate1–gate6、seed_ledger、runs/（权重、loss 分项历史、dev 误差轨迹）、run_record、training_report、trust_vector、claim_gate_decision、claim_statements、TRUST_REPORT.md、plots/、PROVENANCE_MANIFEST、STATE_TRANSITIONS、RUN_SUMMARY；实验 2 另有 failure_record、dev_diagnostics、intervention_plan、intervention、diagnosis_record、diagnosis_verdict、revision_record。

## 5. 事前披露的已知限制

1. C_repro 无法执行（无独立安装）→ BLOCKED → C2/C3 不可达；这是环境事实，不是治理缺陷。
2. Red Team 扰动矩阵 P1–P21 不在本轮范围；TrustVector 的 perturbationsRun 为空。
3. 实验 2 的 claim 集与实验 1 样本相同、artifactId 不同：账本按哈希判 burnt，机器规则允许；信息上队长已见过实验 1 在这些点上的结果——记为 NON-BLOCKING / AMENDMENT CANDIDATE（claim 集身份应按样本而非 artifactId，或协议预注册多套 claim 网格）。
4. 物理阈值由本协议冻结而非协议汇编默认值，来源与理由已写入 config；若评审认为应更严，须在下一版本规格里预注册，不得回改本轮。
