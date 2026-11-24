# EXPERIMENT ANNULUS PREREGISTRATION（Geometry Lift 1，2026-09-17）

本文件在**任何正式 run 之前**提交。冻结后不得修改方法（PART 12）：架构、训练、指标、阈值、claim pool、Red Team 适用性、G6 容差、代码身份一次性冻结；若正式 attempt 暴露代码 bug，按现行 revision 规则处理，不得修完假装同 revision。

## 0. 问题与几何

```text
Omega   = { (x, y) : a^2 < x^2 + y^2 < 1 },  a = 0.35   （曲边、内孔、多连通、两条边界组件）
PDE     -Lap u = f in Omega,  u = 0 on r = a and r = 1
u*      = h g,  h = (1 - s)(s - a^2),  g = 1 + 0.2 sin(pi x) cos(2 pi y) + 0.1 x - 0.1 y,  s = x^2 + y^2
f       = -Lap u*   （解析写死，见第 2 节；运行时不现算）
geometryId  annulus-a035-R1-v1
```

`g` 刻意**非径向**：只处理半径的错误实现无法侥幸通过；同时圆环的旋转对称**不是解的对称性**，因此 x/y 互换对称检查登记 NOT_APPLICABLE（PART 20），不制造假对称。

## 1. 几何合同（machine-readable）

`pinn/geometry/annulus.py` 的 `GEOMETRY`：

| 项 | 值 |
|---|---|
| geometryType | annulus |
| outerBoundary | center (0,0), radius 1，identity `x^2+y^2=1`，**外法向 (x, y)** |
| innerBoundary | center (0,0), radius 0.35，identity `x^2+y^2=a^2`，**外法向 −(x, y)/a（指向洞内）** |
| domain membership | `a^2 < x^2 + y^2 < 1`（两条边界均**不属于**内部） |
| 等面积变量 | `t = (r^2 − a^2)/(1 − a^2) ~ U(0,1)` |
| 求积雅可比 | `dx dy = ((1 − a^2)/2) dt dtheta`（常数） |

## 2. 解析源项与双重验证（PART 4）

```text
h'(s) = 1 + a^2 - 2s          Lap h = 4(1 + a^2) - 16 s
grad h = 2 h'(s) (x, y)       Lap g = -pi^2 sin(pi x) cos(2 pi y)   （= -5 * 0.2 * pi^2 * ...）
f = -[ g (4(1+a^2) - 16 s) + 4 (1 + a^2 - 2 s)(x g_x + y g_y) + h Lap g ]
```

- **Verification A**（独立解析实现）：`pinn/reference/analytic_annulus.py` 的 `laplacian` 与有限差分二阶差商在多点上一致（测试钉死，rel 1e-5）。
- **Verification B**（AD）：torch 对 `u*` 求二阶导，`max |-Lap u* - f|` 在 2000 个独立面积均匀点上 **5.33e-15**（预注册容差 **1e-12**），梯度与解析梯度差 6.66e-16。
- 解析源项与 PINN 残差**不共用** helper：参考模块是纯 Python，不 import torch。

## 3. 硬边界（PART 5）

```text
u_theta(x, y) = (R^2 - s)(s - a^2) N_theta(x, y)
```

两条边界按构造为零（实测 outer 3.5e-17 / inner 4.9e-18；P8 缩放下 4.97e-16 / 6.99e-17）。本轮**不重新比较 soft BC**。

## 4. 数据集（PART 13）

| 集合 | 构造 | 规模 |
|---|---|---|
| D_train pool | 面积均匀：`r = sqrt(a^2 + (1-a^2)U)`、`theta = 2 pi V`，`numpy.default_rng(poolSeed)` | 见配置 |
| D_dev | 同规则、独立 seed | 1024 |
| D_phys | 几何原生求积：面积分数 t 上 Gauss–Legendre × theta 上梯形（周期谱精度） | radialOrder × angularCount |
| 边界集 | 两条组件各自等角节点 + 权 `r·2π/count`，各带**自己的外法向**；spec-known，identity 豁免 | 每条 64 |
| D_claim pool | 四个成员，各自「旋转后的几何原生求积网格」+「面积分数上的内部 CGL × 旋转角度」点集 | 见第 6 节 |

