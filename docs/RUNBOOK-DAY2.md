# Day 2 Runbook — `azd up` から実機 E2E まで (2026-05-26)

> イメージ: 9 ステージのレベル制ゲーム。各ステージに「合格条件 = 次へのキー」がある。詰まったら戻る、飛ばさない。
> 想定所要: 全部スムーズで **約 90 分**。詰まり込みで **約 3h**。

```
[S1] 環境点火    →  [S2] env set      →  [S3] KV secret
   ↓ az ok            ↓ azd env OK         ↓ 7 secret 投入
[S4] azd provision →  [S5] azd deploy   →  [S6] AI Search index
   ↓ Bicep 5 green    ↓ 5 service up       ↓ corpus-dev 作成
[S7] /healthz      →  [S8] E2E 5 step  →  [S9] 失敗パス確認
   ↓ 200             ↓ A1→B1→B2→C1→B3   ↓ SLA / Conflict / Cost
```

---

## S1. 環境点火 (5 min)

```bash
az --version       # >= 2.60
azd version        # >= 1.10
az login           # ブラウザ
az account set --subscription <SUB-ID-hack2026>
azd auth login
```

✅ **キー**: `az account show` で `name = hack2026-dev` 系が出る。

❌ **詰まり**: `az login` が tenant 間違える → `--tenant <TENANT-ID>` 明示。

---

## S2. azd env set (3 min)

```bash
cd scaffold
azd env new hack2026-dev      # 既存なら azd env select
azd env set AZURE_LOCATION swedencentral
azd env set AZURE_SUBSCRIPTION_ID <SUB-ID>
azd env set REVIEWER_GROUP_TENANT_MAP '{"<entra-group-guid>":"hack#tenantA"}'
azd env set SLA_CRON_TENANT_PKS '["hack#tenantA"]'
azd env get-values | sort
```

✅ **キー**: 4 行ぜんぶ出る。

---

## S3. KV secret 7 件投入 (10 min)

事前に Discord 4 webhook URL を `personal-hub/work/.../secrets.md` から拾ってクリップボード or env に貼っておく。

```bash
KV=kv-hack2026-tyu3o4
# discord 4 件
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-SCHEMA-UPDATES --value "<url-1>"
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-PENDING-REVIEW --value "<url-2>"
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-EXPIRED        --value "<url-3>"
az keyvault secret set --vault-name $KV -n DISCORD-WEBHOOK-URL-COST-ALERT     --value "<url-4>"
# aoai (Foundry 作成後に取れる。S4 後でも可)
az keyvault secret set --vault-name $KV -n AOAI-API-KEY --value "<key>"
# aisearch (S5 後でも可)
az keyvault secret set --vault-name $KV -n AISEARCH-ADMIN-KEY --value "<key>"
# Cosmos は disableLocalAuth=true、PLACEHOLDER のまま
```

✅ **キー**: `az keyvault secret list --vault-name $KV -o table` で 7 件全部 enabled。

❌ **詰まり**: webhook URL は Discord 側で 1 回叩かれると revoke される可能性あり → 新規 webhook 推奨。

---

## S4. azd provision (15 min)

```bash
azd provision 2>&1 | tee /tmp/azd-provision.log
```

中で動く Bicep module:
- `cosmos` (12 container, disableLocalAuth=true)
- `aisearch` (Basic, vector index は後で provision script)
- `keyvault-secrets` (placeholder + RBAC)
- `containerapps` (5 service + SLA cron Job)
- `foundry` (hub, swedencentral)

✅ **キー**: ターミナル末尾に `SUCCESS: Your application was provisioned in Azure`。

❌ **詰まり1**: `Foundry` リージョン枠不足 → portal で Foundry hub の available regions 再確認。
❌ **詰まり2**: Cosmos の RU 枠 → サブスク内既存 Cosmos と競合する場合 `azd env set COSMOS_THROUGHPUT_TIER serverless` 確認。

---

## S5. azd deploy (20 min)

```bash
azd deploy 2>&1 | tee /tmp/azd-deploy.log
```

5 service を順に build + push + revision update。
- `api` (Python Dockerfile)
- `agent-runner` (同 Dockerfile, min_replicas=1)
- `web-chat` / `web-admin` / `web-review` (Vite build)

✅ **キー**: `endpoints:` セクションで 4 URL (api + 3 web) が出力される。各 URL を `azd env get-values` で確認。

