# Backlog

> 建立于 2026-10-25 Baseline Audit。
> 若 GitHub Issue 已存在，优先引用 Issue 编号，不重复制造同一条目。

## P0 Critical

- [ ] 为估值与财务计算建立回归测试基线
  - reason: `value/valuation.py` 与 `value/sec.py` 承载核心金融逻辑，当前零测试覆盖，任何重构或依赖升级都无法验证正确性
  - affected: backend/src/agent/value/valuation.py, backend/src/agent/value/sec.py
  - risk: low（仅新增测试，不改业务代码）
  - estimated_scope: small-medium（需先引入 pytest 与最小测试配置）
  - note: 属金融计算，测试用例必须基于真实口径与单位，禁止为了让测试通过而改公式

## P1 Bug

- [ ] 确认 `collect_policy` 遇异常数据是应中断还是跳过
  - reason: `evidence.py:158` 在政策数据晚于截止日时直接 `raise ValueError`，会中断整轮采集；
    而 `verify_page` 的同等情形是记入 `rejected` 并继续。两者行为不一致，
    一条脏数据可能导致整个研究流程失败
  - affected: backend/src/agent/value/evidence.py
  - risk: low-medium（需先与预期行为对齐，金融数据采集路径）
  - estimated_scope: small
  - note: 2026-10-27 读码时发现，尚未确认预期行为，未改动

- [x] TASK-002 修复 `app.py:61` 的 bare except
  - reason: `except:` 会吞掉 `KeyboardInterrupt` / `SystemExit`，且掩盖请求体解析的真实错误
  - affected: backend/src/agent/app.py
  - risk: low
  - estimated_scope: small
  - done: 2026-10-26，改为捕获 `(json.JSONDecodeError, UnicodeDecodeError)` 并用 `errors="replace"` 回退；
    新增 backend/tests/test_app_middleware.py 4 个用例，修复前 2 failed → 修复后通过

## P2 Test

- [x] TASK-001 为 `valuation.py` 的 PE 情景计算补回归测试
  - reason: 估值输出（EPS 中位数 × PE、±20% 敏感性）是项目对外最关键的确定性计算，必须可回归
  - affected: backend/tests/test_valuation.py（新建）
  - risk: low
  - estimated_scope: small
  - done: 2026-10-25，12 个用例全部通过，覆盖三个 blocked 出口、中位数口径、±20% 敏感性、ROUND_HALF_UP 舍入

- [x] TASK-005 为 `evidence.py` 的证据时间过滤补回归测试
  - reason: 截止日前瞻过滤是防前视偏差的核心机制，出错会直接污染研究结论
  - affected: backend/tests/test_evidence.py（新建）
  - risk: low
  - estimated_scope: small
  - done: 2026-10-27，18 个用例，覆盖 ArticleParser.dates 抽取、
    source_id、public_url SSRF 防护、verify_page 截止日门禁的接受与 5 类拒绝分支；
    全部用例不依赖外网

- [x] 引入 pytest 并把测试纳入 CI
  - reason: `pytest` 在 pyproject dev group 中声明但未进 `requirements-lock.txt`，CI 也未调用
  - affected: backend/requirements-dev.txt（新建）, .github/workflows/ci.yml
  - risk: low
  - estimated_scope: small
  - done: 2026-10-25，与运行时 lock 分离，单独建 requirements-dev.txt

## P3 Docs

- [ ] 补充 Windows 本地运行说明
  - reason: 仅有 `macOS安装与运行说明.md`；Windows 需排除 uvloop、设置 `PYTHONUTF8=1`，且 `run*.sh` 不可用
  - affected: README.md（或新增 Windows 安装与运行说明）
  - risk: low
  - estimated_scope: small

- [ ] 记录 `.agent/` 维护目录的用途
  - reason: 新引入的维护状态目录需要在文档中说明，避免被误认为业务代码
  - affected: README.md
  - risk: low
  - estimated_scope: small

## P4 Engineering Debt

- [ ] TASK-003 修复 `post.py` 无效转义序列并移除遗留 `__main__` 演示代码
  - reason: `f"```{pattern}\s(.*?)```"` 触发 SyntaxWarning；`__main__` 中残留了与本项目无关的海峡论坛示例文本
  - affected: backend/src/agent/post.py
  - risk: low
  - estimated_scope: small

- [ ] TASK-004 CI 增加 ruff 检查
  - reason: `pyproject.toml` 已配置完整 ruff 规则集（E/F/I/D/UP），但从未在 CI 执行，规则形同虚设
  - affected: .github/workflows/ci.yml
  - risk: low
  - estimated_scope: small
  - note: 首次接入可能暴露大量存量 D 规则告警，需评估是否分批启用

- [ ] 修复 `configuration.py` 的 Pydantic 废弃告警
  - reason: 运行测试时出现 6 处 `PydanticDeprecatedSince20`：`Field(..., metadata=...)` 已废弃，Pydantic v3 将移除，届时会直接报错
  - affected: backend/src/agent/configuration.py（第 52/57/64/71/78/83 行附近）
  - risk: low-medium（涉及配置字段定义，需确认字段行为不变）
  - estimated_scope: small

- [ ] 修正脚本文件名拼写 `run_fontend.sh`
  - reason: fontend 应为 frontend，脚本名与 README 引用不一致
  - affected: run_fontend.sh, run.sh, README.md
  - risk: low
  - estimated_scope: small

- [ ] 前端构建产物超过 500 kB
  - reason: 单 chunk 508 kB，未做 code split
  - affected: frontend/vite.config.ts
  - risk: medium（需验证路由与懒加载行为）
  - estimated_scope: small-medium

## P5 Small Features

- [ ] CI 增加前端 lint 与 typecheck
  - reason: `npm run lint` 与 `tsc -b` 已配置但 CI 未执行
  - affected: .github/workflows/ci.yml
  - risk: low
  - estimated_scope: small

## Future / Requires Planning

- [ ] REQUIRES_PLANNING：按 `specs/migration-plan.md` 推进 SpecDD 能力模块化
  - reason: 15 份能力 spec 已就绪，但改造涉及大量核心文件，超出每日任务规模
  - affected: backend/src/agent/**（预计 > 5 个核心文件）
  - risk: high（属 Agent Workflow 架构修改，必须人工确认）
  - estimated_scope: large

- [ ] REQUIRES_PLANNING：升级 langgraph-api 0.14.4 → 0.16.x
  - reason: 当前版本已 EOL，启动日志明确告警；属 dependency major upgrade
  - affected: backend/requirements-lock.txt
  - risk: high
  - estimated_scope: medium
