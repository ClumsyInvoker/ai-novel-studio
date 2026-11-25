"""番茄小说榜单元数据抓取（弱文本）。

合规边界：仅读取公开的排行榜元数据（书名/简介片段、题材标签），
绝不下载章节正文或侵权内容。字体混淆导致的错乱文本交给 AI 侧结合行业常识推断。

fail-soft：任何异常都返回空列表，由 AI 端点降级为通用趋势灵感，不阻断流程。
"""

import re
import urllib.request

RANK_URL = "https://fanqienovel.com/rank"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def _fetch(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Referer": RANK_URL})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def _clean(html_frag: str) -> str:
    """去 HTML 标签 + 过滤字体混淆乱码，仅保留可读中英文与常用标点。"""
    text = re.sub(r"<[^>]+>", "", html_frag)
    keep = []
    for ch in text:
        o = ord(ch)
        if 0x4E00 <= o <= 0x9FFF:          # CJK 常用区
            keep.append(ch)
        elif 0x41 <= o <= 0x7A:            # ASCII 字母数字
            keep.append(ch)
        elif ch in "【】「」、，。！？；：'\"…+":
            keep.append(ch)
        # 其余（含私有区 PUA、符号区、生僻扩展区）视为混淆字形丢弃
    return "".join(keep)


def fetch_rank_labels(max_items: int = 20) -> list:
    """返回番茄综合榜每本作品的可读简介/题材标签片段（尽力而为）。"""
    try:
        html = _fetch(RANK_URL)
    except Exception:
        return []
    descs = re.findall(r'class="desc[^"]*"[^>]*>(.*?)</', html, re.S)
    out = []
    for frag in descs[:max_items]:
        t = _clean(frag)
        if len(t) >= 6:                     # 丢弃过短/全灭的
            out.append(t)
    return out