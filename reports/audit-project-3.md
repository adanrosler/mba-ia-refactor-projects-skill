================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13.15 (.venv do projeto)
Framework:     Flask 3.0.0 (Werkzeug 3.1.9)
Dependencies:  flask-sqlalchemy 3.1.1 (SQLAlchemy 2.1.6), flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Database:      SQLite via ORM SQLAlchemy, arquivo `sqlite:///tasks.db` (criado em `instance/tasks.db` via `db.create_all()` no import de `app.py`)
Domain:        Task manager / produtividade (tasks, users, categories, reports)
Architecture:  Parcialmente em camadas: já existem `models/`, `routes/`, `services/` e `utils/`, mas as rotas concentram validação, ORM, regras ("overdue", estatísticas), serialização e logging. Não há controllers, config, middlewares nem tratamento de erro central.
Entry point:   app.py (run: `python app.py`, 0.0.0.0:5000, debug=True)
Source files:  15 files analyzed | ~1158 lines of code
DB tables:     users, categories, tasks (FK tasks.user_id → users, tasks.category_id → categories)
Endpoints:     22 routes (GET /, GET /health; GET/POST /tasks, GET/PUT/DELETE /tasks/<id>, GET /tasks/search, GET /tasks/stats; GET/POST /users, GET/PUT/DELETE /users/<id>, GET /users/<id>/tasks, POST /login; GET /reports/summary, GET /reports/user/<id>; GET/POST /categories, PUT/DELETE /categories/<id>)
Aux scripts:   seed.py (`python seed.py`: importa `app, db` de app.py, apaga e recria 3 usuários, 4 categorias e 10 tasks)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (SQLite via Flask-SQLAlchemy)
Files:   15 analyzed | ~1158 lines of code
Architecture: Parcialmente em camadas

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 6 | LOW: 4  (Total: 18)

## Findings

### #1 [CRITICAL] Configuração Insegura de Execução (AP-06)
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)`. O modo debug fica ligado de forma fixa e o servidor escuta em todas as interfaces de rede.
Impact: O debugger interativo do Werkzeug fica acessível pela rede. Qualquer pessoa que alcance a porta 5000 pode executar código remotamente ao provocar uma exceção. Pela regra do catálogo, debug junto com bind em 0.0.0.0 é CRITICAL.
Recommendation: Ler DEBUG, HOST e PORT de `config/settings.py`, com defaults DEBUG=false, HOST=127.0.0.1 e PORT=5000 (T01). Em `app.py` fica só o composition root.

### #2 [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:13; services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'supe***'` está fixo no código. O `NotificationService` tem host, usuário e senha SMTP literais (`self.email_password = 'senh***'`).
Impact: Qualquer pessoa com acesso ao repositório consegue forjar sessões e tokens assinados com a SECRET_KEY e usar a conta SMTP. Trocar esses segredos exige mudar o código.
Recommendation: Ler SECRET_KEY e SMTP_* do ambiente em `config/settings.py` (T01). Sem SECRET_KEY, gerar uma chave aleatória no boot e logar um warning. Sem credenciais SMTP, o serviço passa a funcionar em modo desabilitado. As credenciais devem ser injetadas no serviço.

### #3 [CRITICAL] Exposição de Dados Sensíveis / Armazenamento Inseguro de Senha (AP-03)
File: models/user.py:21, 27-32; routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password'`, e esse método é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. As senhas são salvas com `hashlib.md5(pwd)`, sem salt.
Impact: Qualquer cliente anônimo obtém o hash MD5 de qualquer usuário. Com rainbow tables, recuperar as senhas é trivial (as do seed são "1234", "abcd" e "pass").
Recommendation: Remover `password` da serialização e usar `werkzeug.security.generate_password_hash`/`check_password_hash` (T03), com verificação de hashes MD5 legados e re-hash no login → camada Model (`models/user.py`).

### #4 [CRITICAL] Endpoint Sensível sem Autenticação/Autorização, Auth Falsa (AP-04)
File: routes/user_routes.py:42-90, 52, 71-72, 92-132, 119-125, 134-151, 210; routes/report_routes.py:12-101, 103-155, 211-223
Description: O login devolve `'fake-jwt-token-' + str(user.id)` (token previsível) e nenhuma rota verifica `Authorization`. Um cliente anônimo consegue:
- criar usuário com `role: "admin"` (escalonamento de privilégio);
- alterar `role`, `password` e `active` de qualquer usuário;
- apagar qualquer usuário junto com todas as tasks dele;
- apagar categorias;
- ler relatórios com nome e e-mail de usuários e métricas de produtividade.

