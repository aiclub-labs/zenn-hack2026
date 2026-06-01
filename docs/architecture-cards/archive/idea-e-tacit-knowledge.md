# idea-e — 暗黙知の形式化 × 検索+生成 両どりエージェント（Architecture Card）

> **目的**: A/C/D/CD と同じ 12 セクション format。CD 統合カードの再フレーミング。  
> CD カードが「2 出力モードの並置」を前面に出していたのに対し、本案は **「暗黙知の形式化」自体を中心命題** に置き、pull（検索）/ push（生成）はその出口として整理する。  
> ユーザー関心: **実装部位の具体** と **入出力インターフェース** をテンプレ内で独立章化。
>
> 関連: [idea-cd-integrated.md](./idea-cd-integrated.md) · [idea-c-knowledge-archive.md](./idea-c-knowledge-archive.md) · [idea-d-domain-learning.md](./idea-d-domain-learning.md) · [.html 版](./idea-e-tacit-knowledge.html)

作成日: 2026-05-11 / ステータス: チーム review 用 draft（5/11 決定で **本構成を採用するか / CD 原案 / 単独 C を選ぶか**）

---

## 0. 30 秒サマリー

> 散在する案件知見・契約書・transcript・chat を **「暗黙知が形式化された corpus」** に集約し、**同一 corpus から 2 出口** で社員に届ける:
>
> - **検索 (pull)**: 営業/PM が「過去にこの種の案件あった?」と自然文で聞ける。共有可と判断された範囲のみ surfaces
> - **生成 (push)**: ジュニア層に毎朝、同じ corpus から個人化された朝刊カード（要約 / クイズ）を配信
>
> **核**: 「暗黙知の形式化」を **agent + HITL の本業** とし、形式化された corpus を pull/push の両出口で再利用。domain-specialty prevalence 前提（domain-specialty prevalence）の直接実装。

---

## 1. As-Is → To-Be

### As-Is

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| 案件完了 | 成果物は SPO に積まれるだけ / 暗黙知は PM の頭の中 | 暗黙知が個人 silo に滞留 |
| 新規提案 | ex-PM への ad-hoc ping、属人探索 | 形式知化されていないので検索不能 |
| 個人のドメイン学習 | 過去素材があるのに死蔵 / 業務外で動機続かない | 暗黙知が次世代に伝わらない |

**共通の根**: 案件知見は「人に紐づいた暗黙知」のまま、組織で形式化されていない。

### To-Be

| 段階 | 何が起きるか | 解決される痛み |
|------|------------|--------------|
| 案件完了 | PM が agent と一緒に **句単位で「形式化 + 共有可否」判断** → corpus 登録 | 暗黙知が形式知化される |
| 新規提案 | 営業/PM が自然文で検索 → 形式化された corpus から共有可範囲のみ surfaces | 属人探索 解消 |
| 個人の朝 | 形式化済 corpus を素材に、個人化された brief が毎朝届く | 業務内で暗黙知が次世代に伝わる |

### 埋まるギャップ（3 点）

1. **暗黙知の形式化** が agent の本業（kill switch ではなく句単位判定）
2. **形式化済 corpus が 2 出口** で活きる（pull 検索 / push 朝刊）
3. **NDA-safe by design** — HITL の共有可否判定が両出口に cascade

---

## 2. 入出力インターフェース（I/O）— **本カードの独立章**

### モード一覧

| モード | 起点 | 入力 | 出力 | 受け取り画面 |
|------|------|-----|------|------------|
| **Ingest** | PM が案件完了時に投入 | 文書 (pdf/docx/transcript/chat) | clause table + 共有可否ラベル | HITL レビュー UI |
| **Pull (検索)** | 営業/PM の任意タイミング | 自然文クエリ「XX のような案件あった?」 | 案件カード×N + 引用元 + 共有可フラグ | 検索 SPA |
| **Push (朝刊)** | Logic Apps 毎朝 06:30 trigger | (なし、profile 自動参照) | 個人化 brief カード（要約 / クイズ） | Web UI 「本日の朝刊」タブ |

