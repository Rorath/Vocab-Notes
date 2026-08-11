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
                chinese_def TEXT NOT NULL,
                sentence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def add_word(word, english_def, chinese_def, sentence=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO words (word, english_def, chinese_def, sentence) VALUES (?, ?, ?, ?)",
            (word, english_def, chinese_def, sentence)
        )

def get_all_words():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM words ORDER BY created_at DESC").fetchall()

def get_word(word_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()

def delete_word(word_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM words WHERE id = ?", (word_id,))

def update_word(word_id, word, english_def, chinese_def, sentence):
    with get_conn() as conn:
        conn.execute(
            "UPDATE words SET word=?, english_def=?, chinese_def=?, sentence=? WHERE id=?",
            (word, english_def, chinese_def, sentence, word_id)
        )
