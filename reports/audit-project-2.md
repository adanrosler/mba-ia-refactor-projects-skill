================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js v20.20.2)
Framework:     Express ^4.18.2 (4.22.1 installed)
Dependencies:  sqlite3 ^5.1.6 (5.1.7 installed); no CORS, ORM or validation library
Database:      SQLite through the raw `sqlite3` driver with callbacks, in memory (`':memory:'`), so state resets on every boot
Domain:        LMS / course platform with checkout (users, courses, enrollments, payments, audit_logs)
Architecture:  God Class. `AppManager` does everything: it opens the DB connection, creates the schema, seeds data, registers routes and holds all checkout and report logic. `utils.js` mixes config, secrets, global state, cache and "crypto".
Entry point:   src/app.js (run: `npm start` → `node src/app.js`, binds all interfaces : 3000)
Source files:  3 files analyzed | ~180 lines of code (+ package.json, api.http, README)
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 routes (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
Aux scripts:   none (the seed runs inside `AppManager.initDb()` at boot)
================================

**Endpoint details**

| Method | Route | Handler | Input / Statuses |
|---|---|---|---|
| POST | /api/checkout | src/AppManager.js:28 | body `usr`, `eml`, `c_id`, `card` required, `pwd` optional. Returns 400 "Bad Request", 404 "Curso não encontrado", 400 "Pagamento recusado", 500 errors, 200 `{msg, enrollment_id}` |
| GET | /api/admin/financial-report | src/AppManager.js:80 | 200 `[{course, revenue, students:[{student, paid}]}]`. Admin/financial route |
| DELETE | /api/users/:id | src/AppManager.js:131 | 200 text "Usuário deletado, mas…". Destructive route |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4 (SQLite in memory, `sqlite3` driver)
Files:   3 analyzed | ~180 lines of code
Architecture: God Class

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 3  (Total: 16)

## Findings

### #1 [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: src/utils.js:2-5
Description: The `config` object holds literal secrets: `dbPass: "senh***"`, `paymentGatewayKey: "pk_l***"` (a live key prefix), and also `dbUser` and `smtpUser`. All of them are in the source code and versioned in git.
Impact: Anyone with access to the repository gets the production DB password and the payment gateway key. Rotating them requires a deploy.
Recommendation: Read everything from `process.env` with no real defaults. A missing gateway key puts the service in simulated mode (T01) → `src/config/index.js`.

### #2 [CRITICAL] Sensitive Data Exposure / Insecure Password Storage (AP-03)
File: src/AppManager.js:45; src/AppManager.js:18, 68; src/utils.js:17-23
Description: (a) Every checkout logs the full card number and the gateway key: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`. (b) Passwords are "hashed" with `badCrypto`, which repeats the first 2 base64 characters of the password 10,000 times and truncates the result to 10 characters. It is deterministic, has no salt and is trivially reversible. (c) When `pwd` is missing, the user gets the fixed default password `"123456"` (line 68). (d) The seed user is stored with the plaintext password `'123'` (line 18).
Impact: Card numbers and the key leak into logs (a PCI-DSS violation). Passwords are recoverable from the stored value. Accounts created without `pwd` share a known password.
Recommendation: Remove sensitive data from logs (mask the card to its last 4 digits). Use `crypto.scrypt` with a random salt. When `pwd` is missing, generate a random password instead of the fixed one (T03) → `src/utils/password.js`, `src/services/paymentService.js`.

### #3 [CRITICAL] Sensitive Endpoint without Authentication/Authorization (AP-04)
File: src/AppManager.js:80, 131-137
Description: `GET /api/admin/financial-report` returns revenue per course plus student names and amounts paid. `DELETE /api/users/:id` deletes any user. Neither route has any authentication middleware.
Impact: Any anonymous client can read personal and financial data and delete users at will. This is CRITICAL because it exposes personal/financial data and is destructive.
Recommendation: Add mandatory, fail-closed authentication through `requireAdmin`, using the static credential `ADMIN_TOKEN` (`Authorization: Bearer <token>`). It returns 401 when the header is missing, when the token is invalid, and when `ADMIN_TOKEN` is not configured (T04) → `src/middlewares/auth.js`. Endpoints that will require the credential: `GET /api/admin/financial-report` and `DELETE /api/users/:id`.

### #4 [CRITICAL] God Class / God File (AP-05)
File: src/AppManager.js:4-139; src/utils.js:1-25
Description: `AppManager` creates the connection (line 7), defines the schema and seed (lines 10-23), registers the routes (lines 25-137) and holds the checkout, payment and report rules. `utils.js` exports config, secrets, global state, cache and hashing all together.
Impact: Nothing can be tested or changed in isolation. Every change touches the same class, and there is no separation between HTTP, business logic and data.
Recommendation: Decompose into config / database / models / controllers / routes / services / middlewares and turn `app.js` into the composition root (T05, T07).

### #5 [HIGH] Insecure Runtime Configuration (AP-06)
File: src/app.js:12; src/utils.js:6
Description: `app.listen(config.port)` is called without a host, so it binds to all network interfaces. The port is fixed at 3000 with no `PORT`/`HOST` from the environment, and `NODE_ENV` is ignored.
Impact: The API, including the routes without auth, is exposed on every network the machine is connected to. There is no way to configure it per environment.
Recommendation: Read `HOST` (default `127.0.0.1`) and `PORT` (default `3000`) in config and use `app.listen(port, host)` (T01) → `src/config/index.js`, `src/app.js`.

### #6 [HIGH] Multi-step Operations without a Transaction / Referential Integrity (AP-08)
File: src/AppManager.js:50-61, 69; src/AppManager.js:133-135
Description: Checkout writes `users` → `enrollments` → `payments` → `audit_logs` in chained callbacks with no `BEGIN/COMMIT/ROLLBACK`. A failure in the middle leaves an enrollment without a payment, and the audit error is ignored (line 57). `DELETE FROM users` does not remove that user's enrollments and payments. The response itself admits it: "as matrículas e pagamentos ficaram sujos no banco".
Impact: The database becomes inconsistent: orphaned enrollments and payments, plus revenue counted in the report for students who no longer exist ("Unknown").
Recommendation: Run checkout in a single transaction with rollback, and delete payments → enrollments → user in one transaction (T06) → `src/models/*`, `src/controllers/*`.

### #7 [HIGH] Business Logic in the Route Layer (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: The checkout handler (about 50 lines) validates input, looks up the course, creates the user, hashes the password, decides payment approval, enrolls the user, records the payment, writes the audit log and updates the cache, all inside the route. The report handler computes revenue inside the route.
Impact: The business rules cannot be reused or tested without HTTP, and any change risks breaking the rest of the flow.
Recommendation: Use thin routes → `checkoutController` / `reportController` / `userController`, with the gateway in a service (T05).

### #8 [HIGH] Tight Coupling / Mutable Global State / No Dependency Injection (AP-09)
File: src/utils.js:9-10, 12-15, 25; src/AppManager.js:2, 7
Description: `globalCache` and `totalRevenue` are mutable module-level variables that get exported. `logAndCache` mutates the global cache. `totalRevenue` is exported as a primitive, so it is a copy that never updates, and it is never used. The connection is created inside the class constructor with `new sqlite3.Database(':memory:')`, so it cannot be replaced.
Impact: There is state shared between requests and tests, and nothing can be injected or mocked.
Recommendation: Create the connection in the composition root and inject it through factories (`createXModel(db)`), and move the cache into `cacheService` (T07).

### #9 [MEDIUM] Missing Input Validation (AP-15)
File: src/AppManager.js:29-35, 46, 132
Description: Only the presence of fields is checked. `card` is used as `cc.startsWith("4")` with no type check: if a client sends `card` as a number, a `TypeError` is thrown inside the sqlite callback and **the whole process crashes**. `c_id`, `eml` and the `:id` route parameter have no type or format validation.
Impact: A single malformed request takes down the API (DoS), and invalid data reaches the database.
Recommendation: Add a checkout validator that checks types (string/integer) and responds 400 "Bad Request" (T12) → `src/validators/checkoutValidator.js`.

### #10 [MEDIUM] Non-centralized Error Handling (AP-12)
File: src/AppManager.js:38, 41, 51, 55, 57, 70, 84, 92-93, 104, 106, 133-135
Description: Each callback handles `err` its own way, and several ignore it entirely: line 57 (audit), lines 92-93 (where `enrollments.length` throws when `err` is set), lines 104/106, and line 133 (DELETE always returns 200). Line 38 treats a DB error as 404. There is no Express error middleware.
Impact: DB errors are silently swallowed or crash the process, and the responses are wrong.
Recommendation: Add domain errors (`HttpError`) plus a single `errorHandler` middleware and an `asyncHandler` wrapper, keeping the same texts and statuses (T10) → `src/middlewares/errorHandler.js`.

### #11 [MEDIUM] N+1 Query (AP-11)
File: src/AppManager.js:83-127
Description: The report makes 1 query for courses, then 1 per course (enrollments), then 2 per enrollment (`users`, `payments`). Completion is tracked with manual `coursesPending--` / `enrPending--` counters.
Impact: Queries grow linearly with the number of enrollments, and the counter logic is fragile (a single error means the response never arrives).
Recommendation: Use one query with `LEFT JOIN courses/enrollments/users/payments` and aggregate in the model (T09) → `src/models/reportModel.js`.

### #12 [MEDIUM] Legacy Async Pattern / Deprecated Dependencies (AP-10)
File: src/AppManager.js:37-77, 83-128; package-lock.json:37, 831, 1078, 1573, 1722, 2117
Description: Callback hell up to 6 levels deep, using `db.run/get/all(sql, cb)` with no Promises. The `sqlite3@5.1.7` tree pulls in packages marked `deprecated` (`@npmcli/move-file`, `glob` v7, `inflight`, `prebuild-install`, `rimraf` v3, `tar` v6).
Impact: The flow is hard to read and to handle errors in. The transitive packages are unsupported and have known vulnerabilities (glob/tar).
Recommendation: Wrap the driver in Promise helpers and use `async/await` (T08) → `src/database/connection.js`. The transitive dependencies come from sqlite3's native build and need a major upgrade or a driver change (out of scope; recorded).

### #13 [MEDIUM] Misplaced Responsibility (AP-14)
File: src/AppManager.js:12-21, 59
Description: The schema and sample data (seed) live in the main application class. The side effect `logAndCache` (cache) and the audit log run in the middle of the HTTP flow.
Impact: Production code always inserts fake data, and side effects are coupled to the handler.
Recommendation: Move the schema and seed to `src/database/seed.js` and the cache to `src/services/cacheService.js`, called by the controller (T05/T07).

### #14 [LOW] `console.log` as the Logging System (AP-16)
File: src/app.js:13; src/utils.js:13
Description: Improvised logs with `console.log` and no levels. The log on line 45 of AppManager is covered in #2.
Impact: Logs cannot be filtered or turned off per environment.
Recommendation: Add a minimal logger (`src/utils/logger.js`) with levels, writing to stderr (T13).

### #15 [LOW] Magic Numbers / Magic Strings (AP-17)
File: src/utils.js:6, 19, 22; src/AppManager.js:21, 46, 48, 108
Description: `10000` iterations and truncation to `10` in the "hash", the approval rule `startsWith("4")`, the status strings `'PAID'`/`"DENIED"` repeated in 4 places, and the port `3000`.
Impact: Business rules are hidden in literals, so changing them requires hunting through the code.
Recommendation: Use named constants (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) and config (T14).

### #16 [LOW] Poor Naming / Non-idiomatic Code / Dead Code (AP-18)
File: src/AppManager.js:2, 26, 29-33; src/utils.js:2, 5, 17
Description: Cryptic variables `u, e, p, cid, cc`. `const self = this` coexists with arrow functions. `let` is used for values that are never reassigned. `totalRevenue` is imported and never used. `dbUser`/`smtpUser` are never used. The name `badCrypto` is misleading. The public keys `usr/eml/pwd/c_id/card` are part of the contract.
Impact: The code is harder to read and keeps dead code around.
Recommendation: Rename internal names only, keep the JSON keys, and remove dead code (T16).

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| src/AppManager.js:37-77, 83-128 | Nested callbacks (≥3 levels) with `db.run/get/all(sql, cb)` | Promise helpers + `async/await` |
| package-lock.json:37, 831, 1078, 1573, 1722, 2117 | `@npmcli/move-file`, `glob@7`, `inflight`, `prebuild-install`, `rimraf@3`, `tar@6` (transitive from `sqlite3@5.1.7`) | Supported versions via a future `sqlite3` upgrade or driver change (recorded, out of scope) |

## Refactoring Plan (Phase 3 preview)
Strategy: Full restructuring. This is a God Class (`AppManager` + `utils`), so the whole Node/Express MVC structure gets created and `src/app.js` becomes the composition root. `AppManager.js` and `utils.js` are removed.

Target structure:
```
src/
├── app.js                       # composition root: config, db+seed, DI, middlewares, listen(host, port)
├── config/index.js              # PORT, HOST, ADMIN_TOKEN, PAYMENT_GATEWAY_KEY, DB_*, SMTP_USER from env
├── database/connection.js       # sqlite connection + run/get/all/transaction (Promise)
├── database/seed.js             # schema + initial data
├── errors/HttpError.js
├── models/{user,course,enrollment,payment,auditLog,report}Model.js
├── controllers/{checkout,report,user}Controller.js
├── routes/{checkout,admin,user}Routes.js
├── services/{paymentService,cacheService}.js
├── middlewares/{auth,errorHandler,asyncHandler}.js
├── validators/checkoutValidator.js
└── utils/{password,logger}.js
```

Contract notes:
- `GET /api/admin/financial-report` and `DELETE /api/users/:id` will require `Authorization: Bearer $ADMIN_TOKEN`. Anonymous requests, invalid tokens, or a server started without `ADMIN_TOKEN` get **401**. With a valid token, the status and format stay the same as the baseline.
- The `DELETE /api/users/:id` message, which describes the defect itself, is corrected because enrollments and payments are now removed in a transaction. It stays 200 and plain text.
- A `card` (or other field) with the wrong type now gets 400 "Bad Request" instead of crashing the process.
- When `pwd` is missing, the user gets a random password instead of `"123456"`. The response does not change.
- The server binds to `127.0.0.1` by default (`HOST` is configurable). The port stays 3000 and the command stays `npm start`.
- Error responses keep the same texts and statuses (plain text).

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
