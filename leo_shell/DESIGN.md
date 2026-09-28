# Leo Shell 重写设计契约（内部文档）

新 Windows 壳，替代 recovered `leo_ai_studio`（.pyc）+ `leo_runtime_patch.py` 的全部职责。
代码与注释用英文（对齐现有 `leo_runtime_patch.py` 风格）。Python 3.12，Windows-only。

2026-09-07 更新：本文保留原始壳重写契约，并补入本地 Qwen3、原生设置与上游选择同步、可恢复会话管理和 LeoTree 导出。原先被列为二期的 entity-state 已有源码实现；CLI 全量数据导入导出仍未实现。本文描述源码设计，**不等同于正式安装版验收**。末节单列当前验证边界和仍待检查的项目。

## 总览

```
leo_shell/
  __init__.py          # __version__ = "1.0.0"
  paths.py             # AppPaths：目录解析、UNC 拒绝、manifest 定位 webview2
  logging_setup.py     # 脱敏滚动日志 user/logs/leo-shell.log
  settings_store.py    # settings.json / model-profiles.json / appearance.json + PRESETS
  secrets_store.py     # DPAPI 凭据存储 + 旧格式尽力迁移
  bridge_client.py     # wsl.exe 调用 bridge/leo_bridge.sh，隐藏窗口，JSON 协议，WSLENV 传密钥
  local_model.py       # 复用唯一 Windows llama.cpp 工程，核验领有关系，管理私有 WSL relay
  entity_store.py      # 本机可恢复的归档/回收站元数据；不删除上游会话正文
  connection.py        # ConnectionCoordinator：串行 worker、代际、ack 超时、5 个公开错误码
  theme_runtime.py     # shell.html 渲染（占位符/1.5MiB 门禁）+ 注入脚本构建 + 受信 URL 校验
  webview2_runtime.py  # 固定版 WebView2 定位 + icacls ACL + webview.settings 注入
  single_instance.py   # 每用户 mutex + 命名管道（DPAPI authkey），action: settings/activate/update
  api.py               # ShellApi：pywebview js_api 对象（前端契约方法集）
  ui.py                # DesktopUI：窗口创建、启动守卫、注入触发、setStatus 推送
  diagnostics.py       # 脱敏诊断报告（bridge preflight/status/doctor）
  app.py               # Application：CLI、组装、启动流程
launcher/
  leo_shell_entry.py   # 新 PyInstaller 入口（不动旧 leo_entry.py）
bridge/
  leo_local_relay.py   # WSL loopback HTTP → Windows curl 互操作管道 → llama.cpp
  leo_model_selection.py # 上游原生选择事务；保留旧全局覆盖行，不改历史 profile/会话绑定
```

## paths.py

```python
@dataclass(frozen=True)
class AppPaths:
    root: Path            # 便携包根（frozen: exe 的父目录；dev: LEO_STUDIO_ROOT 或仓库上级）
    user: Path            # root/"user"
    theme: Path           # root/"theme"
    bridge_script: Path   # root/"bridge"/"leo_bridge.sh"
    runtime_dir: Path     # root/"runtime"
    logs: Path            # user/"logs"
    credentials: Path     # user/"credentials"
    @classmethod
    def from_root(cls, root: Path | None = None) -> "AppPaths": ...
    def webview2_dir(self) -> Path: ...
    def reject_unsupported_root(self) -> None: ...  # UNC / 映射网络盘 → ValueError
```

- frozen 判定：`getattr(sys, "frozen", False)`，root = `Path(sys.executable).parent`。
- dev 模式：环境变量 `LEO_STUDIO_ROOT` 优先；否则 `Path(__file__).resolve().parents[2]`（即 LeoAIStudio-build/ 的上一级不含 theme…实际 dev 根指向部署目录，由测试注入，不猜测）。
- `webview2_dir()`：依次读 `runtime/dependencies.json`、`runtime/runtime-manifest.json`（utf-8-sig，≤1 MiB），取 `dependencies.webview2.path`；必须相对路径、resolve 后仍在 root 内、已存在目录；缺失则回退 `runtime/webview2` 下唯一子目录。
- 拒绝 UNC（`\\...`）与映射网络盘。

## logging_setup.py

```python
def setup_logging(paths: AppPaths, *, verbose: bool = False) -> logging.Logger: ...
def register_redaction(secret: str) -> None: ...   # 运行期登记需抹除的值（如 API key）
```

- `RotatingFileHandler(user/logs/leo-shell.log, maxBytes=1 MiB, backupCount=3, encoding="utf-8")`。
- Filter 脱敏：正则 `sk-[A-Za-z0-9_-]{8,}`、`token=` 查询值、`Bearer \S+`、`api_key`/`password`/`secret` 的 JSON 值，以及 `register_redaction` 登记的字面值。
- 日志只记阶段码、错误码、request id、耗时；绝不记 key、token URL 全文（记 `http://127.0.0.1:8760/?token=<redacted>`）。

## settings_store.py

