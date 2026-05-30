# UAT Scenarios — dialogue-delta-formalization

> 別紙: `../.kiro/specs/dialogue-delta-formalization/handoff-uat.md`
> 対象: 統合 SPA https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/
> 各シナリオ: PRIORITY (HIGH/MED/LOW) / persona / 関連 Story / 関連 Req / 前提 / 手順 / 期待 / KPI / 失敗時 fallback

凡例:
- **Story** = `personas-stories.md` §2 の ID (A1〜A3, B1〜B5, C1〜C5)
- **Req** = `requirements.md` の番号
- **Tenant default** = `manufacturing-s8b` / `line-A` / `haruka@example.com`
- **Reset 印** ⟳ = この shape を実行する前に `reset_tenant.py --confirm` を回すこと

---

## 📍 Affordance Map (UAT 実行前に必ず確認)

各シナリオが要求する操作と、UI 上で実際にそれを実現する affordance の対応表。**ここに「該当 UI 無し」のものが残っていたら、シナリオ実行は dev shortcut を使わずブロック報告すべき。**

### グローバル (ヘッダー / ナビ)

| 操作 | UI affordance | 場所 | モバイル可視性 |
|---|---|---|---|
| sector 切替 | テキスト Input | ヘッダー右側 (Title3 下) | ✅ 折返し後も見える |
| unit 切替 | テキスト Input | ヘッダー右側 | ✅ |
| user_id (ペルソナ) 切替 | テキスト Input ← 2026-05-30 追加 | ヘッダー右側 | ✅ |
| route 切替 | NavLink ボタン | サイドバー (mobile では上端に横並び) | ✅ |
| 現在 tenant 可視化 | Badge `sector / unit` | ヘッダー左 | ✅ |

### Chat (Persona B)

| 操作 | UI affordance | コンポーネント |
|---|---|---|
| 質問送信 | Input + 送信ボタン | `Chat.tsx` composer |
| Redact ON/OFF | トグル (🔒 アイコン) | `RedactToggle.tsx` toolbar |
| HearoutModal 起動 | 自動 (`gap_detected=true` で自動 open) | `HearoutModal.tsx` |
| HearoutModal で skip | 「skip」ボタン | `HearoutModal.tsx` |
| 5W1H 回答送信 | 「送信」ボタン | `HearoutModal.tsx` |
| citation 詳細遷移 | citation バッジ tap → `/records/:id` | `CitationCard.tsx` |
| 矛盾 inline 表示 | 応答上部/下部に banner | `ConflictInline.tsx` |
| schema 更新通知 | 画面上部 banner + 「確認」ボタン | `SchemaUpdateBanner.tsx` |
| 履歴サイドバー | 右ペイン (mobile では非表示) | `SchemaHistorySidebar.tsx` |

### Admin (Persona A)

| 操作 | UI affordance | route |
|---|---|---|
| schema 一覧 | テーブル (mobile は横スクロール) | `/admin/schemas` |
| schema 新規追加 | 「新規追加」ボタン → modal | `/admin/schemas` |
| schema 編集 | 行内 編集ボタン → modal | `/admin/schemas` |
| schema 無効化 | is_active トグル | `/admin/schemas` |
| revision 履歴 | テーブル | `/admin/history` |
| バルクインポート | JSON 入力 textarea + 「適用」 | `/admin/import` |
| 自己承認率 KPI | カード + チャート | `/admin/self-approval` |

### Review (Persona C)

| 操作 | UI affordance | route |
|---|---|---|
| 通常レビュー一覧 | テーブル | `/review` |
| record 詳細 | 行 tap → 右ペイン or modal | `/review` |
| 承認 | 「承認」ボタン | `/review` |
| 編集後承認 | 「編集」→ 「保存して承認」 | `/review` |
| 拒否 | 「拒否」ボタン | `/review` |
| 矛盾比較 | タブ切替 + 並列比較 | `/review/conflict` |
| 自己承認率 KPI | カード + チャート | `/review/self-approval` |

### その他

| 操作 | UI affordance | route |
|---|---|---|
| Ranking 閲覧 | カード列 | `/popular` |
| schema changelog | テーブル | `/changelog` |
| record 詳細 | 全画面 | `/records/:id` |

### ⚠️ 既知 affordance 制限 / 検証 TODO