❌ **詰まり**: Vite build が Container Apps 側で fail → S0 でローカル build 検証済 (2026-05-26 0:00) なので環境差のみ疑う。`node:20-alpine` で動く前提。

---

## S6. AI Search index 作成 (3 min)

```bash
export AISEARCH_ENDPOINT=$(azd env get-values | grep AISEARCH_ENDPOINT | cut -d= -f2 | tr -d '"')
export AISEARCH_INDEX=corpus-dev
python scripts/provision_search_index.py
```

✅ **キー**: `created index: corpus-dev` (or `updated index`)。

❌ **詰まり**: MI が AI Search の Search Service Contributor 持ってない → `az role assignment create --role "Search Service Contributor" --assignee <MI-OBJECT-ID> --scope <SEARCH-RESOURCE-ID>`。

---

## S7. /healthz スモーク (2 min)

```bash
API=$(azd env get-values | grep API_URL | cut -d= -f2 | tr -d '"')
curl -s $API/healthz                  # {"ok": true}
curl -s $API/health                   # {"status":"ok","environment":"dev"}
curl -s $API/version                  # {"version":"...", "environment":"dev"}
curl -s $API/schemas?active_only=true # [] (まだ空)
```

✅ **キー**: 4 個ぜんぶ 2xx + JSON。

❌ **詰まり**: 500 → Container Apps logs を即確認: `az containerapp logs show -n aca-api-dev -g rg-hack2026 --tail 50`。`azure.cosmos` import なら Dockerfile の deps 漏れ。

---

## S8. E2E 5 step (30 min, persona role-play)

ブラウザ3枚を並べて開く:
- `https://web-chat-...azurecontainerapps.io` (5173 相当, Persona B)
- `https://web-admin-...azurecontainerapps.io` (5174 相当, Persona A)
- `https://web-review-...azurecontainerapps.io` (5175 相当, Persona C)

| # | Persona | アクション | 合格条件 |
|---|---|---|---|
| **A1** | A | Admin で `sector=demo / unit=team1` に schema field 追加 | Discord #schema-updates 着信 / Admin History に revision_id=1 |
| **B1** | B | Chat で「今日は雨です」と発言 | 200 / Cosmos `dialogue_turns` に USER + ASSISTANT 2 doc / Delta 検出なし |
| **B2** | B | Chat で schema field に該当する gap を含む発言 | Hearout 5W1H 質問が返る / `hearout_records` に in_progress doc |
| **C1** | C | Review UI で pending を承認 | AI Search corpus-dev に upsert / Discord #pending-review に承認通知 / `corpus_meta` に schema_field_id 入り |
| **B3** | B | A1 で schema 変更後の Chat ターン | banner 表示 / ack ボタン押す → `dialogue_turns.revision_seen_at` 更新 |

✅ **全体キー**: 5 ステップ全 PASS + Application Insights `customMetrics` に各 agent latency / cost が見える。

---

## S9. 失敗パス確認 (15 min, demo 用脚本)

| シナリオ | 起動方法 | 期待 |
|---|---|---|
| SLA expired | `formalization_queue` に `expires_at` を 1h 前にした doc を Cosmos Explorer で投入 → SLA cron job 次回実行 | Discord #expired 通知 |
| Conflict | 同一 schema_field に 2 record を C1 で並列承認 | 並列比較 UI 出現 / C 役が 1 つ選択 |
| Cost alert | `app/util/cost.py` の閾値を一時的に 0.01 USD に下げて再 deploy | Discord #cost-alert 通知 |

---

## ロールバック

詰まったら段階的に戻す:

```bash
azd down --force --purge   # 全部消す (KV は soft-delete)
# 部分的なら:
az containerapp revision deactivate -n aca-api-dev --revision <rev>
```

---

## チェックリスト (印刷用)

- [ ] S1 az / azd login + subscription
- [ ] S2 azd env 4 値
- [ ] S3 KV secret 7 件
- [ ] S4 azd provision SUCCESS
- [ ] S5 azd deploy SUCCESS + 4 URL
- [ ] S6 corpus-dev created
- [ ] S7 /healthz {"ok":true}
- [ ] S8 A1→B1→B2→C1→B3 PASS
- [ ] S9 SLA / Conflict / Cost demo 録画
- [ ] M-10 Foundry App Insights portal 紐付け
