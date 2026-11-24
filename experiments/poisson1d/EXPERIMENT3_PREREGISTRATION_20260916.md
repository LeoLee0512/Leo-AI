# Experiment 3 预注册：claim 集身份修复、BC 诊断、最小修订、新盲验证、Tier-1、G6（2026-09-16）

写定并提交于任何 3A/3B run 之前。宪法 1.2 不变；本文件只做协议澄清与预注册，不起草修正案。实验 1/2 的机器记录不改，只追加 `POST_AUDIT_ANNOTATION.md`。

## 1. Claim 集身份（PART 1）

- `artifactHash = canonical_sha256(清单)`；`sampleSetHash = canonical_sha256(sorted(sampleId))`（`evaluation_sets.sample_set_hash`）。烧毁按 sampleSetHash（账本 L4s/L6/L7/L8，`claim_set_ledger.py`；`validate_problem_definition` 拒绝已打开样本的重新包装）。判定：这是宪法 9.1"打开过的 claim 集"的**实现 bug / 协议澄清**，不是宪法语义变更（宪法说的是"claim 集"，实现误用了 artifact 字节哈希）。
- 已烧毁：sampleSetHash `91414bd5260e…`（GL512 ∪ CGL2000 去端点；实验 1 打开，实验 2 重新包装后再次打开——见 exp2-revised-r1/POST_AUDIT_ANNOTATION.md）。

## 2. Claim pool（协议澄清：claim 网格族）

v1.0 协议只列了网格族的一个实例（GL512/CGL2000），可信校验器与之硬绑定。AC-1..AC-8 的**定义与阈值不变**；claim 网格族 = {Gauss–Legendre 阶 n 节点（numpy leggauss 映射到 [0,1]）} ∪ {CGL m 节点去端点}。预注册 pool（对 problemId `pdef-poisson1d-cal-v1`）：

| 集 | 构成 | 预定 revision |
|---|---|---|
| D_claim_0 | GL512 ∪ CGL2000（BURNT） | r1（已用） |
| D_claim_1 | GL640 ∪ CGL2400 | r2 |
| D_claim_2 | GL768 ∪ CGL2800 | r3 |
| D_claim_3 | GL896 ∪ CGL3200 | r4 |

要求（机器判定，pool manifest 记录）：两两样本互斥；与 D_train / D_dev / D_phys 互斥（minSeparation 1e-9）；反碰撞 min|v − i/d| > 1e-12（d ≤ 64）；全部 SEALED 直到消费；revision r 只能消费 D_claim_{r−1}，G5 FAIL 后该集 BURNT；不得看着 D_claim 调参。评估器：`pinn/experiments/claim_metrics.evaluate_on_grids`，与 `evaluate_samples` 在冻结网格上逐位一致（测试 `test_claim_metrics_matches_trusted_validator`）。

## 3. 干预准则（PART 11，先于 3A 冻结）

`pinn/experiments/criteria.paired_intervention_errors`：配对 seed 三元组，N ≥ 10；相邻档 median(E_high)/median(E_low) < ρ = 0.5（来源：协议汇编 §4 P23 已用的"< 0.5"倍数规则——一个真正起作用的因子在一个预注册十进档内至少把误差减半）；配对改善比例 ≥ q = 0.8（来源：宪法 10.1 的 k/N 0.8 线；N=10 时 H0 p=0.5 下 ≥ 8/10 的单侧概率 0.055）。宪法 3.2 的"≥3 档 × ≥3 seed、中位严格下降"仍是最低要求，本准则只更严。不回溯实验 2。

## 4. Experiment 3A — P24 软 BC 权重干预

- 唯一变量 λ_BC ∈ {10, 100, 1000}（含现行 10；其余两档在此预注册，运行后不加档）。
- 固定：架构 3×32 tanh、identity 参数化、Adam 1e-3→1e-5、6000 步、batch 128、256 配点、pool、seed 协议（同一组 10 个正式三元组，配对）、PDE、参考、阈值。
- 记录每 seed 每档：BCError = max(|u(0)|,|u(1)|)；PDEError = D_dev 归一化 holdout 残差 RMS；SolutionError = D_dev 相对 L2。全部只用 D_dev / D_phys。
- 判读规则（事前）：BC 改善按第 3 节准则（方向：λ ↑ ⇒ BCError ↓）；"不可接受退化" = SolutionError 或 PDEError 的中位数在高档超过预注册阈值（ε_spec 1e-3 / AC-4 1e-2）或高档中位数 > 2 × 低档中位数。

## 5. Experiment 3B — P28 硬 BC（独立干预）

- u = x(1−x)N(x)（`network.outputParameterization = "x(1-x)N"`），改变假设类 / 执行方式；其余一切与基线相同（含 λ_BC = 10，此时 bc 项恒为 0）；同一组 10 个配对 seed。
- 记录同上三项。判读：BCError 按构造 0；关注 SolutionError / PDEError 是否仍可接受。

## 6. 根因判定规则（PART 4，事前）

