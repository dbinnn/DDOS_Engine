# DDoS Engine

Projeto Python que reúne módulos de geração de tráfego de rede, manutenção de conexões TCP e monitoramento HTTP. O código organiza essas tarefas usando threads e programação assíncrona.

## Visão geral

O projeto possui dois pontos de entrada independentes:

- `main.py`: instancia e inicia os módulos de geração de tráfego e conexões.
- `monitor.py`: realiza verificações HTTP periódicas e apresenta um resumo no terminal.

Apesar do nome, a implementação não contém agentes remotos, distribuição de tarefas entre máquinas ou coordenação de uma rede de dispositivos. Trata-se de um programa executado em um único processo, com múltiplas threads e tarefas assíncronas.

## Estrutura do repositório

| Caminho | Responsabilidade |
| --- | --- |
| `main.py` | Orquestra os módulos e mostra uma contagem regressiva no terminal. |
| `monitor.py` | Consulta uma URL, mede o tempo de resposta e contabiliza falhas de conexão. |
| `vectors/volumetric.py` | Implementa os ramos de tráfego HTTP, TCP e UDP. |
| `vectors/exhaustion.py` | Abre conexões TCP e envia dados periodicamente. |
| `vectors/amplification.py` | Contém tarefas UDP rotuladas como NTP, DNS e SSDP, além de um logger compartilhado. |
| `vectors/__init__.py` | Define a pasta como pacote Python; está vazio. |
| `utils/network.py` | Faz o tratamento básico do destino, consulta o IP local e escolhe um User-Agent. |
| `utils/__init__.py` | Define a pasta como pacote Python; está vazio. |
| `README.md` | Documentação do projeto. |

O arquivo recebido também contém diretórios `__pycache__` com bytecode. Eles são artefatos locais do interpretador e não fazem parte do código-fonte necessário para publicação.

## Componentes

### Orquestrador — `main.py`

A função `orchestrate_attack()` cria uma instância de cada módulo principal e inicia três threads marcadas como daemon. O módulo volumétrico é instanciado no modo HTTP; os ramos TCP e UDP existem na classe, mas não são selecionados por esse fluxo.

O terminal mostra o tempo restante, recebe a interrupção por teclado e apresenta mensagens de encerramento. Depois da contagem, há uma espera adicional descrita no código como drenagem de recursos. Essa espera não consulta o estado do servidor nem comprova sua recuperação.

O fluxo não usa `join()` para aguardar as threads e não chama os métodos `stop()` dos três módulos de forma coordenada. Portanto, a mensagem de finalização não garante que as tarefas tenham terminado naquele instante.

### Tráfego volumétrico — `vectors/volumetric.py`

A classe `VolumetricAttacker` possui três ramos:

| Ramo | Comportamento implementado |
| --- | --- |
| HTTP | Cria requisições GET com `urllib.request` e seleciona um User-Agent de uma lista fixa. |
| TCP | Abre uma conexão TCP e envia uma mensagem com formato HTTP. |
| UDP | Envia um datagrama com conteúdo fixo ao destino. |

A execução usa threads e uma flag `active`, alterada por `stop()`. Diversas exceções são ignoradas, e o módulo não registra uma medição confiável de vazão, respostas recebidas ou impacto no destino.

A URL interna é reconstruída como HTTP e utiliza o caminho raiz. O esquema HTTPS e o caminho original informado não são preservados. As respostas de `urlopen()` também não são fechadas explicitamente.

### Conexões persistentes — `vectors/exhaustion.py`

A classe `ExhaustionAttacker` abre conexões TCP em threads separadas e tenta enviar linhas adicionais periodicamente. Há timeout de conexão e um método `stop()` baseado em flag.

Embora o código use o nome Slowloris, a mensagem inicial já inclui o terminador de cabeçalhos HTTP. A implementação não demonstra o comportamento clássico de manter um cabeçalho inicial incompleto, e sua eficácia não foi validada.

As falhas são suprimidas, não existe relatório de conexões efetivamente mantidas e não há tratamento TLS para conexões HTTPS.

### Tarefas UDP — `vectors/amplification.py`

A classe `AmplificationAttacker` cria um event loop próprio com `asyncio` e agenda tarefas rotuladas como NTP, DNS e SSDP. O módulo contém listas fixas de destinos externos e da rede local, construtores de mensagens e contadores em memória de envios por categoria.

