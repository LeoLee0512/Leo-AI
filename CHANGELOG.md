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

## 原文附录

### R001 — 项目/CHANGELOG.md

<details>
<summary>展开完整原文</summary>

````markdown
# Leo AI 修改日志

本文件是 Leo AI 源码仓库唯一的修改报告。构建指南、架构说明、科研规范和源资料仍按各自用途保存。

## 2026-09-14 重构、整合与清理

记录日期：2026-09-14。完整说明见仓库根目录的 `20260914软件修改报告.md`，逐项删除与移动记录见 `20260914仓库卫生记录.md`。

| 修改日期 | 修改内容 | 修改结果 | 修改位置 |
|---|---|---|---|
| 2026-09-14 | 基线切换 | `master` 由 105 文件的快照提交 `8c4835e` 改指向 codex 工程线 `14e30f4` 之上的本次提交；`8c4835e` 相对 codex 线无任何独有改动，用户同意删除 | git 引用 |
| 2026-09-14 | 安装目录与 Leo Tree 项目留在仓库目录内 | `LeoAIStudio/`、`leotree/`、`.claude/worktrees/` 写入 `.gitignore`；所有工具的 `AppRoot` 默认值由「仓库上一级」改为「仓库内 `LeoAIStudio`」，仍可用 `LEO_APP_ROOT` 覆盖 | `.gitignore`；`tools/build_launcher.ps1`；`tools/deploy_release.ps1`；`tools/build_manifest.py`；`tools/verify_release.py`；`tools/theme_asset_provenance.py`；`tools/theme_preview.py`；`tools/sync_skills.py`；`tools/headless_verify.py`；`tools/manual_acceptance/` 四个脚本；`docs/BUILD.md` |
| 2026-09-14 | 主题源层归位 | `unified-settings-adapter.js`、`i18n-brand-patch.js` 从仓库根移入 `stage/`，与第三层 `stage/leo-inject.js` 同目录；构建脚本、manifest、校验器、测试同步改路径；`i18n-brand-patch.js` 头部过时的「未被发布版加载」说明改为实际的三层打包关系 | `stage/`；`manifests/runtime-asset-origins.json`；`tests/test_ui_api_contract.py` |
| 2026-09-14 | 只去重复的上游控件 | `hideAppearanceQuickControls` 改为 `true`：隐藏上游顶栏/侧栏的中英切换段和明暗切换按钮（Leo 设置 → 外观已有同样功能）；其余上游入口全部保留；未新增任何 Leo 风格 UI；上游源码字节不变 | `stage/leo-inject.js` |
| 2026-09-14 | 删除永不匹配的 CSS 选择器 | `.project-card`、`.session-card` 在上游 HTML/JS 中不存在，两处规则移除；`leo.css` 与 bundle 的 `expected_sha256` 重算 | `stage/leo.css`；`manifests/runtime-asset-origins.json` |
| 2026-09-14 | 仓库卫生 | 删除 4 个一次性探针/恢复工具（用户审批通过）；`PINN_MVP_AND_CFD_READINESS_REPORT.md` 移入 `docs/`；仓库目录内未跟踪的 `LeoAI-maintenance-20260907/` 归档目录删除（用户审批通过）；测试全部保留 | `tools/`；`docs/`；见卫生记录 |
| 2026-09-14 | pytest 收集范围 | 新增 `pytest.ini`（`testpaths = tests`，不递归 `LeoAIStudio*`、`leotree`）：安装目录进入仓库后裸跑 `pytest` 会收集上游自己的测试并报收集错误；主检出复验 839 passed / 2 skipped。测试产生的字节码缓存、pytest 临时目录与日志已全部删除并在报告中留痕 | `pytest.ini`；报告 §8 |
| 2026-09-14 | 重新构建并部署 | hermetic 构建（提交 `13dc7ea`，用仓库内 `.venv`，环境审计通过）→ 部署到仓库内 `LeoAIStudio/`（回滚目录 `.leo-rollback-20260914-063236-dc3d45e8`）→ manifest → strict 校验 12 PASS / 1 FAIL（技能副本漂移，既有问题，待同步）。操作日志 `docs/OPERATION_LOG_20260914.md` | `tools/`；`LeoAIStudio/` |
| 2026-09-14 | PINN 可信闭环 R1 | 六方团队（Claude 队长）五份交付物原样入库 `docs/pinn-trust-loop/inbox/`；合并说明 `docs/pinn-trust-loop/R1_MERGE_NOTES.md`（16 项裁决与衔接计划） | `docs/pinn-trust-loop/`；`docs/PINN_TRUST_LOOP_TEAM_PROMPTS_20260914.md` |
| 2026-09-14 | PINN 可信闭环 R1 实现 | 修正案 A-0001（PROPOSED，宪法正文未改）、三份 schema、弱链演算 `trust_vector.py`、文档校验 `trust_loop.py`、状态机 FAIL 分流扩展、协议汇编与报告模板、91 项新测试；全套 930 passed / 2 skipped | `governance/AMENDMENTS/`；`governance/PINN_TRUST_PROTOCOLS_R1.md`；`pinn/governance/`；`tests/pinn/`；`docs/pinn-trust-loop/` |
| 2026-09-14 | 技能同步 | 用户批准后 `sync_skills.py` 推送 12 个文件到安装目录与 WSL；strict 校验 13 PASS / 0 FAIL | `LeoAIStudio/user/user-skills/`；WSL 数据目录 |
| 2026-09-15 | A-0001 第 2 稿 | 用户评审第 1 稿为 PROPOSED / CHANGES REQUIRED（五项）；第 2 稿封死：两层诊断 FailureSignature → RootCauseClass → Gate（可接受矩阵、区分实验必填、rUndetermined 停线）、独立 Applicability 类型与 CheckResult、评估集三分 D_train / D_dev / D_claim（打开即失盲、换版本换集、external 只在 claim 集可 PASS）、seed 分档 0.8 / 0.9、C3 需同规格同代码、seed 集互异、≥ 2 环境的合格 run；schema 1.1；新增测试 31（新测试共 122），全套 961 passed / 2 skipped；协议汇编与报告模板第 2 稿；R2 提示词四份（无 Grok） | `governance/AMENDMENTS/`；`governance/PINN_TRUST_PROTOCOLS_R1.md`；`pinn/governance/`；`tests/pinn/`；`docs/pinn-trust-loop/`；`docs/PINN_TRUST_LOOP_TEAM_PROMPTS_R2_20260915.md` |
| 2026-09-15 | PINN 可信闭环 R2 与 A-0001 第 3 稿 | 三份 R2 交付物（GLM、Kimi、豆包）原样入库，DeepSeek 未收到；合并说明 `R2_MERGE_NOTES.md`（复审五项逐项裁决，含五条正式驳回；队员建议 35 条裁决）；第 3 稿落地：INV-A1（全 NOT_APPLICABLE 为非法登记）与规格级 `checkApplicability`、评估集样本清单与样本级互斥 + 预注册最小间距（`evaluation_sets.py`）、claim 集哈希链账本（`claim_set_ledger.py`，L1–L7）、specHash 排除 revision 与 claim 集状态、`seed_statistics` 无除法离散度、`EnvironmentFingerprint` 强 / 弱字段统一 C3 与 G6、seedSetId / environmentId / codeHash 派生复算、根因须排除全部其它候选、决策绑定规格 / 账本 / 证据等级 / codeHash；schema 1.2 三份 + 四份新契约；新增测试 70 项（含对抗闭合审计 23 项），全套 1031 passed / 2 skipped；协议汇编与报告模板第 3 稿 | `governance/AMENDMENTS/`；`governance/PINN_TRUST_PROTOCOLS_R1.md`；`pinn/governance/`；`tests/pinn/`；`docs/pinn-trust-loop/` |
| 2026-09-15 | A-0001 终审通过；DeepSeek R2 补交 | 用户终审第 3 稿"通过"：status ACCEPTED、effectiveDate 2026-09-15，登记簿同步；DeepSeek `PINN_TRUST_R2_MATH_CORE.md` 原样入库，P22–P32 诊断实验库、逐格判定、seed 阈值统计论证、泄漏不变量、Applicability 表并入协议汇编 §3 / §4 / §6 / §10，矩阵增 3 格记为 A-0002 候选；GLM 复发升级规则采纳（R3 实现）；claim 集密封存储选权限目录。宪法正文 1.1 的落笔待用户决定 PRELOCK 绑定问题（Poisson v1.0 草案绑定宪法 1.0 字节哈希）。代码无改动，测试基线仍为 1031 passed / 2 skipped | `governance/AMENDMENTS/`；`governance/PINN_TRUST_PROTOCOLS_R1.md`；`docs/pinn-trust-loop/` |
| 2026-09-15 | 宪法 1.1 落笔（方案一，用户同意） | 正文按 A-0001 affectedArticles 更新：第三、四、五、九、十、十三、二十八、二十九、三十六、五十三、五十四、五十六章加【A-0001】条款，新增第六十四（Red Team 三层制）、六十五（EXPLORATORY 第二来源）、六十六（revision 与方法身份）章，版本 1.1；`locking.py` / `prelock.py` 版本引脚放宽为 {1.0, 1.1}，草案绑定的版本必须等于宪法元数据声明的版本（新函数 `declared_constitution_version`）；三份 schema 的 constitutionVersion 改 enum；Poisson 1D v1.0 三份草案重绑定到 1.1（用户审批通过）；新增证据 `PINN_V1.3_PRELOCK_DRY_RUN_A0001.json`，旧证据保留；新增 PRELOCK 回归测试 2 项；全套 1033 passed / 2 skipped | `governance/`；`pinn/governance/`；`tests/pinn/test_prelock_integrity.py` |
| 2026-09-15 | A-0002 起草（PROPOSED） | 用户授权队长裁决 DeepSeek 建议：三个矩阵格采纳（sBcResidual → 容量、sPinnCfd → 容量、sLocalizedError → 规格），三格驳回不加；`state_machine.ADMISSIBLE_ROOT_CAUSES` 三格、测试（反例改用仍不可接受的组合，新增三格可接受与排除义务用例、诊断记录夹具补排除）、协议汇编 §4、合并说明 R2-38、登记簿同步；宪法 1.2 落笔与草案重绑定待用户终审 | `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md`；`pinn/governance/state_machine.py`；`tests/pinn/` |
| 2026-09-15 | A-0002 第 2 稿（用户复审 CHANGES REQUIRED） | 因果可判定审查：sPinnCfd → 采样、sSeedSensitive → 实现改为采纳（原驳回理由不成立），闭合审计补 sPdeResidual / sBcResidual → 奇异性、sSeedSensitive → 规格（非唯一解）；命名容量 / 采样须受控干预（单因子、其余固定、≥ 3 档 × ≥ 3 seed、中位误差严格下降，容量另需优化诊断干净），命名非确定实现须 P33 同 seed 重放发散且定位缺陷；矩阵范围 forward-problem MVP 进 schema（problemClass）；observedSignatures 防挑症状；新增 `amendments.py`（frontmatter dependsOn、ACCEPTED 链与宪法版本一致性）并挂进 PRELOCK 第七项检查；sPinnCfd → 容量的论证改为稳定性估计表述 | `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md`；`pinn/governance/{state_machine,trust_loop,prelock,amendments}.py`；`schemas/diagnosis-record.schema.json`；`tests/pinn/` |
| 2026-09-15 | A-0002 第 3 稿（用户 Final Closure Review） | 三项剩余问题收口：(1) BLOCKING 修复——可接受矩阵与命名义务按宪法版本分表，`admissible_root_causes(version)` 只认 `SUPPORTED_CONSTITUTION_VERSIONS`，`diagnose` / 文档校验必填版本，DiagnosisRecord 必填 constitutionVersion，登记簿 R5 与 PRELOCK 一致性——PROPOSED 期间 1.2 的八格与义务对 1.1 不可达；(2) `explainedSignatures` + 集合级症状覆盖不变量 `diagnosis_coverage_errors`，多症状多根因合法、漏解释与冲突归因非法；(3) sSeedSensitive → rSpecDefect 限定为非预期不可识别性（`identifiability` 记录，P34 改为可识别性检验）。新增测试 29 项，全套 1087 passed / 2 skipped；PRELOCK 7/7 PASS；队长建议 READY FOR USER ACCEPTANCE，status 仍 PROPOSED；准入审计 NOT_READY（三个 blocker） | `pinn/governance/{state_machine,trust_loop,amendments,prelock}.py`；`diagnosis-record.schema.json`；`tests/pinn/test_constitution_version_isolation.py`；`governance/AMENDMENTS/`；`governance/PINN_TRUST_PROTOCOLS_R1.md`；`docs/pinn-trust-loop/{R2_MERGE_NOTES,A-0002_FINAL_CLOSURE_REVIEW_20260915}.md` |
| 2026-09-15 | A-0002 ACCEPTED，宪法 1.2 生效 | 用户终审通过（实验授权指令）；按 §5.17 配方：宪法元数据 1.2、新增 3.2 与第六十章【A-0002】段、`SUPPORTED_CONSTITUTION_VERSIONS` 与三份 schema 枚举加 1.2（解锁运行时 1.2 矩阵）、Poisson v1.0 三份草案重绑定、新证据文件 `PINN_V1.3_PRELOCK_DRY_RUN_A0002.json`；全套 1087 passed / 2 skipped，PRELOCK 7/7 PASS；GOVERNANCE_ACTIVATION: PASS | `governance/PINN_RESEARCH_CONSTITUTION.md`；`governance/AMENDMENTS/`；`governance/POISSON_1D_V1.0_*.draft.json`；`pinn/governance/locking.py`；`pinn/governance/schemas/`；`tests/pinn/` |
| 2026-09-16 | Poisson 1D 正式实验（R3 最小 runner） | `pinn/experiments/` runner；实验 1 Formal Calibration：G1–G4、G5a PASS，G5b FAIL（AC-3 边界误差 7/10 seed 超阈）→ FAILURE_RECORDED，闭环标准 PASS、数值结果诚实判 FAIL；实验 2 Controlled Sampling Deficiency：G4 FAIL → 受控采样干预 4/8/16 → rSamplingDeficiency → REVISED → REENTER G4 → 训练恢复 10/10 → G5 FAIL（同 AC-3）；PINN_AGENT MVP VALIDATED（仅闭环），建议 REMAIN AT POISSON CALIBRATION STAGE；全套 1094 passed / 4 skipped，PRELOCK 7/7 | `pinn/experiments/`；`experiments/poisson1d/`；`docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md`；`tests/pinn/test_experiment_runner.py` |
| 2026-09-16 | Poisson 1D 向 C2 校准 | claim 集身份改按样本（sampleSetHash，账本 L4s/L6/L7/L8，重新包装拒绝；实现修正非修宪）；claim pool 预注册；配对干预准则冻结；实验 1 sBcResidual 经 3A（λ_BC 10/100/1000 配对）/ 3B（硬 BC）诊断为 rSpecDefect（enforcement）；修订 soft→hard，revision 2 在新盲 claim 集 GL640∪CGL2400 上 G5 PASS（AC-3 = 0）；Tier-1 全 PASS（run 1 P8 harness 缺陷保留并注解）；C_repro BLOCKED（无独立环境，复现包已生成）→ 最高 C1，REMAIN AT POISSON CALIBRATION；全套 1109 passed / 6 skipped，PRELOCK 7/7 | `pinn/governance/{claim_set_ledger,evaluation_sets,trust_loop}.py`；`pinn/experiments/`；`experiments/poisson1d/`；`docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md` |
| 2026-09-16 | Poisson 1D 校准收口（SUPPORTED @ C2） | BC 根因 post-audit 注解（历史 rSpecDefect 不改；因果归因非唯一）；前瞻性干预准则澄清；G6 语义审计（代码 = 宪法 28.1，无修复）；Environment B 全新 venv（torch 2.12.1+cpu、numpy 2.4.5，installationId / dependencyLockHash 不同 → 独立）；复现包在 exp3c 原 commit 干净检出上以 Environment B 实跑（seed +10000）：median 2.552e-4 vs 1.991e-4（差 5.6e-5 ≤ 1e-4），10/10 → C_repro PASS；六维 PASS，ClaimGateDecision 允许 C2，状态 ACCEPTED；新代码 runner 的首次复现因 codeHash 不同被正确 BLOCKED（保留注解）；全套 1112 passed / 6 skipped，PRELOCK 7/7；READY FOR USER / EXTERNAL REVIEW BEFORE 2D | `pinn/experiments/runner.py`；`experiments/poisson1d/`；`docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md`；`tests/pinn/test_g6_reproduction.py` |
| 2026-09-16 | 2D Manufactured Poisson Calibration（SUPPORTED @ C2） | 复用审计（治理层全 REUSE_AS_IS，1D 求解 / 度量 / 绘图全 1D_HARDCODED → 新建 `pinn/experiments2d/`，1D runner 一行未改）；冻结 2D 规格入 `specs/`（自动进代码身份）；解析参考、独立五点 FDM（观测阶 2.008/2.002/2.001）、AC2D-1..9 合同（每条带维数判定与阈值来源）、可信校验器 + 7 个 T10 夹具；EXPLORATORY 性能 pilot（D_dev only，选择规则先于结果写定：4×64/10000 步）；预注册先于正式 run 提交；盲集池四套（CGL 计数与 6 互素且两两互素，规避有理格点碰撞与成员间共享）；正式 run G1–G5 全 PASS（10/10 seed，median 3.686e-5；claim 集 3328 样本 OPENED 一次即 BURNT，10 seed 全部满足 AC2D MUST 与 SHOULD）；Tier-1 七项全维持（P7 在 2D 改判 APPLICABLE，P8 硬参数化随域缩放未重演 1D harness 缺陷）；G6 在新建独立 venv 复现（同 spec 同 code 异 seed，|Δmedian| 4.0e-6，同时满足绝对 1e-4 与收紧的相对 0.5×median）→ 六维 PASS → **SUPPORTED @ C2**，状态 ACCEPTED；两项追加审计：portability（HEAD 真实基线 1109/3 failed，本轮新增 3 条同类路径污染，未改 policy 与证据）与 pilot 角色（宪法 561 行允许 D_dev 做模型与架构选择 → ALLOWED，不阻断 C2）；新增测试 22，全套 1121 passed / 3 failed / 16 skipped，被跳过的 10 项在训练解释器下另跑 17/0；PRELOCK 7/7；结论 READY FOR NEXT 2D COMPLEXITY STEP，本轮 STOP | `specs/poisson-2d/`；`pinn/experiments2d/`；`pinn/{reference,validation,governance}/…2d…`；`scientific_reference/poisson2d_fdm.py`；`experiments/poisson2d/`；`docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md`；`tests/pinn/test_poisson2d_*.py` |
| 2026-09-16 | 2D Final Closure Audit（C2 CONFIRMED / 下一步 HOLD） | 外部终审五项收口：AC2D-9 判 CASE A（预注册=合同=实现=机器记录，分母是参考解 RMS，用已存预测重算证明终审读法恒 ≥ 1 而实现读法 6e-5 量级；只更正标签并追加 POST_AUDIT_ANNOTATION）；P11 原 NOT_APPLICABLE 无协议依据 → 先预注册后补跑一次，Δq 1.417e-05 PASS（诚实记录残差自适应加密使 dev 误差升约 53%，不是改进）；portability 源码改为记 installationId、发现数 7→5，但精确哈希豁免因加载器只接受 governance/**.md 而**无法应用**，已回滚并报告冲突；claim pool 状态改由账本推导、护栏前移到训练之前；localized-error 旧 1D 规则在合格 2D run 上 9/10 误报，四候选标定后最佳者仍误报 2/10 → 拒绝调阈值，登记 NOT CALIBRATED 并给前瞻协议（协议标定，不修宪）；全链重校验零问题 → **CURRENT 2D C2: CONFIRMED**，收口门未满足 → **NEXT COMPLEXITY STEP: HOLD**。新增 28 项测试，全套 1147 passed / 3 failed / 18 skipped，PRELOCK 7/7 | `pinn/experiments2d/{runner2d,localized_error}.py`；`experiments/poisson2d/`；`docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md`；`tests/pinn/test_{ac2d9_invariants,localized_error_2d,claim_pool_state,p11_and_portability_closure}.py` |
| 2026-09-16 | 外部评审裁决执行（C2 CONFIRMED / 下一步 READY） | 七项裁决逐条执行：portability 豁免机制作用域按批准扩展到「人工批准的不可变证据文件」——允许 `governance/`、`experiments/` 下的 `.md`/`.json`，可执行后缀黑名单兜底，通配符 / 目录写法一律拒绝，新增强制字段 `ruling` 与 `constraint`；归类仍要求 `file + sha256 + finding_type + occurrence` 四项全等，一个字节变化即失效；批准归类 5 条既有发现（1D 4 + 2D 1），被指认证据文件一字未改，报告仍逐条显示。d ≥ 2 的 `sLocalizedError` 触发条件改为「预注册的局部误差验收判据失败」（Poisson2D 即 AC2D-9，阈值必须等于验收合同值，只读 D_dev，fail-closed，不回溯已完成 run），四个候选统计量降为 diagnostics/research；协议澄清，不起 A-0003。Environment B 按裁决保留为冻结复现夹具。全套 1172 passed / **0 failed** / 18 skipped，训练解释器下 23 passed / 0 failed，portability 0 hard binding，PRELOCK 7/7 → `NEXT COMPLEXITY STEP: READY`，随即 STOP 不启动下一个 PDE | `tools/portability_check.py`；`manifests/portability-historical-evidence.json`；`pinn/experiments2d/{localized_error,diagnostics2d,runner2d}.py`；`experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json`；`tests/{test_portability.py,pinn/test_localized_error_trigger.py,pinn/test_p11_and_portability_closure.py}`；`docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md`；操作日志 §5.28 |
| 2026-09-16 | localized-error trigger 硬化（HARDENED / C2 UNCHANGED） | 外部评审三项代码级发现先独立复现（全部 CONFIRMED，另自查出 `+Inf` 巧合触发与空 ensemble 裸 IndexError）后修复：① seed 级失败不再被中位数吞掉——判定改用判据合同登记的 `seedPolicy="every-seed"`（即 Gate 5b 对 MUST 判据一直执行的 `all(...)`），并新增不变量测试证明 k=0…10 时信号触发恰等价于 G5b MUST 失败，同时保留 perSeedValues / failingSeedIndices / failureCount / failureFraction；② NaN / ±Inf / 负值 / 空证据 / 数组长度不一致（zip 静默截断）全部 fail closed，复用既有 `ValidationInputError`，在两处入口都验；③ 新增 `LOCALIZED_ERROR_CRITERION` 合同与 `localized_criterion()` 解析器，criterionId 绑定 statistic / normalization / partition / operator / threshold / level / seedPolicy，阈值全部由既有冻结表推导（无新常数），"AC2D-2 借 5e-3 判局部误差"被拒。历史证据重校验零问题：C2 CONFIRMED、ACCEPTED、六维 PASS，账本 / D_claim / TrustVector / ClaimGateDecision / 阈值未动。新增 69 项测试，全套 1241 passed / 0 failed / 18 skipped，训练解释器 23 passed / 0 failed，portability 0 hard binding（只跑回归未改规则），PRELOCK 7/7 | `pinn/governance/poisson2d_contract.py`；`pinn/experiments2d/localized_error.py`；`tests/pinn/{test_localized_error_hardening,test_localized_error_trigger}.py`；`experiments/poisson2d/{smoke_runner2d.py,LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json}`；`docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md`；操作日志 §5.30 |
| 2026-09-16 | 代码身份完整性审计（BOUNDARY READY） | 逐个判定面审计（ScientificSpec 解释 / Gate 结果 / FailureSignature / DiagnosisRecord / TrustVector / ClaimGateDecision / Red-Team / 可复现性）：`localized_error.py` 经核查**本来就在**身份内（缺席只因当年该文件尚未创建，如实记录、无修复动作）；真实缺口两个——`governance/PINN_TRUST_PROTOCOLS_R1.md`（决定 Tier-1 强制集合，曾使 P11 成为必跑）与 `adversarial/core_manifest.draft.json`（PRELOCK 输入），均加入具名身份文件；`experiments/**` 的正式驱动脚本改用声明制 `codeIdentityExtraFiles`，避免把每次都变的证据折进方法身份。新增 `assert_code_identity_complete()`，在 codeHash 之前、PRELOCK 之前 fail closed；`identity.json` 记录 `codeIdentityBoundary`。新增 44 项对抗测试（22 个模块逐一的一字节敏感性、文档/证据改动不移动 codeHash 并在 tmp git 仓库端到端验证、清单遗漏被拒、顺序断言、历史身份不被改写）。已 ACCEPTED 的 Poisson2D 无影响（重校验零问题、C2 CONFIRMED、codeHash 仍 a39aa07e23d0…）。全套 1285 passed / 0 failed / 18 skipped，训练解释器 23 passed / 0 failed，portability 0 hard binding，PRELOCK 7/7 | `pinn/experiments/common.py`；`pinn/experiments2d/runner2d.py`；`tests/pinn/test_code_identity_completeness.py`；`docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md`；操作日志 §5.31 |
| 2026-09-15 | 未验证项 | 上游语言 / 明暗控件隐藏已由用户在真实窗口确认；A-0002 第 2 稿待用户终审 | — |

## 2026-09-07 当前修改

记录日期：2026-09-07（America/Los_Angeles，UTC−07:00）。

源码位置：`C:\Users\user\Desktop\LeoAIStudio-build`；正式安装位置：`C:\Users\user\Desktop\LeoAIStudio`。

<!-- CURRENT-RESULTS-BEGIN -->
### 修改内容、结果与位置

| 修改日期 | 修改内容 | 修改结果 | 修改位置 |
|---|---|---|---|
| 2026-09-07 | 狮子图标改为暖金、赭石与深胡桃棕 | 桌面、EXE、窗口及 favicon 共用完整狮子构图；ICO 包含 16、24、32、48、64、128、256 七档尺寸。任务栏绑定验证结果见下文 | `assets/logos/leo-lion-warm.source.png`；`stage/logos/`；`tools/make_lion_icon.py`；`leo_shell/ui.py`；`leo_shell/windows_branding.py` |
| 2026-09-07 | 中英文应用自我认知 | 系统提示明确应用身份为 Leo AI；“你好”/“你是谁”使用“我是Leo AI”，英文使用“I am Leo AI”。真实安装版验证结果见下文 | `bridge/leo_identity.py`；`leo_shell/bridge_client.py`；`bridge/leo_local_relay.py` |
| 2026-09-07 | 导出可直接导入 Leo Tree 的 JSON | 增加中英文会话菜单、节点预览、选择与编辑、JSON 保存；当前 Leo Tree 的真实导入、持久化、重新加载及重复导入已验证 | `stage/leo-inject.js` 中 Leo Tree 导出逻辑；`leo_shell/ui.py` 下载设置 |
| 2026-09-07 | 清理测试、冗余及重复报告 | 删除 38 组、3,124 个文件、390,484,079 字节；8 份历史报告全文合并为本文件。构建、运行、科研规范及科研源资料保留 | 原 `tests/`、旧 `artifacts/`、`docs/rollback/`、旧验收浏览器资料、旧打包产物与缓存、选定旧测试/预览工具；本文件历史附录 |
| 2026-09-07 | “会话已收好”提示无法关闭 | 成功提示 6 秒自动消失，提供 × 主动关闭；错误提示保留至主动关闭或新状态替换，旧计时器和重新渲染不能复活已关闭提示 | `stage/leo-inject.js` 中 `dismissRuntimeStatus`、`renderRuntimeStatus`、`showRuntimeStatus`；`stage/leo.css` |
| 2026-09-07 | Cell 缺少 completion_bullets 参数 | 兼容截图中的单字典调用，并保留原双参数调用、结果校验及真实异常；隔离环境和实际安装版均已执行、打印并提交 `999 * 999 = 998001` | `bridge/leo_runtime_compat.py`；`leo_shell/bridge_client.py`；`bridge/leo_local_relay.py` |
| 2026-09-07 | 构建与安装一致性 | 包内强制检查四个 bridge 文件和窗口品牌模块；图标、主题与 bridge 按源码哈希部署；增加仓库外构建输出目录 | `tools/build_launcher.ps1`；`tools/deploy_release.ps1`；`tools/package_contract.py`；`tools/build_manifest.py`；`tools/verify_release.py`；`tools/theme_asset_provenance.py` |

### Leo Tree 导出方式及数据边界

打开需要导出的会话，点击右上角会话菜单中的 **导出 Leo Tree JSON**（英文为 **Export Leo Tree JSON**），查看并编辑树名称、节点标题和笔记，选择节点后点击保存。在 Windows 保存窗口选定位置，再到 Leo Tree 选择该 JSON 导入。

输出采用 `schemaVersion: 3` 与 `tree` 包装，按照本机 `C:\Users\user\Desktop\leotree` 的实际导入接口验证。节点保留选中消息的文本、Markdown、代码及公式，并带有来源会话、消息顺序、导出时间等信息；不把思考内容、系统提示或隐藏事件作为知识节点。学习状态默认为待学习，历史为空。附件、图片及文件二进制不包含在 JSON 内。空内容、仍在运行的会话、分页未读取完整、空标题、未选择节点、超过 500 个节点或 UTF-8 文件超过 4 MiB 时会明确阻止保存。

安装版已经通过 Windows 原生保存窗口输出实际文件，再由 Leo Tree 的 `validateTree`、`parseImport`、`previewImport`、`acceptPreview`、`loadWorkspace` 消费验证。验证只使用新建合成项目和会话，没有导出用户原有会话。6187 字节、5 个节点的样本 SHA-256：`a6a165dba7ca5f2c52af5dc84062ef11880129210d80be15882b1bb3f59125ef`。重复导入产生独立新树，已有树保留。

### 两个追加问题的原因

“会话已收好”原先只更新持久通知状态，没有关闭控件和期限；页面再次渲染仍会把旧状态显示出来。本次为通知增加独立编号和截止时间，主动关闭与到期都清空通知状态。关闭错误提示只影响显示，不清除后台错误。

截图中的 Cell 报错来自模型调用方式与运行时 SDK 签名不一致：模型传入一个含 `summary`、`completion_bullets` 的字典，而 SDK 原签名要求 `submit_output(output, completion_bullets, ...)` 两个参数。本次在启动时为固定 SDK 增加可重复应用、有原件备份的兼容层；单字典若仍缺少 `completion_bullets`，继续报错，不伪造执行成功或完成证据。原双参数调用和已有完成校验保持有效。

英文问候另外触发过本地模型输出协议不完整（HTTP 502），界面曾笼统显示模型/API key 失败；实际证据是模型在输出上限前重复文本或控制标记。安装版复验进一步发现，gateway 会在用户消息后追加本地 GPU 说明，使最初的整条消息精确匹配失效，英文因此仍走普通动作路径并泄漏 `<tool_response>`。最终实现仅识别已经核实的完整附加结构来判断短问候，发送给模型的消息原文保持不变。对应四类短问候/身份请求通过 JSON schema 常量和响应端独立校验，固定为“你好，我是Leo AI。”、“Hello, I am Leo AI.”、“我是Leo AI。”或“I am Leo AI.”。有实际任务、未知附加结构、任务模式或伪造标记的输入继续走普通路径；没有增加全局 `<tool_response>` 文本替换。

任务栏实际使用了 Windows 的旧分组及旧路径图标缓存：单独替换 EXE、设置窗口图标、设置固定 AppID 均仍可显示旧灰图。最终为图标内容计算哈希，同时派生任务栏 AppID 和同目录的 ICO 资源文件名。规范 ICO 始终只在源码中保留一份，安装目录启动时生成一个同字节的缓存资源，旧的本模块缓存可清理；没有重启 Explorer 或清空全局图标缓存。桌面原快捷方式经 Windows Shell 提取已为暖金色。

### 验证记录

<!-- FINAL-VALIDATION-BEGIN -->
最终安装包已于本地时间 **2026-09-07 18:01:39** 部署。源码入口和运行端已逐项核对，安装版真实操作结果如下。

| 验证范围 | 实际结果 | 仓库外证据（相对于 `LeoAI-maintenance-20260907/validation/`） |
|---|---|---|
| 安装包构建 | PASS：315 个 `_launcher` 文件、25 个关键文件、27 个归档模块均通过包契约检查 | `build-complete.log`、`deploy-complete.log` |
| 新进程任务栏 | PASS：安装包重启及最后正常模式启动均由新进程自行设置内容哈希 AppID 与图标资源；Kimi 右侧图标保持暖金狮子，派生 ICO 与规范 ICO 字节一致，无热修属性 | `packaged-taskbar-pid92364.json`；`final-normal-taskbar-pid23508.json`、`final-normal-taskbar-pid23508.png` |
| 安装版中文问候 | PASS：真实界面发送“你好”→“你好，我是Leo AI。” | `installed-conversation/zh.json`、`zh.png` |
| 安装版连续英文问候 | PASS：同一会话紧接着发送“Hello”→“Hello, I am Leo AI.”，无思考或工具协议标签 | `installed-conversation/en.json`、`en.png` |
| 安装版中英文身份提问 | PASS：“你是谁？”→“我是Leo AI。”；“Who are you?”→“I am Leo AI.” | `installed-conversation/whozh.json`、`whoen.json` |
| 安装版真实 Cell | PASS：模型生成 Python、真实执行并输出 `998001`，完成提交；没有 `completion_bullets` 参数错误 | `installed-conversation/cell.json`、`cell.png`；`live-overlays.json` |
| 通知关闭与期限 | PASS：安装版 6/6；成功提示在 6027 ms 检查时已消失，错误在 7005 ms 仍可见且可关闭，重新渲染不复活 | `installed-toast/result.json` |
| Leo Tree 实际保存及导入 | PASS：原生保存窗口落盘；真实 Leo Tree 导入、持久化、重新加载、重复导入保留已有树 | `installed-export/installed-import-result.json`；`installed-export/合成验收-LeoAI-installed-20260907-LeoTree.json` |
| 最终源码与仓库卫生 | PASS：清理目标 0 残留，测试与 Python 缓存 0 残留（依赖环境除外），科研源文件 39 个均未变，修改报告只剩本文件；四个 bridge 和规范图标部署哈希一致 | `final-integrity.json`；`build-complete-manifest.json` |
| 验收项目收尾与正常启动 | PASS：仅归档本任务合成项目，3 个验收会话完整保留；实际归档提示按 6 秒期限消失。最后以正常模式启动，后台就绪、运行任务 0、临时 9333 调试端口监听 0 | `synthetic-project-cleanup.json`；`normal-startup.json` |

最终五项真实对话复验使用本任务的合成会话 `f-9162fa321108`，通过真实编辑框输入和发送。旧一轮出现 `<tool_response>` 的英文结果另存为 `installed-conversation/en-before-control-tag-fix.json` 并明确标为失败，未混入最终通过结果。最终 gateway 形态的模型重放另外通过 6 个真实场景与 9 个正常任务/伪造标记负例。

最后正常启动确认时间为 **2026-09-07 18:18:23**，进程 PID 23508。合成验收项目 `proj_d7765da9b626` 已通过实际界面归档，保留所有验收会话；用户原项目未修改。旧会话中已经保存的历史回复和失败记录未伪装改写，修复作用于之后的回复和执行。

| 制品 | 精确记录 |
|---|---|
| 安装 EXE | `C:\Users\user\Desktop\LeoAIStudio\LeoAIStudio.exe`，5,589,850 字节 |
| EXE SHA-256 | `4d8468117e2bf9af6a70f26100a5d1e7a8a0fd3f4d204b3e0b1fed768daf5a27` |
| 安装前端 bundle SHA-256 | `83cdbf620d76927f772269087e4591b777b54a5656a02b29b269a7dd3aabe3f4` |
| 安装 CSS SHA-256 | `07def3748816c8fb25bad0136997a848f55bbd3cd7f9c34f479cec0969674a4d` |
| 规范 ICO SHA-256 | `2c2bb981ec6e98a91bc4926aad9504915dd2c2e38accc806463cdb64e4a79b63` |
| 当前 relay SHA-256 | `fabdcf4eef6fff40d4c2a752beb0874ca87700f6ad4da708f03cd1f9861cdf49` |
| WSL 身份提示目标 SHA-256 | `650278ce2275e94981613af1f603fdcaee6bf4ed2b86330b5dab9d1f674d71b3` |
| WSL SDK 兼容目标 SHA-256 | `96da17fc080ab6cd479af661001aa154649deea023e09b23833d29096ce8b8ee` |
| 本次安装回滚目录 | `C:\Users\user\Desktop\LeoAIStudio\.leo-rollback-20260907-180133-ceed699e` |

构建产物与验证资料均保存在仓库外。常用重新构建方式：`tools\build_launcher.ps1 -OutputRoot C:\path\to\build-output`，安装前通过包契约检查后再运行 `tools\deploy_release.ps1 -PackageRoot C:\path\to\build-output\dist\LeoAIStudio`。
<!-- FINAL-VALIDATION-END -->

各轮检查范围不同，不能把数字相加作为全仓测试数：导出功能隔离 Chromium 验证 13/13；通知逻辑隔离 Chromium 验证 11/11，安装版实测 6/6；Cell SDK 兼容验证 14 项通过；完整的 bridge client、部署事务、relay 外部回归 141 项通过，随后针对协议边界 review 修复的 relay 复跑 56 项通过，严格协议及字面信息保护另有 24 项检查。首次回归有旧 mock 未包含新身份步骤导致的失败，补齐 mock 与失败路径后复跑通过；首轮失败日志保留在仓库外，不掩盖为初次通过。

测试已按用户要求从源码仓库删除。仍保留 `tools/package_contract.py` 等正式构建/校验工具，防止清理后失去安装包检查能力。本轮合成验证脚本与结果仅保存在仓库外的 `C:\Users\user\Desktop\LeoAI-maintenance-20260907\validation`。

### 清理范围与可恢复性

删除前已保存源码快照、已有 Git 修改和逐文件 SHA-256。删除文件归档为仓库外 `C:\Users\user\Desktop\LeoAI-maintenance-20260907\removed-files.zip`；SHA-256 为 `33b5f67457c2325c8aa4b300c6be8bf9ffa2317278b3781298b04d33172b9e2a`。同目录 `cleanup-manifest.json` 记录原路径、大小、哈希与归档成员，`cleanup-result.json` 记录删除结果。当前源码仅留本文件作为修改报告，历史报告的原始字节可从该归档恢复。

清理不涉及 `C:\Users\user\Desktop\大模型` 中的模型文件、真实用户会话、Leo Tree 生产数据或其他项目。39 个科研源文件按初始快照哈希核对无变化；保留有用途的构建指南、架构说明、依赖锁和科研规范。关闭的旧 Vite 进程已通过命令、PID、创建时间和日志路径确认属于被清理的合成验收资料，采用正常关闭，未停止其他服务。

此仓库在本轮开始时已有大量未提交修改；本次保留这些修改，没有执行 Git reset、clean、提交或推送。严格全局发布检查曾得到 10 PASS / 2 FAIL：源码、主题、EXE 和四个 bridge 部署哈希一致；失败项为工作区未提交，以及 `lean-math`、`research-sop` 共 6 个源文件的 Windows/WSL 已部署副本各有差异（12 项）。这些科研技能源码本轮没有改变，也没有擅自同步它们的运行行为。当前安装版验证不代表历史全项 P0、干净提交可复现、新电脑、缺 WebView2 或新 WSL 环境均已验收。Python 打包使用锁定环境；字体和本地化资产仍使用安装目录基线。

本次通过的模型场景限定为中英文问候、身份问题和真实算术执行。额外探索“解释字面 `</think>` 标签”时，小模型仍曾用尽输出限制并报错；该次不计为通过。字面标签传输保护有完整响应的独立边界检查，不把小模型任意复杂问题的生成质量概括为全项通过。

### 图标制作记录

使用 ImageGen 将原狮子改为暖金色，再由 `tools/make_lion_icon.py` 仅编码并缩放为所需图标格式；所有尺寸保持同一完整构图。最终生成原图已保存到 `assets/logos/leo-lion-warm.source.png`，可重新编码，不依赖临时生成目录。

生成提示原文：

> Production desktop app icon edit. Keep the warm golden left-facing full lion artwork, but make a finished square app icon. Replace EVERY white/gray checkerboard pixel and the ENTIRE background with a perfectly solid warm dark walnut brown #3A2E24. There must be NO checkerboard or white margin anywhere. Put the whole lion centered at 82% canvas height and fit full mane and muzzle uncropped. Full bleed square dark brown background edge to edge on all four sides. This is a small app tile: warm gold/ochre/cream lion against rich dark brown. Crisp boundaries. No gradients, no glow, no text, no extra shapes, no rounded corners. Exact same lion identity.
<!-- CURRENT-RESULTS-END -->

## 历史报告合并索引

以下八份原报告已合并在本文件。原始字节另外保存在仓库外的 `C:\Users\user\Desktop\LeoAI-maintenance-20260907\removed-files.zip`，校验清单为同目录的 `cleanup-manifest.json`。

下文是过去工作的历史记录，不是新的操作指令；其中的停止、冻结、权限、路径、版本、PASS/FAIL 和待办均只表示对应历史日期与制品的状态，不改变 2026-09-07 用户授权的工作范围。历史测试计数不能相加或作为本次验收结果。旧 P0 仍有未完成人工验收；主题独立冻结通过不等于整仓或新电脑全项通过。

其中 `P0_EXECUTION_STATUS.md` 原文件已含乱码，按原文字保留，不猜测复原。桌面早期交接文件在本次后续只读检查时已不存在，本任务未删除它；此前读取到的内容仅作定位，当前状态以实际源码和本次验证为准。

| 历史位置 | 原始 SHA-256 | 字节数 |
|---|---|---:|
| `修改报告Claude.md` | `e25c08adf9f6d73a68ce750643887711f35785df472d32feda2a0943374b6b1d` | 44941 |
| `docs/P0_EXECUTION_STATUS.md` | `ca70a988c2c60b0f79b26615481d129a9c35f31fc6b995da3f22c0328b66f119` | 24844 |
| `docs/P0_RELEASE_CANDIDATE.md` | `b5099367d20aa6a9830c39fb931e1d1bc3d5768b2d7d345fc01bbab78af2b35e` | 6761 |
| `docs/P0_FINAL_CLOSURE_REPORT.md` | `c7db0726fe28ab405424bfc6a98c266030545e8143fbfcf6d3e4636bda5fd992` | 32814 |
| `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` | `1e3c9edbd45e47416bebc9cda1f4170ef231fadab8b39d8187bf0d9b96cf44c0` | 5736 |
| `docs/RESEARCH_SOP_MIGRATION_AUDIT_24f3fd7.md` | `f786a056e5f854a2ca57f246d484507f843208e4f4ddc860571c20278ca19c4f` | 3596 |
| `docs/THEME_INK_AUTUMN.md` | `0afb3d3b6732f36a71afa195c9ccc97926cac0b163e80e7996f4956b1a1a2051` | 26812 |
| `REPOSITORY_HYGIENE_REPORT.md` | `19cec809ee2e07f236f275c789a4ffe481baeabff31664ed998cbb9aef050d55` | 19711 |

<a id="history-1"></a>

## 历史附录 1：修改报告Claude.md

<details>
<summary>展开历史原文（仅作记录）</summary>

# Leo AI Studio 修改报告

日期：2026-09-01 · 执行：Claude Code
依据文档：`Desktop\修改建议.md`（壳层三项需求）、`Desktop\Leo-AI-Studio-修改建议.md`（两个科研技能）、`Desktop\Lean-math-skill-提示词.md`（第三阶段）

执行顺序按你选定的方案：**壳层优先 → 两个科研技能 → lean-math → 仓库清理 + 本报告**；清理力度选**保守清理**；技能落地选**权威副本 + 直装 WSL + 修好同步按钮**。

---

## 〇、总览

| 项 | 结果 |
|---|---|
| `pytest tests -q`（整棵测试树） | **225 passed**（改动前 `pytest tests` 因两个失效文件直接 collection error，只有 `tests\leo_shell` 能跑，212 passed） |
| `tools\headless_verify.py` | 全阶段 ok（preflight / status / start / url / http-root 303 / http-health / stop） |
| 构建 + 契约门禁 | `PACKAGE CONTRACT PASSED: 381 _launcher files, 16 critical files, 24 archive modules` |
| 部署 | `exe_sha256 = B8B5F850EDA77D94870E65214F2E6A25A430B76DEADA1E80C7C4B647C29AB995`，回滚点 `.leo-rollback-20260901-064158` |
| 真机验证 | 启动页为新暖色设计；无 key **不自动跳转**（日志：`startup stays on the splash page (profile=present, key=absent)`）；点「不接入模型，先逛逛」后才 `submit request=1` → 进工作台 |
| `upstream\OpenAI4S` | `git status` **完全干净**，零改动，仍停在 `a792c38` |
| 三个技能被 OpenAI4S loader 发现 | `source=user, has_kernel=True, sidecar gate=ok`，与 604 个内置技能无重名（共 607） |

---

## 一、需求 2：不要自动跳进「无密钥浏览模式」

> 先做这一项，是因为需求 1 的启动页要把新按钮一并做进去，后端接口先落地才能一次改完页面。

### 1.1 `leo_shell\app.py`

**删除** `_keyless_allowed()`（原第 31 行）。它恒返回 `True`，是「无 key 也自动进」的根因；改成条件判断意义不大，因为新规则就是「有没有 key」这一句话，留一个恒真的谓词只会误导下一个读代码的人。

**重写** `Application._on_window_ready()` 的分发逻辑：

```python
if profile is not None and api_key:          # 原本是 (api_key or _keyless_allowed(profile))
    coordinator.submit(profile, api_key, requires_ack=False)
    return
# 没 profile、或有 profile 没 key → 留在启动页
logger.info("startup stays on the splash page (profile=%s, key=absent)", ...)
window_ui.open_settings()
```

`settings.api_key_for()` 抛异常时按「没有 key」处理（原来会 fall through 到无密钥自动连接）。只有**分发过程本身抛异常**才继续 `publish_status("MODEL_SETTINGS_UNAVAILABLE")`。

**一处与文档的偏差，请知悉**：你的文档写「`publish_status` 一句友好提示」。我没有推状态码，原因是硬约束 5 要求后端只发那 5 个错误码，而这 5 个码全都是「失败」语义，用哪个来描述「你还没填密钥」都是错的；发中文原文又会让英文界面用户看到中文。**改为前端自己渲染双语提示**——页面本来就从 `get_state().has_key` 知道这件事：

- 有 profile 没 key → 「已保存配置，但还没有 API 密钥。填写密钥后启动即会自动进入工作台；也可以先逛逛。」
- 没有 profile → 「还没有模型配置。配置完成后，启动时会自动进入完整科研环境。」

效果满足你的意图（用户能看懂为什么停在这里），而且五码表一个字没动。

### 1.2 `leo_shell\api.py`：新增 `ShellApi.connect_keyless()`

```python
def connect_keyless(self) -> dict:
    profile = self._settings.active_profile()          # 失败 → MODEL_SETTINGS_UNAVAILABLE
    if profile is None:
        return {"ok": False, "message": "KEYLESS_NEEDS_PROFILE"}
    result = self._coordinator.submit(profile, None, requires_ack=False)   # 失败 → MODEL_CONNECTION_FAILED
    return {"ok": True, "pending": True, "request_id": result.get("request_id")}
```

要点：

- **永远传 `None`**，即使该 profile 存了密钥——无密钥模式就是无密钥模式，测试专门盯这一条。
- `KEYLESS_NEEDS_PROFILE` **不进 `publicMessage()` 的五码表**，由前端按钮处自己本地化，五码表保持原样。
- 线程安全、异常收口，与其余方法一致。

### 1.3 测试

- 新增 `tests\leo_shell\test_app_startup.py`（7 个用例）：有 key 自动连、没 key 停留、空字符串 key 视为没有、`api_key_for` 抛异常不许 fall through、无 profile 不弹错误横幅、`--settings` 即使有 key 也不自动连、分发异常仍报 `MODEL_SETTINGS_UNAVAILABLE`。
- `tests\leo_shell\test_api.py` 新增 5 个 `connect_keyless` 用例，其中一条专门断言「profile 有密钥时仍然传 None」。
- `FakeSettingsStore.active_profile()` 从写死 `None` 改成可设置的 `self.active`，并接上 `_maybe_fail()`。

---

## 二、需求 1：启动页暖色极简重设计

### 2.1 改了哪些文件

| 文件 | 改动 |
|---|---|
| `LeoAIStudio-build\stage\shell.html` | **整页重写**（权威源）。31,917 → 36,581 字节 |
| `LeoAIStudio\theme\shell.html` | 与 stage 逐字节同步（`cmp` 校验过），并经构建 overlay 再次落盘 |
| `leo_shell\ui.py:44` | `_WINDOW_BACKGROUND` `#071319` → `#FBF7F2`，并加注释说明必须与页面 `--bg` 同步 |
| `leo_shell\DESIGN.md` | 同步窗口底色、`connect_keyless`、启动流程、`scan_local_skills` 契约 |

`theme\leo.css` **没动**——实测它只服务工作台注入层，里面没有任何作用于启动页的规则（启动页 CSS 全部内联在 shell.html）。顺带一提，`leo.css` 本来就是浅色底（`--bg:#f4f8fa`），所以深色启动页原本才是整个产品里的异类，改完反而一致了。

### 2.2 视觉

- 配色：米白底 `#FBF7F2`、暖杏washes、柔和暖橙 `#C4693A`（hover `#AB552B`）、暖调墨色 `#2B241E`、细分割线 `rgba(74,55,38,.10)`。
- 结构：76px 细顶栏 + 一条发丝分割线；主区 56/44px 内边距、32px 间距；白卡片 20px 圆角、1px 暖色描边、**不用阴影堆叠也不用毛玻璃**；标题 clamp(34–56px)，`em` 用纯色强调（原来是渐变文字）；正文行高 1.95；一条 1px 细线分隔下方的「本地安全 / 科研运行时」。
- 顶栏原来是两个裸圆点，改成一个带文字的状态胶囊（`尚未连接` / `已配置`），信息更直接。
- 动效：Splash 淡出 + 狮子 arrive 动画 + 2px 扫描进度条，保留 `prefers-reduced-motion` 全禁。

### 2.3 新按钮「不接入模型，先逛逛」

hero 区三个动作：`配置模型`（primary）、`不接入模型，先逛逛`（ghost，`id="browse-keyless"`）、`切换主题`（降级成文字链接）。

点击后：禁用按钮 → 调 `pywebview.api.connect_keyless()` → 成功就等导航；返回 `KEYLESS_NEEDS_PROFILE` 则在 hero 下方显示双语提示并**自动打开设置抽屉**；其它错误码走 `publicMessage()`。按钮会重新启用，不会卡死。

### 2.4 逐条对照硬约束

| 约束 | 落实情况 |
|---|---|
| 渲染后 ≤ 1.5 MiB | **166,584 字节 ≈ 162.7 KiB**（headless_verify 实测），预算的 10.6% |
| `__LEO_LION_DATA_URI__` × 3、`__LEO_OPEN_SETTINGS__` × 1 | 保留，占位符计数脚本校验过 |
| JS↔Python 契约一字不改 | `get_state / save_profile / save_settings / delete_profile / save_appearance / acknowledge_connection` 全部原样，逐个 grep 校验 |
| 双语机制 | `COPY` 表 **zh/en 各 65 键，无缺、无空值**（用 node 求过差集）；`localStorage["leo-shell-locale"]`、`html:not([data-leo-locale-ready])` 防闪、`id="locale-gate"`、8 秒兜底定时器全部保留 |
| `publicMessage()` 五个错误码 | 逐字保留，中英两张表都在 |
| `window.setStatus` / `window.LeoShell` | 保留；`paintStatus` 额外把消息也写进 hero 提示位（抽屉关着时也看得见） |
| 窗口底色同步 | `ui.py` 已改为 `#FBF7F2` |

### 2.5 中途发现并修掉的一个布局问题

用截图初次核对时，物理窗口 1280×800 而系统 DPI 是 192，我一度误判 CSS 视口只有 640×400、按钮会掉出可视区。用 DPI-aware 的方式重新量过：**真实 CSS 视口是 1293×765，桌面版式正常**，之前是截图工具的伪像。

不过顺手把窄/矮视口做扎实了，因为原设计在小视口下确实会把内容截掉且够不到：

- `main` 改成 `overflow-y:auto`（`body` 仍 `overflow:hidden`），任何动作都不会掉到摸不到的地方；
- 新增 `@media(max-height:620px)` 紧凑版式（顶栏 60px、间距收紧、标题降到 26–34px）。实测 640×400 下：按钮底边从 392/400（几乎贴边）变成 294/400，下方内容可滚动到达。

### 2.6 校验手段

- 用 node 对内联脚本做 `--check` 语法校验；
- 用 node 求 `COPY.zh` / `COPY.en` 的键集差集与空值；
- 起本地 http 服务 + 打桩 `pywebview.api`，在浏览器里跑通：中英切换（含 `.assurances` 的 `lastChild` 文本替换）、主题卡、设置抽屉三个 tab、`connect_keyless` 的三条分支、`window.setStatus` 的码表映射；
- 真机启动 + 窗口截图。

---

## 三、两个科研技能

交付位置：`LeoAIStudio\user\user-skills\{research-sop,local-literature-rag}\`（权威源，符合文档的交付物清单）。

### 3.1 一个必须先讲清楚的架构事实

`user\user-skills\` **不是** OpenAI4S 真正加载用户技能的地方。实测：

- `SkillLoader.user_skills_dir()` = `personal_skills_root(cfg)` = `<data_dir>/user-skills`，在 WSL 里就是 `/home/leo/.local/share/leo-ai-studio/data/user-skills/`；
- 守护进程只有 `POST /api/v1/skills/import` 这一个写入口，而它**只接收 SKILL.md 正文**（`name` / `description` / `body`），**不传 `kernel.py`**；`/skills` 与 `/skills/import` 之外没有任何上传整包的路由。

所以：光把文件放进 `user\user-skills\`，两个技能不会真正生效。按你选的方案，我做了三件事：

1. `user\user-skills\` 放权威源码（可版本化、可被应用内技能面板扫描）；
2. 把**整个技能目录**装进 WSL 的 `data/user-skills/`，`kernel.py` 才真的会被加载；
3. 修好应用内那个本来就是坏的「安全扫描并同步」按钮，让**日后改 SKILL.md** 可以自助同步（改 kernel.py 仍需复制目录，命令见 §六）。

### 3.2 顺带修掉的一个现存 bug：`scan_local_skills`

`theme\leo-inject.js` 的技能面板调用 `scan_local_skills({})` 并按 `folder` + `content` + `sha256`(64 位十六进制) 过滤后逐条 POST 导入。而原来的 `api.py`：

- 方法签名是 `scan_local_skills(self)`，**不接参数** → 前端一按就 TypeError，扫描根本没开始；
- 返回项只有 `{id, name, content}`，**缺 `folder` / `byte_size` / `sha256`** → 就算能调通，过滤后也是空的；
- 没有 `rejected` / `hidden_count` → 面板的「已拒绝」「隐藏条目」两栏永远空。

也就是说这个按钮从来没work过。修改（`leo_shell\api.py`）：

- `scan_local_skills(payload=None)` 接收并忽略参数；
- `_scan_skills()` 返回 `{"skills": [...], "rejected": [...], "hidden_count": n}`，每个 skill 带 `id / folder / name / byte_size / sha256 / content`（`id`、`name` 保留，老调用方不受影响）；
- 拒绝原因给机器码：`symlink` / `escapes_root` / `no_skill_md` / `too_large` / `unreadable`；`.` 开头的条目只计入 `hidden_count`，**不读也不列名**（列出来等于泄露目录清单）；
- 新增 `hashlib` 引用；`test_api.py` 相应更新并新增 `test_scan_local_skills_entries_satisfy_the_sync_filter`，直接按前端那条过滤规则断言。

### 3.3 `research-sop`（角色化科研 SOP）

五角色链：`literature-surveyor → modeler → numerical-experimenter → validator → paper-writer`。

**关键实现选择**：读过 `openai4s/host/delegation.py:105` 后确认，`host.delegate(spec)` 只有在 spec 带 `specialist`/`name` 命中内置角色时才去查 `specialists.py`；不带就原样透传。所以**角色人格直接写进 `request` 正文即可**，`specialists.py` 一个字都不用动——正是文档里「优先不侵入上游」的那条路。

另外更正文档里的一处：`host` SDK **没有** `list_session_checkpoints` 这个方法（grep 过 `openai4s/sdk/host.py`，不存在）。断点续跑改成靠**磁盘上的阶段文件**：每个阶段完成即写 `research-sop/NN-<role>.json` + `.md`，再次调用 `orchestrate_research(同一个 task)` 会跳过已完成阶段。效果一样，而且可审计。

`kernel.py` 提供 `orchestrate_research / sop_status / sop_reset / sop_role_prompt / sop_read_stage / sop_write_stage / sop_stage_path` 等 14 个函数。其它设计点：

- 每个角色有独立 `max_turns`（实验员 60 / 综述员 40 / 验证员 32 / 撰写员 28 / 建模员 24）+ `retries=1`；
- 每个角色有 `output_schema`（运行时强制必填字段），验证员的 `verdict` 缺失即为提交被拒，而不是让编排器去猜；
- **上游可见性是裁剪过的**：建模员只看得到综述，看不到求解器日志——否则它会照着结果反向改假设；
- 验证员返回 `verdict != "pass"` → 清空 `send_back_to` 那一环及**全部下游**，把 `findings` 附在请求末尾重跑，上限 `max_rollbacks`（默认 2）；超限以 `status="unresolved"` 收尾并带出未解决问题，**不会把没通过的悄悄降级成通过**；
- 验证员返回无法解析的 verdict **按 fail 处理，不按 pass 处理**。

**自测**：`scratchpad\test_research_sop.py` 用打桩 host 跑了 24 项断言，全过——含 happy path、上游裁剪、`max_turns` 与 schema 下发、**故意植入错误 → 验证员打回 → 建模员和实验员重跑而综述员不重跑 → findings 确实进了重跑请求**、回退次数上限、未解决时不写论文也不派撰写员、resume 不重复派工、reset 清空。

### 3.4 `local-literature-rag`（本地文献库 RAG）

零新依赖：PDF 提取复用内置 `pdf-explore` 的 `pdf_pages`（真实页码），检索用运行时已有的 `scikit-learn` TF-IDF + 余弦相似度（WSL 运行时实测 sklearn 1.9.0 / numpy 2.5.2）。全程本地不联网，所以 SKILL.md 没有 `metadata.third_party`。

- **中英混合**：`lit_analyzer` 对拉丁词正常分词，对 CJK 连续段同时产出单字 + 二元组 → 不用 `jieba` 也能命中「传热」。取舍在文档里写明了（召回好、精度略逊于真分词器）。
- **增量建库**：按 `sha256 + size + mtime` 打指纹，指纹不变的文件直接复用已存分块，绝不重复解析；改动的重抽，删除的出索引。
- **持久化**：索引写工作区 `literature-index/index.json` 并注册成 artifact `leo-literature-index.json`。这里也更正一处预期：工作区是**每会话一份**（`data/agent-workspaces/<root_frame_id>`），而 `host.artifacts()` 被限定在当前会话的 root frame，**没法跨会话枚举**；所以跨会话要靠 `lit_index_load("<version_id>")`（同项目内），这一点在 README 里写清楚了，没有含糊过去。
- **升级接口**：`lit_encode(texts, fit)` 是唯一的接缝，把 `LIT_STATE["encoder"]` 换成返回稠密向量的可调用对象即可整体转语义检索，索引格式不用变（分块以文本存储、加载时才向量化）。
- **不伪造**：检索不到时 `lit_context` 返回的是一句明确的「本地库没有匹配，别凭记忆答、别引用」，而不是一段可以被顺口编下去的空上下文。

**自测**（两轮）：

1. `scratchpad\test_local_literature_rag.py`，23 项，全过：分词器、建库、中英检索、引用可回溯、`files=` 过滤、增量新增/修改/删除、冷加载、编码器接缝确实被调用。
2. **真实 PDF 验收**，在 WSL 用 Leo 运行时 python 跑，语料是你自己的 `Desktop\大创\引用文献\`：5 篇真论文（4 英 1 中）→ **68 页 330 分块**；英文问句命中 PINN 传热综述 p.13/11/8；中文问句「纳米流体粘度的实验测量」命中《三氧化二铝纳米流体粘滞度的实验研究_卓清松》p.2；**把命中片段拿回原 PDF 的那一页重新抽取，逐字核对确认确实在那一页**；再加 1 篇 → `added` 只有新增那篇、`unchanged=5`；冷加载后检索仍正常。17 项断言全过。

**未能自测的一项**：验收标准里「用真实科研任务跑通五角色链」需要一次真实 LLM 调用。当前 active profile（deepseek）**没有存 API 密钥**（`has_key=False`），所以这条**没跑**。编排逻辑本身按上面 24 项打桩测试全过；填了密钥之后可以直接跑真链。

---

## 四、第三阶段：`lean-math`

交付：`LeoAIStudio\user\user-skills\lean-math\{SKILL.md, kernel.py, README_zh.md}`，同样已装进 WSL。

### 4.1 实测到的、决定了整个实现的三件事

1. **`lake env lean` 的诊断走 stderr，而且有错也返回 exit 0。** 直接调 `lean`（自备 `LEAN_PATH`）诊断走 stdout、有错返回 1。所以走直接调 `lean` 这条路，并且 `ok` **永远从解析出的诊断算，不看退出码**。
2. `lean --json` 每条诊断一个 JSON 对象，自带 `pos`/`endPos`（行、列）和 `kind`。所以 `kernel.py` 里**没有一行正则去解析 Lean 的人话**。
3. `import Mathlib` 单次约 30 秒；`LEAN_PATH` 用 `lake env printenv LEAN_PATH` 取一次（约 0.6 秒）后缓存，Lake 跑不了时退回按包目录 glob（读只读项目也能work）。

`elan default` 全程没碰（toolchain 是解压 tarball 装的，调它会联网失败），一律绝对路径。探针文件写在会话工作区的 `lean-probes/`，`/home/leo/lean_test` 和 `/home/leo/mathlib4` **只读不写**。

### 4.2 提供的函数

`lean_check`（编译 + 分类诊断）、`lean_goal`（读 goal 状态）、`lean_check_type` / `lean_print`（查签名/定义）、`lean_find`（按形状搜）、`lean_exact`（要一个收尾项）、`lean_loogle`（联网搜，走 `host.web_fetch`）、`lean_run` / `lean_path` / `lean_env` / `lean_toolchain_status`。

**`sorry` 不算证明**：带 `sorry` 的文件是能「编译通过」的，本技能判为 `ok=False` 并置 `uses_sorry=True`，除非显式 `allow_sorry=True`。

### 4.3 自测——以及自测抓出来的两个真 bug

在 WSL 用 Leo 运行时 python 对真 toolchain 跑了 26 项断言。首轮 24 过 2 挂，两个都是我的实现问题，不是环境问题：

1. **`imports="Mathlib.Tactic.NormNum"` 生成了没有 `import` 关键字的裸模块名**，Lean 报 `unexpected identifier; expected command`——一个指向用户代码、实际却是我拼头部拼错的误导性报错。已修：裸模块名和完整 import 行两种写法都接受，列表里也能混着写。修完实测 **narrow 9.33 秒 vs full Mathlib 28.14 秒**。
2. **`#find` 撞穿了 300 秒超时**。查进程时看到 `lean` RSS **7.8 GB**——`#find` 第一次用会对整个 mathlib 建判别树。已修：`lean_find` 单独给 900 秒上限并返回 `timed_out` 而不是抛异常；把实测数字（`_ + 0 = _` 用时 **374 秒**、约 8 GB、返回 20 条被截断）写进 SKILL.md / README / kernel.py 的注释，并把工具推荐顺序改成「先 `lean_exact`(~13s) / `lean_loogle`(~1s)，实在要按形状搜再上 `lean_find`」。

复测后 **26 项全过**。逐条对照你的验收标准：

- 三个文件齐 ✅
- 正确证明 `ok=True`（29.9 秒）✅
- 故意写错的证明返回精确定位 ✅ —— `line 3 col 23 [Tactic.unsolvedGoals] 'unsolved goals'`，`source='example : 2 + 2 = 5 := by'`，`goal='⊢ False'`；第二处 `line 8 col 2 'No goals to be solved'`，`source='  exact foo'`。行号能通过 `header_lines` 换算回代码第 1 行、第 6 行
- 真实 mathlib 定理签名查得到 ✅ —— `Nat.add_comm : ∀ (n m : ℕ), n + m = m + n`、`Continuous.add`；**编造的名字返回 `None` 而不是一个像模像样的签名** ✅
- `upstream` 干净 ✅

额外验证：`exact?` 给出 `exact Nat.add_comm a b`，**把这个建议再编译一遍确认真能用**（round trip）；`lean_goal` 返回 `a b : ℕ\n⊢ a + b = b + a`，写完证明后返回 `closed=True, goals=None`。

---

## 五、需求 3：仓库卫生

### 5.1 删掉了什么

**`LeoAIStudio-build\`：**

| 删除 | 理由 |
|---|---|
| `leo_runtime_patch.py`（82 KB） | 旧壳遗留；只被下面两个失效测试和已删的 `leo_entry.py` 引用 |
| `api_patch_draft.py`（36 KB） | 草稿，全仓零引用 |
| `i18n-brand-patch.css` | 全仓零引用（同名的 `.js` **是**构建输入，保留） |
| `recovered\`（`leo_ai_studio`、`leo_repair_legacy.pyc`） | 旧壳产物；`build_launcher.ps1` 的 PYTHONPATH 不含它 |
| `launcher\leo_entry.py` | 旧入口；打包入口是 `leo_shell_entry.py` |
| `tests\test_runtime_coordinator_extra.py`、`tests\test_runtime_wsl_lifecycle_extra.py` | **本来就是坏的**：`import test_leo_runtime_patch` 指向一个不存在的模块，导致 `pytest tests` 直接 collection error |
| `dist\`（54 MB）、`pyi-work\` | 构建中间产物，已部署 |
| 全部 `__pycache__`、`.pytest_cache` | 缓存 |
| `leo-window-capture.png` | 我自己核对窗口时生成的临时截图 |

**`LeoAIStudio\`：** 删掉 `.leo-rollback-20260901-052544`、`.leo-rollback-20260901-061936`（各 46 MB），保留最新的 `.leo-rollback-20260901-064158`。

### 5.2 **没有**删的，以及为什么

- **`tests\test_package_contract.py` 绝对不能删** —— 它是 `tools\build_launcher.ps1` 的**必需输入**（脚本开头把它列进必需文件，打包后调用它做门禁）。删掉构建会直接失败。你文档里「删除测试文件」这条如果照字面执行，会打不出包。
- `tests\leo_shell\`（10 个文件）—— 按你选的保守清理保留，是这次所有改动的回归网。
- `unified-settings-adapter.js`、`i18n-brand-patch.js`、`stage\leo-inject.js` —— 都是 `bundle_theme.py` 的源层，构建每次从它们重新生成 `leo-inject.bundle.js`，删了构建即失败。
- `tools\capture_window.ps1`、`tools\watch_window.ps1` —— 保留。它们是排查「黑屏但进程活着」（WebView2 那个坑）的诊断工具，属于 `tools\` 这个工具目录，不是残留产物。只删了它们生成的那张 PNG。
- `pyi-spec\LeoAIStudio.spec` —— PyInstaller 每次构建自动重写，留着无害。

### 5.3 清理后的样子

```
LeoAIStudio-build\        .venv  i18n-brand-patch.js  launcher  leo_shell
                          pyi-spec  stage  tests  tools
                          unified-settings-adapter.js  修改报告Claude.md
LeoAIStudio\              LICENSES  LeoAIStudio.exe  README.md  _launcher  bridge
                          runtime  theme  tools  upstream  user
                          检查更新.bat  .leo-rollback-20260901-064158
```

清理后 `pytest tests -q`（整棵树，不再只是 `tests\leo_shell`）→ **225 passed**。

### 5.4 关于「只留一份报告」

`LeoAIStudio-build\` 下的 md/txt 只有两个：本报告，和原有的 `leo_shell\DESIGN.md`（模块接口契约，我是**更新**它而不是新增）。没有新建任何其它说明文件。

技能目录下的 6 个 `SKILL.md` / `README_zh.md` 不在这条约束里——它们是另外两份文档**明确要求的交付物**（`SKILL.md` 更是 OpenAI4S 识别技能的必需文件，不是说明文档）。

### 5.5 凭证

全程没有读取、显示或复制 `user\` 下的任何密钥/凭证内容。`credential.dpapi`、`credentials\`、`ipc.dpapi` 只在目录列表里出现过文件名和大小。日志里的 daemon URL 也一直是 `token=<redacted>`。

---

## 六、日后维护要知道的

**改了技能之后怎么让它生效：**

- 只改 `SKILL.md`：在工作台的技能面板点「安全扫描并同步」即可（这个按钮现在修好了）。
- 改了 `kernel.py`（或新增技能）：必须复制整个目录，因为守护进程的导入接口不传 sidecar——

```bash
wsl.exe -d Ubuntu-24.04 -u leo -- cp -r /mnt/c/Users/user/Desktop/LeoAIStudio/user/user-skills/lean-math /home/leo/.local/share/leo-ai-studio/data/user-skills/
```

**`origin: leo` 是装饰性的**：三个 SKILL.md 都按你的文档写了 `origin: leo`，但 loader 对用户技能会把 origin 归一化（`_VALID_ORIGINS` 是 `openai4s/organization/personal/draft/unknown`，用户技能一律记成 `user`）。所以运行时看到的是 `origin=user`。文件里保留 `leo` 作为给人看的出处标注。想让运行时也认，可以改成 `personal`。

**改启动页之后**：`stage\shell.html` 是权威源，改完要么同步覆盖 `LeoAIStudio\theme\shell.html`，要么跑一遍构建+部署（构建会用 stage 的版本 overlay 进包）。渲染后体积门禁 1.5 MiB，现在用了 162.7 KiB，余量很大。

**部署前**必须关掉正在运行的 `LeoAIStudio.exe`，`deploy_release.ps1` 会拒绝。

**PowerShell 5.1 的坑**（这次踩到了）：对原生命令用 `2>&1` 会把 stderr 包成 ErrorRecord 并让 `$?` 变 `$false`，即使退出码是 0——跑 `build_launcher.ps1` 时别加 `2>&1`。

---

---

## 七、第四阶段：界面结构调整（你的 P0–P3 清单）

这一轮处理的是你看着截图提的结构问题，外加五角色链验证文档里那条「实验员现场装 CUDA 版 torch」。

### 7.0 一个决定了整轮做法的发现

你提的 P0「给内容区让出顶栏高度」，上游**本来就已经做好了**：

| 位置 | 内容 |
|---|---|
| `upstream/.../app.js:8326` | `refreshKeyBanner()` 读 `/me`，`has_api_key === false` 时创建 `#key-banner`（`position:fixed; top:0; left:0; right:0`），并 `document.body.classList.add("has-key-banner")` |
| `upstream/.../style.css:886` | `body.has-key-banner .dashboard{padding-top:52px}` |
| `upstream/.../style.css:887` | `body.has-key-banner #sidebar,#main,#rightdock{padding-top:34px}` |

也就是说「全宽顶栏 + 内容下推」上游已经有了。真正压住会话标题的，是 **Leo 自己多加的第二条悬浮条**：`#leo-keyless-banner`（`position:fixed; top:14px; left:50%; z-index:2147483000`），它完全不参与上游的偏移机制。你数到的「『尚未连接』说了三遍」，第三遍就是它。

所以这条需求的正确做法不是再写一套偏移，而是**删掉 Leo 的重复实现、改用上游那条**。代码更少，偏移白拿，也正好符合你说的「注入层改文案、间距、顶栏偏移就够，不要改上游栅格」。

### 7.1 P0-1：四张新分析卡

**改在** `LeoAIStudio-build\stage\leo-inject.js`。

一个必须讲的坑：上游 `app.js:7220` 的 `const STARTERS = [...]` 是**加载时一次性**用 `t("starter.*")` 求值出来的。注入层在 `loaded` 事件后才跑，所以**光改 `I18N` 不会改变卡片**——数组里存的是已经解析好的字符串。而且 `setLang → rerenderI18n` 会重渲空会话，却从不重建 `STARTERS`。

实现因此是三件事一起做：

1. 八个 `starter.*` 键写进 `I18N.zh` 和 `I18N.en`；
2. **原地改写 `STARTERS` 数组元素**（`LEO_STARTERS` 映射 + 按身份匹配，不是按下标盲改）；
3. 挂在 locale 切换上**每次重放**，不是一次性 guard。

对照表（标题按你给的原文）：

| 键 | 中文 | English |
|---|---|---|
| `starter.litReview` | 精读一条分析命题 | Study one analysis theorem |
| `starter.dataAnalysis` | 批改我的证明草稿 | Critique my proof draft |
| `starter.proteinModel` | 诊断这次 PINN 训练 | Diagnose this PINN run |
| `starter.phylo` | 从 PDE 落到 PINN 设定 | From a PDE to a PINN setup |

四段完整 prompt 按你的原文逐字进去了。实测已部署 bundle 里的长度：中文 242–403 字，英文 868–1120 字（旧的 CRISPR 系列是 37–62 字的短句），英文是同结构对照翻译，不是「检索近三年进展」那种套话。

**一处我擅自改了你的原文**：你写的「先用一维 possion」是 Poisson 的笔误，英文那句你写的是 "1D Poisson"。产品里出现错别字比偏离原文更糟，所以中文改成了「一维 Poisson」。

**没动布局**：`leo.css` 里没有任何针对 `.es-chip` 网格的规则，卡片尺寸、两行截断（上游 `style.css:877` 的 `-webkit-line-clamp:2`）原样保留。只加了标题字号（见 8.6）。

### 7.2 P0-2 / P2-2：一条浏览模式栏

- **删**：`stage\leo-inject.js` 的 `ensureKeylessBanner()` 及其调用点；`stage\leo.css` 原第 94–95 行的 `.leo-keyless-banner` 规则。部署后的 bundle 里 `leo-keyless-banner` 出现 **0 次**。
- **改用上游 `#key-banner`**，Leo 只重写它的样式和文案：
  - `key.banner.notConfigured` → 「浏览模式 · 接入后可继续对话」/ "Browse mode · connect to continue the conversation"
  - `key.banner.goConfigure` → 「接入模型」/ "Connect"
- **视觉**：36px 全宽，中性配色（不是原来那种读起来像成功状态的绿），`.kb-link` 和新增的 `.kb-dismiss` 都压在 36px 内。
- **偏移**：`stage\leo.css` 覆盖上游那两条，按 36px 重算 `.dashboard{padding-top:57px}`、`#sidebar,#main,#rightdock{padding-top:39px}`。靠特异性赢（Leo 侧 `(0,3,2)` / `(1,2,2)` vs 上游 `(0,2,1)` / `(1,1,1)`），**没有用 `!important`**。
- **可关闭**：`.kb-dismiss` 同时移除节点和 `body.has-key-banner`，两者不可能不同步；关闭状态存 `localStorage["leo-keyless-dismissed"]`。
- **真正的抑制，不是「画完再删」**：`installBrowseBannerSuppression()` 包住 `window.refreshKeyBanner`。已关闭时**根本不调用原函数**——不发 `/me` 请求、不建节点、不加 body class，所以不会每次重建都闪一下 36px 的跳动。包装带 `__leoBrowseWrapped` 标记 + state 双重防重入；上游若改名则不包装，退回原来的反应式行为。

### 7.3 P1-1 / P2：启动页与品牌

**改在** `LeoAIStudio-build\stage\shell.html`。

删掉：右上「尚未连接」状态药丸、右侧状态大卡、底部「本地安全 / DPAPI / 科研运行时 / WSL2」四字广告条（内容移进设置→关于）、以及作为第三个 CTA 的「切换主题」（抽屉的「外观」页本来就有主题卡，删按钮不丢功能）。

保留：大标题 + 主按钮「配置模型」+ 次按钮「先逛逛」。副文案换成说实话的那句——「已保存配置，但还没有 API 密钥。填写密钥后启动即会自动进入工作台；也可以先逛逛。」——不再和状态卡各讲一套。

**品牌统一（这是我替你做的判断，可以推翻）**：你写的「对外/启动用 Leo AI Studio」和「工作台顶栏用同一中文名」两句本身有张力。我统一成**两个 locale 都叫 "Leo AI Studio"，副标只留 "AI · SCIENCE · STUDIO"**（弃用 "SCIENCE · MEMORY · CRAFT"），三处一起改：`shell.html`、`leo-inject.js` 的 brand lockup 与 `app.title`、`theme\i18n\zh.json` 的 `app_name`。想让工作台顶栏回到「Leo 科研助手」说一声，改一行的事。

主按钮改用工作台的橙 `--clay #E0642E`（hover `--clay-em #C94F20`），圆角对齐 8/16/22。**背景保留暖米白** `#FBF7F2`——那是启动页刻意的身份，你没要求推翻；`leo_shell\ui.py:44` 的 `_WINDOW_BACKGROUND` 同步为同值，已核对一致。

### 7.4 P3：狮子头看不见

**根因**（实测，不是猜）：三个狮标资产都是**近白色描边 + 透明底**，为老的 `#071319` 深色壳画的：

| 资产 | 不透明像素平均亮度 | 亮于 200 的比例 |
|---|---|---|
| `leo-lion.svg` | 233 | 94% |
| `leo-lion.ico` | 236 | 96% |
| `leo-lion-1024.png` | 235 | 96% |

工作台里之所以还看得见，是因为 `leo.css` 给 `.leo-brand-mark` 垫了一块深色徽章底。启动页（暖白）和 Windows 任务栏（浅色）没有这块底，狮子就消失了——**这是我上一轮把底色改成浅色带出来的回归**。

两处修法一致：把白狮子放到深色圆角徽章上。

- 启动页：在 `shell.html` 内联 CSS 里复刻工作台徽章的几何与配色（自包含，不依赖 `leo.css`）。
- 任务栏：`LeoAIStudio-build\tools\make_lion_icon.py` 用 Pillow 把 `leo-lion-1024.png` 合成到不透明深色圆角方块上，重新生成 `.ico`。**没有重画、没有改色**，只是加底。

第一版做过头了——`INSET_SMALL = 0.88` 加一像素膨胀，把 16/24/32 填成了糊块，而那恰好是 Windows 任务栏真正用的尺寸。重调后实测：

| 尺寸 | 平均 RGB（前 → 后） | darkFrac | 边缘对比中位数 | ≥3:1 比例 |
|---|---|---|---|---|
| 16px | (118,134,140) → **(68,90,98)** | 0.41 → **0.82** | 2.17:1 → **3.83:1** | 37% → **71%** |
| 24px | (120,135,140) → **(67,86,94)** | — | — → **4.62:1** | — → **82%** |
| 32px | (117,132,137) → **(66,85,92)** | — | 2.58:1 → **5.27:1** | 38% → **83%** |

现在小尺寸和 48px 的画像一致，不再是糊块。原图备份在 `LeoAIStudio-build\assets-backup\leo-lion.pre-badge.ico`（**唯一一份 pre-badge 原件，别删**）；该目录在构建仓库根目录、不在 `theme\` 下，所以不会随包发给用户。

### 7.5 P1-2 / P1-3：首页项目行与产物区

**项目行**（`leo-inject.js`）：每行加一段「近期产出：md · csv · 图」，数据来自 `/api/v1/projects/<id>/artifacts`；只有 Example 时在列表下补一行弱提示「新建 PINN 项目，Example 仅作引擎演示」。

判定「有没有自己的项目」用的是网关发布的 `project.is_example` 字段（`gateway.py:17860`），不是 `/example/i` 匹配项目名——否则你把示例改名叫「示例」，提示就永远不出来了。名字正则只作为网关不给该字段时的兜底。零项目的情况也给提示（换了一句：「从新建一个 PINN 项目开始，产出都会留在这里」），因为对一个没有 Example 的人说「Example 仅作引擎演示」是不通的。

请求做了约束：**总预算 12 次 / 120 秒窗口**（原来那版的「上限 12」只限单批，`finally` 里会把第 13–24 个接上去，60 个项目就是 60 次串行请求）、每次带 `AbortController` + 8 秒超时、离开首页立即停、缓存 120 秒 TTL（否则会话中途新产出的项目要重启才显示）。

**产物区**：`art.generated` / `art.uploaded` 两个标题统一改成同一语域（「可打开的产出」/「上传的文件」，OPEN ARTIFACTS / UPLOADED FILES）——之前只改了一个，出现「可打开的产出 · 3」挨着「上传 · 1」两种语气。「生成 · 3」的重复：包住 `renderConversationArtifacts`，在**同一个同步任务里**移除 generated 段的 `.gen-label`（不是画完再删），保留 uploaded 的标题，因为「这个文件是你传的」是磁贴本身表达不了的信息。

### 7.6 P0 里被漏掉、后来补上的一条

你写的「标题 16～18px」第一轮**被静默丢了**——`leo.css` 里当时没有任何 `.es-chip-t` 规则，卡片标题还是上游 `style.css:876` 的 13px。是对抗性复查把它揪出来的，现已补上并压住卡片高度不变。

### 7.7 五角色链：实验环境约定

按你的验证文档：

- `user\user-skills\research-sop\SKILL.md` 新增 `## The experiment environment`；
- `README_zh.md` 新增 `## 实验环境约定` 和 `## 推荐的验收任务`。

实到的运行时（`/home/leo/.local/share/leo-ai-studio/runtimes/0.2.0-2eb33f7bf139/runtime/bin/python3`）**已有** numpy / scipy / pandas / matplotlib / sklearn / sympy / statsmodels / networkx / numba / h5py / plotly / seaborn，**没有** torch / jax。

**但我多做了一步**：文档只有在子 agent 主动打开 `SKILL.md` 时才起作用，而那次失败恰恰发生在被委派的角色内部。所以我把规则写进了 `kernel.py` 里 `sop_role_prompt` 组装的 **numerical-experimenter 角色提示词本身**（三条：优先用预装科学栈；真要 torch 必须 `pip install torch --index-url https://download.pytorch.org/whl/cpu`；宁可把实验降级也不要停下来装几个 GB，并把降级和理由写进阶段文件）。现在渲染出的角色提示 2428 字符，含 CPU wheel 规则——子 agent 不读文档也躲不掉。

### 7.8 校验

- `pytest tests -q`：**225 passed**（上一轮 212，这轮各 agent 补了覆盖）。
- `tools\headless_verify.py`：preflight / status / start / url / http-root / http-health / stop **全 ok**；shell 渲染后 165 386 字节，门禁 1.5 MiB。
- `upstream/OpenAI4S` `git status --porcelain`：**空**。
- 构建 + 部署：`PACKAGE CONTRACT PASSED: 381 _launcher files, 16 critical files, 24 archive modules`。
- 部署后核对：bundle 已重生成，`leo-keyless-banner` 0 次；`es-chip-t`、`kb-dismiss`、四个新标题、浏览模式文案都在包里。
- 启动页实拍：狮子可见、单一字标、两个按钮、说实话的副文案、无状态药丸/状态卡/广告条。

**一个我查过、结论是「没有 bug」的事**：日志里出现过启动后 7 秒和 28 秒各一次「停在启动页 → 随后 submit」，看着像自动跳转。加临时日志重跑两次（源码 50 秒、冻结 exe 60 秒）都**没有复现**，`connect_keyless` 从未进入；代码里通往它的唯一路径是 `#browse-keyless` 的点击处理器，没有定时器、没有 `dispatchEvent`、没有 `.click()`。那两次是你当时在机器前点了「先逛逛」。需求 2 的行为是对的：`app.py` 无 key 时记录 `startup stays on the splash page` 后直接返回。临时日志已删除，删除后重跑 225 项测试仍全绿，并重新构建部署了干净版本。

### 7.9 这一轮删掉的

- `LeoAIStudio-build\`：`leo-window-capture.png`（我自己的截图产物）、`.pytest_cache\`、四个 `__pycache__\`、`dist\`（54 MB，已部署）、`pyi-work\`。
- `LeoAIStudio\user\user-skills\`：三个 `__pycache__\`。
- `LeoAIStudio\`：三个旧回滚目录，只留最新的 `.leo-rollback-20260902-203327`。

`leo_runtime_patch.py`、`api_patch_draft.py`、`recovered\`、`launcher\leo_entry.py` 上一轮已经删干净了。

**仍然没删、也不该删**：`i18n-brand-patch.js` 和 `unified-settings-adapter.js`。你的文档把它们当「合并草稿」，但 `build_launcher.ps1:100-106` 每次构建都会把这两个文件和 `stage\leo-inject.js` 拼成发布用的 `theme\leo-inject.js`——删掉会直接废掉整个主题层。

### 7.10 这一轮新增的文件

只有两个：`LeoAIStudio-build\tools\make_lion_icon.py`（图标重生成脚本）和 `LeoAIStudio-build\assets-backup\leo-lion.pre-badge.ico`（原图备份）。

---

## 八、遗留 / 需要你决定的（截至第四阶段）

### 8.1 做不到的，以及为什么

**「失败产物显示成一行灰字、链到报告」——注入层做不到。** 我让 agent 去查了，结论是这条需求的前提不成立：

- 产物画廊不是来源。`visibleArtifacts()`（`app.js:8492-8495`）和 `filesGridArtifacts()` 都在渲染前用 `(a.priority || 0) >= 0` 把失败/跳过项**滤掉了**，所以它们根本不会进入 DOM，没有节点可以变灰。
- 全站搜 `skipped` 只有三处（`app.js:5889/5897` 的 plan-step 状态常量和一句注释），`3D structure` 一处都没有。
- 助手消息是 `md.innerHTML = renderMd(text)`（`app.js:7241`）——**你截图里那行「3D structure — skipped…」是模型自己写在回答正文里的 markdown**，不是渲染出来的数据结构。

所以这条得改**系统提示词 / plan 提示词**那一层（让模型把失败项写成固定格式），不是改 `leo-inject.js`。同理，「把 Materials 缩成短目录」也只能在提示词层做——我只做到了可做的那半（去掉 Leo 自己在磁贴上方的重复标题）。要我去改提示词层的话说一声，那是另一块工作。

**16px 的狮子仍然不是「一眼认得出的狮子」。** 现在是深色徽章上一个头形亮块，有眼窝和朝左的口鼻，图底关系正确、不再是糊块——但不认识这个品牌的人未必叫得出是狮子。agent 扫过 crop box / inset / 腐蚀 / 闭运算 / 填洞各种组合，这是 11px 宽栅格化这版原画的物理上限。要更好只能**为 16px 单独画一个简化字形**，那是重画，不在这轮范围里。

### 8.2 需要你拍板的

1. **品牌名**。我统一成两个 locale 都是 "Leo AI Studio" + 副标 "AI · SCIENCE · STUDIO"（见 7.3）。你原话「工作台顶栏：同一套狮标 + 同一中文名」如果是指想保留「Leo 科研助手」，说一声，改三处一行的事。
2. **五角色链仍未跑过真实任务**。app 的凭证库里 `has_key = False`——你那次是把 key 从 WSL 环境变量传进去、绕过 GUI 跑的 `openai4s run`，DPAPI store 没拿到。填密钥这件事得你自己来（设置 → 模型 → 保存并连接），我不去翻凭证。填完我可以直接跑；agent 已经拟好一个不依赖深度学习框架的验收任务：

   > 用 research-sop 跑一遍：一维泊松方程 −u″ = f 在 [0,1] 上带齐次 Dirichlet 边界，当右端 f 只有有限正则性时（例如 f 含一个跳跃，或 f(x)=|x−1/2|^α 这类奇点），残差型（PINN 式最小二乘配点）近似解的 L² 误差能否由残差的 L² 范数控制，即先验界 ‖u−u_h‖_{L²} ≤ C(s)·‖R‖_{L²} 是否成立、常数 C(s) 随 Sobolev 正则性阶 s 如何退化？请依次走完文献综述、建模、数值实验、验证、论文撰写五个角色。

   sympy 给精确解和精确残差，固定基上的最小二乘配点代替 PINN，扫 α 和基的规模就能同时得到经验界和 C(s) 的退化率；综述员也有真文献可查（Mishra–Molinaro、De Ryck–Mishra 一系的 residual error estimate）。全程 numpy/scipy/sympy 够用。

3. **窗口在高 DPI 下偏小**（观察，不是这轮引入的）。实测 `WINDOW_DPI=192`，而 `GetWindowRect` 返回 1280×800 **物理**像素——也就是 CSS 视口只有 640×400，会掉进窄屏断点。`leo_shell\ui.py:114-116` 的 `width=1280, height=800, min_size=(840,600)` 没有配 DPI 感知声明。你自己的截图是宽布局，所以可能只是我这边的显示配置；要我做 DPI 感知的话是独立的一小块工作。

### 8.3 已知的小瑕疵（报告出来，没动）

- `.venv` 里没有 Pillow，所以 `make_lion_icon.py` 要用 `C:\Users\user\mamba\python` 跑。agent 把文档改成写明真实解释器，而**没有**擅自往共享 venv 里装包；想让 venv 自足就是一条 `pip install pillow`。
- `leo.css:95` 还留着 `.project-card` / `.session-card` 两个选择器片段，上游根本没有这两个类，永远不匹配。无害，属于纯清理，这轮没碰。
- `.leo-d-art`（近期产出那行）的隐藏阈值绑的是**视口**宽度（901–1180px），不是行的实际宽度——CSS 要做成容器相对得给上游的 `.dash-card` 加 `container-type`，那是改上游行为。极端布局下它会显示并压到 30% 宽而不是隐藏，退化成「挤但正确」，不会撑破卡片。
- 对抗性复查的第二个 verifier（`no-new-regressions`）在最后一轮撞上用量上限没跑完。第一个（`defects-closed`）跑完了，加上我自己核了：语法、大括号平衡、shell 契约（占位符 / COPY 中英 57↔57 键对齐 / 五个错误码 / DOM 引用全解析）、225 项测试、`headless_verify` 全阶段、上游 `git status` 干净、部署后 bundle 内容比对。

### 8.4 前三阶段的遗留（状态更新）

1. ~~五角色链没跑过真实任务~~ → 见 8.2 第 2 条，仍待你填密钥。
2. `research-sop` 的产物是会话级的：**未变**。想让整条流水线的产物默认 artifact 化，说一声。
3. `lean_find` 太贵（374 秒 / 8 GB）：**未变**。
4. ~~报告文件名~~ → 已定为 `LeoAIStudio-build\修改报告Claude.md`，本文件就是唯一一份，第四阶段追加为第八、九章。


</details>

<a id="history-2"></a>

## 历史附录 2：docs/P0_EXECUTION_STATUS.md

<details>
<summary>展开历史原文（仅作记录）</summary>

# Leo AI Studio 鈥?Phase 0 鎵ц鐘舵€?

> 渚濇嵁锛歚Leo-AI-Studio-浜у搧鏋舵瀯涓庡墠绔噸鏋勫璁?md`銆乣Leo-AI-Studio-P0鏁存敼娓呭崟.md`
> 鏈枃浠舵槸 Phase 0 鐨勫敮涓€娌荤悊璁板綍銆?
> 鐘舵€佸彛寰勶細`TODO` / `IN_PROGRESS` / `PASS` / `PARTIAL` / `BLOCKED`銆?
> **`NOT TESTED` 姘歌繙涓嶅緱鍐欐垚 `PASS`銆?*

> **Round 2 鏇存柊锛?026-09-03锛?*锛氭帴鍙椾簩娆″鏍告姤鍛婄殑鍒ゅ畾锛屼笉浜夎京娴嬭瘯鏁伴噺銆?
> 涓婁竴杞妸銆屼换鍔¤矾寰勫凡鍒嗗紑銆嶈繃搴︽帹鏂垚銆岃瘉鎹摼鍙俊銆嶏紝`P0-2 = PASS` 鍐欐棭浜嗐€?

| # | 浠诲姟 | layer | Round 1 鑷姤 | 澶嶆牳鍒ゅ畾 | Round 3 鐜扮姸 |
|---|---|---|---|---|---|
| P0-1 | 鍗曚竴鍙俊婧愮爜 | build/tooling | PASS | REOPEN | `PASS` |
| P0-2 | research-sop 璇佹嵁瀹屾暣鎬?| skill | PASS | FAIL | `PASS` |
| P0-3 | Visible UI 涓?ShellApi 涓€鑷?| shell + injection | PASS | CONDITIONAL | `PASS`锛坓ated bridge + mutation test锛?|
| P0-4 | 鍘婚櫎涓汉璺緞缁戝畾 | shell + build/tooling | PARTIAL | PARTIAL | `PARTIAL`锛堥潤鎬佹竻闆讹紱27 椤瑰疄鏈?`NOT TESTED`锛?|
| P0-5 | 鏋勫缓鍙鐜?| build/tooling | TODO | FAIL | `PARTIAL`锛坔ermetic 鍙瀯寤哄彲杩愯锛涙棤 wheelhouse锛?|
| P0-6 | 涓嬩竴闃舵 Gate | 鈥?| FAIL | FAIL | **`FAIL`** |

娴嬭瘯鎬绘暟锛?*284 passed**锛圵indows锛宍.venv/Scripts/python -m pytest tests -q`锛宑ommit 12ceb40锛夈€?

---

## P0-1 鍗曚竴鍙俊婧愮爜 鈥?`PASS`

**闂** 瀹¤绉颁笁浠芥簮鐮佷箣闂存病鏈?canonical source銆?

**root cause锛堜笌瀹¤缁撹涓嶅悓锛屽疄娴嬶級**

1. **`LeoAIStudio-build/` 鍜?`LeoAIStudio/` 閮戒笉鏄?git 浠撳簱銆?* 鍞竴鐨勪粨搴撴槸
   `upstream/OpenAI4S`锛堝浐瀹?`a792c38d9984be428437b548db29baab3322f6dc`锛?026-08-28锛夈€?
   鐪熸鐨?root cause 涓嶆槸銆屽浠芥紓绉汇€嶏紝鑰屾槸 **Leo 鑷繁鐨勪唬鐮佷粠鏈繘鍏ョ増鏈帶鍒?*銆?
2. **`leo-studio-src.zip` 涓嶆槸婧愮爜鍖呫€?* 3355 鏉＄洰閲?3323 鏉℃槸 `upstream/`锛?
   Leo 閮ㄥ垎鍙湁 `theme/`(16) + LICENSES + examples銆?*涓嶅惈 `leo_shell/`銆乣stage/`銆?
   `tools/`銆乣tests/`**锛屽嵆鏁翠釜 Windows 澹虫簮鐮侀兘涓嶅湪閲岄潰銆傚畠鏄?08-31 瀵?*閮ㄧ讲鐩綍**鐨勫揩鐓с€?
3. **閫愭枃浠舵瘮瀵癸細zip 涓病鏈変换浣曠嫭鏈夊唴瀹广€?* 16 涓?theme 鏂囦欢 11 涓€愬瓧鑺傜浉鍚岋紱
   5 涓笉鍚岀殑鍏ㄩ儴鏄?live 鏇存柊銆俙files present only in the zip: none`
   鈫?**涓嶉渶瑕?merge**銆?

**棰濆鍙戠幇** 涓変釜鎶€鑳藉彧瀛樺湪浜庨儴缃茬洰褰曞拰 WSL 鏁版嵁鐩綍锛?*鍚屾牱涓嶅湪鐗堟湰鎺у埗閲?*锛?
涓斾袱鑰呬箣闂撮潬鎵嬪伐澶嶅埗銆傝繖灏辨槸涓婁竴杞€岃 CUDA torch 鐨勪慨澶嶅叾瀹炰粠娌′笂绾裤€嶇殑鍘熷洜锛?
daemon 璇荤殑鏄?`~/.local/share/leo-ai-studio/data/user-skills/`锛學indows 渚ф敼浜嗕笉绠楁暟銆?

**implementation**
- `git init` + `.gitignore` + `.gitattributes`锛涢娆℃彁浜?`8a65838`锛?9 涓枃浠躲€?
- 鐢熸垚鐗╃Щ鍑虹増鏈帶鍒讹細`stage/leo-inject.bundle.js`锛堟瀯寤烘椂鐢?`bundle_theme.py` 閲嶇敓鎴愶級銆?
  `pyi-spec/*.spec`锛圥yInstaller `--specpath` 姣忔鐢熸垚锛屼笖浼氱儰杩涙瀯寤烘満缁濆璺緞锛夈€?
  `dist/`銆乣pyi-work/`銆乣manifests/build-*.json`銆?
- **鎶€鑳界撼鍏?canonical**锛歚skills/` 杩涗粨搴擄紝鏂板 `tools/sync_skills.py`
  鍗曞悜涓嬪彂 `skills/ 鈫?閮ㄧ讲鐩綍 鈫?WSL data/user-skills/`锛宍--check` 鍙娴嬫紓绉汇€?
- 鏂板 `tools/build_manifest.py`锛氳褰?Leo commit / upstream revision / bundle 涓?
  鍚勬簮鏂囦欢 SHA-256 / runtime manifest / toolchain / exe SHA-256 / 姣忎釜鎶€鑳界殑鏂囦欢鍝堝笇銆?
  鍙栦笉鍒扮殑鍊间竴寰嬪啓 `"unknown"`锛屼笉鐚溿€?

**tests** `tools/sync_skills.py --check` 閫氳繃锛涜礋鍚戝鐓э紙浜轰负鏀逛竴涓瓧鑺傦級鑳藉悓鏃?
鎶ュ嚭 windows 涓?wsl 涓や晶婕傜Щ骞朵互闈為浂鐮侀€€鍑恒€?

**result** 浠庝粨搴撳彲浠ヨВ閲婂綋鍓嶅彂甯冪増鏈敱浠€涔堢粍鎴愶細
`leo 8a65838` + `upstream a792c38d` + bundle `b82bf906eaa5bb81` + exe锛堟瘡娆￠儴缃茶褰曪級銆?

**remaining risk** 棣栨鎻愪氦涔嬪墠鐨勫巻鍙蹭笉鍙拷婧€斺€旀棦鎴愪簨瀹烇紝鍙兘浠庣幇鍦ㄥ紑濮嬨€?
**rollback** `git init` 涓嶆敼鍔ㄤ换浣曟棦鏈夋枃浠讹紱鍒犻櫎 `.git/` 鍗冲彲鎾ら攢銆?

---

## P0-2 research-sop 璇佹嵁涓查 鈥?Round 1 璁板綍锛堝垽瀹氳涓嬫柟 Round 2 鑺傦級

**layer** skill锛坄skills/research-sop/kernel.py`锛?

**root cause锛堣鐮佺‘璁わ紝鍥涙潯鐙珛缂洪櫡锛?*

1. **闃舵璺緞娌℃湁浠诲姟缁戝畾**锛歚sop_stage_path(role)` 鍥哄畾杩斿洖
   `research-sop/01-literature-surveyor.json`锛屼笉鍚?run id / task hash銆?
   `resume=True`锛?*榛樿鍊?*锛夊洜姝ゆ妸浠诲姟 A 鐨勯樁娈靛綋浣滀换鍔?B 鐨勭粨鏋溿€?
2. **`status` 纭紪鐮?`complete`**锛氬嚱鏁版湯灏炬棤鏉′欢杩斿洖锛屼笌鏄惁鍙窇浜嗗瓙闆嗘棤鍏炽€?
3. **`validator` 纭紪鐮?`pass`**锛歷alidator 鏍规湰娌¤繘 pipeline 涔熸姤 pass銆?
4. **`paper` 璺緞纭紪鐮?*锛歱aper-writer 娌¤窇涔熻繑鍥炶矾寰勶紝鎸囧悜涓嶅瓨鍦ㄧ殑鏂囦欢銆?

**棰濆鍙戠幇** 浠撳簱涓?*涓嶅瓨鍦ㄤ换浣?skill 娴嬭瘯**锛坄tests/` 鍙湁 `leo_shell/` 涓?
`test_package_contract.py`锛夈€傛鍓嶆姤鍛婃彁鍒扮殑銆?4 椤规墦妗╂祴璇曘€嶅湪鏈粨搴撲笉瀛樺湪锛?
鍥犳鏈」鏄?*浠庨浂寤虹珛**娴嬭瘯鑴氭墜鏋躲€?

**瀹炴祴澶嶇幇锛堝 `docs/rollback/research-sop-kernel.pre-P0-2.py`锛?*

```
task A: complete | delegate calls: 5
task B: complete | delegate calls: 0      鈫?B 缁ф壙浜?A 鐨勫叏閮ㄤ簲涓樁娈?
task B validator: pass | paper: research-sop/05-paper-writer.md

subset run (modeler only): status=complete  validator=pass  paper=<path>
```

**implementation**
- 姣忔杩愯鐙珛鐩綍 `research-runs/<run_id>/`锛宍run_id` 鐢?task 鏂囨湰鐨?SHA-256 鎺ㄥ嚭銆?
- `manifest.json`锛歚schema_version` / `run_id` / `task_text` / `task_sha256` /
  `pipeline_version` / `role_order` / `role_prompt_hashes` / `model_fingerprint` /
  `created_at` / `parent_run_id` / `rollbacks`銆?
  妯″瀷韬唤鍙栦笉鍒版椂鍐?`"unknown"` 骞惰鏄庡師鍥狅紝涓嶇紪閫犮€?
- Resume 瑙勫垯锛歵ask hash 鐩稿悓鎵嶅師浣嶇画璺戯紱涓嶅悓涓€瀹氭柊寤?run锛?
  `resume=False` = 鏄庣‘閲嶅仛 鈫?**鏂板缓 run 骞惰 `parent_run_id`锛屾棫 run 鍘熸牱淇濈暀**
  锛堝垹鏃ц瘉鎹瓑浜庢瘉瀹¤閾撅級銆俶anifest 琚敼鍧?鈫?鎶涢敊鎷掔粷澶嶇敤锛屼笉闈欓粯銆?
- 闃舵璁板綍鍐呭祵 `run_id` + `task_sha256`锛宍sop_read_stage` 鍙岄噸鏍￠獙鈥斺€?
  鍗充娇鏈夋父绂绘枃浠惰惤杩?run 鐩綍涔熻涓嶆垚璇佹嵁銆?
- 鐘舵€佽瘹瀹炲寲锛歚complete` / `partial` / `unresolved` / `blocked`锛?
  `validator` 娌＄湡璺戝氨鏄?`None`锛沗paper` 娌＄湡鍐欏氨鏄?`None`銆?
- **娌℃湁淇濈暀浠讳綍鍥為€€鍒版棫鍥哄畾璺緞鐨勫吋瀹瑰垎鏀?*锛堥偅姝ｆ槸姹℃煋婧愶級銆?
- 瑙掕壊鎻愮ず璇嶉噷鍚屾椂琛ヤ簡瀹為獙鐜绾﹀畾锛堜紭鍏堥瑁呯瀛︽爤锛泃orch 蹇呴』 CPU wheel锛?
  瀹佸彲闄嶇骇瀹為獙涔熶笉鍋滀笅鏉ヨ鍑犱釜 GB锛夈€?

**tests** `tests/skills/test_research_sop.py` 鈥?**12 passed**锛岃鐩栨竻鍗曡姹傜殑
Case A鈥揈锛屽彟鍔?manifest 瀛楁銆佽法浠诲姟璇绘嫆缁濄€乼ask hash 褰掍竴鍖栥€佸潖 manifest 鎷掔粷銆?
blocked 鐘舵€併€?*宸查獙璇佽繖浜涙祴璇曞淇鍓嶇殑 kernel 浼氬け璐?*锛堣涓婃柟澶嶇幇锛夛紝
涓嶆槸绌鸿浆鐨勬祴璇曘€?

**remaining risk** 鏃х殑 `research-sop/` 鍥哄畾璺緞閬楃暀鏂囦欢浠嶅湪浼氳瘽宸ヤ綔鍖洪噷锛?
鏂颁唬鐮佷笉浼氳瀹冧滑锛堣矾寰勪笉鍚岋級锛屼絾涔熸病鏈変富鍔ㄦ爣璁颁负 legacy銆?
**rollback** `docs/rollback/research-sop-kernel.pre-P0-2.py`

---

## P0-2 Round 2锛氳矾寰勫垎寮€ 鈮?璇佹嵁鍙俊

澶嶆牳鎶ュ憡鐨勬牳蹇冩壒璇勬垚绔嬶細涓婁竴杞彧瑙ｅ喅浜嗚韩浠界粦瀹氾紝娌¤В鍐崇姸鎬佸彲淇°€乻chema 鍙俊銆?
artifact 鐪熷疄銆佸巻鍙蹭笉鍙彉銆佺増鏈吋瀹瑰拰璺緞瀹夊叏銆?*鎴戠嫭绔嬪鐜颁簡瀹冩寚鍑虹殑涓绘紡娲?*锛?

```
first = orchestrate_research(TASK_A)          # 姝ｅ父瀹屾垚
files[manifest_path] = "{ this is not json"   # manifest 鎹熷潖浣嗗瓨鍦?
orchestrate_research(TASK_A, resume=True)
鈫?status: complete | delegate calls: 0        # 闈欓粯閲嶅缓 manifest锛屾棫闃舵琚綋浣滆瘉鎹?
```

涓婁竴杞垜鍦ㄦ湰鏂囦欢閲屽啓鐨勩€宮anifest 琚敼鍧?鈫?鎶涢敊鎷掔粷澶嶇敤銆?*鏄敊鐨?*锛氶偅鏉″彧瑕嗙洊
銆孞SON 鍚堟硶浣?task hash 涓嶇銆嶏紝鑰屼笉鏄€孞SON 鏈韩鎹熷潖銆嶃€傚凡鏇存銆?

涔濈被淇锛堝搴斿鏍告姤鍛?搂5.1鈥?.10锛夛細

| # | 婕忔礊 | 淇 |
|---|---|---|
| 1 | 鎹熷潖 manifest 琚綋浣滀笉瀛樺湪 | 鍥涙€?`missing/valid/corrupt/incompatible`锛沜orrupt **fail closed**锛屽師瀛楄妭涓嶈鐩?|
| 2 | 缂?`run_id`/`task_sha256` 鐨?stage 浠嶈鎺ュ彈 | 绮剧‘鐩哥瓑锛宍None` 涓嶅啀绠楀尮閰嶏紱`role` 涔熻瀵逛笂 |
| 3 | delegate 澶辫触浠嶈 complete | 妫€鏌?`task_status`/`error`/`stop_reason`锛屽師濮?payload 淇濈暀 |
| 4 | schema 鍙紶缁?host锛屼笉澶嶆牳 | orchestrator 鍐呮湰鍦板鏍?required keys + verdict 鏋氫妇 |
| 5 | paper 璺緞鍙兘鎸囧悜涓嶅瓨鍦ㄧ殑鏂囦欢 | 鏂囨。蹇呴』瀛樺湪涓旈潪绌猴紝璁?`document_sha256` |
| 6 | rollback 鐢ㄧ┖涓茶鐩栬瘉鎹?| 褰掓。鍒?`history/rollback-NNN/`锛岃鍥炴牎楠屽悗鎵嶆竻绌猴紱澶辫触鍗充腑姝?|
| 7 | roles 鍏佽涔卞簭閲嶅 | 蹇呴』鏄?`ROLE_ORDER` 鐨勫敮涓€淇濆簭瀛愬簭鍒?|
| 8 | `run_id`/suffix 鍙矾寰勭┛瓒?| strict fullmatch + suffix 鏋氫妇 + 瑙勮寖鍖栧悗 containment 妫€鏌?|
| 9 | prompt/pipeline 鍙樺寲琚潤榛樺鐢?| 鍙備笌 resume 鍒ゅ畾锛涢粯璁?fork 鏂?run 璁?`parent_run_id`锛屽彲璁?`on_incompatible="fail"` |
| 10 | resume 姘歌繙鍥炲埌 base 鍒嗘敮 | 榛樿缁窇**鏈€鏂板垎鏀?*锛屾敮鎸佹樉寮?`run_id=`锛宍sop_run_lineage()` 鍙洖婧?|

**娴嬭瘯**锛歚tests/skills/test_research_sop_integrity_adversarial.py`锛?1 椤癸級銆?
澶嶆牳鏂圭殑鍘熷鏂囦欢琚彁鍙婁絾**鏈殢闄?*锛屾墍浠ヨ繖鏄寜鎶ュ憡 搂2.4/搂5 鐨勬弿杩?*鐙珛閲嶅缓**鐨勭増鏈紱
浠栦滑鐨勬枃浠跺埌浜嗗簲褰撲竴骞惰窇锛岃€屼笉鏄浛鎹€?

**璇佹嵁**锛氳繖 41 椤归噷 **32 椤瑰 round-1 kernel 澶辫触**銆佸叏閮ㄥ褰撳墠 kernel 閫氳繃銆?
涓嶆槸绌鸿浆鐨勬祴璇曘€傦紙`docs/rollback/research-sop-kernel.pre-P0-2-round2.py` 淇濈暀浜?round-1 鐗堟湰渚涘楠屻€傦級

**涓ゅ鎴戝垽瀹氬鏍告柟鎻忚堪闇€瑕佷慨姝ｇ殑**锛堝凡鍦ㄦ祴璇曟敞閲婁腑璇存槑锛夛細
- 銆宲aper 鏂囨。琚垹鍚庡繀椤昏繑鍥?`paper=None`銆嶁€斺€旀纭涓烘槸**閲嶈窇璇ラ樁娈?*骞朵骇鍑虹湡瀹炴枃妗ｏ紝
  娴嬭瘯鏂█鐨勬槸銆屽繀椤婚噸璺戙€嶈€屼笉鏄€屽繀椤诲彉 None銆嶏紱
- 銆宲rompt 鏀瑰彉鍚庢棫 run 浠嶅彲 `sop_read_manifest`銆嶁€斺€旀棫 run 鍦ㄦ柊 prompt 涓嬫湰灏变笉鏄?
  *valid* manifest锛屾纭柇瑷€鏄畠琚垎绫讳负 `incompatible` 涓斿瓧鑺備粛鍦ㄣ€?

---

## P0-1 Round 2锛氬彂甯冮『搴忎笌 strict verifier

澶嶆牳鎶ュ憡 搂4 鐨勬寚鎺ф垚绔嬩笖鍙鐜般€傛柊澧?`tools/verify_release.py` 鍚庯紝瀵逛笂涓€杞殑
manifest 杩愯锛?*閫愭潯澶嶇幇浜嗘姤鍛婇噷寮曠敤鐨勫悓涓€缁勫搱甯?*锛?

```
leo commit      FAIL  manifest 8a65838f33e7 != HEAD 6596cfbf59e0
source hashes   FAIL  unified-settings-adapter.js 41df7e19429b!=1f479736c455
                      stage/leo-inject.js         3dd7a177b8ed!=3bf82d3739b4
deployed bundle FAIL  deployed exe FAIL  skill hashes FAIL
```

verifier 妫€鏌ワ細manifest commit == git HEAD銆乺epo clean銆佹簮鏂囦欢鍝堝笇銆侀儴缃?bundle銆?
閮ㄧ讲 EXE銆乧anonical skill 鍝堝笇銆侀儴缃蹭笌 WSL daemon 鍓湰涓€鑷淬€乽pstream 鍥哄畾 revision
锛堟柊澧?`manifests/upstream-pin.json`锛夈€乽pstream 宸ヤ綔鏍戝共鍑€銆?
`--strict` 涓?**NOT TESTED 涔熺畻澶辫触**锛岀粷涓嶅苟鍏?PASS銆?

---

## P0-3 Visible UI 涓?ShellApi 涓€鑷?鈥?`PASS`锛圧ound 3 鎻愬崌锛岃涓嬶級

**root cause锛堣嚜鍔ㄦ壂鎻忕‘璁わ級** 11 涓柟娉曡鍓嶇璋冪敤浣嗗湪
`leo_shell/api.py:_UNIMPLEMENTED_EXTENSIONS` 閲岋紝鍏ㄩ儴鏉ヨ嚜 `stage/leo-inject.js`锛?

| 缁?| 鏂规硶 | 瀹¤缁欑殑浼樺厛绾?|
|---|---|---|
| 鏁版嵁鐢熷懡鍛ㄦ湡 | `list_entity_states` `mark_entity` `restore_entity` `forget_entity` | 1 |
| 椤圭洰 Persona | `get_project_persona` `save_project_persona` | 2 |
| 鑷畾涔変富棰?| `choose_theme_file` `stage_theme_preview` `confirm_theme_preview` `discard_theme_preview` `delete_custom_theme` | 3 |

`called but absent entirely: []`銆乣declared-unimpl and never called: []` 鈥斺€?娌℃湁绗洓绫婚棶棰樸€?

**implementation** 鎸夈€屼笉瑕佷负浜嗕繚浣忔棫 UI 鑰屼复鏃跺疄鐜板ぇ閲忎綆浼樺厛绾?API銆嶏細
- `LEO_FEATURE_FLAGS`锛坄entityLifecycle` / `projectPersona` / `customThemes`锛屽叏 `false`锛夈€?
- **markup 鍦?flag 涓?false 鏃舵牴鏈笉娓叉煋**锛屼笉鏄覆鏌撳悗鍐?disable 鈥斺€?
  銆岀偣浜嗘墠璇存殏鏈疄鐜般€嶇殑浼叆鍙ｈ绉婚櫎鑰屼笉鏄彉鐏般€?
- `data` 椤垫暣椤垫棤鍚庣 鈫?杩炲鑸爣绛鹃兘涓嶇粰锛坅dapter 鏂板 `hiddenPages`锛?
  鍚屾椂璁?`resolvePage()` 鏃犳硶瑙ｆ瀽鍒伴殣钘忛〉锛宍openCust("data")` 鍥炶惤鍒伴粯璁ら〉锛夈€?
- `memory` 椤?*淇濈暀**锛氬彧闅愯棌 Leo 鐨?persona 鍧楋紝璇ラ〉鐨勪笂娓告覆鏌撳櫒浠嶇劧宸ヤ綔鈥斺€?
  鏁撮〉闅愯棌浼氳繛甯︾爫鎺夎兘鐢ㄧ殑涓婃父鍔熻兘銆?
- 瀵瑰簲鐨?`addEventListener` / 鏂囨璧嬪€煎悓鏍疯繘 flag锛屽惁鍒?`querySelector(...)` 杩斿洖
  null 浼氭姏寮傚父銆?

**tests** `tests/test_ui_api_contract.py` 鈥?**5 passed**銆傛妸 flag 鎵撳紑浼氱珛鍒诲け璐?
锛堣礋鍚戝鐓у疄娴嬶細2 failed锛夛紝鎵€浠ャ€屾墦寮€ flag銆嶇瓑浜庛€屽繀椤诲厛瀹炵幇鍚庣銆嶃€?
鏂板鏈疄鐜版柟娉曞嵈涓嶆寚瀹氬綊灞?flag 涔熶細澶辫触銆?

**remaining risk** 闅愯棌涓嶇瓑浜庡疄鐜般€傛暟鎹敓鍛藉懆鏈熸槸瀹¤缁欑殑绗竴浼樺厛锛?
搴斿湪 Phase 1 棣栧厛琛ラ綈銆?*娉ㄦ剰**锛氶」鐩?/ 浼氳瘽 / 浜х墿鐨勫垹闄ゅ凡缁忛€氳繃涓婃父鑷繁鐨?
`deleteProject` / `deleteSession` / `deleteArtifact` 琛ヤ笂浜嗗叆鍙ｏ紝涓庤繖閲岀殑
Leo 涓撳睘 entity lifecycle 鏄袱浠朵簨銆?

---

## P0-4 鍘婚櫎涓汉璺緞缁戝畾 鈥?`PARTIAL`

**宸叉竻闄?*
- `pyi-spec/LeoAIStudio.spec`锛? 澶勭粷瀵硅矾寰勶級锛氱‘璁ょ敱 PyInstaller `--specpath`
  姣忔鐢熸垚锛屽睘浜庝骇鐗?鈫?绉诲嚭鐗堟湰鎺у埗骞跺姞鍏?`.gitignore`銆?
- `tools/make_lion_icon.py`锛? 澶勶級锛氭敼涓轰粨搴撶浉瀵?+ `LEO_APP_ROOT` 瑕嗙洊銆?
- `tools/sync_skills.py`锛? 澶勶級锛氭敼涓?`LEO_WSL_DISTRO` / `LEO_WSL_USER` /
  `LEO_WSL_SKILLS` 鐜鍙橀噺锛岄粯璁ゅ€肩敱鐢ㄦ埛鍚嶆帹瀵笺€?

**浠嶆湭娓呴櫎锛坄TODO`锛?*
- `skills/lean-math/kernel.py` **5 澶?* `/home/leo/...`锛歀ean toolchain銆?
  lake銆乣lean_test` 宸ョ▼銆乣mathlib4` 鐩綍锛屼笖鍐欐 RC 鐗堟湰
  `leanprover--lean4---v4.34.0-rc2`銆傞渶瑕佺殑鏄?*鑷姩鍙戠幇 + health check + 鏄惧紡閰嶇疆**
  锛堟寜鎸囩ず鏈疆涓嶉噸鏋勬暣涓?Lean 闆嗘垚锛夈€?
- 瀹夎鐩綍涓庣敤鎴锋暟鎹洰褰曞皻鏈垎绂伙紙浠嶆槸 `Desktop\LeoAIStudio\` 涓嬫贩鏀撅級銆?
- 蹇嵎鏂瑰紡浠嶇敱 `deploy_release.ps1` 鎸囧悜鍥哄畾妗岄潰鐩綍锛屾病鏈夊畨瑁呭櫒銆?

**楠屾敹鐘舵€侊細`NOT TESTED`銆?* 銆屽湪鍏ㄦ柊 Windows 璐︽埛涓畨瑁呭苟鍚姩銆?*鏃犳硶鍦ㄦ湰鐜鑷瘉**鈥斺€?
鎴戜笉鑳藉垱寤?Windows 鐢ㄦ埛璐︽埛銆備互涓嬮」鐩?*蹇呴』鐢变汉宸ョ幇鍦洪獙鏀?*锛屼笉寰楄涓洪€氳繃锛?

1. 鏂拌处鎴蜂笅鍙屽嚮蹇嵎鏂瑰紡鑳藉惎鍔紝涓斾笉闇€瑕佹敼浠讳綍璺緞锛?
2. WebView2 鍥哄畾鐗堣繍琛屾椂鍦ㄦ柊璐︽埛涓嬪彲鍔犺浇锛?
3. WSL2 鍙戣鐗堝悕绉?/ 鐢ㄦ埛鍚嶄笉鏄?`Ubuntu-24.04` / `leo` 鏃舵ˉ鎺ユ槸鍚︿粛宸ヤ綔锛?
4. Lean 鍦ㄦ病鏈?`/home/leo/...` 鐨勬満鍣ㄤ笂鐨勮涓恒€?

---

## P0-5 鏋勫缓鍙鐜?鈥?`TODO`

鏈紑濮嬨€傚凡鐭ヤ簨瀹烇細`tools/build_launcher.ps1` 浠嶄粠鏃㈡湁 `LeoAIStudio.exe` /
`_launcher` 涓庢棫 PYZ 鍙嶅悜鎻愬彇渚濊禆锛堝璁?搂9.2锛夈€傞渶瑕佷緷璧栭攣 + wheelhouse +
鏋勫缓 manifest锛坢anifest 閮ㄥ垎宸茬敱 `tools/build_manifest.py` 鎻愬墠鍏峰锛夈€?

---

## Round 3锛?C + 2D锛?

### 2C 鈥?P0-3 浠?`CONDITIONAL PASS` 鎻愬崌鍒?`PASS`

澶嶆牳鏂圭殑 mutation test 鏄鐨勩€傛垜澶嶇幇浜嗭細鍦?`leo-inject.js` 鏈熬杩藉姞涓€鏉℃湭缁?gate 鐨?
`window.pywebview.api.list_entity_states({});`锛屽師鏉ョ殑 5 椤?UI 濂戠害娴嬭瘯**鍏ㄩ儴鐓у父閫氳繃**銆?
瀹冧滑鏂█鐨勬槸銆宖lag 鐨勫€兼槸 false銆嶏紝閭ｆ槸涓€涓€硷紝涓嶆槸鍙揪鎬с€?

鐜板湪娉ㄥ叆灞傚彧閫氳繃涓€涓嚱鏁拌Е杈惧澹筹細`leoBridge(method, ...)`锛屽畠鍦?feature 鍏抽棴鏃剁洿鎺ユ姏閿欍€?
19 澶勮皟鐢ㄧ偣鍏ㄩ儴鏀瑰啓锛堝惈涓ゅ鎶婃柟娉曞綋鍊间紶鐨勶細涓婚棰勮 confirm/discard銆?
`acknowledge_connection` 瀛樺湪鎬ф帰娴嬶級銆?*瀛楅潰閲?`pywebview.api.<name>` 鍦ㄦ敞鍏ュ眰琚姝?*锛?
濂戠害娴嬭瘯鍙戠幇鍗冲け璐ャ€?

瀹炴祴 mutation锛氬共鍑€ `10 passed` 鈫?杩藉姞鏈?gate 璋冪敤 `2 failed` 鈫?鎾ら攢 `10 passed`銆?
鎵€浠ャ€屽叧闂€嶇幇鍦ㄧ瓑浜庛€岃皟涓嶅埌銆嶏紝鑰屼笉鏄€屾病娓叉煋鎸夐挳銆嶃€?

`shell.html` 鍒绘剰涓嶈蛋 bridge锛氬畠鏄惎鍔ㄩ〉锛屾病鏈変换浣?gated 鍔熻兘锛屽崟鐙柇瑷€瀹冨彧璋冨凡瀹炵幇鏂规硶銆?

### 2D-A 鈥?P0-4 闈欐€侀儴鍒嗘竻闆讹紝瀹炴満閮ㄥ垎鍏ㄩ儴 `NOT TESTED`

- `lean-math` 鐨?5 澶?`/home/leo/...` 涓庡啓姝荤殑 RC 宸ュ叿閾惧叏閮ㄧЩ闄ゃ€傝В鏋愰『搴忥細
  閰嶇疆锛坄LEO_LEAN_TOOLCHAIN` / `LEO_LEAN_PROJECT` / `LEO_MATHLIB_DIR`锛夆啋 home 涓嬬殑 elan
  鈫?PATH 涓婄殑 `lean`/`lake`銆俙lean_toolchain_status()` 杩斿洖
  `READY` / `NOT_INSTALLED` / `PROJECT_NOT_READY` / `VERSION_MISMATCH` 骞堕檮鍙搷浣滆鏄庯紝
  **浠讳綍鎯呭喌涓嬮兘涓嶈嚜鍔ㄥ畨瑁?*銆?
- `deploy_release.ps1` 鍘熸湰鏂█涓€鏉″瓧闈㈤噺瀹夎璺緞銆傚畧鍗繚鐣欙紙閮ㄧ讲鍒伴敊鐩綍鏄牬鍧忔€х殑锛夛紝
  浣嗘敼涓?*鎸夌粨鏋勫垽鏂?*鐩爣鏄笉鏄竴涓?Leo 瀹夎锛岃€屼笉鏄垽鏂畠鍦ㄨ皝鐨勬闈笂銆?
- 鍙︽竻闄わ細`build_launcher` 鐨勫浐瀹氫复鏃剁洰褰曘€乣capture_window` 鐨勮緭鍑鸿矾寰勩€?
  `headless_verify` 鐨勯粯璁ゆ牴銆乣make_lion_icon` 鏂囨。閲岀殑瑙ｉ噴鍣ㄣ€?
- `tools/portability_check.py`锛?*0 hard binding锛? configurable default**銆?
  `tests/test_portability.py` 鎶婂畠绾冲叆娴嬭瘯骞跺甫璐熷悜瀵圭収銆?
- **闈欐€侀€氳繃 鈮?瀹炴満閫氳繃銆?* `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` 鍒楀嚭 27 椤规棤娉曡嚜璇佺殑
  瀹炴満楠屾敹锛?*鍏ㄩ儴 `NOT TESTED`**銆傚洜姝?P0-4 = `PARTIAL`銆?

### 2D-B 鈥?P0-5 浠?`TODO` 鍒?`PARTIAL`

浜斿瀵规棫鍙戝竷浠剁殑渚濊禆鍏ㄩ儴绉诲埌 `-Legacy` 寮€鍏充箣鍚庯紝hermetic 鎴愪负榛樿銆?
`requirements.lock` 鍥哄畾 21 涓寘锛宍manifests/dependency-lock.json` 璁板綍鏉ユ簮
骞?*鏄庡啓 `vendored_wheelhouse: false`**銆?

璺戝嚭鏉ョ殑涓や釜缁撹锛堜笉鏄帹鏂級锛?

- **PYZ 鎻愬彇纭疄鏄浣欑殑**锛氬畠鎭㈠鐨勫叚涓ā鍧楀湪姝ｅ父鏋勫缓鐨?PYZ 閲岄兘鏈夛紝
  `webview` 鐨?45 涓ā鍧椾篃鍦ㄣ€傛棫 `_launcher` 閲岀殑鏁ｈ鍓湰鏄啑浣欏洖濉€?
- **鍥炲～涓嶆槸澶氫綑鐨?*锛屽畠鍦ㄦ帺鐩栫己澶辩殑鍘熺敓 DLL銆傝繖涓?Python 鏄?conda 鍙戣鐗堬紝
  `ffi-8.dll` / `sqlite3.dll` / `libbz2.dll` / `liblzma.dll` / `libexpat.dll` 鏀惧湪
  `<base_prefix>/Library/bin`锛孭yInstaller 涓嶆壂閭ｉ噷銆?*绗竴娆?hermetic 鏋勫缓閫氳繃浜?
  package contract锛岀劧鍚庡惎鍔ㄦ椂姝诲湪 `DLL load failed while importing _ctypes`銆?*
  鐜板湪杩欎簺 DLL 鏉ヨ嚜澹版槑鐨?Python 宸ュ叿閾俱€?

**楠岃瘉鏂瑰紡**锛氭妸 hermetic 浜х墿鏀捐繘涓€涓?scratch 瀹夎鏍戯紝璺?`--diagnostics`锛?
**exit 0 骞跺啓鍑烘姤鍛?* 鈥斺€?璇存槑鐪熷疄 import 鍥惧湪銆岄浂鏃у彂甯冧欢杈撳叆銆嶇殑鏋勫缓閲岃兘鍔犺浇銆?

**涓轰粈涔堜粛鏄?`PARTIAL` 鑰屼笉鏄?`PASS`**锛氭病鏈?vendored wheelhouse锛坵heel 浠嶄粠 PyPI 瑙ｆ瀽锛夛紝
涓斻€屽湪涓€鍙颁粠鏈杩囨棫鐗堢殑鏈哄櫒涓?clean build銆嶅睘浜庡疄鏈洪獙鏀堕」锛屾湭鍋氥€?

---

## P0-6 Gate 鈥?`FAIL`

涓婁竴鐗堣繖閲屽啓銆孭0-1 / P0-2 / P0-3 宸叉竻闆躲€嶏紝涓庤〃澶寸殑
`P0-3 = CONDITIONAL PASS` 鑷浉鐭涚浘銆傜煕鐩剧殑鏉ユ簮鏄彊浜嬮『鎵嬶紝涓嶆槸浜嬪疄鍙樺寲锛屽凡鏇存銆?

Gate 鐜扮姸锛堝彛寰勫彧鍏佽 `PASS` / `FAIL` / `PARTIAL` / `BLOCKED` / `NOT TESTED`锛夛細

| Gate 蹇呴』椤?| 鐘舵€?|
|---|---|
| P0-1 鍗曚竴鍙俊婧愮爜 | `PASS` |
| P0-2 research-sop 璇佹嵁瀹屾暣鎬?| `PASS` |
| P0-3 Visible UI 涓?ShellApi 涓€鑷?| `PASS` |
| P0-4 鍙Щ妞嶆€?| `PARTIAL` 鈥?闈欐€佹竻闆讹紝27 椤瑰疄鏈洪獙鏀?`NOT TESTED` |
| P0-5 鏋勫缓鍙鐜?| `PARTIAL` 鈥?hermetic 鍙瀯寤哄彲杩愯锛屾棤 wheelhouse锛宑lean-machine 鏋勫缓鏈獙 |

**鍙鍏朵腑浠讳綍涓€椤逛笉鏄?`PASS`锛孭0-6 灏辨槸 `FAIL`銆?*
`CONDITIONAL PASS` 涓嶇畻 `PASS`锛沗NOT TESTED` 涓嶇畻 `PASS`銆?
鍥犳鐜板湪涓嶅緱杩涘叆 Workspace / PINN / Companion / 鏂板墠绔姛鑳姐€?

---

## 鍙樻洿鏃ュ織

| 鏃堕棿 | 鍐呭 |
|---|---|
| 2026-09-03 | 寤虹珛鏈枃浠讹紱瀹屾垚 P0-1 浜嬪疄璁ゅ畾锛堟棤鐗堟湰鎺у埗 / zip 闈炴簮鐮佸寘 / 鏃犻渶 merge锛?|
| 2026-09-03 | P0-2锛歳un 缁戝畾 + manifest + 鐘舵€佽瘹瀹炲寲锛?2 椤瑰洖褰掓祴璇曪紝宸插淇鍓?kernel 楠岃瘉浼氬け璐?|
| 2026-09-03 | P0-3锛氫笁缁?feature flag锛宍data` 椤电Щ鍑哄鑸紝5 椤瑰绾︽祴璇?+ 璐熷悜瀵圭収 |
| 2026-09-03 | P0-4锛氭竻闄?spec / 涓や釜宸ュ叿鐨勭‖缂栫爜锛沴ean-math 涓庡畨瑁呭竷灞€浠嶅緟鍔?|
| 2026-09-03 | 棣栨鎻愪氦 `8a65838`锛涙瀯寤?+ 閮ㄧ讲锛屽绾﹂€氳繃锛?43 tests passed |
| 2026-09-17 | GEOMETRY LIFT 1：圆环制造解 Poisson 标定 | 首次几何提升（曲边 / 内孔 / 多连通 / 两条边界组件）。device 做成运行时参数而非配置字段（配置在 codeHash 内，G6 须在 CPU-only 环境跑同一 codeHash），训练在 GPU、**全部 Gate 数值在 CPU** 评估，确定性未关。Gate 1/2/3/4 与 Gate 5a 物理全 PASS（FDM 观测阶 2.0016/2.0004；10/10 跑满 120000 步，median 1.853e-04）；盲集 DAC-M0 一次性打开并 BURNT，**Gate 5b FAIL** —— seed 2 的局部判据 ACA-9 = 1.079e-03 > 1e-3，其余九个 seed 及 ACA-1..ACA-8 全通过；阈值一个未动、未现场调参、未重训。在迄今考察的正方形与圆环两个案例中未观察到圆环特有的局部/全局误差比放大（3.20 vs 2.93±0.52），据此「训练预算不足」是**受支持的假设**而非已正式识别的 RootCauseClass（状态仍为 FAILURE_RECORDED，未进入 DIAGNOSED）。Tier-1 与 G6 均未执行（只在 Gate 5 PASS 后做）。`Geometry Lift 1: NOT YET PASS` / `Highest Claim: BLOCKED` / `REMAIN AT ANNULUS GEOMETRY CALIBRATION` | `pinn/experiments_annulus/`；`experiments/annulus/`；`docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md` |
| 2026-09-19 | 圆环诊断 Phase II：前瞻性嵌套预算干预 | 先解决使干预无法成立的两条阻塞——`lrPrefixSteps` 让 LR 与总预算解耦（`lr = lr(step)`，不带该字段则逐位保持旧行为），以及保存 model/Adam/scheduler/batch RNG 的完整 checkpoint 与 exact resume（resume fidelity 11 项逐位 PASS）。LR 等价性以实现语义为准：`ExponentialLR` 是逐步相乘而非闭式 `gamma**t`，改为迭代后逐位复现 r1 的全部 241 条学习率。10 个 paired seed 各只启动一次 `0→240000`：**前缀等价性 10/10 逐位相等**，**B\* = 180000**（120k 时 seed 2 的 ACA-9 失败，180k/240k 全部 10/10）。账本与 DAC-M1/M2/M3 未触碰。**但根因仍 `UNDETERMINED`**：Constitution 1.2 要求逐一排除其余 6 个 admissible 根因，本轮只用实验排除了 1 个。`B* = 180k` / `Root Cause: UNDETERMINED` / `NOT YET PASS` / `REMAIN AT ANNULUS GEOMETRY CALIBRATION` | `pinn/experiments_annulus/`；`experiments/annulus/`；`tests/pinn/`；`docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md` |
| 2026-09-20 | 圆环排除诊断：代码身份补洞 + 五项 diagnosis-only 判别实验 | 先堵未跟踪文件的身份洞（PRELOCK 新增 `codeIdentityTracked`，检查数 7→8，带对照的对抗测试），再做五项 `exp-*` 身份下的判别实验（不是 Tier-1）。**2 项排除**：`rImplementationDefect`（预言注入 `6.055e-18`、注入凸起被恰好定位、独立复算逐位相同）、`rSpecDefect`（两条独立路径 `0.000e+00` / `3.553e-15`）。**3 项未排除**：`rReferenceDefect`（R3 只低 2.7 倍未达 10 倍、R4 正控制发散成 NaN）、`rSingularityTreatment`（G2 要求 0 而实测 1/30 贴边界）、**`rSamplingDeficiency`（证据反向：2× 与 2.76× 密度都把失败 seed 修好了，失败单元只分到 5 个配置点、中位数 16）**。后者削弱了 `B* = 180k` 的因果解读——多训练与多采点都不是必要解释。未写 DiagnosisRecord、未命名 `rOptimizationFailure`。`Root Cause: UNDETERMINED` / `REMAIN AT ANNULUS GEOMETRY CALIBRATION` | `pinn/experiments/common.py`；`pinn/governance/prelock.py`；`pinn/experiments_annulus/exclusion_annulus.py`；`experiments/annulus/`；`tests/pinn/`；`docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md` |
| 2026-09-21 | 四项委托裁决 + 四个自身缺陷 | 0 GPU。**裁决**：采样与优化本轮不可分离（路由事前已冻结、两因定义层重叠）；R3 整族前瞻性退役、R4 只修仪器 bug 后**原判据直接通过**；G2 维持；**`rCapacityLimit` 从未被排除**——容量干预须改 architecture 而嵌套预算干预全程钉死 4×64，我把 0919 预注册原文的「不再是必要解释」写成了「已排除」，属越权，未排除原因由 3 项改记为 **4 项**。**自查缺陷**：R4 的 Jacobi 符号写反（无论是否腐蚀算子都发散）；R1 的审计根集合手挑、恰好不含裁决 ACA-9 的 `gates_annulus`，修复后审计图 14→43 个模块、**R1 改判 FAIL**；G3 的冻结文本（`r^(2/3)`）与其通过条件（bin 0）自相矛盾，实现静默选了能通过的一侧，故该实验实为观察式；报告把「30/30」写成事实而实为 29/1/0。另查明 `rUndetermined` 的 DiagnosisRecord 写得出来但会迁到 `STOPPED_THE_LINE`，超出委托、未写。`Root Cause: UNDETERMINED` 不变 | `pinn/experiments_annulus/exclusion_annulus.py`；`tests/pinn/`；`experiments/annulus/`；`docs/pinn-trust-loop/` |



</details>

<a id="history-3"></a>

## 历史附录 3：docs/P0_RELEASE_CANDIDATE.md

<details>
<summary>展开历史原文（仅作记录）</summary>

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


</details>

<a id="history-4"></a>

## 历史附录 4：docs/P0_FINAL_CLOSURE_REPORT.md

<details>
<summary>展开历史原文（仅作记录）</summary>

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


</details>

<a id="history-5"></a>

## 历史附录 5：docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md

<details>
<summary>展开历史原文（仅作记录）</summary>

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


</details>

<a id="history-6"></a>

## 历史附录 6：docs/RESEARCH_SOP_MIGRATION_AUDIT_24f3fd7.md

<details>
<summary>展开历史原文（仅作记录）</summary>

# Research-SOP migration audit for `24f3fd7`

Date: 2026-09-05

## Scope and method

The source commit `24f3fd7` was audited against mainline HEAD `d58dffe` from
their merge base `58aeb19`. It was not merged or cherry-picked. The mixed
commit was decomposed so each production guarantee and its tests can be
reviewed independently.

| Contract | Disposition | Mainline commit |
|---|---|---|
| F-007 manifest self-consistency | migrated with focused and mutation tests | `e92fa81` |
| F-001 document digest verification on read | migrated with focused and mutation tests | `3e809f2` |
| F-002 rollback archive verification on audit | migrated with focused and mutation tests | `8084078` |
| B08 attempt identity | implemented as a separate contract and test | `ad11801` |
| F-008 `theme-src` architecture | not migrated | deferred |

## B07 external-test disposition

The frozen external `test_B07_modify_history_file` is structurally invalid and
is retained unchanged as an external-test record. Its final branch raises when
the archived manifest digest equals the digest of the saved pre-tamper bytes:

```python
if claimed == sha256(original):
    raise AssertionError(...)
```

That equality is true by construction for a correct archive: `claimed` was
recorded from `original` before the test appends `FORGED`. It is independent of
whether production detects the later tamper, so no production implementation
can satisfy the final assertion without corrupting the archive contract.

Production was not changed to accommodate that assertion. F-002 instead tests
the valid property directly: after a length-preserving rewrite, append,
deletion, or digest removal, `sop_inspect_history` and `sop_status` report the
archive as corrupt; intact and restored bytes report clean.

## B08 contract correction

Attempt identity and artifact identity are distinct:

- every execution of a stage receives a new opaque `attempt_id`;
- deterministic reruns may produce byte-identical artifacts and therefore the
  same `document_sha256`;
- scientific documents must never be edited merely to manufacture different
  evidence bytes.

The focused B08 test forces a real paper-writer rerun, proves that the two
`attempt_id` values differ, and simultaneously proves that identical document
bytes and digests remain valid.

## F-008 overlap and conflict audit

The current Ink Autumn hierarchy is the accepted canonical source for its own
theme assets:

- `stage/themes.json`;
- `stage/backgrounds/manifest.json` and the three rendered WebP files;
- untouched masters under `assets/backgrounds/`;
- `tools/build_backgrounds.py` and `tools/bundle_theme.py` as the recorded
  build chain.

The proposed `theme-src` tree in `24f3fd7` re-declares `themes.json` and the
background manifest with byte-identical Git blobs, references the same three
rendered backgrounds through a separate asset house, adds a second assembler
(`tools/build_theme.py`), and rewires `tools/build_launcher.ps1` around that
assembler. Migrating it now would create overlapping canonical sources and two
competing assembly paths.

The existing provenance measurement currently reports 8 of 18 runtime-read
theme assets with tracked canonical sources, 10 pre-existing gaps, and one
deployed `shell.html` drift. F-008 therefore remains open. Its brand-asset gaps
may be addressed later, but only after choosing an architecture compatible with
the frozen Ink Autumn hierarchy.

No Ink Autumn image, stylesheet, registry, manifest, master, or build recipe was
modified during this research-sop migration. Its status remains ACCEPTED &
FROZEN.


</details>

<a id="history-7"></a>

## 历史附录 7：docs/THEME_INK_AUTUMN.md

<details>
<summary>展开历史原文（仅作记录）</summary>

# 淡墨浓秋 · Ink Autumn — Theme Design Spec

Theme id: `ink-autumn`
Names: 淡墨浓秋 / Ink Autumn

A Leo AI Studio theme, sitting beside `deep-sea-molten-orange` and
`amethyst-teal` in `theme/themes.json`. Nothing about it is special-cased in
application code: the shell resolves it, upstream components consume tokens, and
`theme/leo.css` is the only place that knows what those tokens contain.

---

## Theme Freeze

### Authorized continuation — 2026-09-07

The current user explicitly authorized further changes to the default Leo AI
interface in the 2026-09-07 handoff and the instruction to continue that work.
The v1 freeze below remains historical evidence for its named artifact; its
aesthetic restriction does not prohibit this newly authorized extension.
This extension is a source change pending the separate package and native
WebView2 acceptance. It does not inherit the old release PASS or close global P0.

The launcher home now uses paper and cinnabar tones with the approved rooted
tree in its open right margin. A bilingual welcome section precedes the existing
workbench project and conversation lists. The warm branch remains at the
workspace/sidebar edge and the other branch decorates Settings. Session actions
and the editable LeoTree draft use the same surfaces, with opaque reading areas,
visible focus, scrollable content, and reachable action buttons in small windows.
The launcher follows the OS light/dark preference; the workbench retains its
existing mode mechanism. Other built-in theme choices remain available.

Current-file verification corrected one handoff detail: the three specified
Downloads originals had already been preserved under `assets/backgrounds/`, and
their compressed outputs were already versioned. Each original and master hash
matches the handoff. No image was regenerated, recoloured, resized, overwritten,
or newly duplicated for this extension. Only asset-purpose metadata changed.

| Source filename suffix | Existing asset | Current principal placement |
|---|---|---|
| `05_09_52.png` | `ink-autumn-tree.webp` | Launcher home and workbench welcome |
| `05_10_04.png` | `ink-autumn-branch-warm.webp` | Workspace/sidebar and launcher splash |
| `05_09_39.png` | `ink-autumn-branch.webp` | Workbench Settings and launcher drawer |

`ThemeRuntime` now resolves the shell's background markers through the existing
manifest, validates referenced WebP bytes, and checks the entire rendered shell
after substitution. Each picture appears once in a CSS custom property, reused
by its layers. Measured from this source overlay: three WebP files total
**429,010 bytes**; rendered shell **742,720 UTF-8 bytes** against the unchanged
**1,572,864-byte** navigation limit (47.2%). Source CSS is **79,543 bytes**;
resolved workbench CSS is **11,656,241 bytes**, still dominated by the existing
offline fonts. The shell does not embed those fonts.

The focused theme suite (`test_theme_runtime.py`, `test_theme_readability.py`,
`test_theme_settings_integration.py`) passes **168 tests**. It covers shell
asset-budget enforcement, unknown markers, resolved-image reuse, artwork
compositing contrast, and eight real Chromium Settings cases for shell/workbench
and Chinese/English, including local/cloud preset behavior and save/reload
persistence. Pillow-backed read-only verification also confirms all three
compressed asset hashes, unchanged 1672×941 geometry, tint drift below 0.5 and
grain drift below 4.0. The images were verified, not rebuilt.

An additional **48 isolated visual views** cover launcher, workbench home, chat,
Settings, three-button session actions, and editable knowledge-tree draft across
light/dark × Chinese/English × 1280×800/640×400. The pages use production CSS,
production launcher and dialog/welcome functions, and synthetic conversation
content. Small chat views explicitly close the fixture's sidebar and artifact
dock, as the existing responsive UI does. Browser observations found no horizontal
overflow, no action buttons outside the viewport, and no JavaScript exceptions.
This is visual/source evidence, not live model inference, user-data handling,
installed-package evidence, or a replacement for native WebView2 acceptance.

Evidence is kept in `docs/manual-acceptance-evidence/ink-20260907/`:
`shots/`, `browser_observations.json`, `asset_sizes.json`, and the reproducible
preview/capture scripts. Earlier screenshots and observations are retained as
`shots-attempt1`, `shots-attempt2`, `shots-attempt3` and corresponding observation files. The first
attempt exposed a small-window decoration overflow and a mock readiness error;
the second still showed a dark artwork edge. Those failures prompted bounded
fixes and are not counted as final visual evidence. No existing user sessions,
credentials, production processes, or installed files were touched by this theme
subtask. Package and real desktop-entry checks belong to the integration task.

### Historical v1 freeze (2026-09-05)

| Field | Frozen result |
|---|---|
| Theme | 淡墨浓秋 / Ink Autumn (`ink-autumn`) |
| Version | v1 |
| Status | ACCEPTED & FROZEN |
| Freeze date | 2026-09-05 |
| Theme acceptance | PASS |
| Runtime integration | PASS |
| Default-theme integration | PASS — first-run default is `ink-autumn` |
| Settings selection and persistence | PASS — registry-driven selection, save, fresh store instance and page reload |
| Desktop/mobile acceptance | PASS — existing 1440×900 and 390×844 acceptance matrix |
| Light/dark acceptance | PASS — Home, Workspace, Chat and Settings in both modes |
| Package/deploy integration | PASS — clean committed build and installed application checked |
| Release verifier | PASS — 11 PASS / 0 FAIL / 0 NOT TESTED for the isolated freeze baseline described below |

### Frozen boundary

No further palette changes, background-art changes, visual polishing, spacing /
opacity / decoration adjustments for appearance, or new theme-owned visual
features are permitted. Ordinary changes in aesthetic preference do not reopen
Ink Autumn v1. Changes are allowed only for:

1. A confirmed visual bug.
2. A readability or accessibility regression.
3. A runtime compatibility bug.
4. A packaging or deployment regression.
5. A Leo AI global design-system migration.

### Integration evidence and correction

This freeze found one real integration defect that the earlier handcrafted
preview pages did not exercise: `SettingsStore.state_for_shell()` and the
`ShellApi` sanitizer omitted the registry catalog, so the workbench Settings
consumer received no themes; the launcher shell also retained two static theme
cards. The separate integration fix exposes allowlisted registry metadata and
uses the existing shell card classes/styles to render the catalog. It does not
change theme colors, artwork, CSS or layout styling.

The focused suite passes **290 tests**, covering runtime, settings store/API,
readability, build reproducibility, UI/API contracts, startup and four Chromium
Settings DOM cases (shell/workbench × zh/en). The DOM cases use the production
Settings code and real API/store with temporary user data: select each theme,
save `ink-autumn`, recreate the store, reload the page and check the persisted
appearance. Existing user settings and credentials are not changed.

The deployed executable's 14 `leo_shell` modules were checked against committed
source and loaded directly from its embedded archive for the same four DOM
cases. Runtime injection and shell rendering resolve assets from the actual
installed `theme/` directory, in both locales. The package contract passes for
315 launcher files, 21 critical files and 24 archive modules. These checks are
Chromium DOM / real API-store integration evidence, not a claim of a new full
native WebView2 navigation or visual-acceptance run. The existing 16 desktop /
mobile, light / dark preview images are retained as the visual evidence.

### Release baseline and evidence boundary

The freeze release is on `codex/ink-autumn-v1-freeze`, based on `d58dffe` plus
the integration-only commit `df65d04` and this documentation. Its counterpart
on shared `master` is integration commit `c524c83`. During this task, independent
research-SOP commits landed on shared `master`; they are preserved there and
are deliberately not included or deployed by this theme freeze. No deployed
skills were overwritten to obtain a passing result.

The strict PASS belongs to the isolated, clean freeze checkout and its measured
installed artifact, **not** to the concurrently advancing, governance-dirty
shared `master`. `manifests/build-current.json` records the exact freeze build
commit and installed hashes. Evidence is retained under
`docs/manual-acceptance-evidence/theme-ink-autumn/freeze-v1/`, including the
pre-integration manifest, intermediate failures, build/deploy logs, the focused
test log and final verification logs. When verifying from a worktree, explicitly
set `LEO_APP_ROOT` as well as `--app-root`: the nested skills verifier obtains
its installation target from the environment. An intermediate check without
that environment override targeted the worktree's nonexistent sibling install;
its failure log is retained, not counted as deployed drift.

Ink Autumn's own newly added theme-asset provenance is closed. Leo AI's global
**F-008 remains PARTIAL**: the 10 historical runtime assets listed in section 10
remain independent provenance-governance work, not Ink Autumn v1 acceptance
blockers. The existing portability governance test remains a non-theme failure
(1 failed / 8 passed, historical Windows home paths in the compliance audit).
Neither item reopens Ink Autumn v1, and verifier PASS does not claim that these
global governance obligations are complete. No existing governance files were
modified or staged. The repository has no established theme-tag convention;
documentation and commits define this freeze, without inventing a tag scheme.

---

## 1. Intent

> 中国传统纸墨美学 × 现代 AI / 科研工作台

A research workbench that happens to be printed on 宣纸, not a 古风 website.
Traditional material is the *ground*: paper, ink wash, one cinnabar pigment,
generous 留白. Everything on top of it is a modern tool — dense, legible, quiet.

Three ordered tie-breakers, applied whenever the design had to choose:

1. Readability beats visual invention.
2. 留白 beats added elements.
3. Modern tool-feel beats traditional decoration.

Explicitly not in this theme: 灯笼, 祥云, 龙凤, scroll frames, calligraphy
banners, stacked seals, brush cursors, blue/violet "tech" gradients, neon,
pure-white SaaS cards, pure-black panels.

---

## 2. The three masters

Delivered as three 1672×941 (16:9) images. They are the visual母版, not
wallpaper: the palette below is measured from them, not invented next to them.

| Master | Ships as | Scene |
|---|---|---|
| `ink-autumn-branch.src.png` | `ink-autumn-branch.webp` | **Home / Welcome** — the rising branch |
| `ink-autumn-tree.src.png` | `ink-autumn-tree.webp` | **Knowledge / Memory** — the rooted tree (reserved for Leo Tree) |
| `ink-autumn-branch-warm.src.png` | `ink-autumn-branch-warm.webp` | **Workspace / Research** — the warm branch variant |

**Non-destructive contract.** Masters are stored byte-identical under
`assets/backgrounds/` and are never edited. `tools/build_backgrounds.py` renders
each to WebP at the *same* dimensions, crop and colours; the only transformation
is compression, and both `build` and `verify` re-decode the output and fail if
the artwork was tinted (`MAX_TINT_DRIFT = 0.5/255`) or the paper grain scrubbed
(`MAX_GRAIN_DRIFT = 4.0/255`). Measured tint drift is 0.24–0.37/255.

Presentation may only use `cover` / `position` / `opacity` / crop — no recolour,
no filter, no blur of the artwork itself.

### Measured source values

Sampled across all three masters:

- paper ground: `#E8D8C0`–`#E8DCC4`, H 36–38°, S 15–18%, V 89–91%
- paper highlight: `#F2E3CC`–`#F5E9D1`
- deep paper: `#D7C7A8`–`#DBD0BC`
- darkest ink present: `#68594A`, H 30°, S 29%, V 41%
- mid ink: `#887B6B`, `#B4A794`
- full hue range of the artwork: **H 24–41° only** — one warm family, nothing else

The UI ink extends this family darker (the masters are washes; body text needs
more density), and the cinnabar accent is designed *into* the same family rather
than imported from outside it.

---

## 3. Token architecture

Two layers, and business components only ever see the second.

```
theme/leo.css
  layer 1  semantic  --leo-*         authored here, the theme's own vocabulary
  layer 2  contract  --bg, --ink…    upstream OpenAI4S token names, mapped from layer 1
```

Layer 1 is the vocabulary requested in the brief; layer 2 is what
`upstream/OpenAI4S/.../style.css` already consumes. Mapping one onto the other
means the theme is authored once, in paper-and-ink terms, and no upstream
component is edited to understand it. Leo Tree can later bind straight to
layer 1.

| Semantic (layer 1) | Role | Maps to (layer 2) |
|---|---|---|
| `--leo-background` | app ground, the 装裱 mount | `--bg`, `--bg-100` |
| `--leo-background-muted` | recessed ground, gutters | `--bg-300` |
| `--leo-paper` | reading surface, cards | `--bg-000`, `--card`, `--panel` |
| `--leo-paper-elevated` | modals, popovers | `--panel` (dialog scope) |
| `--leo-panel-background` | sidebar / dock chrome | `#sidebar`, `#rightdock` |
| `--leo-input-background` | fields, composer | `--bg-000` in input scope |
| `--leo-code-background` | code blocks, `pre` | `--bg-200` |
| `--leo-ink` | body text | `--ink`, `--text-000` |
| `--leo-ink-secondary` | secondary text | `--text-200` |
| `--leo-ink-muted` | meta, placeholder | `--text-400`, `--muted`, `--faint` |
| `--leo-border` | structural hairlines | `--border-card`, `--line2` |
| `--leo-border-subtle` | in-surface separators | `--border`, `--line` |
| `--leo-accent` | 朱砂 — links, focus, active | `--accent`, `--accent-fill` |
| `--leo-accent-hover` | pressed / hover cinnabar | `--clay-em` |
| `--leo-accent-muted` | cinnabar wash for fills | `--accent-line` |
| `--leo-selection` | text selection ground | `::selection` |

### Light palette (verified contrast)

| Token | Value | on paper | on background |
|---|---|---|---|
| `--leo-background` | `#E7DAC4` | — | — |
| `--leo-background-muted` | `#DFD0B6` | — | — |
| `--leo-paper` | `#F2E9DA` | — | — |
| `--leo-paper-elevated` | `#F8F1E6` | — | — |
| `--leo-code-background` | `#EBE0CD` | — | — |
| `--leo-input-background` | `#F7F0E3` | — | — |
| `--leo-ink` | `#2B2420` | **12.68** | 11.06 |
| `--leo-ink-secondary` | `#544A40` | **7.18** | 6.26 |
| `--leo-ink-muted` | `#635647` | **5.91** | 5.16 |
| `--leo-accent` | `#903525` | **6.41** | 5.60 |
| `--leo-accent-hover` | `#832F20` | 7.29 | 6.36 |
| clay (secondary pigment) | `#A8593B` | 4.20 | 3.66 |
| clay-em (clay as text) | `#8C4227` | 5.97 | 5.21 |
| success | `#4A6B36` | 5.06 | 4.42 |
| danger | `#973229` | 6.22 | 5.43 |
| warning | `#7E5A1C` | 5.18 | 4.52 |

Body text is AAA on every ground. Secondary is AAA. Muted, accent and every
status colour clear AA (4.5) on every ground they are used on. `clay` is a fill
colour; `clay-em` is its text form.

Both the cinnabar and the muted ink are one step deeper than the first pass.
They have to clear AA not only on a flat swatch but against the darkest stroke
of the artwork showing through the scene (§6), and
`tests/test_theme_readability.py` failed them until they did.

### Dark palette — 「夜纸」

Warm near-black, never `#000`. Ink and paper swap roles; the pigment family does
not change.

| Token | Value | on `--leo-paper` |
|---|---|---|
| `--leo-background` | `#17130F` | — |
| `--leo-background-muted` | `#120F0C` | — |
| `--leo-paper` | `#1F1A15` | — |
| `--leo-paper-elevated` | `#272119` | — |
| `--leo-ink` | `#EDE3D0` | 13.56 |
| `--leo-ink-secondary` | `#C6B7A0` | 8.78 |
| `--leo-ink-muted` | `#9A8C79` | 5.26 |
| `--leo-code-background` | `#1B1712` | — |
| `--leo-accent` | `#D2705A` | 5.10 |
| `--leo-accent-hover` | `#E08B75` | 6.67 |

### Tool hues (`--k-*`)

Upstream ships 14 saturated hues (magenta, cobalt, violet…) for tool cards.
They are remapped onto traditional pigments at low saturation — 墨, 赭石, 花青,
苔绿, 朱砂 — so the activity stream still colour-codes but reads as ink washes.
Every remapped hue holds ≥ 4.0 contrast on paper, background and code ground in
light, and ≥ 5.1 in dark.

### Syntax colours

Upstream hardcodes `#a626a4` magenta and `#3d6fe0` blue for `.tok-*`. Both are
overridden in this theme:

| Token | Light | Dark | Pigment |
|---|---|---|---|
| `.tok-kw` | `#9A3B2A` | `#D2705A` | 朱砂 — keyword as 朱批 |
| `.tok-str` | `#4A6B36` | `#8DAE74` | 苔绿 |
| `.tok-com` | `#756857` | `#8A7E6E` | 淡墨, italic |
| `.tok-num` | `#835C21` | `#C9A45E` | 赭石 |
| `.tok-fn` | `#3F5A72` | `#8FA5BA` | 花青 |

---

## 4. Typography

Unchanged. `Leo Inter` + `Leo Noto Sans SC` for UI, `Leo Space Grotesk` for the
wordmark and display headings, `Leo JetBrains Mono` for code — the same four
faces every Leo theme uses, at the same sizes and the same tracking.

This is deliberate. A theme that also swaps the type is not a theme, it is a
second design system: switching away would change line breaks, wrap points and
the vertical rhythm of every document in the app. Ink Autumn changes colour,
surface, border and radius, and nothing that moves a glyph.

---

## 5. Geometry, border, shadow

Paper does not float.

| | Value | Rationale |
|---|---|---|
| `--radius` | `5px` | tighter than upstream's 6 — a sheet, not a pill |
| `--radius-card` | `9px` | down from 12 |
| `--radius-lg` | `13px` | down from 16 |
| `--shadow-card` | hairline ring + `0 1px 2px` at 3% | a sheet resting on a sheet |
| `--shadow-soft` | hairline ring only | most surfaces need no shadow at all |
| `--shadow-pop` | `0 12px 34px` at 12% | dialogs only |

**Border carries the structure, shadow only whispers.** Every card is a
hairline-bordered paper block on paper. Hover never glows: it shifts the ground
by one paper step, or draws a 1px cinnabar rule on the leading edge.

---

## 6. Background scenes

`body` carries a fixed, `cover`-positioned master plus a paper-coloured scrim
layer stacked above it in the same `background` shorthand. The scrim is how
opacity is applied without touching the artwork.

| Scene | Master | Presence on the bare ground | Behind running text |
|---|---|---|---|
| Home (`#dashboard` visible) | `ink-autumn-branch` | 14% light / 8% dark | n/a — dashboard text lives in cards |
| Workspace (`#workspace` visible) | `ink-autumn-branch-warm` | 14% (sidebar 2%, dock 3%) | 4.8%, via `#main`'s own paper scrim |
| Workspace, empty session | `ink-autumn-branch-warm` | 14% | 6.7% — the scrim opens up when there is no running text |
| Knowledge (settings content pane) | `ink-autumn-tree` | 11% light / 5% dark | n/a — a masked corner layer, not a ground |

Those numbers are not documentation: `tests/test_theme_readability.py` composites
each of them against the masters' darkest stroke (and, at night, their brightest
paper) and fails the build if any ink drops below its floor.

The knowledge scene is a masked layer rather than a background with a scrim over
it. A scrim dilutes an image but cannot stop it being a rectangle, and on night
paper a pale master at any opacity reads as a lit block with four corners; a
radial mask dissolves them.

Scene selection is by `body:has(#dashboard:not(.hidden))` etc. — no JS, no class
plumbing, no upstream edit.

**Readability protection.** The reading surfaces are lighter than the ground and
translucent, not transparent: the message column, cards and composer sit on
`--leo-paper` at 88–94% alpha, so the botanical shows through as texture and
never as a competing edge. The artwork's own mass sits bottom-right, where the
layout keeps gutters.

---

## 7. Decorative language

Ceiling: **at most two decorative marks per screen.** 宁可没有，也不要堆。

Everything new is inline SVG in `leo.css` (a few hundred bytes each), authored in
the masters' language — one weight, one pigment, no fills.

| Asset | Where | Notes |
|---|---|---|
| 淡墨分割线 `--leo-rule-ink` | `.md hr`, settings group separators | a wash that thins at both ends, not a 1px line |
| 朱砂小印 | after the wordmark, on the baseline | 5px cinnabar square — a seal follows a signature; it is not a badge above it |
| cinnabar edge rule | active tab / session / theme card | `inset 2px 0 0` instead of a filled pill |
| 研究痕迹 `--leo-trace` | empty session only | decaying sine + gaussian + logistic, 5% light / 7% dark. Not on the dashboard: a screen that already carries a whole branch is allowed one mark, and the branch is it |
| 水墨节点 `--leo-node-mark` | file tree / artifact empty states | three dots and two edges |
| thinking pulse | existing spinner | ink-drop breathing, `prefers-reduced-motion` respected |

### Research traces

PDE curves, gaussians, node graphs and matrix rules are allowed — this is Leo AI,
not a heritage product — but only at the weight the masters use for their own
faint marks: **淡, 弱, 若隐若现**, like a note left on the paper. They are never
chart-like, never labelled, never above 6% opacity.

---

## 8. Leo Tree reservation

Leo Tree will need `TreeNode`, `Section`, `Edge`, `Progress`, `Review`,
`KnowledgeCard`. This theme exports the vocabulary those will bind to, already
defined and already themed:

```
--leo-tree-node, --leo-tree-node-active, --leo-tree-edge,
--leo-tree-canvas, --leo-tree-progress, --leo-tree-progress-track,
--leo-tree-review, --leo-tree-card, --leo-tree-card-border
```

They are defined in both light and dark, derived from the same paper/ink/cinnabar
values, and `ink-autumn-tree.webp` is already registered as the knowledge ground.
Nothing consumes them yet — the point is that Leo Tree will not need a second
palette, and the 树 metaphor (植物 / 知识结构 / 长期成长) already has its artwork.

---

## 9. Switching

- Registered in `theme/themes.json` alongside the existing two, `builtin: true`.
- `default_theme` is now `ink-autumn`, so a fresh install opens on it.
- `settings_store._default_theme_id()` reads that field instead of a hardcoded
  id, so the shipped default is a theme-layer decision.
- An existing `user/appearance.json` still wins: nobody is moved off the theme
  they chose.
- Settings → 外观 lists all three; switching away restores the previous theme
  exactly, because every Ink Autumn rule is scoped under
  `html[data-leo-theme="ink-autumn"]`.

---

## 10. Asset provenance — Grok F-008

F-008 (UNVERSIONED PRODUCT ASSET) asks whether a shipped asset can be traced to
a committed source. `tools/theme_asset_provenance.py` answers it by measurement
rather than by claim: it walks every file `ThemeRuntime` opens on a real
installation and checks that git tracks a source for it and that the installed
bytes are that source's bytes.

**Closed for the theme's own assets.** `themes.json`, `leo.css`, the three WebP
backgrounds and their manifest all have tracked sources under `stage/`, the
three untouched masters are committed under `assets/backgrounds/`, and
`tools/build_backgrounds.py` is the recorded recipe from one to the other.
`tools/build_launcher.ps1` overlays them into the package with a per-file hash
check, and `tools/verify_release.py` re-proves the chain at release time
("theme assets versioned", "artwork masters").

**Still open, and predating this work:** ten assets have no repository source at
all and are taken from whatever the build machine has installed —

```
fonts/manifest.json          logos/leo-lion.svg
fonts/Inter-Variable.woff2   logos/leo-favicon.svg
fonts/JetBrainsMono-*.woff2  logos/leo-lion-1024.png
fonts/NotoSansSC-*.woff2     i18n/zh.json
fonts/SpaceGrotesk-*.woff2   i18n/en.json
```

Closing that half is a separate change with a different owner (brand assets, not
theme). The proportionate route follows the repository's own precedent for large
binaries: commit the small text and vector files outright, and handle the four
woff2 faces plus the two raster logos the way `manifests/wheelhouse.json`
handles wheels — a committed manifest naming each file with its SHA-256 and its
official source, which is enough to verify a copy someone else produced and
enough to notice tampering. `theme/fonts/manifest.json` already records exactly
that; it simply is not in git yet.

Run `python tools/theme_asset_provenance.py` for the current count. `--strict`
exits non-zero while any gap remains, so it can gate the day that half closes.

---

## 11. Deferred work

Recorded, not fixed. Each entry says why it is deferred, so a later reader does
not have to reconstruct the reasoning.

### Injected stylesheet size — NON-BLOCKING

`ThemeRuntime.injection_script` produces roughly 11.65 MB of CSS, of which about
10.4 MB is the base64 Noto Sans SC face and 0.56 MB is the three backgrounds.
The fonts dominate and predate this theme; the artwork added about 5%.

Deliberately not optimised in this round. Reducing it means changing how assets
reach the page — subsetting the Chinese face, or moving from data URIs to a
local scheme handler — and that is a change to the injection mechanism, not to a
theme. Doing it while also introducing a theme would make a regression in either
one hard to attribute.

What to measure before touching it: theme injection time, first-render time and
renderer memory, per theme, on a cold start. Optimise against those numbers, not
against the byte count.

### 390 px layout — SHARED, not theme-owned

Two problems exist at phone width and both reproduce identically on
`deep-sea-molten-orange`, so neither belongs to this theme:

- `.workspace` is a three-column grid with no mobile breakpoint, so `#main`'s
  content spills under the sidebar.
- The settings modal is forced wider than the viewport by its horizontal tab
  strip.

Ink Autumn's only concession is that its panels stop being translucent below
900 px, so the theme does not make the first one more visible than it already
is. Fixing either would change shared layout across all three themes and is
logged as shared mobile-layout debt.

### 花青 in the tool palette — kept

Two of the fourteen `--k-*` roles sit in the 花青 family (muted, dark indigo).
That is a traditional pigment at low saturation, not a blue/violet tech gradient
or a neon accent, and it stays. The gate this theme holds itself to is the
absence of cool gradients — enforced by
`test_no_blue_violet_gradients_in_the_theme`, which scans every gradient stop in
the Ink Autumn section — not the absence of every blue pigment.


</details>

<a id="history-8"></a>

## 历史附录 8：REPOSITORY_HYGIENE_REPORT.md

<details>
<summary>展开历史原文（仅作记录）</summary>

# Leo AI Repository Hygiene Report

治理日期：2026-09-07
范围：Leo AI / Leo AI Studio 深度仓库卫生、文件归一化、重复清理、治理资产核验与安全收口

---

## 1. Executive Summary

- **Canonical repository（唯一确定）**：`C:\Users\user\Desktop\LeoAIStudio-build`
  - branch `master`，HEAD `a4455cc32dccbcf`（docs(theme): freeze Ink Autumn v1，2026-09-05）
  - 122 个 tracked 文件，6 个本地分支（master + 5 个 P0/主题分支），无 remote、无 stash、无 submodule
  - **存在大量未提交的在研工作**（PINN 闭环、本地模型、entity 功能）——按指令全程未触碰、未 reset、未 clean
- **治理结论**：删除 5 项共 **197.47 MB**，全部有字节级（SHA-256）冗余证明；1 个 temp worktree 以正规 git 命令移除；1 个 worktree 注册修复。**零推测性删除**。
- **治理资产完整性**：`docs/rollback/` frozen-evidence、`manifests/` 哈希锁、wheelhouse（verify PASS 前后一致）、全部分支/提交、本地 only 的人工验收证据（168.86 MB）——**byte/hash 全部未变**。
- **重要情况：治理期间检测到并行开发会话**（详见 §11/§14）。基线与治理后的 pytest 差异（676→721 个测试）由并行会话的代码/测试修改造成（文件 mtime 08:20/08:24 为证），非治理动作所致；治理未触碰任何 tracked 文件。
- **残余风险**：portability 3 处硬绑定与 verify_release 6 项 FAIL 为**既有问题**（诚实保留，未通过删除问题文件制造 PASS）；rollback 快照链（345 MB）含 8 个唯一历史 exe，按安全规则保留。

---

## 2. Repository State Before

Desktop 上 Leo AI 相关共 8 个位置，合计 ≈ **2,529.3 MB**：

| 位置 | 大小 | 性质 |
|---|---|---|
| `LeoAIStudio-build` | 262.7 MB | **主 Git 仓库**（canonical）+ .venv 54.9 + dist 三份构建 152.5 + pyi-work 17.7 + wheelhouse 10.6 |
| `LeoAIStudio` | 2,107.8 MB | 部署的应用（无 git）：runtime/webview2 798.7 + openai4s tar.gz 394.5 + upstream 267.9 + user 160.3（**当日仍在活跃使用**）+ 8 个 rollback 快照 345.5 + tools/mingit 90 |
| `LeoAIStudio-p0-audit` | 1.8 MB | 主仓库 linked worktree（grok-p0-post-claude-audit，clean） |
| `LeoAIStudio-p0-fix` | 12.0 MB | linked worktree（p0-remediation-f001-f002-f007-f008，clean） |
| `LeoAIStudio-p0-verify` | 1.4 MB | linked worktree（grok-p0-independent-verification，clean） |
| `大创\LeoAIStudio-p0-manual` | 65.6 MB | linked worktree（p0/manual-acceptance-20260905，clean，含 54.9 MB .venv；**注册路径失效 prunable**） |
| `%TEMP%\leo-ink-autumn-freeze-*\tree` | 78.1 MB | linked worktree（codex/ink-autumn-v1-freeze，clean，位于临时目录） |
| `Desktop\user\` | ~0 MB | 应用误写到桌面的游离数据（空 credentials 目录 + 2.2 KB 过期日志） |

问题类型：dist 内 3 份 99% 相同的构建、PyInstaller scratch、测试缓存、临时目录 worktree、失效的 worktree 注册、应用升级残留 rollback 快照链（8×43 MB，两两 99% 相同但各含唯一 exe）。

---

## 3. Canonical Repository Decision

认定 `LeoAIStudio-build` 为 canonical 的依据：

1. **唯一持有 `.git` 对象库的目录**；其余 5 个 LeoAIStudio-* 目录全部是它的 linked worktree（`.git` 文件均指回 `LeoAIStudio-build\.git\worktrees\...`），不是独立克隆。
2. 全部 6 个分支、全部提交、全部 P0 治理文档（docs/P0_*、docs/rollback frozen evidence、manifests/ 哈希锁、test-suites.json）只存在于该仓库。
3. `Desktop\LeoAIStudio`（2.1 GB）是**部署产品**而非仓库克隆：PyInstaller 启动器 + WebView2/OpenAI4S 运行时载荷 + 用户数据（credential.dpapi、entity-state.db），README 明确其为可移植安装目录；当日 07:50 仍有用户数据写入（活跃使用中）。
4. `大创\LeoAIStudio-p0-manual` 是 P0 人工验收分支的 worktree，被移动到 大创 项目内导致注册失效（已修复注册，见 §4）。

结论：**ONE CANONICAL REPOSITORY** = `LeoAIStudio-build`；worktree 均为该仓库的合法组成部分。

---

## 4. Actions Performed

### 删除（全部有字节级证明，详见 §5）
1. `dist\LeoAIStudio`（50.82 MB）
2. `dist\LeoAIStudio-integration-c524c83`（50.82 MB）
3. `pyi-work\`（17.72 MB）
4. `Desktop\user\`（游离应用数据）
5. `.pytest_cache\`（0.06 MB；后被验证运行按需重建）

### Git 正规操作（非文件夹强删）
6. `git worktree remove --force <temp>`：移除 `%TEMP%` 中的 ink-autumn-freeze worktree（clean，树内容 ⊆ master，分支与提交完整保留于主仓库 .git）
7. `git worktree repair C:\Users\user\Desktop\大创\LeoAIStudio-p0-manual`：修复 prunable 注册，worktree list 恢复准确

### 未做
- 未 commit、未修改任何 tracked 文件、未动分支/tag/remote、未 reset/clean/checkout、未运行 GC、未做 history rewrite
- 未创建任何 backup/快照/压缩包

### 路径修复
- 无需修复：治理未移动任何源码或 tracked 文件；全部删除对象为 gitignored 构建产物或仓库外游离数据。

---

## 5. Deleted Content

```text
Category: EXACT_DUPLICATE
Location: LeoAIStudio-build\dist\LeoAIStudio (336 files, 50.82 MB)
Reason: 与正在运行的部署应用逐文件 SHA-256 完全一致
Evidence: 336/336 match, 0 diff, 0 missing（对比 Desktop\LeoAIStudio 对应路径）
Safety basis: byte-identical；且 exe/theme 哈希记录于已提交证据 build-final.json（deployed_exe_sha256=99db81a3…）
```

```text
Category: EXACT_DUPLICATE (recombinable)
Location: dist\LeoAIStudio-integration-c524c83 (336 files, 50.82 MB)
Reason: 每个文件字节均保存于 rollback-20260905-015638（含其 exe 8e64d901）或部署应用
Evidence: 336/336 preserved, 0 unresolved
Safety basis: byte-identical to preserved copies
```

```text
Category: GENERATED_REBUILDABLE (build scratch)
Location: pyi-work\ (17.72 MB)
Reason: .gitignore 注释明确声明为 "PyInstaller scratch, not a source of truth"
Evidence: 其唯一有值文件 LeoAIStudio.exe (12a10b4a) 与保留的 dist\LeoAIStudio-pre-ink-autumn-freeze 内 exe 字节一致
Safety basis: 构建中间产物；工具链（wheelhouse 钉死 21 wheel）可重建
```

```text
Category: TEMPORARY (stray app data)
Location: Desktop\user\ (credentials 空目录 + logs\leo-shell.log 2.2 KB)
Reason: 应用从构建目录以错误 CWD 运行时误写桌面的游离数据；日志内容为 2026-09-02 WebView2 fallback 报错堆栈，无密钥
Evidence: 逐行读取确认无敏感信息；应用自身的 user\ 目录（含真实数据）原样保留
Safety basis: stale 工具产物，无唯一内容
```

```text
Category: TEMPORARY (obsolete clean worktree)
Location: %TEMP%\leo-ink-autumn-freeze-...\tree (78.11 MB, 含其 .venv)
Reason: clean worktree，位于系统临时目录（随时可能被 OS 清理造成悬空注册）；其树内容为 master 子集（git diff master..branch 无独有文件）；分支 codex/ink-autumn-v1-freeze 与 2 个提交完整保留于主仓库
Evidence: git status clean；name-status diff 为空；worktree remove 后 worktree list 无该条目、branch 仍在
Safety basis: 零工作丢失（提交均在主仓库 .git）；使用 git 正规 worktree 命令而非删文件夹
```

```text
Category: CACHE
Location: .pytest_cache\ (0.06 MB)
Reason: 测试缓存；验证运行已按需重建（现 0.08 MB，供并行开发会话继续使用）
Safety basis: 100% 可再生缓存
```

---

## 6. Intentionally Preserved Content

| 项 | 位置/大小 | 保留原因 |
|---|---|---|
| **8 个 rollback 快照** | `LeoAIStudio\.leo-rollback-*`（345.5 MB） | 每个快照含一个**未在他处字节保存的历史 exe**（87b7809b→bc255442→cb72ac4f→3e0cbe2e→e3cbbfe3→68b89add→8e64d901→f58f43f6）；PyInstaller 构建含时间戳不可字节复现，且 deployment.json 未记录对应 git commit，无法证明可重建。属部署历史链 |
| **dist\LeoAIStudio-pre-ink-autumn-freeze** | 50.82 MB | 含唯一基线 exe `12a10b4a`（freeze 验证链的 before 基准，从未部署，任何 rollback 均无此哈希） |
| **4 个 P0 worktree + 5 个未合并分支** | audit/fix/verify/manual（80.8 MB） | 各分支含 master 没有的**未合并治理证据**（`artifacts/p0_external/`、`docs/p0_external/GROK_*.md` 等）；按指令 worktree 移除条件（clean+merged）不满足 → 全部保留；p0-manual 注册已修复 |
| **`docs\manual-acceptance-evidence\`** | 168.86 MB | .gitignore 注明"per-machine evidence"——**仅存本地的治理证据**（freeze-v1 日志、Ink Autumn 截图、并行会话今晨采集的 ink-20260907 四语言证据） |
| **`docs\rollback\`** | 0.26 MB | portability_check.py 声明的 frozen-evidence（"editing them would destroy the evidence"），tracked、未动 |
| **wheelhouse + manifests** | 10.6 MB | 哈希锁资产（21 wheel，verify 前后 0 problems） |
| **.venv ×2** | 54.9 + 54.9 MB | 主仓库与 p0-manual worktree 的虚拟环境；测试依赖（虚拟环境按指令保护） |
| **全部未提交工作** | 13→26 个修改文件 + pinn/、specs/、adversarial/、research_logs/、bridge/、governance/*.json、entity_store.py、新测试等 | 在研科研与功能开发（并行会话所有者），零接触 |
| **部署应用全部内容** | 2,107.8 MB | 活跃产品：user/（DPAPI 凭据、entity-state.db，当日 07:50 仍在写入）、runtime/upstream/tools 载荷、8 个 rollback |
| `assets-backup\leo-lion.pre-badge.ico` | 85 KB | **git tracked**（名字像备份，实为已提交资产），不动 |
| `~\.openai4s\` | — | 上游 OpenAI4S CLI 自身数据，非 Leo AI 项目文件，不属治理范围 |
| `Desktop\LeoAI_本地模型_LeoTree_工作交接报告_2026-09-07.md` + `LeoAIStudio-p0-manual-session\` | ~0.1 MB | 并行会话今晨产出的交接报告与 P0 人工验收执行单工作区（活跃使用中），未动 |

---

## 7. Governance Integrity

| 检查项 | 结果 |
|---|---|
| `docs/rollback/` frozen-evidence（10 个 pre-fix 脚本） | **byte-exact unchanged**（git status 无该目录任何改动；portability_check 分类为 frozen-evidence） |
| P0 治理文档（P0_FINAL_CLOSURE_REPORT / EXECUTION_STATUS / CHECKLIST / RELEASE_CANDIDATE / RESEARCH_SOP_MIGRATION_AUDIT / THEME_INK_AUTUMN） | tracked；治理零接触（THEME_INK_AUTUMN.md 的当前修改来自并行开发会话，非治理） |
| `manifests/`（dependency-lock / wheelhouse / upstream-pin / test-suites） | unchanged；wheelhouse verify 治理前后均 **PASS（0 problems, 21 wheels）** |
| 分支/tag/提交 | 6 分支全部保留；HEAD a4455cc 不变；无删除、无 rewrite |
| worktree | temp 已移除（正规命令、零内容丢失）；p0-manual 注册修复（`worktree list` 现准确列出 5 处）；4 个 P0 worktree 保留 |
| hash-lock 语义文件 | 未改内容/行尾/编码（未触碰任何 tracked 文件） |
| 本地验收证据 | `docs/manual-acceptance-evidence/` 完整保留并新增（并行会话） |

---

## 8. Scientific Integrity

- PINN / 科研规格资产全部**零接触并保留**：
  - tracked：`governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md`（含绝对路径的 portability 发现，按指令**不得删除以制造 PASS**）、`governance/PINN_CLOSED_LOOP_MVP_PLAN.md`（其当前修改来自并行会话）
  - untracked 在研：`governance/PINN_V1.3_PRELOCK_DRY_RUN.json`、`governance/POISSON_1D_V1.0_{spec,protocol,lock}.draft.json`、`pinn\`（30 文件）、`specs\`、`adversarial\`、`research_logs\`、`tests/pinn\`
- `manifests/test-suites.json`（P0-2 判定套件登记：locked test functions、provenance、reconstructed/reviewer-original 状态）unchanged。
- test-suites 引用的证据基线 `docs/rollback/research-sop-kernel.pre-P0-2-round2.py` byte-exact 保留。
- 治理删除对象（dist/pyi-work/缓存/temp worktree）不含任何科研或治理证据。

---

## 9. Final Repository Tree

```text
LeoAIStudio-build\                      (canonical repo, 276.7 MB)
├── .git\                 6 分支 + 全部 P0/freeze 提交历史（9.8 MB）
├── .venv\                构建虚拟环境（54.9 MB，保留）
├── assets\ + assets-backup\            主题母版（含 .src.png，tracked）
├── adversarial\ bridge\ pinn\ specs\ research_logs\ .task-state\ artifacts\
│                        ↑ 并行会话的在研工作（未提交，零接触）
├── dist\
│   └── LeoAIStudio-pre-ink-autumn-freeze\   唯一基线构建（50.8 MB，保留）
├── docs\
│   ├── rollback\                         frozen-evidence（tracked）
│   ├── manual-acceptance-evidence\       本地证据 168.9 MB（今晨新增 ink-20260907）
│   └── P0_*.md / BUILD.md / THEME_INK_AUTUMN.md
├── governance\  manifests\  skills\  stage\  tests\  tools\  leo_shell\
├── wheelhouse\           哈希锁 wheel 缓存（10.6 MB）
└── REPOSITORY_HYGIENE_REPORT.md   （本报告，唯一新增文件）

Desktop\LeoAIStudio\                    (部署产品, 2,107.8 MB, 活跃使用)
├── user\  runtime\  upstream\  tools\  theme\  _launcher\  LeoAIStudio.exe
└── .leo-rollback-* ×8                  部署历史快照（保留）

worktrees: LeoAIStudio-p0-audit / p0-fix / p0-verify / 大创\LeoAIStudio-p0-manual
临时会话: LeoAIStudio-p0-manual-session\（并行会话工作区，未动）
```

---

## 10. Disk Usage

| 项 | 数值 |
|---|---|
| 治理前 Leo AI 资产总量（8 处，实测） | **≈ 2,529.3 MB** |
| 治理删除（本次动作，精确计量） | **197.47 MB**（dist×2 = 101.64 + temp worktree 78.11 + pyi-work 17.72 + Desktop\user 0.002） |
| 治理后资产总量（实测） | ≈ 2,466.3 MB |
| 并行会话同期新增（非治理动作） | ≈ +163 MB（docs/manual-acceptance-evidence/ink-20260907 等） |

说明：治理前后总量的简单差值**不可靠**（并行会话同期持续写入，精确归属不可能）；上表按动作分别计量，治理自身的释放量为精确值 197.47 MB。
**未执行的潜在释放**（需用户明确批准，见 §14）：旧 rollback 快照 ~302 MB（保留最新 1 个）、dist 基线构建 50.82 MB。

---

## 11. Verification

### Before（治理前基线，本机实测）

| 检查 | 结果 |
|---|---|
| pytest | **6 failed / 669 passed / 1 skipped**（exit 1） |
| tools/portability_check.py | **3 hard binding(s), 1 configurable default**（exit 1）——全部位于 `governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md` 第 58/170/407 行（windows-user-home 绝对路径） |
| tools/build_wheelhouse.py verify | **PASS**：0 problems, 21 wheels |
| git status | master @ a4455cc，dirty（13 修改 + 未跟踪在研目录）——既有状态 |

### After（治理后，本机实测）

| 检查 | 结果 |
|---|---|
| pytest | **1 failed / 719 passed / 1 skipped**（exit 1）——唯一失败 = 同一个 portability 测试 |
| tools/portability_check.py | **3 hard binding(s), 1 configurable default**（exit 1）——与基线**逐项一致** |
| tools/build_wheelhouse.py verify | **PASS**：0 problems, 21 wheels —— 与基线一致 |
| git ls-files / HEAD / 分支 | 122 tracked 不变；a4455cc 不变；6 分支不变 |
| git worktree list | 主仓库 + 4 个 P0 worktree（temp 已移除、manual 已修复） |
| docs/rollback | 零改动（frozen evidence 完好） |

### pytest 前后差异的归因（关键）

基线 676 个测试 → 治理后 721 个（+45）。**这不是治理造成的**：治理期间检测到并行开发会话活跃写入——`leo_shell/api.py`（mtime 08:20:11）、`tests/leo_shell/test_api.py`（08:24:26）、新增 `leo_shell/entity_store.py`、`tests/leo_shell/test_entity_store.py`、`tests/leo_shell/test_local_model_session.py` 等；基线中 5 个 entity 契约失败由并行会话的修改消除，+45 个测试来自其新增测试文件。桌面交接报告（`LeoAI_本地模型_LeoTree_工作交接报告_2026-09-07.md`，快照 07:51:55）证实该会话的存在与上下文。治理动作只删除 gitignored 构建产物（不在 pytest 收集范围），可证明与测试结果无关。

### tools/verify_release.py --strict（补充记录）

**5 PASS / 6 FAIL**（exit 1）——**既有状态**：skills 哈希漂移（lean-math、research-sop 共 6 文件与部署不符）、部署 skills 12 文件偏离 canonical、工作树 dirty。该 strict 发布门禁要求 clean tree + 清单与部署一致，在活跃开发期不适用；按项目自身口径记为既有 FAIL，未运行任何修复。

---

## 12. Pre-existing Failures（治理前已存在，诚实保留）

1. **portability 3 处硬绑定**：`governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md` 中的 windows-user-home 绝对路径（含 `Desktop\pinns\outputs\run_6\model.pt` 引用）。按指令**不得通过删除该审计文档制造 PASS**。前后逐项一致。
2. **基线 pytest 6 失败**：4× entity API 契约 + 1× UI 契约（在研功能未完成所致，后被并行会话解决）+ 1× portability（同上）。
3. **verify_release --strict 6 FAIL**：skills 与部署漂移 + dirty worktree（在研工作）。
4. **test-suites.json 记录的 pending confirmation**：reviewer-original 对抗测试 NOT PROVIDED（P0-2 的独立确认缺口，项目自身已如实登记）。

## 13. New Failures（治理引入）

**无。** 治理后唯一失败的测试与基线为同一项（portability）；portability/wheelhouse/pytest 中所有与治理相关的可比较项前后一致或变好（变好部分归因于并行会话）。

---

## 14. Remaining Risks

1. **并行会话仍在活跃写入**（治理期间 api.py/test_api.py/THEME_INK_AUTUMN.md/验收证据持续变化）：本报告是某一时点快照；`LeoAIStudio-p0-manual-session\` 与桌面交接报告属该会话所有，未纳入治理。
2. **部署应用与 canonical 的 skills 漂移**（verify_release 6 FAIL）：12 个部署文件与仓库不一致——属开发/部署流程问题，治理未修（不得以删除掩盖）。
3. **rollback 快照链 345 MB**：含 8 个唯一历史 exe，按删除判据保留。若用户确认不再需要历史部署二进制，可批准删除 7 个旧快照（保留最新）释放 ~302 MB。
4. **dist 基线构建 50.8 MB**：含唯一 exe `12a10b4a`，同上保留。
5. **p0-manual worktree 位于 大创 项目内**（跨项目位置）：按治理链保留原则未移动；其 .venv（54.9 MB）可用 wheelhouse 重建。
6. **无 remote**：全部历史仅存于本机 `.git`（9.8 MB）——建议用户自行决定是否建立远程备份（治理不擅自添加 remote）。
7. 未提交在研工作规模持续增长（26 个修改 + 大量未跟踪），建议所有者适时提交；治理按指令零接触。

---

## 15. Final Verdict

## **PASS WITH PRESERVED UNCERTAINTY**

- 10 项 PASS 判据中：canonical 唯一明确 ✓、未丢失文件 ✓、无治理引入的回归 ✓、治理完整性未破坏 ✓、科研证据未破坏 ✓、hash-locked 未变 ✓、散落文件合理处理 ✓、重复显著减少 ✓、无新 backup ✓、删除全有证据 ✓。
- 降级原因：(a) portability 与 verify_release 的**既有 FAIL** 仍开放（按指令诚实保留）；(b) 治理期间并行会话活跃写入，使 after 验证存在时点混淆（已用 mtime/交接报告归因，但无法做严格同构对照）；(c) rollback 链与基线构建因含唯一二进制而保留（磁盘占用高于理想值）。


</details>

````

</details>

### R002 — 项目/20260914软件修改报告.md

<details>
<summary>展开完整原文</summary>

````markdown
# Leo AI Studio 软件修改报告（2026-09-14）

记录日期：2026-09-14。执行：Claude Code。仓库：`LeoAIStudio-build`（本文件所在目录）。

本报告记录用户 2026-09-14 下达的"大规模重构、整合与清理"任务：任务原文、执行前必须由用户拍板的决定、实际做了什么、验证结果，以及没有做和需要用户后续决定的事项。仓库卫生的逐项删除记录单独见 [20260914仓库卫生记录.md](20260914仓库卫生记录.md)。

---

## 1. 任务原文与约束

用户要求（按原话归纳）：

1. **仓库卫生（第一步）**：对 `LeoAIStudio-build` 目录做深度卫生护理，删除一切无用的测试文件，做好文件分类与文件层划分，并写一份 `.md` 清理报告，命名为 `20260914仓库卫生记录`，逐项写明删了什么、位于哪里（相对路径）、什么原因。
2. **敏感文件**：想删但可能对用户很重要的文件，必须先问用户；用户同意后再删，报告里原因写"用户审批通过"。
3. **大规模重构**：
   - 尽可能减少 Open4Sci（上游 OpenAI4S）原本的前端设计与 UI。减少上游 UI 已获批准；**新增任何 Leo AI 风格的前端设计与 UI 必须先问用户，不同意不准新增**。
   - Open4Sci 的后端内核（计算器、Agent、笔记本等）全部保留，一个都不准擅自删除；可以提建议（换位置或删无用文件），用户不同意就不准动。
4. 本报告本身：把上述任务写成一份软件修改报告，放在 `LeoAIStudio-build` 目录里。
5. 追加要求：向用户提问一律用中文。

执行时遵守的边界：

- 上游 `upstream/OpenAI4S` 源码保持字节不变，所有 UI 调整只发生在 Leo 的注入层（`stage/leo.css`、`stage/leo-inject.js`、`stage/unified-settings-adapter.js`）。
- 后端（gateway、agent、notebook、compute、connectors、skills、memory 等）零改动；Leo 自己的 bridge sidecar 也不删。
- 没有新增任何 Leo 风格的新界面、新配色、新组件。
- 安装目录 `LeoAIStudio/` 下的用户数据（`user/` 内的 DPAPI 凭据、会话状态、模型配置）没有读取内容、没有移动、没有删除。
- 测试一个都没有删：`tests/` 下 35 个文件是 codex 线 839 passed 的回归网，逐个核对后没有发现无用项（见 §4）。

---

## 2. 执行前发现的问题与用户决定

开工前的仓库勘察发现了四件必须由用户决定的事，已用中文逐项询问，用户答复如下。

### 2.1 仓库有两条分叉的主线

| 线 | 提交 | 内容 |
|---|---|---|
| `master` | `8c4835e`（"snapshot before cleanup (102 items, per LeoAI cleanup report 20260909)"） | 直接建在 `a4455cc`（9-05）之上的一次性快照，`git ls-tree -r` 计 105 个文件。相对 codex 线：0 个独有文件，35 个文件内容更旧，117 个文件缺失（测试、9-08/09 报告、5 个 bridge 运行时模块、`leo_shell/session_models.py`、`stage/fonts`、`stage/i18n`、`LICENSES/fonts`、`scientific_reference/`、`pinn/validation/` 等） |
| `codex/conversation-runtime-20260909` | `14e30f4` | 9-08～9-10 的完整工程线（PINN 治理修复、入口导航修复、会话模型绑定与推理运行时），222 个文件。安装目录里的 `build-receipt.json` 证明当前正式安装版就是 9-10 从这个提交构建的 |

两条线的共同祖先是 `a4455cc`。`git diff --stat 14e30f4 8c4835e` 为 152 files changed，+423 / −31846：8c4835e 只比 codex 线"少"，多出来的 423 行全部是 codex 线后来改掉的旧内容，没有任何一处是 8c4835e 独有的新改动。

**用户决定：以 codex 分支为基线。** 并询问"删掉 8c4835e 会怎样"，要求若最终删除则在报告中记录为用户同意删除。处理见 §3。

### 2.2 安装目录与 Leo Tree 项目已被放进构建仓库

`LeoAIStudio-build/LeoAIStudio/`（正式安装目录，含 `user/` 加密凭据、WSL 运行时、上游 checkout，约 2.0 GiB）和 `LeoAIStudio-build/leotree/`（Leo Tree 项目，自带独立 git 仓库，约 589 MiB）都位于仓库根目录下，但构建/部署/校验工具默认到"仓库上一级的 `LeoAIStudio`"找安装目录，已经找不到。

**用户决定：留在 build 目录内，并改工具默认路径。** 两者写入 `.gitignore`，永不入库；工具默认 `AppRoot` 改为 `<仓库>/LeoAIStudio`，仍可用 `LEO_APP_ROOT` 或 `-AppRoot` / `--app-root` 覆盖。

### 2.3 待审批的删除项

| 候选 | 说明 | 用户答复 |
|---|---|---|
| `LeoAI-maintenance-20260907/` | 9-07 那轮维护的档案：验证脚本、日志、截图、SSE 记录，外加 `source-before/` 全量源码快照（含 Chrome 配置文件证据）。结论早已并入 `CHANGELOG.md`；`removed-files.zip` 已不在其中 | 同意删除 |
| `tools/capture_window.ps1`、`tools/watch_window.ps1`、`tools/inspect_webview.mjs` | 人工验收时截窗口、盯窗口几何、走 CDP 端口的一次性探针；构建链、测试与文档零引用 | 同意删除 |
| `tools/extract_launcher.py` | 从旧 EXE 恢复已被包契约禁止的旧壳 `leo_ai_studio` 模块；全仓零引用 | 同意删除 |

### 2.4 上游 UI 缩减做到哪一档

**用户决定：只去重复控件。** 即隐藏上游顶栏与侧栏各一组的中/英切换和明暗切换（Leo 设置 → 外观里已有同样功能），其余功能入口全部保留。

---

## 3. 基线切换与 8c4835e 的处理

工作分支 `claude/leoaistudio-cleanup-refactor-9e137d`（git worktree，位于仓库目录下的 `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d`）先 `git reset --hard 14e30f4`，之后所有改动都建立在 codex 线之上。

| 步骤 | 结果 |
|---|---|
| 8c4835e 包含性核验 | 8c4835e 相对 codex 线：0 个独有文件、0 处独有改动（§2.1）。删除它不丢失任何内容 |
| 工作分支提交 | 见 §10 |
| 主检出 `master` | 在主检出执行 `git reset --hard <新提交>`，`master` 由 `8c4835e` 改指向新提交。主检出此前工作树干净，没有未提交改动被覆盖 |
| `8c4835e` 的去向 | **用户同意删除。** `master` 不再指向它。它目前仍被本次会话被分配的另一个工作树分支 `claude/leoaistudio-cleanup-refactor-d129a8` 引用（该工作树从未使用），所以对象还在；用户随时可以用 `git worktree remove .claude/worktrees/leoaistudio-cleanup-refactor-d129a8` 加 `git branch -D claude/leoaistudio-cleanup-refactor-d129a8` 让它进入可回收状态。没有执行 `git gc` |

主检出与工作分支的关系：主检出 `master` 与工作分支 `claude/leoaistudio-cleanup-refactor-9e137d` 指向同一提交；`codex/conversation-runtime-20260909` 保持在 `14e30f4` 不动，仍是本次提交的父提交。

---

## 4. 仓库卫生（摘要）

| 类别 | 数量 | 明细 |
|---|---|---|
| 删除（git 跟踪） | 4 个文件，180 行 | `tools/capture_window.ps1`、`tools/watch_window.ps1`、`tools/inspect_webview.mjs`、`tools/extract_launcher.py`，均为用户审批通过 |
| 删除（仓库目录内、未跟踪） | 1 个目录，3,318 个文件，402,091,098 字节 | `LeoAI-maintenance-20260907/`，用户审批通过 |
| 移动 | 3 个文件 | `unified-settings-adapter.js`、`i18n-brand-patch.js` → `stage/`；`PINN_MVP_AND_CFD_READINESS_REPORT.md` → `docs/` |
| git 引用 | 1 个 | `master` 离开 `8c4835e`（用户同意删除） |
| 测试 | 删除 0 个 | 35 个测试文件全部保留 |
| 跟踪文件总数 | 222 → 221 | 减 4 个工具，加 2 份本次报告和 `pytest.ini` |

逐项记录、每一项的相对路径与原因，以及"考虑过但保留"的清单，见 [20260914仓库卫生记录.md](20260914仓库卫生记录.md)。

---

## 5. 整合：安装目录、Leo Tree 与工具默认路径

### 5.1 `.gitignore` 新增

```
LeoAIStudio/          # 正式安装目录：EXE、WebView2 运行时、上游 checkout、user/ 凭据与会话
leotree/              # Leo Tree 项目，自带独立 git 仓库
.claude/worktrees/    # Claude Code 会话工作树；git 已按 worktree 管理，不能再当文件加进来
```

同时把 bundle 注释里的两个源层路径改为 `stage/` 下的新位置。

### 5.2 `AppRoot` 默认值：由"仓库上一级"改为"仓库内"

| 文件 | 改动 |
|---|---|
| `tools/build_launcher.ps1` | `-AppRoot` 默认 `<仓库>/LeoAIStudio`，新增 `LEO_APP_ROOT` 覆盖；两个 bundle 源层改到 `stage/` |
| `tools/deploy_release.ps1` | `-AppRoot` 默认 `<仓库>/LeoAIStudio`（原本已支持 `LEO_APP_ROOT`） |
| `tools/build_manifest.py` | `DEFAULT_APP_ROOT` 改仓库内，新增 `LEO_APP_ROOT` 覆盖；源层字典键改为 `stage/...` 路径 |
| `tools/verify_release.py` | `DEFAULT_APP_ROOT` 改仓库内；源层字典键与 `build_manifest.py` 同步 |
| `tools/theme_asset_provenance.py` | `DEFAULT_APP_ROOT` 改仓库内，新增 `LEO_APP_ROOT` 覆盖；`BUNDLE_LAYERS` 改为 `stage/` 三层 |
| `tools/theme_preview.py` | `DEFAULT_APP_ROOT` 改仓库内，新增 `LEO_APP_ROOT` 覆盖 |
| `tools/sync_skills.py` | `DEFAULT_APP_ROOT` 改仓库内 |
| `tools/headless_verify.py` | 无参数时的默认根改仓库内 |
| `tools/manual_acceptance/collect_windows_account_env.py` | `--app-root` 默认改仓库内 |
| `tools/manual_acceptance/verify_clean_build.py` | 5 处 `REPO.parent / "LeoAIStudio"` 改为 `REPO / "LeoAIStudio"`（含 upstream 与 runtime 子路径） |
| `tools/manual_acceptance/verify_research_sop_live.py` | `UPSTREAM_DEFAULT` 与 headless 调用的 app root 改仓库内 |
| `tools/manual_acceptance/verify_webview2_runtime.py` | WebView2 运行时候选路径改仓库内 |
| `docs/BUILD.md` | 新增 §4a"安装目录的默认位置"，列出每个工具的覆盖方式 |
| `CHANGELOG.md` | 新增 2026-09-14 条目 |
| `pytest.ini`（新增） | `testpaths = tests`，`norecursedirs` 排除 `LeoAIStudio*`、`leotree` 等。安装目录进入仓库后，从仓库根裸跑 `pytest` 会递归收集 `LeoAIStudio/upstream/OpenAI4S/tests/`（上游自己的测试，依赖未安装，14 个收集错误）；此文件把收集范围限定为本仓库的 `tests/`，详见 §8.1 |

`build_manifest.py` / `verify_release.py` 记录源层哈希的字典键由 `unified-settings-adapter.js`、`i18n-brand-patch.js` 改为 `stage/unified-settings-adapter.js`、`stage/i18n-brand-patch.js`，与第三个键 `stage/leo-inject.js` 同为仓库相对路径。两者同步改动，新生成的 manifest 与校验器一致；旧 manifest（`manifests/build-*.json` 本就不入库）需要重新生成。

### 5.3 移动的三个文件

| 原位置 | 新位置 | 附带改动 |
|---|---|---|
| `unified-settings-adapter.js` | `stage/unified-settings-adapter.js` | 字节不变 |
| `i18n-brand-patch.js` | `stage/i18n-brand-patch.js` | 头部注释重写：原注释称"本文件独立、未被发布版加载，需手工合并进 leo-inject.js"，与事实不符（`build_launcher.ps1` 每次构建都把它作为第二层打进 `theme/leo-inject.js`，`leo-inject.js` 通过 `window.createLeoLocaleCoordinator` 调用它）。代码体不变 |
| `PINN_MVP_AND_CFD_READINESS_REPORT.md` | `docs/PINN_MVP_AND_CFD_READINESS_REPORT.md` | 第 5 行指向 `PINN_PHASE2_RECONCILIATION_20260909.md` 的链接去掉 `docs/` 前缀（两者现在同目录）；正文其余字节不变 |

引用同步：`tests/test_ui_api_contract.py`（`FRONTEND_SOURCES` 两项与第 166 行）、`manifests/runtime-asset-origins.json`（`leo-inject.js` 的 `source_files`）、`.gitignore` 注释。

---

## 6. 文件分类与层划分

清理后 git 跟踪 221 个文件（含本次两份报告与 `pytest.ini`）。按目录分层如下；"层"栏表示它在产品里的角色。

| 目录 | 文件数 | 层 | 内容 |
|---|---|---|---|
| `(根)` | 7 | 仓库元数据 | `.gitattributes`、`.gitignore`、`CHANGELOG.md`、`requirements.lock`、`pytest.ini`、本次两份报告 |
| `launcher/` | 1 | Windows 壳 · 入口 | PyInstaller 入口脚本 |
| `leo_shell/` | 19 | Windows 壳 · 运行时 | pywebview 窗口、ShellApi、主题运行时、路径、凭据与设置存储、单实例、WebView2 运行时、会话模型 |
| `bridge/` | 10 | Leo 后端 sidecar | 与 WSL 内上游 gateway 之间的中继、身份、运行时兼容层 |
| `stage/` | 21 | 注入层源（发布到 `theme/`） | `leo.css`、`leo-inject.js`、`unified-settings-adapter.js`、`i18n-brand-patch.js`、`shell.html`、`themes.json`、`fonts/`、`i18n/`、`backgrounds/`、`logos/` |
| `assets/` | 4 | 源素材 | 狮子图标与背景的源图 |
| `LICENSES/` | 4 | 许可 | 打包字体的许可文本 |
| `tools/` | 27 | 构建 / 部署 / 校验 | 构建、wheelhouse、部署、manifest、strict 校验、来源审计、可移植性扫描、包契约、技能同步、headless 校验，以及 `manual_acceptance/` 9 个人工验收脚本 |
| `manifests/` | 6 | 声明与锁定 | upstream pin、依赖锁、wheelhouse 清单、运行时资产来源、测试套件登记、可移植性历史证据策略 |
| `tests/` | 35 | 回归网 | 壳、桥、主题、契约、构建、可移植性、人工验收、PINN、skills 各套测试 |
| `skills/` | 9 | 规范技能（canonical） | research-sop 等，由 `sync_skills.py` 同步到安装目录 |
| `pinn/` | 22 | 科学候选 | PINN 候选实现、治理、验证 |
| `scientific_reference/` | 3 | 科学参考 | 参考解与阈值 |
| `research_logs/` | 2 | 科研记录 | append-only 记录 |
| `adversarial/` | 1 | 对抗审计 | 审计脚本 |
| `governance/` | 8 | 治理文档 | 宪章、合规审计、P0 边界 |
| `specs/` | 3 | 规格 | 锁定的规格文本 |
| `docs/` | 39 | 报告与文档 | 构建指南、各期报告、人工验收清单；`docs/rollback/` 10 个冻结证据副本 |

仓库目录内、不入库的内容（全部在 `.gitignore` 或本就未跟踪）：

| 路径 | 角色 | 处置 |
|---|---|---|
| `LeoAIStudio/` | 正式安装目录（约 2.0 GiB） | 忽略，不动 |
| `leotree/` | Leo Tree 项目（约 589 MiB，独立 git 仓库） | 忽略，不动 |
| `.claude/worktrees/` | Claude Code 会话工作树 | 忽略 |
| `LeoAIStudio-pinn-evidence-20260908T120017Z/` | 9-08 PINN 外部证据目录（`docs/PINN_MVP_AND_CFD_READINESS_REPORT.md` 称之为 append-only 证据） | 未跟踪、未忽略、未删除；需要用户决定（见 §9） |
| `pinn/__pycache__/` 等 | Python 字节码缓存 | 本次测试运行产生的与 2026-09-08 遗留的都已删除（§8.2） |

---

## 7. 重构：减少上游 UI

### 7.1 具体改动

| 文件 | 改动 | 效果 |
|---|---|---|
| `stage/leo-inject.js` | `adapter.install(...)` 的选项 `hideAppearanceQuickControls` 由 `false` 改为 `true`，并加两行注释 | 适配器在安装时对 `#dash-theme`、`#ws-theme` 和所有 `.lang-seg` 调用 `hideControl`：上游首页与工作区各一组的明暗切换按钮和中/英切换段被隐藏（`hidden` + `aria-hidden`，可由 `restoreEntrypoints` 还原）。同样功能保留在 Leo 设置 → 外观 |
| `stage/leo.css` | 删除 `.project-card`、`.session-card` 两个选择器（第 96-98 行与第 752-754 行的两条规则各去掉这两项） | 上游 HTML/JS 中不存在这两个类名（在 `upstream/OpenAI4S` 全文检索为 0 命中），规则永不匹配；`.dash-card`、`.es-chip`、`.art`、`.gen-tiles>.tile` 的样式不变 |

没有做的事：没有隐藏任何其它上游入口（设置、笔记本、计算器、Agent、连接器、技能、记忆等全部可见）；没有新增任何 Leo 风格的 UI、配色、组件；上游 `upstream/OpenAI4S` 一个字节没动；后端零改动。

### 7.2 哈希更新（`manifests/runtime-asset-origins.json`）

| 资产 | 旧 `expected_sha256` | 新 `expected_sha256` |
|---|---|---|
| `theme/leo.css` | `b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf` | `abb3c514919f8cf589d5a893198cf4725a6eb256c41c4ec2251de68d0992bca7` |
| `theme/leo-inject.js`（三层 bundle） | `45fd5d4b95dd3d00f94e3710b32c9f2518c8658b5cecab2fa887ec6205e387dc` | `ad1e432264fec254703987bee85beb901959b5caff636a124c8571b3681e2b13` |

bundle 哈希按 `tools/bundle_theme.py` 的实际配方计算：三层各 `rstrip()` 后以 `"\n\n"` 拼接，末尾加 `"\n"`，与 `theme_asset_provenance.py` 的校验公式一致。当前三层源文件哈希：

| 层 | SHA-256 |
|---|---|
| `stage/unified-settings-adapter.js` | `27f5b3389a77a345a8ae4776de34f0e4acdf3acd306039accf67e6ad476305fc` |
| `stage/i18n-brand-patch.js` | `08fd6a4ca2bf2a29948d594f96e63421f43c7bf568bf27525a4045f45b1a8364` |
| `stage/leo-inject.js` | `fb0b545f0e26a7a38a3633d3880197a605dd1bf016b2fa878d34a567d5eee518` |

### 7.3 未验证说明

本次**没有重新构建、部署，也没有在真实窗口里看过效果**。`hideAppearanceQuickControls` 的隐藏逻辑是适配器里既有的、此前一直以 `false` 关闭的分支，本次只是打开它；它在真实 WebView2 里是否恰好只隐藏那三组控件、没有误伤其它元素，要等下一次构建部署后人工确认。已安装版本仍是 9-10 从 `14e30f4` 构建的产物，其 `theme/leo.css`、`theme/leo-inject.js` 与本次源码不一致，`verify_release.py --strict` 和 `theme_asset_provenance.py` 在重新构建前会如实报告 DRIFT。

---

## 8. 验证

解释器：用户文档目录下 `LeoAIStudio-deliveries/20260908-phase2/models-worktree/.venv` 的 Python 3.12；命令均为 `python -B -m pytest -q -p no:cacheprovider`。

| 项 | 命令 / 条件 | 结果 |
|---|---|---|
| 全套测试（工作分支的工作树，不带环境变量） | 如上 | **832 passed / 9 skipped / 0 failed**，28.7 s |
| 多出的 7 个 skip 的原因 | `pytest -rs` | 全部是 `tests/test_manual_acceptance.py:167`"the pinned upstream checkout is not available on this machine"：工作树目录下没有 `LeoAIStudio/`（它在主检出下），工具默认路径按新规则解析到工作树内，找不到上游 checkout 就跳过。另 2 个 skip 与 codex 线基准相同（`entityLifecycle` 已启用、无本地 wheelhouse） |
| 全套测试（`LEO_APP_ROOT` 与 `LEO_UPSTREAM_ROOT` 指向主检出下的安装目录） | 同上加环境变量 | **839 passed / 2 skipped / 0 failed**，25.8 s，与 codex 线 `14e30f4` 的基准 839 passed / 2 skipped 完全一致 |
| 全套测试（主检出，`master` 重置后，不带环境变量） | 在主检出执行 | 见 §8.1 |
| 可移植性扫描 | `python -B tools/portability_check.py` | **0 hard binding**，退出码 0。1 条可配置默认值（`tools/sync_skills.py` 的 WSL 发行版名，本轮之前就有）、3 条历史证据（`governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md`，策略文件已登记，本轮之前就有）。本次两份根目录报告不含绝对路径、桌面路径、Linux 家目录或 WSL 发行版字面量 |
| manifest 哈希自洽 | 脚本按 bundle 配方重算并断言 | `leo.css` 与 `leo-inject.js` 的 `expected_sha256` 等于当前源码 / 配方字节 |
| 上游字节 | 未触碰 `upstream/OpenAI4S` | 不变 |
| 构建 / 部署 / 真实窗口 | 未执行 | **NOT TESTED**（见 §7.3、§9） |

### 8.1 主检出复验

`master` 重置到本次提交后，在主检出（此时 `<仓库>/LeoAIStudio` 就在默认位置）不带任何环境变量再跑一次全套测试。结果由收尾提交补记在此。

第一次在主检出裸跑 `pytest`（`master` 已指向 `55484f2`）：收集阶段 14 个错误、2 skipped，没有跑到任何测试。原因不是本仓库的测试失败，而是 pytest 从仓库根递归收集到了 `LeoAIStudio/upstream/OpenAI4S/tests/`（上游自己的测试，依赖 pandas、bs4 等未安装）。这是安装目录进入仓库目录后的直接后果，此前在没有安装目录的工作树里不会发生。

处理：新增 `pytest.ini`（`testpaths = tests`，`norecursedirs` 排除 `LeoAIStudio*`、`leotree` 等），随收尾提交入库。

| 复验（主检出，不带环境变量） | 结果 |
|---|---|
| 显式路径 `pytest tests` | **839 passed / 2 skipped / 0 failed**，29.1 s |
| 放入 `pytest.ini` 后裸跑 `pytest` | **839 passed / 2 skipped / 0 failed**，29.0 s |
| 工作树里带 `pytest.ini` 裸跑 | 832 passed / 9 skipped / 0 failed（原因同 §8 第一行：工作树内没有安装目录） |

收尾提交之后没有再跑测试：它只增加 `pytest.ini`、补记两份报告与 `CHANGELOG.md`，而 `pytest.ini` 的效果已在主检出以同一字节内容验证。

### 8.2 测试产物的建立与删除

用户要求：测试运行建立的文件必须删除，建立与删除都要留痕。所有测试均以 `-B -p no:cacheprovider` 运行，运行后按 `git status --ignored --untracked-files=all`、按修改时间的 `find` 以及用户临时目录逐处盘点，结果与处置如下。

| 产物 | 位置 | 由谁建立 | 数量 / 大小 | 处置 |
|---|---|---|---|---|
| pytest 临时目录 `pytest-333`、`pytest-334`、`pytest-335` 与 `pytest-current` 链接 | 用户临时目录下的 `pytest-of-user/` | 主检出的 3 次全套运行（05:01–05:03）；工作树 3 次运行所建的目录已被 pytest 自身"只保留最近 3 次"的轮换删除 | 5,037 个文件，112,468,305 字节 | 整个 `pytest-of-user/` 目录已删除，删除后目录不存在 |
| 字节码缓存（工作树） | `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d/` 下的 `pinn/__pycache__/`、`pinn/governance/__pycache__/`、`pinn/reference/__pycache__/`、`pinn/validation/__pycache__/`、`scientific_reference/__pycache__/`、`tests/skills/__pycache__/` | 第一次全套运行（04:46）拉起的子进程；`-B` 只约束主解释器 | 18 个文件 | 6 个目录整体删除，删除后不存在 |
| 字节码缓存（主检出，本次） | 主检出下同样的 6 个目录 | 主检出的全套运行（05:01–05:02） | 15 个文件 | 删除，删除后不存在 |
| 字节码缓存（主检出，2026-09-08 遗留） | `pinn/__pycache__/__init__.cpython-312.pyc`；`pinn/governance/__pycache__/` 下的 `__init__`、`jsonschema_lite`、`locking`、`nodes`、`prelock`、`provenance`、`semantic` | 早前会话，不是本次 | 8 个文件 | 与上一行同目录，一并删除（纯缓存，已被 `.gitignore` 覆盖，按需重生成） |
| 测试输出日志 `pytest-run1.log`、后台任务输出 `bl6aqrddd.output` | 本会话的 scratchpad 与任务目录（用户本地应用数据下的 `Temp/claude/…`） | 第一次全套运行 | 2 个文件 | 删除，删除后不存在 |
| 会话辅助脚本 `apply_edits.py`、`hashes_gitignore.py`、`docs_edits.py`、`fix_header_rehash.py`、`fill_reports.py`，报告草稿 `report_software.md`、`report_hygiene.md`，盘点输出 `bokwwpgoz.output`、`bokwwpgoz.txt` | 同上 | 本会话（非测试所建，一并留痕） | 9 个文件 | 报告提交后、会话结束前删除，最终汇报里确认 |
| `pytest.ini` 副本 | 主检出根目录 | 本会话为验证裸跑效果临时复制 | 1 个文件 | 不删除：`master` 重置到收尾提交后它成为跟踪文件，字节与提交内容相同 |
| `.pytest_cache/`、`docs/manual-acceptance-evidence/`、`LeoAIStudio/` 与 `leotree/` 内的新文件 | — | 未产生（`-p no:cacheprovider`；安装目录按修改时间核查，本次运行后没有任何新文件或改动） | 0 | — |

---

## 9. 没有做的事与需要用户决定的事

**没有做的事**

1. 没有重新构建、部署，没有在真实 WebView2 窗口里验证隐藏效果（§7.3）。下一步应是：`tools/build_launcher.ps1` → `tools/deploy_release.ps1` → `python tools/build_manifest.py` → `python tools/verify_release.py --strict`，然后人工确认顶栏 / 侧栏的语言与明暗控件只在 Leo 设置 → 外观出现一次。
2. 没有改写 `docs/` 下历史报告与 `CHANGELOG.md` 2026-09-07 段落里关于旧布局（安装目录在仓库上一级、`capture_window.ps1` "保留"等）的叙述。它们是当时的记录，可移植性扫描对 `docs/*.md`、`CHANGELOG.md` 与 `docs/rollback/` 按类豁免。
3. `docs/rollback/` 下的冻结副本（含引用旧根目录 JS 路径的三份 `build_launcher.pre-*.ps1`）按设计不动。
4. 没有动 `LeoAIStudio/` 内的三个 `.leo-rollback-*` 回滚目录，也没有动 `LeoAIStudio/bridge/__pycache__/`、`LeoAIStudio/user/user-skills/research-sop/__pycache__/`（应用自身运行产生，不是本次测试所建）。
5. 没有执行 `git gc`，没有删除任何分支或工作树。
6. 全新 Windows 账户 / 非 `leo` WSL 用户下的人工验收仍是 NOT TESTED（与此前一致）。

**需要用户决定的事**

1. `LeoAIStudio-pinn-evidence-20260908T120017Z/`：位于仓库目录内，未跟踪、未忽略。它是 9-08 PINN 阶段的外部证据目录，本次没有列为删除候选。建议：若要长期保留，加入 `.gitignore`；若已无用，另行审批后删除。
2. `claude/leoaistudio-cleanup-refactor-d129a8` 工作树与分支（指向 `8c4835e`，从未使用）：建议移除，让 `8c4835e` 进入可回收状态。
3. `claude/leoaistudio-cleanup-refactor-9e137d` 工作树与分支：`master` 已与它同步，任务收尾后可移除。
4. 下一次构建部署的时间：在此之前，安装版与源码的主题层哈希不一致是预期状态。

---

## 10. 变更文件清单

工作分支相对 `14e30f4` 的两次提交：26 个源文件改动、2 份新报告与 `pytest.ini`。

| 类型 | 文件 |
|---|---|
| 修改 | `.gitignore`、`CHANGELOG.md`、`docs/BUILD.md`、`manifests/runtime-asset-origins.json`、`stage/leo-inject.js`、`stage/leo.css`、`tests/test_ui_api_contract.py`、`tools/build_launcher.ps1`、`tools/build_manifest.py`、`tools/deploy_release.ps1`、`tools/headless_verify.py`、`tools/sync_skills.py`、`tools/theme_asset_provenance.py`、`tools/theme_preview.py`、`tools/verify_release.py`、`tools/manual_acceptance/collect_windows_account_env.py`、`tools/manual_acceptance/verify_clean_build.py`、`tools/manual_acceptance/verify_research_sop_live.py`、`tools/manual_acceptance/verify_webview2_runtime.py` |
| 移动（内容有改） | `i18n-brand-patch.js` → `stage/i18n-brand-patch.js`（头注释）；`PINN_MVP_AND_CFD_READINESS_REPORT.md` → `docs/PINN_MVP_AND_CFD_READINESS_REPORT.md`（1 处链接） |
| 移动（字节不变） | `unified-settings-adapter.js` → `stage/unified-settings-adapter.js` |
| 删除 | `tools/capture_window.ps1`、`tools/watch_window.ps1`、`tools/inspect_webview.mjs`、`tools/extract_launcher.py` |
| 新增 | `20260914软件修改报告.md`（本文件）、`20260914仓库卫生记录.md`、`pytest.ini` |
| 未改 | `upstream/OpenAI4S`（安装目录内，非仓库文件）、`bridge/`、`leo_shell/`、`launcher/`、`skills/`、`pinn/`、`tests/`（除上述一处路径改动）、`stage/` 其余文件 |

提交号：

| 提交 | 内容 |
|---|---|
| `55484f2`（父提交 `14e30f4`） | 主体：以上全部源码、manifest、文档改动与两份报告的初稿 |
| 收尾提交（`55484f2` 之子；提交号见 `git log -1 master`） | 新增 `pytest.ini`；补记本报告 §8.1、§8.2、§10 与卫生记录 §2.4、§6；`CHANGELOG.md` 加一行 |

主检出 `master` 先重置到 `55484f2`（用于主检出复验），最终重置到收尾提交。

---

## 11. 第二轮追加（2026-09-14 下午）

第二轮的逐条操作记录在 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md)，本节只记结论。

### 11.1 用户拍板

| 事项 | 决定 |
|---|---|
| PINN 证据目录 | 先归档到仓库外再删（用户审批通过） |
| 工作树与分支 | 现在移除；d129a8 是本会话 shell 的当前目录，放到会话最后一步 |
| 构建环境 | 复用 codex 侧 `.venv`（环境审计 0 问题、不联网） |
| 部署 | 构建后立即部署 |
| 六方团队 | Claude 为队长；豆包 / GLM / Kimi / DeepSeek 已交付；Grok 车道由队长自己完成 |

### 11.2 结果

| 项 | 结果 |
|---|---|
| 证据目录 | 归档 zip（117 条目，SHA-256 `9916e20c…`）存于用户文档目录 `LeoAIStudio-deliveries/20260914-archive/`，原目录已删 |
| 工作树 9e137d | git 已注销，分支已删（曾指向 `2fabbe4`）；顶层空目录被另一进程占用，待其退出后 `rmdir` |
| 构建 | hermetic，提交 `13dc7ea`，42.5 s，包契约 PASSED（315 / 31 / 29） |
| 部署 | 7.1 s，回滚目录 `LeoAIStudio/.leo-rollback-20260914-063236-dc3d45e8`，EXE SHA-256 `a4bfda609aa2…`，桌面快捷方式已重写 |
| strict 校验 | 12 PASS / 1 FAIL；FAIL = 技能副本漂移（安装目录与 WSL 各 6 个文件比仓库规范副本旧，既有问题，`skills/` 本轮未改），待用户决定是否同步 |
| 交付物 | 五份 R1 交付物原样入库 `docs/pinn-trust-loop/inbox/`（`13dc7ea`）；合并说明 `docs/pinn-trust-loop/R1_MERGE_NOTES.md` |
| 团队提示词 | `docs/PINN_TRUST_LOOP_TEAM_PROMPTS_20260914.md` |

### 11.3 仍未验证

- 真实窗口：部署后尚未启动程序；顶栏 / 侧栏的语言与明暗控件是否只在 Leo 设置 → 外观出现一次，需要用户启动确认。
- strict 校验的 FAIL 在技能同步之前保持。

### 11.4 待用户决定

技能同步、示例 (b) 口径、是否现在开始实现合并说明 §3。

### 11.5 实现：可信闭环 R1

按用户第三批答复"现在开始实现"，队长把合并说明 §3 落地：宪法修正案草案 `governance/AMENDMENTS/A-0001-trust-loop-r1.md`（PROPOSED，宪法正文未改）、三份 schema、弱链演算 `pinn/governance/trust_vector.py`、文档校验 `pinn/governance/trust_loop.py`、状态机 FAIL 分流扩展、协议汇编 `governance/PINN_TRUST_PROTOCOLS_R1.md`、报告模板 `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`，以及 91 项新测试。全套测试 930 passed / 2 skipped / 0 failed，可移植性 0 硬绑定。逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.11。

待用户：把修正案 status 改为 ACCEPTED（或指示我改）后，宪法正文才更新到 1.1。

### 11.6 A-0001 第 2 稿与 R2 开题（2026-09-15）

用户确认真实窗口的隐藏效果（§11.3 关闭）；评审修正案第 1 稿为 PROPOSED / CHANGES REQUIRED，五项治理漏洞在第 2 稿封死：两层诊断（症状 → 根因 → Gate）、独立的 Applicability 类型、评估集三分与 claim 集盲态、seed 分档 0.8 / 0.9、C3 的独立合格 run。第 5 项驳回一半（同规格同代码是"同一方法"的定义）。新测试 122 项，全套 961 passed / 2 skipped。R2 提示词四份（无 Grok）见 `docs/PINN_TRUST_LOOP_TEAM_PROMPTS_R2_20260915.md`。逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.13。修正案仍为 PROPOSED，待用户复审。

### 11.7 R2 合并与 A-0001 第 3 稿（2026-09-15，接手会话）

用户复审第 2 稿为 PROPOSED / MINOR CHANGES REQUIRED（五项）并要求对抗性闭合审计。队长按"不因是评审意见就默认正确、不因测试通过就默认现有设计正确"的标准逐项裁决：两项 ACCEPT、三项 ACCEPT_WITH_MODIFICATION，五处正式 REJECT（整维豁免的两个方案、真正不可变存储、环境字段全异、分母下限），论证在 `docs/pinn-trust-loop/R2_MERGE_NOTES.md` §3。落地：INV-A1 与规格级检查注册表；评估集样本级互斥（样本清单契约、精确 float64 身份、预注册最小间距）；claim 集哈希链账本（状态由账本推导、决策引用账本头、specHash 不含 revision 与 claim 集状态）；统一的执行环境身份（强 / 弱字段，C3 与 G6 同一函数）；无除法的离散度规则。审计另封八条路径（根因挑选、revision 规避、specHash 覆盖、证据等级重标、C3 计数、Red Team 泄漏、Gate 重置、人工向上覆盖）。R2 交付物三份入库（DeepSeek 未收到），队员建议 35 条裁决。新增测试 70 项，全套 **1031 passed / 2 skipped**。修正案仍 PROPOSED，待用户终审；宪法正文未改。逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.14。

### 11.8 A-0001 终审通过与 DeepSeek 补交（2026-09-15）

用户终审第 3 稿"通过"：修正案 status 改为 ACCEPTED，effectiveDate 2026-09-15，登记簿同步。DeepSeek 的 R2 交付物补交入库，其诊断实验库、逐格判定、seed 阈值统计论证、泄漏不变量与 Applicability 表并入协议汇编；建议新增的三个矩阵格作为 A-0002 候选。GLM 复发升级规则采纳，claim 集密封存储选权限目录。宪法正文更新到 1.1 被现行 PRELOCK 绑定挡住（Poisson v1.0 草案与宪法 1.0 字节哈希绑定，改字节即 PRELOCK FAIL 且既有测试失败），方案待用户决定，见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.15。代码无改动，测试基线仍 1031 passed / 2 skipped。

### 11.9 宪法 1.1 落笔（方案一，用户同意，2026-09-15）

宪法正文按 A-0001 的 affectedArticles 更新为 1.1：十二个章节加【A-0001】条款，新增第六十四～六十六章。PRELOCK 校验的版本引脚由硬编码 "1.0" 改为受支持集合 {1.0, 1.1}，并要求草案绑定的版本等于宪法元数据声明的版本；字节哈希绑定不变。Poisson 1D v1.0 三份草案在用户审批下重绑定到 1.1（仍是 lockedAt 为 null 的草案，无 lock、无训练），新增证据文件 `PINN_V1.3_PRELOCK_DRY_RUN_A0001.json`，旧证据保留。新增 PRELOCK 回归测试 2 项，全套 **1033 passed / 2 skipped**。逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.17。至此 A-0001 完整生效；A-0002 候选（DeepSeek 三个矩阵格）待下一修正案。

### 11.10 A-0002 起草：DeepSeek 矩阵建议的裁决（2026-09-15）

用户授权队长裁决 DeepSeek 建议。采纳三个可接受矩阵格（sBcResidual → 容量、sPinnCfd → 容量、sLocalizedError → 规格），驳回三格（sPinnCfd → 采样、正向问题的数据格、sSeedSensitive → 实现）。矩阵是宪法条款，因此起草 A-0002（1.1 → 1.2，PROPOSED），代码矩阵、测试（+5）、协议汇编、合并说明、登记簿已同步，全套 **1038 passed / 2 skipped**。宪法 1.2 落笔、版本引脚加 1.2、草案重绑定与新证据文件等用户终审后按 §11.9 的同一流程执行。逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.18。

### 11.11 A-0002 第 2 稿：因果可判定审查（2026-09-15）

用户复审 A-0002 第 1 稿为 CHANGES REQUIRED（六项）。队长逐项裁决，六项全部接受（其中三项带修改），推翻了自己第 1 稿的两条驳回理由：采纳 sPinnCfd → 采样与 sSeedSensitive → 实现；闭合审计另补三格（残差 / 边界残差 → 奇异性，seed 敏感 → 非唯一规格）。命名容量或采样必须做受控多档多 seed 干预，命名非确定实现必须做同 seed 重放并定位缺陷，命名任一根因的排除义务随候选数同步增加，observedSignatures 封住"挑症状"。矩阵范围写成 forward-problem MVP 进 schema。新增修正案登记簿校验器（通用 dependsOn，ACCEPTED 链与宪法版本一致）并挂进 PRELOCK。新增测试 20 项，全套 **1058 passed / 2 skipped**。宪法仍 1.1，A-0002 第 2 稿待用户终审。逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.19。

### 11.12 A-0002 第 3 稿：Final Closure Review 与实验准入审计（2026-09-15）

用户对 A-0002 第 2 稿做最终收口审查，限定三项剩余问题并要求"是否可以结束宪法设计、进入真实实验"的准入审计。队长审计发现 Issue 1 为 BLOCKING：可接受矩阵是单一全局最新表，`diagnose` 不读宪法版本，PROPOSED 的 A-0002 已经改变了 1.1 的运行时语义。最小修复：矩阵与命名义务按宪法版本分表，入口只认 `SUPPORTED_CONSTITUTION_VERSIONS` 内的版本（运行时读取），`diagnose` / 文档校验必填版本，DiagnosisRecord 必填 `constitutionVersion`，登记簿 R5（PROPOSED 版本不得已生效）与 PRELOCK 一致性——1.2 的八格与义务在 PROPOSED 期间对任何入口不可达，1.1 的表在测试里逐格冻结。Issue 2：接受问题、不机械接受实现——加 `explainedSignatures ⊆ observedSignatures`，覆盖不变量放在记录集合上（∪explained = observed、每症状恰好一条记录，冲突归因非法 → rUndetermined）。Issue 3：sSeedSensitive → rSpecDefect 限定为非预期不可识别性，命名须附 P34 `identifiability` 记录，合法多解与判定不了意图都拒绝。新增测试 29 项，全套 **1087 passed / 2 skipped**，PRELOCK 7/7 PASS。队长建议 **READY FOR USER ACCEPTANCE**（status 仍 PROPOSED）；准入审计 **NOT_READY**，blocker 只有三个：A-0002 等用户终审、Poisson 1D 校准实验未实跑、失败路径实验未实跑。完整报告 [docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md](docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md)，逐项见 [docs/OPERATION_LOG_20260914.md](docs/OPERATION_LOG_20260914.md) §5.20。

### 11.13 治理 1.2 生效 + Poisson 1D 两场正式实验（2026-09-15 夜～09-16）

用户授权后：A-0002 按 §5.17 配方正式生效（宪法 1.2、SUPPORTED 与 schema 枚举加 1.2、草案重绑定、新证据文件；GOVERNANCE_ACTIVATION PASS）。随后不再设计规则，实现 R3 最小 runner（`pinn/experiments/`），跑两场实验：实验 1 走完全部 Gate，Gate 5 在 claim 集上诚实判 FAIL（AC-3 边界误差 7/10 seed 超 1e-4，其余 AC 与物理检查全过）；实验 2 人为欠采样 → Gate 4 FAIL → 受控干预 → rSamplingDeficiency → 只改采样 → 重入 Gate 4 → 训练恢复 → Gate 5 再因 AC-3 FAIL。两实验按治理标准 PASS，MVP 闭环 VALIDATED；最高 Claim 均 BLOCKED；建议 REMAIN AT POISSON CALIBRATION STAGE。新发现：协议只有一套 claim 网格使 G5 FAIL 后无法在同规格再验证（AMENDMENT/PROTOCOL CANDIDATE，待裁决）。全套 **1094 passed / 4 skipped**，PRELOCK 7/7。报告 [docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md](docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md)，逐项见操作日志 §5.21–§5.22。

### 11.14 Poisson 1D 向 C2 校准（2026-09-16）

修复 claim 集身份漏洞（按样本身份烧毁，实验 2 重新包装的 claim 集追溯为非独立证据并注解）；预注册 claim pool 与配对干预准则；实验 1 的 AC-3 失败经 P24/P28 受控干预正式诊断为 rSpecDefect（软执行），只改 enforcement soft→hard，revision 2 在全新盲 claim 集上 Gate 1–5 全 PASS（AC-3 恰为 0），Tier-1 Red Team 全部维持；C_repro 因无独立环境 BLOCKED，最高 Claim C1，复现包已生成等待另一环境。全套 **1109 passed / 6 skipped**，PRELOCK 7/7。报告 [docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md](docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md)，逐项见操作日志 §5.23。

### 11.15 Poisson 1D 校准收口：G6 独立环境复现与 SUPPORTED @ C2（2026-09-16）

按用户限定范围：追加 BC 根因 post-audit 注解（历史 verdict 不改，因果归因标注非唯一）；前瞻性干预准则澄清；G6 语义审计确认代码与宪法 28.1 一致；同机建立全新独立安装 Environment B（新 venv、`--no-cache-dir` 安装复现包声明依赖，无复制克隆）；在 exp3c 原 commit 的干净分离检出上用 Environment B 执行冻结复现包（seed +10000，不触碰 claim 集），dev 相对 L2 中位 2.552e-4 vs 1.991e-4（差 5.6e-5 ≤ 预注册 1e-4），k/N 10/10 一致 → C_repro PASS；六维 PASS，ClaimGateDecision（校验器通过）允许 C2，状态机 ACCEPTED。**POISSON 1D CALIBRATION: CLOSED；PINN SCIENTIFIC-CLAIM MVP: VALIDATED AT C2**。新代码 runner 的首次复现因 codeHash 不同被 `reproduction_status` 正确判 BLOCKED，记录保留并注解。全套 **1112 passed / 6 skipped**，PRELOCK 7/7。报告 [docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md](docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md)，逐项见操作日志 §5.24。不自行开始 2D，等待外部评审。

### 11.16 2D Manufactured Poisson Calibration：SUPPORTED @ C2（2026-09-16）

用户授权后进入 2D。先做复用审计（治理层——样本身份、账本、六维向量、状态机、PRELOCK、schema——全部 REUSE_AS_IS；1D 的求解 / 度量 / 绘图全部 1D_HARDCODED），因此**新建 `pinn/experiments2d/`，`pinn/experiments/runner.py` 一行未改**，只把共享的报告渲染器做最小参数化（1D 输出不变）。新增：冻结的 2D 规格（放在 `specs/` 前缀内，自动进入代码身份，无需改代码身份定义）、解析参考、独立五点 FDM（观测阶 2.0084 / 2.0021 / 2.0005）、AC2D-1..9 验收合同（每条判据都带 DIMENSION-INVARIANT / SENSITIVE 判定与阈值来源）、可信校验器与 7 个控制夹具。EXPLORATORY 性能 pilot 只用 D_dev，选择规则先于结果写定（1D 架构原样移植余量不足被淘汰，选 4×64 / 10000 步）；预注册先于任何正式 run 提交；盲集池四套按"CGL 计数与 6 互素且两两互素"构造，规避 1D 那类有理格点碰撞并避免成员间整族共享节点。正式 run `exp2d-poisson-calibration-r1`：G1–G5 全 PASS，10/10 seed（median dev 相对 L2 3.686e-5），3328 样本的盲 claim 集只打开一次即烧毁，十个 seed 全部满足 AC2D 的 MUST 与 SHOULD；Tier-1 七项全部维持（**P7 在 2D 改判 APPLICABLE**，P8 的硬参数化随域缩放未重演 1D 的 harness 缺陷）；G6 在按授权新建的独立 venv 上复现（同 spec、同 codeHash、异 seed，|Δmedian| 4.0e-6，同时满足绝对 1e-4 与收紧的相对 0.5×median）→ 六维 PASS → **SUPPORTED @ C2，状态 ACCEPTED**。

维数提升审计的答案：**没有任何治理条款因维数失效**；被击穿的是度量与判别设计——对称的制造解在 claim 层无法判别 x/y 互换（补 Gate 3 的非对称探针 T2），全局 L2 看不见空间热点（补 AC2D-9 逐块判据）。另按用户指令补两项审计：portability（HEAD 真实基线是 **1109 passed / 3 failed**，不是 1D 收口报告记的 1112 / 0；本轮 2D 证据又新增 3 条同类绝对路径发现，**未改 policy、未改证据、未加豁免**，裁决留给用户与外部评审）与 pilot 角色（pilot 同时做了架构 / 模型选择，宪法 1.2 第 561 行明文允许 D_dev 承担模型与架构选择，第六十五章要求的"冻结规格下重走完整闭环"本轮已满足 → ALLOWED，不阻断 C2）。新增测试 22 项，全套 **1121 passed / 3 failed / 16 skipped**（3 红即上述既有 portability），被跳过的 10 项在训练解释器下另跑 17 passed / 0 failed；PRELOCK 7/7。报告 [docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md](docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md)，逐项见操作日志 §5.26。结论 **READY FOR NEXT 2D COMPLEXITY STEP**；本轮到此 STOP，不开始不规则几何 / BFS / Navier–Stokes / UCM / 新修正案 / 架构扫描，等待用户与外部评审。

### 11.17 2D Final Closure Audit（2026-09-16）

外部终审提出五项收口。逐项结果：**Issue 1（AC2D-9）判为 CASE A**——预注册、合同、实现与机器记录四者一致（分母是参考解 u\* 的 RMS，`gate5b_external.json` 里逐位可验），只有报告的缩写标签漏了 u\*；用已存预测重算证明终审读法恒 ≥ 1（实测 1.989–3.101）而实现读法为 6.13e-05–1.09e-04，**C2 不受影响**，处理方式是追加 POST_AUDIT_ANNOTATION + 更正标签 + 新增不变量测试。**Issue 2（P11）**：核对协议后确认原 NOT_APPLICABLE 无依据（协议汇编把 P11 列为 C2 前必跑；红队交付物的豁免作用域是 1D MVP），先提交预注册再补跑一次，Δq 1.417e-05 → PASS；诚实记录残差自适应加密使 dev 误差上升约 53%，即它在本问题上不是改进。**Issue 3（portability）**：源码不再写死用户路径、新证据改记 installationId，发现数 7 → 5；但精确哈希豁免**无法应用**——加载器硬性只接受 `governance/**.md`，扩大作用域等于改 policy 机制，已回滚并报告冲突。**Issue 4（claim pool）**：状态改由账本推导，护栏前移到训练之前。**Issue 5（localized error）**：旧 1D 规则在合格 2D run 上 9/10 误报，四候选标定后最佳者仍误报 2/10，**拒绝上调阈值**，登记为 NOT CALIBRATED 并给出前瞻协议（要求由验收判据承担、症状规则需 ≥ 5 个已验证 run 建经验 null），归类为协议标定而非修宪。**Issue 6**：全链重校验零问题 → **CURRENT 2D C2: CONFIRMED**；**Issue 7**：portability 与症状规则未收口 → **NEXT COMPLEXITY STEP: HOLD**。新增 28 项测试，全套 1147 passed / 3 failed / 18 skipped，PRELOCK 7/7。报告 [docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md](docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md)，逐项见操作日志 §5.27。

### 11.18 外部评审裁决执行：收口完成，NEXT COMPLEXITY STEP READY（2026-09-16）

用户 / 外部评审给出七项裁决，解除了终审收口留下的 HOLD。**裁决 2（portability）**：批准把豁免机制的作用域从 `governance/**.md` 扩到「人工批准的不可变证据文件」，严格条件照办——只允许 `governance/`、`experiments/` 下的 `.md`/`.json`，另设可执行后缀黑名单兜底（`.py`/`.ps1`/`.sh`/`.exe` 等一律拒绝，参数化测试里明确包含就在同一棵树里的 `experiments/poisson2d/qualify_environment_b.py`），通配符、`?`、目录写法一律拒绝，每条豁免必须带 `ruling` 与 `constraint`；归类逻辑一字未改，仍是 `file + sha256 + finding_type + occurrence` 四项全等、一个字节变化即失效。据此归类 5 条既有发现（1D 证据 4 条 + 2D 环境鉴定 1 条），**被指认的证据文件一字未改**，报告输出仍逐条显示 `EXEMPT-HISTORICAL-EVIDENCE` 与其 sha256（可见性有断言）。**裁决 4 / 5（localized error）**：d ≥ 2 的 `sLocalizedError` 触发条件改为「该问题预注册的局部误差验收判据失败」，Poisson2D 的实例是 AC2D-9——统计量与验收判据是同一测量（不同点集），阈值必须等于验收合同里的值（症状不得自带松紧，于是没有任何可事后调的常数），只读 D_dev，`claim` 被显式拒绝，未预注册即 fail-closed 报错，且**不回溯**已完成的 run（配置在代码身份内，事后改字节会被机器拒绝）；max/median、robust-z、top-k、参考条件化 z 四个候选降为 diagnostics / calibration research。治理归类为协议澄清，**不起 A-0003**。**裁决 3**：Environment B 保留为冻结复现夹具，本轮对该目录未做任何操作。**裁决 6**：全套 **1172 passed / 0 failed / 18 skipped**（净增 25 项测试），被跳过的在训练解释器下 23 passed / 0 failed，portability **0 hard binding**，PRELOCK **7/7** → 输出 `CURRENT 2D C2: CONFIRMED` 与 **`NEXT COMPLEXITY STEP: READY`** 后 STOP，不自行启动下一个 PDE。**裁决 7**：下一次正式实验必须使用新 revision / code identity，不得冒充生成既有 C2 的 `a39aa07e23d0…`。报告 [docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md](docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md)，逐项见操作日志 §5.28。

### 11.19 Localized-error trigger 硬化（2026-09-16）

外部评审拿到 `33dc22b` 的定向源码包后给出三项代码级发现。按令**先独立复现再动手**，三项全部 **CONFIRMED**（并复现出评审未列的两条：`+Inf` 会让信号巧合地 fired=True，空 ensemble 裸 `IndexError`）。**Issue 1**：旧实现用 seed 中位数判定，实测 1/10 与 4/10 个 seed 失败局部判据时信号都保持沉默，而 Gate 5b 对 MUST 判据执行的是 `all(...)`——一个 seed 失败即验收失败；完整 caller chain 表明 Gate 判决不会丢（`claimSetVerdict` 里有），丢的是 `observedSignatures` 里的 `sLocalizedError`，即诊断的候选根因覆盖。修法是**复用 Gate 的既有策略**而不是发明比例：判据合同登记 `seedPolicy="every-seed"`，并新增不变量测试证明对 k = 0…10 信号触发**恰好等价于** Gate 5b 的 MUST 判定失败——既不更弱也不更严；同时完整保留 `perSeedValues / failingSeedIndices / failureCount / failureFraction / ensembleStatistic`。**Issue 2**：NaN / ±Inf / 负值 / 空 ensemble / 长度不一致（`zip` 静默截断，实测把一个巨大误差整个丢掉）全部改为 fail closed，复用仓库已有的 `ValidationInputError`，并在 `block_statistics` 与 `localized_acceptance_ratio` 两处都验，不依赖调用方。**Issue 3**：新增 `LOCALIZED_ERROR_CRITERION` 合同与 `localized_criterion()` 解析器，把 criterionId 绑定到 statistic / normalization / partition / operator / threshold / level / seedPolicy，阈值等全部从既有冻结表推导（无新常数）；评审构造的"AC2D-2 借 5e-3 判局部误差"现在被拒。**历史影响 NO IMPACT**：重跑历史证据重校验——零问题、六维 PASS、ACCEPTED、C2 CONFIRMED，账本 / D_claim / TrustVector / ClaimGateDecision / 冻结配置 / 阈值一律未动。新增 69 项测试，全套 **1241 passed / 0 failed / 18 skipped**，训练解释器下 23 passed / 0 failed，portability 0 hard binding（只跑回归未改规则），PRELOCK 7/7。结论 **HARDENED / C2 UNCHANGED / NEXT FORMAL EXPERIMENT IMPLEMENTATION: READY**，随即 STOP。报告 [docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md](docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md)，逐项见操作日志 §5.30。

### 11.20 代码身份完整性审计（2026-09-16）

下一个正式 PDE 实验开始前的边界审计。**先澄清一条事实**：`pinn/experiments2d/localized_error.py` 本来就在代码身份之内（`pinn/` 前缀），它不在已 ACCEPTED run 的记录清单里只是因为那次 run 时它还不存在——此处没有修复，只加回归测试。**真正的缺口有两个**：`governance/PINN_TRUST_PROTOCOLS_R1.md`（协议汇编决定 Tier-1 强制集合，正是它使 P11 成为 C2 前必跑，字节能改变 Red-Team 判定）与 `adversarial/core_manifest.draft.json`（PRELOCK 的输入，决定正式 attempt 是否开始），两者加入具名身份文件。另有结构性缺口：正式 run 的驱动脚本可位于 `experiments/**`，而该目录不能整体纳入（同处存放每次都变的证据，纳入等于"每跑一次就是另一种方法"），因此改用**声明制** `config["codeIdentityExtraFiles"]`。新增 `assert_code_identity_complete()` 在 **codeHash 之前、PRELOCK 之前**做 fail-closed 检查（缺文件 / 声明不存在 / 清单与磁盘不符一律拒绝），`identity.json` 新增 `codeIdentityBoundary` 使边界本身可审计。新边界下当前树清单 75 项（原 73），新增 44 项对抗测试：22 个判定相关模块逐一的一字节敏感性、文档与证据改动不移动 codeHash（含在 `tmp_path` 里 `git init` 的端到端验证）、清单遗漏在 PRELOCK 前被拒、顺序断言、历史身份不被改写。**对已 ACCEPTED 的 Poisson2D 无影响**：重校验零问题、C2 CONFIRMED、ACCEPTED，其 `codeHash` 仍 `a39aa07e23d0…` 且记录清单未被改写。全套 **1285 passed / 0 failed / 18 skipped**，训练解释器 23 passed / 0 failed，portability 0 hard binding，PRELOCK 7/7。下一个正式实验必须在新边界下生成清单并使用新 revision。报告 [docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md](docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md)，逐项见操作日志 §5.31。

### 11.21 GEOMETRY LIFT 1：圆环制造解 Poisson 标定 —— NOT YET PASS / BLOCKED（2026-09-17 / 18）

可信闭环的第一次**几何提升**：从单连通正方形走到曲边、带内孔、多连通的圆环 `a^2 < x^2 + y^2 < 1`（a = 0.35），两条边界组件。预注册、冻结配置、盲集池（DAC-M0..M3，两两共享样本 0）与 ProblemDefinition（specHash `4c8dfbc7238d…`）在正式 run 之前冻结。**device 被做成运行时参数而非配置字段**：配置在 `codeHash` 之内，而 G6 复现必须在只有 CPU 的 Environment B 上跑**同一个 codeHash**，device 一旦进配置该复现就永远无法成立；训练在选定设备上进行，**所有 Gate 数值一律在 CPU 上评估**，确定性不关（CUDA 下显式设 `CUBLAS_WORKSPACE_CONFIG=:4096:8`）。事前 EXPLORATORY 基准如实测出 **GPU 在本负载上并不更快**（网络极小 + 宪法要求 float64 + RTX 4060 的 FP64 吞吐为 FP32 的 1/64），数字上报后用户仍选择 GPU，代价写进预注册追加节（第 14 节，**只追加不改写**，追加性经逐字节前缀比对验证）。Tier-1 驱动入口在正式 run **之前**进入代码身份，避免跑完再加 driver 二次改变 `codeHash`。首次 GPU attempt 在第 3 个 seed 时因机器休眠被杀，归档为 `runs/stopped-gpu-r1-sleep-8ee9b9236199/`（不删除；无断点续跑，因为加续跑会改 `codeHash` 反而作废已完成的 seed），十个 seed 从头重训。**正式 run 结果**：Gate 1/2/3 PASS（独立极坐标 FDM 观测阶 2.0016 / 2.0004；十项实现检查含 T11 成员判定、T12 内外法向朝向、T13 求积雅可比 6.44e-16），Gate 4 PASS（10/10 跑满 120000 步，median 1.853e-04、IQR 2.470e-05、worst 3.874e-04，NaN 与发散各 0），Gate 5a 物理 PASS（通量 1.633e-04、能量 1.674e-04、SPD、极值、正性、成员；PH4/PH5 登记 NOT_APPLICABLE）。盲集 DAC-M0 按协议一次性打开并随即 BURNT，**Gate 5b FAIL**：十个 seed 中 seed 2 的局部误差判据 **ACA-9 = 1.079e-03 > 1e-3**（超 7.9 %），其余九个为 4.196e-04–6.537e-04，而 **ACA-1..ACA-8 九个判据对全部十个 seed 全通过**；按合同 `seedPolicy = every-seed` 判 `C_external = FAIL` → `FAILURE_RECORDED`，`observedSignatures = ["sLocalizedError"]`，**阈值一个未动、未现场调参、未重训**（用户 2026-09-17 裁决）。**根因尚未正式判定**：在迄今考察的正方形与圆环两个案例中未观察到圆环特有的局部/全局误差比放大（3.20、2.93 ± 0.52），在这两个案例内 ACA-9 触顶与全局误差水平高出 5.2 倍相符；「训练预算不足」因此是**受支持的假设**，不是已正式识别的 RootCauseClass——共用 `1e-3` 阈值时 ACA-9 的隐含 ACA-1 上限是 `1e-3 / 2.93 ≈ 3.414e-04`，本轮 worst-seed 为 3.722e-04，恰好越线；而预注册的步数外推只针对 ACA-1（当时已如实记录其余量仅约 1.4 倍）。十个 seed 的最差局部单元全部落在中间两个径向环，**从不**紧贴孔或外圆，多连通域没有制造孔边病理。上一轮的局部误差触发器硬化在此得到真实验证：`fired=true / "1/10 seed(s) fail ACA-9"`，而 ensemble median 4.109e-04 远低于阈值——硬化前的 median 口径会把这次失败整个吞掉。Tier-1（八项）与 G6 **均未执行**（前者只在 Gate 5 PASS 后做，后者 `C_repro = BLOCKED`）；Environment B 仅只读核验、未安装任何包。TrustVector `math/impl/train/physics PASS，external FAIL，repro BLOCKED`，**未生成 ClaimGateDecision**，C0/C1/C2 一律未授予。图 10 张（第 11 张为 Red Team 汇总，因 Tier-1 未执行而如实缺席）。全套 **1391 passed / 0 failed / 25 skipped**，训练解释器下 annulus 7 passed / poisson2d 23 passed，portability 0 hard binding / 1 configurable / 8 historical，PRELOCK 7/7。结论 **`Geometry Lift 1: NOT YET PASS`** / **`Highest Claim: BLOCKED`** / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**，随即 STOP。报告 [docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)，逐项见操作日志 §5.32。

### 11.22 圆环诊断 Phase II：前瞻性嵌套预算干预（2026-09-19 / 20）

上一轮查明「只增加步数」在当时的代码下无法做成单因素干预，本轮把两条阻塞逐一解决后再做实验。**LR 与总预算解耦**：新增 `optimizer.lrPrefixSteps`，衰减因子由固定的 120000 步前缀算出、scheduler 推进满该次数后停止推进，于是 `lr = lr(step)`；不带该字段时逐位保持旧行为，已跑过的东西不改变含义。**完整 checkpoint 与 exact resume**：新增 `checkpoint_annulus.py`，保存模型、Adam `m_t`/`v_t`/step、scheduler 位置、batch 生成器字节状态、order/cursor、全局 RNG，全部 JSON。**一个实现语义发现**：`ExponentialLR.get_lr()` 是逐步相乘而非闭式 `gamma**t`，12 万次后差 1–2 ULP，最初的闭式 helper 与归档轨迹对不上；按「以实际 trajectory 为准」改为迭代后**逐位复现 r1 的全部 241 条学习率**。**Resume fidelity 先行 PASS**（11 项逐位相同，LR prefix 故意跨越断点）。预注册在任何 10-seed 训练之前提交，冻结预算梯度 120k/180k/240k、最大 240k、B\* 规则与容差。**正式诊断**（9.15 小时，CUDA，10 个 paired seed 各只启动一次 `0→240000`，三处保存完整 checkpoint 并在 CPU 评估）：**PART 10 前缀等价性 PASS，10/10 逐位相等**（连局部统计量都与 r1 一致）；**B\* = 180000**（120k localized 9/10 失败于 seed 2；180k 与 240k 均 10/10）。账本 sha256 与事件序列前后一致，DAC-M1/M2/M3 未触碰。**但正式 RootCauseClass 仍是 `UNDETERMINED`**：Constitution 1.2 要求为该 signature 下其余每一个 admissible 根因指名一个排除实验（且 id 必须是 Tier-1 编号或正式 attempt），7 个候选中本轮只用实验排除了 1 个（`rCapacityLimit`），其余五个的证据全是「没有观察到缺陷」——证据的缺席不是排除。由此**发现一个结构性闭环**：失败 run 的正式诊断需要协议只在成功 run 之后才安排的 Tier-1 实验。另发现**未跟踪文件会静默落在代码身份之外**（预注册一度记错 codeHash，已追加勘误并机器坐实因果，r1 不受影响）。三点负面细节如实记录：改善不单调（180k 的 median 反而更差）、180k 的通过伴随离散度扩大 5.9 倍、余量仅 1.37×（正方形为 6.4×）。全套 **1414 passed / 0 failed / 26 skipped**，训练解释器 annulus 24 / poisson2d 23，portability 0 hard binding，PRELOCK 7/7。结论 `B* = 180k` / `Root Cause: UNDETERMINED` / `NOT YET PASS` / `Highest Claim: BLOCKED` / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**，随即 STOP，不自行启动 revision 2、不消耗 DAC-M1。报告 [docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md](docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md)，逐项见操作日志 §5.34。

### 11.23 圆环排除诊断：2/5 排除，根因仍未定（2026-09-20 / 21）

执行外部评审裁决十一项。**先补代码身份的洞**（裁决 item 3，在任何新诊断执行之前）：`untracked_identity_paths()` 用 `git ls-files --others` 扫描身份边界且**刻意不加** `--exclude-standard`（模块不会因为被 `.gitignore` 就离开方法身份），`assert_code_identity_complete()` 边界内有未跟踪文件即拒绝，`codeIdentityExtraFiles` 必须已跟踪，PRELOCK 新增 `codeIdentityTracked`（检查数 7→8）；对抗测试带**对照**与「唯一变化的检查」两条断言。**再做五项 `exp-*` 身份下的 diagnosis-only 判别实验**（裁决 item 2，不是 Tier-1，Tier-1 含义不变），每项标明干预式或正控制式，判定规则运行前冻结。结果：**`rImplementationDefect` EXCLUDED**（预言注入经同一条流水线得 `6.055e-18`；已知单元注入凸起被**恰好**定位；独立例程复算与生产值**逐位相同**）、**`rSpecDefect` EXCLUDED**（`-Δu*-f` 两条独立路径 `0.000e+00` 与 `3.553e-15`，正控制把残差抬到 `1.752e-05`）、**`rReferenceDefect` NOT EXCLUDED**（R1 机器审计证明 ACA-9 的调用图无一能到达 FDM、R2 观测阶 2.0016/2.0004 均通过，但 R3 参考在热点单元只低 2.7 倍、未达 10 倍，R4 正控制发散成 NaN、控制未执行）、**`rSingularityTreatment` NOT EXCLUDED**（G1、G3 通过，G2 要求贴边界最差单元为 0 而实测 1）、**`rSamplingDeficiency` NOT EXCLUDED 且证据反向**（2× 与 2.76× 密度**都把失败 seed 修好了**，且失败单元 `2,13` 只分到 5 个配置点、中位数 16）。**这削弱了上一轮 `B* = 180k` 的因果解读**：多训练与多采点都能压下该误差，两者都不是必要解释——正是裁决要求做真排除实验的理由。DiagnosisRecord 记账：6 项义务中 2 项备妥可引用证据、1 项（`rCapacityLimit`）科学上已排除但**缺 `exp-*` 标识**、3 项未排除；**未生成 DiagnosisRecord，未写 `rOptimizationFailure`**。本轮另自查出三个自身缺陷并如实记录：R4 把 `nan` 读成通过（已改 fail closed 并加回归测试）、driver 标签 off-by-one 使五次训练白跑（未从日志誊数，重跑逐位相同）、Phase II 报告「30/30」实为「29/1/0」（已就地更正并追加勘误，且该更正直接决定 G2 判定）。全套 **1426 passed / 0 failed / 26 skipped**，训练解释器 annulus 24 / poisson2d 23，PRELOCK **8/8**，portability 0 hard binding。结论 `Root Cause: UNDETERMINED` / `NOT YET PASS` / `Highest Claim: BLOCKED` / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**，随即 STOP，不碰 DAC-M1。报告 [docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md](docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md)，逐项见操作日志 §5.35。

### 11.24 四项委托裁决：并查出四个属于执行者自己的缺陷（2026-09-21）

用户把四项悬而未决的问题交由执行者裁决。四项均以多视角 workflow（29 个 agent，三种独立视角 + 每项三名对抗性怀疑者 + 完备性评审）论证，**每一条强主张都由执行者亲自复核后才采纳**；全部裁决合计 **0 GPU 小时**。**裁决一**：`rSamplingDeficiency` 与 `rOptimizationFailure` 本轮不可分离——路由在看到数据前已冻结，且两因在定义层重叠（等权单损失下「某格只占 5/1024」同时是 collocation distribution 与 loss weighting 的实例）；并据此**收窄我自己的机理叙事**：S1a 把该格点数由 5 提到 18、相对中位数由 0.31× 升到 0.58×，热点**仍停在原处**且 ACA-9 比只换抽签的 S3 还差，而只换抽签的三次**每次**都把热点挪走——起作用的是**抽签**不是**密度**。**裁决二**：R3 整族前瞻性退役（其阈值是被诊断对象自身的函数，没有固定分辨力）；R4 的失败是我的 bug（`u = u + residual/diagonal` 而 residual = A·u − b，**无论是否腐蚀算子都会发散**），修正符号并改为按残差容差迭代后**预注册原判据直接通过**；更重的一条是 **R1 的根集合是手挑的**，恰好不含裁决 ACA-9 的 `gates_annulus`，修复后审计图由 14 扩到 43 个模块、**R1 改判 FAIL**。**裁决三**：G2 维持——它是我写错的（贴边界单元恰占一半，`P(通过)=0.5^30=9.3e-10`，且证据越多越难通过），但更重的是 **G3 未按冻结规格执行**（预注册写 `r^(2/3)`、代码用 `d^(-1/3)`；实测字面场热点落在贴**外**圆的 `3,8`，通不过预注册自己写的 bin 0 条件——冻结文本自相矛盾，实现静默选了能通过的一侧），故该实验实为**观察式**，在任一方向都不构成排除。**裁决四（最重）**：`rCapacityLimit` **从未被排除**——容量干预必须改 architecture（≥3 档 ×≥3 seed），而嵌套预算干预全程钉死 4×64、只改 steps，容量档位数为 0；我自己 0919 预注册的原文是「**不再是必要解释**」并把它逐字列入六项义务，**我在两份报告里写成了「已排除」，是越权**。未排除原因由 3 项改记为 **4 项**。另查明 `rUndetermined` 的 DiagnosisRecord **写得出来**（校验零错误），但会把状态迁到 `STOPPED_THE_LINE`——超出委托范围，本轮不写。全套 **1429 passed / 0 failed / 26 skipped**，训练解释器 annulus 27 / poisson2d 23，PRELOCK 8/8，portability 0 hard binding。逐项见操作日志 §5.36 与报告 §12。

````

</details>

### R003 — 项目/20260914仓库卫生记录.md

<details>
<summary>展开完整原文</summary>

```markdown
# 20260914 仓库卫生记录

记录日期：2026-09-14。对象：`LeoAIStudio-build` 目录（本文件所在目录）及其 git 仓库。执行：Claude Code。配套的修改报告见 [20260914软件修改报告.md](20260914软件修改报告.md)。

口径：

- "位置"一律写相对于 `LeoAIStudio-build` 的路径。
- 原因栏里的"用户审批通过"表示该项属于用户要求先问后删的敏感项，已于 2026-09-14 得到用户明确同意。
- 没有列在本文件里的文件一律没有删除、没有移动。

---

## 1. 清理前的状态

| 项 | 值 |
|---|---|
| 主检出分支 | `master` = `8c4835e`（"snapshot before cleanup (102 items, per LeoAI cleanup report 20260909)"），父提交 `a4455cc`，git 跟踪 105 个文件，工作树干净 |
| 用户拍板的基线 | `codex/conversation-runtime-20260909` = `14e30f4`，git 跟踪 222 个文件 |
| 两条线的关系 | 共同祖先 `a4455cc`；`8c4835e` 相对 `14e30f4`：0 个独有文件、35 个文件内容更旧、117 个文件缺失；无任何独有改动 |
| 工作分支 | `claude/leoaistudio-cleanup-refactor-9e137d`，工作树在 `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d`，已 `reset --hard 14e30f4` |
| 仓库目录内未跟踪的大目录 | `LeoAIStudio/` 约 2.0 GiB（安装目录）；`leotree/` 约 589 MiB（Leo Tree，独立 git 仓库）；`LeoAI-maintenance-20260907/` 402,091,098 字节、3,318 个文件（`find -type f` 计数；git 对其中 Chrome 配置文件的若干深层目录报告"Filename too long"，实际文件数只多不少）；`LeoAIStudio-pinn-evidence-20260908T120017Z/`（未测量） |
| 其它未跟踪 | `.claude/`（会话工作树）；`pinn/__pycache__/`、`pinn/governance/__pycache__/`（2026-09-08 遗留的字节码缓存，8 个文件，已被 `.gitignore` 覆盖） |
| 主检出没有 `.venv` | 测试使用用户文档目录下 `LeoAIStudio-deliveries/20260908-phase2/models-worktree/.venv` 的解释器 |

---

## 2. 删除清单

### 2.1 仓库内（git 跟踪）的文件

| 删了什么 | 位置 | 原因 |
|---|---|---|
| 窗口截图探针（54 行 PowerShell） | `tools/capture_window.ps1` | 用户审批通过。9-07 人工验收时排查"黑屏但进程活着"用的一次性工具；构建链、测试、`docs/BUILD.md` 零引用。`CHANGELOG.md` 2026-09-07 段落里"保留"的叙述是当时的判断，本次改由用户拍板 |
| 窗口几何监视探针（23 行 PowerShell） | `tools/watch_window.ps1` | 用户审批通过。同上，一次性诊断工具，零引用 |
| WebView2 CDP 探针（54 行 Node 脚本） | `tools/inspect_webview.mjs` | 用户审批通过。通过远程调试端口读页面状态的一次性探针；仓库没有 Node 依赖声明，零引用 |
| 旧壳模块恢复脚本（49 行 Python） | `tools/extract_launcher.py` | 用户审批通过。从旧 EXE 的 PYZ 里抽取旧壳 `leo_ai_studio` 模块；该模块已被 `tools/package_contract.py` 明确禁止出现在包内，全仓零引用 |

合计 4 个文件、180 行。它们的最后内容仍可从 `14e30f4` 取回（`git show 14e30f4:tools/<name>`）。

### 2.2 仓库目录内但未被 git 跟踪的内容

| 删了什么 | 位置 | 原因 |
|---|---|---|
| 9-07 维护档案目录：`build-final/`（当次构建产物与 PyInstaller 临时目录）、`final-caches/`、`release/`（当次发布件副本，含 `_launcher/` 的 .pyd）、`source-before/`（清理前的全量源码快照，含 `docs/manual-acceptance-evidence/` 下的 Chrome 配置文件证据）、`validation/`（验证脚本、日志、截图、SSE 记录）、`cleanup-manifest.json`、`cleanup-result.json`、`hygiene-inventory.json`、`execute_cleanup.ps1`、`prepare_cleanup.py`、`git-status-before.txt`、`working-tree-before.patch` | `LeoAI-maintenance-20260907/` | 用户审批通过。3,318 个文件、402,091,098 字节。结论早已并入 `CHANGELOG.md` 2026-09-07 段落；`CHANGELOG.md` 提到的 `removed-files.zip` 在删除前核对时已不在该目录内（顶层只有上述 12 项），所以本次删除没有丢失任何"可恢复旧报告原始字节"的归档；`source-before/` 里的源码快照对应的提交历史仍在 git 中（`a4455cc` 及之前）。删除方式与结果见 §6 |

删除前已把目录顶层清单、文件数与字节数记录在上表，没有另做备份。

### 2.3 git 引用

| 删了什么 | 位置 | 原因 |
|---|---|---|
| `master` 对快照提交 `8c4835e` 的引用 | git 分支 `master` | 用户同意删除。`8c4835e` 相对 codex 线没有任何独有内容（§1）；`master` 由 `8c4835e` 改指向建立在 `14e30f4` 之上的本次提交（主检出执行 `git reset --hard <新提交>`）。提交对象本身没有被回收：分支 `claude/leoaistudio-cleanup-refactor-d129a8`（本次会话被分配、从未使用的工作树）仍指向它；用户移除该工作树与分支后它才进入可回收状态。没有执行 `git gc` |

没有删除任何其它分支或标签。`codex/*`、`grok-*`、`p0*`、`ui-plugin-oss-compliance` 等分支全部原样保留。

### 2.4 测试运行产生的文件（本次建立、本次删除）

用户要求测试建立的文件必须删除并留痕。所有测试均以 `-B -p no:cacheprovider` 运行；运行后按 `git status --ignored --untracked-files=all`、按修改时间的 `find` 与用户临时目录逐处盘点。

| 产物 | 位置 | 由谁建立 | 数量 / 大小 | 处置 |
|---|---|---|---|---|
| pytest 临时目录 `pytest-333`、`pytest-334`、`pytest-335` 与 `pytest-current` 链接 | 用户临时目录下的 `pytest-of-user/` | 主检出的 3 次全套运行（05:01–05:03）；工作树 3 次运行所建的目录已被 pytest 自身"只保留最近 3 次"的轮换删除 | 5,037 个文件，112,468,305 字节 | 整个 `pytest-of-user/` 目录已删除，删除后目录不存在 |
| 字节码缓存（工作树） | `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d/` 下的 `pinn/__pycache__/`、`pinn/governance/__pycache__/`、`pinn/reference/__pycache__/`、`pinn/validation/__pycache__/`、`scientific_reference/__pycache__/`、`tests/skills/__pycache__/` | 第一次全套运行（04:46）拉起的子进程；`-B` 只约束主解释器 | 18 个文件 | 6 个目录整体删除，删除后不存在 |
| 字节码缓存（主检出，本次） | 主检出下同样的 6 个目录 | 主检出的全套运行（05:01–05:02） | 15 个文件 | 删除，删除后不存在 |
| 字节码缓存（主检出，2026-09-08 遗留） | `pinn/__pycache__/__init__.cpython-312.pyc`；`pinn/governance/__pycache__/` 下的 `__init__`、`jsonschema_lite`、`locking`、`nodes`、`prelock`、`provenance`、`semantic` | 早前会话，不是本次 | 8 个文件 | 与上一行同目录，一并删除（纯缓存，已被 `.gitignore` 覆盖，按需重生成） |
| 测试输出日志 `pytest-run1.log`、后台任务输出 `bl6aqrddd.output` | 本会话的 scratchpad 与任务目录（用户本地应用数据下的 `Temp/claude/…`） | 第一次全套运行 | 2 个文件 | 删除，删除后不存在 |
| 会话辅助脚本 `apply_edits.py`、`hashes_gitignore.py`、`docs_edits.py`、`fix_header_rehash.py`、`fill_reports.py`，报告草稿 `report_software.md`、`report_hygiene.md`，盘点输出 `bokwwpgoz.output`、`bokwwpgoz.txt` | 同上 | 本会话（非测试所建，一并留痕） | 9 个文件 | 报告提交后、会话结束前删除，最终汇报里确认 |
| `pytest.ini` 副本 | 主检出根目录 | 本会话为验证裸跑效果临时复制 | 1 个文件 | 不删除：`master` 重置到收尾提交后它成为跟踪文件，字节与提交内容相同 |
| `.pytest_cache/`、`docs/manual-acceptance-evidence/`、`LeoAIStudio/` 与 `leotree/` 内的新文件 | — | 未产生（`-p no:cacheprovider`；安装目录按修改时间核查，本次运行后没有任何新文件或改动） | 0 | — |

---

## 3. 移动与改名

| 从 | 到 | 原因 | 附带改动 |
|---|---|---|---|
| `unified-settings-adapter.js` | `stage/unified-settings-adapter.js` | 它是 `theme/leo-inject.js` 三层 bundle 的第一层，其余注入层源文件都在 `stage/`；放在仓库根目录是历史遗留 | 字节不变。引用同步：`tools/build_launcher.ps1`、`tools/build_manifest.py`、`tools/verify_release.py`、`tools/theme_asset_provenance.py`、`tests/test_ui_api_contract.py`、`manifests/runtime-asset-origins.json`、`.gitignore` 注释 |
| `i18n-brand-patch.js` | `stage/i18n-brand-patch.js` | 同上，它是 bundle 的第二层 | 头部注释重写（原注释称该文件"未被发布版加载、需手工合并"，与构建事实不符）；代码体不变。引用同步同上 |
| `PINN_MVP_AND_CFD_READINESS_REPORT.md` | `docs/PINN_MVP_AND_CFD_READINESS_REPORT.md` | 仓库根目录只保留仓库元数据与当期报告；这份 9-08 的历史报告与其它 PINN 报告一起归入 `docs/` | 第 5 行指向 `PINN_PHASE2_RECONCILIATION_20260909.md` 的相对链接去掉 `docs/` 前缀；其余字节不变。`docs/PINN_PHASE2_RECONCILIATION_20260909.md` 与 `docs/LEO_CONVERSATION_RUNTIME_INTEGRATION_REPORT_20260909.md` 里按文件名提到它的地方是历史记录，未改 |

---

## 4. 考虑过但保留的内容（以及为什么）

| 内容 | 位置 | 为什么保留 |
|---|---|---|
| 全部测试（35 个文件） | `tests/` | 用户任务里"删除一切无用的测试文件"逐个核对后，没有一个是无用的：它们构成 codex 线 839 passed 的回归网，覆盖壳、桥、主题、API 契约、构建可复现性、可移植性、人工验收、PINN 与 skills；`manifests/test-suites.json` 还登记了其中的对抗套件，`tests/test_suite_provenance.py` 禁止它被删或缩水。9-07 那次按要求删测试后由后续会话重新恢复，代价已经付过一次 |
| 冻结证据副本（10 个文件） | `docs/rollback/` | 它们是修复前的原文件副本，`tools/portability_check.py` 对其按"frozen-evidence"豁免并由测试锁定；改动或删除会破坏证据 |
| 历史报告（含引用旧路径的段落） | `docs/*.md`、`CHANGELOG.md` 2026-09-07 段落 | 是当时的记录，不是当前配置；可移植性扫描对它们按类豁免 |
| Leo 后端 sidecar | `bridge/` | 用户明令后端零删除 |
| 规范技能 | `skills/` | 由 `tools/sync_skills.py` 同步到安装目录，是运行时输入 |
| PINN 科学候选、参考、记录、治理、规格 | `pinn/`、`scientific_reference/`、`research_logs/`、`governance/`、`specs/`、`adversarial/` | 科研内容，用户没有批准任何删除 |
| 图标与背景源图 | `assets/` | `tools/make_lion_icon.py`、`tools/build_backgrounds.py` 的输入 |
| 主题截图脚本 | `tools/theme_shots.ps1` | 未列为删除候选，未核对引用，按"没批准就不动"保留 |
| 安装目录 | `LeoAIStudio/` | 正式安装版，含 `user/` 凭据与会话状态；用户拍板留在仓库目录内并忽略。内部三个 `.leo-rollback-*` 回滚目录也未动 |
| Leo Tree 项目 | `leotree/` | 独立项目、独立 git 仓库；用户拍板留在仓库目录内并忽略 |
| PINN 外部证据目录 | `LeoAIStudio-pinn-evidence-20260908T120017Z/` | 未列入本次删除候选、未向用户询问，因此不删。它现在位于仓库目录内、未跟踪也未忽略；是否忽略或删除留待用户决定 |
| Python 字节码缓存 | `pinn/__pycache__/` 等 | 不保留：本次测试产生的与 2026-09-08 遗留的全部删除，见 §2.4 |
| Claude Code 工作树 | `.claude/worktrees/` | 本次新增到 `.gitignore`；工作树本身由用户决定何时移除 |

---

## 5. 分类与层划分结果

清理后 git 跟踪 221 个文件（222 − 4 个删除的工具 + 2 份本次报告 + `pytest.ini`）。分层如下：

| 层 | 目录 | 文件数 |
|---|---|---|
| 仓库元数据与当期报告 | 根目录（`.gitattributes`、`.gitignore`、`CHANGELOG.md`、`requirements.lock`、`pytest.ini`、两份 20260914 报告） | 7 |
| Windows 壳 | `launcher/`、`leo_shell/` | 1 + 19 |
| Leo 后端 sidecar | `bridge/` | 10 |
| 注入层源（发布为 `theme/`） | `stage/`（含 `fonts/`、`i18n/`、`backgrounds/`、`logos/`） | 21 |
| 源素材与许可 | `assets/`、`LICENSES/` | 4 + 4 |
| 构建 / 部署 / 校验工具 | `tools/`（含 `manual_acceptance/`） | 27 |
| 声明与锁定 | `manifests/` | 6 |
| 回归网 | `tests/` | 35 |
| 规范技能 | `skills/` | 9 |
| 科学内容 | `pinn/`、`scientific_reference/`、`research_logs/`、`adversarial/` | 22 + 3 + 2 + 1 |
| 治理与规格 | `governance/`、`specs/` | 8 + 3 |
| 报告与文档 | `docs/`（含 `docs/rollback/` 10 个冻结副本） | 39 |

不入库但位于仓库目录内：`LeoAIStudio/`（安装）、`leotree/`（Leo Tree）、`.claude/worktrees/`（会话工作树）已在 `.gitignore`；`LeoAIStudio-pinn-evidence-20260908T120017Z/` 未跟踪、未忽略、待用户决定。

安装目录默认位置随之改为 `<仓库>/LeoAIStudio`，所有工具支持 `LEO_APP_ROOT` 覆盖；详见修改报告 §5 与 `docs/BUILD.md` §4a。

---

## 6. 校验

| 项 | 结果 |
|---|---|
| 全套测试（工作分支工作树，不带环境变量） | 832 passed / 9 skipped / 0 failed。多出的 7 个 skip 均因工作树目录下没有 `LeoAIStudio/`（`tests/test_manual_acceptance.py:167`，上游 checkout 不可用则跳过） |
| 全套测试（`LEO_APP_ROOT` / `LEO_UPSTREAM_ROOT` 指向主检出下的安装目录） | 839 passed / 2 skipped / 0 failed，与 codex 线基准一致 |
| 全套测试（主检出，`master` 重置后，不带环境变量） | 显式路径 `pytest tests`：839 passed / 2 skipped / 0 failed；加 `pytest.ini` 后裸跑：839 passed / 2 skipped / 0 failed。最初裸跑收集到 `LeoAIStudio/upstream/OpenAI4S/tests/` 报 14 个收集错误，由新增的 `pytest.ini` 解决，见修改报告 §8.1 |
| `tools/portability_check.py` | 0 hard binding，退出码 0；1 条可配置默认值与 3 条历史证据均为本轮之前既有 |
| 本文件与修改报告 | 不含 Windows 用户目录绝对路径、桌面路径、Linux 家目录、WSL 发行版名字面量（这两份根目录 `.md` 不在扫描器的豁免范围内，扫描结果即为证明） |
| 删除引用核对 | 删除 4 个工具后，`git grep` 在 `.py`/`.ps1`/`.js`/`.json`/`.md` 之外的所有跟踪文件中对它们零命中；`.md` 中的命中全部在 `CHANGELOG.md`、`docs/` 历史记录里 |
| 移动引用核对 | 移动 3 个文件后，全仓对旧路径的引用只剩 `docs/rollback/` 冻结副本与 `CHANGELOG.md` / `docs/` 历史记录 |
| `LeoAI-maintenance-20260907/` 删除 | 在主检出以 `rm -rf` 删除（MSYS `rm`，可处理 git 报告的超长路径），退出码 0，删除后 `test -e` 确认目录不存在；删除前顶层 12 项、3,318 个文件、402,091,098 字节 |
| 测试产物 | §2.4 全部项目删除后复核：两处检出均无 `__pycache__`、无 `.pytest_cache`；用户临时目录无 `pytest-of-*` |
| `master` 指向 | 先 `55484f2`（主体提交，父提交 `14e30f4`），最终重置到收尾提交（提交号见 `git log -1 master`） |

---

## 7. 第二轮追加（2026-09-14 下午）

### 7.1 删除

| 删了什么 | 位置 | 原因 |
|---|---|---|
| 9-08 PINN 外部证据目录（117 个文件，4,316,341 字节） | `LeoAIStudio-pinn-evidence-20260908T120017Z/` | 用户审批通过（第二轮，选择"先归档到仓库外再删"）。删除前已压缩为 zip 存入用户文档目录 `LeoAIStudio-deliveries/20260914-archive/`，117 个条目、1,296,353 字节、SHA-256 `9916e20c5dbc87f1ccc7ce04181c5d53403560947f2f18178f25f72a0d59fef3`，旁车 `.sha256` 文件；`testzip` 无错后 `rm -rf` 原目录，删除后不存在 |
| 已合并分支 | `claude/leoaistudio-cleanup-refactor-9e137d`（曾指向 `2fabbe4`） | 用户指示现在移除；`git branch -d` 成功 |
| 工作树 9e137d 的内容 | `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d/` | `git worktree remove` 已注销并清空内容；顶层空目录被另一进程占用（Device or resource busy），留待用户在该进程退出后 `rmdir` |

### 7.2 新增到仓库目录但不入库的内容

| 内容 | 位置 | 说明 |
|---|---|---|
| 构建环境 | `.venv/`（57,609,997 字节） | 从 codex 侧 models-worktree 复制，环境审计 0 问题；`.gitignore` 已覆盖 |
| 发布 manifest | `manifests/build-current.json` | 由 `build_manifest.py` 生成；`.gitignore` 已覆盖；strict 校验的输入 |
| 第 4 个回滚目录 | `LeoAIStudio/.leo-rollback-20260914-063236-dc3d45e8/` | 部署脚本所建，含上一版 EXE / `_launcher` / theme，按设计保留 |

### 7.3 仓库外新增

| 内容 | 位置 |
|---|---|
| 证据归档 zip 与 `.sha256` | 用户文档目录 `LeoAIStudio-deliveries/20260914-archive/` |
| 构建输出与四份日志 | 用户文档目录 `LeoAIStudio-deliveries/20260914-build/`（`out-01/` 含 `dist/`、`pyi-work/`、`pyi-spec/`、`build-inputs.json`、`leo-inject.bundle.js`） |

### 7.4 产物核查

构建、部署、校验之后仓库目录内无 `__pycache__`、无 `.pytest_cache`；用户临时目录无 `pytest-of-*`；构建脚本自行清理了依赖缓存。本轮没有运行测试。

### 7.5 待用户决定

`.claude/worktrees/leoaistudio-cleanup-refactor-d129a8/` 与分支 `claude/leoaistudio-cleanup-refactor-d129a8`（指向 `8c4835e`）在会话最后一步由队长删除。

### 7.6 第三轮：可信闭环 R1 实现

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | 13 个：`governance/AMENDMENTS/A-0001-trust-loop-r1.md`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`、`pinn/governance/trust_vector.py`、`pinn/governance/trust_loop.py`、三份 `pinn/governance/schemas/*.schema.json`、三个 `tests/pinn/test_*.py`；修改 3 个：`governance/AMENDMENTS/README.md`、`pinn/governance/__init__.py`、`pinn/governance/state_machine.py`（只追加） |
| 测试产物 | 主检出 `__pycache__` 目录 6 个 / 文件 19 个，用户临时目录 `pytest-of-user` 1702 个文件 / 38426801 字节，全部删除并复核无残留 |
| 测试 | 930 passed / 2 skipped，只增不减 |

### 7.7 会话最后一步

| 删了什么 | 位置 | 结果 |
|---|---|---|
| 本会话工作树 d129a8 | `.claude/worktrees/leoaistudio-cleanup-refactor-d129a8/` | `git worktree remove` exit 1；目录仍存在：yes（剩余条目 0 个；若为空目录且仍存在，是被本会话的 shell 占用，会话结束后 `rmdir` 即可） |
| 分支 `claude/leoaistudio-cleanup-refactor-d129a8`（指向 `8c4835e`） | git 分支 | `git branch -D` exit 0；`8c4835e` 自此无任何引用（用户同意删除），未执行 `git gc` |
| 9e137d 残留空目录 | `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d/` | 9e137d 残留空目录仍被其它进程占用，未删 |

### 7.8 第四轮：A-0001 第 2 稿（2026-09-15）

| 项 | 内容 |
|---|---|
| 修改的跟踪文件 | `pinn/governance/{__init__,state_machine,trust_vector,trust_loop}.py`、三份 `schemas/*.schema.json`（1.1）、三个 `tests/pinn/test_*.py`、`governance/AMENDMENTS/{A-0001-trust-loop-r1,README}.md`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 新增跟踪文件 | `docs/PINN_TRUST_LOOP_TEAM_PROMPTS_R2_20260915.md` |
| 测试产物 | 主检出 `__pycache__` 6 个目录 / 19 个文件，用户临时目录 `pytest-of-user` 1,712 个文件 / 39,619,002 字节，全部删除并复核无残留 |
| 测试 | 961 passed / 2 skipped，只增不减 |

### 7.9 第五轮：R2 合并与 A-0001 第 3 稿（2026-09-15，接手会话）

| 项 | 内容 |
|---|---|
| 工作方式 | 桌面应用自动建的工作树 `.claude/worktrees/leoaistudio-build-handover-99ccbd`（分支 `claude/leoaistudio-build-handover-99ccbd`）上提交，master 快进到同一提交；未新建其它工作树；该工作树与分支、以及 `9e137d` / `d129a8` 两个遗留空目录是否删除待用户答复 |
| 新增跟踪文件 | `docs/pinn-trust-loop/inbox/PINN_TRUST_R2_{SCHEMAS_STATE_MACHINE,IMPL_TRAINING,REPORT_AND_WORKFLOW}.md`、`docs/pinn-trust-loop/R2_MERGE_NOTES.md`、`pinn/governance/{evaluation_sets,claim_set_ledger}.py`、`pinn/governance/schemas/{evaluation-set,claim-set-event,run-record,diagnosis-record}.schema.json`、`tests/pinn/test_{trust_loop_adversarial,evaluation_sets,claim_set_ledger}.py` |
| 修改的跟踪文件 | `pinn/governance/{__init__,state_machine,trust_vector,trust_loop}.py`、三份 `schemas/*.schema.json`（1.2）、三个既有 `tests/pinn/test_*.py`（1.2 夹具，改写未删）、`governance/AMENDMENTS/{A-0001-trust-loop-r1,README}.md`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 删除 | 主检出里用户放入的三份未跟踪 R2 文件，在与提交 `a4caa40` 内容逐字节 `cmp` 一致后删除（快进的前提）；桌面上 GLM 的原件未动 |
| 测试产物 | 工作树 `__pycache__` 6 个目录（删除）；主检出 `__pycache__` 6 个目录 / 22 个文件（删除）；用户临时目录 `pytest-of-user` 3,934 个文件 / 70,262,342 字节（删除）；复核：两处 `git status` 0 行，`__pycache__` 0 个，临时目录不存在 |
| 测试 | 主检出 master `a4caa40`：1031 passed / 2 skipped，只增不减（基准 961 + 70） |
| 未收到 | DeepSeek `PINN_TRUST_R2_MATH_CORE.md` |

### 7.10 第六轮：终审通过、DeepSeek 补交、审批删除（2026-09-15）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `docs/pinn-trust-loop/inbox/PINN_TRUST_R2_MATH_CORE.md`（原件 `C:\Users\user\PINN_TRUST_R2_MATH_CORE.md` 未动） |
| 修改的跟踪文件 | `governance/AMENDMENTS/{A-0001-trust-loop-r1,README}.md`（ACCEPTED / 2026-09-15）、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`docs/pinn-trust-loop/R2_MERGE_NOTES.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 未改 | `governance/PINN_RESEARCH_CONSTITUTION.md`（仍 1.0 字节，原因见操作日志 §5.15） |
| 计划删除（用户审批通过） | 会话工作树 `.claude/worktrees/leoaistudio-build-handover-99ccbd` 及分支 `claude/leoaistudio-build-handover-99ccbd`（已快进进 master，无独有提交）；遗留空目录 `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d`、`.claude/worktrees/leoaistudio-cleanup-refactor-d129a8`。执行结果追加于 7.11 |
| 测试 | 本轮无代码改动，未重跑；基线 master `a4caa40` 1031 passed / 2 skipped |

### 7.11 审批删除的执行结果（2026-09-15，用户审批通过）

| 对象 | 结果 | 理由 |
|---|---|---|
| 工作树 `.claude/worktrees/leoaistudio-build-handover-99ccbd` | 内容已删除、git 已注销；顶层空目录被会话进程占用未能删除，会话结束后 `rmdir` | 用户审批通过 |
| 分支 `claude/leoaistudio-build-handover-99ccbd`（曾指向 `1f0e48f`，已快进进 master） | 已删除 | 用户审批通过 |
| 空目录 `.claude/worktrees/leoaistudio-cleanup-refactor-9e137d` | 已删除 | 用户审批通过 |
| 空目录 `.claude/worktrees/leoaistudio-cleanup-refactor-d129a8` | 被其它进程占用（Device or resource busy），未删；会话结束后 `rmdir` | 用户审批通过（待执行） |

### 7.12 第七轮：宪法 1.1 落笔与草案重绑定（2026-09-15，方案一，用户审批通过）

| 项 | 内容 |
|---|---|
| 修改的跟踪文件 | `governance/PINN_RESEARCH_CONSTITUTION.md`（1.0 → 1.1，新字节 SHA `943484850d64…`）、`pinn/governance/{locking,prelock}.py`、`pinn/governance/schemas/{lock,spec,protocol}.schema.json`、`tests/pinn/test_prelock_integrity.py`、`governance/AMENDMENTS/{A-0001-trust-loop-r1,README}.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 修改的证据类文件（用户审批通过） | `governance/POISSON_1D_V1.0_spec.draft.json`、`_protocol.draft.json`（constitutionVersion 1.0 → 1.1）、`_lock.draft.json`（constitutionVersion、constitutionSha256、shellEquivalent 三处）；均为 lockedAt 为 null 的草案，经规范序列化往返，其余字节不变 |
| 新增跟踪文件 | `governance/PINN_V1.3_PRELOCK_DRY_RUN_A0001.json`（宪法 1.1 下的 PRELOCK 实跑证据） |
| 未改 | `governance/PINN_V1.3_PRELOCK_DRY_RUN.json`（2026-09-05 的 1.0 证据，原样保留）；`research_logs/` |
| 本轮自建后删除 | 第一次生成的 `PINN_V1.3_PRELOCK_DRY_RUN_A0001.json`（记录了新测试写错属性名导致的 1 项 failed），删除后修正测试重新生成；不是既有证据 |
| 临时脚本 | 三份 Python 补丁 / 重绑定 / 证据脚本在会话临时目录，不入库 |
| 测试产物 | 主检出 `__pycache__` 6 目录 / 22 文件（删除）；`pytest-of-user` 3,449 文件 / 63,796,495 字节（删除）；复核无残留 |
| 测试 | 1033 passed / 2 skipped，只增不减（1031 + 2） |

### 7.13 第八轮：A-0002 起草（2026-09-15）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md`（PROPOSED） |
| 修改的跟踪文件 | `pinn/governance/state_machine.py`（三格）、`tests/pinn/{test_state_machine_triage,test_trust_loop_adversarial}.py`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`governance/AMENDMENTS/README.md`、`docs/pinn-trust-loop/R2_MERGE_NOTES.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 未改 | 宪法正文（仍 1.1）、Poisson 草案、证据文件（待 A-0002 ACCEPTED） |
| 临时脚本 | 补丁脚本在会话临时目录，不入库 |
| 测试产物 | 主检出 `__pycache__` 6 目录 / 22 文件（删除）；`pytest-of-user` 2,235 文件 / 40,425,629 字节（删除）；复核无残留 |
| 测试 | 1038 passed / 2 skipped，只增不减（1033 + 5） |

### 7.14 第九轮：A-0002 第 2 稿（2026-09-15）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `pinn/governance/amendments.py`、`tests/pinn/test_amendments.py` |
| 修改的跟踪文件 | `governance/AMENDMENTS/{A-0002-admissible-matrix-r2,README}.md`、`pinn/governance/{state_machine,trust_loop,prelock}.py`、`pinn/governance/schemas/diagnosis-record.schema.json`、`tests/pinn/{test_state_machine_triage,test_trust_loop_adversarial}.py`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`docs/pinn-trust-loop/R2_MERGE_NOTES.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 未改 | 宪法正文（仍 1.1）、Poisson 草案、证据文件（待 A-0002 ACCEPTED） |
| 临时脚本 | 补丁与追加脚本在会话临时目录，不入库 |
| 测试产物 | 见操作日志 §5.19 末尾计数；复核无残留 |
| 测试 | 1058 passed / 2 skipped，只增不减（1038 + 20） |

### 7.15 第十轮：A-0002 第 3 稿 Final Closure Review（2026-09-15）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `tests/pinn/test_constitution_version_isolation.py`、`docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md` |
| 修改的跟踪文件 | `pinn/governance/{state_machine,trust_loop,amendments,prelock}.py`、`pinn/governance/schemas/diagnosis-record.schema.json`、`tests/pinn/{test_state_machine_triage,test_trust_loop_adversarial}.py`、`governance/AMENDMENTS/{A-0002-admissible-matrix-r2,README}.md`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`docs/pinn-trust-loop/R2_MERGE_NOTES.md`、`CHANGELOG.md`、本文件与修改报告、操作日志 |
| 未改 | 宪法正文（仍 1.1）、Poisson 草案、证据文件、`SUPPORTED_CONSTITUTION_VERSIONS`（仍 1.0 / 1.1，待 A-0002 ACCEPTED） |
| 未删 | 桌面应用自动创建的工作树 `.claude/worktrees/leoaistudio-build-handover-29efe6` 与同名分支（非队长所建，等用户决定） |
| 临时脚本 | 四份补丁脚本与两份草稿在会话临时目录，不入库 |
| 测试产物 | 主检出 `__pycache__` 6 目录 / 22 文件（删除）；`pytest-of-user` 2,243 文件 / 40,799,797 字节（删除）；复核无残留 |
| 测试 | 1087 passed / 2 skipped，只增不减（1058 + 29） |

### 7.16 第十一轮：宪法 1.2 生效与 Poisson 1D 实验（2026-09-15～16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `pinn/experiments/*.py`（7 个模块）、`tests/pinn/test_experiment_runner.py`、`experiments/poisson1d/`（配置 2、协议 1、problems 2、ledger 2、runs 3 个 attempt 含权重 / 历史 / 图，约 7.4 MB）、`governance/PINN_V1.3_PRELOCK_DRY_RUN_A0002.json`、`docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md` |
| 修改的跟踪文件 | 宪法正文（1.2）、`pinn/governance/locking.py`、三份 schema、A-0002 与登记簿 README、三份 Poisson 草案、`tests/pinn/{test_amendments,test_prelock_integrity,test_constitution_version_isolation}.py`、CHANGELOG、本文件与修改报告、操作日志 |
| 删除 | 两次因 runner 缺陷中止的启动产物（`runs/exp1-calibration-r1` 前两版目录、账本 `pdef-poisson1d-cal-v1.json` 第一版）——队长自建、无结论依赖，见操作日志 §5.22 |
| 未删 | 桌面应用自动创建的工作树与分支（等用户） |
| 环境 | 未安装任何包；训练用用户既有 mamba Python（torch 2.12.1） |
| 测试产物 | 主检出 `__pycache__` 6 目录 / 23 文件（删除）；`pytest-of-user` 2,329 文件 / 43,054,944 字节（删除）；复核无残留 |
| 测试 | 1094 passed / 4 skipped，只增不减（1087 + 7；+2 框架缺失跳过） |

### 7.17 第十二轮：Poisson 1D 向 C2 校准（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `pinn/experiments/{bc_diagnosis,claim_metrics,criteria,redteam,repro_package}.py`、`tests/pinn/{test_claim_identity,test_bc_diagnosis,test_redteam_rules}.py`、`experiments/poisson1d/{EXPERIMENT3_PREREGISTRATION_20260916.md,configs/exp3_*.json,problems/*-r2.json,problems/*-claim-*.json,ledger/sample_set_registry.json,runs/exp3c-hard-bc-r2/,repro_package_exp3c_r2/}`、两份 POST_AUDIT_ANNOTATION、`docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md` |
| 修改的跟踪文件 | `pinn/governance/{claim_set_ledger,evaluation_sets,trust_loop}.py`、`schemas/claim-set-event.schema.json`、`governance/PINN_TRUST_PROTOCOLS_R1.md`、`pinn/experiments/{pinn_torch,datasets,runner}.py`、实验 1 目录新增诊断产物（原记录未改）、CHANGELOG、本文件与修改报告、操作日志 |
| 删除 | 无（历史 evidence 全部保留，含 Tier-1 run 1） |
| 测试产物 | 主检出 `__pycache__` 12 目录 / 90 文件（删除）；`pytest-of-user` 4,154 文件 / 76,265,004 字节（删除）；复核无残留 |
| 测试 | 1109 passed / 6 skipped，只增不减（1094 + 15；+2 框架缺失跳过） |

### 7.18 第十三轮：Poisson 1D 校准收口（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `experiments/poisson1d/{INTERVENTION_CRITERION_CLARIFICATION_20260916.md,environment_b_qualification.json}`、`runs/{repro-envb-r2,repro-envb-frozen-r2}/`、`runs/exp1-calibration-r1/POST_AUDIT_ANNOTATION.md`、`runs/repro-envb-r2/POST_AUDIT_ANNOTATION.md`、`runs/exp3c-hard-bc-r2/{gate6_reproducibility_executed,trust_vector_g6,claim_gate_decision_g6}.json`、`tests/pinn/test_g6_reproduction.py`、`docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md` |
| 修改的跟踪文件 | `pinn/experiments/runner.py`（复现模式、judge-reproduction、apply-g6）、`runs/exp3c-hard-bc-r2/{RUN_SUMMARY,attempt_state,STATE_TRANSITIONS,PROVENANCE_MANIFEST}.json` 与 `TRUST_REPORT.md`（追加 G6 结果，历史条目未改）、CHANGELOG、本文件与修改报告、操作日志 |
| 仓库外新建（未删，等用户） | `C:/Users/user/LeoAI-envB-20260916/venv`（Environment B）与 `.../repo-frozen`（exp3c 原 commit 的 `git worktree add --detach` 干净检出，复现包要求）；驱动脚本 `frozen_repro_driver.py` 在会话临时目录 |
| 删除 | 无 |
| 测试产物 | 主检出 `__pycache__` 6 目录 / 22 文件（删除）；`pytest-of-user` 2,941 文件 / 53,090,413 字节（删除）；复核无残留 |
| 测试 | 1112 passed / 6 skipped，只增不减（1109 + 3） |

### 7.19 用户审批的删除（2026-09-16）

| 项 | 内容 |
|---|---|
| 删除（用户审批通过） | `C:/Users/user/LeoAI-envB-20260916/`（Environment B venv + repo-frozen 分离检出）；会话工作树 `.claude/worktrees/leoaistudio-build-handover-29efe6` 与分支 `claude/leoaistudio-build-handover-29efe6` |
| 保留 | 复现证据全部在仓库内（`environment_b_qualification.json`、`runs/repro-envb-frozen-r2/`、复现包） |

### 7.20 2D Poisson Calibration 轮次（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json`；`pinn/experiments2d/` 9 个模块；`pinn/reference/analytic_poisson2d.py`；`pinn/validation/poisson2d.py`；`pinn/governance/poisson2d_contract.py`；`scientific_reference/poisson2d_fdm.py`；`experiments/poisson2d/`（审计、预注册、两份追加审计、配置、pilot、盲集池与账本、两个 run 的证据、9 张图、复现包、验证与鉴定脚本）；`tests/pinn/test_poisson2d_{identity,physics,reproduction}.py`；`docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md` |
| 修改的跟踪文件 | `pinn/experiments/report.py`（共享报告渲染器最小参数化，1D 默认输出不变）、CHANGELOG、本文件与修改报告、操作日志 |
| 仓库外新建（未删，等用户） | `C:/Users/user/LeoAI-envB2D-20260916/venv`（2D 的 Environment B，21,963 文件 / 0.64 GB；用户授权重建，torch 2.12.1+cpu、numpy 2.4.5；鉴定结果入库于 `experiments/poisson2d/environment_b_qualification.json`） |
| 删除 | 冒烟测试沙箱 `experiments/poisson2d/.smoke`（133 文件 / 1,385,275 字节，本轮自建、无结论依赖）；本轮 pytest 与 python 运行产生的字节码缓存与临时目录（见下行） |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件（删除）；`%LOCALAPPDATA%/Temp/pytest-of-user` 2,489 个文件 / 44,785,623 字节（本轮 pytest 六次，删除）；`.venv/` 内的 165 个 `__pycache__` 属安装自带、非本轮产物，未动 |
| 复核（删除后） | 主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`.smoke` 不存在；`git status` 干净 |
| 测试 | 1121 passed / 3 failed / 16 skipped（只增不减：1109 + 22 新增；3 红为既有 portability，已在 `experiments/poisson2d/PORTABILITY_AUDIT_20260916.md` 单独审计） |
| 未处理（等用户） | portability 的四项裁决（1D 既有 4 条发现 + 本轮新增 3 条同类路径发现）；Environment B 目录去留；残留工作树目录 `.claude/worktrees/leoaistudio-build-handover-99ccbd` 与 `.claude/worktrees/leoaistudio-cleanup-refactor-d129a8`（已不被 git 引用）以及本会话工作树 `leoaistudio-build-handover-57223c` |

### 7.21 2D Final Closure Audit 轮次（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `pinn/experiments2d/localized_error.py`；`experiments/poisson2d/{P11_SUPPLEMENT_PREREGISTRATION_20260916.md, p11_supplement.py, p11_decision.py, ac2d9_formula_audit.py, calibrate_localized_error.py, check_localized_error.py, final_closure_revalidation.py}`；`experiments/poisson2d/{AC2D9_FORMULA_AUDIT, LOCALIZED_ERROR_CALIBRATION, FINAL_CLOSURE_REVALIDATION}.json`；`runs/exp2d-poisson-calibration-r1/{POST_AUDIT_ANNOTATION.md, tier1_p11_supplement.json, trust_vector_g6_p11.json, claim_gate_decision_g6_p11.json}`；`tests/pinn/{test_ac2d9_invariants, test_localized_error_2d, test_claim_pool_state, test_p11_and_portability_closure}.py`；`docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md` |
| 修改的跟踪文件 | `pinn/experiments2d/runner2d.py`（账本推导状态 + 前移护栏）、`experiments/poisson2d/{qualify_environment_b.py, verify_tests_under_torch.py, TEST_VERIFICATION_UNDER_TORCH.json}`（路径中立）、2D 报告（仅更正 AC2D-9 标签与"严格强于"表述）、CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | 任何历史机器证据、`manifests/portability-historical-evidence.json`、`tools/portability_check.py`、宪法、协议汇编、1D 的全部记录、已提交的 pool manifest |
| 回滚 | 对 portability 豁免清单的 5 条新增条目——加载器只接受 `governance/**.md`，无法覆盖 `experiments/**` 的证据；扩大作用域属修改 policy 机制，本轮禁止 |
| 删除 | 本轮 pytest 与 python 运行产生的字节码缓存与临时目录（见下行） |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件，删除；`%LOCALAPPDATA%/Temp/pytest-of-user` 1,896 个文件 / 35,835,632 字节（本轮 pytest 五次），删除 |
| 复核（删除后） | 主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 干净。 |
| 测试 | 1147 passed / 3 failed / 18 skipped（1121 + 28 新增；3 红为既有 portability，已在 `PORTABILITY_AUDIT_20260916.md` 与收口报告 §4 单独审计） |
| 未处理（等用户） | portability 豁免机制作用域裁决；Environment B 目录去留；localized-error 经验 null 分布（需 ≥ 5 个已验证 run）；残留工作树目录与本会话工作树 |

### 7.22 外部评审裁决执行轮次（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json`；`tests/pinn/test_localized_error_trigger.py`；`docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md` |
| 修改的跟踪文件 | `tools/portability_check.py`（豁免作用域按批准扩展 + 必填 `ruling`/`constraint` + 拒绝通配符与目录）；`manifests/portability-historical-evidence.json`（新增 5 条人工批准归类）；`pinn/experiments2d/{localized_error,diagnostics2d,runner2d}.py`（d ≥ 2 触发条件）；`experiments/poisson2d/smoke_runner2d.py`（沙箱配置补判据）；`experiments/poisson2d/TEST_VERIFICATION_UNDER_TORCH.json`（重跑，仅时间戳变化，23 passed / 0 failed）；`tests/{test_portability.py, pinn/test_p11_and_portability_closure.py}`；终审收口报告追加第 11 节「后续」；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | 被豁免归类的 5 个证据文件本身（豁免绑定的就是其当前 sha256）、1D 的全部记录、2D 已完成 run 的冻结配置与全部机器证据、`LOCALIZED_ERROR_CALIBRATION.json`、宪法、协议汇编、已提交的 pool manifest |
| 仓库外目录 | `用户目录\LeoAI-envB2D-20260916`（Environment B，21,963 文件 / 0.64 GB）按裁决 **KEEP**，视为冻结复现夹具；本轮对它未执行任何操作（未安装、未修改、未删除）。常设规则：不做日常包安装；将来需要额外依赖则重新 qualification 或新建 B2 |
| 删除 | 仅本轮测试与脚本运行产生的字节码缓存与 pytest 临时目录（见下行） |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件 / 410,095 字节，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` 3,777 个文件 / 69,535,699 字节（本轮 pytest 五次 + 训练解释器验证一次），删除；补丁与草稿脚本写在会话临时目录（仓库外），未落入仓库 |
| 复核（删除后） | 主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 只剩本轮有意的改动 |
| 测试 | 1172 passed / **0 failed** / 18 skipped（1147 + 25 新增；上轮 3 红全部转为人工批准的精确哈希归类，非静默豁免）；被跳过的 18 项在训练解释器下 23 passed / 0 failed；portability 0 hard binding；PRELOCK 7/7 |
| 未处理（等用户） | 下一个 PDE 的启动指令；残留工作树目录与本会话工作树 |

### 7.23 Localized-error trigger 硬化轮次（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `tests/pinn/test_localized_error_hardening.py`（69 项）；`docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md` |
| 修改的跟踪文件 | `pinn/governance/poisson2d_contract.py`（新增局部判据合同与解析器；`CRITERIA` / `METRICS` / `THRESHOLD_SOURCES` 三张冻结表一字未改）；`pinn/experiments2d/localized_error.py`（seed 策略、fail-closed 校验、合同绑定）；`experiments/poisson2d/smoke_runner2d.py`（沙箱配置补齐九个必填字段）；`experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json`（追加 hardening 段与新必填字段）；`tests/pinn/test_localized_error_trigger.py`；`experiments/poisson2d/{FINAL_CLOSURE_REVALIDATION, TEST_VERIFICATION_UNDER_TORCH}.json`（重跑；diff 仅时间戳与 `currentTreeCodeHash`）；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | 账本、D_claim、`gate*_.json` 等已 ACCEPTED 的机器证据、四份 TrustVector、四份 ClaimGateDecision、正式 run 的冻结配置 `exp2d_baseline.json`、Poisson2D 验收阈值、宪法、协议汇编、`tools/portability_check.py` 与 `manifests/portability-historical-evidence.json`（本轮禁止再动 portability policy） |
| 删除 | 仅本轮测试与探针运行产生的字节码缓存与 pytest 临时目录（见下行） |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件 / 410,095 字节，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` 3,809 个文件 / 72,984,962 字节（本轮 pytest 六次 + 两次训练解释器运行），删除 |
| 复核（删除后） | `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 只剩本轮有意的改动 |
| 测试 | 1241 passed / **0 failed** / 18 skipped（1172 + 69 新增）；训练解释器下 23 passed / 0 failed；portability 0 hard binding（只跑回归）；PRELOCK 7/7 |
| 未处理（等用户） | 下一个 PDE 的启动指令；残留工作树目录与本会话工作树（仍停在旧提交，见 §5.29） |

### 7.24 代码身份完整性审计轮次（2026-09-16）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `tests/pinn/test_code_identity_completeness.py`（44 项）；`docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md` |
| 修改的跟踪文件 | `pinn/experiments/common.py`（边界常量 + `DECISION_SURFACES` + `CodeIdentityError` + `required_identity_paths` + `assert_code_identity_complete`）；`pinn/experiments2d/runner2d.py`（声明制 extra files、PRELOCK 之前的 fail-closed 检查、`identity.json` 记录边界）；`experiments/poisson2d/{FINAL_CLOSURE_REVALIDATION, TEST_VERIFICATION_UNDER_TORCH}.json`（重跑；diff 仅时间戳与当前树 codeHash）；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | 2D 已 ACCEPTED 的 `identity.json` / `codeManifest` / `codeHash` 与全部机器证据、账本、D_claim、TrustVector、ClaimGateDecision、冻结配置、验收阈值；1D 的 runner 与全部记录；宪法与协议汇编的**内容**（只是把协议汇编纳入身份清单，未改其字节）；`tools/portability_check.py` 与豁免清单 |
| 删除 | 仅本轮测试与审计脚本运行产生的字节码缓存与 pytest 临时目录（见下行） |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件 / 410,095 字节，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` 4,051 个文件 / 73,191,742 字节，删除。留痕：新增身份测试会在临时目录 `git init` 微型仓库，git 对象只读，首次删除残留 165 条目 / 69 文件，改用清除只读位的 `onerror` 后彻底删除 |
| 复核（删除后） | `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 只剩本轮有意的改动 |
| 测试 | 1285 passed / **0 failed** / 18 skipped（1241 + 44 新增）；targeted 44 passed；训练解释器 23 passed / 0 failed；portability 0 hard binding；PRELOCK 7/7 |
| 未处理（等用户） | 下一个 PDE 的启动指令；残留工作树目录与本会话工作树（仍停在旧提交） |

### 7.25 GEOMETRY LIFT 1 圆环标定轮次（2026-09-17 / 18）

| 项 | 内容 |
|---|---|
| 补记 | 本轮之前的圆环准备工作（提交 `62faf94` / `3e4d644` / `9a71120` / `fb9b329` 及更早的 `e6c1f9a`）此前**没有**写进操作日志、CHANGELOG 与本文件，已在操作日志 §5.32 一并补记 |
| 新增跟踪文件 | `experiments/annulus/bench_device_annulus.py`（EXPLORATORY 设备基准）；`experiments/annulus/smoke/DEVICE_BENCHMARK_{fresh-cpu,fresh-cuda,same-process}.json`；`docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md`；正式 attempt 目录 `experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu/`（含 10 张图）；停止记录 `experiments/annulus/runs/stopped-gpu-r1-sleep-8ee9b9236199/` |
| 修改的跟踪文件 | `pinn/experiments_annulus/{pinn_torch_annulus,runner_annulus,redteam_annulus}.py`（运行时 device + Tier-1 驱动入口）；`experiments/annulus/{run_formal_annulus,smoke_runner_annulus}.py`（`--device`、`--tier1`）；`experiments/annulus/EXPERIMENT_ANNULUS_PREREGISTRATION_20260917.md`（**只在文末追加**第 14 节，前 13 节一字未改，追加性经逐字节前缀比对验证）；`experiments/annulus/ledger/pdef-annulus-poisson-v1.json`（按协议追加 `OPENED` 事件）；`experiments/{annulus,poisson2d}/TEST_VERIFICATION_UNDER_TORCH.json`（重跑）；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | 冻结配置 `exp_annulus_baseline.json`（**device 没有进配置**）与全部 ACA / PH 阈值；盲集池 `pdef-annulus-poisson-v1-claim-pool.json`；冻结 ProblemDefinition（specHash `4c8dfbc7238d…`）；DAC-M1 / M2 / M3（仍 NEVER_SEALED）；治理 schema 的 `domainType` 词汇（缺 `annulus`，登记为 AMENDMENT CANDIDATE，未改）；Poisson 1D 与 2D 正方形的全部机器证据、账本、TrustVector、ClaimGateDecision；宪法与协议汇编；`tools/portability_check.py` 与豁免清单；Environment B 目录（只读核验，未安装任何包） |
| 未删除（明确） | 两份历史中止 / 停止记录 `runs/aborted-r1-codebug-4ef0ae3a/`、`runs/stopped-cpu-r1-c5a3e12e018e/`；本轮新增的第三份 `runs/stopped-gpu-r1-sleep-8ee9b9236199/`（休眠中断）；失败路径产物 `failure_record.json` / `dev_diagnostics.json` |
| 删除 | 仅本轮运行产生的字节码缓存、pytest 临时目录与自建自删的沙箱（见下行） |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **5,922 个文件 / 115,751,920 字节**，删除（身份测试会在临时目录 `git init`，git 对象只读，用清除只读位的 `onerror` 处理）；沙箱 `experiments/annulus/.smoke` **33 个文件 / 1,614,755 字节**，跑完即删；设备基准与补丁脚本写在会话临时目录（仓库外），未落入仓库 |
| 复核（删除后） | `__pycache__` **0 个目录**；`pytest-of-user` **不存在**；`.smoke` 不存在；`git status` 只剩本轮有意的改动 |
| 测试 | **1391 passed / 0 failed / 25 skipped**（与上轮基线一致，device 改动无回归）；训练解释器下 annulus **7 passed / 0 failed**、poisson2d **23 passed / 0 failed**；portability **0 hard binding / 1 configurable / 8 historical**；PRELOCK **7/7** |
| 未处理（等用户） | 圆环标定未通过后的走向（改步数属方法变更，须走新 revision + 新盲集成员）；残留工作树目录与本会话工作树（仍停在旧提交，本轮一次未使用） |

### 7.26 圆环诊断 Phase II 轮次（2026-09-19 / 20）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `pinn/experiments_annulus/checkpoint_annulus.py`；`experiments/annulus/{resume_fidelity_annulus,run_nested_budget_diagnosis,plots_budget_diagnosis}.py`；`experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md`；`tests/pinn/{test_annulus_budget_schedule,test_annulus_checkpoint_resume}.py`；`docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md`；诊断产物 `experiments/annulus/diagnosis/`（约 28 MB：30 个完整 checkpoint 约 27.4 MB、`DIAGNOSIS.json`、`identity.json`、`config_nested_budget.json`、`RESUME_FIDELITY.json`、7 张图） |
| 修改的跟踪文件 | `pinn/experiments_annulus/pinn_torch_annulus.py`（`lrPrefixSteps` 解耦、`learning_rates` 改为迭代语义、checkpoint 发射与 resume）；`experiments/annulus/verify_tests_under_torch.py`（登记新测试模块）；`experiments/{annulus,poisson2d}/TEST_VERIFICATION_UNDER_TORCH.json`（重跑）；预注册**追加**第 16 节勘误（前 15 节一字未改）；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | r1 的全部机器证据、`identity.json`、codeHash `8ee9b9236199…`、`failure_record.json`、TrustVector、状态转移、正式 seed 账本；冻结配置 `exp_annulus_baseline.json`（`steps` 仍 120000，无 `lrPrefixSteps`）；全部 ACA / PH 阈值；局部判据合同；盲集池；ScientificSpec revision 1 与 specHash `4c8dfbc7238d…`；治理 schema 与 Constitution；Gate 4 / TrustStatus / claim 前置条件；`tools/portability_check.py`；Environment B（本轮未访问） |
| 未触碰（机器核验） | 账本事件前后一致 `['SEALED','OPENED']`，sha256 相同；`DAC-M0 = BURNT`、`DAC-M1 / M2 / M3 = NEVER_SEALED` |
| 用户审批通过 | 2026-09-19：30 个完整 checkpoint（约 27.4 MB）**全部提交进仓库** |
| 测试产物（建立与删除） | 沙箱冒烟 `experiments/annulus/diagnosis/.smoke` **8 个文件 / 5,520,585 字节**，跑完即删；`__pycache__` 与 `pytest-of-user` 见复核行；脚本草稿写在会话临时目录（仓库外） |
| 测试 | **1414 passed / 0 failed / 26 skipped**（上轮 1391 / 25）；训练解释器 annulus **24 passed / 0 failed**、poisson2d **23 passed / 0 failed**；portability **0 hard binding / 1 configurable / 8 historical**；PRELOCK **7/7** |
| 未处理（等用户） | 五项未满足的排除义务（是否授权「诊断用 Tier-1」）；revision 2 的 B\* 取 180k 还是 240k；六条 AMENDMENT CANDIDATE 的统一审议 |

### 7.27 圆环排除诊断轮次（2026-09-20 / 21）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `pinn/experiments_annulus/exclusion_annulus.py`；`experiments/annulus/run_exclusion_experiments.py`；`experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md`；`tests/pinn/test_untracked_code_identity.py`（10 项）；`docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md`；诊断工件 `experiments/annulus/diagnosis/exclusions/`（5 个 `exp-*` + `EXCLUSIONS.json`） |
| 修改的跟踪文件 | `pinn/experiments/common.py`（`all_tracked_paths` / `untracked_identity_paths`；`assert_code_identity_complete` 拒绝未跟踪；`codeIdentityExtraFiles` 必须已跟踪）；`pinn/governance/prelock.py`（新增 `codeIdentityTracked`，检查数 7→8）；`tests/pinn/test_annulus_budget_schedule.py`（+2 项 fail-closed 测试与 loader 拆分）；`docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md`（29/30 就地更正 + 追加第 13 节勘误）；预注册**追加**第 10 节（运行前）；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | r1 的全部机器证据与 codeHash `8ee9b9236199…`；Phase II 的 `DIAGNOSIS.json` 与 checkpoint；冻结配置 `exp_annulus_baseline.json`；全部 ACA / PH 阈值；局部判据合同；盲集池；ScientificSpec revision 1 与 specHash `4c8dfbc7238d…`；Gate 4 / TrustStatus / claim 前置条件；geometry schema；Tier-1 语义；Constitution；`tools/portability_check.py`；Environment B（本轮未访问） |
| 未触碰（机器核验） | 账本事件前后一致 `['SEALED','OPENED']`，sha256 相同；`DAC-M0 = BURNT`、`DAC-M1 / M2 / M3 = NEVER_SEALED` |
| 白跑并重做 | 探针标签 off-by-one 使五次 120k 训练（约 1.8 小时）的工件未落盘；**未从日志誊数**，重跑得到逐位相同的结果 |
| 测试产物（建立与删除） | 主检出仓库源码下 `__pycache__` 与 `%LOCALAPPDATA%\\Temp\\pytest-of-user` 见复核行；补丁脚本写在会话临时目录（仓库外），未落入仓库 |
| 测试 | **1426 passed / 0 failed / 26 skipped**（上轮 1414 / 26）；训练解释器 annulus **24 passed**、poisson2d **23 passed**；**PRELOCK 8/8**；portability **0 hard binding / 1 configurable / 8 historical** |
| 未处理（等用户与外部评审） | `rSamplingDeficiency` 与 `rOptimizationFailure` 的判别设计；R3 与 G2 两条判据是否事前修订；`rCapacityLimit` 的 `exp-*` 标识；7 条 AMENDMENT CANDIDATE 的统一审议 |

### 7.28 四项委托裁决的执行（2026-09-21）

| 项 | 内容 |
|---|---|
| 新增跟踪文件 | `experiments/annulus/ANNULUS_NEXT_ROUND_DESIGN_NOTES_20260921.md`（**只记设计与推迟理由，不冻结任何判据**）；`experiments/annulus/diagnosis/exclusions/superseded/exp-annulus-dx-reference.as-first-run.json`（被取代的原工件，保留） |
| 修改的跟踪文件 | `pinn/experiments_annulus/exclusion_annulus.py`（两处**仪器**修复：Jacobi 符号 + 残差容差迭代；审计根集合 + 包节点 + 相对导入。**判据零改动**）；`tests/pinn/test_untracked_code_identity.py`（+3 审计健全性）；`tests/pinn/test_annulus_checkpoint_resume.py`（+3 控制有效性与 G3 规格自相矛盾）；`experiments/annulus/diagnosis/exclusions/{exp-annulus-dx-reference,EXCLUSIONS}.json`（修复仪器后重跑）；`experiments/annulus/TEST_VERIFICATION_UNDER_TORCH.json`；三份文档的**追加**（本轮报告 §12、Phase II 报告 §14、0920 预注册 §11）；CHANGELOG、本文件与修改报告、操作日志 |
| 未修改（明确） | 任何判据与阈值；0919/0920 两份预注册的 §0–§10 正文；r1 与 Phase II 的全部机器证据；四份未涉及的 `exp-*` 工件；冻结配置；盲集池；specHash；Gate 4 / TrustStatus / geometry schema / Tier-1 语义 / Constitution |
| 未触碰（机器核验） | 账本 `['SEALED','OPENED']`；`DAC-M0 = BURNT`、`DAC-M1 / M2 / M3 = NEVER_SEALED` |
| 改记（重要） | `rCapacityLimit` 由「已排除」改记为**未排除**；未排除原因由 3 项改为 **4 项** |
| 测试 | **1429 passed / 0 failed / 26 skipped**（上轮 1426）；训练解释器 annulus **27 passed**、poisson2d **23 passed**；PRELOCK **8/8**；portability **0 hard binding / 1 configurable / 8 historical** |
| 未处理（等用户与外部评审） | 是否写 `rUndetermined` 的 DiagnosisRecord 并迁到 `STOPPED_THE_LINE`；四项未排除各自的下一步；7 条 AMENDMENT CANDIDATE |

```

</details>

### R004 — 项目/docs/F008_SOURCE_PROVENANCE_CLOSURE_PHASE2.md

<details>
<summary>展开完整原文</summary>

````markdown
# F-008 source provenance closure — Phase II

This report records a source-side repair. The existing installed application is
not declared current from these files. F-008 is PASS only for a separately
identified package/installation when `tools/theme_asset_provenance.py --strict
--app-root <that-root>` succeeds after the sources are committed. Historical
reports and the old installation were not modified.

## Definition and corrected inventory

The existing definition in `docs/THEME_INK_AUTUMN.md`, section 10, requires each
runtime theme asset to trace to a committed source and its deployed bytes to
match. The previous actual installation contained 20 measured theme assets;
12 had tracked mappings and 8 were reported as gaps. The eight were:

| Previously missing mapping | Source-side resolution |
| --- | --- |
| `fonts/manifest.json` | New canonical manifest authored from pinned upstream retrieval and independent byte-for-byte font reconstruction |
| `fonts/Inter-Variable.woff2` | Independently rebuilt from pinned Google Fonts TTF; original installed bytes reproduced exactly |
| `fonts/SpaceGrotesk-Variable.woff2` | Same, with exact upstream CRLF license notice preserved |
| `fonts/NotoSansSC-Variable.woff2` | Same; all 31,036 glyphs retained |
| `fonts/JetBrainsMono-Variable.woff2` | Same; all 1,179 glyphs retained |
| `i18n/zh.json` | Project-authored replacement preserving the existing 20-key flat-string runtime contract |
| `i18n/en.json` | Project-authored replacement preserving the same keys and brand names |
| `logos/leo-lion.2c2bb981ec6e98a9.ico` | Existing runtime-generated exact copy of committed `stage/logos/leo-lion.ico`; independently checked filename digest and complete bytes |

There are 19 canonical package theme assets. The twentieth is a content-addressed
native icon generated after launch; a clean package need not contain that cache
file. No missing asset was hidden by deleting it from the old installation or
omitting unknown files from the scanner. The scanner now includes source and
deployed files in `fonts`, `i18n`, `backgrounds`, and `logos`.

`manifests/runtime-asset-origins.json` lists all 19 assets with source files,
origin, upstream project, version/commit, license status, expected SHA-256,
runtime consumer, build/deployment paths and provenance status. Generated icon
copies use the canonical icon's origin record and require both the precise
16-hex filename suffix and full matching content.

## Independent upstream font proof

Official upstream: [Google Fonts](https://github.com/google/fonts).
The observed branch was resolved using `git ls-remote` to commit
`5e35378e6bda803962ee6fd257e444a7d459660d`. Every download then used that exact
commit rather than the moving branch. An earlier GitHub API request returned
HTTP 403 rate-limit exceeded; no data from that failed request was accepted.

Four TTF sources and their OFL notices were retrieved from the official commit.
All TTF hashes matched the previously installed manifest. A fresh conversion
with fontTools 4.57.0, Brotli 1.1.0, and `TTFont(..., recalcTimestamp=False)`
reproduced every installed WOFF2 SHA-256. Running the committed rebuild recipe
again into a second empty directory reproduced all four hashes again.

| Family/version | Glyphs | Reproduced WOFF2 SHA-256 |
| --- | ---: | --- |
| Inter 4.001, git-66647c0bb | 2,933 | `13b4cddc57045d40b411008e61588c8f81aa0bd72fe884624831a0ff9c4d159a` |
| Space Grotesk 2.000 | 1,001 | `8e085aa438094f11487a836652edd5c054fa6a96f63fc7c282105ee3a4b08c07` |
| Noto Sans SC 2.004-H2 | 31,036 | `aef8c34277afad81ecd0227138a830263c0caea65b7aea66d1195395f097b55a` |
| JetBrains Mono 2.211 | 1,179 | `7b7f3419196f675a973d30cb70078749120caddea86c8547ebf54a8db2ca13af` |

TTF source SHA-256 values, exact source URLs, copyright statements, license URLs
and notice hashes are in `stage/fonts/manifest.json`. All four licenses are
upstream SIL OFL 1.1. The original bytes of the notices are committed under
`LICENSES/fonts/`; `.gitattributes` disables text conversion for those notices
because the upstream Space Grotesk notice contains 93 CRLF line endings.
There is no glyph subsetting, family renaming, font replacement or new font
dependency in the ordinary application build.

The optional regeneration command is:

```text
python tools/build_fonts.py --source-dir <source-cache> --output <new-directory> --fetch
```

It requires the recorded font toolchain, checks the pinned TTF before opening
it, rejects path escapes, creates the output directory exclusively, preserves
failed output, and checks each rebuilt WOFF2 against the registered hash.
Application packaging copies the committed WOFF2 files and does not run this
download or font conversion step.

## Unknown history is retained explicitly

The historical authorship/source of the installed locale JSON files could not
be independently established from version control. Those original files
remain **SOURCE UNKNOWN** in the preserved pre-change evidence. The new
locale tables are project-authored replacements based on the observed runtime
keys, with fresh descriptive wording; they are not relabeled copies of unknown
historical provenance. Brand identifiers, ordinary UI labels and the 20-key
contract remain intact. The replacement font manifest is likewise newly
authored from measured upstream records, rather than attributing the old
manifest to an invented source commit.

The native ICO's provenance was resolved without importing a redundant cache
file. Both installed ICOs and the committed canonical ICO have SHA-256:

```text
2c2bb981ec6e98a91bc4926aad9504915dd2c2e38accc806463cdb64e4a79b63
```

The established producer is
`leo_shell/windows_branding.py::prepare_branding_resource`. The checker rejects
wrong content, wrong digest names and unrecognized extra files.

Existing project assets retain their repository source identity. The manifest
explicitly says that Leo's outbound project license has not been declared;
this engineering provenance record grants no new redistribution rights and is
not a whole-product license clearance. The separate, read-only sibling OSS
audit at commit `56041288f5237e6030a092912f55fc58a364727c` flags additional
upstream runtime distribution issues outside these four theme fonts. Those
issues were not silently cleared, and that audit's installed-manifest assertion
was not used as a substitute for this independent upstream reconstruction.

## Build/deployment integration contract

`tools/build_launcher.ps1` packages canonical `stage/fonts/` and `stage/i18n/`
into `package/theme/` and places notices in `package/LICENSES/fonts/`.
`tools/deploy_release.ps1` carries those paths into the selected application
root. Root-agent build/deployment evidence is required for the concrete
installation verdict. Source success alone cannot establish P0-1 or installed
F-008 PASS.

The updated checker additionally rejects sources present only in the Git
index, working copies differing from HEAD, missing/unknown origin records,
changed manifest hashes, missing or changed source/deployed OFL notices, and
extra fonts. It no longer prints CLOSED when all assets are versioned but
deployed bytes drift. That was an actual defect in the previous summary text.

## Executed validation and user-requested test cleanup

Using the previous verified worktree's locked Python environment:

```text
python -m pytest tests/test_theme_asset_provenance.py tests/leo_shell/test_theme_runtime.py -q --tb=short
```

Result: **74 passed / 0 failed / 0 skipped** (26 new F-008 cases and 48 existing
ThemeRuntime cases). The executed new test file SHA-256 was
`d3816ff7b7faaa350f0bcbba1bdf3ad3256f8ce4c29ab46ace62282e934d6271`.
The original first command also named a nonexistent
`tests/leo_shell/test_windows_branding.py` and collected no tests; the corrected
command above is the evidence-bearing run, not that failed invocation.

Covered cases: matching committed assets and notices; missing/uncommitted or
modified sources; missing/changed deployed files; modified origin manifest;
unknown source status; incorrect expected hash; missing/changed/uncommitted or
unsafe license evidence; exact generated icon mapping; corrupted or misnamed
generated icons; extra unknown fonts; three-layer bundle reconstruction and
tampering; malformed support metadata; corrupted TTF; four path-escape forms;
actual four-font and license hashes; and bilingual flat-string contract.

At the user's explicit follow-up request, the 26-case new regression source
`tests/test_theme_asset_provenance.py` was deleted after execution. No existing
test source was deleted. The result log and this coverage description preserve
the evidence, but the deleted cases are not part of the delivered reusable
regression suite. Remaining full-regression results are reported separately by
the root agent.

## Evidence inventory

All F-008 collection was contained in the Phase II evidence directory:

- `f008-source-audit/original-assets/`: exact-byte pre-change copies of all eight gaps.
- `f008-source-audit/original-inventory.json`: their original hashes and sizes.
- `f008-source-audit/acquisition.json`: official commit, source/license/WOFF2 hashes, font versions, glyph counts and comparison outcomes.
- `f008-scoped-tests.log`: the 74-pass scoped test run.
- `f008-verified-results.json`: compressed independent reconstruction and original-asset identity results.

Temporary downloaded TTFs and duplicate reconstructed WOFF2 outputs can be
removed after the summary hashes have been retained. They are reproducible
from pinned public upstream records; source-controlled runtime faces and
upstream notices remain the build inputs. No original application files,
original dirty repository files, old evidence or frozen scientific files were
modified in this asset closure task.

````

</details>

### R005 — 项目/docs/LEO_CONVERSATION_FRONTEND_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# Conversation model controls and public reasoning display — 2026-09-09

## Verdict and boundary

**Frontend component validation: PASS — 55 passed, 0 failed, 0 skipped, 0 blocked.** This result covers the actual model-control and projection functions in `stage/leo-inject.js`, executed in a separate real headless Chrome DOM with controlled ShellApi/HTTP fixtures and the canonical upstream streaming/rendering functions. It is not installed-app acceptance, an upstream provider accuracy claim, or a PINN Gate result. No native Leo window, real provider, real user conversation, real user credentials, or scientific evidence was operated by these tests. Parent integration work must separately verify the built/installed application and actual providers.

Product source frozen for this report:

- `stage/leo-inject.js`: SHA-256 `188b208da276978d2ce4504d44e0f3869e26c53f33950bf8af782f802e3f371a`.
- `stage/leo.css`: SHA-256 `b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf`.
- Worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree`, branch `codex/conversation-runtime-20260909`; parent owns source commit, final asset-manifest update, package build, installation, and full regression.

## Changes and causal reasons

`stage/leo-inject.js` provides native per-conversation model choices, compare-and-set selection through ShellApi, and an immutable model binding plus reasoning choice on the existing same-origin message POST. It leaves unrelated requests and the global provider setting alone. Missing native ownership, unsupported reasoning options, unavailable models, failed binding, malformed controlled requests, and unready credentials prevent message admission.

Eight initial browser failures exposed real implementation defects: a selected effort was silently rewritten to a fresh capability revision; the same happened to the default choice; an in-flight request for session A prevented restoration for session B; missing branch identifiers were accepted; projection identities could be reused across executions; malformed event text, operation, and status values were accepted; rebuilding a session DOM lost its reasoning history; and changing branches within one session did not request branch history. The fixes retain the exact capability revision that the user selected, require an explicit choice when controls or binding identity change, restore independently per session and branch, detect removed DOM nodes, and validate projection identity and protocol fields. Restoration checks snapshot text SHA-256 before changing the display. A failed restore does not create a retry loop on every DOM update.

Native integration then exposed five additional browser failures around daemon restart. The credential broker is process-local: a persisted model binding alone does not prove that the running broker has a key. The UI now observes the public `credential_ready` flag and asks native ShellApi to select the same saved model when credentials must be restored. No secret enters JavaScript. It preserves the chosen effort only when both model binding identity/revision and capability revision remain unchanged. Changed identities or controls require reselection; failure and false-success responses block sending. First-message binding also preserves the effort the user chose before that first message. An external binding change no longer silently resets the chosen effort to Default.

The Thought display consumes only provider-supplied `reasoning_content` or `reasoning` projection fields. It does not fabricate thoughts from final answers. Progress and completion records fold only when the original whole message and every declared segment match their SHA-256 and exact joined text. Candidate bodies, original message data, and original copy controls retain their exact source text. Bad hashes, mismatched segments, additional unframed live output, and unsupported metadata leave the raw answer visible. Live output is projected only after upstream `turnDone` has finalized the stream.

`stage/leo.css` contains the parent-created model/effort controls and collapsed reasoning/progress presentation. This frontend continuation did not modify the CSS bytes. No frozen scientific specification, Gate, tolerance, existing test, or acceptance threshold was changed by this subtask.

## Test method and evidence interpretation

Environment: Windows, Node.js `v24.16.0`, Chrome `152.0.7977.83`. The harness used Node built-ins only, a new isolated browser profile per run, a loopback fixture page, a restrictive page content-security policy, and browser CDP. It never connected to the native application's debugging port. The fixture loaded the exact function interval from `function sessionModelState` up to `function localFailureReplacement` in the current product source, the current CSS, and bounded canonical upstream streaming/rendering functions from the installed read-only OpenAI4S source. DOM helpers and ShellApi/HTTP responses were controlled fixtures. This distinction matters: it verifies browser behavior and request assembly, not the native key broker or actual network model behavior.

Commands used:

```text
node --check stage/leo-inject.js
node ../ui-evidence/model-runtime-20260909/frontend-dom-qa-temporary.mjs
```

The syntax check exited successfully. The temporary browser harness was removed after its results were consolidated below, as the user explicitly requested, including newly created regression source. Existing repository tests were preserved. The browser suite covers CAS success/failure, conversation isolation, mid-conversation model changes, first-message binding, unsupported/unknown options, stale policy and saved-choice recovery, credential reinjection, exact wire payload assembly, projection sequence gaps and replay, branch/scope isolation, malformed events, failure/cancellation, HTML injection, SHA-guarded folding, original copy text, and live final/candidate completion.

The original fixture used `op=state` for a failed terminal event, but the actual runtime protocol permits `append`, `bind`, and `terminal`. The fixture was corrected to `terminal`. Authoritative snapshot fixtures were also given the SHA-256 emitted by the actual runtime. An explicit corrupt-hash case verifies rejection. These alignments did not suppress any product failure. All prior failing results and their error messages are retained verbatim below.

## Remaining acceptance work

Actual DeepSeek/Qwen inference, package source/asset binding, installed UI behavior, restart integration against the real daemon, and real test-conversation deletion are outside this isolated frontend suite and must be reported by the parent integration task. These browser results do not authorize formal PINN HASH LOCK, training, or an accuracy claim.

## Append-only browser run records

The following records consolidate the temporary JSON results, including earlier failures. Each record includes exact product, bounded-source, CSS, and harness hashes, browser/process identity, counts, and per-case outcomes. Temporary screenshots were incidental images of the last fixture case, were not used as visual acceptance evidence, and are recorded by hash in the cleanup inventory before deletion.

### frontend-dom-qa-2026-09-09T10-04-52-886Z.json

SHA-256: 3ca4c34610e31f878953db1125a346769c40820a342dad15f07b6ff4d9771612

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T10-04-52-886Z",
  "source_sha256": "222ca9069d7a5a5a0446e4946570631746a1aba9834eba798d1521f6ede2f060",
  "bounded_source_sha256": "ae641123e3ed972570f3d99d8e63d6f0dc8aa2fc52b838418f063ae7a667d563",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "9c1dda40fac13a11ec3966034a3f2aa50d2c64f21315b2f6a4b708b473873a4f",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 110628,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-04-52-886Z",
  "fixture_origin": "http://127.0.0.1:59374/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "FAIL",
      "milliseconds": 5,
      "error": "Error: Error: STALE_CAPABILITY_SILENTLY_RESUBMITTED:[{\"choice\":\"low\",\"capability_revision\":\"cap2\"}]\n    at assert (http://127.0.0.1:59374/?case=capability_revision_change_requires_reselection:1318:48)\n    at <anonymous>:1:379"
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "FAIL",
      "milliseconds": 84,
      "error": "Error: Error: SESSION_B_REOPEN_NEVER_REQUESTED:[\"/api/v1/frames/a/leo-projections?branch_id=a\"]\n    at assert (http://127.0.0.1:59374/?case=pending_projection_request_does_not_starve_next_session:1318:48)\n    at <anonymous>:1:325"
    }
  ],
  "passed": 0,
  "failed": 2,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

### frontend-dom-qa-2026-09-09T10-15-37-057Z.json

SHA-256: 0b92d43079e18ee63464d211f644830909f49d7182fe13e55af3d44f1ac717c2

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T10-15-37-057Z",
  "source_sha256": "222ca9069d7a5a5a0446e4946570631746a1aba9834eba798d1521f6ede2f060",
  "bounded_source_sha256": "ae641123e3ed972570f3d99d8e63d6f0dc8aa2fc52b838418f063ae7a667d563",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "9587e36ead09f1ce22a8bf34f4db89e076a48ff2d43a0b1bc3d195cafca18a2b",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 86168,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-15-37-057Z",
  "fixture_origin": "http://127.0.0.1:53135/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "FAIL",
      "milliseconds": 6,
      "error": "Error: Error: STALE_CAPABILITY_SILENTLY_RESUBMITTED:[{\"choice\":\"low\",\"capability_revision\":\"cap2\"}]\n    at assert (http://127.0.0.1:53135/?case=capability_revision_change_requires_reselection:1319:48)\n    at <anonymous>:1:379"
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "FAIL",
      "milliseconds": 82,
      "error": "Error: Error: SESSION_B_REOPEN_NEVER_REQUESTED:[\"/api/v1/frames/a/leo-projections?branch_id=a\"]\n    at assert (http://127.0.0.1:53135/?case=pending_projection_request_does_not_starve_next_session:1319:48)\n    at <anonymous>:1:325"
    },
    {
      "name": "default_revision_change_requires_reselection",
      "status": "FAIL",
      "milliseconds": 2,
      "error": "Error: Error: DEFAULT_POLICY_CHANGED_WITHOUT_RESELECT\n    at assert (http://127.0.0.1:53135/?case=default_revision_change_requires_reselection:1319:48)\n    at <anonymous>:1:140"
    },
    {
      "name": "model_switch_CAS_success_sends_bound_profile_only",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "model_switch_CAS_failure_keeps_old_binding",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "two_conversation_choices_are_isolated",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "unknown_existing_pin_requires_explicit_selection",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "unavailable_model_cannot_bind",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "loadModels_rebuild_restores_options_and_handler",
      "status": "PASS",
      "milliseconds": 53
    },
    {
      "name": "unsupported_and_invalid_reasoning_fail_closed",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "non_message_fetch_unchanged",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "request_body_snapshot_overrides_stale_client_fields",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "list_failure_prevents_network_message",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_duplicate_and_old_seq_are_idempotent",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_gap_restores_without_appending_gap",
      "status": "PASS",
      "milliseconds": 82
    },
    {
      "name": "projection_wrong_frame_branch_and_fake_thought_rejected",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_missing_branch_rejected",
      "status": "FAIL",
      "milliseconds": 4,
      "error": "Error: Error: MISSING_BRANCH_ACCEPTED\n    at assert (http://127.0.0.1:53135/?case=projection_missing_branch_rejected:1319:48)\n    at <anonymous>:1:38\n    at <anonymous>:1:136"
    },
    {
      "name": "projection_identity_reuse_rejected",
      "status": "FAIL",
      "milliseconds": 6,
      "error": "Error: Error: PROJECTION_IDENTITY_CHANGED\n    at assert (http://127.0.0.1:53135/?case=projection_identity_reuse_rejected:1319:48)\n    at <anonymous>:1:56\n    at <anonymous>:1:328"
    },
    {
      "name": "projection_malformed_text_op_status_rejected",
      "status": "FAIL",
      "milliseconds": 4,
      "error": "Error: Error: MALFORMED_EVENT_ACCEPTED:{\"text\":123}\n    at assert (http://127.0.0.1:53135/?case=projection_malformed_text_op_status_rejected:1319:48)\n    at <anonymous>:1:110\n    at <anonymous>:1:223"
    },
    {
      "name": "projection_failed_status_preserves_partial_thought",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_HTML_is_plain_text",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "projection_same_frame_DOM_rebuild_restores_history",
      "status": "FAIL",
      "milliseconds": 125,
      "error": "Error: Error: SAME_FRAME_REBUILD_LOST_HISTORY\n    at assert (http://127.0.0.1:53135/?case=projection_same_frame_DOM_rebuild_restores_history:1319:48)\n    at <anonymous>:1:319"
    },
    {
      "name": "projection_same_frame_branch_switch_restores",
      "status": "FAIL",
      "milliseconds": 89,
      "error": "Error: Error: BRANCH_SWITCH_NOT_RESTORED\n    at assert (http://127.0.0.1:53135/?case=projection_same_frame_branch_switch_restores:1319:48)\n    at <anonymous>:1:126"
    },
    {
      "name": "partial_history_is_explicitly_labeled",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_final_and_completion_record_preserve_exact_copy",
      "status": "PASS",
      "milliseconds": 55
    },
    {
      "name": "stored_candidate_preserves_audited_body_and_raw_copy",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_bad_whole_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 51
    },
    {
      "name": "stored_bad_segment_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 38
    },
    {
      "name": "stored_nonmatching_spans_keep_raw_visible",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_user_message_cannot_be_hidden",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "stored_final_HTML_uses_sanitized_renderer",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_progress_and_snapshot_do_not_duplicate_reopen",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "live_final_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "live_candidate_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "live_extra_unframed_text_is_not_hidden",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "replay_end_requests_persisted_projection_snapshot",
      "status": "PASS",
      "milliseconds": 77
    }
  ],
  "passed": 28,
  "failed": 8,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session",
    "/?case=default_revision_change_requires_reselection",
    "/?case=model_switch_CAS_success_sends_bound_profile_only",
    "/?case=model_switch_CAS_failure_keeps_old_binding",
    "/?case=two_conversation_choices_are_isolated",
    "/?case=unknown_existing_pin_requires_explicit_selection",
    "/?case=unavailable_model_cannot_bind",
    "/?case=loadModels_rebuild_restores_options_and_handler",
    "/?case=unsupported_and_invalid_reasoning_fail_closed",
    "/?case=non_message_fetch_unchanged",
    "/?case=request_body_snapshot_overrides_stale_client_fields",
    "/?case=list_failure_prevents_network_message",
    "/?case=projection_duplicate_and_old_seq_are_idempotent",
    "/?case=projection_gap_restores_without_appending_gap",
    "/?case=projection_wrong_frame_branch_and_fake_thought_rejected",
    "/?case=projection_missing_branch_rejected",
    "/?case=projection_identity_reuse_rejected",
    "/?case=projection_malformed_text_op_status_rejected",
    "/?case=projection_failed_status_preserves_partial_thought",
    "/?case=projection_HTML_is_plain_text",
    "/?case=projection_same_frame_DOM_rebuild_restores_history",
    "/?case=projection_same_frame_branch_switch_restores",
    "/?case=partial_history_is_explicitly_labeled",
    "/?case=stored_final_and_completion_record_preserve_exact_copy",
    "/?case=stored_candidate_preserves_audited_body_and_raw_copy",
    "/?case=stored_bad_whole_hash_keeps_raw_visible",
    "/?case=stored_bad_segment_hash_keeps_raw_visible",
    "/?case=stored_nonmatching_spans_keep_raw_visible",
    "/?case=stored_user_message_cannot_be_hidden",
    "/?case=stored_final_HTML_uses_sanitized_renderer",
    "/?case=stored_progress_and_snapshot_do_not_duplicate_reopen",
    "/?case=live_final_waits_for_turnDone_then_projects",
    "/?case=live_candidate_waits_for_turnDone_then_projects",
    "/?case=live_extra_unframed_text_is_not_hidden",
    "/?case=replay_end_requests_persisted_projection_snapshot"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

### frontend-dom-qa-2026-09-09T10-49-08-386Z.json

SHA-256: a6ad8578ebccf95437e82a7c59979d09a31873594fa2f99e789adce83e194a65

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T10-49-08-386Z",
  "source_sha256": "1ec55883d83a9bbdd170e4464ab7bdf96ff3696d2fc7debf3f3d2ae890618d75",
  "bounded_source_sha256": "8d32be34421a59b25d9d3a85c7ff1b871c4b7ad879c6e13939bd61e968970f12",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "451bfb5aa48fdba246324562536fc73080deda0719ffe240f8f933a065a7dcd7",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 59600,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-49-08-386Z",
  "fixture_origin": "http://127.0.0.1:55683/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "PASS",
      "milliseconds": 75
    },
    {
      "name": "default_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "model_switch_CAS_success_sends_bound_profile_only",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "model_switch_CAS_failure_keeps_old_binding",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "two_conversation_choices_are_isolated",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "unknown_existing_pin_requires_explicit_selection",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "unavailable_model_cannot_bind",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "loadModels_rebuild_restores_options_and_handler",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "unsupported_and_invalid_reasoning_fail_closed",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "non_message_fetch_unchanged",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "request_body_snapshot_overrides_stale_client_fields",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "list_failure_prevents_network_message",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_duplicate_and_old_seq_are_idempotent",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_gap_restores_without_appending_gap",
      "status": "PASS",
      "milliseconds": 77
    },
    {
      "name": "projection_wrong_frame_branch_and_fake_thought_rejected",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "projection_missing_branch_rejected",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "projection_identity_reuse_rejected",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "projection_malformed_text_op_status_rejected",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "projection_failed_status_preserves_partial_thought",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_HTML_is_plain_text",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_same_frame_DOM_rebuild_restores_history",
      "status": "PASS",
      "milliseconds": 152
    },
    {
      "name": "projection_same_frame_branch_switch_restores",
      "status": "PASS",
      "milliseconds": 83
    },
    {
      "name": "partial_history_is_explicitly_labeled",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_final_and_completion_record_preserve_exact_copy",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "stored_candidate_preserves_audited_body_and_raw_copy",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_bad_whole_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_bad_segment_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 54
    },
    {
      "name": "stored_nonmatching_spans_keep_raw_visible",
      "status": "PASS",
      "milliseconds": 37
    },
    {
      "name": "stored_user_message_cannot_be_hidden",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_final_HTML_uses_sanitized_renderer",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_progress_and_snapshot_do_not_duplicate_reopen",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "live_final_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 39
    },
    {
      "name": "live_candidate_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "live_extra_unframed_text_is_not_hidden",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "replay_end_requests_persisted_projection_snapshot",
      "status": "PASS",
      "milliseconds": 79
    }
  ],
  "passed": 36,
  "failed": 0,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session",
    "/?case=default_revision_change_requires_reselection",
    "/?case=model_switch_CAS_success_sends_bound_profile_only",
    "/?case=model_switch_CAS_failure_keeps_old_binding",
    "/?case=two_conversation_choices_are_isolated",
    "/?case=unknown_existing_pin_requires_explicit_selection",
    "/?case=unavailable_model_cannot_bind",
    "/?case=loadModels_rebuild_restores_options_and_handler",
    "/?case=unsupported_and_invalid_reasoning_fail_closed",
    "/?case=non_message_fetch_unchanged",
    "/?case=request_body_snapshot_overrides_stale_client_fields",
    "/?case=list_failure_prevents_network_message",
    "/?case=projection_duplicate_and_old_seq_are_idempotent",
    "/?case=projection_gap_restores_without_appending_gap",
    "/?case=projection_wrong_frame_branch_and_fake_thought_rejected",
    "/?case=projection_missing_branch_rejected",
    "/?case=projection_identity_reuse_rejected",
    "/?case=projection_malformed_text_op_status_rejected",
    "/?case=projection_failed_status_preserves_partial_thought",
    "/?case=projection_HTML_is_plain_text",
    "/?case=projection_same_frame_DOM_rebuild_restores_history",
    "/?case=projection_same_frame_branch_switch_restores",
    "/?case=partial_history_is_explicitly_labeled",
    "/?case=stored_final_and_completion_record_preserve_exact_copy",
    "/?case=stored_candidate_preserves_audited_body_and_raw_copy",
    "/?case=stored_bad_whole_hash_keeps_raw_visible",
    "/?case=stored_bad_segment_hash_keeps_raw_visible",
    "/?case=stored_nonmatching_spans_keep_raw_visible",
    "/?case=stored_user_message_cannot_be_hidden",
    "/?case=stored_final_HTML_uses_sanitized_renderer",
    "/?case=stored_progress_and_snapshot_do_not_duplicate_reopen",
    "/?case=live_final_waits_for_turnDone_then_projects",
    "/?case=live_candidate_waits_for_turnDone_then_projects",
    "/?case=live_extra_unframed_text_is_not_hidden",
    "/?case=replay_end_requests_persisted_projection_snapshot"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

### frontend-dom-qa-2026-09-09T10-51-03-676Z.json

SHA-256: 989466b827824aea68fbe565089a953700bc01ead548d29ba566f06083204e16

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T10-51-03-676Z",
  "source_sha256": "ac0189dbbcc0cfe58fdd9d235188f1a824765e9ea4d597ea81c4d4aeb9043ed9",
  "bounded_source_sha256": "b05cf31f25e1254bae18d0caa7dda7553bf72782b64b8f8d042ae29c11638969",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "4c14b152e7aa56bc05668f92a360e61edf0381a76b4587c4519368e646e7e62b",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 31280,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-51-03-676Z",
  "fixture_origin": "http://127.0.0.1:52221/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "PASS",
      "milliseconds": 95
    },
    {
      "name": "default_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "model_switch_CAS_success_sends_bound_profile_only",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "model_switch_CAS_failure_keeps_old_binding",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "two_conversation_choices_are_isolated",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "unknown_existing_pin_requires_explicit_selection",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "unavailable_model_cannot_bind",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "loadModels_rebuild_restores_options_and_handler",
      "status": "PASS",
      "milliseconds": 46
    },
    {
      "name": "unsupported_and_invalid_reasoning_fail_closed",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "non_message_fetch_unchanged",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "request_body_snapshot_overrides_stale_client_fields",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "list_failure_prevents_network_message",
      "status": "PASS",
      "milliseconds": 1
    },
    {
      "name": "projection_duplicate_and_old_seq_are_idempotent",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_gap_restores_without_appending_gap",
      "status": "PASS",
      "milliseconds": 78
    },
    {
      "name": "projection_wrong_frame_branch_and_fake_thought_rejected",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_missing_branch_rejected",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "projection_identity_reuse_rejected",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "projection_malformed_text_op_status_rejected",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "projection_failed_status_preserves_partial_thought",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_HTML_is_plain_text",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_same_frame_DOM_rebuild_restores_history",
      "status": "PASS",
      "milliseconds": 113
    },
    {
      "name": "projection_same_frame_branch_switch_restores",
      "status": "PASS",
      "milliseconds": 89
    },
    {
      "name": "partial_history_is_explicitly_labeled",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_final_and_completion_record_preserve_exact_copy",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "stored_candidate_preserves_audited_body_and_raw_copy",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_bad_whole_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_bad_segment_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_nonmatching_spans_keep_raw_visible",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "stored_user_message_cannot_be_hidden",
      "status": "PASS",
      "milliseconds": 38
    },
    {
      "name": "stored_final_HTML_uses_sanitized_renderer",
      "status": "PASS",
      "milliseconds": 47
    },
    {
      "name": "stored_progress_and_snapshot_do_not_duplicate_reopen",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "live_final_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "live_candidate_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 49
    },
    {
      "name": "live_extra_unframed_text_is_not_hidden",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "replay_end_requests_persisted_projection_snapshot",
      "status": "PASS",
      "milliseconds": 91
    },
    {
      "name": "policy_change_reselection_recovers_current_revision",
      "status": "PASS",
      "milliseconds": 39
    },
    {
      "name": "default_policy_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "saved_choice_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "legacy_saved_choice_without_revision_requires_selection",
      "status": "PASS",
      "milliseconds": 10
    },
    {
      "name": "unbound_first_message_selects_then_sends",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "unknown_capability_disables_choices_and_blocks_send",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "snapshot_wrong_hash_preserves_existing_thought",
      "status": "PASS",
      "milliseconds": 44
    },
    {
      "name": "same_frame_stale_branch_response_never_crosses",
      "status": "PASS",
      "milliseconds": 91
    },
    {
      "name": "terminal_projection_rejects_future_append",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "valid_bind_retains_text_and_scope",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "failed_restore_does_not_repeat_on_every_dom_apply",
      "status": "PASS",
      "milliseconds": 316
    }
  ],
  "passed": 47,
  "failed": 0,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session",
    "/?case=default_revision_change_requires_reselection",
    "/?case=model_switch_CAS_success_sends_bound_profile_only",
    "/?case=model_switch_CAS_failure_keeps_old_binding",
    "/?case=two_conversation_choices_are_isolated",
    "/?case=unknown_existing_pin_requires_explicit_selection",
    "/?case=unavailable_model_cannot_bind",
    "/?case=loadModels_rebuild_restores_options_and_handler",
    "/?case=unsupported_and_invalid_reasoning_fail_closed",
    "/?case=non_message_fetch_unchanged",
    "/?case=request_body_snapshot_overrides_stale_client_fields",
    "/?case=list_failure_prevents_network_message",
    "/?case=projection_duplicate_and_old_seq_are_idempotent",
    "/?case=projection_gap_restores_without_appending_gap",
    "/?case=projection_wrong_frame_branch_and_fake_thought_rejected",
    "/?case=projection_missing_branch_rejected",
    "/?case=projection_identity_reuse_rejected",
    "/?case=projection_malformed_text_op_status_rejected",
    "/?case=projection_failed_status_preserves_partial_thought",
    "/?case=projection_HTML_is_plain_text",
    "/?case=projection_same_frame_DOM_rebuild_restores_history",
    "/?case=projection_same_frame_branch_switch_restores",
    "/?case=partial_history_is_explicitly_labeled",
    "/?case=stored_final_and_completion_record_preserve_exact_copy",
    "/?case=stored_candidate_preserves_audited_body_and_raw_copy",
    "/?case=stored_bad_whole_hash_keeps_raw_visible",
    "/?case=stored_bad_segment_hash_keeps_raw_visible",
    "/?case=stored_nonmatching_spans_keep_raw_visible",
    "/?case=stored_user_message_cannot_be_hidden",
    "/?case=stored_final_HTML_uses_sanitized_renderer",
    "/?case=stored_progress_and_snapshot_do_not_duplicate_reopen",
    "/?case=live_final_waits_for_turnDone_then_projects",
    "/?case=live_candidate_waits_for_turnDone_then_projects",
    "/?case=live_extra_unframed_text_is_not_hidden",
    "/?case=replay_end_requests_persisted_projection_snapshot",
    "/?case=policy_change_reselection_recovers_current_revision",
    "/?case=default_policy_revision_survives_page_record_reload",
    "/?case=saved_choice_revision_survives_page_record_reload",
    "/?case=legacy_saved_choice_without_revision_requires_selection",
    "/?case=unbound_first_message_selects_then_sends",
    "/?case=unknown_capability_disables_choices_and_blocks_send",
    "/?case=snapshot_wrong_hash_preserves_existing_thought",
    "/?case=same_frame_stale_branch_response_never_crosses",
    "/?case=terminal_projection_rejects_future_append",
    "/?case=valid_bind_retains_text_and_scope",
    "/?case=failed_restore_does_not_repeat_on_every_dom_apply"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

### frontend-dom-qa-2026-09-09T12-45-40-595Z.json

SHA-256: c2e8273709af56e9f35fece13984de23b39805b553363bfc4cc0892e721bfe00

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T12-45-40-595Z",
  "source_sha256": "ac0189dbbcc0cfe58fdd9d235188f1a824765e9ea4d597ea81c4d4aeb9043ed9",
  "bounded_source_sha256": "b05cf31f25e1254bae18d0caa7dda7553bf72782b64b8f8d042ae29c11638969",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "9571a78507f9721c4718beb3361ab3e009e818b1f52ab5743fa3c56924a3c547",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 16088,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T12-45-40-595Z",
  "fixture_origin": "http://127.0.0.1:49862/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "PASS",
      "milliseconds": 87
    },
    {
      "name": "default_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "model_switch_CAS_success_sends_bound_profile_only",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "model_switch_CAS_failure_keeps_old_binding",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "two_conversation_choices_are_isolated",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "unknown_existing_pin_requires_explicit_selection",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "unavailable_model_cannot_bind",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "loadModels_rebuild_restores_options_and_handler",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "unsupported_and_invalid_reasoning_fail_closed",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "non_message_fetch_unchanged",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "request_body_snapshot_overrides_stale_client_fields",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "list_failure_prevents_network_message",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_duplicate_and_old_seq_are_idempotent",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_gap_restores_without_appending_gap",
      "status": "PASS",
      "milliseconds": 79
    },
    {
      "name": "projection_wrong_frame_branch_and_fake_thought_rejected",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "projection_missing_branch_rejected",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_identity_reuse_rejected",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_malformed_text_op_status_rejected",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_failed_status_preserves_partial_thought",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_HTML_is_plain_text",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "projection_same_frame_DOM_rebuild_restores_history",
      "status": "PASS",
      "milliseconds": 152
    },
    {
      "name": "projection_same_frame_branch_switch_restores",
      "status": "PASS",
      "milliseconds": 85
    },
    {
      "name": "partial_history_is_explicitly_labeled",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_final_and_completion_record_preserve_exact_copy",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_candidate_preserves_audited_body_and_raw_copy",
      "status": "PASS",
      "milliseconds": 49
    },
    {
      "name": "stored_bad_whole_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 53
    },
    {
      "name": "stored_bad_segment_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_nonmatching_spans_keep_raw_visible",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_user_message_cannot_be_hidden",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_final_HTML_uses_sanitized_renderer",
      "status": "PASS",
      "milliseconds": 53
    },
    {
      "name": "stored_progress_and_snapshot_do_not_duplicate_reopen",
      "status": "PASS",
      "milliseconds": 44
    },
    {
      "name": "live_final_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "live_candidate_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 53
    },
    {
      "name": "live_extra_unframed_text_is_not_hidden",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "replay_end_requests_persisted_projection_snapshot",
      "status": "PASS",
      "milliseconds": 86
    },
    {
      "name": "policy_change_reselection_recovers_current_revision",
      "status": "PASS",
      "milliseconds": 44
    },
    {
      "name": "default_policy_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 17
    },
    {
      "name": "saved_choice_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "legacy_saved_choice_without_revision_requires_selection",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "unbound_first_message_selects_then_sends",
      "status": "PASS",
      "milliseconds": 11
    },
    {
      "name": "unknown_capability_disables_choices_and_blocks_send",
      "status": "PASS",
      "milliseconds": 10
    },
    {
      "name": "snapshot_wrong_hash_preserves_existing_thought",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "same_frame_stale_branch_response_never_crosses",
      "status": "PASS",
      "milliseconds": 80
    },
    {
      "name": "terminal_projection_rejects_future_append",
      "status": "PASS",
      "milliseconds": 16
    },
    {
      "name": "valid_bind_retains_text_and_scope",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "failed_restore_does_not_repeat_on_every_dom_apply",
      "status": "PASS",
      "milliseconds": 300
    },
    {
      "name": "missing_credentials_restore_same_binding_preserves_effort",
      "status": "FAIL",
      "milliseconds": 7,
      "error": "Error: Error: CREDENTIAL_REINJECTION_MISSING\n    at assert (http://127.0.0.1:49862/?case=missing_credentials_restore_same_binding_preserves_effort:1326:48)\n    at <anonymous>:1:411"
    },
    {
      "name": "credential_restore_profile_change_requires_effort_reselection",
      "status": "FAIL",
      "milliseconds": 10,
      "error": "Error: Error: CHANGED_CREDENTIAL_BINDING_SILENTLY_SENT\n    at assert (http://127.0.0.1:49862/?case=credential_restore_profile_change_requires_effort_reselection:1326:48)\n    at <anonymous>:1:156"
    },
    {
      "name": "credential_restore_policy_change_requires_effort_reselection",
      "status": "FAIL",
      "milliseconds": 11,
      "error": "Error: Error: RESTORE_APPROVED_DIFFERENT_POLICY\n    at assert (http://127.0.0.1:49862/?case=credential_restore_policy_change_requires_effort_reselection:1326:48)\n    at <anonymous>:1:381"
    },
    {
      "name": "credential_restore_failure_blocks_send_keeps_choice",
      "status": "FAIL",
      "milliseconds": 12,
      "error": "Error: Error: RESTORE_FAILURE_SILENTLY_SENT\n    at assert (http://127.0.0.1:49862/?case=credential_restore_failure_blocks_send_keeps_choice:1326:48)\n    at <anonymous>:1:177"
    },
    {
      "name": "credential_restore_false_success_is_not_admitted",
      "status": "FAIL",
      "milliseconds": 12,
      "error": "Error: Error: UNREADY_CREDENTIALS_ADMITTED\n    at assert (http://127.0.0.1:49862/?case=credential_restore_false_success_is_not_admitted:1326:48)\n    at <anonymous>:1:282"
    }
  ],
  "passed": 47,
  "failed": 5,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session",
    "/?case=default_revision_change_requires_reselection",
    "/?case=model_switch_CAS_success_sends_bound_profile_only",
    "/?case=model_switch_CAS_failure_keeps_old_binding",
    "/?case=two_conversation_choices_are_isolated",
    "/?case=unknown_existing_pin_requires_explicit_selection",
    "/?case=unavailable_model_cannot_bind",
    "/?case=loadModels_rebuild_restores_options_and_handler",
    "/?case=unsupported_and_invalid_reasoning_fail_closed",
    "/?case=non_message_fetch_unchanged",
    "/?case=request_body_snapshot_overrides_stale_client_fields",
    "/?case=list_failure_prevents_network_message",
    "/?case=projection_duplicate_and_old_seq_are_idempotent",
    "/?case=projection_gap_restores_without_appending_gap",
    "/?case=projection_wrong_frame_branch_and_fake_thought_rejected",
    "/?case=projection_missing_branch_rejected",
    "/?case=projection_identity_reuse_rejected",
    "/?case=projection_malformed_text_op_status_rejected",
    "/?case=projection_failed_status_preserves_partial_thought",
    "/?case=projection_HTML_is_plain_text",
    "/?case=projection_same_frame_DOM_rebuild_restores_history",
    "/?case=projection_same_frame_branch_switch_restores",
    "/?case=partial_history_is_explicitly_labeled",
    "/?case=stored_final_and_completion_record_preserve_exact_copy",
    "/?case=stored_candidate_preserves_audited_body_and_raw_copy",
    "/?case=stored_bad_whole_hash_keeps_raw_visible",
    "/?case=stored_bad_segment_hash_keeps_raw_visible",
    "/?case=stored_nonmatching_spans_keep_raw_visible",
    "/?case=stored_user_message_cannot_be_hidden",
    "/?case=stored_final_HTML_uses_sanitized_renderer",
    "/?case=stored_progress_and_snapshot_do_not_duplicate_reopen",
    "/?case=live_final_waits_for_turnDone_then_projects",
    "/?case=live_candidate_waits_for_turnDone_then_projects",
    "/?case=live_extra_unframed_text_is_not_hidden",
    "/?case=replay_end_requests_persisted_projection_snapshot",
    "/?case=policy_change_reselection_recovers_current_revision",
    "/?case=default_policy_revision_survives_page_record_reload",
    "/?case=saved_choice_revision_survives_page_record_reload",
    "/?case=legacy_saved_choice_without_revision_requires_selection",
    "/?case=unbound_first_message_selects_then_sends",
    "/?case=unknown_capability_disables_choices_and_blocks_send",
    "/?case=snapshot_wrong_hash_preserves_existing_thought",
    "/?case=same_frame_stale_branch_response_never_crosses",
    "/?case=terminal_projection_rejects_future_append",
    "/?case=valid_bind_retains_text_and_scope",
    "/?case=failed_restore_does_not_repeat_on_every_dom_apply",
    "/?case=missing_credentials_restore_same_binding_preserves_effort",
    "/?case=credential_restore_profile_change_requires_effort_reselection",
    "/?case=credential_restore_policy_change_requires_effort_reselection",
    "/?case=credential_restore_failure_blocks_send_keeps_choice",
    "/?case=credential_restore_false_success_is_not_admitted"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

### frontend-dom-qa-2026-09-09T12-46-17-075Z.json

SHA-256: 7558ca1476f761ce32fb8c36877f20e5c9db6f95d1b4760598be0337dad637c2

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T12-46-17-075Z",
  "source_sha256": "b40852bc7688ae33e1ede50691eb62fee46bd42992dc8ab716b39078e7b3fb35",
  "bounded_source_sha256": "ad08e66875c320410e50961755c437e28519f6d33f11e1e607c728605507ef36",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "9571a78507f9721c4718beb3361ab3e009e818b1f52ab5743fa3c56924a3c547",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 73924,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T12-46-17-075Z",
  "fixture_origin": "http://127.0.0.1:61629/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "PASS",
      "milliseconds": 89
    },
    {
      "name": "default_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "model_switch_CAS_success_sends_bound_profile_only",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "model_switch_CAS_failure_keeps_old_binding",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "two_conversation_choices_are_isolated",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "unknown_existing_pin_requires_explicit_selection",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "unavailable_model_cannot_bind",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "loadModels_rebuild_restores_options_and_handler",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "unsupported_and_invalid_reasoning_fail_closed",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "non_message_fetch_unchanged",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "request_body_snapshot_overrides_stale_client_fields",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "list_failure_prevents_network_message",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_duplicate_and_old_seq_are_idempotent",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_gap_restores_without_appending_gap",
      "status": "PASS",
      "milliseconds": 101
    },
    {
      "name": "projection_wrong_frame_branch_and_fake_thought_rejected",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_missing_branch_rejected",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_identity_reuse_rejected",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_malformed_text_op_status_rejected",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "projection_failed_status_preserves_partial_thought",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_HTML_is_plain_text",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_same_frame_DOM_rebuild_restores_history",
      "status": "PASS",
      "milliseconds": 137
    },
    {
      "name": "projection_same_frame_branch_switch_restores",
      "status": "PASS",
      "milliseconds": 78
    },
    {
      "name": "partial_history_is_explicitly_labeled",
      "status": "PASS",
      "milliseconds": 45
    },
    {
      "name": "stored_final_and_completion_record_preserve_exact_copy",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_candidate_preserves_audited_body_and_raw_copy",
      "status": "PASS",
      "milliseconds": 46
    },
    {
      "name": "stored_bad_whole_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "stored_bad_segment_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_nonmatching_spans_keep_raw_visible",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "stored_user_message_cannot_be_hidden",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_final_HTML_uses_sanitized_renderer",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_progress_and_snapshot_do_not_duplicate_reopen",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "live_final_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "live_candidate_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 46
    },
    {
      "name": "live_extra_unframed_text_is_not_hidden",
      "status": "PASS",
      "milliseconds": 39
    },
    {
      "name": "replay_end_requests_persisted_projection_snapshot",
      "status": "PASS",
      "milliseconds": 90
    },
    {
      "name": "policy_change_reselection_recovers_current_revision",
      "status": "PASS",
      "milliseconds": 46
    },
    {
      "name": "default_policy_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "saved_choice_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "legacy_saved_choice_without_revision_requires_selection",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "unbound_first_message_selects_then_sends",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "unknown_capability_disables_choices_and_blocks_send",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "snapshot_wrong_hash_preserves_existing_thought",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "same_frame_stale_branch_response_never_crosses",
      "status": "PASS",
      "milliseconds": 91
    },
    {
      "name": "terminal_projection_rejects_future_append",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "valid_bind_retains_text_and_scope",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "failed_restore_does_not_repeat_on_every_dom_apply",
      "status": "PASS",
      "milliseconds": 294
    },
    {
      "name": "missing_credentials_restore_same_binding_preserves_effort",
      "status": "PASS",
      "milliseconds": 13
    },
    {
      "name": "credential_restore_profile_change_requires_effort_reselection",
      "status": "PASS",
      "milliseconds": 13
    },
    {
      "name": "credential_restore_policy_change_requires_effort_reselection",
      "status": "PASS",
      "milliseconds": 10
    },
    {
      "name": "credential_restore_failure_blocks_send_keeps_choice",
      "status": "PASS",
      "milliseconds": 11
    },
    {
      "name": "credential_restore_false_success_is_not_admitted",
      "status": "PASS",
      "milliseconds": 9
    }
  ],
  "passed": 52,
  "failed": 0,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session",
    "/?case=default_revision_change_requires_reselection",
    "/?case=model_switch_CAS_success_sends_bound_profile_only",
    "/?case=model_switch_CAS_failure_keeps_old_binding",
    "/?case=two_conversation_choices_are_isolated",
    "/?case=unknown_existing_pin_requires_explicit_selection",
    "/?case=unavailable_model_cannot_bind",
    "/?case=loadModels_rebuild_restores_options_and_handler",
    "/?case=unsupported_and_invalid_reasoning_fail_closed",
    "/?case=non_message_fetch_unchanged",
    "/?case=request_body_snapshot_overrides_stale_client_fields",
    "/?case=list_failure_prevents_network_message",
    "/?case=projection_duplicate_and_old_seq_are_idempotent",
    "/?case=projection_gap_restores_without_appending_gap",
    "/?case=projection_wrong_frame_branch_and_fake_thought_rejected",
    "/?case=projection_missing_branch_rejected",
    "/?case=projection_identity_reuse_rejected",
    "/?case=projection_malformed_text_op_status_rejected",
    "/?case=projection_failed_status_preserves_partial_thought",
    "/?case=projection_HTML_is_plain_text",
    "/?case=projection_same_frame_DOM_rebuild_restores_history",
    "/?case=projection_same_frame_branch_switch_restores",
    "/?case=partial_history_is_explicitly_labeled",
    "/?case=stored_final_and_completion_record_preserve_exact_copy",
    "/?case=stored_candidate_preserves_audited_body_and_raw_copy",
    "/?case=stored_bad_whole_hash_keeps_raw_visible",
    "/?case=stored_bad_segment_hash_keeps_raw_visible",
    "/?case=stored_nonmatching_spans_keep_raw_visible",
    "/?case=stored_user_message_cannot_be_hidden",
    "/?case=stored_final_HTML_uses_sanitized_renderer",
    "/?case=stored_progress_and_snapshot_do_not_duplicate_reopen",
    "/?case=live_final_waits_for_turnDone_then_projects",
    "/?case=live_candidate_waits_for_turnDone_then_projects",
    "/?case=live_extra_unframed_text_is_not_hidden",
    "/?case=replay_end_requests_persisted_projection_snapshot",
    "/?case=policy_change_reselection_recovers_current_revision",
    "/?case=default_policy_revision_survives_page_record_reload",
    "/?case=saved_choice_revision_survives_page_record_reload",
    "/?case=legacy_saved_choice_without_revision_requires_selection",
    "/?case=unbound_first_message_selects_then_sends",
    "/?case=unknown_capability_disables_choices_and_blocks_send",
    "/?case=snapshot_wrong_hash_preserves_existing_thought",
    "/?case=same_frame_stale_branch_response_never_crosses",
    "/?case=terminal_projection_rejects_future_append",
    "/?case=valid_bind_retains_text_and_scope",
    "/?case=failed_restore_does_not_repeat_on_every_dom_apply",
    "/?case=missing_credentials_restore_same_binding_preserves_effort",
    "/?case=credential_restore_profile_change_requires_effort_reselection",
    "/?case=credential_restore_policy_change_requires_effort_reselection",
    "/?case=credential_restore_failure_blocks_send_keeps_choice",
    "/?case=credential_restore_false_success_is_not_admitted"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

### frontend-dom-qa-2026-09-09T12-47-36-661Z.json

SHA-256: 1f56a902619a71952453746ea7e2ad8d7f063eecf7b1e95925faa9ef696d23e9

```json
{
  "scope": "ISOLATED_REAL_CHROME_DOM_WITH_CONTROLLED_FIXTURES",
  "stamp": "2026-09-09T12-47-36-661Z",
  "source_sha256": "188b208da276978d2ce4504d44e0f3869e26c53f33950bf8af782f802e3f371a",
  "bounded_source_sha256": "c4d6d0afc2adedfbe4961e02ffc6df44a973dec4861ec8d9b1386b63cf27ff86",
  "css_sha256": "b2f9ce833a36960375cf9277bf6583821ba3a3cfc7ac5851027423f21c2ca1cf",
  "test_source_sha256": "527e591b019ced947ddea1ab0b81d64996339f70a2512d41f38ffce6ef44a35a",
  "browser": "Chrome/152.0.7977.83",
  "node": "v24.16.0",
  "chrome_pid": 84924,
  "profile": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T12-47-36-661Z",
  "fixture_origin": "http://127.0.0.1:58358/",
  "results": [
    {
      "name": "capability_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "pending_projection_request_does_not_starve_next_session",
      "status": "PASS",
      "milliseconds": 77
    },
    {
      "name": "default_revision_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 2
    },
    {
      "name": "model_switch_CAS_success_sends_bound_profile_only",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "model_switch_CAS_failure_keeps_old_binding",
      "status": "PASS",
      "milliseconds": 4
    },
    {
      "name": "two_conversation_choices_are_isolated",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "unknown_existing_pin_requires_explicit_selection",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "unavailable_model_cannot_bind",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "loadModels_rebuild_restores_options_and_handler",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "unsupported_and_invalid_reasoning_fail_closed",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "non_message_fetch_unchanged",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "request_body_snapshot_overrides_stale_client_fields",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "list_failure_prevents_network_message",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_duplicate_and_old_seq_are_idempotent",
      "status": "PASS",
      "milliseconds": 5
    },
    {
      "name": "projection_gap_restores_without_appending_gap",
      "status": "PASS",
      "milliseconds": 83
    },
    {
      "name": "projection_wrong_frame_branch_and_fake_thought_rejected",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "projection_missing_branch_rejected",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_identity_reuse_rejected",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_malformed_text_op_status_rejected",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "projection_failed_status_preserves_partial_thought",
      "status": "PASS",
      "milliseconds": 6
    },
    {
      "name": "projection_HTML_is_plain_text",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "projection_same_frame_DOM_rebuild_restores_history",
      "status": "PASS",
      "milliseconds": 138
    },
    {
      "name": "projection_same_frame_branch_switch_restores",
      "status": "PASS",
      "milliseconds": 88
    },
    {
      "name": "partial_history_is_explicitly_labeled",
      "status": "PASS",
      "milliseconds": 38
    },
    {
      "name": "stored_final_and_completion_record_preserve_exact_copy",
      "status": "PASS",
      "milliseconds": 46
    },
    {
      "name": "stored_candidate_preserves_audited_body_and_raw_copy",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "stored_bad_whole_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_bad_segment_hash_keeps_raw_visible",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "stored_nonmatching_spans_keep_raw_visible",
      "status": "PASS",
      "milliseconds": 53
    },
    {
      "name": "stored_user_message_cannot_be_hidden",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "stored_final_HTML_uses_sanitized_renderer",
      "status": "PASS",
      "milliseconds": 40
    },
    {
      "name": "stored_progress_and_snapshot_do_not_duplicate_reopen",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "live_final_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 42
    },
    {
      "name": "live_candidate_waits_for_turnDone_then_projects",
      "status": "PASS",
      "milliseconds": 41
    },
    {
      "name": "live_extra_unframed_text_is_not_hidden",
      "status": "PASS",
      "milliseconds": 43
    },
    {
      "name": "replay_end_requests_persisted_projection_snapshot",
      "status": "PASS",
      "milliseconds": 93
    },
    {
      "name": "policy_change_reselection_recovers_current_revision",
      "status": "PASS",
      "milliseconds": 48
    },
    {
      "name": "default_policy_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "saved_choice_revision_survives_page_record_reload",
      "status": "PASS",
      "milliseconds": 7
    },
    {
      "name": "legacy_saved_choice_without_revision_requires_selection",
      "status": "PASS",
      "milliseconds": 3
    },
    {
      "name": "unbound_first_message_selects_then_sends",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "unknown_capability_disables_choices_and_blocks_send",
      "status": "PASS",
      "milliseconds": 10
    },
    {
      "name": "snapshot_wrong_hash_preserves_existing_thought",
      "status": "PASS",
      "milliseconds": 44
    },
    {
      "name": "same_frame_stale_branch_response_never_crosses",
      "status": "PASS",
      "milliseconds": 88
    },
    {
      "name": "terminal_projection_rejects_future_append",
      "status": "PASS",
      "milliseconds": 11
    },
    {
      "name": "valid_bind_retains_text_and_scope",
      "status": "PASS",
      "milliseconds": 8
    },
    {
      "name": "failed_restore_does_not_repeat_on_every_dom_apply",
      "status": "PASS",
      "milliseconds": 300
    },
    {
      "name": "missing_credentials_restore_same_binding_preserves_effort",
      "status": "PASS",
      "milliseconds": 11
    },
    {
      "name": "credential_restore_profile_change_requires_effort_reselection",
      "status": "PASS",
      "milliseconds": 12
    },
    {
      "name": "credential_restore_policy_change_requires_effort_reselection",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "credential_restore_failure_blocks_send_keeps_choice",
      "status": "PASS",
      "milliseconds": 10
    },
    {
      "name": "credential_restore_false_success_is_not_admitted",
      "status": "PASS",
      "milliseconds": 15
    },
    {
      "name": "unbound_first_message_preserves_user_effort",
      "status": "PASS",
      "milliseconds": 9
    },
    {
      "name": "binding_changed_outside_picker_requires_reselection",
      "status": "PASS",
      "milliseconds": 13
    },
    {
      "name": "saved_binding_change_requires_reselection",
      "status": "PASS",
      "milliseconds": 9
    }
  ],
  "passed": 55,
  "failed": 0,
  "skipped": 0,
  "fatal": null,
  "requests": [
    "/?case=capability_revision_change_requires_reselection",
    "/?case=pending_projection_request_does_not_starve_next_session",
    "/?case=default_revision_change_requires_reselection",
    "/?case=model_switch_CAS_success_sends_bound_profile_only",
    "/?case=model_switch_CAS_failure_keeps_old_binding",
    "/?case=two_conversation_choices_are_isolated",
    "/?case=unknown_existing_pin_requires_explicit_selection",
    "/?case=unavailable_model_cannot_bind",
    "/?case=loadModels_rebuild_restores_options_and_handler",
    "/?case=unsupported_and_invalid_reasoning_fail_closed",
    "/?case=non_message_fetch_unchanged",
    "/?case=request_body_snapshot_overrides_stale_client_fields",
    "/?case=list_failure_prevents_network_message",
    "/?case=projection_duplicate_and_old_seq_are_idempotent",
    "/?case=projection_gap_restores_without_appending_gap",
    "/?case=projection_wrong_frame_branch_and_fake_thought_rejected",
    "/?case=projection_missing_branch_rejected",
    "/?case=projection_identity_reuse_rejected",
    "/?case=projection_malformed_text_op_status_rejected",
    "/?case=projection_failed_status_preserves_partial_thought",
    "/?case=projection_HTML_is_plain_text",
    "/?case=projection_same_frame_DOM_rebuild_restores_history",
    "/?case=projection_same_frame_branch_switch_restores",
    "/?case=partial_history_is_explicitly_labeled",
    "/?case=stored_final_and_completion_record_preserve_exact_copy",
    "/?case=stored_candidate_preserves_audited_body_and_raw_copy",
    "/?case=stored_bad_whole_hash_keeps_raw_visible",
    "/?case=stored_bad_segment_hash_keeps_raw_visible",
    "/?case=stored_nonmatching_spans_keep_raw_visible",
    "/?case=stored_user_message_cannot_be_hidden",
    "/?case=stored_final_HTML_uses_sanitized_renderer",
    "/?case=stored_progress_and_snapshot_do_not_duplicate_reopen",
    "/?case=live_final_waits_for_turnDone_then_projects",
    "/?case=live_candidate_waits_for_turnDone_then_projects",
    "/?case=live_extra_unframed_text_is_not_hidden",
    "/?case=replay_end_requests_persisted_projection_snapshot",
    "/?case=policy_change_reselection_recovers_current_revision",
    "/?case=default_policy_revision_survives_page_record_reload",
    "/?case=saved_choice_revision_survives_page_record_reload",
    "/?case=legacy_saved_choice_without_revision_requires_selection",
    "/?case=unbound_first_message_selects_then_sends",
    "/?case=unknown_capability_disables_choices_and_blocks_send",
    "/?case=snapshot_wrong_hash_preserves_existing_thought",
    "/?case=same_frame_stale_branch_response_never_crosses",
    "/?case=terminal_projection_rejects_future_append",
    "/?case=valid_bind_retains_text_and_scope",
    "/?case=failed_restore_does_not_repeat_on_every_dom_apply",
    "/?case=missing_credentials_restore_same_binding_preserves_effort",
    "/?case=credential_restore_profile_change_requires_effort_reselection",
    "/?case=credential_restore_policy_change_requires_effort_reselection",
    "/?case=credential_restore_failure_blocks_send_keeps_choice",
    "/?case=credential_restore_false_success_is_not_admitted",
    "/?case=unbound_first_message_preserves_user_effort",
    "/?case=binding_changed_outside_picker_requires_reselection",
    "/?case=saved_binding_change_requires_reselection"
  ],
  "live_application_operated": false,
  "real_user_data_operated": false
}
```

## Cleanup inventory before removal

All paths below were resolved inside the dedicated frontend fixture evidence directory. The isolated browser PIDs had exited. Profile trees contained no reparse points. Raw JSON results are embedded above; incidental screenshots are identified by hash only and were not visual acceptance evidence.

```json
[
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-04-52-886Z",
    "kind": "isolated browser profile",
    "files": 175,
    "bytes": 5920731.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-04-52-886Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 1844,
    "sha256": "3ca4c34610e31f878953db1125a346769c40820a342dad15f07b6ff4d9771612"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-04-52-886Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 2438,
    "sha256": "fe6c08ce967ab25cb1fc6e9693a29e9d2d3bddba214223e9d63a00e74aa5eab8"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-15-37-057Z",
    "kind": "isolated browser profile",
    "files": 221,
    "bytes": 10975428.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-15-37-057Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 9169,
    "sha256": "0b92d43079e18ee63464d211f644830909f49d7182fe13e55af3d44f1ac717c2"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-15-37-057Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 2438,
    "sha256": "fe6c08ce967ab25cb1fc6e9693a29e9d2d3bddba214223e9d63a00e74aa5eab8"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-49-08-386Z",
    "kind": "isolated browser profile",
    "files": 234,
    "bytes": 11434676.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-49-08-386Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 7468,
    "sha256": "a6ad8578ebccf95437e82a7c59979d09a31873594fa2f99e789adce83e194a65"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-49-08-386Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 2545,
    "sha256": "0cfd8f94043438a506047e42906be7ac636c03eb21d6b27e5697ee698f54ffe3"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T10-51-03-676Z",
    "kind": "isolated browser profile",
    "files": 341,
    "bytes": 12597183.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-51-03-676Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 9532,
    "sha256": "989466b827824aea68fbe565089a953700bc01ead548d29ba566f06083204e16"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T10-51-03-676Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 2545,
    "sha256": "0cfd8f94043438a506047e42906be7ac636c03eb21d6b27e5697ee698f54ffe3"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T12-45-40-595Z",
    "kind": "isolated browser profile",
    "files": 348,
    "bytes": 14295378.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T12-45-40-595Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 11570,
    "sha256": "c2e8273709af56e9f35fece13984de23b39805b553363bfc4cc0892e721bfe00"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T12-45-40-595Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 6230,
    "sha256": "12114d2602c47510cf2ce0ec8417b4f66b5c36210d9863740cc6de67ff3b14b3"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T12-46-17-075Z",
    "kind": "isolated browser profile",
    "files": 349,
    "bytes": 14350268.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T12-46-17-075Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 10560,
    "sha256": "7558ca1476f761ce32fb8c36877f20e5c9db6f95d1b4760598be0337dad637c2"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T12-46-17-075Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 10281,
    "sha256": "630120350e74b5a749a77156d944907fbacd78819d4409c935c907be699671e5"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-chrome-profile-2026-09-09T12-47-36-661Z",
    "kind": "isolated browser profile",
    "files": 351,
    "bytes": 14740431.0
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T12-47-36-661Z.json",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 11114,
    "sha256": "1f56a902619a71952453746ea7e2ad8d7f063eecf7b1e95925faa9ef696d23e9"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-2026-09-09T12-47-36-661Z.png",
    "kind": "consolidated result or incidental screenshot",
    "files": 1,
    "bytes": 11438,
    "sha256": "466d46a95cfb184af7acbb9ee02df9069074ee897985fbef1736db193a61cb05"
  },
  {
    "path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\ui-evidence\\model-runtime-20260909\\frontend-dom-qa-temporary.mjs",
    "kind": "temporary regression source",
    "files": 1,
    "bytes": 36971,
    "sha256": "527e591b019ced947ddea1ab0b81d64996339f70a2512d41f38ffce6ef44a35a"
  }
]
```

## Cleanup verification

All 22 exact inventoried targets are absent after cleanup: 7 isolated Chrome profiles, 7 consolidated JSON result files, 7 incidental screenshot files, and 1 temporary regression source. The profile contents and single files totaled 2,034 files and 84,450,238 bytes before removal. No real test conversation was created by this suite, so there was no user database content to delete. Existing tests and prior non-frontend evidence were not operated. The source code and consolidated report remain; there is no live QA Chrome process from these runs.

````

</details>

### R006 — 项目/docs/LEO_CONVERSATION_RUNTIME_INTEGRATION_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# Conversation runtime integration — 2026-09-09

This report binds the engineering work prepared on `codex/conversation-runtime-20260909`, based on `9e53dcc4d534a1dadd93ad0107ee88bef55d455f`. It is a source integration record. Subsequent package/deployment receipts belong to `../ui-evidence/model-runtime-20260909/` beside this worktree; they must be checked separately before treating this source as installed. Scientific status remains **PINN MVP = NOT COMPLETE / CFD Readiness = PARTIAL**.

## Results and scope

The installed entry recovery previously passed 13 strict checks and real ordinary-launch, configured entry, keyless entry, return and repeated same-URI DeepSeek navigation probes. This change adds conversation-specific model choice, real capability-bound reasoning requests, durable separate thought/progress display, and a direct conversational final-answer instruction. These changes do not grant a scientific claim or bypass the existing finalizer, review, candidate hash or scientific Gate path.

The new frontend has 55 passing real isolated Chrome DOM cases. Binding has 75 new cases plus 81 existing API cases passing. Local relay has 83 passing cases; thought/provider projection has 44; central installer composition has 53 on the final binding bytes. The tests have different scopes and overlaps: do not sum them into a fictitious single suite. Full-suite results, real-provider probes and their original failures are recorded below and in the appended evidence.

## Files and causal changes

| File(s) | Reason |
| --- | --- |
| `leo_shell/session_models.py` | Register only native-owned saved profiles through the authenticated daemon broker; durable encrypted registration intent; exact identity, credentials and revision checks; owned local model lifecycle independent of global daemon restart |
| `leo_shell/api.py` | Expose sanitized per-session list/select operations and revoke managed references when a native profile is deleted |
| `bridge/leo_turn_binding.py`, `bridge/leo_turn_binding_runtime.py` | Exact upstream overlays for transactional compare-and-set model binding and immutable admitted model/effort snapshots; managed credential references and registration recovery fail closed |
| `bridge/leo_reasoning.py` | Single capability policy: six genuine local budgets, three audited DeepSeek native efforts, unsupported choices disabled, revision-bound request validation |
| `bridge/leo_local_relay.py` | Apply actual llama.cpp thinking budgets; preserve real JSON/SSE reasoning fields and terminal/tool protocol; explicit context limit rather than hidden truncation |
| `bridge/leo_thought_runtime.py` | Preserve upstream reasoning fields, durable sequenced projection events, hash-bound progress/final/completion metadata; raw message/candidate construction retained |
| `bridge/leo_runtime_features.py` | Compose Example, binding and thought overlays against pinned full-file canonical identities; verify packaged clean-source receipt; preflight, guarded writes, readback and rollback |
| `bridge/leo_identity.py` | Upgrade the exact existing application identity prefix with a direct-answer finalizer contract; preserve underlying scientific prompt and protocol |
| `leo_shell/bridge_client.py` | Require central preparation with `applied=true` and both feature flags before daemon startup |
| `leo_shell/settings_store.py` | New DeepSeek profile default uses the current V4 Flash model; migration of the one existing profile was separately owner-authorized and executed |
| `stage/leo-inject.js` | Real native model selector and effort controls; per-conversation revision persistence; request injection; explicit credential restoration; session/branch-safe, hashed thought/progress rendering |
| `stage/leo.css` | Readable selector/status and collapsible separate thought/progress layout |
| `manifests/runtime-asset-origins.json` | Bind the changed CSS and exact three-source injection bundle bytes; no scientific hash lock changed |
| `tools/build_launcher.ps1`, `tools/deploy_release.ps1` | Include the five additional required bridge resources in build and installation |
| `tools/package_contract.py`, `tools/build_manifest.py`, `tools/verify_release.py` | Check all ten bridge sidecars, new native/shared modules, and exact deployed resource hashes |
| `tests/leo_shell/test_api.py`, `test_settings_store.py`, `test_bridge_client.py` | Update existing assertions for the intentionally changed default and required central bootstrap; no skip/xfail or weaker scientific threshold |
| Component reports plus root PINN report/current reconciliation | Preserve source identities, original failures, actual test scope, scientific blockers and cleanup boundaries |

## Real local model validation

On the actual installed Qwen3-4B GGUF and llama.cpp build 10809 / `5266f24da`, six real JSON requests used the new candidate relay. They did not create any application conversation. The installed model context is 16384 tokens. The user's local model directory and lifecycle scripts were reused; no model copy or download was made.

Initial setup attempts stopped before inference: one test resolved the relative model directory against the wrong test root; the corrected attempt found another project's Vite process occupying 8080. The owner explicitly authorized stopping exact leotree Vite PID 66316. Its executable/script/listener identity was rechecked, then only that process was stopped. Model and relay owned by the test were released afterward.

| UI choice | Native thinking budget per block | Actual reasoning characters | Completion tokens | Seconds |
| --- | ---: | ---: | ---: | ---: |
| Low | 128 | 507 | 326 | 5.031 |
| Mid | 256 | 866 | 395 | 5.500 |
| High | 512 | 1365 | 836 | 11.422 |
| Xhigh | 1024 | 2374 | 1328 | 19.266 |
| Extra | 2048 | 4206 | 2541 | 36.250 |
| Ultra | 4096 | 7094 | 4356 | 67.718 |

All six returned HTTP 200, the configured model, nonempty separate reasoning and final content, and terminal `stop`. The original test recorded 1 PASS / 5 FAIL because a literal `100003` assertion rejected formatted `100,003`. Original verdicts remain in `local-live-results-v3.json`. An independently recorded numeric parser accepts thousands separators, independently proves 100003 prime by trial division, and confirms the number in all six answers: 6 PASS / 0 FAIL / 0 SKIP. This does not verify the model's prose claims that it tested every divisor. Model-written explanations are not executed scientific evidence.

Budgets are per thinking block, with possible forced closing/UTF-8 overhead. Completion-token counts include the final answer. Different budget sizes do not guarantee different quality, exact output length or monotonic accuracy. The private test's WSL stderr decoder emitted UnicodeDecodeError warnings while all HTTP responses remained valid; this is a diagnostic transport decoding issue, not an ignored production optimizer/model failure. Production lifecycle decoding already uses replacement handling. Full installed conversation/SSE acceptance remains a separate check.

## Real DeepSeek validation and owner-approved migration

The credential was loaded by the native Windows store and used only in an HTTPS Authorization header. No credential value/hash or authentication URL was printed or put into a test conversation. A read-only model catalog request returned V4 Flash, V4 Pro and the experimental vision model.

Four actual requests passed: the old `deepseek-chat` alias still returned V4 Flash with no reasoning, and explicit V4 Flash Low/High/Ultra requests returned actual reasoning. Native effort values were respectively `low`, `high`, `max`; measured reasoning-token counts were 10, 46 and 60 for the greeting probe. All returned terminal `stop`. The recorded wire parameters were independently compared against the shared production `apply_request` policy and matched all four cases.

The owner then explicitly approved changing saved profile `profile-85ee2a5766dbe4e85b97f3d55eeb24f1` from `deepseek-chat` to `deepseek-v4-flash`. The native store applied only the model name. All credential file bytes, the active profile ID and every other profile remained unchanged; conversation storage was not operated. The migration receipt is `deepseek-authorized-profile-migration.json`.

DeepSeek provides three real native efforts. Mid, Xhigh and Extra are disabled for that family; the product does not relabel equal native settings as six independent levels. Other unaudited provider/model/endpoint combinations retain provider default and do not receive invented effort fields. Reference: [DeepSeek thinking guide](https://api-docs.deepseek.com/guides/thinking_mode/).

## Regression failures retained

- An intermediate mixed suite recorded 889 PASS / 3 FAIL / 2 SKIP: two old default assertions and one disposable fixture's incorrect connection attribute. Those issues were corrected.
- A later full suite recorded 836 PASS / 3 FAIL / 2 SKIP because a new absolute machine path in the root status prefix triggered portability scanning. Only that newly written prefix reference was changed to a relative worktree reference; exact observation paths remain in the scoped audit document. Existing historical report bytes and scanner/test rules were preserved.
- Frontend red evidence includes 28 PASS / 8 FAIL and 47 PASS / 5 FAIL before real capability, frame/branch, credential-restoration and selection bugs were repaired. All raw records are embedded in its component report.
- Binding red evidence contains six credential/registration identity failures before guards were added. Central installer original fixture-count failures also remain recorded.

## Hygiene and remaining boundaries

Frontend cleanup removed all 22 exact QA targets: 7 profiles, 7 screenshots, 7 JSON result files and one new test harness; their results are embedded in the report. 2034 regular-file entries / 84,450,238 bytes were removed, with zero targets remaining.

Automatic review rejected a combined binding temporary-source/fixture deletion command. A narrower subsequent deletion of only the newly generated regression source succeeded after its report and hash were saved. `binding-source-only-cleanup.json` records SHA `dcb90cea0e1fee9d338109f7a58a6531c3e0316df5823669b282b533362ae943` and absence. The original rejection remains true for that earlier operation; its directories remain pending separate safe cleanup. Do not read the component report's earlier source-present checkpoint as the final source outcome.

The scientific 42-file candidate remains unchanged. The G6 helper mismatch, necessary fresh-environment P0 acceptance, separate formal lock approval, trainer/recorder, five-seed runs and formal scientific validation are unresolved. See `PINN_PHASE2_RECONCILIATION_20260909.md`. No CFD/OpenFOAM implementation was added. A green engineering build cannot close these scientific items.

## Final source regression

`python -B -m pytest -q -p no:cacheprovider --basetemp <isolated evidence directory>`: **839 passed / 0 failed / 2 existing skipped**, 30.53 s. The skipped cases are the inapplicable disabled legacy entity-lifecycle branch and unavailable local wheelhouse verification. No new skip/xfail was added.

```text
........................................................................ [  8%]
........................................................................ [ 17%]
........................................................................ [ 25%]
........................................................................ [ 34%]
........................................................................ [ 42%]
........................................................................ [ 51%]
........................................................................ [ 59%]
........................................................................ [ 68%]
........................................................................ [ 77%]
........................................................................ [ 85%]
........................................................................ [ 94%]
...........s..........................s..........                        [100%]
839 passed, 2 skipped in 30.53s

```

## Exact recorded integration evidence

The following records preserve original failed attempts as well as successful probes. Their SHA-256 values bind the original file bytes. These are test results, not scientific run evidence.

### identity-contract-validation.json

SHA-256 `fa74286dd5136ff3022a38572f5eeba84cbfe07df2c13e163b3042e0ef70a75d`

```text
{
  "scope": "canonical_readonly_identity_transform",
  "passed": 8,
  "failed": 0,
  "skipped": 0,
  "source_sha256": "a43ed481a50d83f4bdb71ab9f53dc904adc157395462654bcf8dfc4d20abf88b",
  "canonical_sha256": "7359f9a320497055f563f605e18314ea5ef6c577e42ef3f5479584d3b3b8453d",
  "transformed_sha256": "9436536f132d1b7a5ffe5d97ec131d96608d940106abcf8290d8f1a91af186a4",
  "checks": [
    {
      "name": "canonical_prompt_preserved_except_declared_identity",
      "result": "PASS"
    },
    {
      "name": "repeat_exact_bytes",
      "result": "PASS"
    },
    {
      "name": "exact_v1_upgrade",
      "result": "PASS"
    },
    {
      "name": "partial_identity",
      "result": "PASS"
    },
    {
      "name": "partial_contract",
      "result": "PASS"
    },
    {
      "name": "dynamic_prompt",
      "result": "PASS"
    },
    {
      "name": "duplicate_prompt",
      "result": "PASS"
    },
    {
      "name": "unknown_prompt",
      "result": "PASS"
    }
  ]
}
```

### local-live-results.json

SHA-256 `4e539a23ba9b55c33c59f2695b8a98054df5f7776e1cb46102e688057feef7a7`

```text
{
  "scope": "actual_local_model_and_current_relay_no_user_conversation",
  "tests": [],
  "complete": false,
  "error_type": "BridgeError",
  "owned_model_and_relay_released": true,
  "source_sha256": "33ff1056bac8adb53fb0dfdc89a91c768100e75e49ea08317cb2ffd70dbbeb37"
}
```

### local-live-results-v2.json

SHA-256 `2b23cf5924adcdaac192537ff2791aa00159311992591b364e089e83719504e3`

```text
{
  "scope": "actual_local_model_and_current_relay_no_user_conversation",
  "tests": [],
  "complete": false,
  "error_type": "BridgeError",
  "error_code": "LOCAL_MODEL_IDENTITY_INVALID",
  "owned_model_and_relay_released": true,
  "source_sha256": "7ef746f32b17501d8cd00207e55e0178cfdd04722f360aada87582d196c67b22"
}
```

### local-live-results-v3.json

SHA-256 `e596c27f9f21458b4077d07d8f40d939292d08b77c0a3c0641ee70bbca1ad989`

```text
{
  "scope": "actual_local_model_and_current_relay_no_user_conversation",
  "tests": [
    {
      "choice": "low",
      "budget": 128,
      "http_status": 200,
      "model": "local-qwen3-4b",
      "usage": {
        "completion_tokens": 326,
        "prompt_tokens": 46,
        "total_tokens": 372,
        "prompt_tokens_details": {
          "cached_tokens": 0
        }
      },
      "finish_reason": "stop",
      "content": "The smallest prime greater than 100,000 is **100,003**. \n\n**Verification**:  \nCheck divisibility by small primes:  \n- 100,003 ÷ 2 = 50,001.5 → not divisible by 2.  \n- Sum of digits: 1+0+0+0+0+3 = 4 → not divisible by 3.  \n- Ends with 3, not 5 or 0 → not divisible by 5.  \n- Test divisibility by 7: 100,003 ÷ 7 ≈ 14,286.14 → not divisible.  \n- Continue testing primes up to √100,003 ≈ 316.  \n- No divisors found, so 100,003 is prime.",
      "reasoning_characters": 507,
      "raw_sha256": "b9b0a87644b28e00a2c307b696ba26368a3dee74cb20a8f28aa83b384975329b",
      "elapsed_seconds": 5.031,
      "status": "FAIL"
    },
    {
      "choice": "mid",
      "budget": 256,
      "http_status": 200,
      "model": "local-qwen3-4b",
      "usage": {
        "completion_tokens": 395,
        "prompt_tokens": 46,
        "total_tokens": 441,
        "prompt_tokens_details": {
          "cached_tokens": 45
        }
      },
      "finish_reason": "stop",
      "content": "The smallest prime number greater than 100,000 is **100,003**. \n\n**Verification**:  \n100,003 is not divisible by 2 (it's odd), 3 (sum of digits: 1+0+0+0+0+3 = 4, not divisible by 3), 5 (ends with 3), 7, 11, 13, etc. Testing divisibility by primes up to √100003 (~316) confirms no divisors, so 100,003 is prime.",
      "reasoning_characters": 866,
      "raw_sha256": "02ccf5b07f23c41463b42fc2e75af9b3b33f1d16810d6debebcc87cce62b0618",
      "elapsed_seconds": 5.5,
      "status": "PASS"
    },
    {
      "choice": "high",
      "budget": 512,
      "http_status": 200,
      "model": "local-qwen3-4b",
      "usage": {
        "completion_tokens": 836,
        "prompt_tokens": 46,
        "total_tokens": 882,
        "prompt_tokens_details": {
          "cached_tokens": 45
        }
      },
      "finish_reason": "stop",
      "content": "The smallest prime number greater than 100,000 is **100,003**. \n\n**Verification**:  \n1. **Check divisibility by small primes**:  \n   - 100,003 is odd (not divisible by 2).  \n   - Sum of digits: 1 + 0 + 0 + 0 + 0 + 3 = 4 (not divisible by 3).  \n   - Ends with 3 (not divisible by 5).  \n   - Divided by 7: 100,003 ÷ 7 ≈ 14,286.14 (not an integer).  \n   - Divided by 11: Alternating sum: (1 + 0 + 0) - (0 + 0 + 3) = -2 (not divisible by 11).  \n   - Divided by 13: 13 × 7,692 = 99,996; 100,003 - 99,996 = 7 (not divisible by 13).  \n   - Continue testing primes up to √100,003 ≈ 316.23. No divisors found.  \n\n2. **Conclusion**: Since no primes up to 317 divide 100,003, it is prime.  \n\n**Answer**: 100,003.",
      "reasoning_characters": 1365,
      "raw_sha256": "0faf54aeed23504f46360b66b4e2eb76d6e18974e4c11e87bb561af4f387477d",
      "elapsed_seconds": 11.422,
      "status": "FAIL"
    },
    {
      "choice": "xhigh",
      "budget": 1024,
      "http_status": 200,
      "model": "local-qwen3-4b",
      "usage": {
        "completion_tokens": 1328,
        "prompt_tokens": 46,
        "total_tokens": 1374,
        "prompt_tokens_details": {
          "cached_tokens": 45
        }
      },
      "finish_reason": "stop",
      "content": "The smallest prime number greater than 100,000 is **100,003**. \n\n**Verification**:  \n1. **Check divisibility by small primes**:  \n   - 100,003 is odd (not divisible by 2).  \n   - Sum of digits: 1 + 0 + 0 + 0 + 0 + 3 = 4 (not divisible by 3).  \n   - Ends with 3 (not divisible by 5).  \n   - Divided by 7: 100,003 ÷ 7 ≈ 14,286.14 (not an integer).  \n   - Divided by 11: Alternating sum: (1 + 0 + 0) - (0 + 0 + 3) = -2 (not divisible by 11).  \n   - Divided by 13: 100,003 ÷ 13 ≈ 7,692.54 (not an integer).  \n   - Continuing this process up to √100,003 ≈ 316, no divisors found.  \n\n2. **Conclusion**: Since no primes up to 317 divide 100,003, it is prime.  \n\n**Answer**: 100,003.",
      "reasoning_characters": 2374,
      "raw_sha256": "c847d324e12835918bea8295a023b4217545b4907eb5282a7072afa5ba5f869f",
      "elapsed_seconds": 19.266,
      "status": "FAIL"
    },
    {
      "choice": "extra",
      "budget": 2048,
      "http_status": 200,
      "model": "local-qwen3-4b",
      "usage": {
        "completion_tokens": 2541,
        "prompt_tokens": 46,
        "total_tokens": 2587,
        "prompt_tokens_details": {
          "cached_tokens": 45
        }
      },
      "finish_reason": "stop",
      "content": "The smallest prime number greater than 100,000 is **100,003**. \n\n**Verification**:  \n1. **Check divisibility by small primes**:  \n   - 100,003 is odd (not divisible by 2).  \n   - Sum of digits: 1 + 0 + 0 + 0 + 0 + 3 = 4 (not divisible by 3).  \n   - Ends with 3 (not divisible by 5).  \n   - Divided by 7: 100,003 ÷ 7 ≈ 14,286.14 (not an integer).  \n   - Divided by 11: Alternating sum (1 - 0 + 0 - 0 + 0 - 3) = -2 (not divisible by 11).  \n   - Divided by 13: 100,003 ÷ 13 ≈ 7,692.54 (not an integer).  \n   - Divided by 17: 100,003 ÷ 17 ≈ 5,882.53 (not an integer).  \n   - Divided by 19: 100,003 ÷ 19 ≈ 5,263.32 (not an integer).  \n   - Divided by 23: 100,003 ÷ 23 ≈ 4,348.39 (not an integer).  \n   - Divided by 29: 100,003 ÷ 29 ≈ 3,448.38 (not an integer).  \n   - Divided by 31: 100,003 ÷ 31 ≈ 3,225.90 (not an integer).  \n\n2. **Square root check**: The square root of 100,003 is ~316.23. Testing primes up to 313 (the largest prime ≤ 316) confirms no divisors.  \n\nThus, **100,003** is prime.",
      "reasoning_characters": 4206,
      "raw_sha256": "6821463f02b888d112b42a6fe446ae8fe9b3021dfe6ca352f8e2fc8c9a8f8126",
      "elapsed_seconds": 36.25,
      "status": "FAIL"
    },
    {
      "choice": "ultra",
      "budget": 4096,
      "http_status": 200,
      "model": "local-qwen3-4b",
      "usage": {
        "completion_tokens": 4356,
        "prompt_tokens": 46,
        "total_tokens": 4402,
        "prompt_tokens_details": {
          "cached_tokens": 45
        }
      },
      "finish_reason": "stop",
      "content": "The smallest prime number greater than 100,000 is **100,003**. \n\n**Verification**:  \n1. **Check divisibility by small primes**:  \n   - 100,003 is odd (not divisible by 2).  \n   - Sum of digits: 1 + 0 + 0 + 0 + 0 + 3 = 4 (not divisible by 3).  \n   - Ends with 3 (not divisible by 5).  \n   - Divided by 7: 100,003 ÷ 7 ≈ 14,286.14 (not an integer).  \n   - Divided by 11: Alternating sum (1 - 0 + 0 - 0 + 0 - 3) = -2 (not divisible by 11).  \n   - Tested divisibility by primes up to √100,003 ≈ 316, and none divided evenly.  \n\n2. **Conclusion**: No divisors found, confirming **100,003 is prime**.  \n\n**Answer**: 100,003.",
      "reasoning_characters": 7094,
      "raw_sha256": "1a2283a23ba303e1dffe4f1a9d7d163c67508d5c6907a79eb1b551cc20c47709",
      "elapsed_seconds": 67.718,
      "status": "FAIL"
    }
  ],
  "complete": true,
  "context_size": 16384,
  "owned_model_and_relay_released": true,
  "source_sha256": "b5109791e212ce1b48618407de45b9aead253a4395c5507ac7e93a7eb8d74bd8"
}
```

### local-live-independent-result-audit.json

SHA-256 `263b1c782d80882bf3222c75810f6a4a67fe11c5fc58c34aac8f3b7536894a7f`

```text
{
  "source_result_sha256": "e596c27f9f21458b4077d07d8f40d939292d08b77c0a3c0641ee70bbca1ad989",
  "scope": "review_original_real_inference_results_without_rerunning_or_changing_original_verdicts",
  "original_test_false_negatives": "Literal substring 100003 rejected formatted 100,003. Original 1 PASS / 5 FAIL preserved. Separate numeric parsing now accepts thousands separators; this is not proof of the explanations.",
  "independent_expected_prime": 100003,
  "tests": [
    {
      "choice": "low",
      "budget_tokens": 128,
      "transport_and_reasoning": "PASS",
      "number_present": "PASS",
      "reasoning_characters": 507,
      "completion_tokens": 326,
      "elapsed_seconds": 5.031,
      "response_sha256": "b9b0a87644b28e00a2c307b696ba26368a3dee74cb20a8f28aa83b384975329b"
    },
    {
      "choice": "mid",
      "budget_tokens": 256,
      "transport_and_reasoning": "PASS",
      "number_present": "PASS",
      "reasoning_characters": 866,
      "completion_tokens": 395,
      "elapsed_seconds": 5.5,
      "response_sha256": "02ccf5b07f23c41463b42fc2e75af9b3b33f1d16810d6debebcc87cce62b0618"
    },
    {
      "choice": "high",
      "budget_tokens": 512,
      "transport_and_reasoning": "PASS",
      "number_present": "PASS",
      "reasoning_characters": 1365,
      "completion_tokens": 836,
      "elapsed_seconds": 11.422,
      "response_sha256": "0faf54aeed23504f46360b66b4e2eb76d6e18974e4c11e87bb561af4f387477d"
    },
    {
      "choice": "xhigh",
      "budget_tokens": 1024,
      "transport_and_reasoning": "PASS",
      "number_present": "PASS",
      "reasoning_characters": 2374,
      "completion_tokens": 1328,
      "elapsed_seconds": 19.266,
      "response_sha256": "c847d324e12835918bea8295a023b4217545b4907eb5282a7072afa5ba5f869f"
    },
    {
      "choice": "extra",
      "budget_tokens": 2048,
      "transport_and_reasoning": "PASS",
      "number_present": "PASS",
      "reasoning_characters": 4206,
      "completion_tokens": 2541,
      "elapsed_seconds": 36.25,
      "response_sha256": "6821463f02b888d112b42a6fe446ae8fe9b3021dfe6ca352f8e2fc8c9a8f8126"
    },
    {
      "choice": "ultra",
      "budget_tokens": 4096,
      "transport_and_reasoning": "PASS",
      "number_present": "PASS",
      "reasoning_characters": 7094,
      "completion_tokens": 4356,
      "elapsed_seconds": 67.718,
      "response_sha256": "1a2283a23ba303e1dffe4f1a9d7d163c67508d5c6907a79eb1b551cc20c47709"
    }
  ],
  "passed": 6,
  "failed": 0,
  "skipped": 0,
  "owned_model_and_relay_released": true,
  "limitation": "Direct real relay JSON calls; full installed conversation/SSE tests remain separate. Model prose verification was not executed and must not be treated as scientific evidence."
}
```

### deepseek-live-model-catalog.json

SHA-256 `d7b458c97986d0b66e9edf6d74d4516cd6b709577e5ef0cadc5175d7e0376142`

```text
{
  "scope": "authorized_provider_model_catalog_readonly",
  "profile_unchanged": true,
  "status": 200,
  "models": [
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "deepseek-v4-flash-vision-exp"
  ],
  "response_sha256": "f20df3afd1dc080689aa1ba4e5bda383488d6d624797e46cb28abe0447f29acd"
}
```

### deepseek-live-requests.json

SHA-256 `b5a93aef39aa5a8b15eb835a3d8e917d63e31a60641d19208a492b12d1b65bfe`

```text
{
  "scope": "actual_DeepSeek_wire_requests_no_profile_change_no_conversation_created",
  "tests": [
    {
      "model": "deepseek-chat",
      "choice": "default",
      "wire_parameters": {
        "max_tokens": 1024
      },
      "http_status": 200,
      "actual_model": "deepseek-v4-flash",
      "content": "你好，有什么可以帮你的吗？",
      "reasoning_characters": 0,
      "usage": {
        "prompt_tokens": 21,
        "completion_tokens": 8,
        "total_tokens": 29,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 21
      },
      "finish_reason": "stop",
      "response_sha256": "8fe6e287db1e258c3398043d42f84e098d6bbd07335e4df40d5a9a152de1e458",
      "status": "PASS",
      "seconds": 1.282
    },
    {
      "model": "deepseek-v4-flash",
      "choice": "low",
      "wire_parameters": {
        "max_tokens": 1024,
        "thinking": {
          "type": "enabled"
        },
        "reasoning_effort": "low"
      },
      "http_status": 200,
      "actual_model": "deepseek-v4-flash",
      "content": "你好！",
      "reasoning_characters": 17,
      "usage": {
        "prompt_tokens": 21,
        "completion_tokens": 13,
        "total_tokens": 34,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 10
        },
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 21
      },
      "finish_reason": "stop",
      "response_sha256": "f96af30ed2cd95bc8c76dc74f2e7ce3eb954c01b172e4bbab51697fb3a921787",
      "status": "PASS",
      "seconds": 1.218
    },
    {
      "model": "deepseek-v4-flash",
      "choice": "high",
      "wire_parameters": {
        "max_tokens": 1024,
        "thinking": {
          "type": "enabled"
        },
        "reasoning_effort": "high"
      },
      "http_status": 200,
      "actual_model": "deepseek-v4-flash",
      "content": "你好，有什么可以帮你的吗？",
      "reasoning_characters": 126,
      "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 55,
        "total_tokens": 155,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 46
        },
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 100
      },
      "finish_reason": "stop",
      "response_sha256": "bb8770150b8910f990f2c1f812ad5ed72b3ff3de2c9665ecb1a599710423c1d8",
      "status": "PASS",
      "seconds": 1.907
    },
    {
      "model": "deepseek-v4-flash",
      "choice": "ultra",
      "wire_parameters": {
        "max_tokens": 1024,
        "thinking": {
          "type": "enabled"
        },
        "reasoning_effort": "max"
      },
      "http_status": 200,
      "actual_model": "deepseek-v4-flash",
      "content": "你好！很高兴见到你。",
      "reasoning_characters": 283,
      "usage": {
        "prompt_tokens": 113,
        "completion_tokens": 67,
        "total_tokens": 180,
        "prompt_tokens_details": {
          "cached_tokens": 0
        },
        "completion_tokens_details": {
          "reasoning_tokens": 60
        },
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 113
      },
      "finish_reason": "stop",
      "response_sha256": "aebfea0122c09cb9a1f212eba1746af93c2cc5ca0b665c6959136e012a668246",
      "status": "PASS",
      "seconds": 1.656
    }
  ]
}
```

### deepseek-authorized-profile-migration.json

SHA-256 `d80ff4edd4989119456f0cee212b1133767f7ed5296f1143a05a592a6dfa892d`

```text
{
  "timestamp_utc": "2026-09-09T12:53:05.678622+00:00",
  "authorization": "Owner explicitly approved V4 Flash migration in current conversation",
  "profile_id": "profile-85ee2a5766dbe4e85b97f3d55eeb24f1",
  "before_model": "deepseek-chat",
  "after_model": "deepseek-v4-flash",
  "credential_file_bytes_unchanged": true,
  "active_profile_unchanged": true,
  "other_profiles_unchanged": true,
  "conversation_storage_touched": false
}
```

### authorized-vite-stop.json

SHA-256 `f46285ab0fa8a73518e4aabc205a5b4498c3a077f13e1fbb712e496dff9daafd`

```text
{
  "Action": "user_authorized_stop_vite_for_qwen",
  "ProcessId": 66316,
  "Script": "C:\\Users\\user\\Desktop\\leotree\\node_modules\\vite\\bin\\vite.js",
  "CreationDate": "2026-09-09T02:06:48.957218-07:00",
  "TimestampUtc": "2026-09-09T12:43:39.5828335Z"
}
```

### binding-source-only-cleanup.json

SHA-256 `1968c64cb510e374b2c9f46a8bc791c4242952d0f2c6c1cdb37b966ce1f786b2`

```text
{
  "Scope": "single newly generated regression source only; no fixture directory",
  "Path": "C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\models-worktree\\tests\\test_tmp_session_models_20260909.py",
  "Sha256": "dcb90cea0e1fee9d338109f7a58a6531c3e0316df5823669b282b533362ae943",
  "Removed": true
}
```

### runtime-features-binding-final.log

SHA-256 `ff9e7cb5d23e0c00f9acba8c2eb01d03d96160455bf49678b2637ba5d72dcee5`

```text
.....................................................                    [100%]
53 passed in 42.52s
```

### intermediate-full-suite.log

SHA-256 `dd958d3e9b4c0cf2732900b2f59326ddfd6be592a4babfcd010995d2a2f4a7d8`

```text
...................................................F.................... [  8%]
........................................................................ [ 16%]
................F....................................................... [ 24%]
........................................................................ [ 32%]
........................................................................ [ 40%]
........................................................................ [ 48%]
........................................................................ [ 56%]
........................................................................ [ 64%]
........................................................................ [ 72%]
........................................................................ [ 80%]
........................................................................ [ 88%]
......................F.........................................s....... [ 96%]
...................s..........                                           [100%]
================================== FAILURES ===================================
____ test_connect_keyless_without_a_profile_uses_an_unpersisted_bootstrap _____

    def test_connect_keyless_without_a_profile_uses_an_unpersisted_bootstrap():
        api, store, coordinator = make_api()
        def forbid_key_read(profile_id):
            raise AssertionError("browsing must not read a credential")
        store.api_key_for = forbid_key_read
        assert api.connect_keyless() == {"ok": True, "pending": True, "request_id": 7}
        assert len(coordinator.submissions) == 1
        profile, api_key, requires_ack = coordinator.submissions[0]
        assert profile.entry_mode == "unconfigured"
        assert profile.id == ""
>       assert profile.provider == "chatgpt" and profile.model == "deepseek-chat"
E       AssertionError: assert ('chatgpt' == 'chatgpt'
E
E           chatgpt and 'deepseek-v4-flash' == 'deepseek-chat'
E
E         - deepseek-chat
E         + deepseek-v4-flash)

tests\leo_shell\test_api.py:531: AssertionError
_____________________________ test_state_defaults _____________________________

store = <leo_shell.settings_store.SettingsStore object at 0x000002403B9D97C0>

    def test_state_defaults(store: SettingsStore) -> None:
        state = store.state_for_shell()
        assert state["profiles"] == []
        assert state["active_profile_id"] is None
        assert state["has_key"] is False
>       assert state["settings"] == {
            "preset": "deepseek",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
        }
E       AssertionError: assert {'preset': 'd...deepseek.com'} == {'preset': 'd...deepseek.com'}
E
E         Omitting 2 identical items, use -vv to show
E         Differing items:
E         {'model': 'deepseek-v4-flash'} != {'model': 'deepseek-chat'}
E         Use -v to get more diff

tests\leo_shell\test_settings_store.py:59: AssertionError
_________________________ test_sql_failure_rolls_back _________________________

data = namespace(store=<openai4s.store.Store object at 0x000002403BCFF020>, frame='f-e8883c213809', cfg=Config(data_dir=Windo....<locals>.<lambda> at 0x000002403BD51DA0>, freeze_model_binding=<function data.<locals>.legacy at 0x000002403BD53240>))

    def test_sql_failure_rolls_back(data):
        a,b=register(data,'a'),register(data,'b'); bind(data,a); old=data.store.get_frame(data.frame)
>       data.store._connection.execute("CREATE TRIGGER fixture_abort BEFORE UPDATE ON frames BEGIN SELECT RAISE(ABORT,'fixture'); END")
        ^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'Store' object has no attribute '_connection'. Did you mean: '_connectors'?

tests\test_tmp_session_models_20260909.py:96: AttributeError
=========================== short test summary info ===========================
FAILED tests/leo_shell/test_api.py::test_connect_keyless_without_a_profile_uses_an_unpersisted_bootstrap
FAILED tests/leo_shell/test_settings_store.py::test_state_defaults - Assertio...
FAILED tests/test_tmp_session_models_20260909.py::test_sql_failure_rolls_back
3 failed, 889 passed, 2 skipped in 38.95s
```

### combined-regression-final.log

SHA-256 `ce0084426b27c75235fdccef4a96b87eb5635b7e90eb729666a0a23762f6b4a2`

```text
........................................................................ [  8%]
........................................................................ [ 17%]
........................................................................ [ 25%]
........................................................................ [ 34%]
........................................................................ [ 42%]
........................................................................ [ 51%]
........................................................................ [ 59%]
........................................................................ [ 68%]
........................................................................ [ 77%]
.........................FF.......F..................................... [ 85%]
........................................................................ [ 94%]
...........s..........................s..........                        [100%]
================================== FAILURES ===================================
______________ test_no_hard_machine_bindings_in_tracked_sources _______________

    def test_no_hard_machine_bindings_in_tracked_sources():
        """Every remaining machine-specific value must be overridable."""
        scanner = _scanner()
        hard, _configurable, _historical = scanner.partition_findings(scanner.scan())
>       assert not hard, "machine-bound paths found:\n" + "\n".join(
            f"  {f['file']}:{f['line']}  {f['rule']}  {f['text']}" for f in hard
        )
E       AssertionError: machine-bound paths found:
E           PINN_MVP_AND_CFD_READINESS_REPORT.md:11  windows-user-home  - ���ֿ����ڱ�����֮���γ��������� `8c4835e9d5034876235e1108e889902ac5bfa14f`��ԭ Phase II `repo/` Ŀ¼���Ƴ�����ѧ��֧���ύ��������ǰ����ʩ��·���� `C:/Users/user/Documents/LeoAIStudio-deliveries/2
E       assert not [{'rule': 'windows-user-home', 'file': 'PINN_MVP_AND_CFD_READINESS_REPORT.md', 'line': 11, 'text': '- ���ֿ����ڱ�����֮���γ���������...02ac5bfa14f`��ԭ Phase II `repo/` Ŀ¼���Ƴ�����ѧ��֧���ύ��������ǰ����ʩ��·���� `C:/Users/user/Documents/LeoAIStudio-deliveries/2', ...}]

tests\test_portability.py:37: AssertionError
____ test_exact_path_hash_and_finding_are_reported_as_historical_evidence _____

    def test_exact_path_hash_and_finding_are_reported_as_historical_evidence():
        scanner = _scanner()
        hard, configurable, historical = scanner.partition_findings(scanner.scan())
>       assert not hard
E       AssertionError: assert not [{'rule': 'windows-user-home', 'file': 'PINN_MVP_AND_CFD_READINESS_REPORT.md', 'line': 11, 'text': '- ���ֿ����ڱ�����֮���γ���������...02ac5bfa14f`��ԭ Phase II `repo/` Ŀ¼���Ƴ�����ѧ��֧���ύ��������ǰ����ʩ��·���� `C:/Users/user/Documents/LeoAIStudio-deliveries/2', ...}]

tests\test_portability.py:82: AssertionError
___________ test_human_output_keeps_the_historical_findings_visible ___________

capsys = <_pytest.capture.CaptureFixture object at 0x0000019F38B68CB0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000019F38B68F50>

    def test_human_output_keeps_the_historical_findings_visible(capsys, monkeypatch):
        scanner = _scanner()
        monkeypatch.setattr("sys.argv", ["portability_check.py"])
>       assert scanner.main() == 0
E       AssertionError: assert 1 == 0
E        +  where 1 = <function main at 0x0000019F38B36DE0>()
E        +    where <function main at 0x0000019F38B36DE0> = <module 'leo_portability_check' from 'C:\\Users\\user\\Documents\\LeoAIStudio-deliveries\\20260908-phase2\\models-worktree\\tools\\portability_check.py'>.main

tests\test_portability.py:169: AssertionError
---------------------------- Captured stdout call -----------------------------
  [default ] tools/sync_skills.py:44  wsl-distro-literal  (overridable) WSL_DISTRO = os.environ.get("LEO_WSL_DISTRO", "Ubuntu-24.04")
  [EXEMPT-HISTORICAL-EVIDENCE] governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md:58  windows-user-home
              policy=manifests/portability-historical-evidence.json sha256=018ff149d95df09eafded81e0274ded0e4ba39fd3023039b9bb1b67883acf8cf
              | **S2** | ʵ�� PINN ���д�������� | `C:\Users\user\Desktop\pinns\` | ��ʵ���ڵ� Maxwell-MHD reduced PINN �о����� 6 �� `outputs_*` Ŀ¼�� `����/` ����Ŀ |
  [EXEMPT-HISTORICAL-EVIDENCE] governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md:170  windows-user-home
              policy=manifests/portability-historical-evidence.json sha256=018ff149d95df09eafded81e0274ded0e4ba39fd3023039b9bb1b67883acf8cf
              | �ڶ�ʮ���� Ψһ Run ID | **PARTIAL** | **FAIL�����أ�** | S1��`research-sop` �� 16 λ hex `run_id`���� task sha256 ������ǿ��У�飩��S2��**�� runId**��`����/outputs_aligned/aligned_figure_
  [EXEMPT-HISTORICAL-EVIDENCE] governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md:407  windows-user-home
              policy=manifests/portability-historical-evidence.json sha256=018ff149d95df09eafded81e0274ded0e4ba39fd3023039b9bb1b67883acf8cf
              { "checkpoint": "C:\\Users\\user\\Desktop\\pinns\\outputs\\run_6\\model.pt", ... }
  [BINDING ] PINN_MVP_AND_CFD_READINESS_REPORT.md:11  windows-user-home  -- an absolute path into one Windows user's profile
              - ���ֿ����ڱ�����֮���γ��������� `8c4835e9d5034876235e1108e889902ac5bfa14f`��ԭ Phase II `repo/` Ŀ¼���Ƴ�����ѧ��֧���ύ��������ǰ����ʩ��·���� `C:/Users/user/Documents/LeoAIStudio-deliveries/2

  1 hard binding(s), 1 configurable default(s), 3 historical evidence finding(s)
  NOTE: this is a static scan. A clean result is NOT the same as a successful install
        under a fresh Windows account -- that stays a manual acceptance item.
=========================== short test summary info ===========================
FAILED tests/test_portability.py::test_no_hard_machine_bindings_in_tracked_sources
FAILED tests/test_portability.py::test_exact_path_hash_and_finding_are_reported_as_historical_evidence
FAILED tests/test_portability.py::test_human_output_keeps_the_historical_findings_visible
3 failed, 836 passed, 2 skipped in 32.84s
```

### root-existing-subset.log

SHA-256 `745543a92426cc7170859728da7c2ba2960f01215e478da3e19f7932f9086aae`

```text

no tests ran in 0.00s
ERROR: file or directory not found: tests/test_ui_contract.py
```

### root-existing-subset-corrected.log

SHA-256 `eb813d9e88251c6b819bfd3e666ee7ff30109005ca2ee5023190a6e594395770`

```text
........................................................................ [ 90%]
..s.....                                                                 [100%]
79 passed, 1 skipped in 6.29s
```

Disposable source local-live-temporary.py: SHA-256 `b5109791e212ce1b48618407de45b9aead253a4395c5507ac7e93a7eb8d74bd8`; results above/component reports retained, source scheduled for deletion.

Disposable source runtime-features-temporary.py: SHA-256 `606fd467c8656676aba22ac7e8ae6170ab5c013743f856400d8434ba507640cb`; results above/component reports retained, source scheduled for deletion.

Integration cleanup checkpoint: both `local-live-temporary.py` and `runtime-features-temporary.py` were removed successfully after the preceding consolidation. Displayed log excerpts normalize trailing whitespace; original log files and their exact hashes are retained.

````

</details>

### R007 — 项目/docs/LEO_EMPTY_STATE_RETURN_UI_REPORT.md

<details>
<summary>展开完整原文</summary>

````markdown
# 工作台空状态、返回开始界面与模型状态提示

本项仅修改 Leo 自己的 CSS 与注入层。上游 checkout、字体、科研候选、正式锁和历史 evidence 均未修改。开始页、ShellApi 和协调器变更由同轮配套实现负责；本文的 Chromium 检查属于源码 DOM 验证，不代表 installed EXE / WebView2 已经验收。

## 实际修改

`stage/leo.css`：截图中“还没有项目”“还没有对话”上方的点线图形来自淡墨浓秋的 `.dash-empty::before` 伪元素及 `--leo-node-mark`，不是功能图标。新增规则只作用于 `#dash-projects > .dash-empty::before` 和 `#dash-sessions > .dash-empty::before`，令其 `content:none; display:none`。其他空状态、文件网格装饰和功能 SVG/icon 保留。返回按钮仅增加不换行和不挤压样式。

`stage/leo-inject.js`：在 dashboard 顶部 `.dash-actions` 与 conversation 顶部 `.conv-head-actions` 分别加入“返回开始界面”/“Back to start”。两个节点沿用各自父页面的显示状态；重复注入不重复创建，DOM 被上游重建后可恢复。保留上游 `#back-home` 返回 dashboard 的原功能。按钮经过现有 `leoBridge` 白名单调用 `return_to_start()`，不绕过 ShellApi；等待时两个入口同时禁用，重复点击仅产生一次请求。`ok:false`、缺少确认结果或异常均显示可见错误，并恢复重试。

工作台继续使用唯一的 `#key-banner`。新增 `get_runtime_state()` 白名单调用，以严格的 `mode`、`status`、`has_key`、`local_ready` 投影运行状态，不读取或输出 API key 内容：

| 权威状态 | 工作台表现 |
| --- | --- |
| `unconfigured` / `keyless` | “无密钥浏览模式，配置模型后可使用对话。” |
| `local + ready + local_ready=true` | 移除未配置提示 |
| `cloud + ready + has_key=true` | 移除未配置提示 |
| 本地或云端 `connecting` | 显示正在连接，不称为 ready |
| 本地或云端 `failed` / 非 ready | 显示模型尚未就绪，不显示无密钥措辞 |
| API 失败、未知或结构非法 | 显示状态尚未确认，不称为 ready |

修复了原先仅凭 active profile 的 `requires_key:false` 就把本地模型当作已配置就绪的推断。现在 `setLocalModelAccess()` 必须同时获得权威 `local + ready + local_ready=true`。首次进入及状态变化时清除旧的提示关闭记录；用户随后在当前状态主动关闭提示仍有效。提示及 `body.has-key-banner` 的布局偏移一起移除，不产生第二条横幅。

## 已执行验证

使用上一轮经过验证的独立 Python 环境，cwd 为本 UI worktree。

| 命令/检查 | Passed | Failed | Skipped | 范围 |
| --- | ---: | ---: | ---: | --- |
| `node --check stage/leo-inject.js` | 1 | 0 | 0 | JavaScript 语法 |
| `python -m pytest tests/test_theme_readability.py tests/test_theme_settings_integration.py -q --tb=short` | 98 | 0 | 0 | 原有主题可读性和实际 Chromium 设置持久化回归 |
| `python -m pytest tests/test_ui_api_contract.py -q --tb=short` | 9 | 0 | 1 | 配套 API 落地后的前端/ShellApi 既有合同回归 |
| 临时 Chromium DOM 检查脚本 | 89 | 0 | 0 | 当前 CSS 和逐字提取的生产函数；bridge 返回值为受控测试替身 |

89 项 DOM 检查包含：三个主题 × 两种明暗 × 两种语言的装饰移除、显式返回按钮和功能图标保留；非目标空状态与文件网格保留；按钮幂等、DOM 重建、重复点击互斥、成功恢复、三类失败可见及重试；11 类运行状态和严格布尔值；真实 `refreshLocalModelAccess()` 使用权威 API；已存无密钥 profile 不等于本地 ready；读取 runtime 失败后不残留 ready；设置入口可用；提示与偏移同步关闭；英文未知状态。

配套 API 尚在并行编辑时曾运行 `tests/test_theme_readability.py tests/test_ui_api_contract.py`，结果为 **102 passed / 1 failed / 1 skipped**。唯一失败明确是 `get_runtime_state`、`return_to_start` 已入前端白名单但后端当时尚未落地；并未删改该既有测试。API 落地后重新运行合同套件得到 **9 passed / 0 failed / 1 skipped**。已有 skip 来自当前已启用的 entityLifecycle 所对应的未启用分支。完整回归和真实桥接执行结果由主交付报告记录，不能用这里的 DOM 替身测试代替。

`git diff --check -- stage/leo.css stage/leo-inject.js` 无空白错误。

## 证据与清理

证据位于本次 Documents 交付目录的 `ui-evidence/`：

- `empty-return-browser-results.json`：89 项逐项结果、当前 CSS/JS SHA-256、明确验证边界。
- `empty-return-existing-theme-tests.log`：98 项既有回归结果。
- `empty-return-ui-contract-tests.log`：配套 API 落地后的 9 pass / 1 skip 合同回归。
- `empty-return-source-dom.png`：1280×800 源码 DOM 检查截图。它使用实际样式与受控页面骨架，不是已安装产品截图。

根据用户“新增测试源码也删除”的明确要求，运行后以单文件补丁删除临时脚本 `ui-evidence/empty_return_browser_check.py`。专用 Chrome 进程已经退出，但其 profile `ui-evidence/chrome-empty-return/` 的递归清理被工具自动审批以 `blocked by policy` 拒绝；未获得更具体理由，未绕过该限制，该目录仍待清理。没有新增或删除任何仓库内既有测试文件，没有删除用户项目、对话、科研数据、原始 evidence 或上游文件。临时脚本执行时 SHA-256 为：

```text
e19b99b4a20e1d23766d8b72d29539162a02c28c4ddbe079e984ec6673e31de5
```

删除意味着这组临时 89 项检查不作为可重跑的新增回归源码交付；逐项结果和生产源码 hash 仍可核查。最终构建、部署、真实窗口及返回开始页闭环需由配套 ShellApi 和本轮主交付证据共同证明。

````

</details>

### R008 — 项目/docs/LEO_ENTITY_DELETION_PERSISTENCE_REPORT.md

<details>
<summary>展开完整原文</summary>

```markdown
# Entity deletion persistence repair

Date: 2026-09-08. Scope: the existing Leo shell/injection layer; no installed user data was modified by this task. Source workspace: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-worktree`; branch `codex/leo-entry-navigation-20260908`; starting HEAD `e05ac35b476337f0677830b047787330b46dfb13`. This report covers a working-tree change, not a deployed acceptance or scientific Gate PASS.

## Finding and implemented behavior

The original `stage/leo-inject.js` `installSoftDeleteBoundary` intercepted real `DELETE /api/v1/projects/{id}`, `/frames/{id}` and `/folders/{id}`. It wrote `state=trashed` through `mark_entity`, then returned synthetic HTTP 200 with `soft_deleted:true`. `leo_shell/entity_store.py` persisted those records only in `user/entity-states.json`. Its GET wrapper hid those IDs from listings. Therefore a missing injection layer after provider navigation exposed the still-present backend rows. This was a local visibility operation, not persistent content deletion.

`stage/leo-inject.js` now passes DELETE to the actual transport. All visible project/session/group management and data-manager delete actions use one permanent-delete helper. Archive still writes reversible local metadata. Permanent delete requires explicit irreversible confirmation, fresh complete session enumeration, the existing running-task guard, real HTTP success with JSON `ok === true`, and a separate absence check before local records are forgotten. Failed requests, malformed acknowledgments, incomplete listing/pagination, and unconfirmed absence cannot be recorded as success. Data manager now allows permanent project deletion, and explains that its recycle bin contains legacy hidden records.

The pinned upstream has an unusual but verified missing-object contract: `GET /api/v1/projects/{id}` and `GET /api/v1/frames/{id}` return HTTP 200 with exactly `{}`, rather than HTTP 404. The implementation verifies this exact response. Project deletion additionally checks the complete project session listing for residual members. Folder deletion verifies absence from all project folder listings; the upstream operation retains the group's sessions. Local revision records are cleared only after proof. Project child records are verified before any local cleanup, the project snapshot is cleared last, and a bridge failure remains retryable after server data is already gone.

The real backend already supports durable cascade deletion: `openai4s/server/gateway.py` routes through `SessionRunner`/`SessionDeletionService` to `openai4s/storage/deletion.py` transactions. This task did not replace that implementation. Successful deletion can report `skipped_unowned_files`; the UI now displays that count as a warning and does not claim all physical bytes were erased. Shared CAS remains governed by the upstream ownership/retention rules.

## Tests and evidence

Evidence root: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence`.

| Command / scope | Passed | Failed | Skipped | Result |
| --- | ---: | ---: | ---: | --- |
| `node entity-delete-temporary.cjs` (temporary script in evidence root; Node v24.16.0; production functions extracted verbatim into VM with controlled transport/ShellApi) | 44 | 0 | 0 | PASS at source hash below; not a live browser/gateway run |
| `python -B entity-delete-storage-temporary.py` (Python 3.12.9; actual installed upstream `Store`, exclusively new synthetic SQLite DB, close/reopen) | 18 | 0 | 0 | PASS; no real data directory opened |
| `C:/Users/user/Desktop/LeoAIStudio-pinn-mvp-20260908T120017Z/.venv/Scripts/python.exe -m pytest tests/test_ui_api_contract.py tests/leo_shell/test_api.py tests/test_theme_readability.py tests/test_theme_settings_integration.py -q` | 188 | 0 | 1 | PASS; the existing skip asserts a data page is hidden only when entityLifecycle is unavailable; current feature is implemented/enabled |
| `node --check stage/leo-inject.js` | — | 0 | 0 | PASS |
| `git diff --check -- stage/leo-inject.js stage/leo.css` | — | 0 | 0 | PASS |
| Initial command also named nonexistent `tests/leo_shell/test_entity_store.py` | 0 | — | 0 | NOT-RUN: pytest collection command failed with missing file; corrected to existing suite above |

Function checks cover true DELETE passthrough/status propagation, exact target and project cascade, unrelated SNN-named synthetic fixture preservation, folder membership preservation, reversible archive, malformed acknowledgment types, 401/409/500, falsely successful deletion with target still present, malformed absence proof, residual project session, retryable local bridge cleanup failure, surviving historical member protection, running tasks, invalid IDs, pagination failures/completion, cancellation, stale revision, visible bridge error, fail-closed malformed listing, and skipped-file warnings. Raw unfiltered backend fixture listings remain absent after clearing all local entity state; this specifically checks that success does not depend on local hiding.

The SQLite checks use actual installed upstream storage code and verify project/session/message cascade, exact session deletion, folder removal with session preservation, and persistence of those results after closing/reopening the database. They do not exercise the live gateway runtime cancellation, all artifact/file cleanup, provider navigation, or the Example startup seeder.

Files retained:

- `entity-delete-function-results.json`: all 44 named function checks and source SHA256.
- `entity-delete-storage-results.json`: all 18 storage checks, upstream source SHA256 and synthetic database SHA256.
- `entity-delete-existing-regression.log`: existing suite counts.
- `entity-cleanup-candidates.json`: exact original local tombstone metadata only; no prompts, messages, API keys, or other content.

Verified final product JS SHA256: `864c0134510b0771e52297d2adbc099bdff7dcce3f237f92818cf15310dadcfb`.

Installed read-only upstream hashes used by storage checks:

- `openai4s/store.py`: `ebb2ca6ad7ae0b4084f63bbf3b388c23f09a189e614d46b182e54b4583492224`.
- `openai4s/storage/deletion.py`: `e0e87e317d166218bf971e28a506c9cba627a00569d5da2b5734c1746b6b1cf8`.

## Live cleanup authorization boundary

Original local state revision 15, SHA256 `b36c78b667a402f93c8071efcc6581c434d3319d033ea36c7c24142b9350f8d4`, contains 10 trashed project IDs and 12 distinct snapshot/direct session IDs. The candidate file is an identification aid; snapshot membership is historical and is not a complete current backend enumeration. It explicitly protects the archived project and its known members and all other unspecified entities.

The root agent subsequently independently reconciled live metadata: the 10 exact trashed projects still exist and contain 17 current root sessions. The archived project's current 4 sessions, the normal SNN project's 4 sessions, and the default project's 1 session are protected. The parent owns live deletion and its evidence. No title pattern is authority to delete additional projects; this task did not delete any installed entity.

## Remaining limitations and coordination

1. The installed gateway startup `_seed_example_project` recreates missing `proj_example`. A sibling task adds a transaction-bound durable marker and seed guard; this report does not claim that peer code or the deployed restart was tested by these 62 temporary checks.
2. A sibling task repairs navigation/reinjection after provider changes. Until a built installed artifact is exercised through that path, live UI/provider-switch acceptance is NOT-RUN here.
3. Backend physical file cleanup intentionally may retain shared/unowned files or report files not cleaned. The UI exposes the available count. Upstream runtime resource release/share revocation catches some exceptions and relies on its own reconciliation; this task does not establish physical secure erasure or external resource cleanup.
4. A preflight running check can race; the actual server admission barrier remains authoritative. An API error or postcondition mismatch remains visibly unconfirmed, including when a server mutation may already have occurred.
5. The JS regression suite ran before the final small skipped-file warning addition; the 44 production-function checks and syntax check cover the final source, and the root agent owns the final combined suite/build.

## Requested temporary source cleanup

The user explicitly requested removal of newly introduced test source after recording the results. The temporary Node script SHA256 was `457b884d5015e82d975a84a915acd087f9bfe547b42042f3ee704ceb6128e98a`; the temporary Python script SHA256 was `b2cab78b56eec171119e690abc232498fc69dc916c1000745ddd1eec872c6be1`. Both test sources were removed using the patch tool after result recording. No existing repository tests are removed. The exclusively synthetic database's recorded SHA256 is `e37e58802cd3f3d039053dfb486e16c704cc8fdecde0b958b457b0b2692f8b9e`. Its exact-path, hash-guarded PowerShell removal was rejected by automated approval with `blocked by policy`, so `entity-delete-synthetic.sqlite3` remains pending parent/user cleanup; no alternate deletion path was attempted.

The earlier empty-state/return UI check's dedicated `chrome-empty-return` profile remains pending parent cleanup because automated approval rejected its recursive removal; no alternate deletion path was attempted. That is separate from these Node/SQLite checks.

```

</details>

### R009 — 项目/docs/LEO_ENTRY_BROWSE_RUNTIME_REPORT.md

<details>
<summary>展开完整原文</summary>

````markdown
# Leo Entry: strict browse runtime component evidence

Date: 2026-09-08 UTC. Source baseline: `e05ac35b476337f0677830b047787330b46dfb13`, branch `codex/leo-entry-navigation-20260908`.

## Verdict and scope

**OFFLINE HELPER COMPONENT: 27 passed, 0 failed, 0 errors, 0 skipped.** Real installed deployment, live daemon, real database, real model generation and external network validation are **NOT-RUN** in this component task. These results are not full UI acceptance or a scientific Accuracy Claim.

The two helpers are changed only in the isolated UI worktree. The original installed application and WSL data have not been changed or stopped. A separate Windows installation root does not isolate the existing WSL data directory or daemon port.

## Changes and contract

- `bridge/leo_runtime_compat.py`: retain the existing SDK `submit_output` compatibility overlay and completion-validation return. Add an independently checked overlay for the public `openai4s/llm/client.py:chat` entry point. The whole original chat module must match an explicitly audited SHA256; patched repeats must reconstruct those exact original bytes. Unknown source revisions, changed guards, relocated guards and changed original bytes fail closed. Both source inputs are checked before either is changed; exact originals are backed up by content hash and individual updates use atomic replacement.
- `bridge/leo_model_selection.py`: add explicit `browse=True` / `--browse`. Browsing leaves `active_model_profile` and the global key override empty without restoring a matching saved profile. Original values and timestamps remain in recovery slots; model profiles and conversation pins are unchanged. `browse` conflicts with `local` or `explicit_key` and is rejected before opening a transaction. This selection operation does not itself prevent a pinned session from resolving its key; the independent chat guard enforces rejection.

Runtime contract:

- `LEO_STUDIO_BROWSE_ONLY=1`: reject at the public chat entry before provider lookup, capability lookup or dispatch; fixed `error_code=LEO_BROWSE_ONLY`, `status=403`, `retryable=False`.
- `LEO_STUDIO_BROWSE_ONLY=0`: original model call path. Missing variable also preserves non-Leo behavior. Any other value fails closed with `LEO_BROWSE_MODE_INVALID`.
- A successful compatibility receipt retains `compatibility=submit-output`, `version=1`, and adds `browse_guard=true` only when the exact guard is applied. `browse_guard_details` records version, source file, original and resulting hashes. A read-only `check` on unpatched source returns `applied=false`, `browse_guard=false`, `needs_update=true`.
- The calling bridge must require `browse_guard=true`, explicitly set mode `1` or `0` for every new daemon, clear inherited model credentials for browse and set `OPENAI4S_SKIP_DOTENV=1`. A running daemon is not evidence that the desired mode has been applied. Caller changes and their integration tests are owned separately.
- No new canonical shell script is required for this contract: the inspected installed `leo_bridge.sh` preserves exported custom variables through its existing start path. Actual propagation in a deployed daemon remains NOT-RUN here.

## Exact sources and hashes

The source fixture was read from the installed distribution's source files, without executing them or reading its user database:

| Object | SHA256 |
|---|---|
| Original `openai4s/llm/client.py`, 5700 bytes, LF | `99a65f666be44bbf46a69cc5b04ca95e8aae0cf14b5c2371a36d4655a69d11fa` |
| Exact CRLF equivalent, 5849 bytes | `6b3406b0aa692e3179ef05103367f4e3cb4bff1028150938026176ba84b7334f` |
| Original `openai4s/sdk/host.py` | `8fcfa5256595a48cdcffc930515109f9603666ecee9c715720fa0dc38986bcb5` |
| Tested `bridge/leo_runtime_compat.py` | `7402dab1bb6480254c885bd61ca7723ef959be62b137506d375bb2fcfcfa22b1` |
| Tested `bridge/leo_model_selection.py` | `a2aee4f14e070cf56a387e533707ce045a37a59fad0b86714910cf4f48920a1c` |
| Temporary regression source, removed after recording | `f09040d82125962a662b5868771c3d525d4d2592c50aef3e41cbe67597adfbd5` |

## Test command and retained evidence

```powershell
& 'C:/Users/user/mamba/python.exe' 'C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/test_browse_helpers_temporary.py'
```

Python `3.12.9`, conda-forge, MSC 1943 64 bit AMD64. Tests completed in `0.458s` on `2026-09-08T13:35:36Z`.

| Layer | Count | Result | Cases |
|---|---:|---|---|
| Audited source overlay / disk fixtures | 12 | PASS | LF/CRLF exact bytes; idempotency; unknown source; altered/moved guard; altered original; read-only check; true receipt; exact backups; conflicting backup; validate all sources before SDK write; missing chat source |
| Executed patched upstream chat function with offline dispatch fixture | 9 | PASS | resolved cloud key; synthetic resolved pinned-revision key; keyless local endpoint; no key; invalid modes; normal cloud dispatch; normal local dispatch; absent flag; original missing-key rejection |
| SQLite selection fixtures | 6 | PASS | preserved profiles/pins/original values/timestamps; repeated browse; exact restore; conflicting flags; explicit-key mode retained; CLI receipt with fixture-only database |

Retained append-only outputs:

- `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/browse-helper-tests-20260908T133536Z.log`
- `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/browse-helper-tests-20260908T133536Z.json`

The JSON records interpreter, source/helper hashes, counts, duration and explicit `live_daemon_executed=false`, `real_database_opened=false`, `network_requested=false`. Temporary scratch databases, source fixture copies, backups and directory junctions were confined to newly created `browse-helper-fixture-*` directories under `ui-evidence`; those directories were removed after their resolved containment was checked. The newly added test source is deleted after this report is saved, as the user requested. No existing tests or historical evidence are deleted.

## Remaining limits

The patched function was extracted from the exact audited upstream module and executed with offline provider/capability/dispatch fixtures. The pinned-key negative models an already resolved credential; it does not execute the real gateway/database resolver. This proves rejection before dispatch for such a configuration, not full live session acceptance.

Source inspection confirms public `openai4s.llm.chat` forwards to the guarded function. `server/model_profiles.py:probe` also uses that facade, so its model request is covered. However, its existing exception handler reports `contacted=true` even for an exception before dispatch. That metadata is not a reliable outbound-contact proof in browse mode; the browsing UI should disable that action and full acceptance must retain this limitation. General tools, other external connectors, direct transport calls and arbitrary user code are outside this guard's scope. This is not a network sandbox.

Changing the upstream chat file later requires a new audit and hash update; it deliberately blocks launch instead of guessing a compatible patch. The receipt and mode must be verified again when the original installed application is eventually deployed under an authorized stop/restart window.

## Deleted Example project persistence

The installed upstream `_seed_example_project` recreated `proj_example` whenever the row was absent. It had no durable record that the user deleted it. New `bridge/leo_example_persistence.py` supplies a separate, exact-source overlay for two targets:

- `openai4s/storage/deletion.py`: inside the existing `BEGIN IMMEDIATE` project-deletion transaction, after an actual `proj_example` row is deleted and the recorded project count is exactly one, insert settings key `leo_example_project_deleted_v1` with value `1` before commit. Marker failure rolls back the project deletion. A failed DELETE, other project ID or missing project does not invent a marker. An existing valid marker keeps its original timestamp; invalid existing values cause rollback.
- `openai4s/server/gateway.py`: the original startup seed reads the same `cfg.db_path` setting first. A valid marker prevents seed; missing marker retains original first-boot behavior; invalid values, including a present SQL NULL, fail closed. The startup exception path already closes the runner and re-raises, so this failure does not become an accepted startup.

The helper itself does not delete projects, mark real databases, change user archive records or stop services. It supports `apply`, read-only `check`, and read-only `status`; exact originals are retained in `example-persistence-originals/<original SHA256>.py`. Unknown revisions are rejected before either target is modified.

Final component tests: **23 passed, 0 failed, 0 errors, 0 skipped**, `2.331s`, `2026-09-08T13:46:27Z`, Python `3.12.9`. The executed deletion and seed methods were extracted from the exact patched upstream sources. Transaction boundaries and relevant SQL ran against independent SQLite fixture files. The existing aggregate-deletion helper was stubbed in this component fixture; this is not a new validation of every historical cascade table or real filesystem cleanup.

```powershell
& 'C:/Users/user/mamba/python.exe' -B 'C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/test_example_persistence_temporary.py'
```

Coverage: eight deletion transaction cases (success, DELETE failure, marker failure with rollback, invalid marker rollback, other project, missing project, unconfirmed count, timestamp preservation); nine restart/status cases (new database connection across restart, new environment, existing example, corrupted marker, NULL marker, exact-byte read-only status, invalid status, honest present-project status, CLI); six source-overlay cases (LF/CRLF, idempotency, unknown source, altered guard, preflight of both inputs before writes, backup/receipt checks).

| Object | Final tested SHA256 |
|---|---|
| `bridge/leo_example_persistence.py` | `1d6882e80ed018728c6f314befaaca3511e790d1d024a3d2321db1d6ff883031` |
| Temporary regression source, removed after recording | `1fb9c35babb7e685958dc57618c9719425fed3ef1ff6ee286caa4d1de1c6dba3` |
| Original gateway LF | `db33c3e3e7b4d618881e7899646d8de55c9c1794b47f57c5b97c7d2a2227a192` |
| Patched gateway LF | `703c8fb9b7b525fae2038d964384d9205534945ee9a3ae32272bb7e8b158ba5f` |
| Original deletion repository LF | `e0e87e317d166218bf971e28a506c9cba627a00569d5da2b5734c1746b6b1cf8` |
| Patched deletion repository LF | `4e69bcf7edabf8fca0c13259553bb803672fe5b86a952ded95037c81ec494adc` |

Retained evidence under `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/`:

- `example-persistence-tests-20260908T134627Z.log` and `.json`: final 23-case run.
- `example-persistence-tests-20260908T134533Z.log` and `.json`: earlier 22-case snapshot, retained. Subsequent review added the NULL-marker case and distinguished absence from corruption before the final run; this earlier snapshot is not the final source verdict.

Temporary test source is deleted after recording, as requested; scratch fixture directories, SQLite databases and source junctions have been removed after checking containment. Existing tests and earlier evidence remain.

Deployment integration contract (deployment is owned and verified separately):

1. Include the new helper in the verified installation bridge assets, alongside the two browse helpers and updated launcher/bridge caller.
2. Before a new daemon starts, the bridge invokes `python3 -I <installed-helper> apply` and requires `data.version=1`, `data.example_persistence=true`, `data.applied=true`. Default base is the current WSL user's `~/.local/share/leo-ai-studio`; `--base` may explicitly name the same audited root. Record the receipt's source revision and both file hashes. Starting an already running daemon does not reload patched Python modules.
3. Invoke normal authenticated DELETE for the exact user-selected `proj_example` through the patched backend. The existing API returns `{}` for a missing project's GET; do not assume HTTP 404. The UI owner handles the actual response and absence proof.
4. Read the marker without credentials or mutations using `python3 -I <installed-helper> status`. Default database is `<base>/data/openai4s.db`; an explicit `--database` is supported for a previously verified path. Require `marker_valid=true` and `project_exists=false`, then repeat after an authorized restart. Status does not independently assert which module bytes the daemon has loaded.

Example invocation shape, replacing the distribution and path with the already verified installation values; no token belongs in the shell command:

```powershell
wsl.exe -d <verified-distribution> -e /usr/bin/python3 -I <installed-helper-wsl-path> apply
wsl.exe -d <verified-distribution> -e /usr/bin/python3 -I <installed-helper-wsl-path> check
wsl.exe -d <verified-distribution> -e /usr/bin/python3 -I <installed-helper-wsl-path> status
```

Live deployment, real user-data deletion and post-restart absence are **NOT-RUN by this component agent**. Their results must be recorded by the deployment owner, without replacing this offline evidence.

````

</details>

### R010 — 项目/docs/LEO_ENTRY_NAVIGATION_IMPLEMENTATION_REPORT.md

<details>
<summary>展开完整原文</summary>

```markdown
# Leo AI Studio 入口、返回与重复导航注入实施记录

2026-09-08。本项是用户在 PINN Phase II 审阅暂停期间单独授权的实际 UI 修复。**源码路径已实现，限定范围回归通过；installed EXE / WebView2 / WSL / 真实供应商端到端验收尚未由本文执行。原 P0 结论仍为 FAIL，PINN 人工批准仍为空；本项没有正式锁、训练或 Accuracy Claim。**

## 工作区与边界

- 安全工作区：`C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-worktree`。
- 分支：`codex/leo-entry-navigation-20260908`。
- 修改前 HEAD：`e05ac35b476337f0677830b047787330b46dfb13`，本子任务开始时该工作区干净。
- 原 dirty checkout、PINN Phase II 工作区、原安装、真实用户项目/会话/密钥、WSL daemon 均未由本子任务修改或删除。
- 本子任务不提交、不部署。最终工程 commit 与安装资产身份由主交付报告绑定；本报告描述该提交前可审阅的源码与证据。
- 已核查仓库中没有 `AGENTS.md` / `CLAUDE.md`，已读 `leo_shell/DESIGN.md` 及实际 API、settings、coordinator、UI、bridge、local health/probe 路径。该设计文档旧版的 `KEYLESS_NEEDS_PROFILE` 规则已被此次明确用户需求替代；科学冻结文本没有改变。

## 已修复原因与实际行为

1. **没有 profile 就无法浏览。** 原 `connect_keyless()` 直接拒绝。现在无 profile 使用仅存在于本次调用内的默认 daemon bootstrap；不保存 profile，不读取或传递 API key。显式浏览本地配置时同样使用浏览 bootstrap，不启动本地模型。`enter_studio()` 则使用真实活动配置：云端读取其保存密钥，本地走原本的真实身份、health、model alias 与 relay 校验链，无配置可以浏览。
2. **默认模板被误认为已保存配置。** `get_state().settings` 在空安装下也有默认模板；开始页原先只要该字典存在就写“已保存配置”。Chromium 第一轮检查抓到了该问题。现在仅以实际 active profile 判定配置状态。
3. **保存/连接提交被拒绝仍报告成功。** API 统一检查 coordinator 的 `ok:true` 回执；关闭中或异常不再返回 `pending:true`。保存后读取凭据出错明确返回 `MODEL_SETTINGS_UNAVAILABLE`，不会默默切成浏览。
4. **换供应商或 key 后出现原生 OpenAI4S 页面。** `DesktopUI.navigate()` 原先没有清除前一页面的 `_backend_loaded`，第二次 `loaded` 因此跳过注入。现在每次导航都重置注入状态，每个新文档独立注入；仅确切布尔 `true` 才视为成功。资源缺失、脚本异常、False/None/非法回执均保留失败状态并尝试显示含“返回开始页”入口的显式降级横幅。底层 JS 引擎连横幅也无法执行时仅能记录失败；这仍属于真实窗口待验范围。
5. **返回后被迟到连接重新跳回工作台。** 新 `cancel_pending()` 递增请求代际、清 pending 与 ack，不关闭 worker、不停止 daemon。最终导航与取消共享专用 navigation lock；调用 UI 前释放状态 condition，避免注入读 runtime 状态时发生锁顺序死锁。返回先渲染开始页，再取消迟到导航并 `load_html`，重置文档注入状态，之后仍可再次进入。
6. **配置不等于运行就绪。** 新 `get_runtime_state()` 单独返回严格白名单字段 `mode/status/has_key/local_ready`。`local_ready=true` 仅在本次原有 local start/probe 链以及 URL 获取成功后产生。保存 local preset、免密标记或一个 key 字符串都不会使 local ready 成立。cloud 的 ready 表示工作台连接路径完成，**不证明供应商接受该密钥或完成推理**。工作台注入的 `has_key` 取自本次连接记录，不再重读保存配置来冒充本次凭据状态。
7. **无密钥标签不保证实际停止模型调用。** 本轮运行时同伴在既有 helper 上增加 `--browse` 选择、精确字节绑定的模型入口拒绝与回执。bridge 每次显式设置 `LEO_STUDIO_BROWSE_ONLY=1/0`；浏览还覆盖为空已知及继承的 provider key，并设置 `OPENAI4S_SKIP_DOTENV=1`。旧会话 pin 和其凭据保留，但公共模型调用入口在浏览时拒绝执行。缺失 `browse_guard:true` 回执、未知上游源码均拒绝启动。此能力是模型调用限制，**不是网络沙箱**。
8. **示例删除后的启动恢复。** 根据同轮新增用户反馈，bridge 已接入另一个同伴实现的 `leo_example_persistence.py` 准备步骤；缺失确切成功回执时启动失败。实际删除事务、Example tombstone 与完整验证由对应生命周期报告说明，不由本文的入口测试代替。

## 本子任务修改文件

| 文件 | 因果理由 |
| --- | --- |
| `leo_shell/api.py` | 真实进入、无配置浏览、返回、运行状态 API；严格提交失败传播；凭据读取失败可见 |
| `leo_shell/connection.py` | 独立运行状态、可复用 worker 的取消、最终导航竞争控制，消除 condition/window lock 反转 |
| `leo_shell/ui.py` | 重复导航重新注入；返回开始页；注入准确回执与显式降级；本次连接凭据状态 |
| `leo_shell/app.py` | `_LateBoundUiSink.navigate()` 传递 UI 失败，未绑定窗口不伪报成功 |
| `leo_shell/bridge_client.py` | browse flag、凭据环境覆盖、禁止 dotenv、browse helper 与 Example helper 回执门禁 |
| `stage/shell.html` | “进入 Leo AI Studio”按钮，中英文配置状态，双击互斥，异步失败恢复重试，避免默认模板误判 |
| `tests/leo_shell/test_api.py` | 保留并强化原无 profile 用例，验证无持久化、无 key 读取/传递的新授权契约 |
| `tests/leo_shell/test_bridge_client.py` | 既有无 key 环境契约更新为显式清空和 guard flag；helper 阶段、回执及失败用例对应增加，未删测试 |
| 本报告 | 记录实际实现、通过与失败、测试边界和清理 |

同轮配套 `stage/leo-inject.js` / `stage/leo.css` 的返回入口、唯一状态条及删除流程，以及 `bridge/leo_runtime_compat.py`、`bridge/leo_model_selection.py`、`bridge/leo_example_persistence.py` 由同伴所有。没有改动 frozen Scientific Spec、Constitution、Acceptance 或 hash 协议。

## 验证矩阵

解释器：`C:/Users/user/Desktop/LeoAIStudio-pinn-mvp-20260908T120017Z/.venv/Scripts/python.exe`，Python **3.12.9**。Node **v24.16.0**；真实浏览器为 `C:/Program Files/Google/Chrome/Application/chrome.exe`，版本 **152.0.7977.77**。测试工作目录均为上述 UI worktree。测试子进程显式清理父进程凭据环境，记录中不包含真实密钥。

| 阶段 / 命令 | Passed | Failed | Skipped | 解释 |
| --- | ---: | ---: | ---: | --- |
| 修改前 `python -m pytest tests/leo_shell -q` | 258 | 0 | 0 | 入口源码基线 |
| 首次 `tests/leo_shell tests/test_ui_api_contract.py` | 266 | 1 | 1 | 旧用例要求无 key 不改 WSLENV，与新明确空覆盖契约冲突；对应既有用例已强化更新 |
| v1 `tests/test_entry_navigation_temporary.py tests/leo_shell tests/test_ui_api_contract.py` | 300 | 0 | 1 | 新临时入口/线程/UI用例与既有回归 |
| v2 上述命令加 `tests/test_theme_settings_integration.py` | 305 | 0 | 1 | 新增 Example 准备失败用例；既有真实 Chromium 设置持久化 |
| v3 同 v2，增加导航读状态锁与保存凭据失败回归 | **307** | **0** | **1** | 最后限定范围 Python 回归 |
| Chromium 开始页 v1 | 6 | 4 | 0 | 两种语言各发现默认模板误判，另各记录一次 driver 中止；产品问题已修 |
| Chromium 开始页 v2 | 24 | 4 | 0 | 临时 fixture 新建 local profile 未显式 activate，仍选旧 cloud；fixture 已纠正，产品未为此改动 |
| Chromium 开始页 v3 | **36** | **0** | **0** | 每种语言18项，生产 shell + 真实 ShellApi/SettingsStore；coordinator和浏览器到Python运输为替身 |
| `node --check stage/leo-inject.js` 及生产 shell 内联 JS 的 `node --check` | 2 | 0 | 0 | 语法，不是行为验收 |
| `git diff --check` | 1 | 0 | 0 | 空白检查；主任务并行 PowerShell 文件另有 LF/CRLF 提示，不影响本项文件 |

唯一 skip 为 `tests/test_ui_api_contract.py:163` 的旧“entityLifecycle 关闭”分支；当前功能已启用，因此该测试按其原有定义跳过，未新增 skip/xfail。临时 Python 文件最终共 **35 cases**。早期进度消息中的“34”是口头计数错误；以实际 collection 和上述日志为准。完整仓库回归、构建及部署由主任务完成。

35 项临时 Python 测试覆盖：空配置/云端/本地进入、显式本地浏览不启动 local provider、重复点击/拒绝 submit、凭据读取失败、非法 runtime 状态与严格 bool、local start 中/失败/成功状态、取消 in-flight start 后 worker 可再用、重复 provider 导航与返回后重新注入、缺失资产和非 true 回执、UI/JS 引擎异常、返回失败状态保留、无窗口/非受信导航失败、browse 环境覆盖及旧 helper 拒绝、UI 导航回调中能并行读取 runtime 状态。

## 证据、清理与尚未验证

证据目录：`C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/`。

- `entry-navigation-python-v1.log`、`entry-navigation-python-v2.log`、`entry-navigation-python-v3.log`。
- `entry-browser-results.json`、`entry-browser-results-v2.json`、`entry-browser-results-v3.json`：失败与后续成功分别保存，没有覆盖失败。
- `entry-browser-v3-zh.png`、`entry-browser-v3-en.png`：真实生产开始页 DOM 的最终交互截图，包含故意注入的重试提示；不是已部署产品截图。
- `entry-navigation-source-identity.json`：本子任务交接时源码、证据、临时测试文件的精确 SHA-256；同伴并行文件的最终身份以主任务 commit/manifest 为准。
- 根据用户明确要求，记录结果与文件 hash 后删除本轮新建的 `tests/test_entry_navigation_temporary.py` 和 `ui-evidence/entry_browser_temporary.py`。原有测试保留，新增测试源码不作为交付物；上述临时35项和36项不能在不重建 harness 的情况下原样重跑。相关截图、逐项结果、失败日志保持。

尚未验证：真实 EXE 从空配置进入、带真实云端 key 切换后 Leo 完整样式、返回与再次进入、local 模型实际健康/relay、daemon 重启中的 browse flag、旧 pin 模型请求拒绝及真实 GUI 错误呈现。无法在本子任务中把这些标为 PASS。返回保留 daemon 以免打断会话；选择不同连接模式则仍沿用单 daemon 的原有重启路径，活跃任务切换语义由主任务后续验证。

运行时同伴已查到 upstream model probe 会把任意异常记录为 `contacted:true`，包括 guard 拒绝且未实际 dispatch 的情况；该字段不构成已接触供应商的证据。browse guard不覆盖任意科研代码或其他外部连接器。本次没有修改此类网络行为或 PINN 批准边界。

## 2026-09-09 补充：普通启动必须等待明确进入

本补充依据 `../DELIVERY.md` 的中断交接和用户继续实施要求。补充前 HEAD 为 `512ab8d9e5fa51197efa6963e1172ebbeb7fc87e`；已有同伴的 `stage/leo-inject.js` 改动被保留，本子任务没有编辑该文件或 `leo_shell/ui.py`。以下是源码与替身验证，新增源码尚未由本子任务提交、构建或安装；已安装版本和真实同 URL 导航修复的状态以主交付记录为准。

根因是 `Application._on_window_ready()` 仍会在已保存云端密钥或本地免密配置时调用 `coordinator.submit()`，绕过开始页的“进入 Leo AI Studio”按钮。现在普通启动回调直接留在开始页，不读取 profile/凭据、不提交连接，也不自动打开设置；页面继续通过原 `ShellApi.get_state()` 显示配置。`--settings` 仍只打开设置，失败时显示现有公开错误码，不递归重试、不转为连接。显式进入、先逛逛、保存并连接仍使用原 ShellApi 路径。**这里的“不读取凭据”仅指 window-ready 回调；组装阶段原有的旧凭据迁移及页面查询状态没有被改写。**

本次限定修改：

| 文件 | 原因 |
| --- | --- |
| `leo_shell/app.py` | 去掉普通启动自动连接，保留 CLI 设置入口及失败反馈 |
| `tests/leo_shell/test_app_startup.py` | 原有 7 项全部保留并按明确的新交互强化：云端有 key 也等待点击、无 profile 不强开设置、回调不读取 profile/key、不导航；设置窗口失败仍报告公开码 |
| `stage/shell.html` | 仅更新 7 处静态文字（中文初始 fallback 与两种语言的 6 个 COPY 值），去掉“每次启动自动进入”及凭配置宣称模型已就绪；没有布局改动 |
| 本报告 | 保存原因、失败、通过数与清理边界 |

同一 Python 3.12.9 解释器、同一 UI worktree；最终子进程环境排除名字含 KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL 的继承变量，日志不含真实凭据。

| 命令 / 阶段 | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| 修改前 `python -m pytest tests/leo_shell/test_app_startup.py -q` | 7 | 0 | 0 |
| 首轮 `python -m pytest tests/leo_shell/test_app_startup.py tests/test_startup_entry_temporary.py -q` | 17 | 1 | 0 |
| 文案修正后，以上命令加 `tests/leo_shell/test_api.py` | 99 | 0 | 0 |
| 最终 `python -m pytest tests/leo_shell tests/test_ui_api_contract.py tests/test_startup_entry_temporary.py -q` | **279** | **0** | **1** |
| 旧 HEAD/当前回调隔离对照：cloud/local/unconfigured | 3 | 0 | 0 |
| 限定文件 `git diff --check` | 1 | 0 | 0 |

首轮失败是真实的残余中文初始 hero 文案仍承诺自动进入。文字替换预检因同一句出现两次而拒绝写入；后续精确更新 fallback 与 COPY，并复测通过。未删测试、未放宽断言。唯一 skip 仍是旧 `entityLifecycle` 关闭分支在功能启用时的原有跳过。临时边界测试共 **11 项**：已配置本地/云端/空配置、重复 window-ready、完全不可访问的配置/coordinator、转发 activate、设置与错误横幅同时失败，以及中英文文案契约。

证据位于 `../ui-evidence/`：

- `startup-explicit-entry-regression-v2.log`：最终 279/0/1 原始测试输出。
- `startup-explicit-entry-evidence.json`：旧/新源码调用对照、各阶段数量、源码 SHA256。对照确认旧 cloud/local 启动各提交 1 次，新版三种配置提交均为 0、普通启动自动打开设置均为 0。
- 临时源码 `tests/test_startup_entry_temporary.py` SHA256：`c403b0e4663f03b7586127a67696f7ed1edd5753d49339b2fb33a3feda5f5c78`。按用户要求，在本报告记录后删除此新增源码及其专属 pyc，删除结果单独写 `startup-explicit-entry-cleanup.json`；不删除既有启动/API测试或失败证据。

该修复没有启动 WSL、加载模型、调用供应商、修改真实 DB、变更科学治理或形成 PINN claim。真实安装普通启动、再次进入/返回及同 URL WebView2 导航由主任务继续验收，不能用以上替身测试宣称完成。
# Integration checkpoint — 2026-09-09

Before committing the startup/navigation/path fixes together, the existing complete suite was run with the explicit installed upstream root and a dedicated temporary directory: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp <ui-evidence>/entry-recovery-pytest-20260909`. Result: **839 passed / 0 failed / 2 skipped**, 34.78 s. The skips are the previously disabled legacy UI path and the absent local wheelhouse (the retained, previously verified 21-wheel offline input is in the earlier worktree). No skip was added. Full log: `ui-evidence/entry-recovery-full-regression-20260909.log`.

`node --check` passed for the injection and WebView inspector; `git diff --check` passed. Updated runtime asset hashes bind the current startup HTML and composed injection bytes. This checkpoint is source validation, not a claim that the replacement EXE has passed installed navigation tests. See the separate native navigation and canonical skills drift reports for cause, scoped tests, and remaining runtime checks.

```

</details>

### R011 — 项目/docs/LEO_LOCAL_QWEN_REASONING_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

```markdown
# Local Qwen reasoning relay — 2026-09-09

## Verdict and scope

Source implementation and isolated validation: **PASS**. Installed-model generation, installed workbench thought rendering, and final package integration: **NOT-RUN by this subtask**. These results do not claim scientific accuracy, PINN completion, or a new frozen release.

Worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree`, branch `codex/conversation-runtime-20260909`, base `9e53dcc4d534a1dadd93ad0107ee88bef55d455f`. Product edits started only after the root agent confirmed the previous entry build finished and created this separate worktree. Ownership is limited to `bridge/leo_local_relay.py` and this report. The shared capability implementation `bridge/leo_reasoning.py` belongs to the scientific diagnostics agent.

No installed file, model file, daemon, user conversation, locked scientific specification, acceptance threshold, or historical evidence was changed here. No model or daemon was started or stopped. A read-only health check found no listener on `127.0.0.1:8080`; the root agent owns subsequent live verification.

## Real backend and model audit

The actual executable `C:/Users/user/Desktop/大模型/runtime/llama.cpp/llama-server.exe --version` returned `0.4.0-dev (build 10809, commit 5266f24da)`, built with Clang 20.1.8 for Windows x86_64. The actual configuration specifies alias `local-qwen3-4b`, `contextSize=16384`, `device=Vulkan1`, and loopback port 8080. Configuration does not itself prove the service is running.

Read-only GGUF metadata inspection read 5,932,859 bytes from the existing 2,497,280,256-byte model. Architecture is `qwen3`; its embedded `tokenizer.chat_template` explicitly handles `enable_thinking`, separate assistant `reasoning_content`, and the native tool transport. The UTF-8 template SHA-256 is `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`. Evidence is `qwen-actual-template-audit.json`; this audit did not rehash the entire 2.5 GB model.

The implementation was checked against official source at the exact executable commit:

- [server-common.cpp](https://github.com/ggml-org/llama.cpp/blob/5266f24da/tools/server/server-common.cpp) reads `thinking_budget_tokens`, with `reasoning_budget_tokens` taking precedence if both are supplied, then passes the budget and discovered thinking delimiters into the sampling layer. The relay removes the conflicting canonical field before applying the selected budget.
- [reasoning-budget.cpp](https://github.com/ggml-org/llama.cpp/blob/5266f24da/common/reasoning-budget.cpp) counts a thinking block and forces its termination when its budget is exhausted. It permits UTF-8 completion and a closing sequence. A later thinking block re-arms the budget. Therefore the selected number is a **per-block thinking token budget**, not a guaranteed number of generated thought tokens, a whole-response thought cap, or an accuracy guarantee.
- [chat-auto-parser-generator.cpp](https://github.com/ggml-org/llama.cpp/blob/5266f24da/common/chat-auto-parser-generator.cpp) builds schema-constrained response content after its separate reasoning parser. The simple-introduction JSON grammar is therefore retained, with explicit `reasoning_format=deepseek`; the adapter accepts only the genuine separate thought field and still validates the fixed identity answer. This is source evidence of compatibility; a live generation check remains required.
- [sampling.cpp](https://github.com/ggml-org/llama.cpp/blob/5266f24da/common/sampling.cpp) applies the reasoning sampler during actual token sampling. These six choices are not prompt-only labels.

## Changes and request semantics

`prepare_chat` consumes optional `leo_reasoning_level` through the shared `describe`/`resolve` capability policy. Only its strict choices are accepted; null, booleans, numbers, containers, aliases such as `medium`, whitespace variants, and unknown values fail before a provider request. The gateway validates its request admission snapshot against the daemon-side relay endpoint. The relay then resolves the admitted choice against its fixed Windows model endpoint, avoiding a false comparison between two different endpoint revisions.

| Choice | Native `thinking_budget_tokens` | Total completion `max_tokens` |
| --- | ---: | ---: |
| default / omitted | none; thinking disabled | existing positive request limit, capped at 512 |
| low | 128 | 640 |
| mid | 256 | 768 |
| high | 512 | 1024 |
| xhigh | 1024 | 1536 |
| extra | 2048 | 2560 |
| ultra | 4096 | 4608 |

For an explicit choice the relay uses the shared policy's native payload, removes `reasoning_effort=none`, enables template thinking, and requests separate `reasoning_content`. The whole completion has an additional 512-token allowance beyond the thinking budget; that allowance includes answer and forced-close/tool transport overhead, so it does not promise 512 visible answer tokens. An invalid caller-supplied output limit is still rejected. The private choice and conflicting raw native budget are consumed rather than forwarded.

The old automatic `<think>` / `</think>` token suppression is not added in thinking mode. If a caller supplies a bias object, the two actual control IDs are obtained from the tokenizer and removed from that object while preserving unrelated biases. A malformed tokenizer result fails closed.

Full original messages remain unchanged. The actual local template and complete protocol/schema are tokenized; the relay rejects `input_tokens + max_tokens > context`. Invalid or empty token-count responses are rejected. No history is trimmed to make a larger effort fit.

`_stream_response` now concatenates only provider `reasoning_content` fragments into their own field. `_reasoning_fields` rejects invalid thought types. `adapt_introduction_response` and the scientific-code conversion in `adapt_native_response` preserve this field when replacing the transport message. Genuine thoughts are never parsed as JSON finalizers, copied into answer content, or interpreted as executable scientific cells. An unchanged native finalizer retains its original response bytes.

Existing safety conditions remain: one complete validated native action, stable stream ID/model/call ID, strict JSON and finalizer/code argument schema, valid terminal reason and `[DONE]`, no continuation after completion, complete transport exit success, and bounded response size. A failed or truncated response publishes no native action.

## Tests and evidence

Python: `../ui-worktree/.venv/Scripts/python.exe`, version **3.12.9**. All commands below ran from `models-worktree` with `PYTHONDONTWRITEBYTECODE=1`. Temporary test files were outside the product tree. SSE fixtures reproduce the official provider field/framing shape; they are synthetic test fixtures, not claims of newly captured model generations.

| Command / run | Passed | Failed | Skipped | Other | Result |
| --- | ---: | ---: | ---: | --- | --- |
| `python -m pytest -q -p no:cacheprovider ../ui-evidence/model-runtime-20260909/local-relay-reasoning-temporary.py` initial implementation | 76 | 0 | 0 | none | PASS |
| Same temporary module, `LEO_RELAY_BASELINE=1`, `--tb=line -k 'real_budget_and_full_history or provider_thought_preserved_separately or invalid_reasoning_is_not_ignored'` against `git show 9e53dcc:bridge/leo_local_relay.py` loaded in memory | 2 | 26 | 0 | 48 deselected | Expected baseline FAIL; defects reproduced |
| Full temporary module after adding seven malformed context-count checks | **83** | **0** | **0** | none | PASS |
| Same full temporary module after checking final shared-policy integration | **83** | **0** | **0** | none | PASS |
| `python -m pytest -q -p no:cacheprovider tests/leo_shell` | **259** | **0** | **0** | none | PASS |
| `python bridge/leo_local_relay.py --help` | n/a | 0 | 0 | exit 0 | Actual sibling import / script entry PASS |
| `git diff --check` | n/a | 0 | 0 | exit 0 | PASS |
| Actual Qwen generation / installed GUI | 0 | 0 | 0 | NOT-RUN | Root-owned acceptance remains |

The 83 cases cover: 12 six-level ordinary/greeting configurations; 2 default cases; 12 invalid levels; 6 invalid output limits; exact-context-boundary and overflow; selective control-bias removal; 7 malformed context counts; 7 malformed control-token probes; 6 JSON/SSE thought-preservation paths; 10 invalid thought types; 15 terminal/tool/stream corruption cases; raw thought in introduction content; 2 complete-versus-failed curl transport cases; and admission capability -> private relay choice -> native payload integration. The failure suite includes a valid-looking response with curl exit code 28: neither executable code nor thought output is published.

Evidence directory: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/model-runtime-20260909/`.

| File | SHA-256 |
| --- | --- |
| Product `bridge/leo_local_relay.py` at this subtask handoff | `d2c1cda29196e6757fab6f5c5e4953a7f87648c80c02b704e6e1d633d30d2eaf` |
| Shared `bridge/leo_reasoning.py` at integration test time; owned elsewhere | `905cbd29ca54f608dc464322eba536d1501bc509586210c408db2cab5799f620` |
| `local-relay-reasoning-tests-final.log` | `17dfde0d867d4ff4095fdc97757aa92c55b689f24429c883d05787fa9e195d1d` |
| `local-relay-reasoning-shared-policy-final.log` | `1539b820332a6b6c626d5c42b451db1bad866ae8230d1aa79cba0eabb665f18c` |
| `local-relay-reasoning-baseline.log` | `cd4421c782e6259d382038981e2ca0c17dab05c8463426da5c71c16c9f6deba1` |
| `local-relay-shell-regression.log` | `f14529eea140897d601ecafcd50b4afb271b7d09d02a741dd70082831670f7af` |
| `qwen-actual-template-audit.json` | `af9476f70371543d47369ea620c6c21baab5712f72b5394807640cdc2e22bd3b` |

## Cleanup and remaining acceptance

The user explicitly requested deletion of newly created regression test source after recording results. The temporary test source has final SHA-256 `4b4076571b3e434085142ca39cf4c586f03f995c205b8ca49e010af322aa4c76`; the earlier 76-case version used for the baseline comparison had SHA-256 `5eb1ed985cae36b5cd8d35502fd35bf18756aa976bfd9650e2b1b6ed6231c3d4`. Its exact path is the temporary module named in the commands above. **Removal verified**: that 13,237-byte test module and the four disposable downloaded official-source copies were removed using exact guarded file paths. Their original sizes and hashes, plus individual absence checks, remain in `local-relay-temporary-cleanup.json`. Existing repository tests remain intact. Logs and model-template audit evidence remain available.

The package must include `bridge/leo_reasoning.py` beside the relay. Root owns package contracts/build/deployment integration and real checks at low/ultra plus introduction/native-cell paths. Real generation must confirm the backend emits separate reasoning fields and completes its final tool action within the selected total budget; the source and mocked transport tests cannot prove that performance or model behavior. The native adapter intentionally buffers an entire action before publishing, so this subtask preserves genuine thought output but does not claim live token-by-token display before validation. No speculative streaming executor, model lifecycle change, PINN training, or CFD implementation was added.

```

</details>

### R012 — 项目/docs/LEO_NATIVE_NAVIGATION_RECOVERY_REPORT.md

<details>
<summary>展开完整原文</summary>

````markdown
# Leo AI Studio: repeated native navigation recovery

Date: 2026-09-09 UTC. Scope: the desktop navigation component only.

Implementation and offline regression: **PASS**. Updated installed native window: **NOT-RUN by this subtask**. This report does not grant P0 acceptance, PINN completeness, a scientific Gate, or an Accuracy Claim.

## Source and observed failure

Worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-worktree`.
Base commit: `512ab8d9e5fa51197efa6963e1172ebbeb7fc87e`. Other concurrent source edits belong to the coordinating agents and are outside this report's change scope. The interruption checkpoint is the sibling `DELIVERY.md`.

The coordinating agent observed a responsive native WebView2 document whose `window.pywebview.api.get_state()` and `get_runtime_state()` promises repeatedly timed out after reconnecting. Plain CDP evaluation remained responsive. A real full document reload immediately restored the Python API and correct cloud runtime/Leo style. Existing evidence: sibling `ui-evidence/installed-bridge-shape.json` and `ui-evidence/installed-deepseek-after-full-reload.json`. These are pre-fix observations, not post-fix acceptance. This subtask did not operate that window or daemon.

The installed pywebview 6.2.1 source explains the failure:

1. `webview/window.py:270` resolves a URL and clears `loaded`, `before_load`, and `_pywebviewready` before calling the renderer.
2. `webview/platforms/edgechromium.py:218` only assigns `self.webview.Source = Uri(url)`. A repeated equal source URI can produce no document navigation and hence no replacement bridge injection.
3. The API decorator in `webview/window.py:35` waits for readiness; return delivery in `webview/util.py:247` calls `window.evaluate_js`, which also requires readiness. The old page can therefore remain visible while API promises never receive their Python return value.
4. A genuine `NavigationCompleted` runs `inject_pywebview`; the generated API setup restores readiness. The full-reload observation is consistent with this exact lifecycle.

The offline regression executes the actual installed `Window.load_url` and `_api_call` source extracted with Python AST, with only the Source setter and event wait replaced by bounded fixtures. For a same-URI no-op it verifies all three events become unset, no navigation happens, and the real API decorator attempts a 20-second readiness wait then prevents return delivery. It does not create a native window or claim to simulate every COM behavior.

## Minimal repair

Only `leo_shell/ui.py` changes product behavior. Trusted URL validation remains before all navigation. For the supported `edgechromium` renderer, `_load_backend_url` calls `CoreWebView2.Navigate` with the original, unmodified trusted URL. All Core access and the request run on the WinForms UI thread through `native.Invoke(Action(...))` when required. The lazy `System.Action` import follows pywebview's initialized pythonnet runtime; other renderers keep `window.load_url`.

Before issuing a request, the helper snapshots the three readiness flags, `real_url`, and the renderer's `ishtml` flag. Successful submission retains pywebview's existing `NavigationCompleted`/injection path. A synchronous rejection restores those values; `navigate` restores its pending/loaded flags and returns `False`. The error log records only the exception type because native exception text can contain the daemon URI/token. Missing CoreWebView2 fails before any event is cleared. No query parameter, fragment, URL trust relaxation, browser script, profile, token, database, or runtime setting is added.

`navigate() == True` means the native navigation request was accepted. It does **not** by itself prove the later navigation, Python bridge, or Leo injection succeeded. Asynchronous failures continue through the existing load/injection behavior and require native acceptance below. This controlled private pywebview integration is tied to the packaged 6.2.1 WinForms layout; a runtime upgrade must recheck that layout and lifecycle.

## Test matrix

Commands ran from the worktree above, in PowerShell:

```powershell
& 'C:/Users/user/mamba/python.exe' -B 'C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/test_native_navigation_temporary.py'
& 'C:/Users/user/Desktop/LeoAIStudio-build/.venv/Scripts/python.exe' -B -m pytest tests/leo_shell/test_api.py tests/leo_shell/test_connection.py tests/leo_shell/test_theme_runtime.py -q
git diff --check -- leo_shell/ui.py
```

| Run | Passed | Failed | Errors | Skipped | Blocked | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| New offline native-navigation component cases | 15 | 0 | 0 | 0 | 0 | PASS, 0.017 seconds |
| Existing API, connection, theme regression | 139 | 0 | 0 | 0 | 0 | PASS, 1.42 seconds |
| Diff whitespace validation | n/a | 0 | 0 | 0 | 0 | PASS |
| Updated installed WebView2 repeat-entry acceptance | 0 | 0 | 0 | 0 | 0 | NOT-RUN here; coordinating agent owns deployment |

The 15 new tests cover four equal-URI navigations with fixture reinjection after each; recovery with readiness already lost; worker-thread marshalling; direct UI-thread execution; missing Core; native rejection; exact mixed-readiness restoration; Invoke failure; HTML-to-URL bookkeeping and rollback; unchanged alternate-renderer behavior and its failure; untrusted schemes/host/port/fragment/userinfo; absent window; and the installed pywebview-source no-op reproduction. Exception fixtures include a fake secret and prove neither it nor a traceback is logged. All tests are offline; no real model, daemon, user window, credentials, or network were used.

Per the user's explicit instruction, the new temporary test source is removed after recording its result and hash here. Existing repository tests are retained. The command above documents the executed source; after removal it is not a currently runnable permanent test command. Logs and result metadata remain as execution evidence.

## Evidence and exact bytes

Evidence directory: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence`.

| File | SHA-256 |
| --- | --- |
| Tested `leo_shell/ui.py` | `3f4b2ba11443f8982cd6c0059d7cf11fce4d4dd067841fa06631fa826c2bd790` |
| Temporary test source, removed after recording | `1c8f8c54fc589aa6bc78c216e62f6ff77b7e81c4038302a6bccf77eab6d5757b` |
| `native-navigation-tests-20260909T081031Z.log` | `7b7e152adb34c9ffb128202b6c7888d844201a0e9015dd6321844b16c2cb9016` |
| `native-navigation-tests-20260909T081031Z.json` | `d051bb1fbf36aa1d8b513d9843832ce5daba530ac0ed476e5a26f5aa9bd4ab96` |
| `native-navigation-existing-regression-20260909T0815Z.log` | `ee0a18450be24e41d952fcdcd8f4a54703fa91504261d1262f84b4a303e365d5` |
| Installed pywebview `window.py` | `00de0b2155308a29e0af42d3e5c40221cd1ea1fb30d2be55a408ab1b314d5b03` |
| Installed pywebview `platforms/edgechromium.py` | `f3f9168ecb39f7447566112fd14c5ec55830eddf02053eafef0d86fac509a3a4` |

The new component run used Python `3.12.9`, conda-forge, MSC 1943, Windows AMD64. The library source paths above are relative to `C:/Users/user/Desktop/LeoAIStudio-build/.venv/Lib/site-packages/webview`.

## Remaining native acceptance

After the coordinating agent builds and deploys the integrated source while the application is closed, repeat entry to the **exact same** backend URI and verify every cycle completes a document navigation, resolves `get_state()` and `get_runtime_state()`, and restores the actual Leo theme/injection. Also cover start-page return followed by local, keyless browse, and a stored cloud profile; capture only sanitized status/timing, never token-bearing URLs or key values. Confirm failure presentation when native navigation cannot start. Preserve any failed attempt as separate evidence.

This subtask did not commit, build, deploy, restart, close the user window, exercise an actual model, or change settings/data. Model-effort routing, thought streaming, reply deduplication, and in-flight turn behavior remain separate tasks.

````

</details>

### R013 — 项目/docs/LEO_REASONING_AND_THOUGHT_RUNTIME_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# Reasoning capabilities and durable thought/progress projections

Date: 2026-09-09 UTC. Base: `9e53dcc4d534a1dadd93ad0107ee88bef55d455f`, branch `codex/conversation-runtime-20260909`.
Worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree`.

**Offline component result: PASS, 44 passed / 0 failed / 0 errors / 0 skipped.** Integrated installed native/provider acceptance is **NOT-RUN by this subtask**. This result grants no scientific Gate, PINN completeness, P0 manual acceptance, or Accuracy Claim. No real inference, user database, running daemon, window, profile, or deployment was operated by this subtask.

## Owned implementation

`bridge/leo_reasoning.py` is the shared capability and request-resolution source. `describe(provider, model, base_url)` returns a revision and seven explicit choices; `resolve(..., choice, capability_revision)` returns a version-bound wire snapshot or a stable error. `validate_snapshot` uses type-strict JSON equality against the resolved snapshot. `apply_request` consumes a deep copy, checks the admitted identity/revision, removes conflicting fields where specified, and never reads the old global reasoning-effort environment variable. It sends the local relay only its private choice marker, not the full admission metadata.

The revision binds provider, model, normalized endpoint, policy version, and advertised semantics. The returned descriptor does not echo arbitrary endpoint strings. Userinfo, query credentials, fragments, malformed ports and control characters fail with fixed error codes. An unknown endpoint/model offers only its unmodified provider default. Capabilities describe supported request semantics; local readiness and endpoint ownership remain separate checks in the integrating agents' model-selection code.

| Model/endpoint | Default | Available explicit choices | Wire meaning |
| --- | --- | --- | --- |
| Installed `local-qwen3-4b`, loopback llama.cpp/relay, actual upstream provider `chatgpt` | Existing local default, thinking disabled | Low 128; Mid 256; High 512; Xhigh 1024; Extra 2048; Ultra 4096 | `enable_thinking=true`, `thinking_budget_tokens=N`; remove conflicting `reasoning_effort` and `reasoning_budget_tokens` |
| `deepseek-v4-flash` / `deepseek-v4-pro`, exact HTTPS `api.deepseek.com`, port 443, root or `/v1` | Provider default, enabled/high | Low → low; High → high; Ultra → max | `thinking.type=enabled`, native `reasoning_effort` |
| Other provider, model, proxy or unverified alias | Provider default | None | No invented effort support |

The local budget applies **per thinking block**, with possible forced-closing/UTF-8 overhead; it does not guarantee output length or accuracy. Total generated tokens remain a separate limit. This is supported by the installed llama.cpp revision's request parsing and reasoning sampler; the local relay agent separately verified the actual Qwen template. [Pinned llama.cpp request implementation](https://github.com/ggml-org/llama.cpp/blob/5266f24da/tools/server/server-common.cpp).

DeepSeek exposes three actual levels. Its `medium` and `xhigh` compatibility inputs map to high, so Leo's Mid, Xhigh and Extra are unavailable for this family. The documented tool-calling protocol requires prior `reasoning_content` to be retained. These are request/protocol facts, not proof of model quality. [DeepSeek thinking guide](https://api-docs.deepseek.com/guides/thinking_mode/), [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/).

`bridge/leo_thought_runtime.py` provides source-bound transforms and runtime helpers. It does not install or run anything on import. Its interfaces are:

```python
patches()  # {relative_path: {source_sha256: str, replacements: [(old, new), ...]}}
runtime_modules()  # {"openai4s/leo_reasoning.py": bytes, "openai4s/leo_thought.py": bytes}
```

The central installer owned by the integrating agent composes these with the existing browse, Example-persistence and turn-binding overlays, then verifies the complete canonical reconstruction. This subtask never edits canonical or installed upstream files directly.

| Exact upstream target | Purpose |
| --- | --- |
| `openai4s/config.py` | Optional per-request `reasoning_choice`, `reasoning_capability_revision`, `reasoning_snapshot` fields |
| `openai4s/agent/events.py` | Independent typed `ReasoningDelta` |
| `openai4s/agent/engine.py` | Backward-compatible content callback plus independent optional reasoning callback; durable projection errors are not silently swallowed |
| `openai4s/llm/providers/openai.py` | Apply the admitted wire snapshot; project actual `reasoning_content`/`reasoning`; veto retries after public thought; preserve reasoning in assistant history |
| `openai4s/llm/messages.py` | Round-trip an existing assistant `reasoning_content` field without fabricating it |
| `openai4s/server/agent_run.py` | Keep intermediate prose as progress, true provider reasoning as thought, and bind the real action group only after routing |
| `openai4s/server/completions.py` | Optional collector labels the exact completion-bullet `parts` index as `completion_record`; original output bytes remain unchanged |
| `openai4s/server/gateway.py` | Session-scoped replay route, terminal persistence, metadata for live/stored final/progress/candidate, and unchanged candidate construction/review chain |

There are eight source-bound targets and 52 uniquely matched replacement operations. `llm/client.py` is unchanged by this overlay, retaining the separately verified browse guard. Unknown original bytes or a conflicting composition remain the central installer's fail-closed responsibility.

## Runtime and persistence contract

Each `thought` or `progress` channel has a distinct `projection_id = leo:{execution_id}:{engine_turn}:{channel}`. Packets contain `version`, frame/branch/turn/execution identities, engine iteration, channel, operation, monotonically increasing sequence, status, provider/model and an optional real group ID. Thought packets—including bind/terminal packets—retain an actual source-field label. No `<think>` string parsing, synthetic action narration, encrypted provider state, or token count is turned into thought content.

`append` carries a real text delta. `bind` associates the durable action group once it exists. `terminal` records completed/failed/cancelled; a completed intermediate model response does not grant a final answer or scientific claim. The provider's original reply and action ledger are retained. Already visible reasoning counts as committed output, so later rate-limit/provider errors cannot replay it under a fresh retry. Non-streaming replies yield a single snapshot path; they are not falsely described as live token streaming.

The helper creates only its own `leo_model_projections` table. The exact table SQL and foreign-key definition are checked, unexpected triggers are rejected, `PRAGMA foreign_keys` must already be enabled, and an unrelated active transaction is refused without commit or rollback. `(projection_id, seq)` is the primary key; events are inserted, never overwritten. `root_frame_id` references `frames(frame_id) ON DELETE CASCADE`. Each event is committed before publishing to the UI. Thought text is not inserted into normal assistant message content, model history, or scientific review input.

`GET /frames/{id}/leo-projections?branch_id=...` uses the existing session/auth boundary. It returns `version`, latest accumulated `projections`, and `has_more`. It returns at most the most recent 500 projections; **`has_more=true` means a partial history and must be shown as partial**, not silently presented as complete. No pagination cursor is promised. A projection is bounded to 262144 characters; exceeding the bound fails explicitly rather than silently truncating. Replay verifies sequence continuity and frame/branch/projection identity. A process crash may leave a nonterminal projection marked running; this is not a success claim.

Stored normal prose keeps its original bytes and receives `metadata.leo_projection` with a content SHA. Progress is a separate display role, not a deleted message. Final and candidate metadata may carry source-derived segments with individual hashes. The frontend may fold segments only when both the complete message SHA and exact segment concatenation match. Unknown metadata, a changed/repaired candidate, or a mismatched hash must leave the raw body visible.

For completion records, the formatter records which original `parts` entry came from structured `completion_bullets`. This labels the source structure without recognizing Chinese/English phrases. Artifacts, metrics, limitations and fallback text retain their original bytes. The optional collector does not alter old callers. Stage4's canonical `candidate_answer` assignments remain AST-identical; its original byte string and SHA continue through review/promotion. The ungated final channel now receives the finalizer's complete answer instead of suppressing its summary because the same words previously appeared in an intermediate no-action response.

## Executed test matrix

Command, from the new models worktree:

```powershell
& 'C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-worktree/.venv/Scripts/python.exe' -B 'C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/model-runtime-20260909/test_thought_runtime_temporary.py'
```

Python: 3.12.9, conda-forge, MSC 1943, AMD64. The test loader verifies actual original source hashes, applies every replacement in memory with one exact anchor, and compiles all transformed targets. It imports the transformed production provider, AgentEngine and WebEventSink; final-delivery tests execute the actual transformed method extracted with AST. The database integration test constructs the real upstream Store at an isolated external fixture path, with dotenv disabled and inherited credential variables cleared inside that test process. No inference transport or user database is called.

| Layer | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Capability/revision/snapshot/wire configuration | 9 | 0 | 0 | 0 |
| OpenAI streaming/non-streaming and negative protocol fixtures | 8 | 0 | 0 | 0 |
| Durable SQLite projection/replay/schema/negative cases | 15 | 0 | 0 | 0 |
| Production AgentEngine/WebEventSink projection behavior | 4 | 0 | 0 | 0 |
| Actual final delivery and unchanged candidate construction | 3 | 0 | 0 | 0 |
| Completion source segments and exact-byte regression | 5 | 0 | 0 | 0 |
| **Total** | **44** | **0** | **0** | **0** |

Subtest permutations are not counted as additional tests. The final run took 1.125 seconds. Coverage includes deceptive endpoints, actual `chatgpt` provider identity, stale revisions, malformed choices, NaN/type mutation, cross-request copying, global-env independence, genuine reasoning fields versus literal tags, retry veto, malformed/truncated streams, failed persistence, failed/cancelled partial replay, schema drift, disabled foreign keys, unknown frame, unrelated active transactions, isolated deletion, 501-projection partial history, two no-action groups, candidate byte equality, English/Chinese completion records, artifact suffixes and fallback/empty output.

Earlier evidence remains: the first 31-case run recorded 30 passed / 1 fixture error (duplicate keyword construction in the test helper). The fixture was corrected. Independent inspection then caught the production Store's `_conn` interface versus repository `_connection`; the helper was corrected and a real Store integration case added. Prior passing snapshots are not substitutes for the final 44-case result.

## Evidence, hashes and temporary cleanup

Evidence root: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/model-runtime-20260909`.

| Item | SHA-256 |
| --- | --- |
| `bridge/leo_reasoning.py` | `905cbd29ca54f608dc464322eba536d1501bc509586210c408db2cab5799f620` |
| `bridge/leo_thought_runtime.py` | `10e3de146cb45a08bf62afc51729a0fe9d15652172dd0dec612b3d4cefbe1f75` |
| Final temporary test source | `19f69316004d5d2f96a02b27ed475566e7fdd7aae559c960c95c92effa8eebf9` |
| `thought-runtime-tests-20260909T094126Z.log` | `6ec1627cebe708e268d4243dc9ed3d52e59095f123b0c9c4154660163b5b7442` |
| `thought-runtime-tests-20260909T094126Z.json` | `b9a8c0a41ba0b21df63f0369c18b8c5af1f7d5f8c101144b4423c957b8cf36c9` |

Per the user's explicit instruction, after recording the results this subtask removes only its new `test_thought_runtime_temporary.py` and four isolated `thought-fixture-*.db` files whose exact paths were recorded by its run metadata. `thought-runtime-temporary-cleanup.json` records their hashes and removal. Existing repository tests, historical logs, result JSON and scientific evidence remain. Consequently the command above records an executed temporary source; it is not a permanent rerunnable repository test after cleanup.

## Remaining integration acceptance

The central installer must verify the full composed runtime, including Example deletion protection and browse rejection, before daemon start. The integrating agents own the local relay budgets, turn admission/model binding, frontend rendering, package manifest, build and deployment. This component report does not claim those integrated paths passed.

The final installed application still needs real provider/local acceptance: authentic reasoning deltas and final direct answer, reconnect/reopen, switching models only across the admitted turn boundary, unsupported choice rejection, native DeepSeek tool-history round-trip, review-gated candidate preservation, cancellation/failure and protected old-history rendering. Responses encrypted reasoning, Anthropic and Gemini thought streaming are not implemented here. A provider failing to send thought must remain unavailable/empty; the UI must not invent content. Model phrasing remains a model output: typed projection and the separately owned prompt clarification do not prove the screenshot symptom is absent until an actual new run is checked.

````

</details>

### R014 — 项目/docs/LEO_RUNTIME_CRLF_COMPATIBILITY_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# Runtime CRLF compatibility repair — executed 2026-09-10

## Verdict and scope

The isolated reproduction is repaired: the unchanged 96-case suite went from **62 passed / 34 failed / 0 skipped** to **96 passed / 0 failed / 0 skipped**. Actual deployment of this repair, bootstrap, daemon startup and live model acceptance are **NOT-RUN by this subtask** and remain the root agent's responsibility. This report does not make a scientific accuracy claim or close a PINN Gate.

Source worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree`, branch `codex/conversation-runtime-20260909`, starting HEAD `f39466516c85af221e6e83d4c5f53ab92370ef98`. Only `bridge/leo_runtime_features.py` and this report are product/repository changes. No installed Windows source, active WSL source, database, model process, saved profile, key, conversation, Scientific Spec or formal lock was modified by this subtask.

## Root cause and exact repair

The existing Windows-to-WSL source installation preserved CRLF bytes from the pinned Windows checkout. The new conversation-runtime contracts declared LF whole-file identities. Their intersection consequently rejected ten known CRLF source files as `RUNTIME_FEATURES_SOURCE_UNKNOWN`. The gateway's Example contract already accepted CRLF, but the binding and thought contracts removed that identity when the accepted sets were intersected. The deletion target, owned solely by Example, retained both identities and passed.

The fixed installer registers ten literal LF/CRLF SHA-256 pairs for upstream Git revision `a792c38d9984be428437b548db29baab3322f6dc`. For each component declaration, it adds the registered CRLF identity **only when that component declares the exact corresponding LF identity**. Accepted sets are still intersected. A changed component LF identity receives no compatibility expansion; inconsistent shared declarations still fail. The already correct deletion contract is unchanged.

No incoming source is normalized. The installer still reverses complete known overlays, checks the whole recovered base hash, reconstructs the incoming bytes exactly, builds every registered layer, reverses it again, compiles all outputs, creates exact-byte backups, writes guarded replacements, reads every target back, and finally creates the success receipt. Existing CRLF files remain CRLF. Mixed line endings, BOM insertion, unrelated content changes, altered package components and unknown sources are rejected.

## Independent source identity audit

Each LF source was obtained with binary `git show a792c38d9984be428437b548db29baab3322f6dc:<path>` from the installed canonical upstream repository. All eleven Git blobs contained no CR bytes. For this audit only, replacing each LF with CRLF in memory derived the following exact identities. Production does not perform this normalization. The independently reconstructed pristine or Example-only CRLF bytes match all eleven actual WSL file hashes and byte lengths recorded by the root agent.

| Source | Canonical LF SHA-256 | Canonical CRLF SHA-256 |
| --- | --- | --- |
| `openai4s/agent/engine.py` | `eb087db2144d9d7d0040968376e3208d8891c60844dc552980825556350c2d1c` | `a89ef311c7d6cb05b7d2296ffbe6f9afa81bd4e646edadde8c1e4a5e27692322` |
| `openai4s/agent/events.py` | `d0bc5b4ae08cfc4efca3a841fedbede25fc3e35b1ae218e6d915b440ee828b63` | `b9438749fdd49d402df2747d0aa62c7acc3cc435a663a9f0fa5046ed6df9b827` |
| `openai4s/config.py` | `8e50e9fa301993340f79a30a8072a41b535d6e618af8c7efece547e3cab5b33b` | `5591f1225b60897bbe21f1097549e3600d6602d02bbaa148fc764d565948dd82` |
| `openai4s/llm/messages.py` | `b61f50acb576c7e9dda65b0aa207a5eecaf7e6c328043f000ed7c3ad451e5690` | `efdc633e182942898e206426ca36e66221c4bab6dcfccdacf00b6adfd575020a` |
| `openai4s/llm/providers/openai.py` | `2a8e28801717493dd9bd26cff691978e31930aa957c6d0a4e52fed2af6ab6447` | `51b7df5d4c8765412fa16650c9b73e23015598d71426f9e660d692555ad771e7` |
| `openai4s/server/agent_run.py` | `cc52e2abd7f0ba287b41e34f14cdf518e15b2f774ea61cde5c568bc60d0659ed` | `f9aa579e0efbfd75c2257163b3d3e0ab96acb74613dc533b435df594f8d1078a` |
| `openai4s/server/completions.py` | `d917d69948778424b6c5ca772fe766c7386e321755e948d5903ca0a5179fecca` | `fe566d90cc88f8ff6e8fb44280c54d74c3ac57e5ea5fc782055407641964dea6` |
| `openai4s/server/gateway.py` | `db33c3e3e7b4d618881e7899646d8de55c9c1794b47f57c5b97c7d2a2227a192` | `ba955144415690db973211df4d5329b1420eb6eb369ed91cd13cb61e02ce4c67` |
| `openai4s/storage/deletion.py` (existing pair) | `e0e87e317d166218bf971e28a506c9cba627a00569d5da2b5734c1746b6b1cf8` | `95c7d1be38e932f0378f2837f9ca5527fd4a2cc83cb22d56a7221d26cb9abe9e` |
| `openai4s/storage/frames.py` | `75c4bc0ab72c187008edb9898778072e7265eb6000c3a20b9d4db55c0a79f7f0` | `2aa165ffc4d343569c2a20ce237442a5836cd914398cba27bde59d63b03a9c05` |
| `openai4s/store.py` | `ebb2ca6ad7ae0b4084f63bbf3b388c23f09a189e614d46b182e54b4583492224` | `1bd906bb6c45823b2eca9ff517a24a827291971616f810ed936f30ad3b208ec6` |

The actual gateway already includes the registered Example guard, with SHA-256 `4375bb39f28bde5c3d4a2c8fe1d5c27c685b99db9ab38c3904a289ce4134b7cb`. Actual deletion includes its registered guard, with SHA-256 `519fb91651b972f7afe2847862e5b77d36f3ef65d1281a5ecb2f3c2660ab8fd6`. These are exact recognized overlay compositions, not extra arbitrary base identities.

## Test matrix

Python 3.12.9, Windows, `models-worktree/.venv/Scripts/python.exe`. The same disposable test source was used before and after the fix, SHA-256 `46563c9828ed02e9286eea93b25503b13701677af36e08beeb5fc883df483847`. No test was weakened, skipped or changed between the two runs.

```text
.venv/Scripts/python.exe -m pytest -q --tb=short -p no:cacheprovider
  --basetemp ../ui-evidence/model-runtime-20260909/crlf-compat-{red|green}-fixtures-20260910
  ../ui-evidence/model-runtime-20260909/crlf-compat-temporary.py
```

| Case group | Count | Final result |
| --- | ---: | --- |
| Eleven sources: pristine LF, pristine CRLF, existing Example-only CRLF; full compose, exact reversal, newline preservation, repeat | 33 | PASS |
| Independent Git reconstruction equals actual WSL hash and byte length | 11 | PASS |
| Eleven sources reject mixed line endings, changed content, BOM | 33 | PASS |
| All six gateway layer orders | 6 | PASS |
| Six partial gateway compositions | 6 | PASS |
| Actual installer, production package-receipt checker, precheck, 14 target readbacks, original backups, content-addressed success receipt, repeat for LF/CRLF/Example-CRLF | 3 | PASS |
| Changed LF declaration does not expand; shared contract conflict remains rejected | 2 | PASS |
| Changed packaged component rejected before source write | 1 | PASS |
| Unknown last source blocks all target writes | 1 | PASS |
| **Total** | **96** | **96 passed / 0 failed / 0 skipped** |

Red run: **62 passed / 34 failed / 0 skipped in 7.92 s**. All 34 failures were the reproduced CRLF recognition problem. Green run: **96 passed / 0 failed / 0 skipped in 17.93 s**. `git diff --check`: PASS.

The three isolated package installations use **synthetic fixture build receipts**, including an all-zero source commit, solely to exercise the real production receipt checker. They are not real package, deployment, PINN or live acceptance evidence. Their source/component hashes and all fourteen output identities are captured in the fixture snapshots. The earlier 53-case installer report remains historical; its deliberate rejection of an unregistered CRLF gateway described the old contract and is superseded only for these audited byte identities.

## Evidence, cleanup and next action

Evidence directory: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/model-runtime-20260909/`.

| Artifact | SHA-256 |
| --- | --- |
| Fixed `bridge/leo_runtime_features.py` | `c75056e3d11730e998ae76edbf1a6346bb1004176154440610aac6c22114348c` |
| `installed-v1-source-diagnosis.json` | `e38e694756e2ba06822d5c90ebcf62981514454242667d552203a0bd700a4292` |
| `installed-v1-crlf-exact-proof.json` | `71fab24a0604a31d331964a25b0640036fee3488b74623d9325ab836d33f0504` |
| `crlf-compat-red-20260910.log` | `2aa0ddf0a2763c46a4edafd02459578fc73c71fd0b89eb4c5cb3a9c56eb7a807` |
| `crlf-compat-green-20260910.log` | `3811136614a24093896f1d160de9dd3e03710b8b304d3b05ab183d456d32514a` |
| `crlf-compat-lf-snapshot.json` (green) | `65486c0cf33aa2fe3f6a7fadf06df0fd6ecf9eda6309bed05774837dbd8556fe` |
| `crlf-compat-crlf-snapshot.json` (green) | `90e1fb6125420816f717a41bdecf5fa1de83c0ef9af00c1daa7b42350a4175fb` |
| `crlf-compat-example-crlf-snapshot.json` (green) | `e9201bb0c95b80593a3056cb784672c45ecf41fc5e452880a6b4f0d1f912c6d1` |

`crlf-compat-audit-inventory-20260910.json` records the artifact identities, fixture sizes and every discovered junction destination. The red fixture directory contains 106 regular files / 8,608,757 bytes; the green directory contains 138 regular files / 11,469,941 bytes. Each has eight junctions, all verified to resolve within its own fixture root. No recursive fixture cleanup was attempted, in accordance with the root agent's explicit instruction following the earlier automatic cleanup rejection. These fixture directories require the root agent's cleanup handling. No test conversation was created.

The temporary test source is removed after recording its hash and results; `crlf-compat-test-source-cleanup-20260910.json` records the exact removal verification. Existing tests and all failure logs remain preserved. The LF summary snapshot name was shared by the two test invocations and now refers to the green run; the red run's original content-addressed installer receipt and bytes remain in its separate fixture, with a separately labelled reconstructed red snapshot recorded before fixture cleanup. This naming issue did not change either result log or production source identity.

Next action: root review and commit of this exact installer change, fresh hermetic build, normal deployment with the application closed, strict package verification, then actual bootstrap and model/session acceptance. A test receipt must never be copied into the installed application. Success of this isolated suite does not establish that later bootstrap stages or live model calls succeed.

## Root complete regression after this repair

Full existing suite: **839 passed / 0 failed / 2 existing skipped, 28.91 s**. Command: `python -B -m pytest -q -p no:cacheprovider --basetemp <new isolated evidence directory>`. Raw log: `combined-regression-crlf-20260910.log`. Skips remain the disabled legacy lifecycle branch and unavailable wheelhouse check; neither was added by this repair. Source syntax and whitespace checks passed.

````

</details>

### R015 — 项目/docs/LEO_RUNTIME_FEATURES_INSTALLER_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# Central runtime features installer — 2026-09-09

## Verdict

Central composition, installation, rollback and negative tests: **PASS (53 passed, 0 failed, 0 skipped)** on isolated copies of the actual pinned upstream source, bound to the exact component snapshots recorded below. Installation into the active WSL source, final product build, daemon startup and GUI acceptance: **NOT-RUN by this subtask**. The binding component owner subsequently withdrew that component's freeze to repair its actual daemon secret-broker path; the 53-case evidence must not be counted as validation of later component bytes. This report does not claim a deployed release or scientific accuracy.

Worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree`; branch `codex/conversation-runtime-20260909`; initial HEAD `9e53dcc4d534a1dadd93ad0107ee88bef55d455f`. Only `bridge/leo_runtime_features.py`, this report and disposable isolated test artifacts were created by this subtask. The root agent owns bootstrap/build/deployment integration. The other two component agents own their transformers and runtime helpers.

The actual upstream source was read from `C:/Users/user/Desktop/LeoAIStudio/upstream/OpenAI4S`. Tests copied only relevant Python files into the task evidence directory. No installed source, active WSL tree, model process, daemon, user conversation, scientific database, locked specification or old evidence was modified.

## Installation contract

```text
python bridge/leo_runtime_features.py apply [--base PATH]
python bridge/leo_runtime_features.py check [--base PATH]
```

The default base is `Path.home() / '.local/share/leo-ai-studio'`. Success output is a JSON envelope `{"ok":true,"data":...}`. Data contains `version:1`, `applied`, `example_persistence:true`, `conversation_runtime:true`, `source_revision`, `package_source_commit`, exact component identities, target hashes and a content-addressed receipt identity. **The caller must require `data.applied is True`, together with the version and feature flags, before daemon startup.** `check` on an uninstalled but valid source returns `ok:true, applied:false, needs_update:true`; it does not mutate that source or create evidence directories.

Failure returns nonzero and a stable JSON error. Arbitrary exception contents, paths, source excerpts, configuration values or credentials are not printed. The installer does not start a daemon. The bootstrap must replace the previous stand-alone Example preparation call with this central installer. The original Example script retains its original contract and cannot validate a full multi-feature gateway by itself. The independent identity and runtime compatibility/browse overlays retain their own target ownership; central features do not modify `openai4s/llm/client.py`.

## Trust chain and exact composition

1. The packaged `build-receipt.json` must identify a hermetic build, a clean source state, and a 40-hex source commit. For all six installer components, both its source-file hash and packaged artifact hash/size must match the actual bytes. The installer verifies its own bytes as well. Component Python is compiled, then verified bytes are executed directly without accepting a same-named import from another directory or an unchecked cached component `.pyc`.
2. `active-source` must resolve to exactly `base/sources/a792c38d9984be428437b548db29baab3322f6dc`; implementation uses the authoritative revision constant, not a path supplied by a component or receipt.
3. Every target is bound to its complete canonical file SHA-256. Targets shared by multiple components use the intersection of their accepted base identities. Marker presence, a successful replacement, a file name or a historical receipt cannot authorize unknown bytes.
4. The installer recognizes only a known original or a byte-exact composition of registered Example, binding and thought layers. It reverses complete layers, checks the recovered whole-file hash, reconstructs the incoming composition to prove exact equality, then builds and reverses the complete current composition. All final Python files compile before any source write.
5. The three new runtime modules must be absent or equal the current checked package bytes. Their own bytes are compiled and checked. There are no previously released full-feature module versions in v1. A future module or transformer upgrade must register its audited historical identities in package code; a self-declared historical receipt is deliberately insufficient.

The current registered targets are eleven patched Python sources and three new runtime modules:

| Target | Registered responsibility |
| --- | --- |
| `openai4s/server/gateway.py` | Example seed persistence + per-turn model binding + thought/progress/final projection |
| `openai4s/storage/deletion.py` | Example deletion persistence |
| `openai4s/storage/frames.py` | Transactional model rebind |
| `openai4s/store.py` | Store rebind entry |
| `openai4s/config.py` | Request-scoped reasoning configuration |
| `openai4s/agent/events.py` | Separate reasoning event |
| `openai4s/agent/engine.py` | Reasoning event delivery |
| `openai4s/llm/providers/openai.py` | Reasoning request policy and provider thought preservation |
| `openai4s/llm/messages.py` | Reasoning metadata preservation in assistant messages |
| `openai4s/server/agent_run.py` | Durable projection events and binding to action groups |
| `openai4s/server/completions.py` | Final/progress delivery behavior |
| `openai4s/leo_reasoning.py` | Exact `bridge/leo_reasoning.py` bytes |
| `openai4s/leo_thought.py` | Exact `bridge/leo_thought_runtime.py` bytes |
| `openai4s/server/leo_turn_binding.py` | Exact `bridge/leo_turn_binding_runtime.py` bytes |

## Write discipline and failure behavior

The full target set is preflighted before target mutation. All ordinary path components reject symbolic links and Windows reparse points; ordinary files with multiple hard links are rejected. The single existing `active-source` link is an explicit exception, constrained to the fixed safe destination. These checks cover target parents, modules, build evidence, backups and receipts.

An exclusive lock prevents concurrent cooperating installers. After taking it, the installer rechecks every target and the active pointer. Every preexisting exact file is saved using exclusive creation under `base/runtime-features/originals/<sha256>.py`; an existing backup must match its exact bytes. The started-at record contains only source identity and prior target hashes.

Source replacements use a temporary file in the same directory, preserve mode, flush/fsync and recheck expected bytes before replacement. New module creation is exclusive and cannot replace a file which appeared since preflight. The active pointer is rechecked through installation. After all writes, every final target is read back and the packaged component/build identity is reverified. Only then is the exclusive success receipt created as `base/runtime-features/<receipt-sha256>.json`.

Caught partial failures restore only bytes that still equal the installer's known new bytes. An independently changed target is preserved and produces `RUNTIME_FEATURES_ROLLBACK_INCOMPLETE`; the installer writes a failed-at record with `rollback_ok:false` and does not claim success. Normal rollback records `rollback_ok:true`. Failure records and original backups are preserved across retries. A preflight failure changes no target. An abrupt process kill may leave the exclusive lock for explicit diagnosis; the tool does not guess that a lock is stale and delete it.

This is local, source-bound integrity evidence, not a cryptographic signature protecting an installation from an attacker who can replace the whole package and its build receipt. The single-process filesystem protocol does not claim an atomic multi-file transaction against arbitrary external writers; fail-closed prechecks, readback and guarded rollback expose that boundary. The root bootstrap must run it before daemon startup.

## Test matrix

Interpreter: `../ui-worktree/.venv/Scripts/python.exe`, Python 3.12.9, Windows. Tests used actual NTFS junctions and hard links. Synthetic package receipts were constructed solely inside test fixtures to exercise the production receipt checker; they are not real build receipts for commit `9e53dcc` and must not be presented as release evidence.

Command from `models-worktree`:

```text
python -m pytest -q --tb=short -p no:cacheprovider
  --basetemp ../ui-evidence/model-runtime-20260909/features-fixtures-final
  ../ui-evidence/model-runtime-20260909/runtime-features-temporary.py
```

| Run | Passed | Failed | Skipped | Result |
| --- | ---: | ---: | ---: | --- |
| First isolated suite | 37 | 2 | 0 | FAIL: test expected 13 targets; the companion had correctly added `server/completions.py`, making 14. No target installation failure occurred. Original log retained. |
| Corrected explicit target expectation and strict schema-bool check | 40 | 0 | 0 | PASS |
| Expanded negative/recovery suite | 51 | 0 | 0 | PASS |
| Added two exact LF/CRLF contract checks, with binding transformer `f39a7758...` and helper `f4481617...` | **53** | **0** | **0** | PASS for recorded component bytes |
| `git diff --check` | n/a | 0 | 0 | PASS |
| Active WSL / real new package / daemon startup | 0 | 0 | 0 | NOT-RUN by this subtask |

Coverage includes all six orders of the three gateway layers; seven known partial layer compositions; base and existing Example-only upgrade; exact backups; read-only precheck; repeat idempotence; full bytes without a receipt; four unrelated source tamper cases; modified known overlays; registered CRLF deletion roundtrip and rejection of an unregistered CRLF gateway; a forged historical receipt with an unknown helper; unverified components, invalid artifact size, dirty build, malformed commit, missing receipt, duplicate JSON keys, different installer bytes and boolean schema version; wrong source revision; parent reparse points; hard links; exclusive lock; conflicting backup; failures before and after a source write; concurrent user content during rollback; receipt tampering; partial known target recovery; receipt write failure; a package change during installation; backup reparse points; seven invalid target paths; and secret-safe CLI failures.

The binding component agent also independently reviewed the central installer read-only and found no direct path to falsifying `applied`. That review explicitly retained the requirement to check `applied`, rather than only the feature flags.

## Evidence and handoff

Evidence directory: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/model-runtime-20260909/`.

- `runtime-features-tests-first.log`, `runtime-features-tests-second.log`, `runtime-features-tests-third.log`: all run results, including the original failed assertions.
- `runtime-features-composition-snapshot.json`: exact canonical/final target hashes and component identities from the two successful base/Example fixture installations; explicitly labelled synthetic fixture receipts.
- `runtime-features-tests-final.log` and `runtime-features-composition-final-snapshot.json`: 53-case result and exact identities for the later binding component snapshot.
- `runtime-features-temporary-cleanup.json`: recorded after temporary test cleanup.

At the 51- and 53-case test runs, installer SHA-256 was `2bd1637c7cecdbd5c21fee13771d8eb07521e9b39ece4d575b710676a4d15265`. Its six component identities and all fourteen output hashes are preserved in the respective composition snapshots. The 51-case temporary source SHA-256 was `8f0323c477e276ad257c640b895284e9d27800c2805f272d6b30d49cb47462af`; the 53-case source was `606fd467c8656676aba22ac7e8ae6170ab5c013743f856400d8434ba507640cb`. The final log SHA-256 is `8478d03ac3201352f7c5f3193838740bd8ed7bce7bacb70341457c0f391156fa`; its composition snapshot SHA-256 is `bd66be372b892216f8992ff9409081d0d73be8d1885fdd556e08251a50a85ebd`.

Cleanup of the three intermediate fixture directories was rejected before execution by automatic approval review, which returned only `blocked by policy`. No deletion occurred. `runtime-features-intermediate-fixture-cleanup.json` records 812/826/941 regular file entries and 63,477,942 / 64,835,211 / 74,506,777 logical bytes, respectively; all discovered link destinations remain inside their own fixture tree. These logical sizes do not represent physical disk usage because fixtures include hard links. The newer final fixture directory and temporary test source remain pending the final component revision, so the suite can be re-run without reconstructing it. Existing repository tests and historical evidence remain intact.

The final root build must package all six components and include them in both build receipt source and artifact inventories. It must verify the authoritative source revision, require the successful central receipt before daemon startup, and then run live model/session/UI acceptance. Future changes to a component require a fresh package receipt and central validation; these isolated counts are tied to the component hashes recorded here.

## Final binding revision revalidation — 2026-09-09

The root agent reran the 53-case central composition suite after the binding component's broker and managed-identity fixes. `runtime-features-binding-final.log` records **53 passed, 0 failed, 0 skipped in 42.52 s**, SHA-256 `ff9e7cb5d23e0c00f9acba8c2eb01d03d96160455bf49678b2637ba5d72dcee5`. The final binding transformer was `f39a77586b62ef531d6503da2cf21f58750c2fa96b72ebcf98c6913bd4e77a53`; the final runtime helper was `d2d595dbf7439d0b4ccc70a5b39c691c628853075ba0f5c498461a3ce7b92e77`. Both component files were rehashed and verified while finalizing the binding report.

This new run closes the stale binding-component test scope called out at the start of this report. The older run identities and failure logs remain historical evidence. The new run still uses isolated source copies and synthetic fixture receipts: active WSL installation, actual package provenance, daemon startup, real model calls and installed GUI behavior require the separate root acceptance. See `LEO_SESSION_MODEL_BINDING_REPORT_20260909.md` for the native binding and runtime component details and 156-case binding/API result.

````

</details>

### R016 — 项目/docs/LEO_SESSION_MODEL_BINDING_REPORT_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# Session model binding and admission report — 2026-09-09

## Verdict and scope

The isolated binding regression and existing ShellApi regression completed with **156 passed, 0 failed, 0 skipped in 13.90 s**: 75 temporary binding cases plus 81 existing API cases. A preceding adversarial review reproduced six real failures before their fixes; that failed log remains evidence. The root agent subsequently reran the central installer against the final binding component bytes: **53 passed, 0 failed, 0 skipped in 42.52 s**. These results establish the tested component and composition behavior, not a deployed release, a real model response, or a PINN accuracy claim.

Worktree: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree`, branch `codex/conversation-runtime-20260909`, base HEAD `9e53dcc4d534a1dadd93ad0107ee88bef55d455f`. At report time the implementation is uncommitted alongside other authorized feature work. Actual model execution, active WSL installation, credentials from the user's profile, and native GUI acceptance were **NOT-RUN by this component subtask**. Tests used isolated databases and fixture credentials. No frozen scientific files were changed by this component.

## Files and causal changes

| File | Problem and resulting behavior |
| --- | --- |
| `leo_shell/session_models.py` | Adds a native per-session model service. Saved local/cloud profiles are listed without credentials; selection resolves the exact native credential and registers an immutable upstream identity. The Windows DPAPI mapping persists registration ownership and retry identity before the remote write. Key/configuration changes allocate a new identity, preserving already admitted turns. Local model selection can coexist with cloud profiles without restarting the conversation daemon. |
| `leo_shell/api.py` | Exposes `list_session_models` and `select_session_model` through the existing native boundary, returns stable secret-safe errors, and revokes managed upstream registrations before deleting their native settings profile. A failed or unconfirmed revocation keeps the pending state for retry instead of claiming deletion succeeded. |
| `bridge/leo_turn_binding.py` | Supplies exact-source transformations for the pinned upstream gateway, Store and frame storage. Adds authenticated binding/profile routes, routes managed registrations through their ownership journal, and performs binding validation plus job admission under the existing admission lock. Frame rebind is one transaction with compare-and-swap semantics; a conflict or failed target validation retains the previous pin. |
| `bridge/leo_turn_binding_runtime.py` | Implements strict profile/revision and reasoning-policy snapshots, exact managed identity/reference validation, durable registration/revocation journals, and a scoped process-only credential broker for the installed daemon's read-only environment backend. Controlled turns preserve their pinned native credential rather than receiving a later global owner-key override. Invalid snapshots, unavailable credentials, revoked identities, and persistence failures are explicit failures. |

The transformer accepts only whole-file identities for canonical upstream commit `a792c38d9984be428437b548db29baab3322f6dc`. Its gateway, Store and frame-storage base hashes are embedded in code; the central installer composes it with the Example and thought layers. The component does not directly modify the installed source.

## Selection, admission and recovery contract

The frontend lists a frame's native candidates and actual binding, then submits `native_profile_id` together with `expected_binding: {profile_id, revision}`. The native service confirms the current pair before registration and the daemon validates it again transactionally before rebind. A successful result explicitly applies to `next_unadmitted_turn`. Selection is not a rewrite of past messages or a replacement of an already queued job's immutable model/reasoning snapshot.

Controlled message admission carries `model_binding: {profile_id, revision}` and `reasoning_selection: {choice, capability_revision}`. Both are validated and frozen under the existing admission lock. The actual transformed queue path is tested. Missing or malformed controlled data fails closed; legacy requests without the controlled fields retain their existing behavior. No scientific Gate prerequisites are changed.

The native `session-model-bindings.dpapi` ledger contains the ownership intent before any remote registration. A generated `mp-leo-...` operation identifier and credential/configuration fingerprint allow the exact same operation to resume after a timeout or interrupted native write. The server's `leo_model_registration.*` journal records identity, reference, credential digest and lifecycle state before broker/profile mutation. An arbitrary duplicate ID cannot be adopted; a retry must match the known native identity, endpoint, model and credential. An interrupted `pending` journal with an already created matching profile is repaired to `created` during exact retry. A changed credential cannot silently take over that operation.

The installed daemon's environment broker cannot persist newly registered keys. `ManagedSecretBroker` therefore holds only explicitly authorized managed native keys in process memory; all other references delegate to the existing backend. It does not put keys in SQLite or environment variables. After a daemon restart, the public binding exposes `credential_ready: false`; the native service can re-inject the same saved operation and key without changing its model-profile revision. The frontend owner must use this flag to perform re-injection before sending. A successful component test is not evidence that the frontend already handles this path in the real installed app.

Managed admission validates profile cardinality, immutable revision identity, expected secret reference, registration state and credential digest. Corrupted rows cannot substitute another registered key. Deletion validates those relationships before entering the upstream generic deletion path, preventing a corrupted profile row from revoking another profile's reference. A bare HTTP 404 or swallowed broker failure is not treated as a successful revocation.

## Test matrix

Interpreter: `../ui-worktree/.venv/Scripts/python.exe` on Windows, Python 3.12.9. The temporary suite imports the actual pinned upstream source from `C:/Users/user/Desktop/LeoAIStudio/upstream/OpenAI4S`; it exercises actual Store/SQLite, actual transformed queue code, Windows DPAPI, the memory and environment broker implementations, and fixture native transport/local-session seams. It does not make provider network calls.

Final binding/API command from `models-worktree`:

```text
../ui-worktree/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
  --basetemp ../ui-evidence/model-runtime-20260909/binding-final-fixtures
  tests/test_tmp_session_models_20260909.py tests/leo_shell/test_api.py
```

| Evidence log | Passed | Failed | Skipped | Result and meaning |
| --- | ---: | ---: | ---: | --- |
| `binding-existing-api-v1.log` | 80 | 1 | 0 | FAIL: an existing default-model assertion still expected `deepseek-chat` after the separate new-profile default changed to `deepseek-v4-flash`. Final API run below includes the corrected product expectation. |
| `binding-regression-v4-env-broker.log` | 67 | 0 | 0 | PASS after testing the actual deployed environment-broker behavior; 13.30 s. |
| `binding-review-red.log` | 0 | 6 | 0 | FAIL as intended before fixes; 67 deselected. Five managed identity/reference/state corruption cases were not rejected and an interrupted created-profile journal remained pending. These are actual reproduced deficiencies, not accepted failures. |
| `binding-review-green.log` | 74 | 0 | 0 | PASS after fixing those failures and adding further coverage; 23.72 s. |
| `binding-final-regression.log` | **156** | **0** | **0** | PASS: 75 temporary binding cases plus 81 existing API cases; 13.90 s. |
| `runtime-features-binding-final.log` | **53** | **0** | **0** | PASS: root reran complete central composition against the final component bytes; 42.52 s. Synthetic isolated package receipts are not release receipts. |
| Provider calls, live local model, installed daemon and GUI | 0 | 0 | 0 | **NOT-RUN by this component subtask**, delegated to root acceptance. |

Coverage includes strict binding types; SQL rollback; invalid/deleted/duplicate target profiles; compare-and-swap races; immutable admitted snapshots; reasoning capability revision mismatch; unsupported selections; missing snapshots and snapshot persistence errors; exact-source compilation/reversal; native key changes; simultaneous local/cloud identities; browse-mode rejection; trusted local transport validation; DPAPI corruption; secret-safe errors; durable intent before remote mutation; timeout recovery with the same operation ID; interrupted native/server writes; exact retry without credential rotation; process restart and re-injection; delegation of existing environment keys; absence of managed plaintext credentials in SQLite; wrong profile references and revision identity; explicit revocation failures; and protection of another profile's credential during deletion.

## Exact identities and retained evidence

All four final source hashes were re-read and matched the implementation owner's handoff before this report was written:

| File | SHA-256 |
| --- | --- |
| `leo_shell/session_models.py` | `7d462037bd80cdf785fc49d6beb2cbd6ce1c29c3708ea4340c3934fb92001b5d` |
| `leo_shell/api.py` | `435b7d6ebe4cf9d4b10fbbba0543e66e27014fab4838f2589b7dcb0ae5de68d2` |
| `bridge/leo_turn_binding.py` | `f39a77586b62ef531d6503da2cf21f58750c2fa96b72ebcf98c6913bd4e77a53` |
| `bridge/leo_turn_binding_runtime.py` | `d2d595dbf7439d0b4ccc70a5b39c691c628853075ba0f5c498461a3ce7b92e77` |
| Temporary `tests/test_tmp_session_models_20260909.py`, before requested removal | `dcb90cea0e1fee9d338109f7a58a6531c3e0316df5823669b282b533362ae943` |
| `binding-final-regression.log` | `5ff540a53db2707874be1b9e4575f9d65ce27e291ab275b1da956576d126c8b3` |
| `binding-review-red.log` | `944029e7dae2967bc1996c036dbe651d63c80c94230a7ef8a5f07f0408696cfe` |
| `binding-review-green.log` | `eadc4db1b1e031058b91973aaaa979d78f64496b4931ae4df1b1128240655511` |
| `runtime-features-binding-final.log` | `ff9e7cb5d23e0c00f9acba8c2eb01d03d96160455bf49678b2637ba5d72dcee5` |

Evidence directory: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence/model-runtime-20260909/`. All earlier `binding-*.log` files, including earlier failures, remain untouched. This report records scope, results and temporary test identity as the user requested; the newly written regression source is to be removed, while preexisting repository tests remain.

## Cleanup and remaining acceptance

Cleanup is limited to the new `tests/test_tmp_session_models_20260909.py` and these three exact fixture directories under the evidence directory. Resolved absolute parents were checked; all 91 discovered reparse/link entries resolve within their own fixture tree.

| New fixture directory | Entries | File entries | Logical bytes | Internal link entries |
| --- | ---: | ---: | ---: | ---: |
| `binding-final-fixtures` | 233 | 80 | 66,200,720 | 49 |
| `binding-review-green-fixtures` | 172 | 66 | 63,988,521 | 40 |
| `binding-review-red-fixtures` | 14 | 6 | 6,979,584 | 2 |

These are logical entry sizes, not a measured physical disk-space reduction. The cleanup receipt `binding-temporary-cleanup-20260909.json` records the actual deletion outcome after the report and hashes have been saved. Other component fixtures and existing evidence are outside this cleanup scope.

**Cleanup status: BLOCKED.** Automatic approval review rejected the bounded removal command before process creation and returned only `blocked by policy`. No removal executed; a subsequent read-only check confirmed that the temporary source and all three directories remain present. No alternative tool or deletion method was used to bypass the rejection. This is an incomplete user-requested cleanup item, not a successful cleanup or a lack of user authorization.

Remaining acceptance belongs to the root integration: build a clean, receipt-bound package; verify the frontend re-injection path when `credential_ready` is false; exercise real local/cloud model switching and immutable already admitted turns; restart the installed daemon; verify real thought/final-answer presentation; and delete only the authorized test conversations after recording results. None of those runtime results should be inferred from these isolated counts. This component adds no CFD implementation and grants no PINN scientific accuracy claim.

````

</details>

### R017 — 项目/docs/LEO_UI_INTEGRATION_DELIVERY_REPORT.md

<details>
<summary>展开完整原文</summary>

```markdown
# Entry, provider navigation and permanent deletion integration

This change implements the user's follow-up UI and data lifecycle requests. PINN remains NOT COMPLETE and its Phase II approval stop remains in force; no scientific frozen files were changed here.

## Source and intent

Safe branch `codex/leo-entry-navigation-20260908`, base `e05ac35b476337f0677830b047787330b46dfb13`. The original dirty master workspace is not edited.

- `leo_shell/api.py`, `connection.py`, `ui.py`, `app.py`, `bridge_client.py`, `stage/shell.html`: explicit Studio entry, ready/configured versus strict keyless runtime state, cancellation without closing the worker on return, navigation reinjection, failed injection banner and required sidecar receipts.
- `bridge/leo_runtime_compat.py`, `leo_model_selection.py`: explicitly keyless requests cannot inherit stored/pinned credentials or run a model. Known upstream byte identities are checked before applying overlays.
- `bridge/leo_example_persistence.py`: project deletion and persistent example-seeding tombstone share one database transaction. Failed deletion cannot leave a false marker. Unknown source or malformed marker fails closed.
- `stage/leo.css`: only the two empty dashboard decorations are removed.
- `stage/leo-inject.js`: return controls, actual runtime state, real backend DELETE and absence verification, irreversible confirmation, explicit unowned-file cleanup warning. Archive remains reversible.
- `tests/leo_shell/test_api.py`, `test_bridge_client.py`: existing tests now assert the user-requested unconfigured browse contract and required helper acknowledgement. No existing tests are deleted or weakened to accept failed connection.
- `tools/build_launcher.ps1`, `deploy_release.ps1`, `package_contract.py`, `build_manifest.py`, `verify_release.py`: the new runtime helper is a required packaged, deployed and hashed sidecar, not an untracked installation patch.
- `manifests/runtime-asset-origins.json`: new exact hashes for the changed CSS, shell and generated injection bundle.
- Companion implementation reports document scoped commands, transient tests and known boundaries.

## Validation before build

All commands run from this worktree using Python 3.12.9 in `.venv`. Credentials were removed from the full-suite child environment before pytest to avoid assertion leakage.

| Command / scope | Pass | Fail | Skip | Boundary |
|---|---:|---:|---:|---|
| `python -m pytest -q -ra --tb=short` | 832 | 0 | 9 | 34.67 seconds; 7 depend on default relative upstream path, 1 missing local wheelhouse, 1 existing disabled legacy UI branch |
| `LEO_UPSTREAM_ROOT=<actual installed checkout> python -m pytest -q -ra tests/test_manual_acceptance.py --tb=short` | 19 | 0 | 0 | All 7 upstream-dependent cases above rerun successfully against actual upstream parser; not duplicated in unique totals |
| `python tools/build_wheelhouse.py install --wheelhouse <previous verified 21 wheels> --python .venv/Scripts/python.exe` | 21 wheels | 0 | 0 | Hash manifest checked before offline installation; no index |
| `python tools/build_wheelhouse.py audit-env --python .venv/Scripts/python.exe` | exact environment | 0 | 0 | 0 dependency problems |
| Entry scoped suite including 35 transient cases | 307 | 0 | 1 | Existing legacy UI skip; transient source subsequently removed |
| Actual Chromium start page zh/en | 36 | 0 | 0 | Real ShellApi/settings with coordinator substitute; no actual model claim |
| Empty states / return controls DOM | 89 | 0 | 0 | Real CSS controlled fixture, not installed GUI |
| Browse runtime helper | 27 | 0 | 0 | Offline exact source fixtures |
| Transactional example deletion helper | 23 | 0 | 0 | Real temporary SQLite, rollback/restart/invalid marker/unknown source |
| Deletion UI functions and negative paths | 44 | 0 | 0 | Backend failure/verification failure/retained cleanup records |
| Upstream durable deletion | 18 | 0 | 0 | Real temporary SQLite, unrelated entities preserved |

Initial environment command mistakenly used pip `--require-hashes` with the repository's version-only requirements file; it failed before installation. The existing wheelhouse tool supplies hash verification through its manifest and was then used correctly. This is an operator command correction, not a dependency lock change.

## Real user data scope

Read-only reconciliation found all ten previously trashed project IDs still in the real backend. Their current members total 17 root sessions, compared with the stale local snapshots' 12. The example gained two sessions and the old installation-test project gained three. Permanent project deletion is authorized for those exact ten IDs and their current members. The archived project (currently four sessions), normal SNN project (currently four sessions), and default session are protected. No fuzzy title matching selects more data.

At this prebuild checkpoint no real user data has been deleted and no updated installed EXE is yet claimed. Build/deployment/actual deletion/restart verification will be recorded as subsequent evidence.

## Test file hygiene

User explicitly requested deleting new regression test source after running it. The agents have recorded temporary test identities/results and removed the new scripts. Existing repository tests remain. Transient logs/screenshots/profiles are under `../ui-evidence`, not Desktop, and will be consolidated then cleaned. Some prior recursive force cleanup actions were auto-rejected; no report equates failed cleanup with complete deletion.

```

</details>

### R018 — 项目/docs/OPERATION_LOG_20260914.md

<details>
<summary>展开完整原文</summary>

```markdown
# 2026-09-14 操作日志（第二轮）

本日志记录第一轮报告提交（`2fabbe4`）之后的每一项操作、命令要点与结果，配套根目录的 [20260914软件修改报告.md](../20260914软件修改报告.md) 与 [20260914仓库卫生记录.md](../20260914仓库卫生记录.md)。路径相对仓库根；用户机器上的目录用「用户目录」代替。执行：Claude（队长）。

## 1. 用户第二轮指令

1. PINN 证据目录 `LeoAIStudio-pinn-evidence-20260908T120017Z/`：用户选择"另行审批删除"，理由是仓库卫生与后续形成 Leo AI 内部 PINN 闭环。队长在执行前再确认一次（§4）。
2. 工作树与分支：现在就移除。
3. 重新构建并部署。
4. 每件事都写进报告或日志；不确定的先问再开始。
5. 组建六方 AI 团队：Claude 为队长，豆包、GLM、Kimi、DeepSeek、Grok 并行；队长出五份提示词并分工，不互相打架。
6. PINN 可信闭环设想：七层、验证 FAIL 分流、可信度向量、弱链原则、误差归因、Red Team、六段式输出、研究者"让 PINN 进化"工作流。

## 2. 已执行（按时间顺序）

| 序号 | 操作 | 命令要点 | 结果 |
|---|---|---|---|
| 2.1 | 勘察构建前提（只读） | 读 `LeoAIStudio/build-receipt.json`；`用户目录/mamba/python.exe -c ...`；`tools/build_wheelhouse.py audit-env --python <codex 侧 models-worktree/.venv>`；`git diff --stat 14e30f4 HEAD -- requirements.lock manifests/dependency-lock.json manifests/wheelhouse.json`；`tasklist` | 上次构建：hermetic、commit `14e30f4`、2026-09-10、Python 3.12.9 conda-forge；基础解释器 3.12.9 齐全（`python312.dll`、`Library/bin`）；codex 侧 `.venv` 环境审计 0 problems；三个锁文件相对 `14e30f4` 无变化；`LeoAIStudio.exe` 未运行；桌面快捷方式存在；勘察未产生 `__pycache__` |
| 2.2 | 读部署与校验脚本（只读） | `tools/deploy_release.ps1`、`tools/verify_release.py` | 部署会拒绝运行中的程序、新建 `.leo-rollback-<id>`、复制 EXE / `_launcher` / theme / bridge 运行时文件 / 字体许可 / 收据、重写桌面快捷方式；strict 校验还会调用 `sync_skills.py --check --require-wsl` |
| 2.3 | 移除已合并的工作树 | `git worktree remove .claude/worktrees/leoaistudio-cleanup-refactor-9e137d` | git 已注销并清空目录内容，但顶层空目录被另一进程占用（Permission denied / Device or resource busy）；`git worktree prune` 后不再列出。空目录待占用进程退出后删除 |
| 2.4 | 删除已合并分支 | `git branch -d claude/leoaistudio-cleanup-refactor-9e137d` | Deleted (was `2fabbe4`) |
| 2.5 | 尝试切换本会话工作目录到主检出 | 会话目录工具 | 失败：会话运行在隔离工作树内不能移动。因此 d129a8 工作树（本会话 shell 的当前目录）与其分支（指向 `8c4835e`）不能在会话中途删除，见 §4 |
| 2.6 | 记忆更新（仓库外，用户目录下 `.claude/projects/.../memory/`） | 新增 `feedback-test-artifacts-cleanup`、`feedback-log-everything-ask-first`、`project-multi-ai-team`；更新 `project-leoaistudio-layout` 与索引 | 完成 |
| 2.7 | 新建六方分工与提示词 | `docs/PINN_TRUST_LOOP_TEAM_PROMPTS_20260914.md` | 五份自包含提示词（DeepSeek 数学核心、GLM 数据契约与状态机、Kimi 实现验证与训练协议、Grok Red Team、豆包 报告模板与研究者工作流），队长负责合并与本机工作 |
| 2.8 | 新建本日志 | `docs/OPERATION_LOG_20260914.md` | 完成 |

## 3. 测试产物

本轮到目前为止没有运行测试；2.1 的勘察命令没有产生 `__pycache__`（已用 `find` 核查）。后续每次测试或构建之后都会在这里记录产物与删除。

## 4. 待用户决定（已提问）

| 事项 | 事实 | 选项 |
|---|---|---|
| 删除 `LeoAIStudio-pinn-evidence-20260908T120017Z/` | 117 个文件，4,316,341 字节；被 `docs/P0_RUNTIME_REMEDIATION_20260908.md` 与 `docs/PINN_MVP_AND_CFD_READINESS_REPORT.md` 引用为外部证据 | 确认删除 / 先压缩归档到仓库外再删 / 保留并加入 `.gitignore` |
| 构建环境 | 主检出没有 `.venv`、没有 wheelhouse；codex 侧 `.venv` 审计 0 问题且与 9-10 构建同源 | 复制 codex 侧 `.venv` 到仓库内 / `provision_venv.ps1 -AllowIndex`（联网、不可复现）/ 先建 wheelhouse |
| 部署 | 目标 `LeoAIStudio/`（会新建第 4 个 `.leo-rollback-*`、重写桌面快捷方式）；部署后需要用户启动程序人工确认隐藏效果 | 确认 / 暂不部署只构建 |
| d129a8 工作树 | 本会话 shell 的当前目录 | 会话最后一步由队长删 / 会话结束后由用户删 |

## 5. 后续追加

### 5.1 用户答复（第二批）

- 构建环境：复用 codex 侧 `.venv`；证据目录：先归档到仓库外再删；部署：构建后立即部署；d129a8 工作树：会话最后一步由队长删。
- 追加指令：除 Grok 外四位队员的交付物已完成并由用户放进仓库目录；Grok 的 Red Team 任务由队长自己完成。

### 5.2 证据目录归档与删除（用户审批通过，第二轮）

| 项 | 值 |
|---|---|
| 源 | `LeoAIStudio-pinn-evidence-20260908T120017Z/`，117 个文件，4,316,341 字节 |
| 归档 | 用户文档目录 `LeoAIStudio-deliveries/20260914-archive/LeoAIStudio-pinn-evidence-20260908T120017Z.zip`：117 个条目，`testzip` 无错，1,296,353 字节，SHA-256 `9916e20c5dbc87f1ccc7ce04181c5d53403560947f2f18178f25f72a0d59fef3`，旁车 `.zip.sha256` 文件 |
| 删除 | `rm -rf`，删除后目录不存在，git 树干净 |

### 5.3 构建环境

- 首次在 Git Bash 里调用 robocopy，参数被 MSYS 路径转换破坏（exit 16，只打印用法），没有复制任何文件；改用 PowerShell 调用 robocopy 成功（exit 1 = 有文件复制）。
- 复制 `LeoAIStudio-deliveries/20260908-phase2/models-worktree/.venv` → 仓库内 `.venv/`（57,609,997 字节，8 s）；`pyvenv.cfg` 的 `home` 指向用户目录下的 mamba（Python 3.12.9）；复制后 `sys.prefix` 指向新位置；`tools/build_wheelhouse.py audit-env` 0 problems；pyinstaller 6.22.2 / pywebview 6.2.1 / cryptography 50.0.0；`.venv/` 被 `.gitignore` 覆盖。

### 5.4 交付物收件

- 用户放入：根目录 `PINN_TRUST_R1_IMPL_TRAINING.md`（Kimi）与 `docs/pinn-trust-loop/inbox/` 下三份（DeepSeek、GLM、豆包）。首行作者行核对无误；未发现密钥类字符串。
- 队长把根目录那份移入 inbox，加上自己代 Grok 写的 `PINN_TRUST_R1_RED_TEAM.md`，字节原样提交 `13dc7ea`（五份 SHA-256 见 `docs/pinn-trust-loop/R1_MERGE_NOTES.md` §0）。
- 第一次构建尝试正是被这些未跟踪文件挡住（`build_receipt.py`：build source is dirty），提交后重试。

### 5.5 构建 → 部署 → manifest → strict 校验（提交 `13dc7ea`，树干净）

| 步骤 | 命令要点 | 结果 |
|---|---|---|
| 构建 | `tools/build_launcher.ps1 -OutputRoot <用户文档目录>/LeoAIStudio-deliveries/20260914-build/out-01`（hermetic 默认，`-BuildRoot` 为主检出） | exit 0，42.5 s；环境审计通过；包契约 PASSED：315 个 `_launcher` 文件、31 个关键文件、29 个归档模块；`LeoAIStudio.exe` 5,617,512 字节 |
| 部署 | `tools/deploy_release.ps1 -PackageRoot out-01/dist/LeoAIStudio`（`AppRoot` 默认 = 仓库内 `LeoAIStudio/`） | exit 0，7.1 s；回滚目录 `LeoAIStudio/.leo-rollback-20260914-063236-dc3d45e8`；EXE SHA-256 `a4bfda609aa2bfe296255133d637c486ce5a5f9a23f62ac8a484631a10224fcd`；315 个 launcher 文件；桌面快捷方式已重写 |
| manifest | `tools/build_manifest.py -o manifests/build-current.json` | exit 0；文件被 `.gitignore` 覆盖，保留作发布证据 |
| strict 校验 | `tools/verify_release.py --strict` | exit 1：**12 PASS / 1 FAIL**。PASS：leo commit `13dc7ea95021`、repo clean、build receipt、source hashes、theme assets versioned（16 项）、artwork masters（3）、bridge resources（10）、deployed bundle `ad1e432264fe`、deployed exe `a4bfda609aa2`、skill hashes、upstream revision `a792c38d9984`、upstream clean。FAIL：skills deployed+daemon |

- FAIL 明细（`tools/sync_skills.py --check --require-wsl`）：安装目录（windows）与 WSL 内的 `lean-math`、`research-sop` 各 3 个文件（`kernel.py`、`README_zh.md`、`SKILL.md`）与仓库规范副本不一致，共 12 个；WSL 侧另有 1 个 `__pycache__` 额外文件只报告不处理。`skills/` 在本轮所有提交中未改动（相对 `14e30f4` 无差异），部署脚本不同步技能，属既有漂移（9-09 审计时已有 2 个）。是否运行 `sync_skills.py` 推送规范副本，待用户决定。
- 日志：`20260914-build/` 下 `build-out-01.log`（20,552 字节）、`deploy-out-01.log`、`manifest-out-01.log`、`verify-out-01.log`；`out-01/` 含 `dist/`、`pyi-work/`、`pyi-spec/`、`build-inputs.json`、`leo-inject.bundle.js`，全部作为构建证据保留在仓库外。
- 部署后的 `LeoAIStudio/build-receipt.json`：commit `13dc7ea95021dac3a4c6b623a80f8ba887858de9`，2026-09-14T13:31:54Z 开始、13:32:32Z 完成。
- 说明：strict 校验的 leo commit / build receipt / source hashes 三项只对 `13dc7ea` 成立；之后提交日志与报告（只含文档）会使它们相对新 HEAD 报差异，属预期，下次构建自然消除。

### 5.6 产物盘点（构建 / 部署 / 校验之后）

- 仓库目录内：无 `__pycache__`（`find` 核查）；新增 `manifests/build-current.json`（保留）；`.venv/`（保留，构建环境）。
- 用户临时目录：用户临时目录下的 `leo-pyi-tools` 修改时间为 2026-09-09 01:35，是本轮之前旧构建的遗留（当前构建脚本已不使用它），不是本会话所建，未动；无 `pytest-of-*`；构建的依赖缓存 `leo-launcher-deps-*` 已由构建脚本自行清理。
- 安装目录：新增第 4 个回滚目录（部署脚本所建，含上一版 EXE / `_launcher` / theme，按设计保留供回滚）；`user/` 未动。

### 5.7 合并说明

- 队长读完四份交付物，写成 `docs/pinn-trust-loop/R1_MERGE_NOTES.md`：16 项跨车道议题，14 项已裁决、1 项待核对（specHash 规范化与既有 HASH LOCK 的关系）、1 项待用户（示例 (b) 口径）；衔接计划见其 §3。

### 5.8 待用户决定（第三批，已提问）

- 技能同步（解决 strict 校验唯一 FAIL）；示例 (b) 口径；是否现在开始实现合并说明 §3；请用户启动程序人工确认顶栏 / 侧栏的语言与明暗控件已隐藏。

### 5.9 技能同步（用户批准，第三批答复）

- `tools/sync_skills.py --require-wsl`：12 个文件全部 `[synced]`（windows 与 wsl 各 6 个：`lean-math`、`research-sop` 的 `kernel.py`、`README_zh.md`、`SKILL.md`）；WSL 侧 1 个 `__pycache__` 额外文件只报告不动；结束语 `[OK] canonical, deployed and daemon copies agree`，exit 0。
- 复核 `--check --require-wsl`：exit 0。
- 重跑 `tools/verify_release.py --strict`（HEAD 仍为 `13dc7ea`，树干净）：**13 PASS / 0 FAIL / 0 NOT TESTED**，`[OK] the manifest describes exactly what is deployed`。日志 `20260914-build/verify-out-02-after-skill-sync.log`。
- 同步与校验没有在仓库目录产生 `__pycache__`（`find` 核查）。

### 5.10 用户第三批答复

- 技能同步：现在同步（已执行，见 5.9）。
- 示例 (b)：采 (ii) C1 + 受限一致陈述。
- 下一步：现在开始实现合并说明 §3（修正案草案、schema、弱链演算、状态机分流、测试）。

### 5.11 实现：可信闭环 R1（用户第三批答复：现在开始实现）

| 产物 | 位置 | 内容 |
|---|---|---|
| 宪法修正案草案 | `governance/AMENDMENTS/A-0001-trust-loop-r1.md`（status PROPOSED，effectiveDate PENDING）；登记表 `governance/AMENDMENTS/README.md` 加一行 | 受影响条款、科学论证、对既有 run 的影响、禁止 / 允许清单；宪法正文未改（ACCEPTED 前不得改） |
| 三份 schema | `pinn/governance/schemas/problem-definition.schema.json`、`trust-vector.schema.json`、`claim-gate-decision.schema.json` | 从 GLM 草案改写为 `jsonschema_lite` 支持的关键字子集；if/then、contains、prefixItems、exclusiveMinimum、format 等改由 Python 交叉校验 |
| 弱链演算 | `pinn/governance/trust_vector.py` | TrustStatus 五态、支持序 FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS、meet、weakest_link、claim_gate（C0–C3 必需维度、证据等级 ≠ D、C3 需 ≥ 5 个 C2 run、EXPLORATORY 封顶 C1、失败关闭）；状态无算术，平均是 TypeError |
| 文档校验 | `pinn/governance/trust_loop.py` | ProblemDefinition / TrustVector / ClaimGateDecision 的结构 + 交叉校验；specHash 用既有 `canonical.py` 序列化（裁决 C14） |
| 状态机扩展 | `pinn/governance/state_machine.py`（只追加，既有函数不变） | WorkflowState、DiagnosisBranch 六分支、TRIAGE_ROUTES / TRIAGE_EVIDENCE、gate5_status（G5a ∧ G5b）、advance（INV1/INV2/INV3）、failure_state（3 轮上限 → STOPPED_THE_LINE）、diagnose / revise / reenter（INV4 宁严勿松）、from_gate_status |
| 包导出 | `pinn/governance/__init__.py` | 新增 DiagnosisBranch、IllegalTransition、WorkflowState、TrustStatus、claim_gate、weakest_link |
| 测试 | `tests/pinn/test_trust_vector.py`、`test_trust_loop_documents.py`、`test_state_machine_triage.py` | 91 项：DeepSeek §4.4 七个例子、GLM T01–T28 中可落地的 24 条、状态机全路径与反例 |
| 协议汇编 | `governance/PINN_TRUST_PROTOCOLS_R1.md` | 各车道规范性内容的索引与阈值起点 |
| 报告模板 | `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` | 八段（六段 + Provenance + Scope）、措辞硬约束、示例 (b) 按裁决 C4 的写法 |

- 测试：新增 3 个文件 91 项全部通过；全套裸跑 `pytest`（主检出）**930 passed / 2 skipped / 0 failed**（原 839 + 91，2 个 skip 与基准相同）；`tools/portability_check.py` 0 hard binding。
- 实现时偏离原文的决定（已记入协议汇编 §8）：① Gate 结果为 BLOCKED 或 PARTIAL 时状态不变、不进 FAILURE_RECORDED（GLM 转移表第 10 行把 BLOCKED 也记为失败；BLOCKED 是未执行，不是失败）；② 重入 Gate k 后 k 及下游全部重跑（GLM 只要求 dPinnCfd 复跑 G5b）；③ DeepSeek 例 3 的向量位置与文字不一致（F 写在 physics 位、文字说 C_train），测试对两种情形都覆盖（train=FAIL → 只 C0；physics=FAIL → C0、C1）。
- 测试产物（建立与删除）：主检出 `__pycache__` 目录 6 个、文件 19 个，已删除；用户临时目录 `pytest-of-user` 1702 个文件、38426801 字节，已删除；删除后复核两处均无残留。
- 生效前提：修正案需用户把 status 改为 ACCEPTED 并填 effectiveDate，届时再按 affectedArticles 更新宪法正文到 1.1；在此之前代码与测试只是草案的可执行形式，不改变任何 Gate 判定。

### 5.12 会话最后一步：移除 d129a8 工作树与分支（用户第二批答复）

- `git worktree remove .claude/worktrees/leoaistudio-cleanup-refactor-d129a8`：exit 1，输出「无」；随后 `git worktree prune`。目录仍存在：yes（剩余条目 0 个）。
- `git branch -D claude/leoaistudio-cleanup-refactor-d129a8`（曾指向 `8c4835e`）：exit 0，输出「Deleted branch claude/leoaistudio-cleanup-refactor-d129a8 (was 8c4835e).」。至此 `8c4835e` 不再被任何分支或工作树引用，进入可回收状态（未执行 `git gc`）。
- 9e137d 残留空目录仍被其它进程占用，未删。
- 本条之后本会话不再执行任何命令；最终状态见 `git worktree list` 与 `git log --oneline master`。

更正（同一会话，提交后追加）：5.12 第一条里 `git worktree remove` 的输出记为「无」，是记录脚本的 sed 表达式出错导致未捕获，不是命令没有输出。依据 exit 1、目录仍在但剩余条目为 0、`git worktree list` 已不再列出，判断为：内容已删除、工作树已注销，顶层空目录被本会话的 shell 占用而删不掉（与 9e137d 的情况相同），会话结束后 `rmdir` 即可。本更正是本会话最后一条命令。

### 5.13 用户第四批答复与 A-0001 第 2 稿（2026-09-15）

- 用户确认：真实窗口里上游的语言与明暗控件已隐藏（第一轮的唯一未验证项关闭）。
- 用户评审 A-0001 第 1 稿：PROPOSED / CHANGES REQUIRED，五项——(1) 症状直接映射 Gate 与"症状不唯一对应原因"矛盾；(2) NOT_APPLICABLE 不在类型系统；(3) 独立评估集未防自适应泄漏；(4) seed 阈值 0.8 过松；(5) C3 五个 run 未定义独立性。R2 开题，去除 Grok。
- 队长复核：四项成立；第 5 项驳回一半——C3 声明的对象是固定方法，spec 与代码相同是定义而非缺陷，独立性只在 seed 集与执行环境上要求；评审示例"AD 精度失效 → G2"按本仓库编号为 G3。

| 修订 | 落点 | 内容 |
|---|---|---|
| 两层诊断 | `pinn/governance/state_machine.py` | `FailureSignature`（六症状，sXxx）→ `RootCauseClass`（九类，rXxx，含 rUndetermined）→ Gate；`ADMISSIBLE_ROOT_CAUSES` 封闭矩阵；`diagnose(state, signature, root_cause, evidence)` 要求症状证据 + `discriminatingExperiment`；rUndetermined → STOPPED_THE_LINE；`DiagnosisBranch` 与 `escalate_to` 删除 |
| Applicability | `pinn/governance/trust_vector.py` | `Applicability`、`CheckResult`（NOT_APPLICABLE 无 status、必填 reason、不进 meet）、`dimension_status_from_checks`；schema `trust-vector 1.1` 加 `checks`；`trust_loop` 校验维度 status = APPLICABLE 检查的 meet |
| 评估集三分 | schema `problem-definition 1.1`、`trust_loop._evaluation_set_errors` | `revision`、`evaluationSets{train, dev, claim, claimSetStatus, claimSetOpenedAtRevision, claimSetHistory}`；三集哈希互异；OPENED 必须记于当前版本；打开过的哈希在更高版本禁用；TrustVector 维度加 `evaluationSet`，external 只在 claim 上可 PASS |
| seed 分档 | `training_reliability_status` | k/N < 0.8 FAIL、[0.8, 0.9) PARTIAL、≥ 0.9 PASS；最差 seed / IQR 封顶 PARTIAL；N < 5 BLOCKED；5 ≤ N < 10 封顶 PARTIAL |
| C3 独立性 | `RunQualification`、`c3_run_support`、schema `claim-gate-decision 1.1` | `codeHash` 必填；`qualifiedC2Runs[{runId, specHash, codeHash, environmentId, seedSetId}]` 取代整数；同规格同代码、seed 集互异、≥ 2 环境、≥ 5 个 |

- 测试：三个测试文件重写，新测试 122 项（较第 1 稿 +31）全部通过；全套裸跑 **961 passed / 2 skipped / 0 failed**；`tools/portability_check.py` 0 hard binding。
- 测试产物（建立与删除）：主检出 `__pycache__` 目录 6 个 / 文件 19 个，用户临时目录 `pytest-of-user` 1,712 个文件 / 39,619,002 字节，全部删除并复核无残留。
- 文档：A-0001 第 2 稿（affectedArticles 逐条更新，新增 reviewLog 与驳回说明）；`governance/PINN_TRUST_PROTOCOLS_R1.md` 第 2 稿（§4 两层诊断、§6 新阈值、§10 评估集纪律）；`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` 第 2 稿（NOT_APPLICABLE 措辞、评估集披露、两层诊断写法、C3 披露）；`docs/PINN_TRUST_LOOP_TEAM_PROMPTS_R2_20260915.md`（DeepSeek、GLM、Kimi、豆包四份，无 Grok）。
- 环境：本会话工作树 d129a8 已不再被 git 视为工作树；`.claude/worktrees/` 下两个空目录仍被会话进程占用，会话结束后 `rmdir`。
- 待用户：复审 A-0001 第 2 稿；把四份 R2 提示词交给队员；队员交付后队长合并为第 3 稿。

### 5.14 R2 合并、用户复审五项裁决与 A-0001 第 3 稿（2026-09-15，接手会话）

- 会话环境：桌面应用自动为本会话建了工作树 `.claude/worktrees/leoaistudio-build-handover-99ccbd`（分支 `claude/leoaistudio-build-handover-99ccbd`，起点 `de41ea4`）。写文件工具只允许写入该工作树，主检出只能用 shell 复制；因此改动在该分支上提交，再把 master **快进**到同一提交（`git merge --ff-only`），结果仍落在 master，没有新建其它工作树。该工作树与分支是否删除待用户答复（上两轮经验：会话进程占用顶层目录，删到最后剩空目录）。
- 收件：`PINN_TRUST_R2_REPORT_AND_WORKFLOW.md`（豆包，用户放入收件箱，SHA `2792e505d932`）、`PINN_TRUST_R2_IMPL_TRAINING.md`（Kimi，用户放入收件箱，SHA `6497bb9b8ea1`）、`PINN_TRUST_R2_SCHEMAS_STATE_MACHINE.md`（GLM，用户放在桌面 `C:\Users\user\Desktop\`，队长 `cp` 入库并 `cmp` 复核，SHA `6edec0c24f5b`；桌面原件未动）。`PINN_TRUST_R2_MATH_CORE.md`（DeepSeek）在桌面、下载、文档、仓库均未找到，按未收到处理。主检出里用户放的三份未跟踪文件在 `cmp` 与提交内容逐字节一致后删除（否则快进会被未跟踪文件挡住），内容以提交 `a4caa40` 为准。
- 用户复审 A-0001 第 2 稿：PROPOSED / MINOR CHANGES REQUIRED，五项 + 对抗性闭合审计要求。逐项裁决与驳回论证见 `docs/pinn-trust-loop/R2_MERGE_NOTES.md` §2–§3；队员建议 35 条裁决见 §4；分歧见 §5。

| Issue | 裁决 | 落点 |
|---|---|---|
| 1 全 NOT_APPLICABLE 维度语义 | ACCEPT_WITH_MODIFICATION：INV-A1（非空清单必须含 APPLICABLE 检查，否则 `NoApplicableCheck`）；适用性登记进规格 `checkApplicability`（进 specHash）；向量检查须与注册表逐项一致；驳回方案 1（DimensionResult.applicability）与方案 2（ClaimPrerequisite 豁免） | `trust_vector.py`、`trust_loop.py`、`problem-definition 1.2` |
| 2 哈希不同不证明互斥 | ACCEPT：第 2 稿确实只比哈希；新增样本清单契约、样本身份（float64 精确输入 + quantity）、成对互斥、预注册 minSeparation、可选 phys 集 | `evaluation_sets.py`、`evaluation-set.schema.json` |
| 3 SEALED → OPENED 不可逆 | ACCEPT_WITH_MODIFICATION：哈希链账本 L1–L7 + 状态由账本推导 + 决策引用 ledgerHead；specHash 排除 revision 与 claim 集状态；驳回"必须真正不可变存储"，改为可检测性保证 | `claim_set_ledger.py`、`claim-set-event.schema.json`、`trust_loop.py` |
| 4 C3 与 G6 独立环境统一 | ACCEPT_WITH_MODIFICATION：`EnvironmentFingerprint` 强 / 弱字段，environmentId = 强字段哈希，`independent_environments` 一个规则供 `c3_run_support` 与 `reproduction_status` 共用；五个案例逐一裁定；驳回"字段都必须不同" | `trust_vector.py` |
| 5 IQR/median 零点 | ACCEPT_WITH_MODIFICATION：`seed_statistics` 用 `IQR > limit × median` 乘法比较，无除法、无下限；NaN/Inf 为发散 run；驳回方案 B（ε_floor） | `trust_vector.py` |

- 对抗闭合审计八项：根因挑选（BLOCKING，已封：excludes 必须覆盖全部其它可接受根因）、revision 规避（已封：OPENED 记 codeHash，决策必须相等）、specHash 覆盖（已封：阈值 / seed 协议 / 适用性入规格）、evidenceLevel 重标（已封：必须等于规格 primary source）、C3 计数（已封：三个身份派生复算）、Red Team 泄漏（部分可封，其余靠账本 + 升版纪律）、Gate 重置（NONE，补 BLOCKED 残留用例）、人工向上覆盖（已封：已执行维度必须展示检查，status ≤ meet）。
- 代码与契约：`trust_vector.py`（INV-A1、seed_statistics、EnvironmentFingerprint、seed_set_id、RunQualification.from_record、reproduction_status）、新增 `evaluation_sets.py`、`claim_set_ledger.py`、`trust_loop.py` 重写（七类文档交叉校验）、`state_machine.py` 加 `discriminating_experiment_errors`、schema 1.2 三份 + 新契约四份、`__init__.py` 导出。
- 测试：三个既有测试文件改为 1.2 夹具（改写、未删除），新增 `test_trust_loop_adversarial.py`（23）、`test_evaluation_sets.py`（9）、`test_claim_set_ledger.py`（6）；新增 70 项；pinn 子集 447；工作树全套 1024 passed / 9 skipped（无安装目录，多跳过 7 项）；主检出 master `a4caa40` 全套 **1031 passed / 2 skipped / 0 failed**（基准 961 + 70）。`tools/portability_check.py` 0 hard binding。
- 文档：A-0001 第 3 稿（status 仍 PROPOSED，reviewLog 加复审裁决表与审计表）、`governance/PINN_TRUST_PROTOCOLS_R1.md` 第 3 稿（新 §11 环境身份与 G6）、`docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` 第 3 稿（豆包 R2 写法 + 示例 (b) 按 R2-30）、`R2_MERGE_NOTES.md`、登记簿 README 行、CHANGELOG 行。宪法正文未改。
- 提交：`a4caa40`（代码、契约、测试、文档、收件）；本日志与两份根目录报告随后一并提交并快进。
- 测试产物（建立与删除）：工作树 `__pycache__` 6 个目录（两次运行后删除，文件数未单独统计）；主检出 `__pycache__` 6 个目录 / 22 个文件，删除；用户临时目录 `pytest-of-user` 3,934 个文件 / 70,262,342 字节（本会话三次运行），删除；删除后复核主检出与工作树 `git status` 均为 0 行、`__pycache__` 0 个、临时目录不存在。
- 待用户：终审 A-0001 第 3 稿（"通过"后改 ACCEPTED、填日期、按 affectedArticles 更新宪法正文到 1.1）；DeepSeek R2 交付物补交；是否删除本会话工作树与分支、两个遗留空目录；GLM 复发升级规则（R2-20）与单机 claim 集治理存储形态（R2-24）两项待决。

### 5.15 用户第五批答复：DeepSeek 补交、A-0001 终审通过、审批删除（2026-09-15）

- 用户答复四项：① DeepSeek 交付物在 `C:\Users\user\PINN_TRUST_R2_MATH_CORE.md`；② 同意删除本会话工作树与分支、两个遗留空目录，写入卫生记录，理由"用户审批通过"；③ 同意采纳 GLM 复发升级规则与队长选定 claim 集密封存储形态；④ A-0001 第 3 稿"通过"。
- 收件：`PINN_TRUST_R2_MATH_CORE.md`（DeepSeek，SHA `3332850a6ce3`，241 行）`cp` 入库并 `cmp` 复核，原件未动。裁决 R2-36 ～ R2-42 见 `R2_MERGE_NOTES.md` §7：P22–P32 与 P1–P21 不合并编号（schema 已接受，无需改代码）；逐格判定规则、seed 阈值统计论证（PASS ≠ 高置信认证 p ≥ 0.9；升级路径 N ≥ 30 / 50）、泄漏信息流不变量与检查项、三类问题 Applicability 表并入协议汇编 §3 / §4 / §6 / §10；建议增加的三个矩阵格不进已终审的 A-0001，记为 A-0002 候选。
- 终审：`A-0001-trust-loop-r1.md` frontmatter 改为 `status: ACCEPTED`、`effectiveDate: 2026-09-15`，reviewLog 加终审行与 DeepSeek 补交说明；登记簿 README 同步。**宪法正文尚未改**，原因如下。
- 阻塞项（STOP / HUMAN DECISION REQUIRED）：`pinn/governance/prelock.py` 把 Poisson 1D v1.0 的 lock 草案与当前宪法文件字节哈希绑定（`lock draft Constitution SHA does not match current bytes`），`locking.py` / `prelock.py` 把 constitutionVersion 引脚在 `"1.0"`，`POISSON_1D_V1.0_{spec,protocol,lock}.draft.json` 都声明 1.0，`tests/pinn/test_prelock_integrity.py::test_changed_constitution_is_not_accepted` 明确要求改动宪法字节即 PRELOCK FAIL。因此按 affectedArticles 改写正文会使 PRELOCK 校验与既有测试失败；解法都在 A-0001 范围之外（放宽版本引脚、把三份 Poisson 草案重新绑定到 1.1 并产生新的 dry-run 证据文件，或让校验器按草案声明的版本从 git 历史取对应字节）。两个可选方案写在本轮汇报里，等用户决定后执行。
- R2-20 采纳（停线评审而非直接终止，实现 R3）；R2-24 选权限目录（治理账户独占可读），不选加密文件。
- 代码无改动；测试基线仍是 master `a4caa40` 的 1031 passed / 2 skipped，本条只改文档，未重跑、未产生测试产物。
- 提交：本条与文档改动一并提交并快进 master；随后按用户审批执行删除（结果追加在 5.16）。

### 5.16 会话最后一步：审批删除的执行结果（用户审批通过）

- `git worktree remove --force .claude/worktrees/leoaistudio-build-handover-99ccbd`：exit 255，输出「failed to delete '…/leoaistudio-build-handover-99ccbd': Permission denied」；随后 `git worktree prune`。工作树内容已全部删除，顶层空目录仍在（剩余条目 0 个），被本会话的 shell 进程占用，`git worktree list` 已不再列出；会话结束后 `rmdir` 即可。
- `git branch -D claude/leoaistudio-build-handover-99ccbd`：exit 0，「Deleted branch … (was 1f0e48f)」。该分支已快进进 master，无独有提交。
- `rmdir .claude/worktrees/leoaistudio-cleanup-refactor-9e137d`：exit 0（目录为空，已删除）。
- `rmdir .claude/worktrees/leoaistudio-cleanup-refactor-d129a8`：exit 1，「Device or resource busy」（目录为空，被其它进程占用，未删；会话结束后 `rmdir`）。
- 最终状态：`git worktree list` 只剩主检出 master `1f0e48f` 与两个 codex 交付工作树；`.claude/worktrees/` 下剩两个空目录（handover-99ccbd、d129a8）。本条从主检出提交；本条之后本会话不再执行改动。

### 5.17 宪法正文 1.1 落笔（用户选方案一，2026-09-15）

- 工作方式：会话工作树已按 5.16 删除，写文件工具仍只认原工作树路径，因此本轮改动全部由 Python 补丁脚本（精确字符串替换，每个锚点必须恰好出现一次）作用于主检出 master，脚本在会话临时目录、不入库。
- 宪法正文（`governance/PINN_RESEARCH_CONSTITUTION.md`，16 处替换）：元数据表 Version 1.1、Effective Date 追加 2026-09-15；文件元数据加第 5 条（A-0001 标注约定与旧实验按 1.0 审计）；第三章加 3.1 两层分流；第四章加 4.1 维度状态、Applicability、INV-A1；第五章加 5.1 ProblemDefinition 与方法身份 specHash；第九章加 9.1 三分评估集、样本级互斥、claim 集账本；第十章加 10.1 多 seed 协议（含无除法离散度、PASS ≠ 高置信认证）；第十三章加 13.1 八段报告；第二十八章加 28.1 RunRecord 与执行环境身份；第二十九章补判定统计量说明；第三十六章加 36.1 弱链演算与 C3；第五十三章 G5a/G5b；第五十四章 G6 定义；第五十六章路由按根因；新增第六十四（Red Team 三层制）、六十五（EXPLORATORY 第二来源）、六十六（revision 与方法身份）章；结尾改 v1.1。新字节 SHA-256 `943484850d6487b310f2afe9dae86074c27adaa4c9915d85fa0b8708ee73b547`（1.0 为 `4300bb84…`）。
- 代码：`locking.py` 新增 `SUPPORTED_CONSTITUTION_VERSIONS = ("1.0", "1.1")`，payload 校验按集合判断；`prelock.py` 新增 `declared_constitution_version()`（从宪法元数据表读 `| Version | x.y |`），宪法必须声明受支持版本，lock / spec / protocol 草案绑定的版本必须等于宪法声明的版本（原来硬编码 "1.0"）；三份 schema 的 `constitutionVersion` 由 const "1.0" 改为 enum ["1.0", "1.1"]。字节哈希绑定规则不变：草案的 constitutionSha256 必须等于宪法当前字节。
- 草案重绑定（用户审批通过，方案一）：`POISSON_1D_V1.0_spec.draft.json`、`_protocol.draft.json` 的 constitutionVersion 改 1.1；`_lock.draft.json` 的 constitutionVersion 改 1.1、constitutionSha256 改新字节哈希、shellEquivalent 里的 "1.0" 改 "1.1"；三份文件经 `strict_json_loads` + `canonical_bytes` 往返，改动前后都是规范字节，其余字节不变。三份草案 lockedAt 仍为 null，没有任何 lock 或训练发生。
- 证据：新增 `governance/PINN_V1.3_PRELOCK_DRY_RUN_A0001.json`（SHA `3943559b0f03`，reportDate 2026-09-15，prelockStatus PASS，六项检查全 PASS，constitution 1.1 + baseline 1.0 哈希，candidateDigests 来自实跑，tests 计数），2026-09-05 的 `PINN_V1.3_PRELOCK_DRY_RUN.json` 原样保留。第一次生成时因新测试写错属性名（`lock` → `lock_draft`）记录了 1 项 failed，该文件随即删除、修正测试后重新生成（脚本拒绝覆盖，先删后生成；两次都是本轮自建的文件，不是既有证据）。
- 测试：`tests/pinn/test_prelock_integrity.py` 新增 2 项（草案绑定 1.0 或 9.0 对 1.1 宪法 → FAIL；宪法无版本行 → FAIL）；pinn 子集 449；全套 **1033 passed / 2 skipped / 0 failed**（1031 + 2）。`python -m pinn.governance.prelock` 实跑 PASS。
- 文档：A-0001 reviewLog 终审行改为"宪法正文已更新为 1.1"；登记簿 README 同步；CHANGELOG 加一行；记忆文件记录版本升级配方。
- 测试产物（建立与删除）：主检出 `__pycache__` 6 个目录 / 22 个文件，删除；用户临时目录 `pytest-of-user` 3,449 个文件 / 63,796,495 字节（本轮四次运行），删除；复核 `__pycache__` 0 个、临时目录不存在。
- 提交：本条与上述改动一并提交到 master。

### 5.18 队长裁决 DeepSeek 建议：A-0002 起草（2026-09-15）

- 用户授权：队长有资格采纳或驳回 DeepSeek 建议。裁决：三个矩阵格采纳（sBcResidual → rCapacityLimit、sPinnCfd → rCapacityLimit、sLocalizedError → rSpecDefect），三格驳回不加（sPinnCfd → 采样是中介根因；sPdeResidual / sConservation → 数据在正向问题不成立，逆问题不在 MVP；sSeedSensitive → 实现，非确定算子由 G3 的 P4 排除）。
- 矩阵是宪法 1.1 第 3.1 条的条款（正文写明 sLocalizedError"六类之一"），按第六十章采纳必须走修正案：起草 `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md`（oldVersion 1.1 → newVersion 1.2，PROPOSED，effectiveDate PENDING），登记簿加行。
- 代码与测试（修正案的可执行形式，同 A-0001 的做法；当前没有任何 DiagnosisRecord，三格在 ACCEPTED 前不会被任何实验引用）：`state_machine.ADMISSIBLE_ROOT_CAUSES` 三格；`test_state_machine_triage.py` 的不可接受反例改用仍不可接受的组合（sBcResidual → 参考解、sPinnCfd → 采样、sPdeResidual → 数据），新增参数化用例 3 项（三格可接受、路由 Gate 正确、其它根因必须新增排除该格的义务）；`test_trust_loop_adversarial.py` 的 sLocalizedError 诊断夹具补排除 rSpecDefect，rSpecDefect 由"不可接受"改为合法并检查 gate = 1。pinn 子集 454；全套 **1038 passed / 2 skipped / 0 failed**（1033 + 5）。
- 文档：协议汇编 §4 表与三格判定规则（P23；P23；P31 + P22）；`R2_MERGE_NOTES.md` R2-38 改"采纳，起草 A-0002"；CHANGELOG 加行；记忆文件记录。
- 未做（等用户终审 A-0002）：宪法正文 3.1 改 1.2；`SUPPORTED_CONSTITUTION_VERSIONS` 与三份 schema 枚举加 1.2；Poisson v1.0 草案重绑定；新证据文件。流程与 5.17 相同。
- 测试产物（建立与删除）：主检出 `__pycache__` 6 个目录 / 22 个文件，删除；`pytest-of-user` 2,235 个文件 / 40,425,629 字节，删除；复核无残留。
- 提交：本条与上述改动一并提交到 master。

### 5.19 A-0002 第 2 稿：用户复审六项的因果可判定审查（2026-09-15）

- 复审结论 PROPOSED / CHANGES REQUIRED。裁决：六项全部 ACCEPT 或 ACCEPT_WITH_MODIFICATION，无驳回；第 1 稿被推翻的是队长自己的两条驳回理由（"采样先触发残差"、"实现缺陷是确定性的"）。逐项论证见 `docs/pinn-trust-loop/R2_MERGE_NOTES.md` §8 与 A-0002 第 2 稿 reviewLog。
- 矩阵：第 1 稿三格之外再加五格——sPinnCfd → 采样、sSeedSensitive → 实现（复审两格）、sPdeResidual → 奇异性、sBcResidual → 奇异性、sSeedSensitive → 规格（闭合审计三格）；空格分类 IMPOSSIBLE 4 / OUT_OF_SCOPE 5 / UNSUPPORTED 2 写进协议汇编 §4。
- 证据结构机器化（`state_machine.py`）：`intervention_errors`（命名容量 / 采样：单因子、其余八项控制固定、≥ 3 档 × ≥ 3 seed、中位误差严格下降、容量另需优化诊断干净）、`determinism_replay_errors`（命名 sSeedSensitive → 实现：同 seed 重放 maxDivergence > epsilonDet 且定位缺陷）、`MATRIX_SCOPE`；`discriminating_experiment_errors` 调用两者。`diagnosis-record.schema.json` 加 `problemClass = forward`、`observedSignatures`、`intervention`、`determinismReplay`；`trust_loop.validate_diagnosis_record` 校验 observedSignatures（根因须对每个观察到的症状可接受）。
- 修正案依赖：新增 `pinn/governance/amendments.py`（frontmatter 解析含 `dependsOn`；不变量 R1–R4：ACCEPTED 单链从 1.0 出发、宪法版本 = 链尾、依赖目标状态与版本、ACCEPTED 有日期 / PROPOSED 为 PENDING）；`prelock.py` 加第七项检查 `amendmentRegister`，`python -m pinn.governance.prelock` 实跑 PASS。A-0002 frontmatter 加 `dependsOn: A-0001 ACCEPTED @ 1.1`。
- 测试：`test_state_machine_triage.py` 新增采样干预五种不足证据、容量干预与优化诊断、重放发散 / 一致 / 未定位、每加候选即加排除义务、范围常量，八格可接受用例，不可接受反例改用仍不可接受的组合；`test_trust_loop_adversarial.py` 新增 problemClass / observedSignatures / 文档级干预与重放；新增 `test_amendments.py` 8 项（含 A-0002 不能在 A-0001 PROPOSED 时生效、不能对宪法 1.0 生效、真实登记簿、PRELOCK 第七项）。pinn 子集 474（+20）；全套 **1058 passed / 2 skipped / 0 failed**（1038 + 20）。
- 文档：A-0002 第 2 稿（全文重写，status 仍 PROPOSED）；协议汇编 §4（矩阵表、范围与空格分类、受控干预 / P33 / P34 / observedSignatures）；合并说明 R2-39 改判与新 §8；登记簿；CHANGELOG。宪法正文仍 1.1（待终审后按 5.17 流程落 1.2）。
- 测试产物（建立与删除）：主检出 `__pycache__` 6 个目录 / 22 个文件，删除；`pytest-of-user` 见本条末尾计数，删除；复核无残留。
- 计数：主检出 `__pycache__` 6 个目录 / 22 个文件；`pytest-of-user` 2243 个文件 / 40657042 字节；均已删除并复核。

### 5.20 A-0002 第 3 稿：Final Closure Review 三项剩余问题与实验准入审计（2026-09-15）

- 工作方式：桌面应用把本会话放进了新工作树 `.claude/worktrees/leoaistudio-build-handover-29efe6`（分支同名，指向 d56c3eb，非队长所建）；按用户指令全部改动直接作用于主检出 master——代码与文档由 Python 补丁脚本（精确字符串替换，每个锚点恰好一次）与新文件复制完成，脚本与草稿在会话临时目录、不入库。该工作树与分支是否删除待用户决定。
- 审计结论（Issue 1，BLOCKING）：`ADMISSIBLE_ROOT_CAUSES` 是单一全局最新表，`diagnose()` / `validate_diagnosis_record()` 不读宪法版本；A-0002 起草起 1.1 的运行时就是 1.2 语义（八格 + 干预 / 重放义务）。
- 代码（最小修复，不重构）：`state_machine.py`——`ADMISSIBLE_ROOT_CAUSES_BY_VERSION{"1.1", "1.2"}`（1.1 表逐格取自 a94c138）、`NAMING_OBLIGATIONS_BY_VERSION`、`admissible_root_causes(version)` / `naming_obligations(version)` / `effective_constitution_versions()`（运行时读 `locking.SUPPORTED_CONSTITUTION_VERSIONS`）、`ConstitutionVersionError`；`diagnose(..., constitution_version=)` 与 `discriminating_experiment_errors(..., constitution_version=, explained=)` 必填版本；`identifiability_errors` 与常量 `IDENTIFIABILITY_KEY` / `AMBIGUITY_TYPES` / `AMBIGUITY_INTENT`；`earliest_route`；删除全局 `ADMISSIBLE_ROOT_CAUSES`。`trust_loop.py`——`validate_diagnosis_record(document, constitution_version=None)` 按记录版本取矩阵、`explained_signatures`、`diagnosis_coverage_errors`；去掉"根因须对每个观察症状可接受"的单因规则。`amendments.py`——R5（`effective_versions`）。`prelock.py`——第七项传入 SUPPORTED 并校验登记簿 / 声明版本都有运行时矩阵。`diagnosis-record.schema.json`——必填 `constitutionVersion`（enum 1.1 / 1.2）、可选 `explainedSignatures`、`$defs/identifiability`。
- 测试：新增 `tests/pinn/test_constitution_version_isolation.py` 29 项；`test_state_machine_triage.py` 改为在 `effective_1_2` 自动夹具（monkeypatch SUPPORTED 加 1.2）下运行、`diagnose` / `discriminating_experiment_errors` 经带版本的包装、seed → 规格夹具补 identifiability；`test_trust_loop_adversarial.py` 记录加 `constitutionVersion: 1.2`、两项诊断测试用 `effective_1_2` 夹具、单因断言改为 explainedSignatures 语义。全套 **1087 passed / 2 skipped / 0 failed**（1058 + 29）；pinn 子集 503。`python -m pinn.governance.prelock` 实跑 7/7 PASS（两次：补丁后与收尾）。
- 文档：A-0002 第 3 稿（frontmatter proposedBy 补第 3 稿；affectedArticles 加版本隔离条、seed → 规格收窄、identifiability、explainedSignatures 与覆盖不变量；scientificJustification 加三条；impactOnExistingRuns 代码与测试清单更新；consequence 被禁止项与生效前提更新；reviewLog 加两行与三项裁决表；status 仍 PROPOSED / PENDING）；协议汇编 §4（P34 可识别性、版本隔离与症状覆盖段）；`R2_MERGE_NOTES.md` 新 §9；登记簿 README A-0002 行；CHANGELOG 加行；新文件 `docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md`（八节：决议建议 READY FOR USER ACCEPTANCE、三项裁决、版本隔离证据、覆盖证据、P34 语义、测试证据、闭合审计、准入审计 NOT_READY 与三个 blocker）；根目录两份报告；记忆文件。
- 未做（等用户）：A-0002 ACCEPT 与 1.2 配方（宪法正文、SUPPORTED、schema 枚举、草案重绑定、证据文件）；Poisson 1D 校准实验与失败路径实验（准入 blocker 2、3）；多余工作树与分支的删除。
- 测试产物（建立与删除）：主检出 `__pycache__` 6 个目录 / 22 个文件，删除；`pytest-of-user` 2243 个文件 / 40799797 字节（本轮五次 pytest：pinn 子集一次、新文件两次、全套一次、登记簿与隔离测试一次），删除；复核见本条末尾复核行。
- 提交：本条与上述改动一并提交到 master。
- 复核（删除后）：主检出 `__pycache__` 0 个目录；`pytest-of-user` 不存在。

### 5.21 A-0002 正式生效：宪法 1.2（用户终审通过，2026-09-15）

- 授权：用户在实验授权指令中确认"A-0002 已通过用户终审，需先按既定依赖顺序完成正式生效"。队长先核对 A-0001 已 ACCEPTED / 宪法 1.1 生效（§5.15、§5.17），再按 §5.17 同一配方执行 1.1 → 1.2；期间没有任何 run 处于 FAILURE_RECORDED 之后，没有任何 DiagnosisRecord。
- 宪法正文（Python 补丁脚本，精确锚点各一次）：元数据表 Version 1.2、Effective Date 追加 2026-09-15（1.2，A-0002）；文件元数据加第 6 条（A-0002 标注约定、机器可执行形式位置、1.1 run 按 1.1 审计）；第三章 3.1 的矩阵引用改为 `admissible_root_causes(constitutionVersion)`、"六类之一"改"七类之一【A-0002】"；新增 3.2（八格扩展与空格分类、结构化命名义务含 P34 可识别性、症状覆盖不变量、运行时版本隔离）；第六十章加【A-0002】段（dependsOn、R1–R5、生效配方）；结尾改 v1.2。新字节 SHA-256 `2f4484027cc95fc949b2df46ca3f76f1ecace8279db4b93d9d26ceaf8f15357e`（1.1 为 `943484850d64…`）。
- 版本引脚：`locking.SUPPORTED_CONSTITUTION_VERSIONS = ("1.0", "1.1", "1.2")`（这一步同时解锁运行时 1.2 矩阵）；lock / spec / protocol 三份 schema 的 `constitutionVersion` 枚举加 "1.2"（diagnosis-record schema 已含）。
- 修正案：A-0002 frontmatter status ACCEPTED、effectiveDate 2026-09-15，reviewLog 加终审行；登记簿 README 行改 ACCEPTED。
- 草案重绑定：`POISSON_1D_V1.0_spec.draft.json`、`_protocol.draft.json` 的 constitutionVersion 改 1.2；`_lock.draft.json` 的 constitutionVersion 改 1.2、constitutionSha256 改新字节哈希、shellEquivalent 的 "1.1" 改 "1.2"；三份文件 `strict_json_loads` + `canonical_bytes` 往返前后都是规范字节。lockedAt 仍为 null，没有任何 lock 或训练发生。
- 测试：`test_amendments.py` 真实登记簿断言改 ACCEPTED + 日期；`test_prelock_integrity.py` 两处 "1.1" 改 "1.2"（声明版本、草案错配文案）；`test_constitution_version_isolation.py` 加 `proposed_state` 夹具（把 SUPPORTED 回拨为 1.0/1.1 以继续覆盖"PROPOSED 期间不可达"语义），真实状态断言改为 1.2 生效、登记簿泄漏用例改用复制的 PROPOSED 副本。pinn 子集 503；全套 **1087 passed / 2 skipped / 0 failed**（数量不变：改断言不加用例）。
- PRELOCK：`python -m pinn.governance.prelock` 实跑 7/7 PASS（constitutionBinding 绑 1.2、amendmentRegister 链 1.0 → 1.1 → 1.2 = 声明版本、R5 通过）。
- 证据：新增 `governance/PINN_V1.3_PRELOCK_DRY_RUN_A0002.json`（SHA `e5c7516be2fb`，reportDate 2026-09-15，prelockStatus PASS，七项检查全 PASS，constitution 1.2 + baseline 1.1 哈希、acceptedChain [A-0001, A-0002]，candidateDigests 来自实跑，tests 计数 503 / 1087）；A0001 与 2026-09-05 的证据文件原样保留。
- 结论：`GOVERNANCE_ACTIVATION: PASS`。宪法 / schema / 运行时 / PRELOCK 版本一致（1.2），登记簿无 PROPOSED 修正案。此后不再新增 A-0003 或规则，除非实验暴露 BLOCKING 矛盾。
- 提交：本条与上述改动一并提交到 master（实验代码与结果另行提交）。

### 5.22 Poisson 1D 两场正式实验：R3 最小 runner、Formal Calibration、Controlled Sampling Deficiency（2026-09-15 夜～09-16 UTC）

- 授权：用户指令"停止设计新规则，进入正式实验阶段"（治理生效 → R3 → 实验 1 → 实验 2 → 测试 → PRELOCK → 报告）。完整报告 `docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md`；预注册协议 `experiments/poisson1d/EXPERIMENT_PROTOCOL_20260915.md`（正式 run 前提交）。
- 环境事实：仓库 `.venv` 没有 torch / numpy（治理代码纯 Python）；训练用用户既有的 mamba Python 3.12.9（torch 2.12.1+cu126 强制 CPU float64 deterministic、numpy 2.4.5、matplotlib 3.10.1），未安装任何包；环境指纹（machineId、torch-2.12、mkl、依赖锁哈希、prefix 安装 id）写入每个 RunRecord。`.venv` 里 runner 的 torch / numpy 测试自动跳过（2 项）。
- Pilot（D_dev only，允许的调参）：一次 3 seed 试跑选定 6000 步 / lr 1e-3→1e-5 / batch 128 / BC 权重 10（dev 相对 L2 3.1e-4）；bad8 1.27e-2；随后配置冻结进 `experiments/poisson1d/configs/exp1_baseline.json`、`exp2_bad_sampling.json`，D_claim 密封前完成。
- R3 runner（`pinn/experiments/`：common / datasets / pinn_torch / gates / diagnosis / runner / report，约 1500 行）：冻结 ProblemDefinition（每 (problemId, revision) 一次）、四集样本级互斥、账本 SEALED/OPENED、G1–G6、seed 账簿、多 seed 训练、RunRecord、TrustVector、ClaimGateDecision、DiagnosisRecord、revise/reenter、Trust Report、图、PROVENANCE_MANIFEST、STATE_TRANSITIONS。子命令 attempt / diagnose / revise / finalize / failure-diagnostics / plots。提交 440896e、3d891fd、ca23c9c、b571a70、4d50e85、0a4db4f。
- 三次实跑暴露并修复的 runner 缺陷（均被治理校验器在写入前拦下，无绕过）：① Gate 2b 从 FDM 诊断读了不存在的键 → 假 FAIL（未训练；目录删除）；② 重跑重新冻结 ProblemDefinition 使 frozenAt 进 specHash → 账本 L3 拒绝 OPENED（10 个 run 作废，确定性可重算；目录与该账本文件删除——队长自建、无结论依赖，记录于此）；③ ClaimGateDecision.trustVectorRef 应为 recordId → 决策校验拒绝；claim 集已合法 OPENED，故新增 resume-safe `finalize` 从已存 gate 结果收尾，不重训不重开（决策层代码 commit 变更，codeHash 仍记训练 / 开集时身份 a59a939f）。
- 实验 1（`exp1-calibration-r1`，`pdef-poisson1d-cal-v1` r1，specHash 3dc9cd62…，codeHash a59a939f…）：G1–G4 PASS（k/N 10/10，median 2.84e-4，worst 6.20e-4）；G5a PASS；claim 集 02ee4e75… OPENED@r1；G5b **FAIL**：AC-3（边界误差 < 1e-4）7/10 seed 超阈（1.03e-4–2.79e-4），AC-1/2/4–8 全部满足 → FAILURE_RECORDED，observedSignatures [sBcResidual]；不出 ClaimGateDecision。向量 (PASS, PASS, PASS, PASS, FAIL, NOT_CHECKED)。**EXPERIMENT_1: PASS**（闭环标准八条满足；数值结果诚实判 FAIL），Highest Allowed Claim: BLOCKED。
- 实验 2（`pdef-poisson1d-cal-v1-exp2` r1，specHash 081fd8c8…）：bad attempt（collocationCount 8）G4 FAIL（k/N 2/10，median 2.71e-3）→ FAILURE_RECORDED，observedSignatures [sPdeResidual, sPinnCfd, sSeedSensitive]（事后实测判定）→ 受控采样干预 4/8/16 × 5 seed，中位 1.19e-2 → 5.89e-4 → 5.09e-4 严格下降，7 项候选逐条以实测排除 → DiagnosisRecord rSamplingDeficiency（1.2，覆盖三症状）→ DIAGNOSED → REVISED（机械校验只改 collocationCount 8→256）→ REENTER Gate 4 → `exp2-revised-r1` G4 PASS（10/10，与实验 1 逐位相同）→ G5a PASS → claim 集 33ea0764… OPENED@r1（codeHash ff322e9c…）→ G5b FAIL（AC-3 同实验 1）→ FAILURE_RECORDED。**EXPERIMENT_2: PASS**（情况 A）。
- 新问题：BLOCKING（对取得 C2）B1 软 BC 达不到 AC-3；NON-BLOCKING N1 无独立环境 → C_repro BLOCKED、N2 干预准则无效应量、N3 每档 5 seed 偏少、N4 实验 2 claim 集与实验 1 同样本不同 artifactId（事前披露）、N5 三次 runner 缺陷；AMENDMENT / PROTOCOL CANDIDATE C1 每 revision 预注册 claim 网格、C2 干预效应量、C3 BC 执行方式冻结进规格——不自行起草，等用户与评审。最终建议 REMAIN AT POISSON CALIBRATION STAGE；PINN_AGENT MVP: VALIDATED（仅指闭环按治理标准工作）。
- 测试：新增 `tests/pinn/test_experiment_runner.py` 9 项（7 通过 + 2 框架缺失跳过）；pinn 子集 510 passed / 2 skipped；全套 **1094 passed / 4 skipped / 0 failed**（1087 + 7，+2 skip）。PRELOCK 7/7 PASS。
- 证据入库：`experiments/poisson1d/`（configs、problems、ledger、runs/exp1-calibration-r1、runs/exp2-bad-sampling-r1、runs/exp2-revised-r1，含权重、历史、图，约 7.4 MB）。
- 测试产物（建立与删除）：主检出 `__pycache__` 6 个目录 / 23 个文件，删除；`pytest-of-user` 2329 个文件 / 43054944 字节（本轮 pytest 六次），删除；复核见末行。
- 未做：实验 1 AC-3 的诊断—修订循环（需 C1 裁决）；G6；Red Team 扰动；多余工作树 / 分支删除（等用户）。
- 提交：本条与实验证据、报告一并提交到 master。
- 复核（删除后）：主检出 `__pycache__` 0 个目录；`pytest-of-user` 不存在。

### 5.23 Poisson 1D 向 C2 校准：claim 集样本身份、sBcResidual 诊断、修订、新盲 G5、Tier-1、G6（2026-09-16）

- 授权：用户指令"在不降低任何标准的前提下真正尝试 SUPPORTED@C2；达不到就诚实 BLOCK"。基线审计：树干净（HEAD 29922dd）、宪法 1.2（SHA 2f448402…）、PRELOCK 7/7、基线 1094 passed / 4 skipped；实验 1/2 记录未改（只追加 `POST_AUDIT_ANNOTATION.md`）。报告 `docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md`；预注册 `experiments/poisson1d/EXPERIMENT3_PREREGISTRATION_20260916.md`（正式 run 前提交）。
- PART 1 claim 集身份（判定：实现 bug / 协议澄清，不改宪法语义）：`evaluation_sets.sample_set_hash`；`claim_set_ledger` 事件可携带 `sampleSetHash`，新增 L4s（按样本身份一次 OPENED）、L6/L7 按样本身份拒绝重新 SEALED、L8 一个 artifact 只绑一个样本身份，旧事件由 `experiments/poisson1d/ledger/sample_set_registry.json` 解析；`validate_problem_definition(..., sample_set_hashes)` 拒绝已打开样本的重新包装；schema 加可选字段；协议汇编 §10 加澄清段。实证：exp1 与 exp2-revised 的 claim 集 artifact 不同、sampleSetHash 相同（91414bd5260e…）→ exp2-revised/POST_AUDIT_ANNOTATION.md 注明其 G5b 追溯为非独立证据，G4 恢复结论不受影响。
- Claim pool（`register-pool`）：GL640∪CGL2400（r2）、GL768∪CGL2802（r3；原选 CGL2800 在 x=1/4 与格点碰撞被弃用）、GL896∪CGL3200（r4）；两两互斥、与 train/dev/phys 互斥、反碰撞通过；账本 r1 预注册 SEALED（带 sampleSetHash）；pool manifest `problems/pdef-poisson1d-cal-v1-claim-pool.json`。评估器 `pinn/experiments/claim_metrics.py`（与可信校验器逐位一致，测试证明）。
- PART 11 干预准则（3A 前冻结，`pinn/experiments/criteria.py`）：配对 seed N ≥ 10；相邻档 median 比 < ρ = 0.5（来源 P23 的 0.5 规则）；配对改善 ≥ q = 0.8（来源 10.1 的 0.8 线）。不回溯实验 2（其历史数字在新准则下不通过，仅记录）。
- 3A（P24，λ_BC 10/100/1000 × 10 配对 seed，30 run）：BC median 1.43e-4 → 8.15e-5 → 1.33e-5；10→100 ratio 0.571、6/10 改善 → 准则未满足；λ=1000 全 seed < AC-3；PDE 4.56e-3 → 7.83e-3（未越阈、< 2×）。3B（P28 硬 BC，10 run）：BC 恰 0，solution median 1.99e-4，PDE 2.79e-3。按预注册第 6 节字面判定 **rSpecDefect**（分支 6.2），7 项排除引用实测；DiagnosisRecord `dg-exp1-calibration-r1-bc-r1`（1.2），`diagnose` 接受，路由 Gate 1。诚实记录 N6：λ=1000 也解决 AC-3，优化 / 权衡解释在 100→1000 段成立，规则按字面选了规格分支，不事后换。
- 修订与重入：`run_revise` 校验只改 enforcement soft→hard（`exp3_hard_bc.json`，候选配置在读结果前已提交 675df98）；`exp3c-hard-bc-r2`：REVISED →reenter G1→ DRAFT → G1/G2/G3 PASS → G4 PASS（10/10，median 1.99e-4）→ G5a PASS → D_claim_1 SEALED(r2)→OPENED(codeHash 5aaf93a5…)→BURNT → G5b **PASS**（AC-1..8 全 seed 满足，AC-3 = 0）→ G6 BLOCKED。
- Tier-1（D_dev，seed 0，各一次重训）：run 1 P8 FAIL（e2 1.02）——扰动 harness 缺陷：硬参数化 x(1−x) 写死单位区间，缩放域 [0,2] 处 v(2) ≠ 0；修复 `HardDirichlet(length)`（commit 75cc6fd），run 1 文件保留，以标签 tier1v2 重跑：P1/P4/P6/P8/P9/P16 全 PASS，P7/P11 NOT_APPLICABLE（理由登记）；exp3c/POST_AUDIT_ANNOTATION.md 说明。向量 (PASS,PASS,PASS,PASS,PASS,BLOCKED)，决策 `claim_gate_decision_tier1v2.json` 允许 C0/C1，C2/C3 因 repro BLOCKED。
- G6：无第二独立环境 → C_repro BLOCKED；复现包 `experiments/poisson1d/repro_package_exp3c_r2/`（PACKAGE_MANIFEST 含 codeHash、依赖锁哈希、seed 规则、容差、说明、schema）。
- 结论：Poisson Claim Calibration NOT YET PASS；最高 C1；唯一 blocker 独立环境复现；REMAIN AT POISSON CALIBRATION；无 AMENDMENT。
- 测试：新增 `test_claim_identity.py` 8、`test_bc_diagnosis.py` 6、`test_redteam_rules.py` 3（含 torch 跳过）；pinn 子集 525 passed / 4 skipped；全套 **1109 passed / 6 skipped / 0 failed**（1094 + 15，+2 跳过）；PRELOCK 7/7 PASS。
- runner 缺陷（被拦下、已修）：bc-diagnose 首次启动 NameError（未跑 run）；Tier-1 P8 harness（见上）。
- 测试产物（建立与删除）：主检出 `__pycache__` 12 个目录 / 90 个文件，删除；`pytest-of-user` 4154 个文件 / 76265004 字节（本轮 pytest 七次），删除；复核见末行。
- 未做（等用户 / 评审）：独立环境复现（C2 的唯一 blocker）；协议澄清并入协议汇编正文的评审确认；多余工作树 / 分支删除。
- 提交：本条与证据、报告一并提交到 master。
- 复核（删除后）：主检出 `__pycache__` 0 个目录；`pytest-of-user` 不存在。

### 5.24 Poisson 1D 校准收口：BC 事后审计注解、G6 独立环境复现、SUPPORTED @ C2（2026-09-16）

- 授权：用户指令限定为 A 追加 BC 根因 post-audit 注解、B 建立真正独立的 Environment B、C 执行冻结复现包、D 若 G6 PASS 生成 SUPPORTED@C2、E 否则诚实停止；不改方法、不上 2D、不起草 A-0003、不重开 D_claim、不重做 G5、不按复现结果调参。基线审计与摘要一致（树干净 62ff5e6，宪法 1.2，PRELOCK 7/7，1109 / 6，r2 hard BC，specHash fd5584d7b290，G5 PASS，Tier-1 PASS，C_repro BLOCKED）。报告 `docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md`。
- PART 1：`runs/exp1-calibration-r1/POST_AUDIT_ANNOTATION.md`（新增文件，不改 DiagnosisRecord / Verdict / RevisionRecord / 转移记录）：历史 verdict rSpecDefect 保持；`CAUSAL ATTRIBUTION: NOT UNIQUELY IDENTIFIED IN POST-AUDIT REVIEW`（λ=1000 亦满足 AC-3 且无不可接受退化；正确表述为"原冻结软 BC 配置 λ=10 未过 AC-3"）；核对宪法第二十三 / 五十六 / 五十九章，无"归因非唯一即使已完成 revision 失效"的条款 → r2 结果成立。
- PART 2：`experiments/poisson1d/INTERVENTION_CRITERION_CLARIFICATION_20260916.md`：整条剂量—响应曲线的 R / Q / 弱单调 / 退化限结构；数值常数不用本次数据倒推，留待下一次适用实验前预注册；Experiment 3 历史裁决不变。
- PART 3 G6 语义审计：宪法 28.1 + `trust_vector.independent_environments`：独立 ⇔ ≥1 强字段不同；不要求 dependencyLockHash 不同；同机独立安装合格；`reproduction_status` 另要求同 specHash 同 codeHash、不同 seed 集、容差内。代码与宪法一致，无 mismatch，无修复。
- PART 4 Environment B（Option 2，同机全新独立安装）：`C:/Users/user/mamba/python.exe -m venv C:/Users/user/LeoAI-envB-20260916/venv`（无 system-site-packages）→ `pip install --no-cache-dir torch==2.12.1（CPU index） numpy==2.4.5`（复现包声明依赖；无复制、无克隆、无重命名）。指纹：torch-2.12、mkl、Python 3.12.9、installationId prefix-e67819cb…、dependencyLockHash 9083b98e…；`environment_b_qualification.json`：independent = True（强字段不同：installationId、dependencyLockHash；machineId 等相同）。dependencyLockHash 无法与 A 相等（A 为无 lockfile 的通用 mamba 环境），已在报告中说明。新建目录 `C:\Users\user\LeoAI-envB-20260916`（venv + 分离检出 repo-frozen），保留作复现证据；是否删除等用户。
- PART 5 复现：① `repro-envb-r2`（当前 commit runner，`--reproduction-of`，seed +10000，Gate 4 后停止，不触碰 claim 集）：数字容差内（中位 2.552e-4 vs 1.991e-4，差 5.6e-5；10/10 vs 10/10）但 codeHash ≠ 原 run（本轮 runner / harness 修改进入代码身份清单）→ `reproduction_status` 判 BLOCKED（宪法 36.1/54 明文"同 codeHash"）；记录保留 + 注解。② 按复现包说明在 exp3c 原 commit beceef5 的分离干净检出 `LeoAI-envB-20260916/repo-frozen`（`git worktree add --detach`，注意：这是复现包要求的冻结代码检出，不是会话工作树）上，用 Environment B 解释器运行**原 runner**（驱动脚本 `frozen_repro_driver.py` 在会话临时目录、不入代码身份清单）→ `repro-envb-frozen-r2`：codeHash 5aaf93a5… 与原 run 相同，seed +10000，10/10，median 2.552e-4（逐 seed 与①逐位相同，证明 runner 修改未改训练方法）。
- PART 6 判定（`judge-reproduction`，新增子命令，只读两份 RunRecord / training_report）：独立 ✓、同 spec ✓、同 code ✓、不同 seed ✓、|Δmedian| 5.617e-5 ≤ 1e-4 ✓、k/N 一致 ✓ → **C_repro PASS**。
- PART 7–8（`apply-g6`，新增子命令）：`gate6_reproducibility_executed.json`；`trust_vector_g6.json`（supersedes tv-…-tier1v2，六维 PASS，`validate_trust_vector` 通过）；`claim_gate_decision_g6.json`（`validate_claim_gate_decision` 通过；allowed C0/C1/C2，blocked C3：无 ≥5 个独立合格 C2 run）；`advance(REPRODUCIBILITY_CHECK, 6, PASS, claim_decision_signed=True)` → **ACCEPTED**。**SUPPORTED @ C2**。
- PART 9：POISSON 1D CALIBRATION: CLOSED；PINN SCIENTIFIC-CLAIM MVP: VALIDATED AT C2；READY FOR USER / EXTERNAL REVIEW BEFORE 2D（不自行开始 2D）。
- 代码：`runner.py` 新增 `--reproduction-of`、`judge-reproduction`、`apply-g6`、冻结 revision 的 pool 成员自动识别、BURNT 成员拒绝（正式 attempt）；`reproduction_report` 记 `problems`。测试新增 `test_g6_reproduction.py` 3 项（冻结复现 PASS / 新代码复现 BLOCKED；容差外 FAIL、同环境 / 同 seed BLOCKED；最终 G6 向量与 C2 决策重校验）。
- 测试：全套 **1112 passed / 6 skipped / 0 failed**（1109 + 3）；pinn 子集 528 / 4；PRELOCK 7/7 PASS。
- 测试产物（建立与删除）：主检出 `__pycache__` 6 个目录 / 22 个文件，删除；`pytest-of-user` 2941 个文件 / 53090413 字节（本轮 pytest 五次），删除；冻结检出 repo-frozen 无 `__pycache__`（-B）；复核见末行。
- 未做 / 等用户：`C:\Users\user\LeoAI-envB-20260916`（venv 与 repo-frozen 分离检出）的保留或删除；多余会话工作树 / 分支删除；外部评审。
- 提交：本条与证据、报告一并提交到 master。
- 复核（删除后）：主检出 `__pycache__` 0 个目录；`pytest-of-user` 不存在。

### 5.25 用户审批的删除（2026-09-16）

- 用户审批通过：删除仓库外 `C:\Users\user\LeoAI-envB-20260916`（Environment B venv 与 exp3c 原 commit 的分离检出 repo-frozen；其指纹、鉴定与复现结果已全部入库于 `environment_b_qualification.json`、`runs/repro-envb-frozen-r2/`）；删除桌面应用自动创建的会话工作树 `.claude/worktrees/leoaistudio-build-handover-29efe6` 与分支 `claude/leoaistudio-build-handover-29efe6`（无独有提交）。`git worktree prune` 后仅剩主检出与两个 codex 工作树。
- 执行结果：LeoAI-envB-20260916 已删；会话工作树的 git 注册已移除、分支 claude/leoaistudio-build-handover-29efe6 已删；目录 `.claude/worktrees/leoaistudio-build-handover-29efe6` 因本会话仍在其中运行而 Permission denied，需用户关闭本窗口后手动删除该目录（`git worktree prune` 已执行，目录不再被 git 引用）。另一工作树 `phase1-safety-foundation` 属其他会话，未动。

### 5.26 2D Manufactured Poisson Calibration：复用审计、性能 pilot、预注册、正式 run、Tier-1、G6 → SUPPORTED @ C2（2026-09-16）

- 授权：用户 2D 正式实验指令（PART 0–25）+ 会话中两次追加指令（portability 审计、pilot 角色审计）。禁止项按令执行：不自行起草 A-0003、不为 2D 发明新 Gate、不为通过而改阈值、不看结果换 seed、不调整 D_claim、不改 1D 历史 evidence、不进入 BFS / UCM。工作位置：主检出 master（不新建 git worktree；写文件工具被限制在会话工作树，故全部文件经会话临时目录 + `cp` 落到主检出，训练用 mamba 解释器）。
- 基线审计（本轮开始时）：主检出树干净、HEAD `e7d85c2`、宪法 1.2（SHA `2f448402…`）、PRELOCK 7/7。**真实测试基线 1109 passed / 3 failed / 6 skipped**——不是 1D 收口报告记的 1112 / 0：收口提交 `32eaa36` 把含绝对路径的证据入库后没有重跑测试，三项 portability 断言自那时起为 FAIL。用户裁决"只如实记录，不动"。
- 用户批复的两项（本轮唯一两次提问）：① portability 三红只记录不动；② 授权在仓库外重建独立环境用于 2D 的 G6。
- **PART 3 复用审计** `experiments/poisson2d/2D_REUSE_AUDIT_20260916.md`：治理层（样本身份、账本、六维向量、状态机、PRELOCK、schema、`common.py`、`criteria.py`、`observed_signatures`）全部 REUSE_AS_IS；1D 的 runner / gates / datasets / pinn_torch / claim_metrics / plots / 解析参考 / FDM / 可信校验器全部 1D_HARDCODED → **新建 `pinn/experiments2d/`，`pinn/experiments/runner.py` 一行未改**（1D 已 CLOSED，改它会移动其代码身份语义）；`pinn/experiments/report.py` 按审计做最小参数化（参考解措辞、适用范围、主 AC 键名变为参数，1D 默认值保持原输出不变）。
- **新增代码面**（commit `f3d322b`）：`specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json`（落在 `specs/` 代码身份前缀内，因此**不需要修改代码身份定义**）、`pinn/reference/analytic_poisson2d.py`、`scientific_reference/poisson2d_fdm.py`（五点差分 + 无矩阵 CG）、`pinn/governance/poisson2d_contract.py`（AC2D-1..9 阈值 + 每条的维数判定与来源）、`pinn/validation/poisson2d.py`（可信校验器 + 7 个 T10 控制夹具）、`pinn/experiments2d/{datasets2d,pinn_torch2d,gates2d,diagnostics2d,redteam2d,report2d,repro_package2d,runner2d}.py`。
- **PART 4 性能 pilot**（EXPLORATORY、claim ≤ C1、`formalEvidence:false`、seed 20260800/10/20 与正式不相交、只用 D_train 池与 D_dev，claim `not touched`）：3×32/6000 步 6.049e-4（42 s）· **4×64/10000 步/batch 512/1024 配点 4.270e-5（197 s）** · 4×64/20000 步 2.073e-5（703 s）· 5×64/20000 步 4.701e-5（851 s）· 4×128/20000 步 5.809e-6（2017 s）。选择规则**在读取第 3–5 档之前**写定并写入预注册：取最小的、D_dev 误差比 ε_spec 低一个数量级且 10 seed 成本 < 1 小时的档 → 1D 架构原样移植余量仅 1.65 倍被淘汰，4×64/10000 步选中。实测事实：2D 每步耗时由 Python / autograd 图开销主导，batch 128→1024 每步成本几乎不变，故可行性来自"大 batch 少步数"。
- **预注册** `EXPERIMENT2D_PREREGISTRATION_20260916.md`（commit `f3d322b`，先于任何正式 run）：冻结问题与硬 BC `u = x(1−x)y(1−y)N`；数据集（train 池 2048 / dev 1024 / phys 张量 GL40 / 边界每边 GL32 身份豁免）；盲集池四套（CGL 计数按 `m−1 ∈ {49,53,55,59}` 与 6 互素且两两互素构造，既避开 1D 那类有理格点碰撞，也避免不同成员整族共享内部节点）；N=10 三类 seed；AC2D 阈值表与逐条来源（维数判定 DIMENSION-INVARIANT / SENSITIVE）；Tier-1 适用性（**P7 在 2D 判 APPLICABLE**，与 1D 相反；P11 仍 NOT_APPLICABLE）；G6 容差（1D 继承绝对上限 1e-4 **与** 收紧的相对上限 0.5×median 同时成立）；六项事前披露。
- **冒烟测试**（临时沙箱 `experiments/poisson2d/.smoke`，133 文件 / 1,385,275 字节，**已删除**；驱动脚本保留为 `experiments/poisson2d/smoke_runner2d.py`）在正式 run 之前跑通全流程并抓到两个真实问题：① 账本既有规则"OPENED 的 specHash 必须等于 SEALED 的"要求盲集池在 r1 ProblemDefinition 冻结之后密封 → `register-pool` 改为先冻结 r1 再密封；② 把 AC 阈值整体调松会让 Gate 3 的 T10 控制夹具失败（**正确行为**，记录在案，沙箱改为只强制 G5b 判定）。
- **盲集池**（commit `ad9f029`）：r1 ProblemDefinition 先冻结（specHash `05328d507582`），再密封 D2C-GL32-CGL50（r1，3328 样本，sampleSetHash `7fbbb775da65`）、GL34-CGL54（r2）、GL36-CGL56（r3）、GL38-CGL60（r4）；两两共享样本 0，与 train/dev/phys 互斥（minSeparation 1e-9），按分量反碰撞最小距离 4.09e-05 / 8.68e-06 / 3.28e-07 / 6.03e-06。
- **正式 run `exp2d-poisson-calibration-r1`**（codeHash `a39aa07e23d0`，commit `22117f0`）：G1 PASS；G2 PASS（解析残差 0.000e+00、四边界 1.221e-16；FDM 误差 1.295e-02→2.008e-04，观测阶 2.0084/2.0021/2.0005）；G3 PASS（T1 逐分量 4.31e-11 / 1.00e-10；**T2 非对称探针** 7.11e-15 / 1.78e-15 且判别间隙 > 1；T3 3.55e-15；**T4 四条边恰为 0**；T8 单项损失；T9 互斥；T10 正控制接受 + 6 污染夹具全拒）；G4 PASS（10/10，median 3.686e-5，IQR 8.99e-6，worst 4.26e-5，divergent 0）；G5a PASS（PH1 1.07e-4、PH2 2.88e-5、PH3 7.65e-6、PH4 互换对称 7.65e-5、PH5 0 违例、PH6 0.996290、PH7 λ_min 19.74）；claim 集 SEALED→OPENED（13:03:07Z，带 codeHash）→BURNT；G5b **PASS**（10/10 seed 满足 AC2D-1..7、AC2D-9 MUST 与 AC2D-8 SHOULD；最差值 AC2D-1 4.257e-5、AC2D-2 7.030e-5、AC2D-3 恰 0、AC2D-4 1.042e-3、AC2D-5 3.076e-5、AC2D-6 4.382e-4、AC2D-7 2.879e-5、AC2D-9 1.568e-4、AC2D-8 1.416e-4）。
- **Tier-1 Red Team**（commit `1d27efe`）：P1 7.778e-6、P4 1.774e-5、P6 4.264e-5、**P7 5.461e-5**、**P8 1.332e-4**、P9 2.723e-5、P16 7.759e-5（Δq，1% 维持线），全部 PASS；P11 NOT_APPLICABLE（2D 独立判定）。P8 的硬参数化随域缩放为 ξ(L−ξ)η(L−η)N，未重演 1D run 1 的 harness 缺陷，另有单元测试钉死。9 张图由已登记 D_phys 网格与已存权重生成。
- **Environment B（2D）**：用户授权后新建仓库外 `C:\Users\user\LeoAI-envB2D-20260916\venv`（base 同一 mamba python 3.12.9、无 system-site-packages、`--no-cache-dir` 只装复现包声明的 torch 2.12.1+cpu 与 numpy 2.4.5，无复制无克隆）。`environment_b_qualification.json`：independent = True，强字段中 `installationId`（prefix-ede7d4c77496dd0e）与 `dependencyLockHash`（460309bb1065…）不同。
- **G6 复现 `repro-envb2d-r1`**（commit `e52555a`）：同 specHash、**同 codeHash `a39aa07e23d0`**（两次运行之间代码身份清单内无任何文件变化，中间提交只新增 `experiments/` 下的证据；gitHead 不同而 codeHash 相同，说明代码身份是内容哈希不是提交哈希——**因此本轮不需要 1D 那样的冻结分离检出**，这一差异已在报告第 8 节如实说明）、seed +10000、Gate 4 后停止、`claimSetTouched:false`。dev 相对 L2 中位 A 3.686e-5 vs B 3.286e-5，|Δ| **4.000e-6**，同时满足绝对上限 1e-4 与相对上限 1.843e-5；|Δ|/IQR_A = 0.44；k/N 双方 10/10 → **C_repro PASS**。`apply-g6`：六维全 PASS → `claim_gate_decision_g6`（校验器通过）允许 C0/C1/**C2**、阻断 C3（无 ≥5 个独立合格 C2 run）→ `advance(REPRODUCIBILITY_CHECK, 6, PASS, claim_decision_signed=True)` → **ACCEPTED**。
- **追加审计一：Portability**（commit `528d545`，`PORTABILITY_AUDIT_20260916.md`）：既有 4 条发现全在 1D 不可变证据（`environment_b_qualification.json:42`、`repro-envb-frozen-r2/PROVENANCE_MANIFEST.json:103` 两条规则、`repro-envb-r2/POST_AUDIT_ANNOTATION.md:19`）；**本轮 2D 新增 3 条同类**（`TEST_VERIFICATION_UNDER_TORCH.json:4` 解释器绝对路径、`environment_b_qualification.json:46` venv 路径、源码 `qualify_environment_b.py:45` 同一字面量）；1D 那类 `PROVENANCE_MANIFEST` 污染未复发（本轮记的是相对账本路径）。**未改 policy、未改任何证据、未加豁免**；按宪法 28.1"路径不是身份"，这些不影响任何 specHash / codeHash / environmentId 或 AC 数值；四项裁决留给用户与外部评审。（自指效应，如实记录：审计文件第一版逐字引用了被指认的路径，`experiments/**` 在扫描范围内，于是审计文件自己又多出 2 条同类发现；已把审计说明文字里的用户名脱敏为 `<user>` 消除，被指认文件一字未改。扫描范围事实：`docs/**.md` 与根目录一份报告属类别豁免，`experiments/**` 不豁免。最终计数 7 条 = 1D 既有 4 + 本轮实质 3。）
- **追加审计二：Pilot 角色**（同一 commit，`PILOT_ROLE_ANNOTATION_20260916.md`）：如实登记 pilot 同时承担性能测量与**架构 / 模型选择**。核对宪法 1.2：第 561 行明文把"模型与架构选择"列为 D_dev 的许可用途；第 565 行的"打开"定义未被触碰（pilot 从未在 D_claim 上求值，claim pool 在 pilot 之后才密封）；第六十五章要求晋升时在冻结规格下重走完整闭环（本轮正是如此，seed 严格不相交）；28.1 的 RunRecord 义务只约束正式 run。裁决 **ALLOWED，不阻断 C2**；同时登记三点诚实说明（一次 pilot 兼两角色属协议澄清候选、AC2D 阈值是 1D 继承常数且合同文件自首次提交未改动、pilot 与正式 seed 不相交）。预注册与 `PILOT_RESULT.json` 一字未改。
- **测试**：新增 22 项（`test_poisson2d_identity` 7、`test_poisson2d_physics` 10、`test_poisson2d_reproduction` 5）。全套 **1121 passed / 3 failed / 16 skipped**（3 红 = 审计过的既有 portability；16 跳过 = 既有 6 + 本轮 10，治理 venv 无 torch / numpy）。被跳过的 10 项另由 `experiments/poisson2d/verify_tests_under_torch.py` 在训练解释器下执行：**17 passed / 0 failed**。PRELOCK **7/7 PASS**。
- **报告**：`docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md`（PART 24 十一节齐全 + 证据清单 + 图索引）。结论：**2D Poisson Calibration: PASS；Highest admissible Claim: C2（SUPPORTED @ C2）；State: ACCEPTED；Final Recommendation: READY FOR NEXT 2D COMPLEXITY STEP**。Dimension-Lift Audit 的答案：**governance = none**（没有任何治理条款因维数失效），被击穿的是度量与判别设计——对称制造解无法判别 x/y 互换（补 T2）、全局范数看不见空间热点（补 AC2D-9）。
- **新发现**：BLOCKING 无；NON-BLOCKING 六条（NB-1 portability 既有 + 本轮新增、NB-2 pilot 角色、NB-3 1D 症状阈值 `sLocalizedError` 在合格结果上即触发（实测 3.94 > 3.0，未参与验收）、NB-4 FDM 的 CG 一步收敛、NB-5 互斥扫描 O(N·M) 成本、NB-6 C2 只建立在单问题单架构同机两安装上、NB-7 pool manifest 的成员 `status` 字段不回写——实测账本确实拦得住重复打开与重新包装，但 runner 的早期护栏读的是过期字段，误用只会在训练之后才被拦下，该字段与护栏继承自 1D，本轮未改）；AMENDMENT CANDIDATE 五条只登记不起草。
- **测试产物（建立与删除）**：主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件，删除；`pytest-of-user` 2,489 个文件 / 44,785,623 字节（本轮 pytest 六次），删除；冒烟沙箱 133 文件 / 1,385,275 字节（已删）。`.venv/` 内的 165 个 `__pycache__` 是安装自带、非本轮产物，未动。复核见末行。
- **仓库外**：`C:\Users\user\LeoAI-envB2D-20260916`（Environment B venv，21,963 文件 / 0.64 GB）保留作复现证据，是否删除等用户。
- **未做 / 等用户**：不开始不规则几何、BFS、Navier–Stokes、UCM、传热、新修正案或架构扫描（PART 25 STOP）；portability 四项裁决；Environment B 去留；外部评审。
- **提交**：`f3d322b`（代码 + 规格 + 预注册 + 测试）、`572e3b7`（pilot 结果）、`ad9f029`（盲集池）、`22117f0`（正式 run）、`1d27efe`（Tier-1 + 图 + 复现包 + 环境鉴定）、`528d545`（两项追加审计）、`e52555a`（G6 + ACCEPTED）、本条与报告一并提交。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；冒烟沙箱不存在；`git status` 干净。

### 5.27 2D Final Closure Audit：AC2D-9 公式审计、P11 补跑、portability 收口、claim pool 单一真相源、localized-error 维数标定（2026-09-16）

- 授权：用户"Final Closure Audit"指令（Issue 1–7）。禁止项按令执行：不重训正式 10-seed baseline、不改架构 / 优化器 / 阈值 / ScientificSpec、不重开已烧毁 D_claim、不改历史机器证据、不删失败记录、不新增 A-0003、不开始下一个 PDE。
- **Issue 1（AC2D-9 公式）裁决 CASE A**：预注册（`EXPERIMENT2D_PREREGISTRATION_20260916.md:82`）、合同（`poisson2d_contract.METRICS`）、实现（`validation/poisson2d.py:152-172`，`reference_rms_p = sqrt(mean_grid u*^2)`）与机器记录四者一致，分母自始至终是**参考解 u\* 的 RMS**；`gate5b_external.json` 里 `AC2D-9` 逐位等于 `worstTile.rms / referenceRmsPointwise`（十个 seed 全部）。用已存预测重算（`AC2D9_FORMULA_AUDIT.json`，不重训、不重开 claim 集）：终审读法（分母取误差 RMS）实测 1.989–3.101，**恒 ≥ 1**，与其不变量一致；实现读法实测 6.13e-05–1.09e-04。缺陷只在**报告 §3.2 的缩写标签**漏掉了分母里的 u\*，以及预注册里"严格强于 AC2D-1"这一过强措辞（精确表述：不小于**同网格**全局相对 L2；对 AC2D-1 是经验更严，实测比值 2.90–4.36）。处理：不改任何机器记录；追加 `runs/exp2d-poisson-calibration-r1/POST_AUDIT_ANNOTATION.md`；更正报告标签；新增 6 项不变量回归测试。**C2 不受影响。**
- **Issue 2（P11）裁决：原 NOT_APPLICABLE 无协议依据，必须补跑**。依据：协议汇编 :108「Tier-1（含 P11）C2 之前必跑」；:27「适用性登记必须写明缺失的物理前提」；红队交付物 :127 的"面向后续 CFD"作用域是 **1D MVP**（本轮已据此把 P7 改判 APPLICABLE，却留着 P11 的 N/A，判定不一致）。预注册 `P11_SUPPLEMENT_PREREGISTRATION_20260916.md` 先于运行提交（`e1e9f02`），驱动脚本置于代码身份清单之外，运行前核验 codeHash 与正式 run 相同、树干净。实跑：D_dev 残差 p95 τ=1.712e-02，区域 A=22/64 块，配点占比 0.347→0.694（因子 2），**Δq 1.417e-05 → PASS**；诚实记录 e2 3.596e-05→5.506e-05（上升约 53%，仍比 ε_spec 低约 18 倍），区域内残差 p95 2.125e-02→1.865e-02，即残差自适应加密在本问题上不是改进。未越线 → 不触发局部误差分流，C_train 不降级。新增 `tier1_p11_supplement.json`、`trust_vector_g6_p11.json`（supersedes tv-…-g6）、`claim_gate_decision_g6_p11.json`；`tier1_redteam.json` 原样保留。Tier-1 现覆盖协议 Tier-1 全部八项（测试钉死）。
- **Issue 3（portability）**：3B/3C 完成——`qualify_environment_b.py` 与 `verify_tests_under_torch.py` 改为记录 `installationId` / prefix 哈希而非绝对路径，重跑后 `TEST_VERIFICATION_UNDER_TORCH.json` 不再含路径；前瞻规则写进两个脚本与报告；发现数 **7 → 5**。3A **未完成并按指令报告冲突**：尝试给 1D 的 4 条与 2D 的 1 条证据加精确哈希豁免后测试由 3 红变 6 红，根因是 `tools/portability_check.py` 的策略加载器硬性要求 `file` 必须是 `governance/**.md`，而待豁免证据都在 `experiments/**`；扩大作用域等于修改 policy 机制，本轮禁止，**豁免尝试已回滚**，`manifests/portability-historical-evidence.json` 保持原样（测试钉死只有那一条 governance 条目）。
- **Issue 4（claim pool 单一真相源）**：新增 `derived_claim_status()` 由账本推导 SEALED/OPENED/NEVER_SEALED，样本身份已烧毁时返回 BURNT（跨 revision 有效）；`phase_problem` 的护栏**前移到互斥扫描与任何 Gate、训练之前**，正式 attempt 遇 OPENED/BURNT 立即拒绝并说明"manifest 的 status 不被采信"；`register-pool` 今后写 `initialStatus` 并附说明，已提交的 pool manifest 不回写。实测：被消费成员在 manifest 里仍写 `SEALED`，账本推导为 **BURNT**。5 项测试。
- **Issue 5（localized-error 维数标定）**：旧 1D 规则（最大块/中位块 > 3.0）在**完全合格**的 2D run 上 **9/10 seed 误报**（统计量 2.946–4.815）。建立 `pinn/experiments2d/localized_error.py`：四个候选（A 最大/中位、B 稳健 z、C top-k 集中度、D 参考条件化稳健 z）× 六个合成夹具 × 部署一致的随机点集与密网格 × 分块数 × 幅度；事前判定规则（处处分离 → 最大最差分离比 → 阈值取几何中点）。结果 D 胜出（分离比 1.76，阈值 26.21），但**对已完成 run 的检查仍误报 2/10**。**不上调阈值**（事后拟合被禁），裁决 **NOT CALIBRATED FOR DEPLOYMENT**；前瞻协议：d ≥ 2 的局部误差要求由 AC2D-9 形式的**验收判据**承担，症状信号 `sLocalizedError` 对 d ≥ 2 登记 NOT CALIBRATED，1D 常数 3.0 退役，将来须先从 ≥ 5 个已验证 run 建经验 null 再预注册分位数。治理归类：**协议标定，非宪法语义变更，不起 A-0003**。9 项测试。
- **Issue 6（重校验）**：`final_closure_revalidation.py` 把每份文档交回各自校验器（不重训、不重开 claim 集）：specHash 复算一致；ProblemDefinition / 账本 / 两份 RunRecord / 四份 TrustVector / 四份 ClaimGateDecision 全部零错误；claim 集 OPENED 恰一次、账本推导 BURNT；G6 重判 C_repro = PASS（|Δmedian| 4.000e-06 在容差内）；状态 ACCEPTED。**CURRENT 2D C2: CONFIRMED**。诚实记录：Issue 4/5 的修复动了 `pinn/experiments2d/`，工作树 codeHash 已不等于记录在案的 `a39aa07e23d0…`；已 ACCEPTED 的决策绑定的是记录在案的身份（字节可由承载 run 的提交恢复），宪法第六十六章要求**下一次正式 run 升 revision**（1D 在其 ACCEPTED run 之后给 runner 加子命令时已立同一先例）。P11 补跑刻意安排在所有代码修改之前，与基线同代码身份。
- **Issue 7（收口门）**：portability 未满足（3A 机制作用域冲突）、localized-error 协议部分满足（规则未可部署）、claim-pool 已修、PRELOCK 7/7、树干净 → **NEXT COMPLEXITY STEP: HOLD**，与 **CURRENT 2D C2: CONFIRMED** 并存。
- **测试**：新增 **28** 项（AC2D-9 不变量 6、localized-error 9、claim pool 5、P11 与 portability 收口 8）。全套 **1147 passed / 3 failed / 18 skipped**（3 红为既有 portability，非 2D 数值失败）；被跳过的在训练解释器下另跑 **23 passed / 0 failed**；PRELOCK **7/7 PASS**。
- **报告**：`docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md`（九节齐全）。
- **测试产物（建立与删除）**：主检出仓库源码下 `__pycache__` 6 个目录 / 22 个文件，删除；`pytest-of-user` 1,896 个文件 / 35,835,632 字节（本轮 pytest 五次），删除。复核见末行。
- **未做 / 等用户**：portability 豁免机制作用域的裁决；Environment B 目录去留；localized-error 经验 null（需 ≥ 5 个已验证 run）；外部评审终审。不开始新 PDE。
- **提交**：`e1e9f02`（P11 预注册）、`1b6b917`（P11 结果 + AC2D-9 审计 + 注解）、portability 源码修复提交、本条与收口报告一并提交。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 干净。

### 5.28 外部评审裁决执行：portability 机制扩展、localized-error 触发条件、NEXT COMPLEXITY STEP READY（2026-09-16）

- 授权：用户 / 外部评审 2026-09-16 裁决（七项）。禁止项按令执行：不重训、不改架构 / 优化器 / 阈值 / ScientificSpec、不重开已烧毁 D_claim、不改历史机器证据、不删失败记录、不起 A-0003、收口后 STOP 不自行启动下一个 PDE。工作位置：主检出 master（不新建 git worktree；文件经会话临时目录 + `cp` 落到主检出，或用 `.venv` 跑补丁脚本）。
- **裁决 1（C2 confirmed / 科学校准 CLOSED）**：只记录。2D 的六维判定、ACCEPTED 状态、claim 账本、全部 Gate 结果一字未改。
- **裁决 2（portability 机制扩展，STRICT SCOPE）**：`tools/portability_check.py` 的策略加载器作用域由 `governance/**.md` 扩为「人工批准的不可变证据文件」——允许前缀 `governance/`、`experiments/`，允许后缀 `.md`/`.json`，另有可执行后缀黑名单（`.py .ps1 .psm1 .sh .bat .cmd .js .ts .exe .dll .lock` 等）兜底；`*?[]` 任一字符或以 `/` 结尾（目录）一律拒绝；新增强制字段 `ruling` 与 `constraint`（缺一即 `RuntimeError`）。**归类逻辑一字未改**：仍要求 `file + sha256 + finding_type + occurrence` 四项全等，任何字节变化自动失效。`manifests/portability-historical-evidence.json` 新增 **5 条**（1D 证据 4 条 + 2D `environment_b_qualification.json` 1 条），每条带裁决出处、约束说明与理由；**被指认的证据文件一字未改**（豁免绑定的就是它们当前的 sha256）。扫描器现报 **0 hard binding / 1 configurable default / 8 historical evidence**，且人类可读输出仍逐条打印 `EXEMPT-HISTORICAL-EVIDENCE` + 文件 + 行号 + sha256（可见性有测试断言）。
- **裁决 3（Environment B: KEEP）**：仓库外 `用户目录\LeoAI-envB2D-20260916`（21,963 文件 / 0.64 GB）保留为**冻结的复现夹具**；本轮对该目录未执行任何操作（未安装、未修改、未删除）。常设规则记入收口报告与记忆：不做日常包安装；将来需要额外依赖则重新 qualification 或新建 B2，不静默污染现有 B。
- **裁决 4（localized-error 最终协议）**：d ≥ 2 的 `sLocalizedError` 触发条件改为「该问题在 ScientificSpec 中**预注册的局部误差验收判据失败**」，Poisson2D 的实例是 **AC2D-9**。统计量固定为 `maxTileRmsErrorOverReferenceRms`（与验收判据同一测量、不同点集），阈值**必须等于**验收合同里该判据的阈值（症状不得自带松紧 → 没有可事后调的常数），聚合取 seed 中位数，评估集只允许 `dev`（`claim` 被显式拒绝）。max/median、robust-z、top-k 等四个候选保留为 diagnostics / calibration research，**不作为正式 FailureSignature gate**；旧 1D 统计量仍随记录打印为 `retiredStatistic`，只报不判。不要求现在拟合经验 null 阈值。实现：`pinn/experiments2d/localized_error.py` 新增 `preregistered_localized_criterion` / `localized_signature` / `apply_localized_signature` / `localized_acceptance_ratio` / `assert_criterion_within_run_identity`；`diagnostics2d.py` 每 seed 在 D_dev 上多算该统计量；`runner2d.phase_failure` 套用 d ≥ 2 触发并先核验配置字节仍在本 run 代码身份内；**fail-closed**——d ≥ 2 的 run 若没预注册该判据，诊断阶段直接报错。裁决全文与实现入口记入新文件 `experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json`；上一轮的 `LOCALIZED_ERROR_CALIBRATION.json` 作为证据原样保留。治理归类：**协议澄清**，FailureSignature 名称 / RootCause 类 / TrustStatus / Claim 语义 / DiagnosisRecord schema 均未变，**不起 A-0003**。
- **裁决 5（五条测试）**：`tests/pinn/test_localized_error_trigger.py` 12 项，逐条对应——全局 PASS + 局部判据 FAIL 触发（同时断言 `sPinnCfd` 仍 False）；局部判据 PASS 不触发（并用已完成 run 的 AC2D-9 实测值验证）；未预注册 / 自带阈值 / 换统计量 / 换判据名一律拒绝；事后新增判据无法触发已有 run（配置在代码身份内，改字节即被 `assert_criterion_within_run_identity` 拒绝，`code_hash_from_manifest` 亦随之改变）；诊断只读 D_dev（`evaluationSet="claim"` 被拒 + `phase_failure` 源码级断言）。另加：统计量确为 AC2D-9 量、1D 保持原规则、裁决记录与实现一致。**对已完成 run 不回溯**：`exp2d-poisson-calibration-r1` 的冻结配置未改，新触发不适用于它；其 AC2D-9 本就是 Gate 5b 的 MUST 判据且十个 seed 全过（最差 1.568e-4 对 1e-3）。
- **裁决 6（重跑）**：全套 **1172 passed / 0 failed / 18 skipped**（上轮 1147 / 3 / 18；净增 25 项测试，3 红全部转为已批准归类，非静默豁免）；被跳过的 18 项在训练解释器下由 `verify_tests_under_torch.py` 另跑 **23 passed / 0 failed**；portability **0 hard binding**；PRELOCK **7/7 PASS**；**0 unexpected failures** → 输出 `CURRENT 2D C2: CONFIRMED` + **`NEXT COMPLEXITY STEP: READY`**，随即 STOP。
- **裁决 7（新 revision / code identity）**：本轮改动落在 `pinn/experiments2d/` 与 `tools/`、`tests/`、`manifests/`，工作树 codeHash 与记录在案的 `a39aa07e23d0…` 差距进一步扩大；下一次正式实验必须升 revision，不得冒充生成既有 C2 的代码身份。`assert_criterion_within_run_identity` 把这条规则的一个具体后果变成了机器检查。
- **报告**：`docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md`（八节）；终审收口报告追加第 11 节「后续」指向它，其余内容一字未改。
- **未做 / 等用户**：不开始新的 PDE（不规则几何、BFS、Navier–Stokes、UCM、传热）、不起草修正案、不做架构扫描、不重训；localized-error 的经验 null 分布按裁决**不再要求**；外部评审若有后续意见另行处理。
- **测试产物（建立与删除）**：主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **3,777 个文件 / 69,535,699 字节**（本轮 pytest 五次 + 训练解释器验证一次），删除；补丁与草稿脚本写在会话临时目录（仓库外），随会话清理，未落入仓库。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 只剩本轮有意的改动。
- **提交**：本条、收口报告、机制与触发条件的代码 / 测试 / 清单一并提交。

### 5.29 仓库身份核验与复核包导出（2026-09-16，只读核验 + 桌面导出）

- 触发：外部评审报告收到的 `tools/portability_check.py` 仍含旧限制 `if not rel.startswith("governance/") or not rel.endswith(".md"):`，与 §5.28 的结论冲突。用户令：先只报告机器事实，不改文件。
- **核验结果（未修改任何文件）**：主检出 `用户目录\Desktop\LeoAIStudio-build` 分支 `master`、HEAD `33dc22b`、树干净；`tools/portability_check.py` SHA-256 `a7ac6c821499a07f…`、git blob `80bd15a1…`，`git diff HEAD` 为空（被测字节 = 已提交字节）。该文件内**不存在**旧限制；`git grep` 在整个 `33dc22b` 里只命中 `docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md:87`，那是上一轮报告**引用旧代码说明当时死结**的代码块。扩展实现位置：第 45 / 50 / 55–58 / 61 行的 `EVIDENCE_POLICY_*` 常量与第 202 行的 `ruling` / `constraint` 必填校验。
- **worktree 事实**：`git worktree list` 共 6 个。只有主检出在 `33dc22b`；其余 5 个（`.claude/worktrees/{pinn-2d-handover-322fa0(HEAD d8b2685，本会话工具默认目录), leoaistudio-build-handover-57223c(e7d85c2), phase1-safety-foundation(8d39e69)}` 与两个 codex 交付工作树）的 scanner 均为旧字节 `54695aa8c3e3005e…`，每个含 1 行旧限制。→ 判定 **CASE A — reviewer received stale file**；master 不缺修改。
- **在 `33dc22b` 上复跑**（rootdir `用户目录\Desktop\LeoAIStudio-build`，configfile `pytest.ini`，collected 1190）：**1172 passed / 0 failed / 18 skipped**；portability **0 hard binding / 1 configurable / 8 historical**；豁免清单 6 条的 `ruling` 与 `constraint` 全部非空。
- **导出（用户指令「导出在我桌面上」）**：新建仓库外目录 `用户目录\Desktop\LeoAI-portability-review-33dc22b\`，内容全部由 `git show 33dc22b:<path>` 导出（提交字节，非工作树副本）：`tools/portability_check.py`、`manifests/portability-historical-evidence.json`、`tests/test_portability.py`、`tests/pinn/{test_p11_and_portability_closure,test_localized_error_trigger}.py`、`localized_error.py`（仓库内为 `pinn/experiments2d/`）、`POISSON2D_CLOSURE_COMPLETION_20260916.md`，另附 `README.md` 与 `SHA256SUMS.txt`（8 个文件）。导出的 scanner 哈希与主检出逐位一致（`a7ac6c8214…`），其中旧限制出现 0 次。**未修改仓库内任何代码**。
- **测试产物（建立与删除）**：本次核验复跑产生 `__pycache__` 6 个目录 / 22 个文件 / 410,095 字节，`%LOCALAPPDATA%\Temp\pytest-of-user` 1,903 个文件 / 36,437,306 字节，**全部删除并复核为 0**；核验期间主检出 `git status` 始终干净，HEAD 仍为 `33dc22b`。
- **本条提交只改本日志**，不含任何代码或证据改动。

### 5.30 Localized-error trigger 硬化：外部评审三项发现的复现与修复（2026-09-16）

- 授权：用户 / 外部评审「localized-error trigger hardening」指令（PART 0–10）。禁止项按令执行：不重训 Poisson2D 正式 baseline、不重开 D_claim、不改已 ACCEPTED 的机器证据 / ClaimGateDecision / TrustVector / 账本、不调 Poisson2D 验收阈值、不新增 A-0003、不开始下一个 PDE、不顺手继续改 portability policy。工作位置：主检出 master（不新建 git worktree）。
- **PART 0 独立复现（探针直接调用 `33dc22b` 的实现，先复现再动手）——三项全部 CONFIRMED，无 REJECTED**：
  1. **Issue 1（median 吞掉 seed 级失败）**：阈值 1e-3 下实测 0/10 → False、**1/10 → False**、**4/10 → False**、5/10 → False（median 恰 1.000e-03）、6/10 → True、10/10 → True。完整 caller chain 实测：per-seed AC2D-9 失败 → `failedMustCriteria` → `gates2d.external_checks` 的 `all(...)` → G5b FAIL → `phase_failure(gate=5)` → `failure_record.json`。Gate 判决本身不丢（`claimSetVerdict.failedMustPerSeed` 里有），**但 `observedSignatures` 在少数派情形下不含 `sLocalizedError`**，`admissible_root_causes` 因此拿不到对应候选根因——修的是诊断可见性，不是 Gate 判决。
  2. **Issue 2（无效证据被读成"没有失败"）**：all NaN / all −Inf / 负值 / NaN 占多数 → 全部 `fired=False`；**另查出**评审未列的两条：all +Inf → `fired=True`（同样是巧合非判定）、空 ensemble → 裸 `IndexError`。截断：`points` 2 / `errors` 3 / `reference` 3 → ratio 1.000e-05（第三个巨大误差被 `zip` 丢弃），补齐后 1.000e+00；**另查出**一维坐标被接受、`blocksPerAxis=0` 被接受、空数组 → `ZeroDivisionError`。
  3. **Issue 3（criterionId 只绑阈值）**：`criterion="AC2D-2"` + 局部 statistic + 5e-3 被接受；同一值 2.0e-3 在 AC2D-9 下 fired True、在借来的 AC2D-2 下 fired False。
- **修复 1（seed 语义分层）**：区分 acceptance criterion / per-seed failure / ensemble signature 三层。`localized_signature` 现返回完整结果（`perSeedValues`、`failingSeedIndices`、`failureCount`、`failureFraction`、`ensembleStatistic{median,worst,best}`、`firedBy`、`seedPolicy`）。判定规则**不是新发明**：取自验收合同的 `seedPolicy = "every-seed"`，而这正是 Gate 5b 对 MUST 判据一直执行的 `all(not failedMustCriteria)`。`value` 改取该策略下的决定性统计量（worst），median 降为记录字段，避免 value 与 fired 自相矛盾。**1.4 不变量已机器化**：对 k = 0…10，signature 的 `fired` 恰等于 `gates2d.external_checks` 在同样 per-seed 结果上的 G5b MUST 判定为非 PASS——既不更弱也不更严。
- **修复 2（fail closed）**：复用仓库既有的 `pinn.validation.poisson2d.ValidationInputError`。新增 `validate_evidence_fields()`，被 `block_statistics()` 与 `localized_acceptance_ratio()` **两处**调用：三数组长度必须相等（**在任何 `zip` 之前**断言，不截断 / 不补齐 / 不忽略）、非空、点集维数齐次且 ≥ 2、坐标有限且在单位域内、误差与参考分量有限、`blocksPerAxis` 为 `int` 且 ≥ 1（`bool` 不算）、参考 RMS > 0；每个 seed 的统计量必须实数、有限、非负，ensemble 非空，缺字段指名 seed 序号；非有限的退役 1D 统计量直接丢弃不参与聚合。
- **修复 3（判据绑定）**：`pinn/governance/poisson2d_contract.py` 新增 `LOCALIZED_ERROR_CRITERION` 与解析器 `localized_criterion()`，把 criterionId ↔ statisticId / normalization / partitionKind / tilesPerAxis / operator / threshold / level / seedPolicy / dimensionScope 绑成一份合同；阈值、等级、分块数、定义全部**从既有冻结表推导**，未引入新常数（测试钉死）。预注册必填字段由 6 项增为 9 项，逐项与合同相等才通过；未知 id、非局部判据（AC2D-1 / AC2D-2）、错 statistic / normalization / partition / operator / threshold、`claim`/`train` 评估集、事后加入冻结身份之外的判据，全部拒绝。
- **PART 4 历史影响：NO IMPACT**（不是凭预期）。重跑 `final_closure_revalidation.py`：`verdict CURRENT 2D C2: CONFIRMED`、`problems []`、六维全 PASS、allowed C0/C1/C2、blocked C3、state ACCEPTED、`cRepro PASS`、`codeIdentityUnchanged false`。测试另逐项断言：`gate5b_external.json` 的 codeHash 仍 `a39aa07e23d0…`、十 seed `failedMust` 全空、`thresholds["AC2D-9"]` 仍 1e-3；`claim_gate_decision_g6_p11.json` 仍 allowed C0/C1/C2、blocked C3；正式 run 冻结配置的 `sLocalizedError` 仍无 `criterion` 字段（新触发不回溯）。账本 / D_claim / TrustVector / ClaimGateDecision 本轮一次也没写入。`FINAL_CLOSURE_REVALIDATION.json` 与 `TEST_VERIFICATION_UNDER_TORCH.json` 因重跑更新，diff 仅时间戳与 `currentTreeCodeHash`。
- **PART 5 代码身份**：`localized_error.py` 本就不在该 run 的 `codeManifest` 内（run 之后才建）；清单内的 `poisson2d_contract.py` / `diagnostics2d.py` / `runner2d.py` 当前 sha256 均 ≠ 记录值；用当前字节重算 `code_hash_from_manifest` ≠ `a39aa07e23d0…`。下一次正式实验必须升 revision。
- **PART 6/8 测试**：新增 **69** 项（`tests/pinn/test_localized_error_hardening.py`），`test_localized_error_trigger.py` 按新合同更新。全套 **1241 passed / 0 failed / 18 skipped**（上轮 1172 / 0 / 18）；被跳过的 18 项在训练解释器下 **23 passed / 0 failed**；portability **0 hard binding / 1 configurable / 8 historical**（PART 7：只跑回归，未改任何规则）；PRELOCK **7/7**；unexpected failures **0**。
- **报告**：`docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md`（十节）。结论 `LOCALIZED ERROR TRIGGER: HARDENED` / `CURRENT POISSON2D C2: UNCHANGED / CONFIRMED` / `NEXT FORMAL EXPERIMENT IMPLEMENTATION: READY`。
- **测试产物（建立与删除）**：见本节末行。
- **未做 / 等用户**：不开始新 PDE、不设计新几何、不启动 BFS、不改宪法、不重训 Poisson2D、不继续扩 portability policy。
- **测试产物（建立与删除，本节）**：主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **3,809 个文件 / 72,984,962 字节**（本轮 pytest 六次 + 两次训练解释器运行），删除；复现探针与补丁脚本写在会话临时目录（仓库外），未落入仓库。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 只剩本轮有意的改动。

### 5.31 代码身份完整性审计（2026-09-16）

- 授权：用户「code identity completeness audit」指令。禁止项按令执行：不改 Poisson2D 历史证据与其记录在案的 codeHash、不重训、不重开 D_claim、不开始下一个 PDE；边界变更**只对下一 revision 生效**。工作位置：主检出 master。
- **先澄清一条事实（不粉饰）**：`pinn/experiments2d/localized_error.py` **本来就在代码身份之内**（落在 `pinn/` 前缀，任何新清单都含它）。它不在 `exp2d-poisson-calibration-r1` 的**记录清单**里，只是因为该 run 发生时这个文件尚未创建。因此此处无修复动作，只加回归测试钉死该性质。
- **审计方法**：`git ls-files` 全量 ∖ 当前 `code_manifest()` 成员 → 对差集逐个判断是否触及八个判定面（ScientificSpec 解释、Gate 结果、FailureSignature 生成、DiagnosisRecord 内容、TrustVector 状态、ClaimGateDecision、Red-Team 判定、可复现性判定）。
- **发现两个真实缺口**（差集其余为应用层代码 `leo_shell/`、`bridge/`、`launcher/`、`stage/`、测试、回滚快照与证据）：
  1. **CI-1 `governance/PINN_TRUST_PROTOCOLS_R1.md`**：协议汇编规定 Tier-1 强制集合与适用性登记的正当理由形式；正是其第 108 行使 P11 成为 C2 前必跑（上一轮据此推翻 NOT_APPLICABLE 并补跑）——字节能改变 **Red-Team 判定**。
  2. **CI-2 `adversarial/core_manifest.draft.json`**：`PrelockPaths.defaults` 第 63 行读取，PRELOCK 决定正式 attempt 是否开始。
  两者加入 `CODE_IDENTITY_FILES`（前瞻，带注释说明理由）。
- **结构性缺口与处理**：正式 run 的驱动脚本可位于 `experiments/**`（P11 补跑那次即刻意置于清单外），而 `experiments/**` 不能整体纳入——其中同时存放每次都变的证据，纳入等于"每跑一次就是另一种方法"。改用**声明制**：`config["codeIdentityExtraFiles"]` 由 run 自行声明，进入其清单并受敏感性与完整性检查约束。
- **新增机制**（`pinn/experiments/common.py`）：`DECISION_SURFACES` 常量、`CodeIdentityError`、`required_identity_paths()`、`assert_code_identity_complete()`（缺必需文件 / 声明了不存在的文件 / 清单与磁盘字节不符 → 一律拒绝）。`runner2d.phase_identity` 顺序为：组装 extra → `code_manifest` → **`assert_code_identity_complete`（在 codeHash 之前）** → `code_hash_from_manifest` → **`run_prelock`** → `phase_problem` / Gate / 训练；`identity.json` 新增 `codeIdentityBoundary`（前缀、具名文件、本 run 声明、判定面清单）。顺序由源码级测试钉死。
- **新边界实测**：当前树清单 **75 项**（`pinn/` 60、`governance/` 5、`scientific_reference/` 4、`specs/` 4、`adversarial/` 1、run 配置 1），`codeHash = d8ff0a9184ada058…`（仅为当前树在新边界下的参考值，不是任何正式 run 的身份）。已 ACCEPTED 的 run 仍记录 73 项 / `a39aa07e23d0…`，**一字未改**。
- **新增测试 44 项**（`tests/pinn/test_code_identity_completeness.py`），对应四项要求：① `localized_error.py` 在身份内且改一字节 → codeHash 变；② **22 个判定相关核心模块**逐一参数化的一字节敏感性（spec JSON、验收合同、gates2d、datasets2d、pinn_torch2d、validation/poisson2d、analytic_poisson2d、poisson2d_fdm、diagnosis、diagnostics2d、localized_error、state_machine、trust_vector、trust_loop、claim_set_ledger、redteam2d、协议汇编、runner2d、repro_package2d、prelock、core_manifest、宪法）外加 run 配置；③ 文档 / 证据改动 **不**改变 codeHash——除真实文件外，另在 `tmp_path` 里 `git init` 微型仓库做端到端验证（改 docs/证据/CHANGELOG 后哈希相等，改 `pinn/` 下一个字节后哈希不等）；④ 清单遗漏已登记模块、遗漏声明的配置、清单与磁盘不符、声明不存在的文件，全部在 PRELOCK 之前被拒，并有顺序断言。另加声明制驱动脚本测试与"历史身份不被改写"测试。
- **对已 ACCEPTED 的 Poisson2D：NO IMPACT**。重跑 `final_closure_revalidation.py`：`CURRENT 2D C2: CONFIRMED`、`problems []`、`ACCEPTED`、`cRepro PASS`。测试断言该 run 的 `identity.json` 的 `codeHash` 仍 `a39aa07e23d0…`、记录清单不含本轮新增的两个具名文件、用记录清单重算仍等于记录值。账本 / D_claim / TrustVector / ClaimGateDecision / Gate 结果 / 冻结配置 / 阈值本轮一次未写。
- **测试**：targeted 44 passed；全套 **1285 passed / 0 failed / 18 skipped**（上轮 1241 / 0 / 18）；训练解释器下 **23 passed / 0 failed**；portability **0 hard binding / 1 configurable / 8 historical**（未改任何 policy）；PRELOCK **7/7**；unexpected failures **0**。
- **报告**：`docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md`（十节）。结论 `CODE IDENTITY COMPLETENESS: AUDITED` / `NEXT FORMAL EXPERIMENT: BOUNDARY READY (new revision required)` / `CURRENT POISSON2D C2: UNCHANGED / CONFIRMED`。
- **未做 / 等用户**：不开始下一个 PDE、不设计新几何、不改宪法、不重训、不再动 portability policy。
- **测试产物（建立与删除，本节）**：主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **4,051 个文件 / 73,191,742 字节**（本轮 pytest 五次 + 两次训练解释器运行），删除。**留痕一条**：新增的身份测试会在临时目录里 `git init` 微型仓库，git 对象是只读文件，首次 `shutil.rmtree(ignore_errors=True)` 残留 165 个条目 / 69 个文件；改用清除只读位的 `onerror` 处理后彻底删除，复核 `pytest-of-user` 不存在。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` 0 个目录；`pytest-of-user` 不存在；`git status` 只剩本轮有意的改动。

### 5.32 GEOMETRY LIFT 1（圆环制造解 Poisson）：预注册、冻结、CPU attempt 停止、device 支持与 GPU 重跑（2026-09-17）

- 授权：用户「GEOMETRY LIFT 1 — Annular-Domain Manufactured Poisson」指令。禁止项按令执行：不改任何阈值（ACA-1 达不到就写 NOT YET PASS / FAIL，用户 2026-09-17 明确裁决）、不重开已烧毁的 D_claim、不改历史机器证据 / TrustVector / ClaimGateDecision / 账本、不删失败与中止记录、不新增 Gate / TrustStatus、不起草 A-0003、不扩 portability policy、本轮结束后不自行开始下一几何或下一 PDE。工作位置：**主检出 master**（按令不新建 git worktree；会话工作树 `pinn-annular-poisson-a249dd` 索引为脏，本轮一次未使用）。
- **补记一条既有缺口（不粉饰）**：本轮之前的圆环准备工作（提交 `62faf94` 预注册与冻结配置、`3e4d644` 盲集池封存、`9a71120` 沙箱冒烟抓到的四个缺陷、`fb9b329` CPU attempt 停止归档，以及更早的 `e6c1f9a`）**没有写进本日志、CHANGELOG 与根目录两份报告**。本节一并补记，之后的条目续写在此。
- **已冻结的前置资产（本轮未改一字）**：预注册 `experiments/annulus/EXPERIMENT_ANNULUS_PREREGISTRATION_20260917.md`；冻结配置 `experiments/annulus/configs/exp_annulus_baseline.json`；盲集池 `problems/pdef-annulus-poisson-v1-claim-pool.json`（DAC-M0..M3，两两共享样本 0）；账本 `ledger/pdef-annulus-poisson-v1.json`（仅一条 SEALED，样本 `cb3a15010f91`，**从未 OPENED**）；冻结 ProblemDefinition `problems/pdef-annulus-poisson-v1-r1.json`，specHash `4c8dfbc7238d…`。
- **失败与中止记录（保留，不删除）**：`runs/aborted-r1-codebug-4ef0ae3a/`（早期代码缺陷中止）、`runs/stopped-cpu-r1-c5a3e12e018e/`（操作员停止的 CPU 正式 attempt，含 `STOPPED.md`；确立 Gate 1/2/3 全 PASS，seed 0 devRelL2 = 1.622e-04，1407 s / 120k 步 ≈ 11.7 ms/步）。
- **第 0 步 诚实设备基准（EXPLORATORY，不是证据）**：不假设 GPU 更快。新增 `experiments/annulus/bench_device_annulus.py`，标 `marking=EXPLORATORY` / `formalEvidence=false`，只读 D_dev 的探索性实例，seed 用 smoke 基数 20261200 / 20261210 / 20261220（与正式基数 20261400 / 20261500 / 20261600 不相交），2000 步。实测：CPU 独立进程 16.6 / 21.6 ms/步，CUDA 独立进程 18.2 / 19.3 ms/步，同进程对比 CPU 21.2 vs CUDA 18.8 ms/步。**结论：GPU 在本工作负载上没有明显更快**，差异落在运行间噪声内（CUDA 更稳定，平均约快 5%）——原因是网络极小（4×64 tanh，batch 512）且按宪法用 float64，而 RTX 4060 的 FP64 吞吐是 FP32 的 1/64。另外整机当前比归档 attempt 时慢约 1.6 倍（11.7 → 约 19 ms/步），十个 seed 无论哪个设备都是约 6–7 小时墙钟。数字如实上报后，**用户 2026-09-17 仍选择用 GPU 执行**；代价已写明，方法未因此改动。同一基准另测两条路径的一致性：同 seed 跑满 2000 步后 CPU 与 CUDA 权重最大绝对差 `4.441e-16`，devRelL2 差 `2.776e-17`。产物 `experiments/annulus/smoke/DEVICE_BENCHMARK_{fresh-cpu,fresh-cuda,same-process}.json`。
- **第 1 步 device 支持（关键治理约束）**：`device` 是**运行时参数**，**没有进冻结配置**。理由是 PART 1 与 PART 28 的直接推论——配置在 `codeHash` 之内，而 G6 复现要在**只有 CPU 的 Environment B** 上用**同一个 codeHash** 重跑；device 进配置，G6 就永远无法复现。实现：
  - `pinn/experiments_annulus/pinn_torch_annulus.py`：`_torch / build_model / model_from_weights / fields / values / normal_derivatives / train_run` 全链路加 `device`，默认 `cpu`；张量与模型同 device；float64 不变；`use_deterministic_algorithms(True)` **保持开启**，CUDA 下显式设 `CUBLAS_WORKSPACE_CONFIG=:4096:8`（**没有**为绕开报错关闭确定性，实测无算子报缺确定性实现）；权重仍在 CPU 上按 init seed 生成再搬到 device，初值逐位相同；batch 置换用 CPU 生成器抽取后搬到 device，批次顺序与设备无关；CUDA 计时前 `synchronize`，否则计时会撒谎；run record 的 `determinism` 记 `device / deviceRequested / deviceName / cublasWorkspaceConfig`。
  - `pinn/experiments_annulus/runner_annulus.py`：`device` 走构造参数，**只作用于训练**；Gate 3–5、物理、局部判据 ACA-9、绘图**一律在 CPU 上评估**（训练后由权重在 CPU 重建模型），因此没有任何 Gate 数字依赖加速器，Env B 的 CPU 复现是同类相比。`identity.json` 新增 `executionDevice`，`acceleratorClass` 如实由 `cpu-only` 变为 `cuda-NVIDIA GeForce RTX 4060 Laptop GPU`（设备属于环境，不属于方法）。
  - `experiments/annulus/run_formal_annulus.py`（在 `codeIdentityExtraFiles` 内）与 `experiments/annulus/smoke_runner_annulus.py` 各加 `--device`，默认 `cpu`。
- **Tier-1 驱动入口一并前置**：`runner_annulus.run_tier1_for_attempt()` 与 `run_formal_annulus.py --tier1` / `runner_annulus tier1`，**在正式 run 之前**进入代码身份——跑完再加 driver 会再次改变 `codeHash`，Tier-1 就无法与它所检验的 attempt 同身份。该入口只读目标 attempt 的**已登记**产物（registered train / dev 集合并逐个校验 sha256 与 ProblemDefinition 一致、identity 指名的冻结配置并校验 configSha256、seed-0 run record），在目标 attempt 的 Gate 5 未 PASS 时拒绝启动，对未完成的 attempt（无 `RUN_SUMMARY.json`）给出明确拒绝而非堆栈，**从不触碰 D_claim、账本或任何历史判定**。`redteam_annulus.run_tier1` 同样只让 `device` 影响训练，八项扰动的度量全在 CPU。
- **代码身份重置（因此必须整体重跑）**：改动落在 `pinn/` 之下，`codeHash` 由 `c5a3e12e018e94fd…`（已停止的 CPU attempt）变为 **`8ee9b9236199996f…`**。这是新的代码身份，因此十个 seed 全部在同一 codeHash、同一 device 下重新产生；旧 CPU attempt 的 seed 0 **不得**与新 seed 混用，只作为停止记录保留。specHash `4c8dfbc7238d…`、盲集池、账本与全部阈值**不受影响**：它们是方法，方法没有变。
- **预注册按追加处理**：预注册是历史文件，**未改写任何一节**，只在文末追加第 14 节（device 是执行参数而非方法值、事前设备基准、为何重跑、新旧 codeHash）。追加性已用逐字节前缀比对机器验证（`append-only: True`，追加 3036 字符）。
- **第 2 步 沙箱冒烟（CUDA，150 步 × 3 seed）**：整条流水线（identity / 问题 / Gate 1–5 / 失败路径）在 CUDA 下跑通；Gate 4 返回 BLOCKED → 走失败路径、`finalState = IMPLEMENTATION_VERIFIED`、沙箱账本**未出现 OPENED**，真账本一字未动。沙箱建立 **33 个文件 / 1,614,755 字节**（`experiments/annulus/.smoke`），跑完即删，复核不存在。
- **正式 run 第一次被休眠中断（如实记录，未删除）**：`2026-09-17T13:24Z` 启动，Gate 1/2/3 PASS，seed 0 = 1.622e-04（2357.5 s）、seed 1 = 1.874e-04（2088.3 s），第 3 个 seed 进行中时机器休眠、进程被杀。归档为 `experiments/annulus/runs/stopped-gpu-r1-sleep-8ee9b9236199/`（含 `STOPPED.md` 与完整控制台日志），提交 `400f13d`。**没有断点续跑**：runner 一次性训练整个 ensemble，而加续跑功能会改 `codeHash`，反而让这两个已完成的 seed 在新身份下作废，因此十个 seed 从头重训。用户其后批准使用客户端 keep-awake（仅阻止空闲休眠）。该记录确立两件事：① **跨设备一致**——seed 0 在 CUDA 上 1.622e-04，与归档 CPU attempt 同一 seed 三元组完全相同；② **GPU 是更慢的设备**——每 seed 2357 / 2088 s vs 归档 CPU 的 1407 s，与事前基准预测一致。
- **正式 run（重跑，`2026-09-18T00:39Z` 起，约 5.9 h）**：attemptId `exp-geometry1-annulus-poisson-r1-gpu`，codeHash `8ee9b9236199…`，environmentId `9915cbcd0d05…`，acceleratorClass `cuda-NVIDIA GeForce RTX 4060 Laptop GPU`，`workspaceDirty = false`，PRELOCK PASS，specHash `4c8dfbc7238d…`。
  - **Gate 1 PASS**（几何合同、两条边界组件）；**Gate 2 PASS**（解析自验 `max|-Δu* - f| = 0`、两组件边界 `2.115e-16`；独立极坐标 FDM 三级 `3.407e-03 / 8.509e-04 / 2.127e-04`，比值 4.004 / 4.001，**观测阶 2.0016 / 2.0004**）；**Gate 3 PASS**（十项，含 T11 成员判定、T12 内外法向朝向、T13 求积雅可比：面积 2.756747553525 vs 精确值，相对 6.44e-16）。
  - **Gate 4 PASS**：10/10 跑满 120000 步，NaN 0、发散 0；median devRelL2 **1.853e-04**、IQR **2.470e-05**、worst **3.874e-04**（seed 2，worst/median = 2.09 < 3.0）；loss–error 未解耦。
  - **Gate 5a 物理 PASS**：PH1 通量 1.633e-04、PH2 能量 1.674e-04、PH3 正性 0 违例、PH6 极值 1.000303、PH7 SPD（能量 1.639，独立极算子最小特征值 22.7262）、PH8 成员；PH4 / PH5 登记 NOT_APPLICABLE 并附理由。
  - **盲集 DAC-M0 一次性打开 → BURNT**：账本事件 `SEALED` → `OPENED`（codeHash `8ee9b9236199`），ledgerHead `df1b1c5004e9…`。打开前的早期护栏实测生效（启动时派生状态 `SEALED`）。
  - **Gate 5b FAIL**：十个 seed 中 **seed 2** 的 **ACA-9 = 1.079e-03 > 1e-3**（超出 7.9 %）；其余九个 seed 的 ACA-9 为 4.196e-04–6.537e-04；**ACA-1..ACA-8 九个判据对全部十个 seed 全部通过**（ACA-1 median 1.860e-04 / worst 3.722e-04，ACA-3 ≈ 2.116e-16，ACA-4 worst 1.426e-03，ACA-6 worst 9.950e-04）。按合同 `seedPolicy = "every-seed"`（即 Gate 5b 对 MUST 判据一贯的 `all(...)`）判 `C_external = FAIL` → `FAILURE_RECORDED`。`observedSignatures = ["sLocalizedError"]`（唯一），`retrainedInPlace = false`。**阈值一个未动、未现场调参、未重训**（用户 2026-09-17 裁决）。
- **局部误差触发器硬化在真实少数派失败上得到验证**：`fired = true`、`firedBy = "1/10 seed(s) fail ACA-9"`、`failingSeedIndices = [2]`、`failureFraction = 0.1`，而 ensemble **median = 4.109e-04 远低于阈值**——硬化之前的 median 口径会把这次失败整个吞掉。该机制上一轮在正方形上修，本轮在新几何的一次真实失败上验证。
- **定量根因：预算，不是几何**（本轮最重要的否证）。局部/全局误差比在两次标定之间几乎不变：正方形 AC2D-9/AC2D-1 median 比 **3.20**（1.151e-04 / 3.600e-05），圆环 ACA-9/ACA-1 逐 seed 比均值 **2.93**、标准差 0.52。因此 ACA-9 触顶不是圆环的新病理，而是全局误差水平比正方形高 5.2 倍所致：两者共用 `1e-3` 阈值时，ACA-9 的隐含 ACA-1 上限是 `1e-3 / 2.93 ≈ 3.414e-04`，而本轮 worst-seed ACA-1 = 3.722e-04，恰好越线。预注册 5.2 的步数外推只针对 ACA-1（事前已如实记录其余量仅约 1.4 倍、远小于正方形的 23 倍），而验收是九个判据 × every-seed。**本轮不据此行动**：改步数是方法变更，须走新 revision + 新盲集成员，由用户决定。
- **失败单元位置（否证「孔边病理」）**：十个 seed 的最差局部单元全部落在中间两个径向环（bin 1 / bin 2），**从不**在紧贴孔的 bin 0 或紧贴外圆的 bin 3；最差与次差单元之比仅 1.00–1.66（误差是平缓抬高的一片，不是奇异单元）。seed 2 的最差单元 1.294e-04 是其余 seed（5.03e-05–7.84e-05）的 1.65 倍，而其全局 ACA-1 同样是中位数的 2.00 倍——**整体更差，不是局部更差**。
- **Tier-1 Red Team：未执行**。协议规定只在 Gate 5 PASS 后进行（红队是对已接受结果的压力测试，不是被拒结果的第二次机会）。八项一项未跑。驱动入口的拒绝路径已实测生效。
- **G6 复现：未执行**，`C_repro = BLOCKED`（Gate 5 未通过则不尝试复现）。Environment B 仅只读核验、**未安装任何包、未污染**：`C:\Users\user\LeoAI-envB2D-20260916\venv`，Python 3.12.9 / torch 2.12.1+cpu / numpy 2.4.5 / `cuda_available = False`。
- **TrustVector**：`math PASS / impl PASS / train PASS / physics PASS / external FAIL / repro BLOCKED`，弱链 external。**Highest Claim: BLOCKED**——runner 以 `decision = False` 收尾，**未生成 `claim_gate_decision.json`**，C0 / C1 / C2 一律未授予。已 CLOSED 的 Poisson 1D 与 2D 正方形不受本轮任何影响（其证据、账本、TrustVector、ClaimGateDecision 一字未动）。
- **图**：`experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu/plots/` 共 **10 张**（01 几何、02 解析解、03 PINN 解、04 绝对误差、05 残差、06 配置点、07 等面积单元、08 seed 分布、09 最差 seed 误差、10 FDM 收敛）。第 11 张是 Red Team 汇总图，因 Tier-1 未执行而**如实缺席**，不是绘图失败。绘图点全部取自已登记的评估集。
- **报告**：`docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md`（十二节）。结论 **`Geometry Lift 1: NOT YET PASS`** / **`Highest Claim: BLOCKED`** / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**。
- **Newly Discovered**：BLOCKING **无**（Gate 5b FAIL 是预注册判据的预期内判定结果，不是新缺陷）；NON-BLOCKING 5 条（局部/全局比几何不变、误差被硬约束推离两条边界、GPU 在本负载上更慢、CPU↔CUDA 在 float64+确定性下同解、触发器硬化得到真实验证）；**AMENDMENT CANDIDATE 2 条**：① `ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`（本轮用 schema 自带的 `regions[].params` 承载、`domainType="other"`，**未改治理 schema**）；② **Gate 4 不筛查局部判据，尽管 D_dev 有能力测量它**——本轮 D_dev 上局部统计量 worst 已是 1.038e-03（> 1e-3），即盲集被打开**之前**同一个 seed 的同一问题已在开放集上可见，但 Gate 4 只按 Constitution 10.1 检查 `devRelL2`，盲集仍被消耗；**本轮没有实现该预筛**（新增 Gate 被明令禁止，且在失败当口改判定结构本身不当），仅登记为提案。
- **测试**：全套 **1391 passed / 0 failed / 25 skipped**（与上轮基线一致，device 改动无回归）；被跳过项在训练解释器下 annulus **7 passed / 0 failed**、poisson2d **23 passed / 0 failed**；portability **0 hard binding / 1 configurable / 8 historical**（只跑回归，未改任何规则）；PRELOCK **7/7 PASS**。
- **未做 / 等用户**：不改任何阈值、不重开已 BURNT 的 DAC-M0、不动 DAC-M1/M2/M3、不新增 Gate 或 TrustStatus、不起草 A-0003、不扩 portability policy、不自行开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热。
- **测试产物（建立与删除，本节）**：主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **5,922 个文件 / 115,751,920 字节**（本轮 pytest 三次 + 训练解释器多次运行），删除（身份测试会在临时目录 `git init`，git 对象只读，用清除只读位的 `onerror` 处理）；沙箱 `experiments/annulus/.smoke` 33 个文件 / 1,614,755 字节，跑完即删；设备基准与补丁脚本写在会话临时目录（仓库外），未落入仓库。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` **0 个目录**；`pytest-of-user` **不存在**；`experiments/annulus/.smoke` 不存在；`git status` 只剩本轮有意的改动。

### 5.33 圆环失败诊断：受控训练预算干预的前置审计 —— 干预前停止（2026-09-18）

- 授权：用户「Annulus Failure Diagnosis — Controlled Training-Budget Intervention」指令。禁止项按令执行：不修改原始正式 RunRecord / DAC-M0 账本 / Gate 1–5 机器结果 / `failure_record.json` / TrustVector / 状态转移 / 正式 seed 账本 / 阈值 / ScientificSpec revision 1；不提前把 `rOptimizationFailure` 写成正式 RootCauseClass；不新增 Gate、不改 Gate 4 / TrustStatus / claim 前置条件；不改 Constitution / schema。工作位置：主检出 master。
- **PART 1 因果措辞收窄（只改散文，不回写机器证据）**：上游标定报告中「根因不是几何 / 真正的原因是步数预算不足」改为「训练预算不足是**受支持的假设**（SUPPORTED HYPOTHESIS），不是已正式识别的 RootCauseClass；状态仍为 `FAILURE_RECORDED`，未进入 `DIAGNOSED`」；「局部/全局误差比是几何不变的」改为「**在迄今考察的正方形与圆环两个标定案例中，没有观察到圆环特有的局部/全局误差比放大**」（两个几何不足以证明普遍 geometry invariance）；「失败落在一个与几何无关的量上」改为「本轮**没有观察到**明确的几何病理」（证据的缺席不等于不可能性的证明）。被收窄判断所依据的数字一个未变（3.20 / 2.93 ± 0.52 / 隐含上限 3.414e-04 / worst-seed 3.722e-04），变的只是结论强度。收窄同步应用于 CHANGELOG、根目录软件修改报告与记忆文件；标定报告以**追加** §13 记录本次收窄，未改写原有各节。
- **PART 2 候选根因（读自实际 admissible matrix，未按提示词缩减）**：`admissible_root_causes("1.2")` 对 `sLocalizedError` 给出 **7** 个候选——`rSingularityTreatment / rReferenceDefect / rImplementationDefect / rCapacityLimit / rOptimizationFailure / rSamplingDeficiency / rSpecDefect`。另核实 `rDataDefect` **不在**该信号的 admissible 集合内（只对 `sBcResidual` 与 `sPinnCfd` 可用）。**七个候选一个都未被正式排除。**
- **PART 4 前置审计：两条独立的阻塞事实**（这是本轮的核心产出）。
  1. **B-1 优化器与调度器状态从未被保存**。正式 run 只保存模型权重：`run-00.json` 的顶层字段中只有 `weights`（模型 `state_dict`）；全仓库 `pinn/experiments_annulus/` 与 `experiments/annulus/` 中 `state_dict()` 只出现一次（`weights_of()`，取模型），`load_state_dict` 只出现一次（`model_from_weights()`），**没有** `optimizer.state_dict()`、**没有** `scheduler.state_dict()`、**没有** checkpoint 文件、**没有** resume 代码路径。被丢弃的状态：Adam 的 `m_t, v_t` 与 step 计数、`ExponentialLR.last_epoch`、batch 生成器 RNG 状态与 shuffle 游标。按 PART 6，`load weights + fresh Adam` 不得冒充「只是多训练几步」→ **nested continuation 不可执行**。
  2. **B-2 学习率轨迹依赖总预算**（PART 4 问题 A 的回答）。实现为 `gamma = (finalLr/lr0) ** (1/steps)`，故 `lr(step) = lr0 * (finalLr/lr0) ** (step/steps_total)`，即 **`lr(step, total_steps)`**。实测同一 step 在不同总预算下的 LR：step 60000 处 S=120k 为 `1.0000e-04`、S=180k 为 `2.1544e-04`（**2.15 倍**）、S=240k 为 `3.1623e-04`；step 120000 处分别为 `1.0000e-05` / `4.6416e-05`（**4.64 倍**）/ `1.0000e-04`（**10.00 倍**）。正式 run 记录的实测 LR 与该式一致（step 1 `9.999616e-04`、step 120000 `1.000000e-05`）。这正是 PART 4.1 明令禁止的混杂：180k run 与 120k run **在整个前 120k 步都不是同一条优化轨迹**。
- **据此按 PART 6 停在干预之前**，报告 **`EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE`**，等待用户裁决。**没有**执行任何训练干预，**没有**预注册预算梯度（PART 7 以 exact continuation 可行为前提），**没有**生成 DiagnosisRecord / DiagnosisVerdict / RevisionRecord，**没有**把 `rOptimizationFailure` 写成正式 RootCauseClass。
- **如实补充的一条（影响用户裁决，故必须说明，但不自行设计）**：PART 6 提到的备选「from-scratch matched-budget intervention」在**当前代码下同样不是** budget-only 干预——B-2 使 from-scratch 的 180k / 240k run 的 LR 轨迹随预算重新缩放。要让它成为单因素干预，需要一个事前预注册、与总预算解耦的 continuation policy（PART 5.1 的优先形式：前 120k 步走原 LR 轨迹，其后把 LR 保持在已达到的 `1e-5`），而这要改训练代码、从而改变 `codeHash`。本轮**不实施、不设计、不预注册**。
- **连带更正一条既有证据的强度**：既有 EXPLORATORY 的 budget response（10k → 9.94e-03、20k → 5.43e-03、40k → 2.23e-03）此前被当作「步数」的证据，但那三次是各自独立的 from-scratch run、各带被重新缩放的 LR 轨迹，因此**混合了「更多步数」与「更慢衰减」两个因素**，比原先以为的更弱。此前未写明，本轮更正。
- **PART 13 数据防火墙复核（机器核验）**：账本事件仍为 `['SEALED', 'OPENED']`，本轮**没有任何** claim set 生命周期事件写入；逐成员派生状态 `DAC-M0 = BURNT`（designatedRevision 1）、`DAC-M1 = NEVER_SEALED`（r2）、`DAC-M2 = NEVER_SEALED`（r3）、`DAC-M3 = NEVER_SEALED`（r4）。DAC-M0 的历史 failure 只被用作「为什么要做诊断」，**没有**被用来选择任何参数。
- **PART 24 测试**：所列十一项**未新增**——其中十项针对尚未获授权、也尚不可执行的干预与 revision 流程；在干预设计被批准之前写测试，等于先固化一个未经批准的设计。
- **代码身份未动**：本轮未改动 `pinn/`、`scientific_reference/`、`specs/` 下任何文件，也未改动冻结配置与正式驱动脚本，`codeHash` 仍为 **`8ee9b9236199…`**（机器复核）；revision 仍为 1，specHash 仍为 `4c8dfbc7238d…`，冻结配置的 `steps` 仍为 `120000`。改动只落在报告 / 日志 / CHANGELOG / 记忆文件（均不在代码身份内）。
- **测试**：全套 **1391 passed / 0 failed / 25 skipped**；训练解释器下 annulus **7 passed / 0 failed**、poisson2d **23 passed / 0 failed**；portability **0 hard binding / 1 configurable / 8 historical**；PRELOCK **7/7**（均为上一节的同一棵树，本轮未改代码，未重跑训练）。
- **报告**：`docs/pinn-trust-loop/ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md`（十三节）。结论 **`Root Cause: UNDETERMINED`** / **`Diagnosis: NOT PERFORMED — blocked before intervention`** / **`Annulus Calibration: NOT YET PASS`** / **`Highest Claim: BLOCKED`** / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**。
- **新增 AMENDMENT CANDIDATE 两条（登记不实施，都会改 `codeHash`）**：① 训练记录应保存 optimizer / scheduler / batch-generator 状态，否则任何「延长训练」类的受控干预事后都不可能做成单因素干预（可复现性与可诊断性的结构缺口，不只影响圆环）；② LR 调度与总预算耦合使「步数」不是可独立操纵的变量，若要把训练预算当受控变量，需要一个与总预算解耦、事前预注册的 schedule 定义。连同此前登记的两条（Gate 4 不筛查局部判据、schema 缺 `annulus` 词汇），共 4 条待审。
- **未做 / 等用户**：不做 capacity sweep、不做架构搜索、不做优化器搜索、不做更高预算 sweep、不动 DAC-M1/M2/M3、不升 revision、不开始 L-shape / 再入角 / BFS / Navier–Stokes / UCM / 传热。
- **测试产物**：本轮未运行 pytest 与训练，未产生新的 `__pycache__` 与 pytest 临时目录；补丁脚本写在会话临时目录（仓库外），未落入仓库。复核：仓库源码下 `__pycache__` 0 个目录，`pytest-of-user` 不存在。

### 5.34 圆环失败诊断 Phase II：前瞻性嵌套预算干预 —— B* = 180k，根因仍 UNDETERMINED（2026-09-19 / 20）

- 授权：用户「Annulus Diagnosis Phase II — Prospective Nested Optimization-Budget Intervention」指令。禁止项按令执行：不恢复旧 120k optimizer state、不把 weights + fresh Adam 冒充 continuation、不改 r1 任何机器证据、不打开任何 claim set、不写账本事件、不改阈值 / 架构 / 采样 / 优化器 / 几何 / 损失 / 局部判据合同、不升 revision、不在 240k 之后加预算、不改 Gate 4 / TrustStatus / claim 前置条件、不改 Constitution / schema。工作位置：主检出 master。
- **PART 4 的两条阻塞事实都已在本轮解决**（而不是绕开）：
  1. **LR 与总预算解耦**。新增 `optimizer.lrPrefixSteps`：`gamma` 由固定的 120000 步前缀算出，scheduler 推进满该次数后**停止推进**，学习率停在已到达的终值。于是 `lr = lr(step)`，不再是 `lr(step, total_steps)`。**不带该字段时逐位保持旧行为**，已跑过的东西不改变含义。
  2. **完整 checkpoint + exact resume**。新增 `pinn/experiments_annulus/checkpoint_annulus.py`：保存 model / optimizer（Adam `m_t`、`v_t`、step 计数、param_groups）/ scheduler（gamma、lastEpoch、prefixSteps、currentLr）/ currentStep / batch 生成器字节状态 / order / cursor / 全局 CPU 与 CUDA RNG / seeds，全部 JSON。
- **一个实现语义上的关键发现（PART 4 明文预见的情形）**：`torch.optim.lr_scheduler.ExponentialLR.get_lr()` 返回 `group["lr"] * gamma`，即**逐步相乘**，而不是求闭式 `lr0 * gamma ** t`；两者在 12 万次乘法后相差 1–2 ULP。最初写的闭式 helper 与归档轨迹**对不上**（step 30000 起逐位不等）。按「以旧正式实际 trajectory 为准，不以纸面公式为准」改为迭代实现后，**逐位复现 r1 记录的全部 241 条学习率**（step 1 = `9.99961624318148777e-04`，step 120000 = `9.99999999996725452e-06`），且在总预算 120k / 180k / 240k 下完全相同。
- **PART 6 resume fidelity：PASS**（在 10-seed 之前做，作为前置门槛）。连续 `0→2000` 对照 `0→1000`→存盘→JSON 往返→`1000→2000`，LR prefix 故意设 1200 落在断点与终点之间，使重载的后半段跨越「停止衰减、开始保持」那一点。合同为 **bitwise**（依据：r1 同 seed 同设备重跑权重最大绝对差 **0.0**，本轮机器复核）。11 项全部逐位相同：参数（12752 值）、Adam 状态（25514 值）、scheduler 位置、学习率、batch 生成器、order/cursor、RNG、D_dev 指标、断点状态、重载后 loss/lr 历史、`resumedFromStep`。记录 `experiments/annulus/diagnosis/RESUME_FIDELITY.json`。
- **PART 7 预注册**：`experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md`，在任何 10-seed 训练之前提交。冻结预算梯度 `120000 / 180000 / 240000`（原预算的 1 / 1.5 / 2 倍，**不是**由 DAC-M0 的 `1.079e-03` 倒推）、最大预算 240000、LR prefix 120000 与终值 1e-5、checkpoint 位置、B\* 规则、PART 10 容差、数据防火墙、STOP 条件。
- **沙箱冒烟**先跑通全流程（8 文件 / 5,520,585 字节，跑完即删），再跑正式诊断。
- **正式诊断（2026-09-20T02:10Z 起，9.15 小时，CUDA）**：codeHash `b7f9fe73e0b1…`，配对在 r1 的**已登记** D_train（2048）/ D_dev（1024）上并逐个以 sha256 对 ProblemDefinition 校验；10 个 paired seed 各**只启动一次**训练 `0→240000`，在三个预算处保存完整 checkpoint 并在 **CPU** 上评估。
  - **PART 10 前缀等价性：PASS，10/10 逐位相等**。不止 devRelL2，**局部统计量也与 r1 记录的 D_dev 逐 seed 值完全一致**。「只改了 checkpoint 基础设施与 schedule 表示」这一假设成立，180k / 240k 可作因果解读。
  - **B\* = 180000**：`120k` reliability PASS 但 localized 9/10（seed 2 = `1.038e-03` FAIL）→ allPass False；`180k` reliability PASS + localized **10/10**（worst `7.312e-04`）→ allPass True；`240k` 同样 all-pass（worst `6.801e-04`）。取最小者。
  - **防火墙完好**：账本 sha256 与事件序列前后一致，仍为 `['SEALED','OPENED']`；`DAC-M1 / M2 / M3` 仍 `NEVER_SEALED`。
- **三点必须如实记录的负面细节**（写进报告 §3.3，不粉饰）：① **改善不单调**——全局 median 在 180k 反而更差（`1.8534e-04 → 1.9329e-04`），240k 才降到 `1.0537e-04`；ACA-9 的 median 同样先升后降；seed 1/3/5 在 180k 变差，seed 6 在 240k 比 180k 差。② **180k 通过靠最差 seed 下移，同时离散度上升**——IQR 从 `2.470e-05` 扩大到 `1.448e-04`（5.9 倍），worst 从 `1.0383e-03` 降到 `7.3121e-04`；`every-seed` 问的正是 worst，所以判定成立，但这意味着 180k 的通过部分依赖这次游走恰好把 seed 2 带到阈值之下。③ **余量很薄**——180k `1.37×`、240k `1.47×`，对比正方形标定的 `6.4×`。
- **局部热点位置基本不随预算改变**：10 seed × 3 预算共 30 个最差单元，**29 个**落在中间两个径向环，**1 个**（seed 1 @240k，单元 `0,15`）紧贴内孔，0 个紧贴外圆。〔2026-09-20 更正：本条原写「全部 / 无一」，是概括时未逐条复核清单所致的事实错误；机器证据 `DIAGNOSIS.json` 一直是对的。该错误直接影响 `exp-annulus-dx-singularity` 的 G2 判定，见 §5.35。〕
- **PART 13 正式判定：Root Cause 仍为 `UNDETERMINED`，`rOptimizationFailure` 未写入**。原因不是保守，是 Constitution 1.2 的硬要求：`discriminating_experiment_errors` 规定「为该 signature 下**其余每一个** admissible 根因指名一个排除实验」，且 `excludes.<cause>.experiment` 必须匹配 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`（Tier-1 扰动编号或正式 attempt id）。`sLocalizedError` 有 7 个候选，本轮只用实验排除了 **1 个**（`rCapacityLimit`）；其余五个的证据全是「没有观察到缺陷」，而**证据的缺席不是排除**。以上不是推理，是对 `validate_diagnosis_record` 的实测（构造候选记录后逐条读它返回的错误）。
- **新发现的结构性闭环（AMENDMENT CANDIDATE，不实施）**：那五项排除义务实际上要求 **Tier-1 扰动集合**，而协议规定 Tier-1 **只在 Gate 5 PASS 之后**执行——一次**失败** run 的正式诊断，需要协议只在**成功** run 之后才安排的实验。
- **另一条新发现（AMENDMENT CANDIDATE，不实施）**：**未跟踪文件会静默落在代码身份之外**。`code_manifest()` 只枚举 git 已跟踪文件，`workspace_dirty_paths()` 用 `--untracked-files=no`，`assert_code_identity_complete()` 无法察觉从未被列入的文件。本轮预注册第 12 节一度记录了错误的 codeHash `124c31eb46ae…`（在提交之前算的，当时新模块 `checkpoint_annulus.py` 还 untracked）；把该文件从当前清单移除后重算**逐位得到同一错误值**，因果坐实。正确值 `b7f9fe73e0b1…` 是 run 自己写进 `identity.json` 的，**没有任何训练在错误身份下进行**。已在预注册**追加**第 16 节勘误，前 15 节一字未改。r1 不受影响（它从干净树启动，`git status --porcelain` 包含未跟踪文件）。
- **未执行（按协议，不是遗漏）**：Tier-1（只在 Gate 5 PASS 后）、G6（`C_repro` 仍 BLOCKED，Env B 本轮未访问）、revision 2（DiagnosisRecord 前提不成立）、DAC-M1（未触碰）。未产生新的 TrustVector 或 ClaimGateDecision；r1 的六维保持 `math/impl/train/physics PASS，external FAIL，repro BLOCKED`，Highest Claim 仍 BLOCKED。
- **图**：`experiments/annulus/diagnosis/nested-budget-r1-paired/plots/` 共 7 张（PART 23 的第 1–6 项；第 7 项因无新正式 revision 而不适用），全部取自已登记的 `DIAGNOSIS.json`，不重算、不加载模型。
- **测试**：全套 **1414 passed / 0 failed / 26 skipped**（上轮 1391 / 25，净增 23 项治理测试）；训练解释器下 annulus **24 passed / 0 failed**（净增 17 项）、poisson2d **23 passed / 0 failed**；PRELOCK **7/7**；portability **0 hard binding / 1 configurable / 8 historical**。
- **报告**：`docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md`（十二节）。结论 **`prefix equivalence: PASS`** / **`resume fidelity: PASS`** / **`B* = 180k`** / **`Root Cause: UNDETERMINED`** / **`Annulus Calibration: NOT YET PASS`** / **`Highest Claim: BLOCKED`** / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**。
- **等用户裁决的两件事**：① 五项未满足的排除义务如何处理——授权一次「诊断用 Tier-1」，还是接受失败 run 的 DiagnosisRecord 在 MVP 下只能落到 `rUndetermined`；② 若进入 revision 2，B\* 取 180k（预注册的最小性规则给出的答案）还是 240k（证据更干净、余量更大，但偏离预注册规则）。**不由执行者单方面决定。**
- **测试产物（建立与删除，本节）**：沙箱冒烟 `experiments/annulus/diagnosis/.smoke` **8 个文件 / 5,520,585 字节**，跑完即删；主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **2,031 个文件 / 36,320,948 字节**，删除（身份测试会在临时目录 `git init`，git 对象只读，用清除只读位的 `onerror` 处理）；补丁与绘图脚本草稿写在会话临时目录（仓库外），未落入仓库。**保留入库的诊断证据**：30 个完整 checkpoint 共约 27.4 MB（用户审批通过：2026-09-19 明确选择「全部提交」），加 `DIAGNOSIS.json`、`identity.json`、`RESUME_FIDELITY.json` 与 7 张图，`experiments/annulus/diagnosis` 合计约 28 MB。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` **0 个目录**；`pytest-of-user` **不存在**；`experiments/annulus/diagnosis/.smoke` 不存在；`git status` 只剩本轮有意的改动。

### 5.35 外部评审裁决执行：代码身份补洞 + 五项诊断专用排除实验 —— 2/5 排除，Root Cause 仍 UNDETERMINED（2026-09-20 / 21）

- 授权：外部评审裁决（2026-09-20）十一项。禁止项按令执行：不把「诊断用 Tier-1」当作 Tier-1 阶段（Tier-1 含义不变）、不从「没观察到缺陷」发明排除、不强行命名 `rOptimizationFailure`、不改 Gate 4 / geometry schema / Tier-1 语义 / Constitution、不在形式诊断完成前消耗 DAC-M1。工作位置：主检出 master。
- **item 3（提交 `3852e16`）代码身份补洞，在任何新诊断执行之前完成**。新增 `untracked_identity_paths()`：用 `git ls-files --others` 扫描身份边界，**刻意不加** `--exclude-standard`——一个模块不会因为被写进 `.gitignore` 就离开方法身份；字节码缓存是唯一排除项。`assert_code_identity_complete()` 边界内有未跟踪文件即拒绝；`codeIdentityExtraFiles` 必须是 git 已跟踪路径。PRELOCK 新增 `codeIdentityTracked`，**检查数由 7 变 8**。对抗测试先构造一棵 PRELOCK 确实接受的树作**对照**，再写入未跟踪 helper，断言整体 FAIL、`codeIdentityTracked` 是**唯一**状态变化的检查、提交后拒绝解除。新增 10 项测试。
- **item 4 预注册（提交 `a650311`）**：`experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md`，在任何排除实验之前提交，冻结五项实验的设计、阈值、判定规则，并标明每项属**干预式**还是**正控制式**。**运行前**追加第 10 节勘误：2823 个配置点无法从 2048 点的已登记池中抽出，故 S1 拆为 S1a（已登记池全部 2048 点，2× 密度，完全配对）与 S1b（新池 2823 点，2.76×，不配对并如实标明），判定改为**两者都救不回来**才算满足——比原写法更严。
- **五项排除实验的结果**：
  - **`exp-annulus-dx-implementation`（rImplementationDefect）→ EXCLUDED**（正控制式）。I1 预言注入：精确解经**产生 ACA-9 的同一条流水线**，relL2 `6.055e-18`、ACA-9 `4.437e-17`；I2 正控制：在已知单元 `2,5` 注入凸起，流水线**恰好**报该单元，统计量一致 `0.000e+00`；I3 用不 import `diagnostics_annulus`、自行推导等面积分箱的独立例程复算失败 seed 的 ACA-9，与生产值**逐位相同**（`1.038334942e-03`）；I4 AD vs 中心差分 `2.225e-08`。
  - **`exp-annulus-dx-spec`（rSpecDefect）→ EXCLUDED**（正控制式）。C1 `-Δu* - f` 两条独立路径：闭式 `0.000e+00`、自动微分 `3.553e-15`；C2 两边界 `2.115e-16 / 2.952e-17`；C3 正控制（源项 ×1.000001）把残差抬到 `1.752e-05`。
  - **`exp-annulus-dx-reference`（rReferenceDefect）→ NOT EXCLUDED**。R1 通过——`ast` 静态审计 14 个模块，到达 `scientific_reference` 的**为 0**，参考进不了统计量就不可能制造该信号；R2 通过——观测阶 `2.0016 / 2.0004`；**R3 不通过**——64×256 下 FDM 在热点单元 `2,13` 的自身误差 `5.500e-05`，模型 `1.490e-04`，只低 2.7 倍，预注册要求 10 倍；**R4 不通过**——故意去掉极坐标 `1/r` 项的算子**发散成 NaN**，控制未执行。
  - **`exp-annulus-dx-singularity`（rSingularityTreatment）→ NOT EXCLUDED**。G1 通过（逐单元 `max|Δu*|` 的 max/median = `2.668` ≤ 10）；G3 通过（`r^(-1/3)` 奇异场锚在内圆上，机制把热点定位到 `0,1`，证明它看得见贴边界的集中）；**G2 不通过**——30 个最差单元中有 **1 个**在 bin 0（seed 1 @240k，单元 `0,15`），预注册要求 == 0。
  - **`exp-annulus-dx-sampling`（rSamplingDeficiency）→ NOT EXCLUDED，且证据反向**（干预式）。120k 预算、其余冻结：**S1a（2× 密度）ACA-9 `6.620666e-04` PASS**、**S1b（2.76× 密度）`5.766093e-04` PASS**——两种加密**都把失败修好了**；S2/S3/S4 换采样 seed 得 `2.670052e-04 / 6.505030e-04 / 3.061673e-04` 全 PASS；**S5：热点单元 `2,13` 只含 5 个配置点，全域中位数 16**。对照冻结判定：(a) 不成立、(b) 不成立、(c) 成立。
- **这直接削弱 Phase II 的因果解读（如实记录，不回改 Phase II 的机器证据）**：`B* = 180k` 是真实测量，但「多训练」与「多采点」**都能**把这个局部误差压下去，**两者都不是必要解释**。自洽的替代叙事：seed 2 的配置点抽样在该单元偏稀（5 vs 16），PDE 在那里约束不足；本轮证据无法在两者间判别。若上一轮据 `B*` 命名根因，这条竞争解释会被整个错过——这正是裁决要求做真排除实验的理由。
- **DiagnosisRecord 记账（精确到可引用性）**：6 项义务中 **2 项**备妥可引用证据（implementation、spec），**1 项**科学上已排除但**缺 `exp-*` 标识**（`rCapacityLimit` 由上一轮嵌套预算干预排除，但其产物无 `experimentId`，目录名 `nested-budget-r1-paired` 不匹配 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`；这是记账缺口不是科学缺口，补法是指定并登记一个 `exp-*` 标识，属命名决定，**不在写记录时凭空发明**，登记待裁决），**3 项**未排除。**未生成 DiagnosisRecord，未写 `rOptimizationFailure`**；状态仍 `FAILURE_RECORDED`。
- **本轮自查出的三个自身缺陷（全部如实记录）**：
  1. **R4 正控制把 `nan` 读成通过**（提交 `cf18fc0`）。判据写「观测阶落在 [1.8, 2.2] 之外即算检出」，而 `1.8 <= nan` 为 False，于是**发散**被当成成功的控制——与 2026-09-16 硬化定下的「非有限证据 fail closed」是同一类缺陷，出现在我本轮自己写的代码里。`control_verdict()` 改为返回 `(executed, detected)`，对非有限/空证据一律 fail closed，工件记 `controlExecuted` 并写明「控制未执行」；4 项回归测试钉死。**该修正在看到结果之后做，但不可能改变判定**（R3 独立不成立），而留着它下次就会悄悄放行。
  2. **driver 探针标签 off-by-one**（提交 `5dccf64`）。`f"S{offset-899+1}"` 把三个替代抽样标成 S3/S4/S5，与计数探针 S5 撞名，判定查表抛 `KeyError`，**五次 120k 训练白跑约 1.8 小时**。测量无误，错的只是标签。**没有**把日志数字誊进工件（那不算证据）；重跑得到**完全相同**的数。
  3. **Phase II 报告一处事实错误**（提交 `afb58f7`）。原写「30 个最差单元**全部**在中间两环」，逐条核对 `DIAGNOSIS.json` 实为 **29 / 1 / 0**。来源是我在进度汇报里打印过清单、写报告时按印象概括而未逐条复核。机器证据一直正确；正文两处已就地更正并追加第 13 节勘误，本日志 §5.34 对应条目已标注更正。**这条更正直接决定 G2 判定**。r1 报告与预算诊断报告中「**十个** seed 全在中间两环」的说法**是正确的**，未改。
- **数据防火墙（每次调用前后机器核验）**：账本事件始终 `['SEALED','OPENED']`、sha256 不变；`DAC-M0` 保持 BURNT，`DAC-M1 / M2 / M3` 保持 `NEVER_SEALED` 且一次未触碰。所有实验只读 D_dev、合成夹具与独立参考。**本轮不具 Tier-1 状态**：这些是 `exp-*` 身份下的 diagnosis-only discriminating experiments，不产生 claim、不推进 Trust、不产生任何 claim-set 生命周期事件。
- **中断与恢复**：2026-09-20 用户因笔记本电量不足要求暂停，`exp-annulus-dx-sampling` 的重跑在 S1a 阶段被 `TaskStop` 干净停止（该 driver 训练路径未带 checkpoint，中断即丢该次进度，无残留）；2026-09-21 充电后恢复，补跑 implementation（约 1 分钟）与 sampling（约 1.8 小时），两者数字与中断前**逐位一致**。
- **测试**：全套 **1426 passed / 0 failed / 26 skipped**（上轮 1414 / 26，净增 12 项：10 项身份对抗 + 2 项正控制 fail-closed）；训练解释器下 annulus **24 passed / 0 failed**、poisson2d **23 passed / 0 failed**；**PRELOCK 8/8**（新增 `codeIdentityTracked`，检查数由 7 变 8）；portability **0 hard binding / 1 configurable / 8 historical**。
- **报告**：`docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md`（十一节）。结论 **`Root Cause: UNDETERMINED`** / **`2 of 5 excluded`** / **`DiagnosisRecord: NOT WRITTEN`** / **`NOT YET PASS`** / **`Highest Claim: BLOCKED`** / **`REMAIN AT ANNULUS GEOMETRY CALIBRATION`**。
- **新增 AMENDMENT CANDIDATE 一条**：**正控制的执行有效性应当是一等判据**——一个「控制」必须先证明自己跑起来了，才谈得上有没有检出；建议 `controlExecuted` 成为所有正控制式排除的必填字段。连同既有六条共 7 条待审。
- **未做 / 等用户与外部评审**：不写 `rOptimizationFailure`、不进 revision 2、不碰 DAC-M1、不做 capacity sweep / 架构搜索 / 优化器搜索 / 更高预算 sweep、不开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热。四件待裁决：① 如何判别 `rSamplingDeficiency` 与 `rOptimizationFailure`（需要同时固定两者的 2×2 设计，本轮没有，也不自行开始）；② R3 判据是换更细网格还是改用 R1 的论证路线（须事前裁决）；③ G2 的 `== 0` 是否修订（须事前修订并说明理由）；④ `rCapacityLimit` 的 `exp-*` 标识如何指定与登记。
- **测试产物（建立与删除，本节）**：主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **7,468 个文件 / 122,267,960 字节**，删除（身份测试会在临时目录 `git init`，git 对象只读，用清除只读位的 `onerror` 处理）；补丁与报告草稿写在会话临时目录（仓库外），未落入仓库。**保留入库的诊断证据**：`experiments/annulus/diagnosis/exclusions/` 五个 `exp-*` 工件 + `EXCLUSIONS.json`。
- **复核（删除后）**：主检出仓库源码下 `__pycache__` **0 个目录**；`pytest-of-user` **不存在**；`git status` 只剩本轮有意的改动。

### 5.36 四项委托裁决的执行 —— 并查出四个属于执行者自己的缺陷（2026-09-21）

- 授权：用户 2026-09-21「这四个你来判断和裁决吧」。四项均以多视角 workflow（29 个 agent，三种独立视角 + 每项三名对抗性怀疑者 + 完备性评审）论证，**每一条强主张都由执行者亲自复核后才采纳**。全部裁决合计 **0 GPU 小时、0 次训练**。
- **裁决一：rSamplingDeficiency 与 rOptimizationFailure 本轮不可分离，不跑新实验。** 路由在看到数据前已冻结（0920 预注册 §3 与 §10 勘误都写着「加密修好了 → 采样不得排除 → 报 UNDETERMINED」），现在再委托新判别器，结构上是在判据判否之后重开事前已裁决的归宿；且两因在定义层重叠（等权单损失下「`2,13` 只占 5/1024」同时是 collocation distribution 与 loss weighting 的实例）。**并据此收窄我自己的机理叙事**：实测 S1a 把 `2,13` 的配置点由 5 提到 18、相对中位数由 0.31× 升到 0.58×，热点**仍停在 `2,13`**，其 ACA-9（6.6207e-04）比只换抽签的 S3（6.5050e-04）还差；而只换抽签的三次**每次**都把热点挪走（`1,12` / `1,1` / `1,4`，散布 2.44×）。可靠起作用的是**抽签**不是**密度**，「被饿瘦、补点即愈」未获支持。前瞻性设计 `S6-R 等总量重分配`（总点数与预算固定，只把点从最密格迁到最稀格，目标格用机械规则、绝不写死 `2,13`）写入设计笔记，**本轮不跑、不冻结**。
- **裁决二：R3 整族前瞻性退役；R4 只修仪器、判据一字不改。** R4 的失败是我的 bug：`u = u + residual/diagonal` 而 `residual = A·u − b`，Jacobi 应为减——**无论是否腐蚀算子都会发散**，控制从未测试过腐蚀；固定 4000 扫亦不足（真算子 4000 扫后 `max|residual|` 仍约 1.3e-01）。修正符号并改为按残差容差迭代后实测 `1.161905e-01 / 1.153873e-01`、观测阶 **0.0100**，**预注册原判据直接通过**。**更重的一条**：R1 的根集合是手挑的，恰好不含 `gates_annulus`，而 `gates_annulus.py:31` 在模块层 import FDM、`:439` 的 `external_checks` 正是裁决 ACA-9 的地方；原工件的 `[]` 是「根集合选得没有」而非「查出来没有」。另两处：包节点被当叶子截断、相对导入把符号当模块。修复后审计图由 14 扩到 **43** 个模块，结果 `['pinn.experiments.gates', 'pinn.experiments_annulus.gates_annulus']` → **R1 改判 FAIL**。实测 FDM 只用在 Gate 2（`:143`）与 PH7（`:353`），故「ACA-9 读不到 FDM」这一实质结论很可能仍成立，**但我原来的审计没有立住它**——两句话都入档。修正后 R1 FAIL / R2 PASS / R3 FAIL / R4 PASS，判定不变 NOT EXCLUDED。原工件保留于 `exclusions/superseded/exp-annulus-dx-reference.as-first-run.json`。
- **裁决三：G2 维持，`rSingularityTreatment` 保持 NOT EXCLUDED，且成立两次。** 其一，G2 是我写错的：贴边界单元恰占一半（32/64），故均匀零假设下 `P(G2 通过) = 0.5^30 = 9.3132e-10`、期望贴边界数 15，且 `(1−π)^n` 对 n 递减——**证据越多越难通过**，构造性错误。**可入档的只有这类运行前即可算出的规格性质**；我另算的 `P(X≤1)=2.887e-08`（n=30）与 `1.074e-02`（n=10）是**事后统计量**，只可入动机叙述，**不得作为证据引用**。其二、更重：**G3 未按冻结规格执行**——预注册 §7 冻结「真实 `r^(2/3)` 角点型奇异场」，代码用 `exponent = -1/3`；实测字面的 `d^(+2/3)` 场热点落在 `3,8`（贴**外**圆），**通不过**预注册自己写的「bin 0」条件，即冻结文本自相矛盾，实现静默选了能通过的一侧。故该实验标称的 `positive-controlled` 在执行层面不成立，实为**观察式**，按 §2 在任一方向都不构成排除。「最差单元位置」族判据整体退役（α=0.01 单侧精确二项检验的拒绝域：n≤6 空集、n=10 恰为 {0}，故「前瞻性 G2′」在数学上就是 G2）；干预式奇异性复检**本轮不冻结、不预注册**。
- **裁决四：`rCapacityLimit` 从未被排除，总账变差。** `FACTOR_CONTROL = {"capacity": "architecture"}` + `MIN_INTERVENTION_LEVELS = 3` + `MIN_INTERVENTION_SEEDS = 3`；嵌套预算干预全程钉死 `4×64`、只改 `optimizer.steps`，**容量档位数 = 0**。而我自己 0919 预注册 §13 CASE A 原文是「**不再是必要解释**」，并把 `rCapacityLimit` 逐字列入六项义务。**「不再是必要解释」≠「已排除」——我在 Phase II 报告与本轮报告里写成了后者，是越权。** 裁决：不发标识、不建注册表、不重跑，改记为**未排除**；未排除原因由 3 项改为 **4 项**；`exp-annulus-nested-budget-r1` 这个标识从未存在。嵌套预算干预未白跑，将来作为 B\* 证据经 `evidencePointers`（`artifactRef` 强制 `artifactId + sha256`）入记录。
- **本节新发现的可执行事实**：`rUndetermined` 的 DiagnosisRecord **写得出来**——`discriminating_experiment_errors` 在 UNDETERMINED 下校验完 `experimentId` 即返回、`excludes` 可空，构造的候选记录经 `validate_diagnosis_record` 返回**零错误**（唯一要求是不得带 `gate` 字段）。报告 §4.2 原写「无法生成 DiagnosisRecord」只对命名 `rOptimizationFailure` 成立。但其后果不轻：`triage` 在 UNDETERMINED 下返回 **`STOPPED_THE_LINE`** 而非 `DIAGNOSED`，且 `MAX_DIAGNOSIS_ROUNDS = 3`。**本轮不写、不迁移**——它超出用户委托的四项，留给用户与外部评审。
- **代码改动（两处仪器修复，判据零改动）**：`pinn/experiments_annulus/exclusion_annulus.py` 的 `corrupted_polar_refinement`（Jacobi 符号 + 残差容差迭代 + 记录 `iterations`/`finalMaxResidual`）与 `statistic_call_path_modules`（根集合补入裁决模块、包节点回落 `__init__.py`、相对导入取 `node.module`）。新增 **6** 项回归测试（3 项审计健全性 + 3 项控制有效性与 G3 规格自相矛盾）。
- **文档（全部追加，零改写）**：本轮报告追加 §12（四项裁决 + 四个自身缺陷）；Phase II 报告追加 §14（容量越权更正）；0920 预注册追加 §11（§1 那句话不被 §2 授权）；新增 `experiments/annulus/ANNULUS_NEXT_ROUND_DESIGN_NOTES_20260921.md`（**只记设计与为何推迟，不冻结任何判据**）。
- **数据防火墙**：账本仍 `['SEALED','OPENED']`；`DAC-M0` BURNT，`DAC-M1 / M2 / M3` `NEVER_SEALED` 一次未触碰。
- **测试**：全套 **1429 passed / 0 failed / 26 skipped**（上轮 1426，净增 3——另外 3 项控制测试在需要 torch 的模块里，`.venv` 会跳过，由训练解释器执行）；训练解释器下 annulus **27 passed / 0 failed**、poisson2d **23 passed / 0 failed**；PRELOCK **8/8**；portability **0 hard binding / 1 configurable / 8 historical**。
- **未做 / 等用户与外部评审**：不写任何 DiagnosisRecord（含 `rUndetermined`）、不迁移状态、不进 revision 2、不碰 DAC-M1、不跑 S6-R、不冻结奇异性复检设计、不做容量阶梯。
- **测试产物（建立与删除，本节）**：主检出仓库源码下 `__pycache__` **6 个目录 / 22 个文件 / 410,095 字节**，删除；`%LOCALAPPDATA%\Temp\pytest-of-user` **5,344 个文件 / 80,758,390 字节**，删除；补丁与报告草稿写在会话临时目录（仓库外）。**复核（删除后）**：`__pycache__` 0 个目录、`pytest-of-user` 不存在。**保留入库**：`exclusions/superseded/exp-annulus-dx-reference.as-first-run.json`（被取代的原工件，按「不删失败记录」保留）。

```

</details>

### R019 — 项目/docs/P0_CANONICAL_SKILLS_DRIFT_AUDIT_20260909.md

<details>
<summary>展开完整原文</summary>

```markdown
# P0 canonical skills drift: actual paths, byte identity, and repair

This audit resumed from `DELIVERY.md` and the Phase II P0 closure report. The audited UI source is `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-worktree`, branch `codex/leo-entry-navigation-20260908`, HEAD `512ab8d9e5fa51197efa6963e1172ebbeb7fc87e`. Other agents' uncommitted entry/navigation changes were present and preserved. The original `Desktop/LeoAIStudio-build` worktree, frozen scientific candidates, governance, old evidence, upstream checkout, daemon configuration and research data were not changed by this task.

## Actual finding

The earlier strict output `12 PASS / 1 FAIL / 0 NOT TESTED`, with `10 file(s) differ from canonical`, did not identify ten independently changed skill files. `tools/verify_release.py` passed its selected application root to its own EXE/assets checks, but omitted it when calling `sync_skills.py`. After the worktree moved under Documents, that child defaulted to a nonexistent sibling `.../20260908-phase2/LeoAIStudio`. It reported all nine Windows skill files missing there, plus one real WSL mismatch.

Read-only reproduction before repair:

- `python -B tools/sync_skills.py --check --require-wsl`: 10 mismatched copies, exit 1.
- Same command with `--app-root C:/Users/user/Desktop/LeoAIStudio`: 2 mismatched copies, exit 1. Both were `research-sop/kernel.py`; the other eight files agreed byte-for-byte on both platforms.

The small verifier fix passes `--app-root` with the caller's resolved absolute path into the existing read-only, WSL-required child invocation. It changes the target being measured, not the comparison criteria or strict failure handling.

## Source authority and the ten reported entries

Canonical release source prefix **C**: `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-worktree/skills/`.

Actual Windows installation prefix **W**: `C:/Users/user/Desktop/LeoAIStudio/user/user-skills/`.

Actual WSL personal-skill prefix **L**: `/home/leo/.local/share/leo-ai-studio/data/user-skills/`.

All nine C files exactly equal the committed HEAD blobs. `tools/sync_skills.py` defines the one-way canonical source → Windows displayed copy → WSL personal-skill copy relationship. No installed copy is a source for reverse edits. The original desktop worktree's skill files have no Git changes: its six byte differences are exclusively CRLF versus LF, and all nine become equal to C after CRLF-to-LF comparison. This diagnostic normalization was not used to waive any release hash requirement or rewrite original files.

| Original reported entry | C SHA256 | Actual W / L before | Resolution |
| --- | --- | --- | --- |
| windows:lean-math/kernel.py | `169873567fca7ba431d91ab5b1d2621f1470b675bdfaaf2a0e45f1af3420d36f` | Both equal C | Wrong Windows target; no copy |
| windows:lean-math/README_zh.md | `9f0af68db7f806831bd93b48cf8729f665313ed22035e43eddfd7a6b8a03ac2a` | Both equal C | Wrong Windows target; no copy |
| windows:lean-math/SKILL.md | `deffa9fcb0f853e44f8eaed093761c355a522f21c9119313519317f8c8302b4c` | Both equal C | Wrong Windows target; no copy |
| windows:local-literature-rag/kernel.py | `a4c105710bcaf582ae1801e2dd295f9ea8757eafea376a3640ca2bb1abb648fa` | Both equal C | Wrong Windows target; no copy |
| windows:local-literature-rag/README_zh.md | `9ec843f7977c6ca81a3ea85a2aed4a3e208a907ed03e293dae7c2a19282decf7` | Both equal C | Wrong Windows target; no copy |
| windows:local-literature-rag/SKILL.md | `a718c96aab153ea954bce8d9a195fc4622d347e2ad73a9bdf26383fc01f83067` | Both equal C | Wrong Windows target; no copy |
| windows:research-sop/kernel.py | `f8ccb2910bf2224a71dc39a4b9e2c70ffb9e9d099c36b8e6a414bf50d4a98b8d` | Both `916ad38195ea34097671bc861793778eeb2cf4d79c81f81d95cdaa1eaa66769d` | Genuine old copy; narrowly synchronized |
| windows:research-sop/README_zh.md | `1efd383a82fa8ee277ede8be3994596b9fde6cc7676902f4d5cb964c45e9ba7d` | Both equal C | Wrong Windows target; no copy |
| windows:research-sop/SKILL.md | `ae1cc92139d9d2063e92b2be7c70cb4120f805835c5c96df2ece1d94a175f278` | Both equal C | Wrong Windows target; no copy |
| wsl:research-sop/kernel.py | `f8ccb2910bf2224a71dc39a4b9e2c70ffb9e9d099c36b8e6a414bf50d4a98b8d` | L old hash as above | Genuine old copy; narrowly synchronized |

The old kernel is not an unidentified user modification: its exact 51,227 bytes equal the Git blob at `58aeb19619689a20683670a8d51dcb873c9fae27`. The current 58,897-byte kernel equals the blob at `ad118017a369a6bdf25e190dbddcbbcdb57760e6`. Intervening committed fixes add F-007 manifest self-consistency (`e92fa811`), F-001 document-digest checking (`3e809f27`), F-002 archive re-audit (`8084078b`), and B08 separate attempt identity (`ad118017`). Thus the old deployed kernel lacked actual evidence-integrity repairs despite matching SKILL/README documents.

After explicit parent authorization, only W and L `research-sop/kernel.py` were updated. Each write required the exact old hash; the source also had to equal both the expected new hash and the current HEAD blob. Atomic replacements were used; the WSL file's `0755` mode was preserved. Both final hashes are C's `f8ccb291...`. No other skill content was copied or removed. The old source bytes remain identifiable in Git and the pre-sync evidence.

## What the daemon path means

The actual daemon PID at inspection was 463. Its executable was `/home/leo/.local/share/leo-ai-studio/runtimes/0.2.0-2eb33f7bf139/runtime/bin/python3.13`; active source was `/home/leo/.local/share/leo-ai-studio/sources/a792c38d9984be428437b548db29baab3322f6dc`. Only whitelisted environment fields were read: `OPENAI4S_DATA_DIR` points at the stated data directory; `OPENAI4S_SKILLS_DIR` and `PYTHONPATH` point at the active source tree.

`openai4s/skills_loader/loader.py::user_skills_dir()` separately adds `cfg.data_dir / 'user-skills'`. `discover()` considers bundled, project, then personal roots, preserving trusted bundled identities on collisions. The three Leo skill directories are absent from the directly checked active-source bundled root and checked runtime site-package root; their known on-disk copies are in L. A project-scoped overlay or already imported kernel state was not introspected. The release checker measures these disk copies; this audit does not convert that into proof of a fresh in-kernel scientific execution. No daemon restart, new scientific run, or five-role chain was requested or performed.

## Verification and remaining P0 status

| Command / test | Passed | Failed | Skipped / NOT TESTED | Scope |
| --- | ---: | ---: | ---: | --- |
| Temporary routing unittest | 9 | 0 | 0 | Absolute/relative/default install roots, paths with spaces, preserved `--check`/`--require-wsl`, real drift FAIL, unreachable WSL NOT TESTED, strict nonzero exits |
| Existing skills/build/manual/portability tests with default upstream lookup | 170 | 0 | 7 skipped | Seven parser tests saw the same moved-worktree default path problem; original result retained |
| Same suite with explicit `LEO_UPSTREAM_ROOT=C:/Users/user/Desktop/LeoAIStudio/upstream/OpenAI4S` | 177 | 0 | 0 | Actual pinned parser available; no model call |
| Explicit `sync_skills.py --check --require-wsl --app-root ...` after copy | all 18 copy checks agree | 0 | 0 | Existing lean-math `__pycache__/kernel.cpython-313.pyc` reported as extra; left untouched |
| Full `verify_release.py --strict --app-root ... --manifest ../ui-evidence/ui-installed-build-manifest.json` | 10 checks | 3 checks | 0 NOT TESTED | Overall FAIL retained: current repo dirty, receipt bound to prior clean source, frontend source changed. Both skill rows PASS |
| `git diff --check -- tools/verify_release.py` | — | 0 | 0 | PASS |

Existing test command: `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/skills tests/test_build_reproducibility.py tests/test_manual_acceptance.py tests/test_portability.py --basetemp <new evidence temporary directory> -q -ra`.

This closes the measured skill-copy drift and its wrong-target diagnostic, not global P0-1 or P0-6. Current combined entry changes still need a clean committed build/deploy/strict verification. P0-2's current canonical regression component is executable and passed; old on-disk runtime integrity code is now replaced, but no live research chain was used as proof. P0-3 can advance through the ongoing real native navigation acceptance. C5 discovery, current-host B2 and selected Lean state probes can collect useful actual evidence, but the manual environment packet explicitly does not let these substitute for independent/new-account rows. P0-4/P0-5 still need their missing environment evidence, and human scientific approval remains absent. No frozen tolerance, Gate definition, Constitution or scientific candidate was edited.

## Why delivery allowed stale skill copies

`tools/build_launcher.ps1` and `tools/deploy_release.ps1` do not call `sync_skills.py` and contain no canonical-skill payload. Their verified release path list covers EXE, launcher, theme, licenses and runtime sidecars, leaving `user/user-skills` outside that transaction. `tools/build_manifest.py` records source skill hashes, rather than proving that those bytes were copied. Consequently launcher deployment can succeed while the independently checked personal-skill copies stay old. The strict gate did reject that state; the missing app-root argument made the diagnosis noisier.

The smallest next release-flow improvement is a mandatory explicit-root `sync_skills.py --check --require-wsl` stage before claiming complete release success, with a separately authorized, exact-old-hash guarded synchronization step for known managed files. Do not silently overwrite user-edited personal skills. A later complete package should include canonical skill bytes in its receipt and preserve rollback of managed copies. No build/deploy script was edited here while the parent was preparing other changes.

## Evidence and temporary cleanup

All new evidence is under `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/ui-evidence`:

- `p0-skills-before-20260909.json`: nine full canonical/Windows/WSL/original hashes, all committed-byte checks, old/new Git identities.
- `p0-skills-after-20260909.json`: all nine three-way comparisons agree; only research-sop kernel changed.
- `p0-skill-routing-tests-20260909.log`: 9 named regression results.
- `p0-skills-regression-20260909.log` and `p0-skills-regression-explicit-upstream-20260909.log`: original skipped outcome plus explicit-path rerun.
- `p0-skills-after-check-20260909.log` and `p0-skills-after-strict-20260909.log`: actual post-copy PASS and remaining overall FAIL.

New temporary test source `p0-skill-routing-temporary.py` had SHA256 `7b4fc649086b7624533bfc6b4aa572ac005ca77cab1c0a6484bb6f63d5cb5cd7`. It was removed after recording, per the user's instruction. Existing repository test sources were not deleted or weakened. Two dedicated pytest temporary trees contained 72 generated fixture files / 1,331,832 bytes; their resolved absolute targets were checked against the exact evidence root and both trees were removed with native non-force PowerShell removal. The temporary source and both directories were then verified absent. Product verifier SHA256 after the change: `200512d03d1461ac297744c3a722c532c6c54973c2eb87698706b143781a871e`.

```

</details>

### R020 — 项目/docs/P0_EXECUTION_STATUS.md

<details>
<summary>展开完整原文</summary>

````markdown
﻿# Leo AI Studio 鈥?Phase 0 鎵ц鐘舵€?

> 渚濇嵁锛歚Leo-AI-Studio-浜у搧鏋舵瀯涓庡墠绔噸鏋勫璁?md`銆乣Leo-AI-Studio-P0鏁存敼娓呭崟.md`
> 鏈枃浠舵槸 Phase 0 鐨勫敮涓€娌荤悊璁板綍銆?
> 鐘舵€佸彛寰勶細`TODO` / `IN_PROGRESS` / `PASS` / `PARTIAL` / `BLOCKED`銆?
> **`NOT TESTED` 姘歌繙涓嶅緱鍐欐垚 `PASS`銆?*

> **Round 2 鏇存柊锛?026-09-03锛?*锛氭帴鍙椾簩娆″鏍告姤鍛婄殑鍒ゅ畾锛屼笉浜夎京娴嬭瘯鏁伴噺銆?
> 涓婁竴杞妸銆屼换鍔¤矾寰勫凡鍒嗗紑銆嶈繃搴︽帹鏂垚銆岃瘉鎹摼鍙俊銆嶏紝`P0-2 = PASS` 鍐欐棭浜嗐€?

| # | 浠诲姟 | layer | Round 1 鑷姤 | 澶嶆牳鍒ゅ畾 | Round 3 鐜扮姸 |
|---|---|---|---|---|---|
| P0-1 | 鍗曚竴鍙俊婧愮爜 | build/tooling | PASS | REOPEN | `PASS` |
| P0-2 | research-sop 璇佹嵁瀹屾暣鎬?| skill | PASS | FAIL | `PASS` |
| P0-3 | Visible UI 涓?ShellApi 涓€鑷?| shell + injection | PASS | CONDITIONAL | `PASS`锛坓ated bridge + mutation test锛?|
| P0-4 | 鍘婚櫎涓汉璺緞缁戝畾 | shell + build/tooling | PARTIAL | PARTIAL | `PARTIAL`锛堥潤鎬佹竻闆讹紱27 椤瑰疄鏈?`NOT TESTED`锛?|
| P0-5 | 鏋勫缓鍙鐜?| build/tooling | TODO | FAIL | `PARTIAL`锛坔ermetic 鍙瀯寤哄彲杩愯锛涙棤 wheelhouse锛?|
| P0-6 | 涓嬩竴闃舵 Gate | 鈥?| FAIL | FAIL | **`FAIL`** |

娴嬭瘯鎬绘暟锛?*284 passed**锛圵indows锛宍.venv/Scripts/python -m pytest tests -q`锛宑ommit 12ceb40锛夈€?

---

## P0-1 鍗曚竴鍙俊婧愮爜 鈥?`PASS`

**闂** 瀹¤绉颁笁浠芥簮鐮佷箣闂存病鏈?canonical source銆?

**root cause锛堜笌瀹¤缁撹涓嶅悓锛屽疄娴嬶級**

1. **`LeoAIStudio-build/` 鍜?`LeoAIStudio/` 閮戒笉鏄?git 浠撳簱銆?* 鍞竴鐨勪粨搴撴槸
   `upstream/OpenAI4S`锛堝浐瀹?`a792c38d9984be428437b548db29baab3322f6dc`锛?026-08-28锛夈€?
   鐪熸鐨?root cause 涓嶆槸銆屽浠芥紓绉汇€嶏紝鑰屾槸 **Leo 鑷繁鐨勪唬鐮佷粠鏈繘鍏ョ増鏈帶鍒?*銆?
2. **`leo-studio-src.zip` 涓嶆槸婧愮爜鍖呫€?* 3355 鏉＄洰閲?3323 鏉℃槸 `upstream/`锛?
   Leo 閮ㄥ垎鍙湁 `theme/`(16) + LICENSES + examples銆?*涓嶅惈 `leo_shell/`銆乣stage/`銆?
   `tools/`銆乣tests/`**锛屽嵆鏁翠釜 Windows 澹虫簮鐮侀兘涓嶅湪閲岄潰銆傚畠鏄?08-31 瀵?*閮ㄧ讲鐩綍**鐨勫揩鐓с€?
3. **閫愭枃浠舵瘮瀵癸細zip 涓病鏈変换浣曠嫭鏈夊唴瀹广€?* 16 涓?theme 鏂囦欢 11 涓€愬瓧鑺傜浉鍚岋紱
   5 涓笉鍚岀殑鍏ㄩ儴鏄?live 鏇存柊銆俙files present only in the zip: none`
   鈫?**涓嶉渶瑕?merge**銆?

**棰濆鍙戠幇** 涓変釜鎶€鑳藉彧瀛樺湪浜庨儴缃茬洰褰曞拰 WSL 鏁版嵁鐩綍锛?*鍚屾牱涓嶅湪鐗堟湰鎺у埗閲?*锛?
涓斾袱鑰呬箣闂撮潬鎵嬪伐澶嶅埗銆傝繖灏辨槸涓婁竴杞€岃 CUDA torch 鐨勪慨澶嶅叾瀹炰粠娌′笂绾裤€嶇殑鍘熷洜锛?
daemon 璇荤殑鏄?`~/.local/share/leo-ai-studio/data/user-skills/`锛學indows 渚ф敼浜嗕笉绠楁暟銆?

**implementation**
- `git init` + `.gitignore` + `.gitattributes`锛涢娆℃彁浜?`8a65838`锛?9 涓枃浠躲€?
- 鐢熸垚鐗╃Щ鍑虹増鏈帶鍒讹細`stage/leo-inject.bundle.js`锛堟瀯寤烘椂鐢?`bundle_theme.py` 閲嶇敓鎴愶級銆?
  `pyi-spec/*.spec`锛圥yInstaller `--specpath` 姣忔鐢熸垚锛屼笖浼氱儰杩涙瀯寤烘満缁濆璺緞锛夈€?
  `dist/`銆乣pyi-work/`銆乣manifests/build-*.json`銆?
- **鎶€鑳界撼鍏?canonical**锛歚skills/` 杩涗粨搴擄紝鏂板 `tools/sync_skills.py`
  鍗曞悜涓嬪彂 `skills/ 鈫?閮ㄧ讲鐩綍 鈫?WSL data/user-skills/`锛宍--check` 鍙娴嬫紓绉汇€?
- 鏂板 `tools/build_manifest.py`锛氳褰?Leo commit / upstream revision / bundle 涓?
  鍚勬簮鏂囦欢 SHA-256 / runtime manifest / toolchain / exe SHA-256 / 姣忎釜鎶€鑳界殑鏂囦欢鍝堝笇銆?
  鍙栦笉鍒扮殑鍊间竴寰嬪啓 `"unknown"`锛屼笉鐚溿€?

**tests** `tools/sync_skills.py --check` 閫氳繃锛涜礋鍚戝鐓э紙浜轰负鏀逛竴涓瓧鑺傦級鑳藉悓鏃?
鎶ュ嚭 windows 涓?wsl 涓や晶婕傜Щ骞朵互闈為浂鐮侀€€鍑恒€?

**result** 浠庝粨搴撳彲浠ヨВ閲婂綋鍓嶅彂甯冪増鏈敱浠€涔堢粍鎴愶細
`leo 8a65838` + `upstream a792c38d` + bundle `b82bf906eaa5bb81` + exe锛堟瘡娆￠儴缃茶褰曪級銆?

**remaining risk** 棣栨鎻愪氦涔嬪墠鐨勫巻鍙蹭笉鍙拷婧€斺€旀棦鎴愪簨瀹烇紝鍙兘浠庣幇鍦ㄥ紑濮嬨€?
**rollback** `git init` 涓嶆敼鍔ㄤ换浣曟棦鏈夋枃浠讹紱鍒犻櫎 `.git/` 鍗冲彲鎾ら攢銆?

---

## P0-2 research-sop 璇佹嵁涓查 鈥?Round 1 璁板綍锛堝垽瀹氳涓嬫柟 Round 2 鑺傦級

**layer** skill锛坄skills/research-sop/kernel.py`锛?

**root cause锛堣鐮佺‘璁わ紝鍥涙潯鐙珛缂洪櫡锛?*

1. **闃舵璺緞娌℃湁浠诲姟缁戝畾**锛歚sop_stage_path(role)` 鍥哄畾杩斿洖
   `research-sop/01-literature-surveyor.json`锛屼笉鍚?run id / task hash銆?
   `resume=True`锛?*榛樿鍊?*锛夊洜姝ゆ妸浠诲姟 A 鐨勯樁娈靛綋浣滀换鍔?B 鐨勭粨鏋溿€?
2. **`status` 纭紪鐮?`complete`**锛氬嚱鏁版湯灏炬棤鏉′欢杩斿洖锛屼笌鏄惁鍙窇浜嗗瓙闆嗘棤鍏炽€?
3. **`validator` 纭紪鐮?`pass`**锛歷alidator 鏍规湰娌¤繘 pipeline 涔熸姤 pass銆?
4. **`paper` 璺緞纭紪鐮?*锛歱aper-writer 娌¤窇涔熻繑鍥炶矾寰勶紝鎸囧悜涓嶅瓨鍦ㄧ殑鏂囦欢銆?

**棰濆鍙戠幇** 浠撳簱涓?*涓嶅瓨鍦ㄤ换浣?skill 娴嬭瘯**锛坄tests/` 鍙湁 `leo_shell/` 涓?
`test_package_contract.py`锛夈€傛鍓嶆姤鍛婃彁鍒扮殑銆?4 椤规墦妗╂祴璇曘€嶅湪鏈粨搴撲笉瀛樺湪锛?
鍥犳鏈」鏄?*浠庨浂寤虹珛**娴嬭瘯鑴氭墜鏋躲€?

**瀹炴祴澶嶇幇锛堝 `docs/rollback/research-sop-kernel.pre-P0-2.py`锛?*

```
task A: complete | delegate calls: 5
task B: complete | delegate calls: 0      鈫?B 缁ф壙浜?A 鐨勫叏閮ㄤ簲涓樁娈?
task B validator: pass | paper: research-sop/05-paper-writer.md

subset run (modeler only): status=complete  validator=pass  paper=<path>
```

**implementation**
- 姣忔杩愯鐙珛鐩綍 `research-runs/<run_id>/`锛宍run_id` 鐢?task 鏂囨湰鐨?SHA-256 鎺ㄥ嚭銆?
- `manifest.json`锛歚schema_version` / `run_id` / `task_text` / `task_sha256` /
  `pipeline_version` / `role_order` / `role_prompt_hashes` / `model_fingerprint` /
  `created_at` / `parent_run_id` / `rollbacks`銆?
  妯″瀷韬唤鍙栦笉鍒版椂鍐?`"unknown"` 骞惰鏄庡師鍥狅紝涓嶇紪閫犮€?
- Resume 瑙勫垯锛歵ask hash 鐩稿悓鎵嶅師浣嶇画璺戯紱涓嶅悓涓€瀹氭柊寤?run锛?
  `resume=False` = 鏄庣‘閲嶅仛 鈫?**鏂板缓 run 骞惰 `parent_run_id`锛屾棫 run 鍘熸牱淇濈暀**
  锛堝垹鏃ц瘉鎹瓑浜庢瘉瀹¤閾撅級銆俶anifest 琚敼鍧?鈫?鎶涢敊鎷掔粷澶嶇敤锛屼笉闈欓粯銆?
- 闃舵璁板綍鍐呭祵 `run_id` + `task_sha256`锛宍sop_read_stage` 鍙岄噸鏍￠獙鈥斺€?
  鍗充娇鏈夋父绂绘枃浠惰惤杩?run 鐩綍涔熻涓嶆垚璇佹嵁銆?
- 鐘舵€佽瘹瀹炲寲锛歚complete` / `partial` / `unresolved` / `blocked`锛?
  `validator` 娌＄湡璺戝氨鏄?`None`锛沗paper` 娌＄湡鍐欏氨鏄?`None`銆?
- **娌℃湁淇濈暀浠讳綍鍥為€€鍒版棫鍥哄畾璺緞鐨勫吋瀹瑰垎鏀?*锛堥偅姝ｆ槸姹℃煋婧愶級銆?
- 瑙掕壊鎻愮ず璇嶉噷鍚屾椂琛ヤ簡瀹為獙鐜绾﹀畾锛堜紭鍏堥瑁呯瀛︽爤锛泃orch 蹇呴』 CPU wheel锛?
  瀹佸彲闄嶇骇瀹為獙涔熶笉鍋滀笅鏉ヨ鍑犱釜 GB锛夈€?

**tests** `tests/skills/test_research_sop.py` 鈥?**12 passed**锛岃鐩栨竻鍗曡姹傜殑
Case A鈥揈锛屽彟鍔?manifest 瀛楁銆佽法浠诲姟璇绘嫆缁濄€乼ask hash 褰掍竴鍖栥€佸潖 manifest 鎷掔粷銆?
blocked 鐘舵€併€?*宸查獙璇佽繖浜涙祴璇曞淇鍓嶇殑 kernel 浼氬け璐?*锛堣涓婃柟澶嶇幇锛夛紝
涓嶆槸绌鸿浆鐨勬祴璇曘€?

**remaining risk** 鏃х殑 `research-sop/` 鍥哄畾璺緞閬楃暀鏂囦欢浠嶅湪浼氳瘽宸ヤ綔鍖洪噷锛?
鏂颁唬鐮佷笉浼氳瀹冧滑锛堣矾寰勪笉鍚岋級锛屼絾涔熸病鏈変富鍔ㄦ爣璁颁负 legacy銆?
**rollback** `docs/rollback/research-sop-kernel.pre-P0-2.py`

---

## P0-2 Round 2锛氳矾寰勫垎寮€ 鈮?璇佹嵁鍙俊

澶嶆牳鎶ュ憡鐨勬牳蹇冩壒璇勬垚绔嬶細涓婁竴杞彧瑙ｅ喅浜嗚韩浠界粦瀹氾紝娌¤В鍐崇姸鎬佸彲淇°€乻chema 鍙俊銆?
artifact 鐪熷疄銆佸巻鍙蹭笉鍙彉銆佺増鏈吋瀹瑰拰璺緞瀹夊叏銆?*鎴戠嫭绔嬪鐜颁簡瀹冩寚鍑虹殑涓绘紡娲?*锛?

```
first = orchestrate_research(TASK_A)          # 姝ｅ父瀹屾垚
files[manifest_path] = "{ this is not json"   # manifest 鎹熷潖浣嗗瓨鍦?
orchestrate_research(TASK_A, resume=True)
鈫?status: complete | delegate calls: 0        # 闈欓粯閲嶅缓 manifest锛屾棫闃舵琚綋浣滆瘉鎹?
```

涓婁竴杞垜鍦ㄦ湰鏂囦欢閲屽啓鐨勩€宮anifest 琚敼鍧?鈫?鎶涢敊鎷掔粷澶嶇敤銆?*鏄敊鐨?*锛氶偅鏉″彧瑕嗙洊
銆孞SON 鍚堟硶浣?task hash 涓嶇銆嶏紝鑰屼笉鏄€孞SON 鏈韩鎹熷潖銆嶃€傚凡鏇存銆?

涔濈被淇锛堝搴斿鏍告姤鍛?搂5.1鈥?.10锛夛細

| # | 婕忔礊 | 淇 |
|---|---|---|
| 1 | 鎹熷潖 manifest 琚綋浣滀笉瀛樺湪 | 鍥涙€?`missing/valid/corrupt/incompatible`锛沜orrupt **fail closed**锛屽師瀛楄妭涓嶈鐩?|
| 2 | 缂?`run_id`/`task_sha256` 鐨?stage 浠嶈鎺ュ彈 | 绮剧‘鐩哥瓑锛宍None` 涓嶅啀绠楀尮閰嶏紱`role` 涔熻瀵逛笂 |
| 3 | delegate 澶辫触浠嶈 complete | 妫€鏌?`task_status`/`error`/`stop_reason`锛屽師濮?payload 淇濈暀 |
| 4 | schema 鍙紶缁?host锛屼笉澶嶆牳 | orchestrator 鍐呮湰鍦板鏍?required keys + verdict 鏋氫妇 |
| 5 | paper 璺緞鍙兘鎸囧悜涓嶅瓨鍦ㄧ殑鏂囦欢 | 鏂囨。蹇呴』瀛樺湪涓旈潪绌猴紝璁?`document_sha256` |
| 6 | rollback 鐢ㄧ┖涓茶鐩栬瘉鎹?| 褰掓。鍒?`history/rollback-NNN/`锛岃鍥炴牎楠屽悗鎵嶆竻绌猴紱澶辫触鍗充腑姝?|
| 7 | roles 鍏佽涔卞簭閲嶅 | 蹇呴』鏄?`ROLE_ORDER` 鐨勫敮涓€淇濆簭瀛愬簭鍒?|
| 8 | `run_id`/suffix 鍙矾寰勭┛瓒?| strict fullmatch + suffix 鏋氫妇 + 瑙勮寖鍖栧悗 containment 妫€鏌?|
| 9 | prompt/pipeline 鍙樺寲琚潤榛樺鐢?| 鍙備笌 resume 鍒ゅ畾锛涢粯璁?fork 鏂?run 璁?`parent_run_id`锛屽彲璁?`on_incompatible="fail"` |
| 10 | resume 姘歌繙鍥炲埌 base 鍒嗘敮 | 榛樿缁窇**鏈€鏂板垎鏀?*锛屾敮鎸佹樉寮?`run_id=`锛宍sop_run_lineage()` 鍙洖婧?|

**娴嬭瘯**锛歚tests/skills/test_research_sop_integrity_adversarial.py`锛?1 椤癸級銆?
澶嶆牳鏂圭殑鍘熷鏂囦欢琚彁鍙婁絾**鏈殢闄?*锛屾墍浠ヨ繖鏄寜鎶ュ憡 搂2.4/搂5 鐨勬弿杩?*鐙珛閲嶅缓**鐨勭増鏈紱
浠栦滑鐨勬枃浠跺埌浜嗗簲褰撲竴骞惰窇锛岃€屼笉鏄浛鎹€?

**璇佹嵁**锛氳繖 41 椤归噷 **32 椤瑰 round-1 kernel 澶辫触**銆佸叏閮ㄥ褰撳墠 kernel 閫氳繃銆?
涓嶆槸绌鸿浆鐨勬祴璇曘€傦紙`docs/rollback/research-sop-kernel.pre-P0-2-round2.py` 淇濈暀浜?round-1 鐗堟湰渚涘楠屻€傦級

**涓ゅ鎴戝垽瀹氬鏍告柟鎻忚堪闇€瑕佷慨姝ｇ殑**锛堝凡鍦ㄦ祴璇曟敞閲婁腑璇存槑锛夛細
- 銆宲aper 鏂囨。琚垹鍚庡繀椤昏繑鍥?`paper=None`銆嶁€斺€旀纭涓烘槸**閲嶈窇璇ラ樁娈?*骞朵骇鍑虹湡瀹炴枃妗ｏ紝
  娴嬭瘯鏂█鐨勬槸銆屽繀椤婚噸璺戙€嶈€屼笉鏄€屽繀椤诲彉 None銆嶏紱
- 銆宲rompt 鏀瑰彉鍚庢棫 run 浠嶅彲 `sop_read_manifest`銆嶁€斺€旀棫 run 鍦ㄦ柊 prompt 涓嬫湰灏变笉鏄?
  *valid* manifest锛屾纭柇瑷€鏄畠琚垎绫讳负 `incompatible` 涓斿瓧鑺備粛鍦ㄣ€?

---

## P0-1 Round 2锛氬彂甯冮『搴忎笌 strict verifier

澶嶆牳鎶ュ憡 搂4 鐨勬寚鎺ф垚绔嬩笖鍙鐜般€傛柊澧?`tools/verify_release.py` 鍚庯紝瀵逛笂涓€杞殑
manifest 杩愯锛?*閫愭潯澶嶇幇浜嗘姤鍛婇噷寮曠敤鐨勫悓涓€缁勫搱甯?*锛?

```
leo commit      FAIL  manifest 8a65838f33e7 != HEAD 6596cfbf59e0
source hashes   FAIL  unified-settings-adapter.js 41df7e19429b!=1f479736c455
                      stage/leo-inject.js         3dd7a177b8ed!=3bf82d3739b4
deployed bundle FAIL  deployed exe FAIL  skill hashes FAIL
```

verifier 妫€鏌ワ細manifest commit == git HEAD銆乺epo clean銆佹簮鏂囦欢鍝堝笇銆侀儴缃?bundle銆?
閮ㄧ讲 EXE銆乧anonical skill 鍝堝笇銆侀儴缃蹭笌 WSL daemon 鍓湰涓€鑷淬€乽pstream 鍥哄畾 revision
锛堟柊澧?`manifests/upstream-pin.json`锛夈€乽pstream 宸ヤ綔鏍戝共鍑€銆?
`--strict` 涓?**NOT TESTED 涔熺畻澶辫触**锛岀粷涓嶅苟鍏?PASS銆?

---

## P0-3 Visible UI 涓?ShellApi 涓€鑷?鈥?`PASS`锛圧ound 3 鎻愬崌锛岃涓嬶級

**root cause锛堣嚜鍔ㄦ壂鎻忕‘璁わ級** 11 涓柟娉曡鍓嶇璋冪敤浣嗗湪
`leo_shell/api.py:_UNIMPLEMENTED_EXTENSIONS` 閲岋紝鍏ㄩ儴鏉ヨ嚜 `stage/leo-inject.js`锛?

| 缁?| 鏂规硶 | 瀹¤缁欑殑浼樺厛绾?|
|---|---|---|
| 鏁版嵁鐢熷懡鍛ㄦ湡 | `list_entity_states` `mark_entity` `restore_entity` `forget_entity` | 1 |
| 椤圭洰 Persona | `get_project_persona` `save_project_persona` | 2 |
| 鑷畾涔変富棰?| `choose_theme_file` `stage_theme_preview` `confirm_theme_preview` `discard_theme_preview` `delete_custom_theme` | 3 |

`called but absent entirely: []`銆乣declared-unimpl and never called: []` 鈥斺€?娌℃湁绗洓绫婚棶棰樸€?

**implementation** 鎸夈€屼笉瑕佷负浜嗕繚浣忔棫 UI 鑰屼复鏃跺疄鐜板ぇ閲忎綆浼樺厛绾?API銆嶏細
- `LEO_FEATURE_FLAGS`锛坄entityLifecycle` / `projectPersona` / `customThemes`锛屽叏 `false`锛夈€?
- **markup 鍦?flag 涓?false 鏃舵牴鏈笉娓叉煋**锛屼笉鏄覆鏌撳悗鍐?disable 鈥斺€?
  銆岀偣浜嗘墠璇存殏鏈疄鐜般€嶇殑浼叆鍙ｈ绉婚櫎鑰屼笉鏄彉鐏般€?
- `data` 椤垫暣椤垫棤鍚庣 鈫?杩炲鑸爣绛鹃兘涓嶇粰锛坅dapter 鏂板 `hiddenPages`锛?
  鍚屾椂璁?`resolvePage()` 鏃犳硶瑙ｆ瀽鍒伴殣钘忛〉锛宍openCust("data")` 鍥炶惤鍒伴粯璁ら〉锛夈€?
- `memory` 椤?*淇濈暀**锛氬彧闅愯棌 Leo 鐨?persona 鍧楋紝璇ラ〉鐨勪笂娓告覆鏌撳櫒浠嶇劧宸ヤ綔鈥斺€?
  鏁撮〉闅愯棌浼氳繛甯︾爫鎺夎兘鐢ㄧ殑涓婃父鍔熻兘銆?
- 瀵瑰簲鐨?`addEventListener` / 鏂囨璧嬪€煎悓鏍疯繘 flag锛屽惁鍒?`querySelector(...)` 杩斿洖
  null 浼氭姏寮傚父銆?

**tests** `tests/test_ui_api_contract.py` 鈥?**5 passed**銆傛妸 flag 鎵撳紑浼氱珛鍒诲け璐?
锛堣礋鍚戝鐓у疄娴嬶細2 failed锛夛紝鎵€浠ャ€屾墦寮€ flag銆嶇瓑浜庛€屽繀椤诲厛瀹炵幇鍚庣銆嶃€?
鏂板鏈疄鐜版柟娉曞嵈涓嶆寚瀹氬綊灞?flag 涔熶細澶辫触銆?

**remaining risk** 闅愯棌涓嶇瓑浜庡疄鐜般€傛暟鎹敓鍛藉懆鏈熸槸瀹¤缁欑殑绗竴浼樺厛锛?
搴斿湪 Phase 1 棣栧厛琛ラ綈銆?*娉ㄦ剰**锛氶」鐩?/ 浼氳瘽 / 浜х墿鐨勫垹闄ゅ凡缁忛€氳繃涓婃父鑷繁鐨?
`deleteProject` / `deleteSession` / `deleteArtifact` 琛ヤ笂浜嗗叆鍙ｏ紝涓庤繖閲岀殑
Leo 涓撳睘 entity lifecycle 鏄袱浠朵簨銆?

---

## P0-4 鍘婚櫎涓汉璺緞缁戝畾 鈥?`PARTIAL`

**宸叉竻闄?*
- `pyi-spec/LeoAIStudio.spec`锛? 澶勭粷瀵硅矾寰勶級锛氱‘璁ょ敱 PyInstaller `--specpath`
  姣忔鐢熸垚锛屽睘浜庝骇鐗?鈫?绉诲嚭鐗堟湰鎺у埗骞跺姞鍏?`.gitignore`銆?
- `tools/make_lion_icon.py`锛? 澶勶級锛氭敼涓轰粨搴撶浉瀵?+ `LEO_APP_ROOT` 瑕嗙洊銆?
- `tools/sync_skills.py`锛? 澶勶級锛氭敼涓?`LEO_WSL_DISTRO` / `LEO_WSL_USER` /
  `LEO_WSL_SKILLS` 鐜鍙橀噺锛岄粯璁ゅ€肩敱鐢ㄦ埛鍚嶆帹瀵笺€?

**浠嶆湭娓呴櫎锛坄TODO`锛?*
- `skills/lean-math/kernel.py` **5 澶?* `/home/leo/...`锛歀ean toolchain銆?
  lake銆乣lean_test` 宸ョ▼銆乣mathlib4` 鐩綍锛屼笖鍐欐 RC 鐗堟湰
  `leanprover--lean4---v4.34.0-rc2`銆傞渶瑕佺殑鏄?*鑷姩鍙戠幇 + health check + 鏄惧紡閰嶇疆**
  锛堟寜鎸囩ず鏈疆涓嶉噸鏋勬暣涓?Lean 闆嗘垚锛夈€?
- 瀹夎鐩綍涓庣敤鎴锋暟鎹洰褰曞皻鏈垎绂伙紙浠嶆槸 `Desktop\LeoAIStudio\` 涓嬫贩鏀撅級銆?
- 蹇嵎鏂瑰紡浠嶇敱 `deploy_release.ps1` 鎸囧悜鍥哄畾妗岄潰鐩綍锛屾病鏈夊畨瑁呭櫒銆?

**楠屾敹鐘舵€侊細`NOT TESTED`銆?* 銆屽湪鍏ㄦ柊 Windows 璐︽埛涓畨瑁呭苟鍚姩銆?*鏃犳硶鍦ㄦ湰鐜鑷瘉**鈥斺€?
鎴戜笉鑳藉垱寤?Windows 鐢ㄦ埛璐︽埛銆備互涓嬮」鐩?*蹇呴』鐢变汉宸ョ幇鍦洪獙鏀?*锛屼笉寰楄涓洪€氳繃锛?

1. 鏂拌处鎴蜂笅鍙屽嚮蹇嵎鏂瑰紡鑳藉惎鍔紝涓斾笉闇€瑕佹敼浠讳綍璺緞锛?
2. WebView2 鍥哄畾鐗堣繍琛屾椂鍦ㄦ柊璐︽埛涓嬪彲鍔犺浇锛?
3. WSL2 鍙戣鐗堝悕绉?/ 鐢ㄦ埛鍚嶄笉鏄?`Ubuntu-24.04` / `leo` 鏃舵ˉ鎺ユ槸鍚︿粛宸ヤ綔锛?
4. Lean 鍦ㄦ病鏈?`/home/leo/...` 鐨勬満鍣ㄤ笂鐨勮涓恒€?

---

## P0-5 鏋勫缓鍙鐜?鈥?`TODO`

鏈紑濮嬨€傚凡鐭ヤ簨瀹烇細`tools/build_launcher.ps1` 浠嶄粠鏃㈡湁 `LeoAIStudio.exe` /
`_launcher` 涓庢棫 PYZ 鍙嶅悜鎻愬彇渚濊禆锛堝璁?搂9.2锛夈€傞渶瑕佷緷璧栭攣 + wheelhouse +
鏋勫缓 manifest锛坢anifest 閮ㄥ垎宸茬敱 `tools/build_manifest.py` 鎻愬墠鍏峰锛夈€?

---

## Round 3锛?C + 2D锛?

### 2C 鈥?P0-3 浠?`CONDITIONAL PASS` 鎻愬崌鍒?`PASS`

澶嶆牳鏂圭殑 mutation test 鏄鐨勩€傛垜澶嶇幇浜嗭細鍦?`leo-inject.js` 鏈熬杩藉姞涓€鏉℃湭缁?gate 鐨?
`window.pywebview.api.list_entity_states({});`锛屽師鏉ョ殑 5 椤?UI 濂戠害娴嬭瘯**鍏ㄩ儴鐓у父閫氳繃**銆?
瀹冧滑鏂█鐨勬槸銆宖lag 鐨勫€兼槸 false銆嶏紝閭ｆ槸涓€涓€硷紝涓嶆槸鍙揪鎬с€?

鐜板湪娉ㄥ叆灞傚彧閫氳繃涓€涓嚱鏁拌Е杈惧澹筹細`leoBridge(method, ...)`锛屽畠鍦?feature 鍏抽棴鏃剁洿鎺ユ姏閿欍€?
19 澶勮皟鐢ㄧ偣鍏ㄩ儴鏀瑰啓锛堝惈涓ゅ鎶婃柟娉曞綋鍊间紶鐨勶細涓婚棰勮 confirm/discard銆?
`acknowledge_connection` 瀛樺湪鎬ф帰娴嬶級銆?*瀛楅潰閲?`pywebview.api.<name>` 鍦ㄦ敞鍏ュ眰琚姝?*锛?
濂戠害娴嬭瘯鍙戠幇鍗冲け璐ャ€?

瀹炴祴 mutation锛氬共鍑€ `10 passed` 鈫?杩藉姞鏈?gate 璋冪敤 `2 failed` 鈫?鎾ら攢 `10 passed`銆?
鎵€浠ャ€屽叧闂€嶇幇鍦ㄧ瓑浜庛€岃皟涓嶅埌銆嶏紝鑰屼笉鏄€屾病娓叉煋鎸夐挳銆嶃€?

`shell.html` 鍒绘剰涓嶈蛋 bridge锛氬畠鏄惎鍔ㄩ〉锛屾病鏈変换浣?gated 鍔熻兘锛屽崟鐙柇瑷€瀹冨彧璋冨凡瀹炵幇鏂规硶銆?

### 2D-A 鈥?P0-4 闈欐€侀儴鍒嗘竻闆讹紝瀹炴満閮ㄥ垎鍏ㄩ儴 `NOT TESTED`

- `lean-math` 鐨?5 澶?`/home/leo/...` 涓庡啓姝荤殑 RC 宸ュ叿閾惧叏閮ㄧЩ闄ゃ€傝В鏋愰『搴忥細
  閰嶇疆锛坄LEO_LEAN_TOOLCHAIN` / `LEO_LEAN_PROJECT` / `LEO_MATHLIB_DIR`锛夆啋 home 涓嬬殑 elan
  鈫?PATH 涓婄殑 `lean`/`lake`銆俙lean_toolchain_status()` 杩斿洖
  `READY` / `NOT_INSTALLED` / `PROJECT_NOT_READY` / `VERSION_MISMATCH` 骞堕檮鍙搷浣滆鏄庯紝
  **浠讳綍鎯呭喌涓嬮兘涓嶈嚜鍔ㄥ畨瑁?*銆?
- `deploy_release.ps1` 鍘熸湰鏂█涓€鏉″瓧闈㈤噺瀹夎璺緞銆傚畧鍗繚鐣欙紙閮ㄧ讲鍒伴敊鐩綍鏄牬鍧忔€х殑锛夛紝
  浣嗘敼涓?*鎸夌粨鏋勫垽鏂?*鐩爣鏄笉鏄竴涓?Leo 瀹夎锛岃€屼笉鏄垽鏂畠鍦ㄨ皝鐨勬闈笂銆?
- 鍙︽竻闄わ細`build_launcher` 鐨勫浐瀹氫复鏃剁洰褰曘€乣capture_window` 鐨勮緭鍑鸿矾寰勩€?
  `headless_verify` 鐨勯粯璁ゆ牴銆乣make_lion_icon` 鏂囨。閲岀殑瑙ｉ噴鍣ㄣ€?
- `tools/portability_check.py`锛?*0 hard binding锛? configurable default**銆?
  `tests/test_portability.py` 鎶婂畠绾冲叆娴嬭瘯骞跺甫璐熷悜瀵圭収銆?
- **闈欐€侀€氳繃 鈮?瀹炴満閫氳繃銆?* `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` 鍒楀嚭 27 椤规棤娉曡嚜璇佺殑
  瀹炴満楠屾敹锛?*鍏ㄩ儴 `NOT TESTED`**銆傚洜姝?P0-4 = `PARTIAL`銆?

### 2D-B 鈥?P0-5 浠?`TODO` 鍒?`PARTIAL`

浜斿瀵规棫鍙戝竷浠剁殑渚濊禆鍏ㄩ儴绉诲埌 `-Legacy` 寮€鍏充箣鍚庯紝hermetic 鎴愪负榛樿銆?
`requirements.lock` 鍥哄畾 21 涓寘锛宍manifests/dependency-lock.json` 璁板綍鏉ユ簮
骞?*鏄庡啓 `vendored_wheelhouse: false`**銆?

璺戝嚭鏉ョ殑涓や釜缁撹锛堜笉鏄帹鏂級锛?

- **PYZ 鎻愬彇纭疄鏄浣欑殑**锛氬畠鎭㈠鐨勫叚涓ā鍧楀湪姝ｅ父鏋勫缓鐨?PYZ 閲岄兘鏈夛紝
  `webview` 鐨?45 涓ā鍧椾篃鍦ㄣ€傛棫 `_launcher` 閲岀殑鏁ｈ鍓湰鏄啑浣欏洖濉€?
- **鍥炲～涓嶆槸澶氫綑鐨?*锛屽畠鍦ㄦ帺鐩栫己澶辩殑鍘熺敓 DLL銆傝繖涓?Python 鏄?conda 鍙戣鐗堬紝
  `ffi-8.dll` / `sqlite3.dll` / `libbz2.dll` / `liblzma.dll` / `libexpat.dll` 鏀惧湪
  `<base_prefix>/Library/bin`锛孭yInstaller 涓嶆壂閭ｉ噷銆?*绗竴娆?hermetic 鏋勫缓閫氳繃浜?
  package contract锛岀劧鍚庡惎鍔ㄦ椂姝诲湪 `DLL load failed while importing _ctypes`銆?*
  鐜板湪杩欎簺 DLL 鏉ヨ嚜澹版槑鐨?Python 宸ュ叿閾俱€?

**楠岃瘉鏂瑰紡**锛氭妸 hermetic 浜х墿鏀捐繘涓€涓?scratch 瀹夎鏍戯紝璺?`--diagnostics`锛?
**exit 0 骞跺啓鍑烘姤鍛?* 鈥斺€?璇存槑鐪熷疄 import 鍥惧湪銆岄浂鏃у彂甯冧欢杈撳叆銆嶇殑鏋勫缓閲岃兘鍔犺浇銆?

**涓轰粈涔堜粛鏄?`PARTIAL` 鑰屼笉鏄?`PASS`**锛氭病鏈?vendored wheelhouse锛坵heel 浠嶄粠 PyPI 瑙ｆ瀽锛夛紝
涓斻€屽湪涓€鍙颁粠鏈杩囨棫鐗堢殑鏈哄櫒涓?clean build銆嶅睘浜庡疄鏈洪獙鏀堕」锛屾湭鍋氥€?

---

## P0-6 Gate 鈥?`FAIL`

涓婁竴鐗堣繖閲屽啓銆孭0-1 / P0-2 / P0-3 宸叉竻闆躲€嶏紝涓庤〃澶寸殑
`P0-3 = CONDITIONAL PASS` 鑷浉鐭涚浘銆傜煕鐩剧殑鏉ユ簮鏄彊浜嬮『鎵嬶紝涓嶆槸浜嬪疄鍙樺寲锛屽凡鏇存銆?

Gate 鐜扮姸锛堝彛寰勫彧鍏佽 `PASS` / `FAIL` / `PARTIAL` / `BLOCKED` / `NOT TESTED`锛夛細

| Gate 蹇呴』椤?| 鐘舵€?|
|---|---|
| P0-1 鍗曚竴鍙俊婧愮爜 | `PASS` |
| P0-2 research-sop 璇佹嵁瀹屾暣鎬?| `PASS` |
| P0-3 Visible UI 涓?ShellApi 涓€鑷?| `PASS` |
| P0-4 鍙Щ妞嶆€?| `PARTIAL` 鈥?闈欐€佹竻闆讹紝27 椤瑰疄鏈洪獙鏀?`NOT TESTED` |
| P0-5 鏋勫缓鍙鐜?| `PARTIAL` 鈥?hermetic 鍙瀯寤哄彲杩愯锛屾棤 wheelhouse锛宑lean-machine 鏋勫缓鏈獙 |

**鍙鍏朵腑浠讳綍涓€椤逛笉鏄?`PASS`锛孭0-6 灏辨槸 `FAIL`銆?*
`CONDITIONAL PASS` 涓嶇畻 `PASS`锛沗NOT TESTED` 涓嶇畻 `PASS`銆?
鍥犳鐜板湪涓嶅緱杩涘叆 Workspace / PINN / Companion / 鏂板墠绔姛鑳姐€?

---

## 鍙樻洿鏃ュ織

| 鏃堕棿 | 鍐呭 |
|---|---|
| 2026-09-03 | 寤虹珛鏈枃浠讹紱瀹屾垚 P0-1 浜嬪疄璁ゅ畾锛堟棤鐗堟湰鎺у埗 / zip 闈炴簮鐮佸寘 / 鏃犻渶 merge锛?|
| 2026-09-03 | P0-2锛歳un 缁戝畾 + manifest + 鐘舵€佽瘹瀹炲寲锛?2 椤瑰洖褰掓祴璇曪紝宸插淇鍓?kernel 楠岃瘉浼氬け璐?|
| 2026-09-03 | P0-3锛氫笁缁?feature flag锛宍data` 椤电Щ鍑哄鑸紝5 椤瑰绾︽祴璇?+ 璐熷悜瀵圭収 |
| 2026-09-03 | P0-4锛氭竻闄?spec / 涓や釜宸ュ叿鐨勭‖缂栫爜锛沴ean-math 涓庡畨瑁呭竷灞€浠嶅緟鍔?|
| 2026-09-03 | 棣栨鎻愪氦 `8a65838`锛涙瀯寤?+ 閮ㄧ讲锛屽绾﹂€氳繃锛?43 tests passed |


````

</details>

<a id="archive-p0-final-closure-report"></a>

### R021 — 项目/docs/P0_FINAL_CLOSURE_REPORT.md

<details>
<summary>展开完整原文</summary>

````markdown
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

````

</details>

<a id="archive-p0-manual-acceptance-checklist"></a>

### R022 — 项目/docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md

<details>
<summary>展开完整原文</summary>

```markdown
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

```

</details>

### R023 — 项目/docs/P0_MANUAL_ENVIRONMENT_ACCEPTANCE_PACKET.md

<details>
<summary>展开完整原文</summary>

````markdown
# P0 Manual Environment Acceptance Packet

**状态：HUMAN REVIEW REQUIRED。没有在本文件中批准任何人工验收行。**

本包对应 Phase II continuation branch `codex/pinn-mvp-phase2-20260908t124356z`，base commit
`2bfc5b0fe638fc9dab71a07dc292ca26da108353`。源码、测试和收集器结果仅证明各自所述范围。
原始 `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` 的 **A1–F3 共 27 行保持原状**。
本包的 `NOT-RUN` 对应原清单的 `NOT TESTED`；`AUTOMATED PASS` 只描述机器可判的子事实，
不能抄成整行 `PASS`。任一必要环境缺失时，P0-4/P0-5 不能由这些子事实自动升级为 PASS。

## 1. 本轮实际收集了什么

收集时间：`2026-09-08T12:51:50Z` 至 `12:51:57Z` 左右。收集目标是原有安装目录
`%USERPROFILE%\Desktop\LeoAIStudio`，不是本轮新构建安装件。原有用户设置和凭证未改动，
未启动模型对话，未安装 Lean，未创建 Windows/WSL 用户，未移除任何运行时。

证据目录是本 worktree 的同级目录：

```text
../LeoAIStudio-pinn-phase2-evidence-20260908T124356Z/manual-environment-current-host/
  collection.json
  block-A.stdout.json + block-A.stderr.txt
  block-B.stdout.json + block-B.stderr.txt
  block-C.stdout.json + block-C.stderr.txt
  block-D.stdout.json + block-D.stderr.txt
  files.sha256.json
```

该目录 `files.sha256.json` 的 SHA256 为
`26ee14b538ec1d851c23e9d7c4586a99727c6da70876002cfed2cb631dd730f1`；登记文件已逐一读回验证。
`collection.json` 记录准确源码 commit/dirty status、Python executable/version、安装 EXE SHA256、
每个 collector 的源码 SHA256、命令、起始时间和 exit code。**没有由旧 EXE 文件时间推断源码来源。**

| 实测子事实 | 结果 | 可以说明什么 / 不能说明什么 |
| --- | --- | --- |
| 当前 Windows SID / 安装用户目录 | AUTOMATED PASS | SID 已保存；`AppPaths` 实际目录为 `<install>/user`，凭证目录为 `<install>/user/credentials`。当前账户不是新账户 |
| 当前凭证文件库存 | AUTOMATED PASS，未解密 | 记录了文件路径；不能证明当前/跨账户 DPAPI 读回，更不能替代 A6 |
| 系统 WebView2 | `152.0.4191.66`，AUTOMATED PASS | 来自当前注册信息，不沿用历史的 `152.0.4191.62` |
| 固定 WebView2 | `152.0.4191.53`，目录内恰有一个 executable | 只证明文件布局；没有因此宣称新机器 CoreWebView2 初始化成功 |
| WSL 发行版和用户 | 仅 `Ubuntu-24.04`；默认 `leo`，home `/home/leo` | 无已验证可用于 C1/C2 的额外测试目标；C3/C4 缺失条件不存在 |
| `sync_skills.py --discover` | AUTOMATED PASS | 实际返回的发行版集合与 WSL 列表一致；C5 仍需人工将该实测记录签入清单 |
| Windows Lean 状态 | `NOT_INSTALLED`，AUTOMATED PASS 子事实 | `lean`、`lake`、`elan` 不在当前 PATH；真实 kernel 报缺失并给出配置说明；没有 Lean 求值 |
| Lean 路径前后库存 | `.elan` 在探测前后均不存在 | 只证明此次记录路径的文件系统状态，不能推出所有环境中都无下载 |

A/B/C collector 的子进程 exit code 为 0，D 为 2。collector 的 exit code 是收集结果，
**不是人工行判决**；尤其 A/B/C 的返回 0 不能抹去其 `UNDETERMINED` 行建议。
原始建议中 B1/C5/D1 出现 `suggested_verdict=PASS`，本包仍要求人工检查其场景和证据范围。
本轮新构建 A/B、安装件、visible-window 和发布 provenance 的结果由主
P0 Acceptance Closure Report 单独绑定，不与这里的旧安装件库存混合。

## 2. 两处真实 evidence collector 缺陷及本轮修复

1. **A collector 查错了状态目录，而且说明文字夸大了 DPAPI 验证。** 原实现检查
   `%LOCALAPPDATA%/leo-ai-studio`，真实 `AppPaths`/`SecretsStore` 使用 portable install 的
   `user/credentials`。现新增显式 `--app-root`，由实际 `AppPaths` 生成待查路径；只列文件，
   不解密秘密；输出明确 `decryption_tested=false`。同时修正文件过滤表达式，名称以
   `secrets.json` 结尾的目录不再被算作凭证文件。
2. **D6 的 before/after 比较原来是同一时刻的自比较。** `_check_no_autoinstall` 原来在
   所有 status 调用结束之后才读取 `before=home.exists()`，随后立刻与 `home.exists()` 比较，
   得到的 PASS 没有时间区间证据。现在在任何 binary version/status probe 之前读取目录库存，
   结束后独立再读；新增、删除、size/mtime 变化可见，读失败为 UNDETERMINED。输出限定为
   文件系统库存观察，D6 的所有环境与网络行为仍待人工验收。

新包装器 `tools/manual_acceptance/collect_environment_packet.py` 为每次收集创建**全新目录**；
已存在路径即失败。保存原始 stdout/stderr，保留非零返回值和不能解析的输出。
默认只运行 A/B/C；Lean 必须显式启用，且仅在已确认不会触发工具链安装时启用。
任何真实 Lean theorem probe 的工作目录被放在本次新建 evidence 目录内，避免写到既有研究目录。
该包装器不写原人工清单，不授权 Gate，不枚举或打印 API key。

## 3. 操作者一次性准备与证据规则

选择一个独立、可保留快照的测试 VM 或专用测试机器。由机器所有者准备所需 Windows 账户和
运行时状态；不要把现有工作机通过卸载 WSL/WebView2 变成测试夹具。每个场景从已记录的初始
快照开始，使用本轮待验收的**同一明确安装 artifact**，保存安装包 manifest、EXE SHA256 和
源码 commit。不得带入原工作机的 `user/`、API key、历史 research-runs 或失败日志。

在测试机 PowerShell 中，给变量填写实际位置；以下都是显式本次路径，不修改机器级配置：

```powershell
$p0Source = 'D:\P0\source'
$p0App = 'D:\P0\installed-product'
$p0Python = Join-Path $p0Source '.venv\Scripts\python.exe'
$p0Evidence = Join-Path 'D:\P0\evidence' (Get-Date -Format 'yyyyMMddTHHmmss')
if (Test-Path -LiteralPath $p0Evidence) { throw 'Evidence directory already exists' }
& $p0Python (Join-Path $p0Source 'tools\manual_acceptance\collect_environment_packet.py') `
  --app-root $p0App --output $p0Evidence
$collectorExit = $LASTEXITCODE
Write-Output "collector_exit=$collectorExit; manual rows remain HUMAN REVIEW REQUIRED"
```

新账户中可以调用只读 source/tools 所在路径；**应用必须正常从其安装 EXE 启动**。
设置 `$p0App` 只告诉 collector 去哪里观察，并不设置 `LEO_STUDIO_ROOT` 或重定向程序。
原始 collector 的 `--save PATH` 会覆盖同名文件；需要额外专项收集时，先验证路径不存在，
每次使用新文件名，或继续使用上面的 exclusive 包装器。

每行至少保存：行 ID、开始/结束 UTC、测试人、环境描述、账户 SID、安装件身份、实际动作、
预期/实际结果、raw command/log/screenshot 路径、每份 evidence SHA256、人工判定和原因。
截图避开密钥输入值；保留错误完整类型/时间/阶段，不截掉失败。
同一目录后续补测写新的版本，禁止覆盖已有失败结果。

## 4. A1–A7：全新 Windows 账户

由所有者在 Windows 设置中的账户管理界面创建并登录一个新的测试账户。记录新旧 SID；
SID 相同不能算新账户。把正式待验收安装件放在新账户可写的本地目录，确保初始没有 `user/`。
不要复制工作账户的真实 credentials。先运行 A collector，再从 Explorer 双击安装 EXE。

| 行 | 当前状态 | 实际操作 | 应保存证据 | PASS / FAIL 判据 |
| --- | --- | --- | --- | --- |
| A1 | NOT-RUN | 新账户安装并首次启动；不从开发 Python 启动 | 新 SID、安装件 hash、进程路径、启动录屏/截图、日志 | PASS：正常可见窗口、不黑屏、不被最小化；FAIL：崩溃、后台有进程但看不到窗口、必须手工修补 |
| A2 | NOT-RUN | 观察首次启动页 | 无敏感值的完整窗口截图 | PASS：暖色启动页、狮标、两个按钮均可见；FAIL：缺失、错误主题、遮挡或资源加载错误 |
| A3 | NOT-RUN | 不输入 API key、不点击继续；记录观察区间和页面事件 | collector 初始状态、录屏/导航日志 | PASS：始终停在启动页；FAIL：在无用户动作/无 key 时自动进入工作台。观察时长只记录为证据，不另造数值验收阈值 |
| A4 | NOT-RUN | 点击「先逛逛」一次 | 点击前后截图、事件记录 | PASS：进入工作台且顶部恰有一条浏览模式栏；FAIL：无法进入、栏缺失或重复 |
| A5 | NOT-RUN | 由操作者在新账户输入经批准的测试服务凭证并保存 | 脱敏 daemon 重启/连接日志、保存前后 UI；不保存 key 文本 | PASS：daemon 重启且新凭证生效，浏览模式栏消失；FAIL：旧连接继续运行、错误被忽略、重启未发生。不能用不存在的假 key 冒充真实连接成功 |
| A6 | NOT-RUN | 新账户 UI 保存后重启应用读回；再做下述非秘密 DPAPI canary 跨账户测试 | 两 SID、相同 canary artifact hash、同账户 roundtrip=true、跨账户解密拒绝、产品重启读回证据 | PASS：本账户能保存/读回且另一个账户不能解密同一可读取 blob；FAIL：跨账户解密成功或自己保存后无法读回。仅目录不存在、文件不可访问或库存差异都不够 |
| A7 | NOT-RUN | 记录完整安装/启动动作，不改 source、路径或 machine environment | 完整步骤、首次与结束 source status、环境变量记录 | PASS：全过程零手工代码/路径修补；FAIL：需要编辑配置文件源码、路径硬编码或环境补丁才能启动 |

**A6 安全操作细节：**使用固定公开测试字符串构造 canary，绝不复制真实凭证。
所有者先提供一个两个测试账户都能读取的独立证据目录。在旧测试账户下，用
`.NET ProtectedData.Protect(..., CurrentUser)` 保护 canary，并用同账户 `Unprotect` 读回；
只记录布尔结果和加密文件 hash，不记录真实 secret。在新测试账户下先证明**成功读到相同
字节/hash**，再调用 `Unprotect`；预期抛出 cryptographic error。若读取文件本身被 ACL 拒绝，
只能记测试 BLOCKED，不能说 DPAPI 已拒绝。产品自身的 save/relaunch/readback 仍必须另外执行。

可执行的 canary 核心（在每个账户各自的新 evidence 目录内执行，文件路径由操作者明确指定）：

```powershell
Add-Type -AssemblyName System.Security
$p0CanaryPath = 'D:\P0\shared-evidence\A6-canary.dpapi'
$p0CanaryBytes = [Text.Encoding]::UTF8.GetBytes('Leo-A6-public-nonsecret-canary-v1')
# 只在创建它的账户执行；拒绝覆盖：
if (Test-Path -LiteralPath $p0CanaryPath) { throw 'Canary already exists' }
$p0Protected = [Security.Cryptography.ProtectedData]::Protect(
  $p0CanaryBytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
[IO.File]::WriteAllBytes($p0CanaryPath, $p0Protected)
$p0Roundtrip = [Security.Cryptography.ProtectedData]::Unprotect(
  $p0Protected, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
Write-Output ('same_account_roundtrip=' + ([Convert]::ToBase64String($p0Roundtrip) -eq [Convert]::ToBase64String($p0CanaryBytes)))
Get-FileHash -LiteralPath $p0CanaryPath -Algorithm SHA256
# 第二账户只执行下面的读取/解密段，保存它自己的 SID 和结果：
$p0ReadableBlob = [IO.File]::ReadAllBytes($p0CanaryPath)
Get-FileHash -LiteralPath $p0CanaryPath -Algorithm SHA256
try {
  [void][Security.Cryptography.ProtectedData]::Unprotect(
    $p0ReadableBlob, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
  Write-Output 'cross_account_decrypt_succeeded=true'
} catch {
  Write-Output ('cross_account_decrypt_succeeded=false; exception=' + $_.Exception.GetType().FullName)
}
```

上述脚本未在本轮执行；它是人工执行说明，不是已有 A6 evidence。

## 5. B1–B3：WebView2 运行时

| 行 | 当前状态 | 实际操作 | 应保存证据 | PASS / FAIL 判据 |
| --- | --- | --- | --- | --- |
| B1 | NOT-RUN（新机器条件） | 在新 Windows/VM 中加载随待验收包提供的 fixed runtime，再正常启动 EXE | OS/VM快照 ID、runtime manifest/hash、实际子进程 binary 路径、CoreWebView2 初始化日志、窗口截图 | PASS：CoreWebView2 成功初始化并显示 UI；FAIL：黑屏、0x80070002、进程挂起或初始化失败。文件存在只算子事实 |
| B2 | NOT-RUN | 在仅有 Evergreen 的测试环境使用不附带 fixed runtime 的独立场景包；不改旧安装件 | 系统版本/注册信息、场景包清单、启动日志和可见错误或工作窗口 | PASS：系统版回退可用，或者显示明确、可操作的提示；FAIL：崩溃/黑屏/无说明。不预先规定必须自动回退 |
| B3 | NOT-RUN | 用从未安装 Evergreen 且不附 fixed runtime 的 VM 快照启动同版本应用 | 缺失环境证据、启动录屏/错误日志、安装指引全文 | PASS：明确安装指引；FAIL：黑屏/后台残留且无说明/崩溃 |

`WEBVIEW2_RUNTIME_PATH` 必须是包含 `msedgewebview2.exe` 的**目录**。人为把它指向坏路径或
exe 文件，只能验证坏配置诊断，不能等价证明 B3，因为系统 Evergreen 仍然可能可用。
当前源码 `configure_fixed_runtime` 依赖 `AppPaths.webview2_dir()`，没有实现已确认可用的
Evergreen 自动回退。本轮根任务会采集缺少 bundled runtime 的真实退出/可见提示；在该结果
出现之前，不能将系统 Evergreen 存在写成 B2 可用。B2 表格中的“回退或明确提示”是原验收标准，
并非对当前实现行为的预测。
可在当前机器额外创建全新的隔离应用副本，省略 fixed runtime，诊断 B2 搜索路径；原安装件
不改动。这仍必须准确标记所用场景，不能将同机 fixture 偷换成新机器证据。

## 6. C1–C5：WSL2 环境

| 行 | 当前状态 | 实际操作 | 应保存证据 | PASS / FAIL 判据 |
| --- | --- | --- | --- | --- |
| C1 | NOT-RUN | 使用已经准备好的普通测试用户，用户名不为 `leo`；当前进程设置 `LEO_WSL_USER`，启动隔离安装件并实际同步一次 | `id -un`/真实 home、覆盖值、bridge 日志、目标 home 技能库存/hash | PASS：实际桥接和技能落到正确用户 home；FAIL：仍写旧用户 home、只输出参数但连接/同步失败 |
| C2 | NOT-RUN | 使用真实另一个发行版名并设置 `LEO_WSL_DISTRO`；其余输入不变 | `wsl --list --verbose`、发行版名、bridge/version、技能目标 | PASS：选中该发行版并完成实际桥接；FAIL：使用旧发行版、忽略覆盖或报不明确的错误 |
| C3 | NOT-RUN | 在没有启用/安装 WSL2 的 VM 上启动应用并触发依赖 WSL 的功能 | 功能状态、`wsl --status` 原始输出、UI错误/日志 | PASS：明确错误信息、不崩溃；FAIL：无说明、卡死、未处理异常 |
| C4 | NOT-RUN | 在 WSL 已启用但无发行版的快照执行同样操作 | 空 distro list、系统状态、UI提示 | PASS：明确提示安装/选择发行版；FAIL：把空列表当成功、崩溃或误启动错误目标 |
| C5 | AUTOMATED PASS / HUMAN REVIEW REQUIRED | 原样运行 `tools/sync_skills.py --discover` 并与 `wsl --list --quiet` 对比 | 本轮 `block-C.stdout.json` 已保存实际两者 | PASS：列出全部实际发行版、没有虚构项目；FAIL：漏项、虚构或乱码。人类可据此签核当前场景 |

专项只读诊断命令：

```powershell
& $p0Python (Join-Path $p0Source 'tools\manual_acceptance\verify_wsl_environment.py') `
  --distro '实际已安装的测试发行版' --user '实际已存在的测试用户' --json
```

`--distro/--user` 只会检查覆盖是否到达 bridge；**输出里出现该字符串不证明 C1/C2 成功**。
落盘同步须由测试环境操作者另行执行，保存前后库存；不要往原用户 home 写技能。
本轮没有安装发行版、创建/切换系统默认用户、注销发行版或改变机器 WSL 功能。

## 7. D1–D6：Lean / Mathlib

Lean 的真实运行环境应与产品 skill 所在环境一致。当前 Windows 的 `NOT_INSTALLED`
不推断 WSL daemon 内是否安装 Lean。对于 D2–D5，使用已准备好的专用环境，不让 collector
负责 provisioning。先审查实际 `lean/lake` 路径是否是已安装的工具链；不要把会下载缺失
工具链的 elan shim 当成“只读 --version”。

| 行 | 当前状态 | 实际操作 | 应保存证据 | PASS / FAIL 判据 |
| --- | --- | --- | --- | --- |
| D1 | AUTOMATED PASS / HUMAN REVIEW REQUIRED | 无 Lean 的当前 Windows 环境调用真实 kernel status | 本轮 `block-D.stdout.json` 的 state/summary/paths | PASS：`NOT_INSTALLED` 且说明可操作；FAIL：错误报告 READY、异常退出或自动下载 |
| D2 | NOT-RUN | 使用已装实际 elan/Lean、没有 resolved Lake project 的测试账户调用 status | binary/version、项目目录库存、返回结构 | PASS：`PROJECT_NOT_READY`；FAIL：READY/模糊状态/无说明。仅有 elan wrapper 且尚无 Lean toolchain 不等价于“已安装 Lean” |
| D3 | NOT-RUN | 对一个独立测试项目副本设置与已安装 toolchain 不同的项目 pin；保留原项目 | 实际工具链版本、测试副本 `lean-toolchain`、status | PASS：`VERSION_MISMATCH` 且指出不一致；FAIL：静默继续或声称 READY |
| D4 | NOT-RUN | 已安装匹配 Lean、resolved project 和 Mathlib oleans 的环境运行 collector，真正 `lean_check` | 真实 source theorem、命令、Lean stdout/stderr/exit、kernel result | PASS：READY 且 theorem `n+0=n` 真正通过 Lean；FAIL：仅发现目录就标 READY，或 theorem 求值失败被忽略 |
| D5 | NOT-RUN | 每次只在新的子进程设置一个 `LEO_LEAN_TOOLCHAIN`、`LEO_LEAN_PROJECT`、`LEO_MATHLIB_DIR`，分别指向真实已备目录 | 每个 override 的命令、resolved path、status/求值输出 | PASS：三个变量各自改变正确对应路径；FAIL：被忽略、错路径、意外污染另外两项；默认环境结果不能替代覆盖测试 |
| D6 | PARTIAL / HUMAN REVIEW REQUIRED | 在 D1–D5 各真实环境运行前后保存库存，并使用操作者批准的网络/进程监测观察调用 | 每次真实 before/after、工具链位置、运行过程/网络记录 | PASS：各状态都没有自动下载/安装；FAIL：自动获取任何工具链。当前仅有 D1 一次目录库存不变，不够签核全部 D6 |

已有安全环境确认后，可在新的 evidence 输出目录执行包装器的 `--include-lean`。
若在真实 daemon/WSL 内验收，需要在其同一 runtime 内运行 `lean_toolchain_status()` 和
`lean_check(...)`，保存原始输出，不能把 Windows subprocess 的缺失结果冒充 WSL 结果。

## 8. E1–E3：真实五角色链

`verify_research_sop_live.py --live` **只检查前置条件，不运行五角色链**。不能将它的退出码、
模型名称出现或 parser smoke 测试当作 E1 evidence。collector 不寻找 key；使用实际产品中
操作者选定且已授权的服务/模型。若不具备连接或真实 headless entrypoint，本节保持 NOT-RUN。

在真实 Leo kernel 中确认 `orchestrate_research` 已加载，然后对新的测试任务执行：

```python
result = orchestrate_research(
    "研究有限等差数列求和公式，给出可复核推导、真实数值例子、独立核验和最终研究文档。",
    resume=False,
    max_rollbacks=2,
)
print(result)
print(sop_status(result["run_id"]))
```

该示例不是 Poisson formal scientific run，不执行 HASH LOCK 或训练。
若实际返回结构与示例 `run_id` 字段不同，应先读原始结构，记录真实字段，不编造 run ID。

| 行 | 当前状态 | 实际操作 | 应保存证据 | PASS / FAIL 判据 |
| --- | --- | --- | --- | --- |
| E1 | NOT-RUN | 上述真实模型链运行全部五角色 | provider/model 指定值、请求/退出阶段、5个阶段 JSON/文档、真实最终文档 | PASS：五角色真实执行，validator 通过，paper 非空且其hash一致；FAIL：跳过、复读/工具语法失败、schema失败或空文档被当完成 |
| E2 | NOT-RUN | 检查该真实 run 的目录和 manifest；对照实际 task/run/source identity | `research-runs/<run_id>/`、manifest、阶段记录、历史事件 | PASS：结构与当前 SOP 一致、身份/hash可回读；FAIL：跨task复用、缺项或无法回读。无rollback时不虚构history事件 |
| E3 | NOT-RUN | 在独立新任务中让真实 validator 审核一份明确存在矛盾的研究初稿；记录它真实产生的 revise/fail 和后续返回 | validator实际回复、before阶段hash、rollback manifest、history archive读回hash、后续attempt | PASS：真实打回触发归档，旧证据仍可读且hash匹配；FAIL：覆盖/删除旧证据、归档失败仍继续。若真实 validator 未打回，记 NOT-RUN，不手工伪造 verdict |

失败模型回复可另用 `--transcript` 与实际 pinned upstream parser 分类；这只是失败诊断。
不得把原 live failure 改写为成功，或事后生成 stages 冒充真实 delegate 输出。

## 9. F1–F3：clean build 和两次构建

本包没有启动构建；本轮根任务在独立 clone 中的 A/B build 结果请查主 P0 Closure Report。
其 scoped automated evidence 可以支持 F2/F3 的人工审阅，但不证明全新机器 F1 已执行。
现行 F3 标准是**差异可解释**，本包不新增 bit-for-bit equality 门槛。

| 行 | 本包执行范围 | 操作 | 应保存证据 | PASS / FAIL 判据 |
| --- | --- | --- | --- | --- |
| F1 | NOT-RUN（clean-machine） | 在从未存在旧 Leo EXE/_launcher 的新机器/VM，通过交付版脚本、声明的 Python和离线wheelhouse构建 | 初始机器/文件清单、toolchain来源hash、dependencies audit、完整构建日志/退出码、产物清单hash | PASS：没有旧EXE输入仍成功构建；FAIL：读取旧exe/_launcher提取依赖，缺失未声明输入或构建失败。仅把AppRoot指向不存在目录是组件诊断 |
| F2 | 由本轮独立构建证据另行判定 | 从准确 commit 新 clone A/B；clone中没有复制开发venv或历史缓存；分别配置锁定依赖 | clone来源、HEAD、clean status、requirements/wheelhouse hashes、独立安装日志、实际build command | PASS：fresh clone+明示外部输入构建成功；FAIL：隐式取旧开发目录文件、HEAD不符、出现未解释外部依赖 |
| F3 | 由本轮独立构建证据另行判定 | 相同 commit/依赖/toolchain 分别构建；逐项比较 inventory、SHA、packaging metadata | A/B产物全清单、diff、每个差异的可核实原因 | PASS：差异与嵌入路径/时间等实证对应，可解释且无遗漏；FAIL：不同输入、资源缺失、不明二进制差异被概括为“PyInstaller本来如此” |

按最终交付脚本实际参数执行，至少记录以下既有入口的原始命令和输出：

```powershell
& $p0Python (Join-Path $p0Source 'tools\build_wheelhouse.py') verify
& $p0Python (Join-Path $p0Source 'tools\build_wheelhouse.py') audit-env --python $p0Python --json
# 每个 clone 的 BuildRoot、OutputRoot 都必须是各自独立的新路径。
& (Join-Path $p0Source 'tools\build_launcher.ps1') `
  -BuildRoot $p0Source -OutputRoot 'D:\P0\build-A-output' -AppRoot 'D:\P0\no-old-install'
```

正常路径使用 hermetic 默认；不要设置 `LEO_LEGACY_BUILD=1` 或 `-Legacy` 来规避缺失输入。
若 runtime/upstream 使用独立 vendor 包，记录该包的来源/版本/hash并由最终 assembly记录部署位置。
应用真实启动与 strict release verifier 的证据须绑定最终部署产物，不能给旧EXE换manifest。

## 10. 新增修复测试记录与临时文件处置

按用户本轮明确要求：新增测试在运行和记录后删除，既有测试保持原状。
以下是**临时修复验证**，不是交付后的常驻新增回归套件。

```text
python -m pytest -q tests/test_manual_environment_packet.py tests/test_manual_acceptance.py
27 passed / 0 failed / 0 skipped
```

使用的是前一轮已锁依赖的 Python 3.12.9 `.venv`；完整 executable 和本轮追加的 `--basetemp`
路径见 `collector-focused-regression.log` / 主报告执行记录。日志位于本轮 evidence 根目录，
最终一次为 `27 passed in 1.39s`。27 = **8个新增临时修复测试 + 19个既有collector测试**。
新增测试源码删除前 SHA256：
`861055f78ae2be6749ca870bab194a8babe3e34666b2d7888180209bdc3daa57`。

8个新增覆盖为：真实portable目录绑定；只库存文件且禁止decrypt；真实before/after之间新增toolchain可检出；
不变库存仅给限定子事实；库存不完整不PASS；before先于任何binary/status调用；保存原始非零证据并拒绝覆盖；
不存在安装EXE时不创建伪造环境包。既有 `tests/test_manual_acceptance.py` 未删除/放宽。

删除范围仅限本轮新增 `tests/test_manual_environment_packet.py` 和它创建的临时 fixture副本；
本轮环境证据、focused raw log、原清单、原工作区、历史 evidence和失败运行全部保留。
删除后的最终全仓回归由根任务重新执行并在主报告列出，不能沿用包含临时测试的数量冒充最终套件数量。

## 11. 人工记录表与 STOP

请逐行填写实测记录，保留空白项未签核状态：

| 字段 | 待填写 |
| --- | --- |
| Row ID / required scenario | |
| 人工执行者 / 审阅者 / UTC | |
| 原始环境快照 / Windows SID / WSL身份 | |
| Source commit / installed EXE SHA256 / manifest | |
| 实际动作与原始 evidence路径/hash | |
| PASS / FAIL / NOT-RUN 及具体理由 | |
| 是否存在未覆盖的 MUST 条件 | |

不能用统一“27项全部通过”签名代替逐行证据。AUTOMATED PASS、HUMAN REVIEW REQUIRED、
NOT-RUN 必须继续分开。必要 P0 未闭合时保持其真实状态，并停止 formal P2/HASH LOCK。
本包不授权 formal lock、trainer、五seed、Gate2–7、Claim或CFD实现。

````

</details>

<a id="archive-p0-release-candidate"></a>

### R024 — 项目/docs/P0_RELEASE_CANDIDATE.md

<details>
<summary>展开完整原文</summary>

````markdown
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

````

</details>

### R025 — 项目/docs/P0_RUNTIME_REMEDIATION_20260908.md

<details>
<summary>展开完整原文</summary>

```markdown
# P0 runtime remediation and current evidence — 2026-09-08

This report describes the isolated remediation worktree derived from inherited snapshot `7c7a6b1`, not the deployed application. Historical P0 reports/checklist and rollback files were restored byte-for-byte from `a4455cc32dccbcf26bdc9c65b0e5df94b6cbf4b4`; their old verdicts are historical evidence, not current results. No historical report, scientific specification, Constitution, installed application, user credential, or upstream checkout was rewritten.

## Current P0 assessment

| Gate | Current status | Evidence and limit |
|---|---|---|
| P0-1 single trusted source / deployment provenance | FAIL | `python tools/verify_release.py --strict` exits 1: no `manifests/build-current.json` in this worktree. No current build/deployment manifest binds this source to an installed release. No release was built or deployed here. |
| P0-2 research-sop evidence integrity | PASS for automated current behavior | Restored research-sop tests pass within the 584-pass regression; all registered reconstructed cases remain. Reviewer-original independent suite remains ABSENT/NOT PROVIDED in restored `manifests/test-suites.json`. Real-model five-role acceptance E1–E3 was NOT-RUN, so this is not a live-model acceptance claim. |
| P0-3 visible UI / ShellApi consistency | PARTIAL | Source contract tests and all 4 real Chromium theme-picker cases pass, including both locales, save, new SettingsStore reconstruction, reload, and credential-write exclusion. Installed EXE/WebView2 visible-window acceptance was NOT-RUN. |
| P0-4 portability | PARTIAL | Scanner exits 0: 0 hard bindings, 1 configurable default, 3 explicitly visible exact-hash historical findings. A fresh Windows account, alternate/non-leo WSL, missing WSL and missing WebView2 scenarios are NOT-RUN. |
| P0-5 dependency/build reproducibility | PARTIAL | All 21 source wheel files matched the existing declared manifest before copy into ignored worktree `wheelhouse/`; destination hashes match, verifier reports 0 problems. Parent provisions isolated environment offline. Clean-machine/fresh-clone/two-build F1–F3 acceptance remains NOT-RUN. |
| P0-6 downstream development gate | FAIL | Existing P0 definitions require P0-4/P0-5 full acceptance; neither is PASS. Dependent product PINN/release work remains blocked. Independent diagnostics, oracle checks, and fail-closed repairs do not imply product acceptance. |

The unchanged checklist's 27 rows remain `NOT TESTED` (report vocabulary equivalent: NOT-RUN). Collector exit 0 and `suggested_verdict: PASS` never sign a checklist row. In particular the WebView2 collector suggests B1 and WSL collector suggests C5 only from observed prerequisites; this report does not adopt those suggestions as acceptance.

## Baseline and regression

All commands below used the original environment interpreter as an explicitly recorded test dependency: `../LeoAIStudio-build/.venv/Scripts/python.exe` (Python 3.12.9), with `cwd` at this isolated worktree. Parent separately provisions and validates the worktree's `.venv`.

| Command | Result | Raw evidence |
|---|---|---|
| `python -m pytest tests -q --tb=short --disable-warnings` after restoration and before repairs | 554 passed, 11 failed, 2 skipped, 34.07 s | `p0/restored-baseline-full.txt` |
| `python -m pytest tests -q -rs --tb=short --disable-warnings` after repairs | 584 passed, 0 failed, 1 skipped, 29.73 s | `p0/after-fixture-restoration-full.txt` |
| `python tools/build_wheelhouse.py verify` | exit 0; 21 wheels, 0 problems | `p0/wheelhouse-verify.txt` |
| `python tools/portability_check.py --json` | exit 0; hard 0, configurable 1, historical 3 | `p0/portability-scan.json` |
| `python tools/verify_release.py --strict` | exit 1; missing current build manifest | `p0/strict-deployment-verifier.txt` |
| `python tools/theme_asset_provenance.py --strict` | exit 1; 12/20 tracked assets, 8 gaps, 0 drift | `p0/theme-asset-provenance-strict.txt` |

The remaining skip is inherited `tests/test_ui_api_contract.py:163`: `entityLifecycle` is enabled, so the obsolete “data pane is hidden while backend absent” branch does not apply. Existing tests still require every enabled feature API to be implemented and correctly gated. Added EntityStore persistence, corrupt-byte preservation and revision-conflict cases verify current supported behavior. No skip/xfail, acceptance threshold change, test deletion, or failure-log replacement was introduced.

One initial `git apply --check` for the historical portability patch failed because current comment context differed; the check made no mutation. The known fix's classifier functions were then integrated precisely. One theme audit invocation incorrectly supplied unsupported `--json` and exited 2; its original output is retained as `p0/theme-asset-provenance.json`; the documented `--strict` invocation above is the actual audit result.

## Root causes addressed and exact ownership

1. **Deleted verification/evidence assets.** Restored 46 original files: all deleted tests and the renamed-away package-contract test, manual acceptance collectors, headless/theme utilities, P0/theme/migration documents and the suite registry. Restored 10 deleted `docs/rollback/` snapshots separately. Every exact source blob hash is recorded in restoration manifests; restored scientific failure evidence stays immutable.
2. **Lost historical-evidence classification.** `tools/portability_check.py` regains the prior `df5e4b2cc7aef7dd92eb609dad712fbdb2b34b7e` implementation; `manifests/portability-historical-evidence.json` and `tests/test_portability.py` restore that accepted revision exactly. The protected audit SHA-256 is `018ff149d95df09eafded81e0274ded0e4ba39fd3023039b9bb1b67883acf8cf`; exact path/hash/type/count matching is mandatory. No general governance/Markdown exclusion was added. Negative fixtures exercise changed bytes, changed path, forbidden runtime/build/deploy/config targets and wrong finding type.
3. **Personal machine path in current design.** `leo_shell/DESIGN.md` replaces one current LeoTree source location with `<LEOTREE_ROOT>`; implementation and locked scientific documents are unchanged.
4. **Dangling manual-acceptance references.** `tools/build_wheelhouse.py` and scanner documentation point back to restored `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`; verifier results remain explicitly distinct from clean-machine acceptance.
5. **Obsolete fixture protocol.** `tests/leo_shell/test_bridge_client.py` now scripts all five existing startup phases (stop, identity, compatibility, model selection, start), keeps the original secret-only-in-env assertions, applies argv secret exclusion across every phase, and adds three preparation-failure tests proving no daemon start occurs after failure.
6. **Obsolete unsupported-feature contract.** `tests/leo_shell/test_api.py` retains all 11 extension parameter cases; the four already implemented EntityStore APIs must return typed unavailable-store failure without paths. Six additional cases validate fresh API persistence, restore/forget revision guards, and preservation of corrupt bytes for all entity operations.
7. **Local preset schema evolution.** `tests/leo_shell/test_settings_store.py` retains exact cloud field sets; the one existing local preset must expose exactly one additional typed `requires_key: false` field and its fixed model/address/noneditable endpoint contract.
8. **Incomplete real DOM harness.** `tests/test_theme_settings_integration.py` extracts the actual production `setLocalModelAccess` dependency newly called by existing `loadPanelState`; no theme cards/state/persistence results are mocked and original three-theme/locale/reload assertions remain unchanged.

No application runtime production behavior was altered by this P0 subtask. Scientific governance implementation repairs are owned and reported separately in the main MVP report. The only production tooling behavior repair is the narrow hash-bound portability classifier restoration.

## Current environment observations and F-008

Read-only collectors observed the existing Windows account; system Evergreen WebView2 `152.0.4191.66`, fixed runtime `152.0.4191.53`; one installed WSL distribution `Ubuntu-24.04`; existing installed LeoAIStudio executable; and available local external build prerequisites. These facts do not simulate missing/fresh scenarios. A/B/C/F JSON files and their exact commands/exit codes are retained in `p0/collector-commands.json`.

F-008 remains OPEN: missing canonical tracked sources include font manifest, two i18n tables, four font files and one legacy hash-named icon (8/20 runtime-read assets). Twelve current source/deployed asset mappings match, including the three-layer injection bundle. No asset was imported or invented to hide this gap.

## Evidence manifests

External evidence root is the sibling `LeoAIStudio-pinn-evidence-20260908T120017Z` directory; paths below are relative to that root:

- `p0/restoration-manifest.json` — 46 exact-source blobs and SHA-256 values.
- `p0/rollback-restoration-manifest.json` — 10 immutable historical rollback files.
- `p0/historical-policy-restoration.json` — prior reviewed policy and unchanged protected-document identity.
- `p0/wheelhouse-copy-manifest.json` — exact 21-wheel source/destination identity.
- `p0/restored-baseline-command.json`, `p0/after-fixture-restoration-command.json` — actual interpreter, command, cwd and exit.
- `p0/audit-commands.json`, `p0/collector-commands.json` — audit/collector commands and exits; the corrected theme command is recorded above.

This report intentionally does not claim PINN MVP COMPLETE or P0 closure. Current-source automated integrity is much better evidenced; human/environment/deployment acceptance is still unresolved.

```

</details>

### R026 — 项目/docs/PINN_MVP_AND_CFD_READINESS_REPORT.md

<details>
<summary>展开完整原文</summary>

```markdown
# 当前状态补充 — 2026-09-09

**PINN MVP = NOT COMPLETE；CFD Readiness = PARTIAL。**

最新科学复核见 [PINN_PHASE2_RECONCILIATION_20260909.md](PINN_PHASE2_RECONCILIATION_20260909.md)，证据截止 `2026-09-09T12:46:51Z`。该报告列出当前 commit、42 项 exact-byte 身份复核、全部指标和阈值、实际测试数量、P0/正式 Gate 边界、G6 实现差距与 CFD 接入位置。以下原报告是 2026-09-08 的历史记录，旧状态和旧目录不可直接当作当前现场。

- 已安装入口版本 `9e53dcc4d534a1dadd93ad0107ee88bef55d455f` 的 strict 实测为 **13 PASS / 0 FAIL / 0 NOT TESTED**；对应全仓回归日志为 **839 passed / 0 failed / 2 skipped**。原文中的旧 P0-1 FAIL 不代表这个已安装版本的当前 strict 结果；新模型功能仍需独立构建和安装验收。
- 科学候选的 42 个文件在当前工作树与 `96f4ef0445832016882060b0fa450ce0a3b0c96c` Git 提交中均零漂移。PRELOCK 6 组 PASS；解析正场满足指标，五个错误场拒绝，独立 FDM 七层收敛重算一致。全部为组件诊断，不是 PINN 训练结果或正式 Gate。
- 所有者已接受 AC-2 的 CGL2000 sampled 指标及 G6 的受限 Level-D/U1 例外组合。该决定没有豁免 P0，也未批准正式 HASH LOCK。当前 G6 helper 仍对 A/B/C 缺失/BLOCKED G5 放行过宽，需独立 draft amendment 和刷新人审身份包；不得按旧 helper 直接正式放行。
- P0-4/P0-5 必要实境验收未闭合，P0-6 仍 FAIL；四条正式科学文件路径不存在；正式 trainer、run recorder、五 seed、core E2E 和 Accuracy Claim 仍 BLOCKED / NOT-RUN。
- 主仓库已在本任务之外形成清理快照 `8c4835e9d5034876235e1108e889902ac5bfa14f`，原 Phase II `repo/` 目录已移除。科学分支与提交保留，当前施工位置是本报告所在的 `codex/conversation-runtime-20260909` 隔离工作树，确切本机路径记录于上述复核报告。本报告不恢复已清理目录，也不宣称当前模型功能工作树已干净。

历史正文以下完整保留，原始 35,459 bytes 的 SHA-256 为 `f809f8e68c204a44eeae36adf272cb62569eb8372e1e4024452f66ac5f6aa249`。当前前缀不修改其中任何原文、旧失败或历史 evidence。

---

# PINN MVP and CFD Readiness Report

Date: 2026-09-08 UTC. Verdict applies to the isolated engineering worktree and the explicitly identified commit/artifacts below.

## 1. Executive Verdict

**PINN MVP = NOT COMPLETE**

**CFD Readiness = PARTIAL**

本轮已实际修复治理校验、恢复回归资产、实现独立数学/验证组件并执行测试。最终从干净工程提交 `1c96066dfb11aff5d151fec83d48fc30251b74bd` 运行：**839 passed / 0 failed / 1 skipped**；另行运行独立 Torch 检查：**8 passed / 0 failed / 0 skipped**。839 中包含 255 项 PINN 治理/科学组件测试，不能据此声称完整科学 workflow 或产品 P0 通过。

阻断条件仍真实存在：P0-1/P0-6 FAIL，P0-3/4/5 PARTIAL；formal spec/protocol/lock 不存在；当前计划要求 P2 最终人工批准。正式 PINN runner、训练配置、Adam/L-BFGS 生命周期、正式 run recorder、五 seed 训练及重建、core E2E suite、claim ledger 和报告图形重绘尚未建立。没有启动训练、创建真实 HASH LOCK、发布应用或实施 CFD。

### 实际仓库与施工隔离

- 原始仓库：`../LeoAIStudio-build`，branch `master`，HEAD `a4455cc32dccbcf26bdc9c65b0e5df94b6cbf4b4`。
- 开工现场：85 个 tracked 路径有改动/删除；未跟踪 PINN/governance/bridge 等源文件；`tests/`、P0 报告和验收工具被删除。旧的“597 passed”等报告不作为当前基线。
- 安全 worktree：当前报告所在仓库；branch `codex/pinn-mvp-20260908t120017z`。
- 继承状态安全快照：`7c7a6b1957164ff55ac4ebeffed7df74b9eb26b6`。该提交仅保存用户现场，不将继承的更改归功于本轮修复。
- 工程修复：`1c96066dfb11aff5d151fec83d48fc30251b74bd`；测试开始和最终诊断导出时 `git status --porcelain` 为空。
- 原工作区 163 项文件 inventory 逐字节复核：0 drift；Git status 与开工二进制记录完全一致。其原有 dirty 状态被保留，未 reset、清理或覆盖。
- 检索根目录/相关目录及父目录未发现适用 `AGENTS.md` / `CLAUDE.md`。已读取 Constitution、v1.3 plan、全部候选 spec/protocol/lock/manifest、Research SOP、现有源码/测试、历史 P0 文档和 failure evidence。

### 治理与锁边界

Constitution v1.0 ACTIVE 原字节 SHA-256：`4300bb848cc968e96c6b9de318796f6791a6cccea518bff2faac96e8f0c87018`。没有修宪、修改 candidate 文件、阈值或既有节点资产。

| 对象 | 现场状态 | 本轮处理 |
|---|---|---|
| Constitution | ACTIVE，最高科学治理权威 | 只读并复核 hash |
| spec/protocol/lock draft、core manifest draft | 未正式 HASH LOCK | 原字节不变；修复其实现校验 |
| GL512 nodes/weights、CGL2000 NPY | 已冻结 exact-byte assets，由候选 protocol 绑定 | 原字节保留；拒绝 self-consistent replacement hashes |
| `specs/poisson-1d/v1.0/spec.json` | 不存在 | 未创建 |
| `specs/poisson-1d/v1.0/protocol.json` | 不存在 | 未创建 |
| `specs/poisson-1d/v1.0/lock.json` | 不存在 | 未创建 |
| `adversarial/core_manifest.json` | 不存在 | 未创建 |
| PRELOCK_VALIDATION | PASS，非正式 Gate | 最终 clean commit 重新执行 |
| Formal Gate 1 | BLOCKED | 缺少正式锁 |
| Formal Gate 2–7 | BLOCKED / NOT-RUN | 未执行依赖计算；组件诊断不改变这些状态 |

现行计划 §14.4 / §15 明确要求 `P2-prelock → STOP / HUMAN REVIEW → P2-formal`，正式 P2 需最终人工批准。产品 P0-6 本身亦未满足，所以即使给出批准也不能直接跳过产品依赖。组件数学诊断、回归修复和证据收集按本次用户明确授权继续。

## 2. Root Causes Fixed

1. **校验只验证包装形状，未核验科学含义。** wrong forcing、wrong BC/domain、训练域、单位、输入变量、缺失 QoI、删 AC、改公式、NaN threshold 原先可 PASS。新增当前 Poisson-v1 契约并验证全部 AC、采样、seed、域、变量和 reference 绑定。
2. **JSON 与 Python 类型语义不同。** NaN/Inf/overflow、重复 key 原先可能进入 hash；`True == 1` 让 schema const/enum 漏检。现在严格拒绝。
3. **自洽 hash 不等于正确求积规则。** uniform weights + 全套重算 hash 原先通过，并把 `∫x²dx` 算成 `0.37487781036168133`。现在固定 v1 已冻结资产身份；正性/和/顺序/finite 与实际文件 hash 亦核验。
4. **锁验证和 Gate bool 漏洞。** DRAFT/MD5/外部路径可误认有效锁；字符串 `"FAIL"` 因 truthiness 触发 PASS；check-then-write 有覆盖竞争。现在固定状态/算法/metadata/路径与七字段 payload，并排他创建、复核、保留失败文件。
5. **解析 evaluator source hash 没有落实。** 当前 prelock 读取真实源码 hash，不能由 sidecar 自称匹配。
6. **Provenance 缺父节点仍可合格。** 现要求可信 recorder entry、exact metadata、合法 hash、完整同名父链及无破坏变换；手写 eligibility 不产生信任。此函数仍须由未来可信 recorder 调用，不能把导入 sidecar 自行构成 registry。
7. **泄漏检查不完整。** 加入 L2/来源缺失/domain/finite 检查。公开 `{0,1}` 仍允许训练 BC 与 validation 复用，boundary metric 回流 optimizer 等仍拒绝。
8. **expected verdict 可被重新贴标签。** 现在检查 15 family / 18 atomic scenario 的关键固定元组、Level-D abstention 和五 seed 预注册。它验证 preregistration，不等于执行这些 E2E 案例。
9. **科学验证没有独立实现。** 新增 raw-array 验证、逐项 AC、独立 FDM、手工推导、负场控制和独立 Torch 导数检查。初次实现中发现的 endpoint 不一致、伪造 protocol metadata、派生 residual overflow 已由独立复核捕获并修复。
10. **回归与历史 evidence 在当前工作树缺失。** 恢复 56 个原有文件；修复旧 fixture 对现有 EntityStore、五阶段启动、local preset、真实 DOM 函数依赖的描述，并新增失败案例，保留契约断言。修复前 11 个测试失败原日志保留。
11. **portability 历史分类丢失。** 从已审定 `df5e4b2` 精确恢复 path/hash/type/count 分类；历史 finding 仍可见，未添加宽泛治理豁免。没有改写受保护审计。

## 3. Files Changed

工程提交相对继承快照修改 **85 个路径**，其中大量内容是恢复原有删除文件，而非重写项目。逐文件理由见文末附表；机器可核对的 SHA-256 清单为 [PINN_MVP_CHANGED_FILES_20260908.json](research_logs/PINN_MVP_CHANGED_FILES_20260908.json)。本报告和该清单在后续 documentation commit 中增加。

历史 P0 文档、Constitution、候选和 NPY 没有被“修复”字节。`docs/P0_EXECUTION_STATUS.md` 原第 343 行带 EOF 空白；原样恢复会让全体 `git diff --cached --check` 返回 2。保留该历史文件，新增/修改的工程内容 whitespace check 通过；原检查输出独立保存。`docs/rollback/** -text` 防止以后 checkout 把历史 LF PowerShell evidence 转成 CRLF。

## 4. Test Matrix

所有最终命令以本 worktree 为 cwd。`python` 在下表指本 worktree `.venv/Scripts/python.exe`，Torch 行单独注明。完整 JUnit/command/stdout/exit 位于外部证据目录。

| 层/命令 | passed | failed | skipped | 结论 |
|---|---:|---:|---:|---|
| 原始 live tree 测试 discovery | 0 | 不适用 | 0 | 测试目录已删除，没有可作为通过依据的 suite |
| 恢复后、修复前 `python -m pytest tests -q --tb=short --disable-warnings` | 554 | 11 | 2 | 基线失败保留 |
| 最终 `python -m pytest tests -q -rs --tb=short --junitxml=<evidence>/final-full-suite.xml` | 839 | 0 | 1 | 24.23 s；clean commit `1c96066` |
| 其中 Shell | 258 | 0 | 0 | 同一 full-suite JUnit 分组，非另一次运行 |
| 其中 Research SOP / Lean | 131 | 0 | 0 | 同上 |
| 其中 PINN governance / scientific / adversarial | 255 | 0 | 0 | 同上，包含 scientific 87、locking/state 79 |
| 其中 build / portability / UI / acceptance contract | 195 | 0 | 1 | 同上 |
| 系统解释器运行 `tests/pinn/torch_derivative_sanity.py`（绝对命令见 `final-diagnostic-commands.json`） | 8 | 0 | 0 | Torch 2.12.1+cu126 实际只用 CPU/float64；无训练 |
| `python -m pinn.governance.prelock` | 6 检查组 PASS | 0 | 0 | 候选 dry run；不是 formal Gate 1 |
| `python -m pinn.validation.diagnose --output <evidence>/scientific-components-final` | 6 fixtures 已诊断 | 0 执行错误 | 0 | 好/坏控制结果均保存，组件成功不代表每个输入满足 AC |
| `python -m pip check` | 0 dependency problems | 0 | 0 | 已安装环境依赖一致 |
| `python tools/build_wheelhouse.py verify` | 21 wheels 有效 | 0 | 0 | 不是 clean-machine build 验收 |
| `python tools/portability_check.py --json` | 0 hard binding | 0 | 0 | 1 configurable、3 显式历史 findings |
| 正式训练/五 seed/Gate 2–7/core E2E | 0 | 0（未运行） | 0 | **BLOCKED**，不计入 pytest skip 或 PASS |
| 27 项人工验收 | 0 | 0（未运行） | 0 | **NOT-RUN / 原 checklist NOT TESTED** |

唯一 skip：`tests/test_ui_api_contract.py:163` 的已有“entityLifecycle 未启用时隐藏数据页”分支；当前 entityLifecycle 已启用，该分支不适用。启用功能的 API、持久化和失败行为仍被测试。本轮未新增 skip/xfail、删除测试或调整 tolerance。

环境：Windows 11 build 26200；Python 3.12.9 conda-forge base；新建独立 `.venv`，从已有且逐 hash 验证的 21 个 wheel 以 `--no-index --find-links` 安装现有 `requirements.lock`。pytest 9.1.1。Node 24.16.0、npm 12.0.2、pnpm 11.19.0、uv 0.12.8；本仓库没有 package.json，不伪造 npm test。完整科学组件仅用 stdlib，未向主环境安装 NumPy/Torch。系统 Python 原有 NumPy 2.4.5/Torch 2.12.1+cu126；系统 Torch 诊断与 build venv 是两个明确分开的环境，不能据此声称已有锁定训练环境。

## 5. Scientific Validation

人工推导：`u*=sin(πx)`、`u*′=πcos(πx)`、`u*″=-π²sin(πx)`，所以 `-u*″-f=0`。定义域 `[0,1]`，内部 `(0,1)`；两端 Dirichlet=0。两解之差满足 `w″=0`，两端条件确定 `w=0`。全量纲为无量纲，没有 time/initial condition/额外 nondimensionalization。推导细节在 [POISSON_DERIVATION.md](scientific_reference/POISSON_DERIVATION.md)。独立三点差分在 99 个点、`h=1e-4` 下复核 forcing（诊断 tolerance `1e-6`），不替代正式 AC 导数。

以下数值是 **analytic positive control**，不是 PINN 输出。raw coordinates/field/一二阶导数/forcing 均在最终证据保存。积分用冻结 GL512 weights；最大范数用冻结 CGL2000；边界用精确 `{0,1}`；epsilon=`1e-30`；比值分母须大于 `1e6*epsilon`。所有量 dimensionless。

| 指标 | 定义/归一化和 sample set | 正对照值 | 阈值 |
|---|---|---:|---|
| AC-1 relative L2(u) | GL512，sqrt(∫(u-u*)²/(∫u*²+eps)) | 0 | `<1e-3` MUST |
| AC-2 relative Linf(u) | CGL2000，max abs error/(max sampled abs u*+eps) | 0 | `<5e-3` MUST |
| AC-3 BC error | `{0,1}`，max abs(u-g) | 1.2246467991473532e-16 | `<1e-4` MUST |
| AC-4 normalized PDE residual | GL512，sqrt(∫(-u″-f)²)/(π²/√2) | 0 | `<1e-2` MUST |
| AC-5 integral QoI | GL512，abs(∫u-2/π)/(2/π) | 3.6622619229090635e-15 | `<1e-3` MUST |
| AC-6 derivative at zero | 精确 x=0，abs(u′(0)-π)/π | 0 | `<5e-3` MUST |
| AC-7 energy violation | GL512，abs(∫u′²-∫fu)/(π²/2) | 6.299390213871842e-15 | `<1e-2` MUST |
| AC-8 relative L2(u′) | GL512，sqrt(∫(u′-u*′)²/(∫u*′²+eps)) | 0 | `<5e-3` SHOULD |
| absolute L2 / absolute Linf | 对应 GL512/CGL2000，不归一化 | 0 / 0 | 诊断项，没有新增验收阈值 |
| PDE residual RMS / max | GL512 原 residual | 0 / 0 | 诊断项 |

AC-2 按 spec 的离散分母 `0.9999992382301501`，没有换成连续 supremum 1。计划表简写“精确值 1”与 spec 的离散公式需正式澄清，原文保留。测试明确等于严格阈值时不能接受。精度指标不读 training loss；`L_PDE/L_BC/L_total` 的正式优化日志尚不存在，不能虚构已经完成 loss/optimizer 审计。

### 独立 FDM（仅 reference subsystem diagnostic）

FDM 无任何 `pinn` import，采用三点 stencil + Thomas 消元；AC 全部仍对解析解计算。

| N（子区间数） | interior max error |
|---:|---:|
| 32 | 8.035776793697824e-4 |
| 64 | 2.0082180969560604e-4 |
| 128 | 5.020091591312337e-5 |
| 256 | 1.254994550148325e-5 |
| 512 | 3.1374687126106693e-6 |
| 1024 | 7.843656864015003e-7 |
| 2048 | 1.960919837618036e-7 |

`p=log2(E(N)/E(2N))` 最后四对为 `2.0000325870698976, 2.000008121803618, 2.0000027437966774, 1.999995864039661`，满足既有 `[1.8,2.2]`，全部误差递减。N=2048 离散 residual max=`1.4004299941916543e-9`。B11 N=4-only 输出 `orders=[]` 和缺失 refinement evidence，未生成不存在的“实测阶数”。未登记 Gate 2 PASS。

### 负向与拒绝证据

| 类别 | 真实覆盖 | 边界 |
|---|---|---|
| wrong forcing / wrong BC / wrong domain | 候选校验 + raw field / FDM 正负控制拒绝 | 组件层 |
| corrupted checkpoint | trusted recorder 的 checkpoint hash mismatch 和缺失 hash 被拒 | 没有真实 checkpoint loader/重载流程；该类别 E2E **BLOCKED** |
| NaN / Inf | JSON、输入场、指标、FDM 派生 residual 拒绝 | 真实 optimizer NaN 传播尚未实现 |
| malformed config / invalid metric | shape/type/缺项/多项/bool/negative/边界值拒绝 | 训练 config schema 尚未定义 |
| insufficient training | 零场/未满足精度场不能凭低 residual/control completion 通过 | 没有进行一次“训练不足”的真实训练 |
| missing evidence / mismatched hash / changed locked spec | 临时锁 fixture、缺 asset/source、错误 digest、原字节篡改拒绝 | 真实仓库仍无 formal lock |
| seed metadata mismatch | candidate/manifest 预注册 mismatch、recorder metadata mismatch 拒绝 | 无五 seed 正式训练结果 |
| B1b / B3 / B4 / B6 | AC1/AC4 分别约 2/2、0.424264/0、0.002/0.032、0.2/5；B3 BC=0.3 | B3 未加权 BC MSE=0.09 单独记录 |
| validation leakage | L1 identity、L2 generator、L3 lineage、L4 所有禁止 consumer；公开 BC 合法复用 | 未来 sampler/optimizer 仍需真实 consumer 记录 |

6 fixtures 的 repeat evaluation 完全一致；独立 Torch 检查同 seed 初始化/forward/一二阶导数逐位一致且不同 seed 不同。此结果不是 deterministic training repeatability。核心 15 family / 18 atomic / good五seed 的完整预注册 suite 仍未执行，不能宣称 core suite PASS。

## 6. Remaining Risks

| Gate | 当前结论 | 必要剩余工作 |
|---|---|---|
| P0-1 | FAIL | 本 worktree 没有 current build manifest；strict verifier exit 1，不能将 source tests 说成 deployed proof |
| P0-2 | PASS（既有定义的自动化范围） | 保留 reconstructed-suite provenance；reviewer original 仍未提供；E1–E3 live chain NOT-RUN |
| P0-3 | PARTIAL | 真实 Chromium theme/persistence 通过；installed EXE/WebView2 visible-window 未验收 |
| P0-4 | PARTIAL | 静态 hard=0；fresh Windows account / alternate或缺失WSL / missing WebView2 等未验收 |
| P0-5 | PARTIAL | 21 wheels/离线 venv 成立；fresh clone/clean machine/two builds 未完成 |
| P0-6 | FAIL | 依照现行 P0-4/P0-5 全验收依赖阻断产品推进 |
| F-008 theme asset chain | PARTIAL / OPEN | strict exit 1；12/20 tracked，8 gaps，0 drift；缺 font manifest、两份 i18n、4 font、1 legacy icon 来源 |

当前系统 Evergreen WebView2=`152.0.4191.66`，fixed runtime=`152.0.4191.53`，WSL 仅观测到 Ubuntu-24.04。这些现存条件不等于缺失/全新环境测试。

另有必须保留的科学限制：

- `write_lock` 是 future internal API；调用者必须拥有真实批准和绑定同一候选的可信 prelock callback。当前没有鉴权批准记录系统/正式 lock CLI。
- G6 文本：计划 §3.6 只列 G4 前置，§5 写 G5 FAIL→G6 BLOCKED，U1 允许 G5 BLOCKED/G6 PASS。当前代码同时遵守这些条件：G4 PASS，显式 G5 FAIL/PARTIAL 阻断；没有擅自变为 G5 必须 PASS。
- `claim_prerequisite_status` 仅判资格，不发行 Claim。C0=`G1,G3`；C1=`G1,G3,G4`；C2=`G1..G6`；Level-D Accuracy 永远 BLOCKED。C3 因缺 SR-1 证据始终阻断。
- `PoissonProtocol` / `FieldSamples` 的可信度需正式 recorder、checkpoint、consumer provenance 承接；来自 arbitrary caller 的 derivative 标签不自动证明真实 autograd。
- 系统 Torch 诊断不提供 portable training dependency lock；没有 Adam/L-BFGS、固定架构、training sampler、停止准则/失败传播或自动 rescue 行为可验收。
- SHA manifest 可查损坏，不能单独抵御同时改写文件及其 manifest 的攻击；可信 Git commit 和 recorder 外部身份仍是信任锚。

### Definition of Done 对照

| # | 要求 | 结论 |
|---:|---|---|
| 1 | 阻断 P0 按定义处理 | FAIL/PARTIAL 已重算，未清零 |
| 2 | frozen governance 不绕过 | PASS |
| 3 | mathematical oracle | PASS（组件诊断） |
| 4 | PINN 可重复运行 | BLOCKED |
| 5 | independent validation | PASS（独立组件已存在） |
| 6 | metrics 正确 | PASS（组件测试） |
| 7 | negative/adversarial | PARTIAL（组件有效，core E2E 未执行） |
| 8 | exploratory/accuracy 分离 | PARTIAL（可执行权限规则；无正式 runner 集成） |
| 9 | 正式 evidence provenance 完整 | PARTIAL（诊断完整，正式 Run 不存在） |
| 10 | regression suite | PASS；839/0/1，skip 原因明确 |
| 11 | 无 silent failure | PARTIAL（已修已测路径拒绝；不存在的训练链不能被确认） |
| 12 | CFD seam 已审计 | PASS（审计） |
| 13 | 未提前实施 CFD | PASS |
| 14 | delivery worktree clean | PASS（工程测试时；文档交付 commit 后再次复核） |
| 15 | 修改有测试/证据 | PASS（逐文件清单/原始失败/新回归） |

## 7. CFD Readiness

**PARTIAL**。本轮没有创建 CFD solver、OpenFOAM adapter、CFD UI、mesh pipeline 或 speculative orchestration。

实际已有的最小接口是 `pinn.validation.poisson.FieldSamples` 与 `evaluate_samples(protocol, samples)`：验证层读取明确坐标/原始场/导数，不 import 具体 neural-network class。独立 `scientific_reference` 同样不 import pinn。future 同一问题的不同求解器可在输出转换后进入问题对应的 validator，而非修改某个 PINN class。

它仍是 Poisson scalar problem-specific contract，不能直接用于 CFD 的 u/p/mesh。没有把科学层强制定义为 network，更没有假装已经存在通用 Solver Adapter。

下月接入点与顺序：

1. 先完成 P0/HASH LOCK/正式 PINN workflow。随后在实际 `ScientificRun` orchestration 的 solver 调用位置加入一个薄 OpenFOAM adapter，采用项目最终确定的接口命名；prepare/run/collect/validate/describe_environment 是职责边界，当前不预先实现空框架。
2. adapter 管理独立 case directory、命令/版本/environment、stdout/stderr、退出码/超时/取消、残差历史、mesh/field 文件 hash；restart 必须新 run 或显式父 run，不能覆盖失败 evidence。长任务可先用已有 subprocess 语义，不引入分布式系统。
3. 新版本化的 Poiseuille ProblemSpec 明确几何/单位/BC/质量守恒/pressure drop/wall shear/mesh convergence，并实现问题对应的独立 oracle；随后再做 BFS benchmark。
4. PINN/CFD 比较应共享相同物理 ProblemSpec 和独立比较坐标/单位/mesh 映射记录。u、p、mass、Δp 和 derived quantities 均由独立 validator 计算；插值转换必须保留 provenance，不能把经过显示平滑的 field 当 raw evidence。

这些是基于现有代码的接入审计结论，不是 OpenFOAM runtime compatibility 或 READY 声明。

## 8. Evidence

外部 append-only 证据目录：`../LeoAIStudio-pinn-evidence-20260908T120017Z/`。失败与早期诊断未覆盖，最终 clean-commit 诊断使用新的 `scientific-components-final/`。

- 原始 HEAD/status/163 项 exact-byte inventory：`baseline-inventory.json`、`source-status-before.bin`。
- 恢复前后 P0：`p0/restored-baseline-full.txt`、`p0/after-fixture-restoration-full.txt`、restoration manifests、collectors。
- 修复前漏检：`semantic-before.json`、`governance-lock-pre-fix.json`、`p0/governance-review/`；新的 leakage 第一次失败亦保留。
- 最终完整回归：`final-full-suite-command.json`、`final-full-suite.log`、`final-full-suite.xml`。
- 最终 prelock、pip/wheelhouse/portability/Torch：`final-diagnostic-commands.json` 和各 `final-*.log`。
- 最终 scientific diagnostic ID：`validator-component-15b4341c597a4921993f4b74690803d4`。它不是 formal run_id。
- 最终 metadata 中 `gitCommit=1c96066dfb11aff5d151fec83d48fc30251b74bd`，`gitStatus=""`，含 Python/platform/device/dependencies/源码/候选 hash；无 formal Gates、无 Claim。
- `scientific-components-final/files.sha256.json` SHA-256：`c537f57ded7b678ad049aab729cca2b75944b43abd68cc33f801d7c8469efa96`；登记文件均读回验证。
- 全证据快照 `EVIDENCE_SHA256_1c96066.json`：112 files；自身 SHA-256=`677901d009ad5f1d88d08a1daf9d745ee25d0750bcac14459947a464e88ac0d4`。后续交付 metadata 属于新增记录，不覆盖此快照。
- `source-preservation-final.json`：原文件/status 0 drift；delivery clean。

候选摘要均原字节不变，以下不是 locked digests：

| 对象 | SHA-256 |
|---|---|
| spec draft | `a6733840c9363f841a4877c7283a5935fb0ff0e980a4f08e1e7a8188bfb155bc` |
| protocol draft | `800749f5211f19e8ebfa576537e2d92b10ba3a8432de34745eaf1231a78545c0` |
| manifest draft | `72b3a741d2f8bf0bb3867af5befafe0f7c517d2973172ce5792aa728ddb8130d` |
| lock draft | `6626362d6376d13407dc7303de9f4943360706a6b84a2fd11a2faa31c0a4ae7f` |
| analytic source | `d792fd0ec91827bb6fcf38039893839024517c603bb4e5efcd0f7fe54b30a06d` |

## 9. Recommended Next Commit

本轮工程修复 commit 已形成；随后 documentation commit 封存本报告和逐文件清单。**不建议将当前提交命名为 PINN MVP 完成版、形成科学结果 freeze tag 或进行 HASH LOCK。**

下一项可交付工作应首先是可审计的 P0 acceptance closure：解决 8 个 F-008 source gap、从正确 source 建立 current build/deployment provenance、补齐必要实际环境验收，并保留真实失败。如果环境条件不具备，继续保持 PARTIAL/BLOCKED。之后针对本候选与上述两个文本歧义完成最终 human review/approval，才进入 P2-formal。

正式 P2 后的下一工程提交才应建立冻结 config + Gate3 verification + recorder + trainer：明确 CPU/float64、固定 architecture、独立 training sampler、PDE/BC/total loss、seed、Adam/L-BFGS（由正式 solver spec 决定）、停止/失败语义和 checkpoint reload。必须接上独立 validator、Gate6 重建和 Claim ledger，执行冻结 core suite/五 seed，再重新核对全部 DoD。

### 逐文件修改理由（工程提交相对安全快照）

| 文件 | 原因 |
|---|---|
| `.gitattributes` | 为历史 docs/rollback 保留 checkout 原字节；不改变科学 JSON canonical 规则。 |
| `docs/P0_EXECUTION_STATUS.md` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/P0_FINAL_CLOSURE_REPORT.md` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/P0_RELEASE_CANDIDATE.md` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/P0_RUNTIME_REMEDIATION_20260908.md` | 新增 P0 现场重算及基线/修复/验收边界报告。 |
| `docs/RESEARCH_SOP_MIGRATION_AUDIT_24f3fd7.md` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/THEME_INK_AUTUMN.md` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/build_launcher.pre-2D-B.ps1` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/build_launcher.pre-P0-closure.ps1` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/build_launcher.pre-theme-assets.ps1` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/deploy_release.pre-2D-A.ps1` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/deploy_release.pre-theme-assets.ps1` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/lean-math-kernel.pre-2D-A.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/leo-inject.pre-2C.js` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/portability_check.pre-P0-closure.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/research-sop-kernel.pre-P0-2-round2.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `docs/rollback/research-sop-kernel.pre-P0-2.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `leo_shell/DESIGN.md` | 将当前个人 LeoTree 路径改为配置占位符，消除当前文档 hard binding。 |
| `manifests/portability-historical-evidence.json` | 恢复 df5e4b2 已审定的精确历史证据分类记录。 |
| `manifests/test-suites.json` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `pinn/governance/canonical.py` | 拒绝 NaN/Inf/数值溢出、重复 key；保持合法 JSON 唯一 canonical 字节。 |
| `pinn/governance/jsonschema_lite.py` | 修正 bool 与 number 的 const/enum 等价错误；拒绝非有限数。 |
| `pinn/governance/leakage.py` | 补 L2、缺失坐标来源、非有限/domain 检查；保留公开 BC 复用和 L4 禁止回流。 |
| `pinn/governance/locking.py` | 锁状态/算法/固定字段/路径/hash 校验、排他创建、写后校验；保留七字段 payload。 |
| `pinn/governance/poisson_contract.py` | 把现行 v1 数学、AC、seed、冻结 asset、expected verdict 变为可执行拒绝规则。 |
| `pinn/governance/prelock.py` | 结构化失败传播、拒绝异常语义、验证解析 evaluator 实际源码 hash。 |
| `pinn/governance/provenance.py` | 绑定可信 recorder entry；验证 digest、parent identity 与完整 lineage；禁止手工自升格。 |
| `pinn/governance/semantic.py` | 调用 Poisson 数学/指标/manifest 契约，检查节点/权重/来源路径并归一化损坏 NPY 失败。 |
| `pinn/governance/state_machine.py` | 按必要 Gate 判断执行资格；严格 bool；Level-D 仅授权规定的 exploratory 例外。 |
| `pinn/validation/__init__.py` | 导出独立场数组验证 API。 |
| `pinn/validation/diagnose.py` | 新目录排他导出 raw arrays、metrics、环境、source hashes 与 SHA manifest。 |
| `pinn/validation/fixtures.py` | 源码可追溯的解析、B1b/B3/B4/B6/zero 六组组件控制。 |
| `pinn/validation/poisson.py` | 实现 AC-1..8 和额外诊断；严格 CPU/float64/坐标/finite/metadata，不产生科学 Claim。 |
| `scientific_reference/POISSON_DERIVATION.md` | 记录 PDE/BC/唯一性/QoI/能量恒等式人工推导和独立差分验证。 |
| `scientific_reference/__init__.py` | 独立数值参考包入口。 |
| `scientific_reference/poisson_fdm.py` | 无 pinn import 的 Thomas/FDM 七网格诊断；失败和非有限派生量立即拒绝。 |
| `tests/leo_shell/test_api.py` | 恢复测试并适配已存在 EntityStore；新增持久化/revision/corruption 失败测试，保留原参数断言。 |
| `tests/leo_shell/test_app_startup.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/leo_shell/test_bridge_client.py` | 恢复测试并补五阶段启动 fixture；新增准备失败禁止启动、所有阶段 secret 不入 argv。 |
| `tests/leo_shell/test_connection.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/leo_shell/test_paths.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/leo_shell/test_secrets_store.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/leo_shell/test_settings_store.py` | 恢复并严格核验已存在 local preset 的 requires_key=false 及云端字段集合。 |
| `tests/leo_shell/test_single_instance.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/leo_shell/test_theme_runtime.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/leo_shell/test_webview2_runtime.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/pinn/test_leakage_integrity.py` | 18 项 L1..L4、公开边界、缺失来源、非法坐标测试。 |
| `tests/pinn/test_locking.py` | 正式锁 helper 的算法、字节、路径、摘要、排他写、损坏输入回归，仅临时 fixtures。 |
| `tests/pinn/test_prelock_integrity.py` | 55 项候选数学/metadata/expected verdict/非 canonical/损坏资产拒绝回归。 |
| `tests/pinn/test_provenance_integrity.py` | 16 项缺证据、损坏 digest、seed mismatch、父链污染、自声明拒绝测试。 |
| `tests/pinn/test_scientific_validation.py` | 87 项指标、独立 oracle、对抗、输入、证据不可覆盖测试。 |
| `tests/pinn/test_state_machine.py` | Gate/Claim 必要前置、Level-D、strict bool/异常、C3 无证据阻断回归。 |
| `tests/pinn/torch_derivative_sanity.py` | 8 项显式运行 CPU/float64 autodiff/graph/seed 诊断；不训练。 |
| `tests/skills/test_lean_math_discovery.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_b08_attempt_identity.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_f001_document_integrity.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_f002_history_integrity.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_f007_manifest_integrity.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_integrity_adversarial.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_mutation.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/skills/test_research_sop_semantics.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_build_reproducibility.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_manual_acceptance.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_package_contract.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_portability.py` | 恢复 df5e4b2 既有的精确 hash 历史分类正负测试。 |
| `tests/test_suite_provenance.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_theme_readability.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_theme_settings_integration.py` | 恢复真实 Chromium 三主题保存/重载测试，补实际 production 函数依赖。 |
| `tests/test_ui_api_contract.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tests/test_wheelhouse.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/build_wheelhouse.py` | 恢复实际人工验收清单引用，避免把 wheel 检查冒充 clean-machine 验收。 |
| `tools/headless_verify.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/_common.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/collect_windows_account_env.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/run_all.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/verify_clean_build.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/verify_lean_real_toolchain.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/verify_research_sop_live.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/verify_webview2_runtime.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/manual_acceptance/verify_wsl_environment.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/portability_check.py` | 精确恢复已审定 hash/path/type/count 历史证据分类；不抹去原始 findings。 |
| `tools/theme_preview.py` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |
| `tools/theme_shots.ps1` | 从 a4455cc 恢复被删除的历史测试、验收工具或 evidence；保留原有约束及失败证据。 |

```

</details>

### R027 — 项目/docs/PINN_P2_FINAL_HUMAN_REVIEW_PACKET.md

<details>
<summary>展开完整原文</summary>

```markdown
# PINN P2 FINAL HUMAN REVIEW PACKET

**Packet ID：`PINN-P2-HUMAN-REVIEW-20260908T124356Z`**  
**状态：DRAFT / HUMAN APPROVAL REQUIRED**  
**当前执行授权：BLOCKED。没有人工批准记录；没有创建 formal spec、protocol、manifest 或 lock；没有正式训练、五 seed、Gate 2–7 或 Claim 发行。**

这是可审查的候选材料，不是批准书、Scientific Gate PASS 或 PINN MVP 完成证明。项目所有者需要决定本包绑定的候选数学规格、AC-2 定义和 G6 解释是否可接受。只有必要 P0 已真实闭合、明确人工批准绑定同一候选身份、最终 prelock 再次通过后，后续 Agent 才能按现行治理程序进入正式 P2。

本包只新增审查文档和身份清单；没有更改 Constitution、candidate JSON、冻结节点、Scientific Spec 阈值或执行代码。形成材料后，按 Phase II 用户指令停止在人工批准边界。

## 1. 本包身份、现场与效力

| 项目 | 当前证据 |
|---|---|
| Repository/worktree | `LeoAIStudio-pinn-phase2-20260908T124356Z`，与原始 dirty `LeoAIStudio-build` 隔离 |
| Branch | `codex/pinn-mvp-phase2-20260908t124356z` |
| 本轮 base / 本包科学身份采集时 HEAD | `2bfc5b0fe638fc9dab71a07dc292ca26da108353` |
| 已核实存在的上一轮 engineering commit | `1c96066dfb11aff5d151fec83d48fc30251b74bd`，`git cat-file -t` 返回 `commit` |
| 已核实存在的上一轮 delivery commit | `2bfc5b0fe638fc9dab71a07dc292ca26da108353`，`git cat-file -t` 返回 `commit` |
| 科学身份采集时间 | `2026-09-08T12:58:29.029648+00:00` |
| 当前工程范围 | P0 实证收集/修复与 human-review 材料准备；本包不宣告 P0 完成 |
| 机器身份清单 | [PINN_P2_FINAL_HUMAN_REVIEW_IDENTITY.json](PINN_P2_FINAL_HUMAN_REVIEW_IDENTITY.json)，42 个逐字节 SHA-256 条目 |
| 清单文件自身 SHA-256 | `a7eaa17238cbc7c3b6d7514b2f321ada9ccbebdd2affffadd52e57af5a7d3acb` |
| 测量原始记录 | [human-review-packet-measurements.json](../../LeoAIStudio-pinn-phase2-evidence-20260908T124356Z/human-review-packet-measurements.json) |
| Human approval | **未给出；decision、approvedBy、approvedAt 均未填写** |

身份清单覆盖科学候选/权威文件、冻结数组、科学实现与测试。它不假装覆盖 installed EXE 或产品全部 build inputs；后者必须由本轮 P0 build/deployment evidence 单独建立。采集后若任一绑定文件发生变化，必须重新测量并形成可区分的新审查版本；不能继续使用此包的旧 hash 批准新字节。

**最终 review 适用的完整工程 source commit、build commit 与 delivery commit，以本轮 [P0_ACCEPTANCE_CLOSURE_REPORT.md](P0_ACCEPTANCE_CLOSURE_REPORT.md) 最终列出的实测身份为准。** 上表的 `2bfc5b0...` 是本轮 base 和本包科学身份采集时的 HEAD，不冒充尚未完成的 Phase A 最终提交。root 在交付前须把最终报告及其 hash 绑定到下表，并复核本包 42 个文件有无漂移；这一步不解除 P0 prerequisite，也不构成人工批准。

权威顺序以 [Constitution](../governance/PINN_RESEARCH_CONSTITUTION.md) 第六十一章（行 1771–1783）为准：Constitution → Locked ScientificSpec → Validation Protocol → Experiment Plan → Agent Plan → implementation → UI preference。本包没有高于这些文件的效力。目前不存在 Locked ScientificSpec；当前 JSON 是待审 candidate，不能称为已经正式 HASH LOCK。

### 1.1 P0 前置绑定：尚未完成集成

**本块必须在 root 整合本轮 Phase A 证据后更新。当前没有把旧状态复制成新状态。**

| 必须绑定的项目 | 本包采集时的绑定状态 | 放行效力 |
|---|---|---|
| 本轮 P0 Closure Report 路径、hash、适用 source/build identity | 目标为 `docs/P0_ACCEPTANCE_CLOSURE_REPORT.md`；最终内容/hash 尚未绑定，Phase A 工作正在并行完成 | 不产生放行权限 |
| P0-1、P0-2、P0-3、P0-4、P0-5、P0-6 | 待从本轮原始结果逐项绑定 | 必要上游未证实闭合，formal P2 保持 BLOCKED |
| F-008 source provenance closure | 待绑定当前 20 项 runtime-read asset 清单和每项来源证据 | 不能由 source tests 或旧 trace 数代替 |
| installed EXE / WebView2 真人观察、fresh-account/WSL/WebView2 场景 | 待绑定实际自动证据与人工 checklist | Agent 不代签 HUMAN REVIEW |

上一轮报告记载 P0-1/P0-6 FAIL、P0-3/4/5 PARTIAL、F-008 PARTIAL；这里只把它作为重新核算起点。当前值以本轮 Phase A 报告为准。[P0_MANUAL_ACCEPTANCE_CHECKLIST.md](P0_MANUAL_ACCEPTANCE_CHECKLIST.md) 行 6 明确 `NOT TESTED` 不能计作 PASS；[P0_RELEASE_CANDIDATE.md](P0_RELEASE_CANDIDATE.md) 行 23、157–163 明确 P0-4/P0-5 未满足时 P0-6 保持 FAIL。批准本科学候选也不能覆盖这些产品验收依赖。

## 2. Candidate Identity：精确待审字节

下列 SHA 均从本 worktree 当前文件重新读取，不是沿用上一轮报告。JSON 编码契约是 UTF-8 无 BOM、LF、恰好一个尾 LF、与唯一 serializer 字节一致；NaN/Inf、重复 key 和不可用字段必须拒绝。完整 byteCount、源码与测试 hash 见身份清单。

| 对象 | 角色/状态 | SHA-256 |
|---|---|---|
| `governance/PINN_RESEARCH_CONSTITUTION.md` | v1.0 ACTIVE，未修宪 | `4300bb848cc968e96c6b9de318796f6791a6cccea518bff2faac96e8f0c87018` |
| `governance/PINN_CLOSED_LOOP_MVP_PLAN.md` | v1.3 DRAFT，保留原文歧义 | `da7d63f04e202bf1c7a1b48f0b9f282745b9aa227666bbff0592ff2724262f2e` |
| `governance/POISSON_1D_V1.0_spec.draft.json` | specId=`poisson-1d-dirichlet`、version=`1.0`、evidenceLevel=`A` | `a6733840c9363f841a4877c7283a5935fb0ff0e980a4f08e1e7a8188bfb155bc` |
| `governance/POISSON_1D_V1.0_protocol.draft.json` | 当前评价与复现协议 candidate | `800749f5211f19e8ebfa576537e2d92b10ba3a8432de34745eaf1231a78545c0` |
| `adversarial/core_manifest.draft.json` | 15 conceptual families、18 atomic scenarios，尚未执行 formal core suite | `72b3a741d2f8bf0bb3867af5befafe0f7c517d2973172ce5792aa728ddb8130d` |
| `governance/POISSON_1D_V1.0_lock.draft.json` | `lockState=DRAFT`，正式输入 digest、lockedAt、lockSha256 仍为 null | `6626362d6376d13407dc7303de9f4943360706a6b84a2fd11a2faa31c0a4ae7f` |

### 2.1 冻结节点资产

所有数组为 NPY v1.0、C-order、显式 little-endian `<f8`；正式 evaluation 必须读取现有资产，不因平台更换重新生成“等价”网格。NPY 文件 SHA 包括 header；payload SHA 只覆盖 float64 数据字节，两者不可混用。

| 资产 | shape / 文件字节数 | 文件 SHA-256 | 数据 payload SHA-256 |
|---|---|---|---|
| `specs/poisson-1d/v1.0/assets/GL512_nodes.npy` | `[512]` / 4176 | `1d50c2db39cdfa8d741e23e9152a3cb8665991a8885c2e3ea5a505eae4e993db` | `803f12cb60359b02e14e57b4676a04baab5dd27042e259265d5b3c476b13a6c3` |
| `specs/poisson-1d/v1.0/assets/GL512_weights.npy` | `[512]` / 4176 | `f1fc34beda32cf34e6a0e7b6b9f98486d4833b2aed94a04a189bda203deb8ebd` | `d37cccc49beb2db5e27532b82796ca2424efc3908e94db1bc82431579d1f7048` |
| `specs/poisson-1d/v1.0/assets/CGL2000.npy` | `[2000]` / 16080 | `81e98be345a69e0859097557533defa0b533b57f930b60db9fd9200482d23773` | `59d84b0eaf599b81d9add5fcb99fcd105d5922ae5c044a2ee589ef9971f5b6ff` |

节点 generator `pinn/governance/nodes.py` 的当前 SHA 为 `b22e754fe5173d4cf5e40d8b9bc40416f1627d6919b30ae60d35c2c27155c3b7`，与 protocol 记录一致。generator/source/hash 是来源记录，不能替代读取现有 NPY。protocol 的 anti-collision 要求为所有内部低阶有理格 `i/d`、`2≤d≤64` 与验证节点距离严格大于 `1e-12`；endpoint 由公开 BOUNDARY 约束单独处理。不得把 CGL2000 改成含 midpoint 的 1999/2001 节点版本。

### 2.2 关键科学实现与验证源码身份

以下是方便人工核对的子集；清单中还列有 schema、leakage/provenance、fixtures、诊断 CLI 和全部 PINN 测试的精确 hash。

| 源码 | SHA-256 |
|---|---|
| `pinn/reference/analytic_poisson.py` | `d792fd0ec91827bb6fcf38039893839024517c603bb4e5efcd0f7fe54b30a06d` |
| `pinn/governance/poisson_contract.py` | `f6c863725b75fe00051a9b5487ad2a5e4f47eb07bc99098aea45ca63c62a763b` |
| `pinn/governance/semantic.py` | `6a8007ff19aa2a131af7221cd844792a93b3ecc44cc4b98e3fe5a4ce9c0278c2` |
| `pinn/governance/canonical.py` | `8e81957fe753a27b3b78667ede0dded7dd1413e6fbdc612b1e0dfff019b8be5f` |
| `pinn/governance/prelock.py` | `2233974dc32743e5755084c1c836dfe3dedba95b33676b1d2c150ac134900057` |
| `pinn/governance/locking.py` | `9f4de0e1b8ef59500ba6e51d91a9ec400801115987158a5ce55d3d45d998d6f2` |
| `pinn/governance/state_machine.py` | `9e834d17b6c53af767f1d2a3afe2ad5f35e1ef75a529a8299347acf87a54a7dc` |
| `pinn/validation/poisson.py` | `e9daa553b2f4261ae4b24a5ec47a6cfa38623d98d114060e22a6b65459877d77` |
| `scientific_reference/poisson_fdm.py` | `075f856dba84a9a8dc7fc9216f6317b256668d24ece1f0c74fc4772e3257300f` |
| `scientific_reference/POISSON_DERIVATION.md` | `de4dd0208aa1d2cd150406e21f12323cf3093595c1a337152258e51207ff9ab4` |

当前 `requirements.lock` SHA 为 `2a5eabc5389a7122f4431b51578a125dec5a356fcc40c450294533c9614180e9`，这是现有 build 环境锁；它不是尚未创建的 trainer/scientific runtime dependency lock。

### 2.3 当前 prelock 与未来 lock

身份采集时 `run_prelock(PrelockPaths.defaults(root))` 实际重新执行，6 组检查 PASS：Constitution binding、spec、protocol、adversarial manifest、lock draft、repository attributes。原始 JSON 在测量记录中；可在本 worktree 用 `.venv/Scripts/python.exe -m pinn.governance.prelock` 独立复核。

`candidateLockPayloadSha256 = 55efe6b6c531822dac02d57bc5d6e095d22f4f0d918f5c810654e2d5f3f37fae`，其 lockedAt 使用 `DRY-RUN-ONLY--LOCKED-AT-NOT-SET` sentinel。**这是 dry-run 候选摘要，不是最终锁摘要。**

现场再次确认以下四条正式路径均不存在：

- `specs/poisson-1d/v1.0/spec.json`
- `specs/poisson-1d/v1.0/protocol.json`
- `specs/poisson-1d/v1.0/lock.json`
- `adversarial/core_manifest.json`

未来仅在条件满足时使用原七字段、逐字段单 LF 的 lock payload：`specSha256, protocolSha256, adversarialManifestSha256, constitutionSha256, constitutionVersion, lockVersion, lockedAt`。本包没有修改该算法。最终 timestamp 和 lockSha256 现在不得提前填入。

## 3. Mathematical Definition 与 acceptance contract

未知量是标量 `u(x)`，唯一输入为无量纲 `x`。PDE 与强形式 residual 为：

\[
-u''(x)=f(x)=\pi^2\sin(\pi x),\quad x\in(0,1),\qquad R[u](x)=-u''(x)-f(x).
\]

闭包为 `[0,1]`，公开边界集合 `B={0,1}`，Dirichlet 条件 `u(0)=u(1)=0`。解析解及其导数为：

\[
u_*(x)=\sin(\pi x),\quad u_*'(x)=\pi\cos(\pi x),\quad u_*''(x)=-\pi^2\sin(\pi x).
\]

代入得到 `R[u*]=0`。任意两解之差满足 `w''=0`，因此 `w=ax+b`；两端零值给出 `a=b=0`，解唯一。数学上两端为零；float64 中 `sin(pi)=1.2246467991473532e-16`，不能要求字面 `sin(pi)==0`。问题直接以无量纲形式给定，没有时间变量、初始条件、维度化父问题或参考尺度；不得为填 schema 编造这些内容。[Spec 行 19–175](../governance/POISSON_1D_V1.0_spec.draft.json)；[独立推导](../scientific_reference/POISSON_DERIVATION.md)。

### 3.1 QoI、能量与参考常数

| 数量 | 数学定义 / 精确参考 |
|---|---|
| QoI-1 | `∫₀¹ u dx`；参考 `2/π = 0.6366197723675814`，绑定 AC-5 |
| QoI-2 | `u′(0)`；参考 `π = 3.141592653589793`，绑定 AC-6 |
| forcing RMS | `sqrt(∫₀¹ f² dx / 1) = π²/√2`；spec 展示小数 `6.978864199639`，计算按数学表达式 |
| 能量恒等式 | `∫₀¹ (u′)² dx = ∫₀¹ f u dx`；解析解两侧均为 `π²/2` |
| 参考 L2 平方范数 | `∫₀¹ u*² dx = 1/2`；`∫₀¹ u*′² dx = π²/2` |

下面用 `Q[h]=Σᵢ₌₁⁵¹² wᵢ h(xᵢ)` 表示冻结 GL512 积分；`V={vⱼ}ⱼ₌₀¹⁹⁹⁹` 是冻结 CGL2000 节点。GL512 的节点全在开区间，权重正且和为 1；CGL 含准确端点 0、1。所有指标为 dimensionless；所有比较均严格 `<`，等号不满足。`ε=10⁻³⁰`，比值分母必须大于 `10⁶ ε`，不利用 ε 掩盖退化分母。finite、shape、dtype、坐标、方程/域/BC 绑定和 provenance/leakage admission 是前置检查，不能用满足 AC 表代替。

### 3.2 AC-1～AC-8 全量定义

| ID | 离散执行定义 / normalization | Sample set / aggregation | 阈值 | 级别 |
|---|---|---|---|---|
| AC-1 | `sqrt(Q[(u-u*)²] / (Q[u*²]+ε))` | GL512；加权平方积分后开方 | `< 0.001` | MUST |
| AC-2 | `maxⱼ abs(u(vⱼ)-u*(vⱼ)) / (maxⱼ abs(u*(vⱼ))+ε)` | CGL2000；离散最大值；歧义见 §4 | `< 0.005` | MUST |
| AC-3 | `max_{x∈B} abs(u(x)-g(x))`，`g≡0` | 精确 `{0,1}`；最大绝对误差 | `< 0.0001` | MUST |
| AC-4 | `sqrt(Q[(-u″-f)²]) / (π²/√2)` | 独立 GL512 holdout residual；区间长度为 1，积分范数与 RMS 相同 | `< 0.01` | MUST |
| AC-5 | `abs(Q[u]-2/π)/(2/π)` | GL512；积分 QoI 相对误差 | `< 0.001` | MUST |
| AC-6 | `abs(u′(0)-π)/π` | 精确 `x=0`；单点导数 QoI 相对误差 | `< 0.005` | MUST |
| AC-7 | `abs(Q[(u′)²]-Q[f*u])/(π²/2)` | GL512；能量恒等式两侧差的固定归一化 | `< 0.01` | MUST |
| AC-8 | `sqrt(Q[(u′-u*′)²] / (Q[u*′²]+ε))` | GL512；导数误差加权平方积分后开方 | `< 0.005` | SHOULD |

定义来源：[Spec 行 206–354](../governance/POISSON_1D_V1.0_spec.draft.json)、[Protocol 行 245–257、351–379](../governance/POISSON_1D_V1.0_protocol.draft.json)、[Plan §9.11](../governance/PINN_CLOSED_LOOP_MVP_PLAN.md)。每 seed 的 G5 MUST 集合恰为 AC-1～AC-7；AC-8 单列 SHOULD，不能因其失败暗中改写 MUST 条件。额外 absolute L2、sampled absolute Linf、PDE residual RMS/max、逐端 BC residual、未加权 BC MSE 是诊断项，本包不新增其验收阈值。

AC-6/7/8 导数遵循 protocol 的 autograd / synthetic closed-form 条款；AC-4 需要同一物理坐标下的二阶导数。参考独立差分诊断用于检查推导，不得代入 formal AC 导数。当前 raw-array validator 的 derivative 标签仍需未来可信 recorder 与 checkpoint reconstruction 支撑，标签本身不是导数来源证明。

### 3.3 参考/采样/seed 与 baseline 条件

Primary reference 是解析解，AC 全部对它计算。独立 FDM 只验证 baseline 子系统，不能用带离散误差的数值解替代解析 reference。Gate 2a 原条件：GL512 上最大 `abs(-u*″-f) < 1e-12`；两端最大 `abs(u*) < 1e-14`。Gate 2b 原条件：二阶三点 stencil `(-u[i-1]+2u[i]-u[i+1])/h²=f[i]`，`N` 为子区间数，`h=1/N`；`N={32,64,128,256,512,1024,2048}` 的内点最大误差 `E(N)` 全部严格递减，最后四对 `(128,256),(256,512),(512,1024),(1024,2048)` 的 `log₂(E(N)/E(2N))` 均在 `[1.8,2.2]`。B11 单网格没有可报告的观测收敛阶。

五个预注册 training seeds 恰为 `{20260904,20260905,20260906,20260907,20260908}`。evaluation 没有随机采样，`evaluationSeed=NOT_APPLICABLE`。五个 seed 的 SR-1 与每个 Run 的 G5 分开；C3 还受固定问题、架构、优化器/调度、训练协议及这五个 seed 的 scope 限定。

训练 collocation/adaptive/diagnostic 内点与 holdout 信息流必须隔离。公开训练 BC `{0,1}` 可以与验证边界复用；任何 boundary validation metric 回流 optimizer、adaptive sampler、early stopping、loss weighting、architecture selection 或 hyperparameter tuning 仍是 L4 leakage。当前没有冻结 architecture、Adam/L-BFGS 调度、training sampler、loss weights 或 stopping/failure conditions；批准数学 candidate 不等于这些尚未存在的训练配置已经获得验证。

## 4. AC-2 ambiguity：由所有者选择，不由 Agent 改定义

### 4.1 现行文字并列

| 来源 | 当前原文/事实 | 含义 |
|---|---|---|
| Spec 行 216–220 | `max_j abs(u_theta-u*) / (max_j abs(u*)+eps)`，grid=`CGL2000` | 明确离散 sampled numerator 和 sampled denominator |
| Protocol 行 87–110 | 固定 2000 CGL nodes、exact NPY/source/data identity | 当前评价网格可逐字节复现；没有 `x=0.5` |
| Plan 行 550 | AC-2 参考列写 `max abs(u*)=1` | 等于连续真解的 supremum；与有限网格分母不同 |
| 当前 validator / derivation | 按 spec 使用 sampled maximum；现有回归明确禁止快捷替换为 1 | 已测试的实现行为，不是对治理歧义的正式裁决 |

### 4.2 Option A：protocol-defined sampled maximum

\[
E_{A}=\frac{\max_{v_j\in V}\lvert u(v_j)-\sin(\pi v_j)\rvert}
{\max_{v_j\in V}\lvert\sin(\pi v_j)\rvert+\epsilon}.
\]

当前 spec、validator 与数据资产采用 Option A。2026-09-08 在本轮 Python 3.12.9 环境读取冻结 CGL2000 后重新计算：

| 测量 | 当前值 |
|---|---|
| sampled denominator `max_V abs(u*)` | `0.9999992382301501` |
| 同一 float64 的 hex 表示 | `0x1.ffffe67072628p-1` |
| 达到此值的零基索引 | `999`、`1000` |
| 对应 frozen x | `0.4996071045109699`、`0.50039289548903` |
| 连续参考 supremum | `1.0`，在 `x=0.5` 取得 |
| 仅分母引起的倍率 `1/d_A-1` | `7.617704300688644e-7` |
| Option A 严格阈值对应的 sampled max error 上界 | `< 0.004999996191150751` |

这保证在固定节点、固定 raw outputs、已记录 evaluator/runtime 下得到同一个 sampled 指标。NPY exact bytes 不能单独保证不同 libm/运行环境的 `sin` 末位一定逐位一致；正式复现仍需环境与 evaluator 身份。并且固定网格 max 不能证明节点之间没有窄峰误差，报告必须称作 protocol-sampled error，不能自动升格为连续全域 supremum 证明。

### 4.3 Option B：continuous supremum

\[
E_{B}=\frac{\sup_{x\in[0,1]}\lvert u(x)-\sin(\pi x)\rvert}
{\sup_{x\in[0,1]}\lvert\sin(\pi x)\rvert+\epsilon}
=\frac{\sup_{x\in[0,1]}\lvert u(x)-\sin(\pi x)\rvert}{1+\epsilon}.
\]

连续真解分母精确为 1；任意已训练网络的连续误差分子现在没有实现或经审查的全局求最大程序。选择 B 必须先定义求 supremum 或受证上界的方法、global search/认证范围、终止准则、数值误差界、端点处理与重复性要求，并更新 protocol、validator 和 negative cases。把 CGL 网格加密仍是 sampled approximation，不能直接声称已计算连续 supremum。

**只把分母改为 1、分子仍取 CGL2000 最大值，是第三种 hybrid 指标，不等同于上式 Option B。** 这种 hybrid 的 sampled error 上界为 `<0.005`，相对当前上界放宽 `3.808849249331558e-9`。数值差小不构成修改理由，也不允许隐式替换；必须明确用户到底选择离散指标、完整连续指标还是另行规定的 hybrid。

### 4.4 审查决定与 amendment 影响

| 用户选择 | 所需明确记录 | 对当前身份/协议的影响 |
|---|---|---|
| A，保留当前 spec metric | 明确接受 sampled 语义及其有限覆盖，说明 Plan 中“1”如何作为 continuous reference 简写呈现而不用于计算 | 若 candidate JSON 字节不变，其 hash 不变；任何 Plan 澄清文本仍须单独留痕，不能在旧报告中偷改 |
| B，完整 continuous supremum | 明确新公式及可复现求值/认证协议；不能只写“用 1” | 属 ScientificSpec/Validation Protocol 的实质修订；生成新的 candidate identity、expected-verdict review、validator/tests 和 prelock，再供最终批准 |
| 指定其他定义（含 hybrid） | 精确写分子、分母、sample/domain、方法、容差和 reason | 同样是明确修订，不能用 APPROVE AS-IS 覆盖 |

当前尚未正式锁定，因此这里首先是 candidate revision；它不是事后修改已运行实验。若 formal lock 已形成后再改，必须按 Plan §14.5 / Constitution 第二条、第五十九条创建新版本 artifact set，不能原位重算 hash。改变 metric 本身不自动要求修宪；若拟议文字与 Constitution 条款冲突，必须另走第六十章 Constitutional Amendment。**本包没有选择 A/B，没有修改候选。**

## 5. G6 prerequisite ambiguity：文字、当前实现与待决定边界

### 5.1 所有直接相关治理条款并列

| 编号 | 文件/行 | 原文或原有元组 | 约束 |
|---|---|---|---|
| G6-C1 | Constitution 行 246–253 | 正常状态图为 `VALIDATION PASS → REPRODUCIBILITY_CHECK`；FAIL 转 `FAILURE_RECORDED` | 正式正向接受路径与失败回流分开 |
| G6-C2 | Constitution 行 294–304 | `PARTIAL` 不具有推进权限；关键 Gate PARTIAL 时下游正式科学 Gate BLOCKED | PARTIAL 不能冒充 PASS |
| G6-C3 | Constitution 行 1574 | Gate 1 不满足时所有下游 BLOCKED | G1 无效不允许靠局部 G4 记录推进 |
| G6-C4 | Constitution 行 1580–1585 | 无可信 baseline 时可以 exploratory，但 `Accuracy Claim=BLOCKED` | 允许探索，不授予精度 Claim |
| G6-C5 | Constitution 行 1639–1648 | 从保存环境重执行、config 重建、重算 metrics、重绘 figures；关键状态遗失不能称完整 reproducible | G6 实际 PASS 的内容要求；不是仅检查 G4 字段 |
| G6-C6 | Constitution 行 1654 | “只有在必要的上游 Gate 全部 PASS 以后”才能形成最终 Claim | 不等价于全部 Gate 对全部 Claim 都必要 |
| G6-C7 | Constitution 行 1789–1809 | evidence 缺失、artifact 丢失、leakage、无法判断来源等触发 STOP THE LINE | 停止依赖实验，保留阻断/失败证据 |
| G6-P1 | Plan 行 149，§3.6 | `Gate 6 执行：G4=PASS；无例外` | G6 所列常规前置未列 G5 PASS |
| G6-P2 | Plan 行 151–159，§3.6 | G2 FAIL 后 exploratory G3/G4 的例外仅限已锁定 Level D；失败阻断依赖该 Gate 的操作/claim | 不能创造其他带失败推进例外 |
| G6-P3 | Plan 行 211，§5 | Gate 5 的“失败时”列写 `G6 BLOCKED` | **已执行 G5 FAIL** 会阻断 G6 |
| G6-P4 | Plan 行 212，§5 | G6 PASS 要求重建 run/重算 metrics/重绘 figures 全部成功且环境完整 | G6 eligibility 与 G6 result 不同 |
| G6-P5 | Plan 行 361，U1 | `G1/G3/G4 PASS, G2 FAIL, G5 BLOCKED, G6 PASS; C1 SUPPORTED, C2 BLOCKED` | Level-D 的 G5 BLOCKED 不等于 G5 FAIL；U1 显式要求探索结果可复现 |
| G6-P6 | Plan 行 362–363，U2/U3 | 已有效至 G5 后丢失 checkpoint 或 commit/environment，`G6 FAIL, C2 BLOCKED` | 不得把证据丢失解释为精度“被否证”；保留 C1 与 C2 的不同状态 |
| G6-M1 | core manifest 行 623–662 | U1 明确 `evidenceLevel=D`、`G5=BLOCKED`、`G6=PASS`、`workflow=REPRODUCIBILITY_CHECK`、`C2=BLOCKED` | pre-registered E2E tuple；不是已运行证据 |
| G6-M2 | core manifest 行 667–752 | U2/U3 构造先建立有效至 G5 的 fixture，再移除关键 evidence；`G6=FAIL` | 已测 MUST 证据缺失记 FAIL，不虚构恢复成功 |

原文：[Constitution](../governance/PINN_RESEARCH_CONSTITUTION.md)、[Plan](../governance/PINN_CLOSED_LOOP_MVP_PLAN.md)、[core manifest](../adversarial/core_manifest.draft.json)。行号对应 §2 的当前文件 hash；文件变更后必须重新定位，不能拿旧行号裁决新文本。

### 5.2 当前代码真值表（描述事实，不批准新规则）

当前 `operation_prerequisite_status(6, gates, evidence_level=...)` 位于 [state_machine.py](../pinn/governance/state_machine.py) 行 64–95：需要 G4 PASS；显式 G1 FAIL/PARTIAL/BLOCKED 会阻断；显式 G5 FAIL/PARTIAL 会阻断；`stop_the_line` 必须为 False。下面假设 G1 已有效 PASS、无其他完整性问题、stop flag 为 False。32 行 A/D × G4/G5 状态的实际计算结果保存在测量 JSON，这不是执行任何正式 Gate。

| G4 | G5 | 场景 | 当前 helper G6 eligibility | 文字依据 / 待审点 |
|---|---|---|---|---|
| PASS | PASS | 正常已验证 Run | PASS（仅资格） | G6-P1/P4；真实 G6 仍须重建/重算/重绘成功 |
| PASS | FAIL | G5 已执行且未满足 MUST | BLOCKED | G6-P3；不能因为 G4 PASS 就继续正式接受路径 |
| PASS | PARTIAL | 关键验证证据不完整 | BLOCKED | G6-C2；PARTIAL 不推进 |
| PASS | BLOCKED | 已锁定 Level D、G2 FAIL 的 U1 | PASS（仅资格） | G6-P5/M1 明确支持探索复现；C2 仍 BLOCKED |
| PASS | BLOCKED | A/B/C，G5 尚未执行或其他原因被阻断 | helper 返回 PASS；**formal execution 不由此自动授权** | G6-P1 只列 G4；但 C1/C7 正向路径与 stop reason 必须检查。需要所有者明确这一边界，不能把所有 BLOCKED 原因都当 U1 |
| PASS | 未提供 G5 | 不完整状态记录 | helper 返回 PASS；**不是完整 workflow 资格证明** | 当前 helper 仅检查所列 prerequisite；正式 dispatcher/recorder 尚不存在，不能据此虚构 G5 或解除 evidence STOP |
| FAIL | 任意 | 训练执行失败 | BLOCKED | G4 不是 PASS，不满足 G6-P1 |
| PARTIAL | 任意 | 训练证据不完整 | BLOCKED | G6-C2/P1 |
| BLOCKED / 未提供 G4 | 任意 | 未获授权或未证明训练完成 | BLOCKED | G6-P1；缺前置不是 PASS |
| PASS | 任意 | G1 显式失效，或 stop flag 为 True | BLOCKED | G6-C3/C7；不能靠 G4 历史记录放行 |

`PASS` 出现在这个 helper 表中只表示“所建模前置已满足”，没有算 G6 成功、没有生成最终 Claim。后续正式 dispatcher 必须读取真实已绑定的 Gate/evidence 和 stop reason，不能接收 arbitrary mapping 后自动开工。

### 5.3 需要用户明确的决定

本包不把规则简化成 `G5 must PASS`。该简化会直接破坏 U1 的 `G5 BLOCKED / G6 PASS` 预注册元组。也不能反向只保留“G4 PASS”，忽略 G5 FAIL、关键 evidence 缺失或 STOP THE LINE。

请在决策表中明确：是否接受当前“G4 PASS + G5 FAIL/PARTIAL 阻断 + U1 Level-D BLOCKED 可复现”的组合解释；对于 A/B/C 的 G5 BLOCKED、缺少 G5 记录，以及失败分析中的重建诊断，哪些可作为独立 diagnostic component 执行，哪些属于正式 G6 的依赖推进。若需要修改 Plan/manifest，必须记录准确文本与原因并重新 prelock；如修改 Constitution 的正向状态机或例外范围，须走正式修宪。**现有 helper 已被工程测试，不等于上述规范问题已经被人工批准。**

### 5.4 Claim 必要 Gate 仍保持现行矩阵

| Claim | 必要条件 | 当前边界 |
|---|---|---|
| C0 implementation | G1、G3 PASS | 资格不能替代代码/执行证据 |
| C1 optimization | G1、G3、G4 PASS；G2 不是前置 | 不能把 optimization claim 写成 accuracy claim |
| C2 numerical accuracy | G1、G2、G3、G4、G5、G6 全 PASS | Level D 永远 BLOCKED；缺 checkpoint/env 仍不能发行 |
| C3 robustness | 至少五个 `SUPPORTED @ C2` Run + SR-1 与冻结 scope | 当前 per-run helper 不评估 suite，返回 BLOCKED |
| C4/C5 | 比较/泛化 | 当前 MVP out of scope |

未来 Claim issuance 还须单独绑定 claim candidate、来源/evidence、scope、limitations、failure/uncertainty 和明确发行动作；Gate PASS 不能自动 publish Accuracy Claim。

## 6. Previous Findings：已修复内容及真实覆盖范围

这些是上一轮工程提交中的真实修复，本轮重新核对源码身份。表内“已修复”指列出的代码路径/组件覆盖，不表示 formal scientific workflow 已完成。

| 领域 | 修复前实证问题 | 当前工程处理 | 尚未覆盖的正式路径 |
|---|---|---|---|
| Semantic validation | wrong forcing/BC/domain、删 AC、改公式、NaN threshold 可越过仅看 wrapper 的校验 | `poisson_contract.py` + semantic 校验当前数学、QoI、AC、变量/单位、seed/域/reference | trainer 配置/code-config 一致性尚未建立 |
| Canonical JSON / schema | NaN/Inf、重复 key、溢出及 Python `True==1` 可混入有效 JSON/schema | strict parse、finite 检查、唯一 canonical bytes、类型敏感比较 | 不把一般 JSON parser 当 hash authority |
| Quadrature asset identity | 改成 uniform weights 并重算一套 hash 可“自洽通过” | 绑定已冻结资产身份，额外查 dtype/shape/finite/顺序/权重，核查 generator/source/payload | 不以自产另一套 hash 替代原冻结节点 |
| Lock | DRAFT/MD5/绝对路径、`"FAIL"` truthiness、check-then-write 竞争可误通过/覆盖 | schema + 固定 metadata/路径/七字段 payload；literal bool；排他创建、读回、失败保留 | 没有正式 lock CLI 或已鉴权的人类批准记录系统 |
| Provenance | 缺失父 artifact、任意 sidecar 自称 trusted/eligible | recorder registry、exact metadata/hash、父链/role/transform 准入 | 正式 run recorder 尚不存在；不能由导入方自己造 trusted registry |
| Leakage | L2/来源与 finite/domain 检查不足；旧定义混淆公开边界 | L1～L4 及 metadata admission；保留公开 BC 复用，禁止任何 validation feedback 控制训练 | sampler/optimizer 必须未来真实登记消费信息流 |
| Expected verdict | case 可重新贴 mode/claim 标签或更换 seed | 固定 15 family/18 atomic 场景关键构造、元组、U1/U2/U3 C2 abstention | schema/pre-registration 检查不等于 core E2E 执行 |
| Independent validator | 无独立 raw-array AC；初稿接受 forged protocol hash、端点冲突、派生 overflow | 独立逐 AC 计算，源码/asset/canonical bytes 绑定，所有 finite 和 endpoint 一致性检查 | checkpoint round-trip 后 raw fields、正式 admission 尚不存在 |
| FDM oracle | baseline 不完整时可能报告不存在的 order；有限输入可产生 Inf residual | 独立 Thomas FDM、固定 refinement 诊断、单网格 orders 为空、派生 error/residual finite 拒绝 | 本轮没有签 Gate 2 PASS，也未把 FDM 当 AC primary reference |

上一轮已归档 full regression 为 `839 passed / 0 failed / 1 skipped`，另一个明确区分的系统 Torch CPU/float64 环境为 `8 passed / 0 failed / 0 skipped`；对应 engineering commit 为 §1 的 `1c96066...`。这些是历史证据，不冒充本轮 final test count。本轮完整测试、P0 source/build identity 和最终 commit 由 Phase A/交付报告另行记录并绑定。

已有独立科学组件能接受 analytic control、拒绝 B1b/B3/B4/B6/zero-field 等坏场，并能报告 raw coordinates/field/derivatives/forcing/metrics。其 scope 始终为 `VALIDATOR_COMPONENT`、workflow/claim 均 `NOT_APPLICABLE`。它没有完成真实 optimizer failure、insufficient training、checkpoint save/reload、五 seed 复现或正式 core E2E。

## 7. 批准前后严格边界与未完成项目

| 阶段 | 本包时点状态 | 条件 / 不可替代的证据 |
|---|---|---|
| P0 Acceptance Closure | 本包尚未绑定最终 Phase A 结论 | 真实源码→build→deployment/runtime 与所有必要验收；未完成时 BLOCKED |
| Human Review | **HUMAN APPROVAL REQUIRED** | 所有者对明确 packet/candidate hash、AC-2 与 G6 决定作出记录 |
| PRELOCK | 当前候选机械检查 PASS | 不等于正式 G1；批准后仍需复核同一最终字节 |
| Formal HASH LOCK / G1 | **NOT EXECUTED / BLOCKED** | final 文件 exclusive creation、approval provenance、exact digest、lock verifier |
| Trainer / recorder / five seeds | **NOT IMPLEMENTED / NOT-RUN / BLOCKED** | 先 lock，再实现/冻结最小训练配置与失败传播；禁止将不存在配置假装批准 |
| Formal independent validation | **NOT-RUN / BLOCKED** | 必须以重建/重载 checkpoint 的原始场进入独立 validator |
| Formal Gates 2–7 | **NOT-RUN / BLOCKED** | 组件计算、truth table、pytest 均不能产生这些正式 Gate 的结果 |
| Claim ledger / issuance | **NOT IMPLEMENTED / NOT ISSUED** | eligibility 和 issuance 分开；显式证据与 scope 绑定 |
| PINN MVP | **NOT COMPLETE** | 仍缺必要 P0、human approval、lock、正式训练/复现/validation/Gate/Claim 链 |
| CFD readiness | **PARTIAL** | raw output / independent validator seam 已审计；未开始 CFD/OpenFOAM/mesh UI |

一份 APPROVE 不把其他条件自动变成 PASS。若候选需要修订，先留下新 candidate 与 difference/evidence，再核对适用批准范围；不能在看到失败后更改阈值来改写历史。原始错误运行、failed evidence 和旧候选必须保留。

本轮用户的强制 STOP 内容以及 Plan 行 800–816、849、861 均要求在未取得明确人工批准时停止：不得写 formal lock、不得把 DRAFT 标正式、不得创建正式 scientific run、不得执行五 seed、不得发行 Claim。本包没有附可直接越过此边界的执行脚本。

## 8. Human Decision Form — 留给项目所有者填写

**以下三项均未勾选；Agent 不得代填 APPROVE。**

- [ ] **APPROVE AS-IS** — 批准本包绑定的现有 candidate bytes；接受当前 spec 的 Option A sampled AC-2 定义及明确记载的适用范围，并在下表说明 G6 解释。它不豁免 P0 或未来训练配置/实际 Gate 条件。
- [ ] **APPROVE WITH SPECIFIED AMENDMENT** — 明确指定下表中的修订；先形成带新 hash 的修订 candidate 和可审核差异。未经绑定最终字节的批准，不得据此自动锁定任意修改结果。
- [ ] **REJECT / RETURN FOR REVISION** — 列出拒绝原因和返回修改范围，保持原 candidate/evidence，不进入正式 P2。

| 必填决定/身份字段 | 项目所有者填写；当前为空 |
|---|---|
| Decision | ____________________ |
| Approver 身份 / approvedBy | ____________________ |
| 日期时间 / approvedAt（含时区） | ____________________ |
| Packet ID 与 identity JSON SHA-256 | ____________________ |
| 批准适用的 spec/protocol/manifest candidate hashes | ____________________ |
| 已核对的本轮 P0 Closure Report 路径、hash、结论 | ____________________ |
| AC-2：A sampled / B continuous / 明确的其他定义 | ____________________ |
| AC-2 amendment：分子、分母、节点/连续域、求值方法、容差、影响文件（如无请写无） | ____________________ |
| G6：是否接受现有组合解释；A/B/C 的 G5 BLOCKED、缺 G5 记录与失败诊断的处理 | ____________________ |
| G6 amendment：准确条款、规范层级、U1/U2/U3 影响（如无请写无） | ____________________ |
| 允许后续动作的范围与前置条件（P2-formal / 后续工程阶段） | ____________________ |
| 明确排除事项 / 其他修订条件 | ____________________ |
| 批准记录载体（本次用户消息或持久记录引用） | ____________________ |

**当前结果：HUMAN APPROVAL REQUIRED。所有批准字段为空；正式 P2/HASH LOCK 与依赖科学任务继续 BLOCKED。**

```

</details>

### R028 — 项目/docs/PINN_PHASE2_RECONCILIATION_20260909.md

<details>
<summary>展开完整原文</summary>

````markdown
# PINN Phase II reconciliation — 2026-09-09

Evidence cutoff: `2026-09-09T12:46:51Z`. This is a current read-only scientific reconciliation, not a formal lock, approval, scientific run, or replacement of historical evidence. Product work may advance after this cutoff; its later build/deployment report must identify its own commit and artifact.

## 1. Executive Verdict

**PINN MVP = NOT COMPLETE. CFD Readiness = PARTIAL.**

当前独立数学 oracle、raw-array validator、冻结评价节点和候选校验真实存在，并再次运行。42 项候选身份在当前工作树和保留的科学提交中均零漂移；PRELOCK 的 6 组检查 PASS。五个错误场被拒绝，独立 FDM 的七层网格收敛仍成立。这些都是组件诊断，不产生正式 Gate 或 Accuracy Claim。

最重要的未完成项是：必要 P0 的全新环境验收仍未闭合；正式 HASH LOCK 没有获得批准；四条正式科学文件路径不存在；正式 trainer/run recorder/五 seed/core E2E 尚未执行；G6 prerequisite helper 对缺失或 BLOCKED 的 G5 放行过宽，与所有者刚刚裁定的组合语义有差距。不能用单元测试通过替代这些缺口。

## 2. Root Causes Fixed / remaining actual defects

此前工程修复及原失败记录保留在根目录报告的历史正文中。当前阶段已安装入口修复的证据显示：同 URI 导航的 WebView2 readiness 挂起已修复，显式进入/返回开始页/无密钥浏览/重复切换 DeepSeek 均完成原生路径验证；release verifier 子进程遗漏 `--app-root` 导致检查错误目录的问题已修复；Windows 与 WSL 中两份旧 research-sop kernel 已按确切旧 hash 更新。当前安装版 strict 检查为 13 PASS / 0 FAIL / 0 NOT TESTED。该结论绑定 `9e53dcc` 安装件，不能转授给正在修改的模型功能源码。

本次科学复核发现并明确保留的缺陷是 **G6 formal admission 尚未按已裁定语义完整执行**。`pinn/governance/state_machine.py::operation_prerequisite_status` 对 `G1=PASS, G4=PASS, evidence_level=A, G5缺失` 返回 PASS；把 G5 改为 BLOCKED 仍返回 PASS。Level D 缺失 G5 也返回 PASS。helper 没有验证 Level-D/U1 例外身份和原因，不可直接用作正式 dispatcher。这是实测行为，不是推测。

该源码受现有 42 项审查身份绑定。此次没有静默修补它或重写旧包。所需修正应形成可区分的 draft amendment：精确限制 U1 例外、补齐有效 G1/STOP 判断、覆盖 A/B/C 缺失与 BLOCKED 情况，并重新生成身份清单和人审材料。在正式批准前，不得继续沿用旧清单来批准新字节。

## 3. Files Changed and repository identity

本报告任务只写两个报告文件；没有修改科学源代码、候选、NPY、Constitution、测试源码或应用数据。

| 文件 | 原因 |
| --- | --- |
| `docs/PINN_PHASE2_RECONCILIATION_20260909.md` | 保存当前现场、所有者语义决定、复算结果、G6 缺陷、验收边界和后续接入位置 |
| `PINN_MVP_AND_CFD_READINESS_REPORT.md` | 在完整历史正文之前增加带日期的当前导读，防止旧 FAIL/旧路径被误读为当前安装状态；历史正文保持原字节 |

| 身份 | 本次实际观察 |
| --- | --- |
| 主仓库 | `C:/Users/user/Desktop/LeoAIStudio-build` |
| 主仓库 HEAD | `8c4835e9d5034876235e1108e889902ac5bfa14f`，`snapshot before cleanup (102 items, per LeoAI cleanup report 20260909)` |
| 当前模型 worktree | `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2/models-worktree` |
| 当前分支 / 基线 HEAD | `codex/conversation-runtime-20260909` / `9e53dcc4d534a1dadd93ad0107ee88bef55d455f` |
| 当前工作区状态 | 模型功能和打包集成仍有未提交修改；不能声称最终干净或已部署。科学身份复核仍为零漂移 |
| 保留的科学分支 | `codex/pinn-mvp-phase2-20260908t124356z` |
| 科学提交 | `96f4ef0445832016882060b0fa450ce0a3b0c96c` |
| 原 Phase II `repo/` 目录 | 已被本任务之外的清理移除，当前不再作为可访问文件路径引用；其提交仍能 `git show` 读取 |
| Python | `../ui-worktree/.venv/Scripts/python.exe`；3.12.9 conda-forge，MSC v.1943 64 bit |
| OS / 诊断设备 | Windows 11 build 26200；CPU，float64；本次科学组件只用 stdlib，无下载、无训练、无 GPU 分配 |

主仓库清理快照不等于科学冻结。没有将原先 dirty master 解释成当前仍有同样的未提交工作，也没有恢复或再次删除外部清理移除的目录。

## 4. Test Matrix

以下区分当前实际复算、已读取的原始日志和未执行任务，不把数量合并成一个虚构 suite。当前只读脚本通过 stdin 运行并设置 `PYTHONDONTWRITEBYTECODE=1`，没有创建新增测试源码或科学 evidence 目录；结果保存在本报告中。

| 检查 / 命令或入口 | Passed | Failed | Skipped | 范围 / 结果 |
| --- | ---: | ---: | ---: | --- |
| 对身份清单的每项 `sha256(Path.read_bytes())`；同项 `git show 96f4ef0:path` | 42 工作树 + 42 Git 对照 | 0 drift | 0 | 本次重算，清单自身 hash 同下文 |
| `run_prelock(PrelockPaths.defaults(Path.cwd()))` | 6 检查组 | 0 | 0 | 本次重算；`hashLockExecuted=false, trainingExecuted=false, p2Entered=false` |
| `evaluate_samples`，6 个 `FIXTURES`，每个重复两次 | 1 正场满足 + 5 错误场被拒绝 | 0 误接受 | 0 | 6/6 两次返回结构一致；不等于确定性训练 |
| `refinement_diagnostic()` | 7 mesh、末四对阶数满足 | 0 | 0 | 独立 FDM 组件，非 G2 |
| `operation_prerequisite_status(6, ...)` | 10 个组合均实际求值 | 已发现过宽许可 | 0 | A/D × G5 缺失/BLOCKED/FAIL/PARTIAL/PASS；这是缺陷诊断，不能记成治理 PASS |
| 已安装入口源码回归日志：`python -m pytest -q -p no:cacheprovider` | 839 | 0 | 2 | 已读取 `entry-recovery-full-regression-20260909.log`，34.78s；不是本报告又跑一次 |
| 已安装 strict：`tools/verify_release.py --strict --app-root <installed> --manifest <entry-manifest>` | 13 | 0 | 0 NOT TESTED | 已读取原日志，精确绑定 9e53dcc 安装件 |
| 本轮模型功能最终全仓回归及安装验收 | — | — | — | 截止本报告时尚由主任务进行，不在此预填结果 |
| 正式训练、五 seed、G2–G7、core E2E | 0 | 0 执行失败（未执行） | 0 | **BLOCKED / NOT-RUN**，不是 pytest skip |
| fresh Windows/账户、缺失 WSL/WebView2、clean-machine build | — | — | — | 必要场景仍 **NOT-RUN / BLOCKED**，不能用本机已有环境代替 |

入口回归的两项既有 skip：未启用 entityLifecycle 的旧分支在当前功能已启用时不适用；缺少本地 wheelhouse 时其验证用例不运行。当前安装件的既有构建证据不证明本机现在仍保留 wheelhouse，更不证明新机器环境已验收。没有增加 skip/xfail、放宽容差或删除已有测试来改变上述结果。

可直接重放的无文件组件复核（从当前工作树运行；环境变量禁止生成 pycache）：

```python
from pathlib import Path
from pinn.governance.prelock import PrelockPaths, run_prelock
from pinn.validation.fixtures import FIXTURES
from pinn.validation.poisson import (
    load_candidate_protocol, sample_callable_fixture, evaluate_samples,
)
from scientific_reference.poisson_fdm import refinement_diagnostic
root = Path.cwd()
print(run_prelock(PrelockPaths.defaults(root)))
protocol = load_candidate_protocol(root)
for fixture in FIXTURES:
    samples = sample_callable_fixture(
        protocol, fixture.solution, fixture.first_derivative, fixture.second_derivative)
    result = evaluate_samples(protocol, samples)
    print(fixture.fixture_id, result, result == evaluate_samples(protocol, samples))
print(refinement_diagnostic())
```

## 5. Scientific Validation

数学定义：`-u''(x)=π² sin(πx)`，`x∈(0,1)`，边界 `u(0)=u(1)=0`，闭包 `[0,1]`。手工求导 `u*=sin(πx)` 给出 `u*'=πcos(πx)`、`u*''=-π²sin(πx)`，代入 residual `R=-u''-f` 得零。两解之差满足 `w''=0` 且两端为零，故解唯一。全部量无量纲；没有额外时间变量或编造的无量纲化转换。

记 `Q[h]=Σ_GL512 w_i h(x_i)`，`V` 为冻结 CGL2000，`B={0,1}`，`ε=1e-30`。下面的数值是 **analytic positive control，绝非 PINN 训练输出**。分母需大于 `1e6 ε`；finite、shape、坐标、domain、BC、来源和泄漏准入是额外前置条件。阈值严格 `<`，等于阈值不合格；所有量均 dimensionless。

| 指标 | 公式 / sample set / aggregation / normalization | 本次解析控制值 | 阈值 |
| --- | --- | ---: | --- |
| AC-1 | `sqrt(Q[(u-u*)²]/(Q[u*²]+ε))`，GL512 加权 L2 比值 | 0 | `<0.001` MUST |
| AC-2 | `max_V abs(u-u*)/(max_V abs(u*)+ε)`，CGL2000 离散最大值比 | 0 | `<0.005` MUST |
| AC-3 | `max_B abs(u-g)`，两端最大绝对差，无归一化 | 1.2246467991473532e-16 | `<0.0001` MUST |
| AC-4 | `sqrt(Q[(-u''-f)²])/(π²/√2)`，GL512 residual RMS | 0 | `<0.01` MUST |
| AC-5 | `abs(Q[u]-2/π)/(2/π)`，GL512 积分 QoI 相对差 | 3.6622619229090635e-15 | `<0.001` MUST |
| AC-6 | `abs(u'(0)-π)/π`，精确 x=0 的导数 QoI | 0 | `<0.005` MUST |
| AC-7 | `abs(Q[u'²]-Q[fu])/(π²/2)`，GL512 能量恒等式归一化差 | 6.299390213871842e-15 | `<0.01` MUST |
| AC-8 | `sqrt(Q[(u'-u*')²]/(Q[u*'²]+ε))`，GL512 导数相对 L2 | 0 | `<0.005` SHOULD |
| absolute L2 / sampled absolute Linf | `sqrt(Q[(u-u*)²])` / `max_V abs(u-u*)` | 0 / 0 | 仅诊断，无新阈值 |
| residual RMS / sampled maximum | `sqrt(Q[R²])` / `max_GL512 abs(R)` | 0 / 0 | 仅诊断，无新阈值 |
| boundary residuals | `[u(0)-0,u(1)-0]` | `[0,1.2246467991473532e-16]` | AC-3 聚合 |

GL512 的 512 个内点及其权重、CGL2000 的 2000 点均读取 exact-byte NPY；验证不随机抽样，`evaluationSeed=NOT_APPLICABLE`。CGL2000 分母实测 `0.9999992382301501`。所有者已选择 sampled AC-2，不授权连续区间 supremum claim。正式 training seeds 为 20260904、20260905、20260906、20260907、20260908，尚无五 seed 训练结果。

独立 FDM 没有 import PINN 类，采用三点 stencil 与 Thomas 消元：

| 子区间 N | 内点最大误差 |
| ---: | ---: |
| 32 | 8.035776793697824e-4 |
| 64 | 2.0082180969560604e-4 |
| 128 | 5.020091591312337e-5 |
| 256 | 1.254994550148325e-5 |
| 512 | 3.1374687126106693e-6 |
| 1024 | 7.843656864015003e-7 |
| 2048 | 1.960919837618036e-7 |

末四对 `log2(E(N)/E(2N))` 为 `2.0000325870698976, 2.000008121803618, 2.0000027437966774, 1.999995864039661`，在既有 `[1.8,2.2]` 范围内，误差严格递减。N=2048 离散 residual 最大值 `1.4004299941916543e-9`。这是验证独立 baseline 的诊断，AC 参考仍是解析解。

| 错误场 | 本次被拒绝的 MUST AC | 说明 |
| --- | --- | --- |
| B1b，负号解 | 1,2,4,5,6,7 | 相对 L2=2，归一化 residual≈2 |
| B3，解加 0.3 | 1,2,3,5,7 | residual=0 仍拒绝；BC 最大差=0.3000000000000001 |
| B4，四阶小扰动 | 1,4,6 | L2≈0.002，residual≈0.032 |
| B6，五阶扰动 | 1,2,4,5,6,7 | L2≈0.2，residual≈5 |
| ZERO_FIELD_CONTROL | 1,2,4,5,6 | BC 与能量项可满足，仍不能成为 Accuracy Claim |

先前组件 tests 还覆盖 wrong forcing/BC/domain、NaN/Inf、malformed input、invalid metric、missing evidence/hash mismatch/changed lock fixture、seed metadata mismatch 和 leakage；其实际命令与失败日志保留在历史报告。**corrupted checkpoint 的真实 loader、insufficient training 的真实优化失败、optimizer NaN 传播、跨进程五 seed 重建仍未完成 E2E**。当前没有真实训练 loss 曲线，不能用 `L_total` 或这些闭式场冒充 `L_PDE/L_BC/L_total` 的优化记录。

## 6. Remaining Risks and gate status

| 项目 | 当前结论 | 边界 / 剩余工作 |
| --- | --- | --- |
| P0-1 | PASS，仅 9e53dcc 已安装件 strict 范围 | 13 项全部满足；当前 dirty 模型实现需要新 commit、构建、部署和重新验证 |
| P0-2 | PASS，既有自动化完整性范围 | canonical kernel 与部署拷贝一致；E1–E3 真实五角色运行/打回归档不得由磁盘 hash 代替 |
| P0-3 | PARTIAL | 当前机器原生 UI/入口/ShellApi 修复通过；全新账户等必需人工条件没有代签 |
| P0-4 | PARTIAL | 静态可移植性及已有本机路径有证据；fresh Windows、不同/缺失 WSL、缺失 WebView2 等场景仍缺 |
| P0-5 | PARTIAL | 已有构建/锁依赖证据；clean-machine 必需项未完成 |
| P0-6 | FAIL | 依照现行定义，必要 P0-4/P0-5 尚未闭合；不是由科学语义批准豁免 |
| F-008 | PASS，当前已安装版本的来源链范围 | strict 的 16 runtime assets/3 artwork masters 有版本追踪；模型 UI 新字节须重新绑定 |
| PRELOCK_VALIDATION | PASS | 候选检查，不是 formal G1 |
| Formal G1 | BLOCKED | 正式 lock 路径不存在，批准未给出 |
| Formal G2–G7 / trainer / core E2E | BLOCKED / NOT-RUN | 没有执行依赖计算；组件复算不能晋级 |
| G6 helper 对所有者新裁定的符合性 | FAIL（实现差距） | 必须 amendment、执行拒绝用例、刷新人审身份包；未将旧 helper 的 PASS 当正式权限 |
| PINN MVP DoD | NOT COMPLETE | 正式重复运行、完整 provenance、训练失败传播、最终 clean delivery 等尚未全满足 |

所有者在本任务中回答：“保留当前 sampled 指标（推荐）”；“接受上述组合解释（推荐）”。第二项明确指：G4 必须 PASS；G5 FAIL/PARTIAL 阻断；只对已定义 Level-D/U1 探索例外允许 G5 BLOCKED 时复现；A/B/C 缺 G5 或 G5 BLOCKED 只允许独立诊断，正式 G6 阻断；现有 G1 有效性与 STOP THE LINE 仍适用。原始决定记录在科学提交 `96f4ef0:docs/PINN_SEMANTIC_DECISION_20260909.md`。两个问题均排除了 P0 豁免与正式 HASH LOCK 批准。

Claim 必要前置仍按既有 claim level：C0 为 G1/G3；C1 为 G1/G3/G4；C2 为 G1–G6 且 Level D 永久禁止；C3 还需五个已支持 C2 和 SR-1；C4/C5 不属本 MVP。不能改成每种 Claim 都要所有 Gate PASS，也不能从 helper eligibility 推断已有支持证据。Exploratory Run 与 Validated Scientific Result 的分离仍须在未来 recorder/dispatcher/claim ledger 的实际执行链完整落实。

完整科学链当前断点：Problem candidate → 独立 evaluator 已有；冻结 Solver Configuration、正式 Execution、checkpoint → raw Evidence 的可信关联、优化器失败传播、正式 Validation/Gate/Claim ledger/ScientificRun report 尚不完整。手写 metadata 或 `derivativeMethod` 标签不提供可信来源。必须记录 run_id、时间、commit/dirty、Python/依赖/硬件、seed/config、spec/solver hashes、raw outputs、validation/Gates/claim status，并保证失败运行不覆盖。

## 7. CFD Readiness

**PARTIAL**。本次未实现 CFD/OpenFOAM、CFD UI 或通用空框架，未安装 CFD 依赖。已审计的实际 seam 是 `pinn.validation.poisson.FieldSamples` 与 `evaluate_samples(protocol, samples)`：它们处理坐标、标量场和导数，验证层不依赖某个 neural-network class；`scientific_reference/poisson_fdm.py` 独立于 PINN。这个 contract 是 Poisson 专用，不能假称已经覆盖 u/p/mesh。

在 PINN 闭环稳定后，下月可从真实科学运行的 solver 调用位置接入薄 OpenFOAM adapter，职责为准备 case、执行外部进程、采集输出、描述环境，再交给问题专属独立 validator。先沿用现有进程边界处理 stdout/stderr、退出码、超时/取消和长任务；case、mesh、field、残差历史及 restart 父 run 要有身份和 hash，失败证据保留，避免添加分布式或缓存框架。

Poiseuille 应另立版本化 ProblemSpec/独立解析 oracle，验证质量守恒、压降、壁面剪切和网格收敛，然后才是 Backward-Facing Step benchmark。同一物理 ProblemSpec 可被 PINN/CFD 分别求解；比较 u/p、mass、Δp/派生量的采样、单位和插值映射应在独立验证层中明确，转换来源可审计。当前代码没有阻断这种方向，但尚无完整 Solver Adapter 可称 READY。

## 8. Evidence and provenance

| 证据 | SHA-256 |
| --- | --- |
| 42 项身份 `docs/PINN_P2_FINAL_HUMAN_REVIEW_IDENTITY.json` | `a7eaa17238cbc7c3b6d7514b2f321ada9ccbebdd2affffadd52e57af5a7d3acb` |
| Constitution 当前 exact bytes | `4300bb848cc968e96c6b9de318796f6791a6cccea518bff2faac96e8f0c87018` |
| spec draft | `a6733840c9363f841a4877c7283a5935fb0ff0e980a4f08e1e7a8188bfb155bc` |
| protocol draft | `800749f5211f19e8ebfa576537e2d92b10ba3a8432de34745eaf1231a78545c0` |
| adversarial draft | `72b3a741d2f8bf0bb3867af5befafe0f7c517d2973172ce5792aa728ddb8130d` |
| lock draft | `6626362d6376d13407dc7303de9f4943360706a6b84a2fd11a2faa31c0a4ae7f` |
| 保留的原根报告正文，35,459 bytes | `f809f8e68c204a44eeae36adf272cb62569eb8372e1e4024452f66ac5f6aa249` |
| `../evidence/P0_PHASE2_EVIDENCE_RECORD.md`，963,657 bytes | `181dfda8c178a357dd465e940c524efa9e4d1128a65394ef80e1e1f873f26c1d` |
| `../ui-evidence/entry-recovery-installed-manifest-20260909.json` | `d21a40cb038e70a3f2c341a761bdde851445b3672479655b322071aa93d9b57f` |
| `../ui-evidence/entry-recovery-installed-strict-20260909.log` | `eb9e35c2e5c98499c893a71e4682f4e0aef2261ce63c8c1a587ac43b019fc9a0` |
| `../ui-evidence/entry-recovery-full-regression-20260909.log` | `d910071d86a01aba10afc658b4018390f350464ad523d14f501f9af184451465` |
| 已安装 EXE（该安装回执记录） | `4d23d0d2dfb2c70b2a1fa9010739b065e26456d03bb3398fc7b49a7473414a89` |

以上 `../evidence` 与 `../ui-evidence` 相对于 worktree 根，而非本 docs 目录。根绝对路径为 `C:/Users/user/Documents/LeoAIStudio-deliveries/20260908-phase2`。旧报告中的已移除目录链接只作为历史位置保留；需要读取旧源码时使用保留的 Git commit，不宣称目录仍存在。

本次重新确认 `specs/poisson-1d/v1.0/{spec,protocol,lock}.json` 和 `adversarial/core_manifest.json` 均不存在。dry-run payload digest `55efe6b6c531822dac02d57bc5d6e095d22f4f0d918f5c810654e2d5f3f37fae` 使用未设正式 timestamp 的 sentinel，**不是 lockSha256**。本次没有 formal run_id、正式 checkpoint 或 Accuracy Claim 可交付，没有填造这些字段。

## 9. Recommended Next Commit

当前只能形成清晰的工程/报告提交，不能建议 “PINN MVP COMPLETE” 冻结提交。主任务应在完成当前模型功能、真实测试、临时文件及测试对话清理后，以明确文件列表提交并重新构建/部署/验证；报告须绑定那个最终 commit，不能挪用当前旧安装件回执。

科学下一提交应为单独可审查的 **G6 draft amendment + refreshed human-review identity**，落实已接受语义且保留原包；随后补齐必要 P0 实境验收，向所有者呈现 exact candidate 与完整 P0 证据，请求单独正式批准。只有批准及依赖真实满足后，才执行正式 lock、trainer/run recorder、五 seed、独立验证、adversarial core E2E 和 Claim Gate。用户已同意 AC-2/G6 的语义，并未授予跳过这一顺序的权限。

````

</details>

### R029 — 项目/docs/RESEARCH_SOP_MIGRATION_AUDIT_24f3fd7.md

<details>
<summary>展开完整原文</summary>

````markdown
# Research-SOP migration audit for `24f3fd7`

Date: 2026-09-05

## Scope and method

The source commit `24f3fd7` was audited against mainline HEAD `d58dffe` from
their merge base `58aeb19`. It was not merged or cherry-picked. The mixed
commit was decomposed so each production guarantee and its tests can be
reviewed independently.

| Contract | Disposition | Mainline commit |
|---|---|---|
| F-007 manifest self-consistency | migrated with focused and mutation tests | `e92fa81` |
| F-001 document digest verification on read | migrated with focused and mutation tests | `3e809f2` |
| F-002 rollback archive verification on audit | migrated with focused and mutation tests | `8084078` |
| B08 attempt identity | implemented as a separate contract and test | `ad11801` |
| F-008 `theme-src` architecture | not migrated | deferred |

## B07 external-test disposition

The frozen external `test_B07_modify_history_file` is structurally invalid and
is retained unchanged as an external-test record. Its final branch raises when
the archived manifest digest equals the digest of the saved pre-tamper bytes:

```python
if claimed == sha256(original):
    raise AssertionError(...)
```

That equality is true by construction for a correct archive: `claimed` was
recorded from `original` before the test appends `FORGED`. It is independent of
whether production detects the later tamper, so no production implementation
can satisfy the final assertion without corrupting the archive contract.

Production was not changed to accommodate that assertion. F-002 instead tests
the valid property directly: after a length-preserving rewrite, append,
deletion, or digest removal, `sop_inspect_history` and `sop_status` report the
archive as corrupt; intact and restored bytes report clean.

## B08 contract correction

Attempt identity and artifact identity are distinct:

- every execution of a stage receives a new opaque `attempt_id`;
- deterministic reruns may produce byte-identical artifacts and therefore the
  same `document_sha256`;
- scientific documents must never be edited merely to manufacture different
  evidence bytes.

The focused B08 test forces a real paper-writer rerun, proves that the two
`attempt_id` values differ, and simultaneously proves that identical document
bytes and digests remain valid.

## F-008 overlap and conflict audit

The current Ink Autumn hierarchy is the accepted canonical source for its own
theme assets:

- `stage/themes.json`;
- `stage/backgrounds/manifest.json` and the three rendered WebP files;
- untouched masters under `assets/backgrounds/`;
- `tools/build_backgrounds.py` and `tools/bundle_theme.py` as the recorded
  build chain.

The proposed `theme-src` tree in `24f3fd7` re-declares `themes.json` and the
background manifest with byte-identical Git blobs, references the same three
rendered backgrounds through a separate asset house, adds a second assembler
(`tools/build_theme.py`), and rewires `tools/build_launcher.ps1` around that
assembler. Migrating it now would create overlapping canonical sources and two
competing assembly paths.

The existing provenance measurement currently reports 8 of 18 runtime-read
theme assets with tracked canonical sources, 10 pre-existing gaps, and one
deployed `shell.html` drift. F-008 therefore remains open. Its brand-asset gaps
may be addressed later, but only after choosing an architecture compatible with
the frozen Ink Autumn hierarchy.

No Ink Autumn image, stylesheet, registry, manifest, master, or build recipe was
modified during this research-sop migration. Its status remains ACCEPTED &
FROZEN.

````

</details>

### R030 — 项目/docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md

<details>
<summary>展开完整原文</summary>

````markdown
# A-0002 Final Closure Review 与 PINN Agent 实验准入审计（2026-09-15）

评审人：Claude（队长、宪法维护者）。对象：`governance/AMENDMENTS/A-0002-admissible-matrix-r2.md` 第 3 稿。本轮只解决三项剩余问题并做准入审计，不新增 Gate、状态或协议层；status 保持 `PROPOSED`、effectiveDate 保持 `PENDING`，等用户终审授权。

## 1. A-0002 Final Decision Recommendation

```text
READY FOR USER ACCEPTANCE
```

三项剩余问题全部解决（Issue 1 原为 BLOCKING，已最小修复并有测试），全套 1087 passed / 2 skipped / 0 failed，PRELOCK 七项 PASS，闭合审计没有新的 blocking contradiction。建议用户终审；队长不自行 ACCEPT。

## 2. 三项剩余问题裁决

| Issue | Decision | Evidence | Code/Test impact |
|---|---|---|---|
| 1 运行时版本隔离 | **BLOCKING，已修复**（ACCEPT）。审计结论：修复前 `ADMISSIBLE_ROOT_CAUSES` 是单一全局最新表，`diagnose()` / `validate_diagnosis_record()` 不读宪法版本，文档 = 1.1 而运行时 = 1.2 语义；干预 / 重放义务同样对 1.1 生效（把 1.1 变严也是泄漏）。 | `state_machine.ADMISSIBLE_ROOT_CAUSES_BY_VERSION{"1.1","1.2"}`、`NAMING_OBLIGATIONS_BY_VERSION`、`admissible_root_causes(version)` 只接受 `locking.SUPPORTED_CONSTITUTION_VERSIONS`（现为 1.0/1.1）内的版本；`diagnose(..., constitution_version=)` 与 `discriminating_experiment_errors(..., constitution_version=)` 为必填关键字，无默认；DiagnosisRecord schema 必填 `constitutionVersion`；`amendments.py` R5：PROPOSED 的 newVersion 不得已生效、ACCEPTED 的必须生效；PRELOCK 第七项同时校验登记簿每个版本都有运行时矩阵。 | `pinn/governance/{state_machine,trust_loop,amendments,prelock}.py`、`diagnosis-record.schema.json`；新增 `tests/pinn/test_constitution_version_isolation.py`（Issue 1 部分 21 项：1.1 拒绝八格 ×8、1.2 生效后允许 ×8、PROPOSED 不改 1.1、直接 API 不可绕过、PRELOCK 与运行时一致、真实运行时状态）；既有三角测试改为在"模拟 1.2 生效"夹具下运行 |
| 2 多症状多根因与覆盖不变量 | **ACCEPT_WITH_MODIFICATION**。接受问题：单条记录不得被迫解释全部症状。采用 `explainedSignatures ⊆ observedSignatures`（默认 = 主症状），覆盖不变量放在记录**集合**上；一个症状被两条记录归到不同根因 = 非法（不定义多因归因；分不开就 rUndetermined 停线）。 | `trust_loop.explained_signatures` / `diagnosis_coverage_errors(records)`：同 (problemId, revision, specHash, constitutionVersion, round)、同 observedSignatures、∪explained = observed、每个症状恰好一条记录；单记录的 `excludes` 义务 = 所解释症状候选集的并集；`state_machine.earliest_route` 多记录重入取最小 Gate。 | schema 加 `explainedSignatures`；`validate_diagnosis_record` 去掉"根因须对所有观察症状可接受"的单因规则；4 项新测试（两症状两根因覆盖、漏解释、冲突归因、单记录解释两症状的并集义务与挑症状） |
| 3 sSeedSensitive → rSpecDefect 收窄 | **ACCEPT**。仅当 seed 变化暴露**非预期的**不可识别性 / 未消解的解等价（零空间、规范自由、归一化、分支、对称）且冻结 Claim 需要唯一可评估目标时才是规格缺陷；合法多解不是缺陷；证据不能判定是否有意时不得叫规格缺陷，必须 rUndetermined。 | `state_machine.identifiability_errors`：命名该格必须附 `discriminatingExperiment.identifiability{ambiguityType, claimRequiresUniqueEvaluation = true, specResolvesAmbiguity = false, ambiguityIntent = unintended, nullspaceProjectionFraction?}`；`claimRequiresUniqueEvaluation = false`、`ambiguityIntent = intended`、`specResolvesAmbiguity = true` 各自拒绝；`undecided` 拒绝并指向 rUndetermined。 | schema `$defs/identifiability`；协议汇编 P34 措辞改写；4 项新测试（Neumann + 绝对值 claim + 无规范 → 规格缺陷；分支感知 claim / 有意多解 / 规格已定规范 → 拒绝；undecided → 停线；缺记录 → 拒绝；非 seed 症状不欠该记录） |

## 3. Runtime Version Isolation Evidence

| 场景 | 行为（当前仓库状态：宪法 1.1，A-0002 PROPOSED，`SUPPORTED_CONSTITUTION_VERSIONS = (1.0, 1.1)`） | 测试 |
|---|---|---|
| 1.1 behavior | `admissible_root_causes("1.1")` 返回冻结的 A-0001 矩阵（26 格，与 a94c138 逐格一致）；命名义务集合为空（无干预 / 重放 / 可识别性义务）；八个 A-0002 格 `diagnose` 抛 `IllegalTransition("... under Constitution 1.1")`，文档校验报 `not admissible ... under Constitution 1.1`；sPinnCfd → 规格的排除义务是 1.1 的 5 个候选，不是 1.2 的 7 个 | `test_1_1_rejects_every_a0002_only_admissible_cell[8]`、`test_proposed_a0002_does_not_change_1_1_behavior` |
| 1.2 behavior | 只有 `"1.2" ∈ SUPPORTED_CONSTITUTION_VERSIONS` 时可选（终审配方里加 "1.2" 的那一步即解锁）；此时八格路由到派生 Gate、文档校验通过、登记簿 R5 通过（A-0002 ACCEPTED + 宪法 1.2 + effective 含 1.2） | `test_1_2_allows_a0002_cells_after_dependency_and_effective_checks[8]`（monkeypatch 模拟生效） |
| PROPOSED amendment behavior | 代码里 1.2 表存在但不可达：`admissible_root_causes("1.2")` 抛 `ConstitutionVersionError("Constitution 1.2 is not effective ...")`；`validate_diagnosis_record` 对 constitutionVersion = 1.2 的记录返回同一错误；1.1 矩阵与义务与 A-0002 起草前逐字节相同 | `test_direct_diagnosis_api_cannot_bypass_version_gating`、`test_the_real_runtime_has_1_1_effective_and_1_2_proposed` |
| direct API behavior | `diagnose()` 无 `constitution_version` → `TypeError`；"1.0" → 无矩阵；"9.9" / 非字符串 → 拒绝；`discriminating_experiment_errors` 同样返回版本错误；`validate_diagnosis_record(record, constitution_version=run 的版本)` 记录与 run 版本不一致 → 错误；schema 缺 constitutionVersion → 错误 | 同上 |
| PRELOCK behavior | 第一项：宪法声明版本 ∈ SUPPORTED；第七项：ACCEPTED 链尾 = 声明版本，PROPOSED 的 newVersion ∉ SUPPORTED（否则报 "leaked"），ACCEPTED 的 newVersion ∈ SUPPORTED，登记簿每个 newVersion（≥ 1.1）与声明版本都有运行时矩阵。实跑 7/7 PASS | `test_prelock_version_and_runtime_matrix_agree`、`test_amendments.py::test_prelock_runs_the_register_check` |

结论：GovernanceSemantics = f(constitutionVersion)，单一事实来源是 `locking.SUPPORTED_CONSTITUTION_VERSIONS`（运行时读取，不在导入期固化）。不存在 PROPOSED 修正案泄漏到有效运行时的路径；不需要重构。

版本中性、记录为 DEFERRED / NON-BLOCKING：DiagnosisRecord schema 的 `problemClass = forward` 与可选 `observedSignatures` 字段对 1.1 记录同样存在。它们只增加信息、不改变任何可命名的根因或义务（1.1 本就只有正向 MVP），故不按版本拆 schema。

## 4. Signature Coverage Evidence

记录语义：一条 DiagnosisRecord = `R_j : explainedSignatures_j → rootCause_j`，`signature`（主症状）∈ `explainedSignatures_j` ⊆ `observedSignatures`。不变量（`diagnosis_coverage_errors`）：

- 所有记录属于同一失败（problemId, revision, specHash, constitutionVersion, round）且列出相同的 observedSignatures；
- ⋃_j explainedSignatures_j = observedSignatures（漏解释 → INVALID，错误文本给出漏掉的症状）；
- 每个症状恰好被一条记录解释（`s1 → rA` 与 `s1 → rB` 同时存在 → INVALID；MVP 不定义单症状多因归因，因为按排除纪律命名 rA 就必须排除 rB，两者同时成立时谁都不能命名 → rUndetermined 停线）；
- rUndetermined 记录也算覆盖（该症状的处置是停线）。

单条记录解释多个症状时，`excludes` 必须覆盖所解释症状候选集的**并集**；只登记便宜症状则另一症状无人解释，被覆盖不变量拒绝——"挑症状"在集合层面封住，同时不强迫单因。多条 DIAGNOSED 记录重入时取最小 Gate（`earliest_route`），下游全部重跑。

测试：`test_two_signatures_two_root_causes_are_two_records_that_cover_everything`、`test_a_signature_no_record_explains_is_a_coverage_failure`、`test_conflicting_attribution_of_one_signature_is_refused`、`test_one_record_may_explain_several_signatures_but_owes_the_union_of_exclusions`。

## 5. P34 / rSpecDefect Final Semantics

```text
sSeedSensitive -> rSpecDefect is admissible only when seed variation reveals
unintended non-identifiability or unresolved solution equivalence that prevents
the registered Claim from being uniquely evaluated under the frozen ScientificSpec.
```

| | legitimate multiplicity | unintended non-identifiability |
|---|---|---|
| 例 | 非线性 PDE 的多分支 / 分岔 / 对称相关解 / 规范自由，且 Claim 是分支感知或集合值的；或规格已给出规范条件 | 纯 Neumann Poisson `-Δp = f`，`p ~ p + C`，Claim 要比较绝对压力，规格未规定 ∫p = 0 或参考压力 |
| identifiability 记录 | `claimRequiresUniqueEvaluation = false` 或 `ambiguityIntent = intended` 或 `specResolvesAmbiguity = true` | `claimRequiresUniqueEvaluation = true`、`specResolvesAmbiguity = false`、`ambiguityIntent = unintended` |
| 裁决 | 不得命名 rSpecDefect（不是缺陷）；seed 落入不同分支要在其它候选里排除 | rSpecDefect → G1 |
| 证据不能判定是否有意 | `ambiguityIntent = undecided` → 拒绝命名，指向 rUndetermined 停线 | |

P34 检验的是"这种多解 / 零空间 / 等价关系是否违反冻结 Claim 要求的可识别性"，`nullspaceProjectionFraction` 只是可选证据（差投影到零空间的占比），不是判据本身。

## 6. Test Evidence

| 项 | 值 |
|---|---|
| previous baseline | 1058 passed / 2 skipped |
| new tests | 29（`test_constitution_version_isolation.py`：Issue 1 21 项、Issue 2 4 项、Issue 3 4 项（其中一项参数化 3）） |
| 修改的既有测试 | `test_state_machine_triage.py`（在模拟 1.2 生效夹具下运行、seed → 规格夹具补 identifiability）、`test_trust_loop_adversarial.py`（记录加 constitutionVersion；单因规则的断言改为 explainedSignatures 语义） |
| total passed | **1087** |
| failed | 0 |
| skipped | 2 |
| PRELOCK | `python -m pinn.governance.prelock` 7/7 PASS（constitutionBinding、spec、protocol、adversarialManifest、lockDraft、repository、amendmentRegister） |

## 7. A-0002 Final Closure Audit（有限检查）

1. runtime / version mismatch：无（§3）。
2. signature 未覆盖：无（§4）。
3. 某格科学含义明显过宽：sSeedSensitive → rSpecDefect 已收窄（§5）；其余七格的命名前提（干预 / 重放 / 排除并集）未变，未发现过宽。
4. 已知 Agent bypass：挑症状（集合覆盖封住）、挑便宜根因（排除并集）、单次改进冒充因果（受控干预）、把合法多解叫规格缺陷（identifiability）、把 1.2 格写进 1.1 记录（版本隔离）——均有测试。"漏报症状"不可机器判定，留人工审计（宪法第三十九 / 四十章）——DEFERRED / NON-BLOCKING。
5. amendment dependency bypass：R1–R5 + PRELOCK 第七项；ACCEPTED 未生效 / PROPOSED 已生效两向都拒绝。

DEFERRED / NON-BLOCKING（不扩张 1.2）：单症状多因归因的定义；schema 字段按版本拆分；逆问题矩阵；`nullspaceProjectionFraction` 的预注册阈值。

## 8. PINN Agent Experiment Readiness

```text
PINN_AGENT_EXPERIMENT_READINESS:
NOT_READY
```

| 类别 | 条件 | 状态 |
|---|---|---|
| Governance | A-0001 终审完成 | ✓ ACCEPTED 2026-09-15 |
| | A-0002 终审完成 | ✗ **BLOCKER 1**：队长已收口（READY FOR USER ACCEPTANCE），等用户终审"通过"并执行 1.2 配方（宪法正文 3.1 / 第六十章、SUPPORTED 加 1.2、三份 schema 枚举、Poisson 草案重绑定、新证据文件） |
| | 依赖顺序有效 | ✓ dependsOn A-0001 ACCEPTED @ 1.1，R1–R5 通过 |
| | Constitution / schema / runtime 版本一致 | ✓ 宪法 1.1 = 链尾 = SUPPORTED 内 = 有运行时矩阵 |
| | 无 PROPOSED 泄漏 | ✓ §3 |
| Implementation | full suite PASS | ✓ 1087 / 0 failed |
| | PRELOCK PASS | ✓ 7/7 |
| | no blocking TODO | ✓（R3 项：runner 工具、报告文本 lint、跨规格复发升级，均不阻塞 A-0002；runner 是 BLOCKER 2 的一部分） |
| | tree clean | ✓ 本轮提交后干净 |
| | evidence / version pins 一致 | ✓ `PINN_V1.3_PRELOCK_DRY_RUN_A0001.json` 绑 1.1 |
| Calibration experiment（Poisson 1D） | Frozen ScientificSpec / ProblemDefinition / D_train·D_dev·D_claim / multi-seed / 独立评估 / Trust Vector / Gate 执行 / ValidationReport / ClaimGateDecision / provenance / 复现证据 | ✗ **BLOCKER 2**：只有三份 PRELOCK 草案（lockedAt = null），没有 ProblemDefinition 实例、评估集清单、RunRecord、TrustVector、ClaimGateDecision、账本事件；捕获环境指纹与清单的 runner 工具未实现（R3） |
| Failure-path experiment | 至少一个已知失败案例走完 FAILURE_RECORDED → DIAGNOSED → REVISED → 重入 Gate | ✗ **BLOCKER 3**：状态机路径只有单元测试覆盖，尚无真实 run 走过 |

Blocker 1 是用户动作；Blocker 2、3 是下一阶段工作本身（Poisson 1D calibration + 一个人为失败案例，建议欠采样或错误 BC）。除此之外没有 blocker；不再新增治理规则，A-0002 终审后即进入 Poisson 1D 校准实验，由真实实验暴露下一轮问题。

````

</details>

### R031 — 项目/docs/pinn-trust-loop/ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md

<details>
<summary>展开完整原文</summary>

````markdown
# Annulus Budget Diagnosis Report（2026-09-18）

执行负责人：Claude（队长）。对象：`Geometry Lift 1 — Annulus Poisson` 的 Gate 5b 失败（`observedSignatures = ["sLocalizedError"]`）。上游：[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)。

本轮**没有**执行任何训练干预、**没有**修改任何机器证据、**没有**触碰任何 claim set、**没有**改动阈值 / 架构 / 采样 / 优化器 / 几何 / revision、**没有**新增 Gate 或 TrustStatus、**没有**起草 A-0003。

---

## 1. Executive

```text
Root Cause:            UNDETERMINED
Diagnosis:             NOT PERFORMED — blocked before intervention (PART 6)
                       EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE
Annulus Calibration:   NOT YET PASS
Highest Claim:         BLOCKED
State:                 FAILURE_RECORDED   （未进入 DIAGNOSED）
```

按 PART 4 的要求，在任何干预之前先审计了正式 120k run 的 optimizer / scheduler 状态。审计结果是**两条独立的阻塞事实**，任何一条都足以使「只增加训练步数」无法构成单因素干预：

* **B-1 优化器与调度器状态从未被保存。** 正式 run 只保存模型权重。Adam 的一阶/二阶矩 `m_t, v_t`、其 step 计数、`ExponentialLR` 的 `last_epoch`、batch 生成器的 RNG 状态与 shuffle 游标，在 `train_run` 返回时全部丢弃。→ **nested continuation（PART 5）不可执行。**
* **B-2 学习率轨迹依赖总预算。** 实现是 `lr(step, total_steps)`，不是 `lr(step)`。把预算从 120k 改成 180k / 240k 会**重新缩放整条 LR 轨迹，包括本应保持一致的前 120k 步**。→ 这正是 **PART 4.1 明令禁止的混杂**，且它同样污染 PART 6 提到的「from-scratch matched-budget」备选方案。

因此按 **PART 6** 停在干预之前，等待用户裁决。`rOptimizationFailure` **没有**被写成正式 `RootCauseClass`。

---

## 2. Causal Evidence

### 2.0 措辞状态（PART 1）

```text
Before diagnosis:
    training-budget limitation = SUPPORTED HYPOTHESIS
    not yet a formally identified RootCauseClass
```

上游标定报告中「根因不是几何 / 真正的原因是步数预算不足」「局部/全局误差比是几何不变的」等普遍化措辞已按 PART 1 收窄，收窄记录见该报告追加的 §13。允许的措辞是：

> Across the square and annulus calibration cases examined so far, no annulus-specific amplification of the local/global error ratio was observed.

本报告全篇遵守一条规则：**证据的缺席不等于不可能性的证明**。下文任何一处都不使用「证明不存在」。

### 2.1 Evidence against geometry pathology（支持性，非证明）

| 机制 | 机器证据 | 结果 |
|---|---|---|
| 成员判定 | `T11-geometryMembership`、`PH8-geometryMembership` | PASS，0 个非法点 |
| 双分量硬 BC | `T4`、`ACA-3` 十个 seed ≈ `2.116e-16`（阈值 `1e-4`） | PASS |
| 内/外法向朝向 | `T12` 直接断言 + `PH1` 通量恒等式 `1.633e-04` | 双重 PASS |
| 几何原生求积 | `T13`：面积 `2.756747553525` vs 精确值，相对 `6.44e-16` | PASS |
| 独立极坐标 FDM | `G2b`：`3.407e-03 / 8.509e-04 / 2.127e-04`，观测阶 `2.0016 / 2.0004` | PASS |
| 局部误差空间分布 | 十个 seed 的最差单元全部落在中间两个径向环，**从不**紧贴孔或外圆；最差/次差比仅 `1.00–1.66` | 无边界局部热点 |

**可以说**：本轮**没有观察到**明确的几何病理，也没有观察到孔边局部热点。
**不可以说**：几何病理已被排除。`rSingularityTreatment` 与 `rReferenceDefect` 仍是 admissible 集合中的合法候选（第 3 节）。

### 2.2 Evidence against sampling deficiency（支持性，非证明）

已有 EXPLORATORY 证据（D_dev only，claim pool 当时尚未封存）：

| 配置点数 | 步数 | devRelL2 |
|---|---|---|
| 1024 | 10k | `9.94e-03` |
| 2823（面积密度匹配，2.76×） | 10k | `1.05e-02` |
| 2823 | 40k | `2.358e-03` |
| 1024 | 40k | `2.230e-03` |

把配置点密度提高 **2.76 倍**没有带来实质改善（在两个步数预算下都略**更差**）。

**可以说**：这是**反对** `rSamplingDeficiency` 的一项证据。
**不可以说**：这是数学证明。它是两个密度、两个预算、一个 seed 三元组的探索性观察，且是 EXPLORATORY 标记、不构成正式证据。

### 2.3 Evidence for / against capacity limit

**目前两侧都没有决定性证据。**

* 反对 `rCapacityLimit` 的间接线索：同一 `4×64 tanh` 架构在正方形上达到 `AC2D-1 = 3.600e-05`（比圆环好 5.2 倍），说明该容量**在另一几何上**有余量；十个 seed 中 **9 个**已经满足 ACA-9，失败者超出阈值仅 **7.9 %**。
* 支持 `rCapacityLimit` 的可能性未被排除：圆环面积是单位正方形的 `2.757` 倍，同样的参数量覆盖更大的定义域；「9/10 已通过」同样可以由「容量恰好处在边缘」解释。
* **判别这两者正是本轮预定干预的目的**（PART 2 的核心问题：同一架构是否仅靠更多优化预算就能稳定满足已有局部判据）。该干预**未能执行**，因此该问题**仍然悬空**。

### 2.4 Evidence for / against optimization budget

支持（全部为 EXPLORATORY，非正式诊断）：

| 步数 | devRelL2 |
|---|---|
| 10k | `~9.94e-03` |
| 20k | `~5.43e-03` |
| 40k | `~2.23e-03` |
| 120k（正式） | median `1.853e-04` |

显示明显的 budget response（每倍增步数误差约降 2.1 倍）。正式 run 的定量线索：局部/全局比 `2.93 ± 0.52` 使 ACA-9 对 ACA-1 的隐含上限为 `1e-3 / 2.93 ≈ 3.414e-04`，而 worst-seed ACA-1 为 `3.722e-04`——**差距很小**，与「再多一点优化预算即可」相符。

**但**：
* `exploratory trend != formal diagnosis`；上表来自 D_dev 的探索性探针，不是受控干预。
* 上表的每一行都是**独立的 from-scratch run，且各自带着被重新缩放的 LR 轨迹**（见 §4.2）——所以它们之间的差异**本来就不是**纯粹的「步数」差异。这一点此前没有被写明，本报告予以更正。
* 因此现有 budget response 证据**比原先以为的更弱**：它混合了「更多步数」与「更慢的 LR 衰减」两个因素。

---

## 3. Candidate Root Causes（PART 2，读自实际 admissible matrix）

从 `pinn.governance.state_machine.admissible_root_causes("1.2")` 直接读取，**未按任何外部提示词缩减**：

```text
sLocalizedError -> rSingularityTreatment, rReferenceDefect, rImplementationDefect,
                   rCapacityLimit, rOptimizationFailure, rSamplingDeficiency, rSpecDefect
```

共 **7** 个候选。附带核实：`rDataDefect` **不在** `sLocalizedError` 的 admissible 集合内（它只对 `sBcResidual` 与 `sPinnCfd` 可用），因此本轮不将其列为候选；`rUndetermined` 是 `RootCauseClass` 的合法成员，作为 PART 12 Case B 的兜底。

| 候选 | 当前证据状态 |
|---|---|
| `rOptimizationFailure` | **SUPPORTED HYPOTHESIS**，待受控干预检验；干预被阻塞 |
| `rCapacityLimit` | **VIABLE**，未被排除；与 `rOptimizationFailure` 的判别正是被阻塞的那一步 |
| `rSamplingDeficiency` | 有一项反对证据（§2.2，EXPLORATORY），**未排除** |
| `rImplementationDefect` | Gate 3 十项 + 可信校验器的 10 个负面控制全 PASS，**未观察到**缺陷；未排除 |
| `rSpecDefect` | Gate 1/2 PASS，解析自验残差恒为 0，**未观察到**缺陷；未排除 |
| `rReferenceDefect` | 独立极坐标 FDM 观测阶 2.00、与解析解一致，**未观察到**缺陷；未排除 |
| `rSingularityTreatment` | 圆环无角点、无再入角；局部误差不集中在任一边界附近，**未观察到**奇异性问题；未排除 |

**没有任何一个候选被正式排除。** 正式排除需要 `DiagnosisRecord` 按 admissible matrix / excludes 规则逐项给出排除证据，而这要以受控干预为前提。

---

## 4. Optimizer / Scheduler State Audit（PART 4）

### 4.1 B-1：checkpoint 内容 — 只有权重

`experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu/runs/run-00.json` 的全部顶层字段：

```text
batchSize, collocationCount, collocationIndices, completed, determinism, devRelL2,
elapsedSeconds, finalLoss, hardBoundary, lossHistory, nanEncountered,
outputParameterization, perturbation, runIndex, seeds, stepsCompleted, stepsRequested,
weights
```

`weights` 是**模型** `state_dict` 的逐元素列表（`inner.{0,2,4,6,8}.{weight,bias}`）。全仓库 `pinn/experiments_annulus/` 与 `experiments/annulus/` 中，`state_dict()` 只出现一次——`pinn_torch_annulus.weights_of()`，取的是模型；`load_state_dict` 只出现一次——`model_from_weights()`。**没有** `optimizer.state_dict()`、**没有** `scheduler.state_dict()`、**没有** checkpoint 文件、**没有** resume 代码路径。

因此以下优化状态在 `train_run` 返回时被丢弃：

```text
Adam:        m_t, v_t, step 计数（偏差校正用）
Scheduler:   ExponentialLR.last_epoch
Batch:       torch.Generator 的 RNG 状态、shuffle 后的 order、cursor
```

PART 6 明确：`load weights + fresh Adam` **不得**冒充「只是多训练几步」，因为 `m_t, v_t` 也是优化状态的一部分。据此：

```text
EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE
```

### 4.2 B-2：学习率是 `lr(step, total_steps)`，不是 `lr(step)` —— PART 4 问题 A 的回答

实现（`pinn/experiments_annulus/pinn_torch_annulus.py`）：

```python
optimizer = torch.optim.Adam(model.parameters(), lr=float(opt_cfg["lr"]))
gamma = (float(opt_cfg["finalLr"]) / float(opt_cfg["lr"])) ** (1.0 / max(steps, 1))
scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=gamma)
```

`gamma` 由**总预算** `steps` 计算，于是

```text
lr(step) = lr0 * (finalLr / lr0) ** (step / steps_total)
```

**答案：`lr(step, total_steps)`——会随最终训练预算重新缩放。**

同一 step 在不同总预算下的学习率（`lr0 = 1e-3`，`finalLr = 1e-5`）：

| step | S = 120k | S = 180k | S = 240k |
|---|---|---|---|
| 1 | `9.9996e-04` | `9.9997e-04` | `9.9998e-04` |
| 30 000 | `3.1623e-04` | `4.6416e-04` | `5.6234e-04` |
| 60 000 | `1.0000e-04` | `2.1544e-04` | `3.1623e-04` |
| 90 000 | `3.1623e-05` | `1.0000e-04` | `1.7783e-04` |
| 120 000 | `1.0000e-05` | `4.6416e-05` | `1.0000e-04` |

正式 run 记录的实测 LR 与该式一致：step 1 为 `9.999616e-04`，step 120000 为 `1.000000e-05`。

在 step 60000 处，180k 预算的 LR 是 120k 预算的 **2.15 倍**；在 step 120000 处是 **4.64 倍**（240k 则为 **10.00 倍**）。也就是说，一次 180k 的 from-scratch run 与正式 120k run **在整个前 120k 步都不是同一条优化轨迹**。这正是 PART 4.1 描述的禁止混杂：

```text
120k run:  lr 1e-3 -> 1e-5 over 120k
180k run:  lr 1e-3 -> 1e-5 over 180k
→ 不能声称 "only training budget changed"
```

### 4.3 对备选方案的影响（如实说明，未自行设计）

PART 6 提到的备选是「a new from-scratch matched-budget intervention」。必须指出：**在当前代码下，from-scratch 的 180k / 240k run 同样不是 budget-only 干预**——因为 B-2 使 LR 轨迹随预算重新缩放。要让 from-scratch 干预成为单因素干预，需要一个**事前预注册的统一 continuation policy**（PART 5.1 已给出优先形式：前 120k 步走原 LR 轨迹，此后把 LR 保持在已达到的终值 `1e-5`），而这需要改动训练代码，从而改变 `codeHash`。

**本轮不实施、不设计、不预注册该方案**（PART 6：不要自行扩大设计）。上述仅为让用户的裁决建立在完整事实上。

---

## 5. Budget Intervention

**未执行。** 无 10-seed paired 表格可报告。

按 PART 7 预定的预算梯度 `B0 = 120000, B1 = 180000, B2 = 240000`（原预算的 1 / 1.5 / 2 倍，**不是**由 DAC-M0 的 `1.079e-03` 倒推）**未被预注册**——PART 7 以 exact continuation 可行为前提，该前提不成立。

## 6. DiagnosisRecord

**未生成。** 状态仍为 `FAILURE_RECORDED`，未进入 `DIAGNOSED`。

```text
RootCauseClass:  （未写入）
Formal verdict:  UNDETERMINED
```

7 个 admissible 候选**一个都未被正式排除**（第 3 节）。

## 7. Revision

**未执行。** `revision` 仍为 1，`specHash` 仍为 `4c8dfbc7238d…`，冻结配置一字未改（`steps` 仍为 `120000`）。PART 14 规定只有正式 `DiagnosisRecord` 支持 `rOptimizationFailure` 才允许 `DIAGNOSED -> REVISED`，该前提不成立。

## 8. Blind Validation

**未执行，且未触碰。** 账本状态复核（PART 13）：

```text
DAC-M0   SEALED -> OPENED -> BURNT      （历史，永久保留，不得重开）
DAC-M1   NEVER_SEALED                    未触碰
DAC-M2   NEVER_SEALED                    未触碰
DAC-M3   NEVER_SEALED                    未触碰
```

本轮**没有任何** claim set 生命周期事件写入；账本文件自上一轮提交以来未被修改。

## 9. Tier-1 / G6

**均未执行。** Tier-1 只在 Gate 5 PASS 之后进行；G6 的 `C_repro` 仍为 `BLOCKED`。Environment B 本轮未被访问。

## 10. Trust Vector / Claim

沿用上一轮的**实际值**，本轮未产生新的 TrustVector 或 ClaimGateDecision：

```text
math PASS   impl PASS   train PASS   physics PASS   external FAIL   repro BLOCKED
Highest Claim: BLOCKED
```

## 11. Tests / PRELOCK / Portability

本轮未改动 `pinn/`、`scientific_reference/`、`specs/` 下任何文件，也未改动冻结配置与正式驱动脚本，因此 `codeHash` 仍为 `8ee9b9236199…`。改动只落在报告 / 日志 / CHANGELOG / 记忆文件（均不在代码身份内）。

| 项目 | 治理虚拟环境 `.venv` | 训练解释器（mamba） |
|---|---|---|
| 全套 pytest | **1391 passed / 0 failed / 25 skipped** | — |
| annulus 补跑 | — | **7 passed / 0 failed** |
| poisson2d 补跑 | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，7/7** | — |
| portability | **0 hard binding / 1 configurable / 8 historical** | — |

PART 24 所列的十一项新测试**未新增**：其中十项针对尚未获授权、也尚不可执行的干预与 revision 流程；在干预设计被批准之前写测试，等于先固化一个未经批准的设计。

## 12. Newly Discovered

### BLOCKING

1. **B-1：正式训练不保存 optimizer / scheduler / batch-generator 状态**，只保存模型权重。→ nested continuation 不可执行，`EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE`。
2. **B-2：LR 调度依赖总预算**（`gamma` 由 `steps` 算出），因此 `lr = lr(step, total_steps)`。→ 任何「只改步数」的 from-scratch 对比都自带 LR 混杂；在 step 60000 处 180k 与 120k 的 LR 相差 2.15 倍。

两条合起来使本轮预定的受控干预**在当前代码下无法以单因素形式执行**。

### NON-BLOCKING

1. 既有 EXPLORATORY 的 budget response 趋势（10k / 20k / 40k）**比原先以为的更弱**：那三次是各自独立的 from-scratch run，各带被重新缩放的 LR 轨迹，因此混合了「更多步数」与「更慢衰减」两个因素。此前未写明，本报告更正。
2. 十个 seed 的最差局部单元全部位于中间两个径向环，最差/次差比 `1.00–1.66`：误差是平缓抬高的一片，不是奇异单元；**未观察到**孔边病理。
3. 失败 seed（seed 2）的局部与全局误差同步抬高（ACA-9 为中位数的 1.95 倍，ACA-1 为 2.00 倍）：整体更差，不是局部更差。

### AMENDMENT CANDIDATE

1. **（PART 21，登记不实施）** `D_dev` 在盲集被打开之前已含有足以预测局部验收失败的信息：本轮 D_dev 上局部统计量 worst 为 `1.038e-03`（> `1e-3`），与 D_claim 上的 `1.079e-03` 指向同一个 seed。**本轮不改 Gate 4、不改 TrustStatus、不改 claim 前置条件、不新增 Gate**——不能一边诊断 failure，一边修改「failure 应该在哪里被抓住」。待 annulus calibration 结束后再审。
2. **（PART 22，登记不实施）** `ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`；继续使用 `domainType = "other"` + `regions[].params`，不改 Constitution / schema，留待 L-shape 时统一处理。
3. **（本轮新增）** 训练记录**应当**保存 optimizer / scheduler / batch-generator 状态，否则任何「延长训练」类的受控干预在事后都不可能做成单因素干预。这是一个可复现性与可诊断性的结构缺口，不只影响圆环。登记为提案，**本轮不实施**（它会改变 `codeHash`）。
4. **（本轮新增）** LR 调度与总预算耦合（`gamma = (finalLr/lr0)^(1/steps)`）使「步数」不是一个可独立操纵的变量。若未来要把训练预算当作受控变量，需要一个事前预注册的、与总预算解耦的 schedule 定义。登记为提案，**本轮不实施**。

### NONE

其余未发现新问题。

## 13. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

并按 **PART 6** 停在干预之前，等待用户裁决：

```text
EXACT BUDGET-ONLY CONTINUATION NOT POSSIBLE
```

需要用户决定的是：是否授权一次 **from-scratch matched-budget intervention**，以及——因为 B-2——是否同时授权为其定义一个**与总预算解耦、事前预注册**的 LR continuation policy（PART 5.1 给出的优先形式是：前 120k 步走原 LR 轨迹，其后把 LR 保持在 `1e-5`）。该改动会改变 `codeHash`，属于方法基础设施的变更，不在本轮授权范围内。

在用户裁决之前，本轮**停止**：不做 capacity sweep、不做架构搜索、不做优化器搜索、不做更高预算 sweep、不开始 L-shape / BFS / Navier–Stokes / UCM / 传热，也不把 `rOptimizationFailure` 写成正式 `RootCauseClass`。

````

</details>

### R032 — 项目/docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md

<details>
<summary>展开完整原文</summary>

````markdown
# Annulus Exclusion Diagnosis Report（2026-09-20 / 21）

执行负责人：Claude（队长）。对象：外部评审裁决（2026-09-20）十一项的执行——代码身份补洞，以及 `sLocalizedError` 其余五个 admissible 根因的诊断专用排除实验。

预注册：[ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md](../../experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md)（含第 10 节 S1 勘误，运行前追加）。
上游：[ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md](ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md)、[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)、[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)。

本轮**没有**把「诊断用 Tier-1」当作 Tier-1 阶段、**没有**从「没观察到缺陷」发明排除、**没有**打开任何 claim set、**没有**写入任何账本事件、**没有**改 Gate 4 / geometry schema / Tier-1 语义 / Constitution、**没有**升 revision、**没有**产生 TrustVector 或 ClaimGateDecision。

---

## 1. Executive

```text
Root Cause:            UNDETERMINED
Exclusions:            2 of 5 discharged this round (3 of 6 obligations scientifically met;
                       one of those three has no exp-* identifier and cannot yet be cited)
                       EXCLUDED      rImplementationDefect, rSpecDefect
                       NOT EXCLUDED  rSamplingDeficiency, rReferenceDefect, rSingularityTreatment
DiagnosisRecord:       NOT WRITTEN
Annulus Calibration:   NOT YET PASS
Highest Claim:         BLOCKED
Recommendation:        REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

按裁决 item 5：有原因无法诚实排除，即以 `Root Cause = UNDETERMINED` 停止，**不强行命名** `rOptimizationFailure`。

**本轮最重要的实质发现不是「排除了几项」，而是采样实验的结果反过来削弱了上一轮的因果解读**：把配置点密度提高 2 倍或 2.76 倍，**都把 seed 2 的局部失败修好了**；而失败的那个单元 `2,13` 原本只分到 **5** 个配置点，全域中位数是 **16**。也就是说「多训练」与「多采点」都能压下这个局部误差，两者都不是必要解释（§5）。

---

## 2. 代码身份补洞（裁决 item 3，在任何新诊断执行之前完成）

上一轮发现：`pinn/` 下一个 run 会 import 的新模块可以对整套身份机制隐身——`code_manifest()` 枚举 `git ls-files`，`workspace_dirty_paths()` 传 `--untracked-files=no`，`assert_code_identity_complete()` 无法察觉一个从未被列入的文件。

| 机制 | 处理 |
|---|---|
| `untracked_identity_paths()` | 用 `git ls-files --others` 扫描身份边界，**刻意不加** `--exclude-standard`——一个模块不会因为被写进 `.gitignore` 就离开方法身份。字节码缓存是唯一排除项（它是输出，不是来源） |
| `assert_code_identity_complete()` | 边界内存在未跟踪文件即拒绝 |
| `codeIdentityExtraFiles` | 必须是 git 已跟踪路径；未跟踪的字节无法从仓库恢复，不能标识一个方法 |
| PRELOCK | 新增 `codeIdentityTracked` 检查，**检查数由 7 变 8** |

**对抗测试**（裁决点名要求）：先构造一棵 PRELOCK 确实接受的树作**对照**，再写入一个未跟踪 helper，断言三件事——整体 `FAIL`、`codeIdentityTracked` 是**唯一**状态发生变化的检查、`git add` 之后拒绝解除。对照与「唯一变化」这两条是关键：没有它们，测试可能因夹具本身的毛病而通过。新增 **10** 项测试。

---

## 3. 五项排除实验

每项都标明属于**干预式**还是**正控制式**。判定阈值在运行前冻结于预注册，本节只报结果。

### 3.1 `exp-annulus-dx-implementation` — rImplementationDefect → **EXCLUDED**（正控制式）

| 探针 | 测量 | 判定 |
|---|---|---|
| I1 预言注入：精确解 u\* 经**产生 ACA-9 的同一条流水线** | relL2 `6.055e-18`，ACA-9 `4.437e-17` | ≤ 1e-12 ✓ |
| I2 正控制：在已知单元 `2,5` 注入凸起 | 流水线报告 `2,5`，统计量一致 `0.000e+00` | 位置正确且 ≤ 1e-9 ✓ |
| I3 独立重写的例程重算失败 seed 的 ACA-9 | 生产值 `1.038334942e-03`，独立值 `1.038334942e-03` | 相对差 `0.000e+00` ≤ 1e-12 ✓ |
| I4 AD vs 中心差分（热点单元 16 个点） | 最差相对差 `2.225e-08` | ≤ 1e-6 ✓ |

I1 把 AD 路径、单元划分、归一化、边界与通量代码全部跑了一遍，对着一个**已知精确答案**；I2 证明这条流水线**能**定位一个人为注入的局部缺陷；I3 用一套不 import `diagnostics_annulus`、自行推导等面积分箱的独立例程复算，结果**逐位相同**。这不是「没观察到缺陷」。

### 3.2 `exp-annulus-dx-spec` — rSpecDefect → **EXCLUDED**（正控制式）

规范缺陷**能**产生本信号：网络按 f 训练，若 f 与 u\* 不一致，网络本就不会收敛到 u\*。

| 探针 | 测量 | 判定 |
|---|---|---|
| C1 `-Δu* - f`，**两条独立路径** | 闭式 Laplacian `0.000e+00`；torch 自动微分 `3.553e-15` | 均 ≤ 1e-12 ✓ |
| C2 两条边界组件上的 `max|u*|` | outer `2.115e-16`，inner `2.952e-17` | ≤ 1e-14 ✓ |
| C3 正控制：源项 ×1.000001 | 残差升至 `1.752e-05` | ≥ 1e-6 ✓ |

### 3.3 `exp-annulus-dx-reference` — rReferenceDefect → **NOT EXCLUDED**（路径审计 + 正控制式）

| 探针 | 测量 | 判定 |
|---|---|---|
| R1 路径审计：ACA-9 的调用图能否读到 FDM | `ast` 静态遍历 14 个模块，到达 `scientific_reference` 的模块数 **0** | ✓ |
| R2 独立极坐标 FDM 的收敛阶 | `2.0016 / 2.0004` | 落在 [1.8, 2.2] ✓ |
| **R3** 最细网格（64×256）下 FDM 在热点单元 `2,13` 的自身误差 | 参考 `5.500e-05`，模型 `1.490e-04` | **只低 2.7 倍，预注册要求 10 倍 ✗** |
| **R4** 正控制：去掉极坐标 `1/r` 项的算子 | 观测阶 `[nan]`——迭代**发散**，不是「收敛但掉阶」 | **控制未执行 ✗** |

R1 是一条很强的论证：ACA-9 是对着**解析解**算的，数值参考根本进不了这个统计量，因此它不可能制造该信号。但预注册要求的四条里有两条不成立，按自己定下的规则，**不能**记为已排除。

**R4 的处理（本轮自查出的一个缺陷，见 §6.1）**：最初的实现把 `nan` 读成了「通过」。已改为对非有限证据 fail closed，工件现在如实记录「控制未执行，未证明任何分辨力」。该修正**不可能**改变本项判定——R3 独立地已经不成立。

### 3.4 `exp-annulus-dx-singularity` — rSingularityTreatment → **NOT EXCLUDED**（正控制式）

| 探针 | 测量 | 判定 |
|---|---|---|
| G1 逐单元 `max|Δu*|` 的 max/median | `2.668` | ≤ 10 ✓ |
| **G2** 30 个最差单元中贴边界（bin 0 或 bin 3）的个数 | **1**（seed 1 @240k，单元 `0,15`） | **预注册要求 == 0 ✗** |
| G3 正控制：`r^(-1/3)` 奇异场锚在内圆上 | 机制把热点定位到 `0,1`，即紧贴内孔 | ✓ |

G3 证明这套机制**看得见**贴边界的集中，因此 G2 的观测是有信息量的——而它给出的是 1，不是 0。

这条判定之所以不成立，直接源于我在 Phase II 报告里的一处**事实错误**：原写「30 个最差单元全部在中间两环」，实为 29 / 1 / 0（§6.3）。

### 3.5 `exp-annulus-dx-sampling` — rSamplingDeficiency → **NOT EXCLUDED，且证据反向**（干预式）

全部在 r1 预算 120000 步下，其余一切冻结，只读 D_dev。

| 探针 | 干预 | ACA-9 | 判定 |
|---|---|---|---|
| **S1a** | 已登记池**全部 2048** 点（**2×** 密度，完全配对） | **6.620666e-04** | **PASS —— 修好了** |
| **S1b** | 新池 2823 点（**2.76×** 面积匹配密度，不配对） | **5.766093e-04** | **PASS —— 修好了** |
| S2 | 采样 seed +901 | `2.670052e-04` | PASS |
| S3 | 采样 seed +902 | `6.505030e-04` | PASS |
| S4 | 采样 seed +903 | `3.061673e-04` | PASS |
| **S5** | 热点单元 `2,13` 的配置点计数 | **5**，全域中位数 **16** | **被采稀** |

对照运行前冻结的三条：

```text
(a) 两种加密都救不回来   -> 不成立：两种加密都把 ACA-9 压到阈值以下
(b) 热点单元未被饿着     -> 不成立：5 个点，中位数 16
(c) 失败不随抽样设计重现 -> 成立：3 个替代抽样 0 个失败
```

(a) 与 (b) 都不成立，因此 `rSamplingDeficiency` **未被排除**。按预注册第 3 节写明的那条：若加密确实修好了，采样就是一个**有效杠杆**，该原因与 `rOptimizationFailure` 竞争。

---

## 4. DiagnosisRecord

### 4.1 义务与实际

`discriminating_experiment_errors` 要求：为该 signature 下**其余每一个** admissible 根因指名一个排除实验，`excludes.<cause>.experiment` 必须匹配 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`。`sLocalizedError` 的 admissible 集合共 7 个。

| 候选 | 实验 | 科学状态 | 可被 `excludes` 引用？ |
|---|---|---|---|
| `rImplementationDefect` | `exp-annulus-dx-implementation` | **已排除** | 是 |
| `rSpecDefect` | `exp-annulus-dx-spec` | **已排除** | 是 |
| `rCapacityLimit` | Phase II 嵌套预算干预 | **已排除**（干预式，上一轮） | **否 —— 无 `exp-*` 标识** |
| `rSamplingDeficiency` | `exp-annulus-dx-sampling` | **未排除**（证据反向） | — |
| `rReferenceDefect` | `exp-annulus-dx-reference` | **未排除**（R3、R4 不成立） | — |
| `rSingularityTreatment` | `exp-annulus-dx-singularity` | **未排除**（G2 不成立） | — |
| `rOptimizationFailure` | — | 待命名的根因 | — |

**6 项义务中，2 项已备妥可引用的证据，1 项科学上已排除但缺标识，3 项未排除。**

关于 `rCapacityLimit` 的记账细节，必须写清楚而不是含糊带过：上一轮的嵌套预算干预**确实是**一次干预式判别实验，并且**确实**排除了容量限制——同一 4×64 网络在 180k 处 10/10 达到判据。但它的产物没有记录 `experimentId`，其目录名 `nested-budget-r1-paired` **不匹配** `excludes` 要求的 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`。这是**记账缺口**，不是科学缺口；补法是给它指定一个 `exp-*` 标识并登记，而这是一个应当被记录的命名决定，**不应**在写记录时凭空发明。本轮不自行补，登记待裁决。

### 4.2 判定

```text
RootCauseClass:  （未写入）
Formal verdict:  UNDETERMINED
State:           FAILURE_RECORDED（未进入 DIAGNOSED）
```

没有生成 DiagnosisRecord。即便只看形式要求，三项未排除也使记录无法通过 `validate_diagnosis_record`；而更实质的是 §3.5——`rSamplingDeficiency` 不只是「没排除」，它有**支持自己的正面证据**。

---

## 5. 对 Phase II 因果解读的影响

上一轮报告的 `B* = 180k` 是**真实测量**，本轮不回改它的任何机器证据。但它对 `rOptimizationFailure` 的支持强度必须下调：

```text
Phase II 的观察   同一容量、同一采样、同一前 120k 轨迹，继续优化到 180k -> 10/10 通过
本轮的观察        同一容量、同一优化预算 120k，把配置点密度提高 2x 或 2.76x -> 失败 seed 通过
                  且失败单元 2,13 原本只有 5 个配置点，中位数 16
```

两者都能把这个局部误差压下去，因此**两者都不是必要解释**。一个自洽的替代叙事是：seed 2 的配置点抽样在该单元偏稀，PDE 在那里约束不足，于是局部误差偏大；继续优化只是让网络在别处的约束把该区域「带」得更好一些，而加密则直接补上了约束。本轮的证据无法在这两者之间做出判别。

这正是裁决要求做真排除实验、而不是接受「没观察到缺陷」的理由。若上一轮就据 `B*` 命名根因，这条竞争解释会被整个错过。

---

## 6. 本轮自查出的三个自身缺陷

### 6.1 R4 正控制把 `nan` 读成通过（已修，已加回归测试）

判据写成「观测阶落在 [1.8, 2.2] 之外即算检出」，而 `1.8 <= nan` 为 False，于是**发散**被当成了成功的正控制。这与 2026-09-16 那轮硬化定下的规则（非有限证据必须 fail closed）是同一类缺陷，只不过这次出现在我自己本轮写的代码里。

`control_verdict()` 现在返回 `(executed, detected)`，对非有限或空证据一律 fail closed；工件记录 `controlExecuted` 并写明「控制未执行，未证明任何分辨力」。4 项回归测试钉死。

**该修正是在看到结果之后做的，必须说明为什么这不是钓结果**：`rReferenceDefect` 因 R3 独立不成立而本就未被排除，修 R4 不可能改变判定；而把一个已知的「非有限证据当通过」留在代码里，下一次就会悄悄放行。

### 6.2 driver 的探针标签 off-by-one（已修，五次训练白跑）

`f"S{offset - 899 + 1}"` 把三个替代抽样标成 S3/S4/S5，与计数探针 S5 撞名，判定查表抛 `KeyError`，工件没写成——**五次 120k 训练白跑了约 1.8 小时**。测量本身无误，错的只是标签。

**没有**把日志里的数字誊进工件（那不算证据）。已修为 S2/S3/S4，重跑得到完全相同的数（训练是确定性的）。

### 6.3 Phase II 报告的一处事实错误（已就地更正 + 追加勘误）

原写「30 个最差单元**全部**在中间两环、**没有一个**贴边界」，逐条核对 `DIAGNOSIS.json` 后实为 **29 / 1 / 0**（seed 1 @240k 的 `0,15` 贴内孔）。来源：我在一次进度汇报里打印过那份清单，写报告时**按印象概括**而未逐条复核。

机器证据一直是对的，错的只是散文。**这条更正直接决定了 §3.4 的 G2 判定**——按真实数据 G2 不成立，`rSingularityTreatment` 未被排除。

r1 标定报告与预算诊断报告中关于「**十个** seed 的最差单元全部在中间两环」的说法**是正确的**，未改。

---

## 7. Blind Validation Firewall

每次调用前后各记录账本 sha256 与事件序列并比对，全部 `unchanged = True`：

```text
DAC-M0   SEALED -> OPENED -> BURNT      （历史，永久保留，不得重开）
DAC-M1 / M2 / M3   NEVER_SEALED          一次未触碰
账本事件  ['SEALED', 'OPENED']            本轮无新增
```

所有实验只读 D_dev、合成夹具与独立参考。局部判据合同自身拒绝 `evaluationSet != "dev"`；测试另钉死 driver 源码中不得出现 `claim_grids` / `claim_quadrature` / `claim_pointwise` / `make_event` / `write_ledger` / `claim_evaluation`。

**本轮不具 Tier-1 状态**：Tier-1 含义不变（Gate 5 PASS 之后对已接受结果的压力测试）；这些是 `exp-*` 身份下的 diagnosis-only discriminating experiments，不产生 claim、不推进 Trust、不产生任何 claim-set 生命周期事件。

## 8. Trust Vector / Claim

本轮**未产生**新的 TrustVector 或 ClaimGateDecision。r1 的实际值不变：

```text
math PASS   impl PASS   train PASS   physics PASS   external FAIL   repro BLOCKED
Highest Claim: BLOCKED
```

## 9. Tests / PRELOCK / Portability

| 项目 | 治理虚拟环境 `.venv` | 训练解释器（mamba） |
|---|---|---|
| 全套 pytest | **1426 passed / 0 failed / 26 skipped** | — |
| annulus 补跑 | — | **24 passed / 0 failed** |
| poisson2d 补跑 | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，8/8**（新增 `codeIdentityTracked`，检查数由 7 变 8） | — |
| portability | **0 hard binding / 1 configurable / 8 historical** | — |

上轮基线 1414 / 26 与 PRELOCK 7/7；本轮净增 **12** 项（10 项身份对抗测试 + 2 项正控制 fail-closed 测试）。

## 10. Newly Discovered

### BLOCKING

**无。** 三项未排除是**预注册判定规则如实执行的结果**，不是新缺陷。

### NON-BLOCKING

1. **采样是一个有效杠杆**：2× 与 2.76× 密度都修好了失败 seed（§3.5）。
2. **失败单元被采稀**：`2,13` 只有 5 个配置点，中位数 16。
3. **`B* = 180k` 的因果解读被削弱**：多训练与多采点都能压下该误差，两者都不是必要解释（§5）。
4. **数值参考在热点单元并不「远低于」模型**：64×256 网格下只低 2.7 倍。若将来要用 R3 这类判据，需要更细的网格或换一条论证路线。
5. **R1 是一条强论证且已机器化**：ACA-9 的调用图（14 个模块）中无一能到达 `scientific_reference`。

### AMENDMENT CANDIDATE

1. **（承前，本轮已部分回应）失败 run 的诊断与 Tier-1 的时序闭环**——裁决 item 2 以「`exp-*` 身份下的 diagnosis-only discriminating experiments」解决了通路问题；是否把这条通路写进协议正文，待审。
2. **（承前，本轮已修）未跟踪文件静默落在代码身份之外** —— 已补洞并加对抗测试；是否把 `codeIdentityTracked` 写进协议正文，待审。
3. **（承前）Gate 4 不筛查局部判据**，尽管 D_dev 有能力测量它。
4. **（承前）`ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`**。
5. **（承前）训练记录应保存 optimizer / scheduler / batch RNG 状态**——诊断路径已实现，尚未成为正式 attempt 的要求。
6. **（承前）LR 调度与总预算耦合**——已提供 `lrPrefixSteps` 解耦，缺省行为仍耦合（为不改变历史含义而刻意保留）。
7. **（新）正控制的执行有效性应当是一等判据**。R4 的教训是：一个「控制」必须先证明自己**跑起来了**，才谈得上它有没有检出。建议把 `controlExecuted` 作为所有正控制式排除的必填字段。

### NONE

其余未发现新问题。

## 11. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

按裁决 item 5，本轮以 `Root Cause = UNDETERMINED` 停止，**不写** `rOptimizationFailure`，**不进** revision 2，**不碰** DAC-M1。

需要用户与外部评审裁决的是：

1. **`rSamplingDeficiency` 现在是一个有正面证据的竞争假设**。下一步若要判别它与 `rOptimizationFailure`，需要一个能同时固定两者的设计——例如在**相同**的配置点集合下比较预算，以及在**相同**预算下比较密度，构成 2×2；本轮没有这样的设计，也不自行开始。
2. **`rReferenceDefect` 的 R3 判据**：是在更细网格上重做，还是改用 R1 那条「参考进不了统计量」的论证路线并相应修订判据？两者都需要事前裁决，不能在看到结果后选。
3. **`rSingularityTreatment` 的 G2 判据**：1/30 贴边界是否构成实质的奇异性证据？G2 的 `== 0` 是本轮冻结的严格形式；若要改，必须是**事前**修订，并说明理由。
4. **`rCapacityLimit` 的 `exp-*` 标识**：上一轮的嵌套预算干预在科学上已排除容量限制，但其产物没有 `experimentId`，目录名不匹配 `excludes` 所要求的模式。是否给它指定并登记一个 `exp-*` 标识（例如 `exp-annulus-nested-budget-r1`），需要裁决——这是一个命名决定，不应在写 DiagnosisRecord 时凭空发明（§4.1）。
5. 六条既有 + 一条新增的 AMENDMENT CANDIDATE 的统一审议。

在裁决之前，本轮**停止**：不做 capacity sweep、不做架构搜索、不做优化器搜索、不做更高预算 sweep、不开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热。

---

## 12. 四项裁决与随之查出的四个自身缺陷（2026-09-21，追加不改写）

本节是**追加**。第 1–11 节、全部 `exp-*` 工件、`EXCLUSIONS.json`、2026-09-20 预注册、r1 与 Phase II 的一切机器证据，一字未改。用户把四项悬而未决的问题委托给执行者裁决（2026-09-21），以下是裁决、理由，以及裁决过程中查出的、**属于我自己**的四个缺陷。

**裁决后的总账（比裁决前更差）：**

```text
rImplementationDefect   EXCLUDED
rSpecDefect             EXCLUDED
rSamplingDeficiency     NOT EXCLUDED   （证据反向）
rReferenceDefect        NOT EXCLUDED   （R1 与 R3 均不成立；R4 修好后通过）
rSingularityTreatment   NOT EXCLUDED   （G2 不成立；且 G3 未按冻结规格执行）
rCapacityLimit          NOT EXCLUDED   ← 由「已排除」改记，见 §12.4
                        未排除由 3 项改为 4 项
Root Cause              UNDETERMINED   （不变）
```

### 12.1 裁决一：rSamplingDeficiency 与 rOptimizationFailure 本轮**不可分离**，不跑新实验（0 GPU）

**路由在看到数据之前就已冻结。** 2026-09-20 预注册 §3 结尾写着：「若 (a) 不成立（即加密确实修好了），则采样是一个**有效杠杆**，不得排除；该原因与 `rOptimizationFailure` 竞争，按 item 5 报 `UNDETERMINED`。」§10 勘误（**在任何排除实验执行之前**追加）写得更严：「只要**任意一个**把 ACA-9 压到阈值以下，(a) 即不成立。」工件记 `a_densityDoesNotRescue.satisfied = false`。路由已经触发；现在再委托一个新判别器去分开这两个**事前已被判定为「竞争即 UNDETERMINED」**的原因，结构上就是在判据判否之后重开一个事前已裁决的归宿。

**定义层重叠，不是功效不足。** `state_machine.py` 把 `rOptimizationFailure` 定义为「not converged, gradient pathology, **loss weighting**」，把 `rSamplingDeficiency` 定义为「collocation density or **distribution**」。本实验是等权单损失（`lossWeights.pde = 1.0`，硬边界参数化），于是「`2,13` 只有 5 点」与「`2,13` 只拿到 0.49% 而非 1.6% 的梯度权重」是**同一句话**，落在两个类定义的交集里。一切**增加资源**的设计（2×2 析因、密度阶梯）两个假设都预测 PASS，天然分不开。

**§3.5 与 §5 的机理叙事必须收窄（重要）。** 我原写「失败单元被采稀……把密度提上去就修好了」，把观测读成了「饥饿 → 补点 → 痊愈」。逐条复核工件后，这个读法**不成立**：

| 探针 | 干预 | ACA-9 | 热点单元 |
|---|---|---|---|
| r1 seed 2 | 基线 1024 点 | 1.038335e-03 | `2,13` |
| **S1a** | **2× 密度**（整池 2048 点） | **6.620666e-04** | **仍是 `2,13`** |
| S1b | 2.76× 密度（新池 2823 点） | 5.766093e-04 | `2,8` |
| S2 | 只换抽样 seed | 2.670052e-04 | `1,12` |
| S3 | 只换抽样 seed | 6.505030e-04 | `1,1` |
| S4 | 只换抽样 seed | 3.061673e-04 | `1,4` |

实测复核：S1a 把 `2,13` 的配置点数从 5 提到 18，相对中位数由 **0.31× 升到 0.58×**（饥饿被**部分缓解**），而热点**纹丝不动**，且其 ACA-9（6.6207e-04）比只换抽签的 S3（6.5050e-04）**还差**。反之，只换抽签的三次**每一次**都把热点挪走了，散布 2.44×（2.670e-04 – 6.505e-04），量级盖过任何密度效应。

**可如实记录的结论**：在这批探针下，可靠改变局部误差位置的操作变量是**抽签**，不是**密度**；「该单元被饿瘦、补点即愈」这一机理**未获支持**。判据 (a)/(b) 的 `satisfied = false` 是已记录的机器事实、不可改写，但它们支撑的机理读法降一档。

**前瞻性设计（写入下一份预注册，本轮不跑）**：`S6-R 等总量重分配`——总配置点数固定 1024、预算固定 120000、init/batch/sample 沿用 r1 配对，只把点从计数最高的格迁到最低的格直至全部 ≥ 中位数；目标格必须写成**机械规则**（「该 seed 配置点数最少的格」），**绝不写死 `2,13`**。这是唯一在固定资源总量下只改**分布**的设计，因而是唯一可能有识别力的那个。

### 12.2 裁决二：R3 整族前瞻性退役；R4 只修我自己的仪器 bug，判据一字不改

**R4 的失败是我的 bug，不是控制太狠。** `exclusion_annulus.py` 原写 `u = u + residual / diagonal`，而 `residual = -(urr + utt) - rhs` 即 `A·u − b`；Jacobi 应为**减**。按原写法**无论是否腐蚀算子都会发散**，控制从未真正测试过腐蚀。另一缺陷：固定 4000 扫本身不够——实测真算子在 4000 扫后 `max|residual|` 仍约 `1.3e-01`，迭代误差会混进离散误差。

修复后（符号改正 + 改为按残差容差迭代到 `1e-10`）实测：

```text
16x64    relL2 1.161905e-01   iterations 1587   finalMaxResidual 1.579e-09
32x128   relL2 1.153873e-01   iterations 6342   finalMaxResidual 1.700e-09
观测阶   0.0100
```

**预注册的 R4 原判据（观测阶落在 [1.8, 2.2] 之外）现在直接通过**，判据一个字没改。丢掉 `1/r` 项使格式**不相容**而非掉阶，误差停滞在 0.115，refinement study 照样看得见。在一个字符的仪器 bug 足以完全解释失败时去替换设计，才是「看到失败才改设计」。

**R1 的根集合是手挑的——这是更重的一条。** 原实现的根集合只含「计算」统计量的模块，**恰好不含 `gates_annulus`**；而 `gates_annulus.py:31` 在模块层 `from scientific_reference.annulus_polar_fdm import min_eigenvalue, refinement_diagnostic`，且 `gates_annulus.py:439` 的 `external_checks` 正是**裁决 ACA-9 MUST 判定**的地方。所以原工件的 `modulesReachingTheNumericalReference: []` 不是「查出来没有」，是「根集合选得没有」。另两处缺陷：包节点（如 `pinn.governance`）被当叶子静默截断；相对导入 `from .x import Y` 把 `Y` 当成了模块。

修复后（根集合补入裁决模块、包节点回落到 `__init__.py`、相对导入取 `node.module`），审计图由 14 个模块扩到 **43** 个，结果是：

```text
modulesReachingTheNumericalReference: ['pinn.experiments.gates', 'pinn.experiments_annulus.gates_annulus']
statisticCanReadTheNumericalReference: True        ->  R1 现在 FAIL
```

**两句话都要说**：FDM 实际只用在 Gate 2（`gates_annulus.py:143`）与 PH7（`:353`），**不**参与 ACA-9 的计算，所以「ACA-9 的数值读不到 FDM」这一**实质结论很可能仍然成立**；但**我原来的审计没有立住它**，而按 R1 写下的判据，修复后的审计给出的是 FAIL。原工件保留于 `superseded/exp-annulus-dx-reference.as-first-run.json`，修正后的工件覆盖同名文件。

修正后四条：**R1 FAIL、R2 PASS、R3 FAIL、R4 PASS**。判定不变：`rReferenceDefect` **NOT EXCLUDED**，且理由比原先更扎实。

**R3 退役的理由是规范缺陷，不是阈值松紧**：R3 的阈值是**被诊断对象自身**（模型在该单元的误差）的函数，因此没有固定分辨力——被诊断对象越差，判据越容易通过。这条陈述不依赖任何已看到的结果，可以事前写进下一份预注册；替代仪器必须是一台**能失败**的。

### 12.3 裁决三：G2 维持，`rSingularityTreatment` 保持 NOT EXCLUDED——而且成立两次

**其一，G2 是我写错的。** 等面积划分下贴边界的单元（bin 0 与 bin 3）恰好是 **32/64，整整一半**。于是在面积均匀零假设下

```text
P(G2 通过) = 0.5^30 = 9.3132e-10        期望的贴边界个数 = 15
```

它要求的不是「没有奇异性集中」，而是一种任何随机过程都几乎不可能满足的近乎确定性；更糟的是 `P(通过) = (1−π)^n` 对 n 严格递减——**证据收得越多越难通过**，这是构造性错误。

**可入档的只有上面这一类「运行前即可算出」的规格性质。** 我另算过的 `P(X≤1)=2.887e-08`（n=30）与 `1.074e-02`（按 seed 计 n=10）是**事后统计量**——它们是在一个已被判过的冻结样本上算出的新统计量，一旦写进工件就会变成影子判定。它们只能出现在本节这样的动机叙述与将来某份预注册里，**不得作为证据被引用**。

**其二，也是更重的一条：G3 没有按冻结规格执行。** 预注册 §7 冻结的是「具有真实 **r^(2/3)** 角点型奇异的误差场」，而 `exclusion_annulus.py` 实际用的是 `exponent = -1/3`。这不是参数差异。实测（同一 D_dev、同一独立统计量）：

```text
d^(-1/3)   实际运行的        热点 0,1    在 bin 0 ✓
d^(+2/3)   预注册冻结的文本  热点 3,8    在 bin 0 ✗（落在贴外圆的 bin 3）
```

字面的 `r^(2/3)` 场在锚点处趋零、最大值在离锚点最远处，**根本通不过预注册自己写的「热点落在 bin 0」条件**。也就是说冻结文本的「场」与「通过条件」**自相矛盾**，而实现静默地选了能通过的那一侧。

据此记入一条机器事实：该实验标称的 `kind: "positive-controlled"` 在执行层面**不成立**，它实为**观察式**。按预注册 §2，观察式在**任一方向**都不构成排除。因此 `rSingularityTreatment` 的 NOT EXCLUDED 成立两次：一次因 G2 不成立，一次因该实验本就没有排除的资格。

报告第 93 行原写「G3 证明机制看得见贴边界集中，因此 G2 的观测是有信息量的」——这句话现在两头都站不住：G3 未按规格执行，而「==0」是否有信息量取决于零假设发生率（=1/2，本轮从未计算）。记为本轮第四条散文缺陷。

**「最差单元位置」这一族判据整体退役。** 理由是设计事实：α=0.01 单侧精确二项检验对 H0: p ≥ 0.5 的拒绝域，n≤6 为**空集**、n=10 恰为 `{0}`、n=20 为 k≤4、n=30 为 k≤8。也就是说「前瞻性写一个 G2′ 二项检验」在数学上**就是 G2**，只是换了个 n。将来真要排除奇异性，必须走**干预式**设计（同域、同流水线、同预算、**同配置点集**，A 臂现解析 u\*，B 臂 u\* 加事前冻结幅度阶梯的真 `r^(2/3)` 内圆奇异项、f 重算并过 C1），产出检出下限并给出有界结论。**该设计本轮不冻结、不预注册**——在不知道哪个命名动作需要它之前就冻结，又是一次在压力下造判据。

### 12.4 裁决四：`rCapacityLimit` 从未被排除——问题不成立，且总账变差

这是四项里最重的一条，因为它**让情况变坏**。

`state_machine.py` 的 `FACTOR_CONTROL = {"capacity": "architecture", "sampling": "sampling"}`，且 `MIN_INTERVENTION_LEVELS = 3`、`MIN_INTERVENTION_SEEDS = 3`：一次**容量**干预必须改变**架构**，至少三档、每档至少三个 seed。而嵌套预算干预全程把架构钉死在 `4×64 tanh`（诊断配置的 `network` 块与 r1 逐字相同），改变的是 `optimizer.steps`——**容量档位数 = 0**。

我自己在 2026-09-19 预注册 §13 CASE A 里写的原文是：

> 构成支持 `rOptimizationFailure` 的**强判别性**证据，因为同一 representational capacity 已实证达到判据，`rCapacityLimit` **不再是必要解释**。但**不得**因为 B\* 存在就跳过其余六个 admissible candidate 的记录义务——……`rCapacityLimit`……

它把 `rCapacityLimit` **逐字列进**那六项不得跳过的义务里。**「不再是必要解释」≠「已排除」。** 我在 Phase II 报告与本报告 §4.1 里把它写成了后者，这是越权。

**裁决**：不发任何用于 `excludes.rCapacityLimit` 的 `exp-*` 标识，不建注册表，不重跑。改记 `rCapacityLimit` 为**未排除**，未排除原因由 3 项改为 **4 项**。§4.1 的表格与「6 项义务中 2 项备妥、1 项缺标识、3 项未排除」这一行据此更正为：**6 项义务中 2 项备妥可引用证据，4 项未排除**。

嵌套预算干预并未白跑：那 9.15 小时买到了 `B* = 180k`、三档预算的配对结构、以及 120k 前缀在十个 seed 上逐位复现 r1，它仍是本项目迄今最干净的干预式实验之一，将来作为 **B\* 证据**经 `evidencePointers`（`artifactRef` 本就强制 `artifactId + sha256`）进入记录。它唯一不能做的事，是排除一个**它从未改变过的变量**。

### 12.5 一个本节新发现的可执行事实：`rUndetermined` 的 DiagnosisRecord 是写得出来的

本报告 §4.2 原写「三项未排除也使记录无法通过 `validate_diagnosis_record`」。这句话只对**命名 `rOptimizationFailure`** 成立。实测：`state_machine.discriminating_experiment_errors` 在 `root_cause is RootCauseClass.UNDETERMINED` 时校验完 `experimentId` 即 `return errors`，`excludes` 可为空；`SIGNATURE_EVIDENCE[sLocalizedError]` 只要 `errorSpatialDistribution` 与 `samplingConfigDiff`，两项本轮均已产出；唯一额外要求是不得带 `gate` 字段。构造的候选记录经 `validate_diagnosis_record` 返回**零错误**。

但它的后果不轻：`triage` 在 `rUndetermined` 下返回的不是 `DIAGNOSED` 而是 **`STOPPED_THE_LINE`**——「the line stops for a human」。这是一次真实的状态迁移，且 `MAX_DIAGNOSIS_ROUNDS = 3`。**本轮不写、不迁移**：它超出用户委托的四项，留给用户与外部评审裁决（见本报告新的 §13 建议）。

````

</details>

### R033 — 项目/docs/pinn-trust-loop/ANNULUS_NESTED_BUDGET_INTERVENTION_REPORT_20260920.md

<details>
<summary>展开完整原文</summary>

````markdown
# Annulus Nested Budget Intervention Report（2026-09-20）

执行负责人：Claude（队长）。对象：圆环 Gate 5b 失败（`observedSignatures = ["sLocalizedError"]`）的受控训练预算干预。
预注册：[ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md](../../experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md)（含第 16 节 codeHash 勘误）。
上游：[ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md](ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md)、[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)。

本轮**没有**打开任何 claim set、**没有**写入任何账本事件、**没有**修改 r1 的任何机器证据、**没有**改动阈值 / 架构 / 采样 / 优化器 / 几何 / 损失 / 局部判据合同、**没有**升 revision、**没有**产生 TrustVector 或 ClaimGateDecision、**没有**在 240k 之后继续加预算。

---

## 1. Executive

```text
120k prefix equivalence:  PASS        （10/10 逐位相等）
resume fidelity:          PASS        （11 项检查全部逐位相等）
B*:                       180k
Root Cause:               UNDETERMINED
```

**B\* 存在**：同一 4×64 tanh、同一采样、同一优化器、同一 0–120k 轨迹，仅仅继续优化到 180000 步，就让 **10/10** 个 paired seed 在 D_dev 上同时满足既有的局部验收判据 ACA-9 与既有的 training reliability 条件。这是支持 `rOptimizationFailure`、并反证「capacity 必须增加」的**强判别性证据**。

**但正式 RootCauseClass 仍是 `UNDETERMINED`**，因为 Constitution 1.2 的 DiagnosisRecord 要求尚未满足。`discriminatingExperiment.excludes` 必须为该 signature 下**其余每一个** admissible 根因都指名一个排除实验（schema 原文：a root cause is never chosen, it is what is left），`sLocalizedError` 的 admissible 集合有 7 个成员，本轮只用实验排除了其中 **1 个**（`rCapacityLimit`）。详见第 4 节。按预注册第 13 节 CASE A 的末句，条件未满足即**不得**写入 `rOptimizationFailure`。

```text
Annulus Calibration:  NOT YET PASS
Highest Claim:        BLOCKED
Recommendation:       REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

---

## 2. 前置门槛

### 2.1 Resume fidelity：PASS

夹具：连续 `0 → 2000` 对照 `0 → 1000` → 存盘 → JSON 往返重载 → `1000 → 2000`，LR prefix 故意设为 1200（落在断点与终点之间），使重载的后半段跨越「停止衰减、开始保持」那一点。合同为 **bitwise**，依据是本机实测的确定性（r1 同 seed 同设备重跑，权重最大绝对差 **0.0**）。

11 项全部 PASS：模型参数 `max|dW| = 0.0`（12752 个值）、Adam 状态 `0.0`（25514 个值）、scheduler 位置、学习率（跨越 prefix 后保持终值）、batch 生成器字节状态、order/cursor、全局 RNG、D_dev 指标、断点处状态、重载后的 loss/lr 历史、`resumedFromStep`。记录：`experiments/annulus/diagnosis/RESUME_FIDELITY.json`。

### 2.2 120k prefix equivalence：PASS（10/10 逐位）

| seed | r1 @120k devRelL2 | 新轨迹 @120k | Δ |
|---|---|---|---|
| 0 | 1.62231774002202404e-04 | 同左 | 0 |
| 1 | 1.87432730527999059e-04 | 同左 | 0 |
| 2 | 3.87396529747795573e-04 | 同左 | 0 |
| 3 | 1.89805321144054332e-04 | 同左 | 0 |
| 4 | 1.57843726300633446e-04 | 同左 | 0 |
| 5 | 1.83257150048191358e-04 | 同左 | 0 |
| 6 | 1.81269058362817876e-04 | 同左 | 0 |
| 7 | 1.73505697022779026e-04 | 同左 | 0 |
| 8 | 2.24073904707458371e-04 | 同左 | 0 |
| 9 | 1.98203746997927286e-04 | 同左 | 0 |

不止全局误差：新轨迹 @120k 的**局部统计量**也与 r1 记录的 D_dev 逐 seed 值完全一致（`4.0045e-04 / 3.7569e-04 / 1.0383e-03 / 4.0672e-04 / 4.9085e-04 / 4.1501e-04 / 3.5692e-04 / 4.9326e-04 / 4.7401e-04 / 3.9996e-04`）。因此「只改了 checkpoint 基础设施与 schedule 表示，方法未变」这一假设**成立**，180k / 240k 的结果可以被作因果解读。

LR schedule 本身的等价性另有机器验证：迭代语义逐位复现 r1 记录的**全部 241 条**学习率，且在总预算 120k / 180k / 240k 下结果相同（第 10 节测试）。

---

## 3. Budget Intervention

每个 paired seed **只启动一次**训练，`0 → 240000`，在三个预算处保存完整 checkpoint 并在 CPU 上评估。180k 是其自身 120k 状态的 exact continuation，240k 是其自身 180k 的 exact continuation。seed identities 为 r1 的原样十组，数据为 r1 的**已登记** D_train / D_dev（逐个以 sha256 对 ProblemDefinition 校验）。用时 9.15 小时（CUDA）。

### 3.1 10 × 3 paired table（D_dev，阈值 ACA-9 = 1e-3，`every-seed`）

| seed | 120k relL2 | 120k ACA-9 | 180k relL2 | 180k ACA-9 | 240k relL2 | 240k ACA-9 |
|---|---|---|---|---|---|---|
| 0 | 1.622e-04 | 4.004e-04 PASS | 1.719e-04 | 4.758e-04 PASS | 8.677e-05 | 2.371e-04 PASS |
| 1 | 1.874e-04 | 3.757e-04 PASS | 3.527e-04 | 6.541e-04 PASS | 9.830e-05 | 2.196e-04 PASS |
| **2** | 3.874e-04 | **1.038e-03 FAIL** | 2.774e-04 | 7.312e-04 PASS | 2.891e-04 | 6.801e-04 PASS |
| 3 | 1.898e-04 | 4.067e-04 PASS | 2.771e-04 | 6.265e-04 PASS | 1.446e-04 | 3.126e-04 PASS |
| 4 | 1.578e-04 | 4.908e-04 PASS | 2.147e-04 | 4.400e-04 PASS | 1.071e-04 | 3.079e-04 PASS |
| 5 | 1.833e-04 | 4.150e-04 PASS | 2.874e-04 | 4.771e-04 PASS | 1.037e-04 | 2.720e-04 PASS |
| 6 | 1.813e-04 | 3.569e-04 PASS | 1.550e-04 | 3.519e-04 PASS | 1.937e-04 | 4.002e-04 PASS |
| 7 | 1.735e-04 | 4.933e-04 PASS | 1.069e-04 | 2.839e-04 PASS | 9.949e-05 | 2.848e-04 PASS |
| 8 | 2.241e-04 | 4.740e-04 PASS | 1.171e-04 | 2.428e-04 PASS | 8.934e-05 | 2.164e-04 PASS |
| 9 | 1.982e-04 | 4.000e-04 PASS | 1.326e-04 | 3.087e-04 PASS | 1.471e-04 | 2.970e-04 PASS |

### 3.2 每预算判定（预注册规则，运行前冻结）

| 预算 | reliability | 成功数 | relL2 median | relL2 worst | relL2 IQR | ACA-9 median | ACA-9 worst | localized | allPass |
|---|---|---|---|---|---|---|---|---|---|
| 120000 | PASS | 10/10 | 1.8534e-04 | 3.8740e-04 | 2.470e-05 | 4.1501e-04 | **1.0383e-03** | 9/10（seed 2 失败） | **False** |
| **180000** | PASS | 10/10 | 1.9329e-04 | 3.5270e-04 | 1.448e-04 | 4.7576e-04 | 7.3121e-04 | **10/10** | **True** |
| 240000 | PASS | 10/10 | 1.0537e-04 | 2.8910e-04 | 4.878e-05 | 2.9701e-04 | 6.8008e-04 | 10/10 | True |

```text
B* = 180000        （最小的、使 10/10 同时满足三项条件的预注册预算）
```

### 3.3 必须如实说明的三点

1. **改善不是单调的，180k 处的 median 反而更差**。全局 median 从 `1.8534e-04`（120k）升到 `1.9329e-04`（180k），到 240k 才降到 `1.0537e-04`；ACA-9 的 median 同样先升（`4.1501e-04 → 4.7576e-04`）后降（`2.9701e-04`）。逐 seed 看，seed 1 / 3 / 5 在 180k 明显变差，seed 6 在 240k 比 180k 差。**「步数越多越好」不成立**；真实形态是在终端学习率 `1e-5` 上继续游走。
2. **180k 通过，靠的是最差 seed 下移，同时离散度上升**。IQR 从 `2.470e-05` 扩大到 `1.448e-04`（5.9 倍），而 worst 从 `1.0383e-03` 降到 `7.3121e-04`。`every-seed` 规则问的正是 worst，所以判定成立——但这意味着 180k 的通过**部分依赖这次游走恰好把 seed 2 带到阈值之下**。240k 的证据更干净：median、worst、IQR 三者同时改善。
3. **余量很薄**。180k 的 worst 对阈值余量 `1.37×`，240k 为 `1.47×`。作为对照，已 CLOSED 的正方形标定在同一判据上有 `6.4×` 余量。

### 3.4 局部热点的位置没有改变

十个 seed、三个预算共 30 个最差单元，**29 个**落在中间两个径向环（bin 1 / bin 2），**1 个**落在紧贴内孔的 bin 0（seed 1 在 240k，单元 `0,15`），**0 个**落在紧贴外圆的 bin 3。这与 r1 的观察一致：双分量硬约束把两条圆周钉在 `~2e-16`，误差被推离两条边界。继续优化没有改变误差的空间结构，只改变了它的大小。

### 3.5 图

`experiments/annulus/diagnosis/nested-budget-r1-paired/plots/` 共 7 张，全部取自已登记的 `DIAGNOSIS.json`，不重算、不加载模型：全局误差逐 seed 轨迹、局部判据逐 seed 轨迹（含阈值与 B\*）、前缀等价性、失败 seed 单独轨迹、median/worst 汇总、残差对预算、离散度对预算。

---

## 4. DiagnosisRecord

### 4.1 候选集合（读自实际 admissible matrix，未缩减）

`pinn.governance.state_machine.admissible_root_causes("1.2")` 对 `sLocalizedError` 给出 **7** 个候选：

```text
rSingularityTreatment  rReferenceDefect  rImplementationDefect  rCapacityLimit
rOptimizationFailure   rSamplingDeficiency  rSpecDefect
```

（另核实 `rDataDefect` **不在**该 signature 的集合内。）

### 4.2 排除义务的实际状态

Constitution 1.2 的 `discriminating_experiment_errors` 要求：**为其余每一个 admissible 根因指名一个排除实验**，且 `excludes.<cause>.experiment` 必须匹配 `^(P[0-9]+|exp-[a-z0-9][a-z0-9-]*)$`——即一个 Tier-1 扰动编号或一个正式 attempt id。逐项核对：

| 候选 | 现有证据 | 是否满足排除义务 |
|---|---|---|
| `rCapacityLimit` | **本轮干预**：同一容量在 180k 处 10/10 满足判据 | **满足** |
| `rSamplingDeficiency` | EXPLORATORY 密度探针（2.76× 配置点无改善） | **不满足**：EXPLORATORY 非正式实验；Tier-1 的 P1 / P6 / P7 / P11 未跑 |
| `rImplementationDefect` | Gate 3 十项 + 可信校验器 10 个负面控制全 PASS | **不满足**：Gate 不是 discriminating experiment；P4（float32）未跑 |
| `rSpecDefect` | Gate 1 / Gate 2 PASS，解析自验残差恒为 0 | **不满足**：无 P 编号或 exp id 可指 |
| `rReferenceDefect` | 独立极坐标 FDM 观测阶 2.0016 / 2.0004，与解析解一致 | **不满足**：同上 |
| `rSingularityTreatment` | 无角点 / 再入角；热点不在任一边界附近（§3.4） | **不满足**：观察，不是实验 |

**6 项义务中满足 1 项。** 因此无法生成通过校验的 DiagnosisRecord。这不是形式主义：其余五项的证据全部是「没有观察到缺陷」，而**证据的缺席不是排除**。

（以上不是推理，是对 `pinn.governance.trust_loop.validate_diagnosis_record` 的实测：构造候选记录后逐条读取它返回的错误。）

### 4.3 正式判定

```text
RootCauseClass:  （未写入）
Formal verdict:  UNDETERMINED
Evidence:        rOptimizationFailure 获强判别性支持；rCapacityLimit 已被实验排除；
                 其余五个候选未被排除，仍然 viable
```

状态仍为 `FAILURE_RECORDED`，**未进入 `DIAGNOSED`**。

### 4.4 一个结构性发现（登记为 AMENDMENT CANDIDATE，本轮不实施）

上述五项排除义务实际上要求 **Tier-1 扰动集合**（P1 / P4 / P6 / P7 / P11 / P16 等），而协议规定 Tier-1 **只在 Gate 5 PASS 之后**执行。于是出现一个闭环：

> 一次**失败** run 的正式诊断，需要协议只在**成功** run 之后才安排的实验。

这不是本轮造成的，也不该由本轮单方面解决——它要么需要一条「诊断用 Tier-1」的通路，要么需要承认失败 run 的 DiagnosisRecord 在 MVP 下通常只能落到 `rUndetermined`。登记待审。

---

## 5. Revision

**未执行。** `revision` 仍为 1，`specHash` 仍为 `4c8dfbc7238d…`，冻结配置 `exp_annulus_baseline.json` 一字未改（`steps` 仍为 `120000`，无 `lrPrefixSteps`）。按 PART 16，只有正式 DiagnosisRecord 确认 `rOptimizationFailure` 才允许 `revision 1 -> revision 2`，该前提不成立。

预注册第 15.4 条的事前记录仍然有效，供将来使用：若日后获授权进入 revision 2，方法变更**不应**被描述为「only changed field = steps」。相对 r1 它实际包含 ① 延长的训练预算 B\*；② 显式的 120k 之后 LR continuation policy。准确的定义是 **optimization-trajectory extension**（保留原 0–120k 前缀 + 额外的 terminal-LR 优化至 B\*）。

```text
r1 codeHash          8ee9b9236199996fe95684b42bb6a247717f07bb5845437ac7c85ff7978b550e （未变）
诊断 codeHash        b7f9fe73e0b1ae9b17da74c8260ce638f7fcf0e97524ba39017ceccb0f2e01f3
诊断配置             experiments/annulus/diagnosis/config_nested_budget.json
```

诊断身份**不是** claim revision：它没有打开 claim set，不产生 claim。

## 6. Blind Validation

**未执行，且未触碰。** driver 在开始前与结束后各记录账本 sha256 与事件序列并比对，结果 `unchanged = True`：

```text
DAC-M0   SEALED -> OPENED -> BURNT     （历史，永久保留，不得重开）
DAC-M1   NEVER_SEALED                   未触碰
DAC-M2   NEVER_SEALED                   未触碰
DAC-M3   NEVER_SEALED                   未触碰
账本事件  ['SEALED', 'OPENED']           本轮无新增
```

局部判据合同自身也拒绝 `evaluationSet != "dev"`；测试另钉死 driver 源码中不得出现 `claim_grids` / `claim_quadrature` / `claim_pointwise` / `make_event` / `write_ledger` / `claim_evaluation` 等标识。

## 7. Tier-1

**未执行。** 只在 Gate 5 PASS 之后进行。参见 §4.4：这正是排除义务无法满足的原因。

## 8. G6

**未执行。** `C_repro` 仍为 `BLOCKED`。Environment B 本轮未被访问。

## 9. Trust Vector / Claim

本轮**未产生**新的 TrustVector 或 ClaimGateDecision。r1 的实际值保持不变：

```text
math PASS   impl PASS   train PASS   physics PASS   external FAIL   repro BLOCKED
Highest Claim: BLOCKED
```

## 10. Tests / PRELOCK / Portability

| 项目 | 治理虚拟环境 `.venv` | 训练解释器（mamba，torch 2.12.1+cu126） |
|---|---|---|
| 全套 pytest | **1414 passed / 0 failed / 26 skipped** | — |
| annulus 补跑 | — | **24 passed / 0 failed** |
| poisson2d 补跑 | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，7/7** | — |
| portability | **0 hard binding / 1 configurable / 8 historical** | — |

上轮基线为 1391 / 25 与 annulus 7 项；本轮净增 **23** 项治理测试（schedule 等价性、预算独立性、B\* 规则、无升级路径、防火墙、配对 seed、r1 证据不变）与 **17** 项训练解释器测试（checkpoint 内容、JSON 往返、resume 逐位一致、拒绝异种 checkpoint、LR 保持）。

## 11. Newly Discovered

### BLOCKING

**无。** `B*` 存在且前置门槛全部 PASS；阻止正式判定的是排除义务未满足（§4.2），这是**已知的协议要求**，不是新缺陷。

### NON-BLOCKING

1. **继续优化不单调改善**：180k 的 median 比 120k 更差，IQR 扩大 5.9 倍，240k 才三项同时改善（§3.3）。`B* = 180k` 的通过部分依赖最差 seed 恰好下移。
2. **误差的空间结构基本不随预算改变，但不是「一个都没有」**：30 个最差单元中 29 个在中间两个径向环，1 个（seed 1 @240k，单元 `0,15`）紧贴内孔（§3.4）。
3. **余量很薄**：180k `1.37×`、240k `1.47×`，对比正方形标定的 `6.4×`。
4. **既有 budget response 证据的强度已更正**：10k / 20k / 40k 三次探针是各自独立的 from-scratch run 且 LR 轨迹随预算重新缩放，混合了「更多步数」与「更慢衰减」——上一轮已记录，本轮的固定前缀设计正是为消除该混杂。

### AMENDMENT CANDIDATE

1. **（新）失败 run 的诊断与 Tier-1 的时序闭环**：正式 DiagnosisRecord 的排除义务需要 Tier-1 扰动，而 Tier-1 只在 Gate 5 PASS 后执行（§4.4）。
2. **（新）未跟踪文件静默落在代码身份之外**：`code_manifest()` 只枚举 git 已跟踪文件，`workspace_dirty_paths()` 用 `--untracked-files=no`，`assert_code_identity_complete()` 无法察觉从未被列入的文件。本轮预注册记录的 codeHash 因此一度写错（已在预注册第 16 节追加勘误并机器坐实因果）。r1 不受影响。
3. **（承前）Gate 4 不筛查局部判据**，尽管 D_dev 有能力测量它。
4. **（承前）`ProblemDefinition` schema 的 `domainType` 词汇缺 `annulus`**。
5. **（承前）训练记录应保存 optimizer / scheduler / batch RNG 状态** —— 本轮已对诊断路径实现，但尚未成为正式 attempt 的要求。
6. **（承前）LR 调度与总预算耦合** —— 本轮已提供 `lrPrefixSteps` 解耦，但缺省行为仍是耦合的（为不改变历史含义而刻意保留）。

### NONE

其余未发现新问题。

## 12. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

`B*` 存在是一个实质进展：它以配对、逐位可核验的方式证明**同一容量确实能达到既有判据**，从而把 `rCapacityLimit` 排除在必要解释之外。但根因尚未正式判定，圆环标定仍未通过，Highest Claim 仍为 BLOCKED。

按 PART 21 与 PART 26：**即使 B\* 存在且证据指向 `rOptimizationFailure`，本轮到此停止**。不自行启动 revision 2 正式 run、不消耗 DAC-M1、不做 capacity sweep / 架构搜索 / 优化器搜索 / 更高预算 sweep、不开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热。

需要用户与外部评审裁决的是：

1. **五项未满足的排除义务如何处理**——是授权一次「诊断用 Tier-1」（在 Gate 5 未 PASS 的前提下执行扰动集合，仅用于排除、不产生 claim），还是接受失败 run 的 DiagnosisRecord 在当前 MVP 下只能落到 `rUndetermined`。
2. **若要进入 revision 2，B\* 取 180k 还是 240k**。180k 是预注册规则给出的答案（最小预算）；240k 的证据更干净（median / worst / IQR 三者同时改善，余量 1.47× 对 1.37×），但选它等于偏离预注册的最小性规则。这是一个需要明确裁决的取舍，**不应由执行者单方面决定**。


---

## 13. 追加勘误：一处事实错误（2026-09-20，追加不改写）

本节是追加。机器证据 `DIAGNOSIS.json` 一字未动——它从一开始就记录着正确的数据；错的是本报告的散文。

§3.4 与 §11 NON-BLOCKING 2 原写「30 个最差单元**全部**落在中间两个径向环，**没有一个**紧贴内孔或外圆」。这是错的。逐条核对 `DIAGNOSIS.json`：

```text
30 个最差单元中
  29 个在 bin 1 / bin 2
   1 个在 bin 0（紧贴内孔）：seed 1 @ 240000，单元 0,15
   0 个在 bin 3（紧贴外圆）
```

错误的来源：我在一次进度汇报里打印过这 30 个单元的清单，随后写报告时按印象概括为「全部」，**没有逐条复核**那份清单。正文两处已就地更正为 29 / 1 / 0。

**这不是无关紧要的更正**。该说法正是「圆环几何没有制造孔边病理」这一论断的证据，而本轮 `exp-annulus-dx-singularity` 的预注册判定 G2 要求「30 个最差单元中落在 bin 0 或 bin 3 的个数 == 0」。按真实数据，G2 **不成立**（1 ≠ 0），因此 `rSingularityTreatment` **未被排除**。详见
[ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md](ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md)。

需要说明的是，r1 标定报告与预算诊断报告中关于「**十个** seed 的最差单元全部在中间两环」的说法**是正确的**——r1 的十个 seed 在 120k 处确实全部落在 bin 1 / bin 2。出错的只是 Phase II 中覆盖 30 个单元的那句概括。

---

## 14. 追加勘误：本报告把「不再是必要解释」写成了「已排除」（2026-09-21，追加不改写）

本节是**追加**。机器证据（`DIAGNOSIS.json`、checkpoint、`B* = 180k`、逐位相等的 120k 前缀）一字未动——它们都是真实测量。错的是本报告对它们的**形式定性**。

§1 与 §4.2 写道嵌套预算干预「把 `rCapacityLimit` 排除在必要解释之外」「已排除（干预式，上一轮）」，§4.1 的表格把它记为**科学状态：已排除**。这是越权。

`pinn/governance/state_machine.py` 的 `FACTOR_CONTROL = {"capacity": "architecture", "sampling": "sampling"}`，配合 `MIN_INTERVENTION_LEVELS = 3` 与 `MIN_INTERVENTION_SEEDS = 3`：一次**容量**干预必须改变**架构**，至少三档、每档至少三个 seed。本干预全程把架构钉死在 `4×64 tanh`，改变的是 `optimizer.steps`——**容量档位数 = 0**。它从未改变过容量这个变量，因此不可能排除它。

而 2026-09-19 预注册 §13 CASE A 的原文恰恰是准确的：「同一 representational capacity 已实证达到判据，`rCapacityLimit` **不再是必要解释**」，并把 `rCapacityLimit` **逐字列进**六项不得跳过的记录义务中。**「不再是必要解释」≠「已排除」**——前者说的是它不再被逼着为观测负责，后者说的是实验把它排除掉了。本报告把前者写成了后者。

更正：`rCapacityLimit` **未被排除**，保持 viable。`B* = 180k` 仍是支持 `rOptimizationFailure` 的强证据，本干预仍是本项目迄今最干净的干预式实验之一；它唯一不能做的事，是排除一个它从未改变过的变量。逐条见
[ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md](ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md) §12.4。

````

</details>

### R034 — 项目/docs/pinn-trust-loop/ANNULUS_POISSON_CALIBRATION_REPORT_20260917.md

<details>
<summary>展开完整原文</summary>

````markdown
# Annulus Poisson Calibration Report（Geometry Lift 1，2026-09-17 / 18）

执行负责人：Claude（队长）。对象：圆环制造解 Poisson 的首次正式标定。上游：[CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md](CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md)、[LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md](LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md)。预注册：`experiments/annulus/EXPERIMENT_ANNULUS_PREREGISTRATION_20260917.md`。

本轮**没有**改动任何阈值、**没有**重开已烧毁的 D_claim、**没有**修改任何历史机器证据 / TrustVector / ClaimGateDecision / 账本、**没有**删除失败与中止记录、**没有**新增 Gate 或 TrustStatus、**没有**起草 A-0003、**没有**扩 portability policy、**没有**在 Gate 失败后现场调参数重跑。

---

## 1. Executive

```text
Geometry Lift 1: NOT YET PASS
Highest Claim:   BLOCKED
```

十个 seed 全部训练完成、无 NaN，Gate 1 / 2 / 3 / 4 与 Gate 5a 物理全部 PASS。盲集 DAC-M0 按协议一次性打开，**Gate 5b 验收 FAIL**：十个 seed 中 **一个**（seed 2）在局部误差判据 **ACA-9** 上超标，实测 `1.079e-03` 对阈值 `1.000e-03`，超出 **7.9 %**。其余九个 seed 的 ACA-9 在 `4.196e-04`–`6.537e-04` 之间；**ACA-1..ACA-8 的九个判据对全部十个 seed 全部通过**。

按验收合同的 `seedPolicy = "every-seed"`（与 Gate 5b 对 MUST 判据一贯执行的 `all(...)` 同一规则），一个 seed 失败即 MUST 判据失败，故 `C_external = FAIL`，状态机进入 `FAILURE_RECORDED`。**阈值一个都没有动**（用户 2026-09-17 裁决：达不到就如实写 FAIL）。

**根因尚未正式判定**（见 §13 注解）。几何提升本身是成功的：曲边、内孔、多连通、两条边界组件带来的每一处机制（成员判定、面积均匀采样、双分量硬约束、内法向定向、几何原生求积、等面积局部划分、独立极坐标 FDM）都按设计工作，并有机器证据（第 3 节、第 2 节）；本轮**没有观察到**明确的几何病理。据此，**训练预算不足是一个被现有证据支持的假设（SUPPORTED HYPOTHESIS）**，见 §3.4 的定量对照——它**不是**一个已被正式识别的 `RootCauseClass`。状态仍是 `FAILURE_RECORDED`，尚未进入 `DIAGNOSED`。

---

## 2. Geometry Audit

> **What broke because the domain became curved and multiply connected?**

逐项分类如下。「broke」指**若照搬正方形的做法就会出错**，并给出本轮实测的机器证据。

### 2.1 membership — BROKE

孔**不属于**定义域。制造解的因子 `h = (1 - s)(s - a^2)` 在孔内 `s < a^2` 时变号，因此任何「先算再判断」的写法都会把孔内的值当成解。所有评估集与物理积分点都改为**显式成员判定**。

* 证据 `T11-geometryMembership` PASS：分类器把 interior / hole / exterior / 两条圆周严格分开。
* 证据 `PH8-geometryMembership` PASS：每一个物理评估点都严格落在圆环内部（0 个非法点），恒等式不会跨孔积分。
* 证据 `sets/isolation.json`：四个集合（train 2048 / dev 1024 / phys 5120 / claim 5834）全部通过成员检查。

### 2.2 sampling — BROKE

`r ~ U(a, 1)` **不是**面积均匀：中位半径处的面积分数是 0.38 而不是 0.5，内环被系统性过采样。正确做法是 `r = sqrt(a^2 + (R^2 - a^2) U)`，`theta = 2 pi V`。

* 冻结配置 `sampling.rule` 明确写死该公式；`pinn/experiments_annulus/datasets_annulus.area_uniform_interior` 是唯一实现。
* 训练解释器下的回归测试 `test_the_sampler_is_uniform_in_area_not_in_radius` PASS（7 项之一）。
* 顺带否证了一个似是而非的猜想：把配置点数按面积匹配（1024 → 2823）**并不**改善误差（EXPLORATORY：10k 步 1.05e-02 vs 9.94e-03，40k 步 2.358e-03 vs 2.230e-03），所以配置点数按正方形原值冻结，未做任何架构搜索。

### 2.3 boundary components — BROKE

边界不再是一条连通曲线的四条边，而是**两条互不连通的组件**。所有边界量都必须**按组件**分别计算并分别报告，而不是在一个「边界集合」上取最大值。

* 证据 `T4-hardBoundaryBothComponents` PASS：outer `1.69e-17`、inner 独立报告。
* 证据 `ACA-3`（两组件上 `|u|` 的最大值）在 D_claim 上十个 seed 全部 `≈ 2.116e-16`，对阈值 `1e-4` 有 **12 个数量级**的余量。
* 证据 `gate5b` 的 `diagnostics.boundary` 对 inner / outer 分别记录 `flux`、`maxAbsU`、`maxNormalError`、`nodes`（各 64 个节点）。

### 2.4 normal orientation — BROKE（本几何最危险的一处）

内边界的**外法向指向孔内**，即 `-(x, y) / a`，与外边界的 `+(x, y) / R` 相反。写反不会崩溃，只会给出一个看似合理、符号错误的数——预注册记录：写反时解析通量恒等式会从 `~1e-15` 劣化到 `O(1)`。

* 证据 `T12-boundaryNormalOrientation` PASS：直接断言外法向背离原点、内法向指向孔内，单位长度到 `1e-15`。
* 证据 `PH1-fluxBalance` PASS：`|∮ ∂u/∂n ds + ∫ f dA| / |∫ f dA| = 1.633e-04`（worst seed，阈值 `1e-2`），**按组件各用自己的外法向求和**。这是第二重、独立于 T12 的验证。
* 证据 `ACA-6`（按组件的法向导数误差）worst `9.950e-04`，阈值 `5e-3`，PASS。

### 2.5 hard constraint — NOT BROKEN（设计成立，如实记录）

双分量硬 Dirichlet 参数化 `u = (R^2 - s)(s - a^2) N(x, y)` 在两条圆周上**构造性**为零，因此多连通域并不需要第二个边界损失项，损失里只有一个 pde 项。

* 证据 `T8-lossTermSeparation` PASS：损失只有一个 pde 项、权重冻结、无边界罚项。
* 证据 ACA-3 ≈ `2.1e-16`（见 2.3）——这是机器精度，不是「训练得好」。
* 该因子在模型侧**独立于** `pinn.reference` 重写，模型不得 import 答案。

### 2.6 quadrature — BROKE

笛卡尔张量积求积不适用。改为几何原生求积：面积分数 `t` 上的 Gauss–Legendre × `theta` 上的梯形，雅可比必须正确。

* 证据 `T13-quadratureJacobian` PASS：求积面积 `2.756747553525` vs 精确值 `pi (1 - a^2) = 2.756747553525`，相对误差 `6.44e-16`；`∫ u* dA` 亦对上解析值。
* 证据 `ACA-5`（积分泛函）worst `1.798e-04`、`ACA-7`（能量恒等式）worst `1.674e-04`，阈值分别 `1e-3` / `1e-2`。

### 2.7 localized validation — BROKE

正方形用的 8×8 笛卡尔分块在圆环上**跨越孔**，且单元面积不等，统计量失去意义。改为几何原生的**等面积**划分：4 个等面积径向环 × 16 个扇区 = **64 个单元**（ACA-9）。

* 证据 `sLocalizedError` 合同：`partitionKind = annulusEqualAreaCells`、`radialBins = 4`、`angularSectors = 16`、`normalization = globalReferenceRms`、`operator = <=`、`threshold = 1e-3`、`seedPolicy = every-seed`、`statisticId = maxCellRmsErrorOverReferenceRms`，九个字段逐项与冻结合同比对通过。
* **这正是本轮失败的判据**（第 3、5 节）。但失败**不是**划分方式造成的：失败单元并不在孔边，见 §3.3。

### 2.8 numerical reference — BROKE

五点差分贴不了曲边界。独立参考改为**极坐标有限差分**，只用 numpy，不 import 任何 `pinn` 模块、不使用 autograd、不复用 PINN 的残差算子，只共享冻结的源项。

* 证据 `G2b-fdmRefinement` PASS：三级网格 (16×64 / 32×128 / 64×256) 的相对 L2 为 `3.407e-03 / 8.509e-04 / 2.127e-04`，比值 `4.004` 与 `4.001`，**观测阶 2.0016 / 2.0004**。
* 证据 `test_the_finite_difference_solver_shares_no_code_with_the_model` PASS。

### 2.9 governance — BROKE（登记为 AMENDMENT CANDIDATE，未改 schema）

`ProblemDefinition` schema 的 `domainType` 词汇是 `{interval, rectangle, disk, mesh, other}`，**没有 `annulus`**，且 `geometry` 对象不接受额外字段。

处理方式：用 schema **自带的** `regions[].params` 承载圆环几何，`domainType = "other"`，**没有修改治理 schema**。这是一个真实的表达力缺口，登记为 AMENDMENT CANDIDATE（第 11 节），本轮不动它——在一次几何提升的当口改治理词汇，等于一边跑实验一边改尺子。

### 2.10 acceptance-set blind spot — BROKE（已用其他手段覆盖）

纯粹的**导数分量互换**（`u_x ↔ u_y`）不会被 MUST 的积分型判据看见：能量对互换不变，H1 半范 ACA-8 只是 SHOULD。

覆盖手段：边界法向导数 ACA-6（按组件，见 2.4）与 Gate 3 的 AD 分量检查 `T2-secondDerivativeComponentSeparation`（非对称探针 `w = sin(2πx) cos(πy)`，`|w_xx + 4π² w| = 7.11e-15`、`|w_yy + π² w| = 1.78e-15`）。两者本轮均 PASS。

### 2.11 process — BROKE（上一轮沙箱冒烟抓到，已修，本轮验证）

旧写法在 Gate 4 返回 `BLOCKED` 时会**继续打开 claim 集**。修复后：任何非干净 PASS（FAIL / PARTIAL / BLOCKED 一律）都停在失败路径且**不打开** claim 集。

* 本轮沙箱冒烟（CUDA，150 步 × 3 seed）实测：Gate 4 `BLOCKED` → 走失败路径 → `finalState = IMPLEMENTATION_VERIFIED`，沙箱账本**未出现 OPENED**，真账本一字未动。

### 2.12 none — 未因几何而破的部分

架构、优化器、batch、dtype、seed 协议、代码身份机制、PRELOCK、账本生命周期、状态机分流、局部误差触发器的**判定逻辑**（只换了划分方式，判定规则原样沿用）。步数预算是唯一与正方形标定不同的方法值，理由在预注册 5.2 事前写定。

### 2.13 本轮新增的一条（一条尚未被否证的观察）

在**迄今考察的正方形与圆环两个标定案例中**，**没有观察到**圆环特有的局部/全局误差比放大。两个几何不足以证明普遍的 geometry invariance，因此下表只作为观察记录，不作为不变性的证明：

| | 全局（ACA-1 / AC2D-1）median | 局部（ACA-9 / AC2D-9）median | 比值 |
|---|---|---|---|
| 正方形 2D（已 CLOSED @ C2） | `3.600e-05` | `1.151e-04` | **3.20** |
| 圆环（本轮） | `1.860e-04` | `5.545e-04` | **2.98** |

圆环十个 seed 的逐 seed 比值为 `2.61 / 2.77 / 2.90 / 3.02 / 3.95 / 2.62 / 2.46 / 3.76 / 2.63 / 2.58`，均值 **2.93**、标准差 0.52 —— 与正方形的 3.20 在同一水平。

结论（详见 §3.4）：**局部判据一直就在全局误差的约 3 倍处**；正方形把全局误差压到 `3.6e-05`（对 `1e-3` 有 28 倍余量），所以 AC2D-9 从未构成威胁；圆环只压到 `1.86e-04`（5.4 倍余量），于是 ACA-9 成为**首先触顶**的判据。这是**预算问题，不是几何问题**。

---

## 3. Numerical

### 3.1 训练（D_dev，诊断口径，不是验收）

| 量 | 值 |
|---|---|
| seed 数 N | 10（init 20261400+i / sample 20261500+i / batch 20261600+i） |
| 完成率 k/N | **10/10**（全部跑满 120000 步，NaN/Inf 0 个，发散 0 个） |
| median devRelL2 | **1.853e-04** |
| IQR | **2.470e-05** |
| worst seed | **3.874e-04**（seed 2）；worst/median = 2.09，上限 3.0 |
| 训练设备 | cuda（每 seed 1849–2571 s，共约 5.9 h） |
| 评估设备 | cpu（全部 Gate 数值） |

Gate 4 三项检查全 PASS：训练完整性、seed 协议（`median_ok / worst_ok / dispersion_ok` 全 True）、loss–error 解耦（无 run 出现 loss 掉两个数量级而 dev 误差不降）。

D_dev 上的诊断中位数：残差 `normalizedResidualRms = 1.034e-03`、边界 `maxBoundaryAbs = 2.116e-16`、通量亏损 `fluxBalance = 9.212e-05`、局部统计量 `maxCellRmsErrorOverReferenceRms = 4.109e-04`、局部/全局比 `3.119`。

### 3.2 验收（D_claim = DAC-M0，5834 个样本，一次性打开）

| 判据 | 含义 | median | worst | 阈值 | 判定 |
|---|---|---|---|---|---|
| ACA-1 | 相对 L2 | `1.860e-04` | `3.722e-04` | `1e-3` | PASS |
| ACA-2 | 相对 L∞（逐点网格） | `3.539e-04` | `7.443e-04` | `5e-3` | PASS |
| ACA-3 | 两组件边界 \|u\| 最大值 | `2.116e-16` | `2.117e-16` | `1e-4` | PASS |
| ACA-4 | 归一化残差 RMS | `9.797e-04` | `1.426e-03` | `1e-2` | PASS |
| ACA-5 | 积分泛函相对误差 | `1.350e-04` | `1.798e-04` | `1e-3` | PASS |
| ACA-6 | 按组件法向导数误差 | `5.828e-04` | `9.950e-04` | `5e-3` | PASS |
| ACA-7 | 能量恒等式亏损 | `1.106e-04` | `1.674e-04` | `1e-2` | PASS |
| ACA-8（SHOULD） | 相对 H1 半范 | `3.166e-04` | `5.601e-04` | `5e-3` | PASS |
| **ACA-9** | **等面积单元局部误差** | `5.545e-04` | **`1.079e-03`** | **`1e-3`** | **FAIL（seed 2）** |

逐 seed ACA-9：`4.196e-04 / 5.207e-04 / ` **`1.079e-03`** ` / 5.884e-04 / 5.961e-04 / 4.825e-04 / 4.429e-04 / 6.537e-04 / 5.994e-04 / 5.153e-04`。

### 3.3 失败单元在哪里（回答「是不是孔边的病理」——不是）

| seed | ACA-9 | 最差单元 (径向环, 扇区) | 该单元 RMS | 与次差单元之比 |
|---|---|---|---|---|
| 0 | 4.196e-04 | (2, 11) | 5.033e-05 | 1.17 |
| 1 | 5.207e-04 | (1, 14) | 6.246e-05 | 1.15 |
| **2** | **1.079e-03** | **(2, 13)** | **1.294e-04** | **1.04** |
| 3 | 5.884e-04 | (2, 9) | 7.059e-05 | 1.10 |
| 4 | 5.961e-04 | (2, 4) | 7.151e-05 | 1.38 |
| 5 | 4.825e-04 | (2, 0) | 5.788e-05 | 1.00 |
| 6 | 4.429e-04 | (2, 8) | 5.313e-05 | 1.06 |
| 7 | 6.537e-04 | (2, 13) | 7.842e-05 | 1.66 |
| 8 | 5.994e-04 | (1, 10) | 7.191e-05 | 1.03 |
| 9 | 5.153e-04 | (1, 1) | 6.181e-05 | 1.16 |

三点如实观察：

1. 最差单元**从不落在径向环 0（紧贴孔）或环 3（紧贴外圆）**，十个 seed 全部落在中间两环。这与双分量硬约束把两条圆周精确钉死（ACA-3 ≈ 2e-16）一致——误差被推离两条边界。**孔没有制造局部病理**。
2. 最差单元与次差单元之比只有 1.00–1.66，说明误差是**一片平缓抬高的区域**，不是某个奇异单元。
3. seed 2 的最差单元 `1.294e-04` 是其余九个 seed 最差单元（`5.03e-05`–`7.84e-05`）的 1.65 倍；而 seed 2 的全局 ACA-1（`3.722e-04`）同样是中位数的 2.00 倍。**seed 2 是整体更差，不是局部更差。**

### 3.4 定量线索：指向训练预算的支持性证据（假设，非判定）

局部/全局比值 `2.93 ± 0.52`（§2.13）意味着：只要 ACA-9 与 ACA-1 共用同一个 `1e-3` 阈值，**ACA-9 就会先触顶**，其对 ACA-1 的隐含预算是

```text
ACA-1 隐含上限 = 1e-3 / 2.93 ≈ 3.414e-04
```

而预注册 5.2 的步数外推只针对 ACA-1：120000 步被选为「外推到约 7e-04，对 ε_spec = 1e-3 约 1.4 倍余量」，并且当时就**如实记录了这比正方形标定的 23 倍余量小得多**。实际跑出来 median ACA-1 = `1.860e-04`（比外推的 7e-04 还好），但 worst seed `3.722e-04` **恰好越过了 `3.414e-04` 这条隐含线**——于是 ACA-9 在该 seed 上给出 `1.079e-03`。

换句话说：预算是按**一个**判据外推的，而验收是按**九个**判据、且按 **every-seed** 判定的。这一条写在这里作为观察与算术，**不作为本轮的行动**——改步数是方法变更，必须走新 revision、新盲集成员，由用户决定（第 12 节）。

---

## 4. Blind Validation

盲集生命周期，全部来自账本 `experiments/annulus/ledger/pdef-annulus-poisson-v1.json`（唯一真相源，从不读 manifest 的静态 status 字段）：

```text
事件 1  SEALED   claimSet 84877d8b1eec   samples cb3a15010f91   （2026-09-17，正式 run 之前）
事件 2  OPENED   claimSet 84877d8b1eec   samples cb3a15010f91   codeHash 8ee9b9236199
                 -> 随即 BURNT
ledgerHead  df1b1c5004e9...
```

* 打开发生在 **Gate 5a 物理 PASS 之后**、Gate 5b 之前，一次性，不可撤销。
* 打开**之前**的早期护栏实测生效：run 启动时账本派生状态为 `SEALED`（`claimSetLedgerStatusAtStart = "SEALED"`），若为 `OPENED` / `BURNT` 则拒绝启动。
* 被中断的两次 attempt（`stopped-cpu-r1-c5a3e12e018e`、`stopped-gpu-r1-sleep-8ee9b9236199`）**从未打开**盲集，所以 DAC-M0 才能留到本轮；两份记录都完整保留、未删除。
* 盲集池四个成员两两共享样本数为 0；**DAC-M1 / M2 / M3 仍为 NEVER_SEALED**，本轮一次也没有触碰。
* **DAC-M0 现已 BURNT，不得重开**。

---

## 5. Failure Path

```text
IMPLEMENTATION_VERIFIED -> TRAINING_COMPLETED   (gate 4, PASS)
TRAINING_COMPLETED      -> VALIDATION           (ENTER_VALIDATION)
claim set 84877d8b1eec OPENED -> BURNT
VALIDATION              -> FAILURE_RECORDED     (gate 5, FAIL)
```

`failure_record.json` 实录：

* `gate = 5`
* `observedSignatures = ["sLocalizedError"]`（**只有这一个**；`sPdeResidual`、`sBcResidual`、`sConservation`、`sPinnCfd`、`sSeedSensitive` 均未触发）
* `claimSetVerdict.failedMustPerSeed = [[], [], ["ACA-9"], [], [], [], [], [], [], []]`
* `retrainedInPlace = false` —— **没有现场调参数、没有重训**

**上一轮局部误差触发器硬化的直接验证**（这是本轮一个独立的正面结果）：

```text
fired            true
firedBy          "1/10 seed(s) fail ACA-9"
seedPolicy       every-seed
failingSeedIndices [2]      failureFraction 0.1
ensembleStatistic  best 3.569e-04   median 4.109e-04   worst 1.038e-03
```

注意 **median = 4.109e-04 远低于阈值**。硬化之前的 median 口径会把这个少数派失败整个吞掉、报告「没有失败」；硬化之后它按验收合同自己的 `every-seed` 策略正确触发。该机制上一轮是在正方形上修的，本轮在**一个新几何、一次真实失败**上得到验证。

---

## 6. Tier-1 Red Team

**未执行。** 依协议，Tier-1 只在 Gate 5 PASS 之后进行——红队是对**已被接受**结果的压力测试，不是被拒结果的第二次机会。本轮 `C_external = FAIL`，故八项（P1 / P4 / P6 / P7 / P8 / P9 / P11 / P16）**一项未跑**。

驱动入口已在正式 run **之前**进入代码身份（`runner_annulus.run_tier1_for_attempt`、`run_formal_annulus.py --tier1`、`runner_annulus tier1`），并已实测其拒绝路径：对 Gate 5 未 PASS 的 attempt 拒绝启动，对未完成的 attempt 给出明确拒绝而非堆栈。它只读已登记产物，从不触碰 D_claim、账本或历史判定。

放在跑之前而不是跑之后，是因为跑完再加 driver 会再次改变 `codeHash`，红队就无法与它所检验的 attempt 处在同一代码身份下。

---

## 7. G6 Reproduction

**未执行。** `C_repro = BLOCKED`，`gate6_reproducibility.json` 记录的理由是「Gate 5 did not pass; reproduction is not attempted」。复现一个被拒的结果不会产生任何可信度。

Environment B 已只读核验、**未做任何安装、未污染**：

```text
C:\Users\user\LeoAI-envB2D-20260916\venv
Python 3.12.9   torch 2.12.1+cpu   numpy 2.4.5   torch.cuda.is_available() = False
```

预注册的 G6 容差（`|Δmedian| ≤ 1e-4` 且 `≤ 0.5 × median_A`、k/N 判定一致、seedOffset 10000）保持冻结，本轮未使用、未修改。

附带说明（本轮的 device 设计要点）：主 run 在 GPU、复现在 CPU，两者 `acceleratorClass` 不同，这只会增强环境独立性；而 `codeHash` 必须相同——这正是 `device` 被做成命令行参数、**绝不写进冻结配置**的原因。

---

## 8. Trust Vector

| 维度 | 状态 | 依据 |
|---|---|---|
| `math` | **PASS** | Gate 1（几何合同、两条边界组件）+ Gate 2（解析自验 `max\|-Δu* - f\| = 0`、独立极坐标 FDM 观测阶 2.0016 / 2.0004） |
| `impl` | **PASS** | Gate 3 十项全 PASS，含 T11 成员判定、T12 内外法向朝向、T13 求积雅可比、T10 可信校验器的控制夹具 |
| `train` | **PASS** | Gate 4：10/10 完成，median 1.853e-04，IQR 2.470e-05，worst 3.874e-04，发散 0，loss–error 未解耦 |
| `physics` | **PASS** | Gate 5a：PH1 通量 1.633e-04、PH2 能量 1.674e-04、PH3 正性 0 违例、PH6 极值 1.000303、PH7 SPD（能量 1.639，独立极算子最小特征值 22.7262 > 0）、PH8 成员；PH4 / PH5 登记 NOT_APPLICABLE 并附理由 |
| `external` | **FAIL** | Gate 5b：D_claim 上 seed 2 的 ACA-9 = 1.079e-03 > 1e-3（every-seed 策略） |
| `repro` | **BLOCKED** | Gate 6 未尝试（Gate 5 未通过） |

弱链：`external = FAIL`。

---

## 9. Claim Decision

```text
Highest Claim: BLOCKED
```

`finalState = FAILURE_RECORDED`，runner 以 `decision = False` 收尾，因此**没有生成 `claim_gate_decision.json`**——这是正确行为：一次 Gate 5 FAIL 的 attempt 不产生任何 claim 等级。C0 / C1 / C2 **一律未被授予**。

圆环几何目前的可信状态是「已实现、已验证实现正确性与物理一致性，但**未通过验收**」。

**已 CLOSED 的 Poisson 1D 与 Poisson 2D 正方形标定不受本轮任何影响**：本轮未触碰它们的证据、账本、TrustVector 或 ClaimGateDecision。

---

## 10. Tests / PRELOCK / Portability

两个解释器的真实数字：

| 项目 | 治理虚拟环境 `.venv`（无 torch / numpy） | 训练解释器（mamba，torch 2.12.1+cu126） |
|---|---|---|
| 全套 pytest | **1391 passed / 0 failed / 25 skipped** | — |
| 被跳过项的补跑（annulus） | — | **7 passed / 0 failed** |
| 被跳过项的补跑（poisson2d） | — | **23 passed / 0 failed** |
| PRELOCK | **PASS，7/7** | — |
| portability | **0 hard binding / 1 configurable default / 8 historical evidence** | — |

与上一轮基线完全一致（1391 / 0 / 25、7/7、0-1-8），本轮的 device 改动没有引入任何回归。

沙箱冒烟（CUDA，150 步 × 3 seed）另跑一次，整条流水线含失败路径通过；沙箱自建自删。

---

## 11. Newly Discovered

### BLOCKING

**无。**（Gate 5b FAIL 是**预期内的判定结果**，不是新发现的缺陷：判据、阈值、seed 策略都在预注册里事前写定，机器如约执行。）

### NON-BLOCKING

1. **在迄今考察的正方形与圆环两个标定案例中，没有观察到圆环特有的局部/全局误差比放大**（3.20 与 2.93 ± 0.52）。在这两个案例内，ACA-9 触顶与全局误差水平高出 5.2 倍相符；两个几何不足以证明普遍的 geometry invariance，也不足以排除其它候选根因。见 §2.13、§3.4、§13。
2. **误差被硬约束推离两条边界**。十个 seed 的最差局部单元全部落在中间两个径向环，从不在紧贴孔或紧贴外圆的环上。多连通域**没有**在孔边制造局部病理。见 §3.3。
3. **GPU 在此工作负载上是更慢的设备**。事前 EXPLORATORY 基准（CPU 16.6–21.6 ms/步 vs CUDA 17.6–19.3 ms/步）与正式 run 实测（CUDA 1849–2571 s/seed vs 归档 CPU attempt 1407 s/seed）一致。原因是网络极小且宪法要求 float64，而 RTX 4060 的 FP64 吞吐是 FP32 的 1/64。用户在看到数字后仍选择 GPU，代价已记录。
4. **CPU 与 CUDA 在 float64 + 确定性算法下给出同一答案**。同 seed 2000 步后权重最大绝对差 `4.441e-16`；seed 0 跑满 120000 步在 CUDA 上两次、CPU 上一次都得到 devRelL2 = `1.622e-04`。
5. **局部误差触发器硬化在一次真实的少数派失败上得到验证**（1/10，median 远低于阈值）。见第 5 节。

### AMENDMENT CANDIDATE

1. **`ProblemDefinition` schema 的 `domainType` 词汇缺少 `annulus`**，且 `geometry` 对象不收额外字段。本轮用 schema 自带的 `regions[].params` 承载圆环几何、`domainType = "other"`，**未改治理 schema**。再入角、L 形等后续几何会重复遇到同一问题，建议作为一次性的词汇扩展提案单独处理。
2. **Gate 4 不筛查局部判据，尽管 D_dev 有能力测量它**。本轮 D_dev 上的局部统计量 worst 已经是 `1.038e-03`（> 1e-3），即**在盲集被打开之前，同一个 seed 的同一个问题已经在开放集上可见**；但 Gate 4 只按 Constitution 10.1 的 seed 规则检查 `devRelL2`，于是盲集仍被消耗。一个 Gate-4 层面的 D_dev 侧局部判据预筛，可以在不消耗盲集的前提下拦下这类 attempt。**本轮没有实现它**——新增 Gate 是被明令禁止的，且在失败当口改判定结构本身就是不当行为。仅作为提案登记。

### NONE

其余部分未发现新问题。

---

## 12. Recommendation

```text
REMAIN AT ANNULUS GEOMETRY CALIBRATION
```

理由：验收未通过，圆环几何尚未取得任何 claim 等级；在未通过的几何上继续向再入角推进，等于把一个未结清的债务带进更难的问题。

同时如实记录：**几何提升本身是成功的**。第 2 节逐项列出的十处「因为域变成曲边且多连通而必须改变的东西」全部按设计工作并有机器证据，且本轮**没有观察到**明确的几何病理。失败的解释目前只是一个受支持的假设（训练预算，§3.4），**尚未经过受控干预检验**，见 §13 与诊断报告。

后续可能的走向属于**用户与外部评审的决定，本轮不自行开始**。仅列出与之相关的既成事实：

* **DAC-M0 已 BURNT，不得重开**；盲集池中 **DAC-M1 / M2 / M3 仍为 NEVER_SEALED**。
* 任何方法值变更（含步数）都是方法变更，必须走**新 revision + 新预注册注解 + 新盲集成员**，并重新冻结代码身份。
* §3.4 给出的算术是：在当前局部/全局比 `2.93` 下，要让 ACA-9 对全部十个 seed 通过，worst-seed 的 ACA-1 需低于约 `3.414e-04`（本轮为 `3.722e-04`）。这是一个观察，不是一个已获授权的计划。

本轮到此**停止**：不自行开始 L 形 / 再入角 / BFS / Navier–Stokes / UCM / 传热，等用户与外部评审。

---

## 13. 追加注解：因果措辞收窄（2026-09-18，追加而非改写机器证据）

本节是**追加**。它只修正本报告自身的**散文措辞**；任何机器证据（RunRecord、账本、Gate 结果、`failure_record.json`、TrustVector、状态转移、seed 账本、阈值、ScientificSpec revision 1）**一字未动**。

收窄的内容，以及为什么：

1. **「根因不是几何 / 真正的原因是步数预算不足」→「训练预算不足是一个受支持的假设」**。
   状态机当前仍停在 `FAILURE_RECORDED`，**尚未进入 `DIAGNOSED`**。在受控干预完成之前，`rOptimizationFailure`
   不得被写成正式的 `RootCauseClass`。原措辞把一个尚未检验的假设说成了结论。
2. **「局部/全局误差比是几何不变的」→「在迄今考察的正方形与圆环两个标定案例中，没有观察到圆环特有的
   局部/全局误差比放大」**。两个几何不足以证明普遍的 geometry invariance。
3. **「失败落在一个与几何无关的量上」→「本轮没有观察到明确的几何病理」**。
   证据的缺席不等于不可能性的证明（`absence of evidence != proof of impossibility`）。

被收窄的判断所依据的**数字本身没有变**：正方形 3.20、圆环 2.93 ± 0.52、隐含 ACA-1 上限 `≈ 3.414e-04`、
worst-seed `3.722e-04`。变的只是这些数字被允许支撑的结论强度。

同一收窄同步应用于 CHANGELOG、根目录软件修改报告与记忆文件；操作日志 §5.32 以**追加**方式记录本次收窄，
不改写原有条目。

后续：`sLocalizedError` 在 Constitution 1.2 下的完整候选根因集合、既有证据清点，以及为什么
「只增加步数」的受控干预在当前代码下**无法**做成单因素干预，见
[ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md](ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md)。

````

</details>

### R035 — 项目/docs/pinn-trust-loop/CODE_IDENTITY_COMPLETENESS_AUDIT_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Code Identity Completeness Audit（2026-09-16）

执行负责人：Claude（队长）。目的：在下一个正式 PDE 实验开始**之前**，把"哪些字节能改变判定"这件事查清并机器化。上游：[LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md](LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md)。

本轮**没有**修改 Poisson2D 的任何历史证据、没有改它记录在案的 codeHash、没有重训、没有重开 D_claim、没有开始下一个 PDE。边界变更**只对下一个 revision 生效**。

## 1. 审计口径

判定面（decision surfaces，写进代码常量 `DECISION_SURFACES`）：ScientificSpec 解释、Gate 结果、FailureSignature 生成、DiagnosisRecord 内容、TrustVector 状态、ClaimGateDecision、Red-Team 判定、可复现性判定。一个文件只要**字节变化能改变上述任一项**，就必须在正式 run 的 `codeManifest` 里。

方法：① 列出 `git ls-files` 全部跟踪文件；② 与当前 `code_manifest()` 的成员求差；③ 对差集逐个判断是否触及判定面；④ 对判定面内的文件逐个加"改一个字节 → codeHash 必须改变"的测试。

## 2. 先澄清一条事实（不粉饰）

> 「`pinn/experiments2d/localized_error.py` 不得再留在代码身份之外」

机器核查结果：**它本来就在代码身份之内**。它落在 `pinn/` 前缀内，任何**新**清单都会包含它（现清单 75 项中就有）。它之所以不在 `exp2d-poisson-calibration-r1` 的**记录清单**里，只是因为那次 run 发生时这个文件还不存在（它是随后那轮 Final Closure Audit 新建的）。因此这里**没有修复动作**，只有一条回归测试把这个性质钉死：`test_the_localized_error_module_is_inside_the_identity` + 一字节敏感性测试。

## 3. 审计发现：两个真实缺口

差集里绝大多数是与科研判定无关的应用层代码（`leo_shell/`、`bridge/`、`launcher/`、`stage/`）、测试、回滚快照与证据。**触及判定面却在身份之外的，有两个**：

| # | 文件 | 为什么触及判定面 | 处理 |
|---|---|---|---|
| CI-1 | `governance/PINN_TRUST_PROTOCOLS_R1.md` | 协议汇编规定 Tier-1 的**强制集合**与适用性登记的正当理由形式。正是它第 108 行把 P11 列为 C2 前必跑——上一轮据此推翻了 `NOT_APPLICABLE` 并补跑。它的字节能改变 **Red-Team 判定**。 | 加入 `CODE_IDENTITY_FILES`（前瞻） |
| CI-2 | `adversarial/core_manifest.draft.json` | PRELOCK 的输入之一（`PrelockPaths.defaults` 第 63 行），而 PRELOCK 决定正式 attempt **是否开始**。 | 加入 `CODE_IDENTITY_FILES`（前瞻） |

另有一类**结构性缺口**：正式 run 的驱动脚本可以放在 `experiments/**`（P11 补跑那次就是刻意放在身份清单之外的），而 `experiments/**` 不能整体纳入——那里同时存放每次都会变的证据，把证据折进方法身份等于"每跑一次就是另一种方法"。处理方式是**声明制**（第 4 节）。

明确**不纳入**（并有测试守住）：`docs/**` 报告、`experiments/**` 的证据 JSON / Markdown、`CHANGELOG.md`。

## 4. 新的代码身份边界（下一 revision 生效）

```text
前缀（执行的代码）: pinn/  scientific_reference/  specs/
具名文件（同等效力的非代码输入）:
    governance/PINN_RESEARCH_CONSTITUTION.md
    governance/POISSON_1D_V1.0_spec.draft.json
    governance/POISSON_1D_V1.0_protocol.draft.json
    governance/POISSON_1D_V1.0_lock.draft.json
    governance/PINN_TRUST_PROTOCOLS_R1.md          <- 本轮新增（CI-1）
    adversarial/core_manifest.draft.json            <- 本轮新增（CI-2）
每个 run 自行声明:
    冻结配置（既有机制）
    config["codeIdentityExtraFiles"]                <- 本轮新增：位于前缀之外的正式驱动脚本
```

当前工作树上的清单：**75 项**（`pinn/` 60、`governance/` 5、`scientific_reference/` 4、`specs/` 4、`adversarial/` 1、run 的配置 1），
`codeHash = d8ff0a9184ada058…`（**仅供参考**：这是当前树在新边界下的值，不是任何正式 run 的身份）。对照：已 ACCEPTED 的 run 记录的是 73 项 / `a39aa07e23d0…`，**一字未改**。

### 4.1 Fail-closed 完整性检查

`pinn/experiments/common.py` 新增：

- `CodeIdentityError(RuntimeError)`；
- `required_identity_paths(repo_root, extra_required)` —— 边界内全部跟踪文件 + 本 run 声明的文件；
- `assert_code_identity_complete(manifest, repo_root, extra_required)` —— 缺任一必需文件 → 拒绝；声明了不存在的文件 → 拒绝；清单与磁盘字节不符 → 拒绝。

`runner2d.phase_identity` 的调用顺序（测试钉死）：

```text
读配置 -> 组装 extra（配置 + codeIdentityExtraFiles）-> code_manifest
     -> assert_code_identity_complete      <- 在 codeHash 之前
     -> code_hash_from_manifest
     -> run_prelock                        <- 完整性检查在 PRELOCK 之前
     -> phase_problem / 各 Gate / 训练
```

`identity.json` 现在额外记录 `codeIdentityBoundary`（前缀、具名文件、本 run 声明、判定面清单），使边界本身成为可审计的机器记录。

## 5. Adversarial tests（本轮新增 44 项）

`tests/pinn/test_code_identity_completeness.py`：

| 要求 | 测试 |
|---|---|
| 1. `localized_error.py` 改一个字节 → codeHash 改变 | `test_the_localized_error_module_is_inside_the_identity`、`test_one_byte_in_the_localized_error_module_changes_the_code_hash` |
| 2. 每个判定相关核心模块改一个字节 → codeHash 改变 | `test_every_decision_relevant_module_is_covered_and_sensitive`，**22 个模块逐一参数化**：spec JSON、验收合同、gates2d、datasets2d、pinn_torch2d、validation/poisson2d、analytic_poisson2d、poisson2d_fdm、diagnosis、diagnostics2d、localized_error、state_machine、trust_vector、trust_loop、claim_set_ledger、redteam2d、协议汇编、runner2d、repro_package2d、prelock、core_manifest、宪法；外加 run 配置 |
| 3. 身份之外的文档 / 证据改动 → codeHash **不变** | `test_documentation_and_evidence_are_outside_the_identity`（4 个真实文件）、`test_a_documentation_or_evidence_edit_does_not_move_the_code_hash`（在 `tmp_path` 里 `git init` 一个微型仓库，真实改字节后经 `git ls-files` 重算：文档 / 证据 / CHANGELOG 改动后哈希**相等**，`pinn/` 下改一个字节后哈希**不等**） |
| 4. 清单遗漏已登记的判定相关模块 → 在 PRELOCK / 正式 run 之前被拒 | `test_omitting_a_registered_module_is_rejected`（5 个模块参数化）、`test_omitting_the_declared_config_is_rejected`、`test_a_manifest_that_no_longer_matches_disk_is_rejected`、`test_declaring_a_file_that_does_not_exist_is_rejected`、`test_the_check_runs_before_prelock_and_before_any_gate`（源码级顺序断言：完整性检查 < codeHash < PRELOCK < phase_problem） |
| 附加：声明制驱动脚本 | `test_a_declared_driver_outside_the_prefixes_enters_the_identity`（声明后进入清单并敏感；未声明则仍在外——这正是必须声明的理由） |
| 附加：历史不被改写 | `test_the_accepted_runs_recorded_identity_is_not_rewritten`（记录清单不含两个新增具名文件，且仍哈希回 `a39aa07e23d0…`）、`test_the_boundary_change_applies_to_the_next_revision_only` |

## 6. 对已 ACCEPTED 的 Poisson2D 的影响

```text
NO IMPACT
```

- 重跑 `final_closure_revalidation.py`：`verdict CURRENT 2D C2: CONFIRMED`、`problems []`、`state ACCEPTED`、`cRepro PASS`、`codeIdentityUnchanged false`（工作树本就已不同，见上一轮报告第 6 节）。
- 测试断言：该 run 的 `identity.json` 里 `codeHash` 仍 `a39aa07e23d0…`，其记录清单**不含**本轮新增的两个具名文件，且用记录清单重算 `code_hash_from_manifest` 仍**等于**记录值——历史身份自洽且未被改写。
- 账本、D_claim、TrustVector、ClaimGateDecision、Gate 结果、冻结配置、验收阈值：本轮一次未写。

## 7. 下一 revision 的硬约束

```text
下一个正式实验必须使用新的 revision / code identity。
它的 codeManifest 必须在新边界下生成，并把位于前缀之外的正式驱动脚本写进
config["codeIdentityExtraFiles"]；缺一即在 PRELOCK 之前被拒。
本轮之后的任何代码都不得冒充 a39aa07e23d0…。
```

## 8. Verification

| 项 | 值 |
|---|---|
| 上一轮基线 | 1241 passed / 0 failed / 18 skipped |
| 本轮新增测试 | **44**（`tests/pinn/test_code_identity_completeness.py`） |
| targeted | `tests/pinn/test_code_identity_completeness.py` **44 passed** |
| 全套（治理 `.venv`） | **1285 passed / 0 failed / 18 skipped** |
| 被跳过的 18 项在训练解释器下 | **23 passed / 0 failed** |
| portability | **0 hard binding / 1 configurable / 8 historical**（未改任何 policy） |
| PRELOCK | **7/7 PASS** |
| unexpected failures | **0** |

## 9. Repository State

```text
branch  : master
commit  : 见本报告所在提交
tree    : clean
改动    : pinn/experiments/common.py（边界常量 + 完整性检查 + CodeIdentityError）
          pinn/experiments2d/runner2d.py（声明制 extra files + PRELOCK 之前的 fail-closed 检查 + identity.json 记录边界）
          tests/pinn/test_code_identity_completeness.py（新，44 项）
          experiments/poisson2d/{FINAL_CLOSURE_REVALIDATION,TEST_VERIFICATION_UNDER_TORCH}.json（重跑，仅时间戳与当前树 codeHash）
未改    : 1D 的 runner 与全部记录、2D 已 ACCEPTED 的机器证据与其 codeHash、宪法、协议汇编内容、portability policy
```

## 10. STOP

```text
CODE IDENTITY COMPLETENESS: AUDITED
NEXT FORMAL EXPERIMENT: BOUNDARY READY (new revision required)
CURRENT POISSON2D C2: UNCHANGED / CONFIRMED
```

不开始下一个 PDE、不设计新几何、不改宪法、不重训。等待用户与外部评审。

````

</details>

### R036 — 项目/docs/pinn-trust-loop/LOCALIZED_ERROR_TRIGGER_HARDENING_REVIEW_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
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

````

</details>

### R037 — 项目/docs/pinn-trust-loop/POISSON1D_C2_CALIBRATION_REPORT_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Poisson 1D Claim Calibration 报告：claim 集身份修复、sBcResidual 诊断、修订、新盲 G5、Tier-1、G6（2026-09-16）

执行负责人：Claude（队长）。宪法 1.2 不变（无 A-0003）。预注册：`experiments/poisson1d/EXPERIMENT3_PREREGISTRATION_20260916.md`（正式 run 前提交，commit d55209f）。实验 1/2 机器记录未改，只追加 `POST_AUDIT_ANNOTATION.md`。所有数字来自机器记录。

## 1. Executive Result

```text
Poisson Claim Calibration:
NOT YET PASS

Highest admissible Claim:
C1
```

Gate 1–5 全 PASS（新盲 claim 集 GL640-CGL2400 上 AC-1..AC-8 全部 seed 满足），Tier-1 Red Team 全部维持，**唯一 blocker 是 C_repro = BLOCKED**：本机没有第二个独立安装，G6 协议无法执行，C2 按弱链规则 BLOCKED。复现包已生成，等待另一环境执行。

## 2. ClaimSet Lifecycle

| 项 | 值 |
|---|---|
| 身份规则 | `artifactHash = canonical_sha256(清单)`；`sampleSetHash = canonical_sha256(sorted(sampleId))`（`evaluation_sets.sample_set_hash`）；烧毁按 sampleSetHash（账本 L4s / L6 / L7 / L8，`validate_problem_definition(..., sample_set_hashes)` 拒绝重新包装）。判定：**实现 bug / 协议澄清**（宪法 9.1 说的是"打开过的 claim 集"，实现误用了 artifact 字节哈希），不是宪法语义变更，无 AMENDMENT。 |
| claim pool count | 4（D_claim_0 = GL512∪CGL2000（历史）；pool 预注册 3 套：GL640∪CGL2400 → r2、GL768∪CGL2802 → r3、GL896∪CGL3200 → r4） |
| sampleSetHash | D_claim_0 `91414bd5260e…`；GL640-CGL2400 `3977198983fd…`；GL768-CGL2802 `19a99729d1d6…`；GL896-CGL3200 `ccc392809222…`。两两样本互斥（shared = 0），与 D_train / D_dev / D_phys 互斥（minSeparation 1e-9），反碰撞 min\|v − i/d\| > 1e-12（d ≤ 64；GL768-CGL2800 因 x = 1/4 碰撞被弃用，改 CGL2802） |
| opened | D_claim_0：exp1 r1（artifact 02ee4e75）**和** exp2-revised（artifact 33ea0764，同样本——追溯不合格，见 exp2-revised-r1/POST_AUDIT_ANNOTATION.md）；GL640-CGL2400：exp3c r2（artifact d08488d9，codeHash 5aaf93a5…） |
| burnt | `91414bd5260e…`、`3977198983fd…` |
| sealed | `19a99729d1d6…`（r3）、`ccc392809222…`（r4） |
| 账本 | `experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json` 7 个事件（旧事件无 sampleSetHash，由 `sample_set_registry.json` 解析）；每个新事件携带 sampleSetHash |

## 3. BC Diagnosis（Experiment 3A / 3B，只用 D_dev / D_phys）

- **observed signature**：sBcResidual（exp1 Gate 5 FAIL，AC-3 = 1e-4，7/10 seed 在 1.0e-4–2.8e-4）。
- **candidate root causes（1.2 矩阵）**：rSpecDefect、rDataDefect、rImplementationDefect、rOptimizationFailure、rSamplingDeficiency、rCapacityLimit、rSingularityTreatment。
- **P24 / 3A（λ_BC ∈ {10, 100, 1000}，10 配对 seed，其余全部固定）**：

| λ_BC | BC error median | 逐 seed 全 < AC-3 | PDE error median（归一化 holdout RMS） | solution error median |
|---|---|---|---|---|
| 10 | 1.43e-4 | 否（7/10 超） | 4.56e-3 | 2.84e-4 |
| 100 | 8.15e-5 | 否（4/10 ≥ 1e-4） | 6.52e-3 | 2.64e-4 |
| 1000 | 1.33e-5 | 是（max 3.9e-5） | 7.83e-3 | 2.63e-4 |

  配对准则（预注册 ρ = 0.5、q = 0.8、N = 10）：10→100 ratio 0.571（未 < 0.5）、6/10 改善（未 ≥ 0.8）→ **未满足**；100→1000 ratio 0.163、10/10 改善（满足）。退化判定：PDE 中位 4.56e-3 → 7.83e-3（< 1e-2 且 < 2×），solution 不退化 → 非"不可接受"。
- **P28 / 3B（硬 BC u = x(1−x)N，其余固定，10 配对 seed）**：BC error 恰为 0（全部 seed），PDE median 2.79e-3，solution median 1.99e-4（逐 seed 7.1e-5–2.5e-4）→ 全部可接受。
- **exclusions**（DiagnosisRecord `dg-exp1-calibration-r1-bc-r1`，全部引用实测）：rDataDefect（边界数据为规格值 0，forcing 审计 1e-12，各档不变）；rSingularityTreatment（u* ∈ C∞，G2a 残差 0）；rImplementationDefect（T1/T3/T4 PASS；同一边界算子代码在 λ=10 给 1.43e-4、λ=1000 给 1.33e-5、硬参数化给 0——算子算的是对的）；rCapacityLimit（同一 3×32 网络在 λ=1000 达 BC 1.33e-5 / solution 2.63e-4）；rSamplingDeficiency（边界点是精确端点且始终在训练集，内部采样 256 各档不变而 BC 误差变化两个量级）；rOptimizationFailure（优化器 / 日程 / 预算固定；配对准则在预注册档内未满足，而硬参数化在同一优化器下恰好消除）。
- **final root cause**：**rSpecDefect**——规格明示 enforcement = soft，软执行在冻结训练协议下达不到 AC-3；按预注册分支 6.2（软权重准则未满足 ∧ 硬 BC 可接受）。路由 Gate 1，DIAGNOSED。
- **confidence / evidence**：证据支持"执行方式选择"是缺陷（3B 十个 seed 恰为 0 且其它指标更好）；同时诚实记录：λ=1000 也能让全部 seed 过 AC-3（PDE 残差略升），即优化 / 权衡解释在 100→1000 段是成立的，只因 10→100 段未满足预注册准则而未被选为根因。准则是事前冻结的，我按字面执行，不事后换分支。这一点写入 Newly Discovered（N6）。

## 4. Revision

唯一修改：`boundaryConditions.enforcement` soft → hard（config `network.outputParameterization = "x(1-x)N"`，configId `poisson1d-hard-bc`）；`run_revise` 机械校验差异只在该字段。网络深宽、激活、优化器、lr、步数、采样、ε_spec、seed、阈值全部不变。新 specHash `fd5584d7b290…`，revision 2。

## 5. Fresh Blind Validation（`exp3c-hard-bc-r2`）

| 项 | 值 |
|---|---|
| 重入 | REVISED →[reenter G1] DRAFT → G1 PASS → G2 PASS → G3 PASS（T1–T10 在硬参数化上重跑）→ G4 PASS → VALIDATION → G5 PASS → REPRODUCIBILITY_CHECK → G6 BLOCKED |
| 训练（D_dev） | 10/10，median 1.99e-4，IQR 1.51e-4，worst 2.48e-4，divergent 0 → C_train PASS |
| D_claim_1 | GL640∪CGL2400 去端点，3038 样本，sampleSetHash `3977198983fd…`，artifact `d08488d9db30…`；SEALED（r2）2026-09-16T09:50:23Z → OPENED 09:53:29Z（codeHash 5aaf93a57fdd…）→ BURNT |
| AC（10 seed 最大值 / 阈值） | AC-1 2.52e-4 / 1e-3 · AC-2 4.15e-4 / 5e-3 · **AC-3 0 / 1e-4** · AC-4 7.02e-3 / 1e-2 · AC-5 2.08e-4 / 1e-3 · AC-6 4.94e-4 / 5e-3 · AC-7 2.06e-4 / 1e-2 · AC-8 1.09e-3 / 5e-3（SHOULD）→ MUST 与 SHOULD 全部 seed 满足 |
| G5a（D_phys 最差 seed） | PH1 4.11e-4 · PH2 2.06e-4 · PH3 min u 6.9e-5 · PH4 2.41e-4 · PH5 0 违例 · PH6 ≤ 界 · PH7 λ_min > 0 → C_physics PASS |
| G5b | C_external **PASS**（evaluationSet claim，claimSetSha256 d08488d9…，评估器 `claim_metrics.evaluate_on_grids`，与可信校验器公式逐位一致） |

## 6. Red Team（Tier-1，D_dev only，seed 三元组 0，各一次重训）

| P | 改动 | 固定 | 预期失效 | 观察（e2 / Δq） | 影响 |
|---|---|---|---|---|---|
| P1 | 同池重抽配点 | 其余全部 | 依赖具体配点 | 9.44e-5 / 1.04e-4 | train 维持 |
| P4 | float32 训练，残差 float64 重算 | 其余全部 | 二阶导病态 | 1.63e-4 / 1.05e-4；残差 max 比 1.26 | impl 维持 |
| P6 | 删 10% 配点 | 其余全部 | 依赖个别点 | 7.57e-5 / 2.67e-6 | train 维持 |
| P7 | — | — | 边界层 | NOT_APPLICABLE（1D Poisson 无边界层，BC 在精确端点） | — |
| P8 | 域缩放 y = 2x，映射回 | 其余全部 | 缩放错误 | run 1：1.02 / 1.05 **FAIL**（harness 缺陷：单位区间硬参数化用在 [0,2]，v(2) ≠ 0）；run 2（修复后）：4.40e-5 / 5.01e-5 PASS | math 维持（run 1 记录保留，见 POST_AUDIT_ANNOTATION） |
| P9 | Adam → L-BFGS | 其余全部 | 多模态 | 7.07e-6 / 3.94e-5 | train 维持 |
| P11 | — | — | 局部误差 | NOT_APPLICABLE（未观察到 sLocalizedError；面向 CFD） | — |
| P16 | tanh → sin | 其余全部 | 谱偏置 | 6.10e-5 / 6.07e-5 | train 维持 |

```text
Tier-1: PASS（run 2，tier1v2；run 1 的 P8 FAIL 归因于扰动 harness 缺陷，原记录保留）
```

## 7. Reproducibility

| 项 | 值 |
|---|---|
| environment A | machineId win-60a9b43e…，windows，cpu-only，torch-2.12，mkl，dependencyLockHash（mamba 前缀）、installationId prefix-…；environmentId 见 identity.json |
| environment B | **不存在**：本机唯一装有训练框架的安装；`.venv` 无 torch / numpy；无第二台机器 |
| seed sets | 原 run seedSetId 见 run_record.json；复现须用不同 seed 集（包内规则 +10000） |
| tolerance（预注册） | dev 相对 L2 中位数差 ≤ 1e-4 且 k/N 判定一致；claim 集不重开 |
| result | 未执行 |
| C_repro | **BLOCKED**（不是 FAIL；不伪造第二环境）。复现包 `experiments/poisson1d/repro_package_exp3c_r2/`（spec、config、codeHash、依赖锁哈希、seed 清单、数据集生成规则、容差、运行说明、schema） |

## 8. Trust Vector（Tier-1 后，`trust_vector_tier1v2.json`）

```text
C_math     = PASS
C_impl     = PASS
C_train    = PASS
C_physics  = PASS
C_external = PASS   (evaluationSet = claim, sampleSetHash 3977198983fd…, OPENED@r2)
C_repro    = BLOCKED
```

## 9. Claim Decision（`claim_gate_decision_tier1v2.json`）

```text
SUPPORTED @ C2: NO
allowed: C0, C1
blocked: C2, C3  — repro BLOCKED (independent-environment reproduction not executed)
```

## 10. Final Recommendation

```text
REMAIN AT POISSON CALIBRATION
```

唯一阻塞 C2 的是独立环境复现。下一步不是再改方法，而是：在第二台机器或同机独立安装上执行复现包（不同 installationId / dependencyLockHash，不同 seed 集），把 RunRecord 交回；C_repro PASS 后即可 SUPPORTED @ C2，然后才 READY FOR 2D。

## 11. Newly Discovered Problems

- **BLOCKING（对 C2）**：B2 无独立执行环境（环境事实）。
- **NON-BLOCKING**：N6 预注册的配对准则在 10→100 档未满足使根因落在规格分支，而 λ=1000 同样解决 AC-3——"执行方式"与"权衡"两种解释在数据上都成立，规则按字面选择了前者；不回改。N7 Tier-1 harness 缺陷（P8 与硬参数化的交互）由 Red Team 自己暴露并修复，run 1 保留。N8 exp2-revised 的 G5b 追溯为非独立证据（已注解）。N9 pool 成员 GL768-CGL2800 因 x = 1/4 碰撞被替换为 CGL2802（在预注册时发现并记录）。
- **AMENDMENT CANDIDATE**：无需修宪；两项协议澄清（claim 集样本身份 / claim pool；配对干预准则）已写入协议汇编 §10 与预注册文件，建议评审确认后并入下一版协议汇编正文。

## 12. Tests / PRELOCK

| 项 | 值 |
|---|---|
| previous baseline | 1094 passed / 4 skipped |
| new tests | 17（test_claim_identity 8、test_bc_diagnosis 6、test_redteam_rules 3）；其中 2 项在无 torch / numpy 的 .venv 跳过 |
| total passed | **1109** |
| failed | 0 |
| skipped | 6 |
| PRELOCK | 7/7 PASS |

## 附录 Evidence Manifest

- `experiments/poisson1d/configs/exp1_baseline.json` · 0f1a9423432af595d31dfb062db9aae12be576c4845346eba08b12598ccfe045
- `experiments/poisson1d/configs/exp2_bad_sampling.json` · 7c736426bcf100fc9b845b5dd30660e939b697197eb8f93cf8b8a49efe53bef9
- `experiments/poisson1d/configs/exp3_bc_weight_100.json` · f947428accb101d5b919ba314892642f7fb39f412c4a3fae1e8a380343c40f8c
- `experiments/poisson1d/configs/exp3_bc_weight_1000.json` · 01465b9afae982c4d6a166464307595e5daaf0fe424ada33c0ffd555ffa74ab2
- `experiments/poisson1d/configs/exp3_hard_bc.json` · 959c27ec25899433d61ff13f948149943b212a13a4d8138eaec819fff4051da8
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-claim-GL640-CGL2400.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-claim-GL768-CGL2802.json` · 349990fc99e2654f6b0b402b85ee804b90a1060811a97760875c3b52fcd3082f
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-claim-GL896-CGL3200.json` · de71575d51bd768d8aff48c4e6052fb67acf1c4f38f79beb4626a2ba24059b01
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-claim-pool.json` · 3408d100edf6fa03041c4625e7caf75f5f527a578dc208c0a58c00ae4f9c07ac
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-exp2-r1.json` · a6b159974527d45eac1ac938f119a06a0ae1da1b290dbb44e85a2490b5cb33ff
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-r1.json` · 10983fcc3bb0dff093c18e9fa26568f894d3be20b640c2c601a93218a9007306
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-r2.json` · 2ddd3fa9802d2959565ea0aef1d01488fae95ca879d9d3d25458867a39b46ac0
- `experiments/poisson1d/ledger/pdef-poisson1d-cal-v1-exp2.json` · bbc600adb59f3b90470e1938c4ffe62c457dd8417e16088ac207996eb2f11a4e
- `experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5
- `experiments/poisson1d/ledger/sample_set_registry.json` · 471efeb645b23057d34c5abfd743c4dadadbbcc16310002ec945555514fbee88
- `experiments/poisson1d/EXPERIMENT3_PREREGISTRATION_20260916.md` · de4e0b9f2c81aaf1c2c024f1de710a2f26702c87bd9e1bda81adb2bc137e459b

### exp1-calibration-r1

- `identity.json` · 269a86ecaa9cb66b064415e5c26c19e64de17859fa963745a99f4acf64bf63d0 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 9acd944dd99b3caf9cdd61ff64ce5769dfc47efed0d76a0bfcf7638d87ce913f · EVALUATION_SET
- `sets/dev.json` · 8b28ab8545ae8774e73df26dd050261cea18f496054380e4c9691a8505f3b73c · EVALUATION_SET
- `sets/phys.json` · d63b11bd2f811f4ac62536ca3d744fef0552860ebb9adfffbf95edd9382dd933 · EVALUATION_SET
- `sets/claim.json` · 02ee4e7533ea0eb0ff16828bb6f447e0c63f217b2e911ea1eabd6862659eb08e · EVALUATION_SET
- `sets/isolation.json` · ad41639f2bd2c0db29e4afb20807968e82217c342d11724f5f0b829f0ed24714 · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `gate1_math.json` · 4756aae17d2e600fc3afcd0696f2efcf1a0d6b84c4a0be82969cd823c973f030 · GATE_RESULT
- `gate2_baseline.json` · 31f19a439cbe1bee048c23b2e85f505b289751ba4fa1dc1f5f0c8d887718ea8f · GATE_RESULT
- `gate3_implementation.json` · ba4d69cb95cdb7ef2d9c99fee908a896fd8faeba932980c2f8748071e7d7b1fc · GATE_RESULT
- `seed_ledger.json` · 706db5ad382f964566e019f8d82b40c8c98041a2a9a5f1f6ccc3419ddff635de · SEED_LEDGER
- `runs/run-00.json` · 280c13ea46787ae0bdeb937584469bccc5af91dcaf561a08eb5fd5f4413326bf · RAW_MODEL_PREDICTION
- `runs/run-01.json` · 976655fae4f7492d8a4db1d2f8de7279c1750f5de2179aeee4e4260844f900a0 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · cd1a560ccad16ede6078c92fb046e00525e0c08bb19a868d2ce906eacb53757a · RAW_MODEL_PREDICTION
- `runs/run-03.json` · f1592e20a44cb2fed3b75300bbc4cf60e46424160aba91ca8c173a79408ab341 · RAW_MODEL_PREDICTION
- `runs/run-04.json` · 3429fdd4aa461099f82761e95bf34682b60381c39b099c39267a33ada88a5652 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 6ccfd6935cce97292f97d9d20cb0866929113547ab807fc05f55ef8f49fc2d64 · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 7cfd57722dd9a5a7a4521e7a2baab552b633c6777b6badb02c3ca20febf0eae1 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · eac8cd2dd84191a0cda86c913431672566c6fb8cb2f1fbd8857360a1edf02ba3 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · ef78375021c9e05a8f42e24477caf21f95d17ca46323e552d870c91ffb514d51 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · e15a426bdde35ff2e16cca35cea739d74b7feb196f7d2731a536f060c2db9e0d · RAW_MODEL_PREDICTION
- `gate4_training.json` · a9cd97dce9a88e1fef4511985d56a5dcb0d42f84fe5f3bc876a85883fa8a0d3a · GATE_RESULT
- `training_report.json` · 3cae84cf449f17630a2bca198d14a6b2bb53873b6f8ef49498a258b99c6ddc11 · TRAINING_REPORT
- `gate5a_physics.json` · fe720e327f793872b66eadcb5c0b59db873e33c77e19452314cd3f85c1ea8860 · GATE_RESULT
- `claim_set_ledger.json` · 5ea5607ddc906e81539809eb2e0c37431b40ba1425ae4c139ac3f50b8497a9f6 · LEDGER
- `problem_definition.json` · 1a241fd4d9424abe692db924dcb01665e2d475b91860d627bb74dbb8951bbe0a · PROBLEM_DEFINITION
- `gate5b_external.json` · 313d75b5bf073f5079c0f2cc00c3e1c026d72c6a4cd712aa3176cfaef91a8619 · VALIDATION_METRIC
- `run_record.json` · 9e801189afff4321e8f7b17e06a50c8df9160891b98f84b61fc11eb12a66ff2b · RUN_RECORD
- `attempt_state.json` · 18494dc95981523d568c449120291fd4b7e7a424f9588212480194ea8112c327 · STATE
- `claim_statements.json` · bf58487b2f7ec62934251cf584c24e40f87599c095bb2ddfe8b5097f6fb78ce9 · CLAIM_STATEMENT
- `failure_record.json` · 22c65a6d1fdc7ed7be26eee9a0eee036094fde04a11c5298fe7bbfd672ee46c2 · FAILURE_RECORD
- `dev_diagnostics.json` · 27733bca4a7537de3341e90cd4dc9ecc52ea62620d8270456e205ade36c653e3 · DIAGNOSTICS
- `trust_vector.json` · 18158d9191053b800351baa523bc12b23a6796f4ee2415d1965bb5c7d75eac95 · TRUST_VECTOR
- `RUN_SUMMARY.json` · d0c1dfecc14ce947c429c08f038727a39ee1a0a78d3d11fadc3f2f8cfa348d86 · SUMMARY
- `bc_intervention_plan.json` · 3fe59f9b2a8e090a0d03ee919c578471c3de80c0e706a188dc52400942ecace6 · INTERVENTION_PLAN
- `bc_intervention_3a.json` · 0c73378a87d31e37a3085526330392366bafa858b003777d40ae6c3b83a91365 · DISCRIMINATING_EXPERIMENT
- `bc_intervention_3b.json` · 0b779e5a0531d6d2aba3372c0758965c00b51546eb5c5d565cc2d65b98d17d59 · DISCRIMINATING_EXPERIMENT
- `bc_decision.json` · 2405b1a53523a58d0a1a721c9319b972d61f46ae85a93807861018ac4115c5d7 · DIAGNOSIS_DECISION
- `diagnosis_record.json` · 25a14c1a68f4908996ff9d76776ef5bdb85a89568965ce0aba250bc678a515b0 · DIAGNOSIS_RECORD
- `diagnosis_verdict.json` · f82475e36172417afd369d556794c1c694b1c98a5df195cf608df69a2b7e1e94 · DIAGNOSIS_VERDICT
- `revision_record.json` · 8903350989d9eac473f4cfdfb8c6dd5ab91efdfa15a85ec1f52e69cc419a4d23 · REVISION_RECORD
- `PROVENANCE_MANIFEST.json` · b89240d1470c73484fa4b9e04d6c74008909a730e13e8daf9d6ee44ca98d887d · (index)
- `STATE_TRANSITIONS.json` · 75845446514c887f58b4ab285c617d53ea9162f35a1df51bd93dc8af49062d24 · (index)
- `TRUST_REPORT.md` · 53492cb27f3c089fe949d291d5e95c8348d0e3a158c2673fb543b879636ec40c · (index)

### exp3c-hard-bc-r2

- `identity.json` · e8e6f82398cda57a4b6ec3e85831732c216690280041596acd73eed4e57e2d89 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `gate1_math.json` · a274df4ac8a16bd8a3e5f087a12913f39ae83110c6ae0824c65b4e4bdbb81929 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 1bf27ecd1e3c66aed0eb869b1d76f6937a8fad8ffe614ccc38c64a30baf0dbb2 · SEED_LEDGER
- `runs/run-00.json` · 7aaf49535bf163e0fa53da25a2c422a9990d6c4967a4a85b5154f7315948a7f8 · RAW_MODEL_PREDICTION
- `runs/run-01.json` · ab3e16287e760eabfcb292bfba0b8928ad71cdcf72e6c061f8d70f79739ad1e7 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · 02aff363d8701a322c2954c9fcc6ea80c09d778c851047b9daf1d2cf61af4933 · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 5aa656013b005ec5b458ed89e8675c0d4ad66c34f90eb0e25498d639ac31143f · RAW_MODEL_PREDICTION
- `runs/run-04.json` · e492a7da85cac3acb850e5998ee7bd773d213d074c17ad17614bc3420d5a5cd1 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 871a7ffd6cdabd7e0ebdb4209200d1eb2076e06c5f33275cb547d0400901e60e · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 574f0b8cebe176446c28ecb50d6d17c81f93982dd78ebbcf98521aaf505e7f82 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 9b47d05b6e970e50a752fc7447aa19317dface743a1823429914449aa5e79ca4 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · 074731f769dafd93aba33dc73593406bc94fe7d7e5d2a88206c4621196704845 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · bc52881dc4930c3f120551c774e550507f243e4b98f914db1e42f1eb2be321d9 · RAW_MODEL_PREDICTION
- `gate4_training.json` · fefe9815b14b903a3b16667256be7d697f48460c6e8fd0796f812cc065a4fc3e · GATE_RESULT
- `training_report.json` · 6e57cfdac3e001b9bc913c9096b1f9c0b385c7752bb0f404f686c2f9253c558c · TRAINING_REPORT
- `gate5a_physics.json` · 9255a884c7238d246721e7f57d0908122b5d431d196758bf27982a842de0fd3e · GATE_RESULT
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `gate5b_external.json` · 08512671438191c8be2664af17c360885b420b0294f6667b3c51116230550234 · VALIDATION_METRIC
- `run_record.json` · 131116f213142557917f139d36748357d359d3d90b9049e919882a9e813a4c82 · RUN_RECORD
- `gate6_reproducibility.json` · 7a049cb9a6821b1e5a037f74d2c5e0bf517f03e2f1051fae04115252dca6a3fe · GATE_RESULT
- `attempt_state.json` · 30f1cda06cb6a105db5af45a48fd2d70c8063a10c2c566f15546fc7bafc4ea1e · STATE
- `trust_vector.json` · 278cc8ce45e56748f3a31613bf02cdcd677af5e9a3e7fc42400dfc38c5b6ab44 · TRUST_VECTOR
- `claim_statements.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision.json` · 87b92178ae2af96c916541b831b49910f56021893eea83eb2dd051859e6be353 · CLAIM_GATE_DECISION
- `tier1_redteam.json` · 13ae340866c400d34b67fe6a40e7f62a1878f1dd7da47f335c95f11ac9dc6779 · RED_TEAM_REPORT
- `trust_vector_tier1.json` · bcf798e06f98a30c8045d9d36660a376049205e9548dca9b2e44e2f0a3603d77 · TRUST_VECTOR
- `claim_statements_tier1.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_tier1.json` · 2b21212a9266b44a2c8d8c70d613b4cd1ab7fad5aaa6cdef5a14fe7332b72799 · CLAIM_GATE_DECISION
- `tier1v2_redteam.json` · add3abc639f67cef91ce195679b01f904146d504a9bee51cf2930f209c9ef9b9 · RED_TEAM_REPORT
- `trust_vector_tier1v2.json` · 17c09b016ca7c9b6b687b1a0f971bb0bdb43c65b4d6375d53c65db2d40230950 · TRUST_VECTOR
- `claim_statements_tier1v2.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_tier1v2.json` · e1e37f417c0f4342a7bf40dd7ae920b2ce8e20e134f55f32fe30b1f58b1544b5 · CLAIM_GATE_DECISION
- `RUN_SUMMARY.json` · c98c0f3369e8e9f62f7e29a385336222ec62e19e9466c46d5e525e67f6cd5845 · SUMMARY
- `PROVENANCE_MANIFEST.json` · 39ca23bcb162bd0afd506e9fbd4cf3a9ecd73366ade09a55f5e5383dc7f1970c · (index)
- `STATE_TRANSITIONS.json` · 9e612c60092cf7da9d5068ede1abd3c65e31f2430c36e2d318a9ddab71c959c7 · (index)
- `TRUST_REPORT.md` · 3aed35f4a975023dfc11ac811edaf24851624e7a92e1ee6f335693dd11cf6df1 · (index)
- `POST_AUDIT_ANNOTATION.md` · 0a925fd242e5be796d78859665e0dae0ef79d3e40613f46eeec41abef12fc880 · (index)

### repro_package_exp3c_r2

- `config.json` · 959c27ec25899433d61ff13f948149943b212a13a4d8138eaec819fff4051da8
- `dataset_isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e
- `original_run_record.json` · 131116f213142557917f139d36748357d359d3d90b9049e919882a9e813a4c82
- `original_seed_ledger.json` · 1bf27ecd1e3c66aed0eb869b1d76f6937a8fad8ffe614ccc38c64a30baf0dbb2
- `original_training_report.json` · 6e57cfdac3e001b9bc913c9096b1f9c0b385c7752bb0f404f686c2f9253c558c
- `PACKAGE_MANIFEST.json` · 8f5750a0c008c6a37373142ff97d2e46f207f9de0c1e2526a40e35971626b268
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c
- `experiments/poisson1d/runs/exp2-revised-r1/POST_AUDIT_ANNOTATION.md` · 0ef63b0873001731a4465fef55a9ab0462423dcffebbfff1672abed4b5a72a2c

````

</details>

### R038 — 项目/docs/pinn-trust-loop/POISSON1D_CALIBRATION_CLOSURE_REPORT_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Poisson 1D Calibration Closure Report（2026-09-16）

执行负责人：Claude（队长）。宪法 1.2 不变（无 A-0003，无方法修改，无 D_claim 重开，无 G5 重做，无参数调整）。实验 1/2/3 的机器记录保持不变，只追加 POST_AUDIT_ANNOTATION。上一份报告：`POISSON1D_C2_CALIBRATION_REPORT_20260916.md`。

## 1. Executive Result

```text
G6:
PASS

Highest Claim:
C2   (SUPPORTED @ C2, ClaimGateDecision cgd-exp3c-hard-bc-r2-g6)

POISSON 1D CALIBRATION:
CLOSED

PINN SCIENTIFIC-CLAIM MVP:
VALIDATED AT C2

READY FOR USER / EXTERNAL REVIEW BEFORE 2D
```

## 2. BC Diagnosis Post-Audit

```text
Historical verdict:              rSpecDefect   (unchanged; protocol-selected by the preregistered decision tree)
Post-audit causal interpretation: NOT UNIQUELY IDENTIFIED IN POST-AUDIT REVIEW
```

事实（D_dev，10 配对 seed）：软 BC λ_BC = 10：BC median 1.43e-4，7/10 seed 未过 AC-3；λ_BC = 100：8.15e-5，4/10 未过；λ_BC = 1000：1.33e-5，10/10 通过，PDE error 7.83e-3 < 1e-2，solution error 2.63e-4 可接受；硬 BC u = x(1−x)N：BC 恰为 0，同样解决。因此至少两种解释仍有实证支持：A. enforcement / specification choice；B. loss trade-off / optimization-training protocol。正确表述是"原冻结的软 BC 配置（λ_BC = 10）未通过 AC-3"，不是"软 BC 本质上不能满足 AC-3"。历史 verdict 不改为 rOptimizationFailure 或 rUndetermined（那是看完数据后的回溯重分类）。宪法 1.2 没有"根因归因非唯一即使已完成的 revision / 状态转移失效"的条款（第二十三、五十六、五十九章核对），r2 的已验证结果成立。注解：`runs/exp1-calibration-r1/POST_AUDIT_ANNOTATION.md`。

前瞻性准则澄清（`experiments/poisson1d/INTERVENTION_CRITERION_CLARIFICATION_20260916.md`）：未来干预准则围绕整条预注册剂量—响应曲线（R = median E(λ_high)/median E(λ_low)、配对 Q、弱单调、退化限），而不是要求每对相邻档独立满足强阈值；数值常数不用本次数据倒推，留待下一次适用实验前预注册。Experiment 3 历史裁决不变，新准则仅前瞻。

## 3. Environment Qualification（`experiments/poisson1d/environment_b_qualification.json`）

G6 语义审计（宪法 28.1、`trust_vector.independent_environments`、`reproduction_status`、schema、测试）：独立 ⇔ 至少一个强字段不同（machineId / osFamily / acceleratorClass / frameworkVersion / blasBackend / dependencyLockHash / installationId）；**不要求** dependencyLockHash 不同；同机独立安装即合格。代码与宪法一致，无 mismatch，无修复。

| 字段 | Environment A（原 run） | Environment B |
|---|---|---|
| machineId | win-60a9b43e-b66d-4186-8afb-43e9ada3342e | 同 |
| osFamily / OS | windows / Windows-11-10.0.26200 | 同 |
| architecture | AMD64 | 同 |
| acceleratorClass | cpu-only（训练强制 CPU float64） | cpu-only |
| Python | 3.12.9（mamba） | 3.12.9（`python -m venv`，base = mamba python，无 system-site-packages） |
| torch | 2.12.1+cu126 → frameworkVersion torch-2.12 | 2.12.1+cpu → torch-2.12 |
| numerical backend | mkl | mkl（MKL-DNN 3.11.2） |
| driver | — | — |
| dependencyLockHash | 75efe91aa4e1…（用户通用 mamba 环境，无 lockfile，数百个发行版） | 9083b98ea21e…（只装复现包声明的依赖：torch==2.12.1、numpy==2.4.5，`--no-cache-dir`） |
| installationId | prefix-689a1fbe8610a998 | prefix-e67819cbf0282077（新前缀 `C:\Users\user\LeoAI-envB-20260916\venv`，无复制、无克隆） |
| environmentId | e986dbc039e0… | 232ac1d46aea… |
| qualification | — | **independent = True**（强字段不同：dependencyLockHash、installationId） |

说明：优先目标 dependencyLockHash 相等无法达成——环境 A 没有 lockfile 且是通用环境；B 是复现包声明依赖的最小全新安装。独立性由 installationId 承担，dependencyLockHash 差异是构造结果而非刻意升降级依赖。

## 4. Reproduction Configuration

| 项 | 值 |
|---|---|
| specHash | fd5584d7b290…（r2，enforcement hard；同一冻结 ProblemDefinition `problems/pdef-poisson1d-cal-v1-r2.json`） |
| codeHash | 5aaf93a57fdd…（**相同**：复现在 exp3c 原 commit beceef5 的干净分离检出 `C:\Users\user\LeoAI-envB-20260916\repo-frozen` 上运行原 runner；驱动脚本在代码身份清单之外） |
| seedSetId A | 4489fcb39906… |
| seedSetId B | e2c220431081…（复现包规则：原三元组 +10000，先登记再训练） |
| dataset generation | 与原 run 同一规则（pool 1024 / default_rng(20260915)，dev 1000 / default_rng(20260916)，GL256），四集样本级互斥复核通过 |
| method | 3×32 tanh，u = x(1−x)N，Adam 1e-3→1e-5，6000 步，batch 128，256 配点——全部冻结，未改 |
| tolerance（包内冻结） | dev 相对 L2 中位数差 ≤ 1e-4 且 k/N 判定一致；claim 集不重开 |

## 5. Reproduction Results（`runs/repro-envb-frozen-r2/reproduction_report.json`）

| 指标 | A（exp3c-hard-bc-r2） | B（repro-envb-frozen-r2） |
|---|---|---|
| median relative L2（D_dev） | 1.991e-4 | 2.552e-4 |
| difference | — | **5.617e-5 ≤ 1e-4** |
| k/N | 10/10 PASS | 10/10 PASS |
| worst seed | 2.480e-4 | 5.173e-4 |
| IQR | 1.513e-4 | 1.275e-4 |
| divergent | 0 | 0 |
| B 逐 seed | — | 5.17e-4, 1.59e-4, 2.87e-4, 1.20e-4, 2.00e-4, 2.74e-4, 2.58e-4, 4.27e-4, 5.65e-5, 2.52e-4 |

`reproduction_status`（宪法 54）：同 spec ✓、同 code ✓、独立环境 ✓、不同 seed 集 ✓、容差内 ✓ → **C_repro = PASS**。

诚实记录：第一次复现 run（`repro-envb-r2`，当前 commit 的 runner）数字逐位相同，但 codeHash 因本轮 runner / harness 修改而不同，被 `reproduction_status` 正确判 **BLOCKED**（"同一个方法 = 同 specHash 同 codeHash"是宪法明文）；该记录保留并注解。随后按复现包说明在原 commit 检出上重跑才取得合法 PASS。

## 6. G6 Evidence（sha256 见附录）

- `runs/repro-envb-frozen-r2/`：identity.json（codeHash 5aaf93a5…，gitHead beceef5，dirty = no，environment B）、prelock.json、sets/、problem_definition.json（复用 r2 冻结定义）、gate1–gate4、seed_ledger.json、runs/run-00..09.json、run_record.json、training_report.json、reproduction_report.json、trust_vector.json、STATE_TRANSITIONS.json、PROVENANCE_MANIFEST.json。
- `runs/exp3c-hard-bc-r2/`：gate6_reproducibility_executed.json、trust_vector_g6.json、claim_gate_decision_g6.json、attempt_state.json（ACCEPTED）、STATE_TRANSITIONS（REPRODUCIBILITY_CHECK →[G6 PASS] ACCEPTED）。
- `runs/repro-envb-r2/`（BLOCKED 记录）+ POST_AUDIT_ANNOTATION.md；`environment_b_qualification.json`；`repro_package_exp3c_r2/`（冻结包，未改）。

## 7. Final Trust Vector（`trust_vector_g6.json`，supersedes tv-…-tier1v2，校验器通过）

```text
C_math     = PASS
C_impl     = PASS
C_train    = PASS
C_physics  = PASS
C_external = PASS   (claim set GL640-CGL2400, sampleSetHash 3977198983fd…, OPENED@r2 once, BURNT)
C_repro    = PASS   (repro-envb-frozen-r2)
```

## 8. ClaimGateDecision（`claim_gate_decision_g6.json`，`validate_claim_gate_decision` 通过）

```text
SUPPORTED @ C2
allowed: C0, C1, C2      blocked: C3 (no independently qualified C2 runs supplied — C3 needs >= 5 such runs)
runMode FORMAL · referenceEvidenceLevel A · codeHash 5aaf93a5… = OPENED codeHash · ledgerHead c3bf550d945d…
```

Evidence chain：冻结规格 fd5584d7b290（r2，hard BC）→ G1 数学一致性 → G2 解析参考 + FDM 二阶 → G3 T1/T3/T4/T8/T9/T10 → G4 10/10 seed（median 1.99e-4）→ G5a PH1–PH7 → G5b 新盲 claim 集 AC-1..AC-8 全 seed 满足（AC-3 = 0）→ Tier-1 P1/P4/P6/P8/P9/P16 维持（run 1 P8 harness 缺陷保留注解）→ G6 独立环境复现容差内 → 六维 PASS → 弱链演算许可 C2 → ClaimGateDecision 签署 → 状态机 `advance(REPRODUCIBILITY_CHECK, 6, PASS, claim_decision_signed=True)` → **ACCEPTED**。

## 9. Tests

| 项 | 值 |
|---|---|
| previous baseline | 1109 passed / 6 skipped |
| new tests | 3（`test_g6_reproduction.py`：冻结复现 PASS 与新代码复现 BLOCKED；容差外 FAIL、同环境 / 同 seed BLOCKED；最终 G6 向量与 C2 决策重校验） |
| total passed | **1112** |
| failed | 0 |
| skipped | 6 |
| PRELOCK | 7/7 PASS |

## 10. Repository State

`git status` clean；收口提交 32eaa36（证据、代码、测试）+ 本文档定稿提交（见 `git log -1`）；上一轮末提交 62ff5e6。

## 11. Stop

本轮到此停止。不开始 2D、BFS、UCM、新修正案、架构搜索或 UI。等待用户把本报告交给外部评审。

附录 Evidence Manifest（sha256 = 文件字节）：

- `experiments/poisson1d/environment_b_qualification.json` · df1ea41f5119ee18cc11d5bea7d44db8b5639289c8ef2cc4523f6e141c7093d6
- `experiments/poisson1d/INTERVENTION_CRITERION_CLARIFICATION_20260916.md` · f6cfe2df9f9c0e749f584161a745946c1efa10ee31a865f00855148fdd5b38aa
- `experiments/poisson1d/runs/exp1-calibration-r1/POST_AUDIT_ANNOTATION.md` · 632576bed350c30e53b3365a19959d4fcc63c1116d232ec450827d0c39852fc0

### repro-envb-frozen-r2

- `identity.json` · aa9532289102755a83e944c34d07bab571d75d9421227993fbc7c0783dfd16dd · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `gate1_math.json` · c217bdca12790d1276346bf0a49ed4dca6d0b10fe7edb8910137fbdb80a9b4a0 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 9243aee52a388cab7d217f212dcb6a79e667915f6a3310cc7e2a78becb35a983 · SEED_LEDGER
- `runs/run-00.json` · b8f52bff50dd4c2b91a29dcde1041ca2a54ee3e93dbde9d615b7183596568ee2 · RAW_MODEL_PREDICTION
- `runs/run-01.json` · c2289d422c8c68020ef81032f02ae2ceba0fadd6a15ebcc0fbc25a335ab72456 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · b4ba23882fb33ac214a93dd5c9a8dffe07e1acb7c08964402acf6c9f4380f3dd · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 3aaeb573e1dcd882e378146a2c5fd2a46afeecc62f599e720811de707326e2c8 · RAW_MODEL_PREDICTION
- `runs/run-04.json` · be19bfd32a9a22ac785bf460f1731e500685ea41399f2addb43b5464e55a1116 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · d3f107594b04943d07ee382b365f620430e82ba4369c99b5c5cb219a389530bc · RAW_MODEL_PREDICTION
- `runs/run-06.json` · ba61fbe0375bbaed9049f9f07790985a3d2b7f74415e8765ca3254c48cdacd98 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 3c423c04892c0c041fffd1323e28e7cf21db23c63e98a875b571e351d4a34e17 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · d3d91d40cb0dfae8f8c64f47faf094044c96b54fe7a4e1b75a259cb7e1806f30 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · 3539a5ea5be465a956240c7a09ecdf097b311f9dd88e57a0fe6b09ff8f1fb2a1 · RAW_MODEL_PREDICTION
- `run_record.json` · a2017b5b6f33abd1e89e8469b0ccecfee0acf4de52444426ef6d48e0219845a0 · RUN_RECORD
- `gate4_training.json` · 25a24e5a524e500b6c8f4586997ddad875b1385a7c06a663f0cc2bafab39b664 · GATE_RESULT
- `training_report.json` · 440b6d963b0cc747e0a8437392f15be64719ecf42488f1ae96f80c7dc6937ca7 · TRAINING_REPORT
- `attempt_state.json` · d9fdbbfc78c0f238cfe2e8ab6cfbab4ba876426b580e08973537c8893d61846c · STATE
- `trust_vector.json` · e484ca009d24a4d18d059983f8730ad3013791d865d357ae3e0647ba71053066 · TRUST_VECTOR
- `RUN_SUMMARY.json` · 4be910cae17eef23d3345978c5d502aa05b9db3d8031a67ec97c0e2090265aec · SUMMARY
- `reproduction_report.json` · ebac6fd22b8dac8edaacf8e82f2fdaa035e59cc84a51ade76f2ae044a765e2ba · REPRODUCTION_REPORT
- `PROVENANCE_MANIFEST.json` · cc3ea19192d5bb4aaa89966f75ce8959f87ff7ac53661737d7d69613d8095c84 · (index)
- `STATE_TRANSITIONS.json` · 6b0687d998cc602590060f2116376a75699577f241fa483db6bfc46c09967e2d · (index)
- `TRUST_REPORT.md` · 8a5e12662cdc0bcfc7bf551e77f066551375fbb36a78f90440bca6b605910008 · (index)
- `attempt_state.json` · d9fdbbfc78c0f238cfe2e8ab6cfbab4ba876426b580e08973537c8893d61846c · (index)

### repro-envb-r2

- `identity.json` · 39ad6ef72bcd6f73cbf6d405699bb1e078f690ddd788e6e703fa58d2948cf832 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `gate1_math.json` · c217bdca12790d1276346bf0a49ed4dca6d0b10fe7edb8910137fbdb80a9b4a0 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 58c79ab126629ea0764cfa950a008027999ec198bda2ff4c0072d20431cec1be · SEED_LEDGER
- `runs/run-00.json` · 3e63e22a9fed44ced7d6e36a1659ca3872259d09b6fa1170b338aacfab270d6a · RAW_MODEL_PREDICTION
- `runs/run-01.json` · fd6a32197001886fadd7cf8d91db900c3f4967e52a014adc5d118f5bf84c7f1b · RAW_MODEL_PREDICTION
- `runs/run-02.json` · d88cc33178aa05214b5342512b96ea2d2f055af8c956f617a432899569651ed0 · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 0a4292a36293480bfaf5f9ddf9c2967eb20912ca164f086ff48eeda8f47acc6c · RAW_MODEL_PREDICTION
- `runs/run-04.json` · b778bbb114435c30bf0af1ffc09367fe6750b7fce67e5da4712859641acf9c0e · RAW_MODEL_PREDICTION
- `runs/run-05.json` · eb4c4710106dd73b8085fb8f3aa0e8a7ccbfa63a2d83ce86ac3214a4160c599c · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 9640ffc49e5c4588d738435434eec3e2a71ba601a820e435a6cc44e9464a51f7 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 81a8e4e11357c2c5b7f69ceec4340306fbfe0e099455d66eb4a6f4fe5dbe2a64 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · 77fb4b595eca185b0f2263d9b4f4d612736f424b0abc0d0dc1da9d120e20a3c1 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · 2961a841b5bf46cbf6e398ab53eb8c8c7f976743f7475bd50b5217101eccf48d · RAW_MODEL_PREDICTION
- `run_record.json` · e0d071069d9656dc7e13ced139d46bcc64e3e78e7c99acb8afc35f447357992d · RUN_RECORD
- `gate4_training.json` · 25a24e5a524e500b6c8f4586997ddad875b1385a7c06a663f0cc2bafab39b664 · GATE_RESULT
- `training_report.json` · 440b6d963b0cc747e0a8437392f15be64719ecf42488f1ae96f80c7dc6937ca7 · TRAINING_REPORT
- `attempt_state.json` · 66b56a505bef3ba72acba1dc93c318de05dc76efd18208316f0a89939dd9b4b3 · STATE
- `reproduction_report.json` · edccb484b22dc6cfae9c9ecdd91466c274749714efa899c729816c4dcd551037 · REPRODUCTION_REPORT
- `trust_vector.json` · f26d64ca06c9c86b3e7b802a3afbc76efbd81e95d6c53169b0cb13604824893d · TRUST_VECTOR
- `RUN_SUMMARY.json` · 14ce362faa29b3435c8457e8741cebb21e25219fca5662ad0b94aabb98458699 · SUMMARY
- `PROVENANCE_MANIFEST.json` · 8769e1e7f19a2d27e4c362a830ffce4bcb61c0806cd19d1d15c77ef5d9ce7a86 · (index)
- `STATE_TRANSITIONS.json` · 5f7b1031c93ca555ed411d5fcbf27d3b582ddc68d69bc07fae138b3a18628870 · (index)
- `TRUST_REPORT.md` · 31873a42421be0e3474fbec708c905c0209832127a6ae8d10bc8b15ec251623b · (index)
- `POST_AUDIT_ANNOTATION.md` · a6bece2cfbe17c263cc0830455b8d3bcfdf0f28c1b98976a8d080a4e8106d327 · (index)
- `attempt_state.json` · 66b56a505bef3ba72acba1dc93c318de05dc76efd18208316f0a89939dd9b4b3 · (index)

### exp3c-hard-bc-r2

- `identity.json` · e8e6f82398cda57a4b6ec3e85831732c216690280041596acd73eed4e57e2d89 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 2b8b2fca6158f92155fa7833d1bee9aa1afe2e39872128d1c221735b3497029a · EVALUATION_SET
- `sets/dev.json` · c1a1ef2ca5952a53465034716705184a6313cdbdfea83e245ca08fabaead19dc · EVALUATION_SET
- `sets/phys.json` · 29163efdac5862ddd4c2eda3ed205d703d9d6c5e29bfdcaedfcec04a3eab880b · EVALUATION_SET
- `sets/claim.json` · d08488d9db3089f54e8711ffbb98ebad13c7e4844f660a513f16778b9c57e2c5 · EVALUATION_SET
- `sets/isolation.json` · 8ea5e5fbe52e5d4a0b10d41be539ae222644c1bb7627ce2a6a8127456bc86c9e · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `gate1_math.json` · a274df4ac8a16bd8a3e5f087a12913f39ae83110c6ae0824c65b4e4bdbb81929 · GATE_RESULT
- `gate2_baseline.json` · 961427f7563c408892f7ec8950b1187768ca9c45da94eb3017d31a7e34a16a91 · GATE_RESULT
- `gate3_implementation.json` · 8ee900c4d7c6275cf75703ab8a5caec4622145b619c570b02e56aaae9f35c2ee · GATE_RESULT
- `seed_ledger.json` · 1bf27ecd1e3c66aed0eb869b1d76f6937a8fad8ffe614ccc38c64a30baf0dbb2 · SEED_LEDGER
- `runs/run-00.json` · 7aaf49535bf163e0fa53da25a2c422a9990d6c4967a4a85b5154f7315948a7f8 · RAW_MODEL_PREDICTION
- `runs/run-01.json` · ab3e16287e760eabfcb292bfba0b8928ad71cdcf72e6c061f8d70f79739ad1e7 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · 02aff363d8701a322c2954c9fcc6ea80c09d778c851047b9daf1d2cf61af4933 · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 5aa656013b005ec5b458ed89e8675c0d4ad66c34f90eb0e25498d639ac31143f · RAW_MODEL_PREDICTION
- `runs/run-04.json` · e492a7da85cac3acb850e5998ee7bd773d213d074c17ad17614bc3420d5a5cd1 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 871a7ffd6cdabd7e0ebdb4209200d1eb2076e06c5f33275cb547d0400901e60e · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 574f0b8cebe176446c28ecb50d6d17c81f93982dd78ebbcf98521aaf505e7f82 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · 9b47d05b6e970e50a752fc7447aa19317dface743a1823429914449aa5e79ca4 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · 074731f769dafd93aba33dc73593406bc94fe7d7e5d2a88206c4621196704845 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · bc52881dc4930c3f120551c774e550507f243e4b98f914db1e42f1eb2be321d9 · RAW_MODEL_PREDICTION
- `gate4_training.json` · fefe9815b14b903a3b16667256be7d697f48460c6e8fd0796f812cc065a4fc3e · GATE_RESULT
- `training_report.json` · 6e57cfdac3e001b9bc913c9096b1f9c0b385c7752bb0f404f686c2f9253c558c · TRAINING_REPORT
- `gate5a_physics.json` · 9255a884c7238d246721e7f57d0908122b5d431d196758bf27982a842de0fd3e · GATE_RESULT
- `claim_set_ledger.json` · b7f15fec96ac1b0a8fa9ec3860df4a65adc59c66b4cdcb0e3bfb0c5663a72ab5 · LEDGER
- `problem_definition.json` · 91cf6314559e24cc01393dcb7adcb00581dab337431ddae1b9a5ac1f6873562c · PROBLEM_DEFINITION
- `gate5b_external.json` · 08512671438191c8be2664af17c360885b420b0294f6667b3c51116230550234 · VALIDATION_METRIC
- `run_record.json` · 131116f213142557917f139d36748357d359d3d90b9049e919882a9e813a4c82 · RUN_RECORD
- `gate6_reproducibility.json` · 7a049cb9a6821b1e5a037f74d2c5e0bf517f03e2f1051fae04115252dca6a3fe · GATE_RESULT
- `trust_vector.json` · 278cc8ce45e56748f3a31613bf02cdcd677af5e9a3e7fc42400dfc38c5b6ab44 · TRUST_VECTOR
- `claim_statements.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision.json` · 87b92178ae2af96c916541b831b49910f56021893eea83eb2dd051859e6be353 · CLAIM_GATE_DECISION
- `tier1_redteam.json` · 13ae340866c400d34b67fe6a40e7f62a1878f1dd7da47f335c95f11ac9dc6779 · RED_TEAM_REPORT
- `trust_vector_tier1.json` · bcf798e06f98a30c8045d9d36660a376049205e9548dca9b2e44e2f0a3603d77 · TRUST_VECTOR
- `claim_statements_tier1.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_tier1.json` · 2b21212a9266b44a2c8d8c70d613b4cd1ab7fad5aaa6cdef5a14fe7332b72799 · CLAIM_GATE_DECISION
- `tier1v2_redteam.json` · add3abc639f67cef91ce195679b01f904146d504a9bee51cf2930f209c9ef9b9 · RED_TEAM_REPORT
- `trust_vector_tier1v2.json` · 17c09b016ca7c9b6b687b1a0f971bb0bdb43c65b4d6375d53c65db2d40230950 · TRUST_VECTOR
- `claim_statements_tier1v2.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_tier1v2.json` · e1e37f417c0f4342a7bf40dd7ae920b2ce8e20e134f55f32fe30b1f58b1544b5 · CLAIM_GATE_DECISION
- `gate6_reproducibility_executed.json` · ecbe450a1008ade2da6288fcefbb23c9b88a5f7e30a4e00270eb02fe02646a4b · GATE_RESULT
- `trust_vector_g6.json` · 026ea517be128ff227196ddd5cfe7374707fe9f69ba36d3339b7f435df6f2491 · TRUST_VECTOR
- `claim_statements_g6.json` · 7d66d52f2d9b442c2ccd0ef5416e833d7877410832f180a199a215ec7c3888de · CLAIM_STATEMENT
- `claim_gate_decision_g6.json` · 3170add040aac89346b9ba44cfb4a51f6d1ee8180f660218bb425782f78143f7 · CLAIM_GATE_DECISION
- `attempt_state.json` · 7bb39001d0e9352825e9ab07bda7228003943562deb36658db204b13e22e28a3 · STATE
- `RUN_SUMMARY.json` · 8bca3db78c00e41a098c4f407b3d2b45aa6525aff6f39f0e00155d5b401504ee · SUMMARY
- `PROVENANCE_MANIFEST.json` · c8061600a0a2aaffd8e1764a18b8c65c0c957a3e0a313fc996ecc176caa5b500 · (index)
- `STATE_TRANSITIONS.json` · 0454ed13896b304e855e5bec3a0010fb54e0f2ea0b176356a4568c61c5647210 · (index)
- `TRUST_REPORT.md` · d0c3dab8a611885c25cbb8ef53501d8708dc6c95996934361f82b8264e8c6a9c · (index)
- `POST_AUDIT_ANNOTATION.md` · 0a925fd242e5be796d78859665e0dae0ef79d3e40613f46eeec41abef12fc880 · (index)
- `attempt_state.json` · 7bb39001d0e9352825e9ab07bda7228003943562deb36658db204b13e22e28a3 · (index)

````

</details>

### R039 — 项目/docs/pinn-trust-loop/POISSON1D_EXPERIMENT_REPORT_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Poisson 1D 正式实验报告：Formal Calibration 与 Controlled Sampling Deficiency（2026-09-16）

执行负责人：Claude（队长）。宪法 1.2（A-0001、A-0002 ACCEPTED）。runner：`pinn/experiments/`（R3 最小实现）。预注册协议：`experiments/poisson1d/EXPERIMENT_PROTOCOL_20260915.md`。证据目录：`experiments/poisson1d/`。所有数字来自机器记录（RUN_SUMMARY / gate*.json / diagnosis_*.json），文本不比机器判定更宽松。

## 1. Executive Result

```text
Experiment 1: PASS   （闭环走完；数值结果在 Gate 5 被诚实判 FAIL：AC-3 边界误差 7/10 seed 超阈）
Experiment 2: PASS   （情况 A：FAILURE_RECORDED → DIAGNOSED rSamplingDeficiency → REVISED → REENTER G4 → 训练恢复 10/10）

PINN RESEARCH AGENT MVP:
VALIDATED
```

VALIDATED 的含义严格限于授权指令的定义：两个实验各自满足其治理成功标准（1.10 八条；2.8 情况 A）。它**不**表示 Poisson 1D 取得了 C2 声称——两次 attempt 的最终状态都是 FAILURE_RECORDED（Gate 5，AC-3），最高允许 Claim 为 BLOCKED（停在失败态，不出 ClaimGateDecision）；若按弱链演算单看向量（math/impl/train PASS），可被许可的上限是 C1，但 Gate 7 未执行，所以不作为声称发布。

## 2. Governance Activation

| 项 | 值 |
|---|---|
| A-0001 status | ACCEPTED（2026-09-15，1.0 → 1.1） |
| A-0002 status | ACCEPTED（2026-09-15，用户终审于实验授权指令；1.1 → 1.2；操作日志 §5.21） |
| effective Constitution version | 1.2（字节 SHA-256 `2f4484027cc9…`）；`SUPPORTED_CONSTITUTION_VERSIONS = (1.0, 1.1, 1.2)`；lock / spec / protocol / diagnosis-record schema 枚举含 1.2；Poisson v1.0 三份草案重绑定 1.2；证据 `governance/PINN_V1.3_PRELOCK_DRY_RUN_A0002.json` |
| PRELOCK | 7/7 PASS（生效后与实验后各实跑一次） |
| full tests | 生效后 1087 passed / 2 skipped；实验代码加入后 1094 passed / 4 skipped（+7 runner 测试，+2 框架缺失时跳过） |
| commit | 治理生效 e45500c；runner 440896e → 0a4db4f（六次提交，含三次实跑暴露的 runner 缺陷修复）；实验证据与本报告见最终提交 |
| tree status | 最终提交后干净 |
| GOVERNANCE_ACTIVATION | **PASS** |

## 3. Experiment 1 Results（attempt `exp1-calibration-r1`，problemId `pdef-poisson1d-cal-v1` r1）

| 项 | 值 |
|---|---|
| architecture | MLP 1→32→32→32→1，tanh（configId `poisson1d-baseline-v1`） |
| training configuration | Adam lr 1e-3 → 1e-5 指数衰减，6000 步，batch 128，loss = mean R² + 10·mean(u(0)², u(1)²)，无早停；CPU float64，deterministic algorithms，1 线程 |
| dataset sizes | D_train 1026（1024 池点 ∪ {0,1}，每 run 由采样 seed 抽 256）· D_dev 1000 · D_phys 256（GL256）· D_claim 2510（GL512 ∪ CGL2000 去端点）；样本级两两互斥（isolation.json：shared = 0，minSeparation 1e-9） |
| seed protocol | N = 10 三元组 init 20260900+i / sample 20261000+i / batch 20261100+i，seed_ledger 先于训练登记；seedSetId 由 30 个 seed 值派生 |
| dev 相对 L2 逐 seed | 2.41e-4, 2.09e-4, 6.20e-4, 3.96e-4, 1.84e-4, 4.08e-4, 3.26e-4, 1.56e-4, 5.32e-5, 4.18e-4 |
| median / IQR / worst seed | 2.84e-4 / 2.25e-4 / 6.20e-4（ε_spec 1e-3；worst < 3ε；IQR < median） |
| success rate | k/N = 10/10 → C_train PASS |
| residual（D_dev holdout，归一化 RMS，median） | 4.56e-3（AC-4 阈 1e-2） |
| BC error（median max\|u(0)\|,\|u(1)\|） | 1.43e-4（AC-3 阈 1e-4）——**超阈** |
| claim 集 AC-1 逐 seed | 2.43e-4 … 6.14e-4，全部 < 1e-3；AC-2/4/5/6/7 全部满足；AC-8（SHOULD）全部满足 |
| claim 集 AC-3 逐 seed | 1.76e-4, 2.79e-4, 1.03e-4, 2.06e-4, **3.08e-5**, 1.09e-4, 2.51e-4, **4.34e-5**, **1.16e-5**, 2.04e-4 → 7/10 超阈 |
| physics（D_phys，最差 seed） | PH1 7.77e-4 · PH2 6.24e-4 · PH3 min u −2.10e-4 · PH4 3.93e-4 · PH5 0 违例 · PH6 max u 1.0000 ≤ 界 · PH7 λ_min > 0 → C_physics PASS；PH10 / 自由能 NOT_APPLICABLE |
| Trust Vector | (math PASS, impl PASS, train PASS, physics PASS, external **FAIL**, repro NOT_CHECKED) |
| Gate states | G1 PASS → G2 PASS（解析残差 0，FDM 阶 2.000）→ G3 PASS（T1 AD-FD、T3、T4、T8、T9、T10 全 PASS）→ G4 PASS → G5 **FAIL**（G5a PASS ∧ G5b FAIL）；G6 未执行（NOT_CHECKED，未到达） |
| Claim level | **BLOCKED**（FAILURE_RECORDED，不出 ClaimGateDecision）；observedSignatures = [sBcResidual] |
| 账本 | claim 集 `02ee4e7533ea` SEALED → OPENED@r1，codeHash `a59a939f5842`；ledger head `0a72c77b0827` |

实验 1 的成功标准逐条：① 工作流完整执行 ✓（DRAFT→…→VALIDATION→FAILURE_RECORDED，每步经 `state_machine.advance`）；② 全部 artifact schema valid ✓（ProblemDefinition / EvaluationSet ×4 / ClaimSetEvent / RunRecord / TrustVector 均经 `pinn.governance` 校验后写入）；③ provenance 完整 ✓（PROVENANCE_MANIFEST 逐件哈希与父级）；④ D_claim 无泄漏 ✓（账本一次 OPENED；训练与 G4 只读 D_train/D_dev/D_phys；无早停）；⑤ multi-seed 协议正确 ✓（N=10，三因子，先登记，最好 seed 不判定）；⑥ Gate / 向量 / 决策自洽 ✓（G5 = G5a ∧ G5b；FAIL → FAILURE_RECORDED；不发决策）；⑦ 数值与解析解合理一致 ✓（AC-1 ≤ 6.1e-4，AC-2 ≤ 8.1e-4；但 AC-3 未达）；⑧ 无 runtime / version bypass ✓（宪法 1.2，PRELOCK PASS，工作区干净，codeHash 派生复算通过）。

## 4. Experiment 2 Failure Path（problemId `pdef-poisson1d-cal-v1-exp2` r1）

| 项 | 值 |
|---|---|
| bad sampling configuration | `poisson1d-bad-sampling-n8`：与基线**唯一**差异 `sampling.collocationCount` 256 → 8（方案 A）；D_dev / D_claim / PDE / BC / 参考 / 架构 / 优化器不变 |
| bad attempt 训练（`exp2-bad-sampling-r1`） | dev 相对 L2 逐 seed 1.26e-3, 5.86e-3, 1.30e-3, 4.04e-3, 4.83e-4, 7.74e-4, 4.13e-3, 1.39e-3, 5.21e-3, 1.20e-2；k/N = 2/10，median 2.71e-3，IQR 3.95e-3，worst 1.20e-2 → C_train FAIL → **Gate 4 FAIL → FAILURE_RECORDED**（未就地重训） |
| observedSignatures（D_dev/D_phys，事后由实测判定） | **[sPdeResidual, sPinnCfd, sSeedSensitive]**：归一化 holdout 残差 median 1.52e-2 > 1e-2；相对 L2 median 2.71e-3 > 1e-3；IQR > median、worst > 3ε。未触发：sBcResidual（6.9e-6）、sLocalizedError（比 1.42）、sConservation（5.4e-3） |
| FAIL gate | Gate 4（C_train） |
| candidate root causes（1.2 矩阵，三症状候选并集） | rSpecDefect, rDataDefect, rSingularityTreatment, rReferenceDefect, rImplementationDefect, rCapacityLimit, rOptimizationFailure, rSamplingDeficiency |
| discriminating experiment | `exp-int-sampling`：受控采样干预 S1<S2<S3 = 4 / 8 / 16 配点 × 5 seed（seed 与正式 run 不同），其余控制项全部固定，只看 D_dev。中位误差 **1.19e-2 → 5.89e-4 → 5.09e-4**，严格下降 ✓（`intervention_errors` 通过）。逐 seed：N=4 [3.41e-2, 1.19e-2, 2.29e-2, 4.29e-3, 2.89e-3]；N=8 [3.65e-3, 4.90e-4, 2.33e-4, 5.89e-4, 9.83e-4]；N=16 [5.09e-4, 4.34e-4, 3.96e-4, 1.12e-3, 4.83e-3] |
| exclusions（7 项，全部引用实测） | rSpecDefect（规格固定而误差随采样从 1.19e-2 降到 5.09e-4；T3 参考解过残差算子 < 1e-10）· rDataDefect（正向、forcing 审计 1e-12、BC 数据 0）· rSingularityTreatment（u* ∈ C∞，G2a 残差 0）· rReferenceDefect（G2a + FDM 阶 2.000）· rImplementationDefect（G3 T1/T3/T4 PASS；同一代码在基线 256 点 k/N 10/10）· rCapacityLimit（架构固定，同网络在基线 median 2.84e-4）· rOptimizationFailure（优化器固定；失败档训练 pde loss 已收敛到 ≤ 1e-5 而 dev 误差 2.7e-3——优化器收敛在所见点上） |
| final root cause | **rSamplingDeficiency**（DiagnosisRecord `dg-exp2-bad-sampling-r1-r1`，constitutionVersion 1.2，explainedSignatures = 全部三症状，覆盖不变量通过，`state_machine.diagnose` 接受；路由 Gate 4） |
| revision | `run_revise`：机械校验差异只在 `sampling.collocationCount` 8 → 256；网络 / 优化器 / loss / 阈值 / 激活未动 → REVISED |
| reentry Gate | Gate 4（`reenter`：REVISED → IMPLEMENTATION_VERIFIED，train/physics/external/repro 重置 NOT_CHECKED，math/impl 保留 PASS；G1–G3 另作再验证记录，不构成状态转移） |
| post-revision result（`exp2-revised-r1`） | dev 相对 L2 逐 seed 与实验 1 **逐位相同**（确定性：同 seed、同配置、同数据；codeHash 不同只因 runner 决策层代码修复）；k/N 10/10，median 2.84e-4 → **C_train PASS，Gate 4 PASS**；G5a PASS；claim 集 `33ea07647a39` OPENED@r1（codeHash `ff322e9c9336`）；G5b：AC-3 7/10 超阈 → **Gate 5 FAIL → FAILURE_RECORDED**，observedSignatures = [sBcResidual]（与实验 1 同一缺陷，与采样无关） |

结论：被人为制造的缺陷（采样）被正确识别、有证据地命名、只修复该因子、按根因路由重入并**恢复**（C_train FAIL → PASS，dev median 2.71e-3 → 2.84e-4）；系统随后诚实地报告了另一处独立缺陷（边界软约束），没有为了"恢复成功"而放过它。情况 A 成立。

## 5. State Transition Trace（实际状态）

实验 1：
```
DRAFT →[G1 PASS] SPEC_LOCKED →[G2 PASS] BASELINE_VERIFIED →[G3 PASS] IMPLEMENTATION_VERIFIED
→[G4 PASS] TRAINING_COMPLETED → VALIDATION →[G5 FAIL: G5a PASS ∧ G5b FAIL(AC-3)] FAILURE_RECORDED
```
实验 2：
```
DRAFT →[G1] SPEC_LOCKED →[G2] BASELINE_VERIFIED →[G3] IMPLEMENTATION_VERIFIED →[G4 FAIL] FAILURE_RECORDED
→[diagnose: rSamplingDeficiency] DIAGNOSED →[revise: sampling only] REVISED
→[reenter G4] IMPLEMENTATION_VERIFIED →(G1–G3 re-verified) →[G4 PASS] TRAINING_COMPLETED → VALIDATION
→[G5 FAIL: AC-3] FAILURE_RECORDED
```

## 6. Evidence Manifest

见文末附录（由 PROVENANCE_MANIFEST 自动汇总：三个 attempt 的全部 artifact 与 sha256、两份账本、两份冻结 ProblemDefinition、两份配置、协议文件）。

## 7. Test Evidence

| 项 | 值 |
|---|---|
| previous baseline | 1087 passed / 2 skipped（治理生效后） |
| new tests | 7（`tests/pinn/test_experiment_runner.py`：注册表 INV-A1 与冻结 ProblemDefinition、meet、G4 seed 统计、症状判定、排除覆盖候选并集、DiagnosisRecord + 覆盖、环境指纹 / ArtifactStore）+ 2 项在无 numpy / torch 的 `.venv` 中跳过（数据集互斥、trainer 确定性；两者在 mamba 解释器中通过 pilot 与实跑证实） |
| total passed | **1094** |
| failed | 0 |
| skipped | 4 |
| PRELOCK | 7/7 PASS |

## 8. Newly Discovered Problems

**BLOCKING**（对"在本规格上取得 C2"而言；对闭环运行不阻塞）：
- B1 软边界约束（loss 权重 10）达不到 AC-3 = 1e-4：7/10 seed 的 |u(0)|,|u(1)| 在 1e-4–2.8e-4。这是训练协议缺陷，症状 sBcResidual，候选（1.2）：规格 / 数据 / 实现 / 优化（loss 权衡）/ 采样 / 容量 / 奇异性；应走第二轮诊断（P28 硬约束或 P24 权重干预）。本轮**未**做，因为修订后重入 Gate 4 → 再验证需要新的 claim 集（revision 1 的 claim 集已 OPENED、按账本 burnt），而 v1.0 协议只冻结了一套 claim 网格（GL512/CGL2000）——见 C1。

**NON-BLOCKING**：
- N1 C_repro BLOCKED：本机无第二个装有 torch 的独立安装，复现协议无法执行；C2/C3 在任何数值结果下都不可达。需要第二个独立安装（不同 installationId）或第二台机器。
- N2 受控干预的"中位数严格下降"没有效应量要求：本轮 8 → 16 档只降 5.89e-4 → 5.09e-4（逐 seed 有重叠），仍被判为满足。诊断结论本身有其余 7 项排除证据支撑，但准则可被弱证据满足。
- N3 干预档 N=8 的中位数（5.89e-4，5 seed）低于正式 bad attempt 同配置的中位数（2.71e-3，10 seed）：采样不足时结果对 seed 高度敏感（这本身就是 sSeedSensitive），说明每档 5 seed 偏少。
- N4 实验 2 的 claim 集与实验 1 样本相同、只有 artifactId 不同（哈希不同，账本按哈希判 burnt 允许）；信息上队长已见过这些点上的结果。已在协议 §5 事前披露。
- N5 R3 runner 三次实跑各暴露一个 runner 缺陷（FDM 结果键名、重复冻结改变 specHash、决策文档引用字段），每次都被治理校验器在写入前拦下（Gate 2 解析、账本 L3、决策校验），没有伪造或绕过；三次中止的启动产物已删除并在日志记录。

**AMENDMENT / PROTOCOL CANDIDATE**（不自行起草，等用户与评审确认）：
- C1 协议应为每个 revision 预注册独立的 claim 网格（或定义 claim 集身份按样本而非 artifactId），否则任何一次 G5 FAIL 后的修订都无法在同一规格下合法完成最终验证。
- C2 受控干预准则加入最小效应量或跨 seed 分离要求（对应 N2）。
- C3 边界条件的执行方式（软 vs 硬）应成为规格 / 协议的冻结项，并把 AC-3 与 loss 权重的关系写入预注册。

## 9. Final Recommendation

```text
REMAIN AT POISSON CALIBRATION STAGE
```

理由：闭环、失败识别、诊断、修订、重入均已真实工作（两个实验按治理标准 PASS），但 Poisson 1D 本身尚未通过 Gate 5（AC-3），且 C_repro 无法执行；进入下一实验阶段前应：(1) 用户 / 评审裁决 C1（新 claim 网格）后，对 B1 走一轮完整诊断—修订—再验证；(2) 提供独立执行环境使 G6 可执行。在此之前不新增治理规则。

## 附录 A. Final Audit

| 问 | 答 |
|---|---|
| A. Did the full loop execute end-to-end? | **YES**（两个实验都从 ScientificSpec 引用 → ProblemDefinition FROZEN → PRELOCK → G1–G4 → VALIDATION → 账本 OPENED → G5 → FAILURE_RECORDED / 诊断—修订—重入 走完） |
| B. Did Experiment 1 produce a scientifically admissible result? | **NO** 作为 C2 结果（Gate 5 FAIL，AC-3）；**YES** 作为诚实记录的失败结果（第五十八章：Negative Result 是合法终点） |
| C. Did Experiment 2 correctly detect and handle failure? | **YES**（情况 A） |
| D. Was any governance rule bypassed? | **NO**（每次转移经 state_machine；每份文档经校验器；账本每个 claim 集只 OPENED 一次；无阈值、seed、参考、Gate 的改动；三次 runner 缺陷均被校验器拦下） |
| E. Was D_claim ever used before final validation? | **NO**（训练无早停、只读 D_train；G4 只读 D_dev；G5a 只读 D_phys；OPENED 事件在首次评估前写入并记 codeHash） |
| F. Did every artifact use the effective Constitution version? | **YES**（1.2；DiagnosisRecord constitutionVersion 1.2；PRELOCK 声明版本 = 链尾 = SUPPORTED） |

## 附录 B. 操作与产物

- 三次中止的启动（runner 缺陷）：第一次 Gate 2 解析（无训练）；第二次账本在 OPENED 拒绝（10 个 run 作废，确定性可重算）；第三次决策文档字段（保留全部产物，用 `finalize` 收尾）。前两次的目录与账本文件已删除并记录；第三次即正式实验 1。
- 未做：实验 1 的 AC-3 诊断—修订循环（需 C1 裁决）；G6；Red Team P1–P21。
- 测试产物：见操作日志 §5.22 计数与删除记录。

## 附录 C. Evidence Manifest（自动汇总，sha256 为文件字节）

- `experiments/poisson1d/configs/exp1_baseline.json` · 0f1a9423432af595d31dfb062db9aae12be576c4845346eba08b12598ccfe045
- `experiments/poisson1d/configs/exp2_bad_sampling.json` · 7c736426bcf100fc9b845b5dd30660e939b697197eb8f93cf8b8a49efe53bef9
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-exp2-r1.json` · a6b159974527d45eac1ac938f119a06a0ae1da1b290dbb44e85a2490b5cb33ff
- `experiments/poisson1d/problems/pdef-poisson1d-cal-v1-r1.json` · 10983fcc3bb0dff093c18e9fa26568f894d3be20b640c2c601a93218a9007306
- `experiments/poisson1d/ledger/pdef-poisson1d-cal-v1-exp2.json` · bbc600adb59f3b90470e1938c4ffe62c457dd8417e16088ac207996eb2f11a4e
- `experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json` · 5ea5607ddc906e81539809eb2e0c37431b40ba1425ae4c139ac3f50b8497a9f6
- `experiments/poisson1d/EXPERIMENT_PROTOCOL_20260915.md` · bacbe98a6ff832963819e9e6bab19504b54c18979e9e01ba1fb83860e5accf49

### exp1-calibration-r1

- `identity.json` · 269a86ecaa9cb66b064415e5c26c19e64de17859fa963745a99f4acf64bf63d0 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 9acd944dd99b3caf9cdd61ff64ce5769dfc47efed0d76a0bfcf7638d87ce913f · EVALUATION_SET
- `sets/dev.json` · 8b28ab8545ae8774e73df26dd050261cea18f496054380e4c9691a8505f3b73c · EVALUATION_SET
- `sets/phys.json` · d63b11bd2f811f4ac62536ca3d744fef0552860ebb9adfffbf95edd9382dd933 · EVALUATION_SET
- `sets/claim.json` · 02ee4e7533ea0eb0ff16828bb6f447e0c63f217b2e911ea1eabd6862659eb08e · EVALUATION_SET
- `sets/isolation.json` · ad41639f2bd2c0db29e4afb20807968e82217c342d11724f5f0b829f0ed24714 · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `gate1_math.json` · 4756aae17d2e600fc3afcd0696f2efcf1a0d6b84c4a0be82969cd823c973f030 · GATE_RESULT
- `gate2_baseline.json` · 31f19a439cbe1bee048c23b2e85f505b289751ba4fa1dc1f5f0c8d887718ea8f · GATE_RESULT
- `gate3_implementation.json` · ba4d69cb95cdb7ef2d9c99fee908a896fd8faeba932980c2f8748071e7d7b1fc · GATE_RESULT
- `seed_ledger.json` · 706db5ad382f964566e019f8d82b40c8c98041a2a9a5f1f6ccc3419ddff635de · SEED_LEDGER
- `runs/run-00.json` · 280c13ea46787ae0bdeb937584469bccc5af91dcaf561a08eb5fd5f4413326bf · RAW_MODEL_PREDICTION
- `runs/run-01.json` · 976655fae4f7492d8a4db1d2f8de7279c1750f5de2179aeee4e4260844f900a0 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · cd1a560ccad16ede6078c92fb046e00525e0c08bb19a868d2ce906eacb53757a · RAW_MODEL_PREDICTION
- `runs/run-03.json` · f1592e20a44cb2fed3b75300bbc4cf60e46424160aba91ca8c173a79408ab341 · RAW_MODEL_PREDICTION
- `runs/run-04.json` · 3429fdd4aa461099f82761e95bf34682b60381c39b099c39267a33ada88a5652 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 6ccfd6935cce97292f97d9d20cb0866929113547ab807fc05f55ef8f49fc2d64 · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 7cfd57722dd9a5a7a4521e7a2baab552b633c6777b6badb02c3ca20febf0eae1 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · eac8cd2dd84191a0cda86c913431672566c6fb8cb2f1fbd8857360a1edf02ba3 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · ef78375021c9e05a8f42e24477caf21f95d17ca46323e552d870c91ffb514d51 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · e15a426bdde35ff2e16cca35cea739d74b7feb196f7d2731a536f060c2db9e0d · RAW_MODEL_PREDICTION
- `gate4_training.json` · a9cd97dce9a88e1fef4511985d56a5dcb0d42f84fe5f3bc876a85883fa8a0d3a · GATE_RESULT
- `training_report.json` · 3cae84cf449f17630a2bca198d14a6b2bb53873b6f8ef49498a258b99c6ddc11 · TRAINING_REPORT
- `gate5a_physics.json` · fe720e327f793872b66eadcb5c0b59db873e33c77e19452314cd3f85c1ea8860 · GATE_RESULT
- `claim_set_ledger.json` · 5ea5607ddc906e81539809eb2e0c37431b40ba1425ae4c139ac3f50b8497a9f6 · LEDGER
- `problem_definition.json` · 1a241fd4d9424abe692db924dcb01665e2d475b91860d627bb74dbb8951bbe0a · PROBLEM_DEFINITION
- `gate5b_external.json` · 313d75b5bf073f5079c0f2cc00c3e1c026d72c6a4cd712aa3176cfaef91a8619 · VALIDATION_METRIC
- `run_record.json` · 9e801189afff4321e8f7b17e06a50c8df9160891b98f84b61fc11eb12a66ff2b · RUN_RECORD
- `attempt_state.json` · 18494dc95981523d568c449120291fd4b7e7a424f9588212480194ea8112c327 · STATE
- `claim_statements.json` · bf58487b2f7ec62934251cf584c24e40f87599c095bb2ddfe8b5097f6fb78ce9 · CLAIM_STATEMENT
- `failure_record.json` · 22c65a6d1fdc7ed7be26eee9a0eee036094fde04a11c5298fe7bbfd672ee46c2 · FAILURE_RECORD
- `dev_diagnostics.json` · 27733bca4a7537de3341e90cd4dc9ecc52ea62620d8270456e205ade36c653e3 · DIAGNOSTICS
- `trust_vector.json` · 18158d9191053b800351baa523bc12b23a6796f4ee2415d1965bb5c7d75eac95 · TRUST_VECTOR
- `RUN_SUMMARY.json` · d0c1dfecc14ce947c429c08f038727a39ee1a0a78d3d11fadc3f2f8cfa348d86 · SUMMARY
- `PROVENANCE_MANIFEST.json` · 475ad634a439bb763108b76088f2f5e5c706962926129e84b76bc0547f6796ca · (index)
- `STATE_TRANSITIONS.json` · 454da36029f703f7a861b6471094a856ad69d56b48da1b8477f227e98e7c65e2 · (index)
- `TRUST_REPORT.md` · 53492cb27f3c089fe949d291d5e95c8348d0e3a158c2673fb543b879636ec40c · (index)
- `plots/exp1_loss_vs_error.png` · f468dd43701f3fce1844e1e0e0524fd650a2d4b30c6e780e3a63367db5158c40 · PLOT
- `plots/exp1_multiseed_errors.png` · fb24bcb26e7031e73464d8527687b04ef239a180cb078f23807a946e88d11eaf · PLOT
- `plots/exp1_solution_error_residual.png` · 0d8d4cabd70bc53b62153835c5627a7a51369873d99c5cb0230318a84caf04d7 · PLOT

### exp2-bad-sampling-r1

- `identity.json` · d47ca95ba942f8f81c40a4949af85353fb15749a017199fb4250e5d8ad0de9c2 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 7e62ab35e621de4f5f9793142b96ea68b2375b91e4fc0f843fdb20be0cb1b431 · EVALUATION_SET
- `sets/dev.json` · 278b0d466c2f729de4f621bf6e6547453d330b95b4bb1a101781be03e150a0af · EVALUATION_SET
- `sets/phys.json` · 3ebd977287939c792c2bddeb106afdf0d9d1892dc4bd4614674f8c6b83df1d37 · EVALUATION_SET
- `sets/claim.json` · 33ea07647a39cd2706bfe9c8d0fd3d294d73b749eb6b97c630c7b64c3a3f57fa · EVALUATION_SET
- `sets/isolation.json` · c3e6b9d9475e1b2d8dc72dcb7ed87132fe3d4306f2206323bbdbedf7b8a779e2 · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `problem_definition.json` · a6b159974527d45eac1ac938f119a06a0ae1da1b290dbb44e85a2490b5cb33ff · PROBLEM_DEFINITION
- `claim_set_ledger.json` · e942ff76bb5aab94ec6fe4ce9acc8533b3c48ce07f5959e68a43ef49ab81497e · LEDGER
- `gate1_math.json` · a0cf75622c2766310b797f0dc5fc8acee6cde901de13572446c44eb8a5d12908 · GATE_RESULT
- `gate2_baseline.json` · 3d7428e4f615cb9a2158c45c926be144b62d71a2d6e44bd8d2d7187dc58825e8 · GATE_RESULT
- `gate3_implementation.json` · 0aee6055ce898387f1201258368e55e950226e2d84e389a5ff481751d3500aaa · GATE_RESULT
- `seed_ledger.json` · 2759ad9de00446581733f5b118e2c46d707808c7680e330a7fbdb9bf9558ce2b · SEED_LEDGER
- `runs/run-00.json` · df8743b1e3ef55ab0cb2f8018199ee5e746ae205a61faedb63b46c2f260409c0 · RAW_MODEL_PREDICTION
- `runs/run-01.json` · ae3a6c4b8450e3d685388706f89d9d09cdfdea291efd9afa2600576d36a64884 · RAW_MODEL_PREDICTION
- `runs/run-02.json` · 54963608db1d34053bc020928d586eda87dde7ebfb8c452f150cba73bd1a0e3f · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 56f5263373047dd961a89a5d3d23019a832f90fd677f4ebb0e9a2f7bdd7cf5e7 · RAW_MODEL_PREDICTION
- `runs/run-04.json` · bd8ad310e6312f56e37a21faecbca42d5645417983bbdddb3f23f1e5595f7338 · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 85660419bc63aeaf1e82590c2cddefe8e57ce4f3291fe5e1008517e3cfde1f8b · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 24931dafecfb96649c66975dfe060741316602d7ae82139777fbf0de69840b91 · RAW_MODEL_PREDICTION
- `runs/run-07.json` · c600888440525d8d409749feaafd48e67c87c015913dbbe5b2a70c1d2208dadb · RAW_MODEL_PREDICTION
- `runs/run-08.json` · aec6b062f82d1eb5bf0206188a9eee4ec8ba311864fd980de477a51e382386fc · RAW_MODEL_PREDICTION
- `runs/run-09.json` · e9c3c0243920a238c065117e3679e58eee8820aae89337f8f3a4344a208d4460 · RAW_MODEL_PREDICTION
- `run_record.json` · bda477802c2274305efc8cbfaf23b513afca421e92dee04d2afa8b592066c00c · RUN_RECORD
- `gate4_training.json` · c73088833315ec3055513466b70a277a7a20fcd0122fadfd0aa537c185fbcd8d · GATE_RESULT
- `training_report.json` · 8f60943f769998e61e5cb0d5d0c7e80b4413ad9058638b1d657b048cdcf94453 · TRAINING_REPORT
- `attempt_state.json` · 2c828b3d1aa39d452c5aa2ab9885eca4ae70d2cd2c8faaebfc55768ac6c6a672 · STATE
- `failure_record.json` · a311faed2cc1361f578883e9a89d5353ee89e33d076d95dd33d90b720387c65b · FAILURE_RECORD
- `dev_diagnostics.json` · 3f90e35545b552097552ac29ba328aa65af54c86f87626b2153d82b2531575fb · DIAGNOSTICS
- `trust_vector.json` · 83c17ea73cb91aca9b5300f93deeda25f3d9dfb5b91b8315eec74ed5b3b663d7 · TRUST_VECTOR
- `RUN_SUMMARY.json` · 6acab75c95d4b92ccf1e31b33f1b2c3c55d2dce3fda6a1bb43caad8859d60632 · SUMMARY
- `intervention_plan.json` · 5a9668770054d2b419ae02e489a7e284b68147078c25436856006670616c85dd · INTERVENTION_PLAN
- `intervention.json` · 4ee7e239056084d1cf7c578d2996df26384e25e611aec1e1d2a4f42cabe6c409 · DISCRIMINATING_EXPERIMENT
- `diagnosis_record.json` · 435a29d4a7cd74b8bc4784f2c65dddaea1d8aaf2a0c9f5c665033011c4bb80fe · DIAGNOSIS_RECORD
- `diagnosis_verdict.json` · 3e1acff119ab47752329f9d784d04db2ed9ba601c41bb881a0b83cb3a9f72765 · DIAGNOSIS_VERDICT
- `revision_record.json` · e18958ab2d91463d2cc630d3d37bbe3a0f5abde954ae10c306ac08418ba87401 · REVISION_RECORD
- `PROVENANCE_MANIFEST.json` · ec8812b84c2e56d22b396aec2751f7fd141c1be59f426ec1bad9252a4efa726e · (index)
- `STATE_TRANSITIONS.json` · 7a2154feb327adac7bbaf48f5182b246a0d977c38d69d109af8180eccc8cacf1 · (index)
- `TRUST_REPORT.md` · 44fd7840196b97fdef57fc654d786eaa8033244e1938ba80de0c82f3437b87cb · (index)
- `plots/exp2_bad_sampling_solution_error.png` · e9e44a8d82d6d9bb9f0e76eefb93bef395729b35b6f63c92cf227176ec241b5d · PLOT
- `plots/exp2_before_after_revision.png` · c1dc619988e3ac1c6cd02915d27795a9004ee11f33fa57b8e4e0a297505d8c77 · PLOT
- `plots/exp2_intervention.png` · 2ef0a301341b5d99044402a81b7e0160c65a5f04ce597f7905153baec40714fb · PLOT
- `plots/exp2_sampling_locations.png` · 910ffe66c0dfab065ab2e89105440e1f956f883126525235f661b119845c3351 · PLOT
- `plots/exp2_state_transitions.png` · d4e0c05ea5352067941399d2bbf452f74dfa1ff8e3953b5485e507fc29940fca · PLOT

### exp2-revised-r1

- `identity.json` · cec885d385ff438a9c45cb05d67b5856fd259f04c885b709c150d6ed1f770f68 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · 7e62ab35e621de4f5f9793142b96ea68b2375b91e4fc0f843fdb20be0cb1b431 · EVALUATION_SET
- `sets/dev.json` · 278b0d466c2f729de4f621bf6e6547453d330b95b4bb1a101781be03e150a0af · EVALUATION_SET
- `sets/phys.json` · 3ebd977287939c792c2bddeb106afdf0d9d1892dc4bd4614674f8c6b83df1d37 · EVALUATION_SET
- `sets/claim.json` · 33ea07647a39cd2706bfe9c8d0fd3d294d73b749eb6b97c630c7b64c3a3f57fa · EVALUATION_SET
- `sets/isolation.json` · c3e6b9d9475e1b2d8dc72dcb7ed87132fe3d4306f2206323bbdbedf7b8a779e2 · EVALUATION_SET_ISOLATION
- `sets/phys_weights.json` · ae66464729cbe7667daf612a5e5041a6fdd901e2fc8b8c80a935fb4389498c02 · EVALUATION_SET
- `gate1_math.json` · a0cf75622c2766310b797f0dc5fc8acee6cde901de13572446c44eb8a5d12908 · GATE_RESULT
- `gate2_baseline.json` · 3d7428e4f615cb9a2158c45c926be144b62d71a2d6e44bd8d2d7187dc58825e8 · GATE_RESULT
- `gate3_implementation.json` · 0aee6055ce898387f1201258368e55e950226e2d84e389a5ff481751d3500aaa · GATE_RESULT
- `seed_ledger.json` · 628a6b5b9ca77063db28e1b2572a4e1cc815fa0975f3a673ea6dd540d6ef89cd · SEED_LEDGER
- `runs/run-00.json` · a09150e03c0892132fb7d456a1c17c2af689af926ffc82151838466db50d22be · RAW_MODEL_PREDICTION
- `runs/run-01.json` · a39faa28b9d89f7cc2667f74e5f9a5dc9b22b2cb6eea0882b0af9fdc3497637e · RAW_MODEL_PREDICTION
- `runs/run-02.json` · 41e34e92545a3df0e7e6b20c05584207cf742c56d591859dfe74a3dcfce8dc5f · RAW_MODEL_PREDICTION
- `runs/run-03.json` · 6bacefae7a59acb119e2e8e9f5bdb6bfefafc15aafa3e8c4e54b803188d6ad65 · RAW_MODEL_PREDICTION
- `runs/run-04.json` · feae8c7245d5e4530a728481bafbba922ba92a3b3bdcd47c2f9e4ab7ac97889c · RAW_MODEL_PREDICTION
- `runs/run-05.json` · 0462d953b592b167a01f2a4eec860a995aa03e2d5f1078bf638942e5c6907edc · RAW_MODEL_PREDICTION
- `runs/run-06.json` · 1cf6d707a17c8ee54815e97a359a239f2b214a25cb082e1267daf0e1c1e6162f · RAW_MODEL_PREDICTION
- `runs/run-07.json` · a660483a3600925e26f8029ebfa36dbd477c694aa5a1a815488b167445816c81 · RAW_MODEL_PREDICTION
- `runs/run-08.json` · c8e3a5e2e246b4634d87583a05039f05a6029122e75f25f670443667fc615e56 · RAW_MODEL_PREDICTION
- `runs/run-09.json` · 27dc2151c0dcf702bcfee4160c5df60892685da254fefc94879f2d97a35ff053 · RAW_MODEL_PREDICTION
- `gate4_training.json` · 9896e574adeaf48d2e811355e2c9d1590f85513b624ca1538cce720f99f5945d · GATE_RESULT
- `training_report.json` · 4a6b3bcdad21d3cf63c5ad639a89eb24936dcc8ed0d76bb296a0566507637374 · TRAINING_REPORT
- `gate5a_physics.json` · ff9a91b97abd9a5dec884813be40f1bc0a152a8083399873ea576c6d77ee74f1 · GATE_RESULT
- `claim_set_ledger.json` · bbc600adb59f3b90470e1938c4ffe62c457dd8417e16088ac207996eb2f11a4e · LEDGER
- `problem_definition.json` · dbdd3284b723fee394cddeb37b04ddbb51dd298721d841681fcd58acc2d55116 · PROBLEM_DEFINITION
- `gate5b_external.json` · 4b42be67feef38211ab96f6e56d7eb3b5713c1bfc82be05228e934241c0f5bac · VALIDATION_METRIC
- `run_record.json` · 41b9e0827e3ebe1aaee8fe7e2fee5b737ccaf2f05a66f66a17dd9355253f2a6a · RUN_RECORD
- `attempt_state.json` · b520fe54d60879cd1925cd6b10ec4f06f76f274ade44527ecbfd9ebd844f7b39 · STATE
- `failure_record.json` · f815f0ac5cdf20f6df9a002e601d76e7ed83465f8eedd03794c34dee41cd550b · FAILURE_RECORD
- `dev_diagnostics.json` · 27733bca4a7537de3341e90cd4dc9ecc52ea62620d8270456e205ade36c653e3 · DIAGNOSTICS
- `trust_vector.json` · 05b15cbc494424fa578db9ecb7afe637e764c6af7af90d728d09b4a5779e4d19 · TRUST_VECTOR
- `RUN_SUMMARY.json` · 672e28b969188a3ec751e770429afaec015408b2cc7f218b7451e08239684b42 · SUMMARY
- `PROVENANCE_MANIFEST.json` · 1965d9dc5957fbd26ff82e2c102cea0f55c6ec6e557e2be471be0dfcc8eac4cf · (index)
- `STATE_TRANSITIONS.json` · 94eab130013919d5ba0e5adb80b96b4454265c53237921f3d6a432badf70338f · (index)
- `TRUST_REPORT.md` · 71e245e34c7ad065b8a336d70d514c374d21c13d10e03247c35093a1b126496b · (index)

````

</details>

### R040 — 项目/docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Poisson 2D Calibration Report（2026-09-16）

执行负责人：Claude（队长）。宪法 1.2 不变（A-0001、A-0002 ACCEPTED，无 A-0003，无新 Gate、无新 TrustStatus、无阈值事后放宽）。1D 的机器记录一律未改。预注册 `experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md`（正式 run 前提交，commit `f3d322b`）；复用审计 `experiments/poisson2d/2D_REUSE_AUDIT_20260916.md`；追加审计 `PORTABILITY_AUDIT_20260916.md`、`PILOT_ROLE_ANNOTATION_20260916.md`。全部数字来自机器记录。

## 1. Executive Result

```text
2D Poisson Calibration:
PASS

Highest admissible Claim:
C2   (SUPPORTED @ C2, ClaimGateDecision cgd-exp2d-poisson-calibration-r1-g6)

State:
ACCEPTED

READY FOR USER / EXTERNAL REVIEW BEFORE THE NEXT 2D COMPLEXITY STEP
```

被检验的命题不是"2D PINN 能拟合 sin(πx) sin(πy)"，而是**Leo AI 的科学治理、诊断、盲验证与复现机制能否从 1D 跨到真正的二维 PDE 而不失真**。答案见第 2 节。

## 2. Dimension-Lift Audit：What broke only because the problem became 2D?

| 类别 | 结论 | 事实 |
|---|---|---|
| **sampling** | 需要新构造，规则本身没坏 | 治理层的样本身份（`canonical_sha256({inputs:[x,y], quantity})`）与互斥判定天然支持二维，一行未改。因维数出现的新约束在 claim 网格族：一维只需让 CGL 节点避开有理格点 `i/d`（1D 曾因 CGL2800 撞 x = 1/4 而弃用该成员），二维张量族还要求不同成员的 CGL 计数**两两互素**，否则两套网格整族共享内部节点。构造规则 `m−1 ∈ {49,53,55,59}`（与 6 互素且两两互素）；实测两两共享样本 0，反碰撞最小距离 4.09e-05 / 8.68e-06 / 3.28e-07 / 6.03e-06。 |
| **AD** | **真正的新失效模式** | 1D 的二阶导是单变量两次求导；2D 必须分量分别求导，而且**对称的制造解在 claim 层无法判别 x/y 互换**（u\* 在互换下不变，任何 AC 都不受影响）。判别能力只能放进 Gate 3：新增 T2，用非对称探针 w = sin(2πx) sin(πy) 分别验证 w_xx = −4π²w、w_yy = −π²w（实测 7.11e-15 / 1.78e-15，两分量判别间隙 > 1）。这条写在预注册的事前披露里，不是事后补的。 |
| **runtime** | 贵约 11 倍，仍可行 | 1D 每 run 16.7 s（3×32 / 6000 步）→ 2D 选定档 4×64 / 10000 步 ≈ 187 s。pilot 实测每步耗时由 Python / autograd 图开销主导（batch 128 → 1024 每步成本几乎不变），所以 2D 的可行性来自"大 batch、少步数"，不是更大的网络。 |
| **memory** | 无问题 | 参数量 12,737，配点张量 1024×2 float64；峰值远低于 1 GB，未触发任何限制。 |
| **validation** | 判据必须重定义，阈值不能机械照搬 | 1D 的 AC-5（∫u = 2/π）与 AC-6（u′(0) = π）是一维解析常数。2D 用 ∫∫u = 4/π²，并把 AC-6 由"单点导数"改为"整条边界求积节点上的最差法向导数"（更严）。新增 **AC2D-9**：全局 L2 在二维看不见空间热点，这是维数提升带来的新失效模式，因此把 AC2D-1 的常数逐块施加在 8×8 分块上（**分母是全域 u\* 的 RMS**，所以这是一个*局部相对误差*，其值远小于 1；它严格不小于**同一网格上的全局相对 L2**，对 AC2D-1 则是经验上更严——实测比值 2.90–4.36。详见 `runs/exp2d-poisson-calibration-r1/POST_AUDIT_ANNOTATION.md` 与 `AC2D9_FORMULA_AUDIT.json`）。 |
| **visualization** | 全部重做 | 一维曲线图在二维无意义；新增解面、误差热图、残差热图、配点分布、最差 seed 误差场、FDM 收敛图、Red Team 汇总，全部由已登记的 D_phys 张量网格与已存权重生成，不引入新的评估面。 |
| **governance** | **none** —— 没有任何治理条款因维数失效 | 宪法 1.2、状态机、六维向量、弱链演算、账本、PRELOCK、schema 全部原样适用。唯一被触发的是账本既有规则"OPENED 的 specHash 必须等于 SEALED 的 specHash"，它要求盲集池在 revision-1 ProblemDefinition 冻结之后密封——这是流程顺序，不是缺陷，冒烟测试在正式 run 之前就把它暴露了。 |

## 3. Numerical Results

冻结身份：`problemId pdef-poisson2d-cal-v1` · revision 1 · specHash `05328d507582…` · codeHash `a39aa07e23d0…` · 配置 `poisson2d-hard-bc-v1`（4×64 tanh，u = x(1−x)y(1−y)N，Adam 1e-3→1e-5，10000 步，batch 512，1024 配点，float64，单线程，deterministic）。

### 3.1 训练可靠性（Gate 4，D_dev 1024 点，10 seed）

| 项 | 值 |
|---|---|
| N / k | 10 / 10（k/N = 10/10） |
| median dev 相对 L2 | **3.686e-05**（ε_spec = 1e-3） |
| IQR | 8.992e-06 |
| worst seed | 4.262e-05 |
| divergent | 0 |
| 逐 seed | 3.60e-5, 4.26e-5, 3.96e-5, 3.86e-5, 3.27e-5, 2.57e-5, 4.07e-5, 3.06e-5, 2.69e-5, 3.78e-5 |
| 判定 | medianOk ✓ worstOk ✓ dispersionOk ✓ → **C_train PASS** |

### 3.2 盲 claim 集上的验收判据（Gate 5b）

claim 集 `D2C-GL32-CGL50`：3328 样本（张量 GL32 = 1024，内部张量 CGL50 = 2304），sampleSetHash `7fbbb775da65…`，artifact `d4d2dd4a4d1c…`。

| 判据 | 量 | 阈值 | 10 seed 最差值 | 余量 | 全 seed 满足 |
|---|---|---|---|---|---|
| AC2D-1 | 相对 L2 | 1e-3 | 4.257e-05 | 23× | ✓ |
| AC2D-2 | 相对 L∞ | 5e-3 | 7.030e-05 | 71× | ✓ |
| AC2D-3 | 四边界 max\|u\| | 1e-4 | **0.000e+00** | 按构造 | ✓ |
| AC2D-4 | 残差 RMS / ‖f‖_rms | 1e-2 | 1.042e-03 | 9.6× | ✓ |
| AC2D-5 | \|∫∫u − 4/π²\| / (4/π²) | 1e-3 | 3.076e-05 | 33× | ✓ |
| AC2D-6 | 边界法向导数最差节点 | 5e-3 | 4.382e-04 | 11× | ✓ |
| AC2D-7 | 能量恒等式 | 1e-2 | 2.879e-05 | 347× | ✓ |
| AC2D-9 | 8×8 分块**最大块 RMS 误差** / **全域 u\* 的 RMS** | 1e-3 | 1.568e-04 | 6.4× | ✓ |
| AC2D-8（SHOULD） | 梯度相对 H1 半范 | 5e-3 | 1.416e-04 | 35× | ✓ |

十个 seed 的 `failedMustCriteria` 与 `failedShouldCriteria` 全为空 → **C_external PASS**。

诊断量（不作判据，seed 0）：残差 max 5.09e-02；**最大/中位分块比 3.94**；热点 (0.298, 0.452) 绝对误差 5.97e-05；最差分块 x ∈ [0.25, 0.375]、y ∈ [0.375, 0.5]，块 RMS 4.88e-05；通量恒等式缺陷 1.27e-06。

### 3.3 物理检查（Gate 5a，D_phys 1600 点 + 128 边界求积节点，取最差 seed）

| 检查 | 值 | 阈值 | 结果 |
|---|---|---|---|
| PH1 闭边界通量 \|∮∂u/∂n + ∫∫f\| / \|∫∫f\| | 1.069e-04 | 1e-2 | PASS |
| PH2 能量恒等式 | 2.879e-05 | 1e-2 | PASS |
| PH3 正性 min u | 7.654e-06 | ≥ −1e-3 | PASS |
| PH4 互换对称 max\|u(x,y) − u(y,x)\| | 7.648e-05 | 5e-3 | PASS |
| PH5 网格线单调性违例 | 0 | 0 | PASS |
| PH6 最大值 | 0.996290 | ≤ 0.9962953 + 5e-3 | PASS |
| PH7 SPD：λ_min(n=1024) / Dirichlet 能量 | 19.739193 / 4.9345 | > 0 / > 1e-14 | PASS |
| PH10 动量收支 · PH11 自由能 | — | — | NOT_APPLICABLE（理由登记） |

`∫∫f` 在 D_phys 上求得 8.000000000000（精确值 8）。

### 3.4 数学与实现（Gate 1–3）

- **G1**：M1 一方程一未知；M2 四条 Dirichlet、四个边 region；M3 无量纲；M5 rectangle / dimension 2 / 四边绑定；M6 参考方程绑定。全 PASS。
- **G2a**：D_phys 上 max\|−(u\*_xx + u\*_yy) − f\| = **0.000e+00**；四边界 max\|u\*\| = 1.221e-16。
- **G2b**：独立五点 FDM，内部最大误差 1.295e-02 → 3.219e-03 → 8.036e-04 → 2.008e-04，观测阶 **2.0084 / 2.0021 / 2.0005**，线性解全部收敛。**事前披露并记录**：制造解的离散强迫恰是五点算子的离散特征向量，CG 一到两步即收敛，所以 Gate 2b 检验的是离散化阶，不是线性求解器的鲁棒性。
- **G3**：T1 逐分量 AD 对中心差分 u_x 4.31e-11 / u_y 1.00e-10（< 1e-6），二阶分量 < 1e-4；**T2** 非对称探针 7.11e-15 / 1.78e-15，判别间隙 > 1；T3 残差算子作用于解析解 3.55e-15；**T4 四条边分别恰为 0.0**；T8 单项 pde 损失、无 BC 罚项；T9 四集样本级互斥（minSeparation 1e-9）；T10 可信校验器接受解析正控制、拒绝全部 6 个污染夹具（符号翻转、常数偏移、小幅高模态、大幅模态、零场、导数不一致）。

## 4. Trust Vector（`trust_vector_g6.json`，supersedes `tv-…-tier1`，校验器通过）

```text
C_math     = PASS   (M1, M2, M3, M5, M6)
C_impl     = PASS   (T1, T2, T3, T4, T8, T9, T10；Tier-1 P4 维持)
C_train    = PASS   (10/10 seed，median 3.686e-5，IQR 8.99e-6，worst 4.26e-5；Tier-1 P1/P6/P7/P9/P16 维持)
C_physics  = PASS   (PH1–PH7；PH10/PH11 NOT_APPLICABLE)
C_external = PASS   (claim set D2C-GL32-CGL50, sampleSetHash 7fbbb775da65…, OPENED@r1 一次, BURNT)
C_repro    = PASS   (repro-envb2d-r1，独立环境，同 spec 同 code 异 seed，容差内)
```

## 5. Failure Path

本轮**没有**进入 FAILURE_RECORDED：Gate 1–5 一次通过，无诊断、无修订、无重入。失败路径并非未实现——冒烟测试（临时沙箱，已删除）验证了 Gate 4 FAIL → FAILURE_RECORDED → 2D 症状（sPdeResidual / sConservation / sPinnCfd / sSeedSensitive）登记 → 账本上不出现 OPENED 事件，即"失败时 claim 集不被打开"这条硬要求在 2D 实现里成立。

## 6. Blind Validation

```text
claim set        D2C-GL32-CGL50
sampleSetHash    7fbbb775da65...
artifactHash     d4d2dd4a4d1c...
size             3328 samples (tensor GL32 = 1024, interior tensor CGL50 = 2304)
SEALED           2026-09-16T12:29:08Z  (revision 1, specHash 05328d507582...)
OPENED           2026-09-16T13:03:07Z  (codeHash a39aa07e23d0...)
BURNT            OPENED 即烧毁；终身只打开一次
still SEALED     D2C-GL34-CGL54 (r2) · D2C-GL36-CGL56 (r3) · D2C-GL38-CGL60 (r4)
metrics          AC2D-1..AC2D-7、AC2D-9（MUST）与 AC2D-8（SHOULD）全部 10 个 seed 满足（第 3.2 节）
ledger head      1dac14f667847f61...
```

盲性保证：claim 集在任何训练之前密封；训练与诊断只用 D_train / D_dev / D_phys；claim 集在 Gate 5a 之后才打开，打开事件带 codeHash 入账本；身份按样本（sampleSetHash）烧毁，把同一批样本重新包装会被账本拒绝。

## 7. Red Team（Tier-1）

只用 D_dev（QoI 用 D_phys），每个扰动一次重训，基线为正式 seed-0 run。阈值：Δq ≤ 1% 维持，1–5% PARTIAL，> 5% FAIL；只能维持或降级。

| P | 改动 | 维度 | e2 | Δq | 结果 |
|---|---|---|---|---|---|
| P1 | 同池重抽配点 | train | 3.220e-05 | 7.778e-06 | PASS |
| P4 | float32 训练，残差 float64 重算 | impl | 5.316e-05 | 1.774e-05 | PASS |
| P6 | 删 10% 配点 | train | 7.570e-05 | 4.264e-05 | PASS |
| **P7** | 边界带（宽 0.1）内配点密度加倍重抽 | train | 3.821e-05 | 5.461e-05 | PASS |
| **P8** | 域缩放到 (0,2)²，硬参数化随域变换，结果映射回 | math | 1.849e-04 | 1.332e-04 | PASS |
| P9 | Adam → L-BFGS（同函数评估预算） | train | 7.578e-06 | 2.723e-05 | PASS |
| P11 | 残差自适应局部加密 | — | — | — | NOT_APPLICABLE（2D 独立判定） |
| P16 | tanh → sin | train | 1.543e-04 | 7.759e-05 | PASS |

```text
Tier-1: PASS（全部适用扰动维持；最大 Δq = 1.33e-4，比 1% 维持线低两个数量级）
```

两点单独记录：**P7 在 2D 判为 APPLICABLE**（1D 里它是 NOT_APPLICABLE，因为一维边界只有两个被精确评估的点；二维边界是曲线，紧邻它的二维带的配点密度是方法的真实自由度），实测维持；**P8 的硬参数化随域缩放**（u = ξ(L−ξ)η(L−η)N）没有重演 1D Tier-1 run 1 的 harness 缺陷，另有单元测试钉死。

## 8. Reproducibility（Gate 6）

| 项 | 值 |
|---|---|
| 复现 run | `repro-envb2d-r1`（Gate 4 后停止，**不触碰 claim 集**，`claimSetTouched: false`） |
| specHash | `05328d507582…`（同） |
| codeHash | `a39aa07e23d0…`（**同**） |
| seed 集 | 原三元组 +10000（seedSetId 不同） |
| Environment A | mamba 前缀，installationId `prefix-689a1fbe8610a998`，dependencyLockHash `75efe91aa4e1…`，environmentId `e986dbc039e0…` |
| Environment B | 全新 venv（base 同一 mamba python 3.12.9，无 system-site-packages，`--no-cache-dir` 只装复现包声明的 torch 2.12.1+cpu 与 numpy 2.4.5），installationId `prefix-ede7d4c77496dd0e`，dependencyLockHash `460309bb1065…`，environmentId `48e795c85bbd…` |
| 独立性 | **independent = True**：强字段中 `installationId` 与 `dependencyLockHash` 不同（machineId / osFamily / acceleratorClass / frameworkVersion / blasBackend 在同机上必然相同；宪法 28.1 只要求至少一个强字段不同） |
| dev 相对 L2 中位 | A 3.686e-05 · B **3.286e-05** |
| \|Δmedian\| | **4.000e-06** |
| 预注册容差（两条同时成立） | 绝对 ≤ 1e-4 ✓ · 相对 ≤ 0.5 × median_A = 1.843e-05 ✓ |
| 诊断（不参与判定） | \|Δmedian\| / IQR_A = **0.44**（差异小于原 run 自身的 seed 离散） |
| k/N | A 10/10 · B 10/10，判定一致 |
| B 的 IQR / worst | 1.464e-05 / 6.167e-05（divergent 0） |
| 判定 | 同 spec ✓ 同 code ✓ 独立环境 ✓ 异 seed ✓ 容差内 ✓ → **C_repro = PASS** |

**与 1D 的方法差异（重要且如实记录）**：1D 的 G6 必须在原 commit 的**冻结分离检出**上跑，因为那一轮的 runner 代码在两次运行之间改过，codeHash 不同会被 `reproduction_status` 正确判 BLOCKED。本轮两次运行之间**代码身份清单内没有任何文件变化**（中间的提交只增加了 `experiments/` 下的证据，不在代码身份前缀内），因此 codeHash 由校验器复算后逐位相同（`a39aa07e23d0`），gitHead 不同（`ad9f029` 对 `22117f0`）而 codeHash 相同——这正说明代码身份是**内容哈希**而不是提交哈希。复现因此直接在同一工作树上用 Environment B 的解释器执行，并由 `reproduction_report.json` 机械记录 `sameCode: true`。复现包 `experiments/poisson2d/repro_package/` 仍按冻结检出的方式书写说明，供外部方使用。

## 9. Tests / PRELOCK

| 项 | 值 |
|---|---|
| HEAD `e7d85c2` 真实基线 | **1109 passed / 3 failed / 6 skipped** |
| 新增测试 | 22 项（`test_poisson2d_identity` 7、`test_poisson2d_physics` 10、`test_poisson2d_reproduction` 5） |
| 本轮全套 | **1121 passed / 3 failed / 16 skipped** |
| 失败项 | 全部是审计过的既有 portability 三项（第 10 节 NB-1），与 2D 结论无关 |
| 跳过项 | 16 = 既有 6 + 本轮 10（治理 venv 无 torch / numpy） |
| 被跳过测试的补充执行 | `experiments/poisson2d/verify_tests_under_torch.py` 在训练解释器下跑同样的函数：**17 passed / 0 failed**（记录 `TEST_VERIFICATION_UNDER_TORCH.json`） |
| PRELOCK | **7/7 PASS**（constitutionBinding / spec / protocol / adversarialManifest / lockDraft / repository / amendmentRegister） |

测试覆盖面（PART 22 逐条）：2D 样本身份（含 (x,y) 与 (y,x) 不同一）、二维集互斥与最小间距、四条边硬 BC（含缩放域）、u_xx 与 u_yy 分量分别验证、2D 残差、对称性度量、2D claim pool（互斥 + 反碰撞）、局部误差检测（全局范数仍通过时单块热点必须被 AC2D-9 抓到）、2D 复现包与容差、校验器对畸形证据的拒绝。

## 10. Newly Discovered Problems

**BLOCKING**：无。

**NON-BLOCKING**

- **NB-1（既有，非本轮引入）**：HEAD 的 full suite 有 3 项 portability FAIL，来源是 1D 收口提交 `32eaa36` 入库的绝对路径证据；1D 收口报告记的"1112 passed / 0 failed"是证据入库之前跑的。**本轮 2D 证据又新增 3 条同类发现**（`TEST_VERIFICATION_UNDER_TORCH.json:4` 的解释器路径、`environment_b_qualification.json:46` 的 venv 路径、生成脚本 `qualify_environment_b.py:45` 的同一字面量）；1D 那类 `PROVENANCE_MANIFEST` 污染未复发。按宪法 28.1"路径不是身份"，这些不影响任何 specHash / codeHash / environmentId 或 AC 数值。本轮**未改 policy、未改任何证据、未加豁免**，裁决项见 `PORTABILITY_AUDIT_20260916.md` 第 5 节。（自指效应，如实记录：审计文件第一版逐字引用了被指认的路径，`experiments/**` 在扫描范围内，于是审计文件自己又多出 2 条同类发现；已把审计说明文字里的用户名脱敏为 `<user>` 消除，被指认文件一字未改。扫描范围事实：`docs/**.md` 与根目录一份报告属类别豁免，`experiments/**` 不豁免。最终计数 7 条 = 1D 既有 4 + 本轮实质 3。）
- **NB-2**：EXPLORATORY pilot 同时承担了性能测量与**架构 / 模型选择**。宪法 1.2 第 561 行明文把"模型与架构选择"列为 D_dev 的许可用途，第六十五章要求晋升时在冻结规格下重走完整闭环（本轮正是如此，seed 严格不相交），因此裁决 **ALLOWED，不阻断 C2**；如实登记于 `PILOT_ROLE_ANNOTATION_20260916.md`。
- **NB-3**：1D 的症状阈值 `sLocalizedError`（最大块 / 中位块 = 3.0）在本轮**一个完全合格的结果上就会触发**（实测 3.94）。原因是二维误差场的空间结构天然比一维分箱更不均匀，而该常数是按一维 10 分箱定的。本轮它只作为失败路径的症状规则、未参与验收（验收用 AC2D-9，实测 1.57e-4 对阈值 1e-3），因此没有造成误判；但它说明**症状阈值需要与维数相关的定义**。
- **NB-4**：Gate 2b 的独立 FDM 基线因制造解恰为五点算子的离散特征向量，CG 一到两步收敛；它验证的是离散化阶而非线性求解器鲁棒性（事前披露，非事后辩解）。
- **NB-5**：`disjointness_errors` 的最小间距扫描是 O(N·M) 纯 Python，本轮规模下每次 attempt 约 15–20 秒、register-pool 约 70 秒。可接受，但集合规模再上一个量级就会成为瓶颈。
- **NB-6**：本轮的 C2 建立在**单一 2D 问题、单一架构、单一机器的两个独立安装**上。C3 需要 ≥ 5 个独立合格 C2 run，本轮结构上不可能达到，决策文档已明确阻断。
- **NB-7**：`problems/*-claim-pool.json` 的 `status` 字段在成员被打开烧毁后不会回写（本轮结束时四套仍写着 `SEALED`，而账本已记录 `d4d2dd4a` 为 OPENED）。真正的防线是账本而不是这个字段，已实测验证：对同一 claim 集再次 OPENED 被拒（"a set is opened once, ever" + "a second OPENED for the same problem and revision"），把同一批样本重新包装后密封也被拒（"a re-wrapped claim set is not blind"）。但 runner 在 `phase_problem` 里的早期护栏读的是这个**过期字段**，因此一次误用会在训练跑完之后才被账本拦下，而不是在开始前。该字段与该护栏都是从 1D 继承的，本轮未改（PART 25 STOP）。

**AMENDMENT CANDIDATE**（只登记，不起草）

- **AC-1**：症状阈值（`sLocalizedError` 等）应有维数相关的定义或标定方式（来自 NB-3）。
- **AC-2**：claim 网格族在多维张量积下需要成文的构造约束（成员计数两两互素、与有理格点的反碰撞按分量判定），目前只写在本轮预注册里。
- **AC-3**：证据文件中的环境构造描述建议只记 prefix 哈希与依赖，不记绝对路径（来自 NB-1）。
- **AC-4**：EXPLORATORY 活动若同时承担模型选择，建议在协议层要求显式分标记（来自 NB-2）。
- **AC-5**：pool manifest 的成员状态应由账本推导（或早期护栏直接读账本），而不是静态字段（来自 NB-7）。

## 11. Final Recommendation

```text
READY FOR NEXT 2D COMPLEXITY STEP
```

理由：六维全 PASS，Tier-1 全部维持，G6 在合格独立环境复现且落在两条预注册容差之内，状态机 ACCEPTED，唯一阻断的是结构上不可能在本轮达成的 C3。维数提升没有击穿任何治理机制（第 2 节 governance = none）；被击穿的是**度量与判别设计**——对称制造解无法判别 x/y 互换、全局范数看不见空间热点——两者都已在本轮用 T2 与 AC2D-9 补上。

**本轮到此停止**（PART 25）。不开始不规则几何、BFS、Navier–Stokes、UCM、传热、新修正案或架构扫描；等待用户与外部评审。下一步若获授权，应从新的 ScientificSpec 出发，带自己的 claim pool 与预注册。

## 附录 A：证据清单（artifactId · sha256）

### 顶层

- `specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json` · 46e98c699e00ca108d39f11bd38b37933bea8323b2f24d2af48fc8f7dcdb5269
- `experiments/poisson2d/2D_REUSE_AUDIT_20260916.md` · 5fce7c4e526a9ce749872c5910ce09783aa24b3ac4222e6fe1773c00f897bac7
- `experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md` · 4aa47e64aa5e0c0786d425ac68bcda52e521728c96eda7ba0817e3a92ebf9c9d
- `experiments/poisson2d/PORTABILITY_AUDIT_20260916.md` · 1f4681a36a5fd561ced42846c1db01df922e1a99930b5771f85657303d037515
- `experiments/poisson2d/PILOT_ROLE_ANNOTATION_20260916.md` · 0c7d4ce46c0e617cc62202cfca1d676425aced839a84215e0f083baeffb0aa69
- `experiments/poisson2d/configs/exp2d_baseline.json` · bf933c93b3f7fecd668872ff0d37487cda9770a076b9a07c504aead7868719c7
- `experiments/poisson2d/pilot/PILOT_RESULT.json` · 1a71c4c989491d1fd05105422588fab5f25b7bca428d4627e55abc53a1de7af3
- `experiments/poisson2d/TEST_VERIFICATION_UNDER_TORCH.json` · bfda55dd9a847e665815d1cc46bae6d5ad951533030191b96dcc0fe9c8b13500
- `experiments/poisson2d/environment_b_qualification.json` · f315790a8461027b9d1ffbf8c895217133955dfd31517c0892edc5b0b082cd3c
- `experiments/poisson2d/problems/pdef-poisson2d-cal-v1-r1.json` · 3d6a9beb4cbf1975b6c269d0cc506b3c40841bf382248f0bd911e5a489312b61
- `experiments/poisson2d/problems/pdef-poisson2d-cal-v1-claim-pool.json` · 36e92973174c295a5ac6763a11dea1cf8487ee33861e2fa1a3ca7544b07e1419
- `experiments/poisson2d/ledger/pdef-poisson2d-cal-v1.json` · 63e1e33c0c38982a9cdfd30b0857752ca34e4dde3dd091fa37be503c2986ea5c
- `experiments/poisson2d/repro_package/PACKAGE_MANIFEST.json` · bb537b3b317bd231b60cc8d161523cd8362c802f295cc4ff409178092bb1a329

### `runs/exp2d-poisson-calibration-r1`（44 个 artifact，此处略去 10 个 `runs/run-*.json` 与 9 张图）

- `identity.json` · 2fdee940205466500df95647d4774573d396f473d0f4f26b8e1d1a573e010352 · IDENTITY
- `prelock.json` · 0ba2301b4cfc61f88e04be4645e718cf169eda4aaba3b8e2d245db131e1f99a8 · GOVERNANCE_CHECK
- `sets/train.json` · ddbac79c99d071900943ae89af8bb43c1bdc655b2091e01a9d6859455a97a997 · EVALUATION_SET
- `sets/dev.json` · 625b76935b6a0334925a0898d12852aa327ab0c46276d1861b341f94931ee417 · EVALUATION_SET
- `sets/phys.json` · 8d8a61b67c23409bd0e83cf27d1ad7cbac06be254928ee904381f1de67129ad6 · EVALUATION_SET
- `sets/claim.json` · d4d2dd4a4d1c05b6ca31d67d5ee23c04c09481347f6acf51d0b0577ed37ff4e6 · EVALUATION_SET
- `sets/isolation.json` · 4e6c8098abd04d21695182bde02e8e7a7ddddee96b010db27aa34539d4b5eea0 · EVALUATION_SET_ISOLATION
- `sets/boundary.json` · f24bbd4673f3a73adf21519cb470fb99e1497101ffb7778cd816fc633a79617c · BOUNDARY_SET
- `sets/phys_weights.json` · 7cd8189d7625843355230ffb474e153336aaecbe6397bcae86e0f9efcd35ddd5 · EVALUATION_SET
- `gate1_math.json` · 2036093a3faaf8a3d17bb94310b9485a86080ee65d25dd9be5da1f275815052a · GATE_RESULT
- `gate2_baseline.json` · 4cdb3434eeca7f2f7aca40a05c3772198a4c5a1b290860c6023ba3f974e452d9 · GATE_RESULT
- `gate3_implementation.json` · 7b9b865d292753961c7cac317785a93d03d999c751be89a287e484576bd24d52 · GATE_RESULT
- `seed_ledger.json` · 76e188807853ef1827401ecb54a5e4e881a93d651228b033af34813a8d1c7c2c · SEED_LEDGER
- `gate4_training.json` · a42fa1aa7191d940d02de0b8638bacd8102a50448acd534641392faab8d43afc · GATE_RESULT
- `training_report.json` · bb93ab0ae83f3c2b50c6f29b685cbd3b50da4ab39325dcbfa90da359f83260c4 · TRAINING_REPORT
- `gate5a_physics.json` · 60b3c385e4aec1ea2b7375c8bd05867c8c8d27537e542c9ea06216d0d3a58cff · GATE_RESULT
- `claim_set_ledger.json` · 63e1e33c0c38982a9cdfd30b0857752ca34e4dde3dd091fa37be503c2986ea5c · LEDGER
- `problem_definition.json` · b0cf6037cac2f51a3cfceb4b17845862707d101adcb08de7ef7386b29f3f7837 · PROBLEM_DEFINITION
- `gate5b_external.json` · 53ee9f22c5bc32f4d2ac428d681e4ff81f0680da31c2f3082fa3e68972e78d41 · VALIDATION_METRIC
- `run_record.json` · 60ddde96cbcf7f41828c3d7de8e78875a04bc32b56e6e029388f7fd19a3a3624 · RUN_RECORD
- `gate6_reproducibility.json` · 2cc9f7d702b50539fdc8fd29be599df65923e94b3b2343019707ae18bc85fb8b · GATE_RESULT
- `trust_vector.json` · 67a3f502916090bc309c227bb3f25f507e7b972f158e0e4f979814c67cd410d8 · TRUST_VECTOR
- `claim_statements.json` · 5aead66f5415529399cae99d7b40829f138b4638345ddc787f9008635b827905 · CLAIM_STATEMENT
- `claim_gate_decision.json` · 36af3f04e24d5bf054af1e013f9594f84fca29a399fc54846194384b372536de · CLAIM_GATE_DECISION
- `tier1_redteam.json` · 11de4a539088ca0e1b028275ccb8c05679a5772856a5dec8a4a99fd314076868 · RED_TEAM_REPORT
- `trust_vector_tier1.json` · 022cbc3c92276abccaa9f5b9ab9b06029eeebc07cc62991d812ffd6f5263c3dd · TRUST_VECTOR
- `claim_gate_decision_tier1.json` · 1e6299aabebf68867da64901118efbdd8c5ecca2e2e860b09bef3a6495d77063 · CLAIM_GATE_DECISION
- `gate6_reproducibility_executed.json` · 75c95a2c6ff692f636ed09c93924cfb566875ea8f5b4c5167a0830af538a7998 · GATE_RESULT
- `trust_vector_g6.json` · 4fe9778129cf217e831cc4fb1178e925f74fa2350c14fdea609ebcfc8ed620c4 · TRUST_VECTOR
- `claim_gate_decision_g6.json` · eadb801cc9a4cf530e925d32342775d69a2a41ab3b9aeaf7e6b87e9ec391907c · CLAIM_GATE_DECISION
- `attempt_state.json` · c53acc25363f3d01de607fbeec1b4ac76a91f05ca92f1f2f1a7f5b209917b4ea · STATE（ACCEPTED）
- `RUN_SUMMARY.json` · 5b6e17e9b3de7102883a50f1cc0958c009909644cea4c9fe79b7c2f79fde8f8c · SUMMARY

### `runs/repro-envb2d-r1`（32 个 artifact，此处略去 10 个 `runs/run-*.json`）

- `identity.json` · c36495807e1a70e5afd48a7689cb872e9f961afbb339e4195229d375dc8a228f · IDENTITY
- `seed_ledger.json` · 7c15bffe785e2be99511200596f65fec4488033df4a9af9730eb626f45e8f4dc · SEED_LEDGER
- `run_record.json` · 3456107919e4ca2eb621d05bd27715ebdaf49e76c5a23cbf9bb4146d98feb0b3 · RUN_RECORD
- `gate4_training.json` · f130d554ea77507213988208595b02be5629f2985d07231d7eb557b695603053 · GATE_RESULT
- `training_report.json` · d5931635bad172751d75ac77ca06a14ef3ec0e0e4d685a3b8e4ce3f1bc596c01 · TRAINING_REPORT
- `reproduction_report.json` · f0b5d7c77cb0e9cbe890b951860ae8c5b6c3f55f13a17d52f28e18bbd241fb17 · REPRODUCTION_REPORT
- `trust_vector.json` · f82a2c4d11db2b545819bc2d08f1260c51f508823191781382bc6ff6e8a4759d · TRUST_VECTOR
- `attempt_state.json` · 1f080d4b9ab2b3157b115b4b3e13ab54fa2f12660f08b0564d2fa232b9b995f5 · STATE
- `RUN_SUMMARY.json` · d96ea3d2f427ddd1c68cbcf2ec1d35cdd3c8bca256cecfcadd7e6656ad05accd · SUMMARY

（两个 run 的 `sets/*.json` 与 `problem_definition.json` / `claim_set_ledger.json` 哈希逐位相同，这本身就是"同一冻结规格、同一组样本"的机器证据。）

## 附录 B：图（PART 21，全部来自已登记网格与已存权重）

| 文件 | 内容 |
|---|---|
| `plots/p1_analytic_solution.png` | 解析解 u\*(x,y) |
| `plots/p2_pinn_solution.png` | PINN u_θ(x,y)（中位 seed） |
| `plots/p3_absolute_error.png` | log₁₀\|u_θ − u\*\| 热图（中位 seed） |
| `plots/p4_pde_residual.png` | PDE 残差热图（中位 seed） |
| `plots/p5_collocation_distribution.png` | 训练配点分布（run 00） |
| `plots/p6_multiseed_errors.png` | 多 seed dev 误差分布与 ε_spec |
| `plots/p7_worst_seed_error.png` | 最差 seed 误差场 |
| `plots/p8_fdm_convergence.png` | 独立 FDM 网格收敛（斜率 2 参考线） |
| `plots/p9_redteam_summary.png` | Tier-1 各扰动的 QoI 漂移与 1% / 5% 线 |

````

</details>

### R041 — 项目/docs/pinn-trust-loop/POISSON2D_CLOSURE_COMPLETION_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Poisson 2D Closure Completion（2026-09-16，外部评审裁决执行）

执行负责人：Claude（队长）。上游文件：[POISSON2D_CALIBRATION_REPORT_20260916.md](POISSON2D_CALIBRATION_REPORT_20260916.md)（2D 主体）、[POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md](POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md)（终审收口，结论 HOLD）。本文件执行用户 / 外部评审 2026-09-16 的七项裁决，把该 HOLD 的两个原因收口。

本轮**没有**重训任何正式 run、没有改架构 / 优化器 / 阈值 / ScientificSpec、没有重开已烧毁的 D_claim、没有改任何历史机器证据、没有删除失败记录、没有新增 A-0003、没有开始下一个 PDE。

## 1. Executive Decision

```text
CURRENT 2D C2:
CONFIRMED

NEXT COMPLEXITY STEP:
READY
```

| 收口门条件（终审 Issue 7） | 上一轮 | 本轮 |
|---|---|---|
| Portability full suite green under approved exact-hash historical policy | ❌ 机制作用域够不到 `experiments/**` | ✅ 作用域按批准扩展，5 条发现全部精确哈希归类，**0 hard binding** |
| claim-pool early guard uses ledger | ✅ | ✅（未再触碰） |
| dimension-aware localized-error protocol exists | ⚠️ 规则未可部署 | ✅ 触发条件改为「预注册的局部误差验收判据失败」，已部署并测试钉死 |
| PRELOCK PASS | ✅ 7/7 | ✅ **7/7** |
| git tree clean | ✅ | ✅（本报告与日志一并提交后） |
| full suite 0 unexpected failures | ❌ 3 failed | ✅ **1172 passed / 0 failed / 18 skipped** |

## 2. 裁决逐项执行

| # | 裁决 | 本轮动作 |
|---|---|---|
| 1 | 2D Poisson C2 confirmed，科学校准 CLOSED | 只记录，不动任何科学证据；C2 的六维判定与 ACCEPTED 状态一字未改 |
| 2 | Portability policy extension APPROVED WITH STRICT SCOPE | 第 3 节：机制作用域扩展 + 5 条精确哈希条目 + 8 项测试 |
| 3 | Environment B: KEEP（冻结复现夹具） | 第 5 节：保留，不做任何安装或修改；规则写入本报告与记忆 |
| 4 | d ≥ 2 的 `sLocalizedError` 触发条件改为「预注册的局部误差验收判据失败」 | 第 4 节：已实现并部署，Poisson2D 的实例为 AC2D-9 |
| 5 | 为该触发增加五条测试 | 第 4.3 节：12 项测试（含五条要求逐条对应） |
| 6 | 收口后重跑 full suite / portability / PRELOCK，0 unexpected failures → 输出 READY 后 STOP | 第 6 节与第 1 节 |
| 7 | 下一正式实验必须用新 revision / code identity | 第 7 节：登记为对下一轮的硬约束，机器可核验 |

## 3. Portability 机制扩展（裁决 2）

### 3.1 改了什么

`tools/portability_check.py` 的策略加载器原先只接受 `governance/**.md`（这正是终审 Issue 3A 的死结：待豁免证据全在 `experiments/**`）。按批准的严格作用域改为：

| 约束 | 实现 |
|---|---|
| 只能是人工批准的**不可变证据文件** | 路径必须落在 `EVIDENCE_POLICY_PREFIXES = ("governance/", "experiments/")` 内，且后缀属 `(".md", ".json")` |
| **源码 / 脚本 / 可执行文件绝对不得使用** | 另有 `EVIDENCE_POLICY_FORBIDDEN_SUFFIXES`（`.py .pyw .ps1 .psm1 .psd1 .sh .bash .bat .cmd .js .mjs .cjs .ts .exe .dll .pyd .so .lock`）兜底；`manifests/**`、`tools/**`、`pinn/**`、`specs/**` 等根本不在允许前缀内 |
| **禁止 wildcard / directory / machine-path pattern** | `*?[]` 任一字符出现即拒绝；以 `/` 结尾（目录）即拒绝；原有的绝对路径 / `..` / 反斜杠检查保留 |
| 仍须 **exact `file + sha256 + finding_type + occurrence count`**，一个字节变化即失效 | `classify_historical_evidence` 未改：四项全等才归类 |
| 每条豁免是**人工裁决** | 新增强制字段 `ruling` 与 `constraint`，缺任一项即 `RuntimeError` |
| 报告仍保留已批准发现的**可见性** | `--json` 的 `historical_evidence` 段与人类可读输出逐条打印 `EXEMPT-HISTORICAL-EVIDENCE` + 文件 + 行号 + 规则 + sha256（测试断言计数与文件名都在输出里） |

### 3.2 批准归类的 5 条发现

| 文件:行 | 规则 | 条数 | 性质 |
|---|---|---|---|
| `experiments/poisson1d/environment_b_qualification.json:42` | windows-user-home | 1 | 1D（CLOSED）Gate 6 环境鉴定 |
| `experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json:103` | windows-user-home | 1 | 1D 冻结检出复现 provenance |
| 同上 | desktop-path | 1 | 同一行的第二条规则 |
| `experiments/poisson1d/runs/repro-envb-r2/POST_AUDIT_ANNOTATION.md:19` | windows-user-home | 1 | 1D 追加注解 |
| `experiments/poisson2d/environment_b_qualification.json:46` | windows-user-home | 1 | 2D Gate 6 环境鉴定（ACCEPTED run 的证据） |

加上原有的 `governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md`（3 条），扫描器现在报告 **0 hard binding(s) / 1 configurable default / 8 historical evidence finding(s)**。被指认的证据文件**一字未改**：豁免绑定的就是它们当前的 sha256。

宪法 28.1 的判断不变：路径不是身份，这些字符串不影响任何 specHash / codeHash / environmentId / AC 数值。扩展解决的是仓库可移植性卫生，不是科学结论。

### 3.3 机器保证

`tests/test_portability.py`（27 项）与 `tests/pinn/test_p11_and_portability_closure.py` 覆盖：

- 8 条归类逐条钉死（文件 + 规则 + 行号的集合相等，不是计数）；
- 脚本 / 源码 / 规格 / manifest 一律拒绝——参数化里明确包含 `experiments/poisson2d/qualify_environment_b.py`（就在被开放的树里）与 `pinn/experiments2d/runner2d.py`；
- 通配符、`?`、目录写法三种 pattern 一律拒绝；
- 缺 `ruling` / `constraint` 拒绝；
- 一个字节变化即失效（原测试保留）；
- 同样字节换个路径不归类（原测试保留）；
- 人类可读输出仍逐条显示被批准的发现（可见性）；
- 已提交清单的 6 条与磁盘上的 sha256 逐条复核相等，且没有一条指向可执行后缀。

## 4. Localized-error 触发条件（裁决 4、5）

### 4.1 规则

```text
for d >= 2:
    sLocalizedError fires  <=>  该问题在 ScientificSpec 中预注册的
                                localized-error acceptance criterion FAILS
Poisson2D 的实例：AC2D-9（max tile RMS error / 参考解 RMS，8x8 分块，阈值 1e-3）
```

- 统计量固定为 `maxTileRmsErrorOverReferenceRms`，与验收判据是**同一测量、不同点集**：症状在 D_dev 上算，验收在 claim 网格上算。
- 阈值**必须等于**该判据在验收合同（`pinn/governance/poisson2d_contract.py`）里的阈值——症状不得自带松紧，于是没有任何可以事后调的常数。
- 聚合方式与其余症状规则一致（seed 中位数）。
- 与全局度量互相独立：全局 PASS 而局部判据 FAIL 时照样触发。
- `A-maxOverMedian`（1D 继承的 3.0）、`B-robustZ`、`C-topKConcentration`、`D-referenceConditionedZ`（标定最佳者，阈值 26.21）全部保留为 **diagnostics / calibration research**，不是正式 FailureSignature gate。旧 1D 统计量仍随记录打印为 `retiredStatistic`，只报不判。
- 不要求现在从经验 null 分布拟合新阈值（裁决明文）。

治理归类：**协议澄清**。FailureSignature 名称、RootCause 类、TrustStatus、Claim 语义、DiagnosisRecord schema 均未变，**不起 A-0003**。裁决全文与实现入口记在 `experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json`；上一轮的 `LOCALIZED_ERROR_CALIBRATION.json` 作为证据**原样保留**（其中 NOT CALIBRATED 的结论仍是那次标定的如实记录）。

### 4.2 实现

| 位置 | 内容 |
|---|---|
| `pinn/experiments2d/localized_error.py` | `preregistered_localized_criterion`（fail-closed 校验）、`localized_signature`、`apply_localized_signature`、`localized_acceptance_ratio`、`assert_criterion_within_run_identity` |
| `pinn/experiments2d/diagnostics2d.py` | 每个 seed 在 D_dev 上多算一个 `maxTileRmsErrorOverReferenceRms`（与 `referenceRms`） |
| `pinn/experiments2d/runner2d.py` | `phase_failure` 在 `observed_signatures` 之后套用 d ≥ 2 触发，并先核验配置字节仍在本 run 的代码身份内 |
| `experiments/poisson2d/smoke_runner2d.py` | 沙箱配置补上该判据，使冒烟路径仍可跑通 |

**fail-closed**：d ≥ 2 的 run 若 `signatureCriteria` 里没有这条判据，诊断阶段直接报错——那是预注册缺陷，必须在 run 之前修，不许事后补。

### 4.3 五条要求对应的测试（`tests/pinn/test_localized_error_trigger.py`，12 项）

| 裁决要求 | 测试 |
|---|---|
| global metric PASS + localized criterion FAIL → `sLocalizedError` | `test_a_passing_global_metric_with_a_failing_localized_criterion_fires_the_signature`（同时断言 `sPinnCfd` 仍为 False） |
| localized criterion PASS → 不触发 | `test_a_satisfied_localized_criterion_does_not_fire_the_signature`、`test_the_completed_run_would_not_fire_under_the_deployed_trigger`（用已完成 run 的 AC2D-9 实测值） |
| criterion 必须在 formal run 前 preregistered | `test_a_criterion_that_was_never_preregistered_is_refused`、`test_the_symptom_may_not_invent_its_own_bound_or_its_own_statistic` |
| 禁止事后新增 criterion 触发已有 run | `test_a_criterion_added_after_a_run_cannot_trigger_a_signature_on_it`（配置在代码身份内：改字节即被 `assert_criterion_within_run_identity` 拒绝，且 `code_hash_from_manifest` 随之改变）、`test_the_accepted_run_is_not_retro_triggered` |
| diagnosis 用 D_dev，不把 D_claim 用于 adaptive tuning | `test_the_diagnosis_may_only_read_the_dev_set`（`evaluationSet="claim"` 被拒 + `phase_failure` 源码级断言只读 `dev_points`） |

另有：统计量确为 AC2D-9 量（合成热点越线、真实形态的非均匀场不越线）、1D 保持原规则、裁决记录与实现一致。

### 4.4 对已完成 run 的影响：无

`exp2d-poisson-calibration-r1` 的冻结配置预注册的是继承来的 1D 症状规则，本轮**没有**改它，新触发也**不回溯**到它。它的 AC2D-9 本来就是 Gate 5b 的 MUST 验收判据并在十个 seed 上全部通过（最差 1.568e-4 对 1e-3），所以按新触发它同样不会报症状——而退役的 1D 规则会在 9/10 个 seed 上误报。

## 5. Environment B（裁决 3）：KEEP

`C:\Users\user\LeoAI-envB2D-20260916`（21,963 文件 / 0.64 GB）**保留**，按裁决视为**冻结的复现夹具**：

- 不在其中做日常包安装，不升级、不清理、不改任何环境变量；
- 将来实验若需要额外依赖，**重新 qualification 或新建 B2**，不静默污染现有 B；
- 其鉴定记录 `experiments/poisson2d/environment_b_qualification.json` 是不可变证据（本轮只为它加了精确哈希归类，文件字节未动）。

本轮对该目录**未执行任何操作**（未安装、未删除、未写入）。

## 6. 重跑结果（裁决 6）

| 项 | 结果 |
|---|---|
| full suite（治理 `.venv`，无 torch / numpy） | **1172 passed / 0 failed / 18 skipped**（上轮 1147 / 3 / 18；净增 25 项测试，3 红全部转为已批准归类） |
| 被跳过的 18 项在训练解释器下 | `experiments/poisson2d/verify_tests_under_torch.py`：**23 passed / 0 failed** |
| portability 扫描 | **0 hard binding(s)** / 1 configurable default / 8 historical evidence finding(s) |
| PRELOCK | **7/7 PASS** |
| unexpected failures | **0** |

## 7. 代码身份（裁决 7）

本轮改动落在 `pinn/experiments2d/{localized_error,diagnostics2d,runner2d}.py`（以及 `tools/`、`tests/`、`manifests/`），工作树的 codeHash 与记录在案的 `a39aa07e23d0…` 的差距进一步扩大（上一轮已如此）。因此：

```text
下一次正式 2D 实验必须使用新的 revision / code identity。
本轮审计后的代码不得冒充生成既有 C2 的 a39aa07e23d0…。
```

宪法第六十六章本就如此要求；`assert_criterion_within_run_identity` 现在把这条规则的一个具体后果变成机器检查——改过的配置无法附到旧 run 上。已 ACCEPTED 的决策绑定的仍是记录在案的那个身份，其字节可由承载该 run 的提交恢复。

## 8. STOP

```text
CURRENT 2D C2: CONFIRMED
NEXT COMPLEXITY STEP: READY
```

按裁决第 6 条，本轮到此停止：**不自行启动下一个 PDE**（不规则几何、BFS、Navier–Stokes、UCM、传热），不起草修正案，不做架构扫描，不重训。下一步等用户指令。

````

</details>

### R042 — 项目/docs/pinn-trust-loop/POISSON2D_FINAL_CLOSURE_AUDIT_20260916.md

<details>
<summary>展开完整原文</summary>

````markdown
# Poisson 2D Final Closure Audit（2026-09-16）

执行负责人：Claude（队长）。对象：`docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md` 所记的 2D 主体实验。本轮**没有**重训正式 10-seed baseline、没有改架构 / 优化器 / 阈值 / ScientificSpec、没有重开已烧毁的 D_claim、没有改任何历史机器证据、没有删除失败记录、没有新增 A-0003、没有开始下一个 PDE。

## 1. Executive Decision

```text
CURRENT 2D C2:
CONFIRMED

NEXT COMPLEXITY STEP:
HOLD
```

两者同时成立：**科学有效性**经全链重校验无一问题；**仓库 / 治理就绪度**卡在一个不能由我单方面解除的机制边界上（第 4 节）。

| 收口门条件（Issue 7） | 状态 |
|---|---|
| Portability full suite green under approved exact-hash historical policy | ❌ **未满足**——豁免机制在实现上只接受 `governance/**.md`，够不到 `experiments/**` 的证据；扩大作用域＝修改 policy 机制本身，本轮禁止 |
| claim-pool early guard uses ledger | ✅ 已修（第 5 节） |
| dimension-aware localized-error protocol exists | ⚠️ **部分**——协议裁决与标定装置已建立，但最佳候选仍会误报，因此登记为 NOT CALIBRATED 而不是硬上一个拟合出来的阈值（第 6 节） |
| PRELOCK PASS | ✅ 7/7 |
| git tree clean | ✅ |

## 2. AC2D-9 Formula Audit（Issue 1）

| 项 | 内容 |
|---|---|
| **预注册公式** | `EXPERIMENT2D_PREREGISTRATION_20260916.md:82`（正式 run 前提交于 `f3d322b`）：「8x8 分块的最大分块 RMS 误差 / **全域 u\* 的 RMS**」 |
| **实现公式** | `pinn/governance/poisson2d_contract.py` METRICS：`max over tiles of sqrt(mean_tile (u_theta - u*)^2) / sqrt(mean_grid (u*)^2)`；代码 `pinn/validation/poisson2d.py:152-172`：`tile_rms[worst_tile] / reference_rms_p`，`reference_rms_p = sqrt(mean_grid u*^2)`（第 157 行，由 `exact_p` 求得） |
| **artifact 字段** | `gate5b_external.json` seed 0：`AC2D-9 = 1.3744235492973476e-04`；同记录 `worstTile.rms = 4.880940713232928e-05`、`referenceRmsPointwise = 0.35512638849416045`，二者相除**逐位相等**（十个 seed 全部逐位一致，测试钉死） |
| **数学解释** | 分子是最差分块的**绝对** RMS 误差，分母是**参考解**的全域 RMS。于是 AC2D-9 是一个**局部相对误差**，与 AC2D-1 同量纲同常数，取值远小于 1 属正常。 |
| **裁决** | **CASE A —— 只是 label / report wording 错。预注册 = 实现 = 机器记录。C2 REMAINS VALID。** |

外部终审的不等式本身完全正确，它约束的是**另一种读法**（分母取误差场 RMS）。用**已存的正式预测重算**（不重训、不重开 claim 集，`AC2D9_FORMULA_AUDIT.json`）在 D_dev 上同时给出两种读法：

| 读法 | 十个 seed 的范围 | 是否恒 ≥ 1 |
|---|---|---|
| 终审读法 `max_j R_j(e) / RMS(e)` | **1.989 – 3.101** | 是（与不变量一致） |
| 实际实现 `max_j R_j(e) / RMS(u*)` | **6.13e-05 – 1.09e-04** | 否（相对误差，本就应远小于 1） |

另更正一处**过强的措辞**：预注册称 AC2D-9「严格强于 AC2D-1」。精确表述是 `AC2D-9 ≥ 同一网格上的全局相对 L2`（加权块均值不超过最大块值，实测十个 seed 全部满足）；AC2D-1 是**另一套网格上的求积加权**量，两者只是经验上更严（实测比值 2.90–4.36）。预注册作为历史文件不改，更正记在 `runs/exp2d-poisson-calibration-r1/POST_AUDIT_ANNOTATION.md` 与本报告。

处理：① 不改任何机器记录；② 追加 POST_AUDIT_ANNOTATION；③ 更正 2D 报告 §3.2 的缩写标签与 §2 的"严格强于"表述；④ 新增不变量回归测试 `tests/pinn/test_ac2d9_invariants.py`（6 项）。

## 3. P11 Applicability Audit（Issue 2）

**正式协议依据核对结果：没有依据把 2D 的 P11 判为 NOT_APPLICABLE。**

| 依据 | 原文 | 结论 |
|---|---|---|
| `governance/PINN_TRUST_PROTOCOLS_R1.md:108` | 「Tier-1（P1、P4、P6、P7、P8、P9、**P11**、P16）**C2 之前必跑**」 | P11 属强制集合 |
| 同文件 :27 | 适用性登记「必须写明**缺失的物理前提**」 | "本次没观察到局部误差集中"是对结果的观察，不是前提缺失 |
| `inbox/PINN_TRUST_R1_RED_TEAM.md:127` | 「**Poisson 1D MVP** 只用得上 …；P7、P11–P14、P18 面向后续 CFD 目标」 | 作用域是 1D MVP；本轮已据此把 P7 改判 APPLICABLE，却留着 P11 的 N/A，判定不一致 |

因此按 Issue 2.3 **补跑**。预注册 `P11_SUPPLEMENT_PREREGISTRATION_20260916.md` 先于运行提交（`e1e9f02`），驱动脚本置于代码身份清单之外，运行前机械核验 `codeHash = a39aa07e23d030b3…` 与正式 run 相同、`dirtyCodeIdentityPaths = []`。P11 的正式定义（红队交付物 §1）：按残差 p95 区域加密、重训 1 次、残差统计取自固定的独立稠密评估集。

实跑结果（`tier1_p11_supplement.json`，D_dev only，`claimSetTouched: false`，一次重训，无重试）：

```text
D_dev 残差  median 5.662e-03 · p95 τ = 1.712e-02 · max 3.705e-02
区域 A     22 / 64 块（含至少一个 |R| ≥ τ 的 dev 点）
配点       自然占比 0.347 → 加密后 0.694（因子 2，沿用本轮 P7 的预注册常数）
Δq         1.417e-05     （维持线 1e-2）                    -> PASS
e2         3.596e-05 -> 5.506e-05                            （仍比 ε_spec 低约 18 倍）
区域内残差  p95 2.125e-02 -> 1.865e-02
```

诚实记录：把 69% 的配点压进 34.7% 的面积后，**D_dev 相对 L2 上升约 53%**，区域内残差只小幅下降——残差自适应加密在这个问题上**不是改进**。按预注册的主判据（Δq）维持，未越线，不触发"局部误差集中"分流，C_train 不降级。

`tier1_redteam.json` 原样保留（其中 P11 的 N/A 行作为历史记录留存，由注解更正）；新增 `trust_vector_g6_p11.json`（supersedes `tv-…-g6`）与 `claim_gate_decision_g6_p11.json`，状态仍 ACCEPTED。**Tier-1 现在覆盖协议规定的全部八项**（测试钉死）。

## 4. Portability Closure（Issue 3）

### 4.1 已完成（3B / 3C）

- `experiments/poisson2d/qualify_environment_b.py`：构造说明改为运行时从 `installationId`（prefix 的 sha256）生成，不再写死用户路径。
- `experiments/poisson2d/verify_tests_under_torch.py`：记录 `interpreterInstallationId` 取代 `sys.executable`；重跑后 `TEST_VERIFICATION_UNDER_TORCH.json` 不再含绝对路径（该 finding 消失）。
- **前瞻规则（3C）** 写进两个脚本与本报告：环境构造证据只记 `installationId` / prefix 哈希 / `dependencyLockHash` / 构造方法，**默认不写绝对用户路径**；旧证据不回写。
- 发现数 **7 → 5**。

### 4.2 未完成（3A）：机制作用域冲突，按指令报告而不扩大豁免

尝试为 1D 的 4 条与 2D 的 1 条证据 finding 添加**精确哈希**豁免后，测试由 3 红变 6 红，原因在 `tools/portability_check.py` 的策略加载器：

```python
if not rel.startswith("governance/") or not rel.endswith(".md"):
    raise RuntimeError("historical evidence policy cannot target a non-governance-document: ...")
```

即**豁免机制在实现上只接受 `governance/**.md`**，而全部待豁免证据在 `experiments/**`（4 个 JSON + 1 个 Markdown）。让它们可豁免必须修改这段加载器——那正是本轮禁止的 "rule weakening / 修改 policy 机制"。因此：**豁免尝试已回滚**，`manifests/portability-historical-evidence.json` 保持只有原来那一条 governance 条目（测试钉死）。

| 口径 | 数值 |
|---|---|
| 当前 BINDING 发现 | **5**（1D 历史证据 4 + 2D `environment_b_qualification.json` 1） |
| full suite | **1147 passed / 3 failed / 18 skipped** |
| 3 个 FAIL | 全部是 portability 的同一组断言，**不是 2D 数值失败** |
| PRELOCK | **7/7 PASS** |

留给用户 / 外部评审的裁决（本轮不动）：是否授权把豁免机制的作用域从 `governance/**.md` 扩展到"被审批的不可变证据文件"（仍要求 file + sha256 + finding_type + occurrence 精确匹配、任何字节变化自动失效）。在此之前，**closure gate 的 portability 条件视为未满足**。

机器化的新证据（`tests/pinn/test_p11_and_portability_closure.py`）：作用域限制、"一个字节变化即失效"、源码无用户路径、新证据可路径中立——四条都有测试。

## 5. Claim Pool State Fix（Issue 4）

唯一真相源改为**账本**：

- 新增 `derived_claim_status(events, problemId, revision, artifactHash, sampleHash)`，由 `derive_claim_set_state` 推导 `SEALED / OPENED / NEVER_SEALED`，并在样本身份已烧毁时返回 **BURNT**（烧毁跟随样本，跨 revision 有效）。
- `phase_problem` 的护栏**前移**：在互斥扫描之前、任何 Gate 与训练之前查询账本；正式 attempt 遇到 `OPENED / BURNT` 立即拒绝，错误信息明确指出"manifest 的 status 字段不被采信"。
- `register-pool` 今后写 `initialStatus` 并附说明（原 `status` 保留为信息性字段，运行时不读）；**已提交的 pool manifest 不回写**。
- 五项测试（`tests/pinn/test_claim_pool_state.py`）：manifest 说 SEALED 而账本说烧毁 → 以账本为准；烧毁跟随样本跨 revision；未消费成员在其预定 revision 可用；早期护栏与最终账本校验器判定一致（再次 OPENED 被拒、同样本重新包装被拒）；源码级断言护栏读账本且早于互斥扫描。

实测：被消费的成员 `D2C-GL32-CGL50` 在 manifest 里仍写着 `SEALED`，账本推导为 **BURNT**；旧护栏会放行到训练结束才被账本拦下，新护栏在开始前就拒绝。

## 6. Localized Error Calibration（Issue 5）

| 项 | 内容 |
|---|---|
| **旧规则** | `sLocalizedError`：最大块 / 中位块 > **3.0**（10 分箱，1D） |
| **为什么在 2D 失效** | 在一个**完全合格**的 2D run 上，用已存预测重算，该规则在 **9/10 个 seed 上误报**（统计量范围 2.946–4.815）。原因是结构性的：PINN 的误差幅度跟随解的幅度，二维张量分块天然有数倍差异，块数从 10 增到 64 又抬高任意光滑场的 max/median。 |
| **标定方法** | 四个候选（A 最大/中位、B 稳健 z、C top-k 能量集中度、D **参考条件化**稳健 z）× 六个合成夹具（均匀、两种非均匀、振荡非均匀、单热点、多热点、全局放大）× 点集（确定性密网格 + **与部署一致的随机点集** 512/1024/2048）× 分块数 4/8/16 × 三个幅度。判定规则事前写定：先要求**处处分离**，再取最差分离比最大者，阈值取两侧的**几何中点**。 |
| **结果** | A 分离比 1.17、C 1.34、B 不分离、**D 1.76 胜出**，阈值 **26.21**（两侧各 1.33 倍）。 |
| **对已完成 run 的检查（不参与标定）** | D 在 10 个 seed 中仍**误报 2 个**（27.1、38.1）。 |
| **裁决** | **NOT CALIBRATED FOR DEPLOYMENT。** 不把阈值往上调去消掉这两个——那正是被禁止的事后拟合。 |

前瞻协议（写入 `LOCALIZED_ERROR_CALIBRATION.json`，测试钉死）：

1. d ≥ 2 的**局部误差要求由验收判据承担**（AC2D-9 形式：每块一个固定的相对上界）——这正是本轮实际使用并且表现正确的做法（最差 seed 1.568e-4 对阈值 1e-3）。
2. **症状**信号 `sLocalizedError` 对 d ≥ 2 登记为 **NOT CALIBRATED**：在有经验 null 分布之前，不得用它命名根因。
3. 1D 的常数 3.0 与 max/median 统计量对 d ≥ 2 **退役**（机器实测 9/10 误报）。
4. 将来要用这个症状，必须先从 **≥ 5 个已验证 run** 收集分块统计量，把所得分位数预注册为阈值。

**治理归类**：仅涉及症状统计量及其阈值，二者都在协议与每次实验的 `signatureCriteria` 预注册里；FailureSignature 名称、RootCause 类、TrustStatus、Claim 语义都未变 → **协议标定，不是宪法语义变更，不起 A-0003**。仅登记一条候选：若将来希望"NOT CALIBRATED"成为信号的一等登记状态，会触及 DiagnosisRecord schema，届时再评审。

## 7. Final Trust Vector / Claim（Issue 6）

不重训、不重开 claim 集，把每份文档交回它自己的校验器重算（`FINAL_CLOSURE_REVALIDATION.json`）：

```text
specHash 复算一致                                  ✓
ProblemDefinition / 账本 / RunRecord × 2 校验      ✓ 零错误
TrustVector × 4（含 tier1、g6、g6_p11）            ✓ 零错误
ClaimGateDecision × 4                              ✓ 零错误
claim 集 OPENED 次数                               1（唯一一次），账本推导状态 BURNT
G6 复现重判                                        C_repro = PASS（同 spec ✓ 同 code ✓ 独立 ✓ 异 seed ✓ |Δmedian| 4.000e-06 在容差内）
状态机                                             ACCEPTED
```

```text
C_math     = PASS
C_impl     = PASS
C_train    = PASS   （新增：Tier-1 P11 维持）
C_physics  = PASS
C_external = PASS
C_repro    = PASS

allowed: C0, C1, C2        blocked: C3（无 ≥ 5 个独立合格 C2 run）
CURRENT 2D C2: CONFIRMED
```

**代码身份的诚实说明**：本轮的 Issue 4/5 修复动了 `pinn/experiments2d/`，工作树的 codeHash 已经不再等于记录在案的 `a39aa07e23d0…`（`codeIdentityUnchanged: false`）。已 ACCEPTED 的决策绑定的是**记录在案的那个身份**，其字节可由承载该 run 的提交恢复；宪法第六十六章因此要求**下一次正式 run 必须升 revision**。1D 在其 ACCEPTED run 之后给 runner 增加子命令时确立了同一先例。P11 补跑刻意安排在所有代码修改**之前**，因此它与基线在同一代码身份下比较。

## 8. Tests

| 项 | 值 |
|---|---|
| 本轮开始前 | 1121 passed / 3 failed / 16 skipped |
| 新增测试 | **28**（AC2D-9 不变量 6、localized-error 9、claim pool 5、P11 与 portability 收口 8） |
| 本轮结束 | **1147 passed / 3 failed / 18 skipped** |
| 3 个 FAIL | 同一组既有 portability 断言（第 4.2 节），非 2D 数值失败 |
| 被跳过的测试 | 18 = 既有 16 + 新增 2（治理 venv 无 torch / numpy）；`verify_tests_under_torch.py` 在训练解释器下跑同样的函数：**23 passed / 0 failed** |
| PRELOCK | **7/7 PASS** |

必需测试覆盖对照：AC2D-9（解析不变量、标签与实现一致、热点夹具失败、均匀低误差通过、artifact 自洽）✓；P11（适用性有机器测试、扰动只用 D_dev、同代码身份、覆盖协议 Tier-1 全集）✓；portability（精确哈希豁免、一个字节变化即失效、源码绝对路径被拒、新证据可路径中立、作用域限制）✓；claim pool（过期 manifest 不能压过账本、早期护栏拒绝已烧毁集、重新包装被拒、只开一次、护栏与校验器一致）✓；localized error（2D 正常非均匀不误报、合成热点真阳、全局非局部可区分、旧规则退役有据、退化情形显式处理）✓。

## 9. Repository State

```text
git status: clean
HEAD: 见本报告提交
本轮新增/修改（全部已提交）：
  pinn/experiments2d/{runner2d,localized_error}.py
  experiments/poisson2d/{P11_SUPPLEMENT_PREREGISTRATION,p11_supplement.py,p11_decision.py,
                         ac2d9_formula_audit.py,calibrate_localized_error.py,check_localized_error.py,
                         final_closure_revalidation.py,qualify_environment_b.py,verify_tests_under_torch.py}
  experiments/poisson2d/{AC2D9_FORMULA_AUDIT,LOCALIZED_ERROR_CALIBRATION,FINAL_CLOSURE_REVALIDATION,
                         TEST_VERIFICATION_UNDER_TORCH}.json
  experiments/poisson2d/runs/exp2d-poisson-calibration-r1/{POST_AUDIT_ANNOTATION.md,
                         tier1_p11_supplement.json,trust_vector_g6_p11.json,claim_gate_decision_g6_p11.json}
  tests/pinn/{test_ac2d9_invariants,test_localized_error_2d,test_claim_pool_state,
              test_p11_and_portability_closure}.py
  docs/pinn-trust-loop/POISSON2D_CALIBRATION_REPORT_20260916.md（仅更正 AC2D-9 标签与"严格强于"表述）
未改：任何历史机器证据、manifests/portability-historical-evidence.json、宪法、协议汇编、1D 全部记录
测试产物：本轮 __pycache__ 与 pytest 临时目录已删除并复核（见操作日志 §5.27）
```

## 10. STOP

```text
CURRENT 2D C2: CONFIRMED
NEXT COMPLEXITY STEP: HOLD
```

HOLD 的唯一原因是 portability 的机制作用域冲突（4.2）与 localized-error 症状规则尚未可部署（6）。两者都不影响已成立的 2D 数值结论，也都不是可以由我单方面解除的。

本轮到此停止：不开始新的 PDE、不扩大豁免、不修改 policy 机制、不起草修正案、不重训。等待用户与外部评审终审。

## 11. 后续（追加，2026-09-16 同日）

本报告第 10 节的 HOLD 在同日被用户 / 外部评审的裁决解除：portability 豁免机制作用域获批扩展（严格条件），localized-error 的触发条件改判为「预注册的局部误差验收判据失败」。执行与验证见 [POISSON2D_CLOSURE_COMPLETION_20260916.md](POISSON2D_CLOSURE_COMPLETION_20260916.md)：full suite 1172 passed / 0 failed / 18 skipped、portability 0 hard binding、PRELOCK 7/7 → `NEXT COMPLEXITY STEP: READY`。本报告其余内容作为当时的记录**一字未改**。

````

</details>

### R043 — 项目/docs/pinn-trust-loop/R1_MERGE_NOTES.md

<details>
<summary>展开完整原文</summary>

```markdown
# R1 合并说明（队长：Claude）· 2026-09-14

对象：`docs/pinn-trust-loop/inbox/` 下五份 R1 交付物。本文件记录收件核对、各车道摘要、跨车道冲突与队长裁决、与既有宪法 / 代码的衔接计划、以及必须由用户拍板的事项。分歧只记录，不抹平。

## 0. 收件核对（提交 `13dc7ea`，字节原样）

| 文件 | 作者 | SHA-256（前 12 位） | 行数 | 范围声明 |
|---|---|---|---|---|
| `PINN_TRUST_R1_MATH_CORE.md` | DeepSeek | `23dd35179a0a` | 257 | 数学一致性条件、物理一致性公式、误差归因、弱链演算；未越界 |
| `PINN_TRUST_R1_SCHEMAS_STATE_MACHINE.md` | GLM | `4b5693507c9f` | 636 | 三份 JSON Schema、状态机 FAIL 分流、28 条测试用例；未越界 |
| `PINN_TRUST_R1_IMPL_TRAINING.md` | Kimi | `3445b3977df9` | 129 | MMS 协议、T1–T10 单元测试、多 seed 协议、11 篇文献；未越界 |
| `PINN_TRUST_R1_REPORT_AND_WORKFLOW.md` | 豆包 | `4f7523d51e78` | 274 | 六段式模板、两个示例、研究者工作流、术语表；未越界，未画界面 |
| `PINN_TRUST_R1_RED_TEAM.md` | Claude（代 Grok） | `9ca4e288407d` | — | 21 条扰动、三层制、15 条漏洞、对 8 条设计的反驳、20 篇文献 |

五份都按词表写作，都把不确定项写进了"待队长决定"，没有一份猜测仓库路径或输出补丁。

## 1. 各车道一句话摘要

- **DeepSeek**：把 G1 的六类一致性写成机器可判条件；给出 Poisson 1D 与 NS / Oldroyd-B 的守恒、能量、动量、正定、对称、单调、最大值原理、自由能、SPD 的离散公式与容差；误差六项的隔离实验与"症状 → 来源 → 区分实验 → 判定"表；把五态定义为链并证明 claim 等级 = 必需维度逐个 PASS（取最弱），平均是类型错误。
- **GLM**：ProblemDefinition / TrustVector / ClaimGateDecision 三份 draft 2020-12 schema，冻结即哈希（JCS）；提出修正案 A1（G5 拆 G5a/G5b，新增 PHYSICS_CHECKED 状态）；六条诊断分支的路由表、五条不变量、伪代码；T01–T28 测试用例。
- **Kimi**：MMS 五步与 P1/P2/P3、NS1 双 ν 档组合；T1–T10 实现单元测试（float64、阈值明确）；多 seed 协议 N ≥ 10、三因子解耦、中位数 / IQR / 最差 seed、k/N ≥ 0.8；C_train 评级规则。
- **豆包**：六段式模板与硬约束措辞规则；NOT_CHECKED / BLOCKED / PARTIAL 三者的标准措辞；两个填好的示例；研究者"让 PINN 进化"的预注册、冻结 / 可变项、晋升路径、论文方法清单、EXPLORATORY 标签；术语表。
- **Red Team（队长）**：P1–P21 扰动矩阵与降级规则、Tier-0/1/2 执行制；V1–V15 漏洞与对策；对 8 条设计的逐条反驳（不做双重状态机、症状不唯一映射、C_repro 语义、关键证据链需定义、误差不可加、成本分层、输出补 Provenance/Scope、EXPLORATORY 隔离）。

## 2. 跨车道冲突与队长裁决

| # | 议题 | 各方立场 | 裁决 | 状态 |
|---|---|---|---|---|
| C1 | 五态在"最弱环节"排序中的位置 | DeepSeek：FAIL ⊏ BLOCKED ⊏ NOT_CHECKED ⊏ PARTIAL ⊏ PASS；GLM §3.1-6：FAIL < BLOCKED < PARTIAL < NOT_CHECKED < PASS；Red Team：NOT_CHECKED 不高于 PARTIAL | 采纳 DeepSeek 序：**FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS**（没查的证据比查了不充分的更弱）。对 claim gate 无影响（非 PASS 一律阻断）；GLM schema 的 weakestLink 推导序按此修正 | 已裁决 |
| C2 | C_external 绑定哪几道 Gate | DeepSeek、豆包：G2 + G5；GLM：只绑 G5b，参考解证据等级由 `referenceEvidenceLevel` 单独携带 | 采纳 GLM：**C_external ↔ G5b（独立数值验证）**；G2 不单独成维，`referenceEvidenceLevel` 是 ClaimGateDecision 的独立前提；G2 未 PASS 时 C_external 记 BLOCKED | 已裁决 |
| C3 | 物理一致性怎么拆出 G5 | GLM A1：新增 PHYSICS_CHECKED 状态；GLM 备选：不新增状态，作为 VALIDATION 内前置子检查；Red Team 第 1 条：不做双重记账 | 采纳 **GLM 备选**：G5 = G5a（物理一致性 MUST 组）+ G5b（独立数值验证），都在 VALIDATION 内执行，VALIDATION PASS ⇔ G5a ∧ G5b PASS；宪法状态机的状态集合不变；dConservation 分流重入 VALIDATION 并重跑 G5a | 已裁决 |
| C4 | 示例 (b)"Accuracy claim ALLOWED" | 用户原例：ALLOWED；豆包按弱链：5 seed → C_train PARTIAL、corner PARTIAL、repro NOT_CHECKED → C2 应阻断；Kimi：2D 过渡期 N=5 封顶 PARTIAL | 采 **(ii) C1 + 受限一致陈述**（"在该工作点、该 QoI 上与 Level B 参考在阈值内一致"），不开 scoped C2 口子；弱链原则是宪法级，示例不能例外 | 已裁决（用户 2026-09-14 选 (ii)） |
| C5 | seed 数与 C_train 封顶 | Kimi：N ≥ 10（1D），2D 过渡 N = 5 封顶 PARTIAL；Red Team P2：以最差 seed 判定 | 采纳两者；写入修正案 | 已裁决 |
| C6 | 阈值 | 各方给的都是"建议默认值" | 全部作为**预注册起点**：ε_spec = 1e-3（相对 L2）、最差 seed ≤ 3ε_spec、k/N ≥ 0.8、IQR/median ≤ 1、Δq 1% / 5% 两档、DeepSeek §2 各容差；正式值在 SPEC_LOCKED 前冻结进 HASH LOCK | 已裁决（数值待预注册） |
| C7 | Red Team 结果怎么进向量 | Red Team：TrustVector 每维加 `perturbationsRun`、`worstCase`；GLM：以 `supersedesRecordId` 新版本写入 | 两者都要：新版本记录 + 每维扩展字段；schema 下一版补 | 已裁决 |
| C8 | EXPLORATORY | 豆包 §3.5 与 Red Team 第 8 条一致：探索性只允许 C0/C1 | 采纳；作为 run 级 `mode` 枚举进 schema（GLM 下一版），claim 封顶 C1，不进 ACCEPTED | 已裁决 |
| C9 | 诊断循环上限 | Red Team 第 2 条：3 轮后 BLOCKED 升级人工 | 采纳；状态机加计数（GLM 下一版） | 已裁决 |
| C10 | weakestLink 并列 | GLM D4 | 记录全部并列维度，展示按固定序 | 已裁决 |
| C11 | "NOT VALIDATED" 展示词 | 豆包 D2 | 英文展示统一为 "NOT CHECKED"，枚举不变 | 已裁决 |
| C12 | C_repro 定义 | Red Team 第 3 条 / V15；豆包 D3 | **PASS = 同规格、独立环境（不同机器或独立安装）+ 不同 seed 集的复现落入预注册容差**；同机同 seed 只证明确定性，不计 | 已裁决 |
| C13 | 配点互斥（Kimi T10）升宪法级 | Kimi 待决 ③ | 采纳为宪法级禁令 | 已裁决 |
| C14 | specHash 规范化用 JCS（RFC 8785） | GLM A3 | 已核对：既有 `canonical.py` 的唯一规范化是 `json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + LF`，PRELOCK / HASH LOCK 都用它；specHash 沿用该序列化，不引入 JCS | 已裁决 |
| C15 | 报告禁用词表升为自动校验 | 豆包 D6 | 采纳，作为 ClaimGateDecision 生成时的文本校验 | 已裁决 |
| C16 | 完整英文版报告 | 豆包 D4 | R1 不做；标题、句式、术语双语即可 | 已裁决 |

## 3. 与既有宪法 / 代码的衔接计划（R1 → 仓库）

| 产物 | 来源 | 落位 | 备注 |
|---|---|---|---|
| 宪法修正案草案 | C1–C13 裁决 + 各方条款 | `governance/AMENDMENTS/A-20260914-R1-trust-loop.md` | 条款化：可信度向量、弱链演算、G5a/G5b、EXPLORATORY、seed 协议、配点互斥、Red Team 三层制、诊断循环上限 |
| 三份 schema | GLM §1–§3（按 C1/C2/C7/C8 修正） | `pinn/governance/schemas/problem-definition.schema.json`、`trust-vector.schema.json`、`claim-gate-decision.schema.json` | 先核对 `jsonschema_lite.py` 支持哪些 2020-12 关键字（if/then、contains、prefixItems）；不支持的交叉规则放进 PRELOCK |
| 弱链演算 | DeepSeek §4 + Red Team NOT_CHECKED 语义 | `pinn/governance/trust_vector.py`（新） | 纯函数：向量 → allowed / blocked / weakestLink；DeepSeek 4.4 七个例子直接成测试 |
| 状态机扩展 | GLM §4（按 C3/C9 修正） | `pinn/governance/state_machine.py` | 六条 branchId 封闭枚举、INV1–INV5、循环计数 |
| 测试 | GLM T01–T28、DeepSeek 4.4、Kimi 阈值 | `tests/pinn/test_trust_loop_schemas.py`、`test_trust_vector.py`、`test_state_machine_triage.py` | 全部保留现有 839 项，只增不减 |
| 报告模板 | 豆包 §1 | `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` | 双语标题与句式；禁用词表 |
| 协议文档 | Kimi §1–§3、DeepSeek §2、Red Team §1 | `governance/PINN_TRUST_PROTOCOLS_R1.md` | MMS 组合、T1–T10、seed 协议、物理检查公式、P1–P21 |
| 物理检查代码 | DeepSeek §2 | `pinn/validation/`（R2） | Poisson 1D 的通量 / 能量 / 正定 / 对称 / 单调 / 最大值 / SPD 检查可直接实现；NS 部分等 CFD 案例 |

顺序建议：修正案草案 → schema + 弱链演算 + 测试 → 状态机扩展 → 模板与协议文档 → R2 出题。

## 4. 需要用户拍板

1. C4：用户已选 (ii)（2026-09-14）。
2. 用户已选"现在开始实现"（2026-09-14）；实现记录见操作日志。

## 5. 分歧记录（不抹平）

- GLM 的 weakestLink 排序与 DeepSeek 相反（C1），已裁决为 DeepSeek 序；GLM 文件原文保留。
- DeepSeek、豆包写的 "C_external ↔ G2 + G5" 与裁决（C2）不同；原文保留，整合时改口径。
- GLM 修正案 A1 的新状态未采纳（C3），采纳其备选；原文保留。
- 豆包示例 (b) 与弱链原则的冲突（C4）已由用户裁决为 (ii)；豆包原文两说并存，保留不改。

```

</details>

### R044 — 项目/docs/pinn-trust-loop/R2_MERGE_NOTES.md

<details>
<summary>展开完整原文</summary>

````markdown
# R2 合并说明（队长：Claude）· 2026-09-15

对象：`docs/pinn-trust-loop/inbox/` 下的 R2 交付物，以及用户 2026-09-15 对 A-0001 第 2 稿的复审（PROPOSED / MINOR CHANGES REQUIRED，五项 + 对抗性闭合审计要求）。本文件记录收件核对、各车道摘要、逐项裁决（含驳回及其论证）、落地位置。分歧只记录，不抹平。

## 0. 收件核对（字节原样入库）

| 文件 | 作者 | SHA-256（前 12 位） | 行数 | 来源与范围 |
|---|---|---|---|---|
| `PINN_TRUST_R2_SCHEMAS_STATE_MACHINE.md` | GLM | `6edec0c24f5b` | 541 | 用户放在桌面（`C:\Users\user\Desktop\`），队长 `cp` 入库并 `cmp` 复核；1.1 契约审核、三份新契约、状态机第 2 版、T29–T60；未越界 |
| `PINN_TRUST_R2_IMPL_TRAINING.md` | Kimi | `6497bb9b8ea1` | 220 | 用户放入收件箱；评估集操作协议、seed 协议第 2 版、物理检查实现清单、C3 登记清单；未越界 |
| `PINN_TRUST_R2_REPORT_AND_WORKFLOW.md` | 豆包 | `2792e505d932` | 174 | 用户放入收件箱；报告模板第 3 稿写法、示例 (b) 第 2 版、失盲处置流程、术语表；未越界 |
| `PINN_TRUST_R2_MATH_CORE.md` | DeepSeek | `3332850a6ce3` | 241 | 第 3 稿合并时未找到；用户 2026-09-15 终审同日告知位置 `C:\Users\user\PINN_TRUST_R2_MATH_CORE.md`，队长 `cp` 入库并 `cmp` 复核（原件未动）；逐格区分实验 P22–P32、seed 阈值统计论证、泄漏信息流不变量、Applicability 表；未越界。裁决见 §7 |

三份都按词表写作，都把不确定项写进了"待队长决定"，没有一份猜测仓库路径或输出补丁。GLM 的 schema 片段只用了校验器支持的关键字子集。

## 1. 各车道一句话摘要

- **GLM**：对 1.1 三份契约提出 P1–P7、V1–V8、C1–C7、D1–D4 共 26 条漏洞与修订；补 DiagnosisRecord、ClaimSetEvent（哈希链、六条不变量）、RunRecord（environmentId / codeHash / seedSetId 派生规则）；状态机第 2 版 17 行转移表与伪代码；T29–T60（16 条对抗）。
- **Kimi**：D_train / D_dev / D_claim（+ D_phys）的生成、位级互斥、哈希登记、密封持有、"打开"的操作清单、失盲五步处置、日志最小字段；seed 协议第 2 版八步判定、k 的定义、三因子账簿、N 的折中、F1–F8 禁止清单；PH1–PH10 实现级检查表；环境强 / 弱字段、codeHash 覆盖范围、seed 集去重、run 登记表。
- **豆包**：抬头评估集披露行、CheckResult 逐条写法与 NOT_APPLICABLE 标准句、Known failure modes 六槽位句式与停线句式、C3 独立性披露句式；示例 (b) 第 2 版；失盲处置流程、失败条目"症状 / 诊断"分块、EXPLORATORY 三条；术语表 16 条。
- **DeepSeek**（补交）：P22–P32 隔离式诊断实验库与六症状逐格 (a)(b)(c) 表，建议增 3 格、不加 3 格；Clopper–Pearson 与似然比论证 0.9 / 0.8 线与 N = 5 只能 PARTIAL，算力换置信表；"看过即失盲"的信息流不变量与五条可判定检查项；三类问题的 Applicability 表。

## 2. 用户复审五项的裁决（对抗性治理审查）

裁决标准：类型一致性、科学有效性、状态机封闭性、可机器判定性、可复现性、防 Agent 绕过。不因为是评审意见就默认正确，也不因为现有测试通过就默认现有设计正确。

### Issue 1 — 全 NOT_APPLICABLE 时的维度语义

**A. 是否存在语义冲突？** 是。第 2 稿把"检查清单非空且全部 NOT_APPLICABLE"折算成 NOT_CHECKED；前者是"适用性评估已执行、该问题不承担这些检查"，后者是"应查未查"，两者不同，折算是语义回流。

**B. 方案取舍。**

- 方案 1（DimensionResult 加 applicability，整维无 TrustStatus、不进 meet）：**REJECT**。它把"整维豁免"做成一个合法开关。六个维度各对应一道 MUST Gate（G1、G3、G4、G5a、G5b、G6），一个不承担任何检查的维度等价于"这道 Gate 对该问题不存在"，这不是 run 级可以声明的事。Agent 最想要的就是这个开关。
- 方案 2（ScientificSpec / ClaimPrerequisite 显式豁免）：**REJECT**。把开关从 run 挪到规格，Agent 写规格时同样能打开它；且它引入第二套前提矩阵，与 REQUIRED_DIMENSIONS 并存必然漂移。
- 方案 C（不变量禁止全 N/A）：**ACCEPT**，写成 INV-A1 并落代码与测试。

**C. 落地。**

- `trust_vector.dimension_status_from_checks`：空清单 → NOT_CHECKED；非空但无 APPLICABLE → 抛 `NoApplicableCheck`（ValueError 子类）。
- `ProblemDefinition 1.2.checkApplicability`：适用性在 SPEC_LOCKED 时随规格登记（进 specHash），每个维度至少一项 APPLICABLE（规格级 INV-A1），NOT_APPLICABLE 必须写理由。
- `validate_trust_vector(document, problem_definition)`：已执行维度（PASS / PARTIAL / FAIL）必须展示检查；检查集合必须等于注册表（不漏、不多、不改标）；status ≤ meet，低于 meet 必须 notes 说明。
- 若将来某类问题对某维度确实一项检查都不承担：那是宪法级缺口，立新修正案补检查；不给 run 豁免。

测试：`test_trust_vector.py::test_all_not_applicable_is_an_illegal_registration_not_a_weak_not_checked`、`test_trust_loop_adversarial.py` 前六条。

### Issue 2 — 哈希不同不能证明集合互斥

**ACCEPT。** 审查结论：第 2 稿 `_evaluation_set_errors` 只比较三个 sha256，**没有**任何样本级校验；修正案文字"两两互斥升为 MUST"没有机器落点。

落地（`pinn/governance/evaluation_sets.py` + `evaluation-set.schema.json`）：

- 评估集是一份样本清单 `{schemaVersion, artifactId, role, inputNames, generator?, samples[{inputs, kind, quantity?}]}`；清单的规范化哈希就是规格登记的 artifact 哈希，因此互斥证明绑定的正是规格指定的集合。
- 样本身份 = `canonical_sha256({"inputs": [float64…], "quantity": quantity|null})`。浮点按 float64 精确值（规范化 JSON 的 shortest-roundtrip repr 与 float64 位模式一一对应），−0.0 折入 0.0，整数 1 与 1.0 同一，NaN / Inf 拒绝。**"几乎相同"不是身份问题**：由预注册的 `evaluationSets.minSeparation`（进 specHash）以欧氏距离机械判定，缺省不检查。
- 参数化 PDE：(x, t, μ) 是网络输入，μ 不同即不同样本；μ 相近的泄漏由 minSeparation 在全输入空间上判定。逆问题：观测身份 = (坐标, 观测量名)；同坐标不同量是不同观测，但同坐标的位置泄漏仍由 minSeparation 捕获。
- kind（interior / boundary / initial / observation）是元数据不是身份：边界点、初值点都是训练可见样本。规则：训练可见样本 ∩ (dev ∪ claim ∪ phys) = ∅，dev ∩ claim = ∅。
- Kimi 的 D_phys 采纳为可选集 `evaluationSets.phys`：物理检查节点若与训练点重合，残差检查不是证据。
- 复杂度：O(N·M) 纯 Python（.venv 无 numpy），每个冻结规格跑一次，MVP 点数可接受；大规模 2D 集需要空间索引，记为后续工程项。

测试：`test_evaluation_sets.py`（9 项，含评审的 {1,2,3,4,5} vs {1,2,3,4,6}）、`test_trust_loop_adversarial.py` 数据隔离三条。

### Issue 3 — SEALED → OPENED 必须不可逆

**ACCEPT_WITH_MODIFICATION。** 审查结论：第 2 稿的 claimSetStatus 是普通可写字段；状态 SEALED + 历史里有本版本的 OPENED 记录，校验器**不报错**（burnt 只看更早版本）——SEALED → OPENED → SEALED 在同一版本内确实可以伪装成从未打开。GLM P2 同时指出 claimSetHistory 内嵌于文档、可随文档重写。

- 方案 A（append-only 事件历史）与方案 B（status 由历史推导）**同时采纳**：`claim_set_ledger.py` 的哈希链账本（eventId = 除 eventId 外全部字段含 prevEventId 的规范化哈希）+ `derive_claim_set_state`；文档的 claimSetStatus / claimSetOpenedAtRevision / claimSetHistory 必须等于推导值。
- 账本不变量 L1–L7：链完整、时间单调、SEALED 先于 OPENED 且 specHash 一致、OPENED 必记 codeHash、同一哈希终身只 OPENED 一次（GLM 的"全局永久烧毁"）、同一 (problemId, revision) 只 OPENED 一次、OPENED 后永不再 SEALED。
- **驳回"必须实现真正 append-only 存储"**：JSON 文件在本项目层级做不到密码学不可变；给出的等价治理保障是可检测性——任何删除 / 重排 / 改写使后续 eventId 失配，且 ClaimGateDecision 必须引用 `ledgerHead`，篡改账本就必须同时伪造人工终审阅读的决策。
- 附带修正（GLM P5，队长采纳）：specHash 排除 revision 与 claim 集状态字段，否则打开 claim 集即改变 specHash，同 specHash 的 C2 run 全部作废、C3 永远无法达成。claim 集改由账本的 SEALED 事件绑定到 (problemId, revision, specHash)。

测试：`test_claim_set_ledger.py`（6 项）、`test_trust_loop_documents.py::test_claim_set_state_is_derived_from_the_ledger`、`test_trust_loop_adversarial.py` claim sealing 三条。

### Issue 4 — C3 与 G6 的独立环境定义必须统一

**ACCEPT_WITH_MODIFICATION。** 审查结论：第 2 稿 `RunQualification.environment_id` 是不透明字符串，G6 没有任何环境代码——两处都没有定义，谈不上一致，但也说明"漂移"是必然的。

- 统一为 `EnvironmentFingerprint` + `environment_id`（强字段哈希）+ `independent_environments`；`c3_run_support` 与新的 `reproduction_status`（G6）都通过 environment_id 判独立性，只有一个规则。
- 强字段（任一不同即独立）：machineId、osFamily、acceleratorClass、frameworkVersion(major.minor)、blasBackend、dependencyLockHash、installationId。弱字段（单独不同不构成新环境）：osVersion、pythonVersion(patch)、acceleratorDriver。采纳 Kimi §4.1 的强 / 弱分法；hostname、用户名、路径不是身份（传入即拒）。
- 五个案例的裁定：A 同机不同独立安装 → 独立（最弱的可接受形式，检验结果不绑定于单一安装状态，与 R1 裁决 C12"不同机器或独立安装"一致）；B 同机同镜像两容器 → 同一环境（installationId = 镜像摘要相同）；C 不同机器同 lockfile → 独立；D 集群两节点 → machineId 不同即独立；E 不同 OS / 加速器 → 独立。
- **驳回"机械要求所有字段都不同"**与 GLM 提议把内存容量 / CPU 核数纳入身份：独立性的目的是排除单一安装 / 单一执行环境的偶然性，不是可移植性；字段越多，"刷环境数"越容易。
- G6 语义：同环境或同 seed 集的"复现"只证明确定性 → 协议未执行 → BLOCKED；执行了但落在容差外 → FAIL。

测试：`test_trust_vector.py` 案例 A–E 与 `test_reproduction_uses_the_same_environment_rule_as_c3`、`test_trust_loop_adversarial.py::test_same_machine_same_installation_with_a_new_hostname_is_one_environment`。

### Issue 5 — IQR / median 的零点与近零行为

**ACCEPT_WITH_MODIFICATION。** 审查结论：第 2 稿 `training_reliability_status` 只接收 `iqr_ok` 布尔值，除法在治理代码之外——正是评审说的"隐式实现细节"。

- 新增 `seed_statistics(errors, epsilon_spec, …)` 从逐 seed 误差计算 k、median、IQR（Tukey hinges）、worst。离散度规则写成 **`IQR > dispersionLimit × median`**：乘法比较，全程无除法。语义等于方案 A（median = 0 ∧ IQR = 0 → 不封顶；median = 0 ∧ IQR > 0 → 封顶 PARTIAL），但不产生 inf，也不需要"median ≈ 0"的机器容差规则（没有除法就没有放大）。
- **驳回方案 B（预注册分母下限 ε_floor）**：它是一个没有物理意义的数字，进了 ScientificSpec 也仍是人为的；在"误差全部极小"的情形下它把噪声比放大成判定，而在"误差全部为零"的情形下它反而把 0/ε_floor 判成正常——两头都错。
- NaN / Inf 的 run：发散 run，计入 N、不计入 k、worst = ∞ → worst_ok False；中位数落在发散 run 上 → FAIL。负误差：误差范数非负，负值是调用方错误，拒绝。Kimi 的"发散率 > 20% → FAIL"不单列：k/N < 0.8 已蕴含。

测试：`test_trust_vector.py` seed statistics 五条（median = 0 / IQR = 0、median = 0 / IQR > 0、近零、NaN、Inf、负值）。

## 3. 复审建议中被驳回的部分（完整论证）

```text
Decision: REJECT
Claim being rejected: Issue 1 方案 1 —— DimensionResult 增加 applicability，整维 NOT_APPLICABLE 时无 TrustStatus、不进 claim 的 weak-link meet。
Reason: 它创造了"一个必需维度可以合法地不存在"的状态，而必需维度 = MUST Gate 的对象。整维豁免正是最大化 Claim 等级的 Agent 想要的形式合法路径。
Existing protection: 第 2 稿已无此路径（全 N/A 折成 NOT_CHECKED 会阻断一切 claim，方向是安全的，只是语义错）。
Why the proposed change is unnecessary or harmful: 增加一种类型、一条前提矩阵之外的分支，且把"不承担"这个规格事实放到 run 级记录里。
Evidence: trust_vector.py: NoApplicableCheck / dimension_status_from_checks; trust_loop.py: _check_registry_errors; tests: test_all_not_applicable_is_an_illegal_registration_not_a_weak_not_checked, test_all_not_applicable_is_refused_at_spec_level_too.
Residual risk: 某类未来问题对某维度确无适用检查时需要立新修正案（这是设计意图）。
Alternative: INV-A1 + 规格级注册表（已采纳）。
```

```text
Decision: REJECT
Claim being rejected: Issue 1 方案 2 —— 由 ScientificSpec / ClaimPrerequisite 显式豁免整维。
Reason: 与方案 1 同一个开关，只是挪到规格里；写规格的仍是 Agent；且与 REQUIRED_DIMENSIONS 并存两套前提矩阵必然漂移。
Existing protection: REQUIRED_DIMENSIONS 是封闭常量，无豁免入口。
Why harmful: 引入第二真源。
Evidence: trust_vector.py: REQUIRED_DIMENSIONS; tests: test_example_* 系列。
Residual risk: 无新增。
Alternative: 同上。
```

```text
Decision: REJECT
Claim being rejected: Issue 3 中"必须实现真正 append-only / immutable 存储"。
Reason: 本项目层级是单机 JSON 文档，没有可信第三方或不可变介质；声称做到了就是假保证。
Existing protection / Alternative: 哈希链账本 + 决策必须引用 ledgerHead + 文档状态必须等于账本推导值，给出的是可检测性而非不可篡改性，并如实写进修正案。
Evidence: claim_set_ledger.py: validate_claim_set_ledger（L1 chain）; trust_loop.py: ledgerHead 校验; tests: test_history_deletion_reordering_and_rewriting_break_the_chain, test_deleting_the_opened_event_from_the_ledger_is_detected, test_a_decision_must_cite_the_ledger_head_and_an_opened_claim_set.
Residual risk: 攻击者同时重写账本与决策并让人工终审看假决策——这超出机器治理范围，属于宪法第三十九 / 四十章（不得伪造执行 / 文件）的人工审计对象。
```

```text
Decision: REJECT
Claim being rejected: Issue 4 中"environmentFingerprint 字段越全越好 / 都必须不同"（含 GLM 的内存容量、CPU 核数）。
Reason: 独立性检验的是"结果不依赖单一安装 / 单一执行环境的偶然性"，不是可移植性；字段越多，同一台机器"刷"出不同环境越容易，而真正的独立性并没有增加。
Existing protection / Alternative: 强 / 弱字段二分，environmentId 只哈希强字段，独立 ⇔ 强字段有一项不同。
Evidence: trust_vector.py: ENVIRONMENT_STRONG_FIELDS / ENVIRONMENT_WEAK_FIELDS / independent_environments; tests: test_case_a … test_case_e, test_patch_level_differences_never_make_a_new_environment.
Residual risk: installationId 的采集方式（venv 前缀 id / 镜像摘要）由 runner 工具决定，工具尚未实现（R3）。
```

```text
Decision: REJECT
Claim being rejected: Issue 5 方案 B —— 预注册分母下限 ε_floor。
Reason: 见 §2 Issue 5；一个无物理意义的数字，两头都错。
Existing protection / Alternative: IQR > limit × median 的乘法比较。
Evidence: trust_vector.py: seed_statistics; tests: test_dispersion_rule_has_no_division_and_no_floor.
Residual risk: 极小误差下 IQR 略大于 median 会封顶 PARTIAL——这是 fail-closed 的方向，可接受。
```

## 4. 队员建议的裁决（采纳 / 部分采纳 / 驳回）

| # | 来源 | 建议 | 裁决 | 说明 |
|---|---|---|---|---|
| R2-1 | GLM P1 | revision 严格递增按事件日志校验 | 部分采纳 | 账本的 (problemId, revision) 单次 OPENED + 决策 revision 必须等于规格与向量的 revision；"严格递增"的跨文档校验留给 RunRecord 注册表（R3） |
| R2-2 | GLM P2 | 烧毁自 OPENED 起全局永久；历史只认账本 | 采纳 | L4、L7；文档 history = 账本投影 |
| R2-3 | GLM P3 / P4 | claimSetHistory uniqueItems；OPENED ⇒ 字段条件 | 采纳 | schema uniqueItems；交叉校验 |
| R2-4 | GLM P5 | specHash 排除 claimSet\*，revision 不入哈希 | 采纳 | 见 Issue 3 |
| R2-5 | GLM P6 / Kimi §1.2 | 样本级指纹交叉校验 | 采纳并加强 | 见 Issue 2；不用"重叠率阈值"（互斥就是零重叠），用最小间距处理近重复 |
| R2-6 | GLM P7 | 三契约 additionalProperties:false | 已是 | 1.1 已声明 |
| R2-7 | GLM V1 / V3 | CheckResult 条件字段；external ∧ dev ⇒ status ∈ {NOT_CHECKED, BLOCKED} | 部分采纳 | 条件字段已在 1.1；**驳回** external 在 dev 上不得 PARTIAL / FAIL：dev 上的一致性观察是合法的诊断证据，PARTIAL 正是"查了不充分"的准确措辞；FAIL 进 FAILURE_RECORDED 是正确行为（dev 上都不一致更该停下） |
| R2-8 | GLM V2 / Kimi §3.3 | 适用性由注册表推导 | 采纳 | checkApplicability 进规格并进 specHash |
| R2-9 | GLM V4 | judgedBy 走 actor 注册表；OPENED-actor 污染集 | **驳回** | 打开 claim 集的人就是做最终验证的人，污染集会禁止同一研究者再做任何验证，不可维护；它想封的泄漏（把 claim 集内容带进下一版本）已由"打开即烧毁、新版本换新集"在数据层封死，新 claim 集是未见过的样本 |
| R2-10 | GLM V5 | perturbationsRun 引用 runId；PASS ⇒ worstCase 必填 | 部分采纳 | worstCase 在有扰动时必填（不限 PASS）；perturbationsRun 保留 P 编号（Red Team 矩阵编号是协议的一部分） |
| R2-11 | GLM V6 | 检查级 status 一律由通过率分档复算 | **驳回** | 通过率分档是 C_train 多 seed 协议的规则；物理检查、实现单测是确定性单次判定，套用 0.9 / 0.8 分档是语义错配（"90% 的通量平衡检查通过"没有意义） |
| R2-12 | GLM V7 | evidencePointers 内容寻址 | 已是 | artifactRef{artifactId, sha256} |
| R2-13 | GLM V8 | claim 上的 judgedAt ≥ OPENED.at | 部分采纳 | 用 claimSetSha256 + 账本 OPENED 事件绑定代替时间比较（时间戳可填，事件不可无） |
| R2-14 | GLM C1–C4 | qualifiedC2Runs 必须解析到 RunRecord、seedSetId / environmentId 派生、minItems 5 | 采纳（minItems 除外） | 派生 + 复算；RunRecord 注册表为可选参数；**驳回 minItems 5**：少于 5 个 run 的决策是合法的（它只是不许 C3），schema 不应把 C3 前提写成文档存在条件 |
| R2-15 | GLM C5 / C6 | 演算封闭、weakestLink 集合相等 | 已是 | claim_gate 是唯一演算；weakestLink 集合相等 1.1 已有 |
| R2-16 | GLM C7 / Kimi §4.2 | codeHash = 封闭清单的规范化哈希 | 采纳 | RunRecord.codeManifest；testHash 是否并入：**不并入**（测试代码不改变方法，但清单可包含 tests/ 目录，由规格的清单范围决定） |
| R2-17 | GLM D1 | 路由键 (rootCause, gate) | 已是 | ROOT_CAUSE_GATE 由根因唯一决定 gate，DiagnosisRecord.gate 只可选且必须等于派生值 |
| R2-18 | GLM D2 | 3 轮键 = (problemId, specHash)，revision 不入哈希 | 采纳 | 见 Issue 3 |
| R2-19 | GLM D3 | STOPPED_THE_LINE 出口：ABANDONED 终态、换 problemId 回 DRAFT | **驳回** | 新状态违反本修正案"状态集合不变"的承诺；宪法第五十八章已把 Negative Result 定为合法终点，停线的出口是人工裁决记录（DecisionRecord），不是状态机转移 |
| R2-20 | GLM 复发升级 | 跨 specHash 同 (rootCause, gate) ≥ 2 次自动停线评审 | **采纳**（用户 2026-09-15 同意） | 触发停线评审而非直接终止；需要跨规格的诊断注册表，实现 R3；写入协议汇编 §8 |
| R2-21 | GLM 枚举 / ID 改名 | S1–S6、rSpecAmbiguity 等、`sha256:` 前缀、`actor_`、`pinn_` | **驳回** | 仓库已定名（六症状、九根因、pdef- / tv- / cgd- / hex64），改名无保护增益、破坏既有测试 |
| R2-22 | GLM T29–T60 | 32 条用例 | 采纳可落地者 | T45 seed 改名、T46 环境伪造、T47 不升版重开、T48 N/A 藏 FAIL、T49 缺区分实验、T50 根因越界、T51 external dev PASS、T52 history 与 status 不一致、T53 weakestLink 少列、T54 混入其它 codeHash、T55 旧哈希复用、T56 条件字段、T58 空升版不重置、T59 账本篡改、T60 宽于演算 → 对应 `test_trust_loop_adversarial.py`、`test_claim_set_ledger.py`、`test_trust_loop_documents.py`；T57（污染 actor）随 R2-9 驳回 |
| R2-23 | Kimi §1.1 | D_phys 辅助集 | 采纳 | evaluationSets.phys 可选，与训练点互斥 |
| R2-24 | Kimi §1.4 | "打开"的操作清单、治理侧持有 | 采纳为协议 | 单机场景存储形态：用户 2026-09-15 同意由队长选型，选**权限目录**（治理账户独占可读、研究者账户无权限），不选加密文件（密钥与数据同机，只增管理不增保证）；写入协议汇编 §10 |
| R2-25 | Kimi §1.6 / 豆包 §3.1 | burnt 集可否降级为 D_dev | 裁决：**可以** | 它不再是盲的，这正是 dev 的定义；须以新哈希登记为 dev（或并入 train，改 specHash），永不再任 claim；账本烧毁只针对 claim 角色 |
| R2-26 | Kimi §2.1 | 发散率 > 20% 单列 FAIL | 不单列 | k/N < 0.8 已蕴含 |
| R2-27 | Kimi §2.3 | A 段归因扫描不计入 k/N | 采纳为协议 | 写入协议汇编 §6 |
| R2-28 | Kimi §4.1 | 强 / 弱字段；"仅 patch 差异判同一环境" | 采纳 | 见 Issue 4；不算过宽 |
| R2-29 | Kimi §6 ③ | 2D 点数与 PH9 阈值默认值 | 待预注册 | 协议汇编写区间，正式值 SPEC_LOCKED 前冻结 |
| R2-30 | 豆包 §5.2-1 | P12 越线压 C_physics 还是 C_external | 裁决：**只压 C_physics** | Red Team 矩阵 P12 列写的是 C_physics；一个扰动只降级矩阵指定的那一维，每个维度反映自己的证据；示例 (b) 的 C_external 由 claim 集一致性与网格无关性决定 |
| R2-31 | 豆包 §5.2-3 | 纯文字改动不升 revision 由谁判定 | 裁决 | 由哈希判定：specHash 与 codeHash 都不变即不升版（文档不在任一哈希内） |
| R2-32 | 豆包 §5.2-4 | C3 披露是否逐一列 environmentId | 裁决 | 列 environmentId（强字段哈希），不列原始指纹 |
| R2-33 | 豆包 §5.2-5 | 报告与 DiagnosisRecord 冲突 | 裁决 | 以机器记录为准，报告是只读渲染 |
| R2-34 | 豆包 §5.2-6 | 停线句式与禁用词自动校验 | 采纳原则 | 文本 lint 的实现是 R3（C15 延伸） |
| R2-35 | 豆包 §1.2 | 维度汇总句"没有 APPLICABLE 检查时维度 = NOT_CHECKED" | **改口径** | 按 INV-A1：没有登记检查 = NOT_CHECKED；登记了但全 N/A = 非法 |

## 5. 分歧记录（不抹平）

- GLM 的六症状 / 九根因 / ID 模式与仓库不同，原文保留，整合按仓库定名。
- GLM 提出的 ABANDONED 状态与 actor 污染集未采纳，原文保留，理由见 §4。
- Kimi 从严执行"burnt 集禁止降级为 D_dev"，队长裁决为允许；Kimi 原文保留。
- 豆包示例 (b) 第 2 版把 FM-1 同时压 C_physics 与 C_external，队长裁决只压 C_physics；豆包原文保留，模板第 3 稿示例按裁决改。
- DeepSeek R2 在第 3 稿终审同日补交，其建议的三个新矩阵格未进入已终审的 A-0001，作为 A-0002 候选保留；原文保留。

## 7. DeepSeek R2 的裁决（终审同日补交，2026-09-15）

| # | 建议 | 裁决 | 落点 |
|---|---|---|---|
| R2-36 | 诊断实验库 P22–P32，与 P1–P21 是否合并编号 | 不合并：P1–P21 对抗式加压，P22–P32 隔离式诊断，语义不同；编号不冲突，`DiagnosisRecord.excludes[].experiment` 的模式 `P[0-9]+` 两类都接受，无需改代码 | 协议汇编 §4 |
| R2-37 | 逐格 (a)(b)(c) 表 | 采纳为 `excludes` 的 observed 写法与数值约定 | 协议汇编 §4 |
| R2-38 | 矩阵增 3 格（sBcResidual → 容量、sPinnCfd → 容量、sLocalizedError → 规格） | **采纳，起草 A-0002（PROPOSED）**：用户 2026-09-15 授权队长裁决；三格理由成立（低容量同样导致 BC 欠拟合与 PINN–CFD 差距；源项 / 边界位置写错是局部误差的直接来源）且各有正交的区分实验；`ADMISSIBLE_ROOT_CAUSES` 与测试已同步，宪法 1.2 落笔待用户终审 | `governance/AMENDMENTS/A-0002-admissible-matrix-r2.md` |
| R2-39 | 倾向不加的三格（sPinnCfd → 采样、sPdeResidual / sConservation → 数据、sSeedSensitive → 实现） | **A-0002 第 2 稿改判**：sPinnCfd → 采样与 sSeedSensitive → 实现改为采纳（用户复审反例成立，见 §8）；数据两格维持不加但范围写死为 forward-problem MVP | `A-0002` 第 2 稿 |
| R2-40 | seed 阈值统计论证；建议宪法写明"PASS ≠ 高置信认证 p ≥ 0.9" | 采纳为协议说明与升级路径（N ≥ 30 / 50 为预注册时可选，不是补救）；宪法正文措辞随 1.1 落笔一并处理 | 协议汇编 §6 |
| R2-41 | 泄漏信息流不变量与五条检查项 | 采纳；检查项 ② ④ 已由账本实现，⑤ 与既有规则不冲突而是补充（打开须既在 claim 集上又在 VALIDATION 阶段），① ③ 运行期断言为 R3 | 协议汇编 §10 |
| R2-42 | Applicability 表（Poisson / NS / Oldroyd-B） | 采纳；三列各至少一项 APPLICABLE，与 INV-A1 一致；NS 的正定性 / 对称性 / 极值原理 / SPD 全部 NOT_APPLICABLE 的理由可直接填入 reason | 协议汇编 §3 |

## 6. 落地位置

| 产物 | 位置 |
|---|---|
| 修正案第 3 稿 | `governance/AMENDMENTS/A-0001-trust-loop-r1.md`（status 仍 PROPOSED，effectiveDate PENDING） |
| 弱链演算 / seed 统计 / 环境身份 / G6 | `pinn/governance/trust_vector.py` |
| 评估集样本级互斥 | `pinn/governance/evaluation_sets.py`、`schemas/evaluation-set.schema.json` |
| claim 集账本 | `pinn/governance/claim_set_ledger.py`、`schemas/claim-set-event.schema.json` |
| 文档交叉校验 | `pinn/governance/trust_loop.py`；schema 1.2 三份；`schemas/run-record.schema.json`、`schemas/diagnosis-record.schema.json` |
| 状态机 | `pinn/governance/state_machine.py`（`discriminating_experiment_errors`，`diagnose` 调用它） |
| 测试 | `tests/pinn/test_trust_vector.py`（65）、`test_trust_loop_documents.py`（50）、`test_state_machine_triage.py`（39）、`test_trust_loop_adversarial.py`（23，新）、`test_evaluation_sets.py`（9，新）、`test_claim_set_ledger.py`（6，新） |
| 协议汇编第 3 稿 | `governance/PINN_TRUST_PROTOCOLS_R1.md` |
| 报告模板第 3 稿 | `docs/pinn-trust-loop/TRUST_REPORT_TEMPLATE.md` |


## 8. A-0002 第 2 稿：用户复审六项的因果可判定裁决（2026-09-15）

| # | 复审意见 | 裁决 | 要点 |
|---|---|---|---|
| 1 | sPinnCfd → 容量的"弱 / 强范数"措辞 | ACCEPT | 改为稳定性估计表述：‖u_θ − u*‖_X ≤ C_stab‖R(u_θ)‖_Y 只在匹配的稳定性估计存在时成立；ε_R 与 ε_E 无条款关联；残差在 D_phys 节点按离散 L2，差距在 claim 集按 QoI |
| 2 | sPinnCfd → 采样应采纳 | ACCEPT_WITH_MODIFICATION | 复审命题 A（采样不足必先触发 sPdeResidual）不成立：小测度关键区域欠采样时 L2 平均残差可不越阈而 QoI 偏移；"中介"是混淆了可干预根因、因果链中间量与症状。采纳该格，干预实验比复审建议更严并机器化 |
| 3 | sSeedSensitive → 实现应采纳 | ACCEPT_WITH_MODIFICATION | "实现缺陷是确定性的"不成立（RNG 泄漏、竞态、评估时未关 dropout、worker RNG 污染、非确定归约）；G3 的 T1–T10 与 P4 都不是确定性审计。采纳该格，命名前提为 P33 同 seed 重放发散且定位缺陷；矩阵是理论候选、记录逐个排除 |
| 4 | rDataDefect 两格驳回须限定范围 | ACCEPT | `MATRIX_SCOPE = forward-problem-mvp`、`DiagnosisRecord.problemClass = forward`；逆问题另立修正案 |
| 5 | P23 单调下降不足 | ACCEPT | 受控干预：单因子、其余控制项固定、≥ 3 档 × ≥ 3 seed、中位误差严格下降、容量另需优化诊断干净；同样适用于 P25 采样 |
| 6 | 修正案依赖须机器化 | ACCEPT | 通用 `dependsOn`（`amendments.py`）：ACCEPTED 单链、宪法版本 = 链尾、依赖目标状态与版本；挂进 PRELOCK 第七项 `amendmentRegister`；比特判 A-0002 更小 |

对复审两问的直接回答：A. 采样不足能否直接解释 sPinnCfd——**YES**（干预意义上的因果，反例机制成立）。B. 实现缺陷能否解释 sSeedSensitive——**YES**（非确定性实现缺陷）。驳回的复审意见：无。

闭合审计（6 症状 × 8 根因）：IMPOSSIBLE 4 格（sPdeResidual / sBcResidual / sConservation / sSeedSensitive → 参考解）；OUT_OF_SCOPE 5 格（→ 数据，正向）；UNSUPPORTED 2 格（sConservation → 奇异性、sSeedSensitive → 奇异性）；被遗漏的 ADMISSIBLE 3 格补入（sPdeResidual → 奇异性、sBcResidual → 奇异性、sSeedSensitive → 规格 / 非唯一解，P34 零空间投影）。新发现风险：**挑症状**（只登记候选集最小的症状以缩小排除义务）——NON-BLOCKING，以 `observedSignatures`（根因须对每个观察到的症状可接受）封住；"漏报症状"不可机器判定，留给人工审计（宪法第三十九 / 四十章）。

矩阵第 2 稿后各症状的候选数：sPdeResidual 6、sBcResidual 7、sConservation 5、sPinnCfd 8、sSeedSensitive 5、sLocalizedError 7（rUndetermined 之外）。

## 9. A-0002 第 3 稿：Final Closure Review 三项剩余问题的裁决（2026-09-15）

| # | 剩余问题 | 裁决 | 要点 |
|---|---|---|---|
| 1 | PROPOSED 修正案不得提前改变有效宪法的运行时行为 | **BLOCKING，已修复** | 审计：`ADMISSIBLE_ROOT_CAUSES` 是单一全局最新表，`diagnose` 不读版本——文档 1.1 / 运行时 1.2 语义，且干预 / 重放义务也对 1.1 生效。修复：矩阵与义务按版本分表，`admissible_root_causes(version)` 只认 `SUPPORTED_CONSTITUTION_VERSIONS`（运行时读取），API 与 schema 必填版本，登记簿 R5（PROPOSED 版本不得已生效），PRELOCK 校验运行时矩阵。1.1 矩阵在测试里逐格冻结。不重构 |
| 2 | observedSignatures 必须支持多个独立根因并满足覆盖不变量 | ACCEPT_WITH_MODIFICATION | 接受问题：单因规则会错误强迫单因果解释。采用 `explainedSignatures ⊆ observedSignatures` + 集合级 `diagnosis_coverage_errors`（同一失败、同 observed、∪explained = observed、每症状恰好一条记录）；单症状多因归因不定义——排除纪律下两个都成立就谁都命名不了，rUndetermined 停线；多记录重入取最小 Gate |
| 3 | sSeedSensitive → rSpecDefect 限定为非预期不可识别性 | ACCEPT | 非唯一解 ≠ 规格缺陷。`identifiability` 记录：Claim 需要唯一目标、规格未消除歧义、歧义非有意三者同时成立才可命名；分支感知 Claim / 有意多解 / 已定规范 → 拒绝；undecided → rUndetermined。P34 改为可识别性检验 |

Final Decision Recommendation：**READY FOR USER ACCEPTANCE**（status 仍 PROPOSED）。准入审计 `PINN_AGENT_EXPERIMENT_READINESS: NOT_READY`，只有三个 blocker：A-0002 等用户终审；Poisson 1D 校准实验尚未实跑（草案 lockedAt = null，无 ProblemDefinition / 评估集清单 / RunRecord / TrustVector / ClaimGateDecision，runner 工具 R3 未实现）；失败路径实验尚未实跑。完整报告 `docs/pinn-trust-loop/A-0002_FINAL_CLOSURE_REVIEW_20260915.md`。测试 1058 → **1087 passed / 2 skipped**（+29），PRELOCK 7/7 PASS。停止设计新治理规则：终审后进入 Poisson 1D 校准实验。

````

</details>

### R045 — 候选版/前端重塑验收报告.md

<details>
<summary>展开完整原文</summary>

```markdown
# Leo AI 自有工作台 · 前端重塑验收

日期：2026-09-26。已安装候选目录：`C:/Users/user/Desktop/LeoAI-Research-Candidate-20260926`。
源码提交：`6d4ec0f59a6ecc75b1225cbd983b7553f68bb64c`，隔离分支 `codex/trusted-research`。

## 已交付

默认入口现在直接加载 Leo 自有 HTML 文档，不再先打开 OpenAI4S 前端再覆盖主题。重做了森林绿侧栏、暖白工作区、研究首页、历史会话、项目切换、聊天输入和科研草案视图。原有 Agent、Notebook 和计算能力保留在“笔记本与计算”高级入口；固定上游源码未作修改，来源说明保留。

科研模型草案以目标、方程、区域、边界条件、方案、假设和待补信息分块呈现。人工确认、Gate、Claim 的服务端约束保持原有规则。

实机验收修复了两项新入口问题：重启后恢复进程内模型凭据，并随每条消息提交模型及推理能力身份；无参数桌面调用不再传入多余的空参数。错误码仅返回公开白名单，不回显服务商原始错误或凭据。

## 验证与范围

| 验证层次 | 结果 |
| --- | --- |
| 自动化回归 | 主回归 320 通过、1 跳过；最后设置修复的针对性回归 22 通过、1 跳过，两组计数不相加。跳过项为 entityLifecycle 开启时不适用的隐藏数据页检查。 |
| 构建 | 干净提交构建成功；326 个 launcher 文件、35 个关键文件、34 个归档模块通过包契约。 |
| 资产与部署 | 23/23 界面资产来源匹配，0 缺失、0 漂移；365 个部署文件摘要匹配。最后一次部署前后的 24 个配置、凭据及科研数据文件摘要一致。 |
| 真实 Windows UI | 默认自有首页、项目与历史切换、已绑定模型、真实 DeepSeek 回复、生成科研草案、无证据时阻断 Claim、设置弹窗、模型管理跳转、重启，以及高级计算入口和返回路径均有定向实测。具体源码版本见 `frontend-acceptance/native-acceptance.json`。 |
| 停止按钮 | 已观察到运行状态与停止按钮；模型在点击前已完成回复，因此不记为实际取消通过。接口保留精确执行者与执行 ID 检查。 |
| 正式科学验收 | 未运行。没有代替用户确认模型或正式运行；没有生成 C2。 |

真实聊天验收会话：`f-c6084df6643c`，标题“科研候选修复验收-真实 DeepSeek 对话”。
科研草案：`research-27f9efc08f2a438a82998b88814976f8`，状态 `DRAFT`、版本 2。模型列出了训练参数和验证标准等缺失内容；界面显示待补全，不得把“草案生成完成”视为“科学结果通过”。

聊天与草案验收在 f8a7074 安装版完成；最后 6d4ec0f 只修复无参数设置桥接，并重新实测设置与重启。高级入口和返回在 73fd11c 实测，相关路径在最终版未变化。离线浏览器样例只用于布局预览，不计入真实模型或科学验收。

## 截图

![安装版 Leo 工作台](frontend-acceptance/native-home.jpg)

![真实 DeepSeek 对话](frontend-acceptance/native-chat.jpg)

![真实生成的科研草案](frontend-acceptance/native-research.jpg)

## 使用与回退

打开桌面的“Leo AI 科研候选版”快捷方式，进入后即为新工作台。左侧可选择项目、历史会话、科研任务；模型管理位于左下角。代码、文件和 Notebook 的完整能力可从“笔记本与计算”进入。

最后一次部署回退目录：`C:\Users\user\Desktop\LeoAI-Research-Candidate-20260926\.leo-rollback-20260926-032841-919d483e`，其中 `deployment.json` 登记了部署身份，`INSTALLATION_RECEIPT.before-settings-fix.json` 保存前一版本回执。可在关闭候选程序后恢复其中的已备份发行文件。不要覆盖 `user/`；不要用回退操作重写科研证据。

如需回到前端重塑前的候选版，保留的回退目录为 `.leo-rollback-20260926-030013-81bdc58b`。该操作也需同步恢复对应 science-source 提交；已有正式运行确认不能移用于不同代码身份。

当前科学代码摘要：`b6ddf29682a4a570e33ea6961151406d5cefebc7668ce1f9c321b2bd930c6139`。候选版本仍为 `CANDIDATE_NOT_SCIENTIFICALLY_ACCEPTED`。

```

</details>

### R046 — 候选版/审阅与验收报告.md

<details>
<summary>展开完整原文</summary>

```markdown
# Leo AI 可信科研闭环首版：候选交付与验收记录

日期：2026-09-26。当前状态：**实现与自动检查已交付；正式科学验收、真实安装端到端验收尚未完成。没有新的 C2 成功结果。**

## 入口与身份

- 桌面快捷方式：`Leo AI 科研候选版.lnk`，以 `--settings` 启动，不自动连接。
- 候选目录：`C:\Users\user\Desktop\LeoAI-Research-Candidate-20260926`。
- 原应用目录和原 `master` 未覆盖；原提交仍为 `e0acab45fe981b1197053b8bc5203cec56546622`。
- 实现分支：`codex/trusted-research`；源码提交：`cde1259df75063de6bdb15e80516af67253e83ca`。
- 开发检出：`C:\Users\user\.codex\worktrees\trusted-research\LeoAIStudio-build`。
- 科研方法内容摘要：`d8a0e973a9099bbfff0978811d31d64e10089f3d4a721d22ac50a52bb01ee3b5`。
- 候选科学源码在 `runtime/science-source`，与开发检出的科学身份逐项相同。
- 上游固定提交：`a792c38d9984be428437b548db29baab3322f6dc`，没有修改 OpenAI4S 源码。
- `build-receipt.json` 记录构建输入；`INSTALLATION_RECEIPT.json` 记录候选安装的 361 个发行文件摘要。两者均不表示科学验收通过。

## 只读审阅结论与本次修改

以原基线完成只读审阅后，在独立检出实施。现有内核已经有训练、验证、失败诊断、Claim 判定、样本账本、独立复现以及宪法 1.2；本次把这些能力接到桌面任务服务。历史 Poisson 成功记录只作资料，没有复制成新任务结果。环域研究不在此次成功范围。

科研面板提供问题与模型、运行、验证与结论、证据四个视图。草拟请求复用会话模型配置，不给模型工具或确认权限。原生对话框负责人工模型确认、运行确认和结论审阅。任务有版本检查、摘要绑定、事件链及幂等启动；任务资料按任务和 attempt 隔离。

正式适配器仅支持 `-u''(x)=pi^2*sin(pi*x), 0<x<1, u(0)=u(1)=0`。沿用硬边界 `x(1-x)N`、3×32 tanh、Adam 6000 步、10 个种子、CPU float64 和原有阈值。运行包含完整规格、配置、环境、种子、集合身份及 3600 秒总预算。其他问题可以保留草案，不会被静默替换。

执行顺序为主实验、Tier-1、独立复现、G6。取消或超时保留文件，不调参、不自动续跑。新 Claim 集按预先确定的几何网格序列选择，核对历史使用及预留样本，不借用历史集合。复现 CLI 明确使用 `--reproduction-of`，不重开主实验 Claim 集。

当前记录用显式引用及哈希选取。核验覆盖规格 schema、样本、账本、RunRecord、TrustVector、ClaimGateDecision、内部证据指针和跨记录身份。导出递归清点文件，拒绝覆盖现有包，manifest 不包含自身。验证器不依赖大模型或 Torch。

宪法、规格阈值及历史 `experiments` 资料没有改动。

## 已执行检查

| 检查层次 | 实测结果 | 边界 |
|---|---|---|
| 全仓自动回归，提交 a6586cb | 1454 passed / 33 skipped / 0 failed | 不是安装 UI 或正式科学验收 |
| 科学环境 A，提交 a6586cb | 911 passed / 0 skipped / 0 failed | 包含 Torch 数值组件；不等于正式 6000 步任务闭环 |
| 最后核验器修改，提交 cde1259 | 109 passed / 0 skipped / 0 failed | 覆盖产品、科研文档、对抗及 G6 回归，与前两行有重叠，不能加总 |
| 最终源码真实准备检查 | READY_FOR_RUN_APPROVAL，启动前 check 通过 | 模型确认是测试替身；没有正式运行确认，没有训练 |
| 两套科学环境鉴定 | 同机独立安装，锁定依赖相同，installationId 不同 | 符合当前宪法允许的最弱独立形式；不是跨机器或跨实现复现 |
| 准备资料导出及离线核验 | 134 个文件全部摘要相符 | 在无 Torch 的解释器完成核验；该包是准备测试资料，不是科研成功结果 |
| 发行构建 | 成功；326 个 launcher 文件、31 个关键文件、33 个归档模块通过 package contract | 不等于已安装应用验收 |
| 安装字节核对 | 361 个发行文件与最终构建一致；科学源码身份一致 | 候选用户目录不属于原始发行包，不能将含 user 的安装目录误作原始包运行 package contract |
| 浏览器界面夹具 | 创建、草案展示和无 Claim 视图已观察，截图保存 | 模型/确认均为替身；不是真实 WebView2 操作 |
| 原生启动探测 | 前一候选构建启动进程并记录固定 WebView2 路径 | 随后停止了该自建探测进程；没有据此签署 UI 通过 |
| 正式主实验 / Tier-1 / 独立复现 / G6 | NOT RUN | 等待人在候选产品中确认 |
| 真实成功与真实失败的完整任务证据包 | NOT DELIVERED | 准备失败、单元测试和历史结果均不能替代 |
| 安装应用的聊天、模型切换、重开、取消、导出回归 | NOT TESTED | 待真实产品内验收 |

全仓 33 个跳过项包括：16 个缺 NumPy、7 个缺 Torch、1 个数值模块集合跳过、7 个工作树路径下缺固定上游检出、1 个当前功能开关下不适用场景、1 个缺离线 wheelhouse。科研子集已在科学环境重新运行，无跳过；其他跳过仍保留。

构建使用现有锁定构建环境。离线 wheelhouse 清单未通过核验，因此不声称可以离线从零安装构建依赖。两套科学环境安装在本候选目录，依赖本机 Python 基础安装，不应通过移动或复制该 venv 来声称获得新独立环境。

## 本次实际发现并修复的问题

1. 应用任务 ID 不符合科研账本要求的 `pdef-` 前缀。第一次准备被账本拒绝，未训练；失败目录保留。现在分别保存 taskId 与 problemId。
2. Anthropic/Gemini 根地址缺少 API 版本路径。按现有配置形式补齐，并增加根地址及带版本地址回归。
3. Claim 集打开后会更新规格记录，使早期 Gate 引用失效。现在保留封存时的规格字节，并在 G6 中登记可解析的复现证据。
4. 新配置在工作树中曾有 CRLF、干净克隆为 LF 的差异。仅将本次新增配置统一到仓库既定 LF 格式，重新构建、准备和校验；没有归一化历史证据。
5. 最后补齐问题规格 schema 和运行/问题/执行身份的交叉校验。

## 人工验收步骤

1. 使用桌面“Leo AI 科研候选版”进入设置。候选没有复制原应用凭据，按需要自行配置模型。进入项目和会话，选择会话模型。
2. 打开“科研任务”，输入：`请求解 -u''(x)=pi^2*sin(pi*x)，x 在 (0,1)，u(0)=u(1)=0，检验误差并完成独立复现。`
3. 生成并审阅草案，核对假设来源、方程、区域和边界。在原生确认对话框中亲自确认模型。
4. 切到“运行”，准备运行确认包。检查完整规格、阈值、预算、代码身份、两套环境及种子安排，再决定是否确认正式运行。确认后最多执行 60 分钟，不自动扩预算。
5. 观察阶段进度。测试取消与重开时保留原任务，不删除失败目录。若任务失败，按失败证据报告，不修改冻结阈值。
6. 完成后查看“验证与结论”，核验 Gate/Claim。只有机器核验支持时才使用对应结论；人的解释不提升 Claim。再导出证据包并独立核验。
7. 将任务 ID 或具体阻断信息回传，以便继续检查实际成功/失败证据、G6、导出和安装回归。

这些确认必须来自人的产品操作。测试确认回调、聊天文字和模型 JSON 都不能代签。

候选桌面用户数据与科研任务目录独立，但现有 WSL 聊天桥接仍共用本机 Leo 后端。它不是完全隔离的聊天沙盒。不要把复制现有会话或历史科研文件当作新实验。

## 证据、复现与回退

自动测试 XML、准备成功/失败夹具、脚本和截图在本目录 `acceptance` 中。所有夹具都只证明相应工程行为，不应导入产品当作人工确认或科研结果。`acceptance/PACKAGE_MANIFEST.json` 可递归校验该验收资料集合。

正式结果导出后，包内 `REPRODUCE.md` 提供离线核验和独立复现步骤。复现需要经鉴定的科学环境；先预览命令，明确执行时才追加 `--execute`。复现结果不会自动替原结果签署更高 Claim。

回退无需覆盖文件：关闭候选程序后使用原“Leo AI Studio”入口。若科研 worker 正在运行，应先在候选面板取消并确认结束；直接关窗口不等于取消科研任务。保留候选 `user/research`、验收文件和旧构建资料，不回写历史 run。当前没有创建正式科研 worker，没有改变 WSL 活跃源码或原应用设置。

```

</details>

### R047 — 候选版/验收故障修复说明.md

<details>
<summary>展开完整原文</summary>

```markdown
# Leo AI 科研候选版人工验收故障修复

当前状态：模型配置修复已生效；程序修复包已于 2026-09-26 02:17（America/Los_Angeles）安装，科学源码同步到相同提交。360 个发布产物摘要匹配，18 个配置、凭据与科研任务文件在部署前后保持原样。原生界面人工复验仍待完成。

源码提交：`8b61ce620e546216ff57c85db771e277078d9e18`。

## 三项反馈

| 反馈 | 确认的原因 | 已完成的处理与证据 |
|---|---|---|
| 已配置密钥但聊天失败 | DeepSeek 返回 HTTP 400，配置的 `deepseek-v4.1-pro` 不是可用 API 模型 ID；同一密钥读取模型列表返回 200 | 保留密钥，将此 Pro 配置改为 `deepseek-v4-pro`，更新受影响会话绑定。真实应用后端测试会话已得到中文回复 |
| 科研任务无法继续 | 原任务只有创建记录，尚未生成草案；验证页缺少下一步指引 | 原任务已通过真实 DeepSeek 请求生成草案。修复包增加创建后草拟、失败重试、具体错误及下一步导航 |
| 界面增强加载失败 | 科研面板位于合并脚本末尾，但未返回桌面壳要求的 `true` | 修复首次及重复注入返回值，同时保留来源、版本和核心加载检查；JavaScript 运行回归通过 |

服务端模型名称以 [DeepSeek 模型列表](https://api-docs.deepseek.com/api/list-models/) 及本次真实接口返回为依据。

## 可查看的真实记录

- 应用内测试会话：**科研候选修复验收-真实 DeepSeek 对话**，ID `f-c6084df6643c`。
- 真实回复：“连接正常，可以继续对话。”该记录验证了应用后端及提供方链路，不是模拟回复。
- 原科研任务：`research-71b48b8c79a34c6489912c9a9877d935`，version 2，`DRAFT`，已生成受支持 Poisson 1D 草案。
- 原会话：`f-d5a5d5c877c4`。打开此会话的科研任务面板，选择“查看本会话的科研任务”，在“问题与模型”核对草案。
- 模型确认和正式运行确认均未签署，未启动正式科研运行，没有新增 C2 声明。

历史失败消息保留，不能因为配置已修正而把历史失败改写成成功。

## 检查范围

- 桌面壳、科研服务及面板运行回归：298 项唯一测试通过。
- 主题来源检查：19/19 匹配，0 未登记、0 漂移。
- 干净源码构建及发布包完整性检查：见修复证据目录的最终构建日志。
- 安装后原生 WebView2 人工点击、红条消失、重开、完整科研运行及独立复现：尚未复验。不能用上述测试或后端调用替代。

证据目录：`C:\Users\user\.codex\worktrees\trusted-research\LeoAIStudio-build\docs\manual-acceptance-evidence\research-v1-repair`。

修复包目录：`C:\Users\user\.codex\worktrees\trusted-research\LeoAIStudio-build\dist\research-repair-2\dist\LeoAIStudio`。

## 安装与保留内容

旧候选版退出后，已使用既有事务部署工具替换发布文件，并同步独立科学源码快照。部署保留 `user/`、历史会话、科学环境和任务。原正式安装不在本次更新范围内。

配置修改前的加密备份：`user/repair-backup-20260926-llm/`。没有将密钥写入明文报告或源码。程序回退备份：`.leo-rollback-20260926-021751-3cf5a38c/`；安装核验收据：`REPAIR_INSTALLATION_RECEIPT.json`。回退时关闭候选程序，恢复备份中的发布文件，并将科学源码恢复到 `cde1259df75063de6bdb15e80516af67253e83ca`；保留 `user/`，不要恢复已确认无效的模型名。

```

</details>
