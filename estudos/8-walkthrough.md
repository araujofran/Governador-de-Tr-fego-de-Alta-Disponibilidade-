# Walkthrough — Transposição Visual HospitIQ (Behance) -> AuditAI

Realizamos a transposição completa dos padrões de visualização e UX do case study **HospitIQ AI SaaS CRM** (Behance) para o **AuditAI — Banco Engineer AI**, elevando a experiência executiva **sem alterar ou quebrar qualquer funcionalidade existente**.

---

## 🎨 Principais Inovações Visuais Incorporadas

### 1. Barra de Filtros em Pills Dinâmicos (HospitIQ UI Pattern)
- Adicionada barra de botões com estilo "pill" e contadores visuais sincronizados em tempo real:
  - **✨ Todos (309)**: Exibe a lista completa de atendimentos.
  - **🚨 Risco Crítico / Alto (12)**: Filtra instantaneamente chamadas com alertas críticos.
  - **🏆 Top Performers (245)**: Filtra atendimentos com score CX $\ge 85$.
  - **⚠️ Atenção (52)**: Filtra atendimentos necessitando revisão (score $< 75$).

### 2. Drawer de Inspeção Lateral com 4 Abas Interativas (`#rightDrawer`)
- A gaveta de inspeção profunda foi reorganizada em 4 abas alternáveis de alta velocidade:
  - **Aba 1: 📊 Scorecard 4D & Resumo Executivo**: Barras de progresso Pydantic (CX, Qualidade Operador, Aderência Técnica, Tom Comportamental).
  - **Aba 2: 🎯 Causa Raiz & Evidência**: Bloco em destaque com taxonomia de intenções, responsável e citação literal entre aspas.
  - **Aba 3: 💬 Transcrição Íntegra (1-Click)**: Scroll dedicado com balões coloridos destacando falas de `OPERADOR` (roxo) e `CLIENTE` (azul).
  - **Aba 4: 🛡️ LGPD Presidio Guard**: Relatório detalhado dos dados mascarados pelo engine de segurança da Microsoft (`[CPF_MASCARADO]`, `[TELEFONE_MASCARADO]`, etc.).

---

## 📸 Evidências Visuais e Capturas de Tela

````carousel
![01 - Tela de Login Executiva](/C:/Users/fferr/.gemini/antigravity/brain/67a6f075-10bb-408c-93f5-96f0b240724d/01_login_screen.png)
<!-- slide -->
![02 - Dashboard Executivo com Filter Pills](/C:/Users/fferr/.gemini/antigravity/brain/67a6f075-10bb-408c-93f5-96f0b240724d/02_admin_dashboard.png)
<!-- slide -->
![03 - Drawer de Inspeção HospitIQ com Abas](/C:/Users/fferr/.gemini/antigravity/brain/67a6f075-10bb-408c-93f5-96f0b240724d/03_inspection_modal.png)
<!-- slide -->
![04 - Aba de Transcrição Íntegra](/C:/Users/fferr/.gemini/antigravity/brain/67a6f075-10bb-408c-93f5-96f0b240724d/04_full_transcript.png)
````

---

## 🧪 Suíte de Testes e Versão do Git

- **pytest**: **24/24 testes aprovados** (100% de sucesso).
- **Servidor Ativo**: [http://127.0.0.1:8080](http://127.0.0.1:8080) (AuditAI) e [http://127.0.0.1:9000](http://127.0.0.1:9000) (Hub MANNAGER_FRAN).
- **Commit GitHub**: `15af5fc` sincronizado com sucesso na branch `main` do repositório `araujofran/Governador-de-Tr-fego-de-Alta-Disponibilidade-`.
