#!/bin/bash
# Smoke test do Projeto 2 — verifica status HTTP de cada rota
# Rotas protegidas: 401 sem token e com token inválido; 200 com $ADMIN_TOKEN (se exportado).
# Rode também com o servidor iniciado SEM ADMIN_TOKEN: as rotas protegidas devem seguir em 401.
B=${1:-http://localhost:3000}
check() {
  local metodo=$1 rota=$2 dados=$3 esperado=$4 token=$5 rotulo=$6
  local args=(-s -o /dev/null -w "%{http_code}" -X "$metodo" "$B$rota")
  [ -n "$dados" ] && args+=(-H "Content-Type: application/json" -d "$dados")
  [ -n "$token" ] && args+=(-H "Authorization: Bearer $token")
  code=$(curl "${args[@]}")
  if [ "$code" = "$esperado" ]; then echo "✓ $metodo $rota$rotulo → $code"; else echo "✗ $metodo $rota$rotulo → $code (esperado $esperado)"; fi
}
check POST /api/checkout '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}' 200
check POST /api/checkout '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}' 400

for rota in "GET /api/admin/financial-report" "DELETE /api/users/1"; do
  set -- $rota
  check "$1" "$2" "" 401 ""        " (sem token)"
  check "$1" "$2" "" 401 "invalido" " (token inválido)"
done
if [ -n "$ADMIN_TOKEN" ]; then
  check GET    /api/admin/financial-report "" 200 "$ADMIN_TOKEN" " (com token)"
  check DELETE /api/users/1                "" 200 "$ADMIN_TOKEN" " (com token)"
else
  echo "- ADMIN_TOKEN não exportado: verificações com token válido puladas (modo sem credencial)"
fi
