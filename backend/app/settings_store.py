"""设置持久化：data/settings.json 存 AI provider 配置。

密钥只落本地文件、不打印；读取返回给前端前脱敏。
优先级：settings.json > 环境变量 > 内置默认。"""

import os
import json

from . import db

SETTINGS_PATH = os.path.join(db.DATA_DIR, "settings.json")

DEFAULTS = {
    "provider": "deepseek",  # ark | deepseek | custom
    "api_key": "",
    "base_url": "",
    "model": "",
}

ALLOWED_PROVIDERS = ("ark", "deepseek", "custom")


def load() -> dict:
    data = dict(DEFAULTS)
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                data.update(stored)
        except Exception:
            pass
    return data


def save(settings: dict) -> dict:
    merged = dict(DEFAULTS)
    merged.update(settings)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return merged


MASK = "••••••••"


def public(s: dict) -> dict:
    out = dict(s)
    out["has_key"] = bool(out.get("api_key"))
    out["api_key"] = MASK if out["has_key"] else ""
    return out