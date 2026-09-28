# 2D_REUSE_AUDIT（2026-09-16）

PART 3 交付物：在写任何 2D 代码之前，对现有仓库逐模块判定复用等级。原则：**Generalize only what the experiment actually needs**；不把 runner 改写成通用 PDE 框架，不改 1D 历史 evidence，不新增 Gate。

判定等级：

- `REUSE_AS_IS` — 与空间维数无关，2D 直接调用，不改一行。
- `MINIMAL_GENERALIZATION_REQUIRED` — 结构可用，只需按 2D 需要做最小扩展（新增参数或并行的 2D 实现），不改 1D 行为。
- `1D_HARDCODED` — 与单变量强绑定，2D 需要独立实现（新文件），1D 文件保持不动。
- `NOT_APPLICABLE` — 本轮 2D 实验不使用。

## 1. 治理层（`pinn/governance/`）

| 模块 | 判定 | 依据 |
|---|---|---|
| `canonical.py` | REUSE_AS_IS | 纯 JSON 规范化 / 哈希，无维数概念 |
| `evaluation_sets.py` | REUSE_AS_IS | sample identity = `canonical_sha256({inputs:[float64...], quantity})`，`inputNames` 任意长度；`validate_evaluation_set` 已强制"每个样本坐标数 = len(inputNames)"；`disjointness_errors` 的 `minSeparation` 用欧氏距离，天然二维。**注意性能**：`_min_separation` 是 O(N·M) 纯 Python，2D 集合规模大时代价显著（见第 6 节） |
| `claim_set_ledger.py` | REUSE_AS_IS | 事件链 + `sampleSetHash` 身份（1D 的 L4s/L6/L7/L8 修复直接继承） |
| `trust_loop.py`（`validate_problem_definition` / `validate_trust_vector` / `validate_run_record` / `validate_claim_gate_decision` / `validate_diagnosis_record`） | REUSE_AS_IS | 校验的是结构、交叉引用、账本一致性、specHash；对 `geometry.dimension` 只要求 ≥ 1，对变量个数无上限 |
| `trust_vector.py`（`TrustStatus` / `CheckResult` / `dimension_status_from_checks` / `seed_statistics` / `claim_gate` / `independent_environments` / `reproduction_status` / `seed_set_id`） | REUSE_AS_IS | 六维、弱链演算、多 seed 统计、G6 判定与维数无关 |
| `state_machine.py` | REUSE_AS_IS | 状态机、Gate 路由、FailureSignature 到 RootCauseClass 的三元组与维数无关 |
| `locking.py` / `provenance.py` / `leakage.py` / `semantic.py` / `amendments.py` / `jsonschema_lite.py` | REUSE_AS_IS | 与问题无关的基础设施 |
| `prelock.py` | REUSE_AS_IS | 检查宪法版本 / 已锁 1D 规格与清单的字节完整性 + 修正案链；2D attempt 开始前照常必须 7/7 PASS（它不是"1D 专用"，而是"治理是否锁好"） |
| `nodes.py`（`anti_collision`） | MINIMAL_GENERALIZATION_REQUIRED | 现签名接受一维坐标序列；2D 反碰撞按坐标分量分别调用（对 x 分量与 y 分量各调用一次，见第 5 节） |
| `poisson_contract.py`（AC-1..AC-8 公式与阈值、1D 规格 / 协议合同） | 1D_HARDCODED | 公式写死一维积分与两端点边界；2D 需要独立的 `poisson2d_contract.py`（新文件，不动 1D） |
| `schemas/*.schema.json` | REUSE_AS_IS | `evaluation-set` 的 `inputs` 是数组；`problem-definition` 的 `geometry.domainType` 枚举已含 `rectangle`，`dimension` 为不小于 1 的整数；`checkApplicability` / `trust-vector` / `claim-gate-decision` / `run-record` / `diagnosis-record` 全部与维数无关 |

