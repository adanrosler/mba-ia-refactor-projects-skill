================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13 (runtime installed; no version pin in project)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Database:      SQLite via raw `sqlite3` driver (manual SQL), file `loja.db` created on first boot
Domain:        E-commerce (produtos, usuarios, pedidos, itens_pedido, sales report)
Architecture:  Unstructured monolith (pseudo-MVC): the files are named `models`/`controllers` but there are no layers. `models.py` mixes SQL with business rules (order total, stock deduction, discount). `controllers.py` reads `request`, formats HTTP and runs SQL (health). `app.py` declares routes and runs SQL directly (admin).
Entry point:   app.py (run: `python app.py`, 0.0.0.0:5000, debug=True)
Source files:  4 .py files analyzed (+ requirements.txt, README.md) | ~780 lines of code
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes (GET /, GET|POST /produtos, GET /produtos/busca, GET|PUT|DELETE /produtos/<id>, GET|POST /usuarios, GET /usuarios/<id>, POST /login, GET|POST /pedidos, GET /pedidos/usuario/<usuario_id>, PUT /pedidos/<pedido_id>/status, GET /relatorios/vendas, GET /health, POST /admin/reset-db, POST /admin/query)
Aux scripts:   none (seed runs inside `database.get_db()` at boot)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask (SQLite, raw sqlite3)
Files:   4 analyzed | ~780 lines of code
Architecture: Unstructured monolith (pseudo-MVC)

## Summary
CRITICAL: 7 | HIGH: 3 | MEDIUM: 5 | LOW: 4  (Total: 19)

## Findings

### #1 [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: Almost every query is built by string concatenation (`"SELECT * FROM produtos WHERE id = " + str(id)`, `"... VALUES ('" + nome + "', '" ...`). This includes the search (`LIKE '%" + termo + "%'`, `categoria = '" + categoria + "'`) and the login (`WHERE email = '" + email + "' AND senha = '" + senha + "'`).
Impact: An attacker can read or change any table via `/produtos/busca?q=`, `POST /produtos` and `POST /usuarios`. They can also log in as anyone (including the admin) with `' OR '1'='1`. Names containing an apostrophe (e.g. "D'Ávila") already break inserts with a 500.
Recommendation: Parameterize every query with `?` placeholders (T02) → `models/*_model.py`.

### #2 [CRITICAL] Arbitrary Query Execution (AP-02)
File: app.py:59-78
Description: `POST /admin/query` reads `dados.get("sql")` from the body and calls `cursor.execute(query)` directly. Non-SELECT statements are committed.
Impact: Anyone with network access can run any SQL statement: dump `usuarios` including passwords, `DROP TABLE`, or change prices and orders.
Recommendation: Turn the endpoint off by default; enable it only via an explicit environment variable plus an admin token (T04) → `views/admin_routes.py` + `middlewares/auth.py`.

### #3 [CRITICAL] Sensitive Data Exposure / Insecure Password Storage (AP-03)
File: models.py:83, 99, 109-111, 126-129; database.py:31, 76-78; controllers.py:287-289
Description:
- `GET /usuarios` and `GET /usuarios/<id>` return the `senha` field.
- Passwords are stored and compared in plain text (seed `"admin123"`, `"123456"`; `AND senha = '...'`).
- `GET /health` returns `secret_key` (`minh***`) and `db_path`.
Impact: Anyone can list every user's credentials without authenticating. A leaked database exposes reusable passwords. The leaked signing key lets attackers forge sessions.
Recommendation: Hash passwords with `werkzeug.security` (PBKDF2/scrypt), migrating plain-text passwords on boot. Use a safe serializer with no `senha`, and remove secrets and internal config from `/health` (T03) → `models/usuario_model.py`, `controllers/health_controller.py`.

### #4 [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:7; controllers.py:289
Description: `app.config["SECRET_KEY"] = "minh***"` is a literal in the code, repeated in the `/health` response.
Impact: The key is public (repository and API), so anything signed with it can be forged. Rotating it requires a code change.
Recommendation: Read `SECRET_KEY` from the environment. If it is missing, generate a random one at boot and log a warning (T01) → `config/settings.py`.