采样实现验证（**不是科学 Claim**）：`t` 的经验分布对 U(0,1) 的 Kolmogorov 统计量 < 1.95/√n，且 r-均匀的错误采样必须被这条检查判出（测试钉死）。

## 5. 架构与训练（PART 11）

架构**原样沿用**已在 square-2D 校准中验证过的基线，唯一改动是**步数**（见 5.2），理由与证据在冻结前写定：

```text
MLP         input 2 -> 4 hidden layers x width 64 -> 1，tanh
optimizer   Adam，lr 1e-3 -> 1e-5 指数衰减，batch 512
dtype       float64，deterministic，threads 1
pool        2048（沿用）        collocation 1024（沿用，见 5.2 事实一）
steps       120000             <- 与 square-2D 唯一不同的方法值
```

### 5.1 EXPLORATORY smoke（PART 11.1，只用 D_dev，claim pool 尚未密封）

| 探针 | 配点 | 步数 | dev 相对 L2 | 归一化残差 | 单 seed 耗时 |
|---|---|---|---|---|---|
| 原样沿用 square 配置 | 1024 | 10000 | 9.94e-03 | 4.14e-02 | 119 s |
| 密度匹配 | 2823 | 10000 | 1.05e-02 | 4.52e-02 | 119 s |
| 密度匹配 + 双步数 | 2823 | 20000 | 5.43e-03 | 2.53e-02 | 236 s |
| 密度匹配 + 四倍步数 | 2823 | 40000 | 2.36e-03 | 9.36e-03 | 441 s |
| **沿用配点 + 四倍步数** | **1024** | **40000** | **2.23e-03** | **8.10e-03** | **403 s** |

标记 EXPLORATORY、claimEligibility ≤ C1、formalEvidence false、seed 20261200/10/20（与正式基数 20261400/20261500/20261600 不相交）。

### 5.2 步数变更的理由（PART 11.1 要求留痕）

- 事实一：**密度不是原因，配点数也不是**。把配点按面积放大 2.76 倍，10000 步时误差不降反微升（9.94e-03 → 1.05e-02），40000 步时两者几乎相同且沿用值略好（2.23e-03 vs 2.36e-03）且更省时。因此配点数**保持 square 原值 1024**：没有证据支持改它，就不改。
- 事实二：**这是优化预算受限**。步数每翻倍，误差与残差都约降 2.1 倍（9.94e-03 → 5.43e-03 → 2.36e-03）。
- 事实三：沿用的预算使 dev 相对 L2 比继承阈值 ε_spec = 1e-3 高约一个数量级，归一化残差比 ACA-4 阈值 1e-2 高约 4 倍 —— 即**冻结的 square 预算在本问题上不可行**，正是 PART 11.1 允许在冻结前变更的情形。
- 处理：**只改步数**，不改架构、不改优化器、不改 batch、不改配点数、不做架构搜索、**不改任何阈值**。按实测标度外推，冻结 **steps = 120000**，预期 dev 相对 L2 约 **7e-04**，即对 ε_spec 只有约 **1.4 倍余量**（square 校准当时是 23 倍）——余量小这件事如实记录，不靠动阈值来买。单 seed 约 20 分钟，10 seed 约 3.4 小时。
- 用户裁决（2026-09-17）：提高步数后冻结；**若最终仍达不到 1e-3，如实 FAIL，绝不动阈值**。

## 6. Claim pool（PART 14）

四个成员，全部为圆环新建（**不复用**正方形的任何点）：

