# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas armazenadas com hash).

## Estrutura

```
app.py           # composition root (create_app)
config/          # settings lidas de variáveis de ambiente
models/          # acesso a dados (SQL parametrizado), schema e seed
controllers/     # casos de uso
views/           # Blueprints (rotas HTTP)
validators/      # validação de entrada
services/        # notificações
middlewares/     # tratamento de erros e autorização
errors.py        # erros de domínio
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por boot | Chave de assinatura do Flask |
| `DEBUG` | `false` | Modo debug (nunca habilite em produção) |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço de bind |
| `APP_ENV` | `producao` | Ambiente reportado em `/health` |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `ADMIN_TOKEN` | — | Se definido, exige `Authorization: Bearer <token>` em `GET /usuarios`, `GET /pedidos`, `GET /relatorios/vendas` e `/admin/*` |
| `ENABLE_ADMIN_ENDPOINTS` | `false` | Habilita `POST /admin/query` e `POST /admin/reset-db` (desligados por padrão) |

Listagens (`/produtos`, `/usuarios`, `/pedidos`) aceitam paginação opcional `?page=1&per_page=20`; sem esses parâmetros a lista completa é retornada.
