================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13.15 (.venv do projeto)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1 (CORS liberado para qualquer origem)
Database:      SQLite via driver cru (`sqlite3`, SQL manual), arquivo `loja.db` criado no boot, com seed embutido em `database.get_db()`
Domain:        E-commerce (produtos, usuários, pedidos, itens de pedido, relatório de vendas)
Architecture:  Monolito desestruturado — 4 módulos planos na raiz, sem diretórios de camada; SQL e regras de negócio de 3 domínios em `models.py`, e SQL dentro de rotas em `app.py`
Entry point:   app.py (run: `python app.py`, 0.0.0.0:5000, debug=True)
Source files:  5 files analyzed (4 .py + requirements.txt) | ~794 lines of code
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes (GET /, GET /health, GET/POST /produtos, GET /produtos/busca, GET/PUT/DELETE /produtos/<id>, GET/POST /usuarios, GET /usuarios/<id>, POST /login, GET/POST /pedidos, GET /pedidos/usuario/<usuario_id>, PUT /pedidos/<pedido_id>/status, GET /relatorios/vendas, POST /admin/reset-db, POST /admin/query)
Aux scripts:   nenhum (o seed roda dentro de `database.get_db()` no boot)
================================

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite, driver cru)
Files:   5 analyzed | ~794 lines of code
Architecture: Monolito desestruturado

## Summary
CRITICAL: 6 | HIGH: 3 | MEDIUM: 5 | LOW: 4  (Total: 18)

## Findings

### #1 [CRITICAL] SQL Injection / Execução de Query Arbitrária (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299; app.py:59-78
Description: Todas as queries montam o SQL concatenando entrada do cliente (`"... WHERE id = " + str(id)`,
`"VALUES ('" + nome + "', ..."`). O login (models.py:109-111) monta o WHERE com `email` e `senha`
concatenados. A busca (models.py:289-297) concatena `q` e `categoria` dentro de `LIKE '%...%'`.
Além disso, `POST /admin/query` (app.py:59-78) executa qualquer SQL enviado em `{"sql": ...}`;
a checagem de prefixo `SELECT` só decide se o resultado é devolvido.
Impact: Um atacante faz login como admin sem senha (`' OR '1'='1' --`), lê ou altera qualquer tabela
pela busca ou pelo cadastro, e com `/admin/query` executa `DROP TABLE`/`UPDATE` livremente.
Recommendation: Parametrizar todas as queries com placeholders `?` (T02) → camada Model (`models/*_model.py`).
Desabilitar `/admin/query` por padrão (variável `ENABLE_ADMIN_ENDPOINTS`, desligada) e mantê-lo atrás
da autenticação fail-closed (T04) → `views/admin_routes.py` + `middlewares/auth.py`.

### #2 [CRITICAL] Endpoint Sensível sem Autenticação/Autorização (AP-04)
File: app.py:47-57, 59-78, 28, 18-19, 24, 26, 14-16
Description: Nenhuma rota verifica credencial. Rotas destrutivas e administrativas são anônimas:
`POST /admin/reset-db` apaga as 4 tabelas, `POST /admin/query` executa SQL arbitrário,
`GET /relatorios/vendas` expõe faturamento, `GET /usuarios` e `GET /usuarios/<id>` expõem dados
pessoais (com senha), `GET /pedidos` lista os pedidos de todos os clientes,
`PUT /pedidos/<id>/status` aprova ou cancela qualquer pedido, e `POST/PUT/DELETE /produtos` alteram o catálogo.
O `/login` não emite token, então nenhuma credencial existe hoje.
Impact: Qualquer cliente anônimo na rede apaga o banco, executa SQL, lê dados pessoais e financeiros,
altera preços e muda status de pedidos.
Recommendation: Autenticação obrigatória e fail-closed (T04) via `middlewares/auth.py` com credencial estática
`ADMIN_TOKEN` (`Authorization: Bearer <token>`). Sem header, com token inválido ou sem `ADMIN_TOKEN`
configurado → 401. Passam a exigir credencial: POST /admin/reset-db, POST /admin/query, GET /relatorios/vendas,
GET /usuarios, GET /usuarios/<id>, GET /pedidos, PUT /pedidos/<id>/status, POST /produtos, PUT /produtos/<id>,
DELETE /produtos/<id>.

