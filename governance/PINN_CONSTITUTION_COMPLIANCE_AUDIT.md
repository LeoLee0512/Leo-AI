# PINN 宪法合规审计报告

**PINN Constitution Compliance Audit**

| 字段 | 值 |
| --- | --- |
| Audit ID | `AUDIT-2026-09-04-001` |
| Constitution Version Audited Against | 1.0（2026-09-04 生效） |
| Audit Date | 2026-09-04 |
| Auditor Role | Auditor（宪法第三十七条：与 Builder / Runner / Validator 职责分离） |
| Audit Status | **COMPLETE** |
| 总体裁定 | 见 §3 |

---

## 0. 审计方法与诚实性声明（第三十九条、第四十条）

本宪法第三十九条禁止 Agent 伪造执行、第四十条禁止伪造文件与指标。因此本报告先声明**审计者实际做了什么、没做什么**。

### 0.1 实际执行的动作（已验证）

| 动作 | 说明 |
| --- | --- |
| 目录遍历 | `LeoAIStudio/`、`LeoAIStudio-build/`、`upstream/OpenAI4S/`、`user/user-skills/`、`Desktop/pinns/` |
| 关键词计数 | 对 `upstream/OpenAI4S` 与 `pinns/main.py` 执行 grep 计数，数值见 §4 |
| 源码阅读 | `pinns/main.py`（2697 行，按段读取）、`pinns/复现/autonomous_optimizer.py`（头部与终止判据）、`user/user-skills/research-sop/kernel.py`（结构与状态词汇）、`upstream/OpenAI4S/openai4s/benchmark/model.py` |
| 产出数据解析 | `outputs_singlefile_smoke_final/` 下的 `final_results.json`、`run_config.json`、`training_history.json`、`physics_reconstruction_metrics.json`、`results_discussion.txt`；`复现/outputs_aligned/aligned_figure_config.json` |
| 文件存在性核验 | 对 `aligned_figure_config.json` 声明的 checkpoint 路径做了实际 `ls` |
| 版本控制状态核验 | 对 `pinns/` 执行 `git rev-parse` |

### 0.2 **未**执行的动作（按第三十九条标记 UNVERIFIED）

| 未做的事 | 后果 |
| --- | --- |
| 未运行任何 PINN 训练 | 本报告不对运行时行为下断言，只对**代码路径**与**已落盘的产出记录**下断言 |
| 未加载 `.pt` checkpoint | 未独立复算任何 metric |
| 未逐张打开 `.png` 图像 | 关于图像的结论**全部来自生成这些图像的代码路径与随附 JSON**，而非视觉判断（这本身正是第三十一条要求的做法） |
| 未联系原文献核对 Phys. Fluids 2023 / Shi 2024 的方程与参数 | Level C 证据等级无法在本轮判定 |

**凡本报告写 `UNVERIFIED` 之处，即为审计者无法取得证据之处，不得被下游解读为 PASS。**

### 0.3 状态词汇（严格按第四章）

- `PASS` — 全部 MUST 条件满足且证据完整。
- `FAIL` — Gate 已执行，至少一个 MUST 条件未满足。
- `BLOCKED` — 上游 prerequisite 未满足，本 Gate 不得执行。
- `PARTIAL` — 仅内部诊断。**PARTIAL ≠ PASS，不具推进状态机的权限。**

本报告**不使用**"总体上符合""基本达标""大体没问题"等表述。

---

## 1. 审计对象

