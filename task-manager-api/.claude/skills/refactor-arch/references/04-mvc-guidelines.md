# 04 — Guidelines de Arquitetura MVC (Fase 3)

Arquitetura alvo para APIs backend. Em uma API, a "View" é a camada de apresentação HTTP:
rotas + formatação da resposta (JSON).

## 1. Camadas e responsabilidades

| Camada | Pode | Não pode |
|---|---|---|
| **Config** (`config/`) | Ler variáveis de ambiente, definir defaults seguros, expor constantes de configuração | Conter regra de negócio; ter segredos reais como default |
| **Models** (`models/`) | Definir entidades/tabelas, encapsular **todo** acesso a dados (queries parametrizadas, ORM), regras intrínsecas da entidade (ex.: "está atrasada?", hash/verificação de senha), serialização segura (`to_dict` sem campos sensíveis) | Conhecer `request`/`response`, status HTTP, chamar serviços externos |
| **Controllers** (`controllers/`) | Orquestrar o caso de uso: validar entrada (via validators), chamar models e services, decidir o resultado, lançar erros de domínio | Montar SQL, ler `request` diretamente do framework (recebe dados já extraídos), formatar HTTP |
| **Views / Routes** (`views/` ou `routes/`) | Declarar rotas (método + caminho), extrair dados do request, chamar o controller, devolver JSON + status | Conter regra de negócio, SQL, loops de cálculo |
| **Services** (`services/`, opcional) | Integrações e efeitos colaterais: e-mail, notificação, gateway de pagamento, cache | Acessar `request`; conter regras de outras entidades |
| **Middlewares** (`middlewares/`) | Tratamento centralizado de erros, autenticação, logging de requisição | Regra de negócio |
| **Entry point / composition root** | Criar a aplicação, carregar config, inicializar banco, registrar rotas e middlewares, injetar dependências, iniciar o servidor | Conter rotas ou regras |

**Regra de dependência:** `routes → controllers → models/services → config`. Nunca o
contrário. Models não importam controllers; controllers não importam o framework HTTP
(exceto tipos de erro próprios).

**Erros de domínio:** controllers lançam exceções/erros próprios (`NotFoundError`,
`ValidationError`, `ConflictError`, `UnauthorizedError`) com status e mensagem; o middleware
central converte em resposta JSON. Mensagens e códigos devem ser **os mesmos** que o código
original devolvia.

## 2. Estrutura alvo — Python/Flask

```
<raiz>/
├── app.py                    # composition root: create_app() + if __name__ == "__main__"
├── config/
│   ├── __init__.py
│   └── settings.py           # lê env: SECRET_KEY, DEBUG, HOST, PORT, DATABASE_*
├── models/
│   ├── __init__.py
│   └── <entidade>_model.py   # acesso a dados + regras da entidade
├── controllers/
│   ├── __init__.py
│   └── <entidade>_controller.py
├── views/  (ou routes/, se o projeto já usa esse nome)
│   ├── __init__.py
│   └── <entidade>_routes.py  # Blueprints finos
├── services/                 # opcional: notificações, integrações
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py      # register_error_handlers(app)
├── validators/ (opcional)    # funções/esquemas de validação de entrada
└── <scripts auxiliares existentes, ex.: seed>  # mantidos funcionando
```

- `create_app()` monta tudo; `app = create_app()` em nível de módulo **se** algum script/
  comando existente importar `app` de `app.py` (preserve imports usados por scripts auxiliares).
- Conexão com banco: obtida por função de fábrica em `models/` (ou `database.py` existente),
  nunca por global mutável espalhado. Para SQLite com driver cru, prefira uma conexão por
  requisição (`flask.g` + `teardown_appcontext`) ou uma conexão encapsulada em um objeto
  criado no composition root.

## 3. Estrutura alvo — Node.js/Express

```
<raiz>/
├── package.json              # "start" continua apontando para o entry point
└── src/
    ├── app.js                # composition root: cria app, injeta deps, listen
    ├── config/
    │   └── index.js          # lê process.env com defaults seguros
    ├── database/
    │   ├── connection.js     # cria a conexão + helpers Promise (run/get/all)
    │   └── seed.js           # schema + dados iniciais (separado da aplicação)
    ├── models/
    │   └── <entidade>Model.js
    ├── controllers/
    │   └── <entidade>Controller.js
    ├── routes/               # (views) routers finos
    │   └── <entidade>Routes.js
    ├── services/             # gateway de pagamento, cache, notificação
    ├── middlewares/
    │   ├── errorHandler.js
    │   └── auth.js (se aplicável)
    └── utils/                # helpers puros (hash de senha, logger)
```

