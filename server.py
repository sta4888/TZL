import socket
import threading
import json
import sqlite3
import os
import random
import traceback

CONFIG_FILE = "server_config.json"
ITEMS_FILE = "items.json"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_items():
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


class DB:
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

    def create_account(self, nickname, credits):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO accounts (nickname, credits) VALUES (?, ?)", (nickname, credits))
        conn.commit()
        conn.close()

    def add_credits(self, nickname, amount):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET credits = credits + ? WHERE nickname = ?", (amount, nickname))
        conn.commit()
        conn.close()

    def set_credits(self, nickname, credits):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET credits = ? WHERE nickname = ?", (credits, nickname))
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


def send_json(conn, obj):
    data = json.dumps(obj, ensure_ascii=False) + "\n"
    conn.sendall(data.encode("utf-8"))

def recv_json_line(conn):
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            if data:
                break
            return None
        data += chunk
        if b"\n" in chunk:
            break
    line, _, rest = data.partition(b"\n")
    try:
        return json.loads(line.decode("utf-8"))
    except Exception:
        return None

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr, db, items, cfg):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.db = db
        self.items = items
        self.cfg = cfg
        self.nickname = None

    def run(self):
        try:
            while True:
                msg = recv_json_line(self.conn)
                if msg is None:
                    break
                action = msg.get("action")
                if action == "login":
                    self.handle_login(msg)
                elif action == "logout":
                    self.handle_logout(msg)
                    break
                elif action == "buy":
                    self.handle_buy(msg)
                elif action == "sell":
                    self.handle_sell(msg)
                elif action == "whoami":
                    self.handle_whoami(msg)
                else:
                    send_json(self.conn, {"status": "error", "error": "unknown_action"})
        except Exception as e:
            print("Exception handling client:", e)
            traceback.print_exc()
        finally:
            try:
                self.conn.close()
            except:
                pass
            print("Connection closed", self.addr)

    def handle_login(self, msg):
        nickname = msg.get("nickname")
        if not nickname:
            send_json(self.conn, {"status": "error", "error": "no_nickname"})
            return
        acc = self.db.get_account(nickname)
        if acc is None:
            credits = 0
            self.db.create_account(nickname, credits)
            acc = self.db.get_account(nickname)
        bonus = random.randint(self.cfg["login_credit_min"], self.cfg["login_credit_max"])
        self.db.add_credits(nickname, bonus)
        acc = self.db.get_account(nickname)
        self.nickname = nickname
        send_json(self.conn, {
            "status": "ok",
            "action": "login_result",
            "account": acc,
            "items_master": self.items,
            "login_bonus": bonus
        })
        print("User logged in:", nickname, "bonus", bonus)

    def handle_logout(self, msg):
        send_json(self.conn, {"status": "ok", "action": "logout"})
        self.nickname = None

    def handle_whoami(self, msg):
        if not self.nickname:
            send_json(self.conn, {"status": "error", "error": "not_logged_in"})
            return
        acc = self.db.get_account(self.nickname)
        send_json(self.conn, {"status": "ok", "account": acc})

    def handle_buy(self, msg):
        if not self.nickname:
            send_json(self.conn, {"status": "error", "error": "not_logged_in"})
            return
        item_id = msg.get("item_id")
        if item_id is None:
            send_json(self.conn, {"status": "error", "error": "no_item_id"})
            return
        item = next((it for it in self.items if it["id"] == item_id), None)
        if not item:
            send_json(self.conn, {"status": "error", "error": "item_not_found"})
            return
        acc = self.db.get_account(self.nickname)
        if item_id in acc["items"]:
            send_json(self.conn, {"status": "error", "error": "already_owned"})
            return
        price = item["price"]
        if acc["credits"] < price:
            send_json(self.conn, {"status": "error", "error": "not_enough_credits"})
            return
        self.db.add_item(self.nickname, item_id)
        self.db.add_credits(self.nickname, -price)
        acc = self.db.get_account(self.nickname)
        send_json(self.conn, {"status": "ok", "action": "buy_result", "account": acc, "bought": item})

    def handle_sell(self, msg):
        if not self.nickname:
            send_json(self.conn, {"status": "error", "error": "not_logged_in"})
            return
        item_id = msg.get("item_id")
        if item_id is None:
            send_json(self.conn, {"status": "error", "error": "no_item_id"})
            return
        item = next((it for it in self.items if it["id"] == item_id), None)
        if not item:
            send_json(self.conn, {"status": "error", "error": "item_not_found"})
            return
        acc = self.db.get_account(self.nickname)
        if item_id not in acc["items"]:
            send_json(self.conn, {"status": "error", "error": "not_owned"})
            return
        sale_price = int(item["price"] * 0.5)
        self.db.remove_item(self.nickname, item_id)
        self.db.add_credits(self.nickname, sale_price)
        acc = self.db.get_account(self.nickname)
        send_json(self.conn, {"status": "ok", "action": "sell_result", "account": acc, "sold": item, "received": sale_price})

def main():
    cfg = load_config()
    items = load_items()
    db = DB(cfg.get("db_file", "game.db"))

    host = cfg.get("host", "0.0.0.0")
    port = cfg.get("port", 5000)
    print("Starting server on", host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    try:
        while True:
            conn, addr = s.accept()
            print("Connection from", addr)
            handler = ClientHandler(conn, addr, db, items, cfg)
            handler.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        s.close()

if __name__ == "__main__":
    main()
