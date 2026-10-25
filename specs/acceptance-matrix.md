# 特征测试与验收映射

当前仅有验收场景，没有新增测试脚本；下表状态全部为“待实现、待测试”。构建CI通过不改变此状态。

## 验证层次

- 固定样本特征测试：脱敏/合成JSON、HTML、模型输出；固定时钟和预算，禁止外网。
- 供应商契约测试：验证MCP格式、HTTP错误、FRED历史区间、SEC索引边界；常规CI使用记录样本，不使用生产凭据。
- 真实验收：实现后单独执行CAT/2025-03-01/3年/2轮；记录接入是否成功、证据数量、拒绝原因、预算与报告状态，不要求网络必定产生充分报告。

规范性测试必须同时验证返回结果和被禁止的副作用，例如未来资料不进模型、取消后不写结果、数据缺失时不计算估值。

## 能力场景映射

| 场景编号 | 行为 | Spec | 计划验证位置 | 状态 |
|---|---|---|---|---|
| DV-01-AC-01 | 正常请求 | [DV-01](01-research-scope.md) | tests/features/test_research_scope.py | 待实现、待测试 |
| DV-01-AC-02 | 未来截止日 | [DV-01](01-research-scope.md) | tests/features/test_research_scope.py | 待实现、待测试 |
| DV-01-AC-03 | 非法数值 | [DV-01](01-research-scope.md) | tests/features/test_research_scope.py | 待实现、待测试 |
| DV-01-AC-04 | 时区边界 | [DV-01](01-research-scope.md) | tests/features/test_research_scope.py | 待实现、待测试 |
| DV-01-AC-05 | 模型范围 | [DV-01](01-research-scope.md) | tests/features/test_research_scope.py | 待实现、待测试 |
| DV-02-AC-01 | 身份匹配 | [DV-02](02-company-profile.md) | tests/features/test_company_profile.py | 待实现、待测试 |
| DV-02-AC-02 | 代码冲突 | [DV-02](02-company-profile.md) | tests/features/test_company_profile.py | 待实现、待测试 |
| DV-02-AC-03 | 行业越界 | [DV-02](02-company-profile.md) | tests/features/test_company_profile.py | 待实现、待测试 |
| DV-02-AC-04 | 历史边界 | [DV-02](02-company-profile.md) | tests/features/test_company_profile.py | 待实现、待测试 |
| DV-02-AC-05 | 网络失败 | [DV-02](02-company-profile.md) | tests/features/test_company_profile.py | 待实现、待测试 |
| DV-03-AC-01 | 未来申报 | [DV-03](03-financial-disclosures.md) | tests/features/test_financial_disclosures.py | 待实现、待测试 |
| DV-03-AC-02 | 历史修订 | [DV-03](03-financial-disclosures.md) | tests/features/test_financial_disclosures.py | 待实现、待测试 |
| DV-03-AC-03 | 重复年度 | [DV-03](03-financial-disclosures.md) | tests/features/test_financial_disclosures.py | 待实现、待测试 |
| DV-03-AC-04 | 修订阻断 | [DV-03](03-financial-disclosures.md) | tests/features/test_financial_disclosures.py | 待实现、待测试 |
| DV-03-AC-05 | 索引异常 | [DV-03](03-financial-disclosures.md) | tests/features/test_financial_disclosures.py | 待实现、待测试 |
| DV-03-AC-06 | 公告范围 | [DV-03](03-financial-disclosures.md) | tests/features/test_financial_disclosures.py | 待实现、待测试 |
| DV-04-AC-01 | 口径匹配 | [DV-04](04-financial-facts.md) | tests/features/test_financial_facts.py | 待实现、待测试 |
| DV-04-AC-02 | 概念缺失 | [DV-04](04-financial-facts.md) | tests/features/test_financial_facts.py | 待实现、待测试 |
| DV-04-AC-03 | 冲突值 | [DV-04](04-financial-facts.md) | tests/features/test_financial_facts.py | 待实现、待测试 |
| DV-04-AC-04 | 平衡与符号 | [DV-04](04-financial-facts.md) | tests/features/test_financial_facts.py | 待实现、待测试 |
| DV-04-AC-05 | 非正盈利 | [DV-04](04-financial-facts.md) | tests/features/test_financial_facts.py | 待实现、待测试 |
| DV-04-AC-06 | 摘录身份 | [DV-04](04-financial-facts.md) | tests/features/test_financial_facts.py | 待实现、待测试 |
| DV-05-AC-01 | 初始计划 | [DV-05](05-research-planning.md) | tests/features/test_research_planning.py | 待实现、待测试 |
| DV-05-AC-02 | 定向修复 | [DV-05](05-research-planning.md) | tests/features/test_research_planning.py | 待实现、待测试 |
| DV-05-AC-03 | 任务去重 | [DV-05](05-research-planning.md) | tests/features/test_research_planning.py | 待实现、待测试 |
| DV-05-AC-04 | 共享轮次 | [DV-05](05-research-planning.md) | tests/features/test_research_planning.py | 待实现、待测试 |
| DV-05-AC-05 | 并行预算 | [DV-05](05-research-planning.md) | tests/features/test_research_planning.py | 待实现、待测试 |
| DV-06-AC-01 | 合法文章 | [DV-06](06-web-research.md) | tests/features/test_web_research.py | 待实现、待测试 |
| DV-06-AC-02 | 推荐日期 | [DV-06](06-web-research.md) | tests/features/test_web_research.py | 待实现、待测试 |
| DV-06-AC-03 | 晚修改 | [DV-06](06-web-research.md) | tests/features/test_web_research.py | 待实现、待测试 |
| DV-06-AC-04 | 搜索无正文 | [DV-06](06-web-research.md) | tests/features/test_web_research.py | 待实现、待测试 |
| DV-06-AC-05 | 跨类别同源 | [DV-06](06-web-research.md) | tests/features/test_web_research.py | 待实现、待测试 |
| DV-06-AC-06 | 网络边界 | [DV-06](06-web-research.md) | tests/features/test_web_research.py | 待实现、待测试 |
| DV-07-AC-01 | 修订隔离 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-07-AC-02 | 观测早发布晚 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-07-AC-03 | 缺失宏观值 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-07-AC-04 | 政策状态 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-07-AC-05 | 仅摘要 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-07-AC-06 | 查询关联 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-07-AC-07 | 部分成功 | [DV-07](07-macro-policy.md) | tests/features/test_macro_policy.py | 待实现、待测试 |
| DV-08-AC-01 | 顺序无关 | [DV-08](08-evidence-registry.md) | tests/features/test_evidence_registry.py | 待实现、待测试 |
| DV-08-AC-02 | 来源更新 | [DV-08](08-evidence-registry.md) | tests/features/test_evidence_registry.py | 待实现、待测试 |
| DV-08-AC-03 | 可修复缺失 | [DV-08](08-evidence-registry.md) | tests/features/test_evidence_registry.py | 待实现、待测试 |
| DV-08-AC-04 | 耗尽预算 | [DV-08](08-evidence-registry.md) | tests/features/test_evidence_registry.py | 待实现、待测试 |
| DV-08-AC-05 | 语境缺失 | [DV-08](08-evidence-registry.md) | tests/features/test_evidence_registry.py | 待实现、待测试 |
| DV-08-AC-06 | 冲突未消除 | [DV-08](08-evidence-registry.md) | tests/features/test_evidence_registry.py | 待实现、待测试 |
| DV-09-AC-01 | 财务判断 | [DV-09](09-business-analysis.md) | tests/features/test_business_analysis.py | 待实现、待测试 |
| DV-09-AC-02 | 注入文本 | [DV-09](09-business-analysis.md) | tests/features/test_business_analysis.py | 待实现、待测试 |
| DV-09-AC-03 | 凭空数字 | [DV-09](09-business-analysis.md) | tests/features/test_business_analysis.py | 待实现、待测试 |
| DV-09-AC-04 | 派生摘要 | [DV-09](09-business-analysis.md) | tests/features/test_business_analysis.py | 待实现、待测试 |
| DV-09-AC-05 | 输入超长 | [DV-09](09-business-analysis.md) | tests/features/test_business_analysis.py | 待实现、待测试 |
| DV-09-AC-06 | 无效 JSON | [DV-09](09-business-analysis.md) | tests/features/test_business_analysis.py | 待实现、待测试 |
| DV-10-AC-01 | 假引用 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-10-AC-02 | 真引用弱结论 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-10-AC-03 | 错误期间 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-10-AC-04 | 明确推断 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-10-AC-05 | 补查触发 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-10-AC-06 | 不能继续 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-10-AC-07 | 审查失败 | [DV-10](10-claim-review.md) | tests/features/test_claim_review.py | 待实现、待测试 |
| DV-11-AC-01 | 正常情景 | [DV-11](11-valuation-scenarios.md) | tests/features/test_valuation_scenarios.py | 待实现、待测试 |
| DV-11-AC-02 | 顺序变化 | [DV-11](11-valuation-scenarios.md) | tests/features/test_valuation_scenarios.py | 待实现、待测试 |
| DV-11-AC-03 | 非正EPS | [DV-11](11-valuation-scenarios.md) | tests/features/test_valuation_scenarios.py | 待实现、待测试 |
| DV-11-AC-04 | 舍入边界 | [DV-11](11-valuation-scenarios.md) | tests/features/test_valuation_scenarios.py | 待实现、待测试 |
| DV-11-AC-05 | 缺关键事实 | [DV-11](11-valuation-scenarios.md) | tests/features/test_valuation_scenarios.py | 待实现、待测试 |
| DV-11-AC-06 | 五年请求 | [DV-11](11-valuation-scenarios.md) | tests/features/test_valuation_scenarios.py | 待实现、待测试 |
| DV-12-AC-01 | 充分报告 | [DV-12](12-reporting.md) | tests/features/test_reporting.py | 待实现、待测试 |
| DV-12-AC-02 | 关键阻断 | [DV-12](12-reporting.md) | tests/features/test_reporting.py | 待实现、待测试 |
| DV-12-AC-03 | 语境缺口 | [DV-12](12-reporting.md) | tests/features/test_reporting.py | 待实现、待测试 |
| DV-12-AC-04 | 导出脱敏 | [DV-12](12-reporting.md) | tests/features/test_reporting.py | 待实现、待测试 |
| DV-12-AC-05 | 结果一致 | [DV-12](12-reporting.md) | tests/features/test_reporting.py | 待实现、待测试 |
| DV-12-AC-06 | 重复渲染 | [DV-12](12-reporting.md) | tests/features/test_reporting.py | 待实现、待测试 |
| DV-13-AC-01 | 并行汇合 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-02 | 修复闭环 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-03 | 补查闭环 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-04 | 取消竞态 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-05 | 预算耗尽 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-06 | 重复运行 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-07 | 空调度 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-13-AC-08 | 内部故障 | [DV-13](13-research-runtime.md) | tests/features/test_research_runtime.py | 待实现、待测试 |
| DV-14-AC-01 | 新请求隔离 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-14-AC-02 | 状态分离 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-14-AC-03 | 取消未确认 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-14-AC-04 | 晚到事件 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-14-AC-05 | 配置失败 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-14-AC-06 | 导出正确 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-14-AC-07 | 可访问性 | [DV-14](14-research-workbench.md) | frontend/tests/research-workbench.spec.ts | 待实现、待测试 |
| DV-15-AC-01 | 缺配置 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |
| DV-15-AC-02 | 导入隔离 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |
| DV-15-AC-03 | 协议破坏 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |
| DV-15-AC-04 | 网络重试 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |
| DV-15-AC-05 | 结构失败 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |
| DV-15-AC-06 | 日志脱敏 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |
| DV-15-AC-07 | 生命周期 | [DV-15](15-platform-integrations.md) | tests/features/test_platform_integrations.py | 待实现、待测试 |

## 端到端场景

总规约DV-00-AC-01至DV-00-AC-10分别覆盖完整结果、修复、补查、关键阻断、语境缺口、估值不适用、取消、运行隔离、历史时点和并行顺序。
计划落点：tests/acceptance/test_research_flow.py；固定替身完成可重复路由验证。真实CAT验收结果另外记录，不以模型逐字文本作为快照断言。

## 完成记录要求

实现后每个编号填入测试名称、通过证据及关联PR；如验收发现现有缺陷，按spec修复而非把缺陷加入快照。
模型支持性判断另保留人工复核样本集，包括“真引用但推断过度”；模型输出结构测试不等于语义可靠性已得到证明。
