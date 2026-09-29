# Leo AI 改进日志

整理日期：2026-09-26。范围：桌面 `LeoAIStudio-build` 与 `LeoAI-Research-Candidate-20260926` 两个文件夹的独立改进、测试、审阅及验收报告。本文件是合并后的唯一独立报告入口。

## 当前结论

已安装候选版完成自有工作台及定向前端验收；正式科学闭环仍未验收，没有本轮新增 C2。历史实验的 C2、自动测试通过、模拟界面和真实安装验收不能互相替代。以下为既有报告的整理，不是本次重新运行测试或实验所得结果。

最终候选源码：`6d4ec0f59a6ecc75b1225cbd983b7553f68bb64c`。原项目与候选版本不同，不能把候选验收结论套用到当前项目或旧安装。候选科学状态仍为 `CANDIDATE_NOT_SCIENTIFICALLY_ACCEPTED`。

## 改进历程

| 阶段 | 发现的问题与改进 | 结果与边界 |
| --- | --- | --- |
| 早期 P0 与科研审阅 | 区分重建对抗测试和独立原始测试；登记便携性、技能漂移、安装与科学前提缺口 | 早期 FAIL、PARTIAL、NOT TESTED 原样留档，不被后续组件通过覆盖 |
| 09-08 至 09-10 | 修复入口、重复导航、空状态、实体删除持久化；增加会话模型绑定、推理能力与运行时组合安装；修复 CRLF 兼容问题 | 源码、离线组件、供应商及已安装应用的检查范围分开记录，具体计数见原文 |
| 09-14 | 整理仓库、调整主题源位置与安装路径、限制 pytest 收集范围、重新构建部署并同步技能 | 原清理记录和操作记录完整合并，历史部署身份继续保留 |
| 09-14 至 09-16 | A-0001/A-0002、评估集三分、样本账本、身份派生、独立复现、Gate 与 Claim 约束及对抗审计 | 宪法演进与历史 Poisson 1D/2D 校准是历史证据，不构成本轮候选的新结果 |
| 09-17 至 09-20 | 环域校准失败后开展预算诊断、排除实验和嵌套预算干预 | 失败与未决根因保留，不把预算变化或局部改善包装为成功 |
| 09-26 科研候选 | 接入任务、草案、人工确认、运行准备、身份绑定、主实验/Tier-1/复现/G6 串联及导出校验 | 自动回归和准备夹具通过不等于正式训练、人工确认或完整科学验收 |
| 09-26 人工反馈修复 | DeepSeek 模型 ID 配置错误、草案未生成且缺导航、增强脚本返回值不符合桌面壳约定 | 保留密钥修正模型配置；增加草拟/重试指引；修复注入返回值；历史失败消息保留 |
| 09-26 自有工作台 | 重做首页、项目/历史、聊天、科研四视图及设置；修复重启后凭据恢复、逐消息绑定和无参数桥接 | 真实 DeepSeek 聊天与草案有定向实测，保留高级 Notebook/计算入口及上游来源 |
| 09-26 前端统一与自有笔记本 | 工作台深绿配色与启动页暖黄骤变、颜色单调；「笔记本与计算」会打开 OpenAI4S 上游页面；「管理模型配置」退回启动页却不打开设置；启动页「关于」外链会把窗口带离 Leo | 工作台改用淡墨浓秋（方案 A）并以颜色表达可信度层级；笔记本改为 Leo 自有只读视图，界面上已无进入上游页面的入口；仅离线预览与自动测试验证，真实安装的原生窗口尚未验收 |
| 09-26 环域停线 | 环域 r1 的 Gate 5b 失败根因经三轮诊断仍无法区分：7 个候选原因只排除 2 个 | 按用户决定写入「根因未定」诊断记录，状态由 FAILURE_RECORDED 转为 STOPPED_THE_LINE，交人裁决；未训练、未打开任何 Claim 集，不产生 Claim |
| 09-26 产品闭环缺口 | 现有 3 个科研任务都停在草稿：DeepSeek 把模板冻结的设置当成缺失导致「不支持」；方程只能逐字匹配；准备失败或超时后任务走不下去；过期的「运行中」会挡住其他运行确认；确认模型时看不到方法 | 草案附带方法与验收规则并纳入模型确认的哈希；提示词说明模板设置不算缺失；方程规范化匹配；新增「以此草案新建任务」；超时留痕；过期运行状态先结清。仅自动测试与离线预览验证，尚未构建部署，正式运行尚未进行 |
| 09-26 删除上游注入层 | 上游页面已无入口，只为它服务的注入脚本、样式表、设置适配层、文案补丁与中英文表仍在构建、部署与校验链中 | 用户批准后删除；构建/部署/清单/校验改为逐个核对 Leo 自有文档；部署会把旧安装中残留的注入文件移入回滚目录；字体文件保留待定 |
| 09-26 消息操作 | 用户要求回复可复制与选择性复制、可赞可踩、回复与提问可转发 | 每条消息下增加复制/赞/踩/转发；赞踩存入会话；转发只把内容放进目标对话输入框，不自动发送；仅离线预览与自动测试验证，尚未部署 |

## 验证结果的适用范围

| 版本 / 检查 | 已记录结果 | 不可推断的结论 |
| --- | --- | --- |
| a6586cb 全仓 | 1454 passed / 33 skipped | 不代表最终候选全仓或安装验收 |
| a6586cb 科学环境 | 911 passed / 0 skipped | 不代表正式 6000 步闭环 |
| cde1259 核验器回归 | 109 passed / 0 skipped | 与其他集合重叠，不相加 |
| 8b61ce6 修复回归 | 298 项唯一测试通过 | 后端调用不能替代原生 UI |
| 前端主回归 | 320 passed / 1 skipped | 不是最终提交的全仓重跑 |
| 6d4ec0f 设置修复回归 | 22 passed / 1 skipped | 与主回归重叠，不相加 |
| 最新构建与部署 | 23/23 资产匹配；365 个部署文件摘要匹配；24 个配置、凭据和科研文件部署前后相同 | 仅证明相应字节与部署检查 |
| 实机定向验收 | 自有首页、历史/项目、真实聊天与草案、设置、重启、高级入口/返回 | 聊天与草案在 f8a7074，设置与重启在 6d4ec0f；高级入口在 73fd11c，最终版相关路径未变化 |
| 实际取消 | NOT VERIFIED，回复在点击停止前完成 | 不得登记取消通过 |
| 正式主实验、Tier-1、独立复现、G6、成功/失败完整任务包 | NOT RUN / NOT DELIVERED | 不允许宣布科学验收或新增 C2 |

## 尚需改进与验收

1. 在产品中补齐草案缺失的建模与运行信息，由人确认模型和具体运行包。
2. 在新身份下实际完成主实验、规定验证、Tier-1、独立复现与 G6，保持冻结阈值，保留真实失败路径。
3. 实测取消、运行中重开及最终科学证据导出。自动测试和历史结果不得替代这些检查。
4. 核对完整证据后才允许对应 Claim。人的结论解释不能提升机器允许的 Claim。

## 清理范围与证据保留

本次只删除下表登记且完整并入附录的独立报告；旧 `CHANGELOG.md` 在本文件附录中保留原文。2026-09-26 复核后，仓库内 43 份报告中的 16 份仍被测试、工具、治理文件、代码身份文件、预注册或哈希记录引用，原文件恢复原位（附录原文同时保留），实际删除 27 份；判定见“原文件保留的判定”。没有删除测试代码、程序、配置、密钥、科研任务、实验、账本、原始测试 XML/日志、截图、机器回执、哈希清单或回退包。没有清理其他工作树、固定上游或候选 `runtime/science-source` 中的源码副本。

`governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md` 是被历史证据策略引用的审计证据，`experiments/` 下 TRUST_REPORT/审计记录属于科学证据链，均原位保留。预注册、规范、设计决策、报告模板及 inbox 原始评审建议也原位保留，不能当作独立验收结论删除。

旧文中的相对链接以各自“原位置”为基准；已删除报告的内容可按下表编号在本文件查找，处理为“原文件保留”的报告仍可在原位置直接打开。旧文中的操作指令和旧状态只是历史记录，不是本次执行授权。个别旧报告已有乱码，保留其原字节，不擅自改写。

## 合并来源与删除清单

SHA-256 对应整理前原文件字节。附录原文用于完整保留细节；正文摘要用于快速了解改进与限制。

| 编号 | 原位置 | 字节数 | 原 SHA-256 | 处理 |
| --- | --- | ---: | --- | --- |
| R001 | `项目/CHANGELOG.md` | 208755 | `c48add8c613485157f52cfecd7d23823e5180a364172a8204ae6d91c9bbd383e` | 原地合并 |
| R002 | `项目/20260914软件修改报告.md` | 65173 | `5413eba04e05fcdf68d2569ca3880218e7b8dd665d9fd49b51aa10a7e3b4e3ed` | 原文合并后删除 |
| R003 | `项目/20260914仓库卫生记录.md` | 55260 | `6c3d9f866a361c9f81485ed96a16aba53c80477dc74aac265c99474b0eef1e30` | 原文合并后删除 |
| R004 | `项目/docs/F008_SOURCE_PROVENANCE_CLOSURE_PHASE2.md` | 9820 | `4217b5caa255707e0486841ad0a2adca127a2fdf34d1e886cd6285bf426f1c17` | 原文合并后删除 |
| R005 | `项目/docs/LEO_CONVERSATION_FRONTEND_REPORT_20260909.md` | 77602 | `72a2418d606ff724d242361e84dca5d4aa3470ca19c7bae5b1c9fcbecb5850d6` | 原文合并后删除 |
| R006 | `项目/docs/LEO_CONVERSATION_RUNTIME_INTEGRATION_REPORT_20260909.md` | 42853 | `63be1546994cf892bbc05d175e0e58eea08215588a7723a6670ac69a1bea96f4` | 原文合并后删除 |
| R007 | `项目/docs/LEO_EMPTY_STATE_RETURN_UI_REPORT.md` | 5875 | `968806909b0bd5898861575b572430e65c0fccf8677ae203c34f7afea9da03c5` | 原文合并后删除 |
| R008 | `项目/docs/LEO_ENTITY_DELETION_PERSISTENCE_REPORT.md` | 9485 | `0613bf3e70417798a2f3f9bb02b9108b0cf0e72847e52a165d709aa323977a16` | 原文合并后删除 |
| R009 | `项目/docs/LEO_ENTRY_BROWSE_RUNTIME_REPORT.md` | 13319 | `9d7023f631e87640acae36f81dcea233cf84df60b4a83cf11bb5e039ab5d20d1` | 原文合并后删除 |
| R010 | `项目/docs/LEO_ENTRY_NAVIGATION_IMPLEMENTATION_REPORT.md` | 16258 | `fa452cd6c747046d11988aae6207626dea055e859af4e2b5c535ad410171e522` | 原文合并后删除 |
| R011 | `项目/docs/LEO_LOCAL_QWEN_REASONING_REPORT_20260909.md` | 11296 | `53ccf1dd9d592dd6669765b112ad27f07116d4e67c82870291029d6d0cc365bc` | 原文合并后删除 |
| R012 | `项目/docs/LEO_NATIVE_NAVIGATION_RECOVERY_REPORT.md` | 8077 | `c65fe3c61a97f5143c3de56e499d7ce825a481ca6dc7be97b34c625af052fc2b` | 原文合并后删除 |
| R013 | `项目/docs/LEO_REASONING_AND_THOUGHT_RUNTIME_REPORT_20260909.md` | 14158 | `096fa79d7acac991d59ea25143ec47fec4132072e2129bfdb6624b3b0b3ba9e0` | 原文合并后删除 |
| R014 | `项目/docs/LEO_RUNTIME_CRLF_COMPATIBILITY_REPORT_20260909.md` | 10709 | `2fe84bed7e97bbf85c3f0991005fddedc4c8975a7b1f8207e4cef1b6ebc4789a` | 原文合并后删除 |
| R015 | `项目/docs/LEO_RUNTIME_FEATURES_INSTALLER_REPORT_20260909.md` | 14385 | `53f29704147a94fb55359282d6aba11b74d731e689a105ac74025fb7b866ce5e` | 原文合并后删除 |
| R016 | `项目/docs/LEO_SESSION_MODEL_BINDING_REPORT_20260909.md` | 12826 | `84814dee685e4996db182f9d9726f77f14ee993455e67cfe91f5193f948037f1` | 原文合并后删除 |
| R017 | `项目/docs/LEO_UI_INTEGRATION_DELIVERY_REPORT.md` | 5530 | `ebf855e6c5a3341b6e6dabff80f2a94d2c1cd56df1d4e52194a457988758bd46` | 原文合并后删除 |
| R018 | `项目/docs/OPERATION_LOG_20260914.md` | 157034 | `8b12a15492cf7450b827fb4b7d45c856cdce7e52ed8d32beb2c3dbc1e3fb6e66` | 原文合并后删除 |
| R019 | `项目/docs/P0_CANONICAL_SKILLS_DRIFT_AUDIT_20260909.md` | 11414 | `64ecb307b69df1e8e99150c5102934effab26dfe83565b7c1278620375be3a47` | 原文合并后删除 |
| R020 | `项目/docs/P0_EXECUTION_STATUS.md` | 24844 | `ca70a988c2c60b0f79b26615481d129a9c35f31fc6b995da3f22c0328b66f119` | 原文合并；原文件保留 |
| R021 | `项目/docs/P0_FINAL_CLOSURE_REPORT.md` | 32185 | `6fb34f5dbe5e3b4048b3bb8ba804f257712a5453bdbbf63c022c3960dbf39071` | 原文合并；原文件保留 |
| R022 | `项目/docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` | 5736 | `1e3c9edbd45e47416bebc9cda1f4170ef231fadab8b39d8187bf0d9b96cf44c0` | 原文合并；原文件保留 |
| R023 | `项目/docs/P0_MANUAL_ENVIRONMENT_ACCEPTANCE_PACKET.md` | 26198 | `55518d830daba9bf13a348e339976957f757ca0475b226e5d7b2e0000a9a2357` | 原文合并后删除 |
| R024 | `项目/docs/P0_RELEASE_CANDIDATE.md` | 6761 | `b5099367d20aa6a9830c39fb931e1d1bc3d5768b2d7d345fc01bbab78af2b35e` | 原文合并；原文件保留 |
| R025 | `项目/docs/P0_RUNTIME_REMEDIATION_20260908.md` | 9813 | `abdf17dc7b45c221fb2e437735fbd4eeee4a40ae0acfc81e896002b1729305ba` | 原文合并；原文件保留 |
| R026 | `项目/docs/PINN_MVP_AND_CFD_READINESS_REPORT.md` | 37721 | `afa4fe40df71f60289d430fd9eaf50fbedc8784f7f8252e87713e0ace3a57afc` | 原文合并后删除 |
| R027 | `项目/docs/PINN_P2_FINAL_HUMAN_REVIEW_PACKET.md` | 34581 | `c73e7a954f262840988ea25e1451e428751f33cc144a8e0fac0d82888ea9abbd` | 原文合并后删除 |
| R028 | `项目/docs/PINN_PHASE2_RECONCILIATION_20260909.md` | 19172 | `af6aaeadd7c52e79a49104bbd1383ec0527b754ae714b1ee19cd73e764772a5c` | 原文合并后删除 |
| R029 | `项目/docs/RESEARCH_SOP_MIGRATION_AUDIT_24f3fd7.md` | 3596 | `f786a056e5f854a2ca57f246d484507f843208e4f4ddc860571c20278ca19c4f` | 原文合并；原文件保留 |
| R030 | `项目/docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md` | 13728 | `9881e50d8f6c1cdfbc910ae9c8fdd3b42e37356a457271bbc6862cd53f948fc1` | 原文合并；原文件保留 |
| R031 | `项目/docs/pinn-trust-loop/ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md` | 17961 | `cce46dfe4b55f1c828e05170746c8d1e1879d6306dd561854e5396cfdc014232` | 原文合并；原文件保留 |
| R032 | `项目/docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md` | 33109 | `306fb39b86549d3edd5d1d667318e54ec762c58dd81da5ddaf82ec74be3a34e7` | 原文合并；原文件保留 |
| R033 | `项目/docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md` | 21206 | `b30a5c0bb2d71f49806b4732ea771d6ab53e132a7968806f9ebca0b5cc7b1b65` | 原文合并；原文件保留 |
| R034 | `项目/docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md` | 27666 | `cfb018f5a9676241a710b52422d5a248e8d8f8424bdb3ecc66b5b720de329df3` | 原文合并；原文件保留 |
| R035 | `项目/docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md` | 9992 | `b998796ebbf4c34b5bffbdcf87379234006d957a20338c0aed7945b7bd12e61e` | 原文合并后删除 |
| R036 | `项目/docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md` | 14821 | `5b7d12be1b9e93372e7ab81565daea21cc555adc106ab99d3829124513a32044` | 原文合并；原文件保留 |
| R037 | `项目/docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md` | 24101 | `a3937849685291cf8df0e056c896f69baaec1fd5cb2491490ba5e8647978cc03` | 原文合并后删除 |
| R038 | `项目/docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md` | 22763 | `c3f5ec74dcbe90dcdf2577c97541f6208fee6630639d9aacbe1e702fa7046d37` | 原文合并；原文件保留 |
| R039 | `项目/docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md` | 29853 | `82b86447da1616b2c50f71aa73ef6a855dfaec2786ece694e8e73c1226a1a726` | 原文合并后删除 |
| R040 | `项目/docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md` | 27749 | `5d73938f6f1bf50f88c8f5302f924a06d5cf8433cee8ec3bfe59f90067226314` | 原文合并；原文件保留 |
| R041 | `项目/docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md` | 12573 | `f3fd96e4e0c100fe74c986fbf981c534dc13f024ba543573ea1d25a9475ffff1` | 原文合并后删除 |
| R042 | `项目/docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md` | 17548 | `d6387d1fe2a6b5fc805c581703b441c3f21c60ca63dd8741e1e25e032097a947` | 原文合并后删除 |
| R043 | `项目/docs/pinn-trust-loop/R1_MERGE_NOTES.md` | 9432 | `47816b4214a7d5bd2a8251260997fe64f304054e345e9aa02ff8902530b580fa` | 原文合并；原文件保留 |
| R044 | `项目/docs/pinn-trust-loop/R2_MERGE_NOTES.md` | 32698 | `31dfeac82f580ee13d9008fd4e35f9182f84a8cb7b34563be9447f3f2a5ef487` | 原文合并；原文件保留 |
| R045 | `候选版/前端重塑验收报告.md` | 4233 | `de0225e1c56453ad277adfc65b1a56c8ef611a187eb53583d46713e09d4db699` | 原文合并后删除 |
| R046 | `候选版/审阅与验收报告.md` | 8705 | `0a94144df5388559c3a88f13562dd1f1adb8f42405e1c9d9bc299bef691ce248` | 原文合并后删除 |
| R047 | `候选版/验收故障修复说明.md` | 3554 | `8ef375e8058a8aae0100d0bfd4674f8d990c030d650eaa1febd9dde06a1d932b` | 原文合并后删除 |

## 原文件保留的判定

2026-09-26 复核。报告原文已并入附录，不等于原文件可以删除。仍被下列任一方引用的报告保留原文件：

1. 测试读取它或断言它存在；
2. 工具在输出或说明里把用户指向它；
3. 引用方是治理文件、代码身份文件、预注册、冻结协议或审计证据。这些引用方改一个字节就会移动 codeHash 或破坏证据链，不能靠改引用方来修链接；
4. 仓库内的哈希记录登记了它的原字节。

先例：R020、R021、R022、R024、R029 在 2026-09-07 的报告合并中删过一次（快照 `7c7a6b1`），2026-09-08 由 `1c96066` 从 `a4455cc` 恢复，同时新增 R025，六份的 SHA-256 登记在 `research_logs/PINN_MVP_CHANGED_FILES_20260908.json`。

扫描方法：按文件名（去后缀）和原字节 SHA-256，在除本文件外的全部已跟踪文件中查找引用。R030–R044 均位于 `docs/pinn-trust-loop/`。

| 编号 | 保留的原文件 | 引用方 | 删除后的后果 |
| --- | --- | --- | --- |
| R020 | `docs/P0_EXECUTION_STATUS.md` | `research_logs/PINN_MVP_CHANGED_FILES_20260908.json`（登记 SHA-256）；`docs/rollback/portability_check.pre-P0-closure.py` | 哈希记录无法核对 |
| R021 | `docs/P0_FINAL_CLOSURE_REPORT.md` | `tests/test_suite_provenance.py`；同一哈希记录 | 措辞诚实性检查被静默跳过，跳过理由写成“尚未撰写” |
| R022 | `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` | `tests/test_manual_acceptance.py`；`tools/manual_acceptance/`、`tools/build_wheelhouse.py`、`tools/portability_check.py`；同一哈希记录 | 测试失败（FileNotFoundError）；工具把用户指向不存在的清单 |
| R024 | `docs/P0_RELEASE_CANDIDATE.md` | `tests/test_suite_provenance.py`；同一哈希记录 | 同 R021 |
| R025 | `docs/P0_RUNTIME_REMEDIATION_20260908.md` | 同一哈希记录 | 哈希记录无法核对 |
| R029 | `docs/RESEARCH_SOP_MIGRATION_AUDIT_24f3fd7.md` | 同一哈希记录 | 哈希记录无法核对 |
| R030 | `A-0002_FINAL_CLOSURE_REVIEW_20260915.md` | `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md`（已 ACCEPTED 的修正案） | 修正案的引用断开 |
| R031 | `ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md` | `experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md`（预注册）；`pinn/experiments_annulus/checkpoint_annulus.py`、`pinn_torch_annulus.py`（代码身份内） | 预注册和代码注释的引用断开 |
| R032 | `ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md` | `experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md`（预注册）；`experiments/annulus/ANNULUS_NEXT_ROUND_DESIGN_NOTES_20260921.md` | 预注册的引用断开 |
| R033 | `ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md` | `experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md`（预注册） | 预注册的引用断开 |
| R034 | `ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md` | `experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md`（预注册） | 预注册的引用断开 |
| R036 | `LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md` | `experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json`（冻结协议） | 协议的引用断开 |
| R038 | `POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md` | `experiments/poisson2d/PORTABILITY_AUDIT_20260916.md`（审计证据） | 审计的引用断开 |
| R040 | `POISSON2D_CALIBRATION_REPORT_20260916.md` | `tests/pinn/test_code_identity_completeness.py` 断言它存在 | 测试失败 |
| R043 | `R1_MERGE_NOTES.md` | `governance/PINN_TRUST_PROTOCOLS_R1.md`（代码身份内）；`governance/AMENDMENTS/A-0001-trust-loop-r1.md`；`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`；`docs/PINN_TRUST_LOOP_TEAM_PROMPTS_20260914.md` | 治理文件的引用断开 |
| R044 | `R2_MERGE_NOTES.md` | `governance/PINN_TRUST_PROTOCOLS_R1.md`（代码身份内）；A-0001、A-0002 修正案；`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`；`docs/PINN_TRUST_LOOP_TEAM_PROMPTS_R2_20260915.md` | 治理文件的引用断开 |

其余 27 份（R002–R019、R023、R026–R028、R035、R037、R039、R041、R042）没有来自现存文件的引用，按原计划删除。

待定：保留下来的报告里有 3 处链接指向已删除的报告，内容可按编号在附录查找，暂未恢复：`ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md` → R035，`LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md` → R041，`POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md` → R037。

## 操作日志

### 2026-09-26 基线提交与原文件保留复核

执行位置：工作树 `.claude/worktrees/changelog-review-91e1c6`，分支 `claude/changelog-review-91e1c6`。主检出 `master` 的工作区全程未改动，其中未提交的整理结果保持原状。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 只读核查主检出未提交的整理结果 | 47 份附录与登记的 SHA-256 逐字节一致；R001–R044 与 `e0acab4` 中的原文件一致；删除集合与登记表一致 |
| 2 | 核查时误在系统临时目录创建 `deleted_names.txt` | 随即删除 |
| 3 | 用户选择方案 A：复制主检出的 `CHANGELOG.md` 到工作树，`git rm` 同样的 43 个文件（用户审批通过） | 与主检出工作区的目录树哈希相同（`00d481a8`）；比对用的临时索引已删除，它向共享对象库写入的未引用对象不影响任何分支 |
| 4 | 基线提交 `75524e8` | 原样记录整理结果，不含本会话的改动 |
| 5 | 引用扫描 | 16 份报告仍被引用，见“原文件保留的判定” |
| 6 | 第 1 次全套测试（`75524e8`） | 13 failed / 1407 passed / 35 skipped。2 项失败由删除报告引起；11 项失败是本次指定的 pytest 临时目录路径过长，git 报 `Filename too long`，与整理无关；另有 2 项因报告缺失被静默跳过。排查时在测试临时仓库里手动执行过一次 `git add -A`，同样因路径过长失败 |
| 7 | 按用户指令从 `e0acab4` 恢复 16 份原文件 | 逐个核对原字节 SHA-256 与登记一致；核对用的临时文件 `%TEMP%\restored_sha.txt` 已删除 |
| 8 | 第 2 次全套测试（恢复后，改用短临时目录） | 1422 passed / 33 skipped / 0 failed。33 项跳过：7 项因工作树内没有固定上游，1 项因没有本地 wheelhouse，1 项因 entityLifecycle 已开启，24 项因本解释器未安装 numpy/torch |
| 9 | 更新本文件总述：清理说明、登记表 16 行改为“原文件保留”，新增“原文件保留的判定”和本日志 | 附录原文未改；提交前复核 47 份附录哈希仍一致 |
| 10 | 第 3 次全套测试（本文件定稿后、提交前） | 1422 passed / 33 skipped / 0 failed，跳过原因同第 2 次 |
| 11 | 提交本轮改动 | 见 git 记录 |