```python
PRESETS: tuple[dict, ...]  # 见下
@dataclass
class Profile: id: str; name: str; preset: str; provider: str; model: str; base_url: str
    # requires_key 属性由 preset 决定，本地 preset 为 False；不信任持久化输入覆盖
class SettingsStore:
    def __init__(self, paths: AppPaths, secrets: "SecretsStore"): ...
    def state_for_shell(self) -> dict: ...        # 见 get_state 契约
    def save_profile(self, payload: dict) -> Profile: ...  # 校验失败抛 SettingsInvalid
    def delete_profile(self, profile_id: str) -> None: ...
    def active_profile(self) -> Profile | None: ...
    def api_key_for(self, profile_id: str) -> str | None: ...
    def load_appearance(self) -> dict: ...         # {"theme": ..., "locale": "zh"|"en"}
    def save_appearance(self, theme: str, locale: str) -> dict: ...
class SettingsInvalid(ValueError): ...
```

- `model-profiles.json` 保持现有格式：`{"schema_version":1,"active_profile_id":...,"profiles":[{"base_url","id","model","name","preset","provider"}]}`；`settings.json` 镜像 active profile：`{"base_url","model","preset","provider","schema_version":1}`。原子写（tmp + os.replace），UTF-8 无缩进排序键。
- `appearance.json` 只允许 `{"schema_version":1,"theme","locale"}` 三键；theme ∈ `themes.json` 注册 id，默认主题读取该注册表的 `default_theme`，不在 Python 固定为旧主题；locale ∈ {zh,en}（默认 zh）。
- PRESETS（核心键 `{"id","label","provider","model","base_url","editable_base_url"}`；对 shell 输出 `id,label,model,base_url,editable_base_url`，本地项另含布尔值 `requires_key:false`，省略时按需要密钥处理）：
  - deepseek / DeepSeek / chatgpt / deepseek-chat / https://api.deepseek.com / true
  - qwen / Qwen / chatgpt / qwen-plus / https://dashscope.aliyuncs.com/compatible-mode/v1 / true
  - openai / OpenAI / chatgpt / gpt-4o-mini / https://api.openai.com/v1 / true
  - zhipu / 智谱 GLM / chatgpt / glm-4-flash / https://open.bigmodel.cn/api/paas/v4 / true
  - kimi / Kimi / chatgpt / moonshot-v1-8k / https://api.moonshot.cn/v1 / true
  - ark / 火山方舟 Ark / ark / doubao-seed-1-6-250615 / https://ark.cn-beijing.volces.com/api/v3 / true
  - anthropic / Anthropic / claude / claude-3-5-haiku-20241022 / https://api.anthropic.com / true
  - gemini / Google Gemini / gemini / gemini-2.0-flash / https://generativelanguage.googleapis.com / true
  - local-qwen / 本地 Qwen3 / local-llama / local-qwen3-4b / http://127.0.0.1:8080/v1 / false；`requires_key=false`
  - custom / 自定义（OpenAI 兼容）/ chatgpt / "" / "" / true
  - **必须含 id=deepseek**（shell 无 profile 时默认选中它）。
- profile id：`"profile-" + secrets.token_hex(16)`；空串是 shell 的“新建”哨兵，永不可用。
- 校验：preset 已知、model 非空（≤200 字符）、base_url 为空则取 preset 默认、非空必须 `http(s)://` 且无 userinfo/fragment；name ≤80。
- 本地 preset 的 model、provider、logical base URL 固定；不接受篡改地址或非空 API key。`api_key_for` 不读取该 preset 的 DPAPI 明文；shell 显式得到 `requires_key:false`、`has_key:false`，不能把免密伪装成已存密钥。用户在同一设置页保存并切换本地或云端配置，既有云端 profile 与凭据保留。

## secrets_store.py

```python
class SecretsStore:
    def __init__(self, directory: Path): ...
    def save_key(self, profile_id: str, api_key: str) -> None: ...
    def load_key(self, profile_id: str) -> str | None: ...
    def delete_key(self, profile_id: str) -> None: ...
    def migrate_legacy(self, legacy_file: Path, profile_id: str | None) -> None: ...
```

- DPAPI：`crypt32.CryptProtectData`/`CryptUnprotectData`（ctypes，可选 entropy）；文件 = `b"LEOCRED1\n" + base64url(dpapi(json.dumps({"v":1,"api_key":key})))`，权限仅当前用户。
- 旧格式迁移：对 `user/credential.dpapi` 尝试 `CryptUnprotectData`（无 entropy 先试空，再试若干已知 entropy 候选）→ UTF-8 解码 → JSON 解析找 `api_key`/`key`/`token`，或直接是字符串则当作 key；成功则存入 active profile。**任何一步失败都静默放弃（返回 None），不抛错、不记日志内容**。旧文件不删除。

## bridge_client.py

```python
class BridgeError(RuntimeError):
    def __init__(self, code: str, message: str, guidance: list[str] | None = None): ...
class WslBridge:
    def __init__(self, paths: AppPaths, *, distro: str | None = None,
                 runner: Callable = subprocess.run, logger: logging.Logger | None = None): ...
    def preflight(self) -> dict: ...                      # timeout 60
    def status(self) -> dict: ...                         # timeout 30
    def install(self, source_archive: Path | None = None) -> dict: ...  # 内部：install-runtime + stage-source + activate-source，各 timeout 600
    def start(self, *, provider: str, model: str, base_url: str, api_key: str | None) -> dict: ...  # timeout 120
    def client_url(self) -> str: ...                      # action "url"，timeout 30，返回严格校验后的 URL
    def stop(self) -> dict: ...                           # timeout 60
    def doctor(self) -> dict: ...                         # timeout 120
```

