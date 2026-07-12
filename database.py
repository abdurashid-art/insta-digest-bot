import sqlite3

DB_PATH = "bot_data.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_snapshot (
            username TEXT PRIMARY KEY,
            follower_count INTEGER,
            best_play_count INTEGER,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_subscriber(chat_id):
    conn = _connect()
    conn.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()


def get_subscribers():
    conn = _connect()
    rows = conn.execute("SELECT chat_id FROM subscribers").fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_account_snapshot(username):
    conn = _connect()
    row = conn.execute(
        "SELECT follower_count, best_play_count FROM account_snapshot WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {"follower_count": row[0], "best_play_count": row[1]}


def save_account_snapshot(username, follower_count, best_play_count):
    conn = _connect()
    conn.execute("""
        INSERT INTO account_snapshot (username, follower_count, best_play_count, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(username) DO UPDATE SET
            follower_count = excluded.follower_count,
            best_play_count = excluded.best_play_count,
            updated_at = excluded.updated_at
    """, (username, follower_count, best_play_count))
    conn.commit()
    conn.close()
