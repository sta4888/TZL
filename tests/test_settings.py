import os
import sys, os

from cli import cli_setting

sys.path.append(os.path.dirname(os.path.dirname(__file__)))





def test_default_settings(monkeypatch):
    monkeypatch.delenv("SERVER_HOST", raising=False)
    monkeypatch.delenv("SERVER_PORT", raising=False)
    monkeypatch.delenv("ITEMS_CACHE", raising=False)

    import importlib
    importlib.reload(cli_setting)

    assert cli_setting.SERVER_HOST == "127.0.0.1"
    assert cli_setting.SERVER_PORT == 5000
    assert cli_setting.ITEMS_CACHE == "items_cache.json"


def test_env_settings(monkeypatch):
    monkeypatch.setenv("SERVER_HOST", "192.168.0.10")
    monkeypatch.setenv("SERVER_PORT", "6000")
    monkeypatch.setenv("ITEMS_CACHE", "custom_cache.json")

    import importlib
    importlib.reload(cli_setting)

    assert cli_setting.SERVER_HOST == "192.168.0.10"
    assert cli_setting.SERVER_PORT == 6000
    assert cli_setting.ITEMS_CACHE == "custom_cache.json"
