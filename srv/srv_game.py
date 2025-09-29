import random

from srv.srv_db import DB
from srv.srv_items_repository import ItemRepository


class GameService:
    def __init__(self, db: DB, items_repo: ItemRepository, cfg: dict):
        self.db = db
        self.items = items_repo
        self.cfg = cfg

    def login(self, nickname: str):
        if not nickname:
            raise ValueError("no_nickname")
        self.db.create_account_if_missing(nickname, 0)
        minb = int(self.cfg.get("login_credit_min", 0))
        maxb = int(self.cfg.get("login_credit_max", 0))
        bonus = random.randint(minb, maxb) if maxb >= minb else 0
        if bonus:
            self.db.add_credits(nickname, bonus)
        acc = self.db.get_account(nickname)
        return {"account": acc, "items_master": self.items.list_all(), "login_bonus": bonus}

    def whoami(self, nickname: str):
        acc = self.db.get_account(nickname)
        return acc

    def buy(self, nickname: str, item_id: int):
        if not nickname:
            return {"error": "not_logged_in"}
        item = self.items.get(item_id)
        if not item:
            return {"error": "item_not_found"}
        acc = self.db.get_account(nickname)
        if item_id in acc["items"]:
            return {"error": "already_owned"}
        if acc["credits"] < item["price"]:
            return {"error": "not_enough_credits"}
        self.db.add_item(nickname, item_id)
        self.db.add_credits(nickname, -item["price"])
        acc = self.db.get_account(nickname)
        return {"account": acc, "bought": item}

    def sell(self, nickname: str, item_id: int):
        if not nickname:
            return {"error": "not_logged_in"}
        item = self.items.get(item_id)
        if not item:
            return {"error": "item_not_found"}
        acc = self.db.get_account(nickname)
        if item_id not in acc["items"]:
            return {"error": "not_owned"}
        sale_price = int(item["price"] * 0.5)
        self.db.remove_item(nickname, item_id)
        self.db.add_credits(nickname, sale_price)
        acc = self.db.get_account(nickname)
        return {"account": acc, "sold": item, "received": sale_price}

