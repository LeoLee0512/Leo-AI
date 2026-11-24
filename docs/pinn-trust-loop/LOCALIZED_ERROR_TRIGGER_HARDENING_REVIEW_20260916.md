# Localized-Error Trigger Hardening Review（2026-09-16）

执行负责人：Claude（队长）。对象：外部评审对定向源码复核包（commit `33dc22b`）的三项代码级发现。上游：[POISSON2D_CLOSURE_COMPLETION_20260916.md](POISSON2D_CLOSURE_COMPLETION_20260916.md)。

本轮**没有**重训 Poisson2D 正式 baseline、没有重开 D_claim、没有修改任何已 ACCEPTED 的机器证据 / ClaimGateDecision / TrustVector / 账本、没有调整 Poisson2D 验收阈值、没有新增 A-0003、没有开始下一个 PDE、没有继续改 portability policy。改动只落在**未来**的诊断实现上。

## 1. External Review Reproduction（PART 0）

三项发现都先**独立复现**后才动手（探针直接调用 `33dc22b` 的实现，不读评审结论）：

| Issue | Decision | Reproduced? | 复现出的机器事实 |
|---|---|---|---|
| 1 — seed 级局部失败被 ensemble median 吞掉 | **CONFIRMED** | 是 | 阈值 1e-3：0/10 → fired False；**1/10 → fired False**；**4/10 → fired False**；5/10 → fired False（median 恰 1.000e-03，不 > 阈值）；6/10 → True；10/10 → True |
| 2 — 无效数值被读成「没有失败」 | **CONFIRMED**（并复现出评审未列的两条） | 是 | all NaN → **fired False**；all −Inf → **fired False**；negative ratio −1.0 → **fired False**；NaN 占多数 → fired False。**另查出**：all +Inf → fired **True**（同样是巧合而非判定）；空 ensemble → `IndexError`（裸崩，不是领域错误）。长度不一致：`points` 2 / `errors` 3 / `reference` 3 → ratio **1.000e-05**（第三个巨大误差被 `zip` 丢弃）；补齐坐标后 ratio **1.000e+00**。**另查出**：一维坐标被接受、`blocksPerAxis = 0` 被接受、空数组 → `ZeroDivisionError` |
| 3 — criterionId 只绑定阈值不绑定 statistic | **CONFIRMED** | 是 | `criterion="AC2D-2"` + `statistic="maxTileRmsErrorOverReferenceRms"` + `threshold=5e-3` → **被接受**；同一局部误差值 2.0e-3 在 AC2D-9（1e-3）下 fired True，在借来的 AC2D-2（5e-3）下 fired **False** |

三项**全部 CONFIRMED**，无 REJECTED，无需要不同解释的条目。复现脚本与逐条输出见操作日志 §5.30。

### 1.1 Issue 1 的完整 caller chain（问题 1.2 的回答）

「seed 3 失败、其余 9 个通过」的情形，机器路径实测如下：

```text
per-seed AC2D-9 失败
  -> pinn/validation/poisson2d.evaluate_fields: failedMustCriteria = ["AC2D-9"]（该 seed）
  -> gate5b_external.json: perSeed[i].failedMust
  -> gates2d.external_checks: must_ok = all(not e["failedMustCriteria"] ...)  => G5b-acceptanceCriteriaMust = FAIL
  -> judge("external", ...) => C_external FAIL -> gate5_status => FAIL
  -> runner2d 第 753–754 行: state in (FAILURE_RECORDED, STOPPED_THE_LINE) -> phase_failure(gate=5)
  -> failure_record.json: claimSetVerdict.failedMustPerSeed 保留该 seed 的 ["AC2D-9"]
  -> failure_record.json: observedSignatures  <-- 旧实现在此处丢失 sLocalizedError
```

也就是说：**Gate 的判决本身不会丢**（`claimSetVerdict` 里有），但 `observedSignatures` 在 1/10、4/10 的情形下**不含** `sLocalizedError`，于是 `admissible_root_causes` 拿不到对应的候选根因集合——正是"Gate FAIL 而 signature absent"的形态。因此 Issue 1 判 CONFIRMED，修的是**诊断可见性**，不是 Gate 判决。

## 2. Seed Aggregation Semantics（PART 1）

三个层级在实现里现在是分开的、都可机器读出：