| 代号 | 对象 | 路径 | 性质 |
| --- | --- | --- | --- |
| **S1** | Leo AI Studio 平台 | `LeoAIStudio-build/`、`LeoAIStudio/`、`LeoAIStudio/upstream/OpenAI4S/`、`LeoAIStudio/user/user-skills/` | 承载平台。**内部不存在任何 PINN 实现。** |
| **S2** | 实际 PINN 科研代码与产出 | `C:\Users\user\Desktop\pinns\` | 真实存在的 Maxwell-MHD reduced PINN 研究，含 6 个 `outputs_*` 目录与 `复现/` 子项目 |

### 1.1 S1 的第一性事实：PINN 子系统不存在

对 `upstream/OpenAI4S` 全量源码（`*.py *.md *.js *.json *.yaml *.toml`）的关键词计数：

| 关键词 | 命中文件数 |
| --- | --- |
| `physics-informed` / `physics_informed` | **0** |
| `collocation` | **0** |
| `navier` | **0** |
| `burgers` | **0** |
| `deepxde` | **0** |
| `PDE residual` | **0** |
| `poisson` | 仅 5 个生物统计 SKILL.md（泊松分布，与 PDE 无关） |
| `pinn` | 全部为 `pinned` / `spinner` 等假阳性，**无一为 Physics-Informed Neural Network** |

**结论：Leo AI Studio 内部没有 PINN 子系统。** 因此 S1 在所有"实验如何执行"类条款上的状态是 `BLOCKED`（第四条：上游 prerequisite 未满足，Gate 不得执行），而非 PASS，也不是 FAIL——**没有对象可审不等于合规**。

S1 仅在"平台必须提供什么治理能力"类条款上可被实际判定。

---

## 2. 逐条审计总表

> 说明：S1 的 `BLOCKED` 一律表示"Leo AI Studio 内不存在 PINN 实验对象，该条款无法执行"，不表示豁免。

### 第一章：基本原则

| 条款 | 标题 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- | --- |
| 第一条 | 科学问题先于模型 | BLOCKED | **FAIL** | S2 无任何 ScientificSpec；`main.py` 由 dataclass 配置直接进入网络与训练，`scientificQuestion` 不存在 |
| 第二条 | 规格冻结原则 | BLOCKED | **FAIL** | 无 spec 即无从冻结；`AdaptiveLossBalancer.rebalance_for_pde_dominance()` 在训练中改写权重，`run_config.json` 只存初值 |

### 第二章：证据等级

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| Level A（解析/制造解） | BLOCKED | **FAIL** | `main.py` 中 `analytic` 命中 0 次、`manufactured` 命中 0 次 |
| Level B（收敛数值参考） | BLOCKED | **FAIL** | 无任何独立 solver；无网格/时间步独立性证据 |
| Level C（公开 benchmark） | BLOCKED | **UNVERIFIED** | 存在 `shi2024_pinn_single.py` 与 "Phys. Fluids 2023" 表述，但未记录文献、方程、参数、无量纲化、比较量 |
| Level D（EXPLORATORY 标记） | BLOCKED | **FAIL** | 无独立参考却未标 `EXPLORATORY`，反而产出 `results_discussion.txt` 形式的论文结论段 |

### 第三章～第四章：状态机与 Gate 词汇

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第三章 闭环状态机 | **FAIL** | **FAIL** | S1 有 `research-sop` 五角色流水线与 rollback，但无 `BASELINE_VERIFIED` / `IMPLEMENTATION_VERIFIED` / `REPRODUCIBILITY_CHECK` 三个 Gate；S2 直接 `TRAINING → 出图 → 写结论`，即宪法明令禁止的 `TRAINING_COMPLETED ↓ ACCEPTED` |
| 第四章 Gate 状态定义 | **PARTIAL** | **FAIL** | S1：`benchmark/model.py` 的 `OUTCOMES = {success, failure, cancelled, recovered, permission_denied, provenance}` 有非成功态但**无 BLOCKED、无 PARTIAL**；`acceptance.py` 仅 `"status": "pass" if passed else "fail"`。S2：无 Gate 概念 |

### 第五章～第六章：Spec 与数学一致性

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第五章 ScientificSpec | **FAIL** | **FAIL** | 25 个必需字段，S1 与 S2 均实现 0 个 |
| 第六章-1 方程数/未知量数 | BLOCKED | **FAIL** | 无审计记录 |
| 第六章-2 BC/IC 完整性 | BLOCKED | **FAIL** | 无完整性证明；`hard_boundary_transform` 用网络结构强加边界，替代了数学完整性论证 |
| 第六章-3 单位一致性 | BLOCKED | **FAIL** | `run_config.json` 无 `units` 字段 |
| 第六章-4 无量纲化一致性 | BLOCKED | **FAIL** | `lambda / M / Pr / Prm / R` 均无 characteristic scale 声明 |
| 第六章-5 坐标与几何约定 | BLOCKED | **PARTIAL** | `DomainConfig` 冻结了 `y∈[0,8], t∈[0,1]`，但 `reference length` 未定义 |
| 第六章-6 符号一致性 | BLOCKED | **FAIL** | `M` 在同一代码库中既是磁参数（`magnetic`）又是图例族名，`复现/` 中改用 `B`，未记录等价关系 |

### 第七章～第九章：Baseline、实现验证、数据隔离

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第七章 Baseline 原则 | BLOCKED | **FAIL** | 无独立计算路径；`reference` 在 2697 行中仅出现 1 次且非参考解语义 |
| 第七章 Reference Independence | BLOCKED | **FAIL** | `复现/outputs_aligned*` 的"aligned"目标即为向已发表图形对齐，方向与本条相反 |
| 第八章 Autograd check | BLOCKED | **FAIL** | 无 autograd 验证测试 |
| 第八章 Residual check | BLOCKED | **FAIL** | 无 residual 正确性测试 |
| 第八章 Boundary Operator check | BLOCKED | **FAIL** | 无边界算子测试 |
| 第八章 Coordinate Mapping | BLOCKED | **FAIL** | 无测试 |
| 第八章 Scaling | BLOCKED | **PARTIAL** | 存在 `normalize()` / `unit_y()`，但无 residual scaling 声明 |
| 第八章 Manufactured Solution | BLOCKED | **FAIL** | 0 次命中。**宪法要求此时 `TRAINING MUST NOT START`，而训练已多次执行** |
| 第九章 数据隔离 | BLOCKED | **FAIL** | `CollocationSampler` 每步重采样，`final validation set` 不存在；`should_stop()` 直接依赖绘图网格上的 `profile_ok` → **validation leakage**（见 §4.8） |

### 第十章～第十二章：训练 Gate 与 Loss 语义

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第十章 Run 记录 24 项 | BLOCKED | **PARTIAL** | 已记录：architecture / activation / optimizer / lr / lossWeights / sampling / nInterior / nBoundary / nInitial / seed / iterations / wallTime / lossHistory / gradientDiagnostics。**缺失：runId、specId、codeVersion、commitHash、hardware、softwareEnvironment、terminationReason** |
| 第十一章 禁止单一 total loss | BLOCKED | **PASS** | `training_history.json` 逐项保存 `momentum / magnetic / energy / boundary / initial / divergence / smoothness / normalization / monotonicity / memory_balance / memory_regularization / pde / total` 及全部 `w_*` 权重。**这是 S2 唯一完整合规的条款** |
| 第十二章 Loss 不是精度指标 | BLOCKED | **FAIL** | `results_discussion.txt` 第 3 节标题为 "PINN Performance Summary"，内容仅为 `best_loss = 0.2137` 与 loss 变化，无任何 vs 参考解误差 |

### 第十三章～第二十章：验证协议

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第十三章 ValidationReport | BLOCKED | **FAIL** | 17 个必需字段实现 0 个；`validat*` 在 `main.py` 中命中 0 次 |
| 第十四章 相对 $L_2$ / $L_\infty$ | BLOCKED | **FAIL** | `L2` 命中 0 次 |
| 第十五章 分场误差 | BLOCKED | **FAIL** | $u,v,H,T$ 四个输出场无任一误差指标 |
| 第十六章 PDE residual holdout | BLOCKED | **FAIL** | `holdout` 命中 0 次；仅有训练点上的 residual |
| 第十七章 Boundary validation | BLOCKED | **FAIL（加重）** | 不仅无 $E_{BC}$，且 `enforce_2d_boundaries()` 在**出图前**把边界行直接改写为解析 ramp（见 §4.3） |
| 第十八章 物理守恒 | BLOCKED | **FAIL** | `conserv` 命中 0 次；`divergence` 仅作 loss 项，未在独立点上验证 |
| 第十九章 QoI | BLOCKED | **FAIL** | 无 `targetQuantities` 事前声明；`results_discussion.txt` 事后挑选 roughness / monotonicity 作为汇报指标 |
| 第二十章 事前 acceptance criteria | BLOCKED | **FAIL（严重）** | `复现/autonomous_optimizer.py:585` 的终止判据是**视觉评分**：`score.total >= 0.86 and score.smoothness > 0.82 and score.monotonicity > 0.90 and score.stability > 0.70` → 打印 `Convergence target reached.`（见 §4.5） |

### 第二十一章～第二十四章：失败治理

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第二十一章 FailureRecord | **FAIL** | **FAIL** | 两侧均无 FailureRecord 对象。S2 有 `stability_events.json` 记录 `loss_spike` / `pde_rebalance`，但无 12 项必需字段 |
| 第二十二章 Failure Taxonomy | **FAIL** | **FAIL** | 12 类分类法未实现 |
| 第二十三章 诊断可证伪 | BLOCKED | **FAIL** | `results_discussion.txt` 无 hypothesis / test / result / conclusion 分层 |
| 第二十四章 避免同时改多变量 | BLOCKED | **FAIL** | `autonomous_optimizer.py` 的 `HyperParams` 单次迭代同时扫描 `fourier_features / fourier_scale / smoothness_weight / energy_stability_weight / residual_balance_weight / normalization_weight / parameter_monotonicity_weight / gate_consistency_weight / gate_hidden / magnetic_velocity_damping` 等 10+ 项，且未标 `compound intervention` |

### 第二十五章～第二十八章：证据不可篡改与可追溯

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第二十五章 不可静默修复 | **PARTIAL** | **FAIL** | S1：`research-sop` 的 rollback 会归档旧件且"归档不可验证则中止 rollback"，方向正确但不覆盖 PDE/BC/threshold 修改。S2：训练中 `rebalance_for_pde_dominance()`、`damp_memory()`、`reduce_fourier_scale()`、`fallback_to_best()` 均自动改写模型/权重，仅记事件名与标量，不记改动内容 |
| 第二十六章 不可覆盖证据 | **PARTIAL** | **FAIL** | S1 有 artifact `sha256` 版本机制（`server/artifact_refs.py`）。S2：`outputs_singlefile_smoke_final/` 中 `parameter_M_effect.png` 与 `parameter_M_effect_final.png`、`parameter_M_final.png`、`parameter_sweep_monotone_fixed.png` 并存于同一目录，同一量的多个"修好版本"无版本语义 |
| 第二十七章 唯一 Run ID | **PARTIAL** | **FAIL（严重）** | S1：`research-sop` 有 16 位 hex `run_id`（由 task sha256 派生并强制校验）。S2：**无 runId**。`复现/outputs_aligned/aligned_figure_config.json` 指向 `C:\Users\user\Desktop\pinns\outputs\run_6\model.pt`，实测该路径**不存在**（见 §4.6）→ 已发表级图形无法追溯到任何 checkpoint |
| 第二十八章 环境可复现性 | BLOCKED | **FAIL** | `run_config.json` 记录了 `seed=20230531 / device / dtype`，但 `commit / torch / cuda / python / hardware / version` 全部 ABSENT；且 `pinns/.git` 为**空目录**，`git rev-parse` 返回 `fatal: not a repository` → **无代码版本控制**。按第二十八条应标记 `REPRODUCIBILITY LIMITED`，实际未标记 |

### 第二十九章～第三十三章：统计诚实与公平比较

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第二十九章 随机性原则 | BLOCKED | **FAIL** | 单 seed（20230531），无 mean/std/best/worst；`results_discussion.txt` 仍声称 "The recorded convergence behavior is stable" |
| 第三十章 不得 cherry-pick | BLOCKED | **FAIL** | 6 个 `outputs_*` 目录 + `复现/` 3 个 `outputs_aligned*`（sigma 的三档变体）并存，报告未声明独立实验总数 $N$ |
| 第三十一章 Figure ≠ Evidence | BLOCKED | **FAIL（最严重）** | 见 §4.3、§4.4。图像被高斯平滑、Savitzky-Golay 平滑、PCHIP 重插值、边界改写、并用 `np.minimum/np.maximum` 与 PAVA 保序回归**强制单调**后才出图 |
| 第三十二章 Baseline 非 strawman | BLOCKED | **BLOCKED** | 无 baseline，无从判定强弱 |
| 第三十三章 比较公平性 | BLOCKED | **BLOCKED** | 未进行 PINN vs FEM/FVM 比较 |

### 第三十四章～第三十六章：结论治理

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第三十四章 ScientificClaim Ledger | **FAIL** | **FAIL** | 两侧均无 claim 登记 |
| 第三十五章 结论限定域 | BLOCKED | **FAIL** | `results_discussion.txt` 在 `λ=0.35, M=1.0, Pr=4.0, Prm=1.0` 单点出图，却写出对 M 与 λ 的一般性物理结论 |
| 第三十六章 Claim Levels | BLOCKED | **FAIL（严重）** | 该 Run 证据等级为 **C0**（`final_step=5`、`n_pde=24`），却被用于表述 C2（"expected Lorentz-force damping"）与 C5（"suitable for inclusion as publication-style CFD visualizations"）级结论 |

### 第三十七章～第四十四章：Agent 行为准则

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第三十七章 Builder/Auditor 分离 | **PARTIAL** | **FAIL** | S1：`research-sop` 有独立 `validator` 角色并可回退（`max_rollbacks=2`），职责分离方向正确，但 validator 无权判 `BLOCKED`。S2：同一脚本自训练、自评分、自出图、自写结论 |
| 第三十八章 验证阶段禁改实现 | BLOCKED | **FAIL** | `autonomous_optimizer.py` 的循环即为"评分→改超参→重训→再评分"，验证与实现同环 |
| 第三十九章 不得伪造执行 | **PASS** | **PARTIAL** | S1 未发现伪造执行痕迹。S2：`results_discussion.txt` 称 "No retraining, PDE redesign, or network-architecture change was performed during this finalization pass"，此陈述与 finalization 代码路径一致，未发现伪造；但同一文件把后处理产物表述为物理观测（见第四十二章） |
| 第四十章 不得伪造文件与指标 | **PASS** | **FAIL** | S2：`aligned_figure_config.json` 声明的 checkpoint 路径不存在，构成指向不存在证据的 manifest |
| 第四十一章 Research Log | **PARTIAL** | **FAIL** | S1：`research-sop` 各阶段落盘 `.md` + `.json`。S2：无研究日志，`results_discussion.txt` 是宣传性结论文本而非日志 |
| 第四十二章 Result ≠ Interpretation | BLOCKED | **FAIL（最严重）** | 原始记录 `final_results.json` 写 `"M_velocity_monotone": false`、`"profile_ok": false`；`results_discussion.txt` 写 "velocity profiles are ordered monotonically with increasing M"。**一个 false 的观测被后处理转成了正面物理结论**（见 §4.4） |
| 第四十三章 逐级升级 | BLOCKED | **FAIL** | 未通过任何解析 benchmark，直接做 6 输入 4 输出的多物理 Maxwell-MHD 记忆核问题 |
| 第四十四章 最小闭环优先 | **FAIL** | **FAIL** | 两侧投入均优先于"更漂亮/更自动"：S2 存在 `set_final_paper_style()`、`configure_paper_style()`、`generate_publication_figures()`，但无一行 validation 代码 |

### 第四十五章～第四十八章：领域对象与目录契约

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第四十五章 8 类核心 domain object | **FAIL** | **FAIL** | `ScientificSpec / BaselineRecord / ExperimentRun / ValidationReport / FailureRecord / ScientificClaim / ArtifactManifest / DecisionRecord` 实现数：S1 = 0（`research-sop` 的 manifest 最接近 ExperimentRun 但字段不符），S2 = 0 |
| 第四十六章 ArtifactManifest | **PARTIAL** | **FAIL** | S1：`artifact_refs.py` 具备 `artifact_id / version_id / sha256`；`manifests/wheelhouse.json` 已做 SHA-256 清单化，机制可复用。S2：无 manifest，无 hash，无 source 字段 |
| 第四十七章 DecisionRecord | **FAIL** | **FAIL** | 两侧均未实现 |
| 第四十八章 目录契约 | **FAIL → 本次部分修复** | **FAIL** | 本次审计已创建 `LeoAIStudio-build/governance/` 与 `AMENDMENTS/`；`specs/ baselines/ runs/ validation/ failures/ claims/ research_logs/` 仍不存在。S2 目录为 `outputs_<随手命名>/`，无规格-运行-验证-失败-结论互链 |

### 第四十九章～第五十五章：七道 Gate

| Gate | 条款 | S1 | S2 | 依据 |
| --- | --- | --- | --- | --- |
| Gate 1 | 第四十九章 SPEC | **FAIL** | **FAIL** | 9 项 PASS 条件满足 0 项 → 按本条，所有下游 `BLOCKED` |
| Gate 2 | 第五十章 BASELINE | BLOCKED | BLOCKED | 上游 Gate 1 FAIL。附带裁定：`Accuracy Claim = BLOCKED` |
| Gate 3 | 第五十一章 IMPLEMENTATION | BLOCKED | BLOCKED | 上游 FAIL。附带裁定：`Training = BLOCKED` |
| Gate 4 | 第五十二章 TRAINING | BLOCKED | **FAIL** | 即使单独评判也不通过：`safe_value()` 用 `torch.nan_to_num(nan=0.0)` + `clamp(±100)` **静默吞掉 NaN/Inf**，违反"无静默 NaN"（见 §4.2）；`terminationReason` 未记录 |
| Gate 5 | 第五十三章 VALIDATION | BLOCKED | BLOCKED | 无验证实现，Gate 从未执行 |
| Gate 6 | 第五十四章 REPRODUCIBILITY | BLOCKED | **FAIL** | 关键 checkpoint `outputs/run_6/model.pt` 已遗失，产出图形不可重绘 |
| Gate 7 | 第五十五章 SCIENTIFIC CLAIM | BLOCKED | **FAIL** | 上游全部未 PASS，却已产出论文式结论文本 |

### 第五十六章～第六十三章：回流、修宪与最高原则

| 条款 | S1 | S2 | 核心依据 |
| --- | --- | --- | --- |
| 第五十六章 失败回流规则 | **PARTIAL** | **FAIL** | S1：`research-sop` validator 可回退到上游角色，但不区分 Spec/Baseline/Implementation/Scaling 等 10 个层级。S2：失败一律以"改超参重跑"回应 |
| 第五十七章 禁止无限重试 | **PASS** | **FAIL** | S1：`orchestrate_research(max_rollbacks=2)` 是明确 rescue budget，超预算返回 `unresolved`——**这正是宪法要求的形状**。S2：`autonomous_optimizer.py` 循环直到视觉分达标 |
| 第五十八章 Negative result 合法 | **PASS** | **FAIL** | S1：`unresolved` 是合法终态。S2：不存在 negative result 通路，`results_discussion.txt` 中无一句否定性结论 |
| 第五十九章 禁止改历史造成功 | **PARTIAL** | **FAIL** | S1：rollback 强制归档且归档失败即中止。S2：`*_final.png`、`*_fixed.png`、`*_physics_consistent.png` 与原图同目录并存，"修好的版本"直接充当结论依据 |
| 第六十章 修宪制度 | **PASS（本次建立）** | N/A | `governance/AMENDMENTS/` 已建立，含模板与登记表 |
| 第六十一章 规则优先级 | **PASS（本次建立）** | **FAIL** | 优先级链已由宪法确立；S2 无任何上位规则可被遵守 |
| 第六十二章 Stop-the-Line | **FAIL** | **FAIL** | 两侧均无 `BLOCKED` 状态、无停线机制。S1 的 UI 无 "BLOCKED — upstream scientific gate failed" 表达能力 |
| 第六十三章 最终原则 | **FAIL** | **FAIL** | 当前系统的能力全部用于"跑出结果"，无一处用于"阻止错误结果被当成正确结论" |

### 附录 A / B / C

| 附录 | S1 | S2 | 依据 |
| --- | --- | --- | --- |
| 附录 A 最小闭环定义 | **FAIL** | **FAIL** | 9 个必需环节中，Independent Baseline / Independent Validation / PASS-FAIL / Failure Diagnosis / Re-validation 五环缺失 → **按附录 A，两者都只能叫 pipeline，不得叫科研闭环** |
| 附录 B MVP 基准问题 | **FAIL** | **FAIL** | 解析 Poisson benchmark 从未建立；未构造任何错误版本做拒绝测试 |
| 附录 C 成功标准 | **FAIL** | **FAIL** | Accept Good：未验证。**Reject Bad：能力不存在。** Abstain When Uncertain：能力不存在 |

---

## 3. 总体裁定

### 3.1 当前系统是 pipeline 还是 closed loop？

$$
\boxed{\text{两者都是 pipeline，都不是科研闭环}}
$$

按附录 A，闭环需要 9 个环节。当前状况：

| 环节 | S1 Leo AI | S2 pinns |
| --- | --- | --- |
| ScientificSpec | ✗ | ✗ |
| Independent Baseline | ✗ | ✗ |
| PINN Implementation | ✗（无 PINN） | ✓ |
| Training | ✗（无 PINN） | ✓ |
| Independent Validation | ✗ | ✗ |
| PASS / FAIL | ✗ | ✗ |
| Failure Diagnosis | △（research-sop 有 validator 回退） | ✗ |
| Revision | △ | ✓（但为盲目改参） |
| Re-validation | ✗ | ✗ |

**S2 更准确的定性不是 pipeline，而是一条"训练 → 后处理 → 结论"的单向出图流水线**：它的最后一段（后处理）具备把不合格结果转成合格外观的能力，而没有任何一段具备否决能力。

### 3.2 宪法当前生效状态

- 宪法 v1.0 自 2026-09-04 生效。
- 依第四十九条，Gate 1（SPEC）在 S1 与 S2 均为 `FAIL`，因此**所有下游科学 Gate 一律 `BLOCKED`**。
- 依第五十条，`Accuracy Claim = BLOCKED`。
- 依第六十二条，本审计**触发 STOP THE LINE**。

### 3.3 STOP-THE-LINE 裁定（第六十二条）

$$
\boxed{\text{STOP THE LINE — 已触发}}
$$

触发条件命中 9 条中的 8 条：ScientificSpec 不完整、baseline 不可信（不存在）、evidence 缺失、implementation verification 失败、validation leakage、artifact 丢失（`outputs/run_6/model.pt`）、无法判断数据来源、发现潜在科研完整性问题。

**由此产生的强制后果：**

1. `pinns/` 现有全部结论降级为 **C0（Implementation Claim）**，且标记 `EXPLORATORY`。
2. `results_discussion.txt` 中的物理结论**不得对外使用、不得投稿、不得进入任何报告**，直到通过 Gate 5。
3. `outputs_*` 现有内容按第二十一条与第二十六条 **一律冻结保留，不得删除、不得覆盖**——它们现在是失败证据，不是垃圾。
4. 不得在解析 benchmark 闭环建立前，继续投入 Maxwell-MHD 问题的新训练（第四十三条）。

---

## 4. 证据档案（关键 FAIL 的原始依据）

### 4.1 关键词计数（`Desktop/pinns/main.py`，2697 行）

| 关键词 | 命中次数 | 宪法条款 |
| --- | --- | --- |
| `analytic` | **0** | 第二章 Level A、第八章 |
| `manufactured` | **0** | 第八章（制造解） |
| `validat*` | **0** | 第十三章、第五十三章 |
| `L2` | **0** | 第十四章 |
| `ground truth` | **0** | 第二章 |
| `holdout` | **0** | 第十六章 |
| `conserv*` | **0** | 第十八章 |
| `acceptance` | **0** | 第二十条 |
| `reference` | 1（非参考解语义） | 第七章 |
| `seed` | 12（单 seed） | 第二十九章 |

### 4.2 静默 NaN（第五十二章 / Gate 4）

`main.py:552-556`：

```python
def safe_value(value: torch.Tensor, clip: float = 100.0) -> torch.Tensor:
    out = torch.nan_to_num(value, nan=0.0, posinf=clip, neginf=-clip)
    if clip > 0.0:
        out = out.clamp(min=-clip, max=clip)
