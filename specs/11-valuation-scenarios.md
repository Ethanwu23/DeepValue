# DV-11 确定性估值

状态：Accepted（随本 PR 合并到 dev 生效）；版本：1.0；日期：2026-10-25。
关联：[Issue #13](https://github.com/Ethanwu23/DeepValue/issues/13)。公共约束：[总规约](00-system-contract.md)。本文件定义目标行为，不宣称已实现。

## 1. 目标与范围

近三年披露稀释 EPS 中位数乘 PE 的可复算情景。

非目标：DCF、正常化盈利调整、目标价、股价对比、安全边际、模型计算。

## 2. 现状、复用与变更

现有实现（相对 backend/src/agent，前端及根目录文件除外）：value/valuation.py:calculate。

复制现有中位数算法；修正 normalized_eps 命名、敏感性 float 及默认舍入不一致。

迁移必须先复制对应实现到目标模块再改写；新增能力没有既有实现时明确新增，不复制不相关代码。

## 3. 输入与输出

- 输入：合格 FinancialFact[]、PE 假设、FinancialQualityResult。
- 输出：ValuationResult(status,method,inputs,scenarios,sensitivity,reason)。
- 依赖：DV-01、DV-04。
- 数据字段、状态、日期和预算使用总规约，不自定义同义字段或隐式空成功。

## 4. 行为规则

1. 财务门禁不通过为 blocked；选最近连续三年，按 period_end 排序，不依赖输入列表顺序。
2. 三个 EPS 有任一 <=0 为 not_applicable；不会转绝对值或换估值方法。缺事实是 blocked，不是 not_applicable。
3. eps_median=median(三年 EPS)；每股值=eps_median*PE，币种 USD/share。删除 normalized_eps 字段，禁止正常化盈利命名。
4. 所有输入由十进制字符串构造 Decimal，精度28；最终展示值 ROUND_HALF_UP 至0.01。敏感性使用精确系数0.8/1.0/1.2，与主表同舍入。
5. 记录三个 fact_id、期间、原始 EPS、倍数、公式版本、舍入模式；JSON 金额用字符串，不经 float 中转。
6. 用户选择 4–5 年时全表展示，但本方法仍只用最新三年，报告明确披露。
7. blocked/not_applicable 结果不带价格数组；再次计算前删除旧结果，不把旧估值与新证据混用。

## 5. 失败、预算与安全

使用总规约 ErrorInfo 和全局 BudgetLedger；外部请求仅经 DV-15，实际发出前预留预算。业务缺口与系统异常分开，不以默认值、空对象、备用模型或备用来源掩盖错误。取消和终态优先级由 DV-13 统一控制，纯计算能力也不得提交已取消运行的结果。

本能力的特殊失败行为已在上面的规则与下面的场景中规定；不可恢复的供应商协议错误进入缺口，内部不变量错误由运行时标记 failed。

## 6. 验收场景

| 编号 | 场景 | Given | When | Then |
|---|---|---|---|---|
| DV-11-AC-01 | 正常情景 | EPS 为12.64、20.12、22.05，PE为10/15/20 | 计算 | 中位数20.12，结果201.20/301.80/402.40 |
| DV-11-AC-02 | 顺序变化 | 财年输入打乱 | 计算 | 仍选最近三年且结果一致 |
| DV-11-AC-03 | 非正EPS | 三年中有0或负数 | 计算 | not_applicable，不产生价格 |
| DV-11-AC-04 | 舍入边界 | 中位数1.005且PE为1/2/3 | 计算 | 第一情景1.01；敏感性基准同行与主表一致 |
| DV-11-AC-05 | 缺关键事实 | 财务门禁 blocked | 计算 | blocked，输出原因与依赖缺口 |
| DV-11-AC-06 | 五年请求 | 提供5年合格数据 | 计算 | 仅用最新3年，记录所有输入期间和选择规则 |

## 7. 实现及特征测试映射

- 目标实现：backend/src/deepvalue 下的 capabilities/valuation/。
- 计划测试：`tests/features/test_valuation_scenarios.py`；DV-14 的浏览器行为放在 `frontend/tests/research-workbench.spec.ts`，不重复用 Python 模拟 UI。
- 测试方法：固定输入和脱敏来源样本验证上述编号；涉及供应商的协议检查与真实接入验收分离；模型审查以固定合法/不合法输出验证路由和约束，不要求实时模型逐字相同。
- 当前阶段仅定义场景，不创建测试脚本。目标路径为计划，须与迁移矩阵一起随实现更新。

## 8. 完成条件

规约完成：所有规则有明确输入、输出、错误及可观察验收场景；与总规约无冲突，关联Issue可追踪。

能力完成：按spec实现、逐项特征测试通过、来源/错误/状态可追溯，更新README与CHANGELOG；不得仅因文档合并就关闭实现任务。
