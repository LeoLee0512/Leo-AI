# research-sop · 角色化科研 SOP（中文说明）

把一个开放性科研问题交给**五个子 agent 串成的流水线**跑完：文献综述员 → 建模员 → 数值实验员 → 验证员 → 论文撰写员。每一环只拿到自己需要的上游产物，产出一个固定结构的文件，再交给下一环；验证员发现问题可以把工作**打回**给对应角色重做。

- 归属：Leo 专属技能（`origin: leo`，MIT）。不修改 `upstream/OpenAI4S/`。
- 机制：全部走 `host.delegate`，角色人格写在请求正文里，**不依赖也不修改 `specialists.py`**。

## 怎么触发

在工作台的会话里直接说，例如：

> 用 research-sop 跑一遍：PINN 求解二维热传导方程的误差到底来自哪里。

或者在 Python cell 里直接调用：

```python
result = orchestrate_research(
    "PINN 求解二维热传导方程的误差来源",
    max_rollbacks=2,      # 验证员最多打回几次，默认 2
)
print(result["status"], result["paper"])
```

`kernel.py` 会随技能自动加载。若 `orchestrate_research` 不在 `dir()` 里，读一下本目录的 `kernel.py` 再 exec。

## 产物放在哪

全部写在**当前会话工作区**的 `research-sop/` 目录下：

| 文件 | 内容 |
|---|---|
| `01-literature-surveyor.md` / `.json` | 带 DOI 的文献综述 + 结构化记录 |
| `02-modeler.md` / `.json` | 方程、假设、边界条件、量纲分析 |
| `03-numerical-experimenter.md` / `.json` | 方法、结果、收敛性；代码与数据另存为 artifact |
| `04-validator.md` / `.json` | 验证结论 `verdict` + 具体问题 `findings` |
| `05-paper-writer.md` | 论文/报告草稿 |

`.md` 是给人读的文档，`.json` 是给流水线读的记录。要跨会话保留，让实验员/撰写员用 `host.save_artifact` 存成版本化产物。

## 断点续跑

`orchestrate_research` 每完成一个阶段就落盘。中断后**再调用一次同一个任务**即可继续：已经标记 `complete` 的阶段会被跳过，从下一个没做完的角色接着跑。

**续跑是绑定到研究问题本身的。** 每次运行都落在自己的目录 `research-runs/<run_id>/` 里，`run_id` 由任务文本的 SHA-256 推出，同目录下的 `manifest.json` 记录 `task_text` / `task_sha256` / `pipeline_version` / `role_prompt_hashes` / `model_fingerprint` / `created_at` / `parent_run_id`。因此：

- **同一个任务** → 复用已完成的阶段，接着往下跑；
- **不同任务** → 一定新建 run，绝不会读到别的课题的阶段；
- `resume=False` → 视为一次**明确的重做**：新建 run 并在 manifest 里记下 `parent_run_id`，**旧的那次原样保留**（删掉旧证据等于毁掉审计链）。

```python
sop_status(run_id)   # 只看某次运行的进度，不跑任何东西
sop_list_runs()      # 列出所有有 manifest 的运行
orchestrate_research(task, resume=False)   # 重做：新建 run，保留旧 run
```

返回的 `status` 说的是**实际跑了什么**，不是「函数走到了哪」：

| `status` | 含义 |
|---|---|
| `complete` | 五个角色全跑完 **且** 验证员通过 |
| `partial` | 只跑了一部分角色（例如传了 `roles=`） |
| `unresolved` | 在 `max_rollbacks` 次之内验证员始终没通过 |
| `blocked` | 有阶段没能完成 |

验证员没真的跑过，`validator` 就是 `None`；撰写员没真的产出文档，`paper` 就是 `None`。**不会出现「只跑了一个角色却报告有一篇通过验证的论文」这种事**——这正是修复前的行为。

> 注：OpenAI4S 的 host SDK 并没有 `list_session_checkpoints` 这个方法（原始需求文档里提到的那个接口不存在）。这里的续跑靠的是**磁盘上的阶段文件**，效果一样而且可审计。

### 阶段产物缺失 = 重跑该阶段

阶段的记录或它必须产出的文档不在了，就说明**这一阶段不再是 complete**。正确处理是
**重新执行该阶段并产出真实的新文档**，而不是把这次运行报告成「没有论文」。上游仍然有效的
阶段不会被重跑——恢复只针对真正坏掉的那一环。

`paper=None` 只在撰写员**确实没产出文档**时才是诚实答案；它不是「正确恢复」的定义。一个本可以
重跑却回答 `None` 的系统，是丢掉了完成工作的能力。绝对不允许的是反方向：`paper` 指向一个
并不存在的文件。

重跑时如果文档写不进去，`sop_write_stage` 会读回校验、校验不过就抛错——**整轮停下来，不返回
任何结论**。

