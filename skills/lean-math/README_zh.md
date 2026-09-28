# lean-math · Lean 4 + Mathlib 证明助手（中文说明）

让 Leo 能**真的编译** Lean 4 证明、**精确定位**每一处错误（行、列、报错信息、当前 goal），并查 mathlib 里某个定理**到底存不存在**。这是「教练模式」的底座：证明要么过要么不过，编译器说了算。

- 归属：Leo 专属技能（`origin: leo`，MIT）。不修改 `upstream/OpenAI4S/`。
- 环境：WSL2 Ubuntu-24.04 里已装好的 Lean **4.34.0-rc2** + 完整预编译 mathlib4。本技能不安装任何东西。

## 三个实测结论（决定了整个实现）

1. **`lake env lean` 的报错走 stderr，而且有错也返回 exit 0。** 直接调 `lean`（自己准备好 `LEAN_PATH`）报错走 stdout、有错返回 1。所以 `kernel.py` 走直接调 `lean` 这条路，并且**永远从解析出来的诊断判断成败，不看退出码**。
2. `lean --json` 每条诊断一个 JSON 对象，自带精确的 `pos` / `endPos`（行、列）。所以这里**没有一行正则去解析 Lean 的人话**，行列号是 Lean 自己给的。
3. `import Mathlib` 单次约 **30 秒**；把 import 缩到 `Mathlib.Tactic.NormNum` 实测 9.3 秒 vs 28.1 秒。`LEAN_PATH` 只算一次并缓存；真正能提速的只有**缩小 import 范围**，`lean_check(..., imports=...)` 就是干这个的。

另外：toolchain 是解压 tarball 装的，**不能调 `elan default`**（它会联网并失败）。全部用绝对路径。

## 常用函数

```python
lean_toolchain_status()      # 先跑这个：装了什么、mathlib 在不在、LEAN_PATH 几条，不编译

lean_check("""
example (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b
""")
# -> {"ok": True, "elapsed": 29.9, "errors": [], "warnings": [], "infos": [],
#     "uses_sorry": False, "header_lines": 2, "returncode": 0, ...}
```

代码里没有 `import` 时会自动补 `import Mathlib`，`header_lines` 告诉你补了几行，方便把 Lean 报的行号换算回你自己那段代码的行号。想快就缩小 import：

```python
lean_check("example : 2 + 3 = 3 + 2 := by norm_num\n", imports="Mathlib.Tactic.NormNum")
lean_check(code, imports=["Mathlib.Analysis.Calculus.Deriv.Basic", "Mathlib.Tactic"])
```

`imports=` 两种写法都行：光模块名（`"Mathlib.Tactic.NormNum"`）和完整 import 行（`"import Mathlib.Tactic.NormNum"`）都会拼成合法的头部，列表里也可以混着写。

### 读报错

```python
for e in result["errors"]:
    print(e["line"], e["col"], e["message"])
    print(e["source"])   # 出错那一行的原文
    print(e["goal"])     # Lean 打印的当前 goal（有的话）
```

实测例子（故意写错的证明）：

```
line 3 (代码第 1 行) col 23 [Tactic.unsolvedGoals] 'unsolved goals'
   source: 'example : 2 + 2 = 5 := by'
   goal  : '⊢ False'
line 8 (代码第 6 行) col 2 'No goals to be solved'
   source: '  exact foo'
```

`kind` 是 Lean 自己的错误分类（`Tactic.unsolvedGoals` 等），用它区分「战术块提前结束」和其它错误比看文字可靠。

### 看 goal 状态

```python
lean_goal("(a b : Nat) : a + b = b + a")                       # 初始 goal
lean_goal("(a b : Nat) : a + b = b + a", "rw [Nat.add_comm]")  # 走一步之后剩什么
```

故意不写完证明，让 Lean 报 unsolved goals 把状态打出来。返回 `closed=True` 且 `goals=None` 表示这些战术已经把证明做完了——这也是一个有用的答案。

