# Leo AI Studio — P0 最终收口报告

> 状态口径只允许：`PASS` / `FAIL` / `PARTIAL` / `BLOCKED` / `NOT TESTED`。
> **`NOT TESTED` 不并入 `PASS`。** 不使用「基本通过」「预计可用」「理论上可行」。
>
> 本报告是**新文件**。`docs/P0_RELEASE_CANDIDATE.md`、`docs/P0_EXECUTION_STATUS.md`
> 与 `修改报告Claude.md` 未被改写，它们记录的是当时的状态。

---

## 0. 最终判定

```
P0-6 = FAIL
```

原因不变：**P0-4 与 P0-5 的实机部分仍是 `NOT TESTED`**，27 项人工验收一项都没有由人执行过。
本轮把「可自动判定的部分」推到了尽头，但没有、也不能把人工项变成 PASS。

不进入 PINN / Workspace / Companion / 前端 fork / 新 Skill / 新产品功能。

---

## 1. 分类结论（A/B/C/D/E）

### A. 已程序化 PASS（本机自动化证据）

| 项 | 证据 |
|---|---|
| 全量测试 | **409 passed / 0 failed / 0 skipped** |
| research-sop 全部套件 | 94 passed（core 12 + reconstructed 41 + semantics 20 + mutation 13 + lean 8） |
| 两处复核语义修正 | 20 项 `test_research_sop_semantics.py`，对 round-1 kernel **15/20 失败**、对原始 kernel **20/20 失败** |
| 变异测试 | 13 项，7 个变异中 **6 个被杀死**，第 7 个存活并已写明原因（见 §4） |
| 可移植性静态扫描 | `0 hard binding, 1 configurable default`，exit 0；新增 17 个文件 **0 hard binding** |
| wheelhouse 生成 | 21 wheel / 21 pin，11 MB |
| wheelhouse 校验 | `0 problem(s)`，exit 0 |
| 离线安装 | 全新 venv，`--no-index --find-links wheelhouse` **21 个包全部装上**，exit 0 |
| 构建环境审计 | `.venv` 与 `requirements.lock` **逐项一致**，0 problem |
| UI API 契约 | 10 passed |

### B. 已实机 PASS（这台机器上真的跑起来了）

| 项 | 证据 |
|---|---|
| hermetic clean build | exit 0，`PACKAGE CONTRACT PASSED: 315 _launcher files, 16 critical, 24 archive modules` |
| **连续两次 hermetic build** | 都成功。修复前**第二次必然失败**（见 §5） |
| hermetic 产物实际运行 | scratch 安装树中 `LeoAIStudio.exe --diagnostics` **exit 0** 并写出报告 |
| 产物真的连上了 WSL 桥 | `preflight` 返回 `wsl=true, bwrap 0.9.0, non_root=true`；`status` 返回 `running=true, revision=a792c38d9984…, runtime=0.2.0-2eb33f7bf139` |
| 构建产物 SHA-256 | `B20024E01C1F763D4E2E4DE9100B5C81E260B87DCBD29788559D54906062FC81` |
| upstream 解析边界实测 | 见 §6，对 pinned upstream 实跑 9 种输入 |

> ⚠️ `--diagnostics exit 0` 的含义是**报告写出来了**，不是「一切健康」。
> 这是 `leo_shell/app.py` 文档化的契约（`0` = 正常运行，`1` = 启动/诊断失败）。
> 上一轮报告把它列为构建证据是对的，但它不能被读成健康检查。

### C. FAIL

| 项 | 状态 | 说明 |
|---|---|---|
| strict verifier | **3 FAIL / 6 PASS** | 提交后为 `leo commit` / `skill hashes` / `skills deployed+daemon` FAIL——manifest 描述的是**上一次部署**，本轮变更**有意未部署**。见 §9。 |
| P0-6 | **FAIL** | P0-4 / P0-5 仍是 PARTIAL |

### D. NOT TESTED

27 项人工验收**全部保持 `NOT TESTED`**。详见 §7。
E1/E2/E3 另有一个结构性原因：**仓库里根本没有可以无头驱动五角色链的入口**（§6）。

### E. 仍需人工决定（本轮不猜，写进报告）

1. **upstream fence 解析是否要改。** 三个可复现的边界（§6）都在 pinned upstream 里，
   且是**有意的设计权衡**。`manifests/upstream-pin.json` 要求 upstream 保持字节干净，
   `verify_release.py` 会因漂移而失败。改它 = 改「与 upstream 的关系」，不是修 bug。
   选项：(a) 向上游提 PR；(b) 建立受控 patch 层并接受 P0-1 口径变化；(c) 在 role prompt 里
   约束输出格式（不改代码）。**本轮未选。**
