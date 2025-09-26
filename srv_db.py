import sqlite3


class DB:
    """Небольшой wrapper для sqlite операций (каждый вызов — новое соединение)."""

    def __init__(self, db_file):
        self.db_file = db_file
        self._ensure_schema()

    def _conn(self):
        return sqlite3.connect(self.db_file, check_same_thread=False)

    def _ensure_schema(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                nickname TEXT PRIMARY KEY,
                credits INTEGER NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS account_items (
                nickname TEXT,
                item_id INTEGER,
                PRIMARY KEY (nickname, item_id),
                FOREIGN KEY (nickname) REFERENCES accounts(nickname)
            );
        """)
        conn.commit()
        conn.close()

    def get_account(self, nickname):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT credits FROM accounts WHERE nickname = ?", (nickname,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        credits = row[0]
        cur.execute("SELECT item_id FROM account_items WHERE nickname = ?", (nickname,))
        items = [r[0] for r in cur.fetchall()]
        conn.close()
        return {"nickname": nickname, "credits": credits, "items": items}

    def create_account_if_missing(self, nickname, credits=0):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO accounts (nickname, credits) VALUES (?, ?)", (nickname, credits))
        conn.commit()
        conn.close()

    def set_credits(self, nickname, credits):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET credits = ? WHERE nickname = ?", (credits, nickname))
        conn.commit()
        conn.close()

    def add_credits(self, nickname, amount):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET credits = credits + ? WHERE nickname = ?", (amount, nickname))
        conn.commit()
        conn.close()

    def add_item(self, nickname, item_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO account_items (nickname, item_id) VALUES (?, ?)", (nickname, item_id))
        conn.commit()
        conn.close()

    def remove_item(self, nickname, item_id):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM account_items WHERE nickname = ? AND item_id = ?", (nickname, item_id))
        conn.commit()
        conn.close()