**O nome “amplificação” não comprova uma implementação funcional de reflexão contra o destino informado.** O código usa sockets UDP convencionais, sem implementar falsificação do endereço IP de origem. O valor armazenado em `victim_ip` não é utilizado para encaminhar respostas ao alvo, e as respostas recebidas são ignoradas. Os contadores indicam chamadas de envio realizadas, não entrega confirmada ou volume recebido por outra máquina.

O argumento de duração não é aplicado como limite de execução das tarefas desse módulo. Os loops dependem da flag `active`, enquanto o fluxo normal aguarda essas tarefas antes de chamar `stop()`.

O `FastLogger` acumula mensagens e usa um `threading.Lock`. Existe uma possibilidade de deadlock: `log()` pode chamar `flush()` enquanto já mantém esse mesmo lock, e `flush()` tenta adquiri-lo novamente. O flush depende de novas chamadas de log ou de uma chamada explícita; não há uma thread de descarga periódica.

### Monitoramento — `monitor.py`

A função `monitor_site()` consulta uma URL com `requests`, registra o tempo transcorrido e mostra o código HTTP. O relatório final contém:

- Total de requisições contabilizadas.
- Número de falhas de conexão ou timeout.
- Taxa calculada de sucesso.
- Média do tempo das requisições que receberam resposta.

O monitor possui uma pausa entre consultas, mas o intervalo real também inclui o tempo gasto na requisição. A duração total pode ultrapassar o período solicitado devido a uma consulta em andamento e às pausas.

#### Como interpretar as métricas

| Métrica | Interpretação real |
| --- | --- |
| Status `OK` | A resposta teve código HTTP 200. |
| Outros códigos HTTP | São mostrados no terminal, mas não entram no contador de falhas. |
| Falhas | Contabilizam timeouts e erros de conexão tratados. |
| Taxa de sucesso | Usa o total contabilizado menos as falhas; pode incluir respostas HTTP de erro. |
| Latência média | Considera apenas requisições com resposta, inclusive códigos diferentes de 200. |
| Mensagem de indisponibilidade | É uma classificação local baseada na taxa calculada, sem confirmar a situação para outros usuários. |

Outras exceções são exibidas, mas não necessariamente entram no total. A ausência de resposta de uma única máquina também pode decorrer de problemas locais de rede. O monitor não mede disponibilidade global nem prova que o programa causou uma falha.

O arquivo contém uma URL externa como destino padrão. Ela deve ser revisada antes de qualquer uso; omitir o destino não seleciona automaticamente um ambiente local.

### Utilitários — `utils/network.py`

| Função | Responsabilidade e limites |
| --- | --- |
| `parse_target()` | Remove prefixos HTTP/HTTPS e o caminho, separando host e porta de forma simples. Assume porta 80 quando não há porta explícita, inclusive para URLs HTTPS. Não é um parser completo de URLs e não trata IPv6 corretamente. |
| `get_local_ip()` | Consulta o endereço local selecionado pelo sistema para uma rota externa; retorna loopback em caso de erro. Não identifica necessariamente o IP público. |
| `random_user_agent()` | Retorna um item aleatório de uma lista fixa de identificadores de clientes HTTP. |

`get_local_ip()` está definido, mas não é utilizado no fluxo principal examinado.

## Tecnologias e dependências

| Tipo | Componentes |
| --- | --- |
| Linguagem | Python 3. |
| Biblioteca padrão | `socket`, `struct`, `asyncio`, `threading`, `time`, `random`, `sys` e `urllib.request`. |
| Dependência externa identificada | `requests`, utilizada por `monitor.py`. |
| Saída | Mensagens e relatório textual no terminal. |

O pacote não inclui `requirements.txt`, `pyproject.toml`, versões fixadas de dependências ou uma matriz de compatibilidade. Os arquivos de cache indicam passagem por CPython 3.14, mas não estabelecem a versão mínima nem comprovam compatibilidade integral.

## Estado e limitações gerais

- Implementação experimental, sem testes automatizados no pacote recebido.
- Sem interface web, banco de dados ou autenticação.
- Sem coordenação distribuída ou agentes em outras máquinas.
- Sem validação de autorização, lista restrita de destinos ou isolamento de rede incorporado.
- Sem encerramento sincronizado entre os módulos.
- Sem exportação estruturada de resultados em CSV, JSON ou PDF.
- Sem comprovação de amplificação, indisponibilidade ou recuperação do destino.
- Tratamento silencioso de erros em várias rotinas, dificultando o diagnóstico.


