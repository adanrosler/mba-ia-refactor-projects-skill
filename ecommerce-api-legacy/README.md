# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://127.0.0.1:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `HOST` | `127.0.0.1` | Interface de bind (`0.0.0.0` para expor na rede) |
| `ADMIN_TOKEN` | — | Se definida, `/api/admin/*` e `DELETE /api/users/:id` exigem `Authorization: Bearer <token>` |
| `PAYMENT_GATEWAY_KEY` | — | Chave do gateway; sem ela o pagamento roda em modo simulado |
| `DATABASE_FILE` | `:memory:` | Arquivo SQLite |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |

## Estrutura

`src/app.js` (composition root) → `routes/` → `controllers/` → `models/` / `services/`, com `config/`,
`database/` (conexão + seed), `middlewares/` (auth, erros), `validators/`, `errors/` e `utils/`.
