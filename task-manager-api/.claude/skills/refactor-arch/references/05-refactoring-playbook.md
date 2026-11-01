# 05 — Playbook de Refatoração (Fase 3)

Transformações concretas, cada uma ligada a anti-patterns do catálogo. Os exemplos são
genéricos (entidades fictícias `Item`, `Account`, `Order`); adapte nomes ao projeto.

**Ordem recomendada de aplicação:**
1. T01 Config → 2. T07 Composition root/DI → 3. T05 Separação em camadas →
4. T02 Queries parametrizadas → 5. T03 Senhas/dados sensíveis → 6. T06 Transações →
7. T09 N+1 → 8. T08 Deprecated → 9. T10 Erros centralizados → 10. T11/T12 Duplicação e
validação → 11. T04 Auth → 12. T13–T16 Qualidade.

Regra geral: **prefira biblioteca padrão e dependências já instaladas** (ex.: `werkzeug.security`
e `itsdangerous` já vêm com Flask; `crypto` já vem com Node). Só adicione dependência nova se não
houver alternativa — e então atualize o manifesto e instale.

---

## T01 — Extrair configuração para módulo de config (AP-01, AP-06)

**Python — antes**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "valor-fixo-no-codigo"
app.config["DEBUG"] = True
...
app.run(host="0.0.0.0", port=8000, debug=True)
```
**Python — depois**
```python
# config/settings.py
import logging, os, secrets

logger = logging.getLogger(__name__)

def _bool(value, default=False):
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("APP_DEBUG"), default=False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "8000"))   # mesma porta do código original
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "app.db")

if "SECRET_KEY" not in os.environ:
    logger.warning("SECRET_KEY não definida; usando chave aleatória (sessões não persistem entre restarts)")

# app.py
from config.settings import Settings
app.config.from_object(Settings)
app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
```

**JS — antes**
```js
const config = { dbPass: "senha-fixa", apiKey: "chave-fixa", port: 8080 };
module.exports = { config };
```
**JS — depois**
```js
// src/config/index.js
const config = Object.freeze({
  port: Number(process.env.PORT) || 8080,          // mesma porta do original
  host: process.env.HOST || '127.0.0.1',
  db: { user: process.env.DB_USER, password: process.env.DB_PASS },
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY, // undefined → modo simulado
  adminToken: process.env.ADMIN_TOKEN,
});
module.exports = config;
```

Endpoints de health/info **não** devem devolver segredos nem config interna: troque
`"secret_key": ...` por nada e derive `debug`/`ambiente` da config real (mantendo as chaves que
não são sensíveis para preservar o contrato).

---

## T02 — Parametrizar queries (AP-02)

**Python — antes**
```python
cursor.execute("SELECT * FROM items WHERE id = " + str(item_id))
cursor.execute("SELECT * FROM accounts WHERE email = '" + email + "' AND pwd = '" + pwd + "'")
query = "SELECT * FROM items WHERE 1=1"
if term:
    query += " AND name LIKE '%" + term + "%'"
```
**Python — depois**
```python
cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
cursor.execute("SELECT * FROM accounts WHERE email = ?", (email,))  # senha verificada por hash (T03)
query, params = "SELECT * FROM items WHERE 1=1", []
if term:
    query += " AND name LIKE ?"
    params.append(f"%{term}%")
cursor.execute(query, params)
```
**JS — antes**
```js
db.all(`SELECT * FROM items WHERE category = '${req.query.cat}'`, cb);
```
**JS — depois**
```js
await db.all('SELECT * FROM items WHERE category = ?', [category]);
```
Nomes de coluna/ordenação dinâmicos: valide contra whitelist (`if (!ALLOWED_SORT.has(col)) ...`).

---

## T03 — Senhas com hash forte e respostas sem dados sensíveis (AP-03)

**Python — antes**
```python
password = hashlib.md5(raw.encode()).hexdigest()          # ou texto puro
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```
**Python — depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    if self.password and self.password.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(self.password, raw)
    # compatibilidade: hash legado → verifica e migra no próximo login
    legacy_ok = self.password == hashlib.md5(raw.encode()).hexdigest()
    if legacy_ok:
        self.set_password(raw)
    return legacy_ok

def to_dict(self):
    return {"id": self.id, "email": self.email}           # sem password/hash
```
Seed com senhas em texto puro → gravar `generate_password_hash(...)` no seed; login passa a
buscar por e-mail e verificar com `check_password_hash`.

