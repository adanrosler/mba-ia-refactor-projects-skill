# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, organizada em
camadas MVC: `config/`, `models/`, `controllers/`, `routes/` (views), `middlewares/`,
`validators/`, `services/` e `utils/`. O `app.py` é o composition root.

## Como rodar

```bash
pip install -r requirements.txt
export SECRET_KEY=$(openssl rand -hex 32)   # assina os tokens do /login
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`)
com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os
endpoints vão retornar listas vazias.

### Variáveis de ambiente

| Variável | Default | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória por processo (com warning) | assinatura dos tokens emitidos por `POST /login` |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | bind do servidor |
| `APP_DEBUG` | `false` | modo debug do Flask (nunca use em rede aberta) |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `TOKEN_MAX_AGE_SECONDS` | `86400` | validade dos tokens |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | vazio / `587` | notificações por e-mail (sem eles o serviço fica desabilitado e só registra log) |

### Autenticação

`POST /login` devolve `token`; envie-o como `Authorization: Bearer <token>`. Sem token válido as
rotas abaixo respondem **401**; com papel insuficiente, **403**:

| Rota | Exige |
|---|---|
| `POST /users` com `role` diferente de `user` | admin |
| `PUT /users/<id>` | o próprio usuário ou admin (alterar `role`/`active` exige admin) |
| `DELETE /users/<id>`, `DELETE /categories/<id>` | admin |
| `GET /reports/summary`, `GET /reports/user/<id>` | admin ou manager |

Listagens (`GET /tasks`, `/users`, `/categories`) aceitam `?page=&per_page=` opcionais; sem eles,
devolvem a lista completa.
