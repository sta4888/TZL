import sys, os

from cli import cli_network

sys.path.append(os.path.dirname(os.path.dirname(__file__)))






def test_network_client_connect_and_disconnect(monkeypatch):
    nc = cli_network.NetworkClient(host="127.0.0.1", port=12345)

    class DummySocket:
        def __init__(self):
            self.connected = False
            self.closed = False
            self.sent_data = b""

        def connect(self, addr):
            self.connected = True
            self.addr = addr

        def close(self):
            self.closed = True

        def sendall(self, data):
            self.sent_data += data

        def recv(self, bufsize):
            return b'{"status": "ok"}\n'

    monkeypatch.setattr("socket.socket", lambda *a, **kw: DummySocket())
    nc.connect()
    assert nc.sock.connected is True

    nc.send({"status": "ok"})
    assert b'"status": "ok"' in nc.sock.sent_data

    data = nc.recv()
    assert data["status"] == "ok"

    nc.disconnect()
    assert nc.sock is None
