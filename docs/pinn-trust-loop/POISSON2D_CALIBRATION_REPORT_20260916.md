# Poisson 2D Calibration Report（2026-09-16）

执行负责人：Claude（队长）。宪法 1.2 不变（A-0001、A-0002 ACCEPTED，无 A-0003，无新 Gate、无新 TrustStatus、无阈值事后放宽）。1D 的机器记录一律未改。预注册 `experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md`（正式 run 前提交，commit `f3d322b`）；复用审计 `experiments/poisson2d/2D_REUSE_AUDIT_20260916.md`；追加审计 `PORTABILITY_AUDIT_20260916.md`、`PILOT_ROLE_ANNOTATION_20260916.md`。全部数字来自机器记录。

## 1. Executive Result

```text
2D Poisson Calibration:
PASS

Highest admissible Claim:
C2   (SUPPORTED @ C2, ClaimGateDecision cgd-exp2d-poisson-calibration-r1-g6)

State:
ACCEPTED

READY FOR USER / EXTERNAL REVIEW BEFORE THE NEXT 2D COMPLEXITY STEP
```

被检验的命题不是"2D PINN 能拟合 sin(πx) sin(πy)"，而是**Leo AI 的科学治理、诊断、盲验证与复现机制能否从 1D 跨到真正的二维 PDE 而不失真**。答案见第 2 节。

## 2. Dimension-Lift Audit：What broke only because the problem became 2D?

| 类别 | 结论 | 事实 |
|---|---|---|
| **sampling** | 需要新构造，规则本身没坏 | 治理层的样本身份（`canonical_sha256({inputs:[x,y], quantity})`）与互斥判定天然支持二维，一行未改。因维数出现的新约束在 claim 网格族：一维只需让 CGL 节点避开有理格点 `i/d`（1D 曾因 CGL2800 撞 x = 1/4 而弃用该成员），二维张量族还要求不同成员的 CGL 计数**两两互素**，否则两套网格整族共享内部节点。构造规则 `m−1 ∈ {49,53,55,59}`（与 6 互素且两两互素）；实测两两共享样本 0，反碰撞最小距离 4.09e-05 / 8.68e-06 / 3.28e-07 / 6.03e-06。 |
| **AD** | **真正的新失效模式** | 1D 的二阶导是单变量两次求导；2D 必须分量分别求导，而且**对称的制造解在 claim 层无法判别 x/y 互换**（u\* 在互换下不变，任何 AC 都不受影响）。判别能力只能放进 Gate 3：新增 T2，用非对称探针 w = sin(2πx) sin(πy) 分别验证 w_xx = −4π²w、w_yy = −π²w（实测 7.11e-15 / 1.78e-15，两分量判别间隙 > 1）。这条写在预注册的事前披露里，不是事后补的。 |
| **runtime** | 贵约 11 倍，仍可行 | 1D 每 run 16.7 s（3×32 / 6000 步）→ 2D 选定档 4×64 / 10000 步 ≈ 187 s。pilot 实测每步耗时由 Python / autograd 图开销主导（batch 128 → 1024 每步成本几乎不变），所以 2D 的可行性来自"大 batch、少步数"，不是更大的网络。 |
| **memory** | 无问题 | 参数量 12,737，配点张量 1024×2 float64；峰值远低于 1 GB，未触发任何限制。 |
| **validation** | 判据必须重定义，阈值不能机械照搬 | 1D 的 AC-5（∫u = 2/π）与 AC-6（u′(0) = π）是一维解析常数。2D 用 ∫∫u = 4/π²，并把 AC-6 由"单点导数"改为"整条边界求积节点上的最差法向导数"（更严）。新增 **AC2D-9**：全局 L2 在二维看不见空间热点，这是维数提升带来的新失效模式，因此把 AC2D-1 的常数逐块施加在 8×8 分块上（**分母是全域 u\* 的 RMS**，所以这是一个*局部相对误差*，其值远小于 1；它严格不小于**同一网格上的全局相对 L2**，对 AC2D-1 则是经验上更严——实测比值 2.90–4.36。详见 `runs/exp2d-poisson-calibration-r1/POST_AUDIT_ANNOTATION.md` 与 `AC2D9_FORMULA_AUDIT.json`）。 |
| **visualization** | 全部重做 | 一维曲线图在二维无意义；新增解面、误差热图、残差热图、配点分布、最差 seed 误差场、FDM 收敛图、Red Team 汇总，全部由已登记的 D_phys 张量网格与已存权重生成，不引入新的评估面。 |
| **governance** | **none** —— 没有任何治理条款因维数失效 | 宪法 1.2、状态机、六维向量、弱链演算、账本、PRELOCK、schema 全部原样适用。唯一被触发的是账本既有规则"OPENED 的 specHash 必须等于 SEALED 的 specHash"，它要求盲集池在 revision-1 ProblemDefinition 冻结之后密封——这是流程顺序，不是缺陷，冒烟测试在正式 run 之前就把它暴露了。 |