测试产物建立与删除：

| 产物 | 位置 | 处理 |
| --- | --- | --- |
| 第 1 次测试的 pytest 临时目录（27 MB） | 会话临时目录 `pt-run1` | 已删除 |
| 第 2 次测试的 pytest 临时目录（44 MB） | `%TEMP%\lcr0926` | 已删除 |
| 第 3 次测试的 pytest 临时目录（45 MB）及输出日志 | `%TEMP%\lcr0926b`、会话临时目录 | 已删除 |
| 两次测试的输出日志、`pytest-of-user` 前后对照清单 | 会话临时目录 | 关键数字记入上表后删除 |
| 字节码缓存、`.pytest_cache` | — | 未产生（`-B`、`PYTHONDONTWRITEBYTECODE=1`、`-p no:cacheprovider`）；工作树 `git status --ignored` 为空 |
| 既有的 `%TEMP%\pytest-of-user` | — | 未使用，内容未变 |
| `%TEMP%\57966314-4ed7-42a6-a4b6-650c187b47f4.tmp`（0 字节） | 第 1 次测试期间出现 | 命名方式与本会话之前其他程序留下的临时文件相同，无法确认来源，未删除 |

会话临时目录（仓库外）中保留核验脚本 `verify_changelog.py`、`verify_head.py`、`refscan.py`、`closure.py` 和删除清单 `deleted.nul`，供后续复核，任务结束时删除。

### 2026-09-26 前端线：去除 OpenAI4S 前端入口、统一配色、自有笔记本

用户决定（同日提问、同日答复，均为推荐项）：笔记本由 Leo 自己重做；配色选方案 A「统一秋色」；PINN 先做产品闭环；环域写「根因未定」并停线（后两项属 PINN 线，见其章节）。
执行位置同上。本章只含前端线改动；PINN 线另立章节、另行提交。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 把候选分支 `codex/trusted-research`（`6d4ec0f`）合入工作分支 | 合并提交 `2dafa9b`，两侧文件不重叠、无冲突 |
| 2 | 合流后全套测试 | 1474 passed / 33 skipped / 0 failed；临时目录 `%TEMP%\lcr0926c`（46 MB）已删除 |
| 3 | 三个只读探索代理：前端入口与配色、产品科研流程、PINN 科学线状态 | 只读，无文件改动 |
| 4 | 配色小样以内联图示给用户选择 | 用户选方案 A |
| 5 | 读取上游 OpenAI4S 后端接口（只读）确定笔记本数据来源 | Leo 部署未开启上游 `OPENAI4S_NOTEBOOK_REPL`，笔记本本就是只读；Leo 版保持只读 |
| 6 | 本机网关 `leo_shell/workbench.py` 新增 `notebook`、`kernel`、`artifact_preview` 三个预定义操作，修正原有 `artifacts` 操作（上游返回数组，原网关只收对象，该操作此前不可用） | 只把白名单字段交给页面；单元输出超过 64 KB 截断；图片按文件头识别后以 data URI 返回；文本预览上限 256 KB；预览前核对该产物属于当前会话 |
| 7 | `leo_shell/api.py`、`leo_shell/ui.py`：移除 `open_computational_tools` 及其唯一使用的上游导航函数 `_load_backend_url`；新增 `open_model_settings`，回到启动页时展开设置抽屉 | 界面上不再有导航到上游页面的代码路径；注入层（`leo-inject.js`、`leo.css`）保留但不再被任何入口触达，是否删除待用户决定 |
| 8 | 重写 `stage/workbench.css`、`stage/workbench.html`、`stage/workbench.js` | 方案 A 配色（数值与 `shell.html` 淡墨浓秋一致）、暗色模式、另两套主题；首屏复用启动页淡墨树；四种可信度状态色与图例；新笔记本视图；工作台按已保存主题切换 |
| 9 | `leo_shell/theme_runtime.py`：工作台渲染时解析背景画占位符 | 渲染后约 0.22 MB，低于 1.5 MiB 预算 |
| 10 | `stage/shell.html`：「关于」中的 GitHub 链接（含中英文案）改为可复制的纯文本 | 启动页已无外链；署名与许可说明保留 |
| 11 | 测试：`tests/test_owned_workbench.py` 新增 17 项，`tests/test_workbench_runtime.py` 改 1 项、新增笔记本场景 1 项；离线夹具 `tests/fixtures/workbench-preview.js` 增加笔记本数据并移除旧接口 | 反向验证：临时改坏笔记本脚本使其请求未登记产物，新测试确实失败；随即恢复，文件哈希与改前一致 |
| 12 | `manifests/runtime-asset-origins.json` 更新 4 项哈希（`workbench.html/css/js`、`shell.html`），版本标记 `leo-palette-notebook-20260926` | `research-panel.js` 与注入包未改，哈希不变 |
| 13 | `docs/LEO_OWNED_WORKBENCH.md` 两处过时描述改为现状 | — |
| 14 | 全套测试 | 1493 passed / 33 skipped / 0 failed；工作台相关 42 项全部通过 |
| 15 | 提交前端线改动 | 见 git 记录 |

预览方式：用 `ThemeRuntime.render_workbench()` 渲染并内联离线夹具，写到会话临时目录的 `preview/`，由本机 `127.0.0.1:8791` 静态服务托管，在内置浏览器中检查首页、笔记本、预览、暗色、对话与科研面板。为此在工作树建立临时文件 `.claude/launch.json`（未提交）。

测试与预览产物：

| 产物 | 位置 | 处理 |
| --- | --- | --- |
| 两次全套测试的 pytest 临时目录（46 MB、45 MB） | `%TEMP%\lcr0926c`、`%TEMP%\lcr0926d` | 已删除 |
| 测试日志、预览 HTML、渲染脚本 | 会话临时目录 | 保留到本任务结束后删除 |
| `.claude/launch.json` 与 8791 预览服务 | 工作树、仅本机 | 保留到本任务结束后删除并停止 |
| 字节码缓存、`.pytest_cache` | — | 未产生 |

未验证：以上均为源码、离线预览与自动测试；真实安装版的原生 WebView2 窗口尚未构建部署和实机验收，笔记本对真实会话的读取尚未在真实后端上检查。

### 2026-09-26 PINN 线（一）：环域 r1 写「根因未定」并停线

依据：用户同日选择「写『根因未定』停线」；宪法第 3.1 章、3.2 条第 3 项（两个原因争同一症状时记 rUndetermined 并停线）、第 58 章（负结果是合法终点）。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 只读核对环域 r1 的失败记录、排除实验汇总 `EXCLUSIONS.json`、五个排除实验与嵌套预算诊断 | 宪法 1.2 下 sLocalizedError 共 7 个候选原因；已排除 rImplementationDefect、rSpecDefect；未排除 rSingularityTreatment、rReferenceDefect、rCapacityLimit、rOptimizationFailure、rSamplingDeficiency（此前说的「4 个未排除」是以命名 rOptimizationFailure 为前提的其余 4 个；从「根因未定」看，rOptimizationFailure 本身也未被证明必要，共 5 个） |
| 2 | 新增记录脚本 `experiments/annulus/record_stop_the_line.py` | 只从 FAILURE_RECORDED 出发、只能执行一次；记录先经 `validate_diagnosis_record` 与覆盖检查，状态由 `state_machine.diagnose` 判定 |
| 3 | 执行脚本 | 写入 `diagnosis_record.json`（`dg-exp-geometry1-annulus-poisson-r1-gpu-r1`，round 1，rUndetermined，无 Gate）与 `diagnosis_verdict.json`；状态日志追加 FAILURE_RECORDED → STOPPED_THE_LINE（`STOP:rUndetermined`）；`attempt_state.json` 改为 STOPPED_THE_LINE 并在来源清单中重登哈希 |
| 4 | 再次执行脚本 | 按设计拒绝（exit 1），无文件改动 |
| 5 | 核对来源清单 38 项 | 37 个文件哈希全部一致；`claim_set_ledger.json` 在清单中登记但文件不在运行目录，属原有情况（账本在 `experiments/annulus/ledger/`），本次未改 |
| 6 | 核对 Claim 账本 | 事件仍只有 SEALED、OPENED；文件 SHA-256 与排除实验结束时记录的 `740d5bbe…` 相同；DAC-M0 BURNT，DAC-M1/M2/M3 NEVER_SEALED |
| 7 | 新增测试 `tests/pinn/test_annulus_stop_the_line.py`（5 项） | 与既有环域测试共 30 项通过 |
| 8 | 提交本章改动 | 见 git 记录 |

记录中的写法：两个已排除原因保留为排除记录（校验器对 rUndetermined 不要求，但删去会丢失本轮确立的事实）；5 个未排除原因及理由写入 `diagnosis_verdict.json`。运行摘要 `RUN_SUMMARY.json` 仍记运行结束时的 FAILURE_RECORDED，属历史，未改。`ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md` 被新记录按哈希引用，故不追加说明。

仍待用户裁决：是否以修订 2 重新尝试、采用何种预算。另一分支 `claude/leo-ai-workbench-plan-6f38e9` 的 `STATUS.json` 记有「2026-09-20 用户裁定修订 2 用 240k、授权诊断专用实验」，科学记录中该项仍标为未决，本日询问时用户未确认；本次记录不依赖它，已写入 `unconfirmedRecords`。

### 2026-09-26 PINN 线（二）：产品内科研闭环的缺口

依据：用户同日选择「产品闭环优先」。目标是让候选版能由人确认后真正跑完主实验 → Tier-1 → 复现 → G6 → 导出；本章只改源码与测试，未构建、未部署、未运行任何训练。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 只读调查候选版科研流程（探索代理） | 只支持固定 1D Poisson；3 个真实任务均为 DRAFT，其中 2 个因模型把模板设置列为缺失而不支持；正式运行从未进行 |
| 2 | `leo_shell/research_draft.py`：新增 `TEMPLATE_METHOD` 并放入受支持草案的 `template.method`；提示词写明模板冻结设置不算缺失；新增 `normalize_equation` / `equation_matches_template`，只接受同一方程的等价写法 | 模型确认的哈希覆盖方法与验收规则；用户原写法保留 |
| 3 | `leo_shell/research.py`：新增 `fork` 操作；准备超时记事件 `PREPARATION_TIMED_OUT` 并写日志；抽出 `_refresh`，运行确认前先结清其他任务的过期运行状态 | 原任务、运行数据与预留 Claim 集不被改动；真在运行的任务仍阻止新运行 |
| 4 | `stage/research-panel.js`：显示方法与验收规则；准备失败与计算结束态提供「以此草案新建任务」；新错误码中文说明；验证页用可信度色标显示允许/阻断的结论与各维度状态；上游页返回按钮改用淡墨浓秋色 | 属科学代码身份内文件，故与前端线分开提交 |
| 5 | 测试：`tests/pinn/test_research_product.py` 新增 17 项（等价写法、不同方程、方法随确认、方法与冻结配置一致、提示词、fork 两项、超时、过期与存活运行各一项）；离线夹具的模拟草案加上方法 | 产品测试 54 项通过 |
| 6 | `manifests/runtime-asset-origins.json`：`research-panel.js` 与 `leo-inject.js` 包的哈希，版本标记 `leo-research-loop-20260926` | 先用 HEAD 各层复算出原记录的包哈希，确认打包规则后再更新 |
| 7 | `docs/TRUSTED_RESEARCH_V1.md` 追加「2026-09-26 补充」 | — |
| 8 | 全套测试 | 1515 passed / 33 skipped / 0 failed；临时目录 `%TEMP%\lcr0926e`、`%TEMP%\lcr0926f`（51 MB）已删除 |
| 9 | 离线预览中创建一个任务，核对「方法与验收规则」10 行完整显示 | 仅界面检查，夹具不产生审批或 Claim |
| 10 | 提交本章改动 | 见 git 记录 |

尚未完成：构建与部署到候选版（需用户同意）；在真实安装中由用户确认模型与运行包并完成正式运行；导出与独立复现包的实测；产品扩展到 2D Poisson。

### 2026-09-26 部署到科研候选版（前端线与 PINN 线合并部署）

用户同意：只部署「Leo AI 科研候选版」，正式版「Leo AI Studio」不动；允许启动候选版截图检查（随后屏幕操作授权弹窗被拒，未操作窗口）。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 停止 8791 预览服务，删除临时 `.claude/launch.json` 与空目录 `.claude/` | 工作树恢复干净 |
| 2 | 在工作树建立目录联接 `.venv` → 主检出 `.venv`（与 Codex 工作树相同做法） | 被 `.gitignore` 的 `.venv/` 忽略，git 状态保持干净 |
| 3 | 封闭构建 `tools/build_launcher.ps1 -AppRoot <候选版> -OutputRoot dist/claude-endpoint-1` | 成功；收据绑定 `53321b0`、dirty=False；包契约通过（326 个 `_launcher` 文件、35 个关键文件、34 个归档模块） |
| 4 | 确认无 Leo 进程后事务部署 `tools/deploy_release.ps1 -AppRoot <候选版>`；快捷方式参数指向会话临时目录中的一次性文件，避免改写桌面上正式版快捷方式 | 成功；回滚目录 `.leo-rollback-20260926-054145-b176c916`；EXE `f51574ca…`；`user/`、科研环境、任务与会话保留 |
| 5 | 候选版科学源码快照 `runtime/science-source`：从原 origin 取回分支 `claude/changelog-review-91e1c6`，新建同名本地分支并切到 `53321b0` | 工作区干净；原 `6d4ec0f` 仍在本地分支 `codex/trusted-research` 上，可切回 |
| 6 | 用两套科学环境运行 `pinn.research.worker environment`（只读） | 均可导入新代码；安装标识不同（`prefix-ad1926c3…` / `prefix-38daa655…`），依赖锁相同，CPU |
| 7 | `tools/build_manifest.py -o manifests/build-current.json`（git 忽略）与 `tools/verify_release.py --strict` | 12 PASS / 1 FAIL / 0 NOT TESTED；部署的包 `13974177…`、EXE、源文件、上游版本与洁净均 PASS |
| 8 | 查明 FAIL 项「skills deployed+daemon」：`sync_skills.py --check` | 候选版没有 `user/user-skills/` 目录（候选版与正式版共用 WSL 后台，WSL 副本与标准版一致），缺失的 9 个文件被计为不一致。部署前就存在，与本次改动无关；未擅自写入 `user/`，是否同步待用户决定 |
| 9 | 启动候选版，读取 `user/logs/leo-shell.log` | 05:43:44 启动：WebView2 固定运行时已加载，停在启动页等待进入，无错误。截图检查因授权弹窗被拒而未做，界面验收交用户 |
| 10 | 删除构建输出 `dist/claude-endpoint-1`（71.2 MB）与临时快捷方式 | 已删除；保留 `manifests/build-current.json`，没有它无法校验部署 |

回退方法：关闭候选版，从 `.leo-rollback-20260926-054145-b176c916` 恢复发布文件，并在 `runtime/science-source` 执行 `git checkout codex/trusted-research`（`6d4ec0f`）。不要覆盖 `user/`。

仍待用户：真实窗口中的界面验收；在科研任务中亲自确认模型与运行包，完成第一次正式运行。

### 2026-09-26 前端线（二）：同步候选版技能；删除上游注入层

用户决定（同日）：1. 同步技能；2. 删除注入层；3. 环域修订 2 用 240k（见 PINN 线章节）。

同步技能：

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | `tools/sync_skills.py --app-root <候选版>`（用户审批通过） | 新建候选版 `user/user-skills/`，写入 3 个技能共 9 个文件；WSL 副本本已一致，未改写；WSL 中 `lean-math/__pycache__/kernel.cpython-313.pyc` 为原有额外文件，按工具设计只报告不删除 |
| 2 | 临时切到 `53321b0`（部署对应提交）复跑 `verify_release.py --strict`，再切回分支 | 13 PASS / 0 FAIL / 0 NOT TESTED；工作树干净 |

删除上游注入层（用户审批通过）：

| # | 删除或改动 | 说明 |
| --- | --- | --- |
| 1 | 删除 `stage/leo-inject.js`（211 KB）、`stage/leo.css`（84 KB）、`stage/unified-settings-adapter.js`、`stage/i18n-brand-patch.js`、`stage/i18n/zh.json`、`stage/i18n/en.json` | 只在上游 OpenAI4S 页面上运行；该页面自前端线（一）起已无入口 |
| 2 | 删除 `tools/bundle_theme.py`、`tools/theme_preview.py` | 前者只用于拼装注入包，后者只用于在上游页面上预览注入样式 |
| 3 | `leo_shell/theme_runtime.py`：删除 `injection_script` 及只为它服务的字体、Logo、文案表解析 | 背景画解析保留（启动页与工作台使用） |
| 4 | `leo_shell/ui.py`：删除注入生命周期（`_inject_backend`、`refresh_injection`、`_on_loaded`、失败横幅、上游页状态字段） | 导航只加载 Leo 自有文档 |
| 5 | `leo_shell/api.py`：删除 `return_to_workbench` 与保存外观后的重新注入 | 只被注入层调用过的后端方法（实体隐藏/恢复/删除、本地技能扫描与导入、运行时状态）保留，目前没有界面调用 |
| 6 | `stage/research-panel.js`：只在工作台中安装，删除上游页分支与「返回 Leo 工作台」按钮 | 属科学代码身份内文件；`pinn/research/worker.py` 的身份清单同步删去 `stage/leo-inject.js` |
| 7 | `tools/build_launcher.ps1`、`tools/deploy_release.ps1`、`tools/build_manifest.py`、`tools/verify_release.py`、`tools/theme_asset_provenance.py`、`tools/headless_verify.py`、`tools/package_contract.py` | 构建不再拼装注入包；部署文件表去掉注入文件，并把旧安装中残留的 `theme/leo-inject.js`、`theme/leo.css`、`theme/i18n` 移入本次回滚目录（回滚可恢复）；发布清单与校验改为逐个核对 5 个 Leo 文档的源哈希与部署哈希，「deployed bundle」检查改为「deployed frontend」，发现已退役文件仍在安装中即失败 |
| 8 | `manifests/runtime-asset-origins.json`：删除 4 项（注入包、样式表、两份文案表）；`research-panel.js` 哈希更新，版本标记 `leo-injection-removed-20260926` | 其余 19 项的源文件均存在 |
| 9 | 测试：删除 `tests/test_theme_readability.py`（全部针对 `leo.css` 的颜色变量）；`tests/leo_shell/test_theme_runtime.py` 删除注入脚本的配置、字体、Logo 用例，背景画用例改到 `render_shell` 上保留；`tests/leo_shell/test_api.py` 三个重新注入用例合并为「保存外观不触碰窗口」；`tests/test_theme_settings_integration.py` 删去上游页面主题选择器用例，保留启动页用例；`tests/test_ui_api_contract.py` 删除功能开关与桥接表用例，改为「任何前端文件都不得调用未实现方法」并能识别工作台的 `native(...)` 调用，附反向验证；`tests/test_research_panel_runtime.py` 改为验证面板只在工作台中安装；`tests/test_owned_workbench.py` 新增「淡墨浓秋无冷色渐变」（原 `leo.css` 规则移植） | 全套 1407 passed / 32 skipped / 0 failed（此前 1515 / 33，减少的是只针对被删代码的用例） |
| 10 | `leo_shell/DESIGN.md`、`docs/THEME_INK_AUTUMN.md` 追加日期注记；`docs/BUILD.md` 工具表去掉 `theme_preview.py` | 历史段落保留 |

未删除、待用户决定：`stage/fonts/` 的 4 个字体文件（约 10 MB，含 `LICENSES/fonts/` 授权文本）目前没有任何文档使用，但仍随发布部署。

测试产物：pytest 临时目录 `%TEMP%\lcr0926g`、`lcr0926h`、`lcr0926i`（两次）、`lcr0926j`、`lcr0926k`（33 MB）均已删除；会话临时目录中的编辑脚本在任务结束时删除。

尚未构建部署：候选版仍是 `53321b0`。重新部署要关闭候选版，且不能在正式科研运行进行中移动安装内的科学源码。

### 2026-09-26 前端线（三）：消息的复制、赞踩与转发

用户同日提出：Leo AI 的回复可以复制或选择性复制，可以点赞和踩，可以转发；提示词（提问）也可以转发。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 只读查看上游会话反馈接口 | `POST/GET /frames/{id}/feedback`，以键记录 up/down，空值即清除；赞踩随会话保存 |
| 2 | `leo_shell/workbench.py` 新增预定义操作 `feedback`、`set_feedback` | 键只允许字母数字及 `_.:-`（≤128），评价只允许 up/down/清除；返回只保留合法评价 |
| 3 | 新增 `leo_shell/clipboard.py` 与 `ShellApi.copy_text` | 只写不读的 Win32 剪贴板兜底（纯文本、≤1M 字符、忙时短暂重试、失败释放内存）；页面先用浏览器剪贴板接口，再用 `execCommand`，都不行才用它；`tools/package_contract.py` 把该模块列为必需 |
| 4 | `stage/workbench.js/html/css`：每条消息下的操作栏；转发对话框 | 复制：若在该条消息内选中了文字只复制所选，否则复制显示出的纯文本（去掉加粗与标题标记、代码围栏行）；赞/踩只用于回复，再点一次取消；转发：选择新对话或其他对话，内容放进目标对话输入框并提示核对，从不自动发送；另有「复制为分享文本」（带来源与「由 AI 生成，重要结论请核对证据」） |
| 5 | 离线预览中实测 | 选中 10 个字复制只得这 10 个字；整条复制正确；赞被记为 `m-2: up`；转发到另一对话后输入框内是带引用标记的回复，未发送 |
| 6 | 测试：`tests/test_owned_workbench.py` 新增 5 项（反馈路由与返回、剪贴板写入、忙/失败/超长、`copy_text` 入参）；`tests/test_workbench_runtime.py` 新增 1 个 Node 场景（评价回显与取消、三种复制、转发不发送、不列出来源对话） | 全套 1413 passed / 32 skipped / 0 failed |
| 7 | `manifests/runtime-asset-origins.json`：`workbench.html/css/js` 哈希，版本标记 `leo-message-actions-20260926`；离线夹具增加反馈与剪贴板模拟 | — |

测试产物：临时目录 `%TEMP%\lcr0926l`（32 MB）已删除；临时预览配置 `.claude/launch.json` 在本轮再次建立并已删除，8791 预览服务已停止。尚未构建部署。

### 2026-09-26 前端线（四）：删除未使用的字体；用户对修订 2 的三项决定

用户同日决定：现在部署到候选版；环域修订 2 换新种子；修订 2 保持 specHash 不变；删除字体。后三项中的前两项属 PINN 线，记在此处以便对照，执行见 PINN 线章节。

| # | 删除或改动（用户审批通过） | 说明 |
| --- | --- | --- |
| 1 | 删除 `stage/fonts/`（Inter、JetBrains Mono、Noto Sans SC、Space Grotesk 四个 WOFF2 与 `manifest.json`）、`LICENSES/fonts/`（四份 OFL 授权文本；仓库 `LICENSES/` 随之为空）、`tools/build_fonts.py`（字体重建工具） | 共约 8 MB；只被已删除的注入样式表使用；可从 git 历史恢复 |
| 2 | `tools/build_launcher.ps1`、`tools/deploy_release.ps1`：不再打包、部署字体与授权；部署时把旧安装中的 `theme\fonts`、`LICENSES\fonts` 与注入层文件一样移入回滚目录 | — |
| 3 | `tools/build_manifest.py`、`tools/theme_asset_provenance.py`、`tools/verify_release.py`（安装中仍有字体即判为过时部署）、`manifests/runtime-asset-origins.json`（删去 5 项，余 14 项）、`docs/BUILD.md`、`docs/THEME_INK_AUTUMN.md` 注记 | — |
| 4 | 全套测试 | 1413 passed / 32 skipped / 0 failed；临时目录 `%TEMP%\lcr0926m`（33 MB）已删除 |

### 2026-09-26 第二次部署到科研候选版（`8f17779`）

