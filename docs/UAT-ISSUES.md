# UAT Issues — dialogue-delta-formalization

> 開始: 2026-05-26 / UAT-RESULTS.md FAIL/PARTIAL/BLOCKED の根本原因と対応

## 修正反映 (2026-05-26 PM)

- #1 (turn.py:208) / #2 (reviews._list_tickets) は修正 + 再デプロイ済 → S2.2 PASS、S3.1 PARTIAL (route 結線済、queue 空)
- 副次的に AOAI `text-embedding-3-small` deployment を追加 (これ無しでは detector が embed 例外で sile silent fail)
- 新規 P0 #9 が S2.3 / S4.1 完走を依然ブロックしている (下記参照)

## 緊急度 P0 (デモブロッカー)

### #9 [S2.3 / S4.1 FIXED ✅ 2026-05-26 PM] hearout セッション開始経路が未実装
- **修正内容**:
  - `POST /hearout/start` 追加 (`scaffold/app/api/hearout.py`)
  - `TurnResponse.gap_event_id` を追加 (`scaffold/app/contracts/http.py`)。detector の最初の event id を /turn レスポンスで返す
  - `_run_delta_detector` を bool 戻り→Optional[event_id] に変更 (`scaffold/app/api/turn.py`)
  - `Chat.tsx` で `gap_detected && gap_event_id` の時に `startHearout()` → modal の sessionId を新 record_id に差し替え
  - **追加で発見**: hearout 終了時に FormalizationAgent.submit_for_review を呼ぶ caller が無かった。`hearout.py` の 3 endpoint で `final_record` が立った時に weight + submit を自動実行するよう接続
- **検証**: strategy-poc#auto-mfg で end-to-end (turn → start → respond x4 → expired → ticket pending_review) 通過、`/reviews` に weight_final=0.2 のチケット出現

### #10 [S3.1 FIXED ✅ 2026-05-26 PM] approve 経路が AI Search で Forbidden
- **修正内容**:
  - `az role assignment create --role "Search Index Data Contributor" --assignee-object-id <api MI> --scope <search service id>` を実行 (api Container App MI `f05ec5dc-8bbd-43db-aeb7-aa57bc7ea5ff` → `srch-hack2026-dev-ytzykj`)
  - `infra/modules/aisearch-roles.bicep` 新規追加 + `infra/main.bicep` に `aisearchRoles` モジュール追加 (api + sla-cron 両 MI に `Search Index Data Contributor` を付与)
- **検証**: `POST /reviews/ft_7d211b819e074f4f8697ebbd/decision` (decision=approve, strategy-poc#auto-mfg) → 200 `{record_id, corpus_meta_id}`. `/reviews?...` キューが空になることを確認

### #1 [S2.2 FIXED ✅ 2026-05-26 PM] `gap_detected` が turn API で hardcoded false
- **Repro**: `POST /turn` で具体的個人経験質問を送信 → response の `gap_detected` が常に false
- **Root cause**: `scaffold/app/api/turn.py:208`
  ```python
  gap_detected = False
  if not req.redact and (banner is None or banner_acked):
      background.add_task(_dispatch_delta_detector, user_turn_doc)
  ```
  Delta Detector は background task として走るが結果が同期レスポンスに乗らない
- **Impact**: HearoutModal が永遠に開かない → S2.2 / S2.3 ★ / S4.1 ★ 全部死ぬ
- **Proposed fix**:
  - 案 A: `_dispatch_delta_detector` を `await` で同期化し、戻り値の gap フラグをそのまま返す (cold start 3s 制約に注意)
  - 案 B: detector を投げた直後にポーリング (200ms × 5 回) で delta_events を見る
  - 案 C: SSE/WebSocket で gap 通知を別チャネル化 (実装重い)

### #2 [S3.1 FIXED ✅ 2026-05-26 PM] `_list_tickets` が TODO stub
- **Repro**: `GET /reviews?sector=manufacturing-s8b&unit=line-A` → `[]`
- **Root cause**: `scaffold/app/api/reviews.py:32-43`
  ```python
  async def _list_tickets(...) -> list[FormalizationTicket]:
      """TODO(wt-b-import): FormalizationQueueRepo.list(statuses, pks, priority)."""
      return []
  ```
- **Impact**: レビューキュー UI が永久に「キューは空です」→ S3.1-S3.4 / S4.1 ★ 全死
- **Proposed fix**: `FormalizationQueueRepo` を DI 経由で受け取り、`statuses` filter + `pks` partition lookup で実データを返す。Repo 実装は既に `scaffold/app/repos/formalization_queue.py` にあり (確認推奨)

### #3 [S2.2 副要因] AOAI self-critic が常に高得点
- **Repro**: 経験ベースの具体質問 4 連投で self-critic は 7.5-8.5/10
- **Impact**: gap threshold (< 5) を越えない → Delta Detector が gap 検出しない
- **Proposed fix**:
  - critic prompt を厳しめに調整 (「現場個人判断軸に踏み込めているか」を重視)
  - or threshold を 6 程度に引き上げる
  - or 「個人経験を求める質問」と判定された場合のみ critic 走らせる軽量 classifier を前段に置く

## 緊急度 P1

### #4 [S1.7 PARTIAL] self-approval dashboard が mock 値
- **Repro**: `/admin/self-approval` の数値は静的 mock + UI に "Req 9.9 stub" 注記
- **Root cause**: `reviews._self_approval_rate` 内 TODO (`reviews.py:68-72`)
- **Impact**: KPI 観測が機能不全
- **Fix**: #2 が解決すれば `formalization_queue` + `dialogue_turns` join で集計可能

### #5 [S3.4 BLOCKED] `conflicts` container 未作成
- **Repro**: handoff §4 既知制約 (cosmos に `conflicts`, `cost_ledger` 未作成)
- **Impact**: 矛盾解決の書込先がない
- **Fix**: infra (bicep) で container 追加 or `delta_events` を代替 store として明示化

### #6 [S5.5 NOT TESTED] SLA expired の手動 trigger 経路がない
- **Repro**: 24h 待機 = UAT 不可能。`expired` 状態への手動遷移 API もない
- **Impact**: SLA / Discord 通知の動作確認が UAT で不可
- **Fix**: dev-only エンドポイント `POST /reviews/{id}/_force_expired` (X-Dev-Token gated) を追加 or `created_at` を 25h 前で seed する admin スクリプト追加

## 緊急度 P2 (post-hack)

### #7 [S6.1 DEFERRED] デモ録画は human 担当
- S4.1 を修正して PASS 化した後、OBS で 3 分通し録画。Claude (Playwright) は録画できない

### #8 [全般] `/openapi.json` が SPA index を返す
- **Repro**: `GET /openapi.json` で HTML が返る (FastAPI 自動ドキュメント壊滅)
- **Impact**: API 探索の手間。大きな問題ではないが dev 体験劣化
- **Fix**: nginx route で `/openapi.json` を API container にプロキシ