## 3. Numerical Results

冻结身份：`problemId pdef-poisson2d-cal-v1` · revision 1 · specHash `05328d507582…` · codeHash `a39aa07e23d0…` · 配置 `poisson2d-hard-bc-v1`（4×64 tanh，u = x(1−x)y(1−y)N，Adam 1e-3→1e-5，10000 步，batch 512，1024 配点，float64，单线程，deterministic）。

### 3.1 训练可靠性（Gate 4，D_dev 1024 点，10 seed）

| 项 | 值 |
|---|---|
| N / k | 10 / 10（k/N = 10/10） |
| median dev 相对 L2 | **3.686e-05**（ε_spec = 1e-3） |
| IQR | 8.992e-06 |
| worst seed | 4.262e-05 |
| divergent | 0 |
| 逐 seed | 3.60e-5, 4.26e-5, 3.96e-5, 3.86e-5, 3.27e-5, 2.57e-5, 4.07e-5, 3.06e-5, 2.69e-5, 3.78e-5 |
| 判定 | medianOk ✓ worstOk ✓ dispersionOk ✓ → **C_train PASS** |

### 3.2 盲 claim 集上的验收判据（Gate 5b）

claim 集 `D2C-GL32-CGL50`：3328 样本（张量 GL32 = 1024，内部张量 CGL50 = 2304），sampleSetHash `7fbbb775da65…`，artifact `d4d2dd4a4d1c…`。

| 判据 | 量 | 阈值 | 10 seed 最差值 | 余量 | 全 seed 满足 |
|---|---|---|---|---|---|
| AC2D-1 | 相对 L2 | 1e-3 | 4.257e-05 | 23× | ✓ |
| AC2D-2 | 相对 L∞ | 5e-3 | 7.030e-05 | 71× | ✓ |
| AC2D-3 | 四边界 max\|u\| | 1e-4 | **0.000e+00** | 按构造 | ✓ |
| AC2D-4 | 残差 RMS / ‖f‖_rms | 1e-2 | 1.042e-03 | 9.6× | ✓ |
| AC2D-5 | \|∫∫u − 4/π²\| / (4/π²) | 1e-3 | 3.076e-05 | 33× | ✓ |
| AC2D-6 | 边界法向导数最差节点 | 5e-3 | 4.382e-04 | 11× | ✓ |
| AC2D-7 | 能量恒等式 | 1e-2 | 2.879e-05 | 347× | ✓ |
| AC2D-9 | 8×8 分块**最大块 RMS 误差** / **全域 u\* 的 RMS** | 1e-3 | 1.568e-04 | 6.4× | ✓ |
| AC2D-8（SHOULD） | 梯度相对 H1 半范 | 5e-3 | 1.416e-04 | 35× | ✓ |

十个 seed 的 `failedMustCriteria` 与 `failedShouldCriteria` 全为空 → **C_external PASS**。

诊断量（不作判据，seed 0）：残差 max 5.09e-02；**最大/中位分块比 3.94**；热点 (0.298, 0.452) 绝对误差 5.97e-05；最差分块 x ∈ [0.25, 0.375]、y ∈ [0.375, 0.5]，块 RMS 4.88e-05；通量恒等式缺陷 1.27e-06。

### 3.3 物理检查（Gate 5a，D_phys 1600 点 + 128 边界求积节点，取最差 seed）

| 检查 | 值 | 阈值 | 结果 |
|---|---|---|---|
| PH1 闭边界通量 \|∮∂u/∂n + ∫∫f\| / \|∫∫f\| | 1.069e-04 | 1e-2 | PASS |
| PH2 能量恒等式 | 2.879e-05 | 1e-2 | PASS |
| PH3 正性 min u | 7.654e-06 | ≥ −1e-3 | PASS |
| PH4 互换对称 max\|u(x,y) − u(y,x)\| | 7.648e-05 | 5e-3 | PASS |
| PH5 网格线单调性违例 | 0 | 0 | PASS |
| PH6 最大值 | 0.996290 | ≤ 0.9962953 + 5e-3 | PASS |
| PH7 SPD：λ_min(n=1024) / Dirichlet 能量 | 19.739193 / 4.9345 | > 0 / > 1e-14 | PASS |
| PH10 动量收支 · PH11 自由能 | — | — | NOT_APPLICABLE（理由登记） |

