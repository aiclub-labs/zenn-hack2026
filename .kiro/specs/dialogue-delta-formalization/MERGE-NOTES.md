# Merge Notes — Day 1 EOD (2026-05-25)

> 5 worktree fan-out 完了 → main merge wiring 完了 → **M-1〜M-8/11/12 解消 + TDD 59/59 GREEN**。残: M-9 (済), M-10 (Foundry portal post-deploy)。

## Day 1 深夜 — 追加完了 (Merge-A/B/C/D 4 並列)
- **M-1 解消**: `DialogueTurnsRepo.get_latest_acked_revision / set_revision_seen` 追加。`SchemaGateAdapter` が真の session-scoped state を turns repo 経由で読み書き (in-proc dict 撤廃)。`SchemaRevisionGateI` protocol に `session_id` 引数追加。
- **M-2 解消**: `HearoutAgent.hydrate_from_repo(session_id, pk)` + 各 `respond()` で intermediate `in_progress` 永続化。`hearout_records.get_by_session()` 追加。multi-replica 安全。
- **M-3 解消**: `FormalizationAgent` に `user_resolver` callable 注入。`_wiring._resolve_user` は session_id → user proxy (1 session ↔ 1 user 前提、inline doc)。
- **M-4 解消**: `schema_field_resolver` 注入で AI Search upsert + CorpusMeta の `schema_field_id` back-fill。
- **M-5 解消**: `DeltaDetectorAgent` を `_wiring` で `schemas_repo.list_active` + `turns_repo.recent_session_turn_ids` バインドして構築、`_deps.set_delta_detector` で登録。
- **M-6 解消**: `turn.py` が USER + ASSISTANT turn doc を `DialogueTurnsRepo` 経由で persist。`_dispatch_delta_detector` が live `DialogueTurn` を消費。
- **M-7 解消**: `GET /schemas?sector&unit&active_only` 追加、Admin UI `SchemaList` が history-replay から脱却。
- **M-8 解消**: `SetActiveRequest` frozen DTO + contracts.md §6 に `?pk=` query 正式化。
- **M-11 解消**: `app/util/auth.py::parse_easy_auth_headers` 追加。`REVIEWER_GROUP_TENANT_MAP` env から Entra group → tenant scope。
- **M-12 解消**: `infra/modules/containerapps.bicep` に `aca-sla-cron-${env}` Job (cron `0 * * * *`, 1h interval) 追加。`sla_cron.py::run_expired_check` + `__main__` 化。
- **TDD 59/59 GREEN**: 8 unit test files。`_PHONE_RE` の真バグ (6-9桁裸数字を phone と誤マスク) を test が露出 → `pii.py` を separator/`+`/`(`/JP-bare-10-11桁 制約に締めて修正。
- **残課題**: M-9 (済: design.md §5.2 snake_case 化), M-10 (Foundry hub Application Insights 紐付け — portal post-deploy 案件)。



## 完了サマリ

- **WT-A (Infra)**: Bicep 5 modules (cosmos / aisearch / kv-secrets / containerapps / foundry) + main.bicep wire / azure.yaml / pyproject deps。`az bicep build` green (warnings only)。
- **WT-B (Notification + Schema Gate + Utils)**: NotificationDispatcher (Discord webhook + retry + ErrorLog fallback) / SchemaRevisionGate / KV/PII/telemetry/cost utils / 3 repos (schemas extended, dialogue_turns, error_logs)。
- **WT-C (Schema Manager + Admin UI)**: SchemaManagerAgent (revision auto-inc + audit + SchemaUpdatedEvent emit) / 5 schema API routes / Admin UI 4 pages (CRUD / History / Import / Self-approval)。
- **WT-D (Delta + Hearout + Formalization + TJ)**: 22 files — 4 agents + 7 repos + AI Search + embedding util + SLA cron。
- **WT-E (Chat UI + Retrieval + Review UI)**: 5 API routers + main.py additive wire + Chat UI 8 components + Review UI 3 pages + 3 components。
- **Merge (main)**: `app/api/_wiring.py` + main.py lifespan hook + `scripts/provision_search_index.py` (Bicep gap)。

合計 133 files / 62 Python modules。Smoke import: 28/42 OK locally（残り 14 は azure-cosmos / azure-search-documents / semantic-kernel 未インストール；Container Apps デプロイ時に解決）。

## 既知の merge 課題（明日 TDD と並行解消）

### M-1: SchemaRevisionGate signature mismatch（adapter で吸収中）
- **症状**: WT-B `SchemaRevisionGate.check(session_id, tenant, current_seen_revision)` vs WT-E `_deps.SchemaRevisionGateI.banner_for(user_id, tenant)`。
- **暫定**: `app/api/_wiring.py::SchemaGateAdapter` で in-process `(user_id, pk) -> last_acked_revision` を持って橋渡し。
- **明日**: `dialogue_turns` repo に session-scoped state を持たせる正規化（contracts.md §2.5 `schema_revision_seen_at` フィールドそのものを使う）。

