# Análise Manual — Projeto 1 (code-smells-project, Python/Flask)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | SECRET_KEY exposta na API | `GET /health` retorna `secret_key` | Qualquer pessoa obtém a chave usada para assinar sessões/tokens |
| 2 | CRITICAL | Senhas em texto puro e expostas | `GET /usuarios` retorna o campo `senha` sem hash | Vazamento direto de credenciais de todos os usuários |
| 3 | CRITICAL | Endpoint que executa SQL arbitrário | `app.py:59` → `POST /admin/query` | Permite ler/alterar/apagar o banco via HTTP (a confirmar se há autenticação) |
| 4 | HIGH | Debug ligado em "producao" | `GET /health` → `debug: true`, `ambiente: producao` | Debug expõe stack traces e console interativo |

> Linhas exatas dos itens 1, 2 e 4 serão confirmadas na leitura do código.
| 5 | MEDIUM | Tratamento de erro duplicado e que vaza detalhes internos | `controllers.py:218-220` (padrão repetido em todas as funções) | `except Exception` genérico retorna `str(e)` ao cliente; sem error handler centralizado |
| 6 | MEDIUM | Controller com responsabilidade de notificação | `controllers.py:208-210` | Envio de e-mail/SMS/push acoplado ao controller; deveria estar em um serviço próprio |
| 7 | LOW | Uso de `print` em vez de logging | `controllers.py:208-210, 219` | Sem níveis de log, sem formatação, impossível de controlar em produção |
