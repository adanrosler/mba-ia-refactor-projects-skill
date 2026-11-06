# Skill `refactor-arch`: auditoria e refatoração arquitetural automatizada

Entrega do desafio **"Criação de Skills — Refatoração Arquitetural Automatizada"** (MBA Engenharia de
Software com IA, Full Cycle). O enunciado oficial está em [`docs/enunciado-desafio.md`](docs/enunciado-desafio.md).

A skill `refactor-arch` (Claude Code) faz três coisas, em fases sequenciais:
1. analisa um projeto backend;
2. gera um relatório de auditoria com os anti-patterns encontrados, classificados por severidade e com arquivo e linha, e **pausa pedindo confirmação**;
3. refatora o projeto para o padrão **MVC** e valida que a aplicação continua de pé e que os endpoints respondem como antes.

A mesma skill, sem nenhuma alteração, foi executada nos 3 projetos: dois em Python/Flask e um em Node.js/Express.

| Projeto | Stack | Findings | Smoke test após refatoração | Endpoints sensíveis (fail-closed) |
|---|---|---|---|---|
| `code-smells-project/` | Python 3.13 + Flask 3.1 + sqlite3 | 18 (6 C / 3 H / 5 M / 4 L) | **65/65 ✓** | 10 |
| `ecommerce-api-legacy/` | Node.js 20 + Express 4 + sqlite3 | 16 (4 C / 4 H / 5 M / 3 L) | **14/14 ✓** | 2 |
| `task-manager-api/` | Python 3.13 + Flask 3.0 + SQLAlchemy | 18 (4 C / 4 H / 6 M / 4 L) | **42/42 ✓** | 6 |

