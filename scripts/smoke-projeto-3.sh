#!/bin/bash
# Smoke test do Projeto 3 — verifica status HTTP de cada rota (idempotente)
B=${1:-http://localhost:5000}
J="Content-Type: application/json"
ok() { if [ "$2" = "$3" ]; then echo "✓ $1 → $2"; else echo "✗ $1 → $2 (esperado $3)"; fi; }
get() { ok "GET $1" "$(curl -s -o /dev/null -w "%{http_code}" "$B$1")" 200; }
req() { curl -s -w "\n%{http_code}" -X "$1" "$B$2" -H "$J" ${3:+-d "$3"}; }
code() { echo "$1" | tail -1; }
idof() { echo "$1" | sed '$d' | grep -o '"id": *[0-9]*' | head -1 | grep -o '[0-9]*$'; }

for ep in / /health /tasks /tasks/1 "/tasks/search?q=login" /tasks/stats /users /users/1 /users/1/tasks /reports/summary /reports/user/1 /categories; do get "$ep"; done

r=$(req POST /login '{"email":"joao@email.com","password":"1234"}'); ok "POST /login" "$(code "$r")" 200

EMAIL="smoke$(date +%s)@email.com"
r=$(req POST /users "{\"name\":\"Smoke\",\"email\":\"$EMAIL\",\"password\":\"senha123\",\"role\":\"user\"}"); ok "POST /users" "$(code "$r")" 201; UID_=$(idof "$r")
r=$(req PUT /users/$UID_ '{"name":"Smoke Editado"}'); ok "PUT /users/:id" "$(code "$r")" 200

r=$(req POST /tasks '{"title":"Smoke task","description":"t","priority":2,"user_id":1,"category_id":1,"due_date":"2026-12-31","tags":["smoke"]}'); ok "POST /tasks" "$(code "$r")" 201; TID=$(idof "$r")
r=$(req PUT /tasks/$TID '{"status":"in_progress"}'); ok "PUT /tasks/:id" "$(code "$r")" 200
r=$(req DELETE /tasks/$TID); ok "DELETE /tasks/:id" "$(code "$r")" 200

r=$(req POST /categories "{\"name\":\"Smoke $(date +%s)\",\"description\":\"t\",\"color\":\"#123456\"}"); ok "POST /categories" "$(code "$r")" 201; CID=$(idof "$r")
r=$(req PUT /categories/$CID '{"description":"editada"}'); ok "PUT /categories/:id" "$(code "$r")" 200
r=$(req DELETE /categories/$CID); ok "DELETE /categories/:id" "$(code "$r")" 200

r=$(req DELETE /users/$UID_); ok "DELETE /users/:id" "$(code "$r")" 200
