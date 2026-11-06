# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
pip install -r requirements.txt
ADMIN_TOKEN=<token-forte> python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente
no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

### Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `ADMIN_TOKEN` | — | **Obrigatória** para as rotas protegidas (`Authorization: Bearer <token>`). Sem ela, essas rotas respondem 401. |
| `SECRET_KEY` | aleatória por boot | Chave de assinatura do Flask |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `APP_DEBUG` | `false` | Modo debug (nunca ligue em produção) |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `APP_ENV` | `producao` | Valor informado em `/health` |
| `ENABLE_ADMIN_ENDPOINTS` | `false` | Habilita `/admin/query` e `/admin/reset-db` (continuam exigindo `ADMIN_TOKEN`) |
| `LOG_LEVEL` | `INFO` | Nível de log |

### Rotas protegidas (exigem `ADMIN_TOKEN`)

`GET /usuarios`, `GET /usuarios/<id>`, `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`,
`GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`, `POST /admin/query`, `POST /admin/reset-db`.

As listagens `GET /produtos`, `GET /usuarios` e `GET /pedidos` aceitam paginação opcional `?page=&per_page=`.

## Estrutura

```
app.py            composition root (create_app)
config/           configuração via ambiente
models/           acesso a dados (SQL parametrizado), schema e seed
controllers/      casos de uso
views/            blueprints HTTP
validators/       validação de entrada
services/         notificações
middlewares/      autenticação e tratamento de erros
errors.py         erros de domínio
```
