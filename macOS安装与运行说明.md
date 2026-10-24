# DeepResearch 基础版：macOS 安装与运行说明

验证日期：2026-09-24。

## 实际研究验证

更新日期：2026-09-24。重新加载用户更新的 MCP_APP_ID 后，已通过本机 LangGraph API 完整重试快速研究：
“请检索 Python 官方文档，简要说明虚拟环境 venv 的用途，附一个官方来源，控制在200字以内。”

验证结果：
- generate_search、web_search、critique、final_answer 四个节点均正常完成。
- 最新完整研究实际获得 9 条网页来源，其中包含 Python 官方文档。
- 最终报告已生成，所有 Markdown 引用均能映射到本次搜索结果，内部占位链接已还原。
- 前后端已重启并继续在后台运行。
- 验证记录位于 .run/mcp-retry-verification.json；这是运行产物，不包含应用凭证。

**结论：本地服务、模型调用和联网搜索到报告生成的完整链路均已通过验证。**

### 当前搜索响应契约

新应用已返回真实搜索结果，但工作流会把工具结果 JSON 与 count 数值直接串接，例如：
```text
{"content":[{"type":"text","text":"内部搜索结果JSON"}],"isError":false}10
```

内部搜索结果 JSON 包含 status=0 和 pages 列表，每项具有 snippet、title、url。
本地解析器已针对该实际格式处理：先解码完整工具结果，再解析尾部数量并核对请求值，然后检查结果状态与页面字段。
它不会忽略额外尾部文本，也不再尝试旧版的多种响应路径。
搜索返回条数可以少于请求数量；尾部数量是请求参数的回传，不代表实际命中数。

搜索请求或解析连续失败时，现在会向工作流抛出错误，避免把调用失败当作无结果继续生成报告。
正常返回空 pages 与调用失败仍是不同情况。外部应用若调整输出结构，需要同步修改这一明确契约。

## 1. 当前运行方式

本项目已安装依赖，并通过项目根目录的 `run.sh` 启动本机开发服务。

| 项目 | 地址或位置 |
| --- | --- |
| 前端页面 | http://127.0.0.1:5173/app/ |
| 后端服务 | http://127.0.0.1:2024 |
| 健康检查 | http://127.0.0.1:2024/ok |
| 模型列表 | http://127.0.0.1:2024/api/models |
| Python 虚拟环境 | backend/.venv |
| 前端依赖 | frontend/node_modules |
| 前端构建产物 | frontend/dist |
| 启动进程编号 | .run/app.pid |
| 后端控制台日志 | .run/backend.log |
| 前端控制台日志 | .run/frontend.log |
| 启动器日志 | .run/launcher.log |
| 业务日志 | backend/logs |

服务仅监听 127.0.0.1。当前采用 LangGraph 本地开发运行时，不是生产部署。
前端支持开发热更新；后端启动时关闭自动重载，修改 Python 或 .env 后应重新启动。

## 2. 已验证环境

| 组件 | 版本 |
| --- | --- |
| Python | 3.11.9 |
| Node.js | 20.12.0 |
| npm | 10.5.0 |
| React | 19.1.0 |
| Vite | 6.3.4 |
| TypeScript | 5.7.3 |
| LangGraph | 1.2.12 |
| LangGraph API | 0.14.4 |
| LangGraph CLI | 0.4.32 |

后端安装在独立虚拟环境中，没有向系统 Python 安装项目依赖。
前端使用现有 package-lock.json 执行 npm ci 安装。
后端已安装版本保存在 backend/requirements-lock.txt 中；该快照来自本机 Python 3.11 环境。

## 3. 重新安装依赖

打开终端，先进入项目根目录：

```bash
cd "/path/to/DeepValue"
```

