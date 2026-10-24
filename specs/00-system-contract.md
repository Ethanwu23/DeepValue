# DeepValue 总规约（DV-00）

状态：Proposed，待本 PR 审查。版本：1.0。日期：2026-10-25。
关联：[总任务 #1](https://github.com/Ethanwu23/DeepValue/issues/1)。

本文是后续实现的规范，不描述当前代码已经具备全部能力。MUST/必须为验收约束；修改本规约必须同步能力 spec、验收编号和 CHANGELOG。各 spec 冲突时以本文为准，不能靠实现自行选择语义。

## 1. 产品与本轮边界

保留单公司、美股机械制造业 SIC 3500–3599、固定研究截止日、3–5 个年度财报，以及三年 EPS 中位数乘 PE 的情景方法。默认 CAT / 18230 / 2025-03-01。

本轮存量改造同时补齐目标架构中的数据修复、结论补查、宏观历史版本和政策正文能力。宏观先支持 INDPRO；公告先支持限定 8-K；新闻与行业分别有节点、共享底层抓取。行业资格并不保证固定财务概念全部齐备，缺失必须显式阻断。

目标图的“市场数据”保留能力边界，但 v1 不接股价、不计算安全边际，不因不存在行情接口而让 PE 情景失败；多公司、DCF、交易和多行业不属于本轮。新增行情方法必须另有提供方、时间口径与公司行动处理规约，不能用临时网页价格补上。

## 2. 架构和依赖方向

采用模块化单体，继续使用 React、FastAPI、LangGraph、现有模型与 MCP 供应商协议。能力是可独立调用和验证的业务服务，不要求每个能力都是 Agent。

`api/runtime -> capabilities -> contracts`；集成适配器实现能力所需端口，通过组合根注入。contracts 不依赖 LangGraph、HTTP SDK 或前端。只有分析与支持性审查需要模型，计算、时间判断、预算、状态转换必须确定性执行。

图以 README 最终架构为准：
define_scope -> plan_research -> dispatch_tasks -> 四个采集节点 -> normalize_evidence -> validate_evidence。
数据可用后 analyze_business -> calculate_valuation -> review_thesis。
数据问题走 plan_data_repair，结论问题走 plan_follow_up；两者返回 dispatch_tasks。
write_report / write_limited_report 为显式出口。身份/参数错误、内部错误、取消是图外运行终态，不伪装成有限研究成功。

define_scope 内调用公司核验；collect_financials 同时包含选报及事实提取；collect_macro_policy 包含两个独立子结果。每批按已分发 task_ids 汇合，不要求未派发的类别也返回。

## 3. 数据契约

Python 使用严格 Pydantic 模型（extra=forbid），前端类型以共享 JSON Schema 生成。不得同时维护含义不同的手写同名协议。日期用 ISO date，瞬时时间用有时区 ISO8601；金额和比率的传输使用十进制字符串，禁止 NaN/Infinity。以下字段是必需项；明确写“可空”的才允许 null，空集合不代表成功。

| 模型 | 必需字段与约束 |
|---|---|
| ResearchRequest | ticker、cik、as_of、industry=machinery、years、max_rounds、pe_low/base/high、focus、model；默认与范围见 DV-01 |
| ResearchContext | run_id(UUID)、request、created_at、cutoff_exclusive、spec_version、config_version、prompt_versions、BudgetLedger |
| CompanyProfile | name、ticker、cik、sic、sic_description、source_url、retrieved_at、metadata_basis=current |
| Filing | cik、accession、form、period_end、filed、source_url、artifact_id、content_hash；修订覆盖结果在 FilingSet 中独立保存 |
| FinancialFact | fact_id、metric、value、unit、tag、start(instant 可空)、end、filed、accession、evidence_id、source_locator |
| DerivedFact | fact_id、value、unit、formula_id/version、input_fact_ids、parameters、rounding；不作为独立来源 |
| MacroObservation | series_id、observation_period、value(缺失可空)、unit、frequency、as_of_vintage、realtime_start/end、evidence_id、missing_reason(缺失时必需) |
| PolicyEvidence | evidence_id、document_number、publication_date、document_type、effective_date(可空)、legal_edition、official_version_url(未知可空)、applicability=unknown/conditional、applicability_evidence_ids |
| FinancialQualityResult | status=usable/blocked、required_periods、checked_fact_ids、gap_ids、amendment_coverage |
| ResearchQuestion | question_id、topic、text、required、resolution_criteria；不得只以类别存在作为答案 |
| ResearchTask | task_id、run_id、batch_id、category、question_ids、gap_ids、source、query、window、required_artifacts、reason |
| CollectorResult | task_id、status=succeeded/partial/failed/cancelled、candidates、rejections、gaps、request_ids；零候选必须注明原因 |
| Evidence | evidence_id、source_type、canonical_locator、url、title、categories[]、question_ids[]、task_ids[]、published_at(有依据时)、date_precision、date_basis、retrieved_at、content_hash、artifact_id、excerpt、locator、source_group、representation、eligibility |
| Evidence 时间补充 | modified_at 可空；macro 保存 as_of_vintage、realtime_start/end、observation_period，不强造 published_at；policy 保存 document_number、effective_date(可空)、legal_edition、applicability |
| EvidenceRejection | candidate_id、task_id、url、reason_code、safe_detail；无候选的接口错误用 gap 表示 |
| ResearchGap | gap_id、kind、subject、period(可空)、question_id、blocking、status=open/resolved/unresolvable、reason_code、repairability、attempted_task_ids、resolution_evidence_ids |
| Claim | claim_id、question_id、kind=fact/derived/inference、topic、text、citations[]、premise_fact_ids[]、counterevidence_ids[]、assumptions[] |
| Citation | evidence_id、locator、quote 或 fact_id（二选一）；quote 8–350字符，fact 引用不能伪装自然语言原文 |
| ClaimReview | claim_id、status=supported/unsupported/uncertain/rejected、reason、checked_citations、missing_premises、counterevidence_ids、review_model/version |
| ValuationResult | status、method/version、currency、input_fact_ids、periods、assumptions、rounding、reason_code(非 calculated 必需)、scenarios、sensitivity；非 calculated 的数组为空 |
| ResearchResult | schema_version=1、run_id、scope、company、run_status、research_status、financials、evidence、claims、reviews、valuation、gaps、tasks、budget、report、created_at、finished_at |
| RunEvent | event_id=run_id:seq、run_id、seq(单调递增)、timestamp、node、task_id(节点级可空)、state、reason_code、safe_detail |

Evidence.eligibility=accepted/rejected；rejected 不进入模型输入。representation=source_text/source_fields/derived_summary；来源正文只证明该来源的陈述，不天然证明真实性。原始文件在本地 artifact 存储，导出不暴露绝对路径。content_hash 固定 SHA256 UTF-8 规范正文或规范 JSON；规范 JSON 使用排序键和明确的小数字符串。

## 4. 截止日与来源资格

cutoff_exclusive 为 as_of 下一日 America/New_York 零点。带时区的时间必须小于该值；日期精度来源要求日期 <= as_of，记录仅日级资格，不能声称盘中可见性。

- SEC：按 filingDate 和原始 accession 过滤；period_end 不得在 cutoff 后；当前 Company Facts 按历史申报筛选不代表数据源历史版本完整归档。
- 网页：主体文章发布日期唯一；已知修改晚于 cutoff 排除；未知修改史保持历史内容限制，不能声称无前视偏差。
- 宏观：按 as_of 实时区间取得历史可见版本；观测期和公开可见期分开；响应实时区间可能是请求投影，不冒充原始发布日期。
- 政策：发布日期、规则生效日期和公司适用性分开，不能从摘要或标题推断法律状态。

日期无依据不是当前日期；数值缺失不是零。有限结论是合法业务结果，不是切换来源或模型的 fallback。

## 5. 问题覆盖与状态

必需问题：Q-FIN 年度财务可用性；Q-QUALITY 盈利/现金流事实与限制；Q-CAPITAL 资本配置；Q-EVENT 公司事件；Q-INDUSTRY 行业与竞争；Q-MACRO 宏观背景；Q-POLICY 政策风险。默认窗口均在各采集规约中明确，用户重点附加为 Q-FOCUS，不取消必需问题。

每个必需问题只有在有合格来源、至少一条审查通过的相关观察或有证据的明确不适用解释时才 resolved。搜索零结果不能证明没有事件/政策。模型未提出 gap 不代表问题已解决。

| 维度 | 枚举与含义 |
|---|---|
| run_status | pending / running / completed / failed / cancelled |
| research_status | sufficient / limited / blocked；运行未终止时可空 |
| valuation.status | calculated / not_applicable / blocked |
| data_gate | usable / repairable / unavailable |
| review_decision | sufficient / follow_up / limited |

completed 表示报告生成完成，可同时 research_status=limited 或 blocked。blocked 专指关键财务数据不可用；有限报告用于 limited 与 blocked。not_applicable 表示完整数据不适用于 PE（如负 EPS），不必导致研究 blocked。failed 表示无有效请求/身份或内部异常，不能当作完成报告；cancelled 不生成正式报告。

路由优先级：取消 > 内部不变量错误 > 全局截止时间 > 数据门禁 > 结论审查。全局截止时间到来时只进行本地有限报告渲染，不能再发外部请求。

## 6. 统一预算

这是本轮可实现的产品限制，不是供应商限额。所有数字保存在配置快照，修改必须同步 spec 和验收。

| 预算 | 限制 |
|---|---|
| 采集批次 | max_rounds=1或2，初始批次也占1；repair/follow_up 共用 |
| 逻辑任务 | 每批最多4，总共最多8 |
| 外部请求尝试 | 总计80，包含身份、搜索、HTTP重定向、宏观、政策、模型和重试 |
| 模型尝试 | 总计8，亦计入80；分析与审查各每轮最多1个逻辑调用 |
| 网页候选 | 每个 news/industry 任务最多5；网页并发3 |
| 外部并发 | 整个 run 最多6；各供应商额外限流 |
| 全局时间 | 600秒，其中最后5秒预留本地结果整理；在595秒后不得发外部请求 |
| 单次调用 | 普通HTTP40秒、网页12秒、模型60秒，均不超过剩余时间 |
| 单请求尝试 | 最多2次，适用错误见DV-15；等待不超过5秒 |
| 模型输入 | 48000字符，总量；单来源片段6000字符 |
| 原始响应大小 | 普通网页2MB；SEC JSON50MB；政策正文/PDF10MB；超限返回缺口 |

预算在发起请求前原子预留；未实际发出的预留可释放，已发出即记账。重试消耗请求预算但不创建新批次。无法调度时记录原因并退出，不通过换名字绕过任务去重。没有可验证新任务，即使有剩余预算也结束。

## 7. 错误协议

统一 ErrorInfo(code, capability, task_id, retryable, safe_detail, cause_id)。safe_detail 不含第三方原始异常、认证信息或用户私有正文。

| code | 处理 |
|---|---|
| VALIDATION_ERROR / IDENTITY_MISMATCH / UNSUPPORTED_INDUSTRY | 拒绝本次研究，零后续采集 |
| CONFIG_ERROR | 应用启动失败；模块导入本身不触发网络或生产配置检查 |
| SOURCE_TIMEOUT / SOURCE_RATE_LIMITED / SOURCE_UNAVAILABLE | 按有限重试策略处理，耗尽后变为缺口 |
| SOURCE_SCHEMA_ERROR | 不可重试，保留协议故障 |
| MISSING_METRIC / CONFLICTING_FACT / PERIOD_MISMATCH | 关键 gap，可修复与否由具体可用任务决定 |
| AMENDMENT_REVIEW_REQUIRED / AMENDMENT_COVERAGE_INCOMPLETE | 阻断财务门禁，不自动解释修订 |
| DATE_UNVERIFIED / AFTER_CUTOFF / NETWORK_POLICY_REJECTED | 拒绝来源，禁止放宽条件重收 |
| MODEL_OUTPUT_INVALID / REVIEW_FAILED | 分析/审查缺口，禁止未经核验的完整报告 |
| BUDGET_EXHAUSTED / DEADLINE_EXCEEDED / NO_NEW_TASK | 停止闭环，输出有限结果 |
| RUN_ACTIVE / RESULT_NOT_READY | API并发或导出条件不满足，返回409，不改变已有run |
| RUN_NOT_FOUND / INTERNAL_ERROR | 失效或 failed，记录脱敏诊断 |

## 8. 配置、安全及复算

配置显式且启动校验，禁止默认供应商、默认模型或默认凭据兜底。原始配置和密钥不进入状态、导出、日志。模型和网页内容视为不可信输入，不能更改工具配置或运行规则。

默认仅本机服务；公网抓取必须将 DNS 校验与真实连接绑定。文本展示不执行外部脚本。提交、Issue、PR、CI 样本不含私有环境内容或个人绝对路径。

保存每次研究的参数、非敏感配置、prompt版本、模型标识、请求版本、证据哈希和公式版本。确定性模块应可复算；不承诺外部网页或模型再次运行字节一致。模型支持性评审不是法律/财务审计。

## 9. SpecDD 执行与完成条件

1. 规约先行：总规约、15份能力 spec、迁移表、验收矩阵一并审查。
2. 再实现：先 copy 既有实现，再分离职责与修正行为；不保留双入口和旧协议兼容。
3. 再特征测试：以场景编号验证产品行为，不照抄实现。当前文档中的测试路径均为计划，不表示已有测试或已通过。
4. 最后整体切换：主图、API与前端使用统一契约，真实 CAT 联调明确记录有效来源与剩余缺口。
5. CI当前只有构建/加载检查；不能将绿色CI当作业务验收。每个能力完成后把对应特征测试加入CI；真实付费接入不放入常规CI。

工作分支 codex/specifications，PR目标 dev。仅完成规约不关闭含实现与测试任务的能力Issue。通过规约审查后状态才由 Proposed 变为 Accepted；当前不会提前写业务代码。

## 9.1 对外运行接口

新工作台只使用统一应用API，后端封装LangGraph执行；不把内部state或供应商格式暴露为公共请求。现有图ID仍为deepvalue，直接图装配用于开发与内部验证；正式研究入口必须创建服务端Context并执行预算检查。旧前端useStream调用在统一切换时删除，不维护双API兼容。

| 接口 | 行为 |
|---|---|
| GET /api/models | 200返回可用模型列表；配置失效时503与脱敏CONFIG_ERROR，不提供默认模型 |
| POST /api/research/runs | JSON ResearchRequest；格式/模型范围错误422；启动校验通过后202返回run_id、status、snapshot_url、events_url；身份核验在run内，失败产生failed终态 |
| GET /api/research/runs/{run_id} | 200返回当前运行快照；未知或进程重启后丢失404 RUN_NOT_FOUND |
| GET /api/research/runs/{run_id}/events?after_seq=N | SSE重放seq>N的已记录事件，再订阅新增事件；支持Last-Event-ID，两者同时存在且冲突时400；终态事件发出后关闭流 |
| POST /api/research/runs/{run_id}/cancel | 活跃运行202返回cancel_requested=true；已终止运行200返回已有终态；未知运行404 |
| GET /api/research/runs/{run_id}/export?format=md或json | completed时200下载冻结结果；非completed返回409 RESULT_NOT_READY；不通过前端内部状态拼装导出 |

API错误为 {error: ErrorInfo}。422不创建run；运行内身份核验失败创建可追踪failed结果但不生成报告。使用服务端run_id，客户端不能提供自定义run_id冒充已有运行。

v1为单用户本机运行，同一进程最多1个活跃研究；再次提交返回409 RUN_ACTIVE，不自动取消当前任务。每个run内仍按预算并行采集。内存保留全部活跃run及最近20个终态run，超出时移除最早终态及其事件；客户端404时显示结果已失效。原始artifact位于忽略的.run/artifacts/{run_id}/，只保存规范正文/数据，不保存认证请求头。v1不承诺重启恢复；本地artifact不自动回灌运行状态，也不进入git。

取消与完成用同一运行锁比较状态：若completed已先提交，取消返回completed；若cancel_requested先置位，后续不得提交completed。终态及冻结结果只写入一次。运行级seq在锁内递增；不记录token流事件，以限制事件量。终态后客户端断线重连仍可重放保留事件。

## 10. 总体验收场景

| 编号 | Given | When | Then |
|---|---|---|---|
| DV-00-AC-01 | 四类初始任务可返回且证据充分 | 执行完整流程 | 一次汇合、所有必需问题已解决、完整报告与导出一致 |
| DV-00-AC-02 | 关键事实缺失，存在新来源任务且有一轮预算 | 数据修复 | 第二轮重新校验成功后才分析；不重置预算 |
| DV-00-AC-03 | 财务可用但结论缺前提，有新查询 | 结论补查 | 第二轮后重新规范化、门禁、分析、估值及审查 |
| DV-00-AC-04 | 首轮后关键事实不可取得或两轮用尽 | 终止 | completed+blocked，有限报告无估值 |
| DV-00-AC-05 | 财务充分但新闻无合格证据 | 预算用尽 | completed+limited，可保留已计算情景并披露缺口 |
| DV-00-AC-06 | 非正EPS但全部研究问题有合格结论 | 生成结果 | 估值not_applicable，与研究是否sufficient独立 |
| DV-00-AC-07 | 用户取消且外部响应仍在途 | 响应晚到 | cancelled终态不被覆盖，不生成正式报告 |
| DV-00-AC-08 | 一个run结束后同线程再次提交 | 初始化新run | 旧来源、报告、预算、错误均不串入新结果 |
| DV-00-AC-09 | 截止日前后存在不同宏观版本及未来财报 | 收集与分析 | 未来材料被排除，宏观使用请求历史版本 |
| DV-00-AC-10 | 同批次返回顺序变化 | 合并和计算 | 相同事实输入得到相同证据登记和估值；模型文本不纳入逐字一致承诺 |

## 11. 接入依据

以下是接口能力依据，不代表当前项目已完成接入；查询日期2026-10-24。

- [SEC EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)：submissions、历史索引和Company Facts；当前元数据与历史申报应区分。
- [FRED observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)：明确实时区间、观测窗口与输出类型，取得截止日可见版本。
- [FRED INDPRO](https://fred.stlouisfed.org/series/INDPRO)：月度工业生产总指数，不是机械制造业独立指数。
- [Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1)：检索与文档关联；网页版本不是官方法律版本，法律研究需核对govinfo对应官方版本。
