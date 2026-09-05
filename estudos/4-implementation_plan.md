# Plano de Enriquecimento Arquitetural — AuditAI (Banco Engineer AI)

Este documento detalha o plano de evolução e enriquecimento do **AuditAI — Banco Engineer AI**, incorporando as bibliotecas especializadas para auditoria de transcrições bancárias, mascaramento de dados (LGPD/BACEN), estruturação rígida via LLMs e aprimoramento visual executivo **sem quebrar nenhuma funcionalidade existente**.

---

## 🎯 Visão Geral do Enriquecimento

A proposta é evoluir o motor mantendo **100% de compatibilidade retroativa** com a base de código atual (`database.py`, `web_dashboard.py`, `main.py`, `multi_provider.py`), adicionando camadas modulares de segurança, orquestração e testes de qualidade.

```
+-----------------------------------------------------------------------------------+
|                            FLUXO DE AUDITORIA ENRIQUECIDO                         |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [Transcrição de Áudio de Atendimento Bancário]                                    |
|                         │                                                         |
|                         ▼                                                         |
|  1. 🛡️ SEGURANÇA & PRIVACIDADE (Microsoft Presidio)                               |
|     - Detecção e Anonimização de PII (CPF, Conta, Cartão, Telefone, RG)           |
|                         │                                                         |
|                         ▼                                                         |
|  2. 🧠 ORQUESTRAÇÃO & ESTRUTURAÇÃO (Instructor + LiteLLM)                         |
|     - Roteamento inteligente de provedores (Groq / Gemini / MiniMax)              |
|     - Validação garantida do JSON via Pydantic (Instructor)                        |
|                         │                                                         |
|                         ▼                                                         |
|  3. 📊 MONITORAMENTO & TELEMETRIA (Rich + DataQuality + FinOps)                    |
|     - Cálculo de score 4D (CX, Conformidade, Eficiência, Risco)                   |
|     - Relatório Rich no terminal & banco SQLite (database.py)                     |
|                         │                                                         |
|                         ▼                                                         |
|  4. 🎨 INTERFACE EXECUTIVA (FastAPI + Componentes shadcn/ui & Tremor)              |
|     - REST API completa em FastAPI (`/api/audits`, `/api/operators`, `/docs`)     |
|     - Painel SPA reativo com métricas "Fintech", gráficos e Drawer de Inspeção    |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 🔍 Análise Técnica das Bibliotecas Solicitadas

| Biblioteca | Papel no Projeto AuditAI | Grau de Encaixe | Benefício Prático |
| :--- | :--- | :--- | :--- |
| **Microsoft Presidio** (`presidio-analyzer` / `presidio-anonymizer`) | Anonimização de dados bancários (LGPD) pré-LLM | 🌟 **Essencial** | Garante que CPFs, cartões e contas não sejam vazados para APIs de LLM externas. |
| **Instructor** (`instructor` + `pydantic`) | Garantia de contrato JSON estrito no output da LLM | 🌟 **Essencial** | Força a LLM a responder exatamente no schema Pydantic, eliminando falhas de parsing. |
| **LiteLLM** (`litellm`) | Abstração e fallback universal de modelos LLM | ⚡ **Muito Alto** | Padroniza a chamada de múltiplos provedores (Groq, Gemini, MiniMax, OpenAI) em um único contrato. |
| **Promptfoo** (`promptfoo`) | Testes de regressão e avaliação de Prompts LLM | ⚡ **Muito Alto** | Cria suítes automatizadas de teste para garantir que ajustes no prompt não piorem a auditoria. |
| **Rich** (`rich`) | Relatórios no terminal e telemetria formatada | 🟢 **Já Utilizado** | Continua sendo o motor de terminal para logs coloridos, tabelas executivas e estatísticas. |
| **FastAPI + shadcn/ui & Tremor** | Backend REST reativo e Frontend Executivo Fintech | 🟢 **Já Utilizado & Expansível** | O backend em FastAPI já está pronto (`web_dashboard.py`). Podemos expandir o UI com visuais estilo Tremor/shadcn. |

---

## ⚠️ Cuidados com a Estabilidade do Sistema (Zero Breakage)

> [!IMPORTANT]
> **Garantia de Não-Regressão**: Todas as adições serão feitas como **módulos opcionais/decoradores com fallback**. Se alguma biblioteca externa não estiver instalada ou falhar, o sistema reverte automaticamente para o pipeline nativo atual (`regex_masker`, `validator_post_llm`, `multi_provider`).

---

## 🛠️ Plano de Mudanças Proposto

### Componente 1: Anonimização com Microsoft Presidio (`privacy_guard.py`)
#### [NEW] [`privacy_guard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/privacy_guard.py)
- Módulo isolado de higienização de PII antes do processamento por LLM.
- Suporte a identificadores brasileiros: CPF, RG, cartão de crédito, conta corrente e telefone.
- Integrado de forma transparente ao `preprocessor.py`.

### Componente 2: Orquestração Estruturada com Instructor & LiteLLM (`instructor_provider.py`)
#### [NEW] [`instructor_provider.py`](file:///c:/Users/fferr/Desktop/projetoRATE/instructor_provider.py)
- Wrapper decorador para `base_provider.py` e `multi_provider.py`.
- Utiliza `instructor` para forçar respostas diretamente em instâncias do `AuditResult` Pydantic.

### Componente 3: Suíte de Avaliação de Prompts com Promptfoo (`tests/promptfoo/`)
#### [NEW] [`promptfoo.yaml`](file:///c:/Users/fferr/Desktop/projetoRATE/promptfoo.yaml)
- Configuração de testes de regressão de prompts para auditar a consistência das notas e classificações de risco.

### Componente 4: Refinamento da UI Executiva Estilo Tremor & shadcn/ui (`web_dashboard.py`)
#### [MODIFY] [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py)
- Adição de cartões de métricas estilo Tremor (Progress bars de nota, sparklines de tendência).
- Manutenção da OpenAPI `/docs` em FastAPI para integração simplificada com aplicações React/Next.js caso desejado no futuro.

---

## 🧪 Plano de Verificação

### 1. Testes Automatizados
- Rodar a suíte inteira via `pytest` garantindo 20/20 testes aprovados.
- Criar novos testes unitários em `tests/test_privacy_guard.py` e `tests/test_instructor_provider.py`.

### 2. Validação E2E e Simulação Visual
- Executar o script de simulação via Playwright e gerar screenshots atualizados para verificar se a interface continua 100% funcional.

---

## ❓ Aguardando Aprovação do Usuário

Por favor, revise este plano. Assim que você confirmar a aprovação, iniciarei a implementação incremental sem interromper os serviços ativos.
