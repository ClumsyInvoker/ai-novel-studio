# ai-novel-studio · AI 网文写作助手

一个本地运行、可公网安全访问的 **AI 辅助网文写作工具**。把「灵感构思 → 大纲 → 逐章写作 → 一致性维护 → 导出」串成完整闭环。

技术栈：**FastAPI + SQLite** / **Vue3 + Element Plus + Vite** / **DeepSeek（OpenAI 兼容，可切方舟或自定义）**。

## ✨ 特性

- **灵感建书**：随机 / 关键词 / 番茄榜单趋势 → AI 给出书名、简介、世界观
- **AI 生成卷章结构**：一键生成多卷多章（含章纲），落库即可开写
- **流式续写**：打字机效果，可随时中断
- **按章纲扩写**：由章纲扩写成章，自动生成章节摘要
- **大纲多轮对话**：可追问细化剧情走向
- **人物管理**：AI 生成人设卡并自动落字段
- **长文一致性**：自动注入上文摘要 + 一键校验设定/人物冲突
- **风格卡**：每本设文风，统一全书 AI 生成风格
- **卷章管理**：分卷、章节移卷
- **导出**：TXT / Markdown / DOCX / PDF
- **移动端适配**：手机上也能顺畅写作
- **可公网部署**：搭配 Cloudflare Tunnel + Access 登录墙，随时随地访问

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+

### 1) 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8778
```

### 2) 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 3) 打开
浏览器访问 **http://127.0.0.1:5173**

### 4) 配置 AI Key
两种方式（任选其一）：
- 打开应用的 **设置** 页填写服务商与 API Key（保存到本地 `data/settings.json`）
- 或复制 `.env.example` 为 `.env` / 设置环境变量（见下）

```bash
NOVEL_AI_PROVIDER=deepseek          # deepseek | ark | custom
NOVEL_AI_API_KEY=your_api_key
# 可选
# NOVEL_AI_BASE_URL=https://api.deepseek.com
# NOVEL_AI_MODEL=deepseek-chat
# NOVEL_BACKEND_PORT=8778
```

> 优先级：设置页（`data/settings.json`）> 环境变量 > 内置默认。

## 📁 项目结构

```
backend/app/
  main.py            FastAPI 入口
  db.py              SQLite 连接/建表/迁移
  settings_store.py  设置持久化
  export.py          导出 TXT/MD/DOCX/PDF
  fanqie.py          番茄榜单元数据抓取（弱文本）
  ai/client.py       AI 调用封装（支持流式、多 provider）
  ai/prompts.py      各功能 prompt 模板
  routers/           works / ai / settings 路由
frontend/src/
  views/             Workspace / Characters / Settings
  components/        ChapterTree / OutlinePanel
  router/ api/       路由与 Axios 封装
data/                运行数据（SQLite 与设置，已在 .gitignore）
```

## 🌐 可选：公网访问

推荐用 [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)：
1. `cloudflared` 把 `localhost:5173` 暴露为你的域名
2. 在 Cloudflare Zero Trust 加 **Access** 邮箱登录墙，避免裸奔
3. 记得把域名加入 `frontend/vite.config.js` 的 `server.allowedHosts`

## 📄 License

[MIT](LICENSE)
