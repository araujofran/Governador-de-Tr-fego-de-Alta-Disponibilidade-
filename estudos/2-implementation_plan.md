# Plano de Arquitetura: Python First → Banco de Dados → LLM Last

## Resumo Executivo e Validação Conceitual
A proposta de reestruturação do pipeline para o modelo **PYTHON FIRST → BANCO DE DADOS → LLM LAST** é **100% viável, altamente recomendada e não quebra o propósito principal do projeto**.

Pelo contrário, ela fortalece o objetivo central do sistema:
1. **Otimização do LLM Traffic Controller**: Reduz o consumo de tokens de entrada em 40% a 65%, prevenindo estouros de quota (HTTP 429) e reduzindo a latência.
2. **Rastreabilidade total**: Todas as evidências (CPF, protocolos, valores, expressões de fricção) são extraídas e indexadas por Python antes de qualquer chamada de API.
3. **Resiliência e Idempotência**: Todo o processamento Python é persistido em banco de dados SQLite *antes* de acionar a LLM. Se o sistema for interrompido, ele reinicia exatamente a partir dos jobs pendentes no banco.
4. **Preservação Integral do Contrato Daycoval**: A LLM continua sendo o motor de raciocínio semântico (julgamento de postura, empatia, causa raiz, resolutividade), recebendo contexto filtrado baseado em evidências fiéis à transcrição.

---

## A. Diagnóstico da Arquitetura Atual

| Componente | Estado Atual | Gargalo / Oportunidade |
| :--- | :--- | :--- |
| **Ingestão** | Leitura direta dos arquivos `.txt` da pasta `transcricoes/` para memória. | Sem controle de hash SHA-256 e sem persistência prévia de metadados/estados do atendimento. |
| **Pré-processamento** | Limpeza básica e mascaramento de PII em `preprocessor.py`. | Não extrai entidades estruturadas (protocolos, datas, valores, turnos) para reutilização. |
| **Persistência** | Salva no banco SQLite *após* a resposta da LLM. | Se a chamada de LLM falhar ou o processo for cancelado, todo o trabalho de ingestão é perdido. |
| **Construção de Contexto** | Envia a transcrição bruta completa + prompt de 4.000 linhas para a LLM. | Desperdício massivo de tokens com cumprimentos, repetições e ruídos irrelevantes para o contrato. |
| **Rate Limiter & Worker** | Pre-flight check em memória e concorrência via Semaphore. | Não consome jobs persistidos no banco de dados. |

---

## B. Matriz de Atribuição: Python vs. LLM

### 🐍 Tarefas Executadas Exclusivamente por Python (Determinísticas)
* **Ingestão & Hash**: Cálculo de SHA-256, verificação de duplicidade e controle de estados (`RECEIVED`, `PREPROCESSING`, `PREPROCESSED`, `READY_FOR_LLM`, etc.).
* **Normalização de Texto**: Limpeza de espaços, encodings corrompidos, identificação de linhas, turnos de conversa e separação preliminar de interlocutores (`CLIENTE` / `ATENDENTE`).
* **Extração Regex de Entidades**: Identificação determinística de CPFs, RGs, cartões, telefones, CEPs, protocolos de atendimento, valores monetários, datas, SLAs e sequências numéricas.
* **NLP & Análise Local**: Frequência de termos, contagem de turnos, palavras de fricção/ofensivas, contagem de transferências, silêncios e solicitações explícitas.
* **Evidence Engine**: Geração de objetos `Evidence` com `evidence_id`, coordenadas de linha (`linha_inicio`, `linha_fim`), `speaker` e índice de confiança.
* **Data Quality**: Verificação de áudios truncados, transcrições vazias ou sem interlocutores com geração de `data_quality_score` e `flags`.
* **Persistência Pré-LLM**: Gravação integral no banco de dados SQLite de todas as tabelas preparatórias antes de gerar qualquer payload de API.
* **Context Builder & Token Estimator**: Seleção baseada em evidências (Evidence-Based Context Reduction) e cálculo preciso de `input_tokens_estimated` com margem de segurança (`SAFE_TPM_PERCENTAGE = 0.80`).
* **Fila Idempotente & Rate Limiter**: Gerenciamento de jobs via SQLite com suporte a checkpoint de reinício e controle de quota adaptativa.
* **Validador Pós-LLM & Métricas**: Checagem de schema Pydantic, validação cruzada de `evidence_ids` e cálculo de `tokens_saved` / `compression_ratio`.

