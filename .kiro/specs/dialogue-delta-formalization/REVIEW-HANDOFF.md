# Spec Review Session Handoff — dialogue-delta-formalization

> 作成日: 2026-05-13 / 用途: iPad → PC へのレビューセッション継続用ハンドオフ
> 関連: ./requirements.md, ./research.md, ./spec.json, ../../docs/architecture-cards/idea-f-dialogue-monitoring.md
> ステータス: **`/kiro:spec-requirements` 着手前の上流 input レビュー進行中**

---

## 1. 大枠の目的

`/kiro:spec-requirements dialogue-delta-formalization` 実行前に、**Requirements / Design を導出する元になる上流 input ドキュメント群**をレビューし、team 共有 → 承認 → Requirements 着手の流れに進む。

- **方針**: 最小範囲レビュー、後戻りなし、business / spec レベル（機能要件レベルには立ち入らない）
- **deliverable language**: 日本語（spec.json: `"language": "ja"`）
- **承認フロー**: Requirements → Design → Tasks → Implementation の 3-phase

---

## 2. レビュー対象 9 ドキュメント（Tier 1 + Tier 2 確定済）

### Tier 1：feature 直結

| # | パス | 役割 | 進捗 |
|---|------|------|------|
| 1 | `../../docs/architecture-cards/idea-f-dialogue-monitoring.md` | 採用アーキカード v1 | **§0 / §1 議論中** |
| 2 | `../../docs/research/tacit-knowledge-ai-prior-art.md` | 重み付け / 正誤判定根拠 | 未着手 |
| 3 | `../../docs/research/azure-agent-platform-decision.md` | Foundry+MAF 採用根拠 | 未着手 |
| 4 | `../../docs/research/sector-unit-candidates.md` | POC マス候補 | 未着手 |

### Tier 2：project-wide steering

| # | パス | 役割 | 進捗 |
|---|------|------|------|
| 5 | `../../.kiro/steering/product.md` | プロダクト前提 | 未着手 |
| 6 | `../../.kiro/steering/tech.md` | 技術スタック | 未着手 |
| 7 | `../../.kiro/steering/structure.md` | リポジトリ構造 | 未着手 |
| 8 | `../../.kiro/steering/development-model.md` | AI-driven 開発前提 | 未着手 |
| 9 | `../../.kiro/steering/decisions.md` | open 判断ログ | 未着手 |

各 doc の review checkpoint 詳細は **本セッションのチャット履歴**に展開済（PC で resume する際は本 doc → チャット履歴の順で参照）。

---

## 3. 既出の cross-doc issue（横串）

レビュー全体で潰すべき横串論点。Tier 1 / Tier 2 を進める際に都度参照。

| ID | 内容 | 関連 doc |
|----|------|---------|
| **B-1** | admin As-Is pain 欠落（**§1 議論で深堀中**、As-Is 前提自体が未確定問題に発展） | idea-f §1 / product.md / requirements.md |
| **B-2** | out-of-schema 入力取扱い未定義 | idea-f §2 §12 / requirements.md §確認ポイント |
| **B-3** | Retriever agent が全 doc で欠落 | idea-f §3 §5 / product.md / tech.md / azure-decision §4 |
| **B-4** | idea-f Architecture Card v1 が research 結論と乖離（SK orchestrator / Foundry GA risk🔴 残置） | idea-f §3 §4 §10 §12 |
| **S-1** | 予算 $128 / $143 表記揺れ | idea-f §4 / tech.md / requirements.md L32 |
| **S-2** | 次回対話参照スコープ未決定（既に §確認ポイント #3 で open 化済） | requirements.md L51 |

---

## 4. レビュー進捗

### Review #1: idea-f-dialogue-monitoring.md ← **進行中**

12 章を section-by-section で精査済。findings は本セッションチャット履歴に完全展開。

**編集必要箇所（10 ヶ所）**:

