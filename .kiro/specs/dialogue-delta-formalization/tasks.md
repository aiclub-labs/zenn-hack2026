# Implementation Tasks

> Source: `requirements.md` v2（Req 1–18, Sotaro/Daichi 承認版 2026-05-25）+ `design.md` v2（Notification Dispatcher / Schema Revision Gate / MVP 境界 §1 反映）+ `personas-stories.md`（Persona A/B/C）+ `research.md`。
> 言語: ja（spec.json）。
> Fast-track: spec-tasks は `-y` で自動生成・自動承認。実装着手前にチーム共有レビュー（hack-pm 投下）。
> マイルストーン: M2-M8 = 今回ビルド（MVP）/ M9-M12 = Follow-up（design §1 表）。
> 並列性: 同一マイルストーン内の `[P]` 付きタスクは独立、並列着手可。`[S]` は前段依存で順次。
> 進捗管理: タスク完了時に `[ ]` → `[x]`、PR / commit リンクを末尾に追記。`/kiro:spec-status dialogue-delta-formalization` で集計可。

---

## M2: 基盤・スキャフォールド（Week 1, 2026-05-26〜05-31）

### 2.1 リポジトリ / インフラ scaffold
- [ ] **2.1.1 [P]** monorepo 構成セットアップ（`apps/api`, `apps/web-chat`, `apps/web-admin`, `apps/web-review`, `agents/python`, `infra/bicep`）/ pnpm workspace / Node 20 / Python 3.11 / `tsconfig` strict + `mypy --strict`（Req 17, design §2.5）
- [ ] **2.1.2 [P]** Container Apps Environment / Key Vault `kv-hack2026-tyu3o4` / App Insights / Cosmos Serverless / AI Search Basic の Bicep モジュール化（既存リソース参照＋新規 index/collection 追加）(Req 17, 18, design §2.4)
- [ ] **2.1.3 [S→2.1.2]** Entra ID + Managed Identity の per-service 割当（Schema Manager / Delta Detector / Notification Dispatcher 最小権限）(Req 17.1, 17.7, design §9)
- [ ] **2.1.4 [P]** GitHub Actions: lint / typecheck / unit test / Bicep what-if、PR ゲート（Req 16）

### 2.2 データモデル / 永続化
- [ ] **2.2.1 [S→2.1.2]** Cosmos collection 12 種 provisioning（design §5.1 table）partition key `{sector}#{unit}` 統一（Req 15）
- [ ] **2.2.2 [P]** AI Search `corpus-{env}` index 定義（vector 1536 dim, filterable: sector/unit/schemaFieldId/shareability/isActive/supersededBy）(design §5.2)
- [ ] **2.2.3 [P]** Cosmos repository 層（TS）: 型生成 + partition-key 強制 + redact 時 content 除外ヘルパ（Req 7, 17.4）

### 2.3 開発・運用フレーム
- [ ] **2.3.1 [P]** App Insights `customMetrics` 一覧定義（design §7、`schema.notify.dispatched` 等を含む）
- [ ] **2.3.2 [P]** Cost Telemetry Cron 雛形（毎日 1 回 AOAI token 集計 → $120/$150 で `cost.alert.fired` emit）(Req 16.2, 18)
- [ ] **2.3.3 [P]** PII Scrubber util（emit 直前適用）(Req 16.6)

---

## M3: Schema 管理ループ（Persona A、Week 2 前半）