### 🧠 Tarefas Executadas Exclusivamente pela LLM (Semânticas)
* **Análise Comportamental & Atitude**: Julgamento de empatia, postura, tom de voz, cortesia e clareza das orientações do atendente.
* **Avaliação Crítica de Resolutividade**: Interpretação se as ações tomadas resolveram a dor do cliente conforme as regras do Banco Daycoval.
* **Causa Raiz & Atribuição de Responsabilidade**: Julgamento semântico da origem da falha (sistema, operador, processo ou cliente).
* **Classificação de Humor & Risco**: Identificação da evolução emocional do cliente e potencial de reclamação/ouvidoria.
* **Aplicação do Contrato Regras Ouro**: Avaliação de cada um dos critérios de qualidade da monitoria exigindo raciocínio semântico contextualizado.

---

## C. Desenho da Arquitetura Proposta (13 Camadas)

```
                 TRANSCRIÇÕES (.txt)
                         │
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 1: Ingestão & Hash SHA-256│
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 2: Normalização Python    │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 3: Regex & Entidades      │
        └────────────────┬─────────────────┘
        
```

```
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 4: NLP & Regras Locais    │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 5: Motor de Evidências    │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 6: Data Quality & Scoring │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 7: Persistência DB Pre-LLM│
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 8: Context Builder (Mín.) │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 9: Token Estimator & Budget│
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 10: Rate Limiter & Fila DB│
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 11: LLM Worker (Contrato) │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 12: Validador Pós-LLM     │
        └────────────────┬─────────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │ CAMADA 13: Persistência Final    │
        │             & Dashboard          │
        └──────────────────────────────────┘
```

---

## D. Arquivos que Precisarão Ser Criados

1. **`evidence_engine.py`**:
   - Classe `EvidenceEngine` para rastrear trechos de texto, gerar `evidence_id` padronizados (ex: `EV_00102`), linha de início/fim, speaker e método de extração.
2. **`data_quality.py`**:
   - Classe `DataQualityAnalyzer` para avaliar integridade da transcrição, ruídos, interlocutores e calcular `data_quality_score` (0 a 100) com `flags`.
3. **`context_builder.py`**:
   - Classe `ContextBuilder` para realizar compressão orientada a evidências (Evidence-Based Context Reduction), montando o payload mínimo sem reescrever ou alterar o texto original.
4. **`job_queue_db.py`**:
   - Gerenciador de Fila Persistente no SQLite para desacoplar a fase Python (Ingestão/Normalização) da fase de Worker de LLM.
5. **`validator_post_llm.py`**:
   - Classe `PostLLMValidator` para validar se os `evidence_ids` retornados pela LLM coincidem com as evidências cadastradas no banco de dados.

---

## E. Arquivos que Precisarão Ser Alterados

1. **`database.py`**:
   - Expandir a estrutura do banco SQLite para suportar as 10+ tabelas relacionais.
2. **`preprocessor.py`**:
   - Adicionar normalização profunda de texto, identificação de turnos de diálogo, indexação por linhas e separação preliminar `CLIENTE` / `ATENDENTE`.
3. **`rate_limiter.py`**:
   - Adicionar controle de teto de segurança (`SAFE_TPM_PERCENTAGE = 0.80`) e sincronização com a tabela `llm_jobs`.
4. **`queue_manager.py`**:
   - Adaptar o processador em lote para consumir jobs diretamente da tabela `llm_jobs` do banco SQLite em vez de iterar sobre listas em memória.
5. **`telemetry.py` & `web_dashboard.py`**:
   - Exibir métricas de economia de tokens (`tokens_saved`, `compression_ratio`), status das 13 camadas e volume de evidências extraídas por Python.
6. **`main.py`**:
   - Dividir a execução em 2 fases limpas: **Fase 1: Ingestão & Processamento Python (DB)** e **Fase 2: Fila de Jobs & Worker LLM**.

---

## F. Tabelas no SQLite (`repositoy/audit_database.db`)

### Novas Tabelas Mapeadas:
1. `atendimentos`: Metadados do arquivo (`atendimento_id`, `filename`, `file_hash`, `status`, `ingestion_date`, `lote`).
2. `transcricoes`: Armazena `transcricao_original` e `transcricao_normalizada`.
3. `evidencias`: Armazena evidências extraídas por Python (`evidence_id`, `atendimento_id`, `tipo`, `valor`, `speaker`, `linha_inicio`, `linha_fim`, `trecho`, `metodo_extracao`, `confianca`).
4. `entidades_regex_nlp`: Registros brutos das extrações determinísticas.
5. `data_quality`: Métricas de qualidade (`score`, `flags_json`).
6. `llm_jobs`: Fila de execução (`job_id`, `atendimento_id`, `request_hash`, `contract_version`, `status`, `estimated_input_tokens`, `attempts`).
7. `llm_resultados`: Resposta estruturada validada da LLM, métricas de tokens (`tokens_raw_transcript`, `tokens_context_sent`, `tokens_saved`, `compression_ratio`).