候选 = 1.2 矩阵 sBcResidual 行：rSpecDefect, rDataDefect, rImplementationDefect, rOptimizationFailure, rSamplingDeficiency, rCapacityLimit, rSingularityTreatment。
- 若 3A 满足准则且高档无不可接受退化 → 支持 rOptimizationFailure（loss 权衡属训练 / 优化协议，G4）；容量、采样、实现、规格、数据、奇异性各以 3A/3B/G2/G3 实测排除（同一架构 / 同一采样 / 同一代码在高 λ 或硬 BC 下达标 → 容量 / 采样 / 实现被排除；BC 数据 g=0 与 T4 → 数据 / 规格；u* ∈ C∞ → 奇异性）。
- 若 3A 不满足准则而 3B 达标 → 软执行本身不足：规格已明示 enforcement = soft，改为 hard 是规格变更 → rSpecDefect（G1），前提是 3B 同样排除其余候选。
- 若两者都不达标或互相矛盾 → rUndetermined，STOP_THE_LINE。

## 7. 修订规则（PART 5，事前）

- 若 rOptimizationFailure：只改 `lossWeights.bc`，取**满足准则且每 seed BCError < AC-3 的最小预注册档**；若无档满足"每 seed < AC-3" → 不修订为软权重，回到第 6 节第二支或 rUndetermined。
- 若 rSpecDefect：只改 `boundaryConditions[].enforcement = hard` 与对应 `outputParameterization`，其余不变；新 specHash，revision 2。
- 禁止顺手改：网络、优化器、步数、采样、ε_spec、seed。

## 8. 重入与新盲 G5（PART 6–7）

按根因路由（G4 或 G1）`reenter`；train 及下游重置；revision 2 消费 D_claim_1（SEALED → OPENED → BURNT，记 sampleSetHash、artifactHash、revision、codeHash、时间）。若 FAIL → 新 FAILURE_RECORDED，下一次用 D_claim_2，不得对 D_claim 调参。

## 9. Tier-1 Red Team（PART 8，事前）

只用 D_dev，seed 三元组 0，各一次重训；基线 = revision 2 的正式 seed-0 run。度量：e2 = D_dev 相对 L2，Δq = |QoI-1' − QoI-1| / QoI-1（QoI-1 = ∫u，在 D_phys GL256 上），残差 max 于 D_dev。阈值（沿用 Red Team 交付物示例值，在此正式预注册）：Δq ≤ 1% 维持；1%–5% PARTIAL；> 5% FAIL；P4 另：残差最大值随 dtype 变化超一个数量级 → C_impl FAIL；P8：映射回原尺度后 Δq > 1% → C_math FAIL。只能维持或降级。

| P | 改动 | 固定 | 预期失效模式 | Poisson 适用 |
|---|---|---|---|---|
| P1 | 采样 seed 换为 20261000+900（同池重抽） | 其余全部 | 结果依赖具体配点 | ✓ |
| P4 | dtype float32 训练；残差用 float64 重算 | 其余全部 | 二阶导数值病态 | ✓ |
| P6 | 随机删 10% 配点 | 其余全部 | 依赖个别点 | ✓ |
| P7 | 边界邻域加密 | — | 边界层欠分辨 | ✗ NOT_APPLICABLE：Poisson 1D 无边界层，BC 只在两个精确端点评估，邻域密度不改变 BC 项（Red Team 交付物 §5 假设） |
| P8 | 域尺度 L = 2（y = 2x，v(y) = u(y/2)，f_L = π²/4 sin(πy/2)），结果映射回 [0,1] | 其余全部 | 缩放 / 反缩放错误 | ✓ |
| P9 | Adam → L-BFGS（同函数评估预算） | 其余全部 | 损失面多模态 | ✓ |
| P11 | 残差高区域局部加密 | — | 局部误差集中 | ✗ NOT_APPLICABLE：无 sLocalizedError 观察，残差自适应加密面向 CFD 目标（Red Team §5） |
| P16 | 激活 tanh → sin | 其余全部 | 谱偏置 | ✓ |

## 10. G6（PART 9）

本机只有一个装有训练框架的安装（mamba 前缀）。若无第二环境：C_repro = BLOCKED，C2 = BLOCKED；生成可搬运的 reproduction package（spec、codeHash、依赖锁、seed 清单、数据集生成规则、容差、运行说明、schema）。容差（预注册）：复现 run 的 dev 相对 L2 中位数与原 run 之差 ≤ 1e-4 且 k/N 判定一致；claim 集不重开（复现只在 D_dev 上比较，C_repro 的对象是训练可靠性结果）。

## 11. 事前披露

- 3A 高档 λ 可能使 PDE 残差项相对变弱；这正是第 4 节要记录的 trade-off。
- 若 3A/3B 都显示达标，按第 6 节第一支归因（优化协议），不因硬 BC "更漂亮"而改规格。
- 本轮不进入 2D；不新增 Gate / 状态 / 枚举。