- argv：`[wsl.exe] + (["-d", distro] if distro) + ["-e", "/bin/sh", <bridge 的 /mnt 路径>, action, *args]`； distro None 时用默认发行版。Windows 路径 → `/mnt/<drive 小写>/...`（`C:\x\y` → `/mnt/c/x/y`）。
- **密钥只走环境**：子进程 env 增加 `OPENAI4S_LLM_API_KEY` 与 `OPENAI4S_<PROVIDER 大写>_API_KEY`，并把两者加入 `WSLENV`（冒号分隔，保留已有 WSLENV）。argv 永不携带密钥；若检测到 argv 含 `--api-key`/`--token`/`--secret` 等敏感参数名直接抛 `BridgeError("INVALID_ARGUMENT")`。
- 隐藏窗口：`creationflags |= CREATE_NO_WINDOW (0x08000000)`；`STARTUPINFO.dwFlags |= STARTF_USESHOWWINDOW; wShowWindow = SW_HIDE`。`shell=False, capture_output=True, timeout=...`。
- 输出解析：stdout 最后一行非空行应为 JSON（wsl.exe 可能先打印 localhost 代理警告，通常在 stderr；两边都要容忍噪音行）。`ok:false` → 抛 `BridgeError(error.code, error.message, error.guidance)`。
- 异常映射：`FileNotFoundError` → `WSL_UNAVAILABLE`；`TimeoutExpired` → `WSL_TIMEOUT`；JSON 解析失败 → `BRIDGE_OUTPUT_INVALID`。
- 脱敏：返回/记录前，把 env 中登记过的敏感值从 stdout/stderr 抹除。

### local_model.py / leo_local_relay.py

- 本机配置为 `<安装根>/user/local-model.json`，最小内容 `{"project_directory":"../大模型"}`。相对路径以安装根解析；可使用明确的本机绝对目录。模型工程内部路径必须相对且在项目内，拒绝 symlink、junction、UNC、网络盘与路径逃逸。
- 复用该工程唯一 GGUF、`runtime/llama.cpp/llama-server.exe` 与 `scripts/common.ps1/start.ps1/stop.ps1`。模型服务固定 `127.0.0.1:8080`、alias `local-qwen3-4b`；实际上下文读取 `config/model.json.contextSize`，不把旧 4096 基线性能当作扩容后的结果。
- `LocalModelSession.start()` 核验进程 PID、可执行路径与启动时间，并检查健康、模型 alias 和实际上下文。只有确认由本次 PowerShell 子进程启动的模型才记录为 owned；外部已有健康模型可复用。停止时再次核验身份，只释放 owned 模型；不会按进程名或端口杀进程。
- WSL NAT 下不将 Windows 模型改成外部监听。标准库 relay 绑定 WSL `127.0.0.1` 随机端口，经 Windows `curl.exe` 访问 Windows loopback。curl 禁止读取 `.curlrc`、绕过代理、不跟随重定向；请求正文经 stdin，不进入命令行。
- relay 的随机 token 只在运行内存和子进程环境中传递，不写配置、日志、源码或模型 profile。父进程保留 relay stdin，EOF 关闭 relay。只开放固定健康、模型与聊天路由；拒绝未认证、浏览器 Origin、任意目标及图片输入。
- `_start_local` 将壳内部 `local-llama` 映射为上游 `chatgpt` 加私有 relay URL，并给该进程设置配置中的 context、最多 512 输出 tokens、关闭 thinking。每次实际请求先经模型自身 `/apply-template`、`/tokenize` 检查输入与输出预留；超限明确拒绝，不静默裁掉历史、科研指令或工具。
- 本地执行和完成仍由上游负责。relay 仅对原 system 同时包含既有 `Finishing:`/`host.submit_output` 协议且没有原生 tools 的工作台主请求，保留全部原消息并追加两个私有原生动作，设置 `tool_choice=required`、`parallel_tool_calls=false`：`finalize_response` 由模型提交普通回答及固定合法动作要点，通过校验后原响应字节不变；`run_scientific_cell` 由模型提交真实 Python/R 代码，转换为闭合代码块交回原 gateway 执行、授权检查及记录证据，科学任务的 `host.submit_output` 仍由真实 Python 执行。JSON/SSE 均须完整收齐，确认终止信号、单个动作和有界完整参数后才发布；允许并保留上游要求的模型前导说明，但拒绝说明中夹带额外代码围栏/工具动作、多调用、混合动作及截断。SSE 的 id/model/call_id 保持一致，逐片段 created 时间仅作元数据。纯正文不自动包装为完成，不模拟执行；标题等辅助请求和已有原生 tools 的请求保留原协议。该能力仅限此私有协议，不表示本地模型支持完整原生工具目录；真实复杂科研任务的可靠性仍需单独验证。

### leo_model_selection.py：原生设置与上游运行状态一致

