================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13.15 (`.venv` do projeto)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1 (SQLAlchemy 2.1.6 instalado), flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Database:      SQLite via ORM Flask-SQLAlchemy, arquivo `instance/tasks.db` (URI `sqlite:///tasks.db`, criado com `db.create_all()` no boot)
Domain:        Task manager / produtividade (tasks, users, categories, reports)
Architecture:  Parcialmente em camadas. Já existem `models/`, `routes/`, `services/` e `utils/`, mas as rotas concentram validação, ORM, regra de negócio e serialização. Não há controllers, config nem tratamento central de erros.
Entry point:   app.py (run: `python app.py`, 0.0.0.0:5000, debug=True)
Source files:  15 arquivos .py analisados (+ requirements.txt, README.md) | ~1158 linhas de código
DB tables:     users, tasks, categories
Endpoints:     22 rotas
               GET / · GET /health
               GET|POST /tasks · GET|PUT|DELETE /tasks/<id> · GET /tasks/search · GET /tasks/stats
               GET|POST /users · GET|PUT|DELETE /users/<id> · GET /users/<id>/tasks · POST /login
               GET /reports/summary · GET /reports/user/<id>
               GET|POST /categories · PUT|DELETE /categories/<id>
Aux scripts:   seed.py (`python seed.py`; importa `app, db` de app.py, apaga e repopula as 3 tabelas)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0 (SQLite via Flask-SQLAlchemy)
Files:   15 analyzed | ~1158 lines of code
Architecture: Parcialmente em camadas

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 6 | LOW: 4  (Total: 16)

## Findings

