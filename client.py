import socket
import json
import os
import readchar

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
ITEMS_CACHE = "items_cache.json"


def send_json(sock, obj):
    data = json.dumps(obj, ensure_ascii=False) + "\n"
    sock.sendall(data.encode("utf-8"))


def recv_json_line(sock):
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            if data:
                break
            return None
        data += chunk
        if b"\n" in chunk:
            break
    line, _, _ = data.partition(b"\n")
    try:
        return json.loads(line.decode("utf-8"))
    except:
        return None


def cache_items(master_items):
    with open(ITEMS_CACHE, "w", encoding="utf-8") as f:
        json.dump(master_items, f, ensure_ascii=False, indent=2)


def load_cached_items():
    if not os.path.exists(ITEMS_CACHE):
        return None
    with open(ITEMS_CACHE, "r", encoding="utf-8") as f:
        return json.load(f)


def pretty_print_items(items):
    for it in items:
        print(f"  id:{it['id']}  {it['name']}  цена:{it['price']}")


def menu_loop(sock, account, master_items):
    options = [
        "Баланс",
        "Инвентарь",
        "Магазин",
        "Купить",
        "Продать",
        "Выйти из аккаунта",
        "Exit",
    ]
    selected = 0

    while True:
        os.system("cls")
        print(f"=== Меню игрока: {account['nickname']} ===")
        for i, item in enumerate(options):
            prefix = "👉 " if i == selected else "   "
            print(prefix + item)

        key = readchar.readkey()

        # Обработка стрелок
        if key in ('\x1b[A', readchar.key.UP):
            selected = (selected - 1) % len(options)
        elif key in ('\x1b[B', readchar.key.DOWN):
            selected = (selected + 1) % len(options)

        elif key == readchar.key.ENTER:
            choice = options[selected]
            if choice == "Баланс":
                send_json(sock, {"action": "whoami"})
                resp = recv_json_line(sock)
                if resp and resp.get("status") == "ok":
                    account = resp["account"]
                    print("Ваши кредиты:", account["credits"])
                input("\nНажмите Enter...")
            elif choice == "Инвентарь":
                print("Ваши предметы (id):", account.get("items", []))
                if account.get("items"):
                    my = [it for it in master_items if it["id"] in account["items"]]
                    pretty_print_items(my)
                input("\nНажмите Enter...")
            elif choice == "Магазин":
                print("Все доступные предметы:")
                pretty_print_items(master_items)
                input("\nНажмите Enter...")
            elif choice == "Купить":
                item_id = input("Введите id предмета для покупки: ")
                if item_id.isdigit():
                    item_id = int(item_id)
                    send_json(sock, {"action": "buy", "item_id": item_id})
                    resp = recv_json_line(sock)
                    if resp and resp.get("status") == "ok":
                        account = resp["account"]
                        print("Куплено:", resp.get("bought", {}).get("name"))
                        print("Кредитов осталось:", account["credits"])
                    else:
                        print("Ошибка:", resp.get("error"))
                input("\nНажмите Enter...")
            elif choice == "Продать":
                item_id = input("Введите id предмета для продажи: ")
                if item_id.isdigit():
                    item_id = int(item_id)
                    send_json(sock, {"action": "sell", "item_id": item_id})
                    resp = recv_json_line(sock)
                    if resp and resp.get("status") == "ok":
                        account = resp["account"]
                        print("Продано:", resp.get("sold", {}).get("name"))
                        print("Кредитов теперь:", account["credits"])
                    else:
                        print("Ошибка:", resp.get("error"))
                input("\nНажмите Enter...")
            elif choice == "Выйти из аккаунта":
                send_json(sock, {"action": "logout"})
                _ = recv_json_line(sock)
                print("Вы вышли из аккаунта.")
                input("\nНажмите Enter...")
                return None, None
            elif choice == "Exit":
                print("Выход из клиента...")
                sock.close()
                exit(0)


def main():
    host = SERVER_HOST
    port = SERVER_PORT
    print("=== Игровой клиент ===")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print("Не удалось подключиться к серверу:", e)
        return

    nickname = None
    account = None
    master_items = load_cached_items()

    while True:
        if not nickname:
            n = input("Введите никнейм для входа (или 'выход'): ").strip()
            if n.lower() in ("выход", "quit", "exit"):
                print("Выход из клиента...")
                sock.close()
                return
            nickname = n
            send_json(sock, {"action": "login", "nickname": nickname})
            resp = recv_json_line(sock)
            if resp is None:
                print("Сервер отключился")
                return
            if resp.get("status") != "ok":
                print("Ошибка входа:", resp.get("error"))
                nickname = None
                continue
            account = resp["account"]
            master_items = resp["items_master"]
            print("Вы вошли как:", account["nickname"])
            print("Бонус при входе:", resp.get("login_bonus", 0), "кредитов")
            cache_items(master_items)
            input("\nНажмите Enter для перехода в меню...")
        else:
            account, master_items = menu_loop(sock, account, master_items)
            if account is None:
                sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect((host, port))
                except Exception as e:
                    print("Не удалось переподключиться к серверу:", e)
                    return
                nickname = None
                continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nКлиент завершён.")