- 上游存储的全局 `llm_api_key` 优先于进程环境，旧 `active_model_profile` 也会影响新会话绑定。只改模型名或下拉标签不能证明切换成功。
- 每次原生选择通过固定 helper 在同一 `settings` 数据库中执行事务：原 `llm_api_key`、`active_model_profile` 的值和原时间戳保存在专用恢复槽；活动全局 key 覆盖置空，使本次连接的 key/token 从进程环境解析。原 profile 集合、凭据对象和旧 frame 绑定不改动。
- 本地选择及带本次显式 key 的云端选择将活动 profile 清空；没有新 key 的云端选择，仅在历史 profile 的 provider/model/base URL 全部匹配时恢复该 profile ID。变化需要重启时由 bridge 生命周期负责；本文中的 helper 本身不启停服务。
- helper 不接收密钥参数，不将 relay token 写入 SQL；路径、schema、事务状态异常时拒绝修改。`restore` 只有在活动值仍等于本 helper 记录的 expected 值时才恢复原行；出现外部修改则报告冲突。此恢复能力不表示普通关闭会自动恢复旧云端覆盖。
- 前端仅在壳的活动本地 preset、gateway `/health` 模型、`/models` 当前 live 条目与 `/model-profiles` 活动配置相符时显示本地选项，并设置真实 `S.defaultModelName`。不一致显示待同步且阻止发送。切回云端恢复上游原模型选择行为。
- 既有云端 pin 不随设置切换被偷偷改写。发送前可明确选择新建本地会话，或确认调用标准 `/frames/{id}/model-binding` 后重新读取绑定。上游此路由可能按旧 `frame.model` 回填旧 profile；前端核验失败时不声称已切换，也不继续发送。
- 本地错误文案只做显示投影：要求真实失败 code/支持 ID、当前 gateway 与会话绑定的本地证明，并完整匹配上游生成的通用调用失败或认证失败句子。投影提示检查本地服务/WSL、无需填写 API Key；原消息、copy/export 源和 `request_id/code/output_committed` 不改写。切回云端恢复原显示，无元数据的引用文字和未核验的云端 pin 不改动。已有部分输出时保留避免重复执行的提醒。

## connection.py

```python
PUBLIC_APP_CLOSING = "APP_CLOSING"
PUBLIC_SETTINGS_INVALID = "MODEL_SETTINGS_INVALID"
PUBLIC_SETTINGS_UNAVAILABLE = "MODEL_SETTINGS_UNAVAILABLE"
PUBLIC_CONNECTION_FAILED = "MODEL_CONNECTION_FAILED"
PUBLIC_RECOVERY_REQUIRED = "MODEL_SETTINGS_RECOVERY_REQUIRED"

class UiSink(Protocol):
    def publish_status(self, message: str, *, error: bool = False) -> Any: ...
    def navigate(self, url: str) -> Any: ...
    def open_settings(self) -> Any: ...

class ConnectionCoordinator:
    def __init__(self, bridge: WslBridge, sink: UiSink, logger, *, ack_timeout: float = 15.0): ...
    def submit(self, profile: Profile, api_key: str | None, *, requires_ack: bool) -> dict:
        # 立即返回 {"ok": True, "pending": True, "request_id": n}
    def acknowledge(self, request_id: int) -> None: ...
    def close(self, *, wait_timeout: float = 1.0, stop_daemon: bool = True) -> None: ...
```

- 单 daemon 线程 `leo-shell-connect` + `threading.Condition`；pending 单槽位；`submit` 递增代际号并作废旧代（旧代在下一步执行前自查 `is_current` 退出）。
- worker 阶段（每阶段记日志：阶段码 + 耗时 + request id）：
  1. `PREFLIGHT`：bridge.preflight()
  2. `STATUS`：not-installed → `INSTALL`（runtime tar = `runtime/openai4s-linux-x86_64.tar.gz`，sha256 读 `runtime/runtime-manifest.json`；source tar = `user/cache/source-<revision>.tar`，缺则报 `SOURCE_ARCHIVE_UNAVAILABLE`）→ 再 status
  3. `START`：指纹含 provider、model、base_url 及 key 摘要（只在进程内存）；running、指纹相同且为云端时跳过。本地每次重连都调用 start 核验实际模型及 relay，内部复用健康实例；配置变化时按现有串行生命周期重启。
  4. `URL`：bridge.client_url() → 校验
  5. `NAVIGATE`：`requires_ack` 时先等 ack（`ack_timeout` 秒；**超时且仍 current 则照常导航并记 `ACK_TIMEOUT`**，永不卡死）；`sink.navigate(url)`
- 失败路径：`BridgeError`/`SettingsInvalid`/其他异常 → 若仍 current：`sink.publish_status(公开码, error=True)` + `sink.open_settings()`。BridgeError 一律映射 `MODEL_CONNECTION_FAILED`（精确 code 进日志）；`APP_CLOSING` 时静默。失败时尝试 `bridge.stop()` 一次（吞异常）。
- `close()`：置 closing、作废当前代、等 worker（≤wait_timeout）；`stop_daemon` 时由独立非 daemon 线程执行恰好一次物理 stop（排在 in-flight start 之后）。
- 凭证生命周期：`api_key` 在 worker 用完（start 调用返回/抛出）后立即在 finally 中置 None 并删除局部引用。

