# 修宪登记簿 — Constitutional Amendments

本目录是《Leo AI PINN 闭环科研宪法》第六十条要求的修宪记录。

## 规则

1. 宪法正文只能通过正式 Constitutional Amendment 修改。直接编辑 `PINN_RESEARCH_CONSTITUTION.md` 而不在本目录留下对应记录的行为，一律视为**违宪修改**，必须回滚。
2. 修宪必须**先于**受新规则影响的实验。
3. **禁止在看到实验失败后，通过修宪 retroactively 将失败变成 PASS。**
4. 旧实验仍按其运行时生效的宪法版本审计。因此每个 ExperimentRun 必须记录它所遵守的 `constitutionVersion`。

## 文件命名

```
AMENDMENTS/A-0001-<kebab-case-slug>.md
```

编号一经分配不得复用，即使该修宪案被否决（否决同样留档，状态写 `REJECTED`）。

## 模板

```markdown
---
amendmentId: A-0001
oldVersion: 1.0
newVersion: 1.1
status: PROPOSED | ACCEPTED | REJECTED
effectiveDate: YYYY-MM-DD
proposedBy: <人 或 Agent 角色>
---

## reason
为什么现行条款不足以支撑科研完整性。

## affectedArticles
- 第 X 章：<改前 → 改后>

## scientificJustification
科学论证。不得写"为了让实验通过"。若真实动机是让某次实验通过，
本修宪案必须直接标记 REJECTED。

## impactOnExistingRuns
明确列出：哪些已有 Run 受影响、是否需要重新审计、旧结论是否降级。

## consequence
新规则生效后被禁止 / 被允许的具体行为。
```

## 登记表

| amendmentId | oldVersion | newVersion | status | effectiveDate | 摘要 |
| --- | --- | --- | --- | --- | --- |
| —— | —— | 1.0 | ACCEPTED | 2026-09-04 | 宪法初始建立，无前置版本。 |
| A-0001 | 1.0 | 1.1 | ACCEPTED（第 3 稿，用户 2026-09-15 终审通过；宪法正文已更新为 1.1，Poisson v1.0 草案已重绑定，见操作日志 §5.17） | 2026-09-15 |
| A-0002 | 1.1 | 1.2 | ACCEPTED（第 3 稿，用户 2026-09-15 终审通过；宪法正文已更新为 1.2，Poisson v1.0 草案已重绑定，见操作日志 §5.21；dependsOn A-0001 ACCEPTED @ 1.1，由 `amendments.py` R1–R5 校验并挂进 PRELOCK） | 2026-09-15 | 可接受矩阵增八格（DeepSeek 三格 + 复审两格 + 闭合审计三格），受控干预与确定性重放为命名容量 / 采样 / 非确定实现的前提，sSeedSensitive → 规格限定为非预期不可识别性（P34 可识别性记录），矩阵范围 forward-problem MVP，explainedSignatures + 症状覆盖不变量防挑症状；矩阵与义务按宪法版本分表、PROPOSED 期间 1.2 不可达；代码与测试已同步，宪法 1.2 与草案重绑定待 ACCEPTED | 可信闭环：可信度向量与弱链演算、INV-A1 与规格级检查注册表、两层诊断（根因须排除其余候选）、评估集样本级互斥、claim 集哈希链账本、seed 分档与无除法离散度、统一的执行环境身份（C3 = G6）、RunRecord / DiagnosisRecord 契约、G5a/G5b、Red Team 三层制、EXPLORATORY 第二来源；配套 schema 1.2、代码与测试见 `pinn/governance/`、`tests/pinn/` | 