| 层级 | 定义 | 记录位置 |
|---|---|---|
| **A. Acceptance criterion** | 每个 seed：`maxTileRmsErrorOverReferenceRms ≤ 1e-3`（AC2D-9，MUST） | 验收合同 `LOCALIZED_ERROR_CRITERION`；Gate 5b 在 claim 网格上判 |
| **B. Per-seed failure** | 某 seed 的统计量 > 阈值 | `perSeedValues[]`、`failingSeedIndices[]`、`failureCount`、`failureFraction` |
| **C. Ensemble FailureSignature** | 整个 N-seed 实验是否登记 `sLocalizedError` | `fired` + `firedBy`，由**判据自己的 seedPolicy** 决定 |

**聚合规则不是新发明的**：`seedPolicy = "every-seed"` 取自验收合同，而合同里的这条正是 Gate 5b 对 MUST 判据一直执行的策略——`gates2d.external_checks` 的 `must_ok = all(not e["failedMustCriteria"] for e in evaluations)`。一个 seed 失败即验收失败，因此一个 seed 失败即症状成立。

为避免"value 说没超、fired 说超"的自相矛盾，`value` 现在取该策略下的**决定性统计量**（worst seed），median 降为 `medianStatistic` / `ensembleStatistic.median` 只作记录。

**1.4 的不变量（已机器化）**：对 k = 0…10，
`localized_signature(...)["fired"]` **恰好等于** `gates2d.external_checks` 在同样 per-seed 结果上的 `G5b-acceptanceCriteriaMust != PASS`。
既不更弱（不会静默丢失真实失败），也不更严（没有造出比 Gate 更严的新 Claim 判据）。测试：`test_the_ensemble_rule_is_the_gate_policy_not_a_new_ratio`。

诊断可见性：`apply_localized_signature` 把 `perSeedValues / failingSeedIndices / failureCount / failureFraction / ensembleStatistic / firedBy` 整体写进 `dev_diagnostics.json` 的 `localizedErrorTrigger`，即使 `fired=False` 也写。

## 3. Input Validity（PART 2）—— fail-closed invariants

全部使用仓库已有的 `pinn.validation.poisson2d.ValidationInputError`（其文档串本就是"Invalid evidence must never be coerced into a finite, accepted result"），不新造异常体系。

| 不变量 | 违反时 |
|---|---|
| 每个 seed 的统计量必须是**实数**、**有限**、**非负** | `ValidationInputError`（NaN / ±Inf / 负值 / 非数值全部拒绝） |
| ensemble 非空 | 拒绝：「an empty ensemble is not a passing ensemble」 |
| 每个 seed 记录必须携带该统计量 | 拒绝，并指名是第几个 seed |
| `len(points) == len(errors) == len(reference)`，**在任何 `zip` 之前断言** | 拒绝；不截断、不补齐、不忽略 |
| 证据非空 | 拒绝 |
| 点集维数齐次且 ≥ 2 | 拒绝 |
| 坐标有限且落在单位域 `[0,1]` 内 | 拒绝（否则分块会把域外点钳进边界块） |
| `errors` / `reference` 每个分量有限（允许带符号，误差本就是有符号差） | 拒绝非有限值 |
| `blocksPerAxis` 是 `int` 且 ≥ 1（`bool` 不算 `int`） | 拒绝 |
| 参考场 RMS > 0（相对判据的分母） | 拒绝：相对判据无定义 |
| 退役的 1D 统计量若非有限，**丢弃**而不是参与聚合 | `retiredStatistic` 不写入 |

生效位置：`validate_evidence_fields()` 同时被 `block_statistics()` 与 `localized_acceptance_ratio()` 调用（**两处都验**，不依赖调用方）。关于 2.4 的上游审计：真实入口 `diagnostics2d.dev_diagnostics` 用同一批 `dev_points` 生成 `errors` 与 `exact`，长度天然一致；但科学证据校验层不应依赖 `zip` 的静默语义，所以本模块保留自己的最小防御不变量。

## 4. Criterion Binding（PART 3）—— 正式合同

单一真相源：`pinn/governance/poisson2d_contract.py`

