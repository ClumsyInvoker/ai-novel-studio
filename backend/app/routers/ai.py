"""AI 生成端点：续写 / 大纲 / 章节+摘要 / 人物卡。"""

from fastapi import APIRouter, HTTPException

from .. import db
from ..ai import client, prompts

router = APIRouter(prefix="/api")


def _work_with_ctx(wid: int):
    """拉取作品 + 全部人物 + 指定章节，拼成上下文字典。"""
    conn = db.get_conn()
    try:
        w = conn.execute("SELECT * FROM works WHERE id=?", (wid,)).fetchone()
        if not w:
            raise HTTPException(404, "作品不存在")
        chars = [dict(r) for r in conn.execute("SELECT * FROM characters WHERE work_id=?", (wid,)).fetchall()]
        return dict(w), chars
    finally:
        conn.close()


def _sys_context(w, chars, conn, wid, exclude_chid, n=3) -> str:
    """长文一致性：风格卡 + 世界观 + 近期上文梗概，一并注入系统提示。"""
    sys_text = prompts.system_style(w.get("setting", ""), w.get("style", ""))
    rows = conn.execute(
        "SELECT title,summary FROM chapters WHERE work_id=? AND summary!='' AND id!=? ORDER BY sort_order DESC LIMIT ?",
        (wid, exclude_chid, n)).fetchall()
    if rows:
        brief = "\n".join(f"- {r['title']}：{r['summary']}" for r in reversed(rows))
        sys_text += "\n\n【近期上文梗概（保持连续性）】\n" + brief
    return sys_text


@router.post("/ai/continue")
def ai_continue(payload: dict):
    """续写。入参: work_id, chapter_id, target_len。"""
    wid, chid = payload.get("work_id"), payload.get("chapter_id")
    target = int(payload.get("target_len", 800))
    conn = db.get_conn()
    try:
        ch = conn.execute("SELECT * FROM chapters WHERE id=? AND work_id=?", (chid, wid)).fetchone()
        if not ch:
            raise HTTPException(404, "章节不存在")
        w, chars = _work_with_ctx(wid)
        prev = (ch["content"] or "")
        if not prev:
            raise HTTPException(400, "章节正文为空，无法续写")
        msgs = [
            {"role": "system", "content": _sys_context(w, chars, conn, wid, chid)},
            {"role": "user", "content": prompts.continue_prompt(prev, ch["outline"], prompts.characters_blurb(chars), target)},
        ]
        text = client.chat(msgs, temperature=0.85, max_tokens=max(target * 2, 1000))
        return {"content": text}
    finally:
        conn.close()


@router.post("/ai/continue-stream")
def ai_continue_stream(payload: dict):
    """流式续写（SSE）。入参: work_id, chapter_id, target_len。"""
    import json
    from fastapi.responses import StreamingResponse
    wid, chid = payload.get("work_id"), payload.get("chapter_id")
    target = int(payload.get("target_len", 800))
    conn = db.get_conn()
    try:
        ch = conn.execute("SELECT * FROM chapters WHERE id=? AND work_id=?", (chid, wid)).fetchone()
        if not ch:
            raise HTTPException(404, "章节不存在")
        w, chars = _work_with_ctx(wid)
        prev = (ch["content"] or "")
        if not prev:
            raise HTTPException(400, "章节正文为空，无法续写")
        msgs = [
            {"role": "system", "content": _sys_context(w, chars, conn, wid, chid)},
            {"role": "user", "content": prompts.continue_prompt(prev, ch["outline"], prompts.characters_blurb(chars), target)},
        ]
    finally:
        conn.close()

    def gen():
        try:
            stream = client.chat_stream(msgs, temperature=0.85, max_tokens=max(target * 2, 1000))
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'text': chunk.choices[0].delta.content})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/ai/outline")
def ai_outline(payload: dict):
    """大纲思考。入参: work_id。"""
    wid = payload.get("work_id")
    conn = db.get_conn()
    try:
        w, chars = _work_with_ctx(wid)
        prev_summary = "\n".join(
            f"{r['title']}: {r['summary']}" for r in conn.execute(
                "SELECT title,summary FROM chapters WHERE work_id=? AND summary!='' ORDER BY sort_order", (wid,)).fetchall())
        msgs = [
            {"role": "user", "content": prompts.outline_prompt(w["title"], w["intro"], prev_summary)},
        ]
        text = client.chat(msgs, temperature=0.7, max_tokens=1500)
        return {"content": text}
    finally:
        conn.close()


