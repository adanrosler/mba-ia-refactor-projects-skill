================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
package.json                      # unchanged ("start": "node src/app.js")
README.md                         # env vars documented
api.http
src/
├── app.js                        # composition root: config, db, seed, DI, routes, error handler, listen
├── config/index.js
├── database/
│   ├── connection.js             # sqlite3 + Promise helpers + queued withTransaction
│   └── seed.js                   # schema + seed (password hashed)
├── models/
│   ├── userModel.js  courseModel.js  enrollmentModel.js
│   ├── paymentModel.js           # PAYMENT_STATUS
│   ├── auditLogModel.js
│   └── reportModel.js            # financial report with a single LEFT JOIN
├── services/
│   ├── paymentService.js         # gateway simulation, masked card
│   └── cacheService.js           # injected Map (replaces globalCache)
├── controllers/
│   ├── checkoutController.js  reportController.js  userController.js
├── routes/
│   ├── checkoutRoutes.js  adminRoutes.js  userRoutes.js
├── middlewares/
│   ├── auth.js  errorHandler.js  asyncHandler.js
├── validators/
│   ├── checkoutValidator.js  paginationValidator.js
├── errors/HttpError.js
└── utils/
    ├── logger.js  password.js
```
Removed: `src/AppManager.js`, `src/utils.js`.

## Changes by finding
- #1 [CRITICAL] Hardcoded credentials (AP-01) → The secrets are gone from the code. `config/index.js` reads `PAYMENT_GATEWAY_KEY`, `ADMIN_TOKEN`, `PORT`, `HOST`, `DATABASE_FILE` and `LOG_LEVEL` from the environment, with no real defaults. `dbUser`, `dbPass` and `smtpUser` were never used anywhere, so I dropped them. (config/index.js)
- #2 [CRITICAL] Card number and key in the log (AP-03) → The log now shows only `****4444` and never the key. (services/paymentService.js)
- #3 [CRITICAL] Insecure password storage (AP-03) → `badCrypto` is replaced by scrypt with a random salt. A missing `pwd` now gets a random password instead of `"123456"`, and the seed password is hashed. (utils/password.js, controllers/checkoutController.js, database/seed.js)
- #4 [CRITICAL] Endpoints without auth (AP-04) → `requireAdmin` (constant-time comparison) now guards the report and the DELETE route. It only enforces when `ADMIN_TOKEN` is set; otherwise a warning is logged at boot. (middlewares/auth.js, routes/adminRoutes.js, routes/userRoutes.js)
- #5 [CRITICAL] God Class (AP-05) → `AppManager` and `utils` are split into config, database, models, services, controllers, routes and middlewares. (all of `src/`)
- #6 [HIGH] Insecure runtime config (AP-06) → Default bind is `127.0.0.1`, and a central error handler means stack traces never reach the client. (config/index.js, app.js, middlewares/errorHandler.js)
- #7 [HIGH] No transactions (AP-08) → The payment is approved before anything is written. Checkout (user, enrollment, payment, audit) and the delete cascade (payments, enrollments, user) each run inside `withTransaction`. (database/connection.js, controllers/checkoutController.js, controllers/userController.js)
- #8 [HIGH] Fat Route (AP-07) → Routes are 3-4 lines each, and the flow lives in the controllers. (routes/*, controllers/*)
- #9 [HIGH] Global state / no DI (AP-09) → Everything is built in `app.js` and injected through factory functions; the cache is a service; `totalRevenue` is removed. (app.js, services/cacheService.js)
- #10 [MEDIUM] N+1 (AP-11) → One query with `LEFT JOIN`, grouped with a `Map`. The `'Unknown'` placeholder and `paid: 0` default are kept. (models/reportModel.js)
- #11 [MEDIUM] Callback hell (AP-10) → Promise helpers plus `async/await` throughout. (database/connection.js)
- #12 [MEDIUM] Decentralized errors (AP-12) → `HttpError` carries the original messages and statuses, `asyncHandler` forwards errors, and one middleware handles them. No `err` is ignored anymore, and boot failures are logged with exit code 1. (errors/, middlewares/)
- #13 [MEDIUM] Missing validation (AP-15) → Presence and string-type checks on `usr`, `eml`, `card` and `pwd`; `limit`/`offset` are validated too. (validators/*)
- #14 [MEDIUM] Misplaced responsibility (AP-14) → The seed moved to `database/seed.js`, and payment and cache moved to `services/`.
- #15 [MEDIUM] Duplicated logic (AP-13) → The aggregation now exists once, in `buildReport`. (models/reportModel.js)
- #16 [LOW] `console.log` (AP-16) → Leveled logger; `console.*` only appears inside `utils/logger.js`.
- #17 [LOW] Magic numbers (AP-17) → Named constants: `PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`, `ACTIVE`, `UNKNOWN_STUDENT`, `SALT_BYTES`, `KEY_LENGTH`.
- #18 [LOW] Poor naming / dead code (AP-18) → Descriptive internal names and `const`; `self = this`, `badCrypto` and `totalRevenue` are gone. The public keys `usr`/`eml`/`pwd`/`c_id`/`card` are unchanged.
- #19 [LOW] No pagination (AP-19) → Optional `?limit=&offset=` on the report; without them the response is the full list, as before. (validators/paginationValidator.js, models/reportModel.js)

## Contract notes
- **Default host is `127.0.0.1`** (was all interfaces). Use `HOST=0.0.0.0` to expose it.
- **`DELETE /api/users/:id`** now deletes the user's enrollments and payments too, and replies "Usuário deletado" (still 200, still text). So the financial report no longer lists deleted users as "Unknown" or counts their revenue.
- **Financial report order** is now fixed: by course id, then enrollment id. The original order depended on which callback finished first (it returned Docker before Clean Architecture).
- **A declined checkout no longer creates the user.** Without `pwd`, a random password is generated. Passwords are stored as `scrypt$salt$hash`.
- **A `card` that is not a string returns 400 "Bad Request".** In the original this threw an uncaught `TypeError` that **crashed the whole process**: every request after it got no response.
- **Malformed JSON or a missing body returns 400 "Bad Request" as text**, instead of Express's HTML page with a stack trace.
- **Internal DB failures return 500 "Erro interno do servidor"** instead of the old per-route messages ("Erro DB", "Erro Matrícula", …).
- **When `ADMIN_TOKEN` is set**, the admin routes and DELETE return 401 "Não autorizado" without `Authorization: Bearer <token>`. When it is unset, they behave as before.

## Validation
  ✓ Application boots without errors (`npm start`: only the two expected warnings about `PAYMENT_GATEWAY_KEY` and `ADMIN_TOKEN` being unset)
  ✓ All endpoints respond correctly (11/14 requests match the baseline on status and body shape; the other 3 are the intentional fixes above: the HTML stack trace became a text 400, and the request that used to crash the server now gets 400 while the next one gets 200. The bodies that differ are only the report order and the cascade delete.) I also checked `ADMIN_TOKEN` (401 without the token or with a wrong one, 200 with the right one), pagination, invalid `limit` (400), a request with no Content-Type (400) and a boot failure (logged, exit 1).
  ✓ Zero anti-patterns remaining from the report. The greps for secrets, `console.`, `badCrypto`/`globalCache`/`self = this`/magic numbers and SQL outside `models/`/`database/` are all clean. One pending item: the deprecated **transitive** packages pulled in by `sqlite3@5.1.7` (`inflight`, `glob`, `tar`, …) are still there, because fixing them means changing the dependency or the Node version.
  ✓ MVC checklist (04-mvc-guidelines §7): all 9 items met.

## How to run
```bash
npm install
npm start          # http://127.0.0.1:3000
# optional: PORT=3000 HOST=127.0.0.1 ADMIN_TOKEN=... PAYMENT_GATEWAY_KEY=... DATABASE_FILE=:memory: LOG_LEVEL=info npm start
```
================================

Every server I started has been stopped, port 3000 is free, and the temp directory is deleted. No database files or logs were left in the project, and I made no commits. While working I noticed `../reports/audit-project-2.md` and `audit-project-3.md` showing up as untracked files outside this project. I didn't create or touch them.