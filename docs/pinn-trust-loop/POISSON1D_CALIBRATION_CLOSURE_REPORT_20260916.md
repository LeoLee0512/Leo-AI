# Poisson 1D Calibration Closure Report（2026-09-16）

执行负责人：Claude（队长）。宪法 1.2 不变（无 A-0003，无方法修改，无 D_claim 重开，无 G5 重做，无参数调整）。实验 1/2/3 的机器记录保持不变，只追加 POST_AUDIT_ANNOTATION。上一份报告：`POISSON1D_C2_CALIBRATION_REPORT_20260916.md`。

## 1. Executive Result

```text
G6:
PASS

Highest Claim:
C2   (SUPPORTED @ C2, ClaimGateDecision cgd-exp3c-hard-bc-r2-g6)

POISSON 1D CALIBRATION:
CLOSED

PINN SCIENTIFIC-CLAIM MVP:
VALIDATED AT C2

READY FOR USER / EXTERNAL REVIEW BEFORE 2D
```

## 2. BC Diagnosis Post-Audit

```text
Historical verdict:              rSpecDefect   (unchanged; protocol-selected by the preregistered decision tree)
Post-audit causal interpretation: NOT UNIQUELY IDENTIFIED IN POST-AUDIT REVIEW
```

事实（D_dev，10 配对 seed）：软 BC λ_BC = 10：BC median 1.43e-4，7/10 seed 未过 AC-3；λ_BC = 100：8.15e-5，4/10 未过；λ_BC = 1000：1.33e-5，10/10 通过，PDE error 7.83e-3 < 1e-2，solution error 2.63e-4 可接受；硬 BC u = x(1−x)N：BC 恰为 0，同样解决。因此至少两种解释仍有实证支持：A. enforcement / specification choice；B. loss trade-off / optimization-training protocol。正确表述是"原冻结的软 BC 配置（λ_BC = 10）未通过 AC-3"，不是"软 BC 本质上不能满足 AC-3"。历史 verdict 不改为 rOptimizationFailure 或 rUndetermined（那是看完数据后的回溯重分类）。宪法 1.2 没有"根因归因非唯一即使已完成的 revision / 状态转移失效"的条款（第二十三、五十六、五十九章核对），r2 的已验证结果成立。注解：`runs/exp1-calibration-r1/POST_AUDIT_ANNOTATION.md`。

前瞻性准则澄清（`experiments/poisson1d/INTERVENTION_CRITERION_CLARIFICATION_20260916.md`）：未来干预准则围绕整条预注册剂量—响应曲线（R = median E(λ_high)/median E(λ_low)、配对 Q、弱单调、退化限），而不是要求每对相邻档独立满足强阈值；数值常数不用本次数据倒推，留待下一次适用实验前预注册。Experiment 3 历史裁决不变，新准则仅前瞻。

## 3. Environment Qualification（`experiments/poisson1d/environment_b_qualification.json`）

G6 语义审计（宪法 28.1、`trust_vector.independent_environments`、`reproduction_status`、schema、测试）：独立 ⇔ 至少一个强字段不同（machineId / osFamily / acceleratorClass / frameworkVersion / blasBackend / dependencyLockHash / installationId）；**不要求** dependencyLockHash 不同；同机独立安装即合格。代码与宪法一致，无 mismatch，无修复。

| 字段 | Environment A（原 run） | Environment B |
|---|---|---|
| machineId | win-60a9b43e-b66d-4186-8afb-43e9ada3342e | 同 |
| osFamily / OS | windows / Windows-11-10.0.26200 | 同 |
| architecture | AMD64 | 同 |
| acceleratorClass | cpu-only（训练强制 CPU float64） | cpu-only |
| Python | 3.12.9（mamba） | 3.12.9（`python -m venv`，base = mamba python，无 system-site-packages） |
| torch | 2.12.1+cu126 → frameworkVersion torch-2.12 | 2.12.1+cpu → torch-2.12 |
| numerical backend | mkl | mkl（MKL-DNN 3.11.2） |
| driver | — | — |
| dependencyLockHash | 75efe91aa4e1…（用户通用 mamba 环境，无 lockfile，数百个发行版） | 9083b98ea21e…（只装复现包声明的依赖：torch==2.12.1、numpy==2.4.5，`--no-cache-dir`） |
| installationId | prefix-689a1fbe8610a998 | prefix-e67819cbf0282077（新前缀 `C:\Users\user\LeoAI-envB-20260916\venv`，无复制、无克隆） |
| environmentId | e986dbc039e0… | 232ac1d46aea… |
| qualification | — | **independent = True**（强字段不同：dependencyLockHash、installationId） |