| 項目 | 状態 |
|---|---|
| バルク CSV インポート | 未確認 (JSON のみ実装の可能性) |
| 24h SLA expired の業務 U 側通知 | UI 経路未確認 (Discord webhook のみか?) |
| Persona B → C 兼任時の self-approve UI block | gating 無いと想定 (audit log のみ) |
| モバイルで modal を背景タップで誤閉鎖 | 要確認 |

> **UAT 実行ルール**: シナリオ手順が要求する操作と上表を突き合わせ、「affordance 無し」なら手順を実行せず Skip + UI 改善 issue を切る。dev shortcut (localStorage, DevTools 直書き) は使わない。

---

## S1. Persona A — Admin (シゲル) シナリオ

### S1.1 [HIGH] マス開設: 5-10 件 schema 初期定義 (A1)

**Story**: A1 / **Req**: 1.1, 1.3, 9.3
**前提** ⟳: tenant fresh + `--include-schemas`
**手順**:
1. UI ヘッダーで sector=`strategy-poc`, unit=`auto-mfg`, user_id=`shigeru.dev` に切替
2. `/admin/schemas` → 新規追加 を 5 回
   - `customer_priority_axis` (string, "顧客優先度の判断軸", 例: "売上 > 戦略適合")
   - `internal_review_blocker` (string, "社内承認で詰まる典型ポイント", 例: "リスク部の固有要件")
   - `competitor_response_pattern` (enum, "競合の典型対応", 例: "価格据置+保守強化")
   - `proposal_writing_tone` (string, "顧客別の提案文体", 例: "短文+数値強調")
   - `escalation_threshold` (number, "案件規模のエスカ閾値(MJPY)", 例: 30)
3. 保存後に一覧で全 5 件が表示されることを確認

**期待**:
- 各 row の rev=1, is_active=active, updated_at 表示
- Cosmos `schemas` container の partition `strategy-poc#auto-mfg` に 5 件
- Admin UI 上部 KPI 帯に「リジェクト率」表示 (初回は mock)

**KPI**: スキーマ 5-30 件/マス を満たす入口

**失敗時 fallback**: API `POST /schemas` を直接叩いて投入 → UI は read-only として確認

---

### S1.2 [HIGH] スキーマ調整: 編集で revision を進める (A2)

**Story**: A2 / **Req**: 1.2, 1.4
**前提**: S1.1 完了
**手順**:
1. `/admin/schemas` で `customer_priority_axis` の編集を開く
2. description を「**初回ヒアリング時の**顧客優先度の判断軸」に変更 → 保存
3. `/admin/history` で revision 履歴を確認

**期待**:
- 該当 row の rev が 2 に増加
- 履歴に rev1 (create) と rev2 (update) の audit エントリ
- 旧 rev1 は物理削除されず audit 保持 (Cosmos `schema_audit_log` 確認)

---

### S1.3 [HIGH] is_active トグルで無効化 (A2)

**Story**: A2 / **Req**: 1.2
**前提**: S1.2 完了
**手順**:
1. `escalation_threshold` を「無効化」
2. Chat タブに移動して同マスで関連質問「30 MJPY 以上の案件はどう扱う?」を送信
3. 戻って `/admin/schemas` に再表示

**期待**:
- is_active=false で行が淡色 (or フィルタで非表示)
- 無効化フィールドは Delta Detector の照合対象から外れる (delta_events に escalation_threshold 出ない)
- 履歴に deactivate audit エントリ

---

### S1.4 [MED] バルクインポートで複数フィールド一括投入 (A1)

**Story**: A1 / **Req**: 3.1-3.4
**前提**: 別 unit (`line-B`) を tenant に切替
**手順**:
1. `/admin/import` で JSON 配列を貼付 (5 件)
2. プレビュー → 適用
3. 一覧で 5 件 + 既存 baseline 1 件 = 6 件確認

**期待**:
- partition `manufacturing-s8b#line-B` に書込
- 同一 sector 内の別 unit への複製を想定した API パスが動作
- エラー時は行単位エラー表示

---

### S1.5 [HIGH] マス追加 (横展開): 別 sector でゼロから (A3)

