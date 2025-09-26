import socket
import threading
import logging

from srv_cli_handler import ClientHandler
from srv_config import load_config, DEFAULT_ITEMS_FILE
from srv_db import DB
from srv_game import GameService
from srv_items_repository import ItemRepository


def admin_console_loop(items_repo: ItemRepository, shutdown_event: threading.Event):
    """
    Поддерживает простые команды:
      add <name> <price>   - добавить предмет
      remove <id>          - удалить предмет
      list                 - вывести список предметов
      save                 - сохранить в файл
      reload               - перечитать items из файла (перезапишет текущий список)
      exit/shutdown        - завершить сервер
    """
    print("Admin console ready. Команды: add/remove/list/save/reload/shutdown")
    while not shutdown_event.is_set():
        try:
            line = input("admin> ").strip()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].lower()
        try:
            if cmd == "add" and len(parts) >= 3:
                name = " ".join(parts[1:-1])
                price = int(parts[-1])
                new = items_repo.add(name, price)
                items_repo.save()
                print("Added:", new)
            elif cmd == "remove" and len(parts) == 2:
                iid = int(parts[1])
                ok = items_repo.remove(iid)
                items_repo.save()
                print("Removed:" if ok else "Not found")
            elif cmd == "list":
                for it in items_repo.list_all():
                    print(f"{it['id']}: {it['name']} (price={it['price']})")
            elif cmd == "save":
                items_repo.save()
                print("Saved to", items_repo.path)
            elif cmd == "reload":
                items_repo.load()
                print("Reloaded from", items_repo.path)
            elif cmd in ("exit", "shutdown", "quit"):
                print("Shutting down server (admin)...")
                shutdown_event.set()
                break
            else:
                print("Unknown admin command")
        except Exception as e:
            print("Admin command error:", e)


def main():
    cfg = load_config()
    items_file = cfg.get("items_file", DEFAULT_ITEMS_FILE)
    items_repo = ItemRepository(items_file)
    db = DB(cfg.get("db_file", "game.db"))
    service = GameService(db, items_repo, cfg)

    host = cfg.get("host", "0.0.0.0")
    port = int(cfg.get("port", 5000))

    shutdown_event = threading.Event()

    admin_thread = threading.Thread(target=admin_console_loop, args=(items_repo, shutdown_event), daemon=True)
    admin_thread.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(8)
    logging.info("Server listening on %s:%s", host, port)

    try:
        while not shutdown_event.is_set():
            try:
                s.settimeout(1.0)
                conn, addr = s.accept()
            except socket.timeout:
                continue
            except Exception:
                raise
            logging.info("Connection from %s", addr)
            handler = ClientHandler(conn, addr, service)
            handler.start()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt -> shutting down")
    except Exception:
        logging.exception("Server error")
    finally:
        logging.info("Server shutting down...")
        shutdown_event.set()
        s.close()


if __name__ == "__main__":
    main()
