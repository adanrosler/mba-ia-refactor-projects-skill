# Progresso — execução autônoma do desafio refactor-arch

## Etapa 0 — Lacuna da análise manual do P1
- Verificado no código: SECRET_KEY hardcoded (`app.py:7`), SQL Injection por concatenação
  (`models.py`, 18 pontos, incl. login) e God Module (`models.py:1-314`). Os 3 confirmados e
  acrescentados em `docs/analise-manual-projeto-1.md` (#9–#11).
- Criado `code-smells-project/.venv` (Python 3.13.15, Flask 3.1.1) — não existia.

## Etapa 1 — Skill escrita
Local: `code-smells-project/.claude/skills/refactor-arch/`
- `SKILL.md` — orquestra as 3 fases; Fase 2 termina com a pergunta `[y/n]` sem tocar em
  arquivos; Fase 3 captura baseline do app original (em 127.0.0.1) antes de refatorar e
  compara depois.
- `references/01-project-analysis.md` … `05-refactoring-playbook.md` (5 áreas obrigatórias).
- Catálogo com 19 anti-patterns (consolidações #3+#4, #11+#12, #20+#21 aplicadas;
  AP-06 com regra HIGH/CRITICAL por debug + 0.0.0.0). Playbook com 16 transformações (T01–T16)
  com antes/depois em Python e JS.

Decisões tomadas:
- **Preservação de contrato** como regra explícita (§5 das guidelines). Mudanças de segurança
  permitidas: remover campos sensíveis das respostas, remover endpoints de SQL arbitrário/reset,
  auth de admin **ativável por env** (`ADMIN_TOKEN`) para não quebrar clientes/baseline.
- `datetime.utcnow` → helper que devolve UTC *naive*, para não quebrar comparações com
  colunas SQLite nem o formato de `str(datetime)` das respostas.
- Baseline do app original capturada com bind local: Flask via `flask run --host 127.0.0.1`;
  Node via shim `-r` que injeta `127.0.0.1` no `listen`.
- Varredura "generalizar, nunca decorar": exemplos com valores dos projetos foram trocados por
  genéricos.

## Etapa 2/3 — Projeto 1 (code-smells-project) — ✅ iteração 1
- Fases 1–2: `claude -p "/refactor-arch"` (sessão nova, `--dangerously-skip-permissions`),
  7 turnos, ~US$0,75. Nenhum arquivo alterado antes da confirmação (`git status` limpo).
  Relatório: 19 findings (CRITICAL 7 | HIGH 3 | MEDIUM 5 | LOW 4) → `reports/audit-project-1.md`.
  Cobre os 11 achados manuais do P1.
- Fase 3: `claude -p "y" --resume <session>` (16 turnos, ~9,7 min, ~US$2,39). Estrutura MVC
  completa (config/, models/, controllers/, views/, services/, middlewares/, validators/);
  `controllers.py`, `models.py`, `database.py` removidos. Validação da skill: 36/38 requisições
  iguais à baseline (as 2 diferenças = `/health` sem `secret_key`/`db_path`, intencional).
- Validação externa: `scripts/smoke-projeto-1.sh` → **14/14 ✓**, servidor em 127.0.0.1:5000
  (log em `docs/logs/smoke-projeto-1.txt`; saída da Fase 3 em `docs/logs/fase3-projeto-1.md`).
- Observação: o boot do Flask leva ~35 s nesta máquina (inclusive um app Flask mínimo) — é do
  ambiente, não da refatoração.