### 查定理

```python
lean_check_type("Nat.add_comm")   # "Nat.add_comm : ∀ (n m : ℕ), n + m = m + n"；查不到返回 None  约 5 秒
lean_print("Nat.succ_le_of_lt")   # 完整声明                                                    约 5 秒
lean_exact("(a b : Nat) : a + b = b + a")     # 让 exact? 找一个能收尾的项                      约 13 秒
lean_loogle("Continuous ?f → Continuous ?g")  # 联网搜（走 host.web_fetch）                     约 1 秒
lean_find("_ + 0 = _")            # 按命题形状搜 mathlib —— 约 374 秒、约 8 GB 内存
```

这些耗时都是在这台机器上实测的，顺序有讲究：`#find` 第一次用会对整个 mathlib 建判别树，`_ + 0 = _` 实测 374 秒、内存峰值约 8 GB、返回 20 条（被 Lean 截断）。所以 `lean_find` 单独用 900 秒上限，超时返回 `timed_out: True` 而不是抛异常。**先试 `lean_exact` 或 `lean_loogle`**，只有问题确实是「按命题形状找」时才花这个钱。

**`lean_check_type` 返回 `None` 就是「mathlib 里没有这个名字」——直接这么说。** 编一个符合 mathlib 命名习惯、听起来很像的定理名，是这里最容易犯、用户最难当场识破的错误；有编译器在手就没有任何理由这么干。

`lean_exact` 给的是**建议不是事实**，拿到之后要用 `lean_check` 编译一遍再告诉用户「这个能用」。`lean_loogle` 的命中是线索，要用 `lean_check_type` 在本地确认。

## sorry 不算证明

```python
lean_check("theorem t (n : Nat) : n + 0 = n := by sorry")
# -> ok=False, uses_sorry=True
lean_check(..., allow_sorry=True)   # 明确要占位时才 ok=True
```

带 `sorry` 的文件是能「编译通过」的。本技能把它判为**不通过**，除非你显式传 `allow_sorry=True`。绝不要把一个把目标 admit 掉的文件报成「证明成功」。

## 教练模式的循环

1. `lean_goal` 看清楚到底要证什么。
2. 提一步，并结合 goal 说清楚为什么是这一步。
3. `lean_check` 编译当前的部分证明，把出错的**行、列、报错、剩余 goal** 原样报给用户。
4. 卡在找引理时：先 `lean_exact` / `lean_loogle`（秒级），实在要按形状搜再上 `lean_find`（分钟级）；拿到名字用 `lean_check_type` 确认。
5. 直到 `ok=True` 且 `uses_sorry=False`。

每一轮都要把编译结果如实说出来。「编过了」和「第 4 行挂了」都是好答案，「这样应该可以」不是——毕竟跑一次只要三十秒。

## 文件与写入

- 探针文件写在会话工作区的 `lean-probes/`（kernel cell 唯一可写的地方）。
- 发现到的 lake 项目与 Mathlib 目录**只读不写**，不会被删改。
- 路径不再写死。解析顺序：先看环境变量 `LEO_LEAN_TOOLCHAIN` / `LEO_LEAN_PROJECT` / `LEO_MATHLIB_DIR`，再找 home 下的 elan 安装，最后看 PATH 上的 `lean`/`lake`。
- 先调 `lean_toolchain_status()`，它只报告不安装，返回 `READY` / `NOT_INSTALLED` / `PROJECT_NOT_READY` / `VERSION_MISMATCH` 和一句可操作的说明。**不会**自动下载几个 GB 的工具链——那是你的决定。
- `timeout` 默认 300 秒；超时返回 `timed_out: True`，不抛异常。
- `LEAN_PATH` 优先用 `lake env printenv LEAN_PATH` 取（约 0.6 秒）并缓存；万一 lake 跑不了（例如项目被只读挂载），会退回按包目录 glob 拼出同样的路径，不碰项目。
