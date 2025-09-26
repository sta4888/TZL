import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cli_cach_manager import CacheManager


def test_save_and_load_items(tmp_path):
    filename = tmp_path / "items.json"
    cache = CacheManager(filename)

    items = [{"id": 1, "name": "sword", "price": 100}]
    cache.save_items(items)

    assert os.path.exists(filename)

    loaded = cache.load_items()
    assert loaded == items


def test_load_items_file_not_exists(tmp_path):
    filename = tmp_path / "no_file.json"
    cache = CacheManager(filename)

    assert cache.load_items() is None
