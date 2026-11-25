"""FastAPI 入口。CORS 放行本地前端端口，启动时初始化数据库。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .routers import ai as ai_router
from .routers import works as works_router
from .routers import settings as settings_router
from . import export as export_router

app = FastAPI(title="AI 网文写作助手")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(works_router.router)
app.include_router(ai_router.router)
app.include_router(export_router.router)
app.include_router(settings_router.router)


@app.on_event("startup")
def _startup():
    db.init_db()
    from .ai import client
    app.state.ai_model = client.current_model()


@app.get("/api/health")
def health():
    from .ai import client
    return {"status": "ok", "model": client.current_model()}