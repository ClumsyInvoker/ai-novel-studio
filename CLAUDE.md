# ai-novel-studio · 项目指令（供 AI 助手 / 接手者加载）

AI 辅助网文写作工具。本地 **FastAPI + SQLite** 后端 + **Vue3 + ElementPlus** 前端，公网经 **Cloudflare Tunnel + Access 登录墙**访问。把「灵感 → 大纲 → 逐章写作 → 一致性维护 → 导出」串成闭环。

## 运行方式
- 后端：`backend\run_backend.ps1`（自动从 `~/.cc-connect/config.toml` 注入 DeepSeek key，不落盘）→ 端口 **8778**
- 前端：在 `frontend\` 运行 `npm run dev` → 端口 **5173**
- 访问：本地 http://127.0.0.1:5173 ；公网 https://novel.invokerz.xyz（先过 CF Access 邮箱验证码）
- Python：conda **dev** 环境（`/c/Users/zwh/Miniconda3/envs/dev/python.exe`）
- 开机自启：计划任务 `cloudflared-novel-writer`（隧道）+ `novel-studio-services`（前后端，走 `boot_studio.ps1`，幂等）

## 约定（改代码前先看）
- 数据在 `data/`（`novel.db` + `settings.json`），已加入 `.gitignore`——**勿提交**
- AI 密钥优先级：`settings.json`（设置页）> 环境变量 > 内置默认；**绝不硬编码或打印密钥**
- 后端端口可用环境变量 `NOVEL_BACKEND_PORT` 覆盖（前端 vite 代理同步）
- SQLite 已开 WAL + busy_timeout；改表结构要在 `db.py` 里补 ALTER 迁移（参考 `style` 列）

## 代码结构
- 后端 `backend/app/`：`main.py`(入口) · `db.py`(表/连接) · `settings_store.py` · `export.py`(导出) · `fanqie.py`(番茄抓取) · `ai/client.py`(调用封装) · `ai/prompts.py`(所有 prompt) · `routers/{works,ai,settings}.py`
- 前端 `frontend/src/`：`views/{Workspace,Characters,Settings}.vue` · `components/{ChapterTree,OutlinePanel}.vue` · `router/` · `api/`
- 数据表：works / volumes / chapters / characters；API 共 29 个（前缀 `/api`）

## 状态（2026-10-19）
- ✅ MVP + 第一梯队（风格卡 / 长文一致性 / 一致性校验 / 流式输出）全部完成
- ⏳ 待办见 `PLAN.md`：P0 工程化（测试/类型/拆组件）→ P1 第二梯队 → P2 数据多端 → P3 商业化
- 📖 完整说明书见 `GUIDE.md`；评估报告思路见对话总结