## theme_runtime.py

```python
MAX_SAFE_SHELL_HTML_BYTES = 1536 * 1024
class ThemeRuntime:
    def __init__(self, theme_dir: Path): ...
    def render_shell(self, *, open_settings: bool) -> str: ...
    def injection_script(self, appearance: dict, *, has_key: bool) -> str: ...
    def themes(self) -> list[str]: ...   # themes.json 注册 id 列表
def trusted_backend_url(url: object) -> bool: ...
class ThemeRuntimeError(RuntimeError): ...
```

- `render_shell`：读 `theme/shell.html` → 替换 `__LEO_LION_DATA_URI__`（`logos/leo-lion.svg`，≤512 KiB，`data:image/svg+xml;base64,`）与 `__LEO_FAVICON_DATA_URI__`（`logos/leo-favicon.svg`；模板中可能没有，替换操作需幂等无害）→ `__LEO_OPEN_SETTINGS__` → `"1"`/`"0"` → 结果仍含 `"__LEO_"` 抛 ThemeRuntimeError → utf-8 编码 > 1.5 MiB 抛 ThemeRuntimeError。
- `injection_script`：`"window.__LEO_INJECT_CONFIG__=" + json.dumps(config, ensure_ascii=False, separators=(",",":")) + ";\n" + (theme_dir/"leo-inject.js").read_text()`；config 键序 `version,theme,locale,css,logo,favicon,messages,has_key`：
  - `css` = `theme/leo.css` 全文，其中 4 个 `@font-face` 的 url 占位符替换为 `data:font/woff2;base64,...`（读 `theme/fonts/` 对应文件，校验 `wOF2` magic；占位符的确切写法以 leo.css 实际内容 + `fonts/manifest.json` 为准）；替换后仍有占位符残留 → ThemeRuntimeError。
  - `logo` = `logos/leo-lion-1024.png` 的 `data:image/png;base64`（校验 PNG magic、正方形、512≤边≤2048、≤4 MiB）。
  - `favicon` = `logos/leo-favicon.svg` data URI（≤512 KiB）。
  - `messages` = `{"zh": <i18n/zh.json>, "en": <i18n/en.json>}`（扁平 string→string）。
- 磁盘驱动：每次调用现读文件（可用 mtime+size 缓存）；资产绝不编进二进制。
- `trusted_backend_url`：str、无 <32 控制字符；urlsplit 后 scheme==http、hostname ∈ {127.0.0.1, ::1, localhost}、port==8760、无 username/password、无 fragment。

## webview2_runtime.py

```python
def configure_fixed_runtime(paths: AppPaths, logger) -> None: ...
```

- 定位：`paths.webview2_dir()` 下优先直接子级 `msedgewebview2.exe`，否则 rglob 后必须恰好一个。
- ACL（幂等，每次启动执行）：`%SystemRoot%\System32\icacls.exe <dir> /grant:r "*S-1-15-2-2:(OI)(CI)(RX)" "*S-1-15-2-1:(OI)(CI)(RX)"`，隐藏窗口，timeout 30；失败记日志不致命（继续，系统 WebView2 兜底）。
- 注入：`import webview; webview.settings["WEBVIEW2_RUNTIME_PATH"] = str(selected)`；settings 为 None → 抛 UIError 类异常。

## single_instance.py

```python
class SingleInstance:
    def __init__(self, paths: AppPaths): ...
    def claim(self) -> bool: ...                 # mutex Local\LeoAIStudio-<id>
    def forward(self, action: str) -> bool: ...  # 次实例 → 主实例（命名管道，DPAPI authkey）
    def listen(self, handler: Callable[[str], None]) -> None: ...  # 主实例后台线程
    def close(self) -> None: ...
```

- `<id> = sha256(f"{resolve(root).casefold()}\x00{getpass.getuser().casefold()}")[:24]`；管道 `\\.\pipe\LeoAIStudio-<id>`；authkey 用 SecretsStore 存取 `user/ipc.dpapi`（entropy `b"LeoAIStudio/IPC/v1"`，无则新建随机 32 字节）。
- action 只允许 `{"settings","activate","update"}`；管道消息只接受 `{"action": str}`。
- 实现可用 `multiprocessing.connection.Listener/Client`（与旧壳一致），失败降级：claim 成功即可运行，listen 失败仅记日志。

## api.py（前端契约，方法名/返回形状一字不能差）

```python
class ShellApi:
    def get_state(self) -> dict: ...
    def save_profile(self, payload: dict) -> dict: ...
    def save_settings(self, payload: dict) -> dict: ...   # 别名 → save_profile
    def delete_profile(self, payload: dict) -> dict: ...
    def save_appearance(self, payload: dict) -> dict: ...
    def acknowledge_connection(self, payload: dict) -> dict: ...
    def connect_keyless(self) -> dict: ...
    def open_local_skills_folder(self) -> dict: ...
    def scan_local_skills(self, payload: dict | None = None) -> dict: ...
    def list_entity_states(self, payload: dict | None = None) -> dict: ...
    def mark_entity(self, payload: dict) -> dict: ...
    def restore_entity(self, payload: dict) -> dict: ...
    def forget_entity(self, payload: dict) -> dict: ...
```

