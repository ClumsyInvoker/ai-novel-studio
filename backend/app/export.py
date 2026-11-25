"""导出：整本作品导出为 TXT / Markdown / DOCX / PDF。"""

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

from . import db

router = APIRouter(prefix="/api")

_MEDIA = {
    "txt": "text/plain; charset=utf-8",
    "md": "text/markdown; charset=utf-8",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


@router.get("/works/{wid}/export")
def export_work(wid: int, fmt: str = "txt"):
    if fmt not in _MEDIA:
        raise HTTPException(400, f"fmt 仅支持 {list(_MEDIA)}")
    conn = db.get_conn()
    try:
        w = conn.execute("SELECT * FROM works WHERE id=?", (wid,)).fetchone()
        if not w:
            raise HTTPException(404, "作品不存在")
        chapters = [dict(c) for c in conn.execute(
            "SELECT title,content,summary FROM chapters WHERE work_id=? ORDER BY sort_order,id", (wid,)).fetchall()]
    finally:
        conn.close()

    w = dict(w)
    if fmt == "txt":
        body, media = build_txt(w, chapters), _MEDIA["txt"]
    elif fmt == "md":
        body, media = build_markdown(w, chapters), _MEDIA["md"]
    elif fmt == "docx":
        body, media = build_docx(w, chapters), _MEDIA["docx"]
    else:
        body, media = build_pdf(w, chapters), _MEDIA["pdf"]

    # RFC 5987 filename*：百分号编码的 UTF-8，支持中文文件名（header 保持纯 ASCII）
    from urllib.parse import quote
    enc = quote(f"{w['title']}.{fmt}")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{enc}"}

    if isinstance(body, bytes):
        return Response(body, media_type=media, headers=headers)
    return PlainTextResponse(body, media_type=media, headers=headers)


def build_txt(w, chapters) -> str:
    lines = [w["title"], "=" * 12, ""]
    if w.get("intro"):
        lines += ["简介：", w["intro"], ""]
    for c in chapters:
        lines += [f"{c['title']}", "-" * 8, c["content"] or "", ""]
        if c.get("summary"):
            lines += [f"【摘要】{c['summary']}", ""]
    return "\n".join(lines)


def build_markdown(w, chapters) -> str:
    lines = [f"# {w['title']}", ""]
    if w.get("intro"):
        lines += [f"> {w['intro']}", ""]
    lines.append(f"（共 {len(chapters)} 章）")
    lines += ["", "---"]
    for i, c in enumerate(chapters, 1):
        lines += [f"## {i}. {c['title']}", "", c["content"] or "", ""]
        if c.get("summary"):
            lines += [f"*摘要：{c['summary']}*", ""]
    return "\n".join(lines)


def build_docx(w, chapters) -> bytes:
    from docx import Document
    doc = Document()
    doc.add_heading(w["title"], 0)
    if w.get("intro"):
        doc.add_paragraph(f"简介：{w['intro']}")
    for c in chapters:
        if c.get("title"):
            doc.add_heading(c["title"], 1)
        if c.get("content"):
            for para in c["content"].split("\n\n"):
                doc.add_paragraph(para.strip())
        if c.get("summary"):
            doc.add_paragraph(f"【摘要】{c['summary']}")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_pdf(w, chapters) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    bio = io.BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    h1 = ParagraphStyle("h1", fontName="STSong-Light", fontSize=20, leading=26, spaceAfter=6)
    h2 = ParagraphStyle("h2", fontName="STSong-Light", fontSize=15, leading=20, spaceBefore=10)
    body = ParagraphStyle("b", fontName="STSong-Light", fontSize=11, leading=18)
    summ = ParagraphStyle("s", fontName="STSong-Light", fontSize=9, leading=14, textColor=colors.grey)

    def esc(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    story = [Paragraph(esc(w["title"]), h1), Spacer(1, 4 * mm)]
    if w.get("intro"):
        story.append(Paragraph(f"简介：{esc(w['intro'])}", body))
    for c in chapters:
        if c.get("title"):
            story.append(Paragraph(esc(c["title"]), h2))
        if c.get("content"):
            for para in c["content"].split("\n\n"):
                if para.strip():
                    story.append(Paragraph(esc(para.strip()).replace("\n", "<br/>"), body))
        if c.get("summary"):
            story.append(Paragraph(f"【摘要】{esc(c['summary'])}", summ))
    doc.build(story)
    return bio.getvalue()