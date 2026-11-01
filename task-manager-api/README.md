# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em MVC: `config/`, `models/`, `controllers/`, `routes/` (views), `validators/`, `middlewares/`, `services/` e `utils/`. O `app.py` é o composition root.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo. **Rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Variáveis de ambiente (opcionais; também lidas de `.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por boot (com warning) | chave de assinatura dos tokens |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | bind do servidor |
| `APP_DEBUG` | `false` | modo debug do Flask |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `CORS_ORIGINS` | `*` | origens permitidas, separadas por vírgula |
| `AUTH_REQUIRED` | `false` | exige `Authorization: Bearer <token do /login>` nas rotas sensíveis |
| `AUTH_TOKEN_MAX_AGE` | `86400` | validade do token em segundos |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | desabilitado | envio de e-mail de atribuição de task |
| `LOG_LEVEL` | `INFO` | nível de log |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | `20` / `100` | paginação opcional via `?page=&per_page=` |