## 2. 参考解与独立数值基线

| 模块 | 判定 | 依据 |
|---|---|---|
| `pinn/reference/analytic_poisson.py` | 1D_HARDCODED | `u*(x)=sin(pi x)`、`EQUATION_BINDING` 为 1D 字符串。2D 需新文件 `analytic_poisson2d.py`（`u*(x,y)=sin(pi x) sin(pi y)`，含 `u_xx`、`u_yy`、梯度、`forcing`），1D 文件不动（其 sha256 写进 1D 的 ProblemDefinition 与 prelock） |
| `scientific_reference/poisson_fdm.py` | 1D_HARDCODED | 三点差分、区间网格、`refinement_diagnostic()` 返回一维序列。2D 需新文件 `poisson2d_fdm.py`（五点差分，粗/中/细三档，观测阶 p 约等于 2） |
| `pinn/validation/poisson.py`（可信校验器，AC-1..AC-8 on GL512/CGL2000） | 1D_HARDCODED | 与 1D 协议资产（`.npy` 网格、SHA 清单）硬绑定 |
| `pinn/validation/fixtures.py`（T10 控制夹具） | MINIMAL_GENERALIZATION_REQUIRED | 结构（正控制 + 若干被污染夹具）直接照搬，但函数是一维解析式；2D 需并行的二维夹具集合 |
| `pinn/validation/diagnose.py` | NOT_APPLICABLE | 1D 诊断辅助，本轮不使用 |

## 3. 实验层（`pinn/experiments/`）

