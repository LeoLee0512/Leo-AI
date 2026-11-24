# 2D Manufactured Poisson Calibration 预注册（2026-09-16）

写定并提交于任何正式 run 之前。宪法 1.2 不变（A-0001、A-0002 ACCEPTED，无 A-0003，不新增 Gate、状态或 TrustStatus 枚举）。1D 的历史 evidence 一律不改。本文件只做预注册；若 2D 实验暴露治理缺陷，只登记 `AMENDMENT CANDIDATE`，等用户与外部评审。

上游：`experiments/poisson2d/2D_REUSE_AUDIT_20260916.md`（PART 3 复用审计）、`experiments/poisson2d/pilot/PILOT_RESULT.json`（PART 4，EXPLORATORY）。

## 0. 被检验的命题

不是"2D PINN 能不能拟合 sin(pi x) sin(pi y)"，而是：**Leo AI 的科学治理、诊断、盲验证、复现机制能否从 1D 跨到真正的二维 PDE 而不失真。** 因此本轮只主动改变：空间维数 1→2、2D 配点采样、2D 二阶 AD、2D 空间误差结构、2D 可视化、训练成本。不引入不规则几何、非线性、CFD 参考、角奇性、混合 BC、时间依赖、反问题、UCM。

## 1. 冻结的数学问题（PART 1）

- 区域 Omega = (0,1)^2；方程 -(u_xx + u_yy) = f，f(x,y) = 2 pi^2 sin(pi x) sin(pi y)；四条边 u = 0。
- 制造解 u*(x,y) = sin(pi x) sin(pi y)；u*_xx = u*_yy = -pi^2 u*，故 -Delta u* = 2 pi^2 sin sin = f（Gate 2a 逐点机器验证，阈值 1e-12；四边界 |u*| 阈值 1e-14）。
- 闭式常数（写进规格，供判据使用）：int int u* = 4/pi^2；int int f = 8；int int |grad u*|^2 = int int f u* = pi^2/2；||f||_rms = pi^2；max|u*| = 1；闭边界法向通量 = -8。
- 规格文件 `specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json`（位于 `specs/` 前缀下，自动进入代码身份清单）。**不修改 PDE。**

## 2. 边界执行（PART 2）

冻结 `boundaryConditions.enforcement = hard`、`outputParameterization = x(1-x)y(1-y)N`。本轮不跑 soft-vs-hard 比较；软硬之争不是本轮变量。1D 的事后审计结论（因果归因非唯一）不被本轮引用为"硬 BC 更优"的论据，只作为"硬 BC 已在 C2 级别被验证过"的事实。

## 3. 数据集（PART 7）

| 集 | 构成 | 规模 |
|---|---|---|
| D_train | (0,1)^2 上均匀随机内点池，`numpy.default_rng(20260917).random((n,2))`；每个 run 由 sampling seed 从池中不放回抽 `collocationCount` 个 | 池 2048，抽 1024 |
| D_dev | 均匀随机内点，`default_rng(20260918)` | 1024 |
| D_phys | 张量 Gauss–Legendre 40 阶（含乘积权重） | 1600 |
| D_claim | 见第 4 节盲集池 | 每套 3328–3946 |
| 边界集 | 每边 GL 32 阶节点，弧长权重合计 4（周长）；spec-known 边界坐标，身份豁免（协议 L1），**不是 claim 样本** | 128 |

采样方案选择：沿用 1D 的 `default_rng` 均匀随机（与 1D 血缘一致、可审计），**在正式 run 后不比较哪种采样更好**（不跑 LHS / Sobol 对照）。硬 BC 下没有 BC 损失项，因此训练集只含内点。

样本身份：`canonical_sha256({"inputs": [float64 x, float64 y], "quantity": null})`，负零折叠、NaN/Inf 拒绝、坐标数必须等于 `inputNames` 长度（治理层现成规则，2D 直接适用）；`(x1,y1)` 与 `(x2,y2)` 不得因序列化得到同一 sampleId，另有测试钉死。互斥性由 `pinn.governance.evaluation_sets.disjointness_errors` 在样本级判定，`minSeparation = 1e-9`（欧氏距离，1D 继承）。

## 4. Claim pool（PART 7.5）

网格族：`{张量 GL_n} ∪ {去边界线的张量 CGL_m}`。预注册四套，全部 SEALED，按 `sampleSetHash` 烧毁（不按 artifactId）：

| 集 | 构成 | 预定 revision | 样本数 |
|---|---|---|---|
| D2C-GL32-CGL50 | GL32 x GL32 ∪ 内部 CGL50 x CGL50 | r1 | 1024 + 2304 = 3328 |
| D2C-GL34-CGL54 | GL34 ∪ CGL54 | r2 | 1156 + 2704 = 3860 |
| D2C-GL36-CGL56 | GL36 ∪ CGL56 | r3 | 1296 + 2916 = 4212 |
| D2C-GL38-CGL60 | GL38 ∪ CGL60 | r4 | 1444 + 3364 = 4808 |