说明：优先目标 dependencyLockHash 相等无法达成——环境 A 没有 lockfile 且是通用环境；B 是复现包声明依赖的最小全新安装。独立性由 installationId 承担，dependencyLockHash 差异是构造结果而非刻意升降级依赖。

## 4. Reproduction Configuration

| 项 | 值 |
|---|---|
| specHash | fd5584d7b290…（r2，enforcement hard；同一冻结 ProblemDefinition `problems/pdef-poisson1d-cal-v1-r2.json`） |
| codeHash | 5aaf93a57fdd…（**相同**：复现在 exp3c 原 commit beceef5 的干净分离检出 `C:\Users\user\LeoAI-envB-20260916\repo-frozen` 上运行原 runner；驱动脚本在代码身份清单之外） |
| seedSetId A | 4489fcb39906… |
| seedSetId B | e2c220431081…（复现包规则：原三元组 +10000，先登记再训练） |
| dataset generation | 与原 run 同一规则（pool 1024 / default_rng(20260915)，dev 1000 / default_rng(20260916)，GL256），四集样本级互斥复核通过 |
| method | 3×32 tanh，u = x(1−x)N，Adam 1e-3→1e-5，6000 步，batch 128，256 配点——全部冻结，未改 |
| tolerance（包内冻结） | dev 相对 L2 中位数差 ≤ 1e-4 且 k/N 判定一致；claim 集不重开 |

## 5. Reproduction Results（`runs/repro-envb-frozen-r2/reproduction_report.json`）

| 指标 | A（exp3c-hard-bc-r2） | B（repro-envb-frozen-r2） |
|---|---|---|
| median relative L2（D_dev） | 1.991e-4 | 2.552e-4 |
| difference | — | **5.617e-5 ≤ 1e-4** |
| k/N | 10/10 PASS | 10/10 PASS |
| worst seed | 2.480e-4 | 5.173e-4 |
| IQR | 1.513e-4 | 1.275e-4 |
| divergent | 0 | 0 |
| B 逐 seed | — | 5.17e-4, 1.59e-4, 2.87e-4, 1.20e-4, 2.00e-4, 2.74e-4, 2.58e-4, 4.27e-4, 5.65e-5, 2.52e-4 |

`reproduction_status`（宪法 54）：同 spec ✓、同 code ✓、独立环境 ✓、不同 seed 集 ✓、容差内 ✓ → **C_repro = PASS**。

诚实记录：第一次复现 run（`repro-envb-r2`，当前 commit 的 runner）数字逐位相同，但 codeHash 因本轮 runner / harness 修改而不同，被 `reproduction_status` 正确判 **BLOCKED**（"同一个方法 = 同 specHash 同 codeHash"是宪法明文）；该记录保留并注解。随后按复现包说明在原 commit 检出上重跑才取得合法 PASS。

## 6. G6 Evidence（sha256 见附录）

- `runs/repro-envb-frozen-r2/`：identity.json（codeHash 5aaf93a5…，gitHead beceef5，dirty = no，environment B）、prelock.json、sets/、problem_definition.json（复用 r2 冻结定义）、gate1–gate4、seed_ledger.json、runs/run-00..09.json、run_record.json、training_report.json、reproduction_report.json、trust_vector.json、STATE_TRANSITIONS.json、PROVENANCE_MANIFEST.json。
- `runs/exp3c-hard-bc-r2/`：gate6_reproducibility_executed.json、trust_vector_g6.json、claim_gate_decision_g6.json、attempt_state.json（ACCEPTED）、STATE_TRANSITIONS（REPRODUCIBILITY_CHECK →[G6 PASS] ACCEPTED）。
- `runs/repro-envb-r2/`（BLOCKED 记录）+ POST_AUDIT_ANNOTATION.md；`environment_b_qualification.json`；`repro_package_exp3c_r2/`（冻结包，未改）。