**Story**: A3 / **Req**: 9.3, 9.4
**前提**: tenant fresh
**手順**:
1. sector=`fintech-poc`, unit=`retail-bank` に切替
2. `/admin/schemas` で新規 3 件登録 (compliance_filter / risk_appetite_axis / churn_signal_pattern)
3. Chat タブで該当マスの質問を投げて Delta Detector が新 schema を見ていることを確認

**期待**:
- infra 変更ゼロ (Cosmos の新パーティションのみ自動生成)
- 既存 `manufacturing-s8b` テナントへの影響なし (cross-tenant 漏洩無)

**KPI**: 新マス開設 ≤ 1 日 (今回は ≤ 5 分で達成)

---

### S1.6 [MED] スキーマ履歴の業務ユーザー read 経路 (A2 補助)

**Story**: A2 / **Req**: 2.6
**前提**: S1.2 完了
**手順**:
1. user_id=`haruka@example.com` (業務U) に切替, 同マス
2. Chat 右サイドバー「最近の schema 変更」を確認
3. 個別エントリをクリックで `/admin/schemas/history?sector=...&unit=...` に遷移

**期待**:
- read 専用ビューが業務ユーザーロールで開ける
- write 操作 (編集/削除) ボタンは非表示 or disabled

---

### S1.7 [HIGH] 自己承認率 KPI ダッシュボード (Persona A 指標)

**Story**: §1 A の「導入後に追う指標」
**前提**: いくつかレビュー済 record があると望ましい (なくても OK)
**手順**:
1. `/admin/self-approval` を開く

**期待**:
- reject 率 ≤ 20% 目標値の可視化
- revision 頻度 / マスごとの schema 件数の可視化 (mock でも可)
- 数値が「指標として読める」 (単位 / 期間が明示)

---

## S2. Persona B — 業務ユーザー (ハルカ) シナリオ

### S2.1 [HIGH] 通常対話: gap なしの単純応答 (B1)

**Story**: B1 / **Req**: 2.1, 2.2, 3.5
**前提** ⟳: tenant `manufacturing-s8b#line-A`, baseline schema 1 件あり
**手順**:
1. Chat で一般的な質問「品質管理の標準的なフレームワークは?」を送信
2. 応答 + self-critic を確認

**期待**:
- 応答が一般論として返る (citation なしで OK)
- self-critic ≥ 6 (gap 起動しない閾値)
- HearoutModal は開かない
- dialogue_turns に 1 件追記

---

### S2.2 [HIGH] 5W1H ヒアリング介入: gap 検知で modal 起動 (B2)

**Story**: B2 / **Req**: 3.3, 4.1-4.6
**前提** ⟳: 同上
**手順**:
1. Chat で具体事象を 3 連続で送信:
   - 「ライン A で 5/22 に発生したクラックの一次切り分け、自分はどう判断した?」
   - 「同じクラック、表面処理後だったか研磨後だったか思い出せない、どっち?」
   - 「再発防止で先週決めた暫定対応の中身は?」
2. self-critic score を観察, ≤ 3 になるはず
3. HearoutModal が自動で開くことを確認

**期待**:
- 3 ターン以内に modal が開く
- 5W1H 質問が cold start ≤ 3 秒で表示
- 「skip」「回答送信」両ボタンが視認可能
- modal が通常チャット文脈を隠さず重なる (context 見える UI)

**KPI**: 1 日のヒアリング 1-3 回相当 / skip 率 ≤ 50% (連続起動でも乱発しない)

**失敗時 fallback**: API `POST /turn` のレスポンスで `gap_detected=true` を直接確認 → UI 側の modal 連携バグとして切り分け

---

### S2.3 [HIGH] ヒアリング回答 → record 生成 → 次対話で参照 (B3) ★Critical

**Story**: B3 / **Req**: 8.1, 8.2, 8.5
**前提**: S2.2 完了 (modal が立っている状態) または 過去 record が corpus に既存
**手順**:
1. modal で 5W1H に回答 (who="haruka", what="表面処理後に微細クラック", when="2026-05-22", where="line-A プレス機 #3", why="温度ドリフト疑い", how="目視 + 拡大鏡")
2. 5 ターン以内に完了 → `formalization_queue` に pending_review として入る
3. **(S3.1 で reviewer 承認)** → corpus に上がる
4. 後日 (同 session で OK) 「先週 5/22 のクラック、原因仮説は何だった?」を送信
5. 応答に citation ID が出ること, 「前回△△と話した」言い回しを確認

