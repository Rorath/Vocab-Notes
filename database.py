import sqlite3
import json
from datetime import date

DB = "vocab.db"

# Familiarity is a per-word score the flashcard trainer nudges up ("I knew it")
# and down ("I don't know"). It's clamped to this range; lower = shows up more.
FAMILIARITY_MIN = -4
FAMILIARITY_MAX = 6

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
        # Migration: spaced-repetition tracking for the flashcard trainer.
        if "familiarity" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN familiarity INTEGER DEFAULT 0")
        if "times_seen" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN times_seen INTEGER DEFAULT 0")
        if "last_seen" not in cols:
            conn.execute("ALTER TABLE words ADD COLUMN last_seen TIMESTAMP")
        # Per-day study tally (for the optional daily goal) and a tiny key/value
        # settings table (currently just holds the goal itself).
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_log (
                day TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

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
        unfamiliar = conn.execute(
            "SELECT COUNT(*) AS n FROM words WHERE COALESCE(familiarity, 0) < 0"
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
        "unfamiliar": unfamiliar,
        "groups": [{"name": r["name"], "count": r["count"]} for r in rows],
    }

def get_unfamiliar_words(sort="recent"):
    """Words the trainer has learned you tend to miss (familiarity below neutral)."""
    order = SORT_OPTIONS.get(sort, SORT_OPTIONS["recent"])
    with get_conn() as conn:
        return conn.execute(
            f"SELECT * FROM words WHERE COALESCE(familiarity, 0) < 0 ORDER BY familiarity ASC, {order}"
        ).fetchall()

def find_word_by_name(word, exclude_id=None):
    """Return an existing row that matches this word (case-insensitive), or None."""
    word = (word or "").strip()
    if not word:
        return None
    query = "SELECT * FROM words WHERE word = ? COLLATE NOCASE"
    params = [word]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()

def get_word(word_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()

def delete_word(word_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM words WHERE id = ?", (word_id,))

def set_words_category(ids, category):
    """Assign the same category/group to a batch of words in one shot."""
    ids = [i for i in (ids or []) if i]
    if not ids:
        return 0
    placeholders = ",".join("?" * len(ids))
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE words SET category = ? WHERE id IN ({placeholders})",
            [category, *ids],
        )
        return cur.rowcount

def update_word(word_id, word, english_defs, chinese_def, examples, category=""):
    defs = [d for d in (english_defs or []) if d]
    legacy = defs[0] if defs else ""
    with get_conn() as conn:
        conn.execute(
            "UPDATE words SET word=?, english_def=?, english_defs=?, chinese_def=?, examples=?, category=?"
            " WHERE id=?",
            (word, legacy, _dump_list(defs), chinese_def, _dump_list(examples), category, word_id)
        )

# ---- Flashcard trainer: familiarity + daily goal ------------------------------

def record_result(word_id, known):
    """Nudge a word's familiarity from a flashcard answer and count the rep.

    Returns the word's new familiarity score, or None if the id is unknown.
    """
    delta = 1 if known else -1
    with get_conn() as conn:
        row = conn.execute(
            "SELECT familiarity FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if row is None:
            return None
        fam = max(FAMILIARITY_MIN, min(FAMILIARITY_MAX, (row["familiarity"] or 0) + delta))
        conn.execute(
            "UPDATE words SET familiarity = ?, times_seen = COALESCE(times_seen, 0) + 1,"
            " last_seen = CURRENT_TIMESTAMP WHERE id = ?",
            (fam, word_id),
        )
        conn.execute(
            "INSERT INTO daily_log (day, count) VALUES (?, 1)"
            " ON CONFLICT(day) DO UPDATE SET count = count + 1",
            (date.today().isoformat(),),
        )
    return fam

def get_today_count():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count FROM daily_log WHERE day = ?", (date.today().isoformat(),)
        ).fetchone()
    return row["count"] if row else 0

def get_daily_goal():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'daily_goal'"
        ).fetchone()
    try:
        return int(row["value"]) if row and row["value"] else 0
    except (ValueError, TypeError):
        return 0

def set_daily_goal(n):
    try:
        n = max(0, int(n))
    except (ValueError, TypeError):
        n = 0
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('daily_goal', ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(n),),
        )
    return n
