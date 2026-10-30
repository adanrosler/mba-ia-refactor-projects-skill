#!/bin/bash
# Smoke test do Projeto 2 — verifica status HTTP de cada rota
B=${1:-http://localhost:3000}
check() {
  local metodo=$1 rota=$2 dados=$3 esperado=$4
  if [ -n "$dados" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -X $metodo "$B$rota" -H "Content-Type: application/json" -d "$dados")
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" -X $metodo "$B$rota")
  fi
  if [ "$code" = "$esperado" ]; then echo "✓ $metodo $rota → $code"; else echo "✗ $metodo $rota → $code (esperado $esperado)"; fi
}
check POST /api/checkout '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}' 200
check POST /api/checkout '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}' 400
check GET  /api/admin/financial-report "" 200
check DELETE /api/users/1 "" 200