| 模块 | 判定 | 依据 |
|---|---|---|
| `common.py`（`ArtifactStore`、`code_manifest` / codeHash、`environment_fingerprint`、`git_head`、`workspace_dirty_paths`、`utc_now`） | REUSE_AS_IS | 与问题无关。`CODE_IDENTITY_PREFIXES` 已含 `specs/`，因此 2D 规格放在 `specs/poisson-2d/` 即自动进入代码身份清单，**无需修改代码身份定义**（避免影响 1D 历史 codeHash 语义） |
| `criteria.py`（配对干预准则 rho / q / N） | REUSE_AS_IS | 只吃"每档每 seed 的误差列表"，与维数无关（仅在 2D 走诊断—修订路径时才会用到） |
| `repro_package.py` | MINIMAL_GENERALIZATION_REQUIRED | 打包逻辑通用，只有 attempt 目录内文件名清单与说明文本需要按 2D 调整 |
| `diagnosis.py::observed_signatures` | REUSE_AS_IS | 输入是"每 seed 的测量字典 + seed 统计 + 预注册 criteria"，键名与维数无关 |
| `diagnosis.py::dev_diagnostics` | 1D_HARDCODED | 一维排序分箱、`u''`、两端点、一维通量。2D 需并行实现（二维分箱 / 热点坐标 / 四边界 / 散度通量） |
| `diagnosis.py::run_intervention` / `exclusion_records` / `diagnosis_record` | MINIMAL_GENERALIZATION_REQUIRED | `diagnosis_record` 与 `exclusion_records` 的结构可复用；`run_intervention` 调用一维训练器 |
| `bc_diagnosis.py` | NOT_APPLICABLE | 软 vs 硬 BC 的诊断实验；PART 2 明令本轮直接冻结 hard BC，不再跑 soft-vs-hard 比较 |
| `claim_metrics.py`（任意 GL/CGL 网格上的 AC-1..AC-8） | 1D_HARDCODED | 一维求积与端点约束。2D 需 `claim_metrics2d.py` |
| `datasets.py` | 1D_HARDCODED | `inputNames=["x"]`、`points_of` 取 `inputs[0]`、GL/CGL 一维网格。2D 需 `datasets2d.py`（张量积求积 / 二维盲集族） |
| `pinn_torch.py` | 1D_HARDCODED | `width_in = 1`、`x` 形状为 N×1、单变量二阶 AD、`HardDirichlet = x(L-x)N`。2D 需 `pinn_torch2d.py`（输入 2、`u_xx + u_yy`、`x(1-x)y(1-y)N`） |
| `gates.py` | 结构 MINIMAL_GENERALIZATION_REQUIRED / 执行体 1D_HARDCODED | `REGISTRY`（检查登记表）的**结构**与 `check` / `dimension_status` / `pass_fail` 直接复用；每个 Gate 的**执行体**（M1–M6、T1–T10、PH1–PH7、G5b）都是一维算式，2D 需 `gates2d.py` |
| `redteam.py` | MINIMAL_GENERALIZATION_REQUIRED | 扰动矩阵、维持 1% / FAIL 5% 的判定规则、"只能维持或降级"逻辑直接复用；P1/P4/P6/P9/P16 的 `perturbation` 字典语义与维数无关；**P8（域缩放）必须重写硬 BC 参数化随域变换**（1D run 1 的 harness 缺陷，PART 18 明确点名）；P7/P11 的 Applicability 必须对 2D 重新判定，不得照搬 1D 理由 |
| `report.py::write_trust_report` | MINIMAL_GENERALIZATION_REQUIRED | 读的是 RUN_SUMMARY / trust_vector / pdef 等机器记录，结构无关维数；少数措辞需 2D 化 |
| `report.py::plots_experiment1/2` | 1D_HARDCODED | 一维曲线图。2D 需要 `report2d.py`：解面 / 误差热图 / 残差热图 / 配点分布 / 多 seed 分布 / 最差 seed 误差场 / FDM 收敛图 |
| `runner.py` | 以复制骨架实现（不改 1D 文件） | 骨架（identity 到 problem 到 G1–G3 到训练到 G4 到 validation(G5a/G5b, 开集) 到 G6 到决策；ledger / pool / revise / redteam / judge-reproduction / apply-g6）与维数无关，但 1264 行中**处处直接调用一维的 `datasets` / `pinn_torch` / `gates` / `claim_metrics`**，且模块常量 `LEDGER_DIR` / `PROBLEMS_DIR` 指向 `experiments/poisson1d/`。判定：**新建 `pinn/experiments2d/runner2d.py`，复用治理层与 `common.py`，不修改 `pinn/experiments/runner.py`**（1D 已 CLOSED，改它会改变其代码身份语义并使 1D 测试的假设漂移） |

## 4. 逐条回答 PART 3 的清单

| 问题 | 结论 |
|---|---|
| 是否已有 2D PDE abstraction | **没有**。`geometry.dimension` / `inputNames` 等 schema 字段支持任意维，但没有任何 2D 求解、参考或度量代码 |
| dataset generator 是否支持 (x,y) | **不支持**。`datasets.py` 全部产出标量坐标；但 `evaluation_sets` 的清单格式与校验支持 |
| sampleId 是否正确包含二维坐标 | **是**（`sample_identity(inputs)` 对 `[x, y]` 按 float64 逐位规范化取哈希；负零折叠为零，NaN/Inf 拒绝）。序列化冲突风险已由"坐标数必须等于 `len(inputNames)`"与 canonical JSON 的最短往返表示排除；本轮仍新增测试显式钉死两个不同二维点不得同 id（PART 22） |
| AD residual 是否支持 u_xx + u_yy | **不支持**。`_derivatives` 只对单输入求两次导。2D 实现须**分量各自求二阶导**并分别对照（PART 13：不能只验证和） |
| evaluation set schema 是否天然支持二维 | **是**（`inputs` 为数组，`inputNames` 为数组，维数一致性已校验） |
| plots 是否仅支持 1D | **是**，全部为一维曲线；2D 需新绘图模块 |
| R3 runner 哪些地方写死 1D | 模块常量 `LEDGER_DIR` / `PROBLEMS_DIR`；`build_problem_definition`（方程名、`independentVars=["x"]`、两条 BC、三个 region、`domainType="interval"`、一维规格 / 参考文件引用）；`phase_problem`（一维求积网格、`claim_pool_manifests(GL,CGL)`）；`claim_evaluation`（一维场与端点）；`phase_gate6` 的 BLOCKED 文案；`run_revise` 的 `x(1-x)N` 白名单；`run_redteam` 的一维 pool / dev |
| claim metrics 哪些地方写死单变量 | `claim_metrics.evaluate_on_grids` 全体：一维 GL 权重求和、pointwise 网格首末必须是 0 和 1、`u_boundary` 长度 2、`du_boundary` 长度 2、AC-5（积分等于 2/pi）与 AC-6（左端导数等于 pi）是一维解析常数 |
| Red Team 哪些 perturbation 可直接复用 | P1（重抽配点）、P4（float32）、P6（删 10% 配点）、P9（Adam 换 L-BFGS）、P16（tanh 换 sin）语义直接复用；P8 需要 2D 的正确缩放与硬 BC 参数化变换；P7 / P11 的适用性必须对 2D 重新判定 |