### #3 [CRITICAL] Exposição de Dados Sensíveis / Armazenamento Inseguro de Senha (AP-03)
File: models.py:83, 99, 110, 126-129; controllers.py:128-144, 285-289; database.py:75-83
Description: `get_todos_usuarios` e `get_usuario_por_id` serializam o campo `senha` (models.py:83, 99),
e `GET /usuarios` e `GET /usuarios/<id>` o devolvem. As senhas são gravadas e comparadas em texto puro
(models.py:110, 126-129; seed com `admi***` em database.py:76). `GET /health` devolve `secret_key`,
`db_path` e `debug` (controllers.py:285-289).
Impact: Qualquer pessoa obtém a senha de todos os usuários, inclusive do admin, e a chave de assinatura
da aplicação. Um vazamento do arquivo `loja.db` também expõe todas as credenciais.
Recommendation: Hash com sal via `werkzeug.security` (`generate_password_hash`/`check_password_hash`)
e `to_dict` sem `senha` (T03) → `models/usuario_model.py`. Remover campos internos do `/health`
→ `controllers/health_controller.py`. Migração transparente: senhas legadas em texto puro são
re-hasheadas no primeiro login válido.

### #4 [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:7; controllers.py:289
Description: `app.config["SECRET_KEY"] = "minh***"` está escrito no código, e o mesmo valor é repetido
literalmente na resposta do `/health`.
Impact: A chave está no controle de versão e é publicada pela API. Qualquer pessoa consegue forjar
sessões ou assinaturas da aplicação.
Recommendation: Ler `SECRET_KEY` do ambiente. Se a variável faltar, gerar uma chave aleatória
(`secrets.token_hex(32)`) e logar um warning (T01) → `config/settings.py`.

### #5 [CRITICAL] Configuração Insegura de Execução (AP-06)
File: app.py:8, 88; controllers.py:286-288
Description: `DEBUG = True` está fixo na config e em `app.run(host="0.0.0.0", port=5000, debug=True)`.
O `/health` também anuncia `"ambiente": "producao"` e `"debug": True` fixos. Fica CRITICAL porque o
debug está ligado **e** o bind é em todas as interfaces.
Impact: O debugger interativo do Werkzeug fica acessível pela rede, o que permite execução remota
de código. Stack traces vazam para clientes.
Recommendation: `DEBUG` padrão false, `HOST` padrão 127.0.0.1 e `PORT` padrão 5000, todos lidos
do ambiente (T01) → `config/settings.py`.

### #6 [CRITICAL] God Class / God File (AP-05)
File: models.py:1-314; app.py:47-78
Description: `models.py` reúne o acesso a dados de produtos, usuários e pedidos, a regra de desconto do
relatório (256-262), a validação e baixa de estoque (139-166) e a busca. `app.py` mistura composition root,
registro de rotas e SQL direto em handlers (reset e query).
Impact: Qualquer mudança em um domínio mexe no mesmo arquivo dos outros. Não dá para testar regras
isoladas, e o acoplamento entre camadas é total.
Recommendation: Decompor por entidade e camada (T05 + T07) → `models/{produto,usuario,pedido,relatorio,admin}_model.py`,
`controllers/*`, `views/*_routes.py`. `app.py` vira só composition root.

### #7 [HIGH] Lógica de Negócio na Camada de Rota (Fat Controller) (AP-07)
File: controllers.py:24-62, 64-96, 188-220, 237-255, 264-290; app.py:47-78
Description: As funções em `controllers.py` são handlers HTTP (leem `request` e montam `jsonify`) e ao mesmo
tempo fazem validação extensa, regras de negócio e efeitos colaterais: "envio" de e-mail, SMS e push
(208-210), notificações de status (247-250) e SQL direto no health (266-274). Em `app.py`, os handlers
`reset_database` e `executar_query` executam SQL.
Impact: Não há como reutilizar ou testar regra sem contexto HTTP, e as notificações ficam presas ao fluxo de request.
Recommendation: Separar views (extração do request e JSON), controllers (caso de uso),
validators e `services/notification_service.py` (T05).

### #8 [HIGH] Operações Multi-etapa sem Transação / Integridade Referencial (AP-08)
File: models.py:133-169, 65-70, 275-283
Description: `criar_pedido` valida o estoque num loop (139-146) e depois insere o pedido, os itens e
decrementa o estoque (148-166) na conexão global compartilhada, sem `BEGIN/ROLLBACK`. Se um passo falhar
no meio, as escritas pendentes ficam na conexão e são confirmadas pelo próximo `commit()` de outra requisição.
A validação está separada da baixa (race condition → estoque negativo). `deletar_produto` (68) deixa
`itens_pedido` apontando para o produto removido.
Impact: Pedidos parciais e estoque inconsistente sob concorrência ou erro. Itens órfãos aparecem como "Desconhecido".
Recommendation: Envolver o fluxo do pedido numa transação única com rollback, com baixa condicional
(`UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?`) (T06) → `models/pedido_model.py`.
Para itens de produtos excluídos, manter o histórico do pedido: preservar o comportamento atual de
leitura ("Desconhecido") e registrar a decisão.