- Dependências são criadas no `app.js` e passadas por parâmetro (factory functions:
  `createUserModel(db)`, `createCheckoutController({ models, services })`,
  `createRoutes(controllers)`).
- Use `async/await`; envolva handlers assíncronos para que erros cheguem ao middleware de erro
  (`(fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)`).

## 4. Adaptação ao estado atual (Fase 3 adaptativa)

| Estado (Fase 1) | O que fazer |
|---|---|
| Monolito / God Class | Criar todas as camadas; mover cada função para sua camada; o arquivo original vira composition root (entry point) ou é removido se não for mais referenciado. |
| Parcialmente em camadas | **Manter** diretórios e nomes que já seguem o padrão (`models/`, `routes/`, `services/`). Criar o que falta (normalmente `controllers/`, `config/`, `middlewares/`). Rotas viram finas. Não renomear camadas só por estética. |
| Já em camadas | Só correções pontuais dos findings. |

Arquivos antigos que ficarem vazios ou sem uso devem ser **removidos** (não deixe código
morto). Se um módulo antigo for importado por script auxiliar, mantenha-o como fachada fina
que reexporta da nova camada, ou atualize o script.

## 5. Preservação de contrato (obrigatória)

A refatoração **não pode quebrar clientes**. Para cada endpoint do inventário da Fase 1:

1. **Mesmo método e caminho** (incluindo parâmetros de rota e query string).
2. **Mesmo status HTTP** para os mesmos cenários (sucesso, validação, não encontrado).
3. **Mesmo formato de resposta**: mesmas chaves de topo, mesmo tipo (objeto/lista/texto),
   mesmas mensagens. Se a rota respondia texto puro, a padronização para JSON só é feita se o
   status for mantido — e deve ser registrada como mudança de contrato no resumo.
4. **Mesmo comando de execução, host padrão local e porta** (ex.: `python app.py`, `npm start`).
5. **Mesmos nomes de campos de entrada** (chaves do JSON do request). Nomes internos podem
   melhorar; as chaves públicas não.
6. **Scripts auxiliares** (seed, migrations) continuam executáveis com o mesmo comando.

**Exceções permitidas (mudanças intencionais de segurança), sempre listadas em
"Contract notes" do relatório e no resumo final:**

- Remover de respostas campos sensíveis (senha, hash, segredo, configuração interna).
- Remover ou desabilitar por padrão endpoints que executam SQL/comandos arbitrários ou apagam
  o banco inteiro (habilitáveis só via variável de ambiente explícita, desligada por padrão).
- Proteção de endpoints administrativos que **hoje respondem sem credencial**: implementar o
  middleware/decorator de autorização **ativável por configuração** (ex.: `ADMIN_TOKEN`); se a
  variável não estiver definida, o comportamento original é mantido e um *warning* é logado no
  boot. Assim o contrato é preservado e a proteção fica pronta para produção.
- Mensagens que descrevem o próprio defeito (ex.: "registro removido, mas dependentes ficaram órfãos") podem ser corrigidas junto com o bug,
  mantendo status e tipo de resposta.

## 6. Configuração

- Todo segredo vem de variável de ambiente. Sem segredo real como default:
  - chave de assinatura ausente → gerar aleatória no boot (`secrets.token_hex(32)` /
    `crypto.randomBytes(32)`) e logar *warning*;
  - credenciais de serviços externos ausentes → `None`/`undefined` e o serviço opera em modo
    desabilitado/simulado.
- `DEBUG` padrão **false**; `HOST` padrão **127.0.0.1**; `PORT` padrão = porta original.
- Suporte opcional a `.env` só se a dependência já existir no projeto (não adicionar pacote só
  para isso).

## 7. Checklist de conformidade MVC (usado na validação da Fase 3)

- [ ] Estrutura de diretórios com models / views(routes) / controllers
- [ ] Configuração extraída para módulo de config (sem segredos hardcoded)
- [ ] Models abstraem os dados (nenhum SQL/ORM fora de models)
- [ ] Views/Routes só roteiam e formatam (sem regra de negócio)
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado (handler/middleware único)
- [ ] Entry point claro (composition root)
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem como antes
