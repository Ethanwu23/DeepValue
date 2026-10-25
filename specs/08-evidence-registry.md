# DV-08 证据登记与数据修复

状态：Accepted（随本 PR 合并到 dev 生效）；版本：1.0；日期：2026-10-25。
关联：[Issue #10](https://github.com/Ethanwu23/DeepValue/issues/10)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

统一证据、确定性合并、关键数据门禁及第一条闭环。

非目标：证据登记直接证明结论成立、模型挑选冲突财务数值。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/models.py:merge_records；workflow.py:normalize_evidence、validate_evidence。

消除 URL 单类别覆盖与宽泛字符串缺口；normalize 与 validate 成为独立可调用服务。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：本轮全部 CollectorResult、历史 EvidenceRegistry、FinancialQualityResult。
- 输出：EvidenceRegistry、DataGateResult、ResearchGap[]、repair tasks。
- 依赖：DV-03、DV-04、DV-05、DV-06、DV-07。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. evidence_id=SHA256(source_type + canonical_locator + content_hash)。URL 只移除 fragment、规范主机大小写和默认端口，不删除可能改变内容的查询参数。
2. 同来源同内容并集 categories/question_ids/task_ids，排序输出；同 URL 内容不同保留不同版本，不使用字典最后写入覆盖。
3. 财务使用 accession+字段定位；网页使用最终 URL+选定正文；政策使用文档号+正文版本；宏观使用 series+观测期+请求版本。合并必须与并发完成顺序无关。
4. 保留 accepted/rejected 状态、reason_code、时间依据、来源层级和截断标记。derived_summary 必须链接父事实，不计独立来源。
5. data_gate=usable 仅当所需 years 的七项财务事实及修订覆盖通过；其他来源缺口留给结论审查，不阻断财务分析。
6. 关键缺口同时满足可修复、存在新任务、全局预算允许时为 repairable；否则 unavailable，进入 limited 报告。若两轮用尽，不进入第三轮。
7. 缺口以 kind+subject+period+question_id 稳定标识；新证据满足验收谓词后才 resolved。调度完成或重试次数增加不会自动解决缺口。
8. 冲突始终保留候选值、来源和判定；不可通过删掉冲突值使门禁通过。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-08-AC-01 | 顺序无关 | 相同来源分别由两个分支返回 | 交换完成顺序 | 证据集合、主题和内容哈希完全相同 |
| DV-08-AC-02 | 来源更新 | 同 URL 返回不同内容 | 合并 | 保留两个版本而非覆写 |
| DV-08-AC-03 | 可修复缺失 | 关键事实缺失且有未执行的精确来源任务 | 门禁 | repairable 并关联 gap_id |
| DV-08-AC-04 | 耗尽预算 | 相同关键缺口仍在且已达上限 | 门禁 | unavailable，禁止分析估值 |
| DV-08-AC-05 | 语境缺失 | 财务完整但没有新闻 | 门禁 | usable；新闻 gap 进入审查和有限报告判定 |
| DV-08-AC-06 | 冲突未消除 | 修复拿到第三个冲突值 | 再次校验 | 保持冲突，不挑顺眼数值 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/evidence/；capabilities/planning/repair.py。
- 计划测试：`tests/features/test_evidence_registry.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