### #1 [CRITICAL] Exposição de Dados Sensíveis / Armazenamento Inseguro de Senha (AP-03)
File: models/user.py:21, 27-32; routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password`, e esse dicionário é devolvido por GET /users/<id>, POST /users, PUT /users/<id> e POST /login (`'user': user.to_dict()`). A senha é guardada com `hashlib.md5(pwd.encode()).hexdigest()`, sem salt.
Impact: Qualquer cliente obtém o hash de qualquer usuário. MD5 sem salt é quebrado em segundos com rainbow tables, o que dá acesso às credenciais em texto puro (inclusive do admin).
Recommendation: Remover `password` da serialização e usar `werkzeug.security.generate_password_hash`/`check_password_hash`, com migração transparente dos hashes MD5 no login (T03) → models/user.py.

### #2 [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:13; services/notification_service.py:7-10
Description: `SECRET_KEY = 'supe***'` está fixo no código. O serviço de notificação traz host, usuário (`task***`) e senha SMTP (`senh***`) literais.
Impact: Quem lê o repositório consegue forjar sessões/tokens assinados com a SECRET_KEY e usar a conta de e-mail. Também não há como trocar segredos por ambiente.
Recommendation: Ler tudo de variáveis de ambiente em `config/settings.py`. SECRET_KEY ausente → gerar aleatória e logar warning. SMTP ausente → serviço desabilitado (T01).

### #3 [CRITICAL] Configuração Insegura de Execução (AP-06)
File: app.py:34, 15
Description: `app.run(debug=True, host='0.0.0.0', port=5000)`. Debug fica ligado fixo e o bind é em todas as interfaces. `CORS(app)` libera qualquer origem, sem configuração.
Impact: O debugger interativo do Werkzeug fica acessível pela rede, o que permite execução remota de código (escalonado a CRITICAL por debug + 0.0.0.0).
Recommendation: `DEBUG` padrão false, `HOST` padrão 127.0.0.1, `PORT` padrão 5000 e origens CORS via env (padrão `*`, para manter o comportamento) (T01) → config/settings.py + app.py.

### #4 [HIGH] Endpoint Sensível sem Autenticação / Auth Falsa (AP-04)
File: routes/user_routes.py:207-211, 52, 71, 119-122, 134-151; routes/task_routes.py:225-238; routes/report_routes.py:103-155, 211-223; app.py:18-20
Description: O login devolve `'token': 'fake-jwt-token-' + str(user.id)`, que é previsível e nunca é verificado. Nenhum blueprint tem autenticação. Qualquer cliente pode criar um usuário com `role: 'admin'`, apagar usuários (com as tasks deles), tasks e categorias, e ler relatórios com e-mail.
Impact: O token não protege nada. Escalada de privilégio trivial, e exclusão e leitura de dados pessoais sem credencial.
Recommendation: Emitir token assinado (itsdangerous + SECRET_KEY) e criar o decorator `require_auth` em `middlewares/auth.py`, ativável por `AUTH_REQUIRED` (desligado por padrão, com warning no boot) (T04).

### #5 [HIGH] Lógica de Negócio na Camada de Rota (Fat Route) (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 240-271, 273-299; routes/user_routes.py:42-90, 92-132, 134-151, 153-183, 185-211; routes/report_routes.py:12-101, 103-155
Description: Os handlers validam campo a campo, instanciam models, fazem `db.session.add/commit/rollback`, calculam atraso, estatísticas e taxas de conclusão e montam o JSON. `create_task` tem 70 linhas e `summary_report` tem 90. Não existe camada de controller.
Impact: Regra de negócio fica impossível de testar sem HTTP, e qualquer mudança de regra exige editar várias rotas.
Recommendation: Criar `controllers/` (task, user, category, report) e `validators/`, deixando as rotas só com extração do request e resposta (T05).

### #6 [HIGH] Acoplamento Forte / Estado Global Mutável / Sem DI (AP-09)
File: services/notification_service.py:5-10, 15, 31-36
Description: `NotificationService` cria a conexão `smtplib.SMTP(...)` internamente, embute credenciais e guarda as notificações numa lista mutável em memória (`self.notifications`). O serviço nunca é instanciado nem injetado em lugar nenhum.
Impact: Não dá para substituir o transporte em testes. Se for ligado, as notificações se perdem a cada restart e podem divergir entre workers.
Recommendation: Injetar a configuração SMTP pelo construtor (vinda de config), operar em modo desabilitado sem credenciais e instanciar no composition root (T07).

### #7 [MEDIUM] API / Dependência Deprecated (AP-10)
File: models/user.py:14; models/task.py:15-16, 52; models/category.py:11; routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285; routes/user_routes.py:29, 94, 136, 155, 172; routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74; requirements.txt:4-6
Description: `datetime.utcnow()` está deprecated desde o Python 3.12 e `Model.query.get()` é legado no SQLAlchemy 2.x. `requests==2.31.0` (CVE-2024-35195) e `marshmallow` estão fixados, mas não são usados.
Impact: Warnings no runtime atual e quebra em versões futuras. Dependências mortas aumentam a superfície de ataque.
Recommendation: Usar `db.session.get(Model, id)` e um helper `utcnow()` naive baseado em `datetime.now(timezone.utc)`, para manter a comparação com colunas naive. Remover dependências não usadas (T08).

### #8 [MEDIUM] Query N+1 (AP-11)
File: routes/task_routes.py:41-57, 275-279; routes/user_routes.py:22; routes/report_routes.py:19-28, 55-56, 163
Description: GET /tasks faz `User.query.get` e `Category.query.get` para cada task. GET /users usa `len(u.tasks)` (lazy load por usuário). O summary consulta as tasks de cada usuário em loop, `/categories` faz um `count()` por categoria, e há 4 a 9 `COUNT` separados onde um `GROUP BY` resolveria.
Impact: O número de queries cresce com o volume de dados e a latência das listagens e relatórios piora.
Recommendation: Eager loading (`joinedload`/`selectinload`) e agregações `GROUP BY` nos models (T09).

### #9 [MEDIUM] Tratamento de Erro não Centralizado (AP-12)
File: routes/task_routes.py:62, 137, 146-154, 204, 217-223, 236; routes/user_routes.py:80-90, 130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 48, 88; app.py (sem `errorhandler`)
Description: Há 12 `except:` sem tipo e blocos try/rollback repetidos em cada handler. GET /tasks engole qualquer erro como `'Erro interno'`. Não existe handler global, então erros inesperados (ex.: TypeError) viram 500 em HTML, e 404/405 respondem em HTML.
Impact: Bugs ficam ocultos e os clientes recebem formatos de erro inconsistentes.
Recommendation: Criar erros de domínio (`ValidationError`, `NotFoundError`, `ConflictError`…) e `middlewares/error_handler.py` com `register_error_handlers(app)` respondendo `{'error': msg}`, com rollback central (T10).

### #10 [MEDIUM] Lógica Duplicada (AP-13)
File: routes/task_routes.py:17-39, 71-80, 96-100, 166-170, 283-287, 296; routes/user_routes.py:15-23, 61, 106, 162-180; routes/report_routes.py:33-37, 67, 132-135, 151; models/task.py:50-60; utils/helpers.py:14-23, 57-108
Description: A regra "está atrasada" foi copiada em 6 lugares enquanto `Task.is_overdue()` existe e não é usado. A serialização de task se repete à mão (task_routes 17-28 vs `Task.to_dict`). O regex de e-mail e a taxa de conclusão também estão duplicados, apesar de `validate_email`/`calculate_percentage` existirem (este último importado e não usado). As regras de título e status aparecem repetidas.
Impact: As cópias divergem (ex.: a mensagem de data difere entre POST e PUT) e corrigir uma regra exige editar vários pontos.
Recommendation: Centralizar em `Task.is_overdue()`/`to_dict()`, em validators e num helper de percentual (T11).

### #11 [MEDIUM] Responsabilidade fora do Lugar (AP-14)
File: routes/report_routes.py:157-223
Description: O CRUD completo de categorias (GET/POST/PUT/DELETE /categories) está dentro do blueprint de relatórios.
Impact: Fica difícil achar e manter o código da entidade, e o acoplamento entre domínios aumenta.
Recommendation: Mover para `routes/category_routes.py` + `controllers/category_controller.py`, mantendo os mesmos caminhos (T05).

### #12 [MEDIUM] Validação de Entrada Ausente ou Espalhada (AP-15)
File: routes/task_routes.py:96, 113, 182, 261, 264; routes/user_routes.py:102-103, 106, 124-125; routes/report_routes.py:180, 196-202
Description: `priority < 1` com string causa TypeError (500). `int(request.args['priority'])` não tem tratamento (500). `len(title)` e `re.match` quebram com tipos que não são string. PUT /users aceita nome vazio e `active` de qualquer tipo. PUT /categories sem corpo dá `'name' in None` (500). `color` nunca é validado, apesar da coluna `String(7)` e de `is_valid_color` existir. POST e PUT têm regras diferentes.
Impact: Entradas malformadas derrubam o handler com 500 e dados inconsistentes entram no banco.
Recommendation: `validators/` com checagem de tipo, as mesmas mensagens e 400 para entrada inválida (T12).

### #13 [LOW] print como Sistema de Log (AP-16)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: Os eventos e erros da aplicação são registrados com `print(...)`.
Impact: Não há nível, destino nem formato configuráveis, e os erros se perdem em produção.
Recommendation: Usar `logging.getLogger(__name__)` (T13). O seed.py, por ser CLI, pode manter os prints.

### #14 [LOW] Magic Numbers / Magic Strings (AP-17)
File: routes/task_routes.py:96, 99, 104, 110, 113, 177, 182; routes/user_routes.py:52, 64, 71, 115, 120; routes/report_routes.py:45, 129, 180; models/task.py:12, 39; app.py:34; utils/helpers.py:110-116
Description: Os literais 3/200 (título), 1-5 (prioridade), 4 (senha), 7 dias, `priority <= 2`, `'#000000'` e 5000, além das listas de status e papéis, aparecem repetidos. As constantes de `utils/helpers.py:110-116` existem, mas ninguém as usa.
Impact: Mudar uma regra exige caçar literais pelo código.
Recommendation: Constantes nomeadas nos models e na config (T14).

### #15 [LOW] Nomenclatura Ruim / Código não Idiomático / Código Morto (AP-18)
File: app.py:7; routes/task_routes.py:7, 141, 210; routes/user_routes.py:6; routes/report_routes.py:7-8, 24-28; models/task.py:3, 38-60; models/user.py:34-38; utils/helpers.py:3-7, 9-108; services/notification_service.py:1-48
Description: Imports não usados (`os, sys, json, time, hashlib, math`), `type(tags) == list`, `if cond: return True else: return False`, import dentro de função (helpers.py:33) e nomes crípticos (`p1..p5`, `u`, `t`, `c`). `utils/helpers.py` inteiro e `NotificationService` não têm chamadores.
Impact: Ruído de leitura e falsa impressão de que existe validação ou notificação.
Recommendation: Limpar imports, usar `isinstance`, simplificar booleanos, remover código morto e renomear apenas nomes internos (T16).

### #16 [LOW] Listagem sem Paginação (AP-19)
File: routes/task_routes.py:14, 266; routes/user_routes.py:12; routes/report_routes.py:159
Description: GET /tasks, /tasks/search, /users e /categories retornam `.all()` sem limite.
Impact: Respostas e consumo de memória crescem sem limite.
Recommendation: Paginação opcional via `?page=&per_page=`; sem os parâmetros, a resposta continua sendo a lista completa (T15).

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| models/user.py:14; models/task.py:15, 16, 52; models/category.py:11 | `datetime.utcnow` (default de coluna / comparação) | helper `utcnow()` = `datetime.now(timezone.utc).replace(tzinfo=None)` |
| routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133 | `datetime.utcnow()` | idem |
| services/notification_service.py:35; utils/helpers.py:38; seed.py:66, 67, 69, 70, 74 | `datetime.utcnow()` | idem |
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| requirements.txt:5 | `requests==2.31.0` (CVE-2024-35195, não usado) | remover |
| requirements.txt:4 | `marshmallow==3.20.1` (não usado) | remover |

## Refactoring Plan (Phase 3 preview)
Strategy: Melhoria incremental. O projeto já está parcialmente em camadas, então mantenho `models/`, `routes/`, `services/` e `database.py`, crio `config/`, `controllers/`, `validators/` e `middlewares/`, deixo as rotas finas e reduzo `app.py` a composition root (`create_app()` + `app` em nível de módulo, porque o seed.py importa `app, db`).
Target structure:
```
app.py                      # create_app(), registra blueprints/middlewares, app.run(HOST, PORT, DEBUG)
config/settings.py          # SECRET_KEY, DEBUG, HOST, PORT, DATABASE_URL, CORS_ORIGINS, AUTH_REQUIRED, SMTP_*
database.py                 # db = SQLAlchemy() (mantido)
models/                     # user.py, task.py, category.py + consultas/agregações, is_overdue, to_dict seguro
controllers/                # task_controller.py, user_controller.py, category_controller.py, report_controller.py
routes/                     # task_routes.py, user_routes.py, report_routes.py, category_routes.py (finos)
validators/                 # task_validator.py, user_validator.py, category_validator.py
middlewares/                # error_handler.py, auth.py
services/notification_service.py  # config injetada, modo desabilitado
utils/                      # errors.py (erros de domínio), time.py (utcnow); helpers.py morto removido
seed.py                     # mantido (`python seed.py`)
```
Contract notes:
- `password` deixa de aparecer em todas as respostas de usuário (GET/POST/PUT /users, POST /login).
- Hash de senha passa de MD5 para Werkzeug. Hashes MD5 existentes continuam válidos e são migrados no próximo login bem-sucedido.
- O `token` do /login passa a ser assinado (mesma chave, ainda string). A exigência de token nas rotas só vale com `AUTH_REQUIRED=true`. Por padrão o comportamento atual é mantido e um warning é logado.
- Entradas malformadas que hoje geram 500 (prioridade não numérica, query params não inteiros, PUT /categories sem corpo, tipos errados) passam a responder 400 `{'error': ...}`. 404/405/500 não mapeados passam a responder JSON.
- Debug desligado e bind em 127.0.0.1 por padrão (configuráveis por `DEBUG`/`HOST`). Porta 5000 mantida.
- Paginação só se aplica quando `page`/`per_page` forem enviados.

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]