### prompt 改了 = 旧 run 变成 incompatible，不是被作废删除

改动 `ROLE_MISSIONS` 会改变 `role_prompt_hashes`，此后所有在旧 prompt 下产生的 run 都属于
**另一套方法的运行**。三件事同时成立，很容易混淆：

- **字节仍在**——不删除、不覆盖、不改写；
- **仍可审计**——`sop_inspect_manifest` / `sop_list_runs` 照样返回它的 manifest，并标注
  `incompatible` 与具体原因；
- **但它不是新 pipeline 的证据**——`sop_read_manifest` 返回 `None`，它的阶段不会被新 run 采纳。

`sop_read_manifest` 问的是「这份 manifest 对我现在跑的这条 pipeline 有效吗」，所以返回 `None`
是正确的，并不代表这个 run 丢失或损坏。`incompatible` 与 `corrupt` 是刻意区分的两种状态：前者
是另一套方法的运行，后者是损坏。

## 打回重做

验证员的 `output` 必须带三个字段：

```json
{"verdict": "pass|revise|fail",
 "send_back_to": "modeler",
 "findings": ["边界条件与综述里的结论矛盾", "..."]}
```

只要 `verdict != "pass"`，编排器就会**清空 `send_back_to` 那一环及其所有下游**，把 `findings` 附在请求末尾重跑。超过 `max_rollbacks` 次仍未通过，整轮以 `status="unresolved"` 结束并把未解决的问题一并返回——不会把没通过的东西悄悄当成通过。

验证员返回无法解析的 verdict 时按 **fail** 处理，不按 pass 处理。

## 预算与深度

- 每个角色有独立的 `max_turns` 上限（实验员 60，综述员 40，验证员 32，撰写员 28，建模员 24），防止某一环卡死烧光会话。
- `retries=1`：单次瞬时失败会带着自己的 limitations 自动重跑一次。
- 委派深度上限是 4，`orchestrate_research` 自己占一层，所以角色内部还能再 fan-out（比如参数扫描），但**不要在子 agent 里再调用 `orchestrate_research`**。

## 实验环境约定

运行时已经预装了一整套科学计算栈：`numpy` / `scipy` / `pandas` / `matplotlib` / `sklearn` / `sympy` / `statsmodels` / `networkx` / `numba` / `h5py` / `plotly` / `seaborn`。差分、有限体积、小规模有限元、谱方法、最小二乘拟合、用 sympy 推解析解来做对照——这些**直接就能做**，实验员不要现场装重框架。

`torch` 和 `jax` **没有**预装。确实非要深度学习框架不可时，必须显式装 CPU 版：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

不要裸写 `pip install torch`——默认源给的是 CUDA 轮子，会连带 `nvidia-cudnn` 和 CUDA toolkit 拉好几个 GB。而且 kernel 跑在沙箱里，现场装的东西写进临时 `site-packages`，任务一结束就没了，下一轮还得再装一遍。

所以实验员的第一目标是**能证实或证伪建模员假设的最小可复现实验**，不是跑一次完整训练。一个实验如果需要几 GB 依赖才做得了，应该**降级**（解析解对比、截断误差与收敛阶分析、残差分布统计、把网络缩小到 scipy 优化器能训的规模），而不是停下来装依赖，并在阶段文件里写清楚为什么降级。

## 推荐的验收任务

要完整跑通五角色链，**优先选一个不需要深度学习框架的科研任务**（例如分析某类偏微分方程解的正则性或误差上界），这样实验环节用 numpy/scipy/sympy 就能做完，五个角色能一口气走到论文草稿。

一个可以直接照抄提交的任务：

> 用 research-sop 跑一遍：一维泊松方程 −u″ = f 在 [0,1] 上带齐次 Dirichlet 边界，当右端 f 只有有限正则性时（例如 f 含一个跳跃，或 f(x)=|x−1/2|^α 这类奇点），残差型（PINN 式最小二乘配点）近似解的 L² 误差能否由残差的 L² 范数控制，即先验界 ‖u−u_h‖_{L²} ≤ C(s)·‖R‖_{L²} 是否成立、常数 C(s) 随 Sobolev 正则性阶 s 如何退化？请依次走完文献综述、建模、数值实验、验证、论文撰写五个角色。

这个题目落在实分析 / PDE / PINN 误差理论里，是真问题；解析解和残差都能用 sympy 精确推出来，配点最小二乘用 numpy/scipy 解就行，α 扫一组值拟合 C(s) 的退化率即可，规模小到五个子 agent 能跑完。

## 不做的事

- 不写死领域。计算力学、PINN、传热的具体知识通过任务描述、同时加载的领域技能、以及综述员的检索进来。
- 不伪造。DOI 必须真的解析过才能出现；论文里的每个数字都要能追到一次真实跑过的实验；做不完的阶段就报做不完。