- [ ] **3.1 [S→2.2.1]** `SchemaManagerAgent` 実装: upsert / setActive / bulkImport / getHistory（design §4.1 contract、Python or TS は flag day 結果で確定）(Req 1, 2, 3)
- [ ] **3.2 [S→3.1]** `schemas` / `schema_audit_log` への二相書込（revision 単調増加・物理削除禁止 invariant）(Req 2.1, 17.6)
- [ ] **3.3 [S→3.1]** Admin UI: schema CRUD 画面 + is_active トグル + 変更履歴 read view（Req 2.6）+ 自己承認率 dashboard（Req 9, 16）
- [ ] **3.4 [P]** `POST /schemas/bulk-import`（同セクター内ユニット間複製、partition 自動分離）(Req 3.1-3.4)
- [ ] **3.5 [S→3.2]** `GET /schemas/history?sector&unit&limit&since` API + Chat UI sidebar（業務ユーザー read-only）(Req 2.6, 17.7)

---

## M4: Notification Dispatcher（Daichi review R2 AC#5/#6/#7 中核, Week 2 後半）

- [ ] **4.1 [P]** Discord webhook URL 4 種を Key Vault に格納（`DISCORD_WEBHOOK_URL_{SCHEMA_UPDATES,PENDING_REVIEW,EXPIRED,COST_ALERT}`）+ 参照 helper（Req 17.2, design §4.6）
- [ ] **4.2 [S→3.2,4.1]** `NotificationDispatcher` 実装: subscribe(`schema.updated`/`record.pending_review`/`record.expired`/`cost.alert.fired`) → PII scrub → webhook POST → 3 回 backoff retry → 失敗時 `error_logs` + admin channel 二次通知（design §4.6 + §6 Error）
- [ ] **4.3 [S→3.1,4.2]** Schema Manager Agent から `schema.updated` event emit 結線（payload: `{sector, unit, revisionId, changeType, fieldName, diffSummary, historyUrl}`）(Req 2.5)
- [ ] **4.4 [S→2.2.1]** **Schema Revision Gate**: `POST /turn` 内、Delta Detector invoke 直前に `dialogue_turns.schema_revision_seen_at` ↔ `schemas.revision_id` 比較 → `schemaUpdateBanner` 載せる / ack で `schema_revision_seen_at` 更新（Req 2.7, design §4.6 state diagram）
- [ ] **4.5 [S→4.4]** Chat UI banner コンポーネント + ack action + 「最近の変更」history link（Req 2.7）
- [ ] **4.6 [P]** Discord 通知 E2E テスト（admin 更新 → webhook → 業務ユーザー次 turn で banner → ack → 通常 flow）（design §8 Integration）

---

## M5: 通常対話 / Retrieval / B5 矛盾通知（Persona B 基底, Week 3 前半）

- [ ] **5.1 [S→2.2.1]** `POST /turn` API: dialogue_turns append + AOAI gpt-4o function-calling で `{response, self_critic_score, self_critic_reason}` 構造化出力（Req 4, 12.2）
- [ ] **5.2 [P]** `redact=true` 経路: content 非保存 + Delta Detector skip + retrospective `DELETE /turn/{id}` 物理削除（Req 7, 12.8）
- [ ] **5.3 [S→2.2.2]** Retrieval flow: AI Search query（partition filter + shareability + isActive + supersededBy 除外）+ schemaFieldId group + 矛盾検出（>=2 異見解）(Req 6, 8)
- [ ] **5.4 [S→5.3]** Chat UI: citation 表示 + 矛盾時 inline「他に N 件の異なる見解あり」+ 並列表示（B5 = Req 8）
- [ ] **5.5 [S→5.3]** `GET /citations/{id}`: `corpus_meta.referencedCount` インクリ / `superseded_by` 辿って「更新されています」banner（Req 6.4, 6.5, 10.8）
- [ ] **5.6 [P]** `truth_judgment_logs (pattern: activation-time)` 記録 hook（Req 8.4）

---

## M6: Delta Detector + Hearout（B2 コア, Week 3 後半）