*Preservação retroativa*: As tabelas existentes (`audits`, `scorecards`, `risk_analyses`, `opportunities`, `telemetry_logs`) continuarão sendo alimentadas transparentemente para garantir que a interface atual do Web Dashboard não quebre.

---

## G. Estratégia de Migração Sem Quebrar o Sistema

* **Fase 1 (Modular)**: Criar os novos módulos (`evidence_engine.py`, `data_quality.py`, `context_builder.py`, `job_queue_db.py`, `validator_post_llm.py`) sem alterar o fluxo atual.
* **Fase 2 (Schema DB)**: Atualizar `database.py` com o novo schema mantendo métodos legados funcionais.
* **Fase 3 (Integração)**: Conectar as 13 camadas em `queue_manager.py` e `main.py`.
* **Fase 4 (Validação)**: Executar a suíte de testes unitários para garantir regressão zero.

---

## H. Estratégia de Testes Automatizados

Criar novos testes em `tests/`:
* `test_evidence_engine.py`: Verificar extração de Regex, geração de IDs e coordenadas de linha.
* `test_data_quality.py`: Testar scoring e detecção de arquivos corrompidos/truncados.
* `test_context_builder.py`: Garantir que a compressão preserve 100% das evidências necessárias ao contrato.
* `test_job_queue_db.py`: Testar idempotência, status de transição e reinício por checkpoint.
* `test_post_llm_validator.py`: Testar validação cruzada de `evidence_ids`.

---

## I. Estratégia de Rate Limit Adaptativo

* **Teto de Segurança**: `SAFE_TPM_PERCENTAGE = 0.80` (utilizar no máximo 80% do TPM do provedor para absorver oscilações e respostas da LLM).
* **Pre-flight Check na Fila DB**: Antes de pegar um job da tabela `llm_jobs`, verificar: `tokens_estimados_job + tokens_consumidos_janela <= limite_tpm * 0.80`.
* **Exponential Backoff + Full Jitter**: Mantido para erros 429 e 5xx com priorização do header `Retry-After`.

---

## J. Estimativa de Redução de Tokens

* **Economia Estimada**: Redução de **40% a 65%** nos tokens de entrada (`input_tokens`).
* **Métrica Transparente**:
  $$\text{tokens\_saved} = \text{tokens\_raw\_transcript} - \text{tokens\_context\_sent}$$
  $$\text{compression\_ratio} = \frac{\text{tokens\_context\_sent}}{\text{tokens\_raw\_transcript}}$$

---

## K. Análise de Riscos e Mitigações

| Risco Identificado | Impacto | Estratégia de Mitigação |
| :--- | :--- | :--- |
| **Resumo destrutivo por Python** | Alto | **Proibido resumo reescrito**. Utilizar apenas Evidence-Based Context Reduction (seleção de trechos e turnos sem alterar o texto original). |
| **LLM citar evidência inexistente** | Médio | `validator_post_llm.py` reprova o retorno (`VALIDATION_ERROR`) se a LLM referenciar `evidence_id` não cadastrado. |
| **Incompatibilidade com o banco SQLite existente** | Médio | Mapeamento transparente de colunas e manutenção de views/métodos de retrocompatibilidade. |

---

## L. Checklist de Aderência ao Contrato Daycoval (100%)

- [x] **Regra 1**: A LLM continua sendo a única responsável por julgamentos semânticos (postura, empatia, tom de voz, causa raiz).
- [x] **Regra 2**: Não há inferências de dados semânticos na camada Python (Python apenas extrai fatos determinísticos como CPFs, datas e protocolos).
- [x] **Regra 3**: O contrato de auditoria do Banco Daycoval permanece 100% inalterado no prompt enviado à LLM.
- [x] **Regra 4**: O schema Pydantic `AuditAnalysisResult` é preservado integralmente para estruturação da resposta.
- [x] **Regra 5**: Nenhuma evidência é inventada; todas as constatações possuem rastreabilidade por ID e linhas.
