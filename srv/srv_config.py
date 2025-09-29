import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


CONFIG_FILE = "server_config.json"
DEFAULT_ITEMS_FILE = "items.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"{CONFIG_FILE} not found")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)