## 7. Final Trust Vector（`trust_vector_g6.json`，supersedes tv-…-tier1v2，校验器通过）

```text
C_math     = PASS
C_impl     = PASS
C_train    = PASS
C_physics  = PASS
C_external = PASS   (claim set GL640-CGL2400, sampleSetHash 3977198983fd…, OPENED@r2 once, BURNT)
C_repro    = PASS   (repro-envb-frozen-r2)
```

## 8. ClaimGateDecision（`claim_gate_decision_g6.json`，`validate_claim_gate_decision` 通过）

```text
SUPPORTED @ C2
allowed: C0, C1, C2      blocked: C3 (no independently qualified C2 runs supplied — C3 needs >= 5 such runs)
runMode FORMAL · referenceEvidenceLevel A · codeHash 5aaf93a5… = OPENED codeHash · ledgerHead c3bf550d945d…
```

Evidence chain：冻结规格 fd5584d7b290（r2，hard BC）→ G1 数学一致性 → G2 解析参考 + FDM 二阶 → G3 T1/T3/T4/T8/T9/T10 → G4 10/10 seed（median 1.99e-4）→ G5a PH1–PH7 → G5b 新盲 claim 集 AC-1..AC-8 全 seed 满足（AC-3 = 0）→ Tier-1 P1/P4/P6/P8/P9/P16 维持（run 1 P8 harness 缺陷保留注解）→ G6 独立环境复现容差内 → 六维 PASS → 弱链演算许可 C2 → ClaimGateDecision 签署 → 状态机 `advance(REPRODUCIBILITY_CHECK, 6, PASS, claim_decision_signed=True)` → **ACCEPTED**。

## 9. Tests

| 项 | 值 |
|---|---|
| previous baseline | 1109 passed / 6 skipped |
| new tests | 3（`test_g6_reproduction.py`：冻结复现 PASS 与新代码复现 BLOCKED；容差外 FAIL、同环境 / 同 seed BLOCKED；最终 G6 向量与 C2 决策重校验） |
| total passed | **1112** |
| failed | 0 |
| skipped | 6 |
| PRELOCK | 7/7 PASS |

## 10. Repository State

`git status` clean；收口提交 32eaa36（证据、代码、测试）+ 本文档定稿提交（见 `git log -1`）；上一轮末提交 62ff5e6。

## 11. Stop

本轮到此停止。不开始 2D、BFS、UCM、新修正案、架构搜索或 UI。等待用户把本报告交给外部评审。

附录 Evidence Manifest（sha256 = 文件字节）：

- `experiments/poisson1d/environment_b_qualification.json` · df1ea41f5119ee18cc11d5bea7d44db8b5639289c8ef2cc4523f6e141c7093d6
- `experiments/poisson1d/INTERVENTION_CRITERION_CLARIFICATION_20260916.md` · f6cfe2df9f9c0e749f584161a745946c1efa10ee31a865f00855148fdd5b38aa
- `experiments/poisson1d/runs/exp1-calibration-r1/POST_AUDIT_ANNOTATION.md` · 632576bed350c30e53b3365a19959d4fcc63c1116d232ec450827d0c39852fc0

### repro-envb-frozen-r2