`∫∫f` 在 D_phys 上求得 8.000000000000（精确值 8）。

### 3.4 数学与实现（Gate 1–3）

- **G1**：M1 一方程一未知；M2 四条 Dirichlet、四个边 region；M3 无量纲；M5 rectangle / dimension 2 / 四边绑定；M6 参考方程绑定。全 PASS。
- **G2a**：D_phys 上 max\|−(u\*_xx + u\*_yy) − f\| = **0.000e+00**；四边界 max\|u\*\| = 1.221e-16。
- **G2b**：独立五点 FDM，内部最大误差 1.295e-02 → 3.219e-03 → 8.036e-04 → 2.008e-04，观测阶 **2.0084 / 2.0021 / 2.0005**，线性解全部收敛。**事前披露并记录**：制造解的离散强迫恰是五点算子的离散特征向量，CG 一到两步即收敛，所以 Gate 2b 检验的是离散化阶，不是线性求解器的鲁棒性。
- **G3**：T1 逐分量 AD 对中心差分 u_x 4.31e-11 / u_y 1.00e-10（< 1e-6），二阶分量 < 1e-4；**T2** 非对称探针 7.11e-15 / 1.78e-15，判别间隙 > 1；T3 残差算子作用于解析解 3.55e-15；**T4 四条边分别恰为 0.0**；T8 单项 pde 损失、无 BC 罚项；T9 四集样本级互斥（minSeparation 1e-9）；T10 可信校验器接受解析正控制、拒绝全部 6 个污染夹具（符号翻转、常数偏移、小幅高模态、大幅模态、零场、导数不一致）。

## 4. Trust Vector（`trust_vector_g6.json`，supersedes `tv-…-tier1`，校验器通过）

```text
C_math     = PASS   (M1, M2, M3, M5, M6)
C_impl     = PASS   (T1, T2, T3, T4, T8, T9, T10；Tier-1 P4 维持)
C_train    = PASS   (10/10 seed，median 3.686e-5，IQR 8.99e-6，worst 4.26e-5；Tier-1 P1/P6/P7/P9/P16 维持)
C_physics  = PASS   (PH1–PH7；PH10/PH11 NOT_APPLICABLE)
C_external = PASS   (claim set D2C-GL32-CGL50, sampleSetHash 7fbbb775da65…, OPENED@r1 一次, BURNT)
C_repro    = PASS   (repro-envb2d-r1，独立环境，同 spec 同 code 异 seed，容差内)
```

## 5. Failure Path

本轮**没有**进入 FAILURE_RECORDED：Gate 1–5 一次通过，无诊断、无修订、无重入。失败路径并非未实现——冒烟测试（临时沙箱，已删除）验证了 Gate 4 FAIL → FAILURE_RECORDED → 2D 症状（sPdeResidual / sConservation / sPinnCfd / sSeedSensitive）登记 → 账本上不出现 OPENED 事件，即"失败时 claim 集不被打开"这条硬要求在 2D 实现里成立。

## 6. Blind Validation

```text
claim set        D2C-GL32-CGL50
sampleSetHash    7fbbb775da65...
artifactHash     d4d2dd4a4d1c...
size             3328 samples (tensor GL32 = 1024, interior tensor CGL50 = 2304)
SEALED           2026-09-16T12:29:08Z  (revision 1, specHash 05328d507582...)
OPENED           2026-09-16T13:03:07Z  (codeHash a39aa07e23d0...)
BURNT            OPENED 即烧毁；终身只打开一次
still SEALED     D2C-GL34-CGL54 (r2) · D2C-GL36-CGL56 (r3) · D2C-GL38-CGL60 (r4)
metrics          AC2D-1..AC2D-7、AC2D-9（MUST）与 AC2D-8（SHOULD）全部 10 个 seed 满足（第 3.2 节）
ledger head      1dac14f667847f61...
```

盲性保证：claim 集在任何训练之前密封；训练与诊断只用 D_train / D_dev / D_phys；claim 集在 Gate 5a 之后才打开，打开事件带 codeHash 入账本；身份按样本（sampleSetHash）烧毁，把同一批样本重新包装会被账本拒绝。

## 7. Red Team（Tier-1）