构造约束（机器判定，pool manifest 记录）：GL 阶数取偶数（不含 0.5 节点，不同阶节点互异）；CGL 的 `m-1 ∈ {49, 53, 55, 59}` 两两互素且与 6 互素 —— 与 6 互素排除 cos 取 0、±1/2 的有理节点（即 1D 中 CGL2800 在 x=1/4 撞格点的那类问题），两两互素排除不同成员共享内部节点。反碰撞按坐标分量分别调用现成的 `anti_collision`（d ≤ 64，阈值 1e-12）。要求：成员两两样本互斥；与 D_train / D_dev / D_phys 互斥；revision r 只能消费为其预定的那一套；G5 FAIL 后该套 BURNT；**不得看着 D_claim 调任何东西**。

## 5. 架构与训练协议（PART 5、PART 6、PART 8）

选择规则（**在读取 pilot 第 3–5 档结果之前写定**）：*取最小的 pilot 档，使其 D_dev 相对 L2 至少比 epsilon_spec 低一个数量级，且 10 seed 成本在一小时以内。* 该规则只用 D_dev 数据，不涉及 claim 集、不挑 seed、不动阈值。

按此规则，pilot 第 1 档（3x32、6000 步，1D 架构原样移植）D_dev 6.05e-4，相对 1e-3 只有 1.65 倍余量 —— 不满足"低一个数量级"，**淘汰**；第 2 档（4x64、10000 步、batch 512、1024 配点）D_dev 4.27e-5，余量 23 倍，单 run 197 s，10 seed 约 33 min —— **选中**。为什么改架构：这是 PART 5 允许的"1D 的 3x32 在性能 pilot 中明显不足"情形；证据是 pilot 的 D_dev 数字与运行时间，不是 claim 数据。冻结后不再调整。

冻结配置 `experiments/poisson2d/configs/exp2d_baseline.json`（`configId = poisson2d-hard-bc-v1`）：

```
network:   4 hidden layers x 64, tanh, u = x(1-x)y(1-y)N
optimizer: Adam, lr 1e-3 -> 1e-5 指数衰减, 10000 步, batch 512, threads 1, 无 early stopping
loss:      L = mean( ( -(u_xx+u_yy) - f )^2 )   （单项；硬 BC 下无 BC 罚项）
precision: float64, use_deterministic_algorithms(True), CPU
seeds:     10 个三元组 init=20260920+i, sample=20261020+i, batch=20261120+i（与 pilot 的 20260800/10/20 不相交）
```

多 seed 协议（PART 8）：**N = 10**，三类 seed（initialization / sampling / batch-order）全部在训练前登记进 `seed_ledger.json`。不采用 N = 5。若实际成本使 N = 10 不可行，则按宪法报 `C_train = PARTIAL / BLOCKED`，**不降低 N 之后仍声称 C2**。

线程数固定为 1 并写进冻结配置：pilot 实测 4 线程只快约 20%，而固定线程数让同环境结果完全确定、跨环境只受容差约束。

## 6. 度量与阈值（PART 9、PART 10）

度量定义与阈值冻结在 `pinn/governance/poisson2d_contract.py`，可信校验器 `pinn/validation/poisson2d.py`（同一份实现同时服务 T10 控制夹具与 G5b claim 评估）。

