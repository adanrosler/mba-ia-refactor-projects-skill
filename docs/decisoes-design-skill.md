# Decisões de Design da Skill refactor-arch

## Estrutura
- `SKILL.md`: orquestra as 3 fases (processo). Curto e estável.
- `references/`: conhecimento consultado sob demanda, um arquivo por área obrigatória:
  - `01-project-analysis.md` — heurísticas de detecção de stack, domínio e arquitetura (Fase 1)
  - `02-anti-patterns-catalog.md` — anti-patterns com sinais de detecção e severidade (Fase 2)
  - `03-report-template.md` — formato padronizado do relatório (Fase 2)
  - `04-mvc-guidelines.md` — arquitetura MVC alvo (Fase 3)
  - `05-refactoring-playbook.md` — transformações antes/depois (Fase 3)

## Decisões
1. **Agnóstica de stack**: cada anti-pattern tem descrição genérica e sinais de detecção em Python e JavaScript.
2. **Catálogo derivado da análise manual**: os achados dos 3 projetos foram generalizados em anti-patterns.
3. **Fase 3 adaptativa**: monolito → reestruturação completa; projeto em camadas → melhoria incremental.
4. **Pausa obrigatória**: a Fase 2 termina pedindo confirmação explícita antes de modificar arquivos.
5. **Validação independente**: a skill valida boot + endpoints por conta própria; os scripts em `scripts/` são uma conferência externa, fora da skill.
