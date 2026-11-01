# 02 — Catálogo de Anti-patterns (Fase 2)

Cada anti-pattern tem: **ID**, **severidade**, **descrição**, **sinais de detecção** (Python e
JavaScript/TypeScript), **falsos positivos a descartar** e a **transformação** do playbook
(`05-refactoring-playbook.md`) que o corrige.

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falha grave de segurança ou arquitetura: expõe dados sensíveis, permite injeção, ou viola completamente a separação de responsabilidades. |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes (lógica pesada em rotas, acoplamento sem DI, estado global mutável, integridade de dados). |
| **MEDIUM** | Padronização, duplicação, performance moderada (N+1), middlewares/validação inadequados, APIs deprecated. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, logging improvisado, código não idiomático. |

## Regras de uso

1. **Evidência obrigatória**: só registre um finding se conseguir apontar `arquivo:linha`
   (ou intervalo `arquivo:inicio-fim`) **lido no código**. Confira o número da linha antes de
   escrever (`grep -n` ou leitura numerada).
2. **Agrupe ocorrências do mesmo anti-pattern** num único finding listando todas as linhas
   (ex.: `models.x:12, 40-44, 97`) — exceto quando ocorrências em arquivos diferentes tiverem
   impactos diferentes.
3. **Um mesmo trecho pode gerar findings diferentes** se violar anti-patterns diferentes
   (ex.: um endpoint que executa SQL arbitrário sem autenticação → AP-02 e AP-04).
4. **Severidade condicional**: quando o catálogo indica escalonamento, aplique a regra e cite o
   motivo na descrição.
5. **Rodada de APIs deprecated é obrigatória** (AP-10): verifique a tabela de APIs deprecated em
   todo projeto e reporte "nenhuma encontrada" no resumo se for o caso.

---

## CRITICAL

### AP-01 — Hardcoded Credentials / Secrets
**Descrição:** segredos (chave de assinatura, senha de banco, API key, token, senha SMTP) escritos
literalmente no código-fonte.
**Sinais de detecção:**
- Python: `app.config["SECRET_KEY"] = "<literal>"`, `SECRET_KEY = '...'`, `password = '...'`,
  `api_key = '...'`, `smtplib.SMTP(...).login(user, "<literal>")`, URIs com usuário:senha.
- JS: objetos `config = { dbPass: "...", apiKey: "..." }`, `const SECRET = '...'`,
  `jwt.sign(payload, "<literal>")`.
- Regex úteis: `(secret|passw(or)?d|pass|pwd|token|api[_-]?key|private[_-]?key)\s*[:=]\s*['"][^'"]+['"]`,
  prefixos de chaves reais `sk_live_`, `pk_live_`, `AKIA`, `ghp_`.
- Valor de segredo **retornado em resposta HTTP** agrava (ver também AP-03).
**Falsos positivos:** placeholders lidos de ambiente com default vazio; valores em arquivos de
teste/fixtures claramente fictícios; senhas de usuários de seed (registrar em AP-03 se em texto
puro).
**Correção:** T01.

### AP-02 — SQL Injection / Execução de Query Arbitrária
**Descrição:** entrada externa concatenada/interpolada em SQL, ou endpoint que executa SQL
enviado pelo cliente.
**Sinais de detecção:**
- Python: `cursor.execute("... " + var)`, `execute(f"... {var}")`, `"..." % var`,
  `.format(` dentro de `execute`; `text(f"...")` no SQLAlchemy.
- JS: `db.run(\`... ${var}\`)`, `db.query("..." + var)`, `sequelize.query(\`...${x}\`)`.
- Endpoint que lê SQL do corpo (`request.get_json()["sql"]`, `req.body.query`) e chama
  `execute` → sempre CRITICAL, mesmo com "proteção" por prefixo `SELECT`.
- Login com SQL concatenado → destaque: permite bypass de autenticação (`' OR '1'='1`).
**Falsos positivos:** concatenação de **nomes de coluna/ordenação vindos de whitelist fixa**;
placeholders `?`/`%s`/`:name`/`$1` com parâmetros separados; ORM com filtros
(`filter_by`, `where({...})`).
**Correção:** T02 (parametrizar); endpoints de SQL arbitrário: T04 (remover ou desabilitar por
padrão).

### AP-03 — Exposição de Dados Sensíveis / Armazenamento Inseguro de Senha
**Descrição:** senha, hash de senha, segredo, número de cartão ou token aparece em resposta
HTTP ou log; senha armazenada em texto puro, com hash fraco (MD5/SHA1 sem salt) ou criptografia
caseira; senha padrão fraca atribuída automaticamente.
**Sinais de detecção:**
- Serialização de usuário que inclui `senha`/`password`/`pass`/`hash`
  (`to_dict()`, `dict(row)`, `SELECT *` devolvido direto, `res.json(user)`).
