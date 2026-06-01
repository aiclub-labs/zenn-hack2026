# Handoff: UAT for hackathon submission

> 作成日: 2026-05-26 / 用途: ハッカソン提出前の UAT 実施ハンドオフ
> 関連: `personas-stories.md`, `requirements.md`, `design.md`, `../../docs/UAT-SCENARIOS.md` (本 doc から派生)
> ステータス: **UAT 開始可** (S8 E2E パス, 統合 UI デプロイ済, reset script 稼働)

---

## 0. このドキュメントの目的

ハッカソン審査までに **3 persona × 全 user story が現行デプロイで満たされていること** を、再現可能な手順で検証する。デモナラティブ (起承転結) と差別化メッセージ ("対話の最中に暗黙知が発生した瞬間を捕まえる") が UI 上で実証できる状態にする。

---

## 1. UAT の前提環境

### 稼働中リソース (rg-hack2026-dev)

| サービス | エンドポイント / 名前 | 用途 |
|---|---|---|
| Web UI (統合 SPA) | `https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/` | Chat / Admin / Review すべてここから |
| API | `ca-hack2026-dev-api` (同 FQDN /turn 等で nginx proxy) | FastAPI |
| Agent Runner | `ca-hack2026-dev-agent-runner` | Hearout / Delta Detector 等 |
| AOAI | swedencentral / gpt-5.4 + gpt-5.4-mini (Global Standard 250k TPM) | Main + self-critic |
| Cosmos | `cosmos-hack2026-dev-ytzykj` / db=`dialogue_delta` | 12 container (うち 2 未作成: conflicts, cost_ledger) |
| Key Vault | Discord webhook 4 種 + AOAI / Cosmos secrets | Managed Identity 経由 |

### baseline seed

- tenant `manufacturing-s8b#line-A` に `schemas.defect_root_cause` rev 1 のみ
- 他テナント (`strategy#auto`, `mfg#line-B` 等) は空。UAT で別マス検証する場合は admin UI で先に schema を作る

### リセット手順

```bash
COSMOS_ENDPOINT=https://cosmos-hack2026-dev-ytzykj.documents.azure.com:443/ \
python scaffold/scripts/reset_tenant.py \
  --sector manufacturing-s8b --unit line-A --confirm
```

オプション: `--include-schemas` (baseline も消す), `--dry-run` (件数確認のみ)

**いつ走らせるか**: 各 persona シナリオを通しで回す前 / デモリハーサル前 / 仕様変更後の再検証時。

---

## 2. UAT スコープと非スコープ

### スコープ (must-verify)

1. **Persona A (シゲル)**: schema CRUD / revision / 履歴 / 横展開
2. **Persona B (ハルカ)**: 通常対話 / 5W1H ヒアリング / 過去 record 引用 / redact / 矛盾通知
3. **Persona C (タケシ)**: 通常レビュー / 編集 / 拒否 / 矛盾 / SLA expired
4. **クリティカルパス (デモ線)**: A1 → B1 → B2 → C1 → B3 が連続で動く
5. **品質指標**: persona ごとの数値 KPI が現行 UI で観測可能か / 妥当な値が出るか
6. **差別化メッセージ実証**: 「対話中に暗黙知が捕捉される」「Copilot が拾わないものを拾う」が画面で示せる

### 非スコープ (今回見送り)

- 本番相当の負荷試験 (TPM / RPS) — ハッカソンスケールでは不要
- マルチテナント数十マス並走 — 横展開は 2 マスで検証
- 外部 SSO / 本格 RBAC — stub user header で進める
- Discord 通知の人間視認テスト — 開発期に検証済、UAT は API/payload までで OK

---

## 3. UAT 進行プロトコル

### 役割分担

| 役割 | 担当 | やること |
|---|---|---|
| Driver | テスター本人 | UI 操作 / 入力 / 結果記録 |
| Observer | (任意で 2 人目) | 期待外挙動の早期発見 / スクショ取得 |
| Reset operator | テスター | 各 persona セット冒頭で reset_tenant.py 実行 |

### 実施順序 (推奨)

1. **Persona A scenarios** (S1.x) — schema を作る基盤
2. **Persona B scenarios** (S2.x) — 対話で knowledge を生む
3. **Persona C scenarios** (S3.x) — レビューで corpus を作る
4. **Critical Path (S4.x)** — A→B→C→B' の連鎖
5. **Edge / Risk (S5.x)** — persona カードに書かれたリスクが現実化していないか
6. **Demo dress rehearsal (S6)** — 3 分ナラティブを通しで

各シナリオは **PASS / PARTIAL / FAIL** を `docs/UAT-RESULTS.md` (新規) に記録。FAIL は GitHub issue 化。

### 中断・再開

任意の persona セット完走後で中断可。再開時は当該テナントを reset してからやり直す (state 残骸防止)。

### 完了判定

- すべての PRIORITY=HIGH シナリオが PASS
- Critical Path (S4.1) が PASS かつ録画あり
- Demo dress rehearsal (S6) で 3 分以内に起承転結が成立

---

## 4. 既知の制約・回避策

| 制約 | 影響 | 回避策 |
|---|---|---|
| `conflicts`, `cost_ledger` container 未作成 | C4 矛盾シナリオで Cosmos 書込失敗の可能性 | scenario S3.4 で `delta_events` ベースの代替検証 |
| Hearout modal の 5W1H プロンプトは初期化文言が固定 (`who?` から) | B2 で文脈に応じた質問にならないことがある | S2.2 では「機能が起動して 5 ターン以内で終わる」までを検証、品質改善は P2 issue |
| Truth Judgment / Conflict 検出は MVP では active-time のみ | C4 で必ず conflict_detected が出るとは限らない | S3.4 で意図的に矛盾コーパスを 2 件投入してから検証 |
| Self-critic score は AOAI 出力次第でブレる | B2 起動条件が確率的 | S2.2 では 3 連続クエリで起動を強制 |
| UI 言語固定 (ja-JP) | 英語審査員向け補足不要なら無視 | デモ録画に英字キャプション重ね焼き |

---

## 5. 成果物 (UAT 完了時)

1. `docs/UAT-RESULTS.md` — 全 scenario の合否と evidence (スクショ / 録画リンク)
2. `docs/demo-recording.mp4` (or YouTube unlisted) — Critical Path の通しデモ ≤ 3 分
3. `docs/UAT-ISSUES.md` — FAIL/PARTIAL を GitHub issue 化したリスト + 残課題 (post-hack 対応の P2)
4. ハッカソン提出用 README 末尾に「UAT 完了マーカー」追加

---

## 6. 次のアクション

| # | アクション | 期限 | 主体 |
|---|-----------|------|------|
| 1 | `docs/UAT-SCENARIOS.md` 通読 (本 doc 別紙) | 即時 | テスター |
| 2 | Persona A セット実施 | T+0:30 | テスター |
| 3 | Persona B/C セット実施 | T+1:30 | テスター |
| 4 | Critical Path 通しデモ録画 | T+2:00 | テスター |
| 5 | UAT-RESULTS.md 完成 / FAIL issue 化 | T+2:30 | テスター |
| 6 | 残課題に基づく fix → 再 UAT (差分のみ) | 提出 24h 前 | dev |

---

**End of handoff-uat.md** — シナリオ詳細は `docs/UAT-SCENARIOS.md` 参照
