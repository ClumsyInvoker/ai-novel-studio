"""各功能的 prompt 模板。风格一致性靠「人设卡 + 上文摘要 + 风格设定」注入缓解。"""


def system_style(work_setting: str = "", style_notes: str = "") -> str:
    """统一世界观/风格的系统提示。"""
    s = "你是一名资深中文网络小说写手，创作言情/玄幻/都市等网文。"
    if work_setting:
        s += f"\n【作品世界观/设定】\n{work_setting}\n"
    if style_notes:
        s += f"\n【风格要求】\n{style_notes}\n"
    s += "\n写作要：节奏紧凑、爽点/情绪到位、口语化但流畅、尊重网文体裁惯例。"
    return s


def characters_blurb(characters) -> str:
    """把人设卡压缩成一段上下文。"""
    if not characters:
        return ""
    lines = []
    for c in characters:
        line = f"- {c.get('name','?')}({c.get('identity','')})：性格{c.get('personality','')}；目标{c.get('motivation','')}"
        if c.get("relationships"):
            line += f"；关系{c['relationships']}"
        lines.append(line)
    return "\n".join(lines)


def continue_prompt(prev_text, outline, char_blurb, target_len=800):
    """续写：给定上文、可选的章纲，续写 target_len 字。"""
    user = f"【当前章节/前文】\n{prev_text}\n"
    if outline:
        user += f"\n【本章要达成的要点】\n{outline}\n"
    if char_blurb:
        user += f"\n【登场人物】\n{char_blurb}\n"
    user += f"\n请顺着上文往下续写约 {target_len} 字，人物言行与性格一致，不要复述已写内容，直接输出续写正文，不要任何标题或解释。"
    return user


def outline_prompt(work_title, intro, prev_summary=""):
    """拉纲/章纲思考。"""
    user = f"作品《{work_title}》" + (f"，简介：{intro}" if intro else "")
    if prev_summary:
        user += f"\n已写章节摘要：\n{prev_summary}"
    user += "\n请输出面向后续创作的大纲，包含：当前进度、接下来 3-5 章的分章要点（每章一两句，含钩子/冲突/爽点）、中长期主线走向。用清晰分点列示。"
    return user


def chapter_draft_prompt(outline, char_blurb, prev_summary=""):
    """由章纲扩写成章 + 章节摘要。"""
    user = f"【本章纲】\n{outline}\n"
    if char_blurb:
        user += f"\n【登场人物】\n{char_blurb}\n"
    if prev_summary:
        user += f"\n【前文摘要】\n{prev_summary}\n"
    user += "\n请据此扩写成一章网文正文，约 2000 字。文末单独一行输出：@@SUMMARY@@ 本章一句话摘要（不超过 40 字）。正文不要含标题/解释。"
    return user


def character_card_prompt(work_title, intro, name=""):
    """生成/补全人设卡。要求键值行输出便于自动落入字段。"""
    user = f"作品《{work_title}》" + (f"，简介：{intro}。" if intro else "。")
    user += ("请为角色「" + name + "」" if name else "请设计一个主要角色")
    user += ("生成完整人设卡，严格按下面键名逐行输出（每行“键：值”，不要额外前言或标记）：\n"
             "身份：\n"
             "外貌：\n"
             "性格：\n"
             "动机/目标：\n"
             "内心矛盾：\n"
             "人际关系：\n"
             "成长弧线：\n"
             "每条一两句，客观具体。")
    return user


def inspire_prompt(keywords=""):
    """作品灵感生成。三行结构输出便于解析并回到新建表单。"""
    user = ("你是一位极有创意的中文网络小说策划。请为用户构思一部有新意、可落笔的网文，严格按下面三行输出：\n"
            "书名：<响亮好记>\n"
            "简介：<一句话吸引人的简介，带钩子>\n"
            "设定：<世界观/核心设定两三句，越独特越好>\n"
            "要求：题材/脑洞/爽点鲜明、有开篇钩子，避免烂大街套路与重复已有设定。")
    if keywords:
        user += f"\n\n用户给的方向/关键词（紧扣这些构思）：{keywords}"
    return user


def hot_inspired_prompt(rank_labels, keywords=""):
    """番茄榜单趋势 + 灵感：先提炼热门题材，再据此给新作灵感（三行结构）。"""
    user = "你既是网文市场热点分析师又是创意策划。"
    if rank_labels:
        user += ("\n下面是刚从番茄小说排行榜抓到的近期热门作品简介片段"
                 "（个别字符因反爬成乱码，但题材标签大多可辨识）：\n")
        user += "\n".join(f"- {t[:44]}" for t in rank_labels[:20])
        user += ("\n\n请分两段输出：\n一段【趋势】用 2-4 条要点，每条一句话，提炼这些上榜作品体现的"
                 "热门题材 / 人设 / 爽点 / 结构；\n二段再据此构思 1 部有差异化、不撞车的新作，严格按三行：\n"
                 "书名：\n简介：\n设定：")
    else:
        user += ("\n（番茄榜单暂时抓不到）请直接基于当前网文市场通行的热门趋势构思 1 部新作，严格按三行输出：\n"
                 "书名：\n简介：\n设定：")
    if keywords:
        user += f"\n用户给的方向/关键词（紧扣）：{keywords}"
    return user


def consistency_prompt(w, char_blurb, ch_title, ch_content):
    """一致性校验：对照作品设定/人物，检查当前章是否有矛盾。"""
    user = f"作品《{w['title']}》"
    if w.get("intro"):
        user += f"\n【作品设定】{w['intro']}"
    if w.get("setting"):
        user += f"\n【世界观】{w['setting']}"
    if char_blurb:
        user += f"\n【人物设定】\n{char_blurb}"
    user += f"\n\n【待校验章节】{ch_title}\n{ch_content}\n"
    user += ("请核查该章与上述设定/人物是否存在矛盾（人物性格、能力、称谓、身份关系、时间线、世界观设定等不一致）。"
             "若有，逐条列出：`冲突：<矛盾点>` 并给出简短修改建议；若没有，只输出`未发现明显冲突。`")
    return user