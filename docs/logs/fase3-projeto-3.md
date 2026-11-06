================================
PHASE 3: REFACTORING COMPLETE
================================

## New Project Structure
```
app.py                    # composition root: create_app() + app = create_app() (usado por seed.py e flask --app app)
database.py               # db = SQLAlchemy() (mantido)
seed.py                   # python seed.py (mantido)
config/settings.py        # SECRET_KEY, HOST, PORT, APP_DEBUG, DATABASE_URL, TOKEN_MAX_AGE_SECONDS, SMTP_*
models/
  base.py                 # commit() com rollback + paginate()
  task.py  user.py  category.py   # entidades + consultas/agregações + regras (is_overdue, hash de senha)
controllers/
  task_controller.py  user_controller.py  category_controller.py
  report_controller.py  system_controller.py
routes/                   # blueprints finos (views)
  task_routes.py  user_routes.py  category_routes.py  report_routes.py  system_routes.py
middlewares/
  error_handler.py        # handler único → {'error': ...}
  auth.py                 # require_auth(roles) fail-closed + current_user_or_none()
validators/
  common.py  task_validator.py  user_validator.py  category_validator.py
services/
  token_service.py        # tokens assinados (itsdangerous) com expiração
  notification_service.py # SMTP injetado por config; desabilitado sem config
utils/
  constants.py  errors.py  time.py  stats.py
```
Removido: `utils/helpers.py`, que era código morto.

## Changes by finding
#1 [CRITICAL] AP-06 Config insegura → `debug=True` e `host='0.0.0.0'` saíram do código. Os defaults agora são DEBUG=false, HOST=127.0.0.1 e PORT=5000, todos configuráveis por env (`config/settings.py`, `app.py`).
#2 [CRITICAL] AP-01 Segredos hardcoded → `SECRET_KEY` vem do ambiente; sem ela, o app gera uma chave aleatória e loga um warning. A senha SMTP literal foi removida e as credenciais SMTP vêm do ambiente, injetadas no serviço (`config/settings.py`, `services/notification_service.py`, `app.py`).
#3 [CRITICAL] AP-03 Senha exposta e MD5 → `password` saiu de `User.to_dict()`, e o hash agora é feito com `werkzeug.security` (scrypt). Hashes MD5 legados ainda são aceitos e são migrados no primeiro login (`models/user.py`, `controllers/user_controller.py`).
#4 [CRITICAL] AP-04 Auth falsa e endpoints sem auth → o login emite um token assinado com expiração. `require_auth` é fail-closed e protege 6 endpoints. O cadastro com `role` privilegiado exige admin (`middlewares/auth.py`, `services/token_service.py`, `routes/*`).
#5 [HIGH] AP-07 Fat routes → criei a camada `controllers/`. As rotas agora só extraem o request e devolvem o JSON; queries e agregações foram para os models.
#6 [HIGH] AP-08 Órfãos ao apagar categoria → **o finding era um falso positivo**. A baseline mostrou que o backref do SQLAlchemy já zerava `category_id`. Deixei a desassociação explícita, na mesma transação, em `Category.delete()`, e o comportamento não mudou. A exclusão de usuário e das tasks dele também acontece num único commit.
#7 [HIGH] AP-09 Acoplamento → `NotificationService` e `TokenService` são criados no composition root e injetados nos controllers. A lista mutável de notificações foi removida.
#8 [HIGH] AP-14 Responsabilidade fora do lugar → o CRUD de categorias foi para `routes/category_routes.py` + `CategoryController`, e `/` e `/health` foram para `routes/system_routes.py`.
#9 [MEDIUM] AP-10 Deprecated → `Model.query.get` virou `db.session.get` (via `Model.find`), e `datetime.utcnow` virou `utils.time.utcnow()` (que devolve um valor naive), inclusive no `seed.py`.
#10 [MEDIUM] AP-11 N+1 → uso `joinedload` em `GET /tasks` e agregações com `GROUP BY` para contagem de tasks por usuário e por categoria, status, prioridade e produtividade por usuário.
#11 [MEDIUM] AP-12 Erros → o middleware único cobre `AppError`, `HTTPException` e `Exception`. Não sobrou nenhum `except:` nu, e as mensagens e status originais foram mantidos.
#12 [MEDIUM] AP-15 Validação → criei `validators/`. Entradas com tipo inválido, que antes davam 500, agora dão 400: `priority` como string, `?priority=abc`, PUT de categoria sem corpo, título numérico.
#13 [MEDIUM] AP-13 Duplicação → as regras ficaram num lugar só: `Task.is_overdue`, `Task.to_dict(with_overdue, with_names)`, `to_summary_dict`, `completion_rate`, regex de e-mail e listas de status/papéis.
#14 [MEDIUM] Código morto → `utils/helpers.py` foi removido. O serviço de notificação agora é usado ao atribuir uma task e fica desabilitado sem SMTP.
#15 [LOW] AP-16 print → passei a usar `logging`. Só sobraram os prints de CLI do `seed.py`.
#16 [LOW] AP-17 Magic numbers → `utils/constants.py`.
#17 [LOW] AP-18 Não idiomático → imports mortos removidos (0 restantes pela checagem via AST), `isinstance` no lugar de `type(x) ==`, retornos booleanos diretos e nomes descritivos.
#18 [LOW] AP-19 Paginação → `?page=&per_page=` opcionais em `/tasks`, `/users` e `/categories`; sem esses parâmetros, a resposta continua sendo a lista completa.