用户同意现在部署，并让我代为关闭候选版。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 部署前检查 | 候选版进程 35532 在运行（此前由我启动）；3 个科研任务均为 DRAFT；没有科研计算进程 |
| 2 | 封闭构建到 `dist/claude-endpoint-2` | 收据绑定 `8f17779`、dirty=False；包契约通过（326 个 `_launcher` 文件、35 个关键文件、35 个归档模块，含新增 `leo_shell.clipboard`）；包内主题目录只剩 Leo 自有文档、背景画、Logo 与 `themes.json` |
| 3 | 按用户要求关闭候选版：先发窗口关闭请求 | 进程正常退出，日志记录后台已停止（`physical daemon stop completed`），未强制结束 |
| 4 | 事务部署（快捷方式参数指向会话临时目录中的一次性文件） | 成功；回滚目录 `.leo-rollback-20260926-070359-9875e2c3`；EXE `a1ae560c…`；旧安装中的 `theme\leo-inject.js`、`theme\leo.css`、`theme\i18n`、`theme\fonts`、`LICENSES\fonts` 已移入该回滚目录（逐项核对存在） |
| 5 | 科学源码快照快进到 `8f17779` | 工作区干净；两套科学环境均可运行新代码（安装标识不变） |
| 6 | `build_manifest.py -o manifests/build-current.json`、`verify_release.py --strict` | 13 PASS / 0 FAIL / 0 NOT TESTED；新检查「deployed frontend」：5 个 Leo 文档与源文件一致 |
| 7 | `theme_asset_provenance.py --strict` | 14/14 主题资产可追溯到已提交源，0 未登记、0 漂移 |
| 8 | 重新启动候选版 | 进程 24092；日志显示 WebView2 固定运行时已加载，停在启动页等待进入 |
| 9 | 删除构建输出 `dist/claude-endpoint-2`（64 MB）与临时快捷方式 | 已删除（第一次删除命令因工具安全检查被整体拦截、未执行，改用明确路径后完成） |

回退方法：关闭候选版，从 `.leo-rollback-20260926-070359-9875e2c3` 恢复（其中也保存了被退役的注入层与字体文件），科学源码回到 `53321b0`。

对科研任务的影响：科学代码身份已变化（`research-panel.js` 与身份清单改动），部署前准备好的运行计划会失效；当时 3 个任务均为草稿，未受影响。

### 2026-09-26 PINN 线（三）：环域修订 2 的准备与启动

用户决定（同日）：修订 2 用 240k 步、换新种子、保持 specHash 不变；用 CPU 满负荷并行，主实验 → Tier-1 → 独立复现（G6）一次跑完，中途不再确认。预注册 `experiments/annulus/EXPERIMENT_ANNULUS_R2_PREREGISTRATION_20260926.md` 与代码同一提交冻结。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 新增 `pinn/experiments_annulus/parallel_annulus.py`：每个种子在独立进程里用与顺序执行完全相同的参数训练（spawn，仅 CPU） | torch 解释器下测试：并行与顺序结果逐位相同、顺序保持；GPU 共享被拒绝 |
| 2 | 运行器 `runner_annulus.py` 增加执行参数 `--workers`（写入 identity.json 的 `executionParallelism`，不进配置、不影响 codeHash）；Tier-1 的 8 次扰动重训改为并行 | 行为不变，顺序模式 `workers=1` 与原来相同 |
| 3 | 新增 `closure_annulus.py`：Tier-1 合并（只降不升）、C_repro 判定、G6 应用（只有 PASS 且 C2 已签署才 ACCEPTED，否则停在 REPRODUCIBILITY_CHECK 并写明原因）；规则照搬 2D，不导入 2D 代码 | 状态机约束有测试 |
| 4 | 新配置 `configs/exp_annulus_r2_240k.json`：只改 steps=240000、lrPrefixSteps=120000、种子基数 20263200/20263300/20263400、驱动脚本 | 测试核对「只有这些不同」、种子与 r1 及复现种子全部不相交 |
| 5 | 新 ProblemDefinition `problems/pdef-annulus-poisson-v1-r2.json`：revision 2、claim 改为 DAC-M1 | specHash 与 r1 相同（`4c8dfbc7…`）。specHash 包含 frozenAt，所以沿用 r1 的冻结时间（含义：规格就是 r1 冻结的那一份），已写入预注册 |
| 6 | 驱动 `run_formal_annulus_r2.py`（属代码身份）：防睡眠、主实验、Gate 5 通过才跑 Tier-1、Env B 复现（路径由参数传入，不写进仓库）、判定并应用 G6、链条报告 `runs/<attempt>-CHAIN_REPORT.json` | 本机路径不出现在仓库文件（有测试） |
| 7 | 两个旧测试原先断言台账只有 r1 的两条事件；改为断言这两条是不变前缀（事件 ID `7152b353…`、`df1b1c50…`，以及按原格式序列化后与排除实验防火墙记录的哈希相同），后续只能是修订 2 的其他成员事件 | 通过 |
| 8 | torch 验证记录 `TEST_VERIFICATION_UNDER_TORCH.json` 重新生成（加入并行测试） | 29 通过 / 0 失败 |
| 9 | 全量测试（治理解释器） | 1420 通过 / 33 跳过（提交前 PRELOCK 因新文件未跟踪而失败，暂存后通过；正式运行也要求已提交） |

运行结果、Tier-1 与 G6 结论在运行结束后追加到本章节。

**运行记录（2026-09-26，续）**

| # | 事件 | 结果 |
| --- | --- | --- |
| 10 | 主实验 `exp-geometry1-annulus-poisson-r2`（进程 11464，10 进程并行，15:32Z–18:42Z） | Gate 1–3 PASS；**Gate 4 PASS**：10/10 在 ε_spec 内，dev 相对 L2 中位数 1.406e-4（各种子 9.95e-5 至 1.81e-4），单种子约 3.1 小时；**Gate 5 PASS**：C_physics PASS，C_external PASS（DAC-M1，ACA-1…ACA-9 全部满足）；DAC-M1 已 OPENED → BURNT；状态进入 REPRODUCIBILITY_CHECK |
| 11 | 链条在 `AttemptAnnulus.finish()` 崩溃 | `claim_gate()` 被传入不存在的参数 `environment_id`、`qualified_c2_runs`，返回值又被当成字典。这条路径 r1 从未走到（r1 停在 Gate 4）。`trust_vector.json` 已写出；`claim_gate_decision.json`、`RUN_SUMMARY.json` 未写出。本轮新写的 `closure_annulus.py` 也照抄了同样的错误调用。测量结果没有丢失 |
| 12 | 启动 Env B 独立复现（进程 46576，`--stop-after-gate 4`，10 进程并行） | 不经过出错的代码。codeHash `b9f9e6def344` 与主实验相同，环境 `48e795c8…` 与主实验 `2b081306…` 不同；Gate 1–3 PASS，正在训练 |
| 13 | 编写补全脚本 `experiments/annulus/complete_r2_finish_after_crash.py`（提交 `501ace5`、`7826e16`；放在代码身份边界之外，以免改动 `pinn/` 导致复现与 Tier-1 的 codeHash 变化） | 用未改动的治理函数 `claim_gate` 按 2D 的 schema 1.2 生成决定。第一次运行：校验器因磁盘上的信任向量是 1.2 之前的旧布局而提前返回（第二个潜伏缺陷：环域运行器仍写旧布局）。第二次运行改为对「1.2 布局视图」做完整校验，查出**实质问题**：冻结规格登记了 `PH10-momentumBudget` 与 `PH11-freeEnergy`（均为 NOT_APPLICABLE，附理由），但环域 Gate 5a 没有记录这两项（2D 代码会写出），按宪法属于「登记的检查被静默省略」。脚本因此拒绝写出决定和摘要：`claim_gate_decision.json`、`RUN_SUMMARY.json`、状态记录均未写出。**但**脚本在校验之前已写出 `claim_statements.json`（768 字节，只含 C0–C3 的陈述文本），并登记进该尝试的 `PROVENANCE_MANIFEST.json`（两次运行，第二次覆盖第一次）。这是脚本的顺序缺陷：应先校验、后写入。该文件原样保留，交所有者一并决定 |
| 14 | 暂停 | Tier-1 需要 `RUN_SUMMARY.json`，而如何补全这份被省略的记录需要所有者决定，已向用户提问。复现继续运行（各方案都需要它） |

### 2026-09-26 开场动画（前端线）

用户要求：每次打开 Leo 先播放一段 15 秒开场视频，点击屏幕、按空格等可以跳过；视频由 Seedance 2.5 模型生成，视频画面上不加水印，但必须在设置里注明，并和 OpenAI4S 的网址放在一起。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 检查用户提供的 `AI agent开场动画设计需求 (1).mp4` | H.264 High + AAC 立体声，1280×720，24 fps，15.05 秒，21,459,964 字节，SHA-256 `f21a8472…`；索引（moov）在文件末尾 |
| 2 | 无损重封装到 `stage/intro/leo-intro.mp4`（`ffmpeg -c copy -movflags +faststart`） | 视频流、音频流 MD5 与原文件完全相同（`795462f4…`、`7d03c9b7…`），只把索引移到文件开头；SHA-256 `d39f3b6a…`。原文件未改动、未删除 |
| 3 | 实测加载方式（一次性探针，真实 WebView2 窗口） | 起始页是内存文档（`about:blank`，1.5 MB 上限），视频不能内联。WebView2 虚拟主机映射**只对映射之后才加载的文档生效**：先加载页面、后建映射时，图片和视频都无法访问（错误码 4）；先建映射、再加载内存页面时，视频正常播放 |
| 4 | 新增 `leo_shell/intro.py`；`ui.py` 在启动时先显示一个与窗口同色的空白页，把只含视频的 `intro/` 文件夹映射到保留域名 `intro.leo-studio.example`（`DenyCors`：video 元素可读，脚本跨源读取被拒），再加载起始页 | 不开端口，不联网，安装目录里的其他文件都不可访问；映射失败或 6 秒内没有收到加载事件时，直接显示起始页，不播放动画 |
| 5 | `stage/shell.html`：全屏开场层 | 点击或按任意键跳过（捕获阶段拦截，不会误触下面的按钮），播完自动进入；有声自动播放被拦截时改为静音播放；出错、6 秒内未开始播放、或超过 25 秒时一律结束；画面完整显示（contain），四周用同一视频的模糊放大版填充（最后一帧的文字靠近左边，裁切会切掉它）；打开设置也会结束动画 |
| 6 | 只在**启动时**播放一次 | 从工作台回到起始页不重放；`--settings` 启动不播放 |
| 7 | 设置 → 关于：在 OpenAI4S 网址后加「开场动画由 Seedance 2.5 模型生成。」（中英文两份）；工作台设置的「关于」同样加注 | 视频画面上不加任何文字 |
| 8 | 打包链：`build_launcher.ps1`、`deploy_release.ps1`（`intro` 为必需目录）、`build_manifest.py`、`theme_asset_provenance.py`、`package_contract.py`；`runtime-asset-origins.json` 登记来源（Seedance 2.5、原文件哈希、无损重封装、未加水印）；`.gitattributes` 增加 `*.mp4 binary` | |
| 9 | 测试 `tests/leo_shell/test_intro.py`（11 项），全量测试 | 1431 通过 / 33 跳过 |
| 10 | 端到端实测（一次性探针：真实 `DesktopUI` + `ThemeRuntime` + `stage/shell.html`） | 启动约 2.9 秒后开始播放，**有声**，1280 像素宽；按空格 0.8 秒后开场层移除；「关于」里显示 Seedance 注明 |
| 11 | 清理测试产物 | 端到端探针把 `stage/` 当主题目录，窗口图标代码因此生成了 `stage/logos/leo-lion.2c2bb981ec6e98a9.ico`（163,288 字节，从未被 git 跟踪），已删除；会话临时目录中 4 个探针目录（各含一份 21 MB 视频副本，共约 88 MB）、帧拼图和探针结果已删除 |
| 12 | 部署到科研候选版（`6db2532`）。实验正在本工作区写数据，工作区因此不干净，封闭构建会拒绝；改为在会话临时目录新建一个干净的 git 工作树（detached `6db2532`，`.venv` 用目录联接指向本工作区） | 构建通过：收据绑定 `6db2532`、dirty=False；包契约 326 个 `_launcher` 文件、36 个关键文件（比原来多出视频）、35 个归档模块；包内视频 SHA-256 `d39f3b6a…` |
| 13 | 事务部署（候选版未在运行；快捷方式参数指向临时文件，桌面快捷方式未改） | 成功；回滚目录 `.leo-rollback-20260926-120002-d8c3ef5b`；EXE `384e054a…` |
| 14 | 科学源码快照 `8f17779` → `6db2532`（快进） | 工作区干净 |
| 15 | `build_manifest.py`、`verify_release.py --strict`、`theme_asset_provenance.py --strict` | 13 PASS / 0 FAIL / 0 NOT TESTED；主题资产 15/15 可追溯（含 `intro/leo-intro.mp4`），0 漂移 |
| 16 | 重新启动候选版（进程 29576） | 日志：固定运行时 152.0.4191.53 已加载，没有「opening animation unavailable」或「boot page did not report loaded」警告，说明映射成功；播放画面本身无法从日志确认 |
| 17 | 清理构建产物：先单独删除 `.venv` 目录联接（核对真实 `.venv` 仍在），再 `git worktree remove`；删除构建输出（85 MB）与临时快捷方式 | 已删除 |

回退方法：关闭候选版，从 `.leo-rollback-20260926-120002-d8c3ef5b` 恢复，科学源码退回 `8f17779`。

### 2026-09-26 PINN 线（四）：r2 作废（方案 B），修代码，第 3 版准备与启动

用户选择 **B**：认定 r2 的记录无效，不下结论；修代码后，用第 3 版（DAC-M2）按原方法重做。补全脚本误写的 `claim_statements.json` 用户未表态，按我的建议保留。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 停止 r2 的 Env B 复现（主进程 46576 及其 12 个子进程，其中 11 个 python、1 个 conhost）：按 B，它已无用处，还会与 r3 争用 CPU | 已停止；输出目录保留，写入 `INTERRUPTED.json`（未判定）。机器上另有 3 个 python 进程不属于本工作（hermes agent 2 个；`gate5_pilot` 经 WSL 运行 1 个），未触碰 |
| 2 | `experiments/annulus/record_r2_void.py`（提交 `7ceff59`）写入 `owner_ruling_void.json`，并在状态日志追加一条同状态记录「OWNER_RULING:VOID_NO_CLAIM」 | 状态文件保持 REPRODUCIBILITY_CHECK（状态机没有「作废」，新增状态属于修宪）；r2 永远不写判定，不跑 Tier-1 和 G6；测量产物一字未改；脚本拒绝重复运行 |
| 3 | 代码修正（`7ceff59`）：Gate 5a 记录 PH10、PH11 两项「不适用」；信任向量改为 1.2 布局并先校验；判定改为 1.2，由唯一的 `build_decision` 构造，先校验后写入；**打开盲测集前的预检**；收尾模块改用同一构造 | 新增测试：逐项核对「登记的每项检查都有输出」；预检位于 OPENED 之前；判定先构造后写入 |
| 4 | 第 3 版配置、ProblemDefinition 与驱动 | 方法与 r2 相同；种子基数 20263500/600/700；DAC-M2；specHash `4c8dfbc7…` 不变；驱动在 Gate 5 通过后**同时**运行 Tier-1 和 Env B 复现 |
| 5 | **沙盒全链冒烟**：在临时 git 工作树中用正式驱动加小配置运行（10 个种子、300 步；真实 Env B 子进程；Gate 5 的 APPLICABLE 检查在进程内强制判 PASS），真实实验目录不受影响 | 第 1 次：我的包装脚本缺主模块保护（沙盒自身的问题）。第 2 次：3 个种子不满足 N ≥ 10，Gate 4 BLOCKED（按宪法，正确）。第 3 次：预检通过、判定写出、Tier-1 跑完，**合并时崩溃**：判定 ID 后缀含下划线（schema 只允许 `[a-z0-9-]`），修正于 `63109f9`；同时发现复现尝试 ID 含大写 `B`，run record 会在复现训练结束**后**因 runId 不合规崩溃（r2 的复现也是这个名字，只因提前停止才没暴露），修正于 `984e6d4`。第 4 次：全链走通，Tier-1 降级 → G6 PASS 但保留在 REPRODUCIBILITY_CHECK 并写明原因。第 5 次（额外强制 Tier-1 为 PASS）：进入 ACCEPTED，允许 C0–C2。沙盒工作树（115 MB）已删除 |
| 6 | 全量测试；torch 解释器下的测试 | 1437 通过 / 33 跳过；29 通过 / 0 失败 |
| 7 | 预注册 `EXPERIMENT_ANNULUS_R3_PREREGISTRATION_20260926.md`；提交 r2 的运行数据（尝试目录、中断的复现、控制台日志、链条报告）与台账（DAC-M1 SEALED/OPENED） | 与本章同一提交 |
| 8 | 启动第 3 版（进程 33844，19:21Z） | codeHash `e9fdf023677e`；DAC-M2 SEALED |
| 9 | 主尝试（19:23Z–21:34Z，约 2.2 小时） | Gate 1–3 PASS；**Gate 4 PASS** 10/10，dev 相对 L2 中位数 1.555e-4，最差 2.77e-4；**预检通过**（在打开前）；DAC-M2 OPENED → BURNT；**Gate 5 PASS**（C_physics、C_external）。ACA-1…ACA-9 每个种子都满足；余量最小的是 ACA-9：最差种子 7.631e-4，阈值 1e-3，余量 1.31 倍（r1 失败的正是这一项，余量依然偏薄）；ACA-1 余量 3.56 倍 |
| 10 | Tier-1（8 次扰动）与 Env B 复现同时运行（21:34Z–01:43Z） | Tier-1 全部维持 PASS（最大 Δq 2.23e-4，低于 1% 的维持线）；复现 Gate 4 PASS |
| 11 | G6 | 环境独立（`dependencyLockHash`、`installationId` 不同）；specHash、codeHash 相同；种子集不同；中位数 A 1.555e-4 vs B 1.741e-4，差 1.863e-5（绝对限 1e-4，相对限 7.774e-5）；k/N 判定一致 → **C_repro PASS** |
| 12 | 最终状态 | **ACCEPTED**，允许声明 **C0、C1、C2**（C3 需要 ≥ 5 次独立合格运行，未申请）。三份信任向量与三份判定事后逐一独立重新校验，均无错误；收尾时的 codeHash 与尝试时相同（`e9fdf023…`），中途没有改过代码 |
| 13 | 提交第 3 版运行数据（尝试目录、复现目录、控制台日志、链条报告）与台账（DAC-M2 SEALED/OPENED） | 与本行同一提交 |
| 14 | 全量测试 | 1433 通过 / **4 失败** / 33 跳过。失败原因是我的疏忽：提交 `a263edb` 收入了 r2 的崩溃日志 `exp-geometry1-annulus-poisson-r2-console.err.log`，其中的 traceback 含本机路径，触发可移植性检查（4 个测试）。那次提交前我只跑了 CHANGELOG 测试，没有跑全量。`.log` 不在可登记为「不可变历史证据」的类型（仅 `.md`/`.json`）之内，处理办法（从仓库移除该日志）涉及删除已提交的证据文件，已请用户审批。第 3 版的全部文件已检查，不含本机路径 |
| 15 | 从仓库移除 `experiments/annulus/runs/exp-geometry1-annulus-poisson-r2-console.err.log`（1,186 字节，SHA-256 `b92bfe48…`）（**用户审批通过**） | 已 `git rm`；原文保存在 git 历史 `a263edb` 中（提交时 CRLF 被规范为 LF，按 CRLF 还原后哈希与删除前一致）；报错内容另记于 `exp-geometry1-annulus-poisson-r2-CHAIN_REPORT.json` 与本 CHANGELOG。全量测试 1437 通过 / 0 失败 / 33 跳过 |

**结论**：环形 Poisson（几何提升 1）在第 3 版达到 C2，1D、2D 之后第三个完成可信闭环的问题。
- 适用范围：只限这个冻结规格，以及 DAC-M2 这一个盲测成员。
- 余量：ACA-9 只有 1.31 倍；
- 根因：r1 的根因仍未定，本结果不能倒推 r1 失败的原因；
- 数据：r2 的数字不计入。

### 2026-09-27 合并到 Leo AI 2.1 → 2.1.1

背景：用户让 Astra 从 `master` 发布了 Leo AI 2.1（`900c4b2`，标签 `v2.1.0`），并原位升级了候选版安装目录；随后用户说明「改错了版本」，要求把本分支的修改提交到 2.1 之上。2.1 并入的「科研候选版」是更早的 codex/trusted-research 版本（仍带已退役的 `stage/leo.css` 注入层），本分支 23 个提交全都不在其中。

用户决定（同日）：版本号 **2.1.1**；先在新分支合并验证，再快进 `master`；验证通过就部署，并替用户关闭正在运行的应用。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 预演合并（`git merge-tree`，不改动任何工作区） | 3 个文件有文本冲突：`CHANGELOG.md`、`manifests/runtime-asset-origins.json`、`stage/workbench.html` |
| 2 | 从 `master` 新建分支 `claude/leo-2.1.1` 与工作树 `.claude/worktrees/leo-2-1-1`（`.venv` 目录联接到主仓库环境），合并 `claude/changelog-review-91e1c6` | |
| 3 | `stage/workbench.html`：采用本分支内容（含转发对话框与 Seedance 注明），「关于」标题改为 2.1 的「关于 Leo AI 2.1」；保留「（MIT License）」（2.1 删去了它，但没有测试或规则依赖；许可署名是准确信息，起始页的「关于」也保留了它） | |
| 4 | `runtime-asset-origins.json`：`workbench.html` 条目写入合并后的真实哈希，版本记为「Leo AI 2.1.1」；逐项核对全部 15 个条目与 `stage/` 文件 | 其余 14 项一致，没有缺失或未登记文件。2.1 所说的「23 项」包含已退役的注入层与字体，合并后随本分支一起移除 |
| 5 | `CHANGELOG.md` 7 处冲突：摘要表、清理说明、报告清单、「原文件保留的判定」及各章操作记录采用本分支内容；附录中 Astra 新增的 `archive-p0-…` 锚点采用 2.1 内容 | 附录 47 份归档报告，标题各只出现一次 |
| 6 | **恢复 16 份原位报告原文件**：2.1 删除了全部 43 份报告，改由 `tools/report_archive.read_report` 从本文件附录读取；git 合并默认沿用了这次删除 | 这 16 份仍被治理文件、代码身份文件、预注册引用（用户此前要求保留不可随便删除的文件）。`read_report` 优先读取磁盘文件，因此与 2.1 的归档机制兼容 |
| 7 | 版本号 2.1.0 → **2.1.1**（唯一来源 `leo_shell/__init__.py`，外加 README 一行）；显示名仍为「Leo AI 2.1」 | |
| 8 | 全量测试（治理环境）；torch 解释器下的环形与 2D 测试 | 1446 通过 / 0 失败 / 33 跳过；29/0、23/0。2.1 记录的 1491/25 来自装有更多数值库的构建环境，两组数字不可直接比较 |
| 9 | 发布提交 `4d9300f`（合并提交，父提交为 `900c4b2` 与 `a7ffc9d`）；构建输出到 `Documents\LeoAIStudio-deliveries\2.1.1\build-r1`（沿用 2.1 的交付目录约定，保留） | 收据绑定 `4d9300f`，dirty=False；包契约 326 个 `_launcher` 文件、36 个关键文件、35 个归档模块；EXE 版本元数据为 2.1.1 |
| 10 | 部署（部署时应用未在运行；快捷方式参数指向临时文件，桌面「Leo AI 2.1.lnk」未改） | 成功；回滚目录 `.leo-rollback-20260927-013338-c1c1248d`（其中 `theme` 下保存了 2.1.0 的注入层、字体、`i18n`）；EXE `a4c307d0…` |
| 11 | 科学源码快照：按 2.1 的约定新建 `runtime/science-source-2.1.1-4d9300f`（从本仓库克隆，干净）；`research-runtime.json` 的 `codeRoot` 改指向它，旧文件先备份到回滚目录 `upgrade-state-backup/runtime/` | 2.1.0 快照保留 |
| 12 | 首次严格校验：3 项失败，因为 2.1 的离线依赖包 `wheelhouse/`、`wheelhouse-science/` 被 git 忽略，只存在于主仓库目录。用目录联接接入工作树（只读使用，与 `.venv` 相同）后重跑 | 16 PASS / 1 FAIL：技能 12 个文件与仓库规范版不一致 |
| 13 | 技能差异核查（只读） | 内容逐字节相同，**只有换行符不同**：安装副本是 CRLF；仓库按 `.gitattributes` 规定 `eol=lf`，已提交内容和新工作树都是 LF。主仓库目录的工作副本是过期检出（5 个 CRLF、1 个 CRLF/LF 混合），2.1 从那里同步，所以当时校验通过。仓库里的技能内容在 2.1.0 与 2.1.1 之间没有变化 |
| 14 | 备份后同步技能：Windows 副本复制到回滚目录 `upgrade-state-backup/user-skills-windows/`，WSL 守护进程副本打包为 `wsl-user-skills-2.1.0.tar.gz`（10 项）；随后 `sync_skills.py --require-wsl` | Windows 6 个、WSL 6 个文件已同步；三处副本一致 |
| 15 | 复验 | **严格发布校验 17/17**；主题资产 15/15；科学环境检查无问题；科学环境（`science-a`）PINN 回归 **952 通过 / 0 跳过**（2.1.0 为 916，多出的是本分支的环形测试） |
| 16 | 重新启动（进程 35576） | 窗口标题「Leo AI 2.1」；固定运行时已加载；日志没有开场动画警告 |
| 17 | 本地标签 `v2.1.1` → `4d9300f`；安装根目录写入 `RELEASE_2_1_1_RECEIPT.json`（2.1.0 的回执保留） | 以上校验都在 `4d9300f` 上完成。本行所在的日志提交之后 HEAD 会前移；以后如需复跑发布校验，请先检出 `v2.1.1` |
| 18 | 未做 | 没有发送模型消息，没有提交科研任务，没有推送到任何远端；这次没有像 2.1.0 那样对 `user/` 做完整的前后摘要比对，只改动了上面 6 个技能文件（已备份） |
| 19 | 修正上一条日志提交 `e1e33b6`：heredoc 把路径中的 `\2`、`\b` 变成了控制字符 `\x02`、`\x08`，防护测试 `test_changelog_holds_no_stray_control_characters` 报错。**我的命令链没有在测试失败时停下，带着失败提交了**；改用 Write 工具写修正脚本 | 全量测试 1447 通过 / 0 失败 / 32 跳过 |