只用 D_dev（QoI 用 D_phys），每个扰动一次重训，基线为正式 seed-0 run。阈值：Δq ≤ 1% 维持，1–5% PARTIAL，> 5% FAIL；只能维持或降级。

| P | 改动 | 维度 | e2 | Δq | 结果 |
|---|---|---|---|---|---|
| P1 | 同池重抽配点 | train | 3.220e-05 | 7.778e-06 | PASS |
| P4 | float32 训练，残差 float64 重算 | impl | 5.316e-05 | 1.774e-05 | PASS |
| P6 | 删 10% 配点 | train | 7.570e-05 | 4.264e-05 | PASS |
| **P7** | 边界带（宽 0.1）内配点密度加倍重抽 | train | 3.821e-05 | 5.461e-05 | PASS |
| **P8** | 域缩放到 (0,2)²，硬参数化随域变换，结果映射回 | math | 1.849e-04 | 1.332e-04 | PASS |
| P9 | Adam → L-BFGS（同函数评估预算） | train | 7.578e-06 | 2.723e-05 | PASS |
| P11 | 残差自适应局部加密 | — | — | — | NOT_APPLICABLE（2D 独立判定） |
| P16 | tanh → sin | train | 1.543e-04 | 7.759e-05 | PASS |

```text
Tier-1: PASS（全部适用扰动维持；最大 Δq = 1.33e-4，比 1% 维持线低两个数量级）
```

两点单独记录：**P7 在 2D 判为 APPLICABLE**（1D 里它是 NOT_APPLICABLE，因为一维边界只有两个被精确评估的点；二维边界是曲线，紧邻它的二维带的配点密度是方法的真实自由度），实测维持；**P8 的硬参数化随域缩放**（u = ξ(L−ξ)η(L−η)N）没有重演 1D Tier-1 run 1 的 harness 缺陷，另有单元测试钉死。

## 8. Reproducibility（Gate 6）

| 项 | 值 |
|---|---|
| 复现 run | `repro-envb2d-r1`（Gate 4 后停止，**不触碰 claim 集**，`claimSetTouched: false`） |
| specHash | `05328d507582…`（同） |
| codeHash | `a39aa07e23d0…`（**同**） |
| seed 集 | 原三元组 +10000（seedSetId 不同） |
| Environment A | mamba 前缀，installationId `prefix-<env-A>`，dependencyLockHash `75efe91aa4e1…`，environmentId `e986dbc039e0…` |
| Environment B | 全新 venv（base 同一 mamba python 3.12.9，无 system-site-packages，`--no-cache-dir` 只装复现包声明的 torch 2.12.1+cpu 与 numpy 2.4.5），installationId `prefix-<env-B-2d>`，dependencyLockHash `460309bb1065…`，environmentId `48e795c85bbd…` |
| 独立性 | **independent = True**：强字段中 `installationId` 与 `dependencyLockHash` 不同（machineId / osFamily / acceleratorClass / frameworkVersion / blasBackend 在同机上必然相同；宪法 28.1 只要求至少一个强字段不同） |
| dev 相对 L2 中位 | A 3.686e-05 · B **3.286e-05** |
| \|Δmedian\| | **4.000e-06** |
| 预注册容差（两条同时成立） | 绝对 ≤ 1e-4 ✓ · 相对 ≤ 0.5 × median_A = 1.843e-05 ✓ |
| 诊断（不参与判定） | \|Δmedian\| / IQR_A = **0.44**（差异小于原 run 自身的 seed 离散） |
| k/N | A 10/10 · B 10/10，判定一致 |
| B 的 IQR / worst | 1.464e-05 / 6.167e-05（divergent 0） |
| 判定 | 同 spec ✓ 同 code ✓ 独立环境 ✓ 异 seed ✓ 容差内 ✓ → **C_repro = PASS** |

**与 1D 的方法差异（重要且如实记录）**：1D 的 G6 必须在原 commit 的**冻结分离检出**上跑，因为那一轮的 runner 代码在两次运行之间改过，codeHash 不同会被 `reproduction_status` 正确判 BLOCKED。本轮两次运行之间**代码身份清单内没有任何文件变化**（中间的提交只增加了 `experiments/` 下的证据，不在代码身份前缀内），因此 codeHash 由校验器复算后逐位相同（`a39aa07e23d0`），gitHead 不同（`ad9f029` 对 `22117f0`）而 codeHash 相同——这正说明代码身份是**内容哈希**而不是提交哈希。复现因此直接在同一工作树上用 Environment B 的解释器执行，并由 `reproduction_report.json` 机械记录 `sameCode: true`。复现包 `experiments/poisson2d/repro_package/` 仍按冻结检出的方式书写说明，供外部方使用。