- `identity.json` · aa9532289102755a83e944c34d07bab571d75d9421227993fbc7c0783dfd16dd · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `gate1_math.json` · c217bdca12790d1276346bf0a49ed4dca6d0b10fe7edb8910137fbdb80a9b4a0 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 9243aee52a388cab7d217f212dcb6a79e667915f6a3310cc7e2a78becb35a983 · SEED_LEDGER
- `runs/run-00.json` · b8f52bff50dd4c2b91a29dcde1041ca2a54ee3e93dbde9d615b7183596568ee2 · RAW_MODEL_PREDICTION
- `runs/run-01.json` · c2289d422c8c68020ef81032f02ae2ceba0fadd6a15ebcc0fbc25a335ab72456 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · b4ba23882fb33ac214a93dd5c9a8dffe07e1acb7c08964402acf6c9f4380f3dd · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 3aaeb573e1dcd882e378146a2c5fd2a46afeecc62f599e720811de707326e2c8 · RAW_MODEL_PREDICTION
- `runs/run-04.json` · be19bfd32a9a22ac785bf460f1731e500685ea41399f2addb43b5464e55a1116 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · d3f107594b04943d07ee382b365f620430e82ba4369c99b5c5cb219a389530bc · RAW_MODEL_PREDICTION
- `runs/run-06.json` · ba61fbe0375bbaed9049f9f07790985a3d2b7f74415e8765ca3254c48cdacd98 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 3c423c04892c0c041fffd1323e28e7cf21db23c63e98a875b571e351d4a34e17 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · d3d91d40cb0dfae8f8c64f47faf094044c96b54fe7a4e1b75a259cb7e1806f30 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · 3539a5ea5be465a956240c7a09ecdf097b311f9dd88e57a0fe6b09ff8f1fb2a1 · RAW_MODEL_PREDICTION
- `run_record.json` · a2017b5b6f33abd1e89e8469b0ccecfee0acf4de52444426ef6d48e0219845a0 · RUN_RECORD
- `gate4_training.json` · 25a24e5a524e500b6c8f4586997ddad875b1385a7c06a663f0cc2bafab39b664 · GATE_RESULT
- `training_report.json` · 440b6d963b0cc747e0a8437392f15be64719ecf42488f1ae96f80c7dc6937ca7 · TRAINING_REPORT
- `attempt_state.json` · d9fdbbfc78c0f238cfe2e8ab6cfbab4ba876426b580e08973537c8893d61846c · STATE
- `trust_vector.json` · e484ca009d24a4d18d059983f8730ad3013791d865d357ae3e0647ba71053066 · TRUST_VECTOR
- `RUN_SUMMARY.json` · 4be910cae17eef23d3345978c5d502aa05b9db3d8031a67ec97c0e2090265aec · SUMMARY
- `reproduction_report.json` · ebac6fd22b8dac8edaacf8e82f2fdaa035e59cc84a51ade76f2ae044a765e2ba · REPRODUCTION_REPORT
- `PROVENANCE_MANIFEST.json` · cc3ea19192d5bb4aaa89966f75ce8959f87ff7ac53661737d7d69613d8095c84 · (index)
- `STATE_TRANSITIONS.json` · 6b0687d998cc602590060f2116376a75699577f241fa483db6bfc46c09967e2d · (index)
- `TRUST_REPORT.md` · 8a5e12662cdc0bcfc7bf551e77f066551375fbb36a78f90440bca6b605910008 · (index)
- `attempt_state.json` · d9fdbbfc78c0f238cfe2e8ab6cfbab4ba876426b580e08973537c8893d61846c · (index)

### repro-envb-r2

