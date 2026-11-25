"""作品 / 卷 / 章节 / 人物 CRUD（含存在性校验）。"""

from fastapi import APIRouter, HTTPException

from .. import db

router = APIRouter(prefix="/api")


def _ensure(conn, table: str, rid: int):
    """校验指定表存在主键 rid，否则 404。"""
    if conn.execute(f"SELECT 1 FROM {table} WHERE id=?", (rid,)).fetchone() is None:
        raise HTTPException(404, f"{table} 不存在")


# ---------- 作品 ----------
@router.get("/works")
def list_works():
    conn = db.get_conn()
    try:
        rows = conn.execute("SELECT id,title,intro,tags,created_at,updated_at FROM works ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/works/{wid}")
def get_work(wid: int):
    conn = db.get_conn()
    try:
        w = conn.execute("SELECT * FROM works WHERE id=?", (wid,)).fetchone()
        if not w:
            raise HTTPException(404, "作品不存在")
        data = dict(w)
        data["volumes"] = [dict(r) for r in conn.execute(
            "SELECT * FROM volumes WHERE work_id=? ORDER BY sort_order,id", (wid,)).fetchall()]
        data["chapters"] = [dict(r) for r in conn.execute(
            "SELECT id,volume_id,title,summary,status,word_count,sort_order FROM chapters WHERE work_id=? ORDER BY sort_order,id", (wid,)).fetchall()]
        data["characters"] = [dict(r) for r in conn.execute(
            "SELECT * FROM characters WHERE work_id=? ORDER BY id", (wid,)).fetchall()]
        return data
    finally:
        conn.close()


@router.post("/works")
def create_work(payload: dict):
    title = (payload.get("title") or "未命名作品").strip()
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO works(title,intro,tags,setting,style) VALUES(?,?,?,?,?)",
            (title, payload.get("intro", ""), payload.get("tags", ""),
             payload.get("setting", ""), payload.get("style", "")))
        conn.commit()
        return get_work(cur.lastrowid)
    finally:
        conn.close()


@router.put("/works/{wid}")
def update_work(wid: int, payload: dict):
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "UPDATE works SET title=?,intro=?,tags=?,setting=?,style=?,updated_at=datetime('now','localtime') WHERE id=?",
            (payload.get("title", "").strip(), payload.get("intro", ""),
             payload.get("tags", ""), payload.get("setting", ""),
             payload.get("style", ""), wid))
        if cur.rowcount == 0:
            raise HTTPException(404, "作品不存在")
        conn.commit()
        return get_work(wid)
    finally:
        conn.close()


@router.delete("/works/{wid}")
def delete_work(wid: int):
    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM works WHERE id=?", (wid,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ---------- 卷 ----------
@router.post("/works/{wid}/volumes")
def create_volume(wid: int, payload: dict):
    conn = db.get_conn()
    try:
        _ensure(conn, "works", wid)
        maxo = conn.execute("SELECT COALESCE(MAX(sort_order),0) m FROM volumes WHERE work_id=?", (wid,)).fetchone()["m"]
        cur = conn.execute("INSERT INTO volumes(work_id,title,outline,sort_order) VALUES(?,?,?,?)",
                           (wid, payload.get("title", "新卷"), payload.get("outline", ""), maxo + 1))
        conn.commit()
        return {"id": cur.lastrowid}
    finally:
        conn.close()


@router.put("/volumes/{vid}")
def update_volume(vid: int, payload: dict):
    conn = db.get_conn()
    try:
        _ensure(conn, "volumes", vid)
        conn.execute("UPDATE volumes SET title=?,outline=? WHERE id=?",
                     (payload.get("title", ""), payload.get("outline", ""), vid))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@router.delete("/volumes/{vid}")
def delete_volume(vid: int):
    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM volumes WHERE id=?", (vid,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ---------- 章节 ----------
@router.post("/works/{wid}/chapters")
def create_chapter(wid: int, payload: dict):
    conn = db.get_conn()
    try:
        _ensure(conn, "works", wid)
        maxo = conn.execute("SELECT COALESCE(MAX(sort_order),0) m FROM chapters WHERE work_id=?", (wid,)).fetchone()["m"]
        cur = conn.execute(
            "INSERT INTO chapters(work_id,volume_id,title,outline,content,status,sort_order) VALUES(?,?,?,?,?,?,?)",
            (wid, payload.get("volume_id"), payload.get("title", "新章节"),
             payload.get("outline", ""), payload.get("content", ""),
             payload.get("status", "draft"), maxo + 1))
        conn.commit()
        return {"id": cur.lastrowid}
    finally:
        conn.close()


@router.get("/chapters/{chid}")
def get_chapter(chid: int):
    conn = db.get_conn()
    try:
        r = conn.execute("SELECT * FROM chapters WHERE id=?", (chid,)).fetchone()
        if not r:
            raise HTTPException(404, "章节不存在")
        return dict(r)
    finally:
        conn.close()


@router.put("/chapters/{chid}")
def update_chapter(chid: int, payload: dict):
    conn = db.get_conn()
    try:
        _ensure(conn, "chapters", chid)
        content = payload.get("content", "")
        if "volume_id" in payload:
            conn.execute("UPDATE chapters SET volume_id=? WHERE id=?",
                         (payload.get("volume_id"), chid))
        conn.execute("UPDATE chapters SET title=?,outline=?,content=?,status=?,summary=?,word_count=?,updated_at=datetime('now','localtime') WHERE id=?",
                     (payload.get("title", ""), payload.get("outline", ""), content,
                      payload.get("status", "draft"), payload.get("summary", ""),
                      len(content), chid))
        conn.commit()
        return get_chapter(chid)
    finally:
        conn.close()


@router.delete("/chapters/{chid}")
def delete_chapter(chid: int):
    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM chapters WHERE id=?", (chid,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ---------- 人物 ----------
@router.post("/works/{wid}/characters")
def create_character(wid: int, payload: dict):
    conn = db.get_conn()
    try:
        _ensure(conn, "works", wid)
        cur = conn.execute(
            "INSERT INTO characters(work_id,name,identity,personality,motivation,relationships,growth,notes) VALUES(?,?,?,?,?,?,?,?)",
            (wid, payload.get("name", "新角色"), payload.get("identity", ""), payload.get("personality", ""),
             payload.get("motivation", ""), payload.get("relationships", ""), payload.get("growth", ""), payload.get("notes", "")))
        conn.commit()
        return {"id": cur.lastrowid}
    finally:
        conn.close()


@router.put("/characters/{cid}")
def update_character(cid: int, payload: dict):
    conn = db.get_conn()
    try:
        _ensure(conn, "characters", cid)
        conn.execute(
            "UPDATE characters SET name=?,identity=?,personality=?,motivation=?,relationships=?,growth=?,notes=? WHERE id=?",
            (payload.get("name", ""), payload.get("identity", ""), payload.get("personality", ""),
             payload.get("motivation", ""), payload.get("relationships", ""), payload.get("growth", ""),
             payload.get("notes", ""), cid))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@router.delete("/characters/{cid}")
def delete_character(cid: int):
    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM characters WHERE id=?", (cid,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()