- [ ] **6.1 [S→5.1]** `DeltaDetectorAgent` 実装（gpt-4o-mini）: active schema load → per-field score（self_critic + embedding cosine）→ `delta_events` append（Req 12）
- [ ] **6.2 [S→6.1]** 閾値判定: `self_critic < 3` または `3-5 ∧ distance > 0.4` で gap、cooldown 7d、3 turn 連続抑制（Req 12.3-12.7）
- [ ] **6.3 [S→6.1]** Out-of-schema: `schema_candidate_log` append + admin 集約ビュー（Req 12.9, 12.10）
- [ ] **6.4 [S→2.1.2]** Hearout Agent（gpt-4o + MAF `RequestInfoEvent`）: 5W1H 抽出 + ChatExtract 確認 + 5 ターン上限 + SKIP / expired 状態遷移（Req 5, design §4.3 Python contract）
- [ ] **6.5 [S→6.4]** Chat UI Hearout modal（通常チャット併存・cold start ≤ 3 秒・skip ボタン）(Req 5, 18.7)
- [ ] **6.6 [S→4.4,6.4]** Schema Revision Gate と Hearout 起動の優先順位: banner 未 ack 時は当 turn の Hearout 起動を次 turn に持ち越し（design §4.6）

---

## M7: Formalization / Truth Judgment / Review（Persona C, Week 4）

- [ ] **7.1 [S→6.4]** `FormalizationAgent` 実装（gpt-4o）: weight A=record_self_critic / B=1.0 / C=1.0、final=A/10、閾値 0.5（Req 13、MVP は層 A のみ）
- [ ] **7.2 [S→7.1]** final < 0.5: `formalization_queue.status=pending_review` + Notification Dispatcher 経由で当該業務ユーザーに Discord 通知（Req 13.5）
- [ ] **7.3 [S→7.1]** Truth Judgment Module: GraphCheck で atomic claim 分解 → AI Search 類似検索 → FactCheck 3 LLM ensemble → verdict ∈ {supported, novel, conflict}（Req 14）
- [ ] **7.4 [S→7.3]** verdict=conflict は **Conflict queue**、それ以外は **Normal queue with TJ badge**（Req 9, 10）
- [ ] **7.5 [S→7.4]** Review UI 通常 queue: 5W1H + 重み breakdown tooltip + 関連 turn + TJ バッジ + 5 分 lock TTL（Req 9.7-9.11, design §4.5）
- [ ] **7.6 [S→7.4]** Review UI conflict queue（独立画面）: 並列比較 + 3 択（adopt_new / keep_existing / coexist）+ `citation_audit_log` 追記（Req 10）
- [ ] **7.7 [S→7.5]** decision handler: approve → corpus.upsert + corpus_meta + citation_audit_log / edit → TJ 再走 / reject → cooldown 7d（Req 9.5, 14.6）
- [ ] **7.8 [P]** 自己承認率 dashboard + > 30% warning + レビュー中央値 > 3 分で「優先 3 件」モード切替（Req 9.9-9.11）

---

## M8: SLA / Observability / Cost（運用周り, Week 5）

- [ ] **8.1 [S→7.2]** SLA Cron（24h タイマー満了で `formalization_queue.status=expired`）+ Notification Dispatcher で reviewer + 業務ユーザー両方に Discord 通知 + 業務ユーザーに「再ヒアリング / 諦める」選択肢提示（Req 11.3, 11.4）
- [ ] **8.2 [S→8.1]** 再ヒアリング選択時の Hearout 再起動経路（既存 hearout_records.outcome 連鎖参照）(Req 11.5, 11.6)
- [ ] **8.3 [S→2.3.1]** customMetrics emit を全 agent / API に組込（design §7 リスト全件）
- [ ] **8.4 [S→2.3.2]** Cost Telemetry: $120 / $150 で `cost.alert.fired` → Discord admin channel + Tier A/C 縮退提案表示（Req 18, design §4.6）
- [ ] **8.5 [P]** error_logs に redact 時 content 除外を確認するテスト + 認証エラーは汎用 5xx + 内部ログのみ（Req 17.4, 17.5, 16.4）

---

## M9-M12: Follow-up backlog（**MVP 外**, design §1 表）

