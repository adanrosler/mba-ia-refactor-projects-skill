# Contexto para o Claude Code — Desafio refactor-arch (MBA Full Cycle)

## Objetivo
Criar a skill `refactor-arch` (Claude Code) que, em 3 fases, analisa um projeto, gera relatório de
auditoria de anti-patterns e refatora para MVC. Deve funcionar nos 3 projetos do repo:
- `code-smells-project/` — Python/Flask, e-commerce, monolito (porta 5000)
- `ecommerce-api-legacy/` — Node.js/Express, LMS com checkout, God Class (porta 3000)
- `task-manager-api/` — Python/Flask, task manager, já em camadas (porta 5000, rodar `seed.py` antes)

Enunciado completo e critérios: ver o README do desafio (requisitos resumidos abaixo).

## Status
- [x] Etapa 0 — baseline de endpoints: `docs/baseline-projeto-{1,2,3}.txt`; smoke tests: `scripts/smoke-projeto-{1,2,3}.sh`
- [x] Etapa 1 — análise manual: `docs/analise-manual-projeto-{1,2,3}.md` (8, 13 e 12 achados)
- [x] Etapa 2 — design da skill: `docs/decisoes-design-skill.md`
- [ ] Etapa 3 — escrever os 5 references (um por vez, com revisão humana entre eles)
- [ ] Etapa 4 — escrever o SKILL.md
- [ ] Etapa 5 — rodar no projeto 1 e iterar
- [ ] Etapa 6 — copiar e rodar nos projetos 2 e 3
- [ ] Etapa 7 — README final e entrega

## Requisitos obrigatórios da skill
- Path: `code-smells-project/.claude/skills/refactor-arch/` (nome `refactor-arch` e arquivo `SKILL.md` não podem mudar)
- 3 fases: Análise → Auditoria (relatório + PAUSA pedindo confirmação) → Refatoração MVC + validação (boot + endpoints)
- References em Markdown cobrindo: análise de projeto, catálogo de anti-patterns, template de relatório,
  guidelines MVC, playbook de refatoração
- Catálogo: mínimo 8 anti-patterns, severidades distribuídas (CRITICAL/HIGH/MEDIUM/LOW), incluindo detecção de APIs deprecated
- Playbook: mínimo 8 transformações com exemplos de código antes/depois
- Severidades: CRITICAL (segurança grave, God Class), HIGH (violação forte de MVC/SOLID), MEDIUM (duplicação, N+1, validação ausente), LOW (nomes, magic numbers)
- Cada finding do relatório: arquivo e linhas exatos; ordenados CRITICAL → LOW

## Regras de trabalho
1. **Generalizar, nunca decorar**: os references NÃO podem citar nomes de arquivos, linhas ou valores
   específicos dos 3 projetos. Use os achados manuais só como inspiração para padrões genéricos,
   com sinais de detecção em Python E JavaScript. A skill tem que funcionar em qualquer projeto.
2. **Não modificar o código dos 3 projetos** nesta fase. Só a skill altera código, na Etapa 5.
3. Um reference por vez; ao terminar, pare e espere minha revisão.
4. Commits em português, adicionando paths explícitos (nunca `git add .`).

## Ambiente
- Repo em `~/dev/mba-ia-refactor-projects-skill` (fora do OneDrive, de propósito)
- Proxy corporativo: `NODE_EXTRA_CA_CERTS=~/corp-ca.pem` já configurado no `~/.zshrc`
- `git config core.fileMode false` neste repo
- Cada projeto Python tem seu próprio `.venv`