2. **是否要建 headless 五角色入口。** 这是产品公开面的设计决定（§6）。
3. **`theme/` 资产归属。** 构建从 `<AppRoot>/theme` 读取图标与主题，仓库里没有。
   全新 clone 仍需外部提供（§8）。是否把资产纳入仓库，是架构决定。
4. **是否要部署本轮变更。** P0-6 = FAIL 时发布，我认为不该做，所以没做（§9）。

---

## 2. 修改文件列表

### 新增

| 文件 | 作用 |
|---|---|
| `tools/build_wheelhouse.py` | wheelhouse 生成 / 校验 / 离线安装 / 环境审计 |
| `tools/provision_venv.ps1` | 从声明输入建 `.venv`，优先离线，无 wheelhouse 且未传 `-AllowIndex` 时**硬失败** |
| `tools/manual_acceptance/_common.py` | 采集器公共层：verdict 词表、证据格式、编码安全 |
| `tools/manual_acceptance/collect_windows_account_env.py` | A 区块 |
| `tools/manual_acceptance/verify_webview2_runtime.py` | B 区块 |
| `tools/manual_acceptance/verify_wsl_environment.py` | C 区块 |
| `tools/manual_acceptance/verify_lean_real_toolchain.py` | D 区块 |
| `tools/manual_acceptance/verify_research_sop_live.py` | E 区块 + provider-neutral 失败分类器 |
| `tools/manual_acceptance/verify_clean_build.py` | F 区块 |
| `tools/manual_acceptance/run_all.py` | 一键采集 |
| `manifests/wheelhouse.json` | 21 个 wheel 的 filename / package / version / 三个 tag / SHA-256 / size / origin |
| `manifests/test-suites.json` | 测试套件出处登记：reconstructed vs reviewer-original |
| `tests/skills/test_research_sop_semantics.py` | 两处语义修正 + run/manifest/history 审计（20） |
| `tests/skills/test_research_sop_mutation.py` | 变异测试（13） |
| `tests/test_wheelhouse.py` | wheelhouse（32） |
| `tests/test_suite_provenance.py` | 套件出处可执行化（10） |
| `tests/test_manual_acceptance.py` | 采集器不得自证（19） |
| `docs/BUILD.md` | 构建文档 |
| `docs/P0_FINAL_CLOSURE_REPORT.md` | 本文件 |
| `docs/rollback/build_launcher.pre-P0-closure.ps1` | 回滚依据 |
| `docs/rollback/portability_check.pre-P0-closure.py` | 回滚依据 |

### 修改

| 文件 | 改动 |
|---|---|
| `tools/build_launcher.ps1` | 修复第 6 处旧发布件耦合；hermetic 增加环境审计门槛与 wheelhouse 状态记录 |
| `tools/portability_check.py` | 豁免机制改为「类别 + 逐行标记」，新增 `EXEMPT_KINDS` |
| `skills/research-sop/kernel.py` | **仅注释**：在 `sop_read_stage` / `sop_read_manifest` 写清两处修正语义 |
| `skills/research-sop/SKILL.md` | 新增两节：产物缺失 = 重跑；prompt 改变 = incompatible 但可审计 |
| `skills/research-sop/README_zh.md` | 同上（中文） |
| `manifests/dependency-lock.json` | `vendored_wheelhouse: true` + wheelhouse 段 + `sdist_build_allowed` |
| `tests/test_portability.py` | 新增 4 项豁免纪律测试 |
| `tests/test_build_reproducibility.py` | 重写 wheelhouse 诚实性测试；新增 3 项第 6 处耦合回归 |
| `tests/skills/test_research_sop_integrity_adversarial.py` | **仅文件头 docstring**：写明它不是复核方的文件 |
| `.gitignore` | 忽略 `wheelhouse/` 与 `docs/manual-acceptance-evidence/` |

**没有删除任何文件。** 工作树里原本有一处 `docs/P0_EXECUTION_STATUS.md` 被删（未提交），
已 `git checkout` 还原。

---

## 3. 两处复核语义修正

### A. 「paper 文档被删后必须返回 `paper=None`」——错

**正确语义**：阶段产物缺失 ⇒ 该阶段不再 complete ⇒ **重跑该阶段并产出真实新文档**。
`paper=None` 只在撰写员确实产不出文档时才是诚实答案。

**代码现状**：一致，无需改行为。`sop_read_stage` 对 `ROLE_REQUIRES_DOCUMENT` 返回 `None`，
`orchestrate_research` 随即 `sop_run_role` 重跑。