```

该函数被 **全部 PDE residual、全部边界项、全部初值项** 调用（`residual_clip=100.0`）。后果：一个发散到 NaN 的 residual 会被静默替换为 0，从而在 loss 中表现为"该约束已完美满足"。宪法第五十二条要求 Gate 4 PASS 的条件之一即"无静默 NaN"。

### 4.3 出图前改写边界（第十七章 / 第三十一章）

`main.py:1737-1755`：

```python
def enforce_2d_boundaries(field, kind, t_grid, model_config):
    out = np.asarray(field, dtype=np.float64).copy()
    ramp = _ramp_np(t_grid, model_config.startup_rate)
    if kind in {"u", "T"}:
        out[0, :] = ramp
        out[-1, :] = 0.0
    elif kind == "H":
        out[0, :] = 0.0
        ...
```

被绘图的场**不是模型输出**：边界行被直接赋成解析 ramp。`results_discussion.txt` 对此的表述是：

> "Boundary conditions are restored exactly after Gaussian and Savitzky-Golay smoothing."

即：图上边界条件"完美满足"这一现象，是被写进去的，不是被学出来的。宪法第十七条要求的 $E_{BC}=\max|u_\theta-g|$ 从未被计算。

同一路径上还有 `smooth_final_fields()`（`main.py:1805`，高斯滤波 σ=1.0/0.9/0.8）与 `smooth_display_profile()`（`main.py:1846`，Savitzky-Golay window=9 + PCHIP 重插值到 420 点）。

### 4.4 单调性被强制制造（第三十一章 / 第四十二章，最严重）

`main.py:1887-1894`：

```python
def _enforce_parameter_display_order(curves, family):
    if family == "M":
        for i in range(1, len(curves["u"])):
            curves["u"][i] = np.minimum(curves["u"][i], curves["u"][i - 1])
            curves["H"][i] = np.maximum(curves["H"][i], curves["H"][i - 1])
