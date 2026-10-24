# DeepResearch 后端

后端使用 LangGraph 编排查询生成、并行搜索、反思和报告生成，使用 FastAPI 提供模型配置接口。

## 本地启动

先在 backend 目录创建 .venv 并安装依赖，再从项目根目录运行：

```bash
bash run_backend.sh
```

配置文件为 backend/.env。APP_TOKEN、LLM_BASE_URL、MCP_APP_ID 必须与实际服务一致。
完整安装、启动、停止和排错说明见项目根目录的《macOS安装与运行说明.md》。
