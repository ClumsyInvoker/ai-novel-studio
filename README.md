# AI 网文写作助手（ai-novel-studio）

本地 + 公网可访问的 AI 辅助网文写作工具。前端 Vite+Vue3+Element Plus，后端 FastAPI+SQLite，AI 接 DeepSeek。

## 外网访问（已配置完成）

- **公网地址**：https://novel.invokerz.xyz （Cloudflare Tunnel + Access 邮箱登录墙）
- 其他浏览器/设备访问会先跳登录墙，用你设的邮箱收一次性验证码后进入。
- 若嫌每次输邮箱，改 Access → Applications → Policy → Additional settings → **Session duration** 调长（如 30 天）。

## 本地访问

浏览器打开 http://127.0.0.1:5173

## 端口

| 服务 | 端口 | 说明 |
|---|---|---|
| 前端 Vite | **5173** | 唯一要访问的端口 |
| 后端 FastAPI | **8778** | 前端 /api 代理到它，内部用 |
- 后端端口可用环境变量 `NOVEL_BACKEND_PORT` 覆盖（前端代理会同步）。

## 开机自启（已配好 3 个登录自启任务）

| 任务名 | 作用 |
|---|---|
| `cloudflared-novel-writer` | 登录后自动拉起 Cloudflare 隧道 |
| `novel-studio-services` | 登录后自动拉起前后端（`backend\boot_studio.ps1`，幂等） |

> 电脑重启后登录进桌面，等约 10 秒，隧道 + 前后端会自动起来，外网自动恢复可访问。

## 手动启动（需要时可单独跑）

- 后端：`backend\run_backend.ps1`（自动注入 DeepSeek key）
- 前端：在 `frontend\` 跑 `npm run dev`
- 隧道：`cloudflared tunnel run --token <token>`（计划任务已管自启，一般不用手跑）

## 配置要点（勿忘）

- DeepSeek 密钥通过 `backend\boot_studio.ps1` / `run_backend.ps1` 从 `~/.cc-connect\config.toml` 注入，不落盘、不打印。
- 切换 AI：设 `NOVEL_AI_PROVIDER=ark|deepseek` + 对应 `NOVEL_AI_API_KEY`。
- 数据在 `data\novel.db`（SQLite）。
- Vite 允许了 `novel.invokerz.xyz` Host（`frontend\vite.config.js` 的 `server.allowedHosts`），改域名要同步。

## 里程碑

- ✅ MVP 骨架：建作品/章节/自动保存/AI续写/大纲/扩写
- ⏳ 待做：大纲交互面板、人物管理页、导出 TXT/MD/DOCX、素材库(V2)、一键上传(后置)