- Endpoint de health/info/debug que retorna `secret_key`, `db_path`, variáveis de ambiente.
- Logs: `print(...card...)`, `console.log(\`...${card}...${apiKey}\`)`, log de senha/token.
- Hash fraco: `hashlib.md5(`, `hashlib.sha1(` para senha; `crypto.createHash('md5')`;
  funções caseiras com `base64`, loops, `substring` para "hashear"; comparação
  `senha = '<input>'` no SQL (texto puro).
- Default de senha: `pwd || "<senha fixa>"`, `data.get("password", "...")`.
**Escalonamento:** sempre CRITICAL quando credenciais/cartões saem pela API ou por log; hash
fraco sem exposição também é CRITICAL (credencial recuperável).
**Falsos positivos:** campos chamados `password` em formulários de entrada (request), sem
persistência/retorno.
**Correção:** T03.

### AP-04 — Endpoint Sensível sem Autenticação/Autorização (ou Auth Falsa)
**Descrição:** rotas administrativas, financeiras, destrutivas ou de execução de comandos
acessíveis sem credencial; "tokens" previsíveis que nunca são validados.
**Sinais de detecção:**
- Rotas com prefixo `admin`, `reset`, `query`, `report`, `financial`, `delete` em massa sem
  decorator/middleware de auth (`@login_required`, `@jwt_required`, `requireAuth`,
  `app.use(auth)`).
- Login que retorna `token: '<prefixo-fixo>' + id`, `token = str(user.id)` ou similar, e nenhuma rota
  verifica `Authorization`.
- Exclusão/alteração de qualquer recurso sem checar dono/papel.
**Escalonamento:** CRITICAL quando a rota executa SQL/comandos, apaga dados em massa ou expõe
dados pessoais/financeiros; HIGH quando o problema é só o token falso/sem validação.
**Correção:** T04.

### AP-05 — God Class / God File
**Descrição:** uma classe ou arquivo concentra roteamento, acesso a dados, regras de negócio
(e às vezes seed/config) de vários domínios.
**Sinais de detecção:**
- Arquivo/classe com >150–200 linhas misturando: declaração de rotas **e** SQL/ORM **e**
  cálculos de negócio.
- Classe "*Manager"/"App"/"Utils" com métodos de inicialização de banco, registro de rotas e regras de negócio na mesma classe.
- Um único módulo de "models" com funções de 3+ domínios (ex.: catálogo, clientes, vendas…),
  contendo SQL **e** regra de negócio (cálculo de total, desconto, baixa de estoque).
- Arquivo "utils" que exporta config + estado global + criptografia + cache.
**Falsos positivos:** arquivos grandes, mas coesos (um só domínio e uma só camada).
**Correção:** T05 (+ T07).

---

## HIGH

### AP-06 — Configuração Insegura de Execução
**Descrição:** modo debug ligado de forma fixa, servidor exposto em todas as interfaces,
ambiente/variáveis de execução fixos no código.
**Sinais de detecção:**
- Python: `app.run(debug=True)`, `app.config["DEBUG"] = True`, `host="0.0.0.0"`,
  `FLASK_DEBUG=1` fixo.
- JS: `app.listen(PORT, '0.0.0.0')`, stack traces enviados ao cliente (`res.send(err.stack)`),
  `NODE_ENV` ignorado.
- Endpoint que informa `debug: true` / `ambiente: producao` hardcoded.
**Severidade condicional:** **HIGH** quando debug está ligado; **CRITICAL** quando debug está
ligado **e** o servidor faz bind em `0.0.0.0` (debugger interativo acessível pela rede →
execução remota de código).
**Correção:** T01.

### AP-07 — Lógica de Negócio na Camada de Rota (Fat Route / Fat Controller)
**Descrição:** handlers HTTP com dezenas de linhas de validação, regra de negócio, persistência
e efeitos colaterais (notificações), sem camada de controller/serviço.
**Sinais de detecção:**
- Função decorada com `@bp.route`/`app.post(...)` com >30 linhas ou com `db.session.add`,
  `commit`, `cursor.execute`, cálculos e envio de notificação no mesmo corpo.
- Handler que instancia modelos campo a campo, valida, persiste e formata resposta.
- "Controller" que dispara e-mail/SMS/push diretamente (prints/logs que simulam o envio,
  `smtplib`, `transporter.sendMail`).
**Correção:** T05.

### AP-08 — Operações Multi-etapa sem Transação / Integridade Referencial
**Descrição:** fluxos que gravam em várias tabelas sem transação, ou exclusões que deixam
registros órfãos.
**Sinais de detecção:**
- Sequência de `INSERT`/`UPDATE` em tabelas diferentes sem `BEGIN/COMMIT/ROLLBACK`
  (`db.serialize` não é transação), commit no meio do fluxo, erro intermediário sem rollback.