| 章 | 編集種別 | 内容 | 状態 |
|----|---------|------|------|
| §0 | 軽微 | 「Sotaro テーゼ」言い換え + 問題/提案/核/インパクト 4 段構造化 | ✅ **完了 (2026-05-13)** |
| §1 As-Is callout | **議論要** | admin As-Is 行追加 → As-Is 前提自体の hypothesize vs identify 議論に発展 | ✅ **D6 で管理（5/14 entry session 合意）** + ✅ §1 冒頭 callout 設置 (2026-05-13) |
| §1 As-Is/To-Be 表 | **必須** | 既存システム grounding（M365 Copilot 等）+ To-Be を PM 視点 × ループ各段階軸に統一 + ギャップ埋める主因 = corpus 蓄積 + retrieval を明示（スキーマはガードレール降格） | ✅ **完了 (2026-05-14)** |
| §2 I/O | **必須** | Retrieval mode 追加 / 「AI」→「既存システム + agent layer」表記同期 / 形式化承認の重み slider → 自己批評スコア表示に修正 (Open Q #3 結論と整合) / 画面イメージを Copilot/agent/User 三層に | ✅ **完了 (2026-05-14)** |
| §3 | 必須 | Orchestrator 表記 "Semantic Kernel" → "Foundry Workflow + MAF 1.0" + Retriever 追加 (B-3, B-4) | ✅ **完了 (2026-05-14)** |
| §4 | 軽微 | 予算 $128 vs $143 footnote (S-1) | ✅ **完了 (2026-05-14)** ※ §10 側も $128 に統一 |
| §5 | 必須 | Retriever 用 tool 追加（`corpus.query` / `aoai.augment_with_records` 等）(B-3) | ✅ **完了 (2026-05-14)** |
| §5b | 議論要 | Tier 優先順 + 非削減 2 件 closing | 5/14 セッションで議論 |
| §7 | 軽微 | partition key `{sector}#{unit}` 言及 1 行 | ✅ **完了 (2026-05-14)** |
| §10 | 必須 | Foundry リスク 🔴→🟡 + D4 リンク (B-4) | ✅ **完了 (2026-05-14)** |
| §12 | 必須 | #3 #4 close 化 + #6 out-of-schema (B-2) 追加 ※ #7 admin As-Is は D6 で管理 | ✅ **完了 (2026-05-14)** ※ #3 は research #1 で close (MVP=A 自己批評のみ、Phase 2/3 で B/C 追加) |
| 次アクション | 軽微 | Foundry リサーチ済反映 | ✅ **完了 (2026-05-14)** |

### Review #2-9: 未着手 — flight 中の bulk review 候補

idea-f はオフライン review 用チェックリストを末尾に追記済（`docs/architecture-cards/idea-f-dialogue-monitoring.md` 末尾 `## レビューチェックリスト（オフライン用）`）。
**先に idea-f チェックリストを潰す**のがリスク低。残り 8 doc は idea-f コメント反映後に順次。

| # | パス | 役割 | フライト中に確認すべき点（quick prompt） |
|---|------|------|-------|
| 2 | `../../docs/research/tacit-knowledge-ai-prior-art.md` | 重み付け / 正誤判定根拠 | MVP=A only (LLM 自己批評) の閾値妥当性 / Phase 2/3 への移行条件 / hallucination 軽減策の MVP 含有可否 |
| 3 | `../../docs/research/azure-agent-platform-decision.md` | Foundry+MAF 採用根拠 | Workflow agent preview の region (swedencentral) リスク評価 / Container Apps フォールバック判断基準 / BYO Cosmos パターンの限界 |
| 4 | `../../docs/research/sector-unit-candidates.md` | POC マス候補 | 候補 5 件のうち推奨 A（戦略×製造業/人材アサイン）が demo 強度で最有力か / D（サステナ×製造業/ESG 監査）との 2 マス展開余地 |
| 5 | `../../.kiro/steering/product.md` | プロダクト前提 | idea-f §0/§1 と product 非交渉原則の整合 / Target Use Cases に既存システム重ね layer 視点が入っているか |
| 6 | `../../.kiro/steering/tech.md` | 技術スタック | idea-f §4 Foundry+MAF 採用と tech.md の決定が同期しているか / 予算 $128/$200 表記の一貫性 |
| 7 | `../../.kiro/steering/structure.md` | リポジトリ構造 | idea-f §3 実装部位パス（`app/orchestrator/`, `app/agents/*.py`, `web/chat/`, `web/hitl/`）が structure 方針と整合 |
| 8 | `../../.kiro/steering/development-model.md` | AI-driven 開発前提 | idea-f §10 工数試算（Wall-clock + Human review 二軸）の換算根拠が development-model と整合 |
| 9 | `../../.kiro/steering/decisions.md` | open 判断ログ | D1-D6 のクローズ条件 / 期限 / 主体が最新か（D6 は 5/14 entry session 後の状態を反映する要） |

### フライト bulk review の進め方

1. idea-f 末尾チェックリストを上から順に inline コメント（`<!-- review: ... -->` で囲うとマークダウン崩さない）
2. 各セクションで「OK / NG（コメント）」を埋める。NG の場合は具体的な書き換え方針か質問を残す
3. idea-f 完了後、残時間あれば doc #2-#9 のうち時間がかかりにくい順（research #2, research #4, tech.md, structure.md）から着手
4. 着陸後: コメント push or screenshot 共有 → 再開時に上から順に潰す

---

## 5. §0 書き換え（✅ 完了 2026-05-13）

````markdown
## 0. 30 秒サマリー

**問題**: 業界 × 領域特化の暗黙知（人間関係 / 顧客固有の意思決定癖 / 過去案件の red-flag パターン等）は個人の頭に閉じ込められ組織知化されない。汎用 LLM では埋められず、「業務価値は domain-specific な暗黙知に宿る」前提に立てば、これが組織 knowledge の最大のロス。

**提案**: 特定セクター × ユニットの業務対話を agent が監視し、**事前定義「欲しいデータ項目」スキーマと、AI 出力 / 人間入力の差分**を暗黙知として検知 → **5W1H ヒアリングループ**で形式知化 → 重み付き corpus に蓄積 → 次回対話で参照。

**核となるアプローチ**: 「文書から暗黙知を抽出する」のではなく「**対話の最中に暗黙知が発生した瞬間を捕まえる**」。事前定義スキーマで対話の暴走を防ぎ、重み付き形式化で人間入力の盲信を避ける。

**期待されるインパクト**:
- 暗黙知が文書化を待たず**発生時点で形式化**される
- 次回以降の同種対話で **AI 応答に蓄積知識が反映**、属人化リセット
- セクター × ユニット単位で**組織知の階層 corpus** が育ち、多マス展開時に水平移植可能
````

変更点:
- **「Sotaro テーゼ (domain-specialty prevalence)」 → 「業務価値は domain-specific な暗黙知に宿る」前提** として埋込み（外部 reviewer にも通る言葉に）
- **問題 / 提案 / 核 / インパクト** の 4 段構造
- 文字量はほぼ同等

**確認事項**: 文字量 / 章立て この内容で OK か、user 判断待ち。

---

## 6. §1 取扱い — **decisions.md D6 で管理（5/14 team 合意待ち）**

### 根の問題

現状 §1 As-Is は「**PM / 営業が業務対話の中で AI に判断を聞く**」前提に依存。この前提自体が unconfirmed:

- 対象組織 AI 部の実態で「PM / 営業 → AI」対話が常態化しているか不明
- **M365 Copilot** が既にこのレイヤーをカバーしている可能性 → 本案の As-Is 描き方が変わる
- もし Copilot で「PM が AI に聞く」が日常化していれば、本案 As-Is は **「Copilot は答えるが暗黙知は harvest しない」** に書き換え必要
- 未導入なら **As-Is が想像ベース**になり reviewer から「対象組織での妥当性」を問われる

### Team 合意が必要な選択肢

| Path | 内容 | Pros | Cons |
|------|------|------|------|
| **A. Hypothesize** | 一般的なエンタープライズコンサル業務対話シナリオを想定で As-Is に書く | スコープ動かしやすい / デモシナリオ具体化容易 | 実在性薄、reviewer pushback リスク |
| **B. Identify** | 対象組織 AI 部の実情（Copilot 利用状況 / PM-AI 対話の現状）をヒアリングして As-Is に書く | リアリティ / デモ説得力 | ヒアリング + 守秘層障壁 / 5/14 に間に合うか |
| **C. Hybrid** | Hypothesize として明示しつつ、5/14 セッションで 対象組織での実例の echo を 1-2 マス分回収 | 両立 / 柔軟 | As-Is に「想定」注記必要 / レビュー観点 +1 |

### 差別化主張への影響

M365 Copilot との overlap が論点なら、差別化は **「Copilot は答えるが暗黙知を harvest しない」** に集約される（§11 Differentiation hook に反映が要る）。

### 確定済アクション（2026-05-13）

- ✅ `../../.kiro/steering/decisions.md` に **D6（TOP PRIORITY）** として 3 Path 登録
- ✅ 暫定結論: **Path C (Hybrid)**
- ✅ 判断期限: 2026-05-14 entry session
- ✅ 判断主体: チーム async（5/14 entry session で確定）
- ✅ **判断視点の明示: 「対象 org として」**（= デプロイ対象組織、対象組織 AI 部 を proxy 想定）。**AI club としての視点ではない**

### 5/14 entry session までの宿題

- メンバーに D6 内容を共有（idea-f §1 を team 共有する前に decisions.md D6 が議題に乗っている状態を作る）
- 対象 org の **M365 Copilot 導入状況 / PM-AI 対話の日常性**について事前情報があれば収集
- 5/14 session で Path A / B / C を team が「対象 org として」合意 → D6 close → §1 編集着手

---

## 7. PC で resume する際の最初の action

1. 本 doc を読む（5 分）
2. 直近のチャット履歴を ↓ から確認（必要時のみ）:
   ```
   C:\Users\sshuser\.claude\projects\C--Users-sshuser-personal-hub-ai-club-events-microsoft-agent-hackathon-2026\df7a792a-25c6-4dfe-ba55-73a660c2a497.jsonl
   ```
3. **次の編集タスクに着手**（§0 / §1 は処理済）:
   - **idea-f §3**: Orchestrator 表記 "Semantic Kernel" → "Foundry Workflow + MAF 1.0" + Retriever agent 追加 (B-3, B-4)
   - **idea-f §5**: Retriever 用 tool 追加 (B-3)
   - **idea-f §10**: Foundry リスク 🔴→🟡 + D4 リンク (B-4)
   - **idea-f §12**: Open Q #3 #4 close 化 + #6 out-of-schema 追加 (B-2)
   - **idea-f §4 / §7 / 次アクション**: 軽微編集
4. 全章編集後 → Review #2 (`tacit-knowledge-ai-prior-art.md`) に進む

---

## 8. 全体カレンダー

| 日付 | イベント | 関連判断 |
|------|---------|---------|
| 2026-05-14 | entry session（メンバー集合） | §1 path 確定 / D3 POC マス確定 / Tier 削減順 |
| 2026-05-15 EOD | team review 完了想定 | 全 doc 編集確定 |
| 2026-05-18 | Week 1 flag day | D4 Foundry 最終判断（実機検証後） |
| 2026-05-19 | Week 1 end | D3 / D5 closing |
| 2026-05-26 | PAYG 移行前 | D1 / D2 closing |

---

## 9. 関連ファイル一覧

### 編集対象（順序付き）
1. `../../docs/architecture-cards/idea-f-dialogue-monitoring.md` — Review #1 進行中
2. `./requirements.md` L1-L129 — Project Description 反映（Review #1 確定後）
3. その他 Tier 1 / Tier 2 doc — 後続レビューで判定

### 参考
- `../../docs/STATUS.md` — 全体進捗
- `../../docs/research/` — リサーチ 4 件
- `../../.kiro/steering/decisions.md` — D1-D5 open 判断

---

**End of handoff**