## Contract notes
- O campo `password` não aparece mais em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` nem `POST /login` (`user`).
- `POST /login` mantém a chave `token`, mas o valor agora é um token assinado, não mais `fake-jwt-token-<id>`.
- Sem token ou com token inválido, estes endpoints passam a responder **401**, e **403** com papel insuficiente:
  - `POST /users` com role diferente de `user`
  - `PUT /users/<id>`
  - `DELETE /users/<id>`
  - `DELETE /categories/<id>`
  - `GET /reports/summary`
  - `GET /reports/user/<id>`

  Com o token correto, status e formato são os mesmos da baseline.
- Entradas com tipo inválido que davam 500 agora dão 400 `{'error': ...}`. Os 404/405 do framework agora respondem em JSON, com o mesmo status.
- O host padrão passou a ser 127.0.0.1 e o debug fica desligado; a porta continua 5000.
- Criar ou reatribuir uma task com `user_id` dispara `notify_task_assigned`. Sem SMTP configurado, isso só gera uma linha de log.

## Validation
  ✓ Application boots without errors (`flask --app app run --host 127.0.0.1 --port 5000` e `python app.py`: bind em 127.0.0.1:5000, debug off, sem tracebacks; `python seed.py` ok)
  ✓ All endpoints respond correctly (44/44 status iguais à baseline; 40/44 com chaves idênticas, e as 4 diferenças são a remoção intencional de `password`; 0 diferenças de valor ignorando timestamps/password/token)
  ✓ Sensitive endpoints deny anonymous access (6 endpoints: 401 sem token, 401 com token inválido, 401 com credencial ausente após restart sem `SECRET_KEY` e token antigo, 403 com usuário comum, 200/201 com admin: 45/45 OK)
  ✓ Zero anti-patterns remaining from the report (greps de segredos, debug/0.0.0.0, md5 de geração, `fake-jwt`, `utcnow`, `query.get`, `except:`, `print(`, `type()==`, ORM fora de models e imports mortos: 0 ocorrências)
  ✓ MVC checklist (04-mvc-guidelines §7)

Observações:
- **Correção de um deslize meu:** durante a refatoração rodei `git rm --cached utils/helpers.py`, uma operação de git que a skill proíbe. Restaurei a entrada do índice com o blob original (`eed3bc2`); ela voltou a aparecer como `A` staged, com o arquivo removido só na working tree. Não fiz commit, checkout nem stash.
- O projeto não tinha banco antes da validação, então `instance/` foi apagado no final. Não há servidores rodando nem `__pycache__` no projeto. As evidências (`baseline.txt`, `after.txt`, `auth.txt` e logs) ficaram fora do projeto, no diretório temporário `/var/folders/_p/810l3_fx34ncs9079178tggw0000gn/T/tmp.iJTEUPc8zC`.
- `requirements.txt` não mudou. `marshmallow`, `requests` e `python-dotenv` continuam listados, mas não são usados.

## How to run
```bash
.venv/bin/pip install -r requirements.txt
export SECRET_KEY=$(openssl rand -hex 32)   # obrigatória para tokens estáveis
python seed.py
python app.py                               # http://127.0.0.1:5000
```
Variáveis aceitas: `SECRET_KEY`, `HOST` (127.0.0.1), `PORT` (5000), `APP_DEBUG` (false), `DATABASE_URL` (sqlite:///tasks.db), `TOKEN_MAX_AGE_SECONDS` (86400) e `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`.

**Os endpoints protegidos exigem `Authorization: Bearer <token>`.** O token vem de `POST /login`; o admin do seed é `joao@email.com` / `1234`. Sem token válido, eles respondem 401. Sem `SECRET_KEY`, a chave muda a cada restart e os tokens anteriores passam a dar 401.
================================
