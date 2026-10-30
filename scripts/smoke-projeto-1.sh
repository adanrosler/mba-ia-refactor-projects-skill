#!/bin/bash
# Smoke test do Projeto 1 — verifica status HTTP de cada rota
B=${1:-http://localhost:5000}
check() {
  local metodo=$1 rota=$2 dados=$3 esperado=$4
  if [ -n "$dados" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -X $metodo "$B$rota" -H "Content-Type: application/json" -d "$dados")
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" -X $metodo "$B$rota")
  fi
  if [ "$code" = "$esperado" ]; then echo "✓ $metodo $rota → $code"; else echo "✗ $metodo $rota → $code (esperado $esperado)"; fi
}
check GET  /                     ""  200
check GET  /health               ""  200
check GET  /produtos             ""  200
check GET  /produtos/1           ""  200
check GET  "/produtos/busca?q=mouse" "" 200
check GET  /usuarios             ""  200
check GET  /usuarios/1           ""  200
check POST /login '{"email":"joao@email.com","senha":"123456"}' 200
check POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1}]}' 201
check GET  /pedidos              ""  200
check GET  /pedidos/usuario/2    ""  200
check PUT  /pedidos/1/status '{"status":"aprovado"}' 200
check GET  /relatorios/vendas    ""  200
check POST /produtos '{"nome":"Smoke","descricao":"t","preco":1,"estoque":1,"categoria":"informatica"}' 201