- `get_state()` → `{"appearance":{"locale","theme"},"themes":[...],"presets":[{id,label,model,base_url,editable_base_url}],"profiles":[{id,name,preset,model,base_url,has_key}],"active_profile_id":...,"settings":{"preset","model","base_url"},"has_key":bool}`。本地 preset/profile/settings 另保留布尔 `requires_key:false`；locale 必须合法 zh/en。**永不下发密钥，只有 has_key 和凭据需求策略**。活动设置本身不是连接已成功的证据。
- `save_profile(payload)`：payload=`{profile_id|null,name,preset,model,base_url,api_key,activate}`；校验失败 → `{"ok":False,"message":"MODEL_SETTINGS_INVALID"}`；成功且 activate → `coordinator.submit(..., requires_ack=True)` 并返回 `{"ok":True,"request_id":n,"pending":True}`；不 activate → `{"ok":True,"pending":False}`。
- `delete_profile({profile_id})` → `{"ok":True}` 或 `{"ok":False,"message":...}`。
- `save_appearance({theme,locale})` → `{"ok":True,"appearance":{...}}`；失败 `{"ok":False,"message":...}`；若工作台已加载（`_backend_loaded`）则重新注入生效。
- `acknowledge_connection({request_id})` → 恒 `{"ok":True}`（内部校验 int>0）。
- `connect_keyless()`：启动页「不接入模型，先逛逛」按钮的显式入口。有 active profile → `coordinator.submit(profile, None, requires_ack=False)` 并返回 `{"ok":True,"pending":True,"request_id":n}`；无 profile → `{"ok":False,"message":"KEYLESS_NEEDS_PROFILE"}`；读取 profile 失败 → `MODEL_SETTINGS_UNAVAILABLE`，submit 抛错 → `MODEL_CONNECTION_FAILED`。**永远不传密钥**（即使该 profile 存了密钥）。`KEYLESS_NEEDS_PROFILE` 不进 `publicMessage()` 的五码表，由前端按钮处自行本地化。
- `scan_local_skills(payload=None)`：按 README 规则扫 `user/user-skills/*/SKILL.md`（UTF-8、≤1 MiB、拒符号链接/路径逃逸），返回 `{"ok":True,"skills":[{"id","folder","name","byte_size","sha256","content"}...],"rejected":[{"folder","code"}...],"hidden_count":int}` 或 `{"ok":False,"message":...}`。**形状由 `theme/leo-inject.js` 的技能面板决定**：它按 `folder`+`content`+`sha256`(64 位小写十六进制) 过滤后逐条 POST `/api/v1/skills/import`，并渲染 `byte_size`、`rejected[].code`、`hidden_count`。`payload` 接收但忽略——前端调用形式是 `scan_local_skills({})`，零参签名会让「安全扫描并同步」在扫描前就抛 TypeError。`rejected` 的 code：`symlink` / `escapes_root` / `no_skill_md` / `too_large` / `unreadable`；`.` 开头的条目只计入 `hidden_count`，不读也不列出。注意：该端点只同步 SKILL.md 正文，**不传 `kernel.py`**；带 sidecar 的技能需要把整个目录复制到 WSL 的 `<data_dir>/user-skills/`。
- 未实现的扩展方法（`choose_theme_file, stage_theme_preview, confirm_theme_preview, discard_theme_preview, delete_custom_theme, get_project_persona, save_project_persona`）用 `__getattr__` 兜底返回 `{"ok":False,"message":"此功能暂未在新版壳中提供。"}`，**不得抛 AttributeError**。entity 四方法已实现，不再属于 stub；仍由 `leoBridge` 统一访问。
- 所有方法线程安全（pywebview 在独立线程调 js_api）；所有异常收口为 dict 返回。

### entity_store.py 与会话管理

- `<安装根>/user/entity-states.json` 保存版本 1 文档：全局 revision 和 entities 数组。每条记录只含 `entity_type`（session/folder/project）、`entity_id`、`state`（archived/trashed）、record revision、更新时间、可选标题；folder/project 另含版本化成员 ID 快照。它是本机可恢复的可见性状态，不是云端同步、会话正文备份或附件备份。
- 读写受锁保护，UTF-8、上限 4 MiB。写入使用同目录临时文件、flush/fsync 和 `os.replace`；文件损坏、未知 schema、重复记录、非法 ID、路径链接、写盘错误均拒绝覆盖原文。恢复/忘记记录必须提交正确 `expected_revision`，不以过期页面删除更新后的状态。
- `list_entity_states({offset,limit})` 返回 `entities` 与 `next_offset`；`mark_entity` 保存归档或回收站记录；`restore_entity` 移除隐藏记录使原会话回到列表；`forget_entity` 在明确完成上游永久删除后清理对应元数据。四方法不直接删除上游内容。
- 会话菜单的“归档 / 删除 / 取消”用独立对话框。归档保留上游正文；删除先进入回收站。只有回收站中的“彻底删除”经单独明确确认、再次核验 revision 后才通过既有已认证 fetch 向上游发送 DELETE。组永久删除仅移除组，上游保留组内会话。取消、Esc 和点击遮罩均无删除请求，焦点返回原控件；不异步替换同步 `window.confirm`。
- 注入层过滤已有分页会话/分组列表。元数据读取失败时列表和受管 DELETE 返回失败，不用空数组覆盖档案，不绕过认证继续删除。恢复入口是设置中的数据管理，以及会话菜单的“已归档与回收站”。
- 2026-09-07 延续：项目行菜单、上游项目设置删除按钮、会话组菜单和直接受控删除函数均使用页面内“归档 / 删除 / 取消”对话框。项目归档/回收站保存完整分页成员快照，过滤项目列表及成员会话/分组；恢复移除项目自身隐藏记录，不改成员正文或其独立归档状态。项目回收站仅提供恢复，不调用可能级联删除会话的上游项目 DELETE。正在运行的项目/分组拒绝隐藏。
- 文件删除、模型配置删除、自定义主题删除没有档案恢复语义，只使用明确的“删除 / 取消”异步对话框，等到明确删除结果才调用原有删除 API。启动壳的配置删除也由页面内 HTML dialog 承载，默认聚焦取消，Esc/遮罩取消，捕获目标 ID 并阻止重复提交；API 拒绝或异常只显示失败。文件展示“无法撤销”，不伪称归档；不替换全局 `window.confirm`，不扩展无关非删除 prompt。局部验证使用隔离浏览器、真实 UI 函数和合成记录，不据此宣称已部署或整体验收通过。