### 2026-09-27 唯一指定正版；主仓库技能换行符整理

**所有者声明（2026-09-27）：Leo AI 2.1.1 是唯一指定正版。**

| 项 | 内容 |
| --- | --- |
| 源码 | `C:\Users\user\Desktop\LeoAIStudio-build` 的 `master`（快进自 `claude/leo-2.1.1`）；发布提交 `4d9300f`，本地标签 `v2.1.1` |
| 安装 | `C:\Users\user\Desktop\LeoAI-Research-Candidate-20260926`，桌面入口「Leo AI 2.1」，回执 `RELEASE_2_1_1_RECEIPT.json` |
| 不再作为正版的 | Leo AI 2.1.0（`900c4b2`，Astra 从旧候选线发布）；codex/trusted-research 线及其旧候选版；其余工作树与分支上的并行版本。它们作为历史保留，不删除；以后的开发都从 `master` 开始 |

主仓库 `skills/` 换行符整理（用户同意）：

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 检查：9 个技能文件中 5 个为 CRLF、1 个为 CRLF/LF 混合，都是过期的工作副本（仓库规定 `eol=lf`，已提交内容为 LF）；`git status` 显示干净，与已提交内容没有差异 | |
| 2 | `git checkout-index -f` | 没有改写任何文件（无效，已记录） |
| 3 | 先在一个文件上试验：删除后 `git checkout` 重新检出 | 变为 LF，`git status` 仍然干净 |
| 4 | 其余 5 个文件：先备份到系统临时目录，再删除并重新检出 | 9 个文件全部为 LF；与备份逐个比对，除换行符外字节完全相同；从主仓库执行 `sync_skills.py --check --require-wsl`，三处副本一致 |
| 5 | 删除临时备份 | 已删除 |
| 6 | 仓库里其余 CRLF 文件（3 个 `.ps1`、2 个清单/锁文件、1 个 `requirements.lock`、2 份历史实验日志） | 符合各自的 git 规则（`.ps1` 规定为 CRLF，其余是 `text=auto`）或属于历史证据，没有改动 |

### 2026-09-27 Leo AI 2.1.2（进行中）：新图标替换狮子头

用户决定：下一版 2.1.2，主要是前端修改；第一项是把狮子头换成用户提供的「Leo」手写体图标。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 在本会话工作树切到新分支 `claude/leo-2.1.2`（从 `master` `d813e1c` 起）；版本号改为 2.1.2（`leo_shell/__init__.py`、README）；`wheelhouse`、`wheelhouse-science` 以目录联接接入 | 先在另一个工作树建过 `leo-2-1-2`，写入时被会话钩子拦下（本会话只能写自己的工作树）；已先单独拆掉其中的目录联接（核对主仓库 `.venv` 完好），再移除该工作树，里面只有未提交的版本号改动和图片副本 |
| 2 | 原图存为 `assets/logos/leo-script.original.webp`（1254×1254，SHA-256 `2b47a470…`） | 奶白圆角方块，四角为纯黑 (0,0,0)，没有透明通道 |
| 3 | 新增 `tools/make_logo_master.py`，生成透明母版 `assets/logos/leo-script.source.png` | 第一版用几何圆角矩形遮罩，圆角外沿留下黑边（该图的圆角是连续曲率的「超椭圆」，不是圆弧）；改为从四角做洪水填充取背景、向内收 2 px、超采样柔化，边缘一带最暗像素亮度 235 |
| 4 | `tools/make_lion_icon.py` 改为默认使用新母版；SVG 标题改为「Leo AI」；网页用图内嵌分辨率从 128 提高到 256（起始页按 128 CSS 像素显示，150% 缩放时需要 192 设备像素） | 生成 1024 PNG、7 个尺寸的 ICO（16–256）、2 个 SVG；文件名仍为 `leo-lion.*`（构建、部署、任务栏缓存和来源校验共用这些路径，改名另作一项） |
| 5 | 新测试 `tests/leo_shell/test_logo.py`（只用标准库，自带 PNG 解码）**查出真实问题**：小尺寸帧边缘出现亮度 85 的暗边——母版中完全透明的像素仍保留原来的黑色 RGB，缩放时被混进边缘 | 母版脚本改为：所有非完全不透明的像素都取图块的奶白色。修正后 7 个尺寸可见边缘的最暗亮度为 234–246；256 帧里另有 2 个透明度仅 1/255 的像素颜色不定（屏幕上不可见），测试只看透明度 ≥ 16 的像素，理由写在测试里 |
| 6 | 起始页 `stage/shell.html`：去掉为狮子设计的深色徽章背景、描边与对比度滤镜；加载页与「关于」的图标只保留柔和阴影，圆角与图块一致 | 工作台 `.brand img` 原本就没有徽章，无需修改 |
| 7 | 预览（一次性本机静态服务 `127.0.0.1:8765`，服务会话临时目录；为此临时建的 `.claude/launch.json` 用后已删除） | 起始页加载屏、顶部品牌、设置 → 关于、工作台浅色与深色模式，都显示新图标，没有深色边框 |
| 8 | 来源登记：4 个图标文件与 `shell.html` 条目更新哈希与来源说明（原图 → 母版 → 编码，全部附哈希） | 15/15 条目与 `stage/` 文件一致；狮子旧母版 `leo-lion-warm.source.png` 作为历史保留 |
| 9 | 全量测试 | 1452 通过 / 0 失败 / 32 跳过 |
| 10 | 尚未构建和部署；2.1.2 的其他前端修改等用户给出 | |

### 2026-09-27 Astra · 2.1.2 设置背景范围与预览入口诊断

基线为 `claude/leo-2.1.2` 的 `94511f1`，工作分支为 `astra/leo-2.1.2-frontend`。本节只记录用户要求的设置方框与无法进入问题。

| 项目 | 原因、操作与结果 |
|---|---|
| 设置打开后主页出现矩形色差 | 面板动画结束时 `transform:none` 使其固定定位背景改以整个视口为包含块。保持零位移变换，令背景始终位于设置面板内；手写体图标和其他样式不变。 |
| 无法进入工作台 | 运行中的程序来自 `Documents/LeoAIStudio-deliveries/2.1.2/preview-r1/dist/LeoAIStudio`。该更新/视觉预览包缺少 `bridge/leo_bridge.sh`，日志在 PREFLIGHT 阶段报文件不存在，尚未进入模型连接。它也没有正式安装的用户配置；没有证据表明正版凭据丢失。 |
| 入口诊断修复 | Windows 界面层在调用 WSL 前检查启动脚本；缺失时返回固定公开提示 `APP_PACKAGE_INCOMPLETE`，中英界面提示打开完整安装版。此类错误不弹出模型设置、不执行失败连接清理，不显示磁盘路径或密钥。完整安装继续原连接流程。 |
| 验证 | `.venv` 全量：1458 passed、33 skipped、0 failed。跳过为 25 项 NumPy/Torch 依赖检查、7 项缺少本工作树默认上游安装的检查、1 项缺少本地 wheelhouse 的检查；未计为通过。入口相关定向测试 44 passed。隔离浏览器在浅色、深色、窄窗口下均复现旧背景溢出，修复后像素比对均无溢出；设置滚动/开关及中英两入口报错检查通过。 |
| 来源与交付 | 更新 `manifests/runtime-asset-origins.json` 的 shell 哈希；使用 `tools/theme_asset_provenance.py` 检查隔离资源副本。修改前后截图与测试证据保存在本次 Codex 会话 outputs/leo-2.1.2。 |
| 发布边界 | 未构建、未部署、未覆盖 2.1.1 正版或现有预览包；无法单独运行的预览包需在用户批准统一部署时使用完整安装底座。未改版本号、图标、科学代码、技能或已有实验记录；ACA-9 未处理。 |

## 2026-09-28 · Astra · 2.1.2 聊天重复回复与结束清单

- 用户反馈：问候收到两条相同回复，后者还带有自动生成的「完成内容 / Completed work」清单。
- 原因：工作台逐行展示上游持久化的正文与完成摘要，完成摘要格式器还会追加 completion_bullets。
- 修改：只在聊天显示层移除独立的协议清单，将同一用户轮次内相邻且正文完全相同的普通回复显示一次；轮询、重开、复制和转发都使用一致的可见正文。原始消息及科研记录不改写。
- 边界：不同用户轮次、不同正文、失败记录、审阅/执行身份和产物引用不合并；引用及代码块内的同名标题保留。没有修改上游、模型配置、科学代码、技能或图标，版本仍为 2.1.2。
- 验证：新增真实工作台脚本的 DOM 回归，覆盖中英文清单、重复与非重复回答、轮询、重开、复制、失败/审阅/产物记录和代码引用；定向 4 项通过。提交前另跑全量测试，部署与截图记录随本次交付保存。

## 2026-09-28 · Astra · 2.1.2 首页 Proposal A

- 首页换为「为学习、研究与创作而生的 AI 工作室」，增加五项轻导航、四项能力标签、研究过程示例；Hero 仅保留两个操作，模型配置文案移除，页脚连接状态读取实际运行状态。
- 右侧改为文献、释义笔记、研究结构、公式、代码和示意图组成的研究桌面；树作为渐隐背景，保留手写 Leo 图标及既有图标资源。
- 加入邮箱登录、注册和找回密码界面。按用户决定跳过后端接入：输入与提交均禁用，不发送或保存账号信息，本机工作台不受影响。
- 项目入口只读显示已有项目；工作台入口保持既有启动和可重试错误行为。保留此前重复回答/完成清单修复及设置抽屉背景隔离。
- 验证：首页浏览器回归覆盖中文、英文、深色、窄屏与矮窗口，检查导航、项目文本安全、离线账号、研究示例、真实连接状态及启动失败恢复；设置抽屉像素回归等待动画完成后比较。提交前执行 .venv 全量测试，并同步界面资源来源哈希。

## 2026-09-28 · Astra · 2.1.3 工作区管理与本地账号

- 工作台新增「管理对话与项目」：归档、移入回收站、恢复，以及需要确认文字的彻底删除。彻底删除经原生接口核对回收站记录、版本和目标，再调用已有后端的会话/项目删除服务；失败保留回收站记录。项目操作枚举所有分页，首页及工作台一致隐藏已归档/回收站项目。
- 输入框新增 effort 选择，按绑定模型实际支持的能力显示，选择随每次消息携带能力版本发送；按会话和模型保留选择，能力改变时拒绝旧选择并保留草稿。
- 工作台「管理模型配置」改为当前弹窗内编辑、新建、保存及删除配置，不再导航离开工作台；单独增加「返回主页面」并在有未发送草稿时提醒。
- 邮箱账号接入本地适配器：注册、登录、退出、恢复码重置；密码盐化 PBKDF2 存储，错误尝试限速，恢复码只显示一次。邮箱不验证，账号共用当前 Windows 工作区；设置和工作台始终无需登录。网络适配器可通过 account_request 边界替换。
- 产品版本 2.1.3；手写图标、科学代码和实验记录保持不变。增加账号、删除门禁、发送/草稿及浏览器管理流程测试；同步四个界面资源哈希，构建包检查新增账号模块。

## 工作台个人资料与导航（2026-09-28）

- 左下角改为登录用户的头像、显示名和简介入口；支持本地注册、登录、资料编辑和退出，已有账号自动迁移且保留凭据。
- 左侧集中工作台、科研任务、笔记本和设置，保留项目与历史对话区域；模型、外观、关于在工作台内打开，另设返回主页面入口。
- 顶部文件、编辑、视图、帮助菜单接入实际操作，包括完整分页对话导出、选区编辑、侧栏切换、文字缩放和使用指南。
- 外观支持显示模式、内置配色、自定义 JSON 上传与预览；会话创建仅准备草稿，用户发送后可从主题回复预览，确认后保存。
- 新增隔离账号、资料持久化与主题验证测试及浏览器回归；验证预览取消、保存失败、重启恢复、访客设置、菜单编辑与分页导出。用户现有会话和研究数据未用于变更测试。
- 保持 2.1.3 版本和原科学代码身份；未更改图标、冻结实验、既有记录或 ACA-9。

## 审阅修复：菜单、剪贴板与外观交接（2026-09-28）

- 视图菜单「放大 / 缩小 / 恢复文字大小」改为通过 `--text-scale` 变量作用于对话正文、输入框、科研说明与笔记本摘要；此前只改根字号，而样式全部以 px 定义，用户看不到变化。
- 粘贴读取剪贴板时与写入一致地短暂重试占用；`CLIPBOARD_BUSY`、`CLIPBOARD_TEXT_INVALID` 有了中文提示，不再向用户显示原始错误码；`paste_text` 与 `copy_text` 一样加锁并记录异常。
- 首页「上传自定义主题 / 通过会话创建」进入工作台后打开外观页的意向改由桌面进程一次性交接（`appearance_intent`），不再依赖 `load_html` 之间的 sessionStorage。
- 会话回复中的主题方案只取 `name` 与六个颜色字段再送后端校验，模型多输出说明字段时仍可预览；提示词明确只允许这两个字段。
- 顶部菜单栏 `role=menubar` 只包含菜单项，侧栏开关移到菜单栏之外；分组容器标记 `role=none`。
- 浏览器预览脚本注明为手工回归、不被 pytest 收集，浏览器渠道可用 `LEO_PREVIEW_CHANNEL` 指定。新增剪贴板重试与错误码、意向一次性消费、菜单结构与缩放样式的自动测试；四个界面资源哈希同步。

## 新桌面安装构建准备（2026-09-28）

- 接收 GitHub `claude/peaceful-fermi-nl17gw` 的 `548a068`，包含文字缩放、剪贴板重试和错误文案、主题入口传递及菜单语义修复。
- 对已批准脱敏的历史报告重新登记精确文件哈希，保持原报告范围和 3 项历史路径记录，不扩大审计豁免。
- README 快捷方式示例使用系统桌面目录接口，不绑定用户目录结构。
- 新安装迁移已有账号、模型配置、聊天、项目与科研数据；旧版清理在新安装校验之后按用户确认范围进行。

## 2026-09-28 · Claude · 前端打磨（淡墨浓秋）

- 先做视觉审计：用 `ThemeRuntime` 渲染真实首页与工作台，注入模拟 `pywebview.api`，在浅色、深色、1440/1280/840 宽及窄屏下逐页截图；用户按审计结果选定布局错误、科研层级、工作台框架、首页四组全部处理，在现有配色上打磨，不重做设计。
- 布局错误：840 宽时顶栏面包屑让位于右侧操作，不再与连接状态重叠，窄于 1050 时连接状态只留圆点；矮窗口收紧侧栏，最近对话不再被截断；科研任务面板改为只覆盖右侧工作区并带遮罩，不再盖住半个侧栏；各弹窗关闭按钮统一；头像上传改为按钮样式。
- 头像偏向左下：侧栏底部规则 `.rail-footer>button>span{padding-right:9px}` 同样作用于头像，首字与上传图片都被挤向左侧；首字使用宋体类衬线，中文字形在行框内偏低。改为头像无内边距、无衬线首字，实测水平偏差 0、垂直 0.5px，上传图片居中。
- 科研任务：验证页顶部新增结论卡片，以「允许声明 C2 / 只允许探索性描述 / 尚不可下结论」为标题并按可信度配色；六个可信度维度（数学、实现、训练、物理、外部精度、复现）与状态显示中文，原始键名保留在提示中；创建、生成草案、准备确认包、确认正式运行、确认审阅结论等主操作加重；运行确认包的种子方案、环境与复现容差改为可读文字，完整 JSON 仍可展开。提示横幅改用类名，不再依赖「第二段落」位置。
- 工作台框架：图标栏改为墨褐色，与侧栏合为一列；笔记本改用手绘图标（线圈本加趋势线，导航、首页卡片与笔记本空状态一致），导航文字缩为「笔记本」；在工作台首页时隐藏「返回工作台」；品牌副标题去掉「2.1」；消息下的复制、赞、踩、转发改为悬停显示，已给出的评价保持可见。
- 首页：改为科学研究定位「从一个问题，到可核验的结论」；示例卡片换成问题、结论、研究链路与计算（Poisson 校准示例），中英文同步；「一次研究怎样展开」四步改为提问、确认模型、计算与验证、形成结论；内容在可用高度内垂直居中。
- 验证：全量测试 1486 passed / 33 skipped（两次）；首页 5 个场景、工作台管理、个人资料与外观浏览器回归通过；设置抽屉「narrow: drawer art leaked onto home」像素检查失败，在未改动的 master 上以同一断言失败，为既有问题。同步五个界面资源哈希。仅离线渲染与无头浏览器验证，尚未构建、部署或在安装版中实机验收。
- 边界：`stage/research-panel.js` 属于科研代码身份，本次改动后需冻结再开始 PINN 正式运行。版本号仍为 2.1.3；科学代码、实验记录、冻结阈值与 ACA-9 未改动。

## 2026-09-28 · Claude · Leo AI 2.1.4 发布

用户决定把上一节的前端打磨发为 2.1.4，走完整的构建、部署、校验、回执流程，在安装版中实机查看后冻结界面，再开始 PINN 正式运行。

- 版本号 2.1.3 → 2.1.4：`leo_shell/__init__.py`、README、工作台「关于」；显示名仍为「Leo AI 2.1」。五个界面资源的来源登记标为「Leo AI 2.1.4」，哈希与 `stage/` 一致。
- 正式安装目录为 `C:\Users\user\Desktop\LeoAIStudio`（2026-09-28 新装的 2.1.3，源码 `4f50dc7`，桌面入口「Leo AI 2.1」指向它）；原候选版目录已不存在。本次在该目录原位升级。
- 科学源码快照按惯例新建 `runtime/science-source-2.1.4-<提交>`，`research-runtime.json` 的 `codeRoot` 改指向它；原 `science-source-current`（`4f50dc7`）保留。
- 构建、部署与校验的逐步记录见下表。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 本会话工作树接入主仓库的 `.venv`、`wheelhouse`、`wheelhouse-science`（目录联接，只读使用） | wheelhouse 校验 0 问题（21 个 wheel）；环境审计 0 问题 |
| 2 | 全量测试（治理环境） | 1487 通过 / 0 失败 / 32 跳过 |
| 3 | 发布提交 `6935890`；`master` 由 `4f50dc7` 快进到 `6935890`（主仓库检出仍在 `sync/github-20260928-548a068`，未改动） | |
| 4 | 构建：`tools/build_launcher.ps1`，输出 `Documents\LeoAIStudio-deliveries\2.1.4\build-r1` | hermetic；回执绑定 `6935890`，dirty=False；包契约 328 个 `_launcher` 文件、36 个关键文件、37 个归档模块；EXE 版本 2.1.4，SHA-256 `e300625a…` |
| 5 | 部署前确认应用未运行；`tools/deploy_release.ps1` 原位部署到正式安装目录；快捷方式参数指向会话临时文件 | 成功；回滚目录 `.leo-rollback-20260928-092449-cc8a5a17`；桌面「Leo AI 2.1.lnk」前后哈希相同，未新增快捷方式 |
| 6 | 科学源码快照：从本仓库克隆并检出 `6935890` 到 `runtime/science-source-2.1.4-6935890`；`research-runtime.json` 先备份到回滚目录 `upgrade-state-backup/runtime/`，再把 `codeRoot` 改指向新快照 | 快照 HEAD = `6935890`，工作区干净；`science-source-current`（`4f50dc7`）保留 |
| 7 | `tools/build_manifest.py -o manifests/build-current.json`（该文件被 git 忽略）；`tools/verify_release.py --strict` | **17 PASS / 0 FAIL / 0 NOT TESTED**，含部署前端 5 个文档、EXE、技能三处副本、上游版本、科学运行时与两套 wheelhouse |
| 8 | `tools/theme_asset_provenance.py --strict`；`tools/science_environment.py` | 15/15，0 未登记、0 漂移；科学环境无问题 |
| 9 | 已安装 `science-a` 解释器运行 `tests/pinn` | 952 通过 / 0 跳过 |
| 10 | 用户数据：`user/` 下 38 个文件，部署时刻之后修改数为 0 | 部署未触及用户数据（没有做逐文件摘要前后比对） |
| 11 | 启动已安装程序 | 窗口标题「Leo AI 2.1」；启动后日志无新的错误或警告 |
| 12 | 本地标签 `v2.1.4` → `6935890`；安装根目录写入 `RELEASE_2_1_4_RECEIPT.json` | 以上校验都在 `6935890` 上完成；本日志提交之后 HEAD 前移，复跑发布校验请先检出 `v2.1.4` |
| 13 | 未做 | 用户在安装版中的实机查看；没有发送模型消息、没有运行科研任务；没有推送到任何远端 |

回退方法：关闭应用，从 `.leo-rollback-20260928-092449-cc8a5a17` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-current`）。不要覆盖 `user/`。

## 2026-09-28 · Claude · 2.1.5 前端「一体侧栏」

用户认为 2.1.4 界面「还是差点意思」（整体质感、布局结构、细节交互三方面都有），指出最难看的是侧栏里的系统原生项目下拉框。先出 A 精修 / B 一体侧栏 / C 纸本三套高保真样稿，用户选 B，随后在真实工作台中实现并逐页截图核对。按用户决定，2.1.5 与 PINN 产品闭环并行，**不改动科研身份文件**（`stage/research-panel.js`、`leo_shell/api.py`、`leo_shell/research.py`、`leo_shell/research_draft.py`、`pinn/research/poisson1d-config.json` 改动数为 0），PINN 正式运行仍以冻结的 2.1.4 为代码身份。

- 框架：去掉单独的图标栏，合成一条墨褐侧栏——顶部项目切换器，下接「新对话」、工作台 / 科研任务 / 笔记本与计算、按「今天 / 昨天 / 近 7 天 / 更早」分组的对话，底部头像、返回主页面与设置。菜单栏左段与侧栏同色，窗口读作左右两栏；侧栏收起时品牌与开关回到菜单栏。
- 项目切换器：取代原生下拉框。每个项目有按项目 ID 稳定取色的首字母方块，当前项目打勾，可搜索；「新建项目」「管理对话与项目」收进同一菜单。
- 其余下拉框：模型、思考强度、显示模式、配色、模型配置、供应商、管理对话框的类型与状态，全部换成统一的弹出列表。原生 `<select>` 保留为唯一数据来源（取值、选项、禁用与 change 事件不变），自定义按钮与列表双向同步，支持方向键与 Esc。
- 行内菜单：每个对话、每个项目右侧悬停出现「⋯」，提供「归档」（立即生效，可恢复）与「删除」（确认后移入回收站，可恢复）；彻底删除仍只在「管理对话与项目 → 回收站」中、输入确认文字后进行。
- 顶栏：项目名作小标题，对话标题用衬线字，右侧操作带线条图标。对话区：代码块改为墨底并带语言标签与「复制」按钮，去掉代码块前后多出的空行；提问卡片的操作按钮挂在卡片外，不再撑高卡片。窄窗口下输入框工具条保持一行，长模型名省略。
- 去掉乘号：主题名改为「深海熔橙」「紫晶青绿」（起始页、工作台、`themes.json` 同步）；10 个关闭按钮（工作台 7、起始页 3）改为绘制的细线叉号。
- 测试调整（随结构变化，不放宽检查）：对话列表加入分组标题与行容器后，4 处「点击第一个对话」改为定位对话行；代码块前空行不再计入正文，一处期望值由 `'Example\n'` 改为 `'Example'`；管理回归脚本先打开项目切换器再进入管理；主题名测试随改名更新。
- 验证：全量测试 1486 passed / 33 skipped；浏览器回归「个人资料与外观」「管理对话与项目」「起始页」通过。设置抽屉回归需以修复前的 `94511f1` 起始页作对照；其窄窗口像素检查在未改动的 master 上同样两次失败一次，为既有不稳定项。同步五个界面资源哈希。仅离线渲染与无头浏览器验证，尚未构建、部署或实机查看；版本号仍为 2.1.4。
- 未完成：起始页设置抽屉的三个下拉框（模型配置、供应商、界面语言）仍为原生控件。

## 2026-09-28 · Claude · Leo AI 2.1.5 发布

用户批准提交后决定先单独发 2.1.5，发完启动供其试用，再给出 2.1.6 的改进方向。用户同时约定：2.1.x 版本只做前端，2.2.x 版本才开始 PINN 修改。

- 版本号 2.1.4 → 2.1.5：`leo_shell/__init__.py`、README、工作台「关于」；显示名仍为「Leo AI 2.1」。`shell.html`、`themes.json`、`workbench.html/css/js` 五项来源登记标为「Leo AI 2.1.5」，哈希与 `stage/` 一致。
- 科研身份文件相对 2.1.4 无改动，科学代码身份不变；科学源码快照仍按惯例为本次发布新建，供发布校验对齐源码提交。
- 构建、部署与校验的逐步记录见下表。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 工作树接入主仓库 `.venv`、`wheelhouse`、`wheelhouse-science`（目录联接，只读使用） | wheelhouse 校验 0 问题（21 个 wheel）；环境审计 0 问题 |
| 2 | 全量测试（治理环境） | 1487 通过 / 0 失败 / 32 跳过 |
| 3 | 发布提交 `e2665aa`；`master` 由 `ca33104` 快进到 `e2665aa`（主仓库检出仍在 `sync/github-20260928-548a068`，未改动） | |
| 4 | 构建：`tools/build_launcher.ps1`，输出 `Documents\LeoAIStudio-deliveries\2.1.5\build-r1` | hermetic；回执绑定 `e2665aa`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.1.5，SHA-256 `b747c51b…`。日志中的 `NativeCommandError` 与 android 子模块警告是 PyInstaller 写到 stderr 的提示，不影响构建 |
| 5 | 部署前确认应用未运行；`tools/deploy_release.ps1` 原位部署；快捷方式参数指向会话临时文件 | 成功；回滚目录 `.leo-rollback-20260928-105506-9910199a`；桌面「Leo AI 2.1.lnk」前后哈希相同，未新增快捷方式 |
| 6 | 科学源码快照 `runtime/science-source-2.1.5-e2665aa`（克隆并检出 `e2665aa`）；`research-runtime.json` 先备份到回滚目录 `upgrade-state-backup/runtime/`，再改 `codeRoot` | 快照 HEAD = `e2665aa`，干净；`science-source-2.1.4-6935890` 与 `science-source-current` 保留 |
| 7 | `build_manifest.py -o manifests/build-current.json`；`verify_release.py --strict` | **17 PASS / 0 FAIL / 0 NOT TESTED** |
| 8 | `theme_asset_provenance.py --strict`；`science_environment.py` | 15/15，0 未登记、0 漂移；科学环境无问题 |
| 9 | 已安装 `science-a` 解释器运行 `tests/pinn` | 952 通过 / 0 跳过 |
| 10 | 用户数据：`user/` 下 38 个文件，部署后修改数为 0 | 部署未触及用户数据 |
| 11 | 启动已安装程序供用户试用 | 进程 61288，窗口标题「Leo AI 2.1」；启动后日志无新的错误或警告 |
| 12 | 本地标签 `v2.1.5` → `e2665aa`；安装根目录写入 `RELEASE_2_1_5_RECEIPT.json`（排他创建；第一次因脚本仍指向 2.1.4 回执文件名而被拒绝写入，修正后写入，2.1.4 回执未受影响） | 以上校验都在 `e2665aa` 上完成；复跑发布校验请先检出 `v2.1.5` |
| 13 | 未做 | 用户试用进行中；没有发送模型消息、没有运行科研任务；没有推送到任何远端 |

回退方法：关闭应用，从 `.leo-rollback-20260928-105506-9910199a` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.1.4-6935890`）。不要覆盖 `user/`。