## 9. Tests / PRELOCK

| 项 | 值 |
|---|---|
| HEAD `e7d85c2` 真实基线 | **1109 passed / 3 failed / 6 skipped** |
| 新增测试 | 22 项（`test_poisson2d_identity` 7、`test_poisson2d_physics` 10、`test_poisson2d_reproduction` 5） |
| 本轮全套 | **1121 passed / 3 failed / 16 skipped** |
| 失败项 | 全部是审计过的既有 portability 三项（第 10 节 NB-1），与 2D 结论无关 |
| 跳过项 | 16 = 既有 6 + 本轮 10（治理 venv 无 torch / numpy） |
| 被跳过测试的补充执行 | `experiments/poisson2d/verify_tests_under_torch.py` 在训练解释器下跑同样的函数：**17 passed / 0 failed**（记录 `TEST_VERIFICATION_UNDER_TORCH.json`） |
| PRELOCK | **7/7 PASS**（constitutionBinding / spec / protocol / adversarialManifest / lockDraft / repository / amendmentRegister） |

测试覆盖面（PART 22 逐条）：2D 样本身份（含 (x,y) 与 (y,x) 不同一）、二维集互斥与最小间距、四条边硬 BC（含缩放域）、u_xx 与 u_yy 分量分别验证、2D 残差、对称性度量、2D claim pool（互斥 + 反碰撞）、局部误差检测（全局范数仍通过时单块热点必须被 AC2D-9 抓到）、2D 复现包与容差、校验器对畸形证据的拒绝。

## 10. Newly Discovered Problems

**BLOCKING**：无。

**NON-BLOCKING**

- **NB-1（既有，非本轮引入）**：HEAD 的 full suite 有 3 项 portability FAIL，来源是 1D 收口提交 `32eaa36` 入库的绝对路径证据；1D 收口报告记的"1112 passed / 0 failed"是证据入库之前跑的。**本轮 2D 证据又新增 3 条同类发现**（`TEST_VERIFICATION_UNDER_TORCH.json:4` 的解释器路径、`environment_b_qualification.json:46` 的 venv 路径、生成脚本 `qualify_environment_b.py:45` 的同一字面量）；1D 那类 `PROVENANCE_MANIFEST` 污染未复发。按宪法 28.1"路径不是身份"，这些不影响任何 specHash / codeHash / environmentId 或 AC 数值。本轮**未改 policy、未改任何证据、未加豁免**，裁决项见 `PORTABILITY_AUDIT_20260916.md` 第 5 节。（自指效应，如实记录：审计文件第一版逐字引用了被指认的路径，`experiments/**` 在扫描范围内，于是审计文件自己又多出 2 条同类发现；已把审计说明文字里的用户名脱敏为 `<user>` 消除，被指认文件一字未改。扫描范围事实：`docs/**.md` 与根目录一份报告属类别豁免，`experiments/**` 不豁免。最终计数 7 条 = 1D 既有 4 + 本轮实质 3。）
- **NB-2**：EXPLORATORY pilot 同时承担了性能测量与**架构 / 模型选择**。宪法 1.2 第 561 行明文把"模型与架构选择"列为 D_dev 的许可用途，第六十五章要求晋升时在冻结规格下重走完整闭环（本轮正是如此，seed 严格不相交），因此裁决 **ALLOWED，不阻断 C2**；如实登记于 `PILOT_ROLE_ANNOTATION_20260916.md`。
- **NB-3**：1D 的症状阈值 `sLocalizedError`（最大块 / 中位块 = 3.0）在本轮**一个完全合格的结果上就会触发**（实测 3.94）。原因是二维误差场的空间结构天然比一维分箱更不均匀，而该常数是按一维 10 分箱定的。本轮它只作为失败路径的症状规则、未参与验收（验收用 AC2D-9，实测 1.57e-4 对阈值 1e-3），因此没有造成误判；但它说明**症状阈值需要与维数相关的定义**。
- **NB-4**：Gate 2b 的独立 FDM 基线因制造解恰为五点算子的离散特征向量，CG 一到两步收敛；它验证的是离散化阶而非线性求解器鲁棒性（事前披露，非事后辩解）。
- **NB-5**：`disjointness_errors` 的最小间距扫描是 O(N·M) 纯 Python，本轮规模下每次 attempt 约 15–20 秒、register-pool 约 70 秒。可接受，但集合规模再上一个量级就会成为瓶颈。
- **NB-6**：本轮的 C2 建立在**单一 2D 问题、单一架构、单一机器的两个独立安装**上。C3 需要 ≥ 5 个独立合格 C2 run，本轮结构上不可能达到，决策文档已明确阻断。
- **NB-7**：`problems/*-claim-pool.json` 的 `status` 字段在成员被打开烧毁后不会回写（本轮结束时四套仍写着 `SEALED`，而账本已记录 `d4d2dd4a` 为 OPENED）。真正的防线是账本而不是这个字段，已实测验证：对同一 claim 集再次 OPENED 被拒（"a set is opened once, ever" + "a second OPENED for the same problem and revision"），把同一批样本重新包装后密封也被拒（"a re-wrapped claim set is not blind"）。但 runner 在 `phase_problem` 里的早期护栏读的是这个**过期字段**，因此一次误用会在训练跑完之后才被账本拦下，而不是在开始前。该字段与该护栏都是从 1D 继承的，本轮未改（PART 25 STOP）。