**期待**:
- modal 5 ターン以内, hearout_records に保存
- 承認後 retrieval で自分の record が引用される
- citation バッジクリックで `/citations/{id}` 詳細が見える

**KPI**: citation「役立った」FB 率 ≥ 60% (今回は機能動作までで OK)

---

### S2.4 [HIGH] redact フラグで機密 turn を保存しない (B4)

**Story**: B4 / **Req**: 2.4, 11.3
**前提** ⟳
**手順**:
1. Chat 右上「Redact 機密」を ON
2. 顧客名 + 案件コード入りの質問「顧客 ACME 社 案件 P-2026-093 の見積、自分はどこを譲った?」を送信
3. 応答を受け取った後 Cosmos `dialogue_turns` を確認

**期待**:
- 応答は返る (AI 推論は走る)
- Cosmos には turn メタデータのみ, content フィールドが空 or マスク済
- Delta Detector の delta_events も skip (gap 検知走らない)

**失敗時 fallback**: `--dry-run` で reset script を回し件数差分で content 有無を間接確認

---

### S2.5 [HIGH] 矛盾検知通知: 他見解あり inline 表示 (B5)

**Story**: B5 / **Req**: 8.4
**前提**: 同 schema field に矛盾する record を 2 件以上 corpus に投入 (S3.4 と連携)
**手順**:
1. 「クラックの根本原因は何が定説?」を送信

**期待**:
- 応答末尾 or 上部に「他に N 件の異なる見解あり」inline 表示
- 関連 record 並列表示 (or リンクで citations 詳細にジャンプ)
- ConflictInline コンポーネントの conflict_count > 0

---

### S2.6 [MED] schema update banner: revision 増加後の初回 turn (B1 補助)

**Story**: A2 + B1 / **Req**: 2.7
**前提**: S1.2 (schema rev 2 化) 直後, 別 session_id で Chat 開始
**手順**:
1. 任意の質問送信
2. SchemaUpdateBanner が画面上部に表示
3. 「履歴を見る」リンクで `/admin/schemas/history` に遷移可能
4. 「確認」ボタンで banner クローズ

**期待**:
- banner ack 前は Delta Detector が次 turn の delta 抽出を保留 (design §4.6)
- ack 後の次 turn から通常フロー復活

---

### S2.7 [LOW] 連続入力での skip 率実測 (B2 補助)

**Story**: B2 KPI / **Req**: 5
**手順**:
1. 連続 10 ターン質問 (うち 5 ターンは gap 検知想定)
2. modal 起動回数と skip 回数をカウント

**期待**: skip 率 ≤ 50%, modal 起動が業務リズム阻害でない (主観評価)

---

## S3. Persona C — レビュアー (タケシ) シナリオ

### S3.1 [HIGH] 通常レビュー: 承認 → corpus.upsert (C1) ★Critical

**Story**: C1 / **Req**: 6.1-6.3, 7.1-7.3
**前提**: S2.3 で formalization_queue に 1 件入っている
**手順**:
1. user_id=`takeshi.dev` に切替 → `/review` キューを開く
2. 重み 0.7 以上の record を選択 → 5W1H 要素 / 重み breakdown / 関連 dialogue turns を確認
3. 「承認」ボタンクリック

**期待**:
- 承認後 Truth Judgment 自動起動 (`truth_judgment_logs` に行追加)
- 整合性スコア ≥ 0.4 で corpus.upsert (AI Search index に投入)
- `formalization_queue` の status=approved
- 一覧から該当 row が消える

**KPI**: 処理時間中央値 ≤ 2 分 (この 1 件で 2 分以内に完了できれば PASS)

---

### S3.2 [HIGH] 編集レビュー: 内容修正して承認 (C2)

**Story**: C2 / **Req**: 6.4
**前提**: queue に修正したい record あり
**手順**:
1. 「編集」モードで description 等を修正
2. 「保存して承認」

**期待**:
- `edit_diff` が監査ログに記録 (reviewer_id, edited_at)
- corpus には編集後の値で upsert
- 元データへの diff が後日参照可能

---

### S3.3 [HIGH] 拒否レビュー: 7日 cooldown 発火 (C3)

**Story**: C3 / **Req**: 6.5
**前提**: 拒否したい record が queue にある
**手順**:
1. 「拒否」を選択
2. 同マス同ユーザーで関連 schema field の質問を即時投げる

