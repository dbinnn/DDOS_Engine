import requests
import time
import sys

def monitor_site(url, duration=120):
    """
    Monitora a latência e a disponibilidade do site em tempo real.
    """
    print(f"[*] Iniciando monitoramento de {url} por {duration}s")
    print(f"[*] Verificando status a cada 2 segundos...")
    
    start_time = time.time()
    failures = 0
    total_requests = 0
    latencies = []
    
    while time.time() - start_time < duration:
        try:
            start_req = time.time()
            # Timeout de 5 segundos para simular um usuário real
            response = requests.get(url, timeout=5)
            req_time = time.time() - start_req
            
            total_requests += 1
            latencies.append(req_time)
            
            status = "OK" if response.status_code == 200 else f"HTTP {response.status_code}"
            print(f"[{time.strftime('%H:%M:%S')}] Status: {status} | Latência: {req_time:.2f}s | Código: {response.status_code}")
            
        except requests.exceptions.Timeout:
            total_requests += 1
            failures += 1
            print(f"[{time.strftime('%H:%M:%S')}] TIMEOUT | O site não respondeu em 5s")
        except requests.exceptions.ConnectionError:
            total_requests += 1
            failures += 1
            print(f"[{time.strftime('%H:%M:%S')}] CONEXÃO FALHOU | O site está fora do ar")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ERRO: {e}")
            
        time.sleep(2)
        
    # Relatório final
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    success_rate = ((total_requests - failures) / total_requests) * 100 if total_requests > 0 else 0
    
    print("-" * 50)
    print("[*] RELATÓRIO FINAL")
    print(f"Total de Requests: {total_requests}")
    print(f"Falhas: {failures}")
    print(f"Taxa de Sucesso: {success_rate:.2f}%")
    print(f"Latência Média: {avg_latency:.2f}s")
    if success_rate < 50:
        print("[!] O SITE CAIU DENTRO DO PADRÃO DE ACEITAÇÃO")
    else:
        print("[*] O SITE PERMANECEU OPERACIONAL")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://web.dixiponto.com.br/"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    monitor_site(url, duration)