**残留旧断言**：**没有**。原有 41 项对抗测试里
`test_missing_paper_document_forces_a_rerun_rather_than_a_stale_claim` 的注释已经写着
「The property is not "paper becomes None"」。

**本轮补的**：
- `kernel.py` 在 `sop_read_stage` 处写明「早期描述说必须返回 paper=None，那是错的」；
- `SKILL.md` / `README_zh.md` 各新增一节；
- 5 项回归测试，含参数化的「文档被清空」与「文档被删除」两种形态、上游有效阶段不得被重跑、
  中途阶段记录消失也要重跑、`paper=None` 的正确适用场景。

**一处比预期更强的行为**：文档写不回去时 `sop_write_stage` 读回校验失败并 **raise**，
整轮停下，而不是返回 `paper=None`。测试按实测行为断言（`pytest.raises(RuntimeError)`），
不按我最初的猜测。

### B. 「prompt 修改后旧 run 仍可作为 valid run 使用」——错

**正确语义**：旧 run 字节保留、可审计，但相对新 prompt **不再是 valid-compatible run**，
应分类为 `incompatible`，不得静默当成新 prompt 下的有效证据。

**代码现状**：一致。`MANIFEST_INCOMPATIBLE` 已存在，`sop_manifest_compatibility` 比对
`role_prompt_hashes` / `pipeline_version` / `role_order` / `schema_version`，
`sop_read_manifest` 对它返回 `None`，`sop_inspect_manifest` / `sop_list_runs` 仍返回内容。

**本轮补的**：
- `kernel.py` 在 `sop_read_manifest` 写明三件同时成立的事（字节在 / 可审计 / 不是新 pipeline 的证据），
  并点名「早期描述把这件事说反了」；
- 文档两节；
- 6 项回归测试：字节逐一比对不变、分类为 `incompatible` 且**不是** `corrupt`、
  manifest 仍可读回、`sop_list_runs` 仍列出、新 run 五个角色全部重跑、
  新 run 的阶段路径不得指向旧 run。

---

## 4. 41 项 reconstructed adversarial suite 状态

| 项 | 值 |
|---|---|
| 文件 | `tests/skills/test_research_sop_integrity_adversarial.py` |
| 收集用例数 | **41**（26 个测试函数，其余来自 `parametrize` 展开） |
| 当前 kernel | **41 passed** |
| round-1 kernel（`docs/rollback/research-sop-kernel.pre-P0-2-round2.py`） | **32 failed / 9 passed** |
| 是否被改名 | **否** |
| 是否被删减 | **否**，26 个函数名全部锁定在 `manifests/test-suites.json` |
| 本轮改动 | **仅文件头 docstring**（写明出处、指向登记表、指出两处语义修正在别的文件里） |

**保护机制**（`tests/test_suite_provenance.py`，10 项）：

- `locked_test_functions` 列出 26 个函数名，少一个就红；
- `minimum_collected_cases: 41`，由**子进程调用 pytest 实收**核对，不是重算 parametrize；
- 文件自身 docstring 必须含 "reconstruct" 与 "not supplied"；
- 复核方文件保留独立路径 `test_research_sop_integrity_adversarial_reviewer.py`，
  且断言它 **≠** 现有文件路径；
- 报告文档若引用 41 这个数字，必须同时写明它是 reconstruction。

### reviewer original tests 状态

```
status = ABSENT / NOT PROVIDED
```

登记在 `manifests/test-suites.json` → `pending_confirmations`：

> P0-2 在本仓库证据上保持 `PASS`。**复核方的独立确认是另一回事，尚未发生。**
> 在他们的文件到位并在此跑过之前，这一条作为 release caveat 保留。

**P0-2 = `PASS` 不变**，但「独立确认未完成」是必须继续携带的 caveat。

### 新增的套件分类

| id | 出处 | 状态 | 用例 |
|---|---|---|---|
| `research-sop-core` | leo-authored | PRESENT | 12 |
| `research-sop-adversarial-reconstructed` | **reconstructed** | PRESENT | 41 |
| `research-sop-adversarial-reviewer-original` | **reviewer-original** | **ABSENT** | — |
| `research-sop-corrected-semantics` | leo-authored | PRESENT | 20 |
| `research-sop-mutation` | leo-authored | PRESENT | 13 |

### 变异测试：一个存活的变异，如实记录

7 个变异中 6 个被杀死。第 7 个——把「manifest JSON 解析失败」从 `CORRUPT` 改标为 `MISSING`
——**存活**：`sop_resolve_run` 通过 `sop_run_branches` 找到这个 run，而后者看的是目录里有没有
东西，不是 manifest 能不能解析；未知状态因此落到 fork 分支，损坏字节得以保留。

