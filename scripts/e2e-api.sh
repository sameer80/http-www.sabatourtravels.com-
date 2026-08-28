#!/bin/bash
set -euo pipefail
API="http://localhost:8000"
PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name"
    FAIL=$((FAIL + 1))
  fi
}

TOKEN=$(curl -sf -X POST "$API/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=demo@example.com&password=demo1234' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

AUTH="Authorization: Bearer $TOKEN"

check "health" "curl -sf $API/api/health"
check "me" "curl -sf $API/api/auth/me -H '$AUTH'"
check "websites" "curl -sf $API/api/websites -H '$AUTH'"
check "dashboard" "curl -sf $API/api/websites/1/dashboard -H '$AUTH'"
check "issues" "curl -sf $API/api/websites/1/issues -H '$AUTH'"
check "pages" "curl -sf $API/api/websites/1/pages -H '$AUTH'"
check "keywords" "curl -sf $API/api/websites/1/keywords -H '$AUTH'"
check "opportunities" "curl -sf $API/api/websites/1/opportunities -H '$AUTH'"
check "tasks" "curl -sf $API/api/websites/1/tasks -H '$AUTH'"
check "internal-links" "curl -sf $API/api/websites/1/internal-links -H '$AUTH'"
check "backlinks" "curl -sf $API/api/websites/1/backlinks/gap -H '$AUTH'"
check "chat" "curl -sf -X POST $API/api/websites/1/chat -H '$AUTH' -H 'Content-Type: application/json' -d '{\"message\":\"What should I fix today?\"}'"
check "frontend" "curl -sf http://localhost:3000"

echo "---"
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