首次安装或重新建立环境时执行：

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-lock.txt -e backend
cd frontend
npm ci --no-audit --no-fund
npm run build
cd ..
backend/.venv/bin/python -m pip check
```

已有环境不需要每次启动都重新安装依赖，也不需要先激活虚拟环境。
不要使用 sudo 安装本项目依赖。

## 4. 配置模型与搜索服务

配置文件为 backend/.env。本次保留了现有配置，未将凭证写入本说明。

| 变量 | 用途 |
| --- | --- |
| APP_TOKEN | 模型接口和 DashScope Application 使用的凭证 |
| LLM_BASE_URL | OpenAI 兼容模型接口地址 |
| MCP_APP_ID | DashScope 搜索应用 ID |
| AVAILABLE_MODELS | 前端可选模型列表，内容为 JSON 数组 |
| WEB_SEARCH_MAX_QPS | 搜索请求放行速率，当前配置 12 |
| NUMBER_OF_INITIAL_QUERIES | 未由请求指定时的初始查询数量，当前配置 2 |
| MAX_RESEARCH_LOOPS | 未由请求指定时的最大研究轮数，当前配置 2 |

AVAILABLE_MODELS 中每项包含 model_id、display_name、icon、icon_color。
model_id 必须是真实接口支持且当前账号有权限使用的模型。

页面选择的模型控制反思和最终报告；查询生成与搜索摘要使用 QUERY_GENERATOR_MODEL 配置，未配置时取可用模型列表最后一项。
REFLECTION_MODEL 和 ANSWER_MODEL 用于请求没有指定 reasoning_model 时的默认模型。
环境变量的阶段配置优先于 LangGraph configurable 中的同名配置。

只有模型接口可用还不够：MCP_APP_ID 对应的应用也必须能够返回搜索结果。
当前本地搜索代码通过 DashScope Application 调用外部应用，不是直接连接任意 MCP 服务地址。

如需改变前端连接的后端地址，在 frontend/.env.local 中设置：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:2024
```

随后重启前端。默认已经连接本机 2024 端口，无须额外创建此文件。
正式构建时 Vite 环境变量会写入构建产物，修改后应重新构建。

## 5. 启动、停止与重启

以下命令均在项目根目录执行。

### 前台启动

```bash
bash run.sh
```

脚本同时启动前后端，将日志分别写入 .run 目录。
端口被占用时脚本直接退出，不会杀死已有服务或自动换端口。
在该终端按 Ctrl+C，会停止本次脚本启动的两个服务。

### 后台启动

确认已有实例停止后执行：

```bash
mkdir -p .run
nohup bash run.sh > .run/launcher.log 2>&1 < /dev/null &
```

本次安装后已采用后台方式启动，直接打开前端地址即可，无须重复执行。

### 停止后台服务

```bash
kill -TERM "$(cat .run/app.pid)"
```

该文件记录启动器 PID，启动器收到 TERM 后会停止它创建的前后端进程并清理 PID 文件。
PID 文件不存在表示当前没有由这个脚本记录的运行实例；不要随意终止其他进程。

停止后检查端口：

```bash
lsof -nP -iTCP:2024 -iTCP:5173 -sTCP:LISTEN
```

正常停止后没有监听输出。确认退出后，再运行启动命令完成重启。
后台模式不会自动在 macOS 重启后恢复，需要重新启动。

### 分别启动

也可以在两个终端分别运行：

```bash
bash run_backend.sh
```

```bash
bash run_fontend.sh
```

分别启动时，在对应终端使用 Ctrl+C 停止；不会生成统一启动器的 .run/app.pid。

## 6. 使用流程

1. 打开 http://127.0.0.1:5173/app/。
2. 输入研究问题。
3. 选择研究深度和模型。
4. 点击“探索”，或按 Cmd+Enter。
5. 查看查询生成、网络研究、反思分析和最终报告。
6. 报告支持 Markdown 表格、来源链接和复制。

| 模式 | 每轮提示词约束的查询数量 | 最大研究轮数 |
| --- | --- | --- |
| 快速 | 1 | 1 |
| 均衡 | 3 | 3 |
| 全面 | 5 | 10 |

研究深度控制搜索数量和循环次数，不是模型思考模式开关。
底层模型调用设置 enable_thinking=False，且没有使用逐 token 流式生成。
研究过程主要按节点完成事件更新，较慢的外部调用期间可能暂时没有新进度。

新主题建议点击“探索新专题”。当前研究状态的多轮隔离问题尚未在此次启动修复中重构。

## 7. 代码与数据流

```text
前端 InputForm
  → App 中的 LangGraph useStream
  → generate_search：生成查询
  → web_search：并行调用搜索应用，并用模型生成摘要
  → critique：判断资料是否充分
       → 不充分且未达到轮数上限：继续 web_search
       → 充分或达到上限：final_answer
  → 生成 Markdown 报告并还原引用 URL
  → ChatMessagesView 展示 AIMessage
```