Impact: Qualquer pessoa assume controle administrativo, troca a senha de terceiros e apaga dados em massa. Como há exclusão em cascata e exposição de dados pessoais, a severidade é CRITICAL.
Recommendation: Autenticação por usuário, obrigatória e fail-closed (T04), em `middlewares/auth.py`. O login passa a emitir um token assinado com SECRET_KEY (itsdangerous, já vem com o Flask), com a mesma chave `token`. Sem token ou com token inválido → 401; papel insuficiente → 403. Se SECRET_KEY não estiver configurada, a chave aleatória do boot invalida qualquer token externo, então a resposta continua 401. Endpoints que passarão a exigir credencial:
- `POST /users`, somente quando `role` ≠ `user`: exige admin. O cadastro público com o papel padrão continua aberto.
- `PUT /users/<id>`: autenticado. Pode editar o próprio usuário ou ser admin. Alterar `role` ou `active` exige admin.
- `DELETE /users/<id>`: admin.
- `DELETE /categories/<id>`: admin.
- `GET /reports/summary` e `GET /reports/user/<id>`: admin ou manager.

### #5 [HIGH] Lógica de Negócio na Camada de Rota (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 92-132; routes/report_routes.py:12-101, 103-155
Description: Os handlers têm de 40 a 90 linhas e fazem tudo no mesmo corpo: validam campo a campo, instanciam modelos, chamam `db.session.add/commit`, calculam atraso e estatísticas, montam o JSON e registram log. Não existe camada de controller.
Impact: As regras não podem ser reutilizadas nem testadas sem HTTP, e qualquer mudança de regra exige mexer em vários handlers.
Recommendation: Criar `controllers/` (task, user, category, report) com os casos de uso, e mover queries e agregações para métodos dos models (T05). As rotas ficam finas.

### #6 [HIGH] Integridade Referencial em Exclusão (AP-08)
File: routes/report_routes.py:211-223; models/task.py:14, 21
Description: `DELETE /categories/<id>` apaga a categoria sem tratar as tasks que apontam para ela. O SQLite não aplica FK por padrão e não há `ondelete`/cascade.
Impact: As tasks ficam com `category_id` órfão, apontando para uma categoria inexistente, e relatórios e filtros passam a mostrar dados inconsistentes.
Recommendation: Na mesma transação, desassociar (`category_id = NULL`) as tasks da categoria antes de apagá-la, com rollback em caso de erro (T06) → `models/category.py` + `controllers/category_controller.py`.

### #7 [HIGH] Acoplamento Forte / Serviço sem Injeção de Dependência (AP-09)
File: services/notification_service.py:4-10, 31-36
Description: `NotificationService` cria internamente as próprias credenciais e conexão SMTP e guarda as notificações numa lista mutável da instância. Nenhum módulo o instancia, então é uma dependência impossível de configurar ou substituir.
Impact: Não dá para testar sem SMTP real nem configurar por ambiente. As notificações em memória se perdem e não são thread-safe.
Recommendation: Receber as configurações SMTP pelo construtor, injetadas a partir de config no composition root. Sem SMTP configurado, o serviço fica desabilitado e só loga (T07).

### #8 [HIGH] Responsabilidade fora do Lugar (AP-14)
File: routes/report_routes.py:157-223; app.py:22-28
Description: O blueprint `reports` contém o CRUD completo de categorias. As rotas `/health` e `/` estão declaradas dentro do entry point.
Impact: Fica difícil saber onde mora cada recurso, e quem mexe em relatórios acaba alterando o CRUD de categorias.
Recommendation: Criar `routes/category_routes.py` e `routes/system_routes.py` com seus controllers (T05). O `app.py` vira composition root.

### #9 [MEDIUM] API Deprecated (AP-10)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213; models/task.py:15-16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74
Description: `Model.query.get(id)` é legado no SQLAlchemy 2.x (instalado: 2.1.6), e `datetime.utcnow()` está deprecated desde o Python 3.12 (runtime: 3.13).
Impact: Geram DeprecationWarnings e vão quebrar em versões futuras.
Recommendation: Trocar por `db.session.get(Model, id)` e por um helper `utcnow()` com `datetime.now(timezone.utc).replace(tzinfo=None)`, que mantém valores naive e compatíveis com o que já está gravado (T08).

