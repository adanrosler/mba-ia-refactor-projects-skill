---
name: refactor-arch
description: Audita e refatora um projeto backend para o padrão MVC em 3 fases — (1) análise da stack e da arquitetura, (2) relatório de auditoria de anti-patterns com severidade e arquivo:linha, pausando para confirmação, (3) refatoração para MVC com validação de boot e endpoints. Agnóstica de tecnologia (Python/Flask, Node/Express e outras). Use quando o usuário pedir /refactor-arch, auditoria arquitetural, detecção de code smells ou refatoração para MVC.
---

# refactor-arch — Auditoria e Refatoração Arquitetural

Você é um arquiteto de software sênior. Execute as 3 fases **em ordem**, usando os arquivos de
referência desta skill como fonte de conhecimento:

| Arquivo | Uso |
|---|---|
| `references/01-project-analysis.md` | Fase 1 — detectar stack, banco, domínio, arquitetura, endpoints |
| `references/02-anti-patterns-catalog.md` | Fase 2 — catálogo de anti-patterns, sinais e severidade |
| `references/03-report-template.md` | Fase 2 — formato obrigatório do relatório |
| `references/04-mvc-guidelines.md` | Fase 3 — arquitetura alvo e regras de preservação de contrato |
| `references/05-refactoring-playbook.md` | Fase 3 — transformações antes/depois |

Os caminhos acima são relativos ao diretório desta skill (`.claude/skills/refactor-arch/`).

## Regras gerais

- **Escopo:** trabalhe apenas dentro do diretório atual (raiz do projeto). Não leia nem altere
  nada fora dele. Nunca altere `.claude/`, `.git/`, `node_modules/` ou ambientes virtuais.
- **Evidência:** todo finding precisa de arquivo e linha conferidos no código.
- **Sem git:** não faça commit, push, checkout nem stash — o humano versiona o resultado.
- **Servidores:** em testes, suba a aplicação sempre em `127.0.0.1`, em background, com log em
  arquivo temporário, e **encerre todos os processos que iniciar** antes de terminar
  (inclusive em caso de erro).
- **Arquivos temporários** (logs, capturas de resposta, backups de banco) ficam num diretório
  criado com `mktemp -d`, fora do projeto.

---

## FASE 1 — Análise do projeto (somente leitura)

1. Leia `references/01-project-analysis.md`.
2. Liste os arquivos-fonte (excluindo dependências/artefatos) e conte linhas.
3. Leia **todos** os arquivos-fonte e manifestos (são a base das fases seguintes).
4. Detecte linguagem, framework, dependências, banco, tabelas, domínio, entry point (comando,
   host, porta), scripts auxiliares (seed etc.) e o inventário completo de endpoints.
5. Classifique a arquitetura (monolito / God Class / parcialmente em camadas / em camadas).
6. Imprima o bloco `PHASE 1: PROJECT ANALYSIS` no formato da seção 9 da referência.

Siga direto para a Fase 2 (sem pedir confirmação aqui).

## FASE 2 — Auditoria (somente leitura)

1. Leia `references/02-anti-patterns-catalog.md` e `references/03-report-template.md`.
2. Percorra **cada** anti-pattern AP-01…AP-19 contra o código, usando os sinais de detecção
   (`grep -n` ajuda a obter linhas exatas). Faça também a varredura de APIs deprecated (AP-10)
   pela tabela do catálogo.
3. Monte o relatório **exatamente** no template: findings numerados, ordenados
   CRITICAL → HIGH → MEDIUM → LOW, com `File: caminho:linhas`, Description, Impact e
   Recommendation (com `Txx`); seção Deprecated APIs; Refactoring Plan com a estratégia
   (reestruturação completa vs. incremental, conforme `04-mvc-guidelines.md` §4), estrutura
   alvo e "Contract notes".
4. Confira: Summary bate com os findings; mínimo de 5 findings e pelo menos 1 CRITICAL/HIGH.
5. **PARE.** Sua resposta final desta fase deve conter o bloco da Fase 1 **e** o relatório
   completo (nunca apenas um resumo), terminando com a linha:

   `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`

   **Não crie, altere nem apague nenhum arquivo antes de receber a confirmação.** Encerre a
   resposta e aguarde a próxima mensagem do usuário.
   - Resposta `y`/`yes`/`sim`/`s` (ou equivalente afirmativo) → Fase 3.
   - Qualquer outra resposta → não modifique nada e encerre.

## FASE 3 — Refatoração e validação (somente após confirmação)

Leia `references/04-mvc-guidelines.md` e `references/05-refactoring-playbook.md`.

### 3.1 Preparar ambiente e capturar a baseline (antes de tocar no código)

1. `TMP=$(mktemp -d)`.
2. Ambiente: Python → use `.venv`/`venv` do projeto; se não houver, crie `.venv` e instale o
   manifesto. Node → `npm install` se `node_modules/` não existir.