| 成员 | 求积网格（积分类判据） | 点集网格（ACA-2 / ACA-9） | 指定 revision |
|---|---|---|---|
| DAC-M0 | GL34 × 125 角，偏转 0.011 | CGL50(t) × 33 角，偏转 0.007 | r1 |
| DAC-M1 | GL36 × 127 角，偏转 0.013 | CGL54(t) × 35 角，偏转 0.009 | r2 |
| DAC-M2 | GL38 × 129 角，偏转 0.017 | CGL56(t) × 37 角，偏转 0.011 | r3 |
| DAC-M3 | GL42 × 131 角，偏转 0.019 | CGL60(t) × 39 角，偏转 0.013 | r4 |

角向计数两两互素且各带不同偏转角 → 成员之间、成员与 D_phys 之间都不可能共享节点（测试与登记时的实测共享数均为 0）。生命周期沿用已修好的 `sampleSetHash` + 账本推导（SEALED → OPENED → BURNT）；runner 的早期护栏在**任何训练之前**查账本，不采信 manifest 的静态 status 字段。

## 7. 验收判据与几何判定（PART 17）

| 判据 | 阈值 | 等级 | 几何判定 |
|---|---|---|---|
| ACA-1 相对 L2（圆环求积） | 1e-3 | MUST | INVARIANT（定义）/ SENSITIVE（可达性与求积） |
| ACA-2 相对 L∞（点集网格） | 5e-3 | MUST | INVARIANT（定义）/ SENSITIVE（网格） |
| ACA-3 两条边界上的 max\|u\| | 1e-4 | MUST | SENSITIVE（两条组件而非一条的四条边） |
| ACA-4 残差 RMS / F_RMS | 1e-2 | MUST | SENSITIVE（归一化用**圆环自己的** F_RMS = 6.2631…） |
| ACA-5 \|∫u − ∫u*\|/\|∫u*\| | 1e-3 | MUST | SENSITIVE（∫u* = π(1−a²)³/6，已数值核验） |
| ACA-6 两条组件的 \|∂u/∂n − ∂u*/∂n\| / max\|∂u*/∂n\| | 5e-3 | MUST | **NEW-GEOMETRY**（内法向指向洞内） |
| ACA-7 能量恒等式 | 1e-2 | MUST | INVARIANT（定义）/ SENSITIVE（圆环积分） |
| ACA-9 局部：64 个等面积单元的最大单元 RMS 误差 / 参考解 RMS | 1e-3 | MUST | **NEW-GEOMETRY**（笛卡尔分块会跨越洞） |
| ACA-8 相对 H1 半范 | 5e-3 | SHOULD | INVARIANT / SENSITIVE |

阈值全部在正式 run 前冻结；**看到结果之后不得修改**。

## 8. 局部误差判据与症状触发（PART 15）

```text
partition   4 个等面积径向环（t 均匀）× 16 个角向扇区 = 64 个等面积单元
statistic   maxCellRmsErrorOverReferenceRms
criterion   ACA-9 <= 1e-3
trigger     d >= 2：sLocalizedError 触发 <=> 该预注册局部验收判据失败
seedPolicy  every-seed（即 Gate 5b 对 MUST 判据一贯执行的 all(...)）
evaluation  只读 D_dev；claim 集永不用于诊断或自适应调参
invalid     NaN / ±Inf / 负值 / 空证据 / 长度不一致 → fail closed
```

合同绑定 criterionId ↔ statisticId ↔ normalization ↔ partition ↔ operator ↔ threshold ↔ seedPolicy；任一不符即拒绝（测试参数化覆盖十种错配）。与 square 实现对任意 k/N 的判定一致性由测试钉死。

## 9. 多 seed（PART 16）

N = 10，三类 seed（init / sample / batch）在**第一次正式训练之前**写入 `seed_ledger.json`；失败 seed 不得删除；最好 seed 不单独报告。

## 10. Tier-1 Red Team 适用性（PART 25）

八项全部 **APPLICABLE**（无 N/A）：P1 重采样、P4 float32、P6 丢点 10%、**P7 双边界带加密（内外两条带）**、P8 域缩放（硬因子随域缩放至半径 (2a, 2R)）、P9 L-BFGS、**P11 残差自适应加密（强制项，区域用几何原生单元表达）**、P16 激活 sin。判据：Δq ≤ 1% 维持、1–5% PARTIAL、> 5% FAIL；P4 另有残差量级判据。只可维持或降级。