| 判据 | 量 | 阈值 | 维数判定 | 阈值来源 |
|---|---|---|---|---|
| AC2D-1 (MUST) | 相对 L2（GL 张量网格） | 1e-3 | 定义 DIMENSION-INVARIANT / 可达性 DIMENSION-SENSITIVE | 1D 继承；可达性由 pilot 在 D_dev 上事前确认 |
| AC2D-2 (MUST) | 相对 L_inf（CGL 张量网格） | 5e-3 | DIMENSION-SENSITIVE | 1D 继承（= 5 x AC-1）；2D 的峰值/均方比更大，故这是这对判据里较松的一条，空间结构由 AC2D-9 承担 |
| AC2D-3 (MUST) | 四边界 max|u| | 1e-4 | DIMENSION-INVARIANT | 1D 继承；硬参数化下按构造为 0 |
| AC2D-4 (MUST) | 残差 RMS / ||f||_rms | 1e-2 | DIMENSION-INVARIANT | 1D 继承；比值无量纲（2D 的 ||f||_rms = pi^2） |
| AC2D-5 (MUST) | \|int int u - 4/pi^2\| / (4/pi^2) | 1e-3 | DIMENSION-INVARIANT | 1D 继承 + 2D 数值参考 |
| AC2D-6 (MUST) | 边界法向导数最差节点 \|du/dn - du*/dn\| / pi | 5e-3 | DIMENSION-SENSITIVE（量被重定义） | 1D AC-6 的常数继承；1D 比的是单点 u'(0)，2D 取整条边界求积节点上的最大值，**更严**；积分形式的通量恒等式另由 PH1 检查 |
| AC2D-7 (MUST) | \|int\|grad u\|^2 - int f u\| / (pi^2/2) | 1e-2 | DIMENSION-INVARIANT | 1D 继承 |
| AC2D-9 (MUST) | 8x8 分块的最大分块 RMS 误差 / 全域 u* 的 RMS | 1e-3 | DIMENSION-SENSITIVE（因维数提升而新增） | 协议规则 + 1D 常数：全局 L2 看不见空间热点，这是 2D 才真正出现的失效模式；把 AC2D-1 的常数逐块施加，**严格强于 AC2D-1**，不引入任何新数值常数 |
| AC2D-8 (SHOULD) | 梯度相对 H1 半范 | 5e-3 | DIMENSION-INVARIANT | 1D 继承 |

另作**诊断记录、不作判据**：E_inf 绝对值、残差 max、最大/中位分块比、热点坐标、边界通量恒等式缺陷、int int u。

1D 的症状阈值 `sLocalizedError`（max-bin / median-bin = 3.0，现按 8x8 分块）保留在失败路径的**症状**判据里，**不**作为验收阈值。

**禁止看完结果后放宽任何阈值。** 上表在 claim pool 密封之前、任何正式训练之前冻结。

## 7. 独立数值参考（PART 11）

`scientific_reference/poisson2d_fdm.py`：五点二阶差分 + 无矩阵共轭梯度，细化序列 8/16/32/64，判据为内部最大误差严格下降且观测阶 p ∈ [1.8, 2.2]、线性解收敛。事前披露：制造解的离散强迫恰是五点算子的离散特征向量，CG 一到两步即收敛，**因此 Gate 2b 检验的是离散化阶，不是线性求解器的鲁棒性** —— 这一点写进 Gate 2 的记录，不藏。FDM 只作实现层面的 sanity cross-check，不能替代解析解。

## 8. Gate 与检查登记表（PART 12、PART 13、PART 14）

不新增 Gate，不新增 TrustStatus。检查登记表（进 specHash）：

- math：M1 场数闭合、M2 四条 Dirichlet 条件、M3 量纲齐次、M5 几何绑定（rectangle/dimension 2/四个边 region）、M6 参考方程绑定。
- impl：**T1** 随机网络的 AD 对中心差分，`u_x, u_y, u_xx, u_yy` **逐分量**比对（阈值 1e-6 / 1e-4）；**T2** 非对称探针 w = sin(2 pi x) sin(pi y) 上分别验证 w_xx = -4 pi^2 w、w_yy = -pi^2 w（阈值 1e-9），并记录两分量的判别间隙 —— 因为**对称的制造解本身无法判别 x/y 互换**，这是 2D 才出现的检验义务；T3 残差算子作用于解析解（1e-10）；**T4 四条边分别检查**硬参数化的 |u|（按构造恰为 0）；T8 损失项分离（单项 pde，无 BC 罚项，边界由构造保证并由 T4 独立验证）；T9 四集样本级互斥；T10 可信校验器对控制夹具的判决。
- train：G4 训练完整性、seed 协议（宪法 10.1）、损失—误差解耦。
- physics：PH1 闭边界通量恒等式 |flux + int int f| / |int int f|（1e-2）；PH2 能量恒等式（1e-2）；PH3 正性 min u >= -1e-3（f >= 0）；**PH4 互换对称性** max|u(x,y) - u(y,x)|（5e-3，是证据不是训练约束）；PH5 沿张量网格线的单调性违例数（容差 1e-3）；PH6 最大值原理 max u <= 1 + 5e-3；PH7 五点刚度矩阵最小特征值 > 0 且 Dirichlet 能量 > 下限。PH10（动量收支）、PH11（自由能）NOT_APPLICABLE，理由登记。
- external：G5b MUST / SHOULD。
- repro：G6 独立环境复现。

T10 控制夹具（2D 版）：解析正控制、符号翻转、常数偏移（违反 BC）、小幅高模态 (4,4,0.002)、大幅模态 (5,1,0.2)、零场、**导数不一致夹具**（u 正确但上报的二阶导缩放 0.5，用来证明 AC2D-4 真的连着上报的导数）。要求：正控制接受、其余全部拒绝。

## 9. Tier-1 Red Team（PART 18，事前）

