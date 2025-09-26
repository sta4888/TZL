import json
import logging
import socket
import threading

from srv_game import GameService


def send_json(conn: socket.socket, obj: dict):
    try:
        data = json.dumps(obj, ensure_ascii=False) + "\n"
        conn.sendall(data.encode("utf-8"))
    except Exception as e:
        logging.debug("send_json failed: %s", e)


class ClientHandler(threading.Thread):
    def __init__(self, conn: socket.socket, addr, service: GameService):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.service = service
        self.nickname = None
        self.conn_file = conn.makefile("r", encoding="utf-8")

    def recv_json_line(self):
        try:
            line = self.conn_file.readline()
            if not line:
                return None
            try:
                return json.loads(line.strip())
            except Exception:
                return None
        except Exception:
            return None

    def run(self):
        logging.info("Client connected: %s", self.addr)
        try:
            while True:
                msg = self.recv_json_line()
                if msg is None:
                    break
                action = msg.get("action")
                if action == "login":
                    nickname = msg.get("nickname")
                    if not nickname:
                        send_json(self.conn, {"status": "error", "error": "no_nickname"})
                        continue
                    result = self.service.login(nickname)
                    self.nickname = nickname
                    send_json(self.conn, {"status": "ok", "action": "login_result",
                                          "account": result["account"],
                                          "items_master": result["items_master"],
                                          "login_bonus": result["login_bonus"]})
                    logging.info("User logged in: %s bonus=%s", nickname, result["login_bonus"])
                elif action == "logout":
                    send_json(self.conn, {"status": "ok", "action": "logout"})
                    self.nickname = None
                    break
                elif action == "whoami":
                    if not self.nickname:
                        send_json(self.conn, {"status": "error", "error": "not_logged_in"})
                        continue
                    acc = self.service.whoami(self.nickname)
                    send_json(self.conn, {"status": "ok", "account": acc})
                elif action == "buy":
                    item_id = msg.get("item_id")
                    if item_id is None:
                        send_json(self.conn, {"status": "error", "error": "no_item_id"})
                        continue
                    res = self.service.buy(self.nickname, int(item_id))
                    if "error" in res:
                        send_json(self.conn, {"status": "error", "error": res["error"]})
                    else:
                        send_json(self.conn, {"status": "ok", "action": "buy_result", "account": res["account"],
                                              "bought": res["bought"]})
                elif action == "sell":
                    item_id = msg.get("item_id")
                    if item_id is None:
                        send_json(self.conn, {"status": "error", "error": "no_item_id"})
                        continue
                    res = self.service.sell(self.nickname, int(item_id))
                    if "error" in res:
                        send_json(self.conn, {"status": "error", "error": res["error"]})
                    else:
                        send_json(self.conn, {"status": "ok", "action": "sell_result", "account": res["account"],
                                              "sold": res["sold"], "received": res["received"]})
                else:
                    send_json(self.conn, {"status": "error", "error": "unknown_action"})
        except Exception:
            logging.exception("Exception handling client %s", self.addr)
        finally:
            try:
                self.conn_file.close()
            except Exception:
                pass
            try:
                self.conn.close()
            except Exception:
                pass
            logging.info("Connection closed: %s", self.addr)