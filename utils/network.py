import socket
import random

def parse_target(target):
    """
    Extrai host e porta de uma URL ou IP de forma robusta.
    """
    # Remove o protocolo se existir
    if target.startswith("http://"):
        target = target[7:]
    elif target.startswith("https://"):
        target = target[8:]
    
    # Remove o caminho se existir
    if "/" in target:
        target = target.split("/")[0]
    
    # Define a porta padrão
    port = 80
    host = target
    
    # Verifica se há uma porta explícita
    if ":" in target:
        parts = target.split(":")
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            host = target
            port = 80
            
    return host, port

def get_local_ip():
    """Obtém o IP local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def random_user_agent():
    """Gera um User-Agent aleatório."""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "curl/8.0.1"
    ]
    return random.choice(agents)