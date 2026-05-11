#!/usr/bin/env bash
# AOAI provisioning — wraps §6.1–6.2.
# Run on day 7 (~May 5) once region availability is confirmed (D7).
#
# Usage:
#   ./scripts/aoai-provision.sh <region> [<aoai_name>] [<rg_name>]
#
# Defaults:
#   aoai_name = aoai-hack2026
#   rg_name   = rg-hack2026-shared
#
# Idempotent: re-run is safe (will report "already exists" rather than error).

set -uo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <region> [<aoai_name>] [<rg_name>]" >&2
  echo "example: $0 swedencentral" >&2
  exit 1
fi

LOC="$1"
NAME="${2:-aoai-hack2026}"
RG="${3:-rg-hack2026-shared}"

# Model deployments (name, model-name, model-version, sku-capacity, sku-name)
# gpt-4o-mini = default chat (Scanner / Arbiter); gpt-4o = arbitration / cross-page coherence
# text-embedding-3-small = retrieval. Capacities sized for $200 / 30-day budget.
# All deployments use GlobalStandard in swedencentral: (1) text-embedding-3-small has no `Standard` SKU here,
# (2) gpt-4o-mini 2024-07-18 was rejected on Standard with ServiceModelDeprecated for new deploys (cutoff
# 2026-03-31, even though the model registry still shows GA until 2026-10-01 inference deprecation).
# GlobalStandard accepts the same model version.
DEPLOYMENTS=(
  "gpt-4o-mini|gpt-4o-mini|2024-07-18|50|GlobalStandard"
  "gpt-4o|gpt-4o|2024-11-20|10|GlobalStandard"
  "text-embedding-3-small|text-embedding-3-small|1|50|GlobalStandard"
)

command -v az >/dev/null || { echo "az CLI not found" >&2; exit 1; }

echo "==> [1/4] Check RG $RG exists"
if ! az group show -n "$RG" >/dev/null 2>&1; then
  echo "    RG $RG not found — has Phase 2 (azd provision) run? Aborting." >&2
  exit 1
fi

echo "==> [2/4] Create AOAI account $NAME in $LOC"
if az cognitiveservices account show -g "$RG" -n "$NAME" >/dev/null 2>&1; then
  echo "    $NAME already exists (no-op)"
else
  az cognitiveservices account create \
    -g "$RG" -n "$NAME" -l "$LOC" \
    --kind OpenAI --sku S0 \
    --custom-domain "$NAME" \
    --assign-identity \
    --yes \
    --only-show-errors >/dev/null
  echo "    $NAME created"
fi

echo "==> [3/4] Deploy models"
for entry in "${DEPLOYMENTS[@]}"; do
  IFS='|' read -r DEP_NAME MODEL_NAME MODEL_VERSION CAPACITY SKU_NAME <<<"$entry"
  if az cognitiveservices account deployment show \
    -g "$RG" -n "$NAME" --deployment-name "$DEP_NAME" >/dev/null 2>&1; then
    echo "    deployment $DEP_NAME exists (no-op)"
  else
    az cognitiveservices account deployment create \
      -g "$RG" -n "$NAME" \
      --deployment-name "$DEP_NAME" \
      --model-name "$MODEL_NAME" --model-version "$MODEL_VERSION" \
      --model-format OpenAI \
      --sku-name "$SKU_NAME" --sku-capacity "$CAPACITY" \
      --only-show-errors >/dev/null
    echo "    deployment $DEP_NAME ($MODEL_NAME v$MODEL_VERSION, sku=$SKU_NAME, cap=$CAPACITY) created"
  fi
done

echo "==> [4/4] Stash credentials in Key Vault"
KV="$(az keyvault list -g "$RG" --query "[0].name" -o tsv 2>/dev/null || echo "")"
if [[ -z "$KV" ]]; then
  KV="$(az keyvault list --query "[?tags.project=='hack2026'].name | [0]" -o tsv 2>/dev/null || echo "")"
fi
if [[ -z "$KV" ]]; then
  echo "    no Key Vault found — skipping secret stash. Add manually after locating KV." >&2
  exit 0
fi
echo "    KV: $KV"

KEY="$(az cognitiveservices account keys list -g "$RG" -n "$NAME" --query key1 -o tsv)"
ENDPOINT="$(az cognitiveservices account show -g "$RG" -n "$NAME" --query properties.endpoint -o tsv)"

az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-API-KEY  --value "$KEY"      --only-show-errors >/dev/null
az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-ENDPOINT --value "$ENDPOINT" --only-show-errors >/dev/null
echo "    secrets AZURE-OPENAI-API-KEY + AZURE-OPENAI-ENDPOINT stashed in $KV"

echo
echo "AOAI provisioning complete."
echo "  Endpoint: $ENDPOINT"
echo "  Deployments: $(az cognitiveservices account deployment list -g "$RG" -n "$NAME" --query "[].name" -o tsv | tr '\n' ' ')"
echo
echo "App code should resolve secrets from Key Vault using Managed Identity."
echo "If 429 (quota=0) on first call, file a quota request via portal — 24h lead time."