@router.post("/ai/outline-chat")
def ai_outline_chat(payload: dict):
    """多轮大纲对话。入参: work_id, history=[{role:'user'|'assistant', content}]。
    首轮自动附带作品设定/简介/已有章节摘要作为上下文；后续各轮按 history 多轮续推进。"""
    wid = payload.get("work_id")
    history = payload.get("history") or []
    if not isinstance(history, list):
        raise HTTPException(400, "history 必须是数组")
    conn = db.get_conn()
    try:
        w, chars = _work_with_ctx(wid)
        summaries = conn.execute(
            "SELECT title,summary FROM chapters WHERE work_id=? AND summary!='' ORDER BY sort_order", (wid,)).fetchall()

        # 系统上下文：作品基调 + 已写进度
        sys_ctx = "你是资深中文网络小说大纲策划，用分点、清晰的网文大纲思维辅助作者构思。"
        sys_ctx += f"\n【作品】《{w['title']}》" + (f"\n【简介】{w['intro']}" if w.get("intro") else "")
        if summaries:
            sys_ctx += "\n【已有章节进度】\n" + "\n".join(f"- {s['title']}: {s['summary']}" for s in summaries)
        if w.get("setting"):
            sys_ctx += f"\n【设定】{w['setting']}"

        user_instruction = f"请先从整体给出接下来 3-5 章的大纲（每章含钩子/冲突/爽点），再听我后续追问做细化。"

        msgs = [{"role": "system", "content": sys_ctx}]
        if not history:
            msgs.append({"role": "user", "content": user_instruction})
        else:
            for h in history:
                if h.get("role") not in ("user", "assistant") or not h.get("content"):
                    raise HTTPException(400, "history 项需含 role(user/assistant) 和 content")
                msgs.append({"role": h["role"], "content": h["content"][:4000]})

        text = client.chat(msgs, temperature=0.72, max_tokens=1800)
        return {"content": text}
    finally:
        conn.close()


@router.post("/ai/draft")
def ai_draft(payload: dict):
    """由章纲扩写成章 + 章节摘要, 并写回该章节。入参: chapter_id。"""
    chid = payload.get("chapter_id")
    conn = db.get_conn()
    try:
        ch = conn.execute("SELECT * FROM chapters WHERE id=?", (chid,)).fetchone()
        if not ch:
            raise HTTPException(404, "章节不存在")
        if not ch["outline"]:
            raise HTTPException(400, "章节没有章纲，无法拆分。请先写章纲或用大纲生成了章节")
        w, chars = _work_with_ctx(ch["work_id"])
        # 前文摘要应对齐"上一章"而非当前章
        prev_row = conn.execute(
            "SELECT summary FROM chapters WHERE work_id=? AND id!=? AND summary!='' ORDER BY sort_order DESC LIMIT 1",
            (ch["work_id"], chid)).fetchone()
        prev_summary = prev_row["summary"] if prev_row else ""
        msgs = [
            {"role": "system", "content": _sys_context(w, chars, conn, ch["work_id"], chid)},
            {"role": "user", "content": prompts.chapter_draft_prompt(ch["outline"], prompts.characters_blurb(chars), prev_summary)},
        ]
        text = client.chat(msgs, temperature=0.8, max_tokens=3500)
        # 拆分正文与摘要
        summary = ""
        if "@@SUMMARY@@" in text:
            body, _, summ = text.partition("@@SUMMARY@@")
            text, summary = body.strip(), summ.strip()
        conn.execute("UPDATE chapters SET content=?, summary=?, status='draft', word_count=? WHERE id=?",
                     (text, summary, len(text), chid))
        conn.commit()
        return {"content": text, "summary": summary}
    finally:
        conn.close()


def _parse_card(text: str) -> dict:
    """解析人设卡键值行：{字段名: 内容}。"""
    import re
    keys = ["身份", "外貌", "性格", "动机/目标", "内心矛盾", "人际关系", "成长弧线"]
    spans = []
    for k in keys:
        m = re.search(re.escape(k) + r"[:：]", text)
        if m:
            spans.append((k, m.end()))
    spans.sort(key=lambda x: x[1])
    res = {}
    for i, (k, start) in enumerate(spans):
        end = spans[i + 1][1] if i + 1 < len(spans) else len(text)
        v = text[start:end].strip()
        if v:
            res[k] = v
    return res


@router.post("/ai/character-card")
def ai_character_card(payload: dict):
    """生成人设卡。返回可自动落入字段的 fields + 原文。入参: work_id, name(可选)。"""
    wid = payload.get("work_id")
    w, _ = _work_with_ctx(wid)
    name = payload.get("name", "")
    text = client.chat(
        [{"role": "user", "content": prompts.character_card_prompt(w["title"], w["intro"], name)}],
        temperature=0.7, max_tokens=1200)

    parsed = _parse_card(text)
    mapping = {"身份": "identity", "性格": "personality", "动机/目标": "motivation",
               "人际关系": "relationships", "成长弧线": "growth"}
    fields = {mapping[k]: v for k, v in parsed.items() if k in mapping}
    extra = [f"外貌：{parsed[k]}" for k in ("外貌", "内心矛盾") if parsed.get(k)]
    if extra:
        fields["notes"] = "；".join(extra)
    return {"content": text, "fields": fields or None}


def _parse_inspire(text: str) -> dict:
    """从三行结构解析书名/简介/设定。"""
    import re
    def grab(key):
        m = re.search(key + r"[:：]\s*(.+)", text)
        return m.group(1).strip() if m else ""
    return {
        "title": grab("书名"),
        "intro": grab("简介"),
        "setting": grab("设定"),
        "raw": text,
    }


