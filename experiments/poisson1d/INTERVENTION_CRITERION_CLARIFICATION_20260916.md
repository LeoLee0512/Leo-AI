# 受控干预准则的前瞻性澄清（2026-09-16，post-audit）

适用范围：**只对未来的干预实验**。Experiment 3 的历史裁决（rSpecDefect，按预注册第 6 节）保持不变；本文件不回溯任何 verdict。

## 1. 暴露的问题

`EXPERIMENT3_PREREGISTRATION_20260916.md` 第 3 节把配对准则（median 比 < ρ、配对改善比例 ≥ q）要求在**每一对相邻档**上独立成立。3A 的实际数据：10→100 未达（ratio 0.571、6/10），100→1000 强烈达标（ratio 0.163、10/10）。逐对要求让一段弱响应否决了整条剂量—响应曲线的强证据，决策树因此进入 6.2 分支。这是准则结构问题，不是数据问题。

## 2. 前瞻性准则结构（已澄清；数值常数待预注册）

对预注册的单因子档位 λ₁ < λ₂ < … < λ_k，配对 seed N ≥ 10，在**整条曲线**上定义：

- R = median E(λ_high) / median E(λ_low)，其中 low / high 为预注册的曲线两端（不是相邻档）；
- Q = #{i : E_i(λ_high) < E_i(λ_low)} / N（配对）；
- 单调性：各档 median 沿预注册方向不增（允许弱单调，不要求每段都过强阈值）；
- 退化限：所有其它关键指标（solution error、PDE error 等）在每一档都不超过预注册的 degradation limit。

判定：R < ρ 且 Q ≥ q 且单调性成立且无退化 → 干预支持该因子为根因；否则不支持。

## 3. 常数

`criteria.py` 现行 ρ = 0.5（来源 P23 的 0.5 倍规则）、q = 0.8（来源 10.1 的 0.8 线）是**相邻档**版本的常数。整条曲线版本的 ρ / q 是否沿用同一来源、是否需要更严，**不在本轮决定**——不得用本次 3A 数据倒推一个刚好通过的值。

```text
criterion structure clarified;
numeric constants to be preregistered before the next applicable experiment
```

## 4. 与历史的关系

```text
Experiment 3 historical diagnosis remains unchanged.
New criterion is prospective only.
```

`pinn/experiments/criteria.paired_intervention_errors`（相邻档版本）继续作为已冻结实验的记录依据；整条曲线版本在下一次适用实验的预注册文件中给出常数后再实现，并配 regression tests。
