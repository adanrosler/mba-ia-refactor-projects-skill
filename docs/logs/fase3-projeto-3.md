================================
PHASE 3: REFACTORING COMPLETE
================================

A refatoração terminou e passou na validação. Com as mudanças intencionais normalizadas, as 62 requisições batem com a baseline. A app sobe com o mesmo `python app.py`, agora em 127.0.0.1:5000 com debug desligado.

## New Project Structure
```
app.py                         # composition root: create_app(), DI, blueprints, error handlers
config/settings.py             # leitura de env (+ .env via python-dotenv)
database.py                    # db = SQLAlchemy() (mantido)
models/  base.py               # CrudMixin (get/save/delete/count), commit com rollback, paginate
         task.py  user.py  category.py   # entidades, consultas/agregações, regras, to_dict seguro
controllers/ task_controller.py  user_controller.py  category_controller.py  report_controller.py
routes/  task_routes.py  user_routes.py  report_routes.py  category_routes.py  system_routes.py  pagination.py
validators/ common.py  task_validator.py  user_validator.py  category_validator.py
middlewares/ error_handler.py  auth.py
services/ notification_service.py  token_service.py
utils/   errors.py  time.py  numbers.py          # utils/helpers.py (código morto) removido
seed.py                        # mesmo comando: python seed.py
```

## Changes by finding
- #1 [CRITICAL] AP-03 → `password` não aparece mais em nenhuma resposta. Senhas novas usam hash scrypt do Werkzeug. Hashes MD5 antigos são aceitos e migrados no próximo login (testado: `81dc9bdb…` virou `scrypt:…`). Arquivos: `models/user.py`.
- #2 [CRITICAL] AP-01 → SECRET_KEY e SMTP agora vêm de variáveis de ambiente. Sem SECRET_KEY, a app gera uma chave aleatória e loga um warning; sem SMTP, o envio de e-mail fica desligado. Arquivos: `config/settings.py`, `services/notification_service.py`.
- #3 [CRITICAL] AP-06 → `DEBUG` vem desligado e o host padrão é 127.0.0.1 (configuráveis por `APP_DEBUG`/`HOST`). A porta continua 5000 e o CORS é configurável por `CORS_ORIGINS`. Arquivos: `config/settings.py`, `app.py`.
- #4 [HIGH] AP-04 → o token do login agora é assinado e expira. O novo `middlewares/auth.py` só exige token quando `AUTH_REQUIRED=true`:
  - tasks e categorias: escritas exigem token;
  - users: leitura e escrita exigem token; DELETE exige admin;
  - relatórios: exigem admin ou manager;
  - criar usuário com papel diferente de `user`, ou trocar `role`/`active`, exige admin.
  
  Testado: 401 sem token ou com o token antigo, 403 para usuário comum, 200 para admin. Arquivos: `services/token_service.py`, `middlewares/auth.py`, `routes/*`, `controllers/user_controller.py`.
