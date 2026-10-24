# DV-05 研究规划与任务分发

状态：Proposed；版本：1.0；日期：2026-10-25。
关联：[Issue #7](https://github.com/Ethanwu23/DeepValue/issues/7)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

固定问题模板加用户重点；初始调度和两个补查入口共用任务契约。

非目标：让模型任意创建工具、改变研究范围、无限递归拆问题。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/workflow.py:plan_research、dispatch。

保留 LangGraph Send；将静态类别补查改为关联 question/gap 的确定性计划。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：ResearchContext、CompanyProfile、ResearchGap[]、BudgetLedger。
- 输出：ResearchQuestion[]、ResearchTask[]、本轮任务集合。
- 依赖：DV-01、DV-02、DV-13。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. v1 规划不调用模型。默认问题覆盖财务可用性、经营质量、资本配置、公司事件、行业需求与竞争、宏观和政策风险；focus 保存为补充重点，不替代必需问题。
2. 首次生成 financials/news/macro_policy/industry 四个逻辑任务。宏观与政策在同一节点内保留独立子结果；子请求仍计入全局预算。
3. 每项任务含 task_id、run_id、batch_id、category、question_ids、gap_ids、source、query、window、required_artifacts、reason(initial/repair/follow_up)。
4. task_id 由规范化任务内容和 run_id 生成；去除 query 首尾及重复空格，其他内容不任意变换。相同任务已经 terminal 不重复派发。
5. 补查只为有具体可验证 gap 且存在未执行查询/文档定位的任务生成；同参数重抓属于重试，不消耗一轮新研究来绕过重试上限。
6. 预算不足时按关键财务缺口、原有判断反证、其他必需问题的优先级，最后按 question_id 排序；未入队任务留下 BUDGET_EXHAUSTED。
7. 初始计划只分配任务；不得把任务已经派发或获得搜索结果当作证据覆盖完成。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-05-AC-01 | 初始计划 | 已确认公司与合法范围 | 规划 | 生成四类任务并关联必需问题 |
| DV-05-AC-02 | 定向修复 | 仅一个财年指标缺失 | 规划 repair | 只派发该事实所需来源，不重新采集全部类别 |
| DV-05-AC-03 | 任务去重 | 补查内容与已完成任务相同 | 分发 | 拒绝重复，保留 NO_NEW_TASK 原因 |
| DV-05-AC-04 | 共享轮次 | 初始和 repair 已用完两轮 | 申请 follow_up | 不派发，输出预算缺口 |
| DV-05-AC-05 | 并行预算 | 多个候选任务同时抢最后预算 | 预留 | 原子限额，不超发，顺序可解释 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/planning/；runtime/dispatch.py。
- 计划测试：`tests/features/test_research_planning.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
