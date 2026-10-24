# DV-07 宏观数据与政策原文

状态：Proposed；版本：1.0；日期：2026-10-25。
关联：[Issue #9](https://github.com/Ethanwu23/DeepValue/issues/9)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

v1 宏观选择 INDPRO 月度工业生产指数；政策选择 Federal Register 检索与正文，保留官方版本链接。

非目标：全面宏观数据库、经济预测、法律意见、推断公司一定受益/受损。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/evidence.py:collect_policy；宏观数据当前未实现。

保留政策日期和域名检查，改为消费 task.query；摘要仅可作为检索候选，不计正文覆盖。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：macro_policy ResearchTask、cutoff、配置 FRED_API_KEY。
- 输出：MacroObservation[]、PolicyEvidence[]、各子能力 ResearchGap[]。
- 依赖：DV-05、DV-08、DV-15。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. FRED observations 显式指定 series_id=INDPRO、realtime_start=realtime_end=as_of、observation_start=as_of-730天、observation_end=as_of、units=lin、output_type=1、file_type=json。
2. 使用历史实时区间取得 cutoff 可见版本；记录请求版本日期、响应实时区间、观测日期、数值、单位和频率。请求实时区间不能冒充逐项原始发布日期。
3. INDPRO 为总体工业生产而非机械行业专属；报告必须说明。缺失值 '.' 标记 missing，不转零、不插值、不调用当前版本替代。单位/频率元数据来自服务响应并保存；单位变更冲突不得拼接。
4. 按观测期排序，最多取最近 24 个有效月值；至少 13 个连续月值才允许计算最近月同比，公式为 (current/year_ago-1)*100，使用 Decimal。不足时保留可用观察并记录缺口。
5. 政策查询由任务传入，不硬编码 manufacturing tariffs。截止日前一年最多 3 个文档；保留 document_number、publication_date、type、正文地址、官方 PDF 链接及正文哈希。
6. 正文从该文档关联的 FederalRegister.gov XML/HTML 表示取得，记录其法律版本身份；法律生效/义务断言须核对对应 govinfo 官方版本，未核验则标记未核实，不作确定结论。
7. publication_date 与 effective_date 分开保存。提案、通知、调查不能当作生效规则；适用性默认为 unknown，仅在有正文条款与公司业务证据时允许形成待审查推断。
8. FRED 子任务失败不覆盖政策成功结果，反之亦然；二者各自形成缺口。已启用宏观的运行配置缺 FRED_API_KEY 时在启动校验失败，不运行中悄悄跳过。
9. 没有检索到政策只能表达指定查询/窗口未找到，不等于不存在政策风险。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-07-AC-01 | 修订隔离 | 同月在 cutoff 前后数值不同 | 查询历史版本 | 仅使用 cutoff 可见值并记录请求版本 |
| DV-07-AC-02 | 观测早发布晚 | 观测月在 cutoff 前但当时尚未公开 | 取得历史响应 | 不以当前值补上该月 |
| DV-07-AC-03 | 缺失宏观值 | 响应含 '.' 或月序列不连续 | 计算同比 | 不插值，必要时不计算并说明缺口 |
| DV-07-AC-04 | 政策状态 | 正文是拟议规则或调查通知 | 分析 | 不得输出已经生效 |
| DV-07-AC-05 | 仅摘要 | 政策摘要可得而正文失败 | 登记 | 保留候选与失败原因，正文问题未解决 |
| DV-07-AC-06 | 查询关联 | repair 指定不同政策查询 | 采集 | 实际使用新查询，不再次固定查询词 |
| DV-07-AC-07 | 部分成功 | 宏观接口失败、政策正文成功 | 合并 | 保留政策证据及宏观缺口，不清空整个节点 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/macro_policy/；integrations/fred.py、federal_register.py。
- 计划测试：`tests/features/test_macro_policy.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
