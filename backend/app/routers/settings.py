"""设置页接口：读写 AI provider 配置（key 脱敏）。"""

from fastapi import APIRouter, HTTPException

from .. import settings_store

router = APIRouter(prefix="/api")


@router.get("/settings")
def get_settings():
    return settings_store.public(settings_store.load())


@router.put("/settings")
def put_settings(payload: dict):
    s = settings_store.load()
    MASK = settings_store.MASK

    if "provider" in payload:
        p = payload["provider"]
        if p not in settings_store.ALLOWED_PROVIDERS:
            raise HTTPException(400, f"provider 可选 {list(settings_store.ALLOWED_PROVIDERS)}")
        s["provider"] = p

    # api_key：空 / 掩码占位 → 保留原值不覆盖
    if "api_key" in payload:
        k = (payload["api_key"] or "").strip()
        if k and k != MASK:
            s["api_key"] = k

    if "base_url" in payload:
        s["base_url"] = (payload["base_url"] or "").strip()
    if "model" in payload:
        s["model"] = (payload["model"] or "").strip()

    saved = settings_store.save(s)
    return settings_store.public(saved)


@router.get("/settings/status")
def settings_status():
    """前端展示用：当前生效 provider / model / 是否已配 key。"""
    from ..ai import client
    p = client.provider_label()
    _, _, model, key = client._resolve()
    return {"provider": p, "model": model, "has_key": bool(key)}