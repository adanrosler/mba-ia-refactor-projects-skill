# 01 — Análise de Projeto (Fase 1)

Heurísticas para descobrir **o que** é o projeto antes de auditá-lo. Tudo aqui é leitura: nenhuma
alteração de arquivo acontece na Fase 1.

## 1. Escopo de leitura

Considere **somente** o diretório atual (raiz do projeto). Ignore sempre:

```
.git/  .claude/  node_modules/  .venv/  venv/  env/  __pycache__/  dist/  build/
instance/  coverage/  *.db  *.sqlite*  *.lock  package-lock.json  *.pyc  *.log
```

Comandos úteis (adapte ao SO):

```bash
# arquivos-fonte e linhas de código (sem dependências/artefatos)
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.mjs' -o -name '*.cjs' \
  -o -name '*.rb' -o -name '*.go' -o -name '*.java' -o -name '*.php' \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/venv/*' \
  -not -path '*/.claude/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' | sort
# total de linhas
... | xargs wc -l
```

Arquivos vazios (ex.: `__init__.py` com 0 linhas) contam como arquivos do projeto, mas não
precisam ser lidos.

## 2. Linguagem

| Sinal (arquivo de manifesto / extensão dominante) | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `*.py` | Python |
| `package.json` + `*.js`/`*.mjs`/`*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` / `*.ts` | TypeScript (Node.js) |
| `Gemfile`, `*.rb` | Ruby |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java/Kotlin |
| `composer.json` | PHP |

Registre a **versão do runtime** quando houver pista (`engines` no `package.json`,
`python_requires`, `.python-version`, `.nvmrc`) ou consulte o runtime instalado
(`python3 --version`, `node --version`).

## 3. Framework e dependências

Leia o manifesto e confirme pelos imports:

| Dependência / import | Framework | Como as rotas são declaradas |
|---|---|---|
| `flask` / `from flask import Flask` | Flask | `@app.route`, `@bp.route`, `app.add_url_rule`, `Blueprint` |
| `fastapi` | FastAPI | `@app.get/post`, `APIRouter` |
| `django` | Django | `urls.py` → `path()` |
| `express` / `require('express')` | Express | `app.get/post/put/delete`, `express.Router()` |
| `fastify`, `koa`, `@nestjs/core` | Fastify / Koa / NestJS | `fastify.get`, `router.get`, decorators `@Get` |

Liste as dependências relevantes com versão (ex.: `flask==3.1.1`, `express ^4.18.2`). Plugins
como CORS, ORM e validação contam como dependências.

## 4. Banco de dados e persistência

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(...)` | SQLite via driver cru (SQL manual) |
| `flask_sqlalchemy`, `sqlalchemy`, `db.Model` | ORM SQLAlchemy (SQLite/Postgres/MySQL conforme URI) |
| `require('sqlite3')`, `new sqlite3.Database(...)` | SQLite via driver cru com callbacks |
| `':memory:'` na conexão | Banco **em memória** — estado zera a cada boot |
| `pg`, `mysql2`, `psycopg2`, `pymysql` | Postgres / MySQL |
| `mongoose`, `pymongo` | MongoDB |
| `prisma`, `sequelize`, `typeorm`, `knex` | ORM/query builder Node |

Mapeie **tabelas/entidades**: procure `CREATE TABLE`, classes `db.Model`/`Base`,
`__tablename__`, schemas Mongoose. Anote onde está o **seed** (dados iniciais): no boot da
aplicação, num script separado (ex.: um `seed.*` na raiz) ou em migrations.

## 5. Ponto de entrada e execução

Descubra **como o projeto é iniciado hoje** — esse comando precisa continuar funcionando
depois da refatoração.

- Python: arquivo com `if __name__ == "__main__":` chamando `app.run(...)`; `FLASK_APP`;
  `wsgi.py`; `Procfile`; README.
- Node: `scripts.start` e `main` do `package.json`; arquivo que chama `app.listen(...)`.
- Anote **host e porta** (`app.run(host=..., port=...)`, `app.listen(PORT)`, `config.port`).
- Anote **scripts auxiliares** que importam a aplicação (seed, migrations, CLI) — eles também
  precisam continuar funcionando.
- Ambiente de execução: Python → use o venv do projeto se existir (`.venv/` ou `venv/`); se não
  existir, crie `.venv` e instale o `requirements.txt` (somente na Fase 3). Node → se não
  houver `node_modules/`, rode `npm install` (somente na Fase 3).

## 6. Inventário de endpoints

Extraia **todas** as rotas (método + caminho + handler + arquivo:linha). Ele é a base da
validação da Fase 3.

```bash
# Flask
grep -rnE "@[a-zA-Z_]+\.route\(|add_url_rule\(" --include='*.py' .
# Express
grep -rnE "(app|router)\.(get|post|put|patch|delete)\(" --include='*.js' --include='*.ts' .
```

Para cada rota, anote também: campos obrigatórios do corpo (o que a validação exige), códigos
de status que ela pode retornar e se é uma rota "administrativa" (prefixo `admin`, relatórios
financeiros, reset, execução de query).

## 7. Domínio da aplicação

Infira o domínio pelos **substantivos** dominantes: nomes de tabelas/entidades, prefixos de
rota e mensagens. Exemplos de leitura:

| Entidades encontradas | Domínio provável |
|---|---|
| produtos/products, pedidos/orders, carrinho, estoque | E-commerce |
| courses, enrollments, payments, checkout | LMS / plataforma de cursos com checkout |
| tasks, categories, users, reports, due_date | Task manager / produtividade |
| accounts, transactions, balance | Financeiro |
| posts, comments, authors, tags | Blog / CMS |
| patients, appointments, doctors | Saúde / agendamento |
| rooms, reservations, guests | Reservas / hotelaria |

Descreva em uma linha: `Domínio: <tipo> (<entidades principais>)`.

## 8. Classificação da arquitetura atual

| Classificação | Sinais | Estratégia na Fase 3 |
|---|---|---|
| **Monolito desestruturado** | 1–5 arquivos; rotas, SQL e regra de negócio no mesmo arquivo/classe; nenhum diretório de camada | Reestruturação completa para MVC |
| **God Class** | Uma classe/arquivo com rotas + acesso a dados + regras + seed | Decompor a classe em camadas |
| **Parcialmente em camadas** | Já existem `models/`, `routes/`, `services/`, `utils/`, mas rotas contêm regra de negócio, há duplicação, segurança fraca | Melhoria incremental: manter o que está certo, criar a camada faltante (normalmente `controllers/`), mover lógica |
| **Em camadas (MVC/Clean)** | Rotas finas, controllers/services, models isolados, config externa | Apenas correções pontuais |

Para decidir, responda: onde está o SQL/ORM? Onde está a regra de negócio? Onde está o
roteamento? Quantos desses três aparecem no mesmo arquivo?

## 9. Saída obrigatória da Fase 1

Imprima exatamente neste formato (valores reais do projeto):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Dependencies:  <demais dependências relevantes>
Database:      <banco + forma de acesso (driver cru / ORM) + arquivo/memória>
Domain:        <domínio (entidades principais)>
Architecture:  <classificação> — <1 frase justificando>
Entry point:   <arquivo> (run: <comando>, host:porta)
Source files:  <N> files analyzed | ~<L> lines of code
DB tables:     <tabelas/entidades>
Endpoints:     <N> routes (<lista curta METHOD /path>)
Aux scripts:   <seed/migrations/etc. ou "none">
================================
```
