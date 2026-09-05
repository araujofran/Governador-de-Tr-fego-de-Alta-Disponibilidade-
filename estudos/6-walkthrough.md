# Plano de Implementação: Hub de Gerenciamento de Aplicações (MANNAGER_FRAN)

Criar uma aplicação centralizada de controle de processos e portas (**MANNAGER_FRAN**) no diretório `C:\Users\fferr\Desktop\MANNAGER_FRAN`. 

Este Hub funcionará como um **Painel de Controle Executivo & Process Supervisor** para todos os seus sistemas locais (começando pelo `projetoRATE` na porta `8080`). Ele permitirá visualizar o status de cada sistema em tempo real, ligar/desligar processos com 1 clique, ver logs ao vivo, cadastrar novas aplicações em portas customizadas e manter as aplicações sempre ativas (com auto-restart e inicialização automática junto com o Windows).

---

## User Review Required

> [!IMPORTANT]
> **Como funcionará o Hub MANNAGER_FRAN:**
> 1. **Porta Padrão do Hub**: O `MANNAGER_FRAN` rodará na porta **9000** (`http://127.0.0.1:9000`).
> 2. **Autonomia de Processos**: Você **NÃO precisará abrir o VSCode** para manter os sistemas no ar. O Hub gerencia os subprocessos de forma independente em segundo plano (*daemon*).
> 3. **Recuperação Automática (Auto-Heal)**: Se um sistema cair ou sofrer crash, o Hub detecta em segundos e permite religar manualmente via botão **ON** ou religar automaticamente se configurado com `autostart: true`.
> 4. **Inicialização no Windows**: Um script `install_startup.vbs` será instalado na pasta de inicialização do Windows (`shell:startup`) para que o Hub suba sozinho quando o computador for ligado.

---

## Open Questions

> [!NOTE]
> Tem alguma preferência de porta para o próprio Hub `MANNAGER_FRAN` (sugestão: `9000`)? 
> Se desejar outra porta (ex: `7000` ou `9999`), favor informar ao aprovar o plano.

---

## Proposed Changes

### Componente: Hub Core & Process Engine (`MANNAGER_FRAN`)

Diretório de destino: `C:\Users\fferr\Desktop\MANNAGER_FRAN`

---

#### [NEW] [config.json](file:///C:/Users/fferr/Desktop/MANNAGER_FRAN/config.json)
- Arquivo JSON persistente contendo a lista de sistemas cadastrados, comandos de inicialização, diretórios, portas, status de autostart e histórico de PIDs.
- Inicializado com o `projetoRATE`:
  - **Nome**: `Governador de Tráfego - Banco Engineer AI`
  - **Porta**: `8080`
  - **Diretório**: `C:\Users\fferr\Desktop\projetoRATE`
  - **Comando**: `python main.py --web-only --port 8080`
  - **URL**: `http://127.0.0.1:8080`

#### [NEW] [process_manager.py](file:///C:/Users/fferr/Desktop/MANNAGER_FRAN/process_manager.py)
- Módulo Python encarregado de:
  - Verificar a saúde da porta via socket TCP (`127.0.0.1:port`).
  - Iniciar processos em segundo plano (`subprocess.Popen`) isolados do VSCode.
  - Interromper processos limpos enviando sinal de encerramento (`SIGTERM` / `psutil.kill`).
  - Capturar `stdout` e `stderr` em tempo real para os arquivos de log de cada aplicação.
  - Monitorar consumo de CPU/Memória por PID.

#### [NEW] [hub_server.py](file:///C:/Users/fferr/Desktop/MANNAGER_FRAN/hub_server.py)
- Servidor FastAPI / Uvicorn leve rodando na porta **9000**.
- Endpoints REST API:
  - `GET /api/services`: Retorna a lista de sistemas cadastrados com status (ONLINE/OFFLINE), latência, uso de CPU e memória.
  - `POST /api/services`: Cadastra um novo sistema dinamico.
  - `POST /api/services/{id}/start`: Inicia a aplicação.
  - `POST /api/services/{id}/stop`: Para a aplicação.
  - `POST /api/services/{id}/restart`: Reinicia a aplicação.
  - `GET /api/services/{id}/logs`: Retorna as últimas linhas do log em tempo real.
  - `DELETE /api/services/{id}`: Remove um sistema do Hub.

#### [NEW] [index.html](file:///C:/Users/fferr/Desktop/MANNAGER_FRAN/templates/index.html)
- Interface gráfica executiva SaaS com suporte a Tema Escuro / Claro.
- Cards modernos para cada aplicação com:
  - Badge pulsante (🟢 **ONLINE** / 🔴 **OFFLINE** / 🟡 **INICIANDO**).
  - Medidores de Uptime, Consumo de RAM e CPU.
  - Botão de Ação Direta: 🟢 **LIGAR (ON)** | 🔴 **DESLIGAR (OFF)** | 🔄 **REINICIAR**.
  - Link direto **ABRIR SISTEMA** (`http://127.0.0.1:8080`).
  - Modal de **LOGS AO VIVO** para ver o terminal da aplicação em tempo real.
  - Formulário modal **+ CADASTRAR NOVO SISTEMA** para registrar novos projetos.

#### [NEW] [install_startup.vbs](file:///C:/Users/fferr/Desktop/MANNAGER_FRAN/install_startup.vbs)
- Script VBScript para colocar o `MANNAGER_FRAN` na Inicialização Automática do Windows (pasta `shell:startup`).
- Executa o servidor em modo invisível (sem janela de terminal aberta), garantindo que o Hub fique 100% no ar após reiniciar o Windows.

---

## Verification Plan

### Automated Tests
- Executar testes automatizados com `pytest` ou scripts de validação HTTP:
  1. Testar checagem de sockets e status ONLINE/OFFLINE.
  2. Testar ciclo de vida: `start` -> validar porta 8080 aberta -> `stop` -> validar porta 8080 fechada.
  3. Validar leitura de logs e inclusão de novas URLs.

### Manual Verification
- Acessar `http://127.0.0.1:9000` no navegador.
- Clicar em **LIGAR (ON)** no card do `projetoRATE` e confirmar que `http://127.0.0.1:8080` abre com a página de login do AuditAI.
- Clicar em **DESLIGAR (OFF)** e verificar que o status muda para 🔴 **OFFLINE**.
- Clicar em **+ Cadastrar Novo Sistema** e adicionar um projeto de teste.