## 5. 结论：2D 需要新增的最小代码面

新增（不改 1D 任一文件）：

1. `specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json` — 冻结的 2D 数学规格（自动进入 `specs/` 代码身份前缀）。
2. `pinn/reference/analytic_poisson2d.py` — 可信解析参考。
3. `scientific_reference/poisson2d_fdm.py` — 独立五点 FDM 与网格细化诊断。
4. `pinn/governance/poisson2d_contract.py` — 2D AC 度量定义与阈值（阈值来源逐条登记，PART 10）。
5. `pinn/validation/poisson2d.py`（含 T10 控制夹具） — 可信校验器。
6. `pinn/experiments2d/` 下的 `datasets2d` / `pinn_torch2d` / `gates2d` / `claim_metrics2d` / `diagnostics2d` / `redteam2d` / `report2d` / `runner2d`。
7. `tests/pinn/test_poisson2d_*.py` — PART 22 的测试面。

反碰撞：**不修改** `pinn/governance/nodes.py`，由 `datasets2d` 对 x、y 分量分别调用现有 `anti_collision`，避免动 1D 依赖的函数。

## 6. 已知风险（写在实验之前，不等结果出来再补）

- **R-1 配点数量与离散度量代价**：`disjointness_errors` 的最小间距检查是 O(N·M) 纯 Python。2D 的 train pool 与 claim 集若各取数千点，单对比较即千万量级。缓解：控制集合规模，或按预注册把 `minSeparation` 判定限制在必要的集合对上；任何缓解都必须在冻结前写进预注册，不得在看到耗时后临时放宽。
- **R-2 训练成本**：1D 每 run 16.7 s（3x32、6000 步、batch 128、单线程）。2D 二阶 AD 分量翻倍、网络更宽、配点更多，单 run 可能上升一到两个数量级；N=10 的正式协议与 Tier-1（6 次重训）、G6（再 10 次）总量必须由 PART 4 的性能 pilot 定量后才冻结。若 N=10 不可行，按 PART 8 诚实报 `C_train = PARTIAL / BLOCKED`，不降标准仍声称 C2。
- **R-3 G6 环境**：1D 用过的 Environment B 目录已按用户审批删除（操作日志 5.25），2D 的 G6 需要重新建立一个独立安装（新 venv + 复现包声明依赖），这是仓库外的新目录，将在执行前记录、执行后等用户裁决保留或删除。
- **R-4 解析常数型判据**：1D 的 AC-5（积分 2/pi）、AC-6（左端导数 pi）在 2D 有对应量（二重积分 4/pi^2、边界法向通量），但阈值不得照搬，须按 PART 10 逐条判定 DIMENSION-INVARIANT / DIMENSION-SENSITIVE 并登记来源。
