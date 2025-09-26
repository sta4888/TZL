import os

import readchar

from cli_cach_manager import CacheManager
from cli_network import NetworkClient


class Menu:
    """Базовое меню, управляющее выбором стрелками."""

    def __init__(self, title, options):
        self.title = title
        self.options = options
        self.selected = 0

    def display(self, account):
        os.system("cls")
        print(f"=== {self.title}: {account['nickname']} ===")
        for i, item in enumerate(self.options):
            prefix = "👉 " if i == self.selected else "   "
            print(prefix + item)

    def run(self, account):
        raise NotImplementedError


class MainMenu(Menu):
    """Главное меню игрока."""

    def __init__(self, network: NetworkClient, cache: CacheManager):
        super().__init__("Меню игрока", [
            "Баланс",
            "Инвентарь",
            "Магазин",
            "Купить",
            "Продать",
            "Выйти из аккаунта",
            "Exit",
        ])
        self.network = network
        self.cache = cache
        self.master_items = []
        self.account = None

    def set_account(self, account, master_items):
        self.account = account
        self.master_items = master_items

    def pretty_print_items(self, items):
        for it in items:
            print(f"  id:{it['id']}  {it['name']}  цена:{it['price']}")

    def handle_choice(self, choice):
        if choice == "Баланс":
            self.network.send({"action": "whoami"})
            resp = self.network.recv()
            if resp and resp.get("status") == "ok":
                self.account = resp["account"]
                print("Ваши кредиты:", self.account["credits"])
            input("\nНажмите Enter...")

        elif choice == "Инвентарь":
            print("Ваши предметы:", self.account.get("items", []))
            if self.account.get("items"):
                owned = [it for it in self.master_items if it["id"] in self.account["items"]]
                self.pretty_print_items(owned)
            input("\nНажмите Enter...")

        elif choice == "Магазин":
            print("Все предметы:")
            self.pretty_print_items(self.master_items)
            input("\nНажмите Enter...")

        elif choice == "Купить":
            item_id = input("Введите id предмета для покупки: ")
            if item_id.isdigit():
                self.network.send({"action": "buy", "item_id": int(item_id)})
                resp = self.network.recv()
                if resp and resp.get("status") == "ok":
                    self.account = resp["account"]
                    print("Куплено:", resp["bought"]["name"])
                    print("Остаток кредитов:", self.account["credits"])
                else:
                    print("Ошибка:", resp.get("error"))
            input("\nНажмите Enter...")

        elif choice == "Продать":
            item_id = input("Введите id предмета для продажи: ")
            if item_id.isdigit():
                self.network.send({"action": "sell", "item_id": int(item_id)})
                resp = self.network.recv()
                if resp and resp.get("status") == "ok":
                    self.account = resp["account"]
                    print("Продано:", resp["sold"]["name"])
                    print("Кредитов теперь:", self.account["credits"])
                else:
                    print("Ошибка:", resp.get("error"))
            input("\nНажмите Enter...")

        elif choice == "Выйти из аккаунта":
            self.network.send({"action": "logout"})
            self.network.recv()
            print("Вы вышли из аккаунта.")
            input("\nНажмите Enter...")
            return "logout"

        elif choice == "Exit":
            print("Выход из клиента...")
            self.network.disconnect()
            exit(0)

    def run(self, account):
        self.account = account
        while True:
            self.display(self.account)
            key = readchar.readkey()
            if key in ('\x1b[A', readchar.key.UP):
                self.selected = (self.selected - 1) % len(self.options)
            elif key in ('\x1b[B', readchar.key.DOWN):
                self.selected = (self.selected + 1) % len(self.options)
            elif key == readchar.key.ENTER:
                choice = self.options[self.selected]
                result = self.handle_choice(choice)
                if result == "logout":
                    return None
