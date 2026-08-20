import json
import socket
import threading
import time


LAN_PORT = 27711
DISCOVERY_PORT = 27712
PROTOCOL_VERSION = 1


def _send_json_line(sock, payload):
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    sock.sendall(data)


class _JsonLineReader:
    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def read(self):
        while b"\n" not in self.buffer:
            chunk = self.sock.recv(65536)
            if not chunk:
                return None
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b"\n", 1)
        if not line:
            return {}
        return json.loads(line.decode("utf-8"))


def local_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


class LanServer:
    """Small authoritative LAN server."""

    def __init__(self, player_count, settings=None, port=LAN_PORT):
        self.player_count = max(1, min(4, int(player_count or 1)))
        self.settings = dict(settings or {})
        self.port = int(port)
        self.host_ip = local_lan_ip()
        self.running = False
        self._server_sock = None
        self._clients = {}
        self._inputs = {}
        self._lock = threading.Lock()
        self.last_error = None

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run_tcp, daemon=True).start()
        threading.Thread(target=self._run_discovery, daemon=True).start()

    def stop(self):
        self.running = False
        try:
            if self._server_sock:
                self._server_sock.close()
        except Exception:
            pass
        with self._lock:
            clients = list(self._clients.values())
            self._clients.clear()
        for client in clients:
            try:
                client["sock"].close()
            except Exception:
                pass

    def remote_inputs_for_slot(self, slot):
        with self._lock:
            return dict(self._inputs.get(int(slot), {}))

    def connected_player_count(self):
        with self._lock:
            return 1 + len(self._clients)

    def broadcast_snapshot(self, snapshot):
        if not self.running:
            return
        packet = {"type": "snapshot", "snapshot": snapshot}
        stale = []
        with self._lock:
            clients = list(self._clients.items())
        for slot, client in clients:
            try:
                _send_json_line(client["sock"], packet)
            except Exception:
                stale.append(slot)
        if stale:
            with self._lock:
                for slot in stale:
                    old = self._clients.pop(slot, None)
                    self._inputs.pop(slot, None)
                    if old:
                        try:
                            old["sock"].close()
                        except Exception:
                            pass

    def _run_tcp(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("", self.port))
            srv.listen(4)
            srv.settimeout(0.5)
            self._server_sock = srv
        except Exception as exc:
            self.last_error = str(exc)
            self.running = False
            return

        while self.running:
            try:
                sock, addr = srv.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            threading.Thread(target=self._handle_client, args=(sock, addr), daemon=True).start()

    def _handle_client(self, sock, addr):
        slot = None
        try:
            reader = _JsonLineReader(sock)
            hello = reader.read() or {}
            if hello.get("type") != "join" or int(hello.get("version", 0)) != PROTOCOL_VERSION:
                _send_json_line(sock, {"type": "error", "message": "Falsche LAN-Version."})
                sock.close()
                return

            with self._lock:
                used = set(self._clients.keys())
                slot = None
                for candidate in range(1, self.player_count):
                    if candidate not in used:
                        slot = candidate
                        break
                if slot is None:
                    slot = self.player_count
                if slot >= self.player_count:
                    _send_json_line(sock, {"type": "error", "message": "Lobby ist voll."})
                    sock.close()
                    return
                self._clients[slot] = {"sock": sock, "addr": addr, "name": hello.get("name") or f"LAN {slot + 1}"}
                self._inputs[slot] = {}

            _send_json_line(sock, {
                "type": "welcome",
                "slot": slot,
                "player_count": self.player_count,
                "settings": self.settings,
            })

            while self.running:
                msg = reader.read()
                if msg is None:
                    break
                if msg.get("type") == "input":
                    with self._lock:
                        self._inputs[slot] = dict(msg.get("keys") or {})
        except Exception as exc:
            self.last_error = str(exc)
        finally:
            with self._lock:
                if slot is not None:
                    self._clients.pop(slot, None)
                    self._inputs.pop(slot, None)
            try:
                sock.close()
            except Exception:
                pass

    def _run_discovery(self):
        try:
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp.bind(("", DISCOVERY_PORT))
            udp.settimeout(0.5)
        except Exception as exc:
            self.last_error = str(exc)
            return

        while self.running:
            try:
                data, addr = udp.recvfrom(2048)
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            if msg.get("type") != "discover" or int(msg.get("version", 0)) != PROTOCOL_VERSION:
                continue
            with self._lock:
                taken = 1 + len(self._clients)
            reply = {
                "type": "host",
                "version": PROTOCOL_VERSION,
                "name": "Wauz Kart LAN",
                "ip": self.host_ip,
                "port": self.port,
                "players": taken,
                "max_players": self.player_count,
                "settings": self.settings,
            }
            try:
                udp.sendto(json.dumps(reply).encode("utf-8"), addr)
            except Exception:
                pass
        try:
            udp.close()
        except Exception:
            pass


class LanClient:
    def __init__(self, host, port=LAN_PORT, name="Spieler"):
        self.host = str(host).strip()
        self.port = int(port)
        self.name = name or "Spieler"
        self.slot = 0
        self.player_count = 1
        self.settings = {}
        self.running = False
        self.last_error = None
        self._sock = None
        self._reader = None
        self._lock = threading.Lock()
        self._latest_snapshot = None

    def connect(self, timeout=5.0):
        sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self._sock = sock
        self._reader = _JsonLineReader(sock)
        _send_json_line(sock, {"type": "join", "version": PROTOCOL_VERSION, "name": self.name})
        welcome = self._reader.read() or {}
        if welcome.get("type") == "error":
            raise RuntimeError(welcome.get("message") or "LAN-Verbindung abgelehnt.")
        if welcome.get("type") != "welcome":
            raise RuntimeError("Keine gueltige LAN-Antwort.")
        self.slot = int(welcome.get("slot", 0))
        self.player_count = int(welcome.get("player_count", 1))
        self.settings = dict(welcome.get("settings") or {})
        self.running = True
        sock.settimeout(0.5)
        threading.Thread(target=self._receive_loop, daemon=True).start()

    def close(self):
        self.running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass

    def send_input(self, keys):
        if not self.running or self._sock is None:
            return
        try:
            _send_json_line(self._sock, {"type": "input", "keys": dict(keys or {})})
        except Exception as exc:
            self.last_error = str(exc)
            self.running = False

    def latest_snapshot(self):
        with self._lock:
            return self._latest_snapshot

    def _receive_loop(self):
        while self.running:
            try:
                msg = self._reader.read()
            except socket.timeout:
                continue
            except Exception as exc:
                self.last_error = str(exc)
                break
            if msg is None:
                break
            if msg.get("type") == "snapshot":
                with self._lock:
                    self._latest_snapshot = msg.get("snapshot")
            elif msg.get("type") == "error":
                self.last_error = msg.get("message") or "LAN-Fehler."
                break
        self.running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass


def discover_hosts(timeout=1.0):
    hosts = []
    seen = set()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.2)
        payload = json.dumps({"type": "discover", "version": PROTOCOL_VERSION}).encode("utf-8")
        sock.sendto(payload, ("255.255.255.255", DISCOVERY_PORT))
        end = time.time() + float(timeout)
        while time.time() < end:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            try:
                msg = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            if msg.get("type") != "host":
                continue
            key = (msg.get("ip") or addr[0], int(msg.get("port", LAN_PORT)))
            if key in seen:
                continue
            seen.add(key)
            msg["ip"] = key[0]
            msg["port"] = key[1]
            hosts.append(msg)
    finally:
        sock.close()
    return hosts