```python
LOCALIZED_ERROR_CRITERION = {
    "criterionId":    "AC2D-9",
    "statisticId":    "maxTileRmsErrorOverReferenceRms",
    "normalization":  "globalReferenceRms",
    "partitionKind":  "uniformTiles",
    "tilesPerAxis":   8,                 # = TILES_PER_AXIS
    "operator":       "<=",
    "threshold":      1e-3,              # = CRITERIA 里 AC2D-9 的阈值
    "level":          "MUST",            # = CRITERIA 里 AC2D-9 的等级
    "seedPolicy":     "every-seed",      # = Gate 5b 对 MUST 的既有策略
    "dimensionScope": ">=2",
    "definition":     METRICS["AC2D-9"][0],
    "evaluationGrid": METRICS["AC2D-9"][1],
}
localized_criterion(criterion_id="AC2D-9") -> dict   # 解析器，非局部判据 / 未知 id 一律 ValueError
```

阈值、等级、分块数、定义全部**从既有冻结表推导**，没有引入任何新常数（测试 `test_the_contract_is_the_single_source_of_truth` 钉死）。

调用方只写 `criterion`，其余字段必须与合同**逐项相等**，否则拒绝。以下全部 fail closed：

| 情形 | 结果 |
|---|---|
| criterionId 未知（如 `AC2D-42`） | 拒绝：not an acceptance criterion |
| criterionId 存在但不是局部判据（`AC2D-1`、`AC2D-2`） | 拒绝：not the localized-error criterion |
| statistic 不符（`D-referenceConditionedZ`、`maxBinToMedianBinRatio`） | 拒绝 |
| normalization 不符（`perTileReference`、`globalErrorRms`） | 拒绝 |
| partitionKind 不符（`quadtree`） | 拒绝 |
| 分块数不符（4、16） | 拒绝 |
| operator 不符（`<`） | 拒绝 |
| threshold 不符（5e-3、1e-4） | 拒绝 |
| evaluationSet 非 `dev`（`claim`、`train`） | 拒绝：D_claim 只为验收打开一次 |
| 九个必填字段缺任一 | 拒绝 |
| 判据不在冻结 run 身份内（事后加的） | `assert_criterion_within_run_identity` 拒绝 |

评审的原始构造复测：`AC2D-2` + 局部 statistic + 5e-3 现在**被拒**；同一值 2.0e-3 在 AC2D-9 下照常 fired。

## 5. Historical C2 Impact（PART 4）

```text
NO IMPACT
```

不是凭预期，是重跑 `experiments/poisson2d/final_closure_revalidation.py`（训练解释器，不重训、不重开 claim 集）的结果：

```text
verdict            CURRENT 2D C2: CONFIRMED
problems           []                      （零错误）
finalTrustVector   math/impl/train/physics/external/repro = PASS ×6
allowed            C0, C1, C2              blocked: C3
state              ACCEPTED
cRepro             PASS
codeIdentityUnchanged  false                （工作树已不等于记录在案的身份，见第 6 节）
```

并由测试逐项断言历史证据未动：`gate5b_external.json` 的 `codeHash` 仍以 `a39aa07e23d0` 开头、十个 seed 的 `failedMust` 全空、`thresholds["AC2D-9"]` 仍为 1e-3；`claim_gate_decision_g6_p11.json` 仍是 allowed C0/C1/C2、blocked C3 且绑定同一 codeHash；正式 run 的冻结配置里 `signatureCriteria.sLocalizedError` **仍然没有** `criterion` 字段（新触发不回溯）。账本、D_claim、TrustVector、ClaimGateDecision 本轮**一次也没有写入**。

理由与机器事实一致：该 run 的 AC2D-9 是 Gate 5b 的 MUST 判据且十个 seed 全过（最差 1.568e-4 对 1e-3），按新的 `every-seed` 策略同样 `fired=False`；本轮修的是未来诊断实现。

诚实说明：`FINAL_CLOSURE_REVALIDATION.json` 与 `TEST_VERIFICATION_UNDER_TORCH.json` 因重跑而更新，diff 仅为时间戳与 `currentTreeCodeHash`（后者本就是"当前树"的量），历史字段一字未变。

## 6. Future Revision Rule（PART 5）

```text
下一次正式实验必须使用新的 revision / code identity。
本轮硬化后的 localized-error 实现不得冒充生成既有 C2 的 a39aa07e23d0…。
```

机器证据（测试 `test_the_hardened_implementation_cannot_claim_the_accepted_runs_code_identity`）：

