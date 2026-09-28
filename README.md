# Leo AI 2.1.2

面向科研的 Windows 桌面工作台，包含模型配置、会话界面、科研流程及 PINN 验证代码。

本仓库是用户批准的 **精简完整源码快照**，来自本地发布提交
`afc4aa4645284c270ff69127117aefd97be193d9`。不导入旧 Git 历史。
版本号为 2.1.2，桌面入口和窗口名保留「Leo AI 2.1」。

## 本版修复

- 首页更新为面向学习、研究与创作的研究桌面，加入轻导航及研究示例；邮箱账号仅保留未启用的界面入口，后端按用户要求后续接入。

- 合并同一轮次内相邻的重复回答；隐藏自动附加的「完成内容 / Completed work」清单，历史消息重新打开同样生效。

- 保留用户提供的 Leo 手写体图标，兼容资源名仍为 `leo-lion.*`。
- 修复主页打开设置后装饰背景越界、产生矩形残影的问题。
- 不完整更新包缺少 WSL 桥接脚本时，明确提示安装文件不完整，不再误报模型连接失败。
- 已在原正式安装目录完成升级、恢复桌面入口并验证可以进入工作台；原有配置和会话保留。

## 源码布局

| 路径 | 内容 |
| --- | --- |
| `leo_shell/`, `launcher/` | Windows 界面、配置与启动逻辑 |
| `stage/`, `assets/` | 前端、主题、图标与原始素材 |
| `bridge/` | WSL 桥接脚本与科研工作台服务 |
| `pinn/`, `scientific_reference/`, `specs/`, `governance/` | 科学代码、参考实现、规范与判据 |
| `experiments/` | 实验驱动源码、问题定义、配置与预注册；不含历史运行产物 |
| `skills/`, `tests/`, `tools/` | 技能、测试、构建及校验工具 |
| `manifests/`, `runtime/*.json` | 锁定依赖、资产来源与运行环境下载清单 |

本仓库不包含安装包、Python/WSL/WebView2 二进制、wheelhouse、用户数据、密钥、
历史实验运行目录、检查点、台账和图片产物。本地原档全部保留。
`CHANGELOG.md` 和历史研究文档保留原文；其相对链接可能指向未随快照公开的实验档案。
没有重新运行科学实验，也没有新增科学结论；ACA-9 仍保持原状态。

## 构建

详细工具链要求见 [构建说明](docs/BUILD.md)。在 Windows x64 上使用锁定的 Python 3.12.9
工具链（需符合构建脚本要求的原生 DLL），不要把已有用户安装目录当成源码或构建输入。

```powershell
python tools/build_wheelhouse.py build
tools/provision_venv.ps1
.venv/Scripts/python.exe tools/build_wheelhouse.py verify
tools/build_launcher.ps1 -OutputRoot C:/LeoBuild/2.1.2
```

构建出的 `dist/LeoAIStudio` 是 **更新包**，不能仅复制其中的 EXE 当作完整安装。
完整安装还需要 WSL2 Linux 环境、`bridge/leo_bridge.sh`、锁定的 OpenAI4S 源码和运行环境、
WebView2，以及科研 A/B 环境。`runtime/dependencies.json` 给出原始下载地址与 SHA-256，
`runtime/runtime-manifest.json` 给出相对安装路径，`manifests/upstream-pin.json` 固定上游版本。
下载后必须核对哈希；上游源码须保持该版本且工作树干净。当前仓库不提供一键全新安装器。

对已有完整安装，可使用：

```powershell
tools/deploy_release.ps1 -AppRoot C:/LeoAI -PackageRoot C:/LeoBuild/2.1.2/dist/LeoAIStudio -ShortcutPath "$env:USERPROFILE/Desktop/Leo AI 2.1.lnk"
.venv/Scripts/python.exe tools/theme_asset_provenance.py --app-root C:/LeoAI --strict
```

发布校验还要求生成本次构建的回执和清单，并对齐科研运行时的源码副本，详见
[构建说明](docs/BUILD.md) 和 [发布说明](docs/RELEASE_2_1.md)。
不要将此仓库直接覆盖用户安装目录，也不要上传 `user/` 或运行日志。

## 验证范围

原完整工作树在本次发布前：全量测试 **1460 通过、32 跳过、0 失败**；
已安装科研解释器运行 `tests/pinn`：**952 通过、0 跳过**；
严格发布校验 **17/17**，界面资产来源校验 **16/16**。
32 个跳过项来自构建环境未装科学依赖及独立工作树未设置默认上游安装位置。
真实窗口已验证进入工作台、读取现有配置/会话、打开和关闭设置。

此精简快照中的历史档案审计测试依赖未公开的实验产物，不能把原工作树的全量结果
等同于仅下载本仓库后的全量结果。桌面产品测试可运行：

```powershell
.venv/Scripts/python.exe -m pytest tests/leo_shell
```

`tests/` 保留完整测试源码；恢复历史实验档案和相应科学依赖后才能复核全部审计测试。
Node 浏览器验收脚本另需 Playwright 环境，未打包进 Python 依赖。

## 来源与许可

`manifests/source-export.json` 记录快照基线、补入的运行脚本来源及排除规则。
补入的三个运行文件逐字节来自本次升级所使用的正式安装基线，未包含用户配置。
第三方依赖遵循各自许可证；本次发布未替作者添加新的开源许可授权。
