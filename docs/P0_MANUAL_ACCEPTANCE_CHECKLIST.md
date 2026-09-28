# Leo AI Studio — P0 人工验收清单

> 这些项**无法在开发环境自证**。它们的状态一律是 `NOT TESTED`，
> 直到有人在真实环境里跑过并把结果填进本文件。
>
> **`NOT TESTED` 不得并入 `PASS`，也不得算作 P0-6 的通过条件。**
> 自动化静态检查（`tools/portability_check.py`、`tests/test_portability.py`）
> 通过**不等于**这里任何一项通过——前者只能证明源码里没有写死的路径，
> 不能证明程序在别人的机器上装得上、起得来。

填写方式：把 `NOT TESTED` 改成 `PASS` 或 `FAIL`，写上日期、环境和实际观察到的现象。
失败要写现象，不要只写「不行」。

---

## A. 全新 Windows 用户账户

**为什么必须人工**：需要创建一个新的 Windows 本地账户并在其中登录。
开发环境不能创建 Windows 用户，也不能代替另一个账户的 DPAPI 主密钥。

| # | 项目 | 期望 | 状态 | 记录 |
|---|---|---|---|---|
| A1 | 在全新账户中安装并首次启动 | 窗口正常显示，不黑屏、不最小化 | `NOT TESTED` | |
| A2 | 启动页显示 | 暖色启动页，狮标可见，两个按钮 | `NOT TESTED` | |
| A3 | 无 API key 时的行为 | **停在启动页**，不自动跳转 | `NOT TESTED` | |
| A4 | 点「先逛逛」 | 进入工作台，顶部一条浏览模式栏 | `NOT TESTED` | |
| A5 | 保存 API key 后 | daemon 重启并带上密钥，浏览模式栏消失 | `NOT TESTED` | |
| A6 | DPAPI 凭证 | 新账户下能保存并读回，且**读不到**原账户的密钥 | `NOT TESTED` | |
| A7 | 不需要改任何代码或路径 | 全程零手工修补 | `NOT TESTED` | |

**A6 特别说明**：DPAPI 按 Windows 用户加密。新账户读不到旧账户的凭证是**正确行为**，
不是缺陷。如果新账户能读到，那是严重安全问题，必须立刻报告。

---

## B. WebView2 运行时

| # | 项目 | 期望 | 状态 | 记录 |
|---|---|---|---|---|
| B1 | 新机器上加载固定版运行时 | CoreWebView2 初始化成功 | `NOT TESTED` | |
| B2 | 只装了系统版 WebView2 的机器 | 回退可用或给出明确提示 | `NOT TESTED` | |
| B3 | 完全没有 WebView2 的机器 | 明确的安装指引，而不是黑屏 | `NOT TESTED` | |

**已知的坑（回归测试 `test_webview2_runtime.py` 覆盖）**：
`WEBVIEW2_RUNTIME_PATH` 必须指向**包含** `msedgewebview2.exe` 的目录，
不能是 exe 文件本身，否则 CoreWebView2 初始化失败（0x80070002），
**窗口黑屏但进程还活着**。

---

## C. WSL2 环境

自动化只验证了本机这一个环境（`Ubuntu-24.04` / 用户 `leo`）。
路径已参数化（`LEO_WSL_DISTRO` / `LEO_WSL_USER` / `LEO_WSL_SKILLS`），
但**参数化不等于在别的取值下验证过**。

| # | 项目 | 期望 | 状态 | 记录 |
|---|---|---|---|---|
| C1 | WSL 用户名不是 `leo` | 桥接正常，技能同步到正确的 home | `NOT TESTED` | |
| C2 | 发行版不是 `Ubuntu-24.04` | 通过 `LEO_WSL_DISTRO` 可用 | `NOT TESTED` | |
| C3 | 完全没装 WSL2 | 明确的错误信息，不是崩溃 | `NOT TESTED` | |
| C4 | 装了 WSL 但没装发行版 | 明确提示 | `NOT TESTED` | |
| C5 | `sync_skills.py --discover` | 正确列出实际安装的发行版 | `NOT TESTED` | |

---

## D. Lean / Mathlib

发现逻辑有单元测试（`tests/skills/test_lean_math_discovery.py`，8 项），
但那些测试用的是临时目录里的假工具链。**没有一项验证过真实 Lean 能否求值。**

| # | 项目 | 期望 | 状态 | 记录 |
|---|---|---|---|---|
| D1 | 完全没装 Lean | `lean_toolchain_status()` 返回 `NOT_INSTALLED`，附可操作说明 | `NOT TESTED` | |
| D2 | 装了 elan 但没建项目 | 返回 `PROJECT_NOT_READY` | `NOT TESTED` | |
| D3 | 项目 pin 的版本与实际工具链不符 | 返回 `VERSION_MISMATCH` | `NOT TESTED` | |
| D4 | 环境完整 | 返回 `READY`，`lean_check` 能真正求值 | `NOT TESTED` | |
| D5 | 三个 `LEO_LEAN_*` 覆盖变量 | 各自生效 | `NOT TESTED` | |
| D6 | **不会自动安装** | 任何状态下都不下载工具链 | `NOT TESTED` | |

---

## E. 五角色链真实运行

| # | 项目 | 期望 | 状态 | 记录 |
|---|---|---|---|---|
| E1 | 用真实模型跑完整五角色链 | 五个角色都产出阶段文件 + 真实论文文档 | `NOT TESTED` | |
| E2 | 真实运行下的 run 目录结构 | `research-runs/<run_id>/` + manifest + history | `NOT TESTED` | |
| E3 | 真实的 validator 打回 | 旧证据归档到 `history/`，可读回 | `NOT TESTED` | |

**已知障碍（2026-09-03 实测，非本轮引入）**：
`deepseek-v4-pro` 在本 harness 下退化成复读；`deepseek-v4-flash` 反复自我纠正
却发不出 fenced Python cell。两次都没能走完五角色链。
这是模型与 harness 的工具调用兼容问题，不是 research-sop 的缺陷——
编排逻辑由 53 项自动化测试覆盖。换供应商后需要重跑本节。

---

## F. 构建可复现

| # | 项目 | 期望 | 状态 | 记录 |
|---|---|---|---|---|
| F1 | 在**没有**旧 `LeoAIStudio.exe` 的机器上 clean build | 构建成功 | `NOT TESTED` | |
| F2 | 从全新 clone 构建 | 构建成功 | `NOT TESTED` | |
| F3 | 同一 commit 两次构建 | 差异可解释 | `NOT TESTED` | |

---

## 汇总

| 区块 | 总数 | PASS | FAIL | NOT TESTED |
|---|---:|---:|---:|---:|
| A 新 Windows 账户 | 7 | 0 | 0 | 7 |
| B WebView2 | 3 | 0 | 0 | 3 |
| C WSL2 | 5 | 0 | 0 | 5 |
| D Lean | 6 | 0 | 0 | 6 |
| E 五角色链 | 3 | 0 | 0 | 3 |
| F 构建 | 3 | 0 | 0 | 3 |
| **合计** | **27** | **0** | **0** | **27** |

**因此 P0-4 = `PARTIAL`**（静态部分已清零，实机部分 27 项全部 `NOT TESTED`），
**P0-6 = `FAIL`**。
