# AI 网文写作助手 · 项目说明书

项目：ai-novel-studio　|　更新：2026-10-19　|　用途：说明项目是什么、怎么用、怎么跑、怎么改，供接手/回顾

# 1. 这是什么

一个个人用的 AI 辅助网文写作工具：本地运行、可公网安全访问（手机也能写），把「构思 → 大纲 → 逐章写作 → 一致性维护 → 导出」串成完整闭环。

## 核心能力

- 灵感建书：随机 / 按关键词 / 抓番茄榜单趋势，AI 给书名+简介+设定
- AI 生成整本卷章结构：一键产出多卷多章，每章带章纲
- 逐章写作：编辑器 + 防抖自动保存；按章纲 AI 扩写成章并自动生成摘要
- AI 续写：流式打字机输出，可随时中断
- 大纲对话：多轮追问细化大纲
- 人物形象：AI 生成人设卡并自动填字段
- 长文一致性：自动注入上文摘要 + 一键校验设定/人物冲突
- 风格卡：每本文风设定，统一全本 AI 生成文风
- 导出：TXT / Markdown / DOCX / PDF
- 公网访问：Cloudflare Tunnel + 邮箱登录墙
# 2. 快速开始

## 环境要求

- Python：conda 环境 dev（Python 3.12）
- Node.js：v18+（用于前端 Vite）
- 依赖：后端 fastapi/uvicorn/openai/python-docx/reportlab；前端 vue/vue-router/pinia/axios/element-plus
## 启动（Windows）

```
后端：双击或运行  backend\run_backend.ps1
```
```
前端：在 frontend\ 目录运行  npm run dev
```
```
（后端脚本会自动从 ~/.cc-connect/config.toml 读取 DeepSeek 密钥注入环境，不落盘）
```
## 访问

- 本地：http://127.0.0.1:5173
- 公网：https://novel.invokerz.xyz（先过 Cloudflare Access 邮箱验证码）
# 3. 怎么用（功能指南）

## 建作品

- 工作台顶部「＋ 作品」→ 可手填，或点「🎲 随机」「✨ 灵感（带关键词）」「🔥 番茄」生成灵感 → 填入后创建
## 写章节

- 左侧/抽屉章树选章节 → 中部编辑器写正文（自动保存）
- 顶部可编辑章节标题、填章纲（供 AI 参考）
## AI 写作

- ✍ 续写：按前文续写（流式，可停止）
- 🧩 按章纲扩写：由章纲扩写成整章并写回正文+摘要
- 🧭 大纲：多轮对话式大纲面板，也可一键「由大纲生成 卷/章 结构」
- 🎨 风格：设置本书文风，注入所有 AI 生成
- 🔍 校验：对照世界观+人物，查当前章冲突
## 人物 / 卷 / 导出

- 顶部「人物」页：管理角色卡，可 AI 生成人设卡
- 章树顶部「＋卷」；每章 📁 可移到某卷
- 顶部「⬇ 导出」：TXT / Markdown / DOCX / PDF
## 设置

- 顶部「设置」页：切换服务商（DeepSeek/方舟/自定义）、填 API Key（掩码保存，settings 优先于环境变量）
# 4. 架构与代码地图

## 目录结构

```
ai-novel-studio/
```
```
├─ backend/app/            后端
```
```
│  ├─ main.py             FastAPI 入口 + CORS + 路由挂载
```
```
│  ├─ db.py               SQLite 连接 / 建表 / 迁移(WAL)
```
```
│  ├─ settings_store.py   设置持久化(data/settings.json)
```
```
│  ├─ export.py           导出 TXT/MD/DOCX/PDF
```
```
│  ├─ fanqie.py           番茄榜单抓取(弱文本)
```
```
│  ├─ ai/client.py        AI 调用封装(含流式, 多 provider)
```
```
│  ├─ ai/prompts.py       各功能 prompt 模板
```
```
│  └─ routers/            works.py / ai.py / settings.py
```
```
├─ frontend/src/           前端
```
```
│  ├─ views/              Workspace.vue / Characters.vue / Settings.vue
```
```
│  ├─ components/         ChapterTree.vue / OutlinePanel.vue
```
```
│  ├─ router/ api/       路由 / Axios 封装
```
```
│  └─ App.vue main.js    外壳 + 入口
```
```
├─ data/                  作品库(novel.db) + 设置(settings.json)
```
```
└─ README.md PLAN.md GUIDE.md
```
## 后端分层