### 整理成知识树 / 导出到 LeoTree

- 从会话菜单进入，只在用户点选后读取该会话；复用上游 `fetchAllMessages(fid)` 分页读取并要求 `complete:true`。空会话、不完整读取、超过 500 节点或节点内容超过 4 MiB 时拒绝输出完整草稿，不自动截断冒充完整导出。
- 当前整理是原文驱动的可编辑草稿，不调用模型或声称已事实核验：用户问题归入“问题与目标”，助手原文按 Markdown 标题分入“知识与推导”，代码围栏中的标题不拆成节点。可编辑树名、节点标题、笔记并取消不需要的节点。
- 导出格式是 LeoTree 支持的单树 `{schemaVersion:3, tree:{...}}`，文件名为清洗后的树名加 `-LeoTree.json`；保持 `.json` 因目标导入选择器只接受 `.json/.zip`。产品文案使用“整理成知识树”“导出到 LeoTree”。发起 Blob 下载只显示已请求保存，不能据此声明文件已落盘。
- 全部节点初始 `todo`，`statusHistory:[]`、`firstDoneAt:null`、`attachments:[]`；树的 logs、reviews、learningHistory 为空，`historyComplete:false`。源会话 ID 和导出时间保存在来源 metadata，不伪造掌握历史、实践完成或附件引用。普通导出不包含附件字节。
- 目标契约以指定 `<LEOTREE_ROOT>` 的 `types.ts`、`migrate.ts`、`validation.ts`、`import.ts` 为准，不使用其他同名旧仓库。默认导入为独立新树，需要在 LeoTree 中预览并确认；不覆盖已有树。

## ui.py

```python
class DesktopUI(UiSink):
    def __init__(self, paths, settings: SettingsStore, theme: ThemeRuntime,
                 coordinator: ConnectionCoordinator, logger): ...
    def run(self, on_ready: Callable[[], None]) -> None: ...
    # UiSink:
    def publish_status(self, message, *, error=False): ...   # evaluate_js window.setStatus(...)
    def navigate(self, url): ...                             # 受信校验 → load_url + 标记 _backend_pending
    def open_settings(self): ...                             # evaluate_js LeoShell.openSettings()
```

- 窗口：`webview.create_window("Leo AI Studio", html=theme.render_shell(open_settings=self._open_settings), js_api=ShellApi(...), width=1280, height=800, min_size=(840,600), confirm_close=False, background_color="#FBF7F2"（与 theme/shell.html 的 `--bg` 保持一致，否则加载瞬间闪旧底色）)`；`webview.start(func=on_ready, gui="edgechromium", private_mode=True, debug=False)`。
- 启动守卫：`events.shown`/`events.minimized` 挂载，宽限 10 秒内 `restore()` 后 `show()`（minimized 只恢复一次）；超期自动解除。
- 注入：`events.loaded` → 若 `_backend_pending`：`script = theme.injection_script(appearance, has_key=...)`；`evaluate_js(script)` 返回 `False` → 红色横幅降级（`document.body.insertAdjacentHTML(...)`）并记日志；成功置 `_backend_loaded=True`。
- `publish_status` 任何时机都安全（前端 pending 补播）；evaluate_js 失败吞掉记日志。
- 关窗：`events.closing` → `coordinator.close()`（默认 stop_daemon=True）。

## diagnostics.py / app.py / 入口