**期待**:
- record の status=rejected
- 同 schema field × 同 user_id に対して 7 日間 Hearout 起動抑制 (連投しても modal 開かない)
- cooldown 解除予定時刻が `delta_events` or 専用ストアに記録

**失敗時 fallback**: cooldown は内部 state なので Cosmos 直接確認 OR Hearout 起動有無で間接判定

---

### S3.4 [HIGH] 矛盾検知 → 比較表示で人間判断 (C4)

**Story**: C4 / **Req**: 7.3
**前提**: 同 schema field に矛盾する 2 record (例: 原因仮説 A vs B)
**手順**:
1. `/review/conflict` タブを開く
2. 矛盾候補が並ぶことを確認
3. 既存 record と新 record を比較表示
4. 「新を採用」「既存維持」「両方残す」のいずれかを選択

**期待**:
- conflict_detected フラグ付きで queue に上がる
- 並列比較 UI で 5W1H が左右に並ぶ
- 選択結果が `conflicts` container に書込 (※未作成なら delta_events で代替記録)

**KPI**: conflict resolution 率 ≥ 80% (今回は機能動作で OK)

---

### S3.5 [MED] 24h SLA expired → Discord 通知 (C5)

**Story**: C5 / **Req**: 6.6
**前提**: queue に 24h 以上放置された record (テスト時は SLA を一時的に短縮 or 過去 timestamp で投入)
**手順**:
1. expired 検出 cron が走るのを待つ (or 手動 trigger)
2. `/review` 一覧で該当 row が `expired` 表示

**期待**:
- record status=expired
- Discord webhook (DISCORD-WEBHOOK-URL-EXPIRED) に POST
- 業務ユーザー側に「redo 必要」通知が出る (Chat UI バナー or 別経路)

**失敗時 fallback**: webhook 配信は KV 経由なのでログで status code 確認

---

### S3.6 [MED] 自己承認率 dashboard (Persona C 指標)

**Story**: §1 C の「導入後に追う指標」
**手順**:
1. `/review/self-approval` を開く

**期待**:
- 承認/編集/拒否比率の可視化
- expired 率 ≤ 10% target
- 処理時間中央値の表示

---

### S3.7 [LOW] Persona B=C 兼任ケース: 自己承認フロー (合意済 MVP)

**Story**: §1 末「persona 重複論点」
**前提**: user_id=`haruka@example.com` のまま自分が生成した record を承認
**手順**:
1. ハルカで Hearout 回答 → queue 入り
2. 同じ user_id のまま `/review` で承認

**期待**:
- 自己承認が許容される (UI ブロックなし)
- audit ログに self-approve フラグ (or 同一 user_id) が記録
- Phase 2 で別人レビュー強制化する場合の改修箇所が明確

---

## S4. クリティカルパス (デモナラティブ起承転結)

### S4.1 [HIGH] ★Demo Critical Path: A1 → B1 → B2 → C1 → B3 通し

**Story**: A1 → B1 → B2 → C1 → B3 / **Req**: cross-cutting
**前提** ⟳: tenant fresh + `--include-schemas`
**手順** (3 分以内目標):

| 段 | 時間 | 操作 | 期待 |
|----|------|------|------|
| 起 (A1) | 0:00-0:30 | shigeru で `/admin/schemas` に 3 件投入 (defect_root_cause / inspection_method / escalation_rule) | 3 行 表示, rev=1 |
| 承1 (B1) | 0:30-1:00 | haruka に切替 → Chat で「品質管理の基本フレーム」を送信 | 一般論応答, self-critic ≥ 6 |
| 承2 (B2) | 1:00-1:45 | 「ライン A 5/22 のクラック切り分け方を自分はどう判断?」連投 → modal 起動 → 5W1H 回答 | modal 5 ターン以内, queue 投入 |
| 転 (C1) | 1:45-2:15 | takeshi に切替 → `/review` で 1 件承認 → corpus 反映 | TJ 起動, status=approved |
| 結 (B3) | 2:15-2:45 | haruka に再切替 → 「5/22 クラックの原因仮説、前回何と話した?」 → citation 付き応答 | 前回 record が citation 表示 |