**JS — antes**
```js
function weakHash(pwd) { return Buffer.from(pwd).toString('base64').substring(0, 10); }
const hash = weakHash(body.pwd || 'senha-padrao');
console.log(`Cobrando cartão ${card} com chave ${config.apiKey}`);
```
**JS — depois**
```js
// src/utils/password.js
const crypto = require('crypto');
function hashPassword(plain) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(plain, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}
function verifyPassword(plain, stored) {
  const [, salt, hash] = stored.split('$');
  const candidate = crypto.scryptSync(plain, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
module.exports = { hashPassword, verifyPassword };

// uso: senha ausente → gera senha aleatória (nunca um default fixo)
const hash = hashPassword(password || crypto.randomBytes(12).toString('hex'));
logger.info('Processando pagamento', { card: maskCard(card) }); // ****1111, nunca a chave
```

---

## T04 — Proteger/desabilitar endpoints sensíveis (AP-04, AP-02)

**Endpoint que executa SQL arbitrário / reset do banco — antes**
```python
@app.route("/admin/run-sql", methods=["POST"])
def run_sql():
    cursor.execute(request.get_json()["sql"])
```
**Depois** — removido da API. Se houver necessidade operacional comprovada, mantenha atrás de
flag desligada por padrão **e** autenticação:
```python
# routes/admin_routes.py
if Settings.ENABLE_ADMIN_TOOLS:          # env ENABLE_ADMIN_TOOLS=true, default False
    admin_bp.add_url_rule("/admin/...", view_func=require_admin(controller.reset), methods=["POST"])
```

**Autorização ativável por configuração (preserva contrato quando não configurada)**

Python:
```python
# middlewares/auth.py
import hmac
from functools import wraps
from flask import request, jsonify, current_app

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = current_app.config.get("ADMIN_TOKEN")
        if token:  # só exige quando configurado
            sent = request.headers.get("Authorization", "").removeprefix("Bearer ")
            if not hmac.compare_digest(sent, token):
                return jsonify({"error": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper
```
JS:
```js
// src/middlewares/auth.js
const crypto = require('crypto');
module.exports = (adminToken) => (req, res, next) => {
  if (!adminToken) return next();                       // modo compatível (warning no boot)
  const sent = (req.get('authorization') || '').replace(/^Bearer /, '');
  const ok = sent.length === adminToken.length &&
    crypto.timingSafeEqual(Buffer.from(sent), Buffer.from(adminToken));
  return ok ? next() : res.status(401).json({ error: 'Não autorizado' });
};
```
**Token falso no login — antes:** `token = "prefixo-" + str(user.id)`
**Depois:** token assinado e com expiração, mantendo a chave `token` na resposta:
```python
from itsdangerous import URLSafeTimedSerializer
def issue_token(user_id):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).dumps({"uid": user_id})
```

---

## T05 — Separar God Class / Fat Route em Model, Controller e View (AP-05, AP-07, AP-14)

**Antes (tudo no handler)**
```python
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    if not data or not data.get("account_id"):
        return jsonify({"error": "account_id obrigatório"}), 400
    total = 0
    for it in data["items"]:
        row = db.execute("SELECT price, stock FROM items WHERE id = ?", (it["id"],)).fetchone()
        if row["stock"] < it["qty"]:
            return jsonify({"error": "Sem estoque"}), 400
        total += row["price"] * it["qty"]
    db.execute("INSERT INTO orders (account_id, total) VALUES (?, ?)", (data["account_id"], total))
    db.commit()
    print("EMAIL: pedido criado")
    return jsonify({"total": total}), 201
```
**Depois**
```python
# models/order_model.py  — dados
class OrderModel:
    def __init__(self, db): self.db = db
    def find_items(self, ids): ...
    def create(self, account_id, items, total): ...   # transação (T06)

# controllers/order_controller.py — fluxo
class OrderController:
    def __init__(self, orders, notifier): self.orders, self.notifier = orders, notifier
    def create(self, data):
        validate_order(data)                                   # T12 → ValidationError
        items = self.orders.find_items([i["id"] for i in data["items"]])
        total = calculate_total(items, data["items"])          # regra de negócio pura
        order_id = self.orders.create(data["account_id"], data["items"], total)
        self.notifier.order_created(order_id)                  # services/
        return {"total": total}

# views/order_routes.py — HTTP
def build_order_routes(controller):
    bp = Blueprint("orders", __name__)
    @bp.post("/orders")
    def create_order():
        return jsonify(controller.create(request.get_json(silent=True))), 201
    return bp
```