### 画面イメージ（ASCIIモック）

#### Pull — 検索 SPA

```
┌─────────────────────────────────────────────────────────┐
│ 🔍 過去案件検索                              [maumau ▼] │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 製造業の SAP 導入後の運用保守、何かあった?           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ▼ 過去案件 3 件（共有可範囲のみ）                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [製造業] 大手化学メーカー SAP S/4 運用 (2024)        │ │
│ │ 課題: 月次決算遅延 → AI ベース監視で改善             │ │
│ │ 形式化済 clause: 12件 / 共有可: 9件                  │ │
│ │ 出典: clause #04, #07, #11  [詳細→]                  │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [製造業] 自動車部品 ERP 移行 (2025) …                │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Push — 朝刊カード

```
┌──────────────────────────────────────────┐
│ 🌅 本日の朝刊  2026-06-01 (月)            │
├──────────────────────────────────────────┤
│ あなたの関心: 製造業 SAP / 業務監査       │
│                                          │
│ 📚 今日の 1 case (3 分)                  │
│   "大手化学メーカー 月次決算遅延 案件"    │
│   → 要点: ❶ 原因の切り分け ❷ AI監視導入  │
│   出典: clause #04, #07 (形式化済)        │
│                                          │
│ 🎯 今日のクイズ                          │
│   Q. SAP 月次決算が 3 日遅延する典型原因? │
│     a) マスタ重複  b) インフラ          │
│     c) 業務プロセス  d) 全部             │
│   [回答する]                             │
└──────────────────────────────────────────┘
```

#### Ingest — HITL clause table

```
┌─────────────────────────────────────────────────────────────┐
│ 案件: 大手化学メーカー SAP S/4 運用 (PJ-2024-0042)           │
│ Status: AI 判定済 / 承認待ち                                  │
├──────┬─────────────────────────┬───────────┬──────────────┤
│ #   │ Clause 抜粋              │ AI 判定   │ Action        │
├──────┼─────────────────────────┼───────────┼──────────────┤
│ 01  │ "本契約はXX社…"          │ ❌ 共有不可 │ [承認][修正] │
│ 04  │ "月次決算プロセスは…"    │ ✅ 共有可  │ [承認][修正] │
│ 07  │ "原因分析の手法…"        │ ✅ 共有可  │ [承認][修正] │
│ 11  │ "推奨アーキは AI 監視…"  │ ⚠️ 要redact│ [編集][承認] │
└──────┴─────────────────────────┴───────────┴──────────────┘
```

### 各画面の最小機能（MVP 範囲）

| 画面 | MVP 必達 | nice-to-have |
|------|---------|--------------|
| 検索 SPA | 自然文入力 + 結果カード + 引用 | 絞り込み filter / facet |
| 朝刊 Web UI | 当日カード表示 + クイズ + 解答記録 | 連続日数 streak / 履歴閲覧 |
| HITL レビュー | clause table + 個別承認/修正 | bulk 承認 / 差分比較 |

---

## 3. Agent topology + 実装部位

```
                ┌────────────────────────┐
                │   Orchestrator agent    │  ← Container Apps / FastAPI
                │   (Semantic Kernel)     │
                └────────────────────────┘
                  │           │           │
        Ingest path    Pull path     Push path
                  │           │           │
                  ▼           ▼           ▼
        ┌──────────────┐ ┌─────────┐ ┌──────────┐
        │ Ingest Agent │ │Pull     │ │Push      │
        │ + Contract   │ │Agent    │ │Agent     │
        │ Analyzer     │ │(検索    │ │(朝刊     │
        │ (HITL)       │ │ +生成)  │ │ 生成)    │
        └──────────────┘ └─────────┘ └──────────┘
              │              │             │
              ▼              ▼             ▼
        ┌────────────────────────────────────┐
        │ Shared AI Search index             │
        │  knowledge  (chunk + shareability) │
        │  profile    (user, domain_weights) │
        └────────────────────────────────────┘
