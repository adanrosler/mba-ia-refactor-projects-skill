# Análise Manual — Projeto 3 (task-manager-api, Python/Flask)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Debug ativo e servidor exposto em todas as interfaces | Boot: `Debug mode: on`, `Running on all addresses (0.0.0.0)`, `Debugger is active!` | Debugger do Werkzeug acessível na rede permite execução remota de código |
| 2 | CRITICAL | Senha com hash MD5 sem salt e exposta pela API | `GET /users/1` retorna `password: 81dc9bdb...` (MD5 de "1234") | MD5 é revertido instantaneamente com rainbow tables; hash não deveria sair da API |
| 3 | HIGH | Regra de negócio dentro das rotas (sem camada de controller) | `routes/task_routes.py:85-155` (POST /tasks com ~70 linhas de validação e persistência) | Rotas "gordas" dificultam teste e reuso; viola separação MVC |
| 4 | MEDIUM | Uso de API deprecated (Python) | `seed.py:66-74` → `datetime.utcnow()` | Marcado para remoção; substituir por `datetime.now(datetime.UTC)` |
| 5 | MEDIUM | Uso de API deprecated (SQLAlchemy) | `routes/task_routes.py:188, 195` → `Model.query.get(id)` | API legada no SQLAlchemy 2.x; substituir por `db.session.get(Model, id)` |
| 6 | MEDIUM | Query N+1 | `routes/task_routes.py:44-57` (busca User e Category por task); `routes/report_routes.py:163` (count por categoria) | Número de queries cresce linearmente com os registros |
| 7 | MEDIUM | Serialização e cálculo de `overdue` duplicados | `routes/task_routes.py:18-39`, `task_routes.py:74-80`, `routes/user_routes.py:163-180` | Mesma lógica em 3 lugares, com saídas diferentes por rota |
| 8 | LOW | Magic values: listas de status e roles fixas no código | `routes/task_routes.py:177`, `routes/user_routes.py:120` | Deveriam ser constantes/enums centralizados |
| 9 | LOW | Checagem de tipo com `type(x) == list` | `routes/task_routes.py:210` | Não idiomático; usar `isinstance` |
| 10 | LOW | CRUD de categorias no blueprint de relatórios | `routes/report_routes.py:157-211` | Responsabilidade no lugar errado |
| 11 | LOW | Listagens sem paginação | `GET /tasks`, `GET /users` | Retorna todos os registros de uma vez |
| 12 | HIGH | Autenticação falsa e hash de senha em todas as respostas | `POST /login` retorna `token: fake-jwt-token-1`; `password` aparece em login, `POST /users` e `PUT /users/:id` | Token previsível e nunca validado: nenhuma rota é de fato protegida |
