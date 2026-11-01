================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js v20.20.2; no `engines` field)
Framework:     Express ^4.18.2 (4.22.1 installed)
Dependencies:  sqlite3 ^5.1.6 (5.1.7 installed); nothing else (no CORS, ORM, validation or logger)
Database:      SQLite, raw driver with callbacks (`sqlite3`), **in memory** (`:memory:`), so state resets on every boot
Domain:        LMS / course platform with checkout (users, courses, enrollments, payments, audit_logs)
Architecture:  God Class: `AppManager` mixes DB connection, schema, seed, route registration, payment rules, auditing and caching in one class; `utils.js` mixes config, secrets, global state, "crypto" and logging
Entry point:   src/app.js (run: `npm start` → `node src/app.js`, listen on port 3000 with no host, so all interfaces)
Source files:  3 files analyzed (+ package.json, README.md, api.http) | ~180 lines of code
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 routes (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
Aux scripts:   none (the seed runs at boot inside `AppManager.initDb`)
================================

**Endpoint inventory**
| Method | Path | Handler | Inputs / status codes |
|---|---|---|---|
| POST | /api/checkout | src/AppManager.js:28-78 | body `usr`, `eml`, `c_id`, `card` required (`pwd` optional) → 200 `{msg, enrollment_id}`; 400 "Bad Request"; 404 "Curso não encontrado"; 400 "Pagamento recusado" (card not starting with "4"); 500 text |
| GET | /api/admin/financial-report | src/AppManager.js:80-129 | admin → 200 `[{course, revenue, students:[{student, paid}]}]`; 500 "Erro DB" |
| DELETE | /api/users/:id | src/AppManager.js:131-137 | admin/destructive → always 200 text |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 20) + Express 4 (SQLite in memory, sqlite3 driver)
Files:   3 analyzed | ~180 lines of code
Architecture: God Class

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 6 | LOW: 4  (Total: 19)

## Findings

### #1 [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: src/utils.js:2-6
Description: The `config` object holds production credentials as literals: `dbUser: "admi***"`, `dbPass: "senh***"`, `paymentGatewayKey: "pk_l***"` (a live-key prefix), `smtpUser: "no-r***"`. The port is also fixed (`port: 3000`) and `process.env` is never read.
Impact: Anyone with access to the repository gets the database password and the payment gateway key. Rotating them means editing code and redeploying, and the secrets stay in git history.
Recommendation: Move config to `src/config/index.js`, reading `process.env` (`PAYMENT_GATEWAY_KEY`, `DB_USER`, `DB_PASS`, `SMTP_USER`, `PORT`, `HOST`) with no real secret as a default (T01) → Config layer.

### #2 [CRITICAL] Sensitive Data Exposure, card number and key in the log (AP-03)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` writes the full card number and the payment gateway key to stdout on every checkout.
Impact: The card PAN and the key end up in log files and log aggregators (a PCI-DSS violation). Anyone with log access can reuse both.
Recommendation: Log through a logger with the card masked (last 4 digits only) and never log the key. Put payment processing in `services/paymentService.js` (T03, T13).

### #3 [CRITICAL] Insecure Password Storage / Weak Default Password (AP-03)
File: src/utils.js:17-23; src/AppManager.js:18, 68
Description: `badCrypto` is not a hash. It repeats the first 2 characters of the password's base64 10,000 times and keeps the first 10, so it is reversible and full of collisions (every password that starts the same way gets the same "hash"). The seed stores the password `'123'` in plain text (`:18`). When `pwd` is missing, checkout assigns the fixed password `"123456"` (`:68`).
Impact: Stored credentials can be recovered right away. Every user created without `pwd` shares a known password.
Recommendation: Hash with `crypto.scrypt` plus a random salt in `utils/password.js`. Without `pwd`, generate a random password instead of a fixed default. Hash the seed password too (T03) → Model/utils.