- `pinn/experiments2d/localized_error.py` **根本不在**该 run 的 `codeManifest` 里（它是该 run 之后才建的文件）；
- `pinn/governance/poisson2d_contract.py`、`pinn/experiments2d/diagnostics2d.py`、`pinn/experiments2d/runner2d.py` 三个在清单内的文件，当前 sha256 均 ≠ 记录值；
- 用当前字节重算清单 → `code_hash_from_manifest` ≠ `a39aa07e23d0…`。

已 ACCEPTED 的决策仍绑定**记录在案的那个身份**（字节可由承载该 run 的提交恢复）。

## 7. Test Evidence（PART 6 / PART 8）

| 项 | 值 |
|---|---|
| 上一轮基线 | 1172 passed / 0 failed / 18 skipped |
| 本轮新增测试 | **69**（`tests/pinn/test_localized_error_hardening.py`；另 `test_localized_error_trigger.py` 按新合同更新） |
| 全套（治理 `.venv`） | **1241 passed / 0 failed / 18 skipped** |
| 被跳过的 18 项在训练解释器下 | `verify_tests_under_torch.py`：**23 passed / 0 failed** |
| portability（PART 7，只跑回归不改 policy） | **0 hard binding / 1 configurable default / 8 historical evidence**——无回归，未改任何规则 |
| PRELOCK | **7/7 PASS** |
| unexpected failures | **0** |

新增测试覆盖（对照 PART 6 清单）：

- **Seed aggregation**：0/10、1/10、2/10、4/10、5/10、6/10、9/10、10/10 八档，逐档断言 `failingSeedIndices`、`failureCount`、`failureFraction`、`fired`、`value` 与 `fired` 自洽；评审的 1/10 与 4/10 专测；诊断记录可见性专测；Gate 等价不变量 k = 0…10。
- **Numeric validity**：NaN、+Inf、−Inf、负值、极小负值、单个坏 seed 混在好 seed 中、空 ensemble、缺字段、零参考 RMS、NaN 坐标、域外坐标、一维坐标、参差点、blocks = 0 / 负 / 小数 / 布尔。
- **Truncation**：points 短、errors 短、reference 短三种排列；外加评审原始数值探针（截断后 vs 对齐后答案不同）。
- **Contract binding**：15 组错配（含 AC2D-2 借阈值、错 statistic、错 normalization、错 partition、错 operator、错 threshold、claim/train 评估集）、九个必填字段逐个缺失、单一真相源自洽、事后判据不得触发已有 run。
- **Existing Poisson2D fixture**：已完成 run 的十个 AC2D-9 实测值仍不触发；合成热点仍触发；真实形态的非均匀场不触发。

## 8. Repository State

```text
git status   : clean（本报告与日志提交后）
branch       : master
commit       : 见本报告所在提交
历史证据     : 未修改（账本 / D_claim / TrustVector / ClaimGateDecision / 冻结配置 / 阈值）
本轮改动     : pinn/governance/poisson2d_contract.py（新增局部判据合同，阈值表未动）
               pinn/experiments2d/localized_error.py（seed 策略 + fail-closed 校验 + 合同绑定）
               experiments/poisson2d/{smoke_runner2d.py, LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json}
               tests/pinn/{test_localized_error_hardening.py（新）, test_localized_error_trigger.py}
               experiments/poisson2d/{FINAL_CLOSURE_REVALIDATION, TEST_VERIFICATION_UNDER_TORCH}.json（重跑，仅时间戳与当前树 codeHash）
portability  : 未改 policy（PART 7）
```

## 9. Final Decision（PART 10）

```text
LOCALIZED ERROR TRIGGER:
HARDENED

CURRENT POISSON2D C2:
UNCHANGED / CONFIRMED

NEXT FORMAL EXPERIMENT IMPLEMENTATION:
READY
```

本轮既没有让 `sLocalizedError` 更容易触发，也没有让它更难触发：它现在使用**合法、完整、预注册且正确绑定**的证据；真实的 seed 级失败不会被统计聚合静默丢掉；无效数据永远不会被解释成"没有失败"。

## 10. STOP

不开始新的 PDE、不设计新几何、不启动 BFS、不改宪法、不重训 Poisson2D、不继续改 portability policy。等待用户与外部评审。
