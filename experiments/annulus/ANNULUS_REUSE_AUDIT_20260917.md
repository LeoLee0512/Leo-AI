# Annulus Reuse Audit（Geometry Lift 1，2026-09-17）

对象：`pinn/experiments2d/`（square-2D，已 CLOSED @ C2）、`pinn/validation/`、`pinn/governance/`、`scientific_reference/`、`pinn/experiments/`（1D 共享件）。
原则（本轮指令第 10 节）：**不要为了一个圆环把仓库改写成通用 geometry framework**；只泛化真正需要的接口。
硬约束：square-2D 与 1D 都已 CLOSED，改它们的模块会移动其结果所绑定的代码身份 —— 因此默认**不改**，新建 `pinn/experiments_annulus/`。

分类口径：`REUSE_AS_IS` / `GEOMETRY_GENERALIZATION_REQUIRED` / `ANNULUS_SPECIFIC` / `DO_NOT_REUSE`。

## 1. 治理层（全部原样复用）

| 模块 | 分类 | 理由 |
|---|---|---|
| `pinn/governance/evaluation_sets.py`（样本身份、sampleSetHash、互斥、最小间距） | **REUSE_AS_IS** | 样本身份与互斥是坐标无关的；圆环只是换了点的来源。schema 未扩展（见 §3）。 |
| `pinn/governance/claim_set_ledger.py`（SEALED → OPENED → BURNT，账本推导状态） | **REUSE_AS_IS** | 生命周期与几何无关；圆环只需**新建自己的 claim pool**。 |
| `pinn/governance/trust_vector.py` / `state_machine.py` / `trust_loop.py` | **REUSE_AS_IS** | 六维向量、状态机、弱链、ClaimGateDecision 与几何无关。**未新增 Gate、未新增 TrustStatus**。 |
| `pinn/governance/prelock.py` | **REUSE_AS_IS** | 与几何无关。 |
| `pinn/governance/canonical.py` / `jsonschema_lite.py` / `nodes.py` | **REUSE_AS_IS** | 规范化哈希、schema 校验、反碰撞。 |
| `pinn/experiments/common.py`（代码身份、ArtifactStore、环境指纹） | **REUSE_AS_IS** | 上一轮刚做完完整性审计；圆环的 driver 通过 `codeIdentityExtraFiles` 声明进入清单。 |
| `pinn/experiments/gates.py` 的 `check` / `dimension_status` / `pass_fail` / `gate4_training` | **REUSE_AS_IS** | 多 seed 训练完整性（成功率、离散度、worst seed、发散）是几何无关的判据。 |
| `pinn/experiments/diagnosis.py` 的 `observed_signatures` | **REUSE_AS_IS** | 症状规则本身与几何无关；只有**局部误差触发**需要几何原生分块（见 §2）。 |
| `pinn/experiments/datasets.py` 的 `cgl_unit` / `gauss_legendre_unit` | **REUSE_AS_IS** | 一维节点族，被用在**面积分数 t** 上而不是半径上。 |
| `pinn/experiments/pinn_torch.py` 的 `rel_l2` / `select_collocation` | **REUSE_AS_IS** | 与几何无关。 |

## 2. 需要几何泛化的接口（只泛化这些）

| 对象 | 分类 | 处理 |
|---|---|---|
| 局部误差**触发语义**（seed 策略、fail-closed、判据强绑定） | **GEOMETRY_GENERALIZATION_REQUIRED** | 语义原样沿用 2026-09-16 的硬化版；**分块**换成几何原生的等面积单元。实现落在 `pinn/experiments_annulus/localized_error_annulus.py`，从 `experiments2d.localized_error` 复用公开的 `criterion_failed`，并由测试钉死两实现对任意 k/N 的判定一致。**没有**把 2D 模块改写成分块框架（它属于 CLOSED 实验）。 |
| 验收合同的形状（criterionId ↔ statistic / normalization / partition / operator / threshold / level / seedPolicy） | **GEOMETRY_GENERALIZATION_REQUIRED** | 同一形状，新建 `pinn/governance/annulus_contract.py`：阈值继承但**每条带 geometry 判定**（GEOMETRY-INVARIANT / SENSITIVE / NEW-GEOMETRY METRIC）。 |
| 边界法向导数接口 | **GEOMETRY_GENERALIZATION_REQUIRED** | 从"由坐标推断边"改为 `normal_derivatives(model, points, component)` —— **component 必须显式传入**，因为同一半径公式配错组件会给出看似合理的错号。符号由 `pinn/geometry/annulus.py` 唯一拥有。 |
| 模型的硬约束因子 | **GEOMETRY_GENERALIZATION_REQUIRED** | `u = (R²−s)(s−a²)N`，且随 P8 的域缩放一起缩放（square 版是 `x(1−x)y(1−y)N`）。 |

