import pytest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from unittest.mock import patch, MagicMock

from cli_game import GameClient


@pytest.fixture
def game_client():
    gc = GameClient()
    gc.network = MagicMock()
    gc.cache = MagicMock()
    gc.menu = MagicMock()
    return gc


def test_run_connection_error(game_client, capsys):
    game_client.network.connect.side_effect = Exception("fail connect")
    game_client.run()
    captured = capsys.readouterr()
    assert "Ошибка подключения" in captured.out


def test_successful_login_and_logout(game_client):
    game_client.network.connect.return_value = None
    game_client.network.recv.side_effect = [
        {"status": "ok", "account": {"nickname": "nick"}, "items_master": [], "login_bonus": 10},
    ]

    with patch("builtins.input", side_effect=["nick", "\n", "выход"]), patch("builtins.print"):
        game_client.menu.run.side_effect = [None]
        game_client.run()

    game_client.network.send.assert_called_with({"action": "login", "nickname": "nick"})

