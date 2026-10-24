# DV-04 财务事实

状态：Proposed；版本：1.0；日期：2026-10-25。
关联：[Issue #6](https://github.com/Ethanwu23/DeepValue/issues/6)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

固定 US-GAAP 年度合并口径及确定性校验；供财务门禁和估值使用。

非目标：自动标签猜测、模型填数、会计重述、工业分部拆分、DCF。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/sec.py:METRICS、collect 指标提取；workflow.py:validate_evidence。

保留同申报、期间与平衡检查；从提取中分离质量结果，移除宽泛 issues 字符串协议。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：FilingSet、Company Facts、机械制造业指标契约。
- 输出：FinancialFact[]、FinancialQualityResult、ResearchGap[]。
- 依赖：DV-03、DV-08。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 保留现有七项明确映射：revenue=Revenues；profit=ProfitLoss；operating_cash=NetCashProvidedByUsedInOperatingActivities；capex=PaymentsToAcquirePropertyPlantAndEquipment；eps=EarningsPerShareDiluted；assets=Assets；liabilities_equity=LiabilitiesAndStockholdersEquity。
2. 仅 eps 使用 USD/shares，其余 USD。前五项为 duration，后两项 instant；每个值保存 tag、unit、start/end、filed、accession、evidence_id。
3. 必须同 accession、同期间末、披露不晚于 cutoff；duration 为 330–380 天且流量起始日一致。instant 不接受 start。
4. 同 start/end/value 的重复事实可合并；候选值不唯一或缺失产生缺口，不能将别的概念作为别名兜底。行业资格不保证每家公司满足这套指标契约。
5. 所有数值用 Decimal；资产和负债权益差异 <= max(1 USD, abs(assets)*0.0001)，capex >= 0。七项均为 v1 数据门禁必需项。
6. 要求 years 个最近且连续完整财年。非正 EPS 是估值方法不适用，不是财务事实无效。
7. 生成的中文财务摘录标注 derived_summary；它的事实来源是 XBRL 字段路径，不能作为 SEC 自然语言原文引用。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-04-AC-01 | 口径匹配 | 一个 accession 含多个单位及期间 | 提取 | 仅返回契约允许的年度 USD/每股单位事实 |
| DV-04-AC-02 | 概念缺失 | Revenues 不存在而其他收入概念存在 | 提取 | 返回 MISSING_METRIC，不自动替换 |
| DV-04-AC-03 | 冲突值 | 同 accession 同期有两个不同值 | 校验 | 返回 CONFLICTING_FACT，保留候选来源 |
| DV-04-AC-04 | 平衡与符号 | 资产平衡差超过阈值或 capex 为负 | 校验 | 财务门禁 blocked |
| DV-04-AC-05 | 非正盈利 | 事实完整但 EPS 为零 | 校验 | 财务数据可用，由估值模块判 not_applicable |
| DV-04-AC-06 | 摘录身份 | 根据数值生成中文财务摘要 | 登记证据 | 标记 derived_summary，记录到源字段的依赖 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/financials/facts.py、quality.py。
- 计划测试：`tests/features/test_financial_facts.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
