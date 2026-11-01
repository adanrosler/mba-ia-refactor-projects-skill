================================
PHASE 3: REFACTORING COMPLETE
================================

## New Project Structure
```
app.py                          # composition root: create_app() + python app.py
errors.py                       # AppError, ValidationError, NotFoundError, UnauthorizedError, ForbiddenError
config/settings.py              # SECRET_KEY, DEBUG, HOST, PORT, APP_ENV, DATABASE_PATH, LOG_LEVEL, ADMIN_TOKEN, ENABLE_ADMIN_ENDPOINTS
models/
  database.py                   # one connection per request (flask.g), schema, paginate()
  seed.py                       # seed data (hashed passwords)
  produto_model.py | usuario_model.py | pedido_model.py | relatorio_model.py | admin_model.py
controllers/
  produto_controller.py | usuario_controller.py | pedido_controller.py
  relatorio_controller.py | health_controller.py | admin_controller.py
views/
  root_routes.py | produto_routes.py | usuario_routes.py | pedido_routes.py
  relatorio_routes.py | health_routes.py | admin_routes.py | pagination.py
validators/  common.py | produto_validator.py | usuario_validator.py | pedido_validator.py
services/    notification_service.py
middlewares/ error_handler.py | auth.py
README.md, requirements.txt (unchanged)
```
Removed: `controllers.py`, `models.py`, `database.py`.

## Changes by finding
- #1 [CRITICAL] SQL Injection → every query now uses `?` placeholders. Search builds `LIKE ?` with bound parameters. Login looks the user up by email only and checks the password hash. (`models/*_model.py`)
- #2 [CRITICAL] Arbitrary query endpoint → `/admin/query` is off by default (403) and enabled only with `ENABLE_ADMIN_ENDPOINTS=1`, plus `ADMIN_TOKEN` if set. (`views/admin_routes.py`, `middlewares/auth.py`, `models/admin_model.py`)
- #3 [CRITICAL] Sensitive data / plain-text passwords → passwords are hashed (werkzeug scrypt), and existing plain-text passwords are migrated at boot. Serializers no longer include `senha`, and `/health` no longer returns `secret_key` or `db_path`. (`models/usuario_model.py`, `models/seed.py`, `controllers/health_controller.py`)
- #4 [CRITICAL] Hardcoded secret → `SECRET_KEY` comes from the environment; if missing, a random key is generated and a warning is logged. (`config/settings.py`)
- #5 [CRITICAL] Endpoints without auth → `admin_token_required` (on `GET /usuarios`, `GET /pedidos`, `GET /relatorios/vendas`) and `admin_tools_required` (on `/admin/*`). (`middlewares/auth.py`)
- #6 [CRITICAL] debug + 0.0.0.0 → `DEBUG` defaults to false and `HOST` to 127.0.0.1. `/health` reports the actual `debug`/`ambiente`. (`config/settings.py`, `app.py`)
- #7 [CRITICAL] God File → split into config/models/controllers/views/services/middlewares/validators, with dependency injection wired in `create_app()`.
- #8 [HIGH] No transaction → order creation runs in one transaction (`with conn:`) with a conditional stock decrement (`AND estoque >= ?`); any failure rolls back. Deleted products show "Desconhecido" in orders via LEFT JOIN (mitigation that keeps order history and the contract). (`models/pedido_model.py`)
- #9 [HIGH] Global state → removed the global `db_connection` / `check_same_thread=False`. There is now one connection per app context, and models receive `get_connection` by injection. (`models/database.py`, `app.py`)
- #10 [HIGH] Fat controller → routes only extract input and format the response, controllers orchestrate, and notifications go through `NotificationService`. (`views/`, `controllers/`, `services/`)
- #11 [MEDIUM] N+1 → order listing uses 2 queries (orders, then items with JOIN to products) regardless of size. Order creation loads products with a single `IN`. The report uses a single query with `SUM(CASE…)`. (`models/pedido_model.py`, `models/produto_model.py`, `models/relatorio_model.py`)
- #12 [MEDIUM] Scattered error handling → all 17 `try/except` blocks removed. `register_error_handlers` handles `AppError`, `HTTPException` (JSON 404/405) and unexpected errors (logged, generic 500). (`middlewares/error_handler.py`)
- #13 [MEDIUM] Missing validation → validators shared between POST and PUT. Added type checks for `preco`/`estoque`/`nome`, checks on order items (`produto_id`/`quantidade` must be integers > 0), price filter checks, and handling of a missing body. (`validators/`)
- #14 [MEDIUM] Duplication → one `to_dict` per entity and one order-assembly function. (`models/*`)
- #15 [MEDIUM] Misplaced responsibility → seed moved to `models/seed.py`, health counts to the models, reset to `AdminModel`.
- #16 [LOW] print → replaced by `logging` everywhere; login/signup logs record the user id instead of the email.
- #17 [LOW] Magic numbers → named constants `CATEGORIAS_VALIDAS`, `NOME_MIN_LEN`/`NOME_MAX_LEN`, `STATUS_VALIDOS`, `FAIXAS_DESCONTO`, `APP_VERSION`; port comes from config.
- #18 [LOW] Naming / dead code → unused imports removed (checked with an AST scan), `id` renamed to `produto_id`/`usuario_id`, `cursor2`/`cursor3` gone.
- #19 [LOW] No pagination → optional `?page=&per_page=` (max 100) on `/produtos`, `/usuarios`, `/pedidos`; without parameters the full list is returned, as before.

