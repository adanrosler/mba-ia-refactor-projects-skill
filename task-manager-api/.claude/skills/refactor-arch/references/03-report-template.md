# 03 — Template do Relatório de Auditoria (Fase 2)

O relatório é impresso **inteiro** na resposta da Fase 2 (não resuma, não omita findings) e é
seguido pela pergunta de confirmação. Nenhum arquivo é criado ou alterado nesta fase.

## Regras de preenchimento

1. **Ordenação**: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade,
   ordene por impacto (segurança antes de arquitetura antes de qualidade).
2. **Numeração contínua**: `#1`, `#2`, … na ordem final.
3. **Localização exata**: `File:` sempre com `caminho/relativo:linha` ou `:inicio-fim`; vários
   pontos separados por vírgula; vários arquivos em linhas `File:` separadas por `;`.
   Caminhos relativos à raiz do projeto.
4. **Título** = nome do anti-pattern do catálogo + ID (`AP-xx`). Se um problema não se encaixa
   em nenhum AP, use `AP-00 — <nome>` e justifique a severidade pela escala.
5. **Description** descreve o que foi visto **neste** código (cite o trecho/valor relevante,
   mascarando segredos: mostre no máximo os 4 primeiros caracteres + `***`).
6. **Impact** explica a consequência concreta (o que um atacante/desenvolvedor sofre).
7. **Recommendation** cita a transformação do playbook (`Txx`) e o destino na arquitetura MVC.
   Em findings AP-04, a recomendação é sempre autenticação **obrigatória e fail-closed** (401
   sem token e 401 quando a credencial não estiver configurada) — nunca "opcional", "ativável
   por env" ou "desligada por padrão". Liste os endpoints que passarão a exigir credencial.
8. O **Summary** precisa bater com a contagem de findings listados.
9. A seção **Deprecated APIs** é obrigatória: liste cada uso ou escreva `None found`.
10. Mínimo esperado: **5 findings**, com pelo menos **1 CRITICAL ou HIGH**. Se encontrar menos,
    reexamine o projeto com o catálogo antes de concluir (projetos legados quase sempre têm
    mais).

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <linguagem> + <framework> (<banco>)
Files:   <N> analyzed | ~<L> lines of code
Architecture: <classificação da Fase 1>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>  (Total: <n>)

## Findings

### #1 [CRITICAL] <Nome do anti-pattern> (AP-xx)
File: <caminho>:<linhas>
Description: <o que foi encontrado, com evidência>
Impact: <consequência>
Recommendation: <correção> (T<xx>) → <camada/arquivo alvo>

### #2 [CRITICAL] ...

...

## Deprecated APIs
| File:Line | Deprecated | Modern replacement |
|---|---|---|
| <caminho>:<linha> | <api> | <substituto> |

## Refactoring Plan (Phase 3 preview)
Strategy: <reestruturação completa | melhoria incremental> — <motivo>
Target structure:
<árvore resumida de diretórios propostos>
Contract notes: <mudanças de comportamento intencionais e justificadas, ex.: campos sensíveis
removidos das respostas; ou "nenhuma">

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo de finding bem preenchido (genérico)

```markdown
### #3 [CRITICAL] SQL Injection (AP-02)
File: data/orders.py:31, 58-61, 102
Description: Parâmetros de rota e do corpo são concatenados nas queries
(`"... WHERE id = " + str(id)`); a função de login monta o WHERE com e-mail e senha
concatenados.
Impact: Um atacante lê ou altera qualquer tabela e faz login sem senha com `' OR '1'='1`.
Recommendation: Parametrizar todas as queries com placeholders (T02) → camada Model.
```
