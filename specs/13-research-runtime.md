# DV-13 研究运行编排

状态：Proposed；版本：1.0；日期：2026-10-25。
关联：[Issue #15](https://github.com/Ethanwu23/DeepValue/issues/15)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

保留 LangGraph，按 README 最终图组织节点并明确异常出口。

非目标：微服务、通用插件系统、分布式任务平台、外部供应商强制撤回已发送请求。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/workflow.py 图构建；models.py:ValueState；langgraph.json。

沿用 Send 与 StateGraph；按 batch barrier、结构化状态和共享预算重构，移除直接散布状态字典。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：验证请求、能力服务、运行上下文。
- 输出：RunEvent 流、冻结 ResearchResult、cancel acknowledgement。
- 依赖：全部能力，通过接口组合，不反向依赖 UI。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 运行状态 pending->running->completed/failed/cancelled；终态不可逆。研究质量与估值状态独立，不把 limited 变成 failed。
2. define_scope 完成身份核验后 plan_research；四个采集节点以 batch_id 汇合，全部派发任务成为 succeeded/partial/failed/cancelled 后只 normalize 一次。
3. 采集失败是结构化 CollectorResult，不吞异常为空成功；编程错误/状态不变量破坏为 failed。无任务时直接进入相应有限出口，不等待不存在的分支。
4. data_gate 只能 usable/repairable/unavailable；review 只能 sufficient/follow_up/limited。执行和路由使用显式 enum，不通过报告文本推断。
5. 统一预算见总规约；调用前原子预留，实际开始即记账。补查不能重置预算；重试不增加 batch 但消耗请求次数。
6. 同线程第二次提交建立新 run_id、清空工作集；同一 run 的重复事件以 event_id 去重，客户端只接收当前 run。
7. 取消先设置 cancel_requested；停止派发并取消可取消的 HTTP/模型任务，超过在途调用截止时间后丢弃晚到结果并置 cancelled。后端确认前 UI 不能显示已取消。
8. 截止时间耗尽且已有可审计数据时走 limited；取消不自动生成正式报告；内部异常 failed。报告生成本身失败不能假装 completed。
9. 事件包含 run_id、seq、timestamp、node、task_id、state、reason_code；禁止记录模型完整输入、密钥或请求体。
10. 重启后的 in-memory 运行不承诺恢复；API 返回 RUN_NOT_FOUND 并让 UI 显示失效。v1 不实现断点续跑。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

公共API、SSE重放、终态保留和单活跃研究规则见总规约9.1；由同一运行管理器实现，禁止直接暴露未经Context校验的研究入口。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-13-AC-01 | 并行汇合 | 四任务以不同顺序完成 | 运行 | 每批仅 normalize 一次且结果不依赖顺序 |
| DV-13-AC-02 | 修复闭环 | 关键数据可修复且有预算 | 运行 | repair->dispatch->normalize->validate |
| DV-13-AC-03 | 补查闭环 | 结论有可验证 gap | 运行 | follow_up 后重新分析、估值和审查 |
| DV-13-AC-04 | 取消竞态 | 取消后外部响应晚到 | 写结果 | 取消先置位时丢弃晚到数据；若completed先提交则取消返回completed，终态不互相覆盖 |
| DV-13-AC-05 | 预算耗尽 | 修复已用完所有轮次 | 尝试补查 | 不超预算，进入 limited |
| DV-13-AC-06 | 重复运行 | 同一线程再次提交公司 | 初始化 | 前次终态后新 run 不包含旧证据、报告或计数；前次仍活跃则409 RUN_ACTIVE |
| DV-13-AC-07 | 空调度 | 没有有效新任务 | 路由 | 直接有限出口，不死锁；已淘汰run读取返回404 |
| DV-13-AC-08 | 内部故障 | 能力抛出非预期编程异常 | 终止 | failed 并输出脱敏错误 ID |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 runtime/graph.py、state.py、budget.py、events.py。
- 计划测试：`tests/features/test_research_runtime.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