### #10 [MEDIUM] Query N+1 (AP-11)
File: routes/task_routes.py:41-57; routes/user_routes.py:22; routes/report_routes.py:53-68, 159-164; routes/task_routes.py:275-281; routes/report_routes.py:15-30
Description: `GET /tasks` faz um `User.query.get` e um `Category.query.get` por task. `GET /users` chama `len(u.tasks)` (lazy load) por usuário. O summary faz uma query de tasks por usuário, e `GET /categories` faz um `count()` por categoria. Os stats disparam 5 a 10 `COUNT` separados.
Impact: O número de queries cresce linearmente com o volume de dados, e a latência acompanha.
Recommendation: Usar agregações com `GROUP BY` e `joinedload`/mapas pré-carregados nos métodos de model (T09).

### #11 [MEDIUM] Tratamento de Erro não Centralizado (AP-12)
File: routes/task_routes.py:62, 137, 151-154, 204, 221-223, 236; routes/user_routes.py:87-90, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88
Description: Há vários `except:` nus e `try/except` repetidos em cada handler, e o projeto não tem `@app.errorhandler`. Exceções não tratadas, como as de #12, viram a página HTML de 500 do Flask.
Impact: Erros reais são engolidos, as respostas de erro saem em formatos diferentes e diagnosticar problemas fica difícil.
Recommendation: Criar erros de domínio (`utils/errors.py`) e um `middlewares/error_handler.py` único que devolve JSON `{'error': ...}` com as mesmas mensagens e status atuais (T10).

### #12 [MEDIUM] Validação de Entrada Ausente ou Espalhada (AP-15)
File: routes/task_routes.py:96-100, 113, 166-170, 182, 261, 264; routes/report_routes.py:196-202; routes/user_routes.py:102-103, 124-125
Description: Vários pontos aceitam entrada sem validar o tipo:
- `priority < 1` com valor string dispara TypeError e retorna 500.
- `int(priority)` e `int(user_id)` no search, sem `try`, também retornam 500.
- `PUT /categories/<id>` não checa `data is None`.
- `len(title)` falha com valor não-string.
- `name` e `active` no PUT de usuário não são validados.
- POST e PUT de task divergem: as mensagens de data são diferentes e o PUT não valida o tipo do título.

Impact: Entradas malformadas causam 500 e podem gravar dados inválidos.
Recommendation: Centralizar as validações em `validators/` (task, user, category), com as mesmas mensagens e status do código original (T12). Tipo inválido passa a retornar 400.

### #13 [MEDIUM] Lógica Duplicada (AP-13)
File: routes/task_routes.py:17-39, 71-80, 283-287; routes/user_routes.py:61, 106, 162-180; routes/report_routes.py:33-43, 129-135; models/task.py:38-60; utils/helpers.py:19-23, 57-116
Description: O cálculo de "overdue" está reimplementado 6 vezes, embora `Task.is_overdue()` já exista. A serialização de task é copiada à mão em `GET /tasks` e em `/users/<id>/tasks`. O regex de e-mail aparece 3 vezes. A `completion_rate` aparece 3 vezes. `process_task_data`, `validate_email` e as constantes `VALID_*` existem, mas não são usados.
Impact: As cópias divergem com o tempo, e qualquer correção precisa ser repetida em vários lugares.
Recommendation: Concentrar essas regras no model (`Task.is_overdue`, `to_dict`), em `validators` e em constantes únicas, e remover o código morto (T11).

