# Walkthrough - LLM API Traffic Controller

O sistema **LLM API Traffic Controller** foi criado com sucesso para governar o tráfego de requisições enviadas a APIs de LLM (como **Groq** e **Gemini**) garantindo a eliminação de erros **HTTP 429** e otimização de throughput através de **Dynamic Rate Limiting** adaptativo.

---

## 🚀 O Salto Tecnológico: Dynamic Rate Limiting (Item 9)

Em vez de usar uma pausa estática como `time.sleep(2)`, o sistema calcula o orçamento de tokens antes do envio:

$$\text{Consumo Previsto} = \text{Tokens de Entrada (Tokenizer)} + \text{Tokens de Saída Alocados}$$

Se o consumo previsto couber no limite disponível da janela (TPM/RPM), a requisição é liberada imediatamente. Caso contrário, a tarefa aguarda na fila até que a janela de cota resete ou receba confirmação dos cabeçalhos de resposta HTTP do servidor.

---

## 📁 Estrutura de Arquivos Criados

| Arquivo | Descrição |
| :--- | :--- |
| [`tokenizer.py`](file:///c:/Users/fferr/Desktop/projetoRATE/tokenizer.py) | Contagem de tokens via `tiktoken` (ou heurística de backup) e **Chunking Inteligente** para grandes transcrições. |
| [`rate_limiter.py`](file:///c:/Users/fferr/Desktop/projetoRATE/rate_limiter.py) | **DynamicRateLimiter** cobrindo RPM, TPM, RPD, TPD e sincronização adaptativa via cabeçalhos HTTP (`x-ratelimit-*` / `retry-after`). |
| [`concurrency_manager.py`](file:///c:/Users/fferr/Desktop/projetoRATE/concurrency_manager.py) | Gerenciador assíncrono de concorrência com `asyncio.Semaphore` e contador de workers ativos. |
| [`retry_manager.py`](file:///c:/Users/fferr/Desktop/projetoRATE/retry_manager.py) | Tratamento de HTTP 429/5xx com **Exponential Backoff + Full Jitter** e parsing de `Retry-After`. |
| [`base_provider.py`](file:///c:/Users/fferr/Desktop/projetoRATE/base_provider.py) | Interface padrão para provedores de LLM e dataclass de resultado `ProviderResult`. |
| [`provider_groq.py`](file:///c:/Users/fferr/Desktop/projetoRATE/provider_groq.py) | Provedor Groq com suporte a chamadas HTTP reais e modo de simulação (mock) de cabeçalhos. |
| [`provider_gemini.py`](file:///c:/Users/fferr/Desktop/projetoRATE/provider_gemini.py) | Provedor Gemini com suporte a chamadas HTTP reais (`generativelanguage.googleapis.com`) e modo mock. |
| [`queue_manager.py`](file:///c:/Users/fferr/Desktop/projetoRATE/queue_manager.py) | Fila Producer/Consumer assíncrona com pré-processamento de tarefas e chunking automático. |
| [`telemetry.py`](file:///c:/Users/fferr/Desktop/projetoRATE/telemetry.py) | Dashboard de observabilidade em tempo real construído com a biblioteca `rich`. |
| [`main.py`](file:///c:/Users/fferr/Desktop/projetoRATE/main.py) | CLI interativo e runner de benchmark para simulação e execução com APIs reais. |
| [`requirements.txt`](file:///c:/Users/fferr/Desktop/projetoRATE/requirements.txt) | Dependências do projeto (`rich`, `tiktoken`, `httpx`, `pytest`, `pytest-asyncio`). |
| [`tests/`](file:///c:/Users/fferr/Desktop/projetoRATE/tests) | Suíte de testes automatizados (`test_rate_limiter.py`, `test_retry_manager.py`, `test_tokenizer.py`). |

---

## 🧪 Validação e Testes Automatizados

### 1. Execução de Testes de Unidade (`pytest`)
Todos os 6 testes foram executados com sucesso:
- `test_rate_limiter_pre_flight_budget`: Valida reserva pré-flight de orçamento de tokens.
- `test_rate_limiter_header_synchronization`: Valida sincronização instantânea via headers HTTP (`x-ratelimit-*`).
- `test_full_jitter_bounds`: Valida intervalo aleatório do Full Jitter.
- `test_retry_after_header_override`: Valida respeito ao cabeçalho `Retry-After`.
- `test_tokenizer_count`: Valida contagem precisa de tokens.
- `test_smart_chunking`: Valida divisão inteligente de textos longos.

```bash
pytest -v
```

### 2. Execução de Benchmark de Transcrições

Rodamos uma execução com 30 transcrições sintéticas com limite de taxa configurado:

```bash
python main.py --tasks 30 --tpm 100000 --rpm 100 --concurrency 10
```

#### Resultado do Benchmark:
- **Tempo Total de Execução**: 3.83 segundos
- **Transcrições Concluídas**: 30 / 30
- **Total de Tokens Processados**: 18.531 tokens
- **Throughput Médio (TPM)**: 290.329 tokens/min
- **Erros HTTP 429**: **0 (Zero)**

---

## 💡 Como Executar no Seu Computador

### Modo Simulação / Benchmark (500 Transcrições)
```bash
python main.py --tasks 500 --rpm 30 --tpm 8000 --concurrency 10
```

### Modo API Real com a Groq
```bash
python main.py --provider groq_real --tasks 10 --api-key SUAM_CHAVE_GROQ
```

### Modo API Real com o Gemini
```bash
python main.py --provider gemini_real --tasks 10 --api-key SUAM_CHAVE_GEMINI
```