### M-2: Hearout in-process state cache → multi-replica で破綻
- **症状**: WT-D `HearoutAgent._mem_cache` がプロセス内辞書。Container Apps の min_replicas=1 でも再起動で消える。
- **暫定**: 単一 replica で動かす（agent-runner app だけ min=1 セット済）。
- **明日**: `hydrate_from_repo(record_id, pk)` を追加し、Cosmos `hearout_records` を真の source of truth に。

### M-3: PendingReviewEvent.user_id 仮置き
- **症状**: WT-D 内で `user_id = record.gap_event_id` の placeholder。
- **明日**: turn.py で gap_event → originating user_id を解決して event 構築。

### M-4: schema_field_id back-fill
- **症状**: WT-D の corpus upsert で `schema_field_id` 空。
- **明日**: `hearout_record.gap_event_id` → `delta_events.schema_field_id` を引いて埋める helper を `app/api/_wiring.py` 経由で注入。

### M-5: DeltaDetector callable 注入
- **症状**: `DeltaDetectorAgent.__init__(... load_active_schemas, recent_session_turn_ids, llm_client)` の 2 callables を `_wiring.py` で未注入。
- **明日**: `SchemasRepo.list_active(tenant.pk)` と `DialogueTurnsRepo.recent_turn_ids(session_id, pk, limit)` をラップして渡す。

### M-6: turn.py が dialogue_turns に未書き込み
- **症状**: WT-E `api/turn.py` は UUID 発行 + log のみ。
- **明日**: `_wiring.py` で `DialogueTurnsRepo` を `_deps` に register、turn.py で消費。

### M-7: GET /schemas list endpoint 不在
- **症状**: contracts §6 にもないが、Admin UI が `/schemas/history` を replay している。O(N) 非効率。
- **明日**: `GET /schemas?sector&unit&active_only` を追加 + contracts.md §6 更新。

### M-8: POST /schemas/{id}/active の pk 受け渡し
- **症状**: WT-C は `?pk=` query で受ける。WT-E は schemas router 使わないので直接影響なし。
- **明日**: OpenAPI で正式化 + Admin UI 側で確認。

### M-9: AI Search index 命名 contracts vs design ズレ
- **解消**: contracts.md §3 = snake_case を採用。`scripts/provision_search_index.py` も snake_case。design.md §5.2 の camelCase 表記は明日 contracts に合わせて更新。

### M-10: Foundry hub の Application Insights 紐付け
- **症状**: `infra/modules/foundry.bicep` で applicationInsights slot 未設定（shared.bicep は read-only スコープ）。
- **明日**: Foundry portal 経由で post-deploy 紐付け or shared.bicep 拡張提案。

### M-11: Reviewer Entra group claim → tenant scope
- **症状**: `_deps.current_reviewer_scope()` が空リスト返却。
- **明日**: Container Apps Easy Auth header parsing helper を `app/util/auth.py` に追加。

### M-12: SLA cron schedule
- **症状**: `formalization/sla_cron.py` が単発関数。Container Apps Job として未スケジュール。
- **明日**: `infra/modules/containerapps.bicep` に cronjob spec 追加（1h interval）。

## 明日 (5/26) Day 2 計画

### 午前: TDD layer（design contracts.md §9 policy）
- `tests/test_weight_calculator.py` — A=10/B=1/C=1→1.0, A=4→0.4, A=5→0.5 境界
- `tests/test_cooldown.py` — 7d, 3-turn 抑制
- `tests/test_schema_revision_gate.py` — banner shown / acked / unseen
- `tests/test_partition_filter.py` — AI Search filter exclude superseded
- `tests/test_redact_mask.py` — content None 経路
- `tests/test_webhook_retry.py` — tenacity backoff
- `tests/test_pii_scrub.py` — email/phone/JP-name 検出
- 上記 M-1〜M-6 の merge 課題解消も TDD で

### 午後: EDD layer
- Hearout 5W1H prompt 調整 — Persona B 役で 5 sessions 試行
- ChatExtract follow-up — 「違う」応答時の record 破棄確認
- Truth Judgment golden set 20 件作成 + verdict 精度評価
- Conflict 並列比較 UI — Persona C 役で 3 sessions

### 夕方: integration / deploy
- `azd up` → Cosmos 12 containers + AI Search index + Container Apps 起動
- E2E スモーク: A1 → B1 → B2 → C1 → B3
- App Insights customMetrics 確認

## 5/27-28: テスト + デモ準備
- 各 persona 役で full scenario 通し
- Discord 通知 (R2 AC #5/#6/#7) のデモ脚本
- 失敗パス: SLA expired, conflict, cost alert
- Demo deck 1 枚

## 5/29-31: バッファ + 本番デモ polish
