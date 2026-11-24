# 环形 Poisson 第 2 版正式尝试预注册（2026-09-26）

本文件在第 2 版运行**之前**提交，提交哈希即冻结点。运行后不得修改本文件；任何偏离写入运行报告和 CHANGELOG。

## 1. 依据：所有者裁决

r1（`exp-geometry1-annulus-poisson-r1-gpu`）于 2026-09-26 按所有者决定以 rUndetermined 停线（STOPPED_THE_LINE，根因未定，四个候选原因均未排除）。停线后，所有者在同一天作出以下裁决：

| 事项 | 裁决 |
| --- | --- |
| 训练预算 | 240k 步（不采用 180k 的最小规则） |
| 种子 | 换一套新种子 |
| specHash | 保持不变 |
| 执行方式 | CPU 满负荷并行，一次跑完整条链 |

## 2. 与 r1 的差别（只有这些）

| 项 | r1 | r2 |
| --- | --- | --- |
| 配置 | `configs/exp_annulus_baseline.json` | `configs/exp_annulus_r2_240k.json` |
| `optimizer.steps` | 120000 | 240000 |
| `optimizer.lrPrefixSteps` | 无（学习率衰减绑定总步数） | 120000：前 120k 步的学习率轨迹与 r1 完全相同，之后固定在 `finalLr` |
| 种子基数 init/sample/batch | 20261400 / 20261500 / 20261600 | 20263200 / 20263300 / 20263400 |
| claim 成员 | DAC-M0（已 BURNT） | DAC-M1（预注册给第 2 版，此前从未 SEALED） |
| 驱动脚本（属于代码身份） | `run_formal_annulus.py` | `run_formal_annulus_r2.py` |

以下各项与 r1 相同：
- 网络、优化器（Adam，lr 1e-3 → 1e-5）和 batch 512；
- 线程数为 1，collocation 集和各评估集（train、dev、phys）；
- ε_spec = 1e-3，10 个种子，worst-seed 因子 3.0，离散度限 1.0；
- 物理阈值、签名判据，以及 G6 容差（|Δmedian| ≤ 1e-4 且 ≤ 0.5 × median_A，k/N 判定必须一致，复现种子偏移 10000）。

**偏离说明：** 最小规则建议 180k 步；所有者裁定用 240k 步。这是事前决定，与任何 r2 结果无关。

## 3. specHash 保持不变

`problems/pdef-annulus-poisson-v1-r2.json` 由 r1 的 ProblemDefinition 生成，只改了两处：`revision = 2`，claim 条目改为 DAC-M1（`d2136f59…`）。这两个字段本来就不参与 specHash 计算。

`frozenAt` 也参与 specHash，因此保留 r1 的 `2026-09-17T07:21:11Z`。它的含义是：规格仍是 r1 冻结的那一份，没有重新冻结。

两版的 specHash 都是 `4c8dfbc7…`，由测试 `test_annulus_r2_preparation.py` 核对。

配置变了，驱动脚本也变了，所以 codeHash 会与 r1 不同。这符合预期：方法的执行预算属于代码身份，不属于问题规格。

## 4. 执行（执行参数，不进入配置和 codeHash）

- 主尝试：CPU 训练，10 个种子同时开 10 个进程（`--workers 10`），每个进程 1 个线程。并行结果与顺序执行逐位相同，由 `test_annulus_parallel.py` 在 torch 解释器下验证。
- 链条（`run_formal_annulus_r2.py`）：
  1. 正式尝试（Gate 1–5）；
  2. 只有 Gate 5 PASS 时才运行 Tier-1 红队（8 次扰动重训，并行），然后合并结果——只允许维持或降级；
  3. 在 Env B（独立的 CPU 版 torch 环境，路径作为参数传入）运行复现尝试：同一 codeHash，种子偏移 10000，只跑到 Gate 4；
  4. 判定 C_repro，然后应用 G6。
- 只有 G6 PASS 且 C2 ClaimGateDecision 已签署时，才进入 ACCEPTED；否则停在 REPRODUCIBILITY_CHECK，并写明原因。
- 防睡眠：用 `SetThreadExecutionState` 请求系统不睡眠。不做断点续跑。如果运行中断，本次尝试记为中断，重跑用新的 attempt ID（先例：stopped-gpu）。

## 5. 终止准则与抢救预算

- **抢救预算：1 次尝试。** r2 在任一 Gate 判 FAIL、PARTIAL 或 BLOCKED 时，按规则记为 FAILURE_RECORDED，链条就停在那里。不在原位重训，也不换种子重跑。
- DAC-M1 在 Gate 5 打开后即 BURNT。无论结果如何，都不能再用于第 2 版。
- r2 失败后，下一步由所有者决定。我不会自行启动新一轮，也不会启动新的 PDE。

## 6. 沿用的注意事项

- **Tier-0 未实现**，与 1D/2D 先例相同。本次不补，报告中照实写明。
- r1 的根因仍未定。r2 的结果（无论通过还是失败）都不能倒推为 r1 的根因证据：r2 同时改了预算、学习率保持和种子三项，无法单独归因。
- 旧的 1D 局部化统计量（max/median bin > 3.0）在 d ≥ 2 时仍未校准，只作诊断记录，不参与判定。
- ProblemDefinition schema 没有 annulus 词汇（目前用 domainType "other"），这是修订候选，本次不修补。