## 3. 圆环专有（新建）

| 模块 | 分类 | 说明 |
|---|---|---|
| `pinn/geometry/annulus.py` | **ANNULUS_SPECIFIC** | 几何合同：成员判定、等面积采样、两组件边界节点与外法向、常雅可比求积、等面积单元。 |
| `pinn/reference/analytic_annulus.py` | **ANNULUS_SPECIFIC** | 制造解、解析源项、冻结尺度常数、闭式积分与通量。 |
| `scientific_reference/annulus_polar_fdm.py` | **ANNULUS_SPECIFIC** | 独立极坐标 FDM（numpy only，**不 import 任何 `pinn`**，仓库既有规则）。 |
| `pinn/validation/annulus.py` | **ANNULUS_SPECIFIC** | 可信校验器 + 10 个负面控制夹具。 |
| `pinn/experiments_annulus/{datasets,pinn_torch,gates,diagnostics,localized_error,runner,...}_annulus.py` | **ANNULUS_SPECIFIC** | 与 `pinn/experiments2d/` 平行，不修改后者。 |

## 4. 明确不复用

| 对象 | 分类 | 理由 |
|---|---|---|
| square-2D 的 claim pool 与其样本 | **DO_NOT_REUSE** | 指令第 14 节：必须新建圆环自己的盲集池；复用正方形的点既无意义也会污染身份。 |
| square-2D 的 `datasets2d` 张量网格构造（`gauss_legendre_square`、`cgl_interior_square`、四边 boundary_nodes） | **DO_NOT_REUSE** | 全部假设矩形；在圆环上会把点放进洞里或域外。 |
| square-2D 的 8×8 笛卡尔分块（AC2D-9 的 partition） | **DO_NOT_REUSE** | 会跨越洞、单元面积不等、部分单元为空（合同第 ACA-9 条已写明）。 |
| square-2D 的 `poisson2d_fdm`（五点差分） | **DO_NOT_REUSE** | 矩形网格无法贴合曲边；圆环用极坐标 FDM。 |
| 1D / 2D 的 runner | **DO_NOT_REUSE**（改写会移动已 CLOSED 实验的代码身份语义） | 与 2D 轮次同一先例：新建平行 runner，1D/2D 的 runner 一行未改。 |
| PH5-monotonicity（square 的物理检查） | **DO_NOT_REUSE**（登记 NOT_APPLICABLE） | 圆环上非径向调制使任何单调方向不成立；其信息由 PH6 与 ACA-9 承担。 |
| PH4-symmetry | **DO_NOT_REUSE**（登记 NOT_APPLICABLE） | 制造解刻意非对称，没有可测的互换对称性；不为"多一项检查"制造假对称。 |

## 5. 未扩展的东西（有意为之）

- **EvaluationSet schema 未扩展**：几何信息写在 ProblemDefinition 与几何报告里，不写进样本清单；扩了 schema，圆环的集合就不再能与已 CLOSED 实验的集合比较。
- **未新增 Gate、未新增 TrustStatus、未新增 FailureSignature / RootCause 类**。几何相关的新检查全部落在 Gate 3（T11 membership / T12 normal orientation / T13 quadrature Jacobian）与 Gate 5a（PH8 geometry membership）之内。
- **未改 `tools/portability_check.py` 与豁免清单**（上一轮的收口，本轮不动）。

## 6. 代码身份

本轮新增的全部模块都落在 `pinn/`、`scientific_reference/` 前缀内，因此自动进入下一次正式 run 的 `codeManifest`；位于前缀之外的 driver（`experiments/annulus/*.py`）按上一轮建立的机制通过 `config["codeIdentityExtraFiles"]` 声明。正式 run 必须使用**新的 revision / code identity**，不得复用 square-2D 的 `a39aa07e23d0…`。