```

`physics_reconstruction_metrics.json` 明确记录了这一投影：

```json
"smoothing_method": "explicit discrete heat equation, tau=1",
"monotonic_projection": "PAVA isotonic regression along parameter axis",
"M_velocity_strictly_nonincreasing": true,
"M_H_strictly_nondecreasing": true
```

**三份文件的对照构成完整证据链：**

| 文件 | 陈述 |
| --- | --- |
| `final_results.json`（原始运行记录） | `"M_velocity_monotone": false`，`"lambda_velocity_monotone": false`，`"nonnegative": false`，`"profile_ok": false` |
| `physics_reconstruction_metrics.json`（后处理后） | `"M_velocity_strictly_nonincreasing": true` |
| `results_discussion.txt`（结论） | "Increasing the magnetic parameter M produces the expected Lorentz-force damping of the velocity field. In the final display curves, the velocity profiles are ordered monotonically with increasing M after display-only smoothing" |

模型**没有**学出洛伦兹力阻尼的单调性（原始记录为 `false`）；保序回归把它投影成了单调；结论段把这个投影结果表述为"符合预期的物理"。这同时违反第三十一条（Figure ≠ Evidence）、第四十二条（Result ≠ Interpretation）与第三十六条（C0 证据支撑 C2 结论）。

`final_parameter_plot()` 返回的指标键名本身已经承认了这一点：`"M_velocity_monotone_after_postprocess"`。**指标测的是后处理，不是模型。**

### 4.5 acceptance criteria 是视觉评分（第二十条 / 第五十七条 / 第五十八条）

`复现/autonomous_optimizer.py` 文件头：

> "Autonomous PINN optimization loop for **publication-style figures**."

`复现/autonomous_optimizer.py:585`：

```python
if score.total >= args.target_score and score.smoothness > 0.82 \
   and score.monotonicity > 0.90 and score.stability > 0.70:
    print("Convergence target reached.")