## 2026-09-28 · Claude · 2.1.6 起始页四个真实案例

用户试用 2.1.5 后提出：起始页右侧的四张卡片改成四个案例，并且可以点击。按用户选择，案例取自 Leo 自己的实验记录，点击后在起始页展开详情（不直接跳进工作台——那需要改 `leo_shell/api.py`，属于科研身份文件，2.1.x 不改）。分支 `claude/leo-2.1.6`，从 `master`（`627813a`）起。

- 四张卡片改为按钮：一维 Poisson 校准、二维 Poisson 校准、环域几何第三次尝试（均为 C2），以及环域几何第一次尝试（停线、不下结论）。每张卡片显示案例号、名称、关键方程、结论标签和一行结果；卡片 04 的小图画出第一次尝试 10 个种子的真实局部误差与 1e-3 阈值线。
- 数字逐项取自仓库记录：一维 `POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md`（中位 1.991e-4，复现 2.552e-4）；二维 `POISSON2D_CALIBRATION_REPORT_20260916.md`（中位 3.686e-5，AC2D-9 1.568e-4）；环域第三次 `experiments/annulus/runs/exp-geometry1-annulus-poisson-r3`（中位 1.555e-4，最差种子 ACA-9 7.631e-4，复现 1.741e-4）；环域第一次 `ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md`（种子 2 ACA-9 1.079e-3，中位 1.853e-4）。
- 点击卡片后在起始页下方展开案例详情：问题、模型、计算、验证、结论五步，记录位置，四个案例之间的切换标签，以及「进入工作台开始研究」。再次点击同一张卡片或点叉号收起；「看看四个真实案例」打开案例 01。中英文由同一张数据表渲染，随界面语言切换。
- 清理只服务于旧示意卡片的样式；修正卡片与详情标题中「·」被宋体渲染为宽圆点的问题；说明文字下移，不再被卡片 04 遮挡；手机宽度下结论标签缩小并在放不下时省略。
- 起始页浏览器回归：原先检查旧「研究结构」卡片的断言改为检查四张案例卡，并新增「点击卡片展开对应详情、标签切换、收起」检查；五个场景（桌面、深色、手机、矮窗口、英文）全部通过。全量测试 1486 passed / 33 skipped；科研身份文件改动数为 0；同步 `shell.html` 来源哈希。

## 2026-09-28 · Claude · 2.1.6 起始页设置下拉框

用户确认：起始页设置抽屉的三个原生下拉框换掉后，2.1.6 即完成。

- 模型配置、供应商、界面语言三个下拉框改用与工作台相同的弹出列表：原生 `<select>` 保留为唯一数据来源（取值、选项、禁用与 change 事件不变），自定义按钮与列表双向同步，当前项打勾，支持方向键与 Esc，点击字段标签也能打开。
- 起始页的语言切换代码按 `label[for="…"]` 查找这些标签，因此保留标签原有的 `for`，改为由标签点击事件打开列表（第一次尝试改动 `for` 导致页面脚本报错，已在提交前修正）。
- 验证：选择「本地 Qwen3」后模型栏自动填入 `qwen3-8b`，切换界面语言立即生效并保存；浅色、深色无脚本错误。全量测试 1486 passed / 33 skipped；起始页回归五个场景通过；设置抽屉回归（以修复前 `94511f1` 为对照）连续两次通过。科研身份文件改动数为 0；同步 `shell.html` 来源哈希。

## 2026-09-28 · Claude · Leo AI 2.1.6 发布

用户确认 2.1.6 内容齐备（起始页四个真实案例、设置抽屉下拉框），批准按既定流程发布；随后的 PINN 版本号定为 2.2.6。

- 版本号 2.1.5 → 2.1.6：`leo_shell/__init__.py`、README、工作台「关于」；显示名仍为「Leo AI 2.1」。`shell.html`、`workbench.html` 来源登记标为「Leo AI 2.1.6」，哈希与 `stage/` 一致。
- 科研身份文件相对 2.1.5（及 2.1.4）无改动，科学代码身份不变。
- 构建、部署与校验的逐步记录见下表。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 工作树接入主仓库 `.venv`、`wheelhouse`、`wheelhouse-science`（目录联接，只读使用） | wheelhouse 校验 0 问题；环境审计 0 问题 |
| 2 | 全量测试 | 1487 通过 / 0 失败 / 32 跳过 |
| 3 | 发布提交 `ba19f11`；`master` 由 `627813a` 快进到 `ba19f11` | |
| 4 | 构建，输出 `Documents\LeoAIStudio-deliveries\2.1.6\build-r1` | hermetic；回执绑定 `ba19f11`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.1.6，SHA-256 `3e4191d7…` |
| 5 | 部署前应用正在运行（此前为用户试用启动的 2.1.5，进程 61288），按用户批准的流程以正常关窗方式关闭（未强制结束）；随后原位部署，快捷方式参数指向会话临时文件 | 成功；回滚目录 `.leo-rollback-20260928-115839-30cfbf63`；桌面「Leo AI 2.1.lnk」前后哈希相同 |
| 6 | 科学源码快照 `runtime/science-source-2.1.6-ba19f11`；`research-runtime.json` 先备份到回滚目录，再改 `codeRoot` | 快照 HEAD = `ba19f11`，干净；2.1.5 与更早快照保留 |
| 7 | `verify_release.py --strict`；`theme_asset_provenance.py --strict`；`science_environment.py` | **17 / 0 / 0**；15/15；无问题 |
| 8 | 已安装 `science-a` 解释器运行 `tests/pinn` | 952 通过 / 0 跳过 |
| 9 | 用户数据：`user/` 下 38 个文件，部署后修改数为 0 | |
| 10 | 启动 2.1.6 | 进程 46704，窗口标题「Leo AI 2.1」；启动后日志无新的错误或警告 |
| 11 | 本地标签 `v2.1.6` → `ba19f11`；安装根目录写入 `RELEASE_2_1_6_RECEIPT.json`。回执脚本由 2.1.5 版本替换生成，写入前逐字段核对，发现「上一安装版本」一栏被替换顺序误改为 2.1.6，修正后再写入 | 回执读回核对无误；2.1.4、2.1.5 回执保留 |
| 12 | 未做 | 没有发送模型消息、没有运行科研任务；没有推送到任何远端 |

回退方法：关闭应用，从 `.leo-rollback-20260928-115839-30cfbf63` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.1.5-e2665aa`）。不要覆盖 `user/`。

## 2026-09-28 · Claude · 2.2.6 科研任务闭环准备（代码部分）

用户约定：2.1.x 只做前端，2.2.x 开始 PINN；第一个 PINN 版本号定为 2.2.6；科研任务以后会做成收费功能（后面再改）。开工前的只读调查结论：产品内科研任务只走到过「生成草案」，正式运行从未执行，测试中也没有调用过 worker 的准备、检查与阶段执行；安装中 3 个任务都停在草案，尚未预留任何盲测集。用户选定范围：补齐缺口、补测试、沙盒全链冒烟、冻结后由用户在安装版完成一维 Poisson 正式运行（二维放到之后）；盲测集规则不变但界面显示剩余额度；运行中关窗先提醒、确认后停止并记为已取消；现在预留一个空的收费检查点。本节只含代码部分，分支 `claude/leo-2.2.6`（自 `master` `c4b02a8`）。

- 草案解析：模型把整段 JSON 包在一个 Markdown 代码块里时先去掉外壳再解析（`research_draft.unfence`），其余内容不做任何剥离，仍由严格解析拒绝。
- 准备改为后台：新增 `PREPARING` 状态，服务先保存状态再在线程中调用 `worker prepare`，面板轮询；准备期间读取、列表不再被占用。worker 只接受 `PREPARING` 状态的任务。上次会话遗留的 `PREPARING` 在下次读取时标为 `PREPARATION_INTERRUPTED`。已预留盲测集的任务不能再次准备（`PREPARATION_ALREADY_EXISTS`），界面给出「以此草案新建任务」。
- 过期确认包：确认正式运行时若检查、确认包哈希或模型哈希不一致，在任务上记录 `runBlocked` 与原因；面板不再显示「审阅并确认正式运行」，改为说明原因并提供新建任务。
- 结束原因：supervisor 在写结果前出错时，由 `worker.execute` 写入 `STOPPED`、`phase: supervisor` 与原因代码（已写结果不覆盖）；服务把结果的状态、阶段、退出码、原因、时间写进任务 `completion`；失去 worker 时记为 `WORKER_LOST`。面板用中文说明结束于哪一阶段、为什么。
- 失败证据可见：未得到已核验决策的运行，验证视图附带 `failure`（`RUN_SUMMARY` 的最终状态、可信度向量、未通过的门禁、失败特征、Tier-1 是否通过、结束原因）；面板显示「这次运行记录下的结果」与维度标签。
- 全部任务：`list` 支持 `scope: "all"`（按更新时间倒序，附会话 ID），面板新增「查看全部科研任务」并标注其他对话的任务。
- 盲测集额度：新模块 `pinn/research/quota.py` 固定 32 个候选网格与搜索顺序（worker 改用它），并统计本机任务预留与代码根中已登记的候选网格（同一网格只计一次）；`get` 返回 `quota` 与 `canPrepare`。面板在准备前提示「永久占用 1 个盲测集（剩余 N / 32），成败都不退还」，额度为 0 时不再提供准备。
- 关窗保护：`ui` 的窗口关闭事件（pywebview 在 UI 线程上同步执行）在有准备或运行中的任务时弹出原生确认框；确认则对运行中任务写入取消请求（原因 `APP_CLOSED`），由 supervisor 停止当前阶段并记为 `CANCELLED`、保留证据；取消则不关窗。相关方法在 `ShellApi` 中以下划线开头，页面无法调用。
- 收费检查点：新模块 `leo_shell/entitlements.py`（在科研代码身份之外）定义 `COSTLY = {create, fork, draft, prepare, approve_run}` 与 `check()`，目前一律放行；服务在这些操作前调用它，只传任务 ID 与会话 ID，不传提示词或草案。以后接入收费只改这个模块，不改变 codeHash、不使已准备的确认包失效。
- 测试：新增 `tests/pinn/test_research_loop_226.py`（16 条）、`tests/test_research_panel_226.py`（5 条）、`tests/leo_shell/test_research_close_guard.py`（5 条）；原准备超时测试随新流程改为检查任务上的 `preparationError`，测试夹具改为同步准备。全量测试 1512 passed / 33 skipped；已安装科学解释器运行 `tests/pinn` 968 passed / 0 skipped。新文件在加入 git 之前，代码身份测试会按规则报「身份边界内有未跟踪文件」，加入后通过。同步 `research-panel.js` 来源哈希。
- 科研身份：本次改动了 `leo_shell/api.py`、`research.py`、`research_draft.py`、`stage/research-panel.js` 与 `pinn/research/`，产品运行的 codeHash 相应改变；正式运行须在 2.2.6 冻结之后进行。
- 未做：沙盒全链冒烟（会真实打开一个盲测集，按用户决定稍后再议；届时需把冒烟占用的网格登记入库，使正式运行换用新的盲测集）；没有构建、部署或版本号变更。

## 2026-09-28 · Claude · 2.2.6 沙盒全链冒烟与盲测集登记

用户批准：按正式配置做沙盒全链冒烟；冒烟占用的盲测集登记入库，让正式运行换用新网格；冒烟通过后接着发布 2.2.6；如果发现缺陷，修好后重新冒烟。本轮开始前只读核对了 git 引用、安装版、回执、快捷方式和任务状态，均与记录一致（安装版 3 个任务都停在草案，没有预留过盲测集）。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 本会话分支 `claude/leo-2-2-6-research-loop-b297ec` 由 `c4b02a8` 快进到 `f951acd`（仅本地 ref） | |
| 2 | 干净快照：把本地仓库克隆到 `%TEMP%\leo226\source` 并检出 `f951acd`。第一次克隆到会话临时目录时因 Windows 路径过长失败，残留的空目录已删除 | HEAD = `f951acd`，工作区干净；整个冒烟过程中除字节码缓存外始终干净 |
| 3 | 冒烟脚本（会话临时目录 `smoke226.py`）：使用真实的 `ResearchService`（后台准备）与 `pinn.research.worker`，科研根目录为沙盒 `%TEMP%\leo226\app\user\research`，解释器为安装版 `science-a` / `science-b`。模型回复模拟为带 ```json 外壳的草案，经 `unfence` 与 `validate_draft` 解析；**两次人工确认在沙盒中自动放行**（仅限这个一次性科研根目录，正式运行的两次确认由用户本人完成） | 草案 supported，模板 `poisson1d-v1` |
| 4 | 准备（后台，用时 50 秒） | `READY_FOR_RUN_APPROVAL`；预留盲测集 **GL1024-CGL4002**；codeHash `a6d1ba6f…`，specHash `58b71fea…`；沙盒额度 31 / 32 |
| 5 | 正式运行：主实验 → Tier-1 → 独立复现 → G6（总计约 7 分 30 秒，预算 3600 秒） | 主实验约 160 秒，10/10 成功，dev 相对 L2 中位数 **1.991e-4**，最差 2.480e-4；每个种子 AC-1 在 7.08e-5 到 2.52e-4 之间，没有 MUST 判据失败。Tier-1 通过（最大 Δq 1.052e-4，P4）。复现（science-b，种子偏移 10000）中位数 2.552e-4，差 5.617e-5，容差 1e-4，C_repro PASS。结果 `COMPLETED`，核验 `ACCEPTED`，允许 C0/C1/C2，C3 被阻断（缺少独立合格的 C2 运行）。两个环境只有 `installationId` 不同，为同一台机器上两个独立安装 |
| 6 | 导出 | 222 个文件，`PACKAGE_MANIFEST` 自检通过 |
| 7 | 独立核对 1：在导出包自带的 `source` 目录，用不含 torch 的主仓库 `.venv` 执行 `pinn.research.worker verify --task-root ..` | 返回码 0 |
| 8 | 独立核对 2：用 `science-b` 执行导出包的 `pinn.research.reproduce`，先预览再 `--execute`（约 310 秒） | 返回码 0；`reproduction_report.json`：C_repro PASS，同代码、同规格、不同种子集，没有触碰 claim 集；执行前后导出包逐文件哈希不变 |
| 9 | 登记：把冒烟的 claim 文件原样复制为 `experiments/poisson1d/problems/pdef-research-037832e8b0e64780941f6c9e862c9a72-claim-GL1024-CGL4002.json`（sha256 `4b0cead3…`，与沙盒中一致），并新增说明 `experiments/poisson1d/SMOKE_2_2_6_CLAIM_REGISTRATION_20260928.json`（不匹配 claim 通配规则）。提交 `b3bb0d7` | 模拟准备搜索：新安装额度 31 / 32，跳过 GL1024-CGL4002，下一次会选 **GL1056-CGL4004**。`experiments/` 在科研代码身份之外，登记不改变 codeHash |

- 冒烟与历史记录对得上：一维 Poisson C2 结案时的中位数为 1.991e-4、复现为 2.552e-4，与本次在四位有效数字上相同（同一配置、同一组种子）。
- 冒烟没有发现代码缺陷，所以没有重新冒烟，只占用了一个盲测集。
- 科学地位：冒烟不作为任何结论的证据，也不与正式运行合并统计。
- 冒烟产生的临时文件（沙盒快照、科研根目录、导出包、独立复现输出、日志）在发布完成后清理，清理情况记在发布一节。

## 2026-09-28 · Claude · Leo AI 2.2.6 发布

冒烟通过后按用户批准接着发布，流程同 2.1.6。2.2.6 是第一个 PINN 版本。

- 版本号 2.1.6 → 2.2.6：`leo_shell/__init__.py`、README、工作台「关于」；显示名和桌面入口仍为「Leo AI 2.1」。同步 `workbench.html` 来源哈希与标签。
- 发布包含三个提交：`f951acd`（科研闭环代码）、`b3bb0d7`（冒烟盲测集登记）、`5e03d0d`（版本号、README、冒烟记录）。后两个提交只改动科研代码身份之外的文件。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 工作树接入主仓库 `.venv`、`wheelhouse`、`wheelhouse-science`（目录联接，只读使用，保留） | |
| 2 | 全量测试（版本号改动后、提交前各一次）；已安装 `science-a` 运行 `tests/pinn`（提交前与提交后各一次） | 1513 通过 / 0 失败 / 32 跳过；968 通过 / 0 跳过 |
| 3 | 发布提交 `5e03d0d`；在该提交上重算科研代码身份 | codeHash `a6d1ba6f…`（109 个身份文件），**与冒烟完全一致** |
| 4 | `master` 由 `c4b02a8` 快进到 `5e03d0d`（本地） | |
| 5 | 构建，输出 `Documents\LeoAIStudio-deliveries\2.2.6\build-r1` | hermetic；回执绑定 `5e03d0d`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.2.6，SHA-256 `d8195942…` |
| 6 | 部署前对 `user/` 做摘要（38 个文件）；正在运行的 2.1.6（进程 46704）以正常关窗方式关闭（未强制结束） | 正常退出 |
| 7 | 原位部署，快捷方式参数指向临时文件 | 成功；回滚目录 `.leo-rollback-20260928-132329-b12f598c`；桌面「Leo AI 2.1.lnk」前后哈希相同 |
| 8 | 科学源码快照 `runtime/science-source-2.2.6-5e03d0d`（克隆并检出 `5e03d0d`）；`research-runtime.json` 先备份到回滚目录 `upgrade-state-backup/runtime/`，再只改 `codeRoot`（Git Bash 的 sed 把 CRLF 改成了 LF，随后已恢复为 CRLF，与备份相比仅 `codeRoot` 一处不同） | 快照 HEAD = `5e03d0d`，干净；2.1.6 与更早快照保留 |
| 9 | `build_manifest.py -o manifests/build-current.json`；`verify_release.py --strict`；`theme_asset_provenance.py --strict`；`science_environment.py` | **17 / 0 / 0**；15/15；无问题 |
| 10 | 安装快照核对：科研代码身份与额度 | codeHash `a6d1ba6f…` 与冒烟一致，快照干净；真实安装额度 1 已用 / 31 剩余，下一次准备选 GL1056-CGL4004 |
| 11 | 用户数据：部署后摘要对比 | 部署修改数为 0。唯一变化是 `user/logs/leo-shell.log` 多了两行，由关闭中的 2.1.6 在 13:23:19 写入（早于部署开始的 13:23:29）；摘要是在关窗前取的 |
| 12 | 启动 2.2.6 | 进程 54864，窗口标题「Leo AI 2.1」；启动后日志只有两条 INFO，无错误或警告 |
| 13 | 本地标签 `v2.2.6` → `5e03d0d`（附注标签）；安装根目录写入 `RELEASE_2_2_6_RECEIPT.json`（显式逐字段写出，先打印逐字段核对，发现两个提交是短哈希，改为完整哈希后排他创建） | 回执读回核对无误；「上一安装版本」为 2.1.6 / `ba19f11`；2.1.4–2.1.6 回执保留 |
| 14 | 未做 | 用户本人的一维 Poisson 正式运行（确认模型、确认运行两步由用户完成）；安装版中没有发送模型消息、没有运行科研任务；没有推送到任何远端 |

代码冻结：科研代码身份固定为 `a6d1ba6f…`。以后改动 `pinn/`、科研身份文件或产品配置都会使已准备的确认包失效，并需要新版本号。

