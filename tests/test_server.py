import json
import os
import socket
import tempfile
import threading
import time

import pytest

from srv import server
from srv.srv_items_repository import ItemRepository
from srv.srv_db import DB
from srv.srv_game import GameService


@pytest.fixture
def test_env(tmp_path):
    """Создаёт временные файлы конфигурации и items.json"""
    items_file = tmp_path / "items.json"
    db_file = tmp_path / "game.db"
    config_file = tmp_path / "server_config.json"

    items = [
        {"id": 1, "name": "Sword", "price": 50},
        {"id": 2, "name": "Shield", "price": 30},
    ]
    with open(tmp_path / "items.json", "w", encoding="utf-8") as f:
        json.dump(items, f)

    items_file.write_text(json.dumps(items, ensure_ascii=False))

    cfg = {
        "host": "127.0.0.1",
        "port": 5555,
        "items_file": str(items_file),
        "db_file": str(db_file),
        "login_credit_min": 50,
        "login_credit_max": 50,
    }
    config_file.write_text(json.dumps(cfg, ensure_ascii=False))

    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield cfg
    os.chdir(cwd)


def run_server_in_thread(cfg, shutdown_event):
    items_repo = ItemRepository(cfg["items_file"])
    db = DB(cfg["db_file"])
    service = GameService(db, items_repo, cfg)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((cfg["host"], cfg["port"]))
    s.listen(8)

    def loop():
        while not shutdown_event.is_set():
            try:
                s.settimeout(0.5)
                conn, addr = s.accept()
            except socket.timeout:
                continue
            handler = server.ClientHandler(conn, addr, service)
            handler.start()
        s.close()

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t


def send_recv(sock, obj):
    sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
    data = sock.recv(4096).decode("utf-8")
    return json.loads(data.strip())


def test_login_whoami_buy_sell_logout(test_env):
    shutdown_event = threading.Event()
    run_server_in_thread(test_env, shutdown_event)
    time.sleep(0.3)

    sock = socket.create_connection((test_env["host"], test_env["port"]))


    resp = send_recv(sock, {"action": "login", "nickname": "player1"})
    assert resp["status"] == "ok"
    account = resp["account"]
    assert account["nickname"] == "player1"
    assert resp["login_bonus"] == 50

    resp = send_recv(sock, {"action": "whoami"})
    assert resp["status"] == "ok"
    assert resp["account"]["nickname"] == "player1"

    resp = send_recv(sock, {"action": "buy", "item_id": 1})
    assert resp["status"] == "ok"
    assert resp["bought"]["name"] == "Sword"

    resp = send_recv(sock, {"action": "sell", "item_id": 1})
    assert resp["status"] == "ok"
    assert resp["sold"]["name"] == "Sword"
    assert "received" in resp

    resp = send_recv(sock, {"action": "logout"})
    assert resp["status"] == "ok"

    sock.close()
    shutdown_event.set()
    time.sleep(0.2)
