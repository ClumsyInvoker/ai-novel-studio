"""AI 服务层：OpenAI 兼容接口封装，支持方舟(volc)/DeepSeek/自定义。

密钥优先级：settings.json(from 设置页) > 环境变量 > 内置默认。
绝不硬编码密钥。

provider 可用：ark / deepseek / custom。
  - ark     base=http://ark.cn-beijing.volces.com/api/v3
  - deepseek base=http://api.deepseek.com
  - custom  base 必须显式填（在设置页）
设置页可覆盖 provider 的 base_url 与 model。
"""

import os

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

from .. import settings_store

_PROVIDERS = {
    "ark": {
        "base": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-1-6-250615",
    },
    "deepseek": {
        "base": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
    "custom": {"base": "", "model": ""},
}


def _resolve():
    """返回 (provider, base_url, model, api_key)，settings 优先、env 兜底。"""
    st = settings_store.load()
    provider = st.get("provider") or "deepseek"
    if provider not in _PROVIDERS:
        provider = "custom"

    base = (st.get("base_url") or "").strip() or _PROVIDERS[provider]["base"]
    model = (st.get("model") or "").strip() or _PROVIDERS[provider]["model"]
    key = (st.get("api_key") or "").strip()

    if not key:
        key = os.environ.get("NOVEL_AI_API_KEY", "").strip()
    if not key and provider in ("ark", "deepseek"):
        key = os.environ.get(provider.upper() + "_API_KEY", "").strip()
    return provider, base, model, key


def chat(messages, temperature=0.8, max_tokens=2000):
    """通用 chat 调用，返回文本。messages: [{role, content}]"""
    provider, base, model, key = _resolve()
    if not base:
        raise RuntimeError("custom provider 需要在设置页填写 Base URL")
    if not key:
        raise RuntimeError("缺少 API Key：请在设置页填写，或设置环境变量")
    if OpenAI is None:
        raise RuntimeError("未安装 openai 库")
    client = OpenAI(api_key=key, base_url=base)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def chat_stream(messages, temperature=0.85, max_tokens=2000):
    """流式 chat，返回可迭代 chunk（每个含 choices[].delta.content）。"""
    provider, base, model, key = _resolve()
    if not base:
        raise RuntimeError("custom provider 需要在设置页填写 Base URL")
    if not key:
        raise RuntimeError("缺少 API Key：请在设置页填写，或设置环境变量")
    if OpenAI is None:
        raise RuntimeError("未安装 openai 库")
    client = OpenAI(api_key=key, base_url=base)
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )


def current_model() -> str:
    _, _, model, _ = _resolve()
    return model


def provider_label() -> str:
    p, _, _, _ = _resolve()
    return p