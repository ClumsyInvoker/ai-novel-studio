"""SQLite 存储层。数据放在项目 data/novel.db。

用内置 sqlite3，避免重依赖。提供到连接与建表。"""

import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DB_PATH = os.path.join(DATA_DIR, "novel.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT '',
    intro TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    setting TEXT NOT NULL DEFAULT '',
    style TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS volumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    outline TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    volume_id INTEGER,
    title TEXT NOT NULL DEFAULT '',
    outline TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',   -- draft / done
    word_count INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE,
    FOREIGN KEY(volume_id) REFERENCES volumes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    identity TEXT NOT NULL DEFAULT '',      -- 身份
    personality TEXT NOT NULL DEFAULT '',  -- 性格
    motivation TEXT NOT NULL DEFAULT '',   -- 动机/目标
    relationships TEXT NOT NULL DEFAULT '',-- 人际关系
    growth TEXT NOT NULL DEFAULT '',       -- 成长线
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ch_work ON chapters(work_id);
CREATE INDEX IF NOT EXISTS idx_ch_vol ON chapters(volume_id);
CREATE INDEX IF NOT EXISTS idx_char_work ON characters(work_id);
"""


def get_conn() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA journal_mode = WAL")
        # 轻量迁移：旧库 works 补充 style 列
        cols = [r[1] for r in conn.execute("PRAGMA table_info(works)")]
        if "style" not in cols:
            conn.execute("ALTER TABLE works ADD COLUMN style TEXT NOT NULL DEFAULT ''")
        conn.commit()
    finally:
        conn.close()


def now() -> str:
    # 供 SQL 中用
    return "datetime('now','localtime')"