backend/langgraph.json 注册 agent 图并挂载 FastAPI 自定义应用。
backend/src/agent/app.py 提供 /api/models；研究执行接口由 LangGraph 服务提供。
搜索节点使用外部应用返回的 snippet、title、url，本地没有网页正文抓取实现。

## 8. 本次安装与启动修复

- 创建 backend/.venv 并安装后端依赖。
- 将 langgraph-cli[inmem] 纳入正式依赖，补齐 loguru。
- 补齐打包元数据引用的 backend/README.md。
- 移除导入 graph.py 时绘图和写图片的操作，消除启动对 IPython/绘图服务的依赖。
- 依据原有组件移除没有接通的“研究计划确认”界面分支，解决组件 Props 和 ref 类型错误。
- 将前端监听的事件名对齐后端四个节点名称。
- 对齐中文时间线图标匹配，提交新问题时清理旧错误状态。
- 阻止研究期间通过快捷键重复提交，并明确新专题按钮不是表单提交按钮。
- 统一前端 API 地址配置，修正 Vite 的 API 代理目标。
- 重写 macOS 启动脚本的目录定位和进程管理，不再依赖缺失的 Makefile。
- 保存后端依赖版本快照，并将 .run 目录加入忽略列表。
- 根据新搜索应用的实际结果与数量串接格式更新解析，重试耗尽后明确抛出错误。

此次没有重写研究算法，也没有添加测试脚本。

## 9. 验证结果

- Python 依赖检查：pip check 通过。
- 后端图导入和编译：通过，四个业务节点已注册。
- 前端 TypeScript 检查与 Vite 构建：通过。
- shell 启动脚本语法检查：通过。
- 统一停止与重新启动：已验证，停止后两个监听端口均释放。
- 后端 /ok：HTTP 200，返回 {"ok":true}。
- 后端 /api/models：HTTP 200。
- LangGraph assistants/search：能查到 agent。
- 前端 /app/：HTTP 200。
- 浏览器欢迎页、研究模式选择、模型下拉列表：已实际打开检查。

外部模型与搜索应用的业务验证结果见本文开头的“实际研究验证”。
构建有单个 JavaScript 包超过 500 kB 的体积提示，不影响此次构建成功。

## 10. 日志与常见问题

查看日志：

```bash
tail -n 80 .run/backend.log
tail -n 80 .run/frontend.log
```

| 现象 | 检查方法 |
| --- | --- |
| 提示端口被占用 | 用 lsof 查看 2024、5173 的监听者，先确认是否已有本项目实例 |
| 页面无法打开 | 检查 .run/frontend.log，使用包含 /app/ 的完整地址 |
| 模型列表无法加载 | 检查 /api/models、后端进程、VITE_API_BASE_URL |
| 模型返回 401/403 | 检查 backend/.env 的凭证和服务权限 |
| 模型不存在 | 检查 AVAILABLE_MODELS 和 QUERY_GENERATOR_MODEL 是否与服务支持的模型一致 |
| 搜索返回 401/403 | 检查 APP_TOKEN 与 MCP_APP_ID 是否属于有权限的应用配置 |
| 搜索返回 429 | 检查服务额度和 WEB_SEARCH_MAX_QPS，减少同时提交的任务 |
| 报告没有来源 | 检查搜索应用是否返回 pages，以及日志中的搜索解析错误 |
| 修改配置后没有生效 | 停止并重新启动服务；前端构建产物还需要重新构建 |
| 前端构建成功但页面无结果 | 区分本地服务启动成功与外部模型、搜索服务可用；查看具体调用错误 |

业务日志会记录研究问题和报告，分享日志前先检查内容。
测试目录原有示例包含硬编码凭证；正常服务启动不依赖该示例，若凭证仍有效应撤销并从示例移除。

## 11. 当前边界

- 本次交付是本机开发运行环境，不含公网部署、账号登录或开机自启动。
- 当前基础版没有人工审批研究计划流程。
- 搜索异常已改为明确报错；来源可信度与报告事实仍未进行独立核验。
- 查询记录与来源记录仍存在原有的重复累加问题。
- 多轮研究状态隔离、严格结构化输出、证据核验没有在本次启动任务中重构。