**期待**:
- すべて UI 上で連続実行可能
- 録画 1 本で 3 分以内に収まる
- 「対話の最中に暗黙知が捕まる → レビューで corpus 化 → 次対話で活きる」が視覚的に成立

**KPI**: ハッカソン審査用デモ完成

---

## S5. Edge / Risk シナリオ (persona カード「導入後リスク」由来)

### S5.1 [MED] Persona A リスク: schema 更新が業務側に通知されない

**前提**: admin が rev 2 化したが業務U にバナー出ない場合
**手順**: S1.2 直後に haruka 別 session で chat 開く → banner 表示確認
**期待**: banner 確実に出る = リスク未現実化

### S5.2 [MED] Persona B リスク: modal 連投でフロー阻害

**手順**: 5 ターン連続で gap 検知想定質問を投げる
**期待**: cooldown / 3 turn 連続抑制 (Req 12.3-12.7) が効く / modal は最大 1 回しか開かない

### S5.3 [MED] Persona B リスク: redact 忘れで機密が dialogue_turns に残る

**手順**: redact OFF で機密キーワード入り質問 → Cosmos 確認
**期待**: content が平文で残る (これは現状仕様) → UI で「機密を含む可能性」warning を出すべきか改善 issue 化

### S5.4 [MED] Persona C リスク: 重み breakdown 意味不明で全件承認

**手順**: `/review` で重み breakdown ツールチップ / 説明文の有無を確認
**期待**: 重み A/B/C の意味が UI で読める / なければ UX 改善 issue

### S5.5 [HIGH] Persona C リスク: 24h SLA 超過で expired → redo 負担

**手順**: S3.5 と同じ
**期待**: expired 通知が業務U に届く (Discord + Chat バナー両方)

---

## S6. Demo Dress Rehearsal

### S6.1 [HIGH] 3 分デモ通し録画 + ナレーション

**前提**: S4.1 PASS 済
**手順**:
1. 画面録画 ON (OBS / Win+G)
2. S4.1 をシナリオ通り実演
3. ナレーション英語キャプション準備 ("ai harvests tacit knowledge mid-conversation")
4. 録画を `docs/demo-recording.mp4` (or YouTube unlisted) として保存

**期待**:
- 起承転結 4 段が明示的にわかる
- 差別化メッセージが冒頭 + 締めの 2 箇所で言及
- 3 分 ±15 秒に収まる

### S6.2 [MED] 提出 README に UAT 完了マーカー追加

**手順**: `scaffold/README.md` 末尾に "UAT: passed YYYY-MM-DD by [tester]" を追加

---

## 付録 A. シナリオ-ストーリー対応表

| Story | Scenarios |
|-------|-----------|
| A1 | S1.1, S1.4 |
| A2 | S1.2, S1.3, S1.6 |
| A3 | S1.5 |
| B1 | S2.1, S2.6 |
| B2 | S2.2, S2.7 |
| B3 | S2.3 ★ |
| B4 | S2.4 |
| B5 | S2.5 |
| C1 | S3.1 ★ |
| C2 | S3.2 |
| C3 | S3.3 |
| C4 | S3.4 |
| C5 | S3.5 |
| Persona 兼任 | S3.7 |

## 付録 B. KPI チェックリスト (persona カード由来)

| persona | KPI | 検証 scenario |
|---------|-----|--------------|
| A | スキーマ 5-30 件/マス | S1.1 |
| A | reject 率 ≤ 20% | S1.7 |
| A | 新マス開設 ≤ 1 日 | S1.5 |
| B | ヒアリング 1 日 1-3 回 | S2.2, S2.7 |
| B | skip 率 ≤ 50% | S2.7 |
| B | citation FB ≥ 60% | S2.3 (機能動作のみ) |
| C | 処理時間中央値 ≤ 2 分 | S3.1 |
| C | expired 率 ≤ 10% | S3.5, S3.6 |
| C | conflict resolution ≥ 80% | S3.4 |

## 付録 C. PRIORITY=HIGH 一覧 (UAT 必須)

S1.1, S1.2, S1.3, S1.5, S1.7, S2.1, S2.2, S2.3 ★, S2.4, S2.5, S3.1 ★, S3.2, S3.3, S3.4, S4.1 ★, S5.5, S6.1

★ = デモクリティカル (このどれかが落ちると審査ナラティブが崩れる)

---

**End of UAT-SCENARIOS.md**
