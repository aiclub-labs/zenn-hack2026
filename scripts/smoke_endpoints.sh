#!/usr/bin/env bash
# smoke_endpoints.sh — azd deploy 後に 4 endpoint へ /healthz 等を叩く。

set -uo pipefail

cd "$(dirname "$0")/.."

ENV_FILE=".azure/$(azd env get-value AZURE_ENV_NAME 2>/dev/null)/$(azd env get-value AZURE_ENV_NAME 2>/dev/null).env"

# azd env get-values を直接読む方が確実
get() { azd env get-values 2>/dev/null | grep "^$1=" | cut -d= -f2- | tr -d '"'; }

API_URL=$(get API_URL)
CHAT_URL=$(get WEB_CHAT_URL)
ADMIN_URL=$(get WEB_ADMIN_URL)
REVIEW_URL=$(get WEB_REVIEW_URL)

echo "=== azd endpoints ==="
printf "API    : %s\n" "${API_URL:-MISSING}"
printf "CHAT   : %s\n" "${CHAT_URL:-MISSING}"
printf "ADMIN  : %s\n" "${ADMIN_URL:-MISSING}"
printf "REVIEW : %s\n" "${REVIEW_URL:-MISSING}"
echo

if [ -z "${API_URL:-}" ]; then
  echo "❌ API_URL not set — azd deploy 未完了の可能性" >&2
  exit 1
fi

check() {
  local label="$1" url="$2"
  local code body
  body=$(curl -s -w "\n%{http_code}" --max-time 10 "$url" 2>/dev/null || echo $'\n000')
  code=$(echo "$body" | tail -1)
  body=$(echo "$body" | sed '$d')
  if [ "$code" = "200" ]; then
    printf "✅ %-25s %s  →  %s\n" "$label" "$code" "${body:0:80}"
  else
    printf "❌ %-25s %s  →  %s\n" "$label" "$code" "${body:0:80}"
  fi
}

echo "=== smoke (API) ==="
check "GET /healthz"             "$API_URL/healthz"
check "GET /health"              "$API_URL/health"
check "GET /version"             "$API_URL/version"
check "GET /schemas?active=true" "$API_URL/schemas?active_only=true"

echo
echo "=== smoke (3 SPA HTML) ==="
[ -n "$CHAT_URL" ]   && check "Chat   SPA index" "$CHAT_URL/"
[ -n "$ADMIN_URL" ]  && check "Admin  SPA index" "$ADMIN_URL/"
[ -n "$REVIEW_URL" ] && check "Review SPA index" "$REVIEW_URL/"
