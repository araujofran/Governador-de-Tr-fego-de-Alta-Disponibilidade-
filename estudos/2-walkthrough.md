# Walkthrough - LLM API Traffic Controller (Triplo Provedor)

O sistema **LLM API Traffic Controller** agora conta com arquitetura de **Triplo Provedor com Failover Adaptativo e Leitura Automática de Chaves**, conectando simultaneamente:
1. **GroqCloud** (`groq.txt`) $\rightarrow$ `llama-3.3-70b-versatile` / `llama-3.1-8b-instant`
2. **Google AI Studio** (`Gemini 3.6 Flash.txt`) $\rightarrow$ `gemini-3.6-flash`
3. **OpenRouter** (`MiniMax M3 free.txt`) $\rightarrow$ `minimax/minimax-m3:free`

---

## ⚡ Como Funciona a Integração dos 3 Provedores

```
                 500 TRANSCRIÇÕES
                        │
                        ▼
                ┌──────────────┐
                │ TOKEN COUNTER│
                └──────┬───────┘
                       │
             estima tokens/request
                       │
                       ▼
                ┌──────────────┐
                │    QUEUE     │
                │  1 ... 500   │
                └──────┬───────┘
                       │
                       ▼
          ┌───────────────────────────┐
          │ MULTI-PROVIDER GOVERNOR   │
          │                           │
          │ ├── Groq RateLimiter      │
          │ ├── Gemini RateLimiter    │
          │ └── MiniMax RateLimiter   │
          └────────────┬──────────────┘
                       │
             Qual tem cota imediata?
              /        │        \
          Groq      Gemini    MiniMax
            │          │         │
            ▼          ▼         ▼
          GROQ      GEMINI    OPENROUTER
            │          │         │
            └──────────┴─────────┘
                       │
             lê headers HTTP (x-ratelimit-*)
                       │
                       ▼
         atualiza orçamento do provedor
                       │
                       ▼
             próxima transcrição
```

---

## 📁 Arquivos Adicionados / Atualizados

| Arquivo | Descrição |
| :--- | :--- |
| [`key_loader.py`](file:///c:/Users/fferr/Desktop/projetoRATE/key_loader.py) | **Leitor Automático de Chaves**: Varre a pasta `chavesFree/` e lê as chaves do Groq, Gemini e OpenRouter sem precisar de variáveis de ambiente. |
| [`provider_openrouter.py`](file:///c:/Users/fferr/Desktop/projetoRATE/provider_openrouter.py) | Provedor para o modelo **MiniMax M3 Free** (`minimax/minimax-m3:free`) via OpenRouter API. |
| [`rate_limiter.py`](file:///c:/Users/fferr/Desktop/projetoRATE/rate_limiter.py) | **MultiProviderRateLimiter**: Gerencia múltiplos governors independentes e seleciona o provedor com saldo imediato de cota. |
| [`queue_manager.py`](file:///c:/Users/fferr/Desktop/projetoRATE/queue_manager.py) | Suporte a lote multi-provedor com alternância dinâmica e desvio automático se um provedor estiver pausado. |
| [`telemetry.py`](file:///c:/Users/fferr/Desktop/projetoRATE/telemetry.py) | Dashboard Rich com tabela comparativa de **Quota Headroom Pool** dos 3 provedores lado a lado. |
| [`main.py`](file:///c:/Users/fferr/Desktop/projetoRATE/main.py) | CLI atualizado com opção por padrão `--provider multi_real`. |
| [`tests/test_multi_provider.py`](file:///c:/Users/fferr/Desktop/projetoRATE/tests/test_multi_provider.py) | Testes automatizados para o leitor de chaves e o mecanismo de failover. |

---

## 🧪 Resultados dos Testes Automatizados (`pytest`)

Executamos a suíte inteira de 8 testes automatizados:
```bash
pytest -v
```

```
tests/test_multi_provider.py::test_key_loader_reads_chaves_free PASSED   [ 12%]
tests/test_multi_provider.py::test_multi_provider_limiter_failover PASSED [ 25%]
tests/test_rate_limiter.py::test_rate_limiter_pre_flight_budget PASSED   [ 37%]
tests/test_rate_limiter.py::test_rate_limiter_header_synchronization PASSED [ 50%]
tests/test_retry_manager.py::test_full_jitter_bounds PASSED              [ 62%]
tests/test_retry_manager.py::test_retry_after_header_override PASSED     [ 75%]
tests/test_tokenizer.py::test_tokenizer_count PASSED                     [ 87%]
tests/test_tokenizer.py::test_smart_chunking PASSED                      [100%]
```

---

## 💡 Como Rodar com as 3 Chaves Gratuitas

### Executar com as Chaves Reais (Groq + Gemini + MiniMax)
O comando lê automaticamente os arquivos da pasta `chavesFree/`:

```bash
python main.py --provider multi_real --tasks 500 --concurrency 15
```

### Executar em Modo Simulação (Multi-Mock Benchmark)
```bash
python main.py --provider multi_mock --tasks 500 --concurrency 15
```