```

### 実装部位（agent ごとに「どこに何を作るか」）

| Agent | 実装場所 | 主要処理 | 使う Azure / ライブラリ |
|------|---------|---------|-----------------------|
| **Orchestrator** | `app/orchestrator/` (FastAPI ルート群) | request 振り分け / 状態管理 | Semantic Kernel `Kernel`, Container Apps |
| **Ingest + Contract Analyzer** | `app/agents/ingest.py` | DI で OCR → clause 分割 → GPT-4.1 で「形式化 + 共有可否」判定 → HITL 経て index 登録 | Document Intelligence S0, AOAI GPT-4.1, Cosmos (HITL 状態) |
| **Pull (検索+生成)** | `app/agents/pull.py` | semantic search (shareable_only filter) → 上位 N chunk を context に GPT-4.1 で回答合成 → 引用 link | AI Search Basic, AOAI GPT-4.1 |
| **Push (朝刊生成)** | `app/agents/push.py` | profile から興味 domain 取得 → 直近 corpus 差分検索 → mini で要約 + クイズ生成 | AOAI GPT-4.1 mini, Logic Apps trigger |
| **HITL UI** | `web/hitl/` (React or 静的 + fetch) | clause table 表示 / 承認 fetch POST | Container Apps 上の SPA |
| **検索 SPA** | `web/search/` | 自然文入力 → `/api/pull` POST → 結果描画 | 同上 |
| **朝刊 Web UI** | `web/morning/` | `/api/push/today` GET → カード描画 / クイズ回答 POST | 同上 |

### 「agent である必要」の論証

- (a) **multi-step**: ingest = OCR → 分割 → 判定 → HITL → 登録 の 5 step
- (b) **function calling**: pull は `search_knowledge`, `cite_sources` 等を function として呼ぶ
- (c) **stateful**: HITL の承認状態 / 個人の learning profile を Cosmos に保持
- (d) **MCP 相当の tool 群**: Document Intelligence / AI Search / AOAI を統一 wrapper で

---

## 4. Azure サービス（具体 SKU）

| レイヤ | サービス | SKU | 月額（概算） | 採用根拠 |
|------|---------|-----|------------|--------|
| 文書解析 | Azure AI Document Intelligence | Standard S0 | 〜$15 | ingest 用 OCR + layout |
| LLM | Azure OpenAI | GPT-4.1 + mini | 〜$40 | pull / ingest = 4.1, push = mini |
| 検索 | Azure AI Search | Basic | 〜$75 | 1 service で 2 index |
| ホスト | Azure Container Apps | Consumption | 〜$15 | agent + 3 SPA |
| ストレージ | Blob | Hot LRS | 〜$5 | corpus 原本 |
| 状態 | Cosmos DB | Serverless | 〜$8 | HITL / profile |
| スケジューリング | Logic Apps | Consumption | 〜$3 | 毎朝 push trigger |
| 観測 | App Insights | Basic | 〜$5 | scaffold 済 |
| 認証 | Entra ID | included | $0 | scaffold 済 |

**6週合計見込み: 〜$166 / $200**（バッファ $34）。CD 統合より $7 安いのは push の learning_profile index を knowledge index に統合し index 数を 3→2 に削減できるため。

---

## 5. Tool / MCP インベントリ（コアのみ）

| Tool | 用途 | 利用 agent |
|------|------|-----------|
| `document_intelligence.analyze` | OCR + layout | Ingest |
| `aoai.classify_clause` | 句単位の形式化 + 共有可否 | Ingest |
| `ai_search.upsert` | corpus index 更新 | Ingest |
| `ai_search.query_with_share_filter` | shareable_only=true 必須 | Pull, Push |
| `aoai.synthesize_answer` | 検索結果 → 自然文回答 | Pull |
| `aoai.generate_brief` | 個人化朝刊生成 | Push |
| `cosmos.hitl_log` | 承認履歴 | Ingest, Push (反応) |
| `logicapps.daily_trigger` | 毎朝 06:30 | Push |

---

## 6. 擬似コーポレートシステム

| 実環境 | 擬似実装 | lift |
|------|---------|------|
| SharePoint | Blob + Web UI mock | 中 |
| 契約書 repo | Blob + 同 UI 内タブ | 小 |
| transcript / chat | Blob + Cosmos | 小 |
| 営業/PM 検索画面 | 検索 SPA | 中 |
| 朝刊配信 | Web UI タブ + Logic Apps | 小 |
| HITL レビュー UI | SPA | 中 |
| 認証 | Entra ID | 小 |

**統合 UI shell** で 3 画面（検索 / 朝刊 / HITL）を 1 つの React app として実装し lift を抑える。

---

## 5b. スコープ削減ラダー（**優先順位 TBD、5/11 議論項目**）

> 工数厳しい時に切れる候補。**どれから切るかは決めない** — 5/11 のチーム議論に投げる。

| Tier | 候補 | 切った場合の影響 |
|------|------|---------------|
| **A** | push 個人化ループ → 静的 profile | 朝刊は配信されるが個人化は demo 演出のみ |
| **B** | push 自体を週次 batch | 毎朝感を失う / pitch hook 弱体化 |
| **C** | HITL を句単位 → 文書単位に粗化 | 「暗黙知の形式化」の解像度低下、差別化弱体化 |
| **D** | ingest 自動化を半手動キュレーション | デモ前に corpus を手作業で投入 / agent 1 つ削減 |
| **E** | pull の引用提示を簡略化 | 「形式化された knowledge」の信頼感低下 |
| **F** | クイズを削除し朝刊は要約のみ | push の interactivity 消失 |

**5/11 決定すること**: Day 21 gate で「予実差」を見て切る順序を確定。事前に **「絶対切らない 2 つ」と「最後に残す 2 つ」** をチームで合意。

---

## 7. Corpus

| 種類 | 量 | 用途 |
|------|----|------|
| SPO doc（合成） | 50-80 件 | ingest 対象 / pull 検索 / push 素材 |
| 契約書（合成） | 15-20 件 | 共有可否判定の検証 |
| 会議 transcript（合成） | 20-30 件 | ingest 対象 / 暗黙知抽出 |
| Teams/Slack chat（合成） | 100+ messages | ingest 対象 |

### AI Search index（2 本に削減）

| index | 内容 | 主要 metadata |
|------|-----|------------|
| `knowledge` | doc/契約書/transcript/chat chunk | `domain`, `case_type`, `shareability`, `contract_id` |
| `profile` | user state | `user_id`, `domain_weights`, `last_seen` |

**shareability** が 1 つの metadata になり、pull/push 両出口で同じ filter 式が使える。

---

## 8. HITL surface

| ステップ | UI | 人間がやること |
|--------|-----|--------------|
| 契約書 clause 判定 | clause-by-clause table | 承認 / 修正 / 拒否 |
| 知見エントリ pre-publish | summary + tags | 承認 |
| 朝刊クイズ回答 | 4 択 + 自己評価 | 解答（profile 更新の signal） |

**MVP は ingest 側 HITL を主軸**。push 側の profile 反映は demo 演出（実線は引かない）。

---

## 9. Demo storyboard（3 分以内）

| 時刻 | シーン | 何を見せる |
|------|------|----------|
| 0:00-0:30 | PM 視点: 案件完了 | Ingest agent 起動 → clause 自動判定 |
| 0:30-1:00 | HITL レビュー | clause table で 1 件 修正 → 承認 → corpus 登録 |
| 1:00-1:30 | **場面転換 1**: 6 ヶ月後の別営業の検索 | 自然文 → 結果カード surfaces |
| 1:30-2:00 | **場面転換 2**: ジュニアの朝刊 Web UI | 同じ案件から朝刊 + クイズ |
| 2:00-2:30 | ジュニアが解答 → 解説に「clause #07 で形式化済」が出る | **形式化の本業性を明示** |
| 2:30-3:00 | admin 視点: lifecycle ビュー | 暗黙知 → 形式化 → 2 出口 を 1 枚で訴求 |

**判定基準**: 観客が「暗黙知の形式化が本業で、検索/朝刊は出口」と即理解できるか。

---

## 10. 6週ビルドリスク（R/Y/G）+ 工数試算

### リスク

| レイヤ | リスク | 理由 / 緩和 |
|------|------|-----------|
| **合成 corpus 量（4 種類）** | 🔴 R | Day 7 までに 50% 整備 / ドメインエキスパート リード |
| Ingest 句単位判定の精度 | 🟡 Y | 判定 prompt の試行錯誤、Day 14 まで反復 |
| Pull の回答品質 | 🟡 Y | 引用 link 必須 / Day 21 試走 |
| Push 個人化（simplified） | 🟢 G | 静的 profile 前提なら容易 |
| 統合 UI shell | 🟡 Y | 3 画面 1 app、Day 14 までに骨格 |
| 予算 ($166 / $200) | 🟢 G | バッファ $34、現実的 |
| Logic Apps daily trigger | 🟢 G | managed |
| 認証 / 観測 | 🟢 G | scaffold 済 |

### 工数試算（リサーチ基準: 5名 × 12h/週 × 6週 = 360h、純実装 200-220h）

| 部位 | 概算 h | 担当目安 |
|------|------|--------|
| 合成 corpus 整備 | 40-50h | ドメインエキスパート リード + 1 名 |
| Ingest + Contract Analyzer | 50-60h | 1 名 専任 |
| Pull agent + 検索 SPA | 40-50h | 1 名 |
| Push agent + 朝刊 UI | 25-35h | 1 名（simplified） |
| HITL UI + 統合 shell | 25-35h | UI 担当 |
| Demo / 動画収録 | 20-30h | 全員、最終週 |
| **合計** | **200-260h** | バッファ 微小 |

→ **Tier A 削減**（push 個人化ループ簡略化）を **既に織り込み** で 200-220h 圏。さらに切るなら Tier C/D。

---

## 11. Differentiation hook

> **「暗黙知の形式化を本業にした agent」**
>
> 他チームは「検索 bot」「Q&A bot」を出してくる可能性が高い。本案は **agent の本業を "暗黙知 → 形式知の変換"** に置く（kill switch 判定ではなく句単位判断 + HITL）。形式化済 corpus が pull/push の両出口に流れるのは結果。
>
> domain-specialty prevalence 前提（domain-specialty prevalence）に対し、**「ドメイン暗黙知を形式化する agent こそが差別化資産」** という構造的応答。

**主張可能な独自性**:
1. **形式化が本業**: 検索/生成は出口、形式化が agent 価値
2. **NDA-safe by design**: 句単位判定が両出口に cascade
3. **1 corpus × 2 出口**: lifecycle 訴求

---

## 12. Open question / テンプレ妥当性

### Open question

1. 6週 + $200 で 3 出口（ingest / pull / push）を回し切れるか → Day 7/14/21/28 gate
2. push 簡略化（静的 profile）で「個人化」を 30 秒で説得力ある形で見せられるか
3. 「暗黙知の形式化」を **30 秒で観客に届ける言語化** が必要（コピー検討）
4. CD 原案との pitch 強度比較 — 「lifecycle 訴求 vs 形式化訴求」どちらが審査員に刺さるか

### テンプレ review への所見（このカードから）

- ✅ **§2 I/O 独立章は機能した**: 実装視点が明示できる、他カードにも逆輸入可
- ✅ **§3 実装部位の表**: 「どのファイル/サービスで作るか」が one-shot で把握可、強く推奨
- 📌 **§5b スコープ削減ラダー**: 優先 TBD のまま記載でも価値あり、5/11 議論の足場になる
- 📌 **§9 工数試算 内訳**: 合計だけでなく h ベース内訳があると判断材料として強い
- ⚠️ A/C/D/CD カードへの retro-fit: 最小は §3 に「実装部位」列を追加すれば差分は埋まる