仅在 G5 PASS 之后执行，只用 D_dev（QoI 用 D_phys），每个扰动一次重训，基线为本 attempt 的正式 seed-0 run。度量：e2（D_dev 相对 L2）、delta_q = |QoI' - QoI| / QoI，QoI = int int u（D_phys 张量网格，精确值 4/pi^2）、D_dev 残差 max。阈值（1D 继承，无量纲）：delta_q <= 1% 维持；1%–5% PARTIAL；> 5% FAIL；P4 另：残差 max 随 dtype 变化超一个数量级 → C_impl FAIL。只能维持或降级。

| P | 改动 | 2D 适用性判定 |
|---|---|---|
| P1 | 同池重抽配点（sampling seed +900） | ✓ |
| P4 | float32 训练，残差 float64 重算 | ✓ |
| P6 | 随机删 10% 配点 | ✓ |
| **P7** | 边界带（宽 0.1）内配点密度加倍重抽 | **✓ APPLICABLE（与 1D 相反）**：1D 的边界是两个被精确评估的点，2D 的边界是一条曲线，配点必须分辨紧邻边界的二维带，密度是方法的真实自由度 |
| P8 | 域缩放到 (0,2)^2（v(xi,eta) = u(xi/2,eta/2)，f_L = f/4），结果映射回 | ✓，**硬参数化随域缩放为 xi(L-xi)eta(L-eta)N** —— 这正是 1D Tier-1 run 1 踩过的 harness 缺陷，本轮在代码与测试里钉死 |
| P9 | Adam → L-BFGS（同函数评估预算） | ✓ |
| P11 | 残差自适应局部加密 | ✗ NOT_APPLICABLE：制造解解析、无局部特征；空间误差集中由验收判据 AC2D-9 **度量**，而不是用自适应加密去探测（2D 的独立判定，不照搬 1D 理由） |
| P16 | 激活 tanh → sin | ✓ |

## 10. G6 复现（PART 19）

仅在 G1–G5 PASS 且 Tier-1 完成后执行。要求：同 specHash、同 codeHash、不同 seed 集（规则：原三元组 +10000）、合格的独立环境（宪法 28.1：至少一个强字段不同）、**事前冻结的容差**。不重开 D_claim；复现只在 D_dev 上比较。

容差（**正式 run 之前冻结**，写在 `configs/exp2d_baseline.json` 的 `reproduction` 段与复现包内）：

```
C_repro PASS 需同时满足：
  |median_A - median_B| <= 1e-4            （1D 继承的绝对上限）
  |median_A - median_B| <= 0.5 * median_A  （相对上限，收紧）
  k/N 判定一致
```

相对上限的来源：宪法 10.1 已把"IQR > 1.0 x median"判为同环境内离散过大；跨环境的中位数漂移超过 0.5 x median 同理不可接受。加这一条是因为在 2D 的误差量级（约 1e-5–1e-4）上，单靠 1D 继承的绝对上限过松。另记录 |Δmedian| / IQR_A 作为诊断（不参与判定）。

代码身份提醒（1D 的教训）：复现必须在**原 commit 的干净检出**上运行原 runner，驱动脚本放在代码身份清单之外；否则 codeHash 不同，`reproduction_status` 会（正确地）判 BLOCKED。

## 11. 声明门（PART 20）

只有六维全 PASS 且 Tier-1 完成，才允许 `SUPPORTED @ C2`；否则按真实状态报告。C3 仍需 ≥ 5 个独立合格 C2 run，本轮不可能达到。

## 12. 事前披露

1. **对称制造解的判别力缺口**：u* 对 (x,y) → (y,x) 对称，因此 claim 层的任何判据都无法判别残差算子里的 x/y 互换；该能力由 G3 的 T2 非对称探针承担。这是维数提升带来的真实新问题，事前写明。
2. **AC2D-9 严格强于 AC2D-1**：若空间误差集中，AC2D-9 会先于 AC2D-1 失败；这是有意的，不是失误。
3. **互斥性扫描的成本**：`disjointness_errors` 的最小间距检查是 O(N·M) 纯 Python，本轮集合规模下每次扫描约数十秒，register-pool 阶段数分钟。这是已知代价，不是放宽 `minSeparation` 的理由。
4. **FDM 的 CG 一步收敛**（第 7 节）。
5. **pilot 不是证据**：`PILOT_RESULT.json` 标记 EXPLORATORY、claim 资格 <= C1、与正式 attempt 目录分离；其 seed 与正式 seed 不相交；任何 pilot run 都不得被当作正式 run 复用。
6. **本轮不进入** 2D 之后的任何复杂度台阶（不规则几何、BFS、Navier–Stokes、UCM、传热、新修正案、架构扫描）。
