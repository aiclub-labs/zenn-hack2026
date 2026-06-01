# UAT Procedural — T1-T6 upgrade verification

> 作成: 2026-05-28 / 対象 commit: `c25cfa8`
> Base URL: https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/
> Tenant default: `manufacturing-s8b` / `line-A` / `haruka@example.com`
> 所要時間: 約 15-20 分（App Insights ingestion 5-10 分の待機を含む）

実行順は **Step 0 → 1 → 2 → 3 → 4 → (待機) → 5 → 6**。Step 5 は App Insights 反映を待つ必要があるため、待機中に Step 6 を進めるのが効率的。

---

## Step 0. 前提準備 (3 分)

### 0-1. Tenant reset
ローカル shell で:

```bash
cd <redacted-path>/personal-hub/ai-club/events/microsoft-agent-hackathon-2026/scaffold
python scripts/reset_tenant.py --sector manufacturing-s8b --unit line-A --confirm --include-schemas
```

**期待**: `reset OK` 表示。Cosmos の `manufacturing-s8b#line-A` partition がクリーンな状態 + baseline schemas 投入済。

### 0-2. ブラウザ準備
1. ベース URL をシークレット window で開く (キャッシュ汚染回避)
2. ヘッダー右上 tenant 設定: sector=`manufacturing-s8b`, unit=`line-A`, user=`haruka@example.com`
3. F12 で DevTools → Console + Network タブを開いておく

---

## Step 1. T6-1: Disclosure footer — 3 surface visual check (2 分)

### 1-1. `/chat`
1. サイドバーから **Chat** をクリック
2. 画面を最下部までスクロール
3. **記録**: フッターテキストをスクリーンショット

**合格条件 (全部 ✅ で pass)**:
- ☐ フッターに以下のテキストが表示される (全文一致):
  > この応答は AI が生成し、自己批評スコアで品質評価しています。機密情報は redact フラグでマスクしてください。 / 言語: 日本語 (ja-JP) 固定、accessibility は Phase 2。
- ☐ 背景が薄灰 (Fluent `colorNeutralBackground3`)
- ☐ 中央寄せ・小さめフォント
- ☐ メインコンテンツの直下に来る (sidebar の高さからはみ出ない)

### 1-2. `/admin`
1. サイドバーから **Admin** をクリック
2. 最下部までスクロール
- ☐ 1-1 と同一フッターが表示される

### 1-3. `/review`
1. サイドバーから **Review** をクリック
2. 最下部までスクロール
- ☐ 1-1 と同一フッターが表示される

**fail 時**: AppShell.tsx L173 付近の `<footer>` を Read で確認。Surface 別に異なる Layout を使っていれば AppShell ラップを再確認。

---

## Step 2. T6-2: per-message self-critic badge (1 分)

1. `/chat` で次を送信:
   ```
   品質管理の標準的なフレームワークは?
   ```
2. AI 応答を待つ (cold start で 5-10 秒)

**合格条件**:
- ☐ 応答カードの下端に `self-critic X.X / 10` のバッジが表示される
- ☐ 数値が 0.0〜10.0 の範囲

---

## Step 3. Hearout を発火させて pending_review を 2 件生成 (5 分)

T3 metric を発火させるために `/review` 上で **approve** と **reject** を 1 件ずつ叩く必要があるため、まず 2 件の review ticket を仕込む。

### 3-1. 1 件目の Hearout
1. `/chat` で次を続けて 3 メッセージ送信:
   ```
   ライン A で 5/22 に発生したクラックの一次切り分け、自分はどう判断した?
   ```
   ```
   同じクラック、表面処理後だったか研磨後だったか思い出せない、どっち?
   ```
   ```
   再発防止で先週決めた暫定対応の中身は?
   ```
2. `self-critic ≤ 3` が出たタイミングで **HearoutModal** が自動で開く
3. 5W1H に最小回答:
   - who: `田中`
   - what: `表面処理後に微細クラック`
   - when: `2026-05-22`
   - where: `line-A プレス機 #3`
   - why: `温度ドリフト疑い`
   - how: `目視 + 拡大鏡`
4. **送信** → modal が閉じる
5. **記録**: DevTools Network で `POST /hearout/*` が 200 を返したことを確認

### 3-2. 2 件目の Hearout (別 session で良い)
1. ブラウザをリロード (session_id 切替)
2. 次の質問で再度 Hearout を発火:
   ```
   先週のプレス機 P-12 で出た打痕、自分が決めた応急対応は何だったか?
   ```
   ```
   その判断材料、金型 clearance 測定値は具体的にいくつだった?
   ```
   ```
   再現テストで OK 判定した条件、温度と圧力のセットを思い出せる?
   ```
3. modal で別の 5W1H 入力:
   - who: `鈴木`
   - what: `打痕欠陥応急対応`
   - when: `2026-05-25`
   - where: `line-A プレス機 P-12`
   - why: `金型クリアランス過大`
   - how: `clearance 再測定 + 暫定研磨`
4. **送信** → 完了

**合格条件**:
- ☐ pending_review queue に 2 件追加された (Step 4 で目視確認)

---

## Step 4. T3-1: review.decision metric を発火 (3 分)

### 4-1. Reviewer に切替
1. ヘッダー右上で user=`takeshi@example.com` (reviewer ロール) に切替
2. `/review` を開く
3. ☐ pending_review が 2 件以上見える