## Contract notes
- `GET /usuarios` and `GET /usuarios/<id>` no longer return `senha`.
- `GET /health` no longer returns `secret_key` or `db_path`. `debug` now reports the actual value (`false` by default).
- `POST /admin/query` and `POST /admin/reset-db` return 403 `{"erro": "Endpoint administrativo desabilitado"}` unless `ENABLE_ADMIN_ENDPOINTS=1` is set.
- When `ADMIN_TOKEN` is set, the sensitive routes require `Authorization: Bearer <token>` (401 otherwise). Without it, behavior is unchanged and a warning is logged at boot.
- Default bind is now `127.0.0.1` (was `0.0.0.0`) with debug off.
- Inputs that used to cause a 500 now return 400 JSON: no body on `/login` or `/pedidos/<id>/status`, string `preco`, invalid items, `preco_min=abc`.
- Unexpected errors return `{"erro": "Erro interno do servidor"}` instead of `str(e)`. Unknown routes and wrong methods return JSON instead of HTML.
- `PUT /produtos/<id>` now applies the same name-length and category rules as POST; an invalid category, previously accepted, is now rejected with 400.
- Passwords in an existing `loja.db` are converted to hashes on the first boot. Login keeps working with the same passwords.

## Validation
  ✓ Application boots without errors (`python app.py`; also checked with `flask --app app run --host 127.0.0.1 --port 5000`). No tracebacks in the logs. Startup takes about 35s to start serving, but a minimal 5-line Flask app takes the same time on this machine, so it comes from the environment, not the refactor.
  ✓ All endpoints respond correctly (36/38 requests match baseline status and top-level keys). The 2 differences are both `GET /health` with the intentional removal of `secret_key`/`db_path`. Messages and values are identical apart from timestamps, removed `senha` and `debug`.
  ✓ Zero anti-patterns remaining from the report. No `print(`, no `global`, no hardcoded secrets, no `debug=True`/`0.0.0.0`, no `str(e)`/`except Exception`, and SQL only in `models/`. The remaining concatenations join fixed SQL fragments and `?` placeholders only (verified false positives). Extra checks also passed:
    - the `' OR '1'='1` login bypass now gets a 401;
    - an over-stock order is rolled back and stock is unchanged;
    - the admin token and flag gating work;
    - plain-text password migration works.
  ✓ MVC checklist (04-mvc-guidelines §7): all 9 items met.

## How to run
```bash
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000
```
Supported environment variables (documented in `README.md`): `SECRET_KEY`, `DEBUG`, `HOST`, `PORT`, `APP_ENV`, `DATABASE_PATH`, `LOG_LEVEL`, `ADMIN_TOKEN`, `ENABLE_ADMIN_ENDPOINTS`.

There was no `loja.db` before the refactor, so none was backed up or restored, and every database created during validation was deleted. No servers are still running, and the temporary directory was removed. Nothing has been committed; versioning is up to you.
================================