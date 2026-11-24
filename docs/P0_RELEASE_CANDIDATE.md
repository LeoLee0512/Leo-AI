# Leo AI Studio — P0 Release Candidate 报告

> 状态口径只允许：`PASS` / `FAIL` / `PARTIAL` / `BLOCKED` / `NOT TESTED`。
> 不使用「基本通过」「预计通过」「应当没问题」。
> **`NOT TESTED` 不并入 `PASS`。**

---

## 1. 最终判定

```
P0-6 = FAIL
```

| Gate 项 | 状态 | 依据 |
|---|---|---|
| P0-1 单一可信源码 | `PASS` | strict verifier 9 PASS / 0 FAIL / 0 NOT TESTED |
| P0-2 research-sop 证据完整性 | `PASS` | 53 项测试，其中 41 项对抗测试；32 项对修复前 kernel 失败 |
| P0-3 Visible UI 与 ShellApi 一致 | `PASS` | gated bridge + mutation test 实测生效 |
| P0-4 可移植性 | `PARTIAL` | 静态 0 hard binding；**27 项实机验收 `NOT TESTED`** |
| P0-5 构建可复现 | `PARTIAL` | hermetic 可构建、可运行；**无 vendored wheelhouse**，clean-machine 构建 `NOT TESTED` |

**P0-4 与 P0-5 不是 `PASS`，因此 P0-6 = `FAIL`。**
未进入 PINN / Workspace / Companion / 前端 fork / 新 Skill。

---

## 2. 最终提交与产物

| 项 | 值 |
|---|---|
| Leo commit | `d4ff12e18f36`（生成 manifest 时 `git status --porcelain` 为空） |
| upstream OpenAI4S | `a792c38d9984be428437b548db29baab3322f6dc`（工作树干净） |
| 部署 EXE SHA-256 | `BC25544257C065449360A3879C3849D53C1802031BF8AD3F3A4BD268083EBE43` |
| 部署 bundle | `a9600ae6b536`（前 12 位） |
| 构建方式 | **hermetic**（无任何来自旧发布件的输入） |
| 回滚点 | `.leo-rollback-20260903-073354` |

发布顺序按要求执行：改代码 → 测试 → commit → repo clean → clean build → deploy →
生成 manifest → strict verify。

---

## 3. 测试证据

### A. research-sop

| 套件 | 结果 |
|---|---|
| `tests/skills/test_research_sop.py` | **12 passed**（Case A–E + manifest/绑定/哈希归一化） |
| `tests/skills/test_research_sop_integrity_adversarial.py` | **41 passed** |
| 同一 41 项 vs 修复前 kernel | **32 failed, 9 passed** |

对抗测试是按二次复核报告 §2.4/§5 的描述**独立重建**的——
复核方的原始 `test_research_sop_integrity_adversarial.py` 被提及但未随附。
拿到后应当**并存运行，不替换**。

### B. UI

| 项 | 结果 |
|---|---|
| `tests/test_ui_api_contract.py` | **10 passed** |
| mutation：追加未 gate 的 `window.pywebview.api.list_entity_states({})` | **2 failed**（契约测试正确拦截） |
| 撤销 mutation 后 | **10 passed** |
| 注入层中字面量 `pywebview.api.<name>` 出现次数 | **0** |

### C. 可移植性

| 项 | 结果 |
|---|---|
| `tools/portability_check.py` | **0 hard binding, 1 configurable default**，exit 0 |
| `tests/test_portability.py` | **6 passed**（含负向对照：植入 `/home/someone/...` 必须被抓到） |
| `tests/skills/test_lean_math_discovery.py` | **8 passed** |
| 新 Windows 账户 / 非 `leo` 的 WSL 用户 / 其他 distro / Lean 未装 | **`NOT TESTED`** |

### D. 构建