- #5 [HIGH] AP-07 → a lógica saiu das rotas para `controllers/`, `validators/` e `models/`. Cada rota agora só lê o request e devolve a resposta (1 a 3 linhas).
- #6 [HIGH] AP-09 → o NotificationService recebe config e conexão SMTP pelo construtor e não guarda mais estado em memória. É criado no `app.py` e passado ao TaskController, que notifica quando uma task é atribuída (desligado sem SMTP; testado com SMTP falso).
- #7 [MEDIUM] AP-10 → `datetime.utcnow` foi trocado pelo helper `utils/time.utcnow()` e `Query.get` por `db.session.get` em todo o projeto. O seed roda limpo com `-W error::DeprecationWarning`. Removidas as dependências não usadas `requests` e `marshmallow`.
- #8 [MEDIUM] AP-11 → listagens e relatórios agora fazem poucas consultas fixas em vez de uma por item (`joinedload` em GET /tasks, contagens com `GROUP BY`). Arquivos: `models/task.py`.
- #9 [MEDIUM] AP-12 → um único `register_error_handlers` responde todos os erros em JSON `{'error': ...}` e faz o rollback. Os `except:` sem tipo foram eliminados. As mensagens de erro de banco originais foram mantidas via `save('Erro ao criar task')` etc.
- #10 [MEDIUM] AP-13 → a regra de atraso ficou só em `Task.is_overdue()`, a serialização em `to_dict`/`to_brief_dict`, e regex, constantes e percentual existem em um lugar cada.
- #11 [MEDIUM] AP-14 → o CRUD de categorias foi para `routes/category_routes.py` + `controllers/category_controller.py`, com os mesmos caminhos.
- #12 [MEDIUM] AP-15 → os validators checam tipo e formato de cada campo (prioridade, query params, título, email, senha, cor, `active`). Entrada inválida agora dá 400, e as mensagens originais foram mantidas.
- #13 [LOW] AP-16 → `print` virou `logging` em toda a aplicação. O `seed.py` manteve os prints por ser uma ferramenta de linha de comando.
- #14 [LOW] AP-17 → os valores fixos viraram constantes nomeadas nos models e na config (`VALID_STATUSES`, `CLOSED_STATUSES`, limites de prioridade e título, `VALID_ROLES`, `DEFAULT_COLOR`, `PRIORITY_LABELS` etc.).
- #15 [LOW] AP-18 → removidos imports e código morto (`utils/helpers.py`, métodos de validação sem uso no model), trocado `type()==` por `isinstance` e simplificados os booleanos. A checagem de imports não usados não encontrou nada.
- #16 [LOW] AP-19 → paginação opcional com `?page=&per_page=` (testado: a página 2 com 3 itens devolve os ids [4,5,6]). Sem esses parâmetros, a lista vem completa como antes.

## Contract notes
- O campo `password` não aparece mais em GET/POST/PUT /users nem no `user` do /login. O `token` do /login continua sendo uma string, mas agora é assinado em vez de `fake-jwt-token-<id>`.
- Com `AUTH_REQUIRED=true`, as rotas sensíveis exigem `Authorization: Bearer <token>`. Por padrão a autenticação fica desligada, o comportamento é o de antes e um warning aparece no boot.
- Entradas malformadas que antes davam 500 agora dão 400 com mensagem de erro (ex.: prioridade não numérica, `?priority=abc`, tipos errados, `color` fora do formato `#RRGGBB`, `active` que não seja booleano, nome vazio no PUT).
- Erros 404, 405 e 415 do Flask agora vêm em JSON `{'error': ...}`, com o mesmo status de antes.
- O servidor sobe em 127.0.0.1 com debug desligado por padrão.

## Validation
  ✓ Application boots without errors (`python app.py` → "Running on http://127.0.0.1:5000", "Debug mode: off", 0 tracebacks; `python seed.py` OK)
  ✓ All endpoints respond correctly (62/62 requests match baseline: 56/62 idênticas em status e chaves e as 6 restantes diferem só pela remoção de `password` e pelo token; na comparação estrita, com timestamps, `password` e token normalizados: 0 diferenças)
  ✓ Zero anti-patterns remaining from the report (greps sem ocorrências. Sobram só falsos positivos já explicados: MD5 só para verificar hashes legados, prints do seed, chave `password` como campo de entrada, rollback no handler central)
  ✓ MVC checklist (04-mvc-guidelines §7): todos os 9 itens atendidos

## How to run
```bash
pip install -r requirements.txt
python seed.py
python app.py        # http://127.0.0.1:5000
```
Variáveis de ambiente opcionais (também lidas de `.env`), todas documentadas no README:
- **Servidor:** `SECRET_KEY`, `HOST`, `PORT` (5000), `APP_DEBUG`, `LOG_LEVEL`, `CORS_ORIGINS`
- **Banco:** `DATABASE_URL`
- **Autenticação:** `AUTH_REQUIRED`, `AUTH_TOKEN_MAX_AGE`
- **E-mail:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- **Paginação:** `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`
================================

Observações:
- O `instance/tasks.db` foi devolvido exatamente ao estado original. Os usuários de lá ainda têm hash MD5 e passam para scrypt no primeiro login.
- Os arquivos temporários ficaram em `~/refactor-arch-tmp.*` e já foram apagados. Usei esse local porque o sandbox não guardava o diretório do `mktemp -d` padrão de um comando para o outro.
- Nenhum servidor ficou rodando e nenhum `__pycache__` novo foi criado.
- Nada foi commitado.
- Apareceu um arquivo `../reports/audit-project-3.md`, fora do projeto, que não foi criado por mim.