```

`--target-score` 默认 `0.86`。

该循环的收敛判据中**没有任何一项是对参考解的误差**：`smoothness`、`monotonicity`、`stability` 全部是外观/形状指标。这正是第五十八条明令禁止的行为——"不得因为产品想展示'成功'而继续自动调参直到得到好看的结果"——并且它是被写成代码、自动执行的版本。

同时命中第二十四条：`HyperParams` 单次迭代同时改动 10+ 个因素，未标 `compound intervention`。

### 4.6 证据丢失与无版本控制（第二十六～二十八章、第五十四章）

```
$ cat 复现/outputs_aligned/aligned_figure_config.json
{ "checkpoint": "C:\\Users\\user\\Desktop\\pinns\\outputs\\run_6\\model.pt", ... }

$ ls -d outputs
ls: cannot access 'outputs': No such file or directory
```

生成 `outputs_aligned/` 全部"对齐版"图形的 checkpoint **不存在**。这些图无法重绘、无法复核、无法追溯。

```
$ git -C pinns rev-parse --is-inside-work-tree
fatal: not a git repository (or any of the parent directories): .git

$ ls -a pinns/.git
.  ..
```

`pinns/.git` 是空目录。**该研究项目没有任何代码版本控制**，`run_config.json` 中 `commit / torch / cuda / python / hardware` 全部 ABSENT。

### 4.7 C0 证据支撑 C2/C5 结论（第三十六章）

产出 `results_discussion.txt` 的那次 Run 的实际规模，来自其自身的 `run_config.json` 与 `final_results.json`：

| 项 | 值 |
| --- | --- |
| `warmup_steps` | 2 |
| `adam_steps` | 4 |
| `lbfgs_steps` | 1 |
| `final_step` | **5** |
| `n_pde`（内部配点） | **24** |
| `n_bc` / `n_ic` | 12 / 12 |
| `target_loss` | 0.001 |
| `best_loss` | **0.2137**（未达 target_loss，差 213 倍） |
| `elapsed_s` | 1.65 |

**24 个内部配点、5 步优化、1.6 秒、目标 loss 未达成**的一次 smoke run，产出了一份写着 "Key Physical Observations" 与 "suitable for inclusion as publication-style CFD visualizations" 的 Results & Discussion。

### 4.8 Validation leakage：出图网格直接控制 early stopping（第九章）

`main.py:1036-1040`：

```python
def should_stop(self, step: int, total_loss: float) -> bool:
    if step < self.training.min_steps_before_stop:
        return False
    loss_good = total_loss < self.training.target_loss or self.is_loss_stable()
    return bool(loss_good and self.is_loss_stable() and self.last_profile_ok)