| 项 | 结果 |
|---|---|
| hermetic clean build | exit 0，`PACKAGE CONTRACT PASSED: 315 _launcher files, 16 critical, 24 archive modules` |
| hermetic 产物实际运行 | scratch 安装树中 `--diagnostics` **exit 0** 并写出报告 |
| 部署后 EXE 启动 | `running=True responding=True window='Leo AI Studio'` |
| WSL2 E2E (`headless_verify.py`) | preflight / status / start / url / http-root / http-health / stop **全部 ok** |
| `tests/test_build_reproducibility.py` | **6 passed** |
| strict verifier | **9 PASS / 0 FAIL / 0 NOT TESTED**，exit 0 |
| 无旧发布件的机器上 clean build | **`NOT TESTED`** |

### E. 全量

```
.venv/Scripts/python -m pytest tests -q   ->   308 passed
```

| 分类 | 数量 |
|---|---|
| passed | 308 |
| failed | 0 |
| skipped | 0 |
| **NOT TESTED（实机，见 §4）** | **27** |

---

## 4. `NOT TESTED` / `BLOCKED` 清单

全部 27 项在 `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`，摘要：

| 区块 | 项数 | 为什么不能自证 |
|---|---:|---|
| A 全新 Windows 账户 | 7 | 无法创建 Windows 用户账户；DPAPI 按用户加密 |
| B WebView2 | 3 | 需要没装过运行时的机器 |
| C WSL2 | 5 | 只有一个发行版和一个用户名可测 |
| D Lean | 6 | 本机没有 Lean 工具链；发现逻辑用假目录测过，真实求值没有 |
| E 五角色链真实运行 | 3 | 见下 |
| F 构建可复现 | 3 | 需要一台从未装过旧版的机器 |

**E 区块的已知障碍**（2026-09-03 实测，非本轮引入）：
`deepseek-v4-pro` 在此 harness 下退化成复读；`deepseek-v4-flash` 反复自我纠正却
发不出 fenced Python cell。两次都没走完五角色链。这是模型与 harness 的工具调用
兼容问题，不是 research-sop 缺陷——编排逻辑由 53 项自动化测试覆盖。

**没有 `BLOCKED` 项。** P0-5 剩下的部分（wheelhouse）是未做，不是被阻塞。

---

## 5. 剩余风险

1. **无 vendored wheelhouse**：wheel 仍从 PyPI 解析。`manifests/dependency-lock.json`
   明写 `vendored_wheelhouse: false`，不伪称离线可复现。
2. **`python312.dll` 来自 conda base prefix**：hermetic 构建依赖这个具体的 Python 安装
   提供该 DLL 与 `Library/bin` 下的原生库。这是**声明的工具链**依赖，不是旧发布件依赖，
   但换 Python 发行版需要重新验证。
3. **首次 commit 之前无历史**：既成事实。
4. **legacy 构建路径仍在**（`-Legacy`），它会明确打印「not reproducible」。
5. **旧的 `research-sop/` 固定路径遗留文件**仍可能存在于会话工作区；新代码不读它们
   （路径不同），且有测试断言不会被采纳为证据，但没有主动标记为 legacy。

---

## 6. 回滚

| 变更 | 回滚方式 |
|---|---|
| 部署 | `.leo-rollback-20260903-073354` |
| research-sop kernel | `docs/rollback/research-sop-kernel.pre-P0-2.py`（round 1 前）、`...-round2.py`（round 2 前） |
| leo-inject（2C 前） | `docs/rollback/leo-inject.pre-2C.js` |
| lean-math kernel（2D-A 前） | `docs/rollback/lean-math-kernel.pre-2D-A.py` |
| deploy_release（2D-A 前） | `docs/rollback/deploy_release.pre-2D-A.ps1` |
| build_launcher（2D-B 前） | `docs/rollback/build_launcher.pre-2D-B.ps1` |
| 版本控制本身 | 删除 `.git/`，不影响任何工作文件 |

---

## 7. 下一步

按指示**停止**。不进入 Phase 1、PINN、Workspace、Companion、前端 fork。

要让 P0-6 变成 `PASS`，需要：

1. 有人执行 `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` 的 27 项并填回结果（P0-4、P0-5 的实机部分）；
2. 建立 vendored wheelhouse 或明确接受「从 PyPI 解析」作为可复现的定义（P0-5）；
3. 复核方的原始对抗测试文件到位后并跑一次（P0-2 的独立确认）。

在那之前 P0-6 保持 `FAIL`。
