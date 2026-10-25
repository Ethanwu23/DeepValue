# 存量迁移与实施顺序

关联总任务[#1](https://github.com/Ethanwu23/DeepValue/issues/1)。此文为计划，未开始迁移业务代码。

## 基线盘点

现有图在财报后采集语境资料；只有一个报告节点，按缺失类别补查。财报同accession及期间校验、MCP输出协议、PE中位数计算、Markdown展示和macOS启动脚本可复用。
必须修正：修订索引覆盖、单URL单类别覆盖、引用存在即视为判断成立、配置兜底、过宽重试、停止流不等于取消、全请求体日志。

原型CAT运行曾出现新闻和行业均无合格来源；该事实是验收要能正确表达的有限结果，不得通过放宽日期规则来消除。留存运行数据不提交到公开仓库。

## 能力迁移表

以下 source 为现有相对路径/函数；目标模块相对backend/src/deepvalue，前端除外。

| 能力 | 现有实现 | 目标 | 保留与修正 |
|---|---|---|---|
| DV-01 | value/models.py:ResearchRequest；value/workflow.py:define_scope | capabilities/scope/；contracts/research.py | 保留范围和排序校验；统一时区、严格整数与小数语义，移除松散 dict 在模块之间传播。 |
| DV-02 | value/sec.py:collect 公司身份部分 | capabilities/company/；integrations/sec.py | 将身份职责从财务采集分离；保留代码与行业拒绝规则。 |
| DV-03 | value/sec.py:sec_json、rows_from_columns、collect 选报部分 | capabilities/financials/disclosures.py；integrations/sec.py | 复制现有选报逻辑后修正按行数提前停止、列长度静默截断；将 I/O 与选报纯函数拆开。 |
| DV-04 | value/sec.py:METRICS、collect 指标提取；workflow.py:validate_evidence | capabilities/financials/facts.py、quality.py | 保留同申报、期间与平衡检查；从提取中分离质量结果，移除宽泛 issues 字符串协议。 |
| DV-05 | value/workflow.py:plan_research、dispatch | capabilities/planning/；runtime/dispatch.py | 保留 LangGraph Send；将静态类别补查改为关联 question/gap 的确定性计划。 |
| DV-06 | value/evidence.py:ArticleParser、read_page、verify_page、collect_web；base_agent.py:WebSearchAgent | capabilities/web_research/；integrations/search.py、http.py | 复制现有抓取限制；修复全页面日期混入和 DNS 校验与连接分离问题，保留失败记录。 |
| DV-07 | value/evidence.py:collect_policy；宏观数据当前未实现 | capabilities/macro_policy/；integrations/fred.py、federal_register.py | 保留政策日期和域名检查，改为消费 task.query；摘要仅可作为检索候选，不计正文覆盖。 |
| DV-08 | value/models.py:merge_records；workflow.py:normalize_evidence、validate_evidence | capabilities/evidence/；capabilities/planning/repair.py | 消除 URL 单类别覆盖与宽泛字符串缺口；normalize 与 validate 成为独立可调用服务。 |
| DV-09 | workflow.py:analyze_business；models.py:Analysis/Claim；base_agent.py:JsonAgent | capabilities/analysis/；contracts/claims.py | 保留 JsonAgent 结构化思路；将 facts、derived 和 inference 显式分类，限制模型计算及凭空推断。 |
| DV-10 | workflow.py:review_thesis、research_route | capabilities/review/；capabilities/planning/follow_up.py | 引用存在升级为支持性分层审查；用问题和前提缺口取代 missing_categories 判断。 |
| DV-11 | value/valuation.py:calculate | capabilities/valuation/ | 复制现有中位数算法；修正 normalized_eps 命名、敏感性 float 及默认舍入不一致。 |
| DV-12 | workflow.py:write_report；frontend/src/App.tsx:download | capabilities/reporting/；contracts/result.py | 从 workflow 抽离模板，补统一报告数据模型和安全导出；不保留旧聊天导出路径。 |
| DV-13 | value/workflow.py 图构建；models.py:ValueState；langgraph.json | runtime/graph.py、state.py、budget.py、events.py | 沿用 Send 与 StateGraph；按 batch barrier、结构化状态和共享预算重构，移除直接散布状态字典。 |
| DV-14 | frontend/src/App.tsx、lib/api.ts；components/ChatMessagesView.tsx | frontend/src/features/research/、contracts/、components/markdown/ | 从 App 抽业务 hooks 与视图；复用 Markdown 组件并移除未使用旧聊天入口。 |
| DV-15 | base_agent.py、llm/llm.py、configuration.py、app.py、logger.py；run*.sh | integrations/；config/；api/；保留现有根目录启动脚本 | 先复制现有协议解析；删除 MCPAgent 返回 None、模型默认列表、广泛异常重试等兜底。避免重写已验证的供应商格式。 |

## 实施批次与依赖

1. 公共契约与接入基础：contracts、DV-15配置/协议，以及DV-13预算和状态骨架；不提前重写整个图。
2. 范围与财务主链：DV-01/02/03/04；以确定性样本验证时点、修订覆盖与冲突。实现阶段可构建/联调，正式特征测试在能力实现后落地。
3. 证据与采集：DV-08登记部分、DV-06、DV-07；完成原始响应和派生数据区别。
4. 规划与双闭环：DV-05、DV-08修复部分、DV-13调度部分；用已定义端口组合，不通过循环导入耦合。
5. 分析、审查、估值与报告：DV-09/10/11/12；明确旧结果失效，补查后全链重算。
6. API和前端：DV-14、DV-13取消/事件；生成共享schema并完成图组合。
7. 特征测试及整体验收：按验收矩阵逐项补齐，接入CI，最后做真实CAT有限预算运行。
8. 切换与清理：唯一图入口仍注册deepvalue，改指向新runtime；删除无引用旧agent/聊天代码，更新安装、配置与运行文档。

依赖表表示契约依赖，不意味着所有依赖代码必须先完成；contracts先行，组件在组合根装配，避免循环依赖。

## 迁移操作约束

- 每个能力从dev开特性分支，关联对应Issue；迁移先copy对应实现再改写，保留可审查差异。
- 不引入旧请求兼容层。最后统一切换，未完成期间不将半套新图作为正式入口。
- 每次PR同步spec差异、实现状态与CHANGELOG；PR不能凭CI构建成功就声称业务验收完成。
- 每次合并后dev保持可启动；main仅通过版本PR更新，不在本阶段打正式release tag。
- 新增FRED_API_KEY与SEC_USER_AGENT配置校验必须同步.env.example和页面提示；只写占位符。
- 已使用的源码Markdown组件先提取再删除旧聊天视图，避免误删复用代码。
- 后端包名计划统一deepvalue；在切换PR同步pyproject、langgraph.json、import、CI图加载命令。
- 不在本轮搭建迁移脚本框架、插件注册平台或持久化任务系统。