- `DELETE FROM <pai>` sem apagar/tratar filhos e sem `ON DELETE CASCADE`; mensagens de resposta
  que admitem dados "sujos".
- Validação de estoque/saldo separada da baixa (race condition).
**Correção:** T06.

### AP-09 — Acoplamento Forte / Estado Global Mutável / Sem Injeção de Dependência
**Descrição:** módulos acessam singletons globais mutáveis (conexão, cache, contadores) e criam
suas dependências internamente, impedindo substituição em testes.
**Sinais de detecção:**
- Python: `global db_connection`, variáveis de módulo mutáveis (`cache = {}`) alteradas por
  funções; `sqlite3.connect(..., check_same_thread=False)` compartilhado entre threads;
  serviço instanciado dentro do handler com credenciais internas.
- JS: `let globalCache = {}`/`let total = 0` exportados e mutados; `new Database()` dentro do
  construtor da classe de negócio; `require` de config dentro de funções de domínio.
**Correção:** T07.

---

## MEDIUM

### AP-10 — API / Dependência Deprecated ou Padrão Assíncrono Legado
**Descrição:** uso de APIs marcadas como obsoletas pela linguagem/framework, dependências sem
suporte, ou padrões legados (callback hell) com equivalente moderno.
**Tabela de detecção (verificar sempre):**