```

`last_profile_ok` 的来源（`main.py:1238-1241`、`1372-1375`、`1403-1405`）：

```python
metrics = profile_metrics(self.model, self.domain, self.plot, self.device, self.dtype)
self.controller.last_profile_ok = bool(metrics["profile_ok"])
```

`profile_metrics()` 在 **`self.plot` 配置的网格**（即后续出图所用的同一组 $\lambda$、$M$、时间切片）上评估 `M_velocity_monotone / lambda_velocity_monotone / H_M_monotone / nonnegative / noise_ok`。

因此：**用于评价结果的那组点，同时是决定训练何时停止的那组点。** 宪法第九条明确列出 `final validation points` 不得用于 `early stopping`。此处不仅用了，而且是唯一的形状类停止条件。

配合 §4.4 可以看到完整链条：同一组网格既决定何时停训、又被后处理投影成单调、再被写进结论段。

---

## 5. 最大的 10 个合规缺口（按危害排序）

| # | 缺口 | 违反条款 | 危害 | 现状 |
| --- | --- | --- | --- | --- |
| **1** | **后处理可以把 FAIL 变成 PASS 的外观** —— 高斯平滑 + 保序回归 + 边界改写 + PCHIP 重插值，且结论段直接引用后处理结果作为物理观测 | 三十一、四十二、三十六 | 系统当前**具备制造虚假科研结论的能力**，且已实际发生一次 | FAIL |
| **2** | **完全没有独立参考解与 validation 层** —— `validat*`/`L2`/`holdout`/`conserv` 命中均为 0 | 七、十三、十四、十六、十八、五十三 | 没有任何机制能判定一个解是对是错 | FAIL |
| **3** | **没有 ScientificSpec，acceptance criteria 不是事前声明的误差阈值而是事后的视觉评分** | 一、二、五、二十 | post-hoc acceptance manipulation 被自动化 | FAIL |
| **4** | **系统没有 `BLOCKED` 这个状态** —— `benchmark` 只有 pass/fail，UI 无停线表达 | 四、六十二 | 证据不足时只能猜，不能弃权；附录 C 三分之一能力缺失 | FAIL |
| **5** | **没有实现验证 Gate（autograd / residual / 制造解）** —— 宪法要求此时 `TRAINING MUST NOT START`，而训练已多次执行 | 八、五十一 | 无法区分"模型学不会"与"PDE 写错了" | FAIL |
| **6** | **静默 NaN** —— `nan_to_num(nan=0.0)` 应用于全部 residual | 五十二 | 发散被记录成"约束完美满足" | FAIL |
| **7** | **无 runId、无 commit、无环境记录、关键 checkpoint 已丢失** | 二十七、二十八、四十六、五十四 | 已发表级图形不可复现、不可追溯 | FAIL |
| **8** | **无 FailureRecord / Failure Taxonomy / 可证伪诊断** —— 失败只以"改参重跑"回应 | 二十一～二十四、五十六、五十七 | 失败不产生知识，只产生下一次盲目尝试 | FAIL |
| **9** | **8 类核心 domain object 一个都不存在** | 四十五～四十七 | 科研状态只存在于文件名和聊天历史里 | FAIL |
| **10** | **未通过任何解析 benchmark 就直接做 6 输入 4 输出多物理问题** | 四十三 | 上游未验证的错误被下游复杂度掩盖 | FAIL |

---

## 6. 可直接复用的模块（不必重写）

| 模块 | 路径 | 可复用为 | 证据 |
| --- | --- | --- | --- |
| **research-sop run/manifest 机制** | `user/user-skills/research-sop/kernel.py`（1220 行） | `ExperimentRun` + `ArtifactManifest` 骨架 | 16 位 hex `run_id` 由 task sha256 派生并强制校验；manifest 含 `task_sha256 / pipeline_version / role_prompt_hashes / model_fingerprint / parent_run_id / rollbacks`；路径包含性校验 `sop_contained_path` |
| **research-sop rescue budget** | 同上，`orchestrate_research(max_rollbacks=2)` | 第五十七条 rescue budget 的现成实现 | 超预算返回 `unresolved` |
| **research-sop negative result 终态** | 同上，`"unresolved"` | 第五十八条合法终点 | 已有语义 |
| **research-sop 角色分离** | 同上，五角色 + validator 回退 | 第三十七条 Builder/Runner/Validator/Auditor | validator 可 send back |
| **research-sop 严格完成判定** | 同上，`DELEGATE_SUCCESS_STATUS` / `ROLE_REQUIRES_DOCUMENT` | 第四条"不得用 almost passed 代替 PASS" | 明确拒绝把 `failed/cancelled/timeout` 当完成；缺文档则 `state="incomplete"` |
| **rollback 归档不可验证即中止** | 同上，`sop_rollback` | 第二十六条不可覆盖证据 | `"archiving {source} to {target} could not be verified; rollback aborted"` |
| **artifact 版本与 SHA-256** | `openai4s/server/artifact_refs.py`、`openai4s/server/artifacts.py` | `ArtifactManifest.hash` | 已有 `artifact_id / version_id / sha256` 与 `_PinnedVersionStage` |
| **benchmark case 声明式期望结果** | `openai4s/benchmark/model.py`、`runner.py`、`steps.py` | **adversarial calibration suite 的执行器** | `OUTCOMES` 已包含 `failure / recovered / permission_denied`，其注释即宪法附录 C 的思想："a benchmark that only measures success measures the half of the system nobody doubted" |
| **PINN 数学核心** | `pinns/main.py` 的 `grad_wrt`、`pde_residuals`、`CollocationSampler`、`BoundaryLayerPINN` | Poisson MVP 的实现基底 | 结构清晰，autograd 路径可直接复用 |
| **逐项 loss 记录** | `pinns/main.py` 的 `losses_to_float` + `log_row` | 第十一条（**S2 唯一 PASS 项**） | 已逐项落盘含权重 |
| **构建期哈希清单** | `LeoAIStudio-build/manifests/wheelhouse.json`、`tools/build_manifest.py` | 环境可复现性（第二十八条） | 已有成熟的 SHA-256 清单模式 |

---

## 7. 必须重构或废弃的模块

| 模块 | 处置 | 理由 |
| --- | --- | --- |
| `pinns/main.py` 的 `enforce_2d_boundaries` / `enforce_profile_boundaries` | **废弃**（不得进入新代码库） | 使图像显示模型未产生的边界满足性（第十七、三十一条） |
| `pinns/main.py` 的 `_enforce_parameter_display_order` | **废弃** | 用 `np.minimum/np.maximum` 制造单调性（第三十一、四十二条） |
| `pinns/main.py` 的 `smooth_final_fields` / `smooth_display_profile` / `_pchip_display` | **隔离**：只允许在明确标注 "DISPLAY ONLY — NOT EVIDENCE" 的图上使用，且必须同时输出未平滑原图 | 第三十一条 |
| `pinns/main.py` 的 `safe_value`（`nan_to_num`） | **重构**：NaN/Inf 必须抛出并终止 Run，记入 FailureRecord（`NUMERICAL` 类） | 第五十二条 |
| `pinns/main.py` 的 `profile_metrics` 参与训练停止判断 | **重构**：迁出训练循环，改为 holdout 上的诊断 | 第九条 validation leakage |
| `pinns/复现/autonomous_optimizer.py` | **整体废弃或重写** | 收敛判据为视觉评分（第二十、五十七、五十八条）；单次改 10+ 变量（第二十四条） |
| `pinns/main.py` 的 `AdaptiveLossBalancer.rebalance_for_pde_dominance` | **保留但必须记录**：每次改权重生成 DecisionRecord | 第二十五条不可静默修复 |
| `openai4s/benchmark` 的 `"status": "pass" if passed else "fail"` | **扩展**：加入 `BLOCKED` 与 `PARTIAL` | 第四条 |
| `results_discussion.txt` 生成逻辑 | **废弃** | 在无 validation 的情况下自动生成论文式结论（第五十五、六十三条） |
| `LeoAIStudio` 成品包中放置科研状态 | **禁止** | 该目录被 `assemble.ps1` 整体替换（第二十六条） |

---

## 8. 本轮明确**不应该**做的事（第四十四条）

| 不做 | 理由 |
| --- | --- |
| 不给 Maxwell-MHD 问题继续调参、加网络、加训练步数 | 第四十三条：上游解析 benchmark 未验证前，复杂问题只会掩盖问题 |
| 不做 PINN 的 UI / 可视化工作台 | 第四十四条：更漂亮不提高 specification / validation / reproducibility |
| 不接入更多 PDE 问题族 | 同上；先证明系统能拒绝一个坏解 |
| 不做多 GPU / 性能优化 / 训练加速 | 跑得更快只会更快地产出不可信结果 |
| 不做 PINN vs FEM 的性能比较 | 第三十二、三十三条：无可信 baseline 时的比较只能是 strawman |
| 不删除 `pinns/outputs_*` 任何内容 | 第二十一、二十六条：它们现在是失败证据 |
| 不重写 `results_discussion.txt` 让它"看起来更严谨" | 第五十九条：禁止修改历史以制造成功。应新增版本并标注原件已降级 |
| 不修改本宪法以让现有结果通过 | 第六十条：禁止 retroactive 修宪 |

---

## 9. 从现状到闭环 MVP 的最短路径

详见 `PINN_CLOSED_LOOP_MVP_PLAN.md`。摘要：

```
① 建立 domain object 骨架（复用 research-sop manifest 机制）
        ↓