## 11. G6 复现容差（PART 28）

```text
|median_A - median_B| <= 1e-4            （继承的绝对上限）
且 |median_A - median_B| <= 0.5 * median_A（相对上限）
且 k/N 判定一致
seedOffset = 10000
```

在正式 run 之前预注册；不得跑完再选。环境：优先使用已保留并冻结的 Environment B；若需新依赖则重新 qualification 或新建 B2，**不污染现有 B**。本轮实测不需要新增依赖（torch / numpy / scipy / matplotlib 均已就位，FDM 只用 numpy）。

## 12. 代码身份（PART 1）

正式 run 必须使用**新的 revision / code identity**，不得复用 square-2D 的 `a39aa07e23d0…`。边界：前缀 `pinn/`、`scientific_reference/`、`specs/` + 具名治理文件 + 冻结配置 + `codeIdentityExtraFiles` 声明的正式驱动脚本 `experiments/annulus/run_formal_annulus.py`。绘图脚本**不在**身份内（它只渲染已登记证据，不能改变判定）。完整性检查在 codeHash 之前、PRELOCK 之前 fail-closed。

## 13. 事前披露

1. 步数是唯一与 square-2D 不同的方法值，理由见 5.2；架构、优化器、batch、dtype、seed 协议、阈值全部不变。
2. ACA 阈值是 square-2D 继承常数；其在圆环上的**可达性**由 EXPLORATORY smoke 事前评估，但 smoke 不参与任何判定。
3. 制造解刻意非对称，因此 x/y 互换对称检查登记 NOT_APPLICABLE；PH5 单调性同样登记 NOT_APPLICABLE（圆环上无单调方向），理由写在 registry 里。
4. 一次 smoke 同时承担性能测量与步数选择；步数选择规则在读取 20000 步结果**之后、冻结之前**写定，并如实记录于 5.2（这是本轮唯一的"看了 D_dev 数字再定方法值"的环节，且只涉及预算、不涉及阈值）。
5. 本轮**不**引入角点奇异、再入角、非线性、时间依赖、NS、UCM、反问题、传热。

---

## 14. 追加注解：执行设备与代码身份重置（2026-09-17，追加而非修改）

本节是**追加**。第 0–13 节一个字都没有改动：预注册一旦提交，方法不得重写；这里记录的是**执行环境**的变化和由此触发的重跑，不是方法的变化。

### 14.1 device 是执行参数，不是方法值

操作员要求把十个 seed 放到 GPU 上跑（NVIDIA GeForce RTX 4060 Laptop，8 GB，cc 8.9，torch 2.12.1+cu126）。训练设备因此成为一个新的执行选择，处理方式如下：

* `device` 是**命令行参数**（`run_formal_annulus.py --device`，或 `runner_annulus attempt --device`），**没有、也不会写进冻结配置** `exp_annulus_baseline.json`。理由是 PART 1 与 PART 28 的直接推论：配置文件在 `codeHash` 之内，而 G6 复现要求在**只有 CPU 的 Environment B** 上用**同一个 codeHash** 重跑。device 一旦进配置，G6 就永远无法复现——这不是风格问题，是可复现性的硬约束。
* device 只作用于**训练**。Gate 3–5、物理检查、局部判据 ACA-9、绘图的全部数值都在 **CPU** 上计算（`runner_annulus.phase_training` 把权重搬回 CPU 重建模型）。于是没有任何一个 Gate 数字依赖加速器，Environment B 的 CPU 复现比较的是同类。
* 精度不变：float64（宪法要求），`torch.use_deterministic_algorithms(True)` 保持开启。CUDA 下该开关要求 `CUBLAS_WORKSPACE_CONFIG=:4096:8`，代码里显式设置该环境变量；**没有**为了绕开报错而关闭确定性，实测也没有任何算子报缺确定性实现。
* device 确实改变环境指纹里的 `acceleratorClass`（`cpu-only` → `cuda-NVIDIA GeForce RTX 4060 Laptop GPU`）。这是正确的位置：设备属于**环境**，不属于方法。它同时被记进 `identity.json.executionDevice` 与每条 run record 的 `determinism` 块。主 run 在 GPU、G6 复现在 CPU，两者 `acceleratorClass` 不同，只会让环境独立性更强（PART 28.1 的 strong field 判据）。