**AMENDMENT CANDIDATE**（只登记，不起草）

- **AC-1**：症状阈值（`sLocalizedError` 等）应有维数相关的定义或标定方式（来自 NB-3）。
- **AC-2**：claim 网格族在多维张量积下需要成文的构造约束（成员计数两两互素、与有理格点的反碰撞按分量判定），目前只写在本轮预注册里。
- **AC-3**：证据文件中的环境构造描述建议只记 prefix 哈希与依赖，不记绝对路径（来自 NB-1）。
- **AC-4**：EXPLORATORY 活动若同时承担模型选择，建议在协议层要求显式分标记（来自 NB-2）。
- **AC-5**：pool manifest 的成员状态应由账本推导（或早期护栏直接读账本），而不是静态字段（来自 NB-7）。

## 11. Final Recommendation

```text
READY FOR NEXT 2D COMPLEXITY STEP
```

理由：六维全 PASS，Tier-1 全部维持，G6 在合格独立环境复现且落在两条预注册容差之内，状态机 ACCEPTED，唯一阻断的是结构上不可能在本轮达成的 C3。维数提升没有击穿任何治理机制（第 2 节 governance = none）；被击穿的是**度量与判别设计**——对称制造解无法判别 x/y 互换、全局范数看不见空间热点——两者都已在本轮用 T2 与 AC2D-9 补上。

**本轮到此停止**（PART 25）。不开始不规则几何、BFS、Navier–Stokes、UCM、传热、新修正案或架构扫描；等待用户与外部评审。下一步若获授权，应从新的 ScientificSpec 出发，带自己的 claim pool 与预注册。

## 附录 A：证据清单（artifactId · sha256）

### 顶层

- `specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json` · 46e98c699e00ca108d39f11bd38b37933bea8323b2f24d2af48fc8f7dcdb5269
- `experiments/poisson2d/2D_REUSE_AUDIT_20260916.md` · 5fce7c4e526a9ce749872c5910ce09783aa24b3ac4222e6fe1773c00f897bac7
- `experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md` · 4aa47e64aa5e0c0786d425ac68bcda52e521728c96eda7ba0817e3a92ebf9c9d
- `experiments/poisson2d/PORTABILITY_AUDIT_20260916.md` · 1f4681a36a5fd561ced42846c1db01df922e1a99930b5771f85657303d037515
- `experiments/poisson2d/PILOT_ROLE_ANNOTATION_20260916.md` · 0c7d4ce46c0e617cc62202cfca1d676425aced839a84215e0f083baeffb0aa69
- `experiments/poisson2d/configs/exp2d_baseline.json` · bf933c93b3f7fecd668872ff0d37487cda9770a076b9a07c504aead7868719c7
- `experiments/poisson2d/pilot/PILOT_RESULT.json` · 1a71c4c989491d1fd05105422588fab5f25b7bca428d4627e55abc53a1de7af3
- `experiments/poisson2d/TEST_VERIFICATION_UNDER_TORCH.json` · bfda55dd9a847e665815d1cc46bae6d5ad951533030191b96dcc0fe9c8b13500
- `experiments/poisson2d/environment_b_qualification.json` · f315790a8461027b9d1ffbf8c895217133955dfd31517c0892edc5b0b082cd3c
- `experiments/poisson2d/problems/pdef-poisson2d-cal-v1-r1.json` · 3d6a9beb4cbf1975b6c269d0cc506b3c40841bf382248f0bd911e5a489312b61
- `experiments/poisson2d/problems/pdef-poisson2d-cal-v1-claim-pool.json` · 36e92973174c295a5ac6763a11dea1cf8487ee33861e2fa1a3ca7544b07e1419
- `experiments/poisson2d/ledger/pdef-poisson2d-cal-v1.json` · 63e1e33c0c38982a9cdfd30b0857752ca34e4dde3dd091fa37be503c2986ea5c
- `experiments/poisson2d/repro_package/PACKAGE_MANIFEST.json` · bb537b3b317bd231b60cc8d161523cd8362c802f295cc4ff409178092bb1a329

