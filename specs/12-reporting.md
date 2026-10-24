# DV-12 报告与导出

状态：Proposed；版本：1.0；日期：2026-10-25。
关联：[Issue #14](https://github.com/Ethanwu23/DeepValue/issues/14)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

write_report 与 write_limited_report 两个显式入口共享确定性模板。

非目标：报告阶段再调用模型生成新观点、有限报告掩盖阻断、公开原始抓取全文。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：workflow.py:write_report；frontend/src/App.tsx:download。

从 workflow 抽离模板，补统一报告数据模型和安全导出；不保留旧聊天导出路径。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：ResearchResult、已审查 Claims、财务与估值结果、完整缺口账本。
- 输出：ReportArtifact(Markdown)、ExportBundle(JSON)。
- 依赖：DV-08、DV-10、DV-11、DV-13。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 完整报告必须满足 sufficient；有限报告列出未解问题、失败原因、已用预算和停止依据。两者都包含固定截止日、来源时间边界和估值假设。
2. 报告只消费 supported 判断；uncertain/rejected 进入审查记录或待核实章节，不展示为主结论。推断清楚标注。
3. 关键数据 blocked 时保留可用事实但不显示估值；非关键研究 gap 可保留已计算情景，同时标为 limited。
4. 导出包含 schema_version、run_id、请求/配置非敏感快照、事实、证据摘录、引用定位、审查、任务账本、预算与终态。排除 token、HTTP认证头、环境变量原文及本地绝对路径。
5. 默认不打包第三方全文或原始响应；本地原始 artifact 保留 hash/locator，导出仅有必要摘录和来源链接。
6. Markdown 对表格分隔符、链接标题及不可信 HTML 做安全处理；仅允许安全 HTTP(S) 来源链接，不执行正文脚本。
7. 只允许 completed 终态导出正式报告；cancelled/failed 可查看诊断快照但不得标为正式完成报告。
8. 同一冻结 ResearchResult 重复渲染应字节一致，不把当前时间嵌入渲染结果；使用 run 的固定时间字段。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-12-AC-01 | 充分报告 | review=sufficient 且已冻结结果 | 渲染 | 进入完整出口，所有主结论可定位来源 |
| DV-12-AC-02 | 关键阻断 | 财务缺口 unresolved | 有限报告 | 保留事实与原因，绝不显示旧价格 |
| DV-12-AC-03 | 语境缺口 | 估值 calculated 但新闻缺口存在 | 渲染 | 有限报告可展示估值并清楚说明缺口 |
| DV-12-AC-04 | 导出脱敏 | 运行配置含凭据且正文含恶意链接 | 导出 | 无凭据/本地路径，危险链接不渲染 |
| DV-12-AC-05 | 结果一致 | 同一 run 在页面和 JSON 查看 | 对比 | 标的、截止日、终态与估值一致 |
| DV-12-AC-06 | 重复渲染 | 相同冻结结果输入两次 | 生成 Markdown | 字节一致 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/reporting/；contracts/result.py。
- 计划测试：`tests/features/test_reporting.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
