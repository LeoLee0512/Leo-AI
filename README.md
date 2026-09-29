# Leo AI 3.0.0

面向科学研究的 Windows 桌面工作台：用对话推进研究，用可核验的科研任务得出结论。
一个真实的科学问题可以从想法走到模型、计算、验证，最后得到一份经得起检查、复现和质疑的结论；
科学判断、建模选择和结论始终由人来做，AI 负责计算、核对与执行。

版本号为 3.0.0，桌面入口和窗口名为「Leo AI 3.0」。

## 主要能力

**对话工作台**
- 按项目和日期组织对话，支持归档、回收站与经确认的彻底删除；可导出完整对话。
- 每个对话单独选择模型与思考强度；每一轮只突出最终答案，过程说明、执行步骤和模型原始思考
  （DeepSeek 等推理模型的 `reasoning_content`，标明「原文，未经核实」）收在可展开的「思考与步骤」里。
- 审批模式 Off / Smart / Auto：Smart 下运行计算、写新文件、查资料直接进行，命令行、修改已有文件、
  外部工具与凭据操作先问；明确只读的命令（如 `pip list`、`df -h`）自动放行并记入步骤。
  打开对话时会与后端实际规则对账。
- 定时任务：到点在指定对话里发出一条消息；只在应用打开时执行，错过的只标记不补发。
- 答案里的文件链接可直接预览；自带技能 `local-env-check` 让本机问题直接执行命令而不先联网。

**科研任务（可信 PINN 闭环）**
- 两个已验证模板：一维 Poisson −u″ = π² sin(πx)（0 < x < 1，两端 u = 0），
  二维 Poisson −(u_xx + u_yy) = 2π² sin(πx) sin(πy)（单位正方形，四条边 u = 0）。
  草案由模型整理并自动识别一维或二维，匹配规则是确定的，模型无法扩大支持范围。
- 流程：草案 → **本人确认模型** → 准备（预留盲测集）→ **本人确认正式运行** → 主实验 G1–G5 →
  Tier-1 扰动检验 → 独立环境复现 → G6 → 结论等级（C0–C3）→ 导出证据包。两次确认不受任何审批模式影响。
- 盲测集在训练前生成并封存、只打开一次；每台安装一维、二维各 32 个，准备即永久占用，成败不退。
- 每次运行绑定代码指纹（codeHash）、规格、环境与种子；证据页和导出包内的「证据说明书」
  分三层讲清结论、六项检查和凭什么算证据，并可一键重新核对。
- 二维的 10 个种子与 Tier-1 重训并行进行，结果与逐个训练逐位相同。

**外观与账号**
- 墨色秋意主题与多套内置配色，支持跟随系统、深浅色与自定义 JSON 主题（先预览再保存）。
- 本地账号可修改显示名、头像和简介；设置、工作台无需登录。

## 源码布局

| 路径 | 内容 |
| --- | --- |
| `leo_shell/`, `launcher/` | Windows 桌面壳：界面、配置、审批、定时任务、科研任务服务 |
| `stage/`, `assets/` | 前端页面与样式、主题、图标、开场动画及原始素材 |
| `bridge/` | WSL 桥接脚本与对上游后端的运行时覆盖层（上游源码本身不在仓库里） |
| `pinn/`, `scientific_reference/`, `specs/` | PINN 研究核心、独立参考解与冻结规格（科研代码身份） |
| `governance/`, `adversarial/` | 研究宪法、可信协议、修正案与 PRELOCK 输入 |
| `experiments/` | 预注册与协议、盲测集登记（产品的额度与防重复抽取依赖它），以及测试用到的少量记录 |
| `docs/` | 构建说明、可信研究说明与主要研究报告 |
| `skills/`, `tests/`, `tools/` | 自带技能、测试、构建 / 部署 / 校验工具 |
| `manifests/`, `runtime/*.json` | 锁定依赖、资产来源、上游版本与运行环境下载清单 |

## 构建与部署

详细工具链要求见 [构建说明](docs/BUILD.md)。在 Windows x64 上使用锁定的 Python 3.12.9 工具链，
不要把已有用户安装目录当成源码或构建输入。

```powershell
python tools/build_wheelhouse.py build
tools/provision_venv.ps1
.venv/Scripts/python.exe tools/build_wheelhouse.py verify
tools/build_launcher.ps1 -OutputRoot C:/LeoBuild/3.0.0
```

构建出的 `dist/LeoAIStudio` 是 **更新包**，不能仅复制其中的 EXE 当作完整安装。
完整安装还需要 WSL2 Linux 环境、`bridge/leo_bridge.sh`、锁定的 OpenAI4S 源码和运行环境、WebView2，
以及两个独立的科研 Python 环境。`runtime/dependencies.json` 给出原始下载地址与 SHA-256，
`runtime/runtime-manifest.json` 给出相对安装路径，`manifests/upstream-pin.json` 固定上游版本。
下载后必须核对哈希；当前仓库不提供一键全新安装器。

对已有完整安装：

```powershell
tools/deploy_release.ps1 -AppRoot C:/LeoAI -PackageRoot C:/LeoBuild/3.0.0/dist/LeoAIStudio -ShortcutPath <临时路径>
.venv/Scripts/python.exe tools/build_manifest.py -o manifests/build-current.json --app-root C:/LeoAI
.venv/Scripts/python.exe tools/verify_release.py --manifest manifests/build-current.json --app-root C:/LeoAI --strict
.venv/Scripts/python.exe tools/theme_asset_provenance.py --app-root C:/LeoAI --strict
```

发布校验要求构建回执与清单一致，并要求科研运行时的源码快照与发布提交一致（见构建说明）。
不要将此仓库直接覆盖用户安装目录，也不要上传 `user/` 或运行日志。

## 验证

- 全量测试：`.venv/Scripts/python.exe -m pytest -p no:cacheprovider`；构建环境不装科学依赖，
  需要 torch 的测试会跳过，请在科研 Python 环境里另跑 `tests/pinn`。
- 3.0.0 整理后（科研代码身份未变，codeHash `84ac5b8f…`）：全量测试 1591 通过、0 失败、34 跳过；
  科研环境 `tests/pinn` 956 通过、0 失败。
- 已验证的科学结论只来自各自的运行记录与证据包；构建、测试通过不等于任何科学结论。

## 公开快照说明

公开仓库是经用户批准的源码快照，不含私有开发历史，也不含：安装包与二进制运行环境、wheelhouse、
用户数据与密钥、历史实验的原始运行目录（运行记录里带有设备标识）、检查点与图片产物。
因此少数依赖这些记录的测试在公开快照里会找不到文件；研究报告中的相对链接也可能指向未公开的原始记录。

## 来源与许可

- 计算与会话后端基于 [OpenAI4S](https://github.com/PKU-YuanGroup/OpenAI4S)（MIT License），
  版本固定在 `manifests/upstream-pin.json`；上游源码不随本仓库分发，`bridge/` 只包含运行时覆盖层。
- 界面素材的来源记录在 `manifests/runtime-asset-origins.json`；开场动画与背景原图为 AI 生成
  （使用受各生成服务条款约束）。
- 本仓库未授予任何开源许可，保留所有权利（All rights reserved）；公开仅供查看。
