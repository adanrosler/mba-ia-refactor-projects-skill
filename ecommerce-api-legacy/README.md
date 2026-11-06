# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=<token-secreto> npm start
```

A aplicação sobe em `http://127.0.0.1:3000`. O banco SQLite é em memória e o schema + seeds são
carregados automaticamente no boot (`src/database/seed.js`).

### Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `ADMIN_TOKEN` | — (obrigatória para rotas admin) | Token exigido em `Authorization: Bearer <token>` por `GET /api/admin/financial-report` e `DELETE /api/users/:id`. Sem ela, essas rotas respondem **401**. |
| `PORT` | `3000` | Porta HTTP |
| `HOST` | `127.0.0.1` | Interface de bind (use `0.0.0.0` só atrás de proxy/firewall) |
| `PAYMENT_GATEWAY_KEY` | — | Chave do gateway; ausente → gateway em modo simulado |
| `DB_FILE` | `:memory:` | Arquivo SQLite |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, `error` |

## Estrutura

```
src/
├── app.js            # composition root
├── config/           # leitura de variáveis de ambiente
├── database/         # conexão (Promise + transações) e seed
├── models/           # acesso a dados (SQL parametrizado)
├── controllers/      # casos de uso (checkout, relatório, usuários)
├── routes/           # rotas Express finas
├── services/         # gateway de pagamento, cache
├── middlewares/      # auth (fail-closed), erros, asyncHandler
├── validators/       # validação de entrada
├── errors/           # HttpError
└── utils/            # hash de senha (scrypt), logger
```

Exemplos de requisições estão em `api.http`.
