# Portability Audit（2026-09-16，2D 轮次追加审计）

用户指令：最终报告必须报告真实的 full-suite 状态，不得写成 0 failed，不得静默豁免或修改历史证据；另须单独检查本轮 2D 新证据是否新增同类绝对路径污染。**本文件不修改 portability policy、不修改任何证据文件、不新增豁免条目**，裁决留给用户与外部评审。

扫描器：`tools/portability_check.py`（规则与豁免清单 `manifests/portability-historical-evidence.json`，条目需人工审批，按 file + sha256 + finding_type + occurrence 精确匹配，任何字节变化都使豁免失效）。

## 1. 真实测试状态

| 口径 | 结果 |
|---|---|
| HEAD `e7d85c2`（本轮开始前，只含 1D 证据） | **1109 passed / 3 failed / 6 skipped** |
| 1D 收口报告 `POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md` 第 9 节记载 | 1112 passed / 0 failed / 6 skipped |
| 差异原因 | 收口提交 `32eaa36` 把含绝对路径的 G6 证据文件入库**之后没有重跑测试**；三项 portability 断言自那一刻起为 FAIL。不是本轮引入。 |

失败的三项（同一组发现的三种断言）：

- `tests/test_portability.py::test_no_hard_machine_bindings_in_tracked_sources`
- `tests/test_portability.py::test_exact_path_hash_and_finding_are_reported_as_historical_evidence`
- `tests/test_portability.py::test_human_output_keeps_the_historical_findings_visible`

## 2. 发现清单（当前 HEAD + 本轮新增）

### 2.1 既有（1D，pre-existing，本轮未碰）

| 文件:行 | 规则 |
|---|---|
| `experiments/poisson1d/environment_b_qualification.json:42` | windows-user-home |
| `experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json:103` | windows-user-home |
| `experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json:103` | desktop-path |
| `experiments/poisson1d/runs/repro-envb-r2/POST_AUDIT_ANNOTATION.md:19` | windows-user-home |

来源：1D 的 G6 需要在仓库外新建 Environment B 与冻结检出，其构造描述与 provenance note 写进了绝对路径。这些是**不可变历史证据**（1D 已 CLOSED），本轮不改、不注解、不豁免。

### 2.2 本轮 2D 新增（同类污染，**必须单独报告**）

| 文件:行 | 规则 | 内容 | 性质 |
|---|---|---|---|
| `experiments/poisson2d/TEST_VERIFICATION_UNDER_TORCH.json:4` | windows-user-home | `"executable": "C:\\Users\\<user>\\mamba\\python.exe"`（此处用户名已脱敏，见第 6 节） | 证据（测试验证记录，记录用哪个解释器跑了被跳过的测试） |
| `experiments/poisson2d/environment_b_qualification.json:46` | windows-user-home | `constructionB`: `... at C:/Users/<user>/LeoAI-envB2D-20260916/venv; pip install ...`（此处用户名已脱敏，见第 6 节） | 证据（G6 环境构造描述） |
| `experiments/poisson2d/qualify_environment_b.py:45` | windows-user-home | 生成上一条的源码字符串字面量 | **源码**，不是证据 |

净增 **3 条**（2 条在证据文件、1 条在新源码）。失败的测试数量仍是 3（断言是"不存在任何未豁免的 BINDING 发现"，与发现条数无关），但发现总数由 4 增至 7。

### 2.3 没有复发的一类

1D 的 `PROVENANCE_MANIFEST.json` 污染源于复现时把**绝对**账本路径传给了 runner。本轮复现 run `repro-envb2d-r1` 的 provenance note 为相对路径 `experiments\poisson2d\ledger\pdef-poisson2d-cal-v1.json`，**未复发**。

## 3. 与科学结论的关系

宪法 28.1 明文：**"hostname、用户名、路径不是身份"**。环境身份由 `environmentId`（强字段的规范化哈希）承担，其中与安装位置相关的是 `installationId = sha256(prefix)[:16]`，本身已是哈希。因此上述绝对路径在证据里是**描述性文字**，删除或改写不会改变任何 specHash / codeHash / environmentId，也不改变 G6 的独立性判定或任何 AC 数值。

结论：这是**仓库可移植性卫生问题**，不是科学有效性问题；但它确实让 full-suite 无法为绿，且本轮把它从 4 条扩大到 7 条。

## 4. 本轮不做的事

- 不修改 `manifests/portability-historical-evidence.json`（新增条目需人工审批，用户在本轮开始时的裁决是"只如实记录，不动"）。
- 不修改 1D 的任何历史证据文件。
- 不修改本轮已提交的 2D 证据文件（`TEST_VERIFICATION_UNDER_TORCH.json`、`environment_b_qualification.json`）——改写已入库证据同样需要用户审批。
- 不改 `tools/portability_check.py` 的规则。

## 5. 留给用户 / 外部评审的裁决项

1. 1D 的 4 条：加历史证据豁免条目（file + sha256 + 类型 + 条数精确匹配），还是保留红色状态？
2. 本轮 2D 的 2 条证据：同上处理，还是批准重新生成这两个文件、把绝对路径换成不含用户名的描述（例如"仓库外新建 venv，prefix 哈希见 installationId"）并重新提交？
3. `experiments/poisson2d/qualify_environment_b.py:45` 是**源码**而非证据，可以直接改为不含用户名的写法而不触及任何证据；是否批准？（改它不影响 codeHash：`experiments/` 不在代码身份前缀内。）
4. 是否给"证据文件里的绝对路径"制定一条常设规则（例如：环境构造描述只写 prefix 哈希与依赖，不写路径），避免下一轮再次扩大。

在裁决之前，最终报告按真实状态报告：**full suite 有 3 项 FAIL，全部来自 portability，其中 4 条发现是 1D 既有、3 条是本轮 2D 新增。**

## 6. 自指效应（本节是本轮发现的一部分，如实记录）

第一版本审计写完提交后重新扫描，发现**审计文件自己**多出 2 条 `windows-user-home` 发现：第 2.2 节的表格逐字引用了被指认的绝对路径，而 `experiments/**` 在扫描范围内。也就是说，"如实引用问题字符串"这一行为本身会被计为同类问题。

处理（**只改本轮自己写的审计说明文字，不改任何证据、不改 policy、不加豁免**）：第 2.2 节表格中的两处引用把用户名脱敏为 `<user>`，被指认文件的真实内容一字未动，三条实质发现照常报告。

扫描范围的事实（读 `tools/portability_check.py`）：`docs/**.md` 与仓库根的一份报告作为**类别豁免**（"docs 下的 Markdown 是关于机器的文档，不是对机器的绑定"），因此操作日志、2D 报告、两份根报告即使写了环境路径也不计入；`experiments/**`（含 `.md`）在扫描范围内。

计数（本文件脱敏之后的最终状态）：

| 口径 | 条数 |
|---|---|
| 1D 既有（不可变历史证据） | 4 |
| 本轮 2D 新增（实质） | 3 |
| 本轮 2D 新增（审计文件自指，已脱敏消除） | 2 → 0 |
| **当前总计** | **7** |

失败的测试仍是 3 项（断言是"不存在未豁免的 BINDING 发现"，与条数无关）。