### #14 [MEDIUM] Inconsistência: Utils Genérico e Código Morto (AP-18 → agrupado como MEDIUM por volume)
File: services/notification_service.py:1-48; utils/helpers.py:9-116; routes/report_routes.py:7
Description: `NotificationService` nunca é instanciado. `utils/helpers.py` tem 116 linhas, das quais só `format_date` e `calculate_percentage` são importados, em `report_routes.py:7`, e mesmo esses não são usados.
Impact: O código morto engana o leitor; o serviço morto, por exemplo, guarda uma credencial real.
Recommendation: Remover os helpers não usados e manter só o que for consumido (T16). O serviço de notificação passa a ser configurável (#7).

### #15 [LOW] `print` como Sistema de Log (AP-16)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: Eventos e erros da aplicação são registrados com `print(...)`, sem logger configurado.
Impact: Não há nível nem formato, e não dá para filtrar ou direcionar a saída.
Recommendation: Usar `logging.getLogger(__name__)` com configuração no composition root (T13). Os prints do `seed.py` são saída de CLI e ficam.

### #16 [LOW] Magic Numbers / Magic Strings (AP-17)
File: routes/task_routes.py:32, 96-114, 177, 182, 286; routes/user_routes.py:64, 71, 115, 120; routes/report_routes.py:24-28, 45, 129; models/task.py:39, 46; app.py:34
Description: As listas literais de status e papéis aparecem em 6 lugares. Os limites 3/200 (título), 1–5 (prioridade), 4 (senha), `priority <= 2` (alta prioridade) e 7 dias (atividade recente) estão soltos no código, assim como a porta 5000.
Impact: Mudar uma regra exige caçar literais pelo código, com risco de inconsistência.
Recommendation: Criar constantes nomeadas num único módulo (T14).

### #17 [LOW] Nomenclatura Ruim / Código não Idiomático (AP-18)
File: app.py:7; routes/task_routes.py:7, 141, 210; routes/user_routes.py:6; routes/report_routes.py:8; models/task.py:3, 38-60; models/user.py:3, 34-38; utils/helpers.py:2-7, 103; routes/report_routes.py:24-28
Description: Há imports não usados (`os, sys, json`, `time`, `hashlib`) e `type(x) == list` em vez de `isinstance`. `if cond: return True else: return False` aparece em `validate_status` e `is_admin`. Os nomes são crípticos (`t`, `u`, `c`, `p1..p5`).
Impact: O código fica mais difícil de ler e manter.
Recommendation: Remover os imports mortos, usar `isinstance` e retornos booleanos diretos, e dar nomes descritivos aos identificadores internos (T16). As chaves do JSON não mudam.

### #18 [LOW] Listagem sem Paginação (AP-19)
File: routes/task_routes.py:14; routes/user_routes.py:12; routes/report_routes.py:159
Description: `GET /tasks`, `GET /users` e `GET /categories` retornam `query.all()` inteiro.
Impact: As respostas crescem sem limite, junto com o tempo e a memória usados.
Recommendation: Aceitar `?page=&per_page=` opcionais; sem esses parâmetros, a resposta continua sendo a lista completa (T15).

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| routes/user_routes.py:29, 94, 136, 155 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| models/task.py:15, 16, 52; models/user.py:14; models/category.py:11 | `datetime.utcnow` | `datetime.now(timezone.utc)` (naive via helper) |
| routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133 | `datetime.utcnow()` | idem |
| services/notification_service.py:35; utils/helpers.py:38; seed.py:66, 67, 69, 70, 74 | `datetime.utcnow()` | idem |

## Refactoring Plan (Phase 3 preview)
Strategy: melhoria incremental. O projeto já é parcialmente em camadas, então mantenho `models/`, `routes/`, `services/`, `utils/` e `database.py`, e crio o que falta: `config/`, `controllers/`, `middlewares/` e `validators/`. As rotas ficam finas e as categorias e rotas de sistema saem para blueprints próprios.
Target structure:
```
app.py                      # composition root: create_app(); app = create_app() (seed importa app, db)
database.py                 # db = SQLAlchemy() (mantido)
config/settings.py          # SECRET_KEY, DEBUG, HOST, PORT, DATABASE_URI, SMTP_*
models/{task,user,category}.py   # entidades + queries/agregações + regras (is_overdue, hash)
controllers/{task,user,category,report,system}_controller.py
routes/{task,user,category,report,system}_routes.py   # blueprints finos
middlewares/{error_handler,auth}.py
validators/{task,user,category}_validator.py
services/{notification_service,token_service}.py
utils/{errors,time,constants}.py
seed.py                     # continua `python seed.py`
```
Contract notes:
- O campo `password` (hash) é removido das respostas de usuário: `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
- `POST /login` continua retornando a chave `token`, mas o valor passa a ser um token assinado em vez de `fake-jwt-token-<id>`.
- Os endpoints de #4 passam a responder 401 sem token ou com token inválido, e 403 com papel insuficiente: `POST /users` com role privilegiado, `PUT /users/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`, `GET /reports/summary` e `GET /reports/user/<id>`. Com o token correto, status e formato não mudam.
- Entradas com tipo inválido que hoje geram 500 passam a gerar 400 com JSON `{'error': ...}`.
- `DELETE /categories/<id>` passa a desassociar as tasks da categoria (`category_id = null`).
- O CRUD de tasks e de categorias (exceto o DELETE de categoria) continua público, como no original, porque não existe modelo de posse.
- O host padrão passa a ser 127.0.0.1 e o debug fica desligado por padrão; os dois são configuráveis por env. A porta continua 5000.

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