> spec-driven 改修サイクル（機能レビュー → 運用メトリクス再判定）で昇格／降格。`tasks.md` には起票するが M2-M8 のクリティカルパスには載せない。

- [ ] **F-W1** 層 B（EffiARA reliability）/ 層 C（時間減衰）重み導入 + 閾値 0.7 復帰（Req 13、design §1）
- [ ] **F-T1** Web/KG hybrid grounding（Bing / Wikipedia）(Req 14)
- [ ] **F-N1** Teams Adaptive Card 配信、メール通知、ベテラン PM の opt-in subscription（Req 2.5 拡張）
- [ ] **F-A1** Schema bulk import UI / テンプレ複製 / マス間 schema diff（Req 3 拡張）
- [ ] **F-B1** redact 自動候補提示（LLM scrubbing）(Req 7 拡張)
- [ ] **F-B2** proactive な「あなたの過去 record と矛盾」warning（Req 8 拡張）
- [ ] **F-C1** Reviewer pool 自動 routing / レビュー学習 loop（Req 9 拡張）
- [ ] **F-C2** Conflict クラスタリング + 自動マージ提案（Req 10 拡張）
- [ ] **F-D1** 検索 SPA（pull retrieval UI）昇格判定（decisions.md D1）
- [ ] **F-D2** 2nd spec（業務改革ナラティブ）判定（decisions.md D2）
- [ ] **F-X1** multi-tenant / マス横断検索（Phase 2、Req 6.1）
- [ ] **F-E1** embedding モデル切替 + 全 index 再構築（Req 18.5/18.6）

---

## 横断・常時タスク

- [ ] **X-1** 各 PR で Req traceability 表（design §3）の該当行 link を必須化
- [ ] **X-2** `/kiro:spec-status` を週 1 で hack-pm に投下
- [ ] **X-3** Mao が hack-pm / hack-chat レビューを 24h SLA で取り込み、tasks.md に反映

---

## Traceability Matrix（Req → Task 番号）

| Req | Tasks |
|-----|-------|
| Req 1 | 3.1, 3.3 |
| Req 2 | 3.1, 3.2, 3.3 |
| **Req 2.5（new）** | **4.1, 4.2, 4.3, 4.6** |
| **Req 2.6（new）** | **3.3, 3.5** |
| **Req 2.7（new）** | **4.4, 4.5, 6.6** |
| Req 3 | 3.4 |
| Req 4 | 5.1 |
| Req 5 | 6.4, 6.5 |
| Req 6 | 5.3, 5.5 |
| Req 7 | 2.2.3, 5.2, 8.5 |
| Req 8 | 5.3, 5.4, 5.6 |
| Req 9 | 3.3, 7.5, 7.7, 7.8 |
| Req 10 | 7.4, 7.6, 7.7 |
| Req 11 | 8.1, 8.2 |
| Req 12 | 5.1, 6.1, 6.2, 6.3 |
| Req 13 | 7.1, 7.2 |
| Req 14 | 7.3, 7.7 |
| Req 15 | 2.2.1 |
| Req 16 | 2.3.1, 2.3.3, 8.3, 8.5 |
| Req 17 | 2.1.3, 4.1, 8.5 |
| Req 18 | 2.3.2, 8.4 |

---

## Definition of Done（MVP = M2-M8 終了基準, design §0 Goals 完全準拠）

1. Critical path（A1 → B1 → B2 → C1 → B3）が 1-2 マスで E2E 動作（Integration E2E green）
2. R2 AC #5/#6/#7（Discord 通知 + 履歴 view + banner）通し E2E green
3. HITL 承認後 record が次回 turn で必ず retrieve され citation ID 応答に明示
4. Azure 累積コスト $200 内（想定 $143、バッファ $57）
5. wall-clock 6 週内（M2 start 2026-05-26 → M8 end 2026-07-05 目安）