### 14.2 事前设备基准（EXPLORATORY，不是证据）

不假设 GPU 更快。网络极小（4×64 tanh，batch 512），且按宪法用 float64，而 4060 的 FP64 吞吐是 FP32 的 1/64，所以先测后用。基准脚本 `experiments/annulus/bench_device_annulus.py`，标记 `marking=EXPLORATORY`、`formalEvidence=false`，只读 D_dev 的一个探索性实例，seed 用 smoke 基数 20261200 / 20261210 / 20261220（与正式基数 20261400 / 20261500 / 20261600 不相交），2000 步：

| 测量（2000 步） | 单步 | 10 seed × 120000 步推算 |
| --- | --- | --- |
| CPU，独立进程 | 16.6 / 21.6 ms | 5.5 – 7.2 h |
| CUDA，独立进程 | 18.2 / 19.3 ms | 6.1 – 6.4 h |
| 同进程 CPU vs CUDA | 21.2 vs 18.8 ms | CUDA 快 1.13× |
| 已归档 CPU attempt（历史） | 11.7 ms | ≈ 3.9 h |

结论如实记录：**GPU 在这个工作负载上没有明显更快**，四次测量的差异落在运行间噪声之内（CUDA 更稳定，平均约快 5%）。另外，今天整机比归档 attempt 时慢约 1.6 倍（11.7 → 约 19 ms/步），所以无论哪个设备，十个 seed 都是约 6–7 小时墙钟。操作员在看到这些数字之后，仍选择用 GPU 执行（2026-09-17 裁决）。代价已如实写明，方法没有因此改动一个字。

同一基准还测了两条路径的数值一致性：同 seed 跑满 2000 步后，CPU 与 CUDA 的权重最大绝对差 `4.441e-16`，devRelL2 差 `2.776e-17`。float64 + 确定性算法下，两者给的是同一个答案，差异只是归约顺序的浮点累积。

### 14.3 为什么必须整体重跑

给训练链路加 device 支持改动了 `pinn/` 下的文件，`codeHash` 因此改变：

```text
旧（CPU attempt，已停止并归档为 runs/stopped-cpu-r1-c5a3e12e018e/）
    codeHash  c5a3e12e018e94fd8dc36746fd6056373e587233060ffe69b8d51b0c9a5d0dcc
新（本轮 GPU attempt）
    codeHash  8ee9b9236199996fe95684b42bb6a247717f07bb5845437ac7c85ff7978b550e
```

这是一个**新的代码身份**。因此：

1. 正式 attempt **整体重跑**，十个 seed 全部在同一 codeHash、同一 device 下产生。
2. 旧 CPU attempt 的 seed 0（devRelL2 = 1.622e-04，1407 s）**不得**与新 seed 混用；它留在 `runs/stopped-cpu-r1-c5a3e12e018e/` 作为停止记录，连同更早的 `runs/aborted-r1-codebug-4ef0ae3a/`，都不删除、不改写。
3. 同一次改动里，Tier-1 Red Team 的驱动入口（`runner_annulus.run_tier1_for_attempt` 与 `run_formal_annulus.py --tier1`）也一并加好，**在正式 run 之前**进入代码身份——否则跑完再加 driver 会再次改变 `codeHash`，Tier-1 就无法与它所检验的 attempt 处在同一身份下。该入口在目标 attempt 的 Gate 5 未 PASS 时拒绝启动，且从不触碰 D_claim、账本或任何历史判定。
4. 盲集池、账本、ProblemDefinition、specHash `4c8dfbc7238d…` 与全部阈值**不受影响**：它们是方法，方法没有变。账本在本节写下时仍只有一条 SEALED，从未 OPENED。
