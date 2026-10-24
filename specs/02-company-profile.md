# DV-02 公司身份

状态：Proposed；版本：1.0；日期：2026-10-25。
关联：[Issue #4](https://github.com/Ethanwu23/DeepValue/issues/4)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

代码、CIK、名称及 SIC 的身份核验；在 define_scope 中执行。

非目标：历史证券主数据数据库、自动纠正 CIK、模型猜测公司身份。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/sec.py:collect 公司身份部分。

将身份职责从财务采集分离；保留代码与行业拒绝规则。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：ResearchRequest、SEC submissions 响应。
- 输出：CompanyProfile 或 IDENTITY_MISMATCH / UNSUPPORTED_INDUSTRY / SOURCE_ERROR。
- 依赖：DV-01、DV-15。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 使用指定 CIK 获取 submissions；请求 ticker 必须在返回 tickers 中，SIC 必须为整数 3500–3599。
2. 保存 name、ticker、cik、sic、sic_description、source_url、retrieved_at；metadata_basis 固定 current，报告必须披露不是历史身份快照。
3. 缺字段或类型错误是 SOURCE_SCHEMA_ERROR，不解释为空公司；身份不符时立即结束，不调度其他采集。
4. 公司端点在同一运行只取得一次，供后续 SEC 采集复用；身份请求计入外部请求预算。
5. 元数据变化不能自动改变本次 scope；新 run 才重新取得。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-02-AC-01 | 身份匹配 | SEC 返回 CAT 和 SIC 3531 | 核验 CIK18230 | 返回可追溯 CompanyProfile |
| DV-02-AC-02 | 代码冲突 | CIK 对应公司 tickers 不含请求代码 | 核验 | IDENTITY_MISMATCH，尚无报告或估值 |
| DV-02-AC-03 | 行业越界 | SIC 为 6000 或为空 | 核验 | 分别返回 UNSUPPORTED_INDUSTRY 或 SOURCE_SCHEMA_ERROR |
| DV-02-AC-04 | 历史边界 | 截止日早于元数据取得日 | 构造 profile | 明确 current，不声称历史身份验证通过 |
| DV-02-AC-05 | 网络失败 | 身份接口持续超时 | 有限重试结束 | 运行 failed，不能改用网页搜索猜身份 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/company/；integrations/sec.py。
- 计划测试：`tests/features/test_company_profile.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