### #5 [CRITICAL] Sensitive Endpoints without Authentication/Authorization (AP-04)
File: app.py:47-57, 59-78; controllers.py:128-134, 257-262
Description:
- `POST /admin/reset-db` deletes all four tables, and `POST /admin/query` runs SQL. Neither has any credential check.
- `/usuarios` (personal data) and `/relatorios/vendas` (revenue) are also public.
- `POST /login` issues no token, so no route can verify identity.
- Escalated to CRITICAL because these routes run SQL and wipe data in bulk.
Impact: A single anonymous request wipes the whole database or exposes customer and financial data.
Recommendation: Add an `admin_required` decorator enabled by `ADMIN_TOKEN`, and turn the destructive and SQL endpoints off by default (T04) → `middlewares/auth.py`.

### #6 [CRITICAL] Insecure Runtime Configuration (AP-06)
File: app.py:8, 88; controllers.py:286, 288
Description: `DEBUG = True` and `app.run(host="0.0.0.0", port=5000, debug=True)` are hardcoded. `/health` reports a fixed `"ambiente": "producao"` and `"debug": True`. Escalated to CRITICAL: debug is on **and** the server binds to `0.0.0.0`.
Impact: The Werkzeug interactive debugger is reachable from the network, which allows remote code execution through any exception (and exceptions are easy to trigger, see #13).
Recommendation: Read `DEBUG` (default false), `HOST` (default 127.0.0.1), `PORT` (default 5000) and `APP_ENV` from the environment (T01) → `config/settings.py`.

### #7 [CRITICAL] God File (AP-05)
File: models.py:1-314; controllers.py:1-292; app.py:47-78
Description:
- `models.py` (314 lines) covers three domains (catalog, users, orders/reports). It mixes SQL with business rules: total calculation and stock deduction (133-169), discount tiers (256-262).
- `controllers.py` covers every domain, reads `request` directly, formats HTTP and runs SQL itself (`health_check`, 264-274).
- `app.py` declares routes **and** runs SQL (reset/query).
Impact: No layer can be tested in isolation. Any change touches several domains at once, and rules are hard to find.
Recommendation: Split into `models/` (per entity), `controllers/` (use cases), `views/` (Blueprints), `services/` and `config/`, leaving `app.py` as the composition root (T05 + T07).

### #8 [HIGH] Multi-step Operations without a Transaction (AP-08)
File: models.py:133-169, 65-70
Description:
- `criar_pedido` checks stock in one loop (144), then inserts `pedidos`, `itens_pedido` and decrements stock in another loop (148-166), with no rollback.
- An exception mid-way (e.g. an item missing `quantidade`) leaves pending writes on the **shared** connection, which the next request's `commit()` then persists.
- The stock check is separate from the decrement, so two concurrent orders can oversell.
- `deletar_produto` deletes the product and leaves orphan `itens_pedido` rows (orders then show "Desconhecido").
Impact: Inconsistent orders and stock, partial orders committed by another request, negative stock.
Recommendation: Wrap the flow in `with conn:` (BEGIN/COMMIT/ROLLBACK). Make the decrement conditional (`UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?`) (T06) → `models/pedido_model.py`.

### #9 [HIGH] Mutable Global State / Tight Coupling (AP-09)
File: database.py:4-11; models.py:1; controllers.py:3; app.py:4
Description: `global db_connection` is a single connection opened with `check_same_thread=False` and shared by every thread of the server. Every module imports `get_db` directly; no dependency is injected.
Impact: Race conditions and mixed transactions between concurrent requests (see #8). Tests cannot swap the database.
Recommendation: Use a per-request connection (`flask.g` + `teardown_appcontext`) with a factory configured in the composition root (T07) → `models/database.py`, `app.py`.

### #10 [HIGH] Fat Controller / Side Effects in the HTTP Flow (AP-07)
File: controllers.py:24-62, 64-96, 188-220, 237-255; app.py:47-78
Description:
- The "controllers" do everything in one function: read `request`, run long validation blocks, apply rules and format the JSON response.
- `criar_pedido` "sends" email, SMS and push notifications inline with `print` (208-210).
- `atualizar_status_pedido` sends notifications inline (247-250).
- The `/admin/*` handlers in `app.py` contain the SQL itself.
Impact: Business rules are tied to the HTTP layer, and notifications cannot be swapped or tested.
Recommendation: Thin routes (views) that extract data → controllers that orchestrate → `services/notification_service.py` for side effects (T05).

### #11 [MEDIUM] N+1 Query (AP-11)
File: models.py:187-199, 219-231, 154-156, 239-254; controllers.py:268-274
Description:
- `get_pedidos_usuario` and `get_todos_pedidos` run one query per order for its items, plus one per item for the product name.
- `criar_pedido` selects each product's price a second time.
- The report and `/health` run separate `COUNT(*)` queries.
Impact: The number of queries grows with orders × items, so the order listing slows down linearly.
Recommendation: Use `JOIN itens_pedido LEFT JOIN produtos` in a single query, and aggregate counts with `SUM(CASE ...)`/`GROUP BY` (T09) → `models/pedido_model.py`.

### #12 [MEDIUM] Non-centralized Error Handling (AP-12)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: Every handler repeats `except Exception as e: return jsonify({"erro": str(e)}), 500`. There is no `@app.errorhandler`, and internal exception messages are sent to the client.
Impact: Internal details leak (SQL errors, table names). The pattern is duplicated 17 times, and Flask's default 404/405 responses come back as HTML.
Recommendation: Add domain errors plus a `register_error_handlers(app)` that logs the traceback and returns JSON, keeping the same messages and status codes (T10) → `middlewares/error_handler.py`.

### #13 [MEDIUM] Missing or Scattered Input Validation (AP-15)
File: controllers.py:26-54, 66-90, 118-121, 169-170, 195-201, 239-240; models.py:140-146; app.py:61-62
Description:
- `request.get_json()` can return `None` before `.get()` (login, order status, admin/query), which raises a 500.
- `preco < 0` with a string value raises a TypeError (500), and `float(preco_min)` with no `try` also raises a 500.
- PUT does not check name length or category, unlike POST (validation diverges between the two).
- Order items (`produto_id`, `quantidade`) are not validated; a negative quantity *increases* stock.
Impact: Easy-to-trigger 500 errors (combined with #6, this is RCE), inconsistent data, and stock manipulation.
Recommendation: Centralize validators per resource and reuse them in POST and PUT, keeping the original messages (T12) → `validators/`.

### #14 [MEDIUM] Logic Duplicated across Functions (AP-13)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 178-199, 211-231; controllers.py:28-46, 72-90
Description: The product serialization is copied three times and the user serialization twice. The order + items assembly is identical in `get_pedidos_usuario` and `get_todos_pedidos`. Product field validation is duplicated between create and update, and the two copies already differ.
Impact: Fixes applied to one copy and not the others (e.g. removing `senha` from one serializer only).
Recommendation: Extract `_row_to_dict`/`to_dict` helpers per entity and a shared validator (T11) → models/validators.

### #15 [MEDIUM] Misplaced Responsibility (AP-14)
File: database.py:56-84; controllers.py:264-274; app.py:47-57
Description: Seed data (products and users with passwords) is inserted inside `get_db()`, the production connection function. `health_check` runs SQL in the controller layer, and `reset_database` runs SQL in the entry point.
Impact: Seed and schema are coupled to every connection, and data access is spread across three files.
Recommendation: Move schema and seed into `models/database.py` (`init_db`, `seed_db`), called by the composition root, and move counts into models (T05/T07).

### #16 [LOW] `print` as Logging System (AP-16)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: Around 20 `print(...)` calls stand in for logging. They write users' emails on login/signup (PII) and fake notifications.
Impact: No levels, no timestamps, no control over output; PII written to stdout.
Recommendation: Use `logging.getLogger(__name__)` with a config in the composition root (T13).

### #17 [LOW] Magic Numbers / Magic Strings (AP-17)
File: controllers.py:47-50, 52, 242, 285; models.py:247-262; app.py:36, 85, 88
Description:
- Name limits (2/200), the category list and the status list are inline literals.
- Discount tiers (10000/5000/1000 → 10%/5%/2%) have no names.
- Version `"1.0.0"` is repeated, and the port/URL are fixed.
Impact: Business rules are hidden and changes must be made in several places.
Recommendation: Named constants in the model/config (`CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`, `FAIXAS_DESCONTO`, `APP_VERSION`) (T14).

### #18 [LOW] Poor Naming / Non-idiomatic Code / Dead Code (AP-18)
File: models.py:2, 187-192, 219-224; database.py:2; controllers.py:14, 56, 64, 98, 136, 200
Description:
- `import sqlite3` (models.py) and `import os` (database.py) are never used.
- The parameter `id` shadows the builtin.
- Cursors are named `cursor2`/`cursor3`.
- `if not itens or len(itens) == 0` is redundant.
Impact: Harder to read, and the dead code misleads readers.
Recommendation: Remove unused imports and rename internals only (`produto_id`), keeping the public JSON keys (T16).

### #19 [LOW] Listing without Pagination (AP-19)
File: models.py:7, 75, 206
Description: `SELECT * FROM produtos`, `usuarios` and `pedidos` have no `LIMIT` and are returned in full by `GET /produtos`, `/usuarios` and `/pedidos`.
Impact: Responses grow without bound as data grows.
Recommendation: Optional pagination through `?page=&per_page=`, keeping the current behavior (full list) when no parameters are sent (T15).

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| — | None found (Flask 3.1.1 / flask-cors 5.0.1 are current; no `utcnow`, `before_first_request`, `pkg_resources` etc.) | — |

## Refactoring Plan (Phase 3 preview)
Strategy: Full restructuring to MVC. This is a monolith where the files are named after layers but none exist. `models.py`, `controllers.py` and `database.py` are broken up, and `app.py` becomes the composition root (`create_app()` + `python app.py`).
Target structure:
```
app.py                      # composition root
config/settings.py          # SECRET_KEY, DEBUG, HOST, PORT, DATABASE_PATH, ADMIN_TOKEN, ENABLE_ADMIN_ENDPOINTS
models/database.py          # per-request connection (flask.g), schema, seed, password migration
models/produto_model.py | usuario_model.py | pedido_model.py | relatorio_model.py
controllers/produto_controller.py | usuario_controller.py | pedido_controller.py | relatorio_controller.py | health_controller.py | admin_controller.py
views/produto_routes.py | usuario_routes.py | pedido_routes.py | relatorio_routes.py | health_routes.py | admin_routes.py
services/notification_service.py
middlewares/error_handler.py | auth.py
validators/produto_validator.py | pedido_validator.py
errors.py                   # domain errors (ValidationError, NotFoundError, ...)
```
Contract notes:
- `GET /usuarios` and `GET /usuarios/<id>` no longer return `senha`.
- `GET /health` no longer returns `secret_key` or `db_path`; `debug`/`ambiente` reflect the actual config.
- `POST /admin/query` and `POST /admin/reset-db` are off by default (403 JSON) and enabled via `ENABLE_ADMIN_ENDPOINTS=1`. With `ADMIN_TOKEN` set, they require `Authorization: Bearer <token>`.
- Passwords are stored as hashes (existing plain-text passwords in `loja.db` are migrated at boot); login keeps working with the same passwords.
- Default host is `127.0.0.1` and debug is off (configurable via `HOST`/`DEBUG`).
- Inputs that used to cause a 500 (missing/invalid JSON, wrong types, invalid items) now return 400 with JSON; unexpected errors return 500 `{"erro": "Erro interno do servidor"}` with no internal details.
- Deleting a product that has orders keeps working; order items keep the name via LEFT JOIN ("Desconhecido").
- Every route, method, success status and top-level key otherwise stays the same.

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]