回退方法：关闭应用，从 `.leo-rollback-20260928-132329-b12f598c` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.1.6-ba19f11`）。不要覆盖 `user/`。注意：2.1.6 的科学快照里没有冒烟的盲测集登记，回退状态下不要做正式运行。

测试与冒烟产物的建立和删除：

| 产物 | 建立者 | 处理 |
| --- | --- | --- |
| 会话临时目录下 `smoke226`（克隆因路径过长失败留下的空目录） | 冒烟准备 | 当即删除 |
| `%TEMP%\leo226`（217 MB：沙盒快照、沙盒科研根目录与任务、导出包、独立复现输出、冒烟日志与摘要、各步输出、`user/` 部署前后摘要、部署用临时快捷方式） | 冒烟与部署 | 发布完成后删除；冒烟的 claim 文件已原样登记入库，数字记在本节与回执 |
| `%TEMP%\pytest-of-user\pytest-3`、`pytest-4`、`pytest-5` 与 `pytest-current` 链接 | 本轮四次 pytest | 删除（父目录保留） |
| 工作树中的 `__pycache__`（两轮，各 6 个目录） | 测试子进程 | 删除 |
| 工作树 `manifests/build-current.json` | 发布清单 | 保留（git 忽略，发布校验需要） |
| 会话临时目录下 `smoke226.py`、`receipt226.py` | 冒烟驱动与回执脚本 | 保留在会话临时目录备查，不在仓库和安装目录中 |

## 2026-09-29 · 用户 · 一维 Poisson 产品内正式运行（Leo AI 2.2.6）

用户在安装版 2.2.6 中亲手完成了第一次产品内正式运行。确认模型、准备、确认正式运行都由用户本人点击；Claude 没有操作界面，只在运行前后只读核对任务目录，本节是用户同意后写入的记录。安装版中的证据没有任何改动。

| 项目 | 内容 |
| --- | --- |
| 任务 | `research-a7fc950532844c7ea91564e0f045405a`；草案模型 deepseek-v4-pro |
| 时间线（UTC） | 建立 03:49:37 → 草案 03:50:07 → 确认模型 03:51:31（原生对话框，内容 SHA-256 `d999c113…`，与草案一致）→ 准备 03:51:43–03:52:15 → 确认正式运行 04:33:45（原生对话框）→ 完成 04:41:13 |
| 身份 | codeHash `a6d1ba6f…`（2.2.6 冻结身份，科学快照 `science-source-2.2.6-5e03d0d`）；specHash `40d46d72…` |
| 盲测集 | **GL1056-CGL4004**（样本集哈希 `9a8c71c3…`），与冒烟的 GL1024 不同；本机额度已用 2 / 剩 30 |
| 结果 | `COMPLETED`，核验 **ACCEPTED**；六个维度全部 PASS；允许 C0、C1、C2；C3 阻断（缺少独立合格的 C2 运行） |
| 数字 | 训练 10/10，dev 相对 L2 中位数 1.991e-4，最差 2.480e-4；盲测 AC-1 逐种子最大 2.519e-4（阈值 1e-3），没有 MUST 失败；Tier-1 通过（最大 Δq 1.052e-4）；独立复现中位数 2.552e-4，差 5.617e-5 < 1e-4，C_repro PASS |
| 核对 | 证据文件哈希与完成回执一致；在科学快照上重新 `verify_attempt` 结果相同；快照工作区干净 |

- 盲测误差与冒烟在约 13 位有效数字上相同：两次种子相同，训练结果相同（训练不接触盲测集）；1056 点与 1024 点的高阶求积都几乎精确地积分这个光滑误差，因此只在末几位不同。这同时说明训练没有接触盲测集。
- 同一时段还有一个任务 `research-5be2b897…` 停在草案：模型把区间和边界条件写进了「方程」字段（`-u''(x)=pi^2*sin(pi*x), 0<x<1, u(0)=u(1)=0`），方程精确匹配失败，被判为不受支持，界面只显示笼统提示。用户随后新建任务成功。列入 2.2.7 修复清单。
- 用户反馈：界面「点什么都卡几秒」。只读实测（在任务副本上）：已完成任务每次读取都完整重新核验证据，耗时 5.7 秒，主要在纯 Python 的逐对最小间距检查（约 1150 万对），期间占住解释器锁，整个应用都会变慢。列入 2.2.7 修复清单（核验一次、按证据哈希缓存）。测时用的任务副本 `%TEMP%\leo227probe` 已删除。
- 尚未做：导出证据包、人工结论审阅（都由用户决定）。

## 2026-09-29 · Claude · 2.2.7 开发（代码部分）

用户试用 2.2.6 后提出：界面「点什么都卡几秒」；导出的证据让数学背景的读者看懂的知识成本和时间成本太高（Leo 的初心是降低做科研的各种成本，而不是替人做科研）；2.2.7 把运行预算改成「预计约 8 分钟，上限 60 分钟」；左侧栏加定时任务（可随时取消删除，精确到分钟）；对话区加审批模式 Off / Smart / Auto（Auto 红字警告高风险）。用户选定：三层证据说明书 + 应用内证据页重做；审批模式按上游规则映射、默认 Smart；定时任务到点在指定对话里自动发一条消息、仅应用开着时执行；样稿三组全部通过；草案缺陷「改提示词 + 说清原因」。分支 `claude/leo-2.2.7`（自 `master` `012d920`）。

- 卡顿：只读实测已完成任务每次读取都完整核验证据（5.7 秒，主要是纯 Python 的逐对最小间距检查，约 1150 万对，期间占住解释器锁，整个应用变慢）。改为完成后完整核验一次，结果按「完成回执 + 证据哈希 + 桌面版本」缓存在 `user/research/cache/`；之后每次读取只重算证据哈希（实测 50–60 毫秒）。导出与「一键重新核对」始终完整核验。治理层核验代码未改。
- 证据可读：新模块 `leo_shell/evidence_guide.py`（科研代码身份之外）从证据记录生成三层说明——一句话结论、四个关键数字与「可以说 / 不能说」；用数学语言讲六项检查（每项可展开看逐条机器判定）；「凭什么算证据」五步（标准先定、考题封存、只拆一次、代码指纹、独立复算），附术语表与证据地图。数字全部取自记录；复现未通过时不写「一致」，没有核验通过时不生成说明书。导出时生成「证据说明书.html」放进证据包，受包内哈希清单保护；生成失败不阻止导出，旧版说明书不会混进新包。
- 一键重新核对：新操作 `recheck`，四步逐项显示结果与耗时——证据文件与完成回执一致；运行记录的代码指纹与运行确认包一致；盲测检验点训练前封存且只打开一次；完整复核六项判定与结论等级。
- 草案：提示词写明「方程」一栏只写方程本身；草案不受支持时 `unsupportedReasons` 逐项说明哪一栏对不上（匹配规则仍是精确匹配，不放宽），面板引导直接「修改模型草案」。
- 运行时长文案：确认对话框与运行页都改为「预计约 8 分钟，上限 60 分钟」（按产品配置给出预计值，未知配置只写上限）。
- 审批模式：只读调查发现 Leo 从未接入上游的审批机制——AI 调用需要批准的工具（如命令行）时，对话会停住最长 15 分钟后按拒绝处理，界面上没有可点的地方。新增 `leo_shell/approvals.py`：每个对话的模式存于 `user/approval-modes.json`，通过上游已有的权限接口写成「本对话」规则（Off：上游默认放行的工具全部改为先问；Smart：在上游默认之外，改写文件也先问；Auto：上游默认要问的工具全部放行；任何模式都不写拒绝规则，上游的 `.env` 拒读规则始终有效）；切换模式只替换 Leo 自己写的规则，写到一半失败会撤回。新增标准库 WebSocket 客户端 `leo_shell/websocket_client.py`（外壳没有打包任何 WebSocket 库），订阅当前对话的待批准请求；页面显示审批卡片，可「允许这一次」「本对话内都允许同类操作」「拒绝」，凭据内容永不显示。上游代码未改动。
  - 与样稿的一处出入：上游对沙盒内运行的计算代码（Python / R 单元）不经过审批，所以 Off 的说明写作「受控操作之前都先问你，沙盒里运行的计算代码不在此列」。
- 定时任务：新增 `leo_shell/schedules.py`（`user/schedules.json`）与侧栏入口、独立页面、新建 / 编辑对话框（对话选择用统一弹出列表）。到点用该对话自己的模型绑定、默认思考强度发送；只在 Leo 打开时执行，关闭期间错过的只记一条「已错过」，可手动「现在发送」或「忽略」；一次性任务执行后自动停用。
- 接线：`leo_shell/workbench.py` 增加本地操作注册口，`leo_shell/extensions.py` 在窗口启动时挂上审批中心与定时器、关窗时停止；页面仍只通过 `workbench_request` 调用，`api.py` 未改动。
- 科研身份：改动了 `leo_shell/research.py`、`research_draft.py`、`stage/research-panel.js`，产品运行的 codeHash 相应改变；发版前须重新做沙盒冒烟（会再占用 1 个盲测集）。
- 测试：新增 `tests/pinn/test_research_guide_227.py`（23 条）、`tests/leo_shell/test_approvals_227.py` 与 `tests/leo_shell/test_schedules_227.py`（共 39 条）；`tests/test_workbench_runtime.py` 的笔记本操作白名单加入启动时读取角标用的 `schedules`（本地处理，不访问守护进程）。全量 1575 passed / 0 failed / 32 skipped；已安装 `science-a` 运行 `tests/pinn` 991 passed。版本号 2.2.6 → 2.2.7，同步 `workbench.html`、`workbench.css`、`workbench.js`、`research-panel.js` 来源哈希。
- 浏览器核对（会话临时目录，真实模板 + 模拟接口）：证据页、重新核对、草案原因、运行页文案，以及审批模式弹层、Auto 确认（需先勾选）、审批卡片与决定、定时任务列表与新建，均无脚本错误。测时与导出测试用的任务副本 `%TEMP%\leo227probe`（安装版正式任务的复制，9.5 MB，含一次测试导出）已删除；安装版原件未改动。
- 提交：`41d132d`（科研部分）、`35faac4`（审批模式、定时任务、版本号）。

## 2026-09-29 · Claude · 2.2.7 沙盒全链冒烟与盲测集登记

用户选择：Off 档接受如实说明（上游不对沙盒内的计算代码做审批）；冒烟通过就连着发版；发版后由 Claude 在安装版里实测审批与定时任务。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 干净快照：克隆到 `%TEMP%\leo227\source`，检出 `abf9371` | HEAD = `abf9371`，干净 |
| 2 | 冒烟驱动（会话临时目录 `smoke227.py`，在 2.2.6 版基础上加入「打开已完成任务两次计时、一键重新核对、导出包内说明书」三项检查）；两次人工确认只在沙盒中自动放行 | |
| 3 | 准备（30 秒） | 预留 **GL1056-CGL4004**。这与用户正式运行打开过的是同一个网格（样本集哈希 `9a8c71c3…` 相同）：沙盒科研目录看不到安装版的预留，仓库登记表中只有 GL1024。该网格已被正式运行用掉，冒烟没有额外占用安装版额度；冒烟不作为证据 |
| 4 | 正式运行：主实验 → Tier-1 → 独立复现 → G6（约 5 分钟） | `COMPLETED`，核验 `ACCEPTED`，允许 C0/C1/C2；中位数 1.991e-4，最差 2.480e-4，盲测最大 2.519e-4，复现 2.552e-4（差 5.617e-5 < 1e-4）；确认对话框显示「预计约 8 分钟，上限 60 分钟」 |
| 5 | 打开已完成任务两次 | 0.08 秒、0.06 秒（完成时已核验并缓存） |
| 6 | 驱动脚本在打印含上标「⁻」的日志时因控制台 GBK 编码报错退出（驱动自身问题，产品无误）；以 UTF-8 输出续跑同一沙盒任务的其余步骤 | |
| 7 | 一键重新核对 | 四步全部通过，6.0 秒 |
| 8 | 导出 | 223 个文件；`证据说明书.html` 在包内且列入哈希清单 |
| 9 | 独立核对：不含 torch 的 `.venv` 在导出包源码中 `worker verify`；`science-b` 执行导出包的 `reproduce`（预览 + 执行，116 秒） | 返回码均为 0；复现报告 C_repro PASS、未触碰 claim 集；导出包执行前后逐文件哈希不变 |
| 10 | 登记：冒烟 claim 文件原样复制为 `experiments/poisson1d/problems/pdef-research-41c03c7b150a432499cbd088ba402ab5-claim-GL1056-CGL4004.json`（sha256 `b1d0c029…`），说明 `experiments/poisson1d/SMOKE_2_2_7_CLAIM_REGISTRATION_20260929.json`；提交 `f9756fc` | 安装版额度按此登记表计算仍为 2 已用 / 30 剩余；下一次正式准备选 GL1088-CGL4006 |

- 冒烟 codeHash `b14a43c2…`（2.2.7 新身份；2.2.6 为 `a6d1ba6f…`）。
- 冒烟产生的临时文件在发布完成后清理，记在发布一节。

## 2026-09-29 · Claude · Leo AI 2.2.7 发布

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 全量测试；已安装 `science-a` 运行 `tests/pinn`（均在发布提交上） | 1575 通过 / 0 失败 / 32 跳过；991 通过 |
| 2 | 发布提交 `6d00a1f`（冒烟记录）；重算科研代码身份 | codeHash `b14a43c2…`（109 个身份文件），与冒烟一致 |
| 3 | `master` 由 `012d920` 快进到 `6d00a1f`（本地） | |
| 4 | 构建，输出 `Documents\LeoAIStudio-deliveries\2.2.7\build-r1` | hermetic；回执绑定 `6d00a1f`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.2.7，SHA-256 `3195dca9…` |
| 5 | 部署前对 `user/` 做摘要（148 个文件）；应用此前已由用户关闭，未做关窗操作 | |
| 6 | 原位部署，快捷方式参数指向临时文件 | 成功；回滚目录 `.leo-rollback-20260928-231031-35c7de93`；桌面「Leo AI 2.1.lnk」前后哈希相同 |
| 7 | 科学源码快照 `runtime/science-source-2.2.7-6d00a1f`；`research-runtime.json` 先备份到回滚目录，再按字节只替换 `codeRoot`（CRLF 保持不变） | 快照 HEAD = `6d00a1f`，干净；2.2.6 与更早快照保留 |
| 8 | `build_manifest.py -o manifests/build-current.json`；`verify_release.py --strict`；`theme_asset_provenance.py --strict`；`science_environment.py` | **17 / 0 / 0**；15/15；无问题 |
| 9 | 安装快照核对 | codeHash 与冒烟一致，快照干净；额度 2 已用 / 30 剩余，下一次准备选 GL1088-CGL4006（模拟搜索验证） |
| 10 | 用户数据对比 | 148 个文件，部署修改数为 0 |
| 11 | 启动 2.2.7 | 进程 51976，窗口「Leo AI 2.1」；日志无错误，审批与定时服务正常启动（没有「无法启动」记录） |
| 12 | 本地标签 `v2.2.7` → `6d00a1f`（附注）；写入 `RELEASE_2_2_7_RECEIPT.json`（显式逐字段写出，先打印核对后排他创建） | 读回无误；「上一安装版本」为 2.2.6 / `5e03d0d` |
| 13 | 实机验收（用户同意由 Claude 进行） | **未完成**：申请了控制 Leo AI 窗口的权限，但 Windows 处于锁屏状态，截图为空白；改为只连后台守护进程做不调用模型的实测，发现守护进程尚未启动（应用停在开始页，要等用户进入工作台才启动），第一步即连接失败，没有创建任何对话、没有写入任何文件。Claude 不代替用户进入工作台。待用户回来后再做 |
| 14 | 未做 | 实机验收；没有推送到任何远端 |

- 2.2.6 时准备好的运行确认包在 2.2.7 下不能再确认（codeHash 改变），需「以此草案新建任务」。
- 回退方法：关闭应用，从 `.leo-rollback-20260928-231031-35c7de93` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.2.6-5e03d0d`）。不要覆盖 `user/`。

测试与冒烟产物的建立和删除：

| 产物 | 建立者 | 处理 |
| --- | --- | --- |
| `%TEMP%\leo227`（221 MB：沙盒快照、沙盒科研根目录与任务、导出包、独立复现输出、冒烟日志、`user/` 部署前后摘要、部署用临时快捷方式） | 冒烟与部署 | 发布完成后删除；冒烟 claim 文件已原样登记入库 |
| `%TEMP%\leo227probe`（9.5 MB） | 开发期测时 | 已删除（见开发一节） |
| `%TEMP%\pytest-of-user\pytest-*` 与工作树 `__pycache__` | 各轮 pytest | 每轮后删除 |
| 工作树 `manifests/build-current.json` | 发布清单 | 保留（git 忽略，发布校验需要） |
| 会话临时目录下样稿截图、`mock227/`、`smoke227*.py`、`receipt227.py`、`live227.py`、补丁与同步脚本 | 样稿、冒烟、回执、实测 | 保留在会话临时目录备查，不在仓库和安装目录中 |

## 2026-09-29 · 用户 / Claude · 2.2.7 人工验收反馈与 2.2.8 开发（代码部分）

用户亲自在安装版 2.2.7 中测试后反馈：切换审批模式要等很久（例如 Smart → Auto）；让 AI 执行 `pip list` 时它先说了好几句话才给结果，希望有思考链（接的是 DeepSeek，应有思考内容）；Smart 模式下连续问了两次；定时任务表单去掉「（精确到分钟）」；生成草案特别慢且失败过一次；Auto 确认框里「我了解风险」的勾选框难看。用户同时开放了电脑控制权限（高危操作仍须先问）。

只读调查（未改任何东西）：
- 运行日志显示测试的 15 分钟内页面发出 418 次请求，每次都先调用 `wsl.exe leo_bridge.sh url` 取后台地址（中位数 0.39 秒）。这是整体发卡与切换 Auto（需写 21 条规则）慢的根源。
- 上游收到 DeepSeek 的 `reasoning_content` 后只解析、既不保存也不发给页面，Leo 目前拿不到原始思考文字（上游不能改）。那几句话是 AI 在工具调用之间的过程话；问了两次是模型两次尝试了不同写法的命令，不是界面重复。
- 草案是对 deepseek-v4-pro 的单次请求，超时 90 秒；以往用时 30–67 秒；23:26 那次任务没有草案（大概率超时），失败原因没有记录。
- 上游对命令行没有按具体命令给出「只读」判定（`authorize_bash` 的副作用分类固定），因此只读放行由 Leo 自己用保守白名单判断，用户确认了名单。
- 为读取真实时间线数据，Claude 两次尝试操作安装版：第一次屏幕处于锁屏；第二次启动应用后仍为锁屏，随即以正常关窗方式关闭了自己启动的实例（进程 23164），没有进入工作台、没有创建任何对话。

用户选择（均为推荐项），版本号 **2.2.8**：
- 后台地址缓存：`WslBridge.client_url()` 缓存 10 分钟，守护进程启动 / 停止时清空，页面网关遇到令牌被拒（401/403）时清缓存重试一次，连接失败时只对读取请求重试（发消息等写操作可能已送达，绝不重发）；审批中心 WebSocket 连接失败时同样清缓存。
- 「思考与步骤」：新网关操作 `timeline`（上游 `/frames/{id}/action-timeline`，只保留步骤类型、标题、状态、审批结果，不含命令与参数）。对话每一轮只突出最终答案，此前的过程话与执行步骤（运行计算 / 调用工具 / 交给子助手，完成 / 未成功，经你批准 / 自动放行 / 审批超时）收进可展开的一栏，运行中自动展开；失败的回复仍单独显示。原始 DeepSeek 思考文字本轮不做。
- Smart 只读放行：命令必须完整匹配白名单（`pip list/freeze/show`、`python --version`、`conda list/info`、`ls`、`pwd`、`whoami`、`date`、`uname`、`free`、`df`、`which`、`nvidia-smi`、`git status/log/diff/branch`），出现管道、重定向、`;`、引号、`$`、`~`、通配符等一律照常询问；只在 Smart 下生效；自动批准失败时退回审批卡片；放行记录显示在「思考与步骤」里。
- 草案：等待上限 90 → 180 秒（连接阶段的超时也归为超时）；面板每秒显示已等待时间；失败时在任务上记录 `draftError`（原因代码与等待秒数，事件 `DRAFT_FAILED`），面板说明原因并提供「重新生成草案」；未知错误文本只记通用代码，不记原文。
- Auto 确认的「我了解风险」改为卡片式勾选（勾选后整卡变红，才可开启）；定时任务表单去掉「（精确到分钟）」。
- 科研身份：改动了 `leo_shell/research.py`、`research_draft.py`、`stage/research-panel.js`，codeHash 相应改变；发版前重新冒烟。
- 测试：新增 `tests/leo_shell/test_workbench_228.py`（地址缓存与重试、时间线、折叠渲染、只读放行等，33 条）与 `tests/pinn/test_research_draft_228.py`（3 条）；`tests/test_workbench_runtime.py` 中三个「同一轮多条回复全部显示」的旧预期改为新行为（前面的回复折叠，失败回复仍显示）；`tests/leo_shell/test_approvals_227.py` 的示例命令由 `git status`（现属只读）改为 `git push`。全量 1611 passed / 0 failed / 32 skipped；`science-a` 运行 `tests/pinn` 994 passed。版本号 2.2.7 → 2.2.8，同步四个界面资产来源哈希。
- 浏览器核对（会话临时目录）：思考与步骤折叠 / 展开、新勾选卡片未勾 / 已勾、定时任务表单、草案失败面板，以及 2.2.7 的全部界面检查，均无脚本错误。
- 提交：`5f6f0b0`。

## 2026-09-29 · Claude · 2.2.8 沙盒全链冒烟与盲测集登记

用户确认只读命令白名单，并选择冒烟通过就连着发 2.2.8、发版后由 Claude 实测。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 干净快照：克隆到 `%TEMP%\leo228\source`，检出 `52165bc` | 干净 |
| 2 | 冒烟驱动 `smoke228.py`（与 2.2.7 相同的检查项，控制台输出改为 UTF-8） | 一次跑完，没有中断 |
| 3 | 准备（30 秒） | 预留 **GL1088-CGL4006**（仓库已登记 GL1024、GL1056） |
| 4 | 主实验 → Tier-1 → 独立复现 → G6（约 5.5 分钟） | `COMPLETED`，核验 `ACCEPTED`，允许 C0/C1/C2；中位数 1.991e-4，盲测最大 2.519e-4，复现 2.552e-4，C_repro PASS |
| 5 | 打开已完成任务两次；一键重新核对；导出 | 0.09 秒、0.06 秒；四步全部通过（6.5 秒）；`证据说明书.html` 在包内且列入清单 |
| 6 | 独立核对：不含 torch 的 `.venv` 在导出包中 `worker verify`；`science-b` 执行导出包 `reproduce`（138 秒） | 返回码均为 0；复现未触碰 claim 集；导出包前后不变 |
| 7 | 登记：冒烟 claim 文件原样复制为 `experiments/poisson1d/problems/pdef-research-4b5a795483ee4096a27f5af1f864d41c-claim-GL1088-CGL4006.json`（sha256 `0a57852c…`），说明 `experiments/poisson1d/SMOKE_2_2_8_CLAIM_REGISTRATION_20260929.json`；提交 `d0b4cf3` | 安装版额度按此登记表为 3 已用 / 29 剩余 |

- 冒烟 codeHash `76c01ee2…`（2.2.8 新身份）。

## 2026-09-29 · Claude · Leo AI 2.2.8 发布

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 全量测试；已安装 `science-a` 运行 `tests/pinn`（均在发布提交上） | 1611 通过 / 0 失败 / 32 跳过；994 通过 |
| 2 | 发布提交 `3e9b583`（冒烟记录）；重算科研代码身份 | codeHash `76c01ee2…`，与冒烟一致 |
| 3 | `master` 由 `98fe638` 快进到 `3e9b583`（本地） | |
| 4 | 构建，输出 `Documents\LeoAIStudio-deliveries\2.2.8\build-r1` | hermetic；回执绑定 `3e9b583`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.2.8，SHA-256 `aa411c8b…` |
| 5 | 部署前 `user/` 摘要（152 个文件）；应用未在运行 | |
| 6 | 原位部署，快捷方式参数指向临时文件 | 回滚目录 `.leo-rollback-20260929-001013-98fe8b77`；桌面「Leo AI 2.1.lnk」前后哈希相同 |
| 7 | 科学源码快照 `runtime/science-source-2.2.8-3e9b583`；`research-runtime.json` 先备份再按字节只替换 `codeRoot`（CRLF 不变） | 快照 HEAD = `3e9b583`，干净 |
| 8 | 清单与严格校验、资产来源、科学环境 | **17 / 0 / 0**；15/15；无问题 |
| 9 | 安装快照核对与用户数据对比 | codeHash 与冒烟一致；额度 3 已用 / 29 剩余；`user/` 152 个文件，部署修改数为 0 |
| 10 | 启动 2.2.8 | 进程 15816；日志无错误 |
| 11 | 本地标签 `v2.2.8` → `3e9b583`（附注）；写入 `RELEASE_2_2_8_RECEIPT.json`（整份重新编写、逐字段核对后排他创建） | 读回无误；「上一安装版本」为 2.2.7 / `6d00a1f` |
| 12 | 实机验收（Claude 用用户开放的控制权限） | **未完成**：屏幕仍处于锁屏，没有进行任何界面操作 |
| 13 | 清理 | `%TEMP%\leo228`（224 MB：沙盒快照、科研根目录、导出包、复现输出、日志、`user/` 摘要、临时快捷方式）已删除；冒烟 claim 已登记入库。会话临时目录下的截图与脚本保留备查 |

