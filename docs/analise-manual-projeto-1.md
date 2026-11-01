# Análise Manual — Projeto 1 (code-smells-project, Python/Flask)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | SECRET_KEY exposta na API | `controllers.py:289` → `GET /health` retorna `secret_key` | Qualquer pessoa obtém a chave usada para assinar sessões/tokens |
| 2 | CRITICAL | Senhas em texto puro e expostas | `GET /usuarios` retorna o campo `senha` sem hash | Vazamento direto de credenciais de todos os usuários |
| 3 | CRITICAL | Endpoint que executa SQL arbitrário | `app.py:59` → `POST /admin/query` | Permite ler/alterar/apagar o banco via HTTP |
| 4 | HIGH | Debug ligado em "producao" | `GET /health` → `debug: true`, `ambiente: producao` | Debug expõe stack traces e console interativo |
| 5 | MEDIUM | Tratamento de erro duplicado e que vaza detalhes internos | `controllers.py:218-220` (padrão repetido em todas as funções) | `except Exception` genérico retorna `str(e)` ao cliente; sem error handler centralizado |
| 6 | MEDIUM | Controller com responsabilidade de notificação | `controllers.py:208-210` | Envio de e-mail/SMS/push acoplado ao controller; deveria estar em um serviço próprio |
| 7 | LOW | Uso de `print` em vez de logging | `controllers.py:208-210, 219` | Sem níveis de log, sem formatação, impossível de controlar em produção |
| 8 | LOW | Magic numbers na regra de desconto | `models.py:257-262` → faixas `10000/5000/1000` e taxas `0.1/0.05/0.02` | Regra de negócio sem nome nem explicação; difícil de alterar com segurança |
| 9 | CRITICAL | SECRET_KEY hardcoded no código-fonte | `app.py:7` → `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` (e `app.py:8`, `app.py:88` com `debug=True` e `host="0.0.0.0"`) | Chave de assinatura versionada no repositório; qualquer um com acesso ao código pode forjar sessões |
| 10 | CRITICAL | SQL Injection por concatenação de strings | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 149-150, 155-166, 174, 188, 192, 220, 224, 280, 289-297` | Entrada do usuário vai direto para o SQL; em `login_usuario` (`models.py:109-111`) permite bypass de autenticação com `' OR '1'='1` |
| 11 | CRITICAL | God Module concentrando acesso a dados e regras de negócio de 4 domínios | `models.py:1-314` (produtos, usuários, pedidos e relatórios: SQL, serialização, cálculo de total/estoque e regra de desconto no mesmo arquivo) | Impossível testar ou alterar um domínio sem afetar os outros; não há fronteira entre Model e regra de negócio |