这是**代码的纵深防御**，不是测试失效。已在文件里写明，并补了一个**确实能打破该性质**的变异
（让损坏的 run 对分支发现不可见 → manifest 被就地覆盖 + 旁边的阶段文件被采纳），该变异被杀死。

变异测试若「改了却全绿」而不记录，与「测试什么都没测」无法区分——所以写下来。

---

## 5. wheelhouse 实现状态

### 已做到

| 能力 | 状态 | 证据 |
|---|---|---|
| 生成脚本 | ✅ | `tools/build_wheelhouse.py build` |
| manifest | ✅ | `manifests/wheelhouse.json`：filename / package / version / python_tag / abi_tag / platform_tag / SHA-256 / size / origin / resolution |
| lock ↔ wheelhouse 逐项对应 | ✅ | 双向：lock 有而 wheelhouse 无 → `missing-wheel`；wheelhouse 有而 lock 无 → `unlocked-package` |
| `--no-index --find-links` 离线安装 | ✅ | 全新 venv 实测 21/21 装上 |
| 缺 wheel 时明确 FAIL | ✅ | 见下 |
| 自动测试 | ✅ | 32 项 |

### 实测发现：`proxy_tools==0.1.0` 在 index 上**只有 sdist**

第一次 `build` **正确地硬失败**：

```
ERROR: Could not find a version that satisfies the requirement proxy_tools==0.1.0 (from versions: none)
[FAIL] pip download (published wheels) failed; the wheelhouse was not completed.
```

也就是说：**这套依赖集无法只用已发布 wheel 组出完整 wheelhouse。**

处理方式是显式且可审计的，不是静默回落：

- 允许源码构建的包名写在 `manifests/dependency-lock.json` → `sdist_build_allowed`（**数据，不是命令行开关**）；
- 记录 sdist 的 SHA-256 `ccb3751f…`（这是它可校验的身份）；
- manifest 条目标 `origin: built-from-sdist`；
- 不在名单上又没有 wheel 的包，一律硬失败。

### 又一个实测发现：本地构建的 wheel **字节不稳定**

同一台机器上相隔几分钟构建同一个 sdist，产出 wheel 的 SHA-256 不同
（`4013c8e8…` → `c85fbaec…`，zip 条目带构建时间戳）。

manifest 因此**不**声称跨机器字节一致，而是写明：对这类条目要校验 **sdist 哈希**，
wheel 自己的哈希只描述「现在这个文件」。

### 顺带修好的两处

1. `requirements.lock` 的哈希原来按**原始字节**算。`.gitattributes` 让 Windows 检出 CRLF、
   其他平台 LF，同一份提交在两台机器上哈希不同 → 误报 `requirements-drift`。改为按**规范化文本**算。
2. `resolution.pip` 原来存 `pip 24.3.1 from C:\Users\user\...`，把作者 home 写进了**受版本控制的 manifest**——
   正是 `portability_check.py` 要抓的那类缺陷。改为只存版本号。

### 不入 git 的理由

`wheelhouse/` 已 gitignore（11 MB 二进制）。入库的是 manifest：每个 wheel 一个 SHA-256，
足以校验别人建出来的 wheelhouse。`manifests/dependency-lock.json` → `wheelhouse.committed = false` 明写。

### 边界

> **「这台机器能生成并校验 wheelhouse」≠「全新机器 clean build PASS」。**
> 后者是 F1 / F2，仍 `NOT TESTED`。这句话同时写在 `build_wheelhouse.py` 的输出里、
> `docs/BUILD.md` 里，并由 `tests/test_wheelhouse.py` 断言其存在。

### 附带：环境审计

新增 `audit-env`：比对 `.venv` 实装内容与 `requirements.lock`
（`not-installed` / `version-drift` / `undeclared-package`，venv 自带的 pip/setuptools/wheel 除外）。

**hermetic 构建现在把它当硬门槛**。在此之前，「从 requirements.lock 构建」说的是意图——
构建实际用的是 `.venv` 里碰巧装着的东西。本机实测 `0 problem(s)`。

---

## 6. 五角色链与 harness 解析边界

### 实测的三个解析边界（对 pinned upstream `a792c38d`，只读导入，未改一字节）

| 输入 | `extract_action` | `incomplete` |
|---|---|---|
| ` ```python ` … ` ``` ` | ✅ cell | false |
| 裸 ` ``` ` … ` ``` ` | ✅ cell | false |
| **` ```python ` 内再出现一个 ` ```python `，然后一个 ` ``` `** | ❌ **无 cell** | **true** |
| **用 ` ```python ` 收尾而不是裸 ` ``` `** | ❌ **无 cell** | **true** |
| **` ```python3 `** | ❌ **无 cell** | false |
| ` ```Python `（大写） | ✅ cell | false |
| 前导空格 | ✅ cell | false |
| cell 内嵌 ` ```tool ` 示例 | ✅ cell | false |

