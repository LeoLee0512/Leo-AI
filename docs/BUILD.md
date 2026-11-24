# Leo AI Studio — 构建

> 本文件描述**如何构建**，以及构建到底保证了什么、没保证什么。
> 状态口径只有 `PASS` / `FAIL` / `PARTIAL` / `BLOCKED` / `NOT TESTED`。
> 「在这台机器上成功」**不等于**「在别人的机器上成功」。后者是人工验收项，见
> [统一修改日志](../CHANGELOG.md) 中完整保留的历史 P0 人工验收清单。

---

## 1. 声明的输入

| 输入 | 在哪里声明 | 说明 |
|---|---|---|
| Python | `manifests/dependency-lock.json` → `python` | 3.12.9；base prefix 必须提供 `python312.dll` |
| Python 包 | `requirements.lock` | 全部 `==` 钉死，21 项 |
| 包的实际 wheel | `manifests/wheelhouse.json` | 每个 wheel 的文件名 / 版本 / 三个 tag / SHA-256 / 大小 / 来源 |
| upstream OpenAI4S | `manifests/upstream-pin.json` | 固定 revision，工作树必须干净 |

`requirements.lock` 只能保证**声明**，不能保证**可复现**：pip 仍然要去某个 index
解析这些 pin。某个版本被 yank、被重传，或者 index 不可达，构建就变了或者根本跑不起来。
wheelhouse 就是用来关掉这个口子的。

---

## 2. wheelhouse

### 2.1 生成

```bash
python tools/build_wheelhouse.py build
```

做三件事：

1. 用 `--only-binary=:all: --no-deps` 把 `requirements.lock` 里每个 pin 的 wheel 下到
   `wheelhouse/`。**没有 wheel 的包直接失败并点名**，不会退化成源码构建，也不会在安装时
   偷偷回到 index。
2. `manifests/dependency-lock.json` → `sdist_build_allowed` 里点名的包，走**显式记录**的
   源码路径：下载 sdist、记下 sdist 的 SHA-256、本地构建 wheel。
3. 写出 `manifests/wheelhouse.json`。

### 2.2 校验

```bash
python tools/build_wheelhouse.py verify
```

会失败的情况（由 `tools/build_wheelhouse.py verify` 检查；旧测试及结果见
[统一修改日志](../CHANGELOG.md) 的历史记录）：

| 问题 | 含义 |
|---|---|
| `missing-file` | manifest 里声明了，目录里没有 |
| `hash-mismatch` | wheel 字节被改过，或 manifest 被改过 |
| `size-mismatch` | 同上，另一维度 |
| `tag-mismatch` | manifest 记录的 tag 与文件名不符 |
| `undeclared-wheel` | 目录里有 manifest 没记的文件 |
| `missing-wheel` | lock 里钉了但 wheelhouse 里没有 |
| `version-mismatch` | 包在，版本不对 |
| `unlocked-package` | wheelhouse 里有 lock 没钉的包 |
| `requirements-drift` | lock 改过了，wheelhouse 是给旧 lock 建的 |
| `unknown-origin` | wheel 没说自己从哪来 |
| `undeclared-sdist-build` | 本地源码构建但没在 `sdist_build_allowed` 里 |
| `missing-sdist-hash` | 本地构建的 wheel 没记 sdist 哈希 |

### 2.3 离线安装

```bash
python -m pip install --no-index --find-links wheelhouse -r requirements.lock
```

`--no-index` 是关键。只写 `--find-links` 时 pip **仍然会回落到 index**。

### 2.4 wheel 二进制不入 git

`wheelhouse/` 在 `.gitignore` 里。入库的是 `manifests/wheelhouse.json`——它给每个 wheel
记了 SHA-256，足以校验别人建出来的 wheelhouse，也足以发现被篡改。

### 2.5 已知的一个例外：`proxy_tools==0.1.0`

这个包在 index 上**只有 sdist，没有 wheel**。因此这套依赖集**无法只用已发布 wheel 组出
完整 wheelhouse**。处理方式是显式的：

- 在 `manifests/dependency-lock.json` → `sdist_build_allowed` 里点名；
- 记录 sdist 的 SHA-256（`ccb3751f…`），这是它可校验的身份；
- manifest 里该条目标 `origin: built-from-sdist`；
- 明写「本地构建的 wheel 不保证跨机器字节一致」。

**这不是措辞上的谨慎，是实测结果**：同一台机器上相隔几分钟构建同一个 sdist，产出的
wheel SHA-256 不同（zip 条目带构建时间戳）。所以对这一条要校验的是 **sdist 哈希**，
wheel 自己的哈希只描述「现在这个文件」。

不在 `sdist_build_allowed` 名单上、又没有 wheel 的包，一律硬失败。

---

## 3. 准备构建环境

```powershell
tools\provision_venv.ps1                 # 有可校验的 wheelhouse 时离线安装
tools\provision_venv.ps1 -AllowIndex     # 明确允许走 index
tools\provision_venv.ps1 -Recreate       # 先删掉 .venv 再建
```

没有可校验的 wheelhouse 且没传 `-AllowIndex` 时**直接失败**，不会自己去 PyPI。
装完会跑一次环境审计。

### 环境审计

```bash
python tools/build_wheelhouse.py audit-env --python .venv/Scripts/python.exe
```

比对 `.venv` 里实际装了什么与 `requirements.lock`：

- `not-installed` —— lock 里有，环境里没有；
- `version-drift` —— 版本对不上；
- `undeclared-package` —— 环境里有、lock 里没有（`pip` / `setuptools` / `wheel` 等
  venv 自带的除外）。

这一项现在是 hermetic 构建的**硬门槛**。在此之前，「从 requirements.lock 构建」说的是
意图，不是事实——构建用的是 `.venv` 里碰巧装着的东西。

---

## 4. 构建

```powershell
tools\build_launcher.ps1              # hermetic（默认）
tools\build_launcher.ps1 -Legacy      # 从旧发布件恢复输入；会明确打印 not reproducible
tools\build_launcher.ps1 -OutputRoot C:\path\to\build-output # 产物和打包临时目录置于仓库外
```

hermetic 模式：

- 不读任何旧发布件（不做 ABI 对比、不从旧 EXE 的 PYZ 里抽模块、不 `--paths` 进
  `_launcher`、不从旧 onedir 回填）；
- 原生 DLL 来自**声明的 Python 工具链**（conda 的 `<base_prefix>/Library/bin`），
  不是来自上一个发布件。少了它们，冻结后的程序会在 `import _ctypes` 就死掉，还到不了
  `main()`；
- 跑环境审计，不过就停；
- 记录 wheelhouse 状态（verified / 不校验 / 没有）。

Phase II 起，主题资产从 `stage/` 打包与部署（2026-09-26 起字体、语言表及其许可随上游注入层退役，
不再打包）；不再读取旧安装的 theme。PyInstaller 归档读取器
也来自当前锁定 venv，不再依赖 `%TEMP%/leo-pyi-tools`。
Hermetic 构建开始时必须是 clean source；`build-inputs.json` 记录全部 tracked
文件的实际字节 hash、commit、环境；完成时重新检查同一 snapshot，并以排他创建
写入产物 `build-receipt.json`，包含整个 package 的大小与 SHA-256 清单。
每次构建使用全新 `-OutputRoot`，重复使用已有 receipt 会失败。
部署携带 receipt，release verifier 重新核验源码与已安装产物。
Receipt 是本地证据而非签名；真实构建日志和独立产物比较仍须保存。

`-Legacy` 会打印 `LEGACY BUILD: ... (not reproducible)`。它只是逃生舱。

---

## 4a. 安装目录的默认位置

自 2026-09-14 起，正式安装目录放在**仓库目录内部**：`<仓库>/LeoAIStudio/`。
构建、部署、生成 manifest、strict 校验、主题预览、技能同步、headless 校验和
人工验收脚本的 `AppRoot` 默认值全部指向这里（此前默认是仓库的**上一级**目录）。

| 覆盖方式 | 适用 |
|---|---|
| 环境变量 `LEO_APP_ROOT` | 所有工具 |
| `-AppRoot <path>` | `tools/build_launcher.ps1`、`tools/deploy_release.ps1` |
| `--app-root <path>` | `tools/build_manifest.py`、`tools/verify_release.py`、`tools/theme_asset_provenance.py`、`tools/sync_skills.py`、`tools/manual_acceptance/collect_windows_account_env.py` |
| 第一个位置参数 | `tools/headless_verify.py` |

`LeoAIStudio/` 与同样位于仓库内的 Leo Tree 项目 `leotree/`（自带独立 git 仓库）都在
`.gitignore` 里，**永不提交**。`LeoAIStudio/user/` 下是 DPAPI 凭据与会话状态，
任何工具都不应把它们当作源码读取或复制。

---

## 5. 发布顺序

```
改代码 → 测试 → commit → repo clean → clean build → deploy
      → python tools/build_manifest.py → python tools/verify_release.py --strict
```

`tools/verify_release.py --strict` 检查：manifest 的 commit == git HEAD、工作树干净、
源文件哈希、部署的 bundle、部署的 EXE、skill 哈希、upstream pin。

---

## 6. 这些**没有**证明什么

| 做到了 | 没做到 |
|---|---|
| 这台机器能生成并校验 wheelhouse | 全新机器能从干净 clone 构建（F1/F2，`NOT TESTED`） |
| 依赖能用 `--no-index` 装上 | 换一个 Python 发行版仍然可用 |
| 环境与 lock 逐项一致 | 同一 commit 两次构建字节一致（F3，`NOT TESTED`） |
| hermetic 产物能跑 | 在没装过 WebView2 的机器上能跑（B 区块，`NOT TESTED`） |

`python312.dll` 与 `Library/bin` 下的原生库来自这个具体的 conda 安装。这是**声明的
工具链**依赖，不是旧发布件依赖——但换 Python 发行版需要重新验证。

---

## 7. 相关文件

| 文件 | 作用 |
|---|---|
| `tools/build_wheelhouse.py` | 生成 / 校验 wheelhouse，审计环境 |
| `tools/provision_venv.ps1` | 从声明的输入建 `.venv`，优先离线 |
| `tools/build_launcher.ps1` | 构建 EXE |
| `tools/deploy_release.ps1` | 部署 |
| `tools/build_manifest.py` | 生成发布 manifest |
| `tools/verify_release.py` | strict verifier |
| `tools/portability_check.py` | 静态扫机器绑定 |
| `tools/package_contract.py` | 构建脚本调用的正式包契约校验，检查运行依赖、资源、嵌入模块及敏感材料 |
| [统一修改日志](../CHANGELOG.md) | 修改日期、位置、结果，以及已归档的历史测试、构建和人工验收记录 |