### #9 [HIGH] Acoplamento Forte / Estado Global Mutável (AP-09)
File: database.py:4-11; models.py:1, 5, 25, ...; controllers.py:3, 266
Description: `global db_connection` é um singleton mutável criado com `check_same_thread=False` e
compartilhado por todas as threads do servidor. Models e controllers importam `get_db` diretamente,
e o caminho `loja.db` está fixo.
Impact: Condições de corrida entre requisições concorrentes (transações misturadas na mesma conexão),
impossível trocar o banco em testes.
Recommendation: Uma conexão por requisição via `flask.g` + `teardown_appcontext`, com o caminho do banco
vindo da config injetada no `create_app()` (T07) → `models/database.py`.

### #10 [MEDIUM] Validação de Entrada Ausente ou Espalhada (AP-15)
File: controllers.py:43-50, 87-90, 118-121, 169-170, 195-201, 239-240; models.py:140-146
Description: `preco < 0` com string no JSON gera `TypeError` → 500. O PUT de produto não aplica as
regras de tamanho de nome nem de categoria que o POST aplica (87-90 vs 43-54). `float(preco_min)` inválido → 500.
`login` e `atualizar_status_pedido` chamam `.get` sem checar se o corpo é `None` (169-170, 239-240) → 500.
Os itens do pedido não validam `produto_id` e `quantidade` (quantidade negativa aumenta o estoque).
Impact: Erros de cliente viram 500 com mensagem interna, e dá para gravar dados inválidos
(pedido com quantidade ≤ 0 ou categoria inválida via PUT).
Recommendation: Centralizar as validações em `validators/` com regras únicas para POST e PUT (T12).
Mensagens e status de validação já existentes ficam iguais.

### #11 [MEDIUM] Tratamento de Erro não Centralizado (AP-12)
File: controllers.py:10, 21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291; app.py:77-78
Description: São 17 blocos `except Exception as e: return jsonify({"erro": str(e)}), 500`, sem
`errorhandler`. O formato varia (`{"status":"erro","detalhes":...}` no health).
Impact: Mensagens internas do SQLite e do Python vazam para o cliente, e há boilerplate repetido.
Recommendation: Erros de domínio (`ValidationError`, `NotFoundError`...) com handler central em
`middlewares/error_handler.py` (T10). O 500 genérico passa a não expor detalhes.

### #12 [MEDIUM] Query N+1 (AP-11)
File: models.py:187-199, 219-231, 154-156, 239-254
Description: Para cada pedido roda uma query de itens, e para cada item outra query do nome do produto
(cursor2/cursor3). `criar_pedido` relê o preço de cada produto. O relatório faz 5 consultas separadas
que caberiam em uma agregação.
Impact: O custo cresce com pedidos × itens, e a listagem geral fica lenta com volume.
Recommendation: Um `JOIN itens_pedido/produtos` com `WHERE pedido_id IN (...)` e agregação única com
`SUM(CASE ...)` no relatório (T09) → `models/pedido_model.py`, `models/relatorio_model.py`.

### #13 [MEDIUM] Lógica Duplicada (AP-13)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233; controllers.py:28-46, 72-90
Description: A montagem do dicionário de produto aparece 3 vezes, a de usuário 2 vezes, e
`get_pedidos_usuario` e `get_todos_pedidos` são cópias quase idênticas. A validação de produto
está duplicada (e divergente) entre criar e atualizar.
Impact: Correções aplicadas numa cópia e esquecidas na outra (por exemplo, o PUT sem validação de categoria).
Recommendation: Serializadores únicos por entidade e um só montador de pedidos com itens (T11),
mais um validador compartilhado.

### #14 [MEDIUM] Responsabilidade fora do Lugar (AP-14)
File: database.py:56-84; controllers.py:208-210, 247-250, 264-274
Description: O seed de dados de exemplo roda dentro da função de conexão de produção. As notificações
(e-mail, SMS, push) são disparadas no meio do handler HTTP. O health executa SQL no controller.
Impact: Dados de exemplo são inseridos em qualquer banco vazio, inclusive em produção.
Os efeitos colaterais não podem ser trocados nem desligados.
Recommendation: Mover o seed para `models/seed.py`, chamado no boot pelo composition root
(mantém o comportamento atual), e as notificações para `services/notification_service.py` (T05/T07).

