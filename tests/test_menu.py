import builtins
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock

from cli.cli_menu import MainMenu


@pytest.fixture
def menu():
    network = MagicMock()
    cache = MagicMock()
    m = MainMenu(network, cache)
    m.set_account({"nickname": "test", "credits": 50, "items": [1]}, [{"id": 1, "name": "sword", "price": 100}])
    return m


def test_handle_choice_balance(menu, capsys):
    menu.network.recv.return_value = {"status": "ok", "account": {"nickname": "test", "credits": 150}}
    with patch.object(builtins, "input", lambda _: "\n"):
        menu.handle_choice("Баланс")
    captured = capsys.readouterr()
    assert "Ваши кредиты: 150" in captured.out


def test_handle_choice_inventory(menu, capsys):
    with patch.object(builtins, "input", lambda _: "\n"):
        menu.handle_choice("Инвентарь")
    captured = capsys.readouterr()
    assert "sword" in captured.out


def test_handle_choice_exit(menu, capsys):
    menu.network.disconnect = MagicMock()
    with pytest.raises(SystemExit):
        menu.handle_choice("Exit")
