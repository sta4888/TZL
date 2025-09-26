from dotenv import load_dotenv
import os

load_dotenv()

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 5000))
ITEMS_CACHE = os.getenv("ITEMS_CACHE", "items_cache.json")
