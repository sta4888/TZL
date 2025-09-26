import json
import socket

from cli_setting import SERVER_HOST, SERVER_PORT


class NetworkClient:
    """Класс для работы с сервером (отправка/приём JSON)."""

    def __init__(self, host=SERVER_HOST, port=SERVER_PORT):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, obj: dict):
        data = json.dumps(obj, ensure_ascii=False) + "\n"
        self.sock.sendall(data.encode("utf-8"))

    def recv(self):
        """Получение одного JSON-объекта из сокета."""
        data = b""
        while True:
            chunk = self.sock.recv(4096)
            if not chunk:
                if data:
                    break
                return None
            data += chunk
            if b"\n" in chunk:
                break
        line, _, _ = data.partition(b"\n")
        try:
            return json.loads(line.decode("utf-8"))
        except Exception:
            return None
