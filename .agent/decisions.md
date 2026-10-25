# Decisions

## 2026-10-25 Baseline Audit

- **决定**：首次运行只做基线审计，不修改任何业务代码。
  依据原则 37，基线完成后等待人工确认再进入 Daily Maintenance 模式。

- **决定**：`.agent/` 目录纳入版本管理。
  维护状态（state / backlog / repo_summary）是长期记忆，需要随仓库演进；
  内容均为无敏感信息的工程结论。

- **决定**：本次不创建 `.agent/daily/2026-10-25.md` 之外的提交，也不 commit。
  基线文件先落盘，待人工确认分支与提交策略后再入库。

- **环境事实（Windows 本地部署）**：
  - `git` 不在 PATH，使用 GitHub Desktop 内置版本
    `C:\Users\wudin\AppData\Local\GitHubDesktop\app-3.5.5\resources\app\git\cmd\git.exe`
  - SSH 克隆因 host key verification 失败，改用 HTTPS 远程
  - 全局 `pip index-url` 指向 `mirrors.aliyun.com`，该域名 DNS 不可解析，
    需显式 `-i https://pypi.tuna.tsinghua.edu.cn/simple`
  - `requirements-lock.txt` 中的 `uvloop` 仅支持 Unix，Windows 安装须排除
  - Windows 下必须设置 `PYTHONUTF8=1`，否则 `langgraph_api` 读取 openapi 文件时 GBK 解码失败

- **未验证项（不假装成功）**：
  - 远程 CI 运行记录与 GitHub Issue 列表：`gh` CLI 不可用，无法读取
  - 端到端研究流程：`backend/.env` 为占位配置，未填真实 `APP_TOKEN` / `LLM_BASE_URL` / `MCP_APP_ID`