### `runs/exp2d-poisson-calibration-r1`（44 个 artifact，此处略去 10 个 `runs/run-*.json` 与 9 张图）

- `identity.json` · 2fdee940205466500df95647d4774573d396f473d0f4f26b8e1d1a573e010352 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · ddbac79c99d071900943ae89af8bb43c1bdc655b2091e01a9d6859455a97a997 · EVALUATION_SET
- `sets/dev.json` · 625b76935b6a0334925a0898d12852aa327ab0c46276d1861b341f94931ee417 · EVALUATION_SET
- `sets/phys.json` · 8d8a61b67c23409bd0e83cf27d1ad7cbac06be254928ee904381f1de67129ad6 · EVALUATION_SET
- `sets/claim.json` · d4d2dd4a4d1c05b6ca31d67d5ee23c04c09481347f6acf51d0b0577ed37ff4e6 · EVALUATION_SET
- `sets/isolation.json` · 4e6c8098abd04d21695182bde02e8e7a7ddddee96b010db27aa34539d4b5eea0 · EVALUATION_SET_ISOLATION
- `sets/boundary.json` · f24bbd4673f3a73adf21519cb470fb99e1497101ffb7778cd816fc633a79617c · BOUNDARY_SET
- `sets/phys_weights.json` · 7cd8189d7625843355230ffb474e153336aaecbe6397bcae86e0f9efcd35ddd5 · EVALUATION_SET
- `gate1_math.json` · 2036093a3faaf8a3d17bb94310b9485a86080ee65d25dd9be5da1f275815052a · GATE_RESULT
- `gate2_baseline.json` · 4cdb3434eeca7f2f7aca40a05c3772198a4c5a1b290860c6023ba3f974e452d9 · GATE_RESULT
- `gate3_implementation.json` · 7b9b865d292753961c7cac317785a93d03d999c751be89a287e484576bd24d52 · GATE_RESULT
- `seed_ledger.json` · 76e188807853ef1827401ecb54a5e4e881a93d651228b033af34813a8d1c7c2c · SEED_LEDGER
- `gate4_training.json` · a42fa1aa7191d940d02de0b8638bacd8102a50448acd534641392faab8d43afc · GATE_RESULT
- `training_report.json` · bb93ab0ae83f3c2b50c6f29b685cbd3b50da4ab39325dcbfa90da359f83260c4 · TRAINING_REPORT
- `gate5a_physics.json` · 60b3c385e4aec1ea2b7375c8bd05867c8c8d27537e542c9ea06216d0d3a58cff · GATE_RESULT
- `claim_set_ledger.json` · 63e1e33c0c38982a9cdfd30b0857752ca34e4dde3dd091fa37be503c2986ea5c · LEDGER
- `problem_definition.json` · b0cf6037cac2f51a3cfceb4b17845862707d101adcb08de7ef7386b29f3f7837 · PROBLEM_DEFINITION
- `gate5b_external.json` · 53ee9f22c5bc32f4d2ac428d681e4ff81f0680da31c2f3082fa3e68972e78d41 · VALIDATION_METRIC
- `run_record.json` · 60ddde96cbcf7f41828c3d7de8e78875a04bc32b56e6e029388f7fd19a3a3624 · RUN_RECORD
- `gate6_reproducibility.json` · 2cc9f7d702b50539fdc8fd29be599df65923e94b3b2343019707ae18bc85fb8b · GATE_RESULT
- `trust_vector.json` · 67a3f502916090bc309c227bb3f25f507e7b972f158e0e4f979814c67cd410d8 · TRUST_VECTOR
- `claim_statements.json` · 5aead66f5415529399cae99d7b40829f138b4638345ddc787f9008635b827905 · CLAIM_STATEMENT
- `claim_gate_decision.json` · 36af3f04e24d5bf054af1e013f9594f84fca29a399fc54846194384b372536de · CLAIM_GATE_DECISION
- `tier1_redteam.json` · 11de4a539088ca0e1b028275ccb8c05679a5772856a5dec8a4a99fd314076868 · RED_TEAM_REPORT
- `trust_vector_tier1.json` · 022cbc3c92276abccaa9f5b9ab9b06029eeebc07cc62991d812ffd6f5263c3dd · TRUST_VECTOR
- `claim_gate_decision_tier1.json` · 1e6299aabebf68867da64901118efbdd8c5ecca2e2e860b09bef3a6495d77063 · CLAIM_GATE_DECISION
- `gate6_reproducibility_executed.json` · 75c95a2c6ff692f636ed09c93924cfb566875ea8f5b4c5167a0830af538a7998 · GATE_RESULT
- `trust_vector_g6.json` · 4fe9778129cf217e831cc4fb1178e925f74fa2350c14fdea609ebcfc8ed620c4 · TRUST_VECTOR
- `claim_gate_decision_g6.json` · eadb801cc9a4cf530e925d32342775d69a2a41ab3b9aeaf7e6b87e9ec391907c · CLAIM_GATE_DECISION
- `attempt_state.json` · c53acc25363f3d01de607fbeec1b4ac76a91f05ca92f1f2f1a7f5b209917b4ea · STATE（ACCEPTED）
- `RUN_SUMMARY.json` · 5b6e17e9b3de7102883a50f1cc0958c009909644cea4c9fe79b7c2f79fde8f8c · SUMMARY

