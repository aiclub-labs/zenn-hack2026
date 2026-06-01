#!/usr/bin/env bash
# inject_kv_secrets.sh — KV に Day 2 必須 7 secret を投入する。
#
# 使い方:
#   bash scripts/inject_kv_secrets.sh \
#     <webhook-schema-updates> \
#     <webhook-pending-review> \
#     <webhook-expired> \
#     <webhook-cost-alert>
#
# AOAI / AISEARCH key は azd provision 後の Azure リソースから CLI で自動取得する。
# Cosmos は disableLocalAuth=true なので PLACEHOLDER のまま。

set -euo pipefail

KV="${KV_NAME:-kv-hack2026-tyu3o4}"
RG="${RG_NAME:-rg-hack2026}"

if [ $# -ne 4 ]; then
  echo "usage: $0 <wh-schema> <wh-review> <wh-expired> <wh-cost>" >&2
  exit 1
fi
WH_SCHEMA="$1"
WH_REVIEW="$2"
WH_EXPIRED="$3"
WH_COST="$4"

echo "[1/3] Discord webhook 4 件を KV へ"
az keyvault secret set --vault-name "$KV" -n DISCORD-WEBHOOK-URL-SCHEMA-UPDATES --value "$WH_SCHEMA" -o none
az keyvault secret set --vault-name "$KV" -n DISCORD-WEBHOOK-URL-PENDING-REVIEW --value "$WH_REVIEW" -o none
az keyvault secret set --vault-name "$KV" -n DISCORD-WEBHOOK-URL-EXPIRED        --value "$WH_EXPIRED" -o none
az keyvault secret set --vault-name "$KV" -n DISCORD-WEBHOOK-URL-COST-ALERT     --value "$WH_COST" -o none

echo "[2/3] AOAI key (Foundry hub 経由) を auto-pull"
AOAI_NAME=$(az cognitiveservices account list -g "$RG" --query "[?kind=='OpenAI'].name | [0]" -o tsv 2>/dev/null || true)
if [ -n "${AOAI_NAME:-}" ]; then
  AOAI_KEY=$(az cognitiveservices account keys list -g "$RG" -n "$AOAI_NAME" --query key1 -o tsv)
  az keyvault secret set --vault-name "$KV" -n AOAI-API-KEY --value "$AOAI_KEY" -o none
  echo "  ✓ $AOAI_NAME → AOAI-API-KEY"
else
  echo "  ⚠ AOAI resource not found in $RG — skip (provision 後に再実行)"
fi

echo "[3/3] AISEARCH admin key を auto-pull"
SEARCH_NAME=$(az search service list -g "$RG" --query "[0].name" -o tsv 2>/dev/null || true)
if [ -n "${SEARCH_NAME:-}" ]; then
  SEARCH_KEY=$(az search admin-key show --service-name "$SEARCH_NAME" -g "$RG" --query primaryKey -o tsv)
  az keyvault secret set --vault-name "$KV" -n AISEARCH-ADMIN-KEY --value "$SEARCH_KEY" -o none
  echo "  ✓ $SEARCH_NAME → AISEARCH-ADMIN-KEY"
else
  echo "  ⚠ AI Search resource not found in $RG — skip"
fi

echo
echo "✅ done. 確認:"
echo "   az keyvault secret list --vault-name $KV -o table"
