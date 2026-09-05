# Plano de Implementação — Módulos Zendesk AI & Painéis de Alta Precisão Visual

Este plano detalha como evoluir o **AuditAI — Banco Engineer AI** para incorporar as funcionalidades avançadas de nível enterprise inspiradas no **Zendesk AI / Quality Assurance** e nos gráficos comparativos de alta precisão do mockup visual em anexo, **preservando 100% da estabilidade do backend e da suíte de testes**.

---

## 📸 Análise das Referências Fornecidas

### 1. Funcionalidades Enterprise Zendesk AI Solicitadas:
- **🤖 Copilot & Assistente Proativo de IA**: Assistente proativo no painel de inspeção que gera sugestões automáticas de ação corretiva para o operador com base nas falhas detectadas.
- **🏷️ Triagem Inteligente & Classificação Autônoma**: Classificação automática da intenção do cliente (Cancelamento, Cobrança, Dúvida, Fraude) com roteamento inteligente de severidade.
- **📈 Controle de Qualidade Automático (Auto QA)**: Cálculo contínuo da pontuação de conformidade humana e robótica por amostragem total (309 chamadas).
- **🛡️ Governança & Segurança (Trust Center)**: Mantido através do nosso **Microsoft Presidio Guard** para anonimização LGPD/BACEN de PIIs.

### 2. Recursos Visuais do Mockup (Anexo `media_1788626098398.png`):
- **🌓 Theme Switcher (Modo Escuro / Modo Claro)**: Alternador no cabeçalho superior para alternar visualmente entre *Dark Theme* (`#0B0F17`) e *Light Theme* (`#F8FAFC`).
- **📊 Gráfico de Tendência Comparativo (Smooth Bezier Line Chart)**: Gráfico de evolução temporal comparando o **Período Atual vs Período Anterior** (Evolução das notas CX).
- **⭕ Donut Chart de Anéis Concentricos (Learner / Operator Engagement)**: Gráfico circular de engajamento e risco em formato de múltiplos anéis (Ativos, Em Alerta, Em Risco).
- **⚡ Feed de Atividades Recentes e Alertas Coloridos**: Painel de alertas com bordas indicadoras de severidade.

---

## 📐 Arquitetura da Solução Proposta

```
+-----------------------------------------------------------------------------------+
|              DASHBOARD EXECUTA ZENDESK AI + PATHWAY HIGH-PRECISION UI             |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [Header Sticky] 🛡️ Presidio LGPD  |  🤖 AI Copilot Active  |  [ ☀️ Light / 🌙 Dark ] |
|                                                                                   |
|  [Cards KPI com Indicadores de Tendência Temporal]                               |
|   Total Auditorias (309)  |  Média CX (85.4)  |  Triagem IA (100%)  |  Riscos (12)|
|                                                                                   |
|  [Seção de Gráficos Avançados - Layout 2 Colunas]                                 |
|   ┌─────────────────────────────────────┐  ┌───────────────────────────────────┐ |
|   │ 📈 Tendência Temporal CX (Bezier)   │  │ ⭕ Distribuição de Risco / Anéis  │ |
|   │ (Período Atual vs Período Anterior) │  │ (Conforme, Alerta, Crítico)       │ |
|   └─────────────────────────────────────┘  └───────────────────────────────────┘ |
|                                                                                   |
|  [Drawer de Inspeção com AI Copilot Assistente Proativo]                          |
|   ┌─────────────────────────────────────────────────────────────────────────────┐ |
|   │ 🤖 AI Copilot: "Sugerir treinamento em LGPD para o operador João Silva"     │ |
|   └─────────────────────────────────────────────────────────────────────────────┘ |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## ⚠️ Cuidados com a Estabilidade do Sistema (Zero Breakage)

> [!IMPORTANT]
> **Preservação de Regras de Negócio e Testes**: As atualizações visuais e os novos cálculos de triagem/copiloto serão implementados no [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py) e no [`evidence_engine.py`](file:///c:/Users/fferr/Desktop/projetoRATE/evidence_engine.py). Toda a suíte de 24 testes no `pytest` continuará 100% aprovada.

---

## 🛠️ Detalhamento das Entregas Propostas

### 1. Alternador de Tema Claro / Escuro (Light & Dark Mode Switcher)
#### [MODIFY] [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py)
- Adicionar alternador de tema funcional na barra de cabeçalho (sol e lua).
- Suporte a classes CSS reativas para alteração dinâmica de paleta entre Dark (`bg-slate-950`) e Light (`bg-slate-100`).

### 2. Gráfico de Tendência Comparativo (Período Atual vs Anterior - Smooth Bezier Curves)
#### [MODIFY] [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py)
- Adicionar gráfico de linhas comparativo utilizando **Chart.js** com tensão de curva suave (`cubicInterpolationMode: 'monotone'`), comparando o desempenho histórico da operação.

### 3. Assistente AI Copilot no Drawer de Inspeção
#### [MODIFY] [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py)
- Incluir caixa de assistência proativa do **AI Copilot** no drawer lateral, recomendando ações de feedback, reciclagens ou elogios ao operador com base no score 4D.

### 4. Triagem Inteligente & Badges de Categoria de Atendimento
#### [MODIFY] [`web_dashboard.py`](file:///c:/Users/fferr/Desktop/projetoRATE/web_dashboard.py)
- Exibir a categoria de atendimento (Cobrança, Cancelamento, Suporte Técnico, Informação) com filtros automáticos por intenção.

---

## 🧪 Plano de Verificação

### 1. Suíte de Testes Automatizados
- Executar o `pytest` para confirmar aprovação dos 24/24 testes.

### 2. Simulação e Capturas de Tela via Playwright
- Executar simulação automatizada e gerar capturas de tela demonstrando o modo Claro, modo Escuro, gráfico comparativo de tendência e o assistente AI Copilot.

---

## ❓ Aguardando Sua Aprovação

Por favor, analise a proposta acima. Assim que você aprovar este plano, efetuarei a implementação!
