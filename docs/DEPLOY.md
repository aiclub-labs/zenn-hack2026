# Deploy Guide — Day 2 朝イチで `azd up` を一発で通すための前提整理

> 対象: `dialogue-delta-formalization` Container Apps デプロイ初回。
> ゴール: `azd up` → `/healthz` 200 → 3 SPA から E2E スモーク (A1→B1→B2→C1→B3) 完走。

## 0. 前提環境チェック

```bash
az --version          # >= 2.60
azd version           # >= 1.10
az account show       # subscription = hack2026 dev
az account set --subscription <SUB-ID>
azd auth login        # ブラウザ SSO
```

## 1. 必須 env / param (Bicep main.parameters.json で固定済)

| Key | 値 | 出所 |
|---|---|---|
| `project` | `hack2026` | parameters.json |
| `location` | `swedencentral` | parameters.json (Foundry preview region) |
| `env` | `dev` | parameters.json |
| `kvName` | `kv-hack2026-tyu3o4` | 既存 KV (作成しない) |
| `memberObjectIds` | 3 GUID | Entra members |
| `ownerObjectId` | df9f49d3-... | operator |
| `budgetAmount` | 180 USD | 月予算 |

追加で `azd env` に入れる値:

```bash
azd env new hack2026-dev
azd env set AZURE_LOCATION swedencentral
azd env set AZURE_SUBSCRIPTION_ID <SUB-ID>
# Reviewer Entra group → tenant scope JSON map (M-11)
azd env set REVIEWER_GROUP_TENANT_MAP '{"<entra-group-guid>":"hack#tenantA"}'
# SLA cron が見回る tenant の pk リスト
azd env set SLA_CRON_TENANT_PKS '["hack#tenantA"]'
```

## 2. KV secret 事前投入 (Bicep は placeholder のみ作る)

`infra/modules/keyvault-secrets.bicep` が枠だけ作るので、値は CLI で投入:

```bash
KV=kv-hack2026-tyu3o4

# Discord webhook 4 種 (AI Club bot とは別チャンネル/webhook 推奨)
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-SCHEMA-UPDATES --value 'https://discord.com/api/webhooks/.../...'
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-PENDING-REVIEW --value 'https://discord.com/api/webhooks/.../...'
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-EXPIRED      --value 'https://discord.com/api/webhooks/.../...'
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-COST-ALERT   --value 'https://discord.com/api/webhooks/.../...'

# Cosmos は disableLocalAuth=true なので connection-string は使わない。
# placeholder のままで OK (Bicep が空値で作成済)。

# AI Search Admin key (provision_search_index.py 実行用)
AISEARCH_ENDPOINT=$(az search service show -n srch-hack2026-<suffix> -g rg-hack2026 --query 'properties.endpoint' -o tsv)
AISEARCH_KEY=$(az search admin-key show --service-name srch-hack2026-<suffix> -g rg-hack2026 --query primaryKey -o tsv)
az keyvault secret set --vault-name $KV -n AISEARCH-ADMIN-KEY --value "$AISEARCH_KEY"

# AOAI key (Foundry hub 経由でも MI 推奨。手動 fallback 用)
az keyvault secret set --vault-name $KV -n AOAI-API-KEY --value '<key>'
```

> KV secret 名はハイフン区切り (KV 制約)。Python 側 `app/util/kv.py` がアンダースコアにマップして返す。

## 3. `azd up` 実行手順

```bash
cd scaffold
azd provision      # Bicep のみ先に確認
azd deploy         # 全 5 service ビルド + push + revision update
# まとめてやるなら:
azd up
```

5 service:
- `api` (FastAPI, Dockerfile root)
- `web-chat` (Vite, ui/chat)
- `web-admin` (Vite, ui/admin)
- `web-review` (Vite, ui/review)
- `agent-runner` (同 Dockerfile, min_replicas=1)

## 4. Post-deploy ステップ

```bash
# 4-1. AI Search index 作成 (Bicep でカバーできない)
export AISEARCH_ENDPOINT=$(azd env get-values | grep AISEARCH_ENDPOINT | cut -d= -f2 | tr -d '"')
export AISEARCH_INDEX=corpus-dev
python scripts/provision_search_index.py

# 4-2. /healthz スモーク
API_URL=$(azd env get-values | grep API_URL | cut -d= -f2 | tr -d '"')
curl -s "$API_URL/healthz"   # {"ok": true}
curl -s "$API_URL/health"    # {"status":"ok","environment":"dev"}

# 4-3. M-10 Foundry hub の App Insights 紐付け
# portal: Foundry hub → Settings → Diagnostic settings → AI insights を選択
```

## 5. E2E スモーク シナリオ (A1→B1→B2→C1→B3)

3 SPA 経由で手動実行。Persona 別動線:

1. **A1 (Persona A, Schema 編集)** — Admin UI から 1 field 追加 → SchemaUpdatedEvent → Discord webhook 着信確認
2. **B1 (Persona B, 通常対話)** — Chat UI から発言 → DialogueTurn 永続化 → DeltaDetector 起動 → 何も検出されないこと
3. **B2 (Persona B, Gap 発火)** — Schema field に該当する記述ギャップを含む発言 → Hearout 5W1H 質問が返ること
4. **C1 (Persona C, レビュー)** — Review UI で pending を承認 → AI Search に upsert → Discord 通知 (review)
5. **B3 (Persona B, schema 変更通知)** — Chat UI に banner 表示 → ack → `dialogue_turns.revision_seen_at` 更新

## 6. 失敗シナリオ (Demo 用脚本)

- **SLA expired** — SLA cron Job (1h interval) が `formalization_queue` の期限切れ検出 → Discord (expired)
- **Conflict** — 同一 schema_field に 2 録音が衝突 → 並列比較 UI で C1 役が選択
- **Cost alert** — `app/util/cost.py` の閾値超え → Discord (cost-alert)

## 7. ローカル UI ビルド検証ログ (2026-05-26 0:00 時点)

- `ui/chat` ✅ `vite build` OK (276 KB / gzip 86 KB)
- `ui/admin` ✅ `vite build` OK (315 KB / gzip 98 KB) — TS2345 修正済 (`SchemaHistory.tsx` diff 型 optional 化)
- `ui/review` ✅ `vite build` OK (298 KB / gzip 93 KB)
- TDD: 59/59 GREEN (`_PHONE_RE` 真バグ修正含む)

## 8. 残課題 (Day 2 以降)

- M-10: Foundry hub Application Insights — Bicep スコープ外、post-deploy portal 操作
- EDD layer: Hearout 5W1H prompt 調整 / Truth Judgment golden set 20 件
- demo deck 1 枚