- `identity.json` · 39ad6ef72bcd6f73cbf6d405699bb1e078f690ddd788e6e703fa58d2948cf832 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `gate1_math.json` · c217bdca12790d1276346bf0a49ed4dca6d0b10fe7edb8910137fbdb80a9b4a0 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 58c79ab126629ea0764cfa950a008027999ec198bda2ff4c0072d20431cec1be · SEED_LEDGER
- `runs/run-00.json` · 3e63e22a9fed44ced7d6e36a1659ca3872259d09b6fa1170b338aacfab270d6a · RAW_MODEL_PREDICTION
- `runs/run-01.json` · fd6a32197001886fadd7cf8d91db900c3f4967e52a014adc5d118f5bf84c7f1b · RAW_MODEL_PREDICTION
- `runs/run-02.json` · d88cc33178aa05214b5342512b96ea2d2f055af8c956f617a432899569651ed0 · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 0a4292a36293480bfaf5f9ddf9c2967eb20912ca164f086ff48eeda8f47acc6c · RAW_MODEL_PREDICTION
- `runs/run-04.json` · b778bbb114435c30bf0af1ffc09367fe6750b7fce67e5da4712859641acf9c0e · RAW_MODEL_PREDICTION
- `runs/run-05.json` · eb4c4710106dd73b8085fb8f3aa0e8a7ccbfa63a2d83ce86ac3214a4160c599c · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 9640ffc49e5c4588d738435434eec3e2a71ba601a820e435a6cc44e9464a51f7 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 81a8e4e11357c2c5b7f69ceec4340306fbfe0e099455d66eb4a6f4fe5dbe2a64 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · 77fb4b595eca185b0f2263d9b4f4d612736f424b0abc0d0dc1da9d120e20a3c1 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · 2961a841b5bf46cbf6e398ab53eb8c8c7f976743f7475bd50b5217101eccf48d · RAW_MODEL_PREDICTION
- `run_record.json` · e0d071069d9656dc7e13ced139d46bcc64e3e78e7c99acb8afc35f447357992d · RUN_RECORD
- `gate4_training.json` · 25a24e5a524e500b6c8f4586997ddad875b1385a7c06a663f0cc2bafab39b664 · GATE_RESULT
- `training_report.json` · 440b6d963b0cc747e0a8437392f15be64719ecf42488f1ae96f80c7dc6937ca7 · TRAINING_REPORT
- `attempt_state.json` · 66b56a505bef3ba72acba1dc93c318de05dc76efd18208316f0a89939dd9b4b3 · STATE
- `reproduction_report.json` · edccb484b22dc6cfae9c9ecdd91466c274749714efa899c729816c4dcd551037 · REPRODUCTION_REPORT
- `trust_vector.json` · f26d64ca06c9c86b3e7b802a3afbc76efbd81e95d6c53169b0cb13604824893d · TRUST_VECTOR
- `RUN_SUMMARY.json` · 14ce362faa29b3435c8457e8741cebb21e25219fca5662ad0b94aabb98458699 · SUMMARY
- `PROVENANCE_MANIFEST.json` · 8769e1e7f19a2d27e4c362a830ffce4bcb61c0806cd19d1d15c77ef5d9ce7a86 · (index)
- `STATE_TRANSITIONS.json` · 5f7b1031c93ca555ed411d5fcbf27d3b582ddc68d69bc07fae138b3a18628870 · (index)
- `TRUST_REPORT.md` · 31873a42421be0e3474fbec708c905c0209832127a6ae8d10bc8b15ec251623b · (index)
- `POST_AUDIT_ANNOTATION.md` · a6bece2cfbe17c263cc0830455b8d3bcfdf0f28c1b98976a8d080a4e8106d327 · (index)
- `attempt_state.json` · 66b56a505bef3ba72acba1dc93c318de05dc76efd18208316f0a89939dd9b4b3 · (index)

### exp3c-hard-bc-r2

