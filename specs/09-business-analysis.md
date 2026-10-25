# DV-09 经营与风险分析

状态：Accepted（随本 PR 合并到 dev 生效）；版本：1.0；日期：2026-10-25。
关联：[Issue #11](https://github.com/Ethanwu23/DeepValue/issues/11)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

经营、盈利与现金流质量、资本配置、行业和政策风险的有界分析。

非目标：模型补数字、目标价、投资建议、模型自己获取外部资料或执行网页指令。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：workflow.py:analyze_business；models.py:Analysis/Claim；base_agent.py:JsonAgent。

保留 JsonAgent 结构化思路；将 facts、derived 和 inference 显式分类，限制模型计算及凭空推断。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：usable 财务事实、合格证据片段、问题、focus、模型配置。
- 输出：AnalysisResult：Claim[]、ResearchGap[]、模型调用溯源。
- 依赖：DV-04、DV-08、DV-15。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 最多 8 条原子判断，每条一个主要断言；类型分 fact/derived/inference，topic 为 business/quality/risk/policy/industry/macro。
2. 每条含 question_id、text、citations、premise_fact_ids、counterevidence_ids、assumptions；至少一个有效引用。推断必须列假设和不确定性，不包装成披露事实。
3. 输入片段采用稳定排序，财务和必需问题优先；总上限 48000 字符、单来源 6000 字符，记录遗漏列表及 INPUT_TRUNCATED 缺口。
4. 引文 8–350 字符，必须来自传入的片段；字段型财务引用使用 fact_id 和源字段，不把派生摘要当原文。
5. 模型不得增加未给出的数值或执行运算。增长率等派生值需引用确定性 DerivedFact；没有对应事实则改为问题。
6. 经营质量不能由单一现金流数字推定，护城河不能由营收增长推定；至少明确支持机制、反证和结论边界，交 DV-10 审查。
7. 结构不合法返回 MODEL_OUTPUT_INVALID，并按既定策略结束该分析，不以自由文本替代；输入/输出哈希、模型 ID、prompt_version 写入审计。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-09-AC-01 | 财务判断 | 提供事实及合法引文 | 分析 | 返回结构化原子 Claim 与依赖，不返回额外价格 |
| DV-09-AC-02 | 注入文本 | 网页要求忽略规则或执行工具 | 分析 | 作为数据处理，无额外工具调用 |
| DV-09-AC-03 | 凭空数字 | 模型输出未输入的增长率 | 结构审查 | 不接受为 derived fact，交审查拒绝 |
| DV-09-AC-04 | 派生摘要 | 证据是生成的中文财务摘要 | 引用 | 使用 fact_id，不声称 SEC 原文 |
| DV-09-AC-05 | 输入超长 | 资料超过输入上限 | 组装 | 确定性选片、记录遗漏及缺口 |
| DV-09-AC-06 | 无效 JSON | 模型返回不可解析内容 | 完成调用 | MODEL_OUTPUT_INVALID，不返回空成功 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/analysis/；contracts/claims.py。
- 计划测试：`tests/features/test_business_analysis.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
