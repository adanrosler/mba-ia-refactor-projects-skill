#!/bin/bash
# Smoke test do Projeto 1 — verifica status HTTP de cada rota
# Rotas protegidas: 401 sem token e com token inválido; sucesso com $ADMIN_TOKEN (se exportado).
# Rode também com o servidor iniciado SEM ADMIN_TOKEN: as rotas protegidas devem seguir em 401.
B=${1:-http://localhost:5000}
check() {
  local metodo=$1 rota=$2 dados=$3 esperado=$4 token=$5 rotulo=$6
  local args=(-s -o /dev/null -w "%{http_code}" -X "$metodo" "$B$rota")
  [ -n "$dados" ] && args+=(-H "Content-Type: application/json" -d "$dados")
  [ -n "$token" ] && args+=(-H "Authorization: Bearer $token")
  code=$(curl "${args[@]}")
  if [ "$code" = "$esperado" ]; then echo "✓ $metodo $rota$rotulo → $code"; else echo "✗ $metodo $rota$rotulo → $code (esperado $esperado)"; fi
}
# protegida: sem token → 401, token inválido → 401, token válido → <esperado>
protegida() {
  local metodo=$1 rota=$2 dados=$3 esperado=$4
  check "$metodo" "$rota" "$dados" 401 ""         " (sem token)"
  check "$metodo" "$rota" "$dados" 401 "invalido" " (token inválido)"
  [ -n "$ADMIN_TOKEN" ] && check "$metodo" "$rota" "$dados" "$esperado" "$ADMIN_TOKEN" " (com token)"
}
[ -z "$ADMIN_TOKEN" ] && echo "- ADMIN_TOKEN não exportado: verificações com token válido puladas (modo sem credencial)"

# rotas públicas (contrato original)
check GET  /                     ""  200
check GET  /health               ""  200
check GET  /produtos             ""  200
check GET  /produtos/1           ""  200
check GET  "/produtos/busca?q=mouse" "" 200
check POST /login '{"email":"joao@email.com","senha":"123456"}' 200
check POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1}]}' 201
check GET  /pedidos/usuario/2    ""  200

# rotas sensíveis (AP-04): autenticação obrigatória e fail-closed
protegida GET  /usuarios          ""  200
protegida GET  /usuarios/1        ""  200
protegida GET  /pedidos           ""  200
protegida PUT  /pedidos/1/status '{"status":"aprovado"}' 200
protegida GET  /relatorios/vendas ""  200
protegida POST /produtos '{"nome":"Smoke","descricao":"t","preco":1,"estoque":1,"categoria":"informatica"}' 201
protegida PUT  /produtos/1 '{"nome":"Notebook Gamer","descricao":"t","preco":3500,"estoque":10,"categoria":"informatica"}' 200
# ferramentas de admin: 401 sem credencial; com token e sem ENABLE_ADMIN_ENDPOINTS=1 → 403
protegida POST /admin/query '{"sql":"SELECT 1"}' 403
check POST /admin/reset-db "" 401 ""         " (sem token)"
check POST /admin/reset-db "" 401 "invalido" " (token inválido)"
# DELETE por último: apaga o produto criado acima (se houver token)
if [ -n "$ADMIN_TOKEN" ]; then
  ID=$(curl -s "$B/produtos" | grep -o '"id": *[0-9]*' | grep -o '[0-9]*$' | sort -n | tail -1)
  protegida DELETE /produtos/$ID "" 200
else
  protegida DELETE /produtos/1 "" 200
fi
