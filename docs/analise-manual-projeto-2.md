# Análise Manual — Projeto 2 (ecommerce-api-legacy, Node.js/Express)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | God Class concentrando rotas, regras de negócio e acesso a dados | `src/AppManager.js:28, 80, 131` (todas as rotas no mesmo arquivo) | Impossível testar em isolamento; qualquer mudança afeta tudo |
| 2 | CRITICAL | Endpoint administrativo sem autenticação | `GET /api/admin/financial-report` responde 200 sem credencial | Expõe nomes de alunos e valores pagos a qualquer pessoa |
| 3 | HIGH | Exclusão sem cascata/transação deixa registros órfãos | `DELETE /api/users/:id` (`AppManager.js:131`) — a própria resposta admite "matrículas e pagamentos ficaram sujos" | Quebra integridade referencial; relatórios passam a mostrar dados inconsistentes |
| 4 | MEDIUM | Dependências com pacotes deprecated | `npm install` → `tar@6`, `glob@7`, `inflight` (via `sqlite3@5`) | Pacotes sem suporte, alguns com vulnerabilidades conhecidas |
| 5 | MEDIUM | Formato de resposta inconsistente | Sucesso retorna JSON `{"msg":...}`; recusa retorna texto puro `Pagamento recusado` | Clientes da API não conseguem tratar erros de forma padronizada |
| 6 | LOW | Nomes de campos crípticos | Payload do checkout: `usr`, `eml`, `pwd`, `c_id` | Reduz legibilidade e aumenta chance de erro de integração |

> Linhas exatas serão confirmadas na leitura do código.
