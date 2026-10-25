# DV-10 结论审查与补充研究

状态：Accepted（随本 PR 合并到 dev 生效）；版本：1.0；日期：2026-10-25。
关联：[Issue #12](https://github.com/Ethanwu23/DeepValue/issues/12)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

引用完整性、事实支持、推断边界、反证与第二条闭环。

非目标：自动审查等同人工审计、用重复来源提升置信度、只看类别非空。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：workflow.py:review_thesis、research_route。

引用存在升级为支持性分层审查；用问题和前提缺口取代 missing_categories 判断。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：AnalysisResult、Registry、问题覆盖、ValuationResult、预算。
- 输出：ClaimReview[]、ReviewDecision、FollowUpTask[]。
- 依赖：DV-05、DV-08、DV-09、DV-11。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 先做确定性检查：来源存在且 accepted、片段定位和 hash 匹配、财务字段与数值/单位/期间一致、derived 公式来自计算模块。失败即 rejected。
2. 文字片段只允许统一换行及连续空白，不更改标点、数字或词语；保存原文定位，不用宽松相似度冒充逐字引用。
3. 通过结构检查后使用独立审查提示词检查断言与前提支持关系，输出 supported/unsupported/uncertain、reason、引用前提、缺失前提及反证。相同模型可以审查，但不称独立第三方认证。
4. fact 仅在来源直接陈述该事实时为 supported；inference 即使支持充分也保留推断标签，不能升级 fact。复合断言缺任一关键前提即 uncertain。
5. 数值事实不能自动证明质量强劲、护城河、因果或政策适用；缺支持的判断排除主结论并形成具体 gap。
6. 所有必需问题已回答、无未解决实质 gap、无关键数据阻断且至少一条 supported 判断，才 sufficient。正常范围限制不作为无穷补查理由；not_applicable 估值可与 sufficient 研究共存。
7. 存在可验证 gap、新任务及剩余预算则 follow_up；否则 limited。模型无效输出形成 review gap，不能把未经审查判断送完整报告。
8. follow_up 进入分发后必须重新 normalize、validate、analyze、calculate、review；任何旧分析结果因事实版本变化而失效。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-10-AC-01 | 假引用 | 引文不在输入片段 | 审查 | rejected 并标记原文匹配失败 |
| DV-10-AC-02 | 真引用弱结论 | 引用单年经营现金流却断言护城河强 | 审查 | unsupported/uncertain，不进入主结论 |
| DV-10-AC-03 | 错误期间 | 数值真实但句子财年错误 | 审查 | 确定性拒绝 |
| DV-10-AC-04 | 明确推断 | 前提有来源且假设明确 | 审查支持 | 保持 inference 标签并展示边界 |
| DV-10-AC-05 | 补查触发 | 存在可验证前提缺口且剩一轮 | 路由 | 只补对应任务，完成后重新走完整审查链 |
| DV-10-AC-06 | 不能继续 | 有缺口但无新查询或预算已耗尽 | 路由 | limited，不循环 |
| DV-10-AC-07 | 审查失败 | 审查模型返回无效结构 | 路由 | 记录 REVIEW_FAILED，不输出完整结论 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/review/；capabilities/planning/follow_up.py。
- 计划测试：`tests/features/test_claim_review.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
