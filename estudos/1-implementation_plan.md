# Plano de Implementação: Pipeline de Auditoria de Atendimento & SaaS Dashboard Admin

Este plano une o **Governador de Tráfego de Alta Disponibilidade (Multi-LLM Rate Limiter)** ao fluxo de negócio completo da **Auditoria de Atendimento do Banco Daycoval** (`contratoRegrasOuro/1-promptAnaliseAtendimentos.txt`).

---

## 🏗️ Arquitetura Integrada do Sistema

```
            309 TRANSCRIÇÕES REAIS (transcricoes/*.txt)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  1. PRÉ-PROCESSAMENTO PYTHON                 │
        │     - Limpeza de caracteres corrompidos      │
        │     - Mascaramento Regex de PII (CPF, etc.)  │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  2. TOKENIZER & SMART CHUNKING               │
        │     - Estimação de orçamento de tokens       │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  3. MULTI-PROVIDER RATE LIMITER GOVERNOR     │
        │     - Balanceador: Groq, Gemini & MiniMax    │
        │     - Pre-flight budget check + Header sync  │
        │     - Dynamic failover com zero 429s         │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  4. EXECUÇÃO DA ANÁLISE + PYDANTIC           │
        │     - Prompt Contrato Ouro (Especialista CX) │
        │     - Validação Estrita de JSON Pydantic     │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  5. REPOSITÓRIO BANCO DE DADOS (SQLite)      │
        │     - Persistência relacional em repositoy/  │
        │     - Tabelas: audits, scorecards, risks...  │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  6. INTERFACES DE APRESENTAÇÃO               │
        │     - Terminal Executivo Rich Console        │
        │     - SaaS Admin Web Dashboard (FastAPI)     │
        └──────────────────────────────────────────────┘
```

---

## 📊 Estrutura de Banco de Dados (`repositoy/audit_database.db`)

O banco SQLite será criado dentro da pasta [`repositoy/`](file:///c:/Users/fferr/Desktop/projetoRATE/repositoy) com as seguintes tabelas relacionais normalizadas:

1. **`audits`**: Registro principal de cada áudio/transcrição auditada.
   - `id`, `filename`, `protocol_number`, `operator_name`, `client_name`, `audit_date`, `overall_score`, `call_classification`, `status`.
2. **`scorecards`**: Detalhamento numérico de pontuação.
   - `audit_id`, `cx_score`, `operator_quality_score`, `technical_score`, `behavioral_score`, `resolutivity_score`.
3. **`risk_analyses`**: Identificação de riscos, causa raiz e responsável.
   - `audit_id`, `risk_level`, `identified_risks`, `root_cause`, `problem_owner`, `evidence_quote`.
4. **`opportunities`**: Recomendações de melhoria.
   - `audit_id`, `operator_opportunities`, `operational_opportunities`.
5. **`telemetry_logs`**: Métricas de tráfego LLM.
   - `audit_id`, `provider_used`, `input_tokens`, `output_tokens`, `latency_sec`, `http_status`.

---

## 🎨 Dashboard Web Frontend (Inspirado no Design SaaS Admin)

Criaremos uma aplicação Web moderna em **FastAPI + HTML5 / TailwindCSS / Chart.js** servida localmente em `http://localhost:8000`:

- **Painel Superior (KPI Cards)**: Total de Atendimentos Auditados, Pontuação Média de Qualidade, Taxa de Resolutividade %, Total de Riscos Críticos e Tokens Processados.
- **Gráficos em Tempo Real**:
  - Distribuição de Causa Raiz.
  - Performance do Traffic Controller (Throughput TPM/RPM por Provedor: Groq vs Gemini vs MiniMax).
- **Tabela de Auditoria Interativa**: Lista de transcrições com badges coloridas de nota, cliente, operador e modal interativo para visualizar a auditoria na íntegra.

---

## 📁 Arquivos a Criar e Modificar

#### [NEW] [`preprocessor.py`](file:///c:/Users/fferr/Desktop/projetoRATE/preprocessor.py): Limpeza de texto e mascaramento PII por Regex.
#### [NEW] [`audit_schema.py`](file:///c:/Users/fferr/Desktop/projetoRATE/audit_schema.py): Modelos **Pydantic** do contrato de auditoria do Banco Daycoval.
#### [NEW] [`database.py`](file:///c:/Users/fferr/Desktop/projetoRATE/database.py): Gerenciamento do banco de dados SQLite em `repositoy/audit_database.db`.
#### [NEW] [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py): Aplicação Web FastAPI com o Dashboard SaaS Admin.
#### [MODIFY] [`queue_manager.py`](file:///c:/Users/fferr/Desktop/projetoRATE/queue_manager.py): Integração do fluxo pré-processamento -> análise LLM Pydantic -> salvamento SQLite.
#### [MODIFY] [`main.py`](file:///c:/Users/fferr/Desktop/projetoRATE/main.py): CLI atualizado para rodar a auditoria das transcrições reais de `transcricoes/` e iniciar o servidor do Web Dashboard.

---

## Plano de Verificação

### Testes Automatizados (`pytest`)
- Adicionar `tests/test_preprocessor.py` (validação de mascaramento de CPF/cartão) e `tests/test_database.py` (validação de inserção e consulta relacional).

### Validação da Auditoria Real e Web Dashboard
- Processar as 309 transcrições reais da pasta `transcricoes/`.
- Iniciar o servidor Web e verificar a interface visual em `http://localhost:8000`.
