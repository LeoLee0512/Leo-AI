# 环形 Poisson 第 3 版正式尝试预注册（2026-09-26）

本文件在第 3 版运行**之前**提交，提交哈希即冻结点。运行后不得修改；任何偏离写入运行报告和 CHANGELOG。

## 1. 依据：所有者裁决（方案 B）

r2（`exp-geometry1-annulus-poisson-r2`，codeHash `b9f9e6def344…`）的情况：
- Gate 1–5 全部通过：Gate 4 10/10，dev 相对 L2 中位数 1.406e-4；C_physics、C_external 在 DAC-M1 上 PASS，DAC-M1 已 BURNT。
- 之后出了两处问题：
  1. `finish()` 生成声明判定时崩溃（`claim_gate` 调用写错）；
  2. 补全记录时发现信任向量无效：冻结规格登记的 PH10-momentumBudget、PH11-freeEnergy（均为 NOT_APPLICABLE）没有被记录。

所有者在 A（补记录）、B（作废 r2，修代码后按原方法重做第 3 版）、C（等待）中选择了 **B**。r2 的裁决记录在 `runs/exp-geometry1-annulus-poisson-r2/owner_ruling_void.json`（`record_r2_void.py`）。**r2 的数字不是 r3 的证据，不得与 r3 合并。**

## 2. 与 r2 的差别

方法**不变**：网络、优化器、240k 步、学习率在前 120k 步衰减后保持、batch、collocation、评估集、阈值、物理阈值、签名判据、G6 容差（|Δmedian| ≤ 1e-4 且 ≤ 0.5 × median_A，k/N 判定必须一致，复现种子偏移 10000），都与 r2 相同。r2 的结果**没有**被用来调整任何东西。

变化只有以下几项：

| 项 | r2 | r3 |
| --- | --- | --- |
| 配置 | `exp_annulus_r2_240k.json` | `exp_annulus_r3_240k.json` |
| 种子基数 init/sample/batch | 20263200/300/400 | **20263500/600/700**（与 r1、r2 及其复现种子都不相交） |
| claim 成员 | DAC-M1（BURNT） | **DAC-M2**（预注册给第 3 版，从未 SEALED） |
| 驱动（属于代码身份） | `run_formal_annulus_r2.py` | `run_formal_annulus_r3.py` |
| 代码 | 有缺陷，见 §3 | 已修正，codeHash 会变 |

specHash 仍为 `4c8dfbc7…`：r3 的 ProblemDefinition 与 r1 相比，只改了 revision 和 claim 条目；frozenAt 沿用 r1 的值，理由与 r2 相同。

## 3. 代码修正（均在 `pinn/` 内，属于新的代码身份）

1. `gates_annulus.physics_checks` 记录 PH10、PH11 两项「不适用」（理由取自冻结规格原文）。测试逐项核对：登记的每项检查都有某个 Gate 输出。
2. 信任向量改为 schema 1.2 布局（与 2D 相同），写出前先对照冻结规格校验。
3. 声明判定改为 schema 1.2，由唯一的 `build_decision` 构造（与 2D 的 `decision_document` 相同），**先校验、后写入**。尝试本身、预检和收尾步骤共用这一个构造函数。
4. **打开前预检**：Gate 5a 判定之后、DAC-M2 被 OPENED 之前，用当时已有的维度（external、repro 此时为 NOT_CHECKED）构造信任向量和判定并完整校验，不通过就停止，**不会烧掉盲测集**。r2 事后发现的三类问题（调用、布局、漏记登记检查）在这个时点都能查出来。
5. 收尾模块（Tier-1 合并、G6）使用同一套构造与校验；判定 ID 的后缀用 `-`（schema 只允许 `[a-z0-9-]`）。
6. 驱动中的复现尝试 ID 改为小写 `…-repro-envb`（runId 只允许小写；r2 的写法会在复现训练完成**之后**崩溃）。

## 4. 启动前的沙盒全链冒烟（已完成）

在临时的干净 git 工作树里（真实实验目录、台账、样本登记都不受影响），用正式驱动加小配置跑完整条链：
- 小配置：10 个种子，300 步；阈值和容差放宽；沙盒自己的 claim 成员；
- 真实的 Env B 子进程负责复现；
- Gate 5 的 APPLICABLE 检查在进程内强制判 PASS，因为 300 步的模型不可能达到真实阈值；检查清单本身仍由真实代码生成。

冒烟查出并修正了第 3 节的第 5、6 两项。修正后：
- 普通运行：Tier-1 降级，G6 PASS 但被保留在 REPRODUCIBILITY_CHECK 并写明原因——走通了降级路径；
- 额外强制 Tier-1 为 PASS：状态进入 ACCEPTED，允许 C0–C2——走通了接受路径。

沙盒随后删除。**冒烟只证明代码路径能走通，不是证据。**

## 5. 执行

- 主尝试：CPU，10 个种子各用 1 个进程（`--workers 10`），并行结果与顺序执行逐位相同。
- 只有 Gate 5 PASS 后，才**同时**启动：
  - Tier-1：8 次扰动重训，在本进程的进程池中运行；
  - Env B 独立复现：子进程，同一 codeHash，种子偏移 10000，只跑到 Gate 4。

  两者互不依赖，同时运行可以缩短总时长；每个训练仍是单线程、确定性的。
- 然后依次：合并 Tier-1（只允许维持或降级）→ 判定 C_repro → 应用 G6。只有 G6 PASS 且 C2 判定已签署，才进入 ACCEPTED；否则停在 REPRODUCIBILITY_CHECK 并写明原因。
- 链条报告：`runs/exp-geometry1-annulus-poisson-r3-CHAIN_REPORT.json`，其中记录收尾时的 codeHash。
- 运行期间请求系统不睡眠，不做断点续跑；中断即记为中断。

## 6. 终止准则与抢救预算

- **抢救预算：1 次。** 任一 Gate 判为 FAIL、PARTIAL 或 BLOCKED，按规则记录后链条就停下，不原地重训、不换种子。
- DAC-M2 一旦打开即 BURNT。
- 失败或记录异常之后怎么做，由所有者决定。我不自行开第 4 版，也不启动新的 PDE。

## 7. 沿用的注意事项

- Tier-0 未实现（与 1D/2D 先例相同）。
- r1 的根因仍未定。r3 的结果不能倒推为 r1 的根因证据。
- 旧的 1D 局部化统计量在 d ≥ 2 时只作诊断。
- ProblemDefinition schema 没有 annulus 词汇（修订候选，仍未修补）。
- 另有一个进程在同一台机器上运行（`gate5_pilot`，WSL，不属于本实验）。它只会影响运行时长，不影响结果：训练是单线程、确定性的。