**JS — antes (classe "Manager" com tudo)**
```js
class Everything {
  constructor() { this.db = new sqlite3.Database(DB_FILE); }
  init() { /* CREATE TABLE + INSERT seed */ }
  registerRoutes(app) { app.post('/api/orders', (req, res) => { /* SQL + regra + resposta */ }); }
}
```
**JS — depois**
```js
// src/app.js (composition root)
const config = require('./config');
const { createConnection } = require('./database/connection');
const { initSchema, seed } = require('./database/seed');
const createOrderModel = require('./models/orderModel');
const createOrderController = require('./controllers/orderController');
const createOrderRoutes = require('./routes/orderRoutes');
const errorHandler = require('./middlewares/errorHandler');

async function bootstrap() {
  const db = createConnection(config.databaseFile);
  await initSchema(db); await seed(db);
  const orderController = createOrderController({ orders: createOrderModel(db) });
  const app = express();
  app.use(express.json());
  app.use('/api', createOrderRoutes(orderController));
  app.use(errorHandler);
  app.listen(config.port, config.host, () => logger.info(`listening on ${config.port}`));
}
bootstrap();

// src/routes/orderRoutes.js
module.exports = (controller) => {
  const router = express.Router();
  router.post('/orders', asyncHandler(async (req, res) => {
    res.status(201).json(await controller.create(req.body));
  }));
  return router;
};
```

---

## T06 — Envolver operações multi-etapa em transação (AP-08)

**Python (sqlite3) — antes**
```python
cur.execute("INSERT INTO orders ...")
for it in items:
    cur.execute("INSERT INTO order_items ...")
    cur.execute("UPDATE items SET stock = stock - ? WHERE id = ?", ...)
db.commit()
```
**Depois**
```python
try:
    with db:                      # commit automático; rollback em exceção
        cur = db.execute("INSERT INTO orders ...")
        for it in items:
            db.execute("INSERT INTO order_items ...")
            db.execute("UPDATE items SET stock = stock - ? WHERE id = ? AND stock >= ?", ...)
except sqlite3.Error:
    raise
```
**JS — exclusão sem órfãos (antes)**
```js
db.run('DELETE FROM accounts WHERE id = ?', [id], () => res.send('ok'));
```
**Depois**
```js
async function deleteAccount(db, id) {
  await db.run('BEGIN');
  try {
    await db.run('DELETE FROM payments WHERE order_id IN (SELECT id FROM orders WHERE account_id = ?)', [id]);
    await db.run('DELETE FROM orders WHERE account_id = ?', [id]);
    await db.run('DELETE FROM accounts WHERE id = ?', [id]);
    await db.run('COMMIT');
  } catch (err) { await db.run('ROLLBACK'); throw err; }
}
```
SQLAlchemy: as operações já ficam na mesma sessão — faça um único `commit()` no fim do caso de
uso e `rollback()` no handler de erro.

---

## T07 — Composition root e injeção de dependência; eliminar estado global mutável (AP-09, AP-14)

**Python — antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)
    return db_connection
```
**Python — depois**
```python
# models/database.py
import sqlite3
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_schema(get_db())
        seed_if_empty(get_db())      # seed separado do código de domínio
```
**JS — antes**
```js
let cache = {}; let counter = 0;
module.exports = { cache, counter, save(k, v) { cache[k] = v; } };
```
**JS — depois**
```js
// src/services/cacheService.js
module.exports = function createCache() {
  const store = new Map();
  return { set: (k, v) => store.set(k, v), get: (k) => store.get(k) };
};
// criado uma vez no app.js e injetado em quem precisar
```
Serviços com credenciais (e-mail, gateway) recebem a config no construtor; o controller recebe o
serviço pronto.

---

## T08 — Substituir APIs deprecated e padrões legados (AP-10)

**datetime.utcnow (Python ≥3.12)**
```python
# antes
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if task.due < datetime.utcnow(): ...
```
```python
# depois — utils/time.py
from datetime import datetime, timezone

