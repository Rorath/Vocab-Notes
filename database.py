import sqlite3

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
                english_def TEXT NOT NULL,
                chinese_def TEXT,
                sentence TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration: add category column if an older DB is missing it
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(words)")]
        if "category" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN category TEXT")

# Map sort keys -> SQL ORDER BY clauses (whitelist, so it's injection-safe)
SORT_OPTIONS = {
    "recent": "created_at DESC",
    "oldest": "created_at ASC",
    "az": "word COLLATE NOCASE ASC",
    "za": "word COLLATE NOCASE DESC",
}

def add_word(word, english_def, chinese_def="", sentence="", category=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO words (word, english_def, chinese_def, sentence, category) VALUES (?, ?, ?, ?, ?)",
            (word, english_def, chinese_def, sentence, category)
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

def update_word(word_id, word, english_def, chinese_def, sentence, category=""):
    with get_conn() as conn:
        conn.execute(
            "UPDATE words SET word=?, english_def=?, chinese_def=?, sentence=?, category=? WHERE id=?",
            (word, english_def, chinese_def, sentence, category, word_id)
        )