### #4 [CRITICAL] Sensitive Endpoint without Authentication/Authorization (AP-04)
File: src/AppManager.js:80, 131
Description: `GET /api/admin/financial-report` (revenue per course, student names and amounts paid) and `DELETE /api/users/:id` (destructive) have no middleware or credential check.
Impact: Any anonymous client can see financial and personal data and delete any user.
Recommendation: Add `middlewares/auth.js` (`requireAdmin`) driven by `ADMIN_TOKEN` (the `Authorization: Bearer <token>` header). If the variable is unset, keep the current behavior and log a warning at boot (T04) → Middlewares + Routes.

### #5 [CRITICAL] God Class / God File (AP-05)
File: src/AppManager.js:4-139; src/utils.js:1-25
Description: `AppManager` creates the connection (`:7`), defines the schema and seed (`:10-23`) and registers the 3 routes with SQL, payment rules, auditing and caching inline (`:25-138`). `utils.js` exports config, secrets, global state, fake crypto and logging all together.
Impact: Nothing can be tested in isolation. Any change touches the same class, and the domains (checkout, report, users) are tangled together.
Recommendation: Split into config / database / models / services / controllers / routes / middlewares. `app.js` becomes the composition root (T05, T07).

### #6 [HIGH] Insecure Runtime Configuration (AP-06)
File: src/app.js:5-12
Description: `app.listen(config.port)` has no host, so it binds every interface (`0.0.0.0`/`::`). There is no error middleware and `NODE_ENV` is never set, so Express's default handler sends the **stack trace** to the client (for example, on malformed JSON in the body, or the `TypeError` from `cc.startsWith` when `card` is not a string).
Impact: The service is exposed on the network by default, and internal paths and code details leak in error responses.
Recommendation: `HOST` defaults to `127.0.0.1` and `PORT` defaults to 3000, both from config. Add a central error middleware that never returns the stack (T01, T10).

### #7 [HIGH] Multi-step Operations without a Transaction / Referential Integrity (AP-08)
File: src/AppManager.js:50-61, 66-72, 133-135
Description: Checkout writes `users` → `enrollments` → `payments` → `audit_logs` in chained callbacks with no `BEGIN/COMMIT/ROLLBACK`. A failure halfway leaves an enrollment without a payment. The user is created **before** the payment is approved, so a declined checkout still persists the user. `DELETE FROM users` leaves orphaned enrollments and payments, and the response itself admits the data is "dirty".
Impact: The database becomes inconsistent: enrollments without payment, and orphan records showing up as "Unknown" in the financial report.
Recommendation: Approve the payment before writing anything. Run checkout and the delete cascade (payments → enrollments → user) inside `withTransaction` (T06) → Models/Controller.

### #8 [HIGH] Business Logic in the Route Layer (Fat Route) (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: The checkout handler (50 lines) validates input, looks up the course, creates the user, hashes the password, decides the payment, enrolls, records payment and audit, writes the cache and formats the response. The report handler builds the aggregation with manual counters.
Impact: The business rules cannot be reused or tested, and the routes cannot change without touching domain logic.
Recommendation: Thin routes → `checkoutController`/`reportController`/`userController` orchestrating models and services (T05).

### #9 [HIGH] Tight Coupling / Global Mutable State / No DI (AP-09)
File: src/utils.js:9-10, 25; src/AppManager.js:2, 7
Description: `globalCache` and `totalRevenue` are module-level mutable state that gets exported (`totalRevenue` is exported as a primitive copy, imported in `AppManager.js:2` and never used). The class creates its own `new sqlite3.Database(':memory:')` in the constructor and imports `config` directly.
Impact: The database and cache cannot be swapped in tests, and shared state is invisible.
Recommendation: Create the connection and services in `app.js` and inject them through factory functions (`createCourseModel(db)`, `createCheckoutController({...})`). Make the cache an injected service (T07).

### #10 [MEDIUM] N+1 Query (AP-11)
File: src/AppManager.js:83-128 (92, 104, 106)
Description: The financial report runs 1 query for courses, then 1 for enrollments per course, then 2 per enrollment (user and payment), with `coursesPending--`/`enrPending--` counters to know when to respond.
Impact: 1 + C + 2E queries per request, and response order is nondeterministic.
Recommendation: A single query with `LEFT JOIN` across courses/enrollments/users/payments, aggregated in the model (T09).