| Ecossistema | Deprecated / legado | Equivalente moderno |
|---|---|---|
| Python ≥3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` (ver nota de naive/aware em T08) |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)`, `session.query(M).get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `engine.execute(...)`, `Query` legado em código novo | `with engine.connect() as c: c.execute(text(...))`, `select()` |
| Flask ≥2.3 | `@app.before_first_request`, `app.json_encoder`, `flask.escape`/`flask.Markup` | inicializar no factory/`with app.app_context()`, `app.json` provider, `markupsafe` |
| Python | `pkg_resources`, `imp`, `distutils`, `asyncio.get_event_loop()` fora de loop | `importlib.metadata`, `importlib`, `setuptools`, `asyncio.run` |
| Node.js | `new Buffer(...)` | `Buffer.from(...)` / `Buffer.alloc(...)` |
| Node.js | `url.parse()`, `querystring` | `new URL()`, `URLSearchParams` |
| Node.js | `crypto.createCipher`, `fs.exists` | `crypto.createCipheriv`, `fs.existsSync`/`fs.promises.access` |
| Node.js | callbacks aninhados (≥3 níveis), `db.run(sql, cb)` sem Promise | `async/await` + wrapper Promise (`util.promisify` ou helper) |
| Express | `body-parser` separado, `req.param()`, `res.send(status)`, `res.json(status, obj)` | `express.json()`, `req.params/query/body`, `res.status(s).json(obj)` |
| npm/pip | pacotes com aviso `npm WARN deprecated` ou sem manutenção (`request`, etc.) | versão suportada / substituto oficial |

Sinais extras: `npm ls`/`npm install` exibindo `deprecated`; versões fixadas muito antigas no
`requirements.txt`.
**Correção:** T08.

### AP-11 — Query N+1
**Descrição:** uma query por item dentro de um loop, em vez de JOIN/eager loading/agregação.
**Sinais de detecção:**
- Python: `for x in rows:` contendo `cursor.execute(...)`, `Model.query.get(x.fk)`,
  `Model.query.filter_by(fk=x.id).count()`; acesso a relacionamento lazy em loop
  (`len(parent.children)` para cada pai).
- JS: `rows.forEach(r => db.get(...))`, `for (...) await db.query(...)`, contadores manuais
  `restantes--` para saber quando todas as queries terminaram.
- Vários `COUNT(*)` separados que poderiam ser um `GROUP BY`.
**Correção:** T09.

### AP-12 — Tratamento de Erro não Centralizado / Respostas Inconsistentes
**Descrição:** cada handler tem seu `try/except`/`catch` genérico; erros vazam detalhes internos
ao cliente; formato de erro varia (texto puro vs JSON); `except:` nu engole erros.
**Sinais de detecção:**
- `except Exception as e: return jsonify({"erro": str(e)}), 500` repetido; `except:` sem tipo.
- `res.status(500).send("Erro DB")` em uma rota e `res.json({error})` em outra.
- Ausência de `@app.errorhandler` / `app.register_error_handler` (Flask) ou middleware
  `(err, req, res, next)` (Express).
- Callbacks que ignoram o parâmetro `err`.
**Correção:** T10.

### AP-13 — Lógica Duplicada
**Descrição:** mesma serialização, cálculo ou validação copiada em vários lugares, com
divergências entre as cópias.
**Sinais de detecção:**
- Blocos idênticos de montagem de dicionário/objeto a partir de uma linha do banco em várias
  funções.
- Mesmo cálculo derivado (ex.: "está atrasado?", "total do pedido", "taxa de conclusão")
  reimplementado em vários handlers.
- Mesmo regex/validação repetido; constantes/funções utilitárias existentes mas não usadas.
**Correção:** T11.

### AP-14 — Responsabilidade fora do Lugar
**Descrição:** código em camada/módulo que não lhe pertence: seed de dados no código de produção
da aplicação, CRUD de uma entidade dentro do módulo de outra, efeitos colaterais (notificação,
cache) no meio do fluxo HTTP.
**Sinais de detecção:**
- `INSERT` de dados de exemplo dentro da classe/inicialização principal da aplicação.
- Blueprint/router de "relatórios" contendo CRUD de outra entidade.
- Handler que envia notificação/cache diretamente em vez de delegar a um serviço.
**Correção:** T05 / T07.

### AP-15 — Validação de Entrada Ausente ou Espalhada
**Descrição:** entrada do cliente usada sem validação de tipo/formato, ou validações
espalhadas e inconsistentes entre criação e atualização.
**Sinais de detecção:**
- `request.get_json()` sem checar `None` antes de `.get()`; `int(request.args[...])` sem
  `try`; comparação `x < 1` com valor que pode ser string.
- `req.body.campo` usado direto sem checar presença/tipo.
- Regras de validação diferentes no POST e no PUT do mesmo recurso.
**Correção:** T12.

---

## LOW

### AP-16 — `print` / `console.log` como Sistema de Log
**Sinais de detecção:** `print(` em código de aplicação (fora de scripts CLI/seed);
`console.log(` em código de servidor; ausência de `logging.getLogger` / logger configurado.
**Escalonamento:** se o log contiver dado sensível → registrar como AP-03 (CRITICAL).
**Correção:** T13.

### AP-17 — Magic Numbers / Magic Strings
**Sinais de detecção:** literais numéricos de regra de negócio sem nome (faixas e percentuais,
limites de tamanho, número de iterações, truncamentos); listas literais de status/papéis/
categorias repetidas em vários pontos; porta/URL fixas.
**Falsos positivos:** `0`, `1`, `-1`, `100` em porcentagem óbvia, códigos HTTP.
**Correção:** T14.

### AP-18 — Nomenclatura Ruim / Código não Idiomático / Código Morto
**Sinais de detecção:**
- Nomes crípticos de variáveis/campos (`u`, `e`, `p`, `cc`, abreviações sem vogais); nomes
  enganosos (`fooCrypto` que não é cripto de verdade, `utils` genérico).
- Python: `type(x) == list` (usar `isinstance`), `if cond: return True else: return False`,
  `if x == True`, imports não usados (`import os, sys, json` sem uso), imports dentro de funções
  sem motivo.
- JS: `var`, `let` que nunca é reatribuído, `self = this` com arrow functions disponíveis,
  variáveis/exports não usados.
**Nota:** renomear **campos de contrato da API** (chaves do JSON de entrada/saída) quebra
clientes — reporte, mas na Fase 3 renomeie apenas nomes internos (ver T16).
**Correção:** T16.

### AP-19 — Listagem sem Paginação
**Sinais de detecção:** `Model.query.all()` / `SELECT * FROM t` sem `LIMIT` retornado inteiro
num endpoint de listagem; `db.all("SELECT * ...")` em rota pública.
**Correção:** T15 (paginação opcional, preservando o comportamento padrão).

---

## Mapa anti-pattern → transformação

| AP | Severidade | Transformação |
|---|---|---|
| AP-01 Hardcoded Credentials | CRITICAL | T01 |
| AP-02 SQL Injection | CRITICAL | T02, T04 |
| AP-03 Dados sensíveis / senha insegura | CRITICAL | T03 |
| AP-04 Endpoint sem auth | CRITICAL/HIGH | T04 |
| AP-05 God Class | CRITICAL | T05, T07 |
| AP-06 Config insegura | HIGH/CRITICAL | T01 |
| AP-07 Fat Route | HIGH | T05 |
| AP-08 Sem transação | HIGH | T06 |
| AP-09 Acoplamento / estado global | HIGH | T07 |
| AP-10 Deprecated / legado | MEDIUM | T08 |
| AP-11 N+1 | MEDIUM | T09 |
| AP-12 Erros não centralizados | MEDIUM | T10 |
| AP-13 Duplicação | MEDIUM | T11 |
| AP-14 Responsabilidade fora do lugar | MEDIUM | T05, T07 |
| AP-15 Validação ausente | MEDIUM | T12 |
| AP-16 print/console.log | LOW | T13 |
| AP-17 Magic numbers | LOW | T14 |
| AP-18 Nomes / não idiomático | LOW | T16 |
| AP-19 Sem paginação | LOW | T15 |
