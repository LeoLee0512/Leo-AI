# Pilot-Role Annotation（2026-09-16，2D 轮次追加审计）

用户指令：正式记录本轮 EXPLORATORY pilot 实际同时承担了**冻结前的架构可行性 / 模型选择**（3×32、4×64、4×128 等档），使用的是非 claim 的 development/pilot 数据，发生在正式预注册与 spec 冻结之前；核对宪法 1.2 是否允许；允许则追加注解（**不修改历史预注册文件**），不允许则标记 BLOCKING 并停止 C2 声称。

本文件是**追加注解**。`experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md` 与 `pilot/PILOT_RESULT.json` 一字未改。

## 1. 事实（机器记录，不是回忆）

`experiments/poisson2d/pilot/PILOT_RESULT.json`：

```text
marking            EXPLORATORY
claimEligibility   <= C1
formalEvidence     false
evaluationSets     trainPool 2048 uniform interior points default_rng(20260917)
                   dev       1024 uniform interior points default_rng(20260918)
                   claim     not touched
seeds              init 20260800 / sample 20260810 / batch 20260820（与正式 seed 基数 20260920 / 20261020 / 20261120 不相交）
```

五档实测（单 seed 三元组，只在 D_dev 上评估）：

| 档 | 参数量 | dev 相对 L2 | 单 run 耗时 |
|---|---|---|---|
| 3×32 / 6000 步 / batch 256 / 1024 配点（1D 架构原样移植） | 2,241 | 6.049e-04 | 42 s |
| **4×64 / 10000 步 / batch 512 / 1024 配点（选中）** | 12,737 | **4.270e-05** | 197 s |
| 4×64 / 20000 步 / batch 1024 / 2048 配点 | 12,737 | 2.073e-05 | 703 s |
| 5×64 / 20000 步 / batch 1024 / 2048 配点 | 16,897 | 4.701e-05 | 851 s |
| 4×128 / 20000 步 / batch 1024 / 2048 配点 | 50,049 | 5.809e-06 | 2017 s |

用途（如实陈述，不美化）：**这次 pilot 同时承担了两件事**——(a) PART 4 授权的性能 / 可行性测量（CPU 实用性、batch、内存、运行时）；(b) **架构与训练预算的选择**（在五档之间选一档）。第二项就是"model selection"，本注解正式登记这一点。

选择规则在读取第 3–5 档结果之前写定，并写进预注册第 5 节：*取最小的、D_dev 误差比 ε_spec 低一个数量级且 10 seed 成本 < 1 小时的档*。按此规则：1D 架构 6.049e-04 对 ε_spec = 1e-3 只有 1.65 倍余量 → 淘汰；4×64/10000 步 4.270e-05（23 倍余量，197 s）→ 选中。选择只用 D_dev 数字与墙钟时间，未触碰 claim 集。

## 2. 宪法 1.2 条款核对

| 条款 | 原文要点 | 对本轮的判定 |
|---|---|---|
| 第 561 行（数据三分） | "**D_dev**（诊断、调参、失败分析、**模型与架构选择**、早停、扰动实验、区分实验都只准看它）" | **明文允许**：模型与架构选择是 D_dev 的登记用途之一。pilot 只看 D_dev 与 D_train 池，claim 集 `not touched`。 |
| 第 561 / 563 行（互斥） | 训练可见样本 ∩ (D_dev ∪ D_claim ∪ D_phys) = ∅；D_dev ∩ D_claim = ∅ | pilot 用的 train 池与 dev 集由与正式 run 相同的生成规则与种子产生，正式 run 的 T9 在样本级复核互斥并 PASS。 |
| 第 565 行（claim 集） | "打开"包括在 D_claim 上计算任何聚合统计，以及人看了结果再做决定 | pilot 从未在 D_claim 上求值；claim pool 在 pilot 结束后才密封（`ad9f029`），正式 run 才打开其中一套。**无违反**。 |
| 第 622 行（多 seed） | N 与 ε_spec 预注册，事后不得改；最好 seed 永不进入判定 | ε_spec = 1e-3 是 1D 继承的 AC2D-1 阈值，写在 `poisson2d_contract.py` 与预注册表内，事后未改。pilot 是单 seed 的可行性探针，**不进入任何判定**；正式判定用 10 个独立 seed 三元组。 |
| 第六十五章（EXPLORATORY 第二来源） | 在 D_dev 上产生的观察默认 EXPLORATORY；封顶 C1；产物不进入 ACCEPTED；**晋升必须在冻结规格下重新走完整闭环** | pilot 自标 EXPLORATORY、claimEligibility ≤ C1、`formalEvidence: false`，产物不在任何 attempt 目录内、无 RunRecord、不进状态机。晋升方式正是该条要求的：冻结规格（specHash `05328d507582`）→ 密封盲集池 → 用不相交的 10 个正式 seed 重新走完 G1–G6。**符合**。 |
| 第 1132 行（28.1） | "**正式 run** 的机器契约是 RunRecord" | pilot 不是正式 run，不承担 RunRecord 义务；其不完整登记不构成违规。 |
| 第六十六章（1941 行） | 架构、优化器、采样、loss 权重在 **codeHash** 内；阈值、seed 协议、D_train/D_dev 在 **specHash** 内 | 架构选择落在冻结配置 `exp2d_baseline.json` 内，该文件进入代码清单，正式 run 的 codeHash `a39aa07e23d0` 由校验器复算。冻结后未改。 |

## 3. 裁决

```text
PILOT ROLE:
ALLOWED UNDER CONSTITUTION 1.2

依据：第 561 行明文把"模型与架构选择"列为 D_dev 的许可用途；第六十五章允许 EXPLORATORY 的观察，
      并要求晋升时在冻结规格下重走完整闭环——本轮正是这样做的。

NOT BLOCKING for C2。
```

## 4. 同时登记的三点诚实说明（不影响裁决）

1. **一次 pilot 承担了两种角色**（性能测量 + 模型选择）。PART 4 的授权文本只点名了性能用途，对模型选择既未授权也未禁止；宪法层面由第 561 行覆盖。若评审希望把二者拆成两次分别标记的 EXPLORATORY 活动，那是**协议澄清候选**（PROTOCOL CANDIDATE），不是本轮的违规，也不在本轮自行起草。
2. **阈值与 pilot 的先后**：AC2D 阈值是 1D 继承常数，其定义与来源写在 `pinn/governance/poisson2d_contract.py`（首次提交后至今未改动，可由 `git log -- pinn/governance/poisson2d_contract.py` 机械核验）。pilot 的作用是确认该阈值在 2D **可达**，不是用 pilot 数据反推阈值。预注册第 6 节对 AC2D-1 已如实写明"可达性由 pilot 在 D_dev 上事前确认"。
3. **pilot 与正式 run 的 seed 严格不相交**（20260800/10/20 对 20260920/20261020/20261120），因此不存在"挑 seed"的通道；正式 run 的 10 个三元组在训练前写入 `seed_ledger.json`。

## 5. 不做的事

不修改预注册、不修改 `PILOT_RESULT.json`、不重跑 pilot、不改阈值、不重开 D_claim。本注解只追加。
