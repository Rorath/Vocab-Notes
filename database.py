import sqlite3
import json

DB = "vocab.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                english_def TEXT,
                chinese_def TEXT,
                sentence TEXT,
                examples TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(words)")]
        # Migration: add category column if an older DB is missing it
        if "category" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN category TEXT")
        # Migration: multi-example support — add examples (JSON) and backfill
        # each row's old single sentence into a one-item list.
        if "examples" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN examples TEXT")
            for r in conn.execute("SELECT id, sentence FROM words").fetchall():
                s = (r["sentence"] or "").strip()
                conn.execute(
                    "UPDATE words SET examples = ? WHERE id = ?",
                    (json.dumps([s] if s else []), r["id"])
                )
        # Migration: multi-definition support — add english_defs (JSON) and
        # backfill each row's old single english_def into a one-item list.
        if "english_defs" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN english_defs TEXT")
            for r in conn.execute("SELECT id, english_def FROM words").fetchall():
                d = (r["english_def"] or "").strip()
                conn.execute(
                    "UPDATE words SET english_defs = ? WHERE id = ?",
                    (json.dumps([d] if d else []), r["id"])
                )

# Map sort keys -> SQL ORDER BY clauses (whitelist, so it's injection-safe)
SORT_OPTIONS = {
    "recent": "created_at DESC",
    "oldest": "created_at ASC",
    "az": "word COLLATE NOCASE ASC",
    "za": "word COLLATE NOCASE DESC",
}

def _dump_list(items):
    """Serialize a list of strings to JSON, dropping blanks."""
    return json.dumps([i for i in (items or []) if i])

def add_word(word, english_defs=None, chinese_def="", examples=None, category=""):
    defs = [d for d in (english_defs or []) if d]
    legacy = defs[0] if defs else ""  # keep the NOT NULL english_def column populated
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO words (word, english_def, english_defs, chinese_def, examples, category)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (word, legacy, _dump_list(defs), chinese_def, _dump_list(examples), category)
        )

def get_all_words(sort="recent", category=None):
    order = SORT_OPTIONS.get(sort, SORT_OPTIONS["recent"])
    query = "SELECT * FROM words"
    params = []
    if category:
        query += " WHERE category = ?"
        params.append(category)
    query += f" ORDER BY {order}"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()

def get_categories():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM words WHERE category IS NOT NULL AND category != '' ORDER BY category COLLATE NOCASE"
        ).fetchall()
    return [r["category"] for r in rows]

def get_ungrouped_words(sort="recent"):
    order = SORT_OPTIONS.get(sort, SORT_OPTIONS["recent"])
    with get_conn() as conn:
        return conn.execute(
            f"SELECT * FROM words WHERE category IS NULL OR category = '' ORDER BY {order}"
        ).fetchall()

def get_group_summary():
    """Return total word count, ungrouped count, and each group with its count."""
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM words").fetchone()["n"]
        ungrouped = conn.execute(
            "SELECT COUNT(*) AS n FROM words WHERE category IS NULL OR category = ''"
        ).fetchone()["n"]
        rows = conn.execute("""
            SELECT category AS name, COUNT(*) AS count
            FROM words
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY category COLLATE NOCASE
        """).fetchall()
    return {
        "total": total,
        "ungrouped": ungrouped,
        "groups": [{"name": r["name"], "count": r["count"]} for r in rows],
    }

def get_word(word_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()

def delete_word(word_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM words WHERE id = ?", (word_id,))

def update_word(word_id, word, english_defs, chinese_def, examples, category=""):
    defs = [d for d in (english_defs or []) if d]
    legacy = defs[0] if defs else ""
    with get_conn() as conn:
        conn.execute(
            "UPDATE words SET word=?, english_def=?, english_defs=?, chinese_def=?, examples=?, category=?"
            " WHERE id=?",
            (word, legacy, _dump_list(defs), chinese_def, _dump_list(examples), category, word_id)
        )
