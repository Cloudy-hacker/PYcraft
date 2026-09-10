# -*- coding: utf-8 -*-
"""
Клиентская сеть: строчный протокол.
ВАЖНО: сокет в БЛОКИРУЮЩЕМ режиме, иначе makefile отравляется таймаутом.
"""
import socket, threading, json, logging
from constants import SERVER_PORT, DISCOVERY_PORT

logger = logging.getLogger(__name__)

def encode_message(data):
    return json.dumps(data, ensure_ascii=False).encode('utf-8') + b"\n"

def decode_message(line):
    return json.loads(line.decode('utf-8'))

class NetworkClient:
    def __init__(self):
        self.socket = None
        self.reader = None
        self.connected = False
        self.player_id = None
        self.incoming = []
        self.lock = threading.Lock()
        self.running = False
        self.recv_thread = None

    def connect(self, ip, port=SERVER_PORT):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((ip, port))
            self.socket.settimeout(None)   # блокирующий режим: ридер живёт вечно
            self.reader = self.socket.makefile('rb')
            self.connected = True
            self.running = True
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
            return True
        except Exception as e:
            logger.error("Ошибка подключения: {}".format(e))
            self.connected = False
            return False

    def _recv_loop(self):
        while self.running:
            try:
                line = self.reader.readline()
            except Exception:
                break   # сокет закрыли мы сами (esc/выход) — тихо выходим
            if not line:
                logger.warning("Сервер закрыл соединение")
                break
            line = line.strip()
            if not line:
                continue
            try:
                data = decode_message(line)
            except Exception as e:
                logger.error("Ошибка разбора пакета: {}".format(e))
                continue
            with self.lock:
                self.incoming.append(data)
        self.connected = False

    def send(self, data):
        if self.connected and self.socket is not None:
            try:
                self.socket.sendall(encode_message(data))
            except Exception as e:
                logger.error("Отправка не удалась: {}".format(e))
                self.connected = False

    def get_messages(self):
        with self.lock:
            msgs = self.incoming[:]
            self.incoming.clear()
        return msgs

    def disconnect(self):
        self.running = False
        self.connected = False
        if self.reader is not None:
            try:
                self.reader.close()
            except Exception:
                pass
            self.reader = None
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

def discover_servers(timeout=2.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    sock.bind(('', 0))
    servers = []
    try:
        sock.sendto(b"DISCOVER", ('255.255.255.255', DISCOVERY_PORT))
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data.startswith(b"BARBERRY:"):
                    servers.append({"ip": addr[0], "info": data.decode('utf-8')[9:]})
            except socket.timeout:
                break
    except Exception:
        pass
    finally:
        sock.close()
    return servers
