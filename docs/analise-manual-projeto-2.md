# Análise Manual — Projeto 2 (ecommerce-api-legacy, Node.js/Express)

| # | Severidade | Problema | Evidência | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de produção hardcoded | `src/utils.js:3-4` → `dbPass` e `paymentGatewayKey: "pk_live_..."` | Qualquer pessoa com acesso ao código obtém a senha do banco e a chave live do gateway |
| 2 | CRITICAL | Número do cartão e chave do gateway impressos em log | `src/AppManager.js:45` | Dados de cartão em log violam PCI-DSS; logs costumam ser amplamente acessíveis |
| 3 | CRITICAL | God Class concentrando rotas, regras de negócio, seed e acesso a dados | `src/AppManager.js:18-131` (todas as rotas no mesmo arquivo) | Impossível testar em isolamento; qualquer mudança afeta tudo |
| 4 | CRITICAL | Endpoint administrativo sem autenticação | `GET /api/admin/financial-report` (`AppManager.js:80`) responde 200 sem credencial | Expõe nomes de alunos e valores pagos a qualquer pessoa |
| 5 | HIGH | Criptografia caseira e senha padrão fraca | `src/utils.js:19-22` (`badCrypto`); `src/AppManager.js:68` (`badCrypto(p \|\| "123456")`) | Hash inseguro e truncado; usuários sem senha recebem "123456" |
| 6 | HIGH | Exclusão sem cascata/transação deixa registros órfãos | `DELETE /api/users/:id` (`AppManager.js:131`) — a resposta admite "matrículas e pagamentos ficaram sujos" | Quebra integridade referencial; relatórios ficam inconsistentes |
| 7 | MEDIUM | Callback hell (padrão legado) | `src/AppManager.js:38-60` (callbacks aninhados do sqlite3) | Difícil de ler e tratar erros; equivalente moderno é `async/await` com Promises |
| 8 | MEDIUM | Dependências com pacotes deprecated | `npm install` → `tar@6`, `glob@7`, `inflight` (via `sqlite3@5`) | Pacotes sem suporte, alguns com vulnerabilidades conhecidas |
| 9 | MEDIUM | Formato de resposta inconsistente | `src/AppManager.js:35-60` → erros em texto puro (`res.send("Pagamento recusado")`), sucesso em JSON | Clientes da API não conseguem tratar erros de forma padronizada |
| 10 | MEDIUM | Seed de dados embutido na classe principal | `src/AppManager.js:18-21` | Dados de teste misturados com código de produção |
| 11 | LOW | `console.log` como sistema de log | `src/utils.js:13`, `src/app.js:13`, `src/AppManager.js:45` | Sem níveis, formato ou controle por ambiente |
| 12 | LOW | Magic numbers | `src/utils.js:19` (`10000` iterações), `src/utils.js:22` (`substring(0, 10)`) | Parâmetros de segurança sem nome nem explicação |
| 13 | LOW | Nomes de campos crípticos | Payload do checkout: `usr`, `eml`, `pwd`, `c_id` | Reduz legibilidade e aumenta chance de erro de integração |
