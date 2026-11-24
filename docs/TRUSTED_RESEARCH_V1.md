# Leo AI 可信科研任务 v1

## 基线与范围

只读审阅基线：`e0acab45fe981b1197053b8bc5203cec56546622`，原始工作区干净。
在独立 `codex/trusted-research` 分支实施。宪法 1.2、冻结阈值、历史实验及上游 OpenAI4S 均不修改。

首版是固定 Poisson 1D 的产品校准工作流：`-u''=pi^2*sin(pi*x)`，区间 `(0,1)`，齐次 Dirichlet。
模型生成草案不能执行代码；模型和正式运行须经桌面原生确认。未支持问题保留原方程和缺失信息，不自动替换。
运行设置是已有硬边界方法的产品模板：3×32 tanh，6000 步 Adam，10 个种子，CPU float64。
这些设置是已知基准的方法，不能将本轮结果解释为独立的新方法发现。

## 架构与接口

`ShellApi.research_request` 的 `operation` 支持 create/list/get/draft/update/approve_model/prepare/approve_run/cancel/evidence/export/review。
除读取外，请求携带 `taskId` 与 `expectedVersion`；新建还需当前会话 `frameId`、`projectId` 和原问题 `prompt`。
`approve_run` 对已经接纳的任务幂等，不产生第二个 attempt。任务记录与带前序哈希的事件快照存于 `user/research/tasks/<taskId>`。
原生确认绑定草案/完整运行计划的摘要。模型响应和请求中的 approved 字段没有授权含义。

科研运行依赖 `runtime/research-runtime.json`，其中 `codeRoot`、`pythonA`、`pythonB` 均可用相对安装根路径。
代码根必须是干净 Git 检出，依赖锁为 `pinn/research/requirements-science.lock`。
两套科学环境独立安装，不允许通过复制或重命名环境伪造独立性。正式工作由现有宪法环境身份规则鉴定。
桌面壳环境不安装 Torch，任务在外部科学解释器中运行。

`pinn.research.context.RunContext` 明确代码根、数据根和执行者。原 CLI 不传 context 时保留原语义；新 CLI 可传 `--context <json>`。
产品数据根与源码完全分离；历史打开或预留的 Claim 样本均纳入新集合互斥检查。
新的 GL/CGL 网格按事前确定的序列选择，只看样本重合和最小间距，不看模型误差。
准备阶段建立规格、集合、账本和运行计划，但不训练、不执行 Gate 1、不产生正式 Claim。

正式执行由单任务 supervisor 顺序调用 main/tier1/reproduction/g6。复现只运行 Gate 1–4，不再次打开 Claim 集。
任务状态、科学状态和人工结论分离。超时、取消、崩溃保留文件；首版不实现训练续跑。
取消由文件请求传递到 supervisor，仅结束它启动的当前计算子进程。

## 报告和复现

运行摘要显式引用当前 TrustVector 和 ClaimGateDecision，报告按引用及哈希读取，不用文件名排序。
G6 在应用前重新计算复现判定，拒绝人工篡改的复现报告。未满足六维前提不得生成 C2。
导出目录不可覆盖；递归哈希覆盖资料与源码，manifest 不包含自身。导出包包含离线核验与独立复现说明。
`python -m pinn.research.reproduce --package <package> --out <new-dir>` 默认只预览；追加 `--execute` 才执行独立复现。

## 验收边界

测试分为纯 Python 回归、Torch 数值组件测试、界面夹具检查、真实安装应用与正式科学运行。
使用测试确认回调、测试模型或合成记录的测试，不能当作人工审批或真实 C2 证据。
正式科学验收必须在候选安装版上由人确认模型和具体运行包；在此之前状态为 **NOT RUN / AWAITING HUMAN CONFIRMATION**。
候选版不覆盖正式安装目录或复现环境；失败证据不删除，修正不得回写历史 run。
构建产物、环境资格记录、界面检查和最终运行结果须另附机器证据，不能仅凭本设计说明宣称验收通过。

## 2026-09-26 补充：闭环缺口

- 草案在支持时附带模板的方法与验收规则（`TEMPLATE_METHOD`：网络、训练、采样、权重、种子、精度、参考解、验收、验证链、结论规则）。模型确认对整个草案取哈希，因此人确认的就是界面上显示的方法；测试保证摘要与 `pinn/research/poisson1d-config.json` 一致。
- 提示词写明模板冻结的设置不属于「缺失」；`missing` 只用于用户未给出的问题定义信息。
- 方程匹配改为确定性规范化：只接受同一方程的几种等价写法（π/pi、全角符号、上标、`d²u/dx²`、移项），不同方程一律不支持；保留用户原写法。
- 新操作 `fork`：以已有任务的草案新建任务，需重新确认模型；原任务、其运行数据与预留的 Claim 集原样保留。用于准备失败、计算中断/取消/超时/停止之后的重试。
- 准备超时（300 秒）记录为 `PREPARATION_TIMED_OUT` 事件并保存日志，不再表现为笼统的不可用。
- 运行确认前会先结清其他任务的过期「运行中」状态；真正仍在运行的任务照旧阻止新的运行确认。
