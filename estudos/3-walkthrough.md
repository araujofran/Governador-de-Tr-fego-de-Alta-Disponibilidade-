# Walkthrough: Arquitetura Python First → Banco de Dados → LLM Last

Transformação completa do sistema para o pipeline de 13 camadas modularizado e resiliente, com foco na economia de tokens de entrada, prevenção de Rate Limit (HTTP 429), idempotência e 100% de aderência ao Contrato de Auditoria do Banco Daycoval.

---

## 🛠️ O Que Foi Criado e Atualizado

### 1. Novos Módulos Criados (Fase 1 - Python First)
* [`evidence_engine.py`](file:///c:/Users/fferr/Desktop/projetoRATE/evidence_engine.py): Extração determinística de CPFs, RGs, cartões, telefones, CEPs, protocolos, valores monetários, datas, SLAs, transferências, palavras de fricção e termos regulatórios com rastreabilidade por linha e `speaker`.
* [`data_quality.py`](file:///c:/Users/fferr/Desktop/projetoRATE/data_quality.py): Validador de integridade das transcrições com cálculo do `data_quality_score` (0-100) e alertas (`EMPTY_TRANSCRIPTION`, `LOW_TEXT_QUANTITY`, `SPEAKER_SEPARATION_LOW_CONFIDENCE`, `POSSIBLE_TRUNCATED_AUDIO`).
* [`context_builder.py`](file:///c:/Users/fferr/Desktop/projetoRATE/context_builder.py): Compressão orientada a evidências (*Evidence-Based Context Reduction*), preservando trechos e turnos literais importantes sem resumo destrutivo.
* [`job_queue_db.py`](file:///c:/Users/fferr/Desktop/projetoRATE/job_queue_db.py): Fila de jobs persistente no SQLite com idempotência via hash SHA-256 e checkpoint de reinício.
* [`validator_post_llm.py`](file:///c:/Users/fferr/Desktop/projetoRATE/validator_post_llm.py): Validação pós-LLM para verificação cruzada de Pydantic schemas, regras de contrato e integridade das justificativas.

### 2. Módulos Core Atualizados
* [`database.py`](file:///c:/Users/fferr/Desktop/projetoRATE/database.py): Schema SQLite expandido para 10+ tabelas relacionais (`atendimentos`, `transcricoes`, `evidencias`, `data_quality`, `llm_jobs`, `llm_resultados`, etc.) com preserção da retrocompatibilidade 100%.
* [`preprocessor.py`](file:///c:/Users/fferr/Desktop/projetoRATE/preprocessor.py): Normalização avançada com indexação de linhas e separação preliminar de turnos (`CLIENTE` / `ATENDENTE`).
* [`rate_limiter.py`](file:///c:/Users/fferr/Desktop/projetoRATE/rate_limiter.py): Margem de segurança adaptativa `SAFE_TPM_PERCENTAGE = 0.80` (utilizando no máximo 80% da quota TPM para evitar erros 429).
* [`queue_manager.py`](file:///c:/Users/fferr/Desktop/projetoRATE/queue_manager.py): Encadeamento completo das 13 camadas no lote.
* [`main.py`](file:///c:/Users/fferr/Desktop/projetoRATE/main.py): Orquestração em duas etapas limpas: Fase Python (Ingestão/DB) e Fase LLM Worker.

---

## 🧪 Validação dos Testes Automatizados (16/16 Passed)

```bash
pytest -v
```

**Resultados do Pytest:**
- `test_evidence_engine.py`: PASSED (Extração de CPF, Protocolos, Valores e Fricção)
- `test_data_quality.py`: PASSED (Scoring de integridade e detecção de áudio truncado)
- `test_context_builder.py`: PASSED (Preservação de evidências e redução de contexto)
- `test_job_queue_db.py`: PASSED (Ciclo de vida de jobs, idempotência e checkpoint)
- `test_post_llm_validator.py`: PASSED (Validação de contrato e Pydantic schema)
- `test_database.py`: PASSED (Persistência e integridade relacional SQLite)
- `test_multi_provider.py`: PASSED (Failover Multi-Provider Groq/Gemini/OpenRouter)
- `test_preprocessor.py`: PASSED (Mascaramento de PII)
- `test_rate_limiter.py`: PASSED (Pre-flight check e sincronização de headers HTTP)
- `test_retry_manager.py`: PASSED (Exponential Backoff + Full Jitter)
- `test_tokenizer.py`: PASSED (Contagem de tokens e chunking inteligente)

---

## 🚀 Como Executar o Processamento Completo

### Processamento Real de 309 Transcrições:
```bash
python main.py --provider multi_real --tasks 309
```

### Visualizar o SaaS Web Dashboard:
```bash
python main.py --provider multi_mock --tasks 0
```
*(O dashboard estará disponível na URL exibida no terminal, ex: `http://127.0.0.1:8000`)*