### `runs/repro-envb2d-r1`（32 个 artifact，此处略去 10 个 `runs/run-*.json`）

- `identity.json` · c36495807e1a70e5afd48a7689cb872e9f961afbb339e4195229d375dc8a228f · IDENTITY
- `seed_ledger.json` · 7c15bffe785e2be99511200596f65fec4488033df4a9af9730eb626f45e8f4dc · SEED_LEDGER
- `run_record.json` · 3456107919e4ca2eb621d05bd27715ebdaf49e76c5a23cbf9bb4146d98feb0b3 · RUN_RECORD
- `gate4_training.json` · f130d554ea77507213988208595b02be5629f2985d07231d7eb557b695603053 · GATE_RESULT
- `training_report.json` · d5931635bad172751d75ac77ca06a14ef3ec0e0e4d685a3b8e4ce3f1bc596c01 · TRAINING_REPORT
- `reproduction_report.json` · f0b5d7c77cb0e9cbe890b951860ae8c5b6c3f55f13a17d52f28e18bbd241fb17 · REPRODUCTION_REPORT
- `trust_vector.json` · f82a2c4d11db2b545819bc2d08f1260c51f508823191781382bc6ff6e8a4759d · TRUST_VECTOR
- `attempt_state.json` · 1f080d4b9ab2b3157b115b4b3e13ab54fa2f12660f08b0564d2fa232b9b995f5 · STATE
- `RUN_SUMMARY.json` · d96ea3d2f427ddd1c68cbcf2ec1d35cdd3c8bca256cecfcadd7e6656ad05accd · SUMMARY

（两个 run 的 `sets/*.json` 与 `problem_definition.json` / `claim_set_ledger.json` 哈希逐位相同，这本身就是"同一冻结规格、同一组样本"的机器证据。）

## 附录 B：图（PART 21，全部来自已登记网格与已存权重）

| 文件 | 内容 |
|---|---|
| `plots/p1_analytic_solution.png` | 解析解 u\*(x,y) |
| `plots/p2_pinn_solution.png` | PINN u_θ(x,y)（中位 seed） |
| `plots/p3_absolute_error.png` | log₁₀\|u_θ − u\*\| 热图（中位 seed） |
| `plots/p4_pde_residual.png` | PDE 残差热图（中位 seed） |
| `plots/p5_collocation_distribution.png` | 训练配点分布（run 00） |
| `plots/p6_multiseed_errors.png` | 多 seed dev 误差分布与 ε_spec |
| `plots/p7_worst_seed_error.png` | 最差 seed 误差场 |
| `plots/p8_fdm_convergence.png` | 独立 FDM 网格收敛（斜率 2 参考线） |
| `plots/p9_redteam_summary.png` | Tier-1 各扰动的 QoI 漂移与 1% / 5% 线 |

> 3.0.0 公开整理（2026-09-29）：本报告中的设备标识（machineId）与安装前缀（installationId）已替换为占位符，其余内容保持原样。
