import json
import os
import threading
from typing import Optional

from srv.srv_config import DEFAULT_ITEMS_FILE


class ItemRepository:
    """
    Хранит master-list предметов в файле JSON и предоставляет методы для управления ими.
    Потокобезопасен.
    """
    def __init__(self, path=DEFAULT_ITEMS_FILE):
        self.path = path
        self.lock = threading.Lock()
        self.items = []
        self.load()

    def load(self):
        with self.lock:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    normalized = []
                    next_id = 1
                    for it in data:
                        if "id" not in it:
                            it["id"] = next_id
                        normalized.append(it)
                        next_id = max(next_id, it["id"] + 1)
                    self.items = normalized
            else:
                self.items = []

    def save(self):
        with self.lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)

    def list_all(self):
        with self.lock:
            return [dict(it) for it in self.items]

    def get(self, item_id: int) -> Optional[dict]:
        with self.lock:
            for it in self.items:
                if it["id"] == item_id:
                    return dict(it)
            return None

    def add(self, name: str, price: int) -> dict:
        with self.lock:
            max_id = max((it.get("id", 0) for it in self.items), default=0)
            new = {"id": max_id + 1, "name": name, "price": int(price)}
            self.items.append(new)
            return dict(new)

    def remove(self, item_id: int) -> bool:
        with self.lock:
            for i, it in enumerate(self.items):
                if it["id"] == item_id:
                    del self.items[i]
                    return True
            return False

    def update(self, item_id: int, **kwargs) -> Optional[dict]:
        with self.lock:
            for it in self.items:
                if it["id"] == item_id:
                    it.update(kwargs)
                    return dict(it)
            return None