3. Estado do banco: se o projeto usa banco em arquivo, faça backup dos arquivos de banco
   existentes para `$TMP` e defina como **resetar** o estado antes de cada rodada de testes
   (apagar o arquivo gerado no boot, ou rodar o script de seed existente). Banco em memória
   reseta sozinho a cada boot.
4. Monte o **plano de requisições** a partir do inventário de endpoints: todas as rotas de
   leitura + as de escrita com payloads válidos (derivados das validações do código e dos
   dados de seed) + pelo menos um caso de erro de validação/não encontrado por recurso.
   Ordene para que escritas que apagam dados venham por último. Não inclua endpoints que
   executam SQL arbitrário ou apagam o banco inteiro.
5. Suba a aplicação **original** sem editar o código e **sempre em `127.0.0.1`** (nunca
   `0.0.0.0`), na porta original:
   - Flask com host fixo no código → use a CLI: `<venv>/bin/flask --app <módulo> run --host
     127.0.0.1 --port <porta>` (debug fica desligado).
   - Node com `listen` sem host → pré-carregue um shim criado em `$TMP`:
     ```js
     // $TMP/bind-local.js — uso: node -r $TMP/bind-local.js <entry>
     const net = require('net'); const orig = net.Server.prototype.listen;
     net.Server.prototype.listen = function (...a) {
       if (typeof a[0] === 'number' && typeof a[1] !== 'string') a.splice(1, 0, '127.0.0.1');
       return orig.apply(this, a);
     };
     ```
   - Outros stacks: use a opção de host do runtime/CLI ou variável de ambiente.
   Aguarde a porta responder, execute o plano com `curl -s -w '\n%{http_code}'` e salve
   `método rota → status + corpo` em `$TMP/baseline.txt`. Encerre o servidor e restaure/resete o
   banco.

### 3.2 Refatorar

1. Aplique a estratégia do Refactoring Plan:
   - **Monolito/God Class** → criar a estrutura MVC completa (config, models, views/routes,
     controllers, middlewares, services se necessário) e reduzir o entry point a composition
     root.
   - **Parcialmente em camadas** → manter o que já está correto, criar as camadas que faltam
     (controllers, config, middlewares), afinar rotas, corrigir os findings.
2. Corrija **todos** os findings do relatório usando as transformações `Txx` indicadas. Se
   algum não puder ser corrigido sem quebrar contrato, aplique a mitigação prevista em
   `04-mvc-guidelines.md` §5 e registre.
3. Preserve contrato (§5 das guidelines): mesmas rotas, métodos, status, formatos, chaves de
   entrada, comando de execução e porta; scripts auxiliares continuam funcionando.
4. Remova arquivos antigos que ficaram sem uso e imports mortos. Não deixe arquivos de banco,
   logs ou `__pycache__` novos dentro do projeto.

### 3.3 Validar (obrigatório — repetir até passar)

1. **Compilação/sintaxe:** Python → `python -m compileall -q <pastas do projeto>` (excluindo
   venv); Node → `node --check` em cada arquivo `.js` alterado.
2. **Boot:** resete o banco (e rode o seed, se o projeto tiver script de seed), suba a
   aplicação com o **mesmo comando original** em `127.0.0.1`; confirme no log que iniciou sem
   erros/tracebacks.
3. **Endpoints:** execute o mesmo plano de requisições e salve em `$TMP/after.txt`. Compare com
   a baseline: para cada requisição, **status igual** e **mesmas chaves de topo/tipo de corpo**,
   exceto as mudanças intencionais listadas em "Contract notes".
4. **Verificação de anti-patterns:** repita os greps de detecção dos findings corrigidos
   (ex.: concatenação em SQL, segredos literais, `print(`/`console.log(`, APIs deprecated) e
   confirme que não restam ocorrências.
5. Se qualquer verificação falhar: corrija e repita a validação. Encerre o servidor ao final.
6. Restaure o estado do banco: apague os bancos criados pela validação e devolva os backups
   de `$TMP` (se havia).

### 3.4 Saída final da Fase 3

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios/arquivos-fonte, sem dependências>

## Changes by finding
#<n> [SEV] <anti-pattern> → <o que foi feito> (<arquivos>)
...

## Contract notes
<mudanças intencionais de comportamento, ou "None">

## Validation
  ✓/✗ Application boots without errors (<comando>)
  ✓/✗ All endpoints respond correctly (<x>/<y> requests match baseline)
  ✓/✗ Zero anti-patterns remaining from the report (<detalhe de pendências, se houver>)
  ✓/✗ MVC checklist (04-mvc-guidelines §7)

## How to run
<comando de execução e variáveis de ambiente suportadas>
================================
```

Use ✗ honestamente quando algo não passou e explique o motivo.
