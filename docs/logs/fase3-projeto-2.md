================================
PHASE 3: REFACTORING COMPLETE
================================

The 3-file God Class is now a layered MVC app. All 16 findings are fixed and every validation check passed, including the auth checks with and without `ADMIN_TOKEN` set.

## New Project Structure
```
src/
├── app.js                          # composition root (DI, middlewares, listen host:port)
├── config/index.js
├── database/{connection.js, seed.js}
├── errors/HttpError.js
├── models/{userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, reportModel}.js
├── controllers/{checkoutController, reportController, userController}.js
├── routes/{checkoutRoutes, adminRoutes, userRoutes}.js
├── services/{paymentService, cacheService}.js
├── middlewares/{auth, errorHandler, asyncHandler}.js
├── validators/checkoutValidator.js
└── utils/{password, logger}.js
```
I removed `src/AppManager.js` and `src/utils.js`. That leaves 25 files and about 537 lines. I also updated `README.md` and `api.http`, which now sends the `Authorization` header to the admin routes.

## Changes by finding
#1 [CRITICAL] Hardcoded secrets → the literals are gone. `PAYMENT_GATEWAY_KEY` and `ADMIN_TOKEN` come from env with no default. A missing gateway key puts the gateway in simulated mode. The unused `dbUser`/`dbPass`/`smtpUser` were removed (`config/index.js`).
#2 [CRITICAL] Sensitive data / weak password storage → the card is logged masked (`****4444`) and the key is never logged. Passwords use `scrypt` with a salt, and the seed user is hashed too. A missing `pwd` now gets a random password instead of `"123456"` (`utils/password.js`, `services/paymentService.js`, `database/seed.js`).
#3 [CRITICAL] Endpoints without auth → `requireAdmin` (fail-closed, constant-time comparison) now protects `GET /api/admin/financial-report` and `DELETE /api/users/:id` (`middlewares/auth.js`, `routes/*`).
#4 [CRITICAL] God Class → split into config / database / models / controllers / routes / services / middlewares. `app.js` is now the composition root.
#5 [HIGH] Insecure runtime config → `app.listen(port, host)` with `HOST` defaulting to `127.0.0.1` and `PORT` defaulting to `3000` from env.
#6 [HIGH] No transaction → checkout (user + enrollment + payment + audit) runs in a single `BEGIN IMMEDIATE…COMMIT/ROLLBACK`. DELETE removes payments → enrollments → user atomically. Transactions are queued on the shared connection (`database/connection.js`, controllers).
#7 [HIGH] Fat route → the routes are 3 lines each and the flow lives in the controllers.
#8 [HIGH] Global state / no DI → factories receive `db`, models and services. `globalCache` became `cacheService` (one instance per app), and `totalRevenue` was removed.
#9 [MEDIUM] Missing validation → `checkoutValidator` checks types (strings, a positive integer `c_id`, `pwd` as an optional string) and returns 400 "Bad Request". A numeric `card` no longer kills the process.
#10 [MEDIUM] Non-centralized errors → `HttpError` + `errorHandler` + `asyncHandler`. Errors stay plain text with the same messages and statuses, and invalid JSON → 400.
#11 [MEDIUM] N+1 → the report is one `LEFT JOIN` query (`models/reportModel.js`), aggregated in the controller.
#12 [MEDIUM] Callback hell → Promise helpers plus `async/await` everywhere. The deprecated transitive dependencies from `sqlite3@5.1.7` were **not** changed (they need a driver upgrade; out of scope).
#13 [MEDIUM] Misplaced responsibility → the schema and seed moved to `database/seed.js` and the cache moved to `services/cacheService.js`.
#14 [LOW] console.log → a leveled logger (`utils/logger.js`).
#15 [LOW] Magic numbers/strings → `PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`, `VISIBLE_CARD_DIGITS`, `SALT_BYTES`, `DEFAULT_PORT`.
#16 [LOW] Naming / dead code → clear internal names (`name`, `email`, `courseId`, `card`), no more `self = this` or unused imports, and `badCrypto` was removed. The public keys `usr/eml/pwd/c_id/card` are unchanged.

## Contract notes
- **Admin routes:** `GET /api/admin/financial-report` and `DELETE /api/users/:id` now require `Authorization: Bearer $ADMIN_TOKEN`. Without it, or with a wrong token, they return 401 `{"error":"Não autorizado"}`. They also return 401 when the server starts without `ADMIN_TOKEN`. With a valid token, the status and format are the same as before.
- **DELETE message:** it no longer says the data was left dirty. It is now "Usuário deletado, junto com suas matrículas e pagamentos." (still 200, plain text). Enrollments and payments are actually removed now, so the report no longer shows "Unknown" students or revenue from deleted users.
- **Denied payments:** a denied checkout no longer creates the user in the database (the payment is decided before any write). It still returns 400 "Pagamento recusado".
- **Wrong field types:** fields with the wrong type (e.g. a numeric `card`) get 400 "Bad Request". Before, the process crashed.
- **Unexpected DB errors:** these get 500 "Erro interno do servidor". Before, the text varied by step and some were wrongly 404.
- **Missing `pwd`:** the user gets a random password instead of `"123456"`.
- **Default bind:** the server binds to `127.0.0.1` by default (`HOST` can change it).
- **Report order:** courses come by id and students by enrollment, deterministically. Before, the order depended on the callbacks.

## Validation
  ✓ Application boots without errors (`npm start`, log: `Frankenstein LMS rodando em http://127.0.0.1:3000`, no stack traces)
  ✓ All endpoints respond correctly (11/11 requests match the baseline: same status and the same body type and top-level keys; only the intentional differences above)
  ✓ Sensitive endpoints deny anonymous access (2 endpoints: 401 without a token, 401 with an invalid token, 401 with the credential unset (no header, old token, empty Bearer), 200 with a valid token)
  ✓ Zero anti-patterns remaining from the report. The greps find no secrets, `console.*`, SQL interpolation, `badCrypto`/`123456`/global state, or SQL outside models/database. The one exception is #12's deprecated transitive dependencies of `sqlite3`, which are recorded and not fixed.
  ✓ MVC checklist (04-mvc-guidelines §7)

Notes on the run:
- **Your Next.js server:** you have a Next.js dev server (`next-server`, running since Nov 3) listening on `*:3000`. I didn't touch it. Tests were only counted after the app's boot log appeared, and `lsof` confirmed `node` on `127.0.0.1:3000`.
- **First attempt:** the first boot failed on a leftover `verifyPassword` export. I fixed it and re-ran the full validation, which is what the results above show.
- **Cleanup:** all processes I started were stopped. No database files were needed because the DB is in memory, and no files were created in the project beyond the source code. Logs, `baseline.txt`, `after.txt` and `auth.txt` are in a `mktemp -d` directory outside the project.

## How to run
```bash
npm install
ADMIN_TOKEN=$(openssl rand -hex 16) npm start     # http://127.0.0.1:3000
```
Environment variables: `ADMIN_TOKEN` (**required** for `/api/admin/financial-report` and `DELETE /api/users/:id`; without it those routes return 401), `PORT` (3000), `HOST` (127.0.0.1), `PAYMENT_GATEWAY_KEY` (missing → simulated gateway), `DB_FILE` (`:memory:`), `LOG_LEVEL` (`info`).
================================

Nothing has been committed. Git is up to you.