- `identity.json` · e8e6f82398cda57a4b6ec3e85831732c216690280041596acd73eed4e57e2d89 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `gate1_math.json` · a274df4ac8a16bd8a3e5f087a12913f39ae83110c6ae0824c65b4e4bdbb81929 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 1bf27ecd1e3c66aed0eb869b1d76f6937a8fad8ffe614ccc38c64a30baf0dbb2 · SEED_LEDGER
- `runs/run-00.json` · 7aaf49535bf163e0fa53da25a2c422a9990d6c4967a4a85b5154f7315948a7f8 · RAW_MODEL_PREDICTION
- `runs/run-01.json` · ab3e16287e760eabfcb292bfba0b8928ad71cdcf72e6c061f8d70f79739ad1e7 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · 02aff363d8701a322c2954c9fcc6ea80c09d778c851047b9daf1d2cf61af4933 · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 5aa656013b005ec5b458ed89e8675c0d4ad66c34f90eb0e25498d639ac31143f · RAW_MODEL_PREDICTION
- `runs/run-04.json` · e492a7da85cac3acb850e5998ee7bd773d213d074c17ad17614bc3420d5a5cd1 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 871a7ffd6cdabd7e0ebdb4209200d1eb2076e06c5f33275cb547d0400901e60e · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 574f0b8cebe176446c28ecb50d6d17c81f93982dd78ebbcf98521aaf505e7f82 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 9b47d05b6e970e50a752fc7447aa19317dface743a1823429914449aa5e79ca4 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · 074731f769dafd93aba33dc73593406bc94fe7d7e5d2a88206c4621196704845 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · bc52881dc4930c3f120551c774e550507f243e4b98f914db1e42f1eb2be321d9 · RAW_MODEL_PREDICTION
- `gate4_training.json` · fefe9815b14b903a3b16667256be7d697f48460c6e8fd0796f812cc065a4fc3e · GATE_RESULT
- `training_report.json` · 6e57cfdac3e001b9bc913c9096b1f9c0b385c7752bb0f404f686c2f9253c558c · TRAINING_REPORT
- `gate5a_physics.json` · 9255a884c7238d246721e7f57d0908122b5d431d196758bf27982a842de0fd3e · GATE_RESULT
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `gate5b_external.json` · 08512671438191c8be2664af17c360885b420b0294f6667b3c51116230550234 · VALIDATION_METRIC
- `run_record.json` · 131116f213142557917f139d36748357d359d3d90b9049e919882a9e813a4c82 · RUN_RECORD
- `gate6_reproducibility.json` · 7a049cb9a6821b1e5a037f74d2c5e0bf517f03e2f1051fae04115252dca6a3fe · GATE_RESULT
- `trust_vector.json` · 278cc8ce45e56748f3a31613bf02cdcd677af5e9a3e7fc42400dfc38c5b6ab44 · TRUST_VECTOR
- `claim_statements.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision.json` · 87b92178ae2af96c916541b831b49910f56021893eea83eb2dd051859e6be353 · CLAIM_GATE_DECISION
- `tier1_redteam.json` · 13ae340866c400d34b67fe6a40e7f62a1878f1dd7da47f335c95f11ac9dc6779 · RED_TEAM_REPORT
- `trust_vector_tier1.json` · bcf798e06f98a30c8045d9d36660a376049205e9548dca9b2e44e2f0a3603d77 · TRUST_VECTOR
- `claim_statements_tier1.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_tier1.json` · 2b21212a9266b44a2c8d8c70d613b4cd1ab7fad5aaa6cdef5a14fe7332b72799 · CLAIM_GATE_DECISION
- `tier1v2_redteam.json` · add3abc639f67cef91ce195679b01f904146d504a9bee51cf2930f209c9ef9b9 · RED_TEAM_REPORT
- `trust_vector_tier1v2.json` · 17c09b016ca7c9b6b687b1a0f971bb0bdb43c65b4d6375d53c65db2d40230950 · TRUST_VECTOR
- `claim_statements_tier1v2.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_tier1v2.json` · e1e37f417c0f4342a7bf40dd7ae920b2ce8e20e134f55f32fe30b1f58b1544b5 · CLAIM_GATE_DECISION
- `gate6_reproducibility_executed.json` · ecbe450a1008ade2da6288fcefbb23c9b88a5f7e30a4e00270eb02fe02646a4b · GATE_RESULT
- `trust_vector_g6.json` · 026ea517be128ff227196ddd5cfe7374707fe9f69ba36d3339b7f435df6f2491 · TRUST_VECTOR
- `claim_statements_g6.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_g6.json` · 3170add040aac89346b9ba44cfb4a51f6d1ee8180f660218bb425782f78143f7 · CLAIM_GATE_DECISION
- `attempt_state.json` · 7bb39001d0e9352825e9ab07bda7228003943562deb36658db204b13e22e28a3 · STATE
- `RUN_SUMMARY.json` · 8bca3db78c00e41a098c4f407b3d2b45aa6525aff6f39f0e00155d5b401504ee · SUMMARY
- `PROVENANCE_MANIFEST.json` · c8061600a0a2aaffd8e1764a18b8c65c0c957a3e0a313fc996ecc176caa5b500 · (index)
- `STATE_TRANSITIONS.json` · 0454ed13896b304e855e5bec3a0010fb54e0f2ea0b176356a4568c61c5647210 · (index)
- `TRUST_REPORT.md` · d0c3dab8a611885c25cbb8ef53501d8708dc6c95996934361f82b8264e8c6a9c · (index)
- `POST_AUDIT_ANNOTATION.md` · 0a925fd242e5be796d78859665e0dae0ef79d3e40613f46eeec41abef12fc880 · (index)
- `attempt_state.json` · 7bb39001d0e9352825e9ab07bda7228003943562deb36658db204b13e22e28a3 · (index)