- 2.2.7 下准备好、尚未确认运行的任务在 2.2.8 下需「以此草案新建任务」。
- 回退方法：关闭应用，从 `.leo-rollback-20260929-001013-98fe8b77` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.2.7-6d00a1f`）。不要覆盖 `user/`。

## 2026-09-29 · Claude · 2.2.8 实机核对与 2.2.9（Smart 写文件放行）

更正：此前三次说「屏幕处于锁屏」是误判。截图工具把未授权应用的窗口涂成深色，`lockapp.exe` 常驻后台并不代表锁屏；实际原因是 Leo 窗口被最小化、前台是 Claude 桌面应用，而且 Leo 的界面由 WebView2 子进程绘制，截图工具无法授权该进程，所以 Leo 的界面在截图里始终是黑的。Claude 用系统接口把 Leo 窗口还原到前台（不涉及数据），界面仍不可见，改为请用户点「进入工作台」后在后台接口层实测。

2.2.8 实测（脚本 `live228.py`，直接连正在运行的守护进程，未调用模型）：

| 项目 | 结果 |
| --- | --- |
| 取后台地址 | 第一次 0.41 秒，之后缓存命中几乎为 0 |
| 连续 10 次页面请求 | 0.14 秒（2.2.7 时每次先付约 0.4 秒） |
| 新建测试对话「2.2.8 验收」（`f-e1de46c0c7d3`，hello 项目），首次写入 Smart 规则 | 0.05 秒 |
| 切到 Auto、切回 Smart | 各 0.41 秒，守护进程中的对话规则与设计逐条一致（此次模式记录写在临时目录，避免与运行中的应用抢写同一文件） |
| 读取用户 pip list 对话的真实时间线（只读） | 17 条消息、16 个步骤；第一轮 AI 写了 6 次文件（`write_file`）再在计算代码里执行 `host.bash("pip list")`；第二轮两次审批分别是 `write_file` 与 bash |

据此查明：Smart 问了两次，其中一次是 AI 写临时脚本（2.2.7 的 Smart 规则让写文件也先问），另一次才是命令行（2.2.8 已对只读命令自动放行）。用户选择（推荐项）：**新写文件放行，修改已有文件才问**，并马上发 2.2.9。

- `leo_shell/approvals.py`：Smart 规则只保留 `edit_file` 先问；规则版本 1 → 2，已有对话下次打开时自动替换为新规则（旧的写文件规则被删除）。面板文字同步为「读写新文件……直接进行；……修改已有文件……前先问你」。
- 科研身份文件未改动，codeHash 仍为 `76c01ee2…`，不需要冒烟、不占盲测集。
- 测试：`tests/leo_shell/test_approvals_227.py` 更新 Smart 规则与规则编号的预期，新增「旧版本规则在下次打开时被替换」。版本号 2.2.8 → 2.2.9，同步 `workbench.html` 来源哈希。
- 尚未实测：AI 在 Smart 下执行只读命令时不再弹卡片——需要一次真实的模型调用，由用户在「2.2.8 验收」对话里发一句即可核对。

### Leo AI 2.2.9 发布

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 全量测试；发布提交 `0aa7ee6`；重算科研代码身份；`master` 快进 `0fcad15` → `0aa7ee6` | 1612 通过 / 0 失败 / 32 跳过；codeHash 仍为 `76c01ee2…` |
| 2 | 构建 `Documents\LeoAIStudio-deliveries\2.2.9\build-r1` | hermetic，回执绑定 `0aa7ee6`，dirty=False；EXE 2.2.9，SHA-256 `06ac7291…` |
| 3 | `user/` 摘要（152 个文件）后，以正常关窗方式关闭用户自行打开的 2.2.8（进程 51804） | 正常退出 |
| 4 | 原位部署（快捷方式参数指向临时文件） | 回滚目录 `.leo-rollback-20260929-003725-68aa9f33`；桌面快捷方式不变 |
| 5 | 科学源码快照 `runtime/science-source-2.2.9-0aa7ee6`（发布校验要求快照提交与仓库一致）；备份后按字节只替换 `codeRoot` | 快照干净，codeHash 与 2.2.8 相同 |
| 6 | 清单、严格校验、资产来源、科学环境 | **17 / 0 / 0**；15/15；无问题；额度仍为 29 / 32（本版不冒烟、不占盲测集） |
| 7 | 用户数据对比 | 部署修改数为 0；`leo-shell.log` 多出的两行是关闭 2.2.8 时（00:37:14）写的，早于部署（00:37:25） |
| 8 | 启动 2.2.9；本地标签 `v2.2.9`；写入 `RELEASE_2_2_9_RECEIPT.json`（逐字段核对后排他创建） | 进程 23172，日志无错误；回执读回无误 |
| 9 | 清理 | `%TEMP%\leo229`（`user/` 摘要与临时快捷方式）与实测时的临时模式目录 `%TEMP%\leo228-modes-*` 已删除；测试对话「2.2.8 验收」保留，留给用户做最后一次模型实测，删不删由用户决定 |

- 回退方法：关闭应用，从 `.leo-rollback-20260929-003725-68aa9f33` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.2.8-3e9b583`）。不要覆盖 `user/`。

### 2.2.9 用户实测：写文件仍在反复申请（Claude 的失误）

用户在「2.2.8 验收」对话里用 Smart 发消息，写文件仍然一次次弹出审批卡片。只读核对守护进程规则：该对话有一条「写文件先问」的对话规则（`perm_50a16da7ed33`），是 Claude 的实测脚本 `live228.py` 按 2.2.8 版 Smart 规则写入的；脚本当时把模式记录写在临时目录（为避免与运行中的应用抢写文件），并在事后删除，所以应用不知道这条规则，2.2.9 的规则升级也就没有清掉它。用户 pip list 对话的旧规则在应用记录中（版本 1），下次打开会被自动替换，不受影响。

- 处理：Claude 删除了这条由自己误留的规则（`DELETE /permissions/perm_50a16da7ed33`），复查后该对话只剩「修改已有文件先问」，与 2.2.9 设计一致。删除前已被发出的那一次审批请求需要用户点一次「允许这一次」。
- 待定改进（未实施，待用户决定）：打开对话时除应用记录外，再核对守护进程中实际存在的对话规则，清掉不属于当前模式的 Leo 管理规则（`*` 通配、Leo 管理的工具）；用户通过「本对话内都允许同类操作」授予的规则不动。

### 2.2.9 用户实测：Smart 不再反复申请（只读核对）

用户在新对话 `f-4f0e6da21bf5` 中以 Smart 发送「请用命令行执行 pip list，告诉我前 3 行。」，界面显示最终答案，上方「思考与步骤 · 20 项」折叠。Claude 只读核对：该对话的模式记录为 Smart（规则版本 2），守护进程中只有「修改已有文件先问」一条对话规则；本轮 8 次工具调用（两次写文件、三次列目录、一次读文件、一次联网抓取失败、一次联网搜索）与 1 次计算代码，**审批请求 0 次**。

- 本轮 AI 是在沙盒计算代码里用 `subprocess` 执行 `pip list`，上游不对计算代码做审批，所以「只读命令自动放行」这条路径没有被触发；它目前只有单元测试覆盖。
- 另记两处观察（未处理）：模型在执行命令前先尝试联网抓取与搜索，拖慢了回答；答案中的产物链接显示为原始 Markdown 文本（`[名称](/api/artifacts/…)`），未渲染为可点击链接。

## 2026-09-29 · Claude · 2.2.10（审批规则对账、答案里的文件链接、减少 AI 绕路）

用户在 2.2.9 实测后同意三件事，并选择版本号 **2.2.10**、第 3 项走「方案 A：自带技能」。本轮调查阶段只读（读源码与已安装的上游代码），没有调用守护进程接口，没有改任何文件。

1. **审批规则对账**（`leo_shell/approvals.py`）
   - 起因：2.2.9 实测里一条没有记录的「写文件先问」规则（Claude 的实测脚本留下）让 Smart 反复申请。此前应用只信自己的记录 `user/approval-modes.json`，守护进程里实际存在的规则从不核对。
   - 现在打开对话时读 `GET /frames/{id}/permissions` 的会话规则，与当前模式对账：属于 Leo 管理的规则（工具与 pattern 恰好是某个模式会写的那些，如 `write_file *`）但不属于当前模式的，删除；模式需要而缺失的，补写；决定不一致的（如 `edit_file *` 被改成 allow），改回。**用户通过「本对话内都允许同类操作」授予的具体 pattern 规则、全局规则、项目规则一律不动。**
   - 每个对话每次运行只核对一次（多一次读请求），切换模式时也会核对一次；读不到列表或补写失败只记日志、下次打开重试，不影响打开对话。
   - 顺手堵住一个隐患：「本对话内都允许」在上游没给建议 pattern、目标又为空（或应用重启后已不记得这次请求）时，过去会退回 `*`，写出一条与模式规则同键的「整个工具都放行」规则；现在这种情况只放行这一次，不写常驻规则。
   - 测试：新增 `tests/leo_shell/test_approvals_2210.py`（10 项，含状态化的假守护进程）；`test_approvals_227.py` 一处断言只看 POST 请求。
2. **答案里的文件链接**（`stage/workbench.js`、`workbench.html`、`workbench.css`）
   - 上游默认给的链接是 `/api/artifacts/<产物 id>`（打开可信交付开关后是 `/api/v1/artifacts/versions/<版本 id>`）。以前直接显示成 Markdown 原文。
   - 现在渲染成可点击的文字按钮（不带地址）；点击后在本对话的产物列表里按 id、版本 id、文件名匹配，走已有的 `artifact_preview` 网关操作，在对话框里预览图片或文本（其他类型说明暂不能预览）。匹配不上就说明「不在本对话的产物中」，不发预览请求；`[文字](https://…)` 外链保持原样文字，不打开。
   - 网关的产物列表多带 `versionId`（`leo_shell/workbench.py`）；文件列表每个对话只读一次，找不到才刷新。
   - 测试：新增 `tests/test_answer_artifact_links_2210.py`（Node 运行时，覆盖图片、文本、版本链接、缺失文件、外链）；`test_owned_workbench.py` 更新产物列表的预期。
3. **减少 AI 绕路**（新增技能 `skills/local-env-check`）
   - 调查：上游系统提示里有一条硬规定——「涉及外部事实、数据集、文献时必须先用 web_search/web_fetch，不要凭记忆」，模型把 `pip list` 也当成了外部事实。上游没有用户自定义指令字段、没有按工具禁用的配置（`config.py` 的 egress 只管出网白名单）。可行的杠杆只有：技能（上游每轮把技能名和不超过 200 字的描述拼进系统提示）、发送时给消息加前缀（会写进对话记录，需要在显示和导出里剥掉）、拒绝 web 工具的权限规则（会误伤真正的研究联网）。用户选了第一种。
   - 新增技能 `local-env-check`：一句话描述本身就是引导（本机/沙盒问题直接执行一条命令，不要 web_search / web_fetch），正文给出命令对照表和边界（只读；安装、升级、卸载仍要审批；外部事实仍应联网）。不改上游、不进对话记录。
   - 技能靠 `tools/sync_skills.py` 推到已安装目录 `user/user-skills/` 和 WSL 守护进程读取的目录；发布校验 `verify_release` 核对这两处与仓库一致，因此发版流程多一步「同步技能」。
   - 效果需要一次真实模型调用来验证（在测试对话里发一句 pip list，看有没有先联网），结果见下方实测记录。
   - 测试：新增 `tests/skills/test_local_env_check_2210.py`（前置信息、描述长度不超过上游截断的 197 字符、正文引用的 host 调用）。

- 版本号 2.2.9 → 2.2.10（`leo_shell/__init__.py`、`workbench.html` 关于页、`README.md`）；`manifests/runtime-asset-origins.json` 同步 `workbench.html/css/js` 的来源哈希与版本。
- 科研身份文件（`research.py`、`research_draft.py`、`api.py`、`research-panel.js`、`pinn/`）均未改动，codeHash 预计仍为 `76c01ee2…`，不需要冒烟、不占盲测集。
- 全量测试（本工作树，未安装科学依赖、无上游检出）：**1625 通过 / 0 失败 / 33 跳过**（同一提交 `2bf544a` 在 2.2.9 工作树里是 1612 / 0 / 32；新增 14 项，多出的 1 个跳过是本工作树没有本地 wheelhouse 的 `test_wheelhouse.py:350`，跳过清单其余部分逐条一致）。

### Leo AI 2.2.10 发布

用户确认「我自己关」应用后，Claude 才做部署（没有代关用户的窗口）。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 发布提交 `5a64e2d`；`master` 快进 `2bf544a` → `5a64e2d`（本地）；重算科研代码身份 | codeHash 仍为 `76c01ee2…`（109 个身份文件）；不冒烟、不占盲测集（额度 3 已用 / 29 剩余） |
| 2 | 构建 `Documents\LeoAIStudio-deliveries\2.2.10\build-r1`（本工作树用目录联接 `.venv`、`wheelhouse`、`wheelhouse-science` 指向主仓库，git 忽略，验收后只删联接本身） | hermetic；回执绑定 `5a64e2d`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.2.10，SHA-256 `c087ba4a…` |
| 3 | 部署前对 `user/` 做摘要（152 个文件）；确认用户已关闭 2.2.9 | |
| 4 | 原位部署，快捷方式参数指向临时文件 | 成功；回滚目录 `.leo-rollback-20260929-014325-36ba43ce`；桌面「Leo AI 2.1.lnk」前后哈希相同 |
| 5 | **同步技能**：`tools/sync_skills.py`（先 `--check` 只见新技能的 4 处差异，再同步） | 已安装目录 `user/user-skills/local-env-check/` 与 WSL 守护进程技能目录各写入 2 个文件；`--check --require-wsl` 三处一致（WSL 里 `lean-math` 的一个旧 `.pyc` 属既有额外文件，未动） |
| 6 | 科学源码快照 `runtime/science-source-2.2.10-5a64e2d`（`git clone` + 分离检出 `5a64e2d`）；`research-runtime.json` 先备份到回滚目录（该目录此前没有 `upgrade-state-backup`，由脚本新建），再按字节只替换 `codeRoot`（CRLF 保持不变） | 快照干净；安装快照重算 codeHash = `76c01ee2…`；2.2.9 及更早快照保留 |
| 7 | `build_manifest.py -o manifests/build-current.json`；`verify_release.py --strict`；`theme_asset_provenance.py --strict`；`science_environment.py` | 第一次 `science wheelhouse` 失败（本工作树缺 `wheelhouse-science` 联接，与部署内容无关）；补联接重跑后 **17 / 0 / 0**；15/15；无问题 |
| 8 | 用户数据对比 | 152 → 154 个文件：没有任何文件被改动或删除，只多出 `user-skills/local-env-check` 的两个文件（第 5 步同步所致） |
| 9 | 启动 2.2.10；本地附注标签 `v2.2.10` → `5a64e2d`；写入 `RELEASE_2_2_10_RECEIPT.json`（整份重新编写，写入后读回逐字段核对，排他创建） | 进程 6536，窗口「Leo AI 2.1」，日志无错误，停在开始页等待进入；「上一安装版本」为 2.2.9 / `0aa7ee6` |
| 10 | 未做 | 守护进程实测（规则对账、产物预览）与模型实测：要等用户点「进入工作台」；没有推送到任何远端 |