> **Revisão 2 (após o feedback da correção).** Na primeira entrega, a autenticação dos endpoints sensíveis era *opt-in*: sem `ADMIN_TOKEN`/`AUTH_REQUIRED`, as rotas continuavam abertas, contradizendo os próprios relatórios, que as classificavam como CRITICAL/HIGH. Corrigi a skill (`04-mvc-guidelines.md` §5, T04 do playbook, template do relatório e validação da Fase 3), restaurei os 3 projetos ao código original e rodei a skill de novo. Agora a proteção é **obrigatória e fail-closed**: sem credencial configurada, a rota nega (401). A Fase 3 testa 401 sem token, 401 com token inválido, 401 com a credencial ausente do ambiente e 200 com token válido. Detalhes em [Segurança: autenticação fail-closed](#segurança-autenticação-fail-closed).

---

## A) Análise Manual

Antes de escrever a skill, li os 3 projetos e registrei os problemas encontrados. A baseline de respostas de cada endpoint ficou em `docs/baseline-projeto-N.txt` e há um smoke test por projeto em `scripts/smoke-projeto-N.sh`. Os achados de cada projeto também estão em `docs/analise-manual-projeto-N.md`.

### Projeto 1 — code-smells-project (Python/Flask, e-commerce)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | SECRET_KEY exposta na API | `controllers.py:289` → `GET /health` retorna `secret_key` | Qualquer pessoa obtém a chave usada para assinar sessões/tokens |
| 2 | CRITICAL | Senhas em texto puro e expostas | `GET /usuarios` retorna o campo `senha` sem hash | Vazamento direto de credenciais de todos os usuários |
| 3 | CRITICAL | Endpoint que executa SQL arbitrário | `app.py:59` → `POST /admin/query` | Permite ler/alterar/apagar o banco via HTTP |
| 4 | HIGH | Debug ligado em "producao" | `GET /health` → `debug: true`, `ambiente: producao` | Debug expõe stack traces e console interativo |
| 5 | MEDIUM | Tratamento de erro duplicado e que vaza detalhes internos | `controllers.py:218-220` (padrão repetido em todas as funções) | `except Exception` genérico retorna `str(e)` ao cliente; sem error handler centralizado |
| 6 | MEDIUM | Controller com responsabilidade de notificação | `controllers.py:208-210` | Envio de e-mail/SMS/push acoplado ao controller; deveria estar em um serviço próprio |
| 7 | LOW | Uso de `print` em vez de logging | `controllers.py:208-210, 219` | Sem níveis de log, sem formatação, impossível de controlar em produção |
| 8 | LOW | Magic numbers na regra de desconto | `models.py:257-262` → faixas `10000/5000/1000` e taxas `0.1/0.05/0.02` | Regra de negócio sem nome nem explicação; difícil de alterar com segurança |
| 9 | CRITICAL | SECRET_KEY hardcoded no código-fonte | `app.py:7` → `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` (e `app.py:8`, `app.py:88` com `debug=True` e `host="0.0.0.0"`) | Chave de assinatura versionada no repositório; qualquer um com acesso ao código pode forjar sessões |
| 10 | CRITICAL | SQL Injection por concatenação de strings | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 149-150, 155-166, 174, 188, 192, 220, 224, 280, 289-297` | Entrada do usuário vai direto para o SQL; em `login_usuario` (`models.py:109-111`) permite bypass de autenticação com `' OR '1'='1` |
| 11 | CRITICAL | God Module concentrando acesso a dados e regras de negócio de 4 domínios | `models.py:1-314` (produtos, usuários, pedidos e relatórios: SQL, serialização, cálculo de total/estoque e regra de desconto no mesmo arquivo) | Impossível testar ou alterar um domínio sem afetar os outros; não há fronteira entre Model e regra de negócio |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de produção hardcoded | `src/utils.js:3-4` → `dbPass` e `paymentGatewayKey: "pk_live_..."` | Qualquer pessoa com acesso ao código obtém a senha do banco e a chave live do gateway |
| 2 | CRITICAL | Número do cartão e chave do gateway impressos em log | `src/AppManager.js:45` | Dados de cartão em log violam PCI-DSS; logs costumam ser amplamente acessíveis |
| 3 | CRITICAL | God Class concentrando rotas, regras de negócio, seed e acesso a dados | `src/AppManager.js:18-131` (todas as rotas no mesmo arquivo) | Impossível testar em isolamento; qualquer mudança afeta tudo |
| 4 | CRITICAL | Endpoint administrativo sem autenticação | `GET /api/admin/financial-report` (`AppManager.js:80`) responde 200 sem credencial | Expõe nomes de alunos e valores pagos a qualquer pessoa |
| 5 | HIGH | Criptografia caseira e senha padrão fraca | `src/utils.js:19-22` (`badCrypto`); `src/AppManager.js:68` (`badCrypto(p \|\| "123456")`) | Hash inseguro e truncado; usuários sem senha recebem "123456" |
| 6 | HIGH | Exclusão sem cascata/transação deixa registros órfãos | `DELETE /api/users/:id` (`AppManager.js:131`) — a resposta admite "matrículas e pagamentos ficaram sujos" | Quebra integridade referencial; relatórios ficam inconsistentes |
| 7 | MEDIUM | Callback hell (padrão legado) | `src/AppManager.js:38-60` (callbacks aninhados do sqlite3) | Difícil de ler e tratar erros; equivalente moderno é `async/await` com Promises |
| 8 | MEDIUM | Dependências com pacotes deprecated | `npm install` → `tar@6`, `glob@7`, `inflight` (via `sqlite3@5`) | Pacotes sem suporte, alguns com vulnerabilidades conhecidas |
| 9 | MEDIUM | Formato de resposta inconsistente | `src/AppManager.js:35-60` → erros em texto puro (`res.send("Pagamento recusado")`), sucesso em JSON | Clientes da API não conseguem tratar erros de forma padronizada |
| 10 | MEDIUM | Seed de dados embutido na classe principal | `src/AppManager.js:18-21` | Dados de teste misturados com código de produção |
| 11 | LOW | `console.log` como sistema de log | `src/utils.js:13`, `src/app.js:13`, `src/AppManager.js:45` | Sem níveis, formato ou controle por ambiente |
| 12 | LOW | Magic numbers | `src/utils.js:19` (`10000` iterações), `src/utils.js:22` (`substring(0, 10)`) | Parâmetros de segurança sem nome nem explicação |
| 13 | LOW | Nomes de campos crípticos | Payload do checkout: `usr`, `eml`, `pwd`, `c_id` | Reduz legibilidade e aumenta chance de erro de integração |

### Projeto 3 — task-manager-api (Python/Flask, task manager)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Debug ativo e servidor exposto em todas as interfaces | Boot: `Debug mode: on`, `Running on all addresses (0.0.0.0)`, `Debugger is active!` | Debugger do Werkzeug acessível na rede permite execução remota de código |
| 2 | CRITICAL | Senha com hash MD5 sem salt e exposta pela API | `GET /users/1` retorna `password: 81dc9bdb...` (MD5 de "1234") | MD5 é revertido instantaneamente com rainbow tables; hash não deveria sair da API |
| 3 | HIGH | Regra de negócio dentro das rotas (sem camada de controller) | `routes/task_routes.py:85-155` (POST /tasks com ~70 linhas de validação e persistência) | Rotas "gordas" dificultam teste e reuso; viola separação MVC |
| 4 | MEDIUM | Uso de API deprecated (Python) | `seed.py:66-74` → `datetime.utcnow()` | Marcado para remoção; substituir por `datetime.now(datetime.UTC)` |
| 5 | MEDIUM | Uso de API deprecated (SQLAlchemy) | `routes/task_routes.py:188, 195` → `Model.query.get(id)` | API legada no SQLAlchemy 2.x; substituir por `db.session.get(Model, id)` |
| 6 | MEDIUM | Query N+1 | `routes/task_routes.py:44-57` (busca User e Category por task); `routes/report_routes.py:163` (count por categoria) | Número de queries cresce linearmente com os registros |
| 7 | MEDIUM | Serialização e cálculo de `overdue` duplicados | `routes/task_routes.py:18-39`, `task_routes.py:74-80`, `routes/user_routes.py:163-180` | Mesma lógica em 3 lugares, com saídas diferentes por rota |
| 8 | LOW | Magic values: listas de status e roles fixas no código | `routes/task_routes.py:177`, `routes/user_routes.py:120` | Deveriam ser constantes/enums centralizados |
| 9 | LOW | Checagem de tipo com `type(x) == list` | `routes/task_routes.py:210` | Não idiomático; usar `isinstance` |
| 10 | LOW | CRUD de categorias no blueprint de relatórios | `routes/report_routes.py:157-211` | Responsabilidade no lugar errado |
| 11 | LOW | Listagens sem paginação | `GET /tasks`, `GET /users` | Retorna todos os registros de uma vez |
| 12 | HIGH | Autenticação falsa e hash de senha em todas as respostas | `POST /login` retorna `token: fake-jwt-token-1`; `password` aparece em login, `POST /users` e `PUT /users/:id` | Token previsível e nunca validado: nenhuma rota é de fato protegida |

**Totais:** 11, 13 e 12 achados. Cada projeto tem pelo menos 1 CRITICAL/HIGH, 2 MEDIUM e 2 LOW.

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # processo: orquestra as 3 fases
└── references/
    ├── 01-project-analysis.md            # Fase 1: heurísticas de linguagem, framework, banco, domínio, arquitetura, endpoints
    ├── 02-anti-patterns-catalog.md       # Fase 2: 19 anti-patterns com sinais de detecção (Python e JS) e severidade
    ├── 03-report-template.md             # Fase 2: formato obrigatório do relatório
    ├── 04-mvc-guidelines.md              # Fase 3: camadas, estrutura alvo por stack, preservação de contrato
    └── 05-refactoring-playbook.md        # Fase 3: 16 transformações com código antes/depois
```

### Decisões de design

1. **O `SKILL.md` define o processo e os references guardam o conhecimento.** O `SKILL.md` é curto e diz *o que fazer e em que ordem*. Cada fase manda ler apenas os references de que precisa, e cada uma das 5 áreas obrigatórias tem o seu arquivo.
2. **Pausa obrigatória.** A Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e com a instrução explícita de não criar, alterar ou apagar nenhum arquivo antes do "y". Nos testes, `git status` continuou limpo depois da Fase 2 nos 3 projetos.
3. **Validação contra a própria baseline.** Antes de mexer no código, a Fase 3 sobe a aplicação **original** em `127.0.0.1` e grava status e corpo de cada endpoint. Depois da refatoração, repete o mesmo plano de requisições e compara os resultados. Assim a skill valida sozinha, sem depender de scripts externos.
4. **Preservação de contrato** (`04-mvc-guidelines.md` §5). Rotas, métodos, status, chaves de entrada e saída, comando de execução e porta continuam iguais. As exceções são só as mudanças de segurança, e cada uma aparece em "Contract notes":
   - campos sensíveis removidos das respostas;
   - endpoints de SQL arbitrário desligados;
   - autenticação **obrigatória e fail-closed** em todo endpoint citado em finding AP-04. Sem token, com token inválido ou sem a credencial configurada no ambiente, a resposta é 401. Com o token válido, status e formato são os da baseline. Não existe flag que desligue a verificação.
5. **Fase 3 adaptativa.** A estratégia depende do tipo de projeto: um monolito ou God Class passa por reestruturação completa; um projeto parcialmente em camadas recebe melhoria incremental, mantendo `models/`, `routes/` e `services/` e criando as camadas que faltam.
6. **Evidência obrigatória.** Todo finding precisa ter `arquivo:linha` conferido no código, e os findings ficam ordenados de CRITICAL a LOW. O Summary tem que bater com a lista de findings.

### Catálogo de anti-patterns (19)

| ID | Anti-pattern | Severidade | Origem (achados manuais) |
|---|---|---|---|
| AP-01 | Hardcoded Credentials / Secrets | CRITICAL | P1-9, P2-1 |
| AP-02 | SQL Injection / Execução de query arbitrária | CRITICAL | P1-3, P1-10 |
| AP-03 | Exposição de dados sensíveis / senha insegura | CRITICAL | P1-1, P1-2, P2-2, P2-5, P3-2, P3-12 |
| AP-04 | Endpoint sensível sem auth (ou auth falsa) | CRITICAL/HIGH | P1-3, P2-4, P3-12 |
| AP-05 | God Class / God File | CRITICAL | P1-11, P2-3 |
| AP-06 | Configuração insegura de execução | HIGH; CRITICAL se debug + 0.0.0.0 | P1-4, P3-1 |
| AP-07 | Lógica de negócio na rota (Fat Route) | HIGH | P3-3, P1-6 |
| AP-08 | Operações sem transação / integridade | HIGH | P2-6 |
| AP-09 | Acoplamento / estado global / sem DI | HIGH | P2-3 (+ enunciado) |
| AP-10 | API/dependência deprecated e padrão assíncrono legado | MEDIUM | P3-4, P3-5, P2-7, P2-8 |
| AP-11 | Query N+1 | MEDIUM | P3-6 |
| AP-12 | Erros não centralizados / respostas inconsistentes | MEDIUM | P1-5, P2-9 |
| AP-13 | Lógica duplicada | MEDIUM | P3-7, P1-5 |
| AP-14 | Responsabilidade fora do lugar | MEDIUM | P2-10, P3-10, P1-6 |
| AP-15 | Validação ausente ou espalhada | MEDIUM | P3-3 (+ enunciado) |
| AP-16 | `print`/`console.log` como log | LOW | P1-7, P2-11 |
| AP-17 | Magic numbers / strings | LOW | P1-8, P2-12, P3-8 |
| AP-18 | Nomes ruins / código não idiomático / código morto | LOW | P2-13, P3-9 |
| AP-19 | Listagem sem paginação | LOW | P3-11 |

**Por que estes:** cada um generaliza um ou mais achados manuais (os 36 estão cobertos). Os casos AP-09 e AP-15 também cobrem exemplos que o próprio enunciado dá na escala de severidade. O AP-10 traz uma **tabela de APIs deprecated** (Python, SQLAlchemy, Flask, Node, Express, npm/pip) com o equivalente moderno de cada uma, e a skill é obrigada a percorrê-la em todo projeto. O playbook tem **16 transformações (T01–T16)** com código antes/depois, e cada AP aponta para a transformação que o corrige.

### Como a skill ficou agnóstica de tecnologia

- **Regra "generalizar, nunca decorar".** Os references não citam nomes de arquivos, linhas nem valores dos 3 projetos. Os exemplos usam entidades fictícias (`Item`, `Order`, `Account`). Fiz uma varredura com grep para garantir isso.
- **Detecção por sinais.** A stack é identificada pelo manifesto (`requirements.txt`, `package.json`, `go.mod`…) e pelos imports, e as rotas por padrões de declaração por framework (Flask, FastAPI, Django, Express, Fastify, Nest).
- **Sinais de detecção em Python e em JS/TS** para cada anti-pattern, e estrutura MVC alvo descrita para Flask e para Express.
- **Validação independente de stack.** Usa HTTP com `curl` e o comando de execução original. Para subir o app original em `127.0.0.1` sem editar o código, a skill usa no Flask o `flask --app <módulo> run --host 127.0.0.1` e no Node um shim carregado com `node -r` que injeta o host no `listen`.

### Desafios encontrados e soluções

| Desafio | Solução |
|---|---|
| Corrigir a segurança sem deixar brecha "por padrão" | Na 1ª entrega a auth era *opt-in* (rota aberta sem a variável), justificada por um smoke que eu mesmo tinha escrito esperando 200 anônimo. O enunciado só exige que os endpoints continuem respondendo, e 401 é uma resposta. Na revisão 2 a regra virou **fail-closed** na skill, a mudança 200 → 401 anônimo vai para "Contract notes" e a Fase 3 valida 401/200. |
| `datetime.utcnow()` → `datetime.now(UTC)` quebra comparações com colunas *naive* do SQLite e muda o `str()` das respostas | O playbook (T08) prescreve um helper `utcnow()` que devolve UTC *naive*. |
| Provar que a confirmação é real em modo não interativo | Execução em **duas chamadas isoladas**: `claude -p "/refactor-arch"` (Fases 1–2) e depois `claude -p "y" --resume <session_id>` (Fase 3). |
| Não expor servidores na rede durante os testes | O padrão `HOST=127.0.0.1` vai para a config, e a baseline do app original é capturada com bind local. |
| Lacuna na minha análise manual do P1 | Conferi no código e adicionei SECRET_KEY hardcoded, SQL Injection e God Module (P1-9 a P1-11). |
| O sandbox da sessão headless não preservou o `mktemp -d` entre comandos (P3) | A própria skill contornou com um diretório temporário em `$HOME` e limpou tudo no fim. Registrado em `docs/progresso.md`. |

**Iterações:**
1. **Entrega 1:** os 3 projetos passaram na 1ª execução, mas com autenticação *opt-in*.
2. **Revisão 2 (feedback da correção):** os references foram ajustados para auth fail-closed com validação 401/200. Os 3 projetos foram restaurados ao original e a skill rodou de novo, sem intervenção manual no código gerado. Os 3 passaram na primeira rodada da revisão.

O registro completo está em [`docs/progresso.md`](docs/progresso.md).

---

## C) Resultados

### Findings por severidade (Fase 2)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Achados manuais cobertos |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 6 | 3 | 5 | 4 | **18** | 11/11 |
| 2 — ecommerce-api-legacy | 4 | 4 | 5 | 3 | **16** | 13/13 |
| 3 — task-manager-api | 4 | 4 | 6 | 4 | **18** | 12/12 |

Os números diferem um pouco da entrega 1 porque a skill rodou de novo do zero. A diferença está em como os findings foram agrupados (por exemplo, no P1 o SQL arbitrário de `/admin/query` entrou no finding de SQL Injection), não em problemas perdidos.

Relatórios completos: [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md) e [`reports/audit-project-3.md`](reports/audit-project-3.md). A saída da Fase 3 de cada projeto está em `docs/logs/fase3-projeto-N.md`.

APIs deprecated detectadas:
- **P2:** API de callbacks do `sqlite3` (callback hell) e pacotes transitivos deprecated do `sqlite3@5` (`inflight`, `glob`, `tar`…).
- **P3:** `datetime.utcnow()`, `Model.query.get()` (SQLAlchemy 2.x) e as dependências não usadas `requests==2.31.0` e `marshmallow`.
- **P1:** nenhuma; o relatório registra "None found" explicitamente.

### Antes / depois

**Projeto 1: monolito, reestruturação completa** (4 arquivos / 780 linhas → 37 arquivos / 1141 linhas)
```
ANTES                         DEPOIS
app.py                        app.py                 # composition root (create_app)
controllers.py                config/settings.py
models.py                     models/      database.py, seed.py, produto/usuario/pedido/relatorio/sistema_model.py
database.py                   controllers/ produto/usuario/pedido/relatorio/sistema_controller.py, pagination.py
requirements.txt              views/       *_routes.py (Blueprints finos), request_utils.py
                              services/    notification_service.py
                              middlewares/ error_handler.py, auth.py
                              validators/  produto/pedido/usuario_validator.py, common.py
                              errors.py
```

**Projeto 2: God Class, reestruturação completa** (3 arquivos / 180 linhas → 25 arquivos / 537 linhas)
```
ANTES                         DEPOIS
src/app.js                    src/app.js             # composition root + DI
src/AppManager.js             src/config/index.js
src/utils.js                  src/database/   connection.js (Promises + transação), seed.js
                              src/models/     user, course, enrollment, payment, auditLog, report
                              src/controllers/ checkout, report, user
                              src/routes/     checkout, admin, user
                              src/services/   paymentService.js, cacheService.js
                              src/middlewares/ errorHandler.js, asyncHandler.js, auth.js
                              src/validators/ checkout               src/errors/HttpError.js
                              src/utils/      logger.js, password.js (scrypt)
```

**Projeto 3: parcialmente em camadas, melhoria incremental** (15 arquivos / 1158 linhas → 38 arquivos / 1455 linhas)
```
ANTES                         DEPOIS
app.py                        app.py                 # create_app + DI (seed.py continua importando app, db)
database.py                   database.py            (mantido)
models/ task, user, category  models/ base.py (CrudMixin) + task, user, category com consultas/agregações
routes/ task, user, report    routes/ task, user, report, category (novo), system   ← finos
services/notification_service services/ notification_service (config injetada), token_service
utils/helpers.py (morto)      utils/ errors.py, time.py (utcnow naive), constants.py, stats.py
seed.py                       seed.py
                              config/settings.py      controllers/ task, user, category, report, system
                              validators/ task, user, category, common   middlewares/ error_handler, auth
```

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1:** linguagem detectada corretamente | ✅ Python 3.13 | ✅ JavaScript/Node 20 | ✅ Python 3.13 |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4 | ✅ Flask 3.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2:** relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 18 | ✅ 16 | ✅ 18 |
| Detecção de APIs deprecated | ✅ (nenhuma, declarado) | ✅ | ✅ |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3:** estrutura de diretórios segue MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ | ✅ | ✅ |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` | ✅ `src/app.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 65/65 | ✅ 14/14 | ✅ 42/42 |
| Endpoints sensíveis negam acesso anônimo (401 sem token / 401 sem credencial configurada / 200 com token) | ✅ 10 rotas | ✅ 2 rotas | ✅ 6 rotas (+403 p/ papel insuficiente) |

Validação interna da própria skill (baseline × depois):
- **P1:** 34/34 requisições com o mesmo status e as mesmas chaves (rotas protegidas chamadas com token); a única diferença é o `/health` sem `secret_key`/`db_path`. Auth: 10 endpoints com 401 sem token, 401 com token inválido, 401 com `ADMIN_TOKEN` ausente e 200/201 com token.
- **P2:** 11/11 iguais em status e formato. Auth: 2 endpoints com 401 sem token, 401 com token inválido, 401 com `ADMIN_TOKEN` ausente e 200 com token.
- **P3:** 44/44 status iguais à baseline; as diferenças de chave são só o `password` removido. Auth: 6 endpoints, 45/45 verificações (401 sem token, 401 com token inválido, 401 após restart sem `SECRET_KEY`, 403 com usuário comum, 200/201 com admin).

### Logs (smoke test externo, `scripts/smoke-projeto-N.sh`, servidores em 127.0.0.1)

Em P1 e P2 o smoke roda duas vezes: com `ADMIN_TOKEN` exportado e com o servidor iniciado **sem** a variável, para provar o fail-closed. No P3 o token vem do `POST /login` (admin do seed) e o smoke também testa um usuário comum (403).

<details><summary>Projeto 1: 65/65</summary>

```
## Servidor com ADMIN_TOKEN definido
✓ GET / → 200
✓ GET /health → 200
✓ GET /produtos → 200
✓ GET /produtos/1 → 200
✓ GET /produtos/busca?q=mouse → 200
✓ POST /login → 200
✓ POST /pedidos → 201
✓ GET /pedidos/usuario/2 → 200
✓ GET /usuarios (sem token) → 401
✓ GET /usuarios (token inválido) → 401
✓ GET /usuarios (com token) → 200
✓ GET /usuarios/1 (sem token) → 401
✓ GET /usuarios/1 (token inválido) → 401
✓ GET /usuarios/1 (com token) → 200
✓ GET /pedidos (sem token) → 401
✓ GET /pedidos (token inválido) → 401
✓ GET /pedidos (com token) → 200
✓ PUT /pedidos/1/status (sem token) → 401
✓ PUT /pedidos/1/status (token inválido) → 401
✓ PUT /pedidos/1/status (com token) → 200
✓ GET /relatorios/vendas (sem token) → 401
✓ GET /relatorios/vendas (token inválido) → 401
✓ GET /relatorios/vendas (com token) → 200
✓ POST /produtos (sem token) → 401
✓ POST /produtos (token inválido) → 401
✓ POST /produtos (com token) → 201
✓ PUT /produtos/1 (sem token) → 401
✓ PUT /produtos/1 (token inválido) → 401
✓ PUT /produtos/1 (com token) → 200
✓ POST /admin/query (sem token) → 401
✓ POST /admin/query (token inválido) → 401
✓ POST /admin/query (com token) → 403
✓ POST /admin/reset-db (sem token) → 401
✓ POST /admin/reset-db (token inválido) → 401
✓ DELETE /produtos/11 (sem token) → 401
✓ DELETE /produtos/11 (token inválido) → 401
✓ DELETE /produtos/11 (com token) → 200

## Servidor SEM ADMIN_TOKEN (fail-closed)
- ADMIN_TOKEN não exportado: verificações com token válido puladas (modo sem credencial)
✓ GET / → 200
✓ GET /health → 200
✓ GET /produtos → 200
✓ GET /produtos/1 → 200
✓ GET /produtos/busca?q=mouse → 200
✓ POST /login → 200
✓ POST /pedidos → 201
✓ GET /pedidos/usuario/2 → 200
✓ GET /usuarios (sem token) → 401
✓ GET /usuarios (token inválido) → 401
✓ GET /usuarios/1 (sem token) → 401
✓ GET /usuarios/1 (token inválido) → 401
✓ GET /pedidos (sem token) → 401
✓ GET /pedidos (token inválido) → 401
✓ PUT /pedidos/1/status (sem token) → 401
✓ PUT /pedidos/1/status (token inválido) → 401
✓ GET /relatorios/vendas (sem token) → 401
✓ GET /relatorios/vendas (token inválido) → 401
✓ POST /produtos (sem token) → 401
✓ POST /produtos (token inválido) → 401
✓ PUT /produtos/1 (sem token) → 401
✓ PUT /produtos/1 (token inválido) → 401
✓ POST /admin/query (sem token) → 401
✓ POST /admin/query (token inválido) → 401
✓ POST /admin/reset-db (sem token) → 401
✓ POST /admin/reset-db (token inválido) → 401
✓ DELETE /produtos/1 (sem token) → 401
✓ DELETE /produtos/1 (token inválido) → 401

--- server log (sem ADMIN_TOKEN, boot):
2026-11-06 12:36:24,089 WARNING config.settings: SECRET_KEY não definida; usando chave aleatória (não persiste entre restarts)
2026-11-06 12:36:24,089 WARNING config.settings: ADMIN_TOKEN não definido; rotas protegidas responderão 401 até a variável ser configurada
2026-11-06 12:36:24,290 INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```
</details>

<details><summary>Projeto 2: 14/14</summary>

```
## Servidor com ADMIN_TOKEN definido
✓ POST /api/checkout → 200
✓ POST /api/checkout → 400
✓ GET /api/admin/financial-report (sem token) → 401
✓ GET /api/admin/financial-report (token inválido) → 401
✓ DELETE /api/users/1 (sem token) → 401
✓ DELETE /api/users/1 (token inválido) → 401
✓ GET /api/admin/financial-report (com token) → 200
✓ DELETE /api/users/1 (com token) → 200

## Servidor SEM ADMIN_TOKEN (fail-closed)
✓ POST /api/checkout → 200
✓ POST /api/checkout → 400
✓ GET /api/admin/financial-report (sem token) → 401
✓ GET /api/admin/financial-report (token inválido) → 401
✓ DELETE /api/users/1 (sem token) → 401
✓ DELETE /api/users/1 (token inválido) → 401
- ADMIN_TOKEN não exportado: verificações com token válido puladas (modo sem credencial)
```
</details>

<details><summary>Projeto 3: 42/42 (após <code>python seed.py</code>)</summary>

```
✓ GET / → 200
✓ GET /health → 200
✓ GET /tasks → 200
✓ GET /tasks/1 → 200
✓ GET /tasks/search?q=login → 200
✓ GET /tasks/stats → 200
✓ GET /users → 200
✓ GET /users/1 → 200
✓ GET /users/1/tasks → 200
✓ GET /categories → 200
✓ POST /login (admin) → 200
✓ POST /login (usuário comum) → 200
✓ GET /reports/summary (sem token) → 401
✓ GET /reports/summary (token inválido) → 401
✓ GET /reports/summary (usuário comum) → 403
✓ GET /reports/user/1 (sem token) → 401
✓ GET /reports/user/1 (token inválido) → 401
✓ GET /reports/user/1 (usuário comum) → 403
✓ GET /reports/summary (admin) → 200
✓ GET /reports/user/1 (admin) → 200
✓ POST /users (sem token) → 401
✓ POST /users (token inválido) → 401
✓ POST /users (usuário comum) → 403
✓ POST /users role=admin (admin) → 201
✓ POST /users role=user (anônimo) → 201
✓ PUT /users/:id (sem token) → 401
✓ PUT /users/:id (outro usuário) → 403
✓ PUT /users/:id (admin) → 200
✓ POST /tasks → 201
✓ PUT /tasks/:id → 200
✓ DELETE /tasks/:id → 200
✓ POST /categories → 201
✓ PUT /categories/:id → 200
✓ DELETE /categories/5 (sem token) → 401
✓ DELETE /categories/5 (token inválido) → 401
✓ DELETE /categories/5 (usuário comum) → 403
✓ DELETE /categories/:id (admin) → 200
✓ DELETE /users/5 (sem token) → 401
✓ DELETE /users/5 (token inválido) → 401
✓ DELETE /users/5 (usuário comum) → 403
✓ DELETE /users/:id (admin) → 200
✓ DELETE /users/:id (admin criado no smoke) → 200
```
</details>

Os logs completos, incluindo o log de cada servidor, estão em `docs/logs/`.

### Evidência: dados sensíveis fora do log (P2)

Na versão original, cada checkout gravava no log o número completo do cartão e a chave live do gateway:

```
Processando cartão 4111222233334444 na chave pk_live_...
```

Log de boot e do checkout no P2 refatorado: a chave vem do ambiente (sem ela, o gateway roda em modo simulado), o cartão aparece mascarado e o servidor escuta só em `127.0.0.1`:

```
[2026-11-06T15:27:14.034Z] WARN PAYMENT_GATEWAY_KEY não definido; gateway de pagamento em modo simulado
[2026-11-06T15:27:14.035Z] WARN ADMIN_TOKEN não definido; rotas protegidas responderão 401 até ser configurado
[2026-11-06T15:27:14.040Z] INFO Frankenstein LMS rodando em http://127.0.0.1:3000
[2026-11-06T15:27:14.062Z] INFO Processando pagamento {"card":"****4444","simulated":true}
```

### Mudanças de comportamento intencionais (segurança)

| Projeto | Mudança |
|---|---|
| Todos | Bind padrão `127.0.0.1` (antes `0.0.0.0`) e debug desligado; configuráveis por `HOST`/`PORT`/`APP_DEBUG`. Os segredos vêm do ambiente. |
| P1 | `senha` sai de `/usuarios`. `secret_key`/`db_path` saem de `/health`. As senhas passam a ser guardadas com hash (scrypt), com migração. Cadastro anônimo com `"tipo":"admin"` é gravado como cliente. **10 rotas exigem `ADMIN_TOKEN`** (`GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`, `POST/PUT/DELETE /produtos`, `POST /admin/query`, `POST /admin/reset-db`). As duas de admin também ficam desligadas por padrão (403 com token, a menos que `ENABLE_ADMIN_ENDPOINTS=1`). Entradas que davam 500 agora dão 400. |
| P2 | **`GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `ADMIN_TOKEN`.** O DELETE apaga em cascata, numa transação, e a mensagem não admite mais dados órfãos. Checkout recusado não cria mais o usuário. Sem `pwd`, a senha é aleatória em vez de "123456". O relatório sai em ordem determinística. |
| P3 | `password` sai de todas as respostas. MD5 → scrypt, com migração no login. O token do `/login` passa a ser assinado e expira. **Sempre exigem token:** `POST /users` com papel acima de `user` (só admin), `PUT /users/<id>` (o próprio usuário ou admin; `role`/`active` só admin), `DELETE /users/<id>` e `DELETE /categories/<id>` (admin), e `GET /reports/*` (admin/manager). Entradas inválidas dão 400 e os erros saem em JSON. |

### Segurança: autenticação fail-closed

Todo endpoint citado em finding AP-04 passa a exigir credencial, **sem chave de liga/desliga**:

| Situação | P1 / P2 (credencial estática `ADMIN_TOKEN`) | P3 (token assinado do `/login`) |
|---|---|---|
| Sem header `Authorization` | 401 | 401 |
| Token inválido | 401 | 401 |
| Credencial não configurada no servidor | **401** (ninguém acessa; o boot loga um *warning*) | Sem `SECRET_KEY`, a chave aleatória do boot invalida tokens antigos → 401 |
| Usuário autenticado sem o papel exigido | — | 403 |
| Token válido | 200/201, mesmo corpo da baseline | 200/201, mesmo corpo da baseline |

O status anônimo dessas rotas passou de 200 para 401. É uma mudança intencional de contrato, registrada em "Contract notes" de cada `docs/logs/fase3-projeto-N.md`. As demais rotas mantêm o contrato original.

### Como a skill se comportou em stacks diferentes

- **Monolito Python (P1):** reestruturação completa, com o maior número de CRITICAL (6) e de endpoints protegidos (10). Detectou o bypass de login por SQL Injection e o *escalonamento* do AP-06 (debug + `0.0.0.0` → CRITICAL), exatamente como o catálogo define.
- **Node/Express (P2):** a mesma skill trocou o vocabulário sozinha: Promises e `async/await` no lugar de callbacks, factory functions para DI e `asyncHandler`. Manteve os erros em **texto puro** onde o original respondia texto, preservando o contrato. Também identificou um bug latente que derrubava o processo (`card` não-string).
- **Projeto em camadas (P3):** escolheu a estratégia **incremental**. Manteve `models/`, `routes/`, `services/` e `seed.py`, criou só o que faltava, moveu o CRUD de categorias para o lugar certo e removeu código morto. O `python seed.py` continuou funcionando.
- **Custo e tempo da revisão 2** (Fases 1–2 / Fase 3): P1 ~US$0,80 / ~US$2,73 (6,8 min); P2 ~US$0,67 / ~US$1,94 (6,7 min); P3 ~US$0,93 / ~US$3,51 (8,4 min).

---

## D) Como Executar

### Pré-requisitos
- [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado e autenticado (`claude --version`; testado com 2.1.319).
- Python 3.12+ com `venv` (P1 e P3) e Node.js 18+ com npm (P2).
- Preparar os ambientes:
  ```bash
  (cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)
  (cd task-manager-api   && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)
  (cd ecommerce-api-legacy && npm install)
  ```

### Executar a skill

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto. Para outro projeto, basta copiar a pasta.

```bash
# Interativo
cd code-smells-project && claude "/refactor-arch"   # responda "y" após o relatório

# Não interativo (como foi feito nesta entrega): 2 chamadas isoladas
cd code-smells-project
claude -p "/refactor-arch" --output-format json --dangerously-skip-permissions > fase2.json
SID=$(python3 -c "import json;print(json.load(open('fase2.json'))['session_id'])")
claude -p "y" --resume "$SID" --output-format json --dangerously-skip-permissions > fase3.json
```
Repita com `ecommerce-api-legacy/` e `task-manager-api/`. Para voltar um projeto ao estado original:
`git checkout original -- <pasta>` (a tag `original` marca o boilerplate) e remova os arquivos novos.

### Validar a refatoração

Cada bloco é independente e começa na raiz do repositório. O servidor sobe em background e o loop `until curl ...` espera até ele responder (qualquer resposta HTTP serve; nesta máquina o Flask leva ~35 s). Só então o smoke roda e, por fim, o servidor é encerrado. P1 e P3 usam a mesma porta (5000), então rode um bloco por vez.

```bash
REPO=$(git rev-parse --show-toplevel)   # raiz do repositório
wait_for() { until curl -s -o /dev/null "$1"; do sleep 1; done; }

# Projeto 1 — code-smells-project (porta 5000): com token e depois sem a credencial (fail-closed)
cd "$REPO/code-smells-project"
export ADMIN_TOKEN=$(openssl rand -hex 16)
.venv/bin/python app.py > /tmp/p1.log 2>&1 & PID=$!
wait_for http://127.0.0.1:5000/
bash "$REPO/scripts/smoke-projeto-1.sh" http://127.0.0.1:5000   # 401 sem token, 200 com token
kill $PID; unset ADMIN_TOKEN; rm -f loja.db
.venv/bin/python app.py > /tmp/p1b.log 2>&1 & PID=$!
wait_for http://127.0.0.1:5000/
bash "$REPO/scripts/smoke-projeto-1.sh" http://127.0.0.1:5000   # rotas protegidas seguem em 401
kill $PID

# Projeto 2 — ecommerce-api-legacy (porta 3000): idem
cd "$REPO/ecommerce-api-legacy"
export ADMIN_TOKEN=$(openssl rand -hex 16)
node src/app.js > /tmp/p2.log 2>&1 & PID=$!     # o mesmo que "npm start"
wait_for http://127.0.0.1:3000/                 # a rota "/" responde 404, mas já indica que o servidor subiu
bash "$REPO/scripts/smoke-projeto-2.sh" http://127.0.0.1:3000
kill $PID; unset ADMIN_TOKEN
node src/app.js > /tmp/p2b.log 2>&1 & PID=$!
wait_for http://127.0.0.1:3000/
bash "$REPO/scripts/smoke-projeto-2.sh" http://127.0.0.1:3000
kill $PID

# Projeto 3 — task-manager-api (porta 5000; seed antes; o smoke obtém o token via /login)
cd "$REPO/task-manager-api"
export SECRET_KEY=$(openssl rand -hex 32)
.venv/bin/python seed.py
.venv/bin/python app.py > /tmp/p3.log 2>&1 & PID=$!
wait_for http://127.0.0.1:5000/
bash "$REPO/scripts/smoke-projeto-3.sh" http://127.0.0.1:5000
kill $PID
```
Todas as linhas do smoke devem começar com `✓`. O log de cada servidor fica em `/tmp/pN.log`.

**Credenciais necessárias para usar as rotas protegidas:** `ADMIN_TOKEN` (P1/P2); no P3, o token do `POST /login` (com `SECRET_KEY` definida para os tokens sobreviverem a restarts). Sem elas, essas rotas respondem 401.

Demais variáveis, documentadas no README de cada projeto: `SECRET_KEY`, `HOST`, `PORT`, `APP_DEBUG`, `LOG_LEVEL`, `APP_ENV`/`DATABASE_PATH`/`ENABLE_ADMIN_ENDPOINTS` (P1), `PAYMENT_GATEWAY_KEY`/`DB_FILE` (P2), `DATABASE_URL`/`TOKEN_MAX_AGE_SECONDS`/`SMTP_*` (P3).

### Estrutura do repositório
```
├── README.md
├── code-smells-project/   .claude/skills/refactor-arch/ + código refatorado (P1)
├── ecommerce-api-legacy/  .claude/skills/refactor-arch/ + código refatorado (P2)
├── task-manager-api/      .claude/skills/refactor-arch/ + código refatorado (P3)
├── reports/               audit-project-1.md, audit-project-2.md, audit-project-3.md
├── scripts/               smoke-projeto-{1,2,3}.sh  (validação externa)
└── docs/                  enunciado, análises manuais, baselines, decisões, progresso, logs/
```
