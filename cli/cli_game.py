from cli.cli_cach_manager import CacheManager
from cli.cli_menu import MainMenu
from cli.cli_network import NetworkClient


class GameClient:
    def __init__(self):
        self.network = NetworkClient()
        self.cache = CacheManager()
        self.menu = MainMenu(self.network, self.cache)

    def run(self):
        print("=== Игровой клиент ===")
        try:
            self.network.connect()
        except Exception as e:
            print("Ошибка подключения:", e)
            return

        master_items = self.cache.load_items()
        nickname = None
        account = None

        while True:
            if not nickname:
                n = input("Введите никнейм (или 'выход'): ").strip()
                if n.lower() in ("выход", "quit", "exit"):
                    self.network.disconnect()
                    return
                self.network.send({"action": "login", "nickname": n})
                resp = self.network.recv()
                if not resp or resp.get("status") != "ok":
                    print("Ошибка входа:", resp.get("error") if resp else "Нет ответа")
                    continue
                account = resp["account"]
                master_items = resp["items_master"]
                print("Вход выполнен как:", account["nickname"])
                print("Бонус:", resp.get("login_bonus", 0), "кредитов")
                self.cache.save_items(master_items)
                self.menu.set_account(account, master_items)
                nickname = n
                input("\nНажмите Enter для меню...")
            else:
                account = self.menu.run(account)
                if account is None:  # logout
                    self.network.disconnect()
                    self.network.connect()
                    nickname = None