def utcnow():
    """UTC 'naive' — compatível com colunas DateTime sem timezone (SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
if task.due < utcnow(): ...
```
⚠️ Não compare `datetime` *aware* com valores *naive* vindos do banco (gera `TypeError`) e não
mude o formato de `str(datetime)` das respostas — por isso o helper devolve *naive*.

**SQLAlchemy `Query.get`**
```python
user = User.query.get(user_id)          # antes
user = db.session.get(User, user_id)    # depois
```

**Callback hell → async/await (Node)**
```js
// antes
db.get('SELECT * FROM items WHERE id = ?', [id], (err, item) => {
  if (err) return res.status(500).send('Erro');
  db.run('INSERT INTO orders (item_id) VALUES (?)', [id], function (err) {
    if (err) return res.status(500).send('Erro');
    db.run('INSERT INTO logs ...', [], () => res.json({ id: this.lastID }));
  });
});
```
```js
// depois — src/database/connection.js
function promisify(db) {
  return {
    get: (sql, p = []) => new Promise((ok, ko) => db.get(sql, p, (e, row) => (e ? ko(e) : ok(row)))),
    all: (sql, p = []) => new Promise((ok, ko) => db.all(sql, p, (e, rows) => (e ? ko(e) : ok(rows)))),
    run: (sql, p = []) => new Promise((ok, ko) =>
      db.run(sql, p, function (e) { return e ? ko(e) : ok({ lastID: this.lastID, changes: this.changes }); })),
  };
}
// controller
const item = await db.get('SELECT * FROM items WHERE id = ?', [id]);
const { lastID } = await db.run('INSERT INTO orders (item_id) VALUES (?)', [id]);
await db.run('INSERT INTO logs ...', []);
return { id: lastID };
```

**Dependência deprecated**: atualize para a versão suportada **somente** se `npm install`/
`pip install` + boot + validação passarem; caso contrário mantenha e registre no resumo final.

---

## T09 — Eliminar N+1 (AP-11)

**SQL cru — antes**
```python
for order in cursor.execute("SELECT * FROM orders").fetchall():
    items = db.execute("SELECT * FROM order_items WHERE order_id = " + str(order["id"])).fetchall()
    for it in items:
        name = db.execute("SELECT name FROM items WHERE id = ?", (it["item_id"],)).fetchone()
```
**Depois**
```python
rows = db.execute("""
    SELECT o.id AS order_id, o.status, oi.item_id, oi.qty, i.name AS item_name
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN items i ON i.id = oi.item_id
    ORDER BY o.id, oi.id