第 3 行**精确对应 flash 的症状**：模型在闭合前又发一个带标签的 fence → 外层永不闭合 →
harness 回 `INCOMPLETE_CELL_NUDGE` → 模型再自我纠正 → 循环。

根因在 `openai4s/tools/registry.py::scan_fenced_blocks`：块内**带 info 的** fence 会**入栈**
（被当作嵌套示例），只有**裸** fence 才出栈。这是**有意的**——为了让 cell 里引用的
` ```tool ` 示例不把 cell 截断。

第 5 行：`PYTHON_INFOS = ("", "python", "py")` 不含 `python3`，这类回复被当作**完全没有代码**。

### 结论

**这是模型 / harness 兼容问题，不是 research-sop 缺陷。** 编排逻辑由 94 项测试覆盖。
按指示**没有**把它错修成 research-sop 的问题，也**没有**为了跑通而放宽 integrity。

### 为什么没做「最小修复」

修复点在 upstream。`manifests/upstream-pin.json` 要求 checkout 保持字节干净，
`tools/verify_release.py` 会因漂移而 FAIL——这是 P0-1 = PASS 的组成部分。
改 upstream = 改「与 upstream 的关系」，是架构决定，不是 bug fix。
**按指示停止该项并写入报告，不猜。** 见 §1.E。

也**没有**加针对某个模型的脆弱 hardcode：
`tests/test_manual_acceptance.py::test_the_classifier_is_provider_neutral`
断言 runner 代码里不出现任何厂商名。

### provider-neutral live acceptance runner

`tools/manual_acceptance/verify_research_sop_live.py`：

- `--transcript <file>`：拿**上游真正的 parser**（只读导入）给一段模型回复定性。
  实测四种输入分别得到 `ok` / `unclosed-cell` / `unexecutable-info-string` / `repetition`。
- `--live`：检查每一个前置条件并报告哪些成立。

失败分类（6 类）：`no-action-in-reply` / `unclosed-cell` / `unexecutable-info-string` /
`repetition` / `schema-rejected` / `orchestration`。最后一类被明确标注为
「**这一类才会是 research-sop 自己的问题**」，好让「不属于这一类」成为可核对的陈述。

### 一个必须承认的缺口

**仓库里没有可以无头驱动 `orchestrate_research` 的入口。**
`tools/headless_verify.py` 验证的是 daemon 生命周期（preflight / status / start / url / http / stop），
不是 skill 编排。

我第一版给它编造了 `--status` / `--research-sop` / `--provider` 等**并不存在的参数**——
那会做出一个「看起来跑了验收项、其实没有」的工具。已删除，改为如实报告缺口。
（这个错误也导致第一次采集把「daemon 不可达」报错了；修正后实测 daemon **可达**。）

要不要建这个入口，是产品公开面的设计决定，见 §1.E。

### E1 / E2 / E3

```
E1 = NOT TESTED
E2 = NOT TESTED
E3 = NOT TESTED
```

本机实测前置条件：

| 前置 | 结果 |
|---|---|
| upstream 干净 | ✅ `a792c38d9984` |
| daemon 可达 | ✅ preflight + status 都 ok |
| provider / model 已指定 | ❌ 未指定（不默认任何厂商） |
| 凭证 | ❌ `OPENAI_API_KEY` 未设置 |
| 无头五角色入口 | ❌ **不存在** |

**没有伪造，没有 simulated PASS。**
工具明写：不会去别处找 key，也不会用找到的 key——真实跑一次要花钱、要调外部服务。

---

## 7. 27 项人工验收当前状态

```
PASS 0   FAIL 0   NOT TESTED 27
```

采集器**不能**改动 checklist。`tests/test_manual_acceptance.py`（19 项）用 AST 静态断言
`tools/manual_acceptance/` 下没有任何代码写向 checklist 路径，且 verdict 词表里
**拼不出** "SIMULATED PASS" / "PROBABLY PASS" 之类。

本机实际采到的事实（**这些是观察，不是验收结论**）：

| 区块 | 本机观察 |
|---|---|
| A（7） | 账户 SID 已记录；`%LOCALAPPDATA%\leo-ai-studio` 尚不存在；无 `LEO_STUDIO_ROOT` 覆盖。A1–A5 是**目视项**，脚本看不到 |
| B（3） | 系统 Evergreen `152.0.4191.62`；固定版 `152.0.4191.53` 可定位，唯一 `msedgewebview2.exe`，将 pin 到其父目录 → **本机是 B1 场景**，但 B1 要求的是**新机器** |
| C（5） | 只有 `Ubuntu-24.04` 一个发行版，默认用户就是配置值 → **C1/C2 在本机无法被行使**；`--discover` 输出与 `wsl.exe` 一致 → **C5 在本机可判定为 PASS**（仍需人确认写入） |
| D（6） | `lean` / `lake` / `elan` 都不在 PATH；`lean_toolchain_status()` 返回 `NOT_INSTALLED` → **本机是 D1 场景**；`.elan` 目录在调用前后**状态不变**（D6 的正向观察）。**真实求值仍是 0 次** |
| E（3） | 见 §6 |
| F（3） | 本机**有**旧发布件 → **不是 F1 环境**；四项外部输入全部齐备；wheelhouse 校验通过；环境审计 0 problem |

采集器同时暴露了 3 个自身缺陷并已修好：
`wsl.exe` 的 UTF-16LE 输出在 GBK 机器上让 subprocess reader 线程崩溃、
JSON 输出遇到非 GBK 字符时 `print` 抛异常整个采集器倒掉、
B 区块的判定比 `leo_shell/webview2_runtime.py` 更严格（会把正确的嵌套布局误判为 FAIL）。

证据文件写到 `docs/manual-acceptance-evidence/`（**已 gitignore**：里面必然含主机名与
操作者 home 目录，那正是不该进仓库的东西）。

---

## 8. clean-machine 状态

```
F1 = NOT TESTED
F2 = NOT TESTED
F3 = NOT TESTED
```

本轮把「全新机器构建」从**不可能**推进到**可能但未验证**：修复前，一台没装过旧版的机器
连输入检查都过不了（§5 的第 6 处耦合）。

全新 clone **仍需**从仓库外提供的四项，已逐项列出：

| 输入 | 来源 | 为什么 |
|---|---|---|
| `python312.dll` | 声明 Python 的 base prefix | PyInstaller bootloader ABI |
| `ffi-8 / sqlite3 / libbz2 / liblzma / libexpat` | `<base_prefix>/Library/bin`（conda 布局） | 少了它们，冻结后在 `import _ctypes` 就死，到不了 `main()` |
| upstream OpenAI4S checkout | `manifests/upstream-pin.json` 指定 revision | 构建把它的身份写进 manifest |
| `<AppRoot>/theme` + WebView2 固定版运行时 | 随应用分发 | 图标与主题；没有可加载的运行时则窗口全黑 |

`theme/` 不在仓库里，是**架构问题**，见 §1.E。

---

## 9. 构建 / verifier / git

### 构建

| 项 | 结果 |
|---|---|
| hermetic clean build | **exit 0** |
| 包契约 | `315 _launcher files, 16 critical files, 24 archive modules` |
| 连续第二次 build | **exit 0**（修复前必然失败） |
| 产物 SHA-256 | `B20024E01C1F763D4E2E4DE9100B5C81E260B87DCBD29788559D54906062FC81` |
| hermetic 日志 | 记录 python312.dll 来源、环境审计结果、wheelhouse 状态 |

#### 本轮最重要的一个发现：第 6 处旧发布件耦合

`docs/P0_RELEASE_CANDIDATE.md` 记的是「五处耦合全部已 guard」。**还有第六处，而且没被 guard**：

```powershell
$webviewHooks = Join-Path $launcherDeps 'webview\__pyinstaller'   # 旧发布件里的路径
...
'--additional-hooks-dir', $webviewHooks
```

它在**无条件**的必需输入列表里。而且它**自我作废**：hermetic 构建的产物里**没有**
`webview/__pyinstaller`，所以一旦部署了一次 hermetic 产物，**下一次构建必然失败**。

实测就是这样失败的：

```
Required build input is missing: C:\...\LeoAIStudio\_launcher\webview\__pyinstaller
```

这解释了为什么上一轮能记录一次成功构建——那次用的是**尚未被 hermetic 产物替换掉的**旧 `_launcher`。

**修复**：hermetic 模式从**安装好的 pywebview 包**取 hooks（它本来就自带），
`-Legacy` 保留旧来源；旧 onedir 与旧 EXE 从无条件必需列表移到 `if (-not $Hermetic)` 里；
`Assert-SafeBaselineTree -Root $launcherDeps` 同样只在 legacy 下跑。

**为什么之前的测试没抓到**：`test_every_dependency_on_a_previous_release_is_guarded`
枚举的是「已经被发现的那五处」，因此无法报出没人发现的第六处。**是把构建真跑一遍才发现的。**
已补 3 项回归测试。

### strict verifier

```
6 PASS   3 FAIL   0 NOT TESTED
```

两次都是 **6 PASS / 3 FAIL / 0 NOT TESTED**，但失败项在提交前后不同——两次都记下来，
因为这正好说明每一项 FAIL 各自在说什么：

| 检查 | 提交前 | 提交后（最终） |
|---|---|---|
| leo commit | PASS `ede34d28322d` | **FAIL** — manifest `ede34d28322d` != HEAD `58aeb1961968` |
| repo clean | **FAIL** — 21 个未提交文件 | PASS |
| source hashes | PASS | PASS |
| deployed bundle | PASS `a9600ae6b536` | PASS `a9600ae6b536` |
| deployed exe | PASS `bc25544257c0` | PASS `bc25544257c0` |
| skill hashes | **FAIL** | **FAIL** — research-sop 的 kernel/README/SKILL 与部署副本不同 |
| skills deployed+daemon | **FAIL** | **FAIL** — 6 个文件与 canonical 不同 |
| upstream revision | PASS `a792c38d9984` | PASS `a792c38d9984` |
| upstream clean | PASS | PASS |

**这三个 FAIL 都是正确的。** manifest 描述的是**上一次部署**（`ede34d2` + 那次的 EXE）；
本轮改了 research-sop 的注释与文档并已提交，但**没有部署**，所以 manifest 既对不上新 HEAD，
也对不上新的 skill 哈希。

**为什么不部署**：P0-6 = `FAIL` 时发布一个版本是错的。发布顺序（改码 → 测试 → commit →
repo clean → clean build → **deploy** → manifest → strict verify）是**发布**流程，
本轮是**收口**。是否部署由人决定，见 §1.E。

> 所以：**strict verifier 现在不是绿的，本报告不把它写成绿的。**

### git

| 项 | 值 |
|---|---|
| 改动前 HEAD | `ede34d28322d9fe0d56f82f37182066afffd9fcf` |
| 本轮 commit | `58aeb1961968` |
| 分支 | `master` |
| 提交后工作树 | 干净（`git status --porcelain` 为空） |
| 改动前工作树 | 一处 `docs/P0_EXECUTION_STATUS.md` 被删（未提交）→ **已还原** |
| 删除的文件 | **0** |
| 改写的历史报告 | **0** |
| 回滚依据 | `git reset --hard ede34d2` + `docs/rollback/build_launcher.pre-P0-closure.ps1` + `docs/rollback/portability_check.pre-P0-closure.py` |
| 新增/修改 | 21 新增 + 10 修改（31 个路径） |

---

## 10. 全量测试数量

```
.venv/Scripts/python -m pytest tests -q  ->  409 passed
```

（写本报告之前是 `408 passed, 1 skipped`：唯一的 skip 是 `test_suite_provenance.py`
检查本报告是否已写出。本文件写出后该项转为实跑，并断言凡引用 41 这个数字的报告
都必须同时写明它是 reconstruction。）

| 文件 | 用例 |
|---|---|
| `tests/leo_shell/test_api.py` | 70 |
| `tests/skills/test_research_sop_integrity_adversarial.py` | **41** |
| `tests/leo_shell/test_theme_runtime.py` | 39 |
| `tests/leo_shell/test_settings_store.py` | 34 |
| `tests/test_wheelhouse.py` | **32** |
| `tests/leo_shell/test_bridge_client.py` | 23 |
| `tests/skills/test_research_sop_semantics.py` | **20** |
| `tests/test_manual_acceptance.py` | **19** |
| `tests/leo_shell/test_paths.py` | 19 |
| `tests/leo_shell/test_secrets_store.py` | 15 |
| `tests/skills/test_research_sop_mutation.py` | **13** |
| `tests/skills/test_research_sop.py` | 12 |
| `tests/test_ui_api_contract.py` | 10 |
| `tests/test_suite_provenance.py` | **10** |
| `tests/leo_shell/test_connection.py` | 10 |
| `tests/test_portability.py` | 9 |
| `tests/skills/test_lean_math_discovery.py` | 8 |
| `tests/leo_shell/test_app_startup.py` | 7 |
| `tests/test_build_reproducibility.py` | 9 |
| `tests/leo_shell/test_single_instance.py` | 5 |
| `tests/leo_shell/test_webview2_runtime.py` | 4 |

上一轮 308 → 本轮 409（新增 101）。

| 分类 | 数量 |
|---|---|
| passed | 409 |
| failed | **0** |
| skipped | 0 |
| **NOT TESTED（实机）** | **27** |

### 起点是红的

接手时 `HEAD = ede34d2` 的全量测试是 **307 passed / 1 failed**，不是上一轮报告里的 308 passed：
`tools/portability_check.py` 把 `docs/P0_RELEASE_CANDIDATE.md` 里作为负向对照被引用的
`/home/someone/...` 判成了硬绑定。308 那个数字是在**提交那份报告之前**测的。

修法不是把文件加进豁免名单（每写一份新报告就会再红一次），而是：

- `docs/**/*.md` 作为**类别**豁免（散文里写路径不是绑定到路径）；
- 新增逐行 `portability-allow: <rule>` 标记，规则粒度，不能顺手静音别的绑定；
- 新增 `EXEMPT_KINDS`：豁免只允许覆盖 `frozen-evidence` / `documentation` / `the-scanner-itself`，
  由 `test_no_executable_or_consumed_file_is_exempt` **遍历每个受版本控制文件**断言——
  任何可执行 / 被构建消费的文件都豁免不了。

---

## 11. 剩余风险

1. **复核方的原始对抗测试仍未提供。** P0-2 = PASS 建立在本仓库自建的 41 项上。
   独立确认未发生，作为 release caveat 保留（`manifests/test-suites.json`）。
2. **27 项人工验收一项都没跑过。** 这是 P0-6 = FAIL 的直接原因。
3. **五角色链从未真正跑通过。** 且**没有**无头入口可跑。
4. **upstream fence 解析的三个边界仍在。** 未改 upstream（有意为之），需人决定。
5. **`proxy_tools` 只能本地源码构建。** wheelhouse 因此不是纯已发布 wheel 组成；
   本地构建的 wheel 字节不稳定，只有 sdist 哈希是稳定身份。
6. **`python312.dll` 与 `Library/bin` 来自这个具体的 conda 安装。** 换 Python 发行版需重新验证。
7. **`theme/` 与 WebView2 运行时不在仓库里。** 全新 clone 不足以构建。
8. **strict verifier 3 FAIL。** 本轮变更未部署（有意为之）。
9. **legacy 构建路径仍在**（`-Legacy`），会明确打印 not reproducible。
10. **旧 `research-sop/` 固定路径遗留文件**仍可能存在于会话工作区；有测试断言它们不会被采纳为证据。
11. **`--diagnostics` exit 0 只代表报告写出来了**，不代表健康。契约如此，但容易被误读为健康检查。

---

## 12. P0-1 ~ P0-6 最终 Gate 表

| Gate | 状态 | 依据 | 本轮变化 |
|---|---|---|---|
| **P0-1** 单一可信源码 | `PASS` | upstream 干净且在 pin 上；verifier 的 commit/source-hash/upstream 项 PASS | 不变；未改 upstream 一个字节 |
| **P0-2** research-sop 证据完整性 | `PASS` | 94 项 research-sop 测试（含 41 项 reconstructed adversarial、20 项语义、13 项变异）；32/41 对修复前 kernel 失败 | 加强：两处语义修正可执行化、套件出处可执行化。**caveat：复核方原始测试仍 ABSENT** |
| **P0-3** Visible UI 与 ShellApi 一致 | `PASS` | `tests/test_ui_api_contract.py` 10 passed | 不变 |
| **P0-4** 可移植性 | `PARTIAL` | 静态：0 hard binding（含新增 17 个文件）；**27 项实机 `NOT TESTED`** | 加强：豁免机制不再能藏绑定；新增采集器；修好 3 个采集器自身缺陷 |
| **P0-5** 构建可复现 | `PARTIAL` | wheelhouse 可生成/可校验/可离线消费；环境审计成为硬门槛；**第 6 处旧发布件耦合已修**；**clean-machine 构建 `NOT TESTED`** | 大幅加强，但实机部分仍未验证 |
| **P0-6** 下一阶段 Gate | **`FAIL`** | P0-4、P0-5 均非 PASS | 不变 |

```
P0-6 = FAIL
```

**停止。** 不进入 Phase 1 / PINN / Workspace / Companion / 前端 fork / 新 Skill。

### 要让 P0-6 变 PASS，仍然需要

1. 有人执行 `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` 的 27 项并把结果填回去
   （`tools/manual_acceptance/` 现在会把事实采好，但**不会替人下结论**）；
2. 一台没装过旧版的机器上从干净 clone 构建成功（F1 / F2），外加同 commit 两次构建的差异说明（F3）；
3. 用真实模型跑通五角色链（E1–E3）——这需要先决定要不要建无头入口；
4. 复核方的原始对抗测试到位并在此跑过（P0-2 的独立确认）。

在那之前 P0-6 保持 `FAIL`。