### #15 [LOW] print como Sistema de Log (AP-16)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: São 19 `print(...)` como log, incluindo e-mails de usuários em tentativas de login (179, 182).
Impact: Não há nível, timestamp nem destino configurável, e dados pessoais vão para o stdout.
Recommendation: `logging.getLogger(__name__)` com níveis adequados, sem dados pessoais (T13).

### #16 [LOW] Magic Numbers / Magic Strings (AP-17)
File: models.py:247-262; controllers.py:47-52, 242; app.py:36, 88; controllers.py:285
Description: As faixas de desconto (10000/5000/1000 → 10%/5%/2%), os limites de nome (2/200), as listas
literais de categorias e status, a versão "1.0.0" repetida e a porta 5000 fixa estão espalhados pelo código.
Impact: Mudar uma regra exige caçar literais em vários arquivos.
Recommendation: Constantes nomeadas (`CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`, `FAIXAS_DESCONTO`, `APP_VERSION`) (T14).

### #17 [LOW] Nomenclatura Ruim / Código não Idiomático / Código Morto (AP-18)
File: models.py:2, 63, 70, 187-192, 283; database.py:2; controllers.py:56, 160, 200
Description: Há imports sem uso (`sqlite3` em models.py:2, `os` em database.py:2), a variável `id` que
sombreia o builtin, `cursor2`/`cursor3`, `return True` incondicional sem uso, e
`if not itens or len(itens) == 0` redundante.
Impact: Ruído de leitura e sinais enganosos de retorno.
Recommendation: Remover código morto e renomear identificadores internos (T16). Chaves do JSON
permanecem iguais.

### #18 [LOW] Listagem sem Paginação (AP-19)
File: models.py:7, 75, 206
Description: `GET /produtos`, `GET /usuarios` e `GET /pedidos` retornam a tabela inteira (`SELECT *` sem `LIMIT`).
Impact: As respostas crescem sem limite à medida que os dados aumentam.
Recommendation: Paginação opcional por `?page=&per_page=`. Sem os parâmetros, a resposta continua
idêntica à atual (T15).

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| — | None found (Python 3.13 / Flask 3.1.1: no utcnow, before_first_request, json_encoder, pkg_resources, etc.) | — |

## Refactoring Plan (Phase 3 preview)
Strategy: Reestruturação completa — monolito plano sem nenhuma camada; criar todas as camadas MVC e reduzir app.py a composition root.
Target structure:
app.py                      # create_app() + python app.py (127.0.0.1:5000 por padrão)
config/settings.py          # SECRET_KEY, DEBUG, HOST, PORT, DATABASE_PATH, ADMIN_TOKEN, ENABLE_ADMIN_ENDPOINTS
models/database.py          # conexão por requisição (flask.g) + schema
models/seed.py              # dados de exemplo (boot)
models/{produto,usuario,pedido,relatorio,admin}_model.py
controllers/{produto,usuario,pedido,relatorio,health,admin}_controller.py
views/{root,produto,usuario,pedido,relatorio,health,admin}_routes.py   # Blueprints finos
validators/{produto,usuario,pedido}_validator.py
services/notification_service.py
middlewares/{auth,error_handler}.py
errors.py                   # erros de domínio
(database.py, models.py, controllers.py removidos)
Contract notes:
- `senha` removido das respostas de /usuarios e /usuarios/<id>; senhas passam a ser hash (login com as senhas do seed continua funcionando).
- /health deixa de retornar `secret_key`, `db_path`, `debug`, `ambiente`.
- Endpoints AP-04 (lista em #2) passam a exigir `Authorization: Bearer <ADMIN_TOKEN>`: anônimo/token inválido/ADMIN_TOKEN não configurado → 401; com token válido, status e corpo iguais aos atuais.
- /admin/query e /admin/reset-db: além do token, desabilitados por padrão (403) até `ENABLE_ADMIN_ENDPOINTS=1`.
- Erros 500 genéricos deixam de expor `str(e)`; entradas malformadas que hoje viram 500 passam a 400 com mensagem de validação.
- Servidor sobe em 127.0.0.1 com debug desligado por padrão (HOST/DEBUG via ambiente).

================================
Total: 18 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