### #11 [MEDIUM] Deprecated API / Legacy Async Pattern (AP-10)
File: src/AppManager.js:37-77, 83-128
Description: Callback hell: 5 levels in checkout (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`) and 4 in the report, using the callback-based sqlite3 API with no Promises. The installed tree has deprecated transitive packages (see table).
Impact: Error flow is hard to follow (several callbacks ignore `err`), and the code is fragile to change.
Recommendation: `database/connection.js` with Promise helpers (`run/get/all`) and `async/await` throughout (T08).

### #12 [MEDIUM] Decentralized Error Handling / Inconsistent Responses (AP-12)
File: src/AppManager.js:38, 41, 51, 55, 57, 70, 84, 92-93, 104, 106, 133
Description: Each callback has its own `res.status(500).send("...")` with a different message. Database errors are treated as "not found" (`:38`, `err || !course` → 404). Many callbacks ignore `err` (`:57`, `:104`, `:106`, `:133`). At `:92-93`, an error leaves `enrollments` as `undefined` and `.length` crashes the process. There is no `(err, req, res, next)` middleware.
Impact: Failures are silent or crash the server, and clients get inconsistent formats.
Recommendation: Domain errors (`HttpError` with status and the original message), an `asyncHandler` and a single `middlewares/errorHandler.js` (T10).

### #13 [MEDIUM] Missing or Scattered Input Validation (AP-15)
File: src/AppManager.js:29-35, 46, 132
Description: Only truthiness is checked (`!u || !e || !cid || !cc`). Types are not validated: `card` sent as a number makes `cc.startsWith` throw a `TypeError` → 500 with a stack. `pwd` is never validated, and `:id` is used without any checks.
Impact: Malformed input causes crashes and 500s instead of 400s.
Recommendation: `validators/checkoutValidator.js` with presence and type checks (strings), called from the controller (T12).

### #14 [MEDIUM] Misplaced Responsibility (AP-14)
File: src/AppManager.js:18-21, 45-46, 59
Description: The sample data seed lives in the application's main class. Payment-gateway simulation (`cc.startsWith("4")`) and the cache side effect (`logAndCache`) sit in the middle of the HTTP handler.
Impact: Production code is mixed with fixtures and integrations, so the payment gateway cannot be swapped.
Recommendation: Schema and seed go to `database/seed.js`, payment to `services/paymentService.js`, cache to `services/cacheService.js` (T05, T07).

### #15 [MEDIUM] Duplicated Logic (AP-13)
File: src/AppManager.js:95-99, 117-122
Description: The "push courseData → decrement coursesPending → respond if zero" block is copied in two places in the report.
Impact: Fixing one copy and not the other produces a double response or a request that never completes.
Recommendation: The aggregation goes to a single function in the model (it disappears with T09) (T11).

### #16 [LOW] `console.log` as the Logging System (AP-16)
File: src/app.js:13; src/utils.js:13
Description: The boot message and `[LOG] Salvando no cache` use `console.log` directly, with no levels and no logger. (The card log at `:45` is already covered by #2.)
Impact: Log volume and destination cannot be controlled, and nothing is structured.
Recommendation: `utils/logger.js` with levels (`LOG_LEVEL`), injected where needed (T13).

### #17 [LOW] Magic Numbers / Magic Strings (AP-17)
File: src/utils.js:19, 22; src/AppManager.js:21, 46, 48, 68, 108
Description: `10000` and `10` in "crypto", the `"4"` prefix as the approval rule, the `'PAID'`/`'DENIED'` statuses repeated, and the `"123456"` default.
Impact: Business rules are implicit and can diverge between copies.
Recommendation: Named constants (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) in the model/service (T14).

### #18 [LOW] Poor Naming / Non-idiomatic Code / Dead Code (AP-18)
File: src/AppManager.js:2, 26, 29-33; src/utils.js:10, 17, 25
Description: Cryptic variables (`u`, `e`, `p`, `cid`, `cc`), `const self = this` alongside arrow functions, `let` that is never reassigned, a misleading name (`badCrypto`), and the dead export/import of `totalRevenue`. The input keys (`usr`, `eml`, `pwd`, `c_id`, `card`) are the public contract and stay as they are.
Impact: Readability suffers and the code misleads whoever maintains it.
Recommendation: Descriptive internal names, `const`, remove dead code; keep the request keys (T16).

### #19 [LOW] Listing without Pagination (AP-19)
File: src/AppManager.js:83
Description: `SELECT * FROM courses` returns every course (and every enrollment) in the report, with no limit.
Impact: The response grows without bound as the catalog and student base grow.
Recommendation: Optional pagination via `?limit=&offset=`, with the default unchanged (full list) (T15).

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| src/AppManager.js:37-77, 83-128 | Callback-based sqlite3 API (`db.run/get/all(sql, cb)`), nested 4-5 levels deep | Promise wrapper + `async/await` |
| package-lock.json:33, 160, 763, 827, 1074, 1478, 1569, 1718, 2113 | Deprecated transitive packages pulled in by `sqlite3@5.1.7` (`@npmcli/move-file`, `are-we-there-yet`, `gauge`, `glob`, `inflight`, `npmlog`, `prebuild-install`, `rimraf`, `tar`) | Upgrade `sqlite3` when a release drops them, or use `node:sqlite` (Node ≥22.5); out of scope here because it would change a dependency or the runtime |

No deprecated Express API was found (`express.json()` is already in use; no `body-parser`, `req.param()` or `res.send(status)`).

## Refactoring Plan (Phase 3 preview)
Strategy: Full restructuring. The project is a God Class: every responsibility lives in `AppManager.js` and `utils.js`. Both files are removed, and `src/app.js` becomes the composition root (still started by `npm start`).
Target structure:
```
src/
├── app.js                       # composition root: config, db, seed, DI, routes, error handler, listen
├── config/index.js              # env: PORT=3000, HOST=127.0.0.1, ADMIN_TOKEN, PAYMENT_GATEWAY_KEY, DB_*, SMTP_USER, LOG_LEVEL
├── database/
│   ├── connection.js            # sqlite3 :memory: + run/get/all/withTransaction (Promise)
│   └── seed.js                  # schema + initial data (seed password hashed)
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   ├── enrollmentModel.js
│   ├── paymentModel.js
│   ├── auditLogModel.js
│   └── reportModel.js           # financial report with a single JOIN
├── services/
│   ├── paymentService.js        # approval simulation, masked log
│   └── cacheService.js          # injected cache (replaces globalCache)
├── controllers/
│   ├── checkoutController.js
│   ├── reportController.js
│   └── userController.js
├── routes/
│   ├── checkoutRoutes.js
│   ├── adminRoutes.js
│   └── userRoutes.js
├── middlewares/
│   ├── errorHandler.js
│   ├── asyncHandler.js
│   └── auth.js                  # requireAdmin (enabled when ADMIN_TOKEN is set)
├── validators/checkoutValidator.js
├── errors/HttpError.js
└── utils/
    ├── password.js              # scrypt + salt
    └── logger.js
```
Contract notes:
- Routes, methods, success status codes, response formats (JSON on success, plain text on errors, with the same messages), the input keys and `npm start` on port 3000 all stay the same.
- **Default host is now `127.0.0.1`** (`HOST` env var to expose it).
- `DELETE /api/users/:id`: deletes the user's enrollments and payments in a transaction, and the message changes to "Usuário deletado" (same status 200, same text type). As a result, the financial report stops listing a deleted user's enrollments.
- Checkout: a declined payment no longer persists the user. Without `pwd`, a random password is generated instead of `"123456"`. Passwords are stored with scrypt.
- Invalid input types (e.g. `card` not a string) and malformed JSON return 400 "Bad Request" instead of 500 with a stack trace. Unexpected errors return 500 text with no stack.
- Admin routes: authentication via `ADMIN_TOKEN` (`Authorization: Bearer`). When it is unset, the routes stay open and a warning is logged.
- Financial report: deterministic order (by course id / enrollment id); optional pagination via `limit`/`offset`.

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]