""").fetchall()
orders = group_rows_by_order(rows)   # monta a mesma estrutura de resposta de antes
```
**SQLAlchemy — antes:** `for t in Task.query.all(): User.query.get(t.user_id)`
**Depois:**
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
# contagens por grupo
counts = dict(db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all())
```
**JS — antes:** `parents.forEach(p => db.all('... WHERE parent_id = ?', [p.id], ...))`
**Depois:** um `SELECT ... LEFT JOIN ... ` e agrupamento em memória com `Map`, preservando
ordem, valores default (ex.: nome ausente → mesmo placeholder do original) e formato.

---

## T10 — Tratamento de erro centralizado (AP-12)

**Python — antes**
```python
def get_item(id):
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Python — depois**
```python
# middlewares/error_handler.py
import logging
from flask import jsonify
logger = logging.getLogger(__name__)

class AppError(Exception):
    status = 400
    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.message, self.payload = message, payload or {}
        if status: self.status = status

class NotFoundError(AppError): status = 404

def register_error_handlers(app, error_key="erro"):   # use a MESMA chave que o projeto já usa
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({error_key: err.message, **err.payload}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado")
        return jsonify({error_key: "Erro interno do servidor"}), 500   # sem str(e)
```
Atenção: `@app.errorhandler(Exception)` também captura `HTTPException` (404 de rota
inexistente, 405). Trate-as antes para manter os status originais:
```python
from werkzeug.exceptions import HTTPException
@app.errorhandler(HTTPException)
def handle_http(err):
    return jsonify({error_key: err.description}), err.code
```
**JS — depois**
```js
// src/middlewares/errorHandler.js
class AppError extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.status).send(err.message); // mesmo tipo de corpo do original
  logger.error(err);
  return res.status(500).json({ error: 'Erro interno do servidor' });
}
module.exports = { AppError, errorHandler };
```
Se o original respondia **texto puro** num erro, o `AppError` desse caso deve continuar
respondendo texto puro com o mesmo status (contrato).

---

## T11 — Extrair lógica duplicada (AP-13)

**Antes (mesma serialização em 3 handlers)**
```python
data = {"id": t.id, "title": t.title, "due": str(t.due) if t.due else None}
data["late"] = bool(t.due and t.due < now and t.status not in ("closed", "archived"))
```
**Depois**
```python
# models/task.py
def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

def to_dict(self, include=()):
    data = {...}
    if "overdue" in include: data["overdue"] = self.is_overdue()
    return data
```
Cada rota chama `to_dict(include=...)` para reproduzir **exatamente** as chaves que devolvia antes.

---

## T12 — Validação de entrada centralizada (AP-15)

**Antes**
```python
data = request.get_json()
if not data.get("name"): ...
if data["priority"] < 1: ...          # quebra se vier string / se data for None
```
**Depois**
```python
# validators/item_validator.py
def validate_item(data, partial=False):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    if not partial and not data.get("name"):
        raise ValidationError("Nome é obrigatório")
    if "priority" in data:
        try:
            p = int(data["priority"])
        except (TypeError, ValueError):
            raise ValidationError("Prioridade inválida")
        if not MIN_PRIORITY <= p <= MAX_PRIORITY:
            raise ValidationError(f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}")
    return data
```
JS: `function validateCheckout(body) { if (!body.name || !body.email) throw new AppError('Bad Request', 400); ... }`
Mantenha as **mesmas mensagens e status** que o código original retornava.

---

## T13 — Logging estruturado no lugar de print/console.log (AP-16)

```python
# antes
print("Item criado: " + str(id))
# depois
import logging
logger = logging.getLogger(__name__)
logger.info("Item criado: id=%s", item_id)
# app.py: logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
```
```js
// antes
console.log(`[LOG] salvando ${key}`);
// depois — src/utils/logger.js
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[process.env.LOG_LEVEL || 'info'];
const log = (lvl) => (...a) => { if (LEVELS[lvl] <= current) console[lvl === 'debug' ? 'log' : lvl](`[${lvl.toUpperCase()}]`, ...a); };
module.exports = { error: log('error'), warn: log('warn'), info: log('info'), debug: log('debug') };
```
Nunca logar senha, token, chave ou cartão completo.

---

## T14 — Nomear magic numbers e strings (AP-17)

```python
# antes
if revenue > 50000: discount = revenue * 0.15
if status not in ["open", "closed", "archived"]: ...
```
```python
# depois — models/constants.py (ou no model da entidade)
DISCOUNT_TIERS = ((50_000, 0.15), (20_000, 0.08))   # (limite, taxa) — ordem decrescente
VALID_STATUSES = ("open", "closed", "archived")

def discount_for(revenue):
    return next((revenue * rate for limit, rate in DISCOUNT_TIERS if revenue > limit), 0)
```
```js
const MAX_RETRIES = 3;  // antes: for (let i = 0; i < 3; i++) retry()
```

---

## T15 — Paginação opcional (AP-19)

Preserva o contrato: sem parâmetros, a resposta é idêntica à original.
```python
def list_items():
    page = request.args.get("page", type=int)
    per_page = min(request.args.get("per_page", default=DEFAULT_PAGE_SIZE, type=int), MAX_PAGE_SIZE)
    query = Item.query.order_by(Item.id)
    if page:
        query = query.limit(per_page).offset((page - 1) * per_page)
    return jsonify([i.to_dict() for i in query.all()]), 200
```
```js
const { page, per_page: perPage = 20 } = req.query;
const sql = page ? 'SELECT * FROM items LIMIT ? OFFSET ?' : 'SELECT * FROM items';
```

---

## T16 — Nomes claros e código idiomático (AP-18)

```js
// antes
let n = req.body.nm; let a = req.body.addr; let q = req.body.qt;
// depois — nomes internos claros; chaves públicas do JSON preservadas
const { nm: customerName, addr: shippingAddress, qt: quantity } = req.body;
```
```python
# antes
if type(tags) == list: ...
def is_admin(self):
    if self.role == "admin":
        return True
    else:
        return False
import os, sys, json        # não usados
# depois
if isinstance(tags, list): ...
def is_admin(self):
    return self.role == ROLE_ADMIN
```