- 回退方法：关闭应用，从 `.leo-rollback-20260929-014325-36ba43ce` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.2.9-0aa7ee6`）。不要覆盖 `user/`；如需撤回技能，删除 `user/user-skills/local-env-check` 与 WSL 数据目录下同名目录。

### 2.2.10 实机核对（接口层 + 用户手点）

用户点「进入工作台」后，Claude 用脚本 `live2210.py`（在会话临时目录，连正在运行的守护进程，不打印令牌）先只读列出 10 个对话的规则与产物；随后新建测试对话「2.2.10 验收」（`f-6fd8a9f769c6`，hello 项目）并预置两条规则：一条漏网的 `write_file *` 先问（模拟旧脚本遗留），一条用户式授予的 `bash echo hello` 允许。用户按约定在应用里发了一次真实消息，并点开了对话。

| 项目 | 结果 |
| --- | --- |
| 只读列表 | 产物列表带版本号（`latest_version_id`），`artifact_preview` 读出 `_run_pip.py` 文本；旧对话 `f-805d7ef2b8db` 仍是版本 1 规则（守护进程里有 `write_file` 先问） |
| 规则对账 | 用户点开「2.2.10 验收」时（02:14:48）日志记「removing 1 approval rule(s) … do not belong to smart mode」：漏网的 `write_file *` 被删，`bash echo hello` 保留；点开旧对话 `f-805d7ef2b8db` 后（02:15:51）记录升为版本 2，守护进程只剩 `edit_file` 先问；其余两个 Smart 对话原本就一致 |
| 答案里的文件链接 | 用户截图：答案的「产物：- pip_list.txt」显示为可点击虚线文字，点击弹出预览对话框，内容为 `pip list` 的表头与包列表 |
| 模型实测（用户在「2.2.8 验收」`f-e1de46c0c7d3` 发「请用命令行执行 pip list，把完整结果存成文件 pip_list.txt，并告诉我前 3 行。」，Smart） | 时间线 12 步：6 次 `write_file`、1 段计算代码里 `host.bash("pip list > pip_list.txt …")`、`finalize_response`；**没有 `web_fetch` / `web_search`**，没有审批卡片。2.2.9 的同类请求里有一次联网抓取失败和一次联网搜索。仅一次样本，不能据此断定是技能起的作用（看不到系统提示是否被采用），需要多用几次再看 |
| 顺带发现 | 用户消息末尾已被附加「[System note: dynamic remote GPU configuration context] Accelerator…」——附加提示的机制早就存在于桥接层（`bridge/`），若以后要走「发送时加提示」方案，可以复用；本轮未动 |
| 需用户留意 | 「2.2.10 验收」在打开 10 秒后（02:14:58）被切成了 Auto（记录里 21 条 `*` 允许 + 那条 `echo hello`）；不是 Claude 操作。测试对话，未改回，由用户决定 |

- 测试对话「2.2.10 验收」保留，「2.2.8 验收」保留，删不删由用户决定。Claude 在测试对话里预置的规则未清理（`echo hello` 允许仍在，模式为 Auto）。
- 清理：`%TEMP%\leo2210`（`user/` 摘要与部署脚本）；`%TEMP%\pytest-of-user` 下 `pytest-7/8/9` 与 `pytest-current`；本工作树 7 个、2.2.9 工作树 6 个 `__pycache__`（均为今天 01:27 之后本轮测试产生）；本工作树的三个目录联接 `.venv`、`wheelhouse`、`wheelhouse-science`（只用 `rmdir` 删联接本身，主仓库目标核对完好）。会话临时目录里的 `live2210.py` 保留备查。`manifests/build-current.json` 是 git 忽略的生成物，保留。

## 2026-09-29 · Claude · 2.2.11（二维 Poisson 进科研任务、模型原始思考、补实测）

用户在新窗口选定本轮四件事并定版本号 **2.2.11**：二维 Poisson 进产品；补测 2.2.10 未证实的两点；显示 DeepSeek 原始思考；清理两个测试对话。二维方案四项用户均选推荐项：种子并行（上限 90 分钟）、二维盲测集单独一份 32 个、草案由模型自动识别一维 / 二维、一维和二维各做一次沙盒冒烟（各占 1 个盲测集并登记）。新分支 `claude/leo-ai-2-2-10-continue-be9359`（起点 master `0fd0532`）。

开工前只读核对：安装版 2.2.10（回执、exe `c087ba4a…`、回滚目录、`codeRoot` = `science-source-2.2.10-5a64e2d` 且快照 HEAD 为 `5a64e2d`）与交接一致；额度按候选表计 3 已用（GL1024 / GL1056 / GL1088）、29 剩余，下一次一维准备会抽到 GL1120-CGL4008；Leo 正在运行（进程 6536），守护进程在线（只读列出 11 个对话及其规则）。

1. **模型原始思考**（`leo_shell/workbench.py`、`stage/workbench.js`、`stage/workbench.css`）
   - 调查结论与 2.2.8 时的判断不同：早先的桥接层 `bridge/leo_thought_runtime.py` 已把每次模型调用的 `reasoning_content` 逐条写进守护进程数据库（表 `leo_model_projections`），并提供 `GET /frames/{id}/leo-projections`；只读核实安装版数据库里已有 3833 条思考记录。缺的只是前端：旧的显示代码随 `stage/leo-inject.js` 在 2.1 前端重做时删除。**本轮不改桥接层任何字节**（已安装的覆盖层按哈希核对，改动会让守护进程拒绝启动）。
   - 网关新增只读操作 `thoughts`：只保留 `thought` 通道、来源为 `reasoning_content` / `reasoning` 且文本摘要与记录一致的条目；每条最多 32 KB、最多 200 条，超出如实标注；不向页面透露执行编号、服务商等字段。
   - 「思考与步骤」里新增「模型思考 · 原文，未经核实」，按回合匹配、按调用顺序逐条折叠，纯文本显示（不会生成链接按钮）；只有思考的回合也会折叠；没有思考记录（其他模型）时与原来完全一样。运行中每 5 秒最多读取一次。
   - 在守护进程上只读验证：三个对话分别读出 10、13、1 条思考，回合编号与时间线一致。
   - 测试：新增 `tests/leo_shell/test_workbench_thoughts_2211.py`（路由、筛选与截断、大响应读取上限、Node 运行时渲染：按回合、按顺序、只有思考也折叠、无思考时不变）。
2. **二维 Poisson 进科研任务**（科研身份文件，codeHash 会变）
   - 新增产品配置 `pinn/research/poisson2d-config.json`：方法与已验收的二维校准配置 `experiments/poisson2d/configs/exp2d_baseline.json` 逐项相同（测试核对），只改 `configId` 为 `leo-poisson2d-hard-bc-v1` 和说明。
   - `pinn/research/worker.py`：按问题族（`poisson1d` / `poisson2d`，由草案 `templateId` 决定）分派配置、runner、盲测集目录与预算；二维预算 5400 秒、种子并行进程数 `min(10, CPU 核数 − 2)`（执行参数，写进计划和 identity，不进方法）；准备时二维候选网格还要过「坐标不落在小有理数上」的预注册规则；运行确认包多了 `family`、`parallelWorkers`，二维的复现容差取自其冻结配置（绝对 1e-4 且相对 0.5 倍中位数）；停止或超时改用 `taskkill /T` 连同并行训练的子进程一起结束；两个配置都进入代码身份。
   - `pinn/experiments2d/runner2d.py` 补齐产品模式（只在科研任务的运行上下文里生效，历史校准的运行方式不变）：数据写进任务目录；用产品代码身份并拒绝脏工作树；尝试目录自带台账副本与封存版问题定义；主实验、Tier-1、G6 写当前结论指针；G6 先按两份运行记录重算复现结论、再把复现证据复制进主实验目录；复现容差取自冻结配置而不是旁边的历史校准包；命令行支持 `--context`、`--workers`。
   - 新增 `pinn/experiments2d/parallel2d.py`（与环形域的并行训练同一做法：spawn 进程、每个训练单线程、结果按任务顺序返回）；`redteam2d.run_tier1` 先训练全部扰动（可并行）再按固定顺序测量。
   - `pinn/research/quota.py`：二维候选表 32 个，`D2C-GL{n}-CGL{m}`，n 为 42 起的偶数，m − 1 为 61 起的连续素数（避开校准用过的 GL32–38、D_phys 的 GL40 与 m − 1 ∈ {49, 53, 55, 59}）；一维、二维分开计数，返回值带 `family`。越往后网格越大，二维准备上限设为 15 分钟。
   - `pinn/research/reproduce.py`：导出包的独立复现按包里的问题族选 runner 与目录。
   - `leo_shell/research_draft.py`：第二个已验证模板（方程 −(u_xx + u_yy) = 2π² sin(πx) sin(πy)，区域 [[0,1],[0,1]]，四条边 u = 0）及其方法说明（逐项复述冻结配置，测试核对）；提示词写明两道已验证问题和二维的 domain / boundary 格式；二维方程的等价写法按确定规则匹配（Δu、∇²u、∂²u/∂x² 等），模型无法扩大支持范围；未匹配时按二维口径说明原因。
   - `leo_shell/research.py`：按问题族显示额度、二维准备上限 900 秒；「预计约 N 分钟」移到身份之外的新文件 `leo_shell/research_estimates.py`（只是显示文字，冒烟实测后可以更正而不作废冒烟；硬上限仍在确认包里）。
   - `stage/research-panel.js`：「问题类型」卡片、二维方程 / 区域 / 四条边的显示；「修改模型草案」按草案形状给出一维或二维字段并可切换；额度提示写明一维 / 二维分开计数；准备提示按问题族给出上限；确认包列出并行进程数和二维的相对容差。
   - `leo_shell/evidence_guide.py`（身份之外）：证据说明书按问题族换用二维的方程、边界、物理检查与盲测点位置等说法；数字仍全部取自运行记录。
   - 测试：新增 `tests/pinn/test_research_2d_2211.py`（模板识别与等价写法、方法复述、配置与已验收方法相同、二维网格构造规则、分开计数、问题族与预算、停止时整树结束、二维计划走二维 runner、二维任务的额度与准备上限、二维说明书）、`tests/pinn/test_poisson2d_parallel.py`（需 torch：并行与串行逐位相同、Tier-1 先训后测）、`tests/test_research_panel_2d_2211.py`（Node 运行时：二维显示、编辑器切换与保存形状、二维额度提示）；`test_research_loop_226.py` 两处额度断言加上 `family`。
- 版本号 2.2.10 → 2.2.11（`leo_shell/__init__.py`、`workbench.html` 关于页、`README.md`）；`manifests/runtime-asset-origins.json` 同步 `workbench.html/css/js` 与 `research-panel.js` 的来源哈希与版本（其余条目核对未变）。
- 新文件 `git add` 暂存：`pinn/` 下的未跟踪文件会让 PRELOCK 的「代码身份文件均已跟踪」检查失败（第一次全量测试因此在 `test_amendments` 失败，暂存后通过）。
- 测试环境备注：本会话环境带有 `PYTHONIOENCODING=utf-8`，会让 `test_diagnostic_evidence_command_refuses_overwrite` 按 GBK 解码子进程的 UTF-8 输出而失败（与改动无关，去掉该变量后通过）；此后全量测试都在去掉它的环境里运行。
- 全量测试（本工作树）：**1656 通过 / 0 失败 / 34 跳过**（多出的 1 个跳过是需 torch 的并行测试）；已安装 science-a 运行 `tests/pinn`：**1021 通过 / 0 失败**（原 994）。

### 干跑全链（不占盲测集）

真冒烟会永久占用盲测集，所以先在临时克隆（`%TEMP%\leo2211dry`，由脚本 `dry_setup.py` 从工作树未提交改动生成，在克隆内做临时提交 `e6d65a5` / `2069bde`）里各跑一遍完整产品链。放宽项只存在于该临时克隆：二维训练 200 步、验收阈值与复现容差放宽、Gate 5 判定强制通过（检查清单与数字保持真实）、Tier-1 维持阈值放宽、候选网格换成不在正式候选表里的网格（二维 D2C-GL22-CGL30 / D2C-GL24-CGL32，一维 GL544-CGL2004，一维仍用真实方法）。

| 链 | 结果 |
| --- | --- |
| 二维 | 准备 25 秒 → 主实验 → Tier-1 → 复现 → G6 → ACCEPTED，核验通过；重新核对四步通过；导出含证据说明书；无 torch 的 Python 核验 rc 0；导出包在 science-b 下的独立复现 rc 0、C_repro PASS；导出包前后不变；第二个任务正确跳过了第一个任务已预留的网格。第一次运行在最后因冒烟脚本的控制台打印（GBK 不能输出 ⁻）中断，与产品无关，修正脚本后整链重跑通过 |
| 一维 | 约 5 分钟到 COMPLETED / ACCEPTED；数值与历史一维一致（中位数 1.991e-4、复现 2.552e-4）；导出包复现第一次因输出目录已被二维干跑占用而被产品正确拒绝（`REPRODUCTION_OUTPUT_MUST_BE_NEW_AND_OUTSIDE_PACKAGE`），换新目录后 rc 0、C_repro PASS |

### 沙盒全链冒烟与盲测集登记

代码提交 `88f66e1`（工作分支）后，在两个干净克隆（`%TEMP%\leo2211s1`、`%TEMP%\leo2211s2`，`git clone --no-checkout` + 分离检出 `88f66e1`）里用真实方法各冒烟一次（用户已批准，各占 1 个盲测集），两条同时运行。确认在临时研究目录里自动通过，仅限沙盒。

| 项目 | 一维 | 二维 |
| --- | --- | --- |
| 预留网格 | **GL1120-CGL4008** | **D2C-GL42-CGL62**（5364 个检验点） |
| codeHash | `84ac5b8f…` | `84ac5b8f…` |
| 准备 | 30 秒 | 50 秒 |
| 运行（确认到完成） | 约 10.6 分钟（与二维同时跑） | 约 16.2 分钟（10 个种子并行，每个约 290 秒） |
| 结论 | ACCEPTED，C0–C2，六维全部 PASS | ACCEPTED，C0–C2，六维全部 PASS |
| 开发集中位数 / 复现中位数 | 1.991e-4 / 2.552e-4（与历史相同） | 3.686e-5 / 3.286e-5（主实验与历史二维校准完全相同：同样的种子、并行训练，逐位一致；差 4.0e-6，绝对 1e-4、相对 1.843e-5 两道限都在内） |
| 重新核对 / 导出 / 无 torch 核验 | 通过 / 含说明书 / rc 0 | 通过 / 含说明书 / rc 0 |
| 导出包独立复现（science-b） | rc 0，C_repro PASS，约 5 分钟 | rc 0，C_repro PASS（中位数与产品内复现相同），约 18 分钟（该工具逐个训练） |

- 登记：两份 claim 文件原样复制到 `experiments/poisson1d/problems/` 与 `experiments/poisson2d/problems/`，说明各写 `SMOKE_2_2_11_CLAIM_REGISTRATION_20260929.json`（脚本 `register2211.py`）；提交 `8a5670f`。登记后按安装目录计算：一维 **4 已用 / 28 剩余**（下一次 GL1152-CGL4010），二维 **1 已用 / 31 剩余**（下一次 D2C-GL44-CGL68）。登记后全量测试仍为 1656 / 0 / 34。
- 冒烟只检验产品链路，不是任何结论的证据，不与正式运行合并。
- 二维「预计约 N 分钟」按实测改为 17（`leo_shell/research_estimates.py`，身份之外，冒烟不作废）。

### Leo AI 2.2.11 发布

用户确认「已关闭」后，Claude 核对 Leo 进程数为 0 才部署（没有代关用户的窗口）。

| # | 操作 | 结果 |
| --- | --- | --- |
| 1 | 发布提交 `773980f`（实测估计 + README 验证记录）；`master` 快进 `0fd0532` → `773980f`（本地）；重算科研代码身份 | 111 个身份文件，codeHash `84ac5b8f…`，与两次冒烟、登记提交之前的 `88f66e1` 相同 |
| 2 | 本工作树建目录联接 `.venv`、`wheelhouse`、`wheelhouse-science` 指向主仓库；构建 `Documents\LeoAIStudio-deliveries\2.2.11\build-r1` | hermetic；回执绑定 `773980f`，dirty=False；包契约 328 / 36 / 37；EXE 版本 2.2.11，SHA-256 `e8afe4ba…` |
| 3 | 部署前对 `user/` 做摘要（154 个文件，`%TEMP%\leo2211deploy`）；桌面「Leo AI 2.1.lnk」哈希 `60349046…` | |
| 4 | 原位部署，快捷方式参数指向临时文件 | 成功；回滚目录 `.leo-rollback-20260929-043953-466c1b46`；桌面快捷方式前后哈希相同 |
| 5 | 技能 | 本轮 `skills/` 无改动（`git diff 0fd0532 773980f -- skills` 为空），不需要同步；严格校验确认三处一致 |
| 6 | 科学源码快照 `runtime/science-source-2.2.11-773980f`（`git clone --no-checkout` + 分离检出 `773980f`）；`research-runtime.json` 先备份到回滚目录 `upgrade-state-backup/runtime/`，再按字节只替换 `codeRoot`（CRLF 保持不变，其余字段不变） | 快照干净，HEAD = `773980f`；安装快照重算 codeHash = `84ac5b8f…`；2.2.10 及更早快照保留 |
| 7 | `build_manifest.py -o manifests/build-current.json`；`verify_release.py --strict`；`theme_asset_provenance.py --strict`；`science_environment.py` | **17 / 0 / 0**；15/15；无问题 |
| 8 | 用户数据对比 | 154 → 154 个文件，没有任何改动、删除或新增 |
| 9 | 启动 2.2.11；本地附注标签 `v2.2.11` → `773980f`；写入 `RELEASE_2_2_11_RECEIPT.json`（整份重新编写，排他创建，读回逐字段核对 17 个字段） | 进程 11664，窗口「Leo AI 2.1」，日志无错误，停在开始页等待进入；「上一安装版本」为 2.2.10 / `5a64e2d` |
| 10 | 删除本工作树的三个目录联接（`cmd /c rmdir`，只删联接本身） | 主仓库三个目标核对完好 |
| 11 | 未做 | 守护进程实测（等用户进入工作台并发测试消息）；没有推送到任何远端 |

- 回退方法：关闭应用，从 `.leo-rollback-20260929-043953-466c1b46` 恢复发布文件，把该目录 `upgrade-state-backup/runtime/research-runtime.json` 复制回 `runtime/`（`codeRoot` 回到 `science-source-2.2.10-5a64e2d`）。不要覆盖 `user/`。注意：回退后 2.2.10 看不到二维模板，但登记在代码库里的两个冒烟网格不影响它（2.2.10 的快照里没有这两份登记，一维额度会显示 3 已用；GL1120 已经被冒烟打开，若回退后再做一维正式准备，会抽到 GL1120——所以回退后应先把登记文件复制进 2.2.10 快照，或不要在回退版本上做正式准备）。

### 2.2.11 实机核对（用户手发消息 + 接口层只读核对）

用户进入 2.2.11 工作台，在「2.2.8 验收」（Smart）里按顺序发了 5 条测试消息，并展开「思考与步骤」目视检查。Claude 只读核对：守护进程时间线与消息（脚本 `live2211.py`，不打印令牌）、WSL 里守护进程数据库的 `permission_requests` 表（脚本 `perm_audit.py`，以只读方式打开）、上游源码。

| 消息 | 模型实际做法 | 审批记录（发起 → 处理） | 结论 |
| --- | --- | --- | --- |
| 1 numpy 版本 | Python 单元里 `host.bash("python -c '…' 2>&1; pip show numpy \| head -n 2")` | 12.0 秒，允许一次 | 命令带引号、分号、管道，不在只读白名单 → 弹卡片，用户确认是自己点的允许 |
| 2 当前目录文件 | 原生工具 `list_dir` | 无需审批 | 正常 |
| 3 Python 版本 | `host.bash("python --version 2>&1; python3 --version 2>&1")` | 2.8 秒，允许一次 | 同上，用户点的允许 |
| 4 直接调 bash 执行 pip list | 先 `search_capabilities`，然后回答「没有独立的 bash 工具，只能在 Python 单元里用 host.bash()」，没有执行 | — | 回答属实：上游 `tools/native.py` 的 `_NEVER_NATIVE = {"bash", "submit_output"}`，bash 永远不作为原生工具 |
| 5 df -h | `host.bash("df -h")` | **0.018 秒**，允许一次 | 命令完全匹配只读白名单 → **Leo 的 Smart 只读自动放行在真实使用中生效** |

- **绕路联网**：第 1–3 条本机问题都直接执行命令或列目录，没有一次 `web_fetch` / `web_search`。连同 2.2.10 那一次，4 个样本都没有联网（2.2.9 的同类请求有一次联网抓取失败和一次联网搜索）。样本仍少，不能断定是 `local-env-check` 技能起的作用。
- **更正一个旧认识**：2.2.8 / 2.2.9 的记录说「在内核代码里跑的命令上游从不审批，只读放行只有单元测试覆盖」，这只对了一半。上游确实不审批 Python 单元本身，但单元里的 `host.bash()` 会经上游的 `authorize_bash` 发起一次工具名为 `bash` 的审批请求，Leo 的只读放行接的正是这个请求，所以第 5 条被自动放行了。数据库里没有上游自动审阅（guardian）的评估记录，这几次放行不是上游自己批的。
- **模型原始思考**：接口读出 5 个回合中 4 个带思考（2、1、2、2 条），「Python 版本」一轮模型没有产生思考。用户目视确认「模型思考 · 原文，未经核实」显示正常。
- **测试对话移入回收站**（用户选择「现在移进回收站」）：先把 `user/entity-states.json` 备份到 `%TEMP%\leo2211deploy`，再用 Leo 自己的 `EntityStore.mark` 把「2.2.10 验收」（`f-6fd8a9f769c6`）和「2.2.8 验收」（`f-e1de46c0c7d3`）标记为 trashed（记录 9 → 11 条，修订号 9 → 11，原有 9 条逐条不变）。回收站里的彻底删除由用户自己操作。备份随临时目录一起删除。
- **清理**：`%TEMP%\leo2211dry`（干跑沙盒，约 269 MB）、`%TEMP%\leo2211s1`（一维冒烟，约 231 MB）、`%TEMP%\leo2211s2`（二维冒烟，约 250 MB）、`%TEMP%\leo2211deploy`（`user/` 摘要与回收站记录备份）、`%TEMP%\leo2211-build.log`；`%TEMP%\pytest-of-user` 下的 `pytest-6/7/8`（本轮 02:52–03:29 的测试）与 `pytest-current` 链接（`rmdir` 只删链接）；本工作树 8 个 `__pycache__`（均为本轮 02:37 之后产生，git 忽略）。第一次删除命令因路径含变量被安全检查拦下，一个都没删；改用完整路径后删除。安装快照 `science-source-2.2.11-773980f` 核对无缓存、工作树干净。会话临时目录里的脚本（`smoke2211.py`、`dry_setup.py`、`register2211.py`、`receipt2211.py`、`live2211.py`、`perm_audit.py` 等）保留备查。`manifests/build-current.json` 是 git 忽略的生成物，保留。

## 2026-09-29 · 用户 · 二维 Poisson 产品内正式运行（Leo AI 2.2.11）

用户按 Claude 给出的题目在已安装的 2.2.11 里新建科研任务，**本人点了「确认模型」与「确认正式运行」**。Claude 在运行期间只读监视（脚本 `watch_task.py` 每分钟读一次任务文件），没有点击任何确认，也没有停止或改动任务。结束后 Claude 只读核对任务记录，并用安装快照里的核验程序独立重做了一次证据核验。

| 项目 | 结果 |
| --- | --- |
| 任务 | `research-aece08ebc1004fbdb29d70c9e6646f30`，模板 `poisson2d-v1`，问题族 `poisson2d` |
| 盲测集 | **D2C-GL44-CGL68**（6292 个检验点）；准备时封存（12:06:28Z），主实验中打开一次（12:16:39Z） |
| 代码身份 | codeHash `84ac5b8f…`（与冒烟、发布、安装快照一致）；并行进程 10 |
| 时间 | 确认正式运行 12:07:41Z → 完成 12:32:30Z，约 **24.8 分钟**（上限 90 分钟）：主实验约 9.2 分钟、Tier-1 约 5.7 分钟、复现约 8.9 分钟 |
| 训练（开发集） | 10 / 10 达标，相对 L2 中位数 **3.686e-5**，最差 4.262e-5，发散 0 |
| 盲测集判据 | 每个种子所有 MUST 与 SHOULD 判据都满足；AC2D-1 最大 4.257e-5（验收线 1e-3）、AC2D-2 最大 7.007e-5、AC2D-9（8×8 分块局部误差）最大 1.540e-4（验收线 1e-3，余量约 6.5 倍） |
| Tier-1 | PASS，六个维度均维持 |
| 独立复现（环境 B、另一组种子） | 中位数 3.286e-5，与原结果相差 4.0e-6（绝对限 1e-4，相对限 1.843e-5），判定一致 → C_repro PASS |
| 结论 | **ACCEPTED，允许 C0–C2**，六维全部 PASS；C3 被阻断（需要其他独立完成的合格运行） |
| Claude 独立核验 | 安装快照 `science-source-2.2.11-773980f` + science-a 运行 `python -B -m pinn.research.worker verify --task-root <任务>`：rc 0，verified，ACCEPTED，C0–C2，codeHash 一致 |

- 数值与历史二维校准、2.2.11 冒烟完全相同（同一方法、同一组种子，训练是确定性的，结果逐位一致）；换的只是盲测集，这正是正式运行要检验的东西：在一个训练前封存、从未打开过的新检验点集上，同一方法仍然达到验收线。
- 用时比预计的 17 分钟长：每个种子的训练用时约 455 秒，冒烟时约 290 秒（当时还有一维冒烟在同时跑）。计算结果不受影响；变慢的原因从记录里看不出来（可能是机器当时的负载或电源 / 散热状态），没有下结论。「预计约 17 分钟」暂不修改，等再有一次实测再定。
- 安装快照里出现 8 个 `__pycache__`（12:05:53Z 生成，即用户点「准备」时）：这是产品 worker 运行时自己写的（它不带 `-B`），git 忽略，不进代码身份；Claude 没有动它们。
- 额度：二维 **2 已用 / 30 剩余**（D2C-GL42-CGL62 冒烟、D2C-GL44-CGL68 本次），下一次二维准备会抽到 D2C-GL46-CGL72；一维不变（4 / 28）。
- Claude 在核对时产生的临时文件 `%TEMP%\leo2211-verify.json` 已删除。

## 2026-09-29 · Claude · 3.0.0 更新准备：深度仓库卫生与整理

用户批准下一阶段为 **Leo AI 3.0.0**，要求深度仓库卫生与整理、删除一切能删除的，整理到满意后推送到公开仓库 `LeoLee0512/Leo-AI`。新分支 `claude/leo-3.0.0`（起点 master `add648b`）。

**只读普查**（三路并行，未改任何东西）：本地仓库无远端；38 个分支、12 个标签、6 个工作树；master 有 202 个提交的私有历史（2026-09-03 起），与公开仓库 `main`（7 个快照提交、停在 2.1.3 左右）不同源；公开仓库为 PUBLIC，当前账号有推送权限。文件树 1144 个文件、约 133 MB，其中历史研究证据约 95 MB。安全扫描：没有真实密钥；本机用户名在当前树 13 处、历史 72 个提交里出现；设备标识（MachineGuid）在 54 个文件里（几乎都在哈希绑定的运行记录中）；没有 LICENSE。

**用户决定**（四项均为推荐项）：删减力度「深度」（删无引用内容 + 只为历史证据存在的测试及其证据 + CHANGELOG 归档原文 + 含用户名的文件；不动科研身份文件）；推送方式「在远端 main 上加一个 3.0.0 快照提交」（普通推送，本地私有历史不上传）；公开版不带运行记录；本机杂物四类全部清理。

### 仓库整理（提交 `d342a53` 及其后续）

- 为确认哪些证据真的被需要，用只记录不改动的 pytest 插件在两个解释器下追踪每个测试实际打开的仓库文件（`trace_reads.py`）：排除扫描全树的 `test_portability` 后，保留的测试只读 16 个实验文件；8 个「只复核历史证据」的测试独占 766 个文件。追踪带来的一次线程时序失败在不追踪时不复现。
- 删除 **769 个文件、约 89.5 MB**（用户审批通过，均仍在本地私有历史中）：
  - `experiments/` 下的历史运行目录、诊断检查点、台账、复现包、试运行、驱动脚本与审计记录（环形域 318、一维 266、二维 130 个）；保留 **51** 个：产品运行时读取的盲测集登记（`runs/*/sets/claim.json`、`problems/*-claim-*.json`）、冒烟网格登记说明、预注册与协议、保留测试要读的少量记录、开始页引用的环形域 r3 可读记录（`TRUST_REPORT.md`、`RUN_SUMMARY.json`）。
  - 8 个只复核历史证据的测试（`test_g6_reproduction`、`test_poisson2d_reproduction`、`test_claim_pool_state`、`test_p11_and_portability_closure`、`test_annulus_stop_the_line`、`test_annulus_budget_schedule`、`test_annulus_r2_preparation`、`test_annulus_r3_preparation`），以及 `test_redteam_rules` 里只读历史记录的一个测试和它读的两份记录。
  - `docs/rollback/`（10，含本机用户名）、`docs/pinn-trust-loop/inbox/`（9）与两份合并笔记、团队提示词、乱码的 `P0_EXECUTION_STATUS.md` 等 10 份过时文档；`governance/` 的 3 份 PRELOCK 演练输出、合规审计（提到另一个私人项目）与旧 MVP 计划；`research_logs/`；`tests/` 里 4 个手动 Playwright 脚本、0 个测试的 `test_package_contract.py`、预览夹具；`tools/theme_shots.ps1`；`manifests/source-export.json`；已退役的狮子原图 `assets/logos/leo-lion-warm.source.png`。
- `CHANGELOG.md`：删除「原文附录」下的 47 份历史原文（R001–R047，约 1.29 MB），标题保留并写明原文在提交 `add648b` 及更早的历史里；补做脱敏（4 处 `pytest-of-<本机用户名>`、2 处设备标识）。1.47 MB → 0.18 MB。
- 随删除更新：可移植性豁免清单清空（它登记的 6 个文件都已删除），测试改为断言「树里没有任何个人绝对路径」；`test_logo` 不再要求已删的狮子原图；4 个环形域测试的说明文字不再指向已删脚本；新增 `docs/pinn-trust-loop/README.md` 说明原始记录去向。历史报告与预注册原文不改（其中的相对链接可能指向已移出的记录）；`.gitattributes`、修正案、可信协议、`localized_error.py` 等科研身份文件里的残留提法不改（一改 codeHash 就变）。
- `README.md` 按 3.0.0 重写（产品定位、主要能力、源码布局、构建部署、验证、公开快照说明、来源与许可），不再逐版罗列；版本号 2.2.11 → **3.0.0**（`leo_shell/__init__.py`、关于页、README），同步 `workbench.html` 的资产来源哈希；`.gitignore` 删去已不存在的注入层打包规则并更正安装目录说明。
- 科研代码身份未变：111 个身份文件，codeHash 仍为 `84ac5b8f…`，不需要冒烟、不占盲测集。
- 测试：全量 **1591 通过 / 0 失败 / 34 跳过**；science-a `tests/pinn` **956 通过 / 0 失败**（少掉的都是随证据删除的历史复核测试）。

### 本机清理（用户审批通过）

脚本 `local_clean.py`（先演练列清单，再执行；可重复运行）。工作树里的 `.venv` 等链接先按链接单独拆除，确认没有顺着链接删到主仓库。

| 类别 | 内容 | 大小 |
| --- | --- | --- |
| 安装目录旧回滚 | 8 个 `.leo-rollback-*`（09-28 09:24 → 09-29 01:43）；保留最新的 `.leo-rollback-20260929-043953-466c1b46` | 550 MB |
| 旧科学快照 | `science-source-` 2.1.4 / 2.1.5 / 2.1.6 / 2.2.6 / 2.2.7 / 2.2.8 / 2.2.9 / current；保留 2.2.10 与 2.2.11（当前 `codeRoot`） | 1741 MB |
| 旧工作树 | `leo-ai-2-2-9-continue-bc3f8f`、`leo-2-2-6-research-loop-b297ec`、`read-and-discuss-b3e681`、Codex 的 `trusted-research`（含 721 MB 构建产物）；另删空的遗留目录 `changelog-review-91e1c6` | 1118 MB |
| 旧交付物 | `Documents\LeoAIStudio-deliveries` 的 2.1.4–2.2.9 与 `current-desktop-548a068`；保留 2.2.10、2.2.11 | 706 MB |
| 临时文件与缓存 | `%TEMP%` 的 `leo-astra-preinject-r2-20260922`（187 MB）、旧构建 / 部署日志、空目录；主仓库 20 个 `__pycache__` 与 `.pytest_cache`；`.git` 里中断操作留下的 3 MB `tmp_pack` | 195 MB |
| 分支 | 37 个（23 个已合并、14 个未合并）；只留 `master`、`claude/leo-3.0.0`、主仓库所在的 `sync/github-20260928-548a068`；12 个标签全部保留 | — |

- 合计约 **4.4 GB**。核对：主仓库 `.venv`（5680 个文件，Python 3.12.9 正常）、`wheelhouse`（21）、`wheelhouse-science`（18）完好；工作树只剩主仓库与当前工作树；`.git` 无垃圾。
- 第一次执行在删除第一个旧工作树时因「目录被另一个程序占用」中断（此前的回滚与快照已删完）；脚本改为记录并跳过被占用的空目录后重跑完成。遗留：`leo-ai-2-2-9-continue-bc3f8f`、`leo-2-2-6-research-loop-b297ec` 两个**空目录**仍被此前的会话占用，已从 git 注销，等那些会话关闭后可删；Codex 的工作树 git 因路径过长未能删除，由脚本改用 Python 删净，只留下 Codex 自己的 0 字节记录文件 `.codex-worktree-name`（未动）。
- 未动：环境 B、当前安装、leotree 与 leotree-new、`openai4s` 安装包、`%TEMP%` 里的 leotree 压缩包与 `LeoLee0512-*.url`（不属于 Leo AI）。

### 公开快照准备（尚未推送）

- 发布前扫描发现两份研究报告（`POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md`、`POISSON2D_CALIBRATION_REPORT_20260916.md`）正文里有设备标识与安装前缀：替换为占位符（`win-<machine-guid>`、`prefix-<env-A>` 等，共 5 处）并在文末注明，其余不改（提交 `5adbebc`；两份报告的哈希只出现在本文件「合并来源」历史表里，不做校验）。此后整个仓库只剩二维校准运行的 `identity.json` 带设备标识，它只供本地测试，不进公开快照。
- 用户决定（2026-09-29）：**不声明开源许可，保留所有权利**（README 写明公开仅供查看）；公开提交作者用 **Leo Lee + GitHub 匿名邮箱**；桌面入口与窗口名改为 **「Leo AI 3.0」**（`leo_shell/__init__.py` 的 `DISPLAY_NAME`、工作台页面标题与关于页，同步 `workbench.html` 资产来源哈希；不在科研代码身份里，codeHash 不变）；远端多余分支 `claude/peaceful-fermi-nl17gw` 推送时删除。已安装的 2.2.11 与桌面快捷方式「Leo AI 2.1.lnk」本轮不动，等真正发布 3.0.0 安装版时再换。
- 公开快照由脚本 `export_public.py` 从已提交的 HEAD 生成：去掉 `experiments/**/runs/` 下除盲测集 `sets/claim.json` 以外的运行记录（4 份：环形域 r3 运行摘要、二维校准的 `identity.json`、`gate5b_external.json`、`claim_gate_decision_g6_p11.json`），其余原样；再逐文件扫描本机用户名、设备标识、安装前缀、用户邮箱、GitHub 令牌、API 密钥、私钥，结果 **0**。快照 372 个文件、约 42 MB。
- 在公开仓库的临时克隆（`%TEMP%\leo300pub`，基于远端 `main` 的 `4451fc5`）里用快照替换工作区并暂存：相对远端新增 49、删除 80、修改 40 个文件；等用户确认满意后再提交并推送（普通推送，不改写远端已有的 7 个提交）。
- 测试（显示名修改后）：全量 1591 通过 / 0 失败 / 34 跳过；science-a `tests/pinn` 956 通过 / 0 失败。

## 原文附录

3.0.0 整理（2026-09-29，用户审批通过）：此处原先收录的 47 份历史原文（旧修改日志 R001 与归档报告 R002–R047，以及其中的历史附录）已从文件树删除。它们仍完整保存在本地私有 Git 历史里：在提交 `add648b` 或更早的任意提交中，`CHANGELOG.md` 末尾即是原文。仍在磁盘上的报告（`docs/P0_FINAL_CLOSURE_REPORT.md`、`docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`、`docs/P0_RELEASE_CANDIDATE.md` 等）照常由 `tools/report_archive.read_report` 读取。