② 解析 Poisson benchmark：-u'' = π²sin(πx), u(0)=u(1)=0, u* = sin(πx)
        ↓
③ Implementation Verification Gate（autograd + residual + 制造解）
        ↓
④ 独立 baseline（三点差分 FDM，含网格独立性）
        ↓
⑤ Validation Gate（relative L2 / L∞ / BC error / holdout residual）
        ↓
⑥ Adversarial calibration suite（1 good + ≥3 bad + ≥1 ambiguous）
        ↓
⑦ 只有 ⑥ 全部按预期 PASS/FAIL/BLOCKED，才宣布 MVP 成立
```

关键判据不是"Poisson 能不能解对"（那是容易的），而是：

$$
\boxed{
\text{Accept Good} + \text{Reject Bad} + \text{Abstain When Uncertain}
}
$$

---

## 10. 审计签署

| 项 | 值 |
| --- | --- |
| 本报告依据的宪法版本 | 1.0 |
| 审计结论 | S1 与 S2 **均为 pipeline，均不是科研闭环** |
| Gate 1 (SPEC) | **FAIL** → 所有下游 Gate `BLOCKED` |
| Stop-the-Line | **已触发** |
| 允许的下一步 | 仅限 `PINN_CLOSED_LOOP_MVP_PLAN.md` 中经批准的闭环基础设施建设 |
| 禁止的下一步 | 任何 Maxwell-MHD 新训练、任何基于现有产出的科学声明 |

**审计者声明：** 本报告中每一条 FAIL 均附有可复核的文件路径、行号或 JSON 字段。凡审计者未取得证据之处，已标记 `UNVERIFIED`，不得被解读为 PASS（第三十九条）。