### 4-2. 1 件目: **approve**
1. 1 件目のチケットをクリック → 詳細パネル展開
2. **承認 (approve)** ボタンを押下
3. **記録**: DevTools Network → `POST /reviews/{id}/decision` が 200 を返したことを確認
4. レスポンス body をスクリーンショット (CorpusUpsertResult のキー: `id`, `pk`, etc.)

### 4-3. 2 件目: **reject**
1. 2 件目のチケットをクリック
2. **却下 (reject)** ボタンを押下
3. ☐ POST 200 を確認

### 4-4. 即時 sanity check (Cosmos 経由)
ローカル shell で:
```bash
python scripts/watch_cosmos.py --container formalization_queue --pk "manufacturing-s8b#line-A" --limit 5
```
- ☐ approve したチケットの `decision_status` が `approved` になっている
- ☐ reject したチケットの `decision_status` が `rejected` になっている

---

## Step 5. App Insights で `review.decision` を確認 (5-10 分の ingestion 待機後)

> ⚠️ Step 4 から **最低 5 分** 待つこと。OpenTelemetry → AppInsights の ingestion 遅延あり。

### 5-1. Azure Portal にログイン
1. https://portal.azure.com → resource `appi-hack2026-dev` を開く
2. 左メニュー **Logs** をクリック

### 5-2. クエリ実行 (T3 メイン検証)
次を Logs エディタに貼り付けて Run:

```kusto
customMetrics
| where name == "review.decision"
| where timestamp > ago(30m)
| extend reviewer_id = tostring(customDimensions["reviewer_id"]),
         decision    = tostring(customDimensions["decision"]),
         sector      = tostring(customDimensions["sector"]),
         unit        = tostring(customDimensions["unit"]),
         ticket_id   = tostring(customDimensions["ticket_id"])
| project timestamp, reviewer_id, sector, unit, decision, ticket_id
| order by timestamp desc
```

**合格条件**:
- ☐ 2 行返る (Step 4-2 と 4-3 に対応)
- ☐ `decision` の値が `approve` / `reject` で 1 行ずつ
- ☐ `reviewer_id` = `takeshi@example.com`
- ☐ `sector` = `manufacturing-s8b`, `unit` = `line-A`
- ☐ `ticket_id` が 2 件で異なる

### 5-3. Fairness proxy KQL の動作確認 (`docs/observability-kql.md` §1.1)
```kusto
customMetrics
| where name == "review.decision"
| where timestamp > ago(7d)
| extend reviewer_id = tostring(customDimensions["reviewer_id"]),
         sector       = tostring(customDimensions["sector"]),
         unit         = tostring(customDimensions["unit"]),
         decision     = tostring(customDimensions["decision"])
| summarize count() by reviewer_id, sector, unit, decision
| evaluate pivot(decision, sum(count_))
| extend total = coalesce(approve, 0) + coalesce(edit, 0) + coalesce(reject, 0)
| extend approve_rate = todouble(coalesce(approve, 0)) / todouble(total),
         reject_rate  = todouble(coalesce(reject, 0))  / todouble(total)
| project reviewer_id, sector, unit, approve, edit, reject, total, approve_rate, reject_rate
```

**合格条件**:
- ☐ takeshi の行で `approve=1, reject=1, total=2, approve_rate=0.5, reject_rate=0.5`

**fail 時**:
- `customMetrics` が空 → Container App env `APPLICATIONINSIGHTS_CONNECTION_STRING` を確認。
  ```bash
  az containerapp show -g rg-hack2026-dev -n ca-hack2026-dev-api --query "properties.configuration.secrets[].name"
  ```
- name は出るが reviewer_id が空 → UI の `X-Reviewer-Id` header が抜けている。Network タブで送信 header を確認

---

## Step 6. T5/T2 ドキュメント link sanity (1 分、Step 5 待機中に並走可)

1. リポジトリ root の `README.md` を開く (GitHub or ローカル)
2. Sustainability セクションで以下 link が機能するか確認:
   - ☐ `docs/observability-kql.md` → 200 で開く
   - ☐ `docs/impact-assessment.md` → 200 で開く
   - ☐ `.kiro/specs/dialogue-delta-formalization/framework-review.md` → 200 で開く
3. `framework-review.md` を開いて §0 で:
   - ☐ Grade 表に「初版 → 2026-05-28」の表記がある
   - ☐ Top 3 リスクのうち #1 と #2 が ✅ マーク付き

---

## サマリ判定

| Step | 内容 | 結果 | 備考 |
|---|---|---|---|
| 1-1 | /chat footer | ☐ pass ☐ fail | |
| 1-2 | /admin footer | ☐ pass ☐ fail | |
| 1-3 | /review footer | ☐ pass ☐ fail | |
| 2 | self-critic badge | ☐ pass ☐ fail | |
| 3 | Hearout x2 → pending | ☐ pass ☐ fail | |
| 4-2 | approve POST 200 | ☐ pass ☐ fail | |
| 4-3 | reject POST 200 | ☐ pass ☐ fail | |
| 4-4 | Cosmos status 反映 | ☐ pass ☐ fail | |
| 5-2 | review.decision metric 2 行 | ☐ pass ☐ fail | 5-10 min lag |
| 5-3 | Fairness pivot KQL | ☐ pass ☐ fail | |
| 6 | README links + grade 更新 | ☐ pass ☐ fail | |

**最低合格ライン**: 1-1〜1-3 (footer) + 4-2/4-3 (POST 200) + 5-2 (metric ≥ 1 行) の 5 項目すべて pass で「T1-T6 upgrade 動作確認 OK」。

**End of UAT-T1-T6.md**
