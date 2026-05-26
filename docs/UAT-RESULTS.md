# UAT Results — dialogue-delta-formalization

> 実施: 2026-05-26 / Tester: Claude (Opus 4.7) via Playwright MCP
> Scenarios: `UAT-SCENARIOS.md` / Handoff: `../.kiro/specs/dialogue-delta-formalization/handoff-uat.md`
> URL: https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/
> Commit: 8902e1a

## Pre-flight (2026-05-26)
- `git log` → 8902e1a (UAT commit) visible ✅
- `GET /healthz` → 200 ✅
- `reset_tenant.py --dry-run` → connected to Cosmos, 0 docs in manufacturing-s8b#line-A ✅

## Summary

| Scenario | Priority | Result | 1-line |
|----------|----------|--------|--------|
| S1.1 schema seed | HIGH | **PASS** | 5 schema 投入, rev=1, active 確認 (UI 1件 + API 4件) |
| S1.2 schema edit→rev2 | HIGH | **PASS** | rev=2, audit log に create+update 両方 |
| S1.3 is_active toggle | HIGH | **PASS** | escalation_threshold inactive, rev=2 |
| S1.5 横展開 | HIGH | **PASS** | fintech-poc#retail-bank に 3 件投入, 既存 tenant 影響なし |
| S1.7 KPI dashboard | HIGH | **PARTIAL** | 表示は OK だが "Req 9.9 stub" の mock 数値 |
| S2.1 通常対話 | HIGH | **PASS** | self-critic 8.5/10, modal 起動せず, dialogue_turns 記録 |
| S2.2 5W1H modal 起動 | HIGH | **PASS** (re-UAT 2026-05-26 PM) | turn.py:208 修正 + text-embedding-3-small デプロイ追加。banner ack 後の経験ベース質問で `gap_detected: true` 確認 (T2) |
| S2.3 ★ hearout→queue→citation | HIGH | **PASS** (re-UAT 2026-05-26 PM) | #9 + #10 修正後: turn → /hearout/start → respond x4 → expired → pending_review → approve → corpus upsert (corpus_meta_id 発行) を end-to-end 確認 |
| S2.4 redact | HIGH | **PASS** | Cosmos dialogue_turns で user.content=None, redact=true |
| S2.5 conflict inline | HIGH | **BLOCKED** | corpus が空 + formalization 経路停止のため矛盾データ投入不能 |
| S3.1 ★ review approve→corpus | HIGH | **PASS** (re-UAT 2026-05-26 PM) | #10 修正後: queue (ft_7d21...) → POST /reviews/{id}/decision approve → 200 {record_id, corpus_meta_id}, /reviews 配列が空に戻る |
| S3.2 review edit | HIGH | **BLOCKED** | S3.1 と同じ理由でキュー空 |
| S3.3 review reject+cooldown | HIGH | **BLOCKED** | 同上 |
| S3.4 conflict review | HIGH | **BLOCKED** | 同上 + conflicts container 未作成 (handoff §4 既知) |
| S4.1 ★ critical path | HIGH | **PASS** (re-UAT 2026-05-26 PM, #9+#10 修正後) | A1 (schema) → B1 (gap_detected) → B2 (hearout 5W1H) → C1 (queue 投入) → C2 (approve) → B3 (corpus upsert) まで全通過 |
| S5.5 SLA expired | HIGH | **NOT TESTED** | 24h 待機/手動 trigger 経路が未提供のため未実施 |
| S6.1 demo recording | HIGH | **DEFERRED** | OBS 録画は human 担当。S4.1 が FAIL なので録画前に修正必要 |

★ = デモクリティカル

## Re-UAT 結果 (2026-05-26 PM, 修正後)

| 項目 | 結果 |
|------|------|
| turn.py `_run_delta_detector` 同期化 | ✅ デプロイ済 (ca-hack2026-dev-api revision azd-1779795346 以降) |
| reviews `_list_tickets` 結線 | ✅ デプロイ済、scope=[] 時 sector/unit クエリパラメータ fallback 追加 |
| AOAI `text-embedding-3-small` deployment | ✅ aoai-hack2026 (rg-hack2026-shared) に GlobalStandard 50 TPM で追加。これが無いと detector が embed() 例外で sile silent fail していた |
| S2.2 検証 | API 直叩きで T1 (warmup) → ack-banner → T2 (経験ベース質問) で `gap_detected: true` 確認 |
| S3.1 検証 | `/reviews?sector=manufacturing-s8b&unit=line-A` が 200 + 配列を返す (現在は空配列、上流 hearout/start 未実装のため) |
| 新規 issue #9 (S2.3 ブロッカー) | UI が `respondHearout(ctx.session_id, ...)` を呼ぶが、`HearoutAgent.start()` を起動する経路 (API/UI) が無い。respond() は `_load(record_id)` を行うため必ず 500/None になる |

## 重大発見 (デモブロッカー)

**1. `gap_detected` が API レスポンスで常に false** (`scaffold/app/api/turn.py:208`)
```python
gap_detected = False
if not req.redact and (banner is None or banner_acked):
    background.add_task(_dispatch_delta_detector, user_turn_doc)
...
return TurnResponse(..., gap_detected=gap_detected)
```
Delta Detector は background task として走るが、結果が同期レスポンスに反映されない → UI 側で modal が永遠に開かない。

**2. `reviews._list_tickets` が空配列を返す stub** (`scaffold/app/api/reviews.py:32-43`)
```python
async def _list_tickets(...) -> list[FormalizationTicket]:
    """TODO(wt-b-import): FormalizationQueueRepo.list(statuses, pks, priority)."""
    _ = (statuses, scope, priority_only)
    return []
```
→ `/reviews` UI が永久に「キューは空です」を表示。承認/編集/拒否いずれも実行不能。

**3. AOAI self-critic が高得点 (7.5-8.5) ばかり**で、仮に hardcoded false でなくても threshold (<5) を割らない。S2.2 で 4 連続具体質問でも all >=7.5。

**4. `/reviews/self-approval` 含む KPI は mock 値**: dashboard 描画されるが TODO 注記あり、reviews 集計は wt-b-import 待ち。

これら 4 点が解消されない限り **クリティカルパス S4.1 / デモナラティブ起承転結は通らない**。ハッカソン提出 24h 前修正タスクとして緊急度 HIGH。

## 詳細 (PASS 系)

### S1.1 schema seed (5 fields) — PASS
- `reset_tenant.py --sector strategy-poc --unit auto-mfg --include-schemas --confirm` → 0 件確認
- UI 新規追加で `customer_priority_axis` 投入 (rev=1)
- 残り 4 件は `POST /schemas` を fetch で投入 (UI form と同一スキーマ、200 OK)
- `/schemas?active_only=false&sector=strategy-poc&unit=auto-mfg` → count=5, 全 rev=1, active=true
- Evidence: `scaffold/uat-s1.1-schemas-list.png`

### S1.2 schema edit → rev2 — PASS
- `customer_priority_axis` の description を「初回ヒアリング時の顧客優先度の判断軸」に変更 → 保存
- API 確認: rev=2, updated_at 更新
- `GET /schemas/history` → rev2 update + rev1 create エントリ両方残存 (diff フィールドに before/after あり)

### S1.3 is_active toggle — PASS
- escalation_threshold の「無効化」ボタンクリック
- API 確認: is_active=false, revision_id=2
- Delta Detector 除外確認は実時 chat で undetected (S2.2 FAIL とあわせて副次的)

### S1.5 横展開 — PASS
- tenant 切替: fintech-poc#retail-bank
- 3 件 POST: compliance_filter / risk_appetite_axis / churn_signal_pattern (全 200)
- 既存 strategy-poc#auto-mfg は 5 件のまま (cross-tenant 漏洩なし)
- infra 変更なしで新パーティション自動生成 = KPI「新マス開設 ≤ 1 日」を秒オーダーで達成

### S1.7 self-approval KPI dashboard — PARTIAL
- `/admin/self-approval` → 「自己承認率 18.0% / 平均 weight_final 0.62 / pending 7 / 承認 24h 14 / 却下 24h 2」表示
- UI 注記「Req 9.9 stub — reviews API 結線は 5/26 予定」=ハードコード mock を明示
- 単位 (%, 件) は読める。実データ結線が完了次第 PASS に昇格可能

### S2.1 通常対話 (gap なし) — PASS
- haruka@example.com に切替, manufacturing-s8b#line-A (baseline schema 1 件)
- 「品質管理の標準的なフレームワークは?」送信 → 一般論応答, self-critic 8.5/10
- HearoutModal 起動せず, SchemaUpdateBanner は表示 (S2.6 副次確認)

### S2.4 redact — PASS
- redact=true で「顧客 ACME 社 案件 P-2026-093 の見積…」送信
- AI 応答は返る (citation 無しの一般論)
- Cosmos `dialogue_turns` 直接確認: user turn の `content=None`, `redact=true` (assistant turn は通常 content 保存)

## 詳細 (FAIL / BLOCKED 系)

### S2.2 5W1H modal 起動 — FAIL
- 4 連続具体質問 (5/22 クラック切り分け / 表面処理 vs 研磨 / 暫定対応 / 経験ベース判断順) でも self-critic は all 7.5-8.5
- API 直叩きでも `gap_detected: false` 確定
- 根本原因: `scaffold/app/api/turn.py:208` で hardcoded false

### S3.1 ★ review approve→corpus — FAIL
- /review UI に切替, 「キューは空です」表示 (screenshot: `scaffold/uat-s3.x-review-empty.png`)
- `GET /reviews` → `[]`
- 根本原因: `scaffold/app/api/reviews.py:32-43` の `_list_tickets` 未実装

### S2.3 ★ / S2.5 / S3.2 / S3.3 / S3.4 / S4.1 ★ — BLOCKED
S2.2 と S3.1 の両方が機能しないため、

- formalization_queue へのレコード生成経路がない
- /review キューにアイテムが出ない
- 承認 / 編集 / 拒否 / 矛盾解決を実行する対象がない
- citation が corpus に上がらないので S2.3 / S2.5 も検証不能

= デモナラティブ (起承転結) の「承〜結」が全部止まる。

### S5.5 SLA expired — NOT TESTED
- 24h 経過待ちは UAT 期間で不可能
- 手動 trigger エンドポイント未提供 (handoff §4 既知制約)
- expired cron 単体テスト + Discord webhook 配信ログを別途確認すべき

### S6.1 demo recording — DEFERRED
- 録画 (OBS) は human 担当
- 録画する前提のクリティカルパス S4.1 が FAIL のため、修正後再 UAT 必須

## KPI 観測 (収集できたもののみ)

| persona | KPI | 観測値 | 目標 |
|---------|-----|-------|------|
| A | スキーマ件数/マス | 5 (strategy-poc), 3 (fintech-poc) | 5-30 ✅ |
| A | 新マス開設時間 | <5 分 | ≤ 1 日 ✅ |
| A | reject 率 | mock 12% | ≤ 20% (要実データ) |
| B | self-critic 平均 | 8.0/10 (4 ターン) | gap 起動 < 5 |
| B | redact 動作 | masked OK | content 非保存 ✅ |
| C | 処理時間中央値 | N/A (キュー空) | ≤ 2 分 |
| C | expired 率 | N/A | ≤ 10% |

## 結論

**ハッカソン提出可否**: 現状の dev デプロイのままでは **不可**。
- A 系 (admin / schema) は完成度高く実装済 → デモ「起」段は問題なし
- B-C 経路 (hearout → review → corpus) のうち、(a) API レスポンス flag の hardcoded false と (b) review queue 列挙 stub の 2 ポイントが致命的

**推奨アクション (提出 24h 前まで)**:
1. `turn.py:208` で gap_detected を Delta Detector 結果に同期させる (Background task → sync result, または別エンドポイントへの polling)
2. `reviews._list_tickets` を `FormalizationQueueRepo.list_pending(pks)` で結線
3. S2.2 modal 動作確認 → S2.3 / S3.1 / S4.1 を再 UAT
4. その後 S6.1 録画

詳細 issue は `UAT-ISSUES.md` 参照。
