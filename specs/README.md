# DeepValue 规约索引

状态：Proposed；本目录是目标行为契约，当前代码仍为原型实现。顺序：先规约、再实现、再特征测试。

先读 [总规约](00-system-contract.md)，再读能力 spec、[迁移矩阵](migration-plan.md) 和 [验收矩阵](acceptance-matrix.md)。规则变更必须同时更新这些文档，不以新增 fallback 解决冲突。

| 能力 | Spec | Issue |
|---|---|---|
| DV-01 研究范围 | [规约](01-research-scope.md) | [#3](https://github.com/Ethanwu23/DeepValue/issues/3) |
| DV-02 公司身份 | [规约](02-company-profile.md) | [#4](https://github.com/Ethanwu23/DeepValue/issues/4) |
| DV-03 财报与市场数据 | [规约](03-financial-disclosures.md) | [#5](https://github.com/Ethanwu23/DeepValue/issues/5) |
| DV-04 财务事实 | [规约](04-financial-facts.md) | [#6](https://github.com/Ethanwu23/DeepValue/issues/6) |
| DV-05 研究规划与任务分发 | [规约](05-research-planning.md) | [#7](https://github.com/Ethanwu23/DeepValue/issues/7) |
| DV-06 新闻与行业研究 | [规约](06-web-research.md) | [#8](https://github.com/Ethanwu23/DeepValue/issues/8) |
| DV-07 宏观数据与政策原文 | [规约](07-macro-policy.md) | [#9](https://github.com/Ethanwu23/DeepValue/issues/9) |
| DV-08 证据登记与数据修复 | [规约](08-evidence-registry.md) | [#10](https://github.com/Ethanwu23/DeepValue/issues/10) |
| DV-09 经营与风险分析 | [规约](09-business-analysis.md) | [#11](https://github.com/Ethanwu23/DeepValue/issues/11) |
| DV-10 结论审查与补充研究 | [规约](10-claim-review.md) | [#12](https://github.com/Ethanwu23/DeepValue/issues/12) |
| DV-11 确定性估值 | [规约](11-valuation-scenarios.md) | [#13](https://github.com/Ethanwu23/DeepValue/issues/13) |
| DV-12 报告与导出 | [规约](12-reporting.md) | [#14](https://github.com/Ethanwu23/DeepValue/issues/14) |
| DV-13 研究运行编排 | [规约](13-research-runtime.md) | [#15](https://github.com/Ethanwu23/DeepValue/issues/15) |
| DV-14 研究工作台 | [规约](14-research-workbench.md) | [#16](https://github.com/Ethanwu23/DeepValue/issues/16) |
| DV-15 外部接入与运行配置 | [规约](15-platform-integrations.md) | [#17](https://github.com/Ethanwu23/DeepValue/issues/17) |

## 关键决策

- 模块化单体，沿用现有技术栈；能力不等于 Agent，不拆微服务。
- 两种补查共用 max_rounds，最多两批；数据修复必须先通过财务门禁。
- 运行终态、研究完整性、估值适用性分开，有限报告是显式业务结果。
- 财务数值和估值使用确定性计算；引文存在与结论受到支持分别检查。
- 宏观本轮选择 INDPRO 历史可见版本；政策补充正文和法律版本身份。
- 行情、安全边际和 DCF 不进入 v1 实现范围，目标图保留后续位置。
- 取消必须等后端确认；当前前端停止接收的行为不作为未来取消契约。
- 当前仅新增规约，没有业务实现或特征测试完成的声明。

## 审查与状态

本PR合并到dev后才将规约标记Accepted；实现中若发现不满足契约的供应商行为，先通过PR修改spec和验收，再改实现，禁止静默扩大支持范围。总任务[#1](https://github.com/Ethanwu23/DeepValue/issues/1)跟踪规约交付，能力Issue持续跟踪实现与测试。

本轮接口方案参考 [SEC](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)、[FRED](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)、[Federal Register](https://www.federalregister.gov/developers/documentation/api/v1) 官方说明，详细时间口径见总规约。
