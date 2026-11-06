#!/bin/bash
# Smoke test do Projeto 3 — verifica status HTTP de cada rota (idempotente)
# Rotas sensíveis (AP-04): 401 sem token e com token inválido, 403 com usuário comum,
# sucesso com o token do admin do seed (obtido via POST /login).
B=${1:-http://localhost:5000}
J="Content-Type: application/json"
ok() { if [ "$2" = "$3" ]; then echo "✓ $1 → $2"; else echo "✗ $1 → $2 (esperado $3)"; fi; }
get() { ok "GET $1" "$(curl -s -o /dev/null -w "%{http_code}" "$B$1")" 200; }
# req MÉTODO ROTA [DADOS] [TOKEN]
req() { curl -s -w "\n%{http_code}" -X "$1" "$B$2" -H "$J" ${3:+-d "$3"} ${4:+-H "Authorization: Bearer $4"}; }
code() { echo "$1" | tail -1; }
idof() { echo "$1" | sed '$d' | grep -o '"id": *[0-9]*' | head -1 | grep -o '[0-9]*$'; }
tokenof() { echo "$1" | sed '$d' | grep -o '"token": *"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/'; }
# protegida MÉTODO ROTA DADOS: sem token → 401, token inválido → 401, usuário comum → 403
protegida() {
  ok "$1 $2 (sem token)"        "$(code "$(req "$1" "$2" "$3")")" 401
  ok "$1 $2 (token inválido)"   "$(code "$(req "$1" "$2" "$3" invalido)")" 401
  ok "$1 $2 (usuário comum)"    "$(code "$(req "$1" "$2" "$3" "$USER_TOKEN")")" 403
}

for ep in / /health /tasks /tasks/1 "/tasks/search?q=login" /tasks/stats /users /users/1 /users/1/tasks /categories; do get "$ep"; done

r=$(req POST /login '{"email":"joao@email.com","password":"1234"}'); ok "POST /login (admin)" "$(code "$r")" 200; ADMIN_TOKEN=$(tokenof "$r")
r=$(req POST /login '{"email":"maria@email.com","password":"abcd"}'); ok "POST /login (usuário comum)" "$(code "$r")" 200; USER_TOKEN=$(tokenof "$r")

# relatórios: só admin/manager
protegida GET /reports/summary
protegida GET /reports/user/1
ok "GET /reports/summary (admin)" "$(code "$(req GET /reports/summary "" "$ADMIN_TOKEN")")" 200
ok "GET /reports/user/1 (admin)"  "$(code "$(req GET /reports/user/1 "" "$ADMIN_TOKEN")")" 200

# escalonamento de papel: criar admin exige admin autenticado
ADM="{\"name\":\"Smoke Admin\",\"email\":\"smokeadm$(date +%s)@email.com\",\"password\":\"senha123\",\"role\":\"admin\"}"
protegida POST /users "$ADM"
r=$(req POST /users "$ADM" "$ADMIN_TOKEN"); ok "POST /users role=admin (admin)" "$(code "$r")" 201; AID=$(idof "$r")

# cadastro com papel padrão continua público
EMAIL="smoke$(date +%s)@email.com"
r=$(req POST /users "{\"name\":\"Smoke\",\"email\":\"$EMAIL\",\"password\":\"senha123\",\"role\":\"user\"}"); ok "POST /users role=user (anônimo)" "$(code "$r")" 201; UID_=$(idof "$r")
ok "PUT /users/:id (sem token)" "$(code "$(req PUT /users/$UID_ '{"name":"X"}')")" 401
ok "PUT /users/:id (outro usuário)" "$(code "$(req PUT /users/$UID_ '{"name":"X"}' "$USER_TOKEN")")" 403
r=$(req PUT /users/$UID_ '{"name":"Smoke Editado"}' "$ADMIN_TOKEN"); ok "PUT /users/:id (admin)" "$(code "$r")" 200

r=$(req POST /tasks '{"title":"Smoke task","description":"t","priority":2,"user_id":1,"category_id":1,"due_date":"2026-12-31","tags":["smoke"]}'); ok "POST /tasks" "$(code "$r")" 201; TID=$(idof "$r")
r=$(req PUT /tasks/$TID '{"status":"in_progress"}'); ok "PUT /tasks/:id" "$(code "$r")" 200
r=$(req DELETE /tasks/$TID); ok "DELETE /tasks/:id" "$(code "$r")" 200

r=$(req POST /categories "{\"name\":\"Smoke $(date +%s)\",\"description\":\"t\",\"color\":\"#123456\"}"); ok "POST /categories" "$(code "$r")" 201; CID=$(idof "$r")
r=$(req PUT /categories/$CID '{"description":"editada"}'); ok "PUT /categories/:id" "$(code "$r")" 200
protegida DELETE /categories/$CID
r=$(req DELETE /categories/$CID "" "$ADMIN_TOKEN"); ok "DELETE /categories/:id (admin)" "$(code "$r")" 200

protegida DELETE /users/$UID_
r=$(req DELETE /users/$UID_ "" "$ADMIN_TOKEN"); ok "DELETE /users/:id (admin)" "$(code "$r")" 200
r=$(req DELETE /users/$AID "" "$ADMIN_TOKEN"); ok "DELETE /users/:id (admin criado no smoke)" "$(code "$r")" 200
