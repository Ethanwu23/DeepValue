# DeepValue Repository Summary

> 首次建立：2026-10-25（Baseline Audit）
> 本文件只保存稳定架构信息，仅在架构变化时更新。

## Product Goal

面向价值投资的 DeepResearch 研究工作台。以**单家公司、固定研究截止日、明确行业范围**为研究边界，
围绕财报、新闻、宏观政策与行业资料构建研究流程，输出可追溯的经营观察、风险与可复算的估值情景。

当前为**原型版本**，默认研究对象 Caterpillar（CAT）。主流程已跑通，证据覆盖与判断审查仍需完善。

## Architecture

LangGraph 单图编排 + FastAPI 自定义路由 + React/Vite 前端。

```
frontend (Vite + React 19 + TS + Tailwind v4)
        │  HTTP / LangGraph SDK
        ▼
langgraph dev (in-memory runtime, port 2024)
        ├── graph:  agent.graph:graph   (langgraph.json -> src/agent/graph.py)
        └── http:   agent.app:app       (自定义 FastAPI，/api/models)
```

研究图节点（`backend/src/agent/value/workflow.py`）：

```
__start__ → define_scope → collect_financials → plan_research → collect_context
         → normalize_evidence → validate_evidence → analyze_business
         → calculate_valuation → review_thesis → write_report
```

## Backend

- 位置：`backend/`，Python（要求 >=3.11,<4.0），setuptools src-layout，包名为 `agent`
- 运行：`langgraph dev --host 127.0.0.1 --port 2024 --no-browser --no-reload --allow-blocking`
- 依赖锁：`backend/requirements-lock.txt`（97 行，含 langgraph-api 0.14.4 / langgraph 1.2.12 / openai 3.19.2 / dashscope）
- 配置：`backend/.env`（gitignore），键：`APP_TOKEN`、`LLM_BASE_URL`、`MCP_APP_ID`、`AVAILABLE_MODELS`、`WEB_SEARCH_MAX_QPS`
- 关键模块：
  - `src/agent/value/sec.py` — SEC 申报目录与 XBRL Company Facts
  - `src/agent/value/evidence.py` — 网页/政策抓取与证据时间校验
  - `src/agent/value/valuation.py` — PE 情景估值（确定性计算）
  - `src/agent/value/workflow.py` — 研究编排、审查与报告
  - `src/agent/base_agent.py` — 模型与 MCP 调用
  - `src/agent/app.py` — 自定义 FastAPI（`/api/models`）
  - `src/agent/post.py` — Markdown 代码块抽取工具

## Frontend

- 位置：`frontend/`，Vite 6 + React 19 + TypeScript + Tailwind v4 + Radix UI
- 路由基址：`/app/`（见 `vite.config.ts`），入口 `src/App.tsx`
- 构建产物超过 500 kB 警告（未做 code split）
- 无测试框架（未配置 vitest / jest）

## Agent / RAG

- 研究 Agent：LangGraph 图，最多 2 轮采集（财报 → 新闻/行业/政策并行）
- 检索：外部 MCP 应用提供网页搜索，解析协议要求 JSON 中含 `status` 与 `pages`（`title`/`url`/`snippet`）
- 证据治理：`normalize_evidence` 统一口径去重；`validate_evidence` 做数据门禁；
  证据时间检查会排除日期缺失/冲突或发布/修改时间晚于截止日的网页
- Prompt 集中在 `src/agent/prompts.py`

## Database

无数据库。运行态使用 LangGraph in-memory runtime（`langgraph_runtime_inmem`），
持久化目录 `backend/.langgraph_api`（已 gitignore）。

## External APIs

- SEC EDGAR（申报目录、XBRL Company Facts）— 需 `SEC_USER_AGENT`
- Federal Register（政策官方摘要）
- MCP 网页搜索应用（`MCP_APP_ID`）
- OpenAI 兼容 LLM 服务（`LLM_BASE_URL` + `APP_TOKEN`）
- 可选 LangSmith（未启用）

## Tests

**当前不存在任何自动化测试。**
- 无 `backend/tests/`，无 `*.test.tsx`
- `pytest` 在 `pyproject.toml` 的 dev dependency-group 中声明，但**不在** `requirements-lock.txt`
- `ruff` 在 `pyproject.toml` 配置了规则集，但 CI 未执行
- 唯一验证手段：`python -m compileall` + 图加载断言（见 CI）

## CI

`.github/workflows/ci.yml`，触发：push / PR to `dev`、`main`，workflow_dispatch。

- job `frontend-build`：Node 22 + `npm ci` + `npm run build`
- job `backend-check`：Python 3.11 + 装 lock + `python -m compileall -q backend/src`
  + `python -c "from agent.graph import graph; assert graph.name == 'DeepValue'"`
- 未运行：pytest、ruff、mypy、前端 lint、类型检查、测试覆盖率

分支策略：`main`（发布）/ `dev`（集成），经 PR 更新；特性分支 `codex/<feature>`。
基线标签：`baseline-prototype`。

## Important Directories

```
.agent/                  维护状态（本目录）
.github/workflows/       CI 与 Issue 模板
backend/src/agent/      后端源码（包名 agent）
backend/src/agent/value/ 投研核心：sec / evidence / valuation / workflow / models
frontend/src/           前端源码
specs/                   SpecDD 规约：00 总规约 + 01-15 能力 spec + 验收矩阵 + 迁移计划
.run/                    本地运行日志（gitignore）
```

## Critical Business Logic

1. **估值**（`value/valuation.py`）：近三年披露稀释 EPS 中位数 × 用户设定 PE（10/15/20），
   并对 EPS ±20% 做敏感性。三年内存在非正 EPS 或关键财务未通过检查时不执行估值。
2. **财务事实**（`value/sec.py`）：按披露日与原始申报筛选；合并净利润取含非控股权益的 ProfitLoss。
3. **证据时间检查**（`value/evidence.py`）：严格按截止日过滤，防止前视偏差。
4. **引用检查**：检查引用片段是否真实出现在提供的证据中（仅证明片段存在，不证明因果）。

> 修改上述逻辑属于高风险，必须独立分支 + 人工确认（见原则 9 / 十二）。

## Known Risks

- **零测试覆盖**：估值与财务计算无回归保护，重构或升级依赖时无法验证正确性。
- CI 只做“能编译 + 图能加载”，不保证行为正确。
- 端到端研究流程依赖外部凭据，本地未配置真实凭据时无法验证。
- 仅 macOS 有运行脚本（`run*.sh` 依赖 `lsof`、`.venv/bin/`），Windows 需手动启动。
- `requirements-lock.txt` 含 `uvloop`（仅 Unix），Windows 安装需排除；
  Windows 下还需 `PYTHONUTF8=1` 规避 `langgraph_api` 的 GBK 解码错误。
- 前端构建产物 508 kB，未做 code split。
