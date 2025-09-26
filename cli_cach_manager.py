import json
import os

from cli_setting import ITEMS_CACHE


class CacheManager:
    """Управляет сохранением и загрузкой предметов в кэше."""

    def __init__(self, filename=ITEMS_CACHE):
        self.filename = filename

    def save_items(self, items):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def load_items(self):
        if not os.path.exists(self.filename):
            return None
        with open(self.filename, "r", encoding="utf-8") as f:
            return json.load(f)