@router.post("/ai/inspire")
def ai_inspire(payload: dict):
    """作品灵感：入参 keywords(可选)。返回书名/简介/设定，可一键建书。"""
    keywords = (payload.get("keywords") or "").strip()
    msgs = [{"role": "user", "content": prompts.inspire_prompt(keywords)}]
    text = client.chat(msgs, temperature=1.0, max_tokens=700)
    return _parse_inspire(text)


@router.post("/ai/hot-inspired")
def ai_hot_inspired(payload: dict):
    """番茄榜单热门灵感：抓榜 → AI 提炼趋势 → 给新作灵感（三行）。入参 keywords(可选)。"""
    keywords = (payload.get("keywords") or "").strip()
    from .. import fanqie
    labels = fanqie.fetch_rank_labels(20)
    text = client.chat(
        [{"role": "user", "content": prompts.hot_inspired_prompt(labels, keywords)}],
        temperature=1.0, max_tokens=900)
    return {**_parse_inspire(text), "sourced": bool(labels)}


def _parse_structure(text: str):
    """从 AI 输出中提取 JSON 结构（容忍 markdown 裹壳/多余文字）。"""
    import json
    s = text.find("{")
    e = text.rfind("}")
    if s < 0 or e < s:
        return None
    try:
        data = json.loads(text[s:e + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


@router.post("/ai/generate-structure")
def ai_generate_structure(payload: dict):
    """按作品设定/进度，AI 生成卷章结构并直接落库为卷+章。
    入参: work_id, instruction(可选)。返回创建的卷数/章数。"""
    wid = payload.get("work_id")
    ins = (payload.get("instruction") or "").strip()
    w, _ = _work_with_ctx(wid)

    sys_ctx = "你是中文网络小说卷章结构规划师，擅长把作品拆成清晰的卷与章层级。"
    sys_ctx += f"\n【作品】《{w['title']}》"
    if w.get("intro"):
        sys_ctx += f"\n【简介】{w['intro']}"
    if w.get("setting"):
        sys_ctx += f"\n【设定】{w['setting']}"

    user = ("请为这部作品规划一套可落地的卷章结构，只输出一个 JSON 对象（不要 markdown 代码块、不要任何多余文字），字段形如：\n"
            "{\"volumes\":[{\"title\":\"卷名\",\"chapters\":[{\"title\":\"章名\",\"outline\":\"一两句话章纲，含钩子/冲突或爽点\"}]}]}\n"
            "要求：3-5 卷，每卷 5-8 章，章纲简短可执行、有明显钩子与推进。")
    if ins:
        user += f"\n紧扣以下方向构思：{ins}"

    msgs = [{"role": "system", "content": sys_ctx}, {"role": "user", "content": user}]
    text = client.chat(msgs, temperature=0.8, max_tokens=2500)

    data = _parse_structure(text)
    if not data or not isinstance(data.get("volumes"), list):
        raise HTTPException(400, "AI 未返回可解析的卷章结构，请稍后重试。原始返回已附。" + text[:200])

    conn = db.get_conn()
    vcount = ccount = 0
    try:
        for iv, vol in enumerate(data["volumes"], 1):
            if not isinstance(vol, dict) or not vol.get("title"):
                continue
            cur = conn.execute(
                "INSERT INTO volumes(work_id,title,outline,sort_order) VALUES(?,?,?,?)",
                (wid, str(vol["title"])[:120], "", iv))
            vid = cur.lastrowid
            vcount += 1
            for ic, ch in enumerate(vol.get("chapters") or [], 1):
                if not isinstance(ch, dict) or not ch.get("title"):
                    continue
                conn.execute(
                    "INSERT INTO chapters(work_id,volume_id,title,outline,content,status,sort_order) VALUES(?,?,?,?,?,?,?)",
                    (wid, vid, str(ch["title"])[:120], str(ch.get("outline", ""))[:500], "", "draft", ic))
                ccount += 1
        conn.commit()
    finally:
        conn.close()
    return {"volumes": vcount, "chapters": ccount, "raw": data}


@router.post("/ai/consistency-check")
def ai_consistency_check(payload: dict):
    """一致性校验：对照作品设定/人物，检查当前章冲突。入参: work_id, chapter_id。"""
    wid = payload.get("work_id")
    chid = payload.get("chapter_id")
    conn = db.get_conn()
    try:
        ch = conn.execute("SELECT * FROM chapters WHERE id=? AND work_id=?", (chid, wid)).fetchone()
        if not ch:
            raise HTTPException(404, "章节不存在")
        w, chars = _work_with_ctx(wid)
        content = ch["content"] or ""
        if not content:
            raise HTTPException(400, "章节正文为空，无法校验")
        msgs = [
            {"role": "user", "content": prompts.consistency_prompt(w, prompts.characters_blurb(chars), ch["title"], content)},
        ]
        text = client.chat(msgs, temperature=0.3, max_tokens=900)
        return {"content": text}
    finally:
        conn.close()