- `run_diagnostics(paths, bridge, logger) -> Path`：依次 preflight/status（installed 时再 doctor），汇总 `{generated_at, preflight, status, doctor}`（error 时记 code+message+guidance，不含任何密钥），写 `user/logs/diagnostics-<yyyymmdd-HHMMSS>.json`，返回路径。
- CLI（`app.py`，argparse）：无参 / `--settings`（启动后直接开设置抽屉）/ `--diagnostics`（跑诊断写文件后退出码 0/1）/ `--update`、`--export-data`、`--import-data`（本版不支持：写日志 + 退出码 2，留待二期）。
- 启动流程 `Application.run()`：
  1. paths 校验 → logging → secrets 迁移（尽力）→ stores → bridge → coordinator → single_instance.claim()
  2. claim 失败（已有实例）：按 CLI 选择 action forward（--settings→settings，否则 activate），退出 0
  3. `webview2_runtime.configure_fixed_runtime`（失败记日志继续）
  4. 主实例：`single_instance.listen(handler)`（settings/activate → UI 线程 restore+show+openSettings；update → 忽略记日志）
  5. `ui.run(on_ready)`；on_ready（webview 线程）：active profile 且有密钥，或 profile 明确 `requires_key=False` 时，调用 `coordinator.submit(..., requires_ack=False)`。本地 preset 不读取 DPAPI；云端缺密钥及无 profile 仍留在启动页，只 `open_settings()`。无密钥浏览仍由用户显式点击 `ShellApi.connect_keyless()`。分发过程本身抛异常才 `publish_status("MODEL_SETTINGS_UNAVAILABLE")` + `open_settings()`。`--settings` 时无论有无 profile 都 open_settings 且不自动连接。
  6. 退出：finally `coordinator.close()` + `single_instance.close()`。
- `launcher/leo_shell_entry.py`：`sys.dont_write_bytecode = True` → `from leo_shell.app import main` → `raise SystemExit(main())`。

## 验证约束与历史记录

- 无 GUI 环境应能导入壳的非界面模块；`ui.py` / `webview2_runtime.py` 的 `webview` / `clr` 导入必须延迟到需要界面的函数内。
- 原验证范围包括 settings_store CRUD / 原子写 / 校验失败、secrets DPAPI 往返与旧格式迁移、bridge 参数及错误映射、密钥仅经环境传递、coordinator 代际 / ack 超时 / 退出回收、theme_runtime 占位符 / 预算 / 受信 URL 和 paths 的 UNC 拒绝。使用替身进程、桥或 SQLite fixture 的历史结果，只证明其对应契约。
- 2026-09-07 按用户要求归档并移除旧测试及一次性验收脚本。原记录和结果统一保存在根 [CHANGELOG.md](../CHANGELOG.md)；它们不是当前仓库中的可运行测试命令。
- 构建继续调用 `tools/package_contract.py` 执行正式包契约校验；运行依赖、嵌入模块、前端资源和敏感材料检查继续保留。发布与依赖验证入口见 [构建说明](../docs/BUILD.md)。

## 2026-09-07 验证边界与维护入口

- 本地生命周期、模型选择事务、relay、会话持久化、壳 API 暴露边界及设置双语浏览器回归的历史结果，见 [CHANGELOG.md](../CHANGELOG.md)；具体结论绑定当时的源文件和运行记录。
- 历史 LeoTree 验收使用独立 Chromium profile、合成会话、真实上游菜单 / 新会话函数及 mock 网络，检查导出文件，并执行目标仓库自身 `parseImport/assertTree/previewImport/acceptPreview/loadWorkspace` 的新树保存与旧树保留。该记录不访问正式用户会话，也不代表真实 WebView2 与 WSL 端到端已通过；本次正式安装版结果以 [CHANGELOG.md](../CHANGELOG.md) 当日条目为准。
- 正式安装版仍需按当前构建产物验证：免密与带 key 切换、真实完整问答和持久化、关闭重开、实际菜单/文件保存、LeoTree 实际页面导入、归档恢复及仅针对专用测试对象的删除。小模型长上下文、复杂科研执行可靠性、网络物理断开场景均不可由局部通过推定。
- Python 模块进入 EXE 的 PYZ，需要重建；注入源需经 `tools/bundle_theme.py` 组成安装版 `theme/leo-inject.js`。bridge Python 运行资源必须随构建 / 部署并核验，不能仅复制壳 Python 源文件到正式目录。

## 明确不做（二期；原始范围已按上述实现更新）

在线更新（--update）、CLI 全量工作台数据导出导入、自定义主题上传、项目 persona、--settings 之外的实例 action 细化仍未实现。检查更新.bat 调 --update 会得到退出码 2（日志说明）。本次会话知识树文件导出与本机归档/回收站不再列为二期待办；它们也不能替代整个工作台或附件的完整备份。

## 2026-09-26 注：上游注入层已移除

经用户批准，删除了只服务于上游 OpenAI4S 页面的注入层：`stage/leo-inject.js`、`stage/leo.css`、`stage/unified-settings-adapter.js`、`stage/i18n-brand-patch.js`、`stage/i18n/`，以及 `ThemeRuntime.injection_script`、`DesktopUI` 的注入生命周期（`_inject_backend`、`refresh_injection`、失败横幅）和 `ShellApi.return_to_workbench`。上文描述这些部分的段落是历史设计记录。现在壳只加载两个 Leo 自有文档：启动页 `shell.html` 与工作台 `workbench.html`（内联 `workbench.css/js` 与 `research-panel.js`）。只被注入层调用过的后端方法（实体隐藏/恢复/删除、本地技能扫描与导入、运行时状态）仍保留，目前没有界面调用。