- db.py：所有 SQL 表定义与连接（含 WAL、busy_timeout、style 列迁移）
- routers/works.py：作品/卷/章节/人物 CRUD（带存在性校验）
- routers/ai.py：所有 AI 端点（续写/大纲/扩写/人设/灵感/结构/校验）
- routers/settings.py：设置读写
- ai/client.py：统一调用，provider 优先级 settings.json > 环境变量
- ai/prompts.py：全部 prompt 模板集中在此
## 数据模型（4 张表）

- works：id, title, intro, tags, setting(世界观), style(文风), 时间戳
- volumes：id, work_id, title, outline, sort_order
- chapters：id, work_id, volume_id, title, outline(章纲), content(正文), summary(摘要), status, word_count, sort_order
- characters：id, work_id, name, identity, personality, motivation, relationships, growth, notes
## API 一览（29 个端点，前缀 /api）

- 作品：GET/POST /works；GET/PUT/DELETE /works/{id}
- 卷：POST /works/{id}/volumes；PUT/DELETE /volumes/{id}
- 章节：POST /works/{id}/chapters；GET/PUT/DELETE /chapters/{id}
- 人物：POST /works/{id}/characters；PUT/DELETE /characters/{id}
- AI：/ai/continue, /ai/continue-stream(SSE), /ai/outline, /ai/outline-chat, /ai/draft, /ai/character-card, /ai/inspire, /ai/hot-inspired, /ai/generate-structure, /ai/consistency-check
- 设置：GET/PUT /settings, GET /settings/status
- 导出：GET /works/{id}/export?fmt=txt|md|docx|pdf
# 5. 怎么改（开发者指南）

## 加一个新 API

- 在 routers/ 对应文件加 @router.post/get(...) 函数；新模块则在 main.py 里 include_router
## 加一个新前端页面

- 在 views/ 新建 .vue；在 router/index.js 注册路由；在 App.vue 顶部导航加链接
## 改 AI 行为

- 改措辞/输出格式 → 改 ai/prompts.py 里对应 prompt 函数
- 改调用参数（温度/长度/模型）→ 改 routers/ai.py 对应端点里的 client.chat(...)
## 改数据模型

- 在 db.py 的 SCHEMA 加列；对已有库补 ALTER TABLE 迁移（参考 style 列的写法）
## 换 AI 模型 / provider

- 在设置页切换，或改 ai/client.py 的 _PROVIDERS 默认值；密钥走 settings.json 或环境变量
## 加一个端到端 AI 功能（示例步骤）

- 1) prompts.py 加 prompt　2) routers/ai.py 加端点调 client.chat　3) 前端加按钮调该端点　4) 测试
# 6. 运维与部署

## 端口与进程

- 前端 5173（唯一要访问的端口）；后端 8778（前端 /api 代理到它）
- 后端端口可用环境变量 NOVEL_BACKEND_PORT 覆盖
## 公网部署

- Cloudflare Tunnel（cloudflared）把 localhost:5173 暴露为 https://novel.invokerz.xyz
- Cloudflare Access 在域名上套邮箱登录墙（未授权 302 拦截）
- Vite 需在 vite.config.js 的 server.allowedHosts 放行域名
## 开机自启（计划任务）

- cloudflared-novel-writer：登录后拉起隧道
- novel-studio-services：登录后拉起前后端（backend\boot_studio.ps1，幂等）
## 密钥管理

- 优先级：data/settings.json（设置页写入）> 环境变量 > 内置默认
- data/ 已加入 .gitignore，防止密钥/作品库误提交
## 备份

- 直接备份 data/ 目录（novel.db + settings.json）即可
## 故障排查

- 外网打不开：确认 cloudflared 进程在跑、5173 在监听
- AI 报错：检查设置页 Key / 服务商；看后端日志
- 页面空白：看浏览器控制台 + 前端 vite 编译输出
# 7. 已知限制与待办

## 限制

- 单机单用户：无账号、无多端同步、无自动备份
- 无自动化测试、无类型标注
- 应用层无鉴权（仅靠 Cloudflare Access）
- Workspace.vue 偏大（约 492 行），待拆分
## 待办（优先级）

- P0 工程化：测试 + 类型 + 拆组件
- P1 功能：校对润色 / 自动标题 / 导入作品 / 版本快照 / 写作统计 / 灵感碎片桶
- P2 数据多端：自动备份、多设备同步、素材库
- P3 商业化：分享、协作、一键上传平台
# 8. 关键文件速查

- 入口：backend/app/main.py　前端 frontend/src/main.js
- 数据模型：backend/app/db.py
- AI 逻辑：backend/app/routers/ai.py + ai/prompts.py + ai/client.py
- 主界面：frontend/src/views/Workspace.vue
- 启动脚本：backend/run_backend.ps1、boot_studio.ps1
- 数据目录：data/（novel.db、settings.json）