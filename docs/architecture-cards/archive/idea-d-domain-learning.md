# 新案D — 毎朝のドメイン学習エージェント（Architecture Card）

> **目的**: 新案C / 新案A カードと同じ 12 セクション format で並置。本カードは新案D（member-a 提案・**横串前提 "domain-specialty prevalence" の最直接 instantiation**・drop 不可制約あり）。
>
> 関連: [problem-statement.md §2](../../problem-statement.md#候補のマトリクスkickoff-後4-候補で再構成) · [.html 版](./idea-d-domain-learning.html)

作成日: 2026-05-11 / ステータス: チーム review 用 draft

---

## 0. 30 秒サマリー

> agent が過去 **SharePoint / 会議 transcript / chat** を漁り、ドメイン × クライアント軸で **毎朝 push 配信**（問題出題 or 要約）。ユーザーの解答 / 反応をログし、苦手・関心領域を個人プロファイルに更新 → 翌朝の配信に反映する **個人化ループ**。
>
> **核**: 「法人 固有 corpus × 個人化学習プロファイル × 毎朝 push」の 3 点セット。push 型 + 個人化は他社（McKinsey Lilli 等の pull 型 RAG）との差別化軸。

---

## 1. As-Is → To-Be

### As-Is

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| ドメイン学習意識 | 「ドメイン理解を継続せよ」というメッセージは社内に存在 | 動機はあるが習慣化されない |
| 学習素材アクセス | 過去 SPO / transcript / chat は分散・死蔵 | 隙間時間に開く動機がない / 検索コスト高 |
| 学習継続 | 場当たり的 / 単発 | 蓄積されない / 個人 fit に欠ける |
| 結果 | コンサルのドメイン特化が個人差激しく organic 任せ | 提案精度 / クライアント信頼に直結 |

### To-Be

| 段階 | 何が起きるか | 解決される痛み |
|------|------------|--------------|
| ドメイン学習意識 | 毎朝 5-10 分の push で agent が "本日の教材" を届ける | habit loop 形成 |
| 学習素材アクセス | agent が curate 済の問題 / 要約を配信 | 検索コスト ゼロ |
| 学習継続 | 反応ログ → プロファイル更新 → 翌朝個人化 | 個人 fit + 蓄積効果 |
| 結果 | 組織全体のドメイン理解水準が底上げ + 個人差可視化 | 提案精度向上 / 自己 awareness 形成 |

### 埋まるギャップ（3 点）

1. **学習素材の発見コスト**: 死蔵 → 毎朝 push
2. **学習動機**: 「いつかやろう」→ 個人化 quiz（自分用）
3. **継続性**: 場当たり → habit loop（毎朝 5-10 分）

---

## 2. Azure サービス（具体 SKU）

| レイヤ | サービス | SKU | 月額（概算） | 採用根拠 |
|------|---------|-----|------------|--------|
| 文書解析 | Azure AI Document Intelligence | Standard S0 | 〜$10 | SPO doc / transcript の構造化 |
| LLM | Azure OpenAI | mini（出題・要約）+ 4.1（個人化判断） | 〜$30 | bulk 配信 → mini 主、profile 更新で 4.1 |
| 検索 | Azure AI Search | Basic | 〜$75 | docs / responses index |
| ホスト | Azure Container Apps | Consumption | 〜$10 | UI + agent backend |
| ストレージ | Blob Storage | Hot LRS | 〜$5 | corpus 原本 |
| 状態 | Cosmos DB | Serverless | 〜$5 | 学習プロファイル + 反応履歴 |
| **スケジューリング** | **Logic Apps** | Consumption | 〜$5 | 毎朝の push トリガー |
| 観測 | App Insights | Basic | 〜$5 | scaffold 済 |
| 認証 | Entra ID | included | $0 | scaffold 済 |

**6週合計見込み: 〜$145 / $200**（バッファ $55、C と同等）。

---

## 3. Agent topology

```
[ 朝の Push: Teams DM or Web UI "朝刊" タブ ]
            ▲
            │ (Logic Apps schedule)
            │
   ┌─────────────────────┐
   │  Orchestrator agent │
   └─────────────────────┘
       │            │
   push flow    feedback flow
       │            │
       ▼            ▼
┌──────────────┐  ┌──────────────┐
│ Generator    │  │ Feedback     │
│ agent        │  │ agent        │
│ (quiz +      │  │ (profile     │
│  summary)    │  │  update)     │
└──────────────┘  └──────────────┘
       │            │
       ▼            ▼
   AI Search   Cosmos profile
   (docs)      (interest/weakness)
       ▲            │
       │            │
       └────────────┘
       Profile が次回 Generator 入力に反映
            ▲
            │
   ┌──────────────┐
   │ Ingest agent │  (SPO / transcript / chat → AI Search)
   └──────────────┘
```

**MVP 構成**: Ingest（バッチ前処理）+ Generator + 簡素 Feedback の 3 agent。Profile は MVP では「明示変更のみ」（自動学習は Day 28 で）。

**「agent である必要」の論証**:
- (a) ingest → retrieval → generation の **multi-step**
- (b) Feedback ログから **state（プロファイル）を更新**
- (c) 翌朝の配信が **過去反応に依存** = stateful な振る舞い。LLM 1-shot では不可能。

---

## 4. Tool / MCP インベントリ

| Tool | 種別 | 用途 |
|------|-----|------|
| `mock_spo.list_docs` / `read_doc` | mock API | 擬似 SPO アクセス |
| `mock_transcript.list` / `get` | mock API | 擬似会議 transcript |
| `mock_chat.search` | mock API | 擬似 Teams / Slack chat |
| `document_intelligence.extract` | Azure AI wrapper | doc → 構造テキスト |
| `ai_search.query_docs` | AI Search | 個人化 retrieval |
| `ai_search.upsert` | AI Search | ingest 結果登録 |
| `llm.generate_quiz` | structured output | 4 択 + 解説 + 出典 |
| `llm.generate_summary` | structured output | "本日の要約" |
| `llm.update_profile` | structured output | 反応 → weakness/interest 更新 |
| `logic_apps.schedule_daily_push` | Azure SDK | 毎朝トリガー |
| `cosmos.log_response` | Cosmos SDK | 解答 / 反応ログ |

---

## 5. 擬似コーポレートシステム

| 実環境 | 擬似実装 | 構築コスト（lift） |
|------|---------|------------------|
| SharePoint（過去 doc） | Blob + Web UI（doc list / preview） | 小（3 日） |
| 会議 transcript | Blob + Web UI | 小（2 日） |
| Teams / Slack chat | Cosmos + Web UI thread view | 小（2 日） |
| 配信先 | **MVP: Web UI "朝刊" タブ** / Stretch: Teams webhook | 小（Web UI）/ 中（Teams Graph） |
| 認証 | Entra ID + roles | 小（managed） |

**lift 評価**: D は **mock 環境が最少**（外部 system 連携なし、KC Bridge / 契約書のような複雑物なし）。**6週で最も build-friendly**。

---

## 6. Corpus（D は corpus 設計が中心）

### 過去 SharePoint 文書

- **50-80 docs = 5-7 domain × 3-5 client × 案件タイプ 3-5**
- 業界知識 / 案件レポート / 内部 KB / トレーニング資料を mix
- 生成: AOAI structured output → human sanity check

### 会議 transcript

- **20-30 件 × 各 30-60 分換算**
- 会議 type: kickoff / status / brainstorm / wrap-up
- 生成: AOAI で対話形式生成

### Teams / Slack chat

- **100+ messages × 10-15 thread**
- 業界話題 / 質問応答 / 共有リンク

### 学習プロファイル schema

```json
{
  "user_id": "...",
  "domain_weights": {"retail": 0.8, "finance": 0.3, ...},
  "weakness_topics": ["retail KPI design", ...],
  "recent_responses": [...]
}
```

### AI Search index 設計

| index | 内容 | metadata | vector |
|------|-----|---------|-------|
| `docs` | doc / transcript / chat の chunk（800 token） | `domain`, `client_type`, `case_type`, `source_type` | chunk embedding |
| `responses` | ユーザー反応履歴 | `user_id`, `topic`, `correctness` | n/a |

---

## 7. HITL surface（user feedback loop）

| ステップ | UI | 人間がやること | feedback 保存先 |
|--------|-----|--------------|---------------|
| 出題への解答 | 4 択 + 自由記述 | 解答 + 自己評価（"yes I knew" / "kind of" / "no"） | Cosmos: profile 更新入力 |
| 要約への反応 | thumbs up/down + "more like this" | 関心 / 不関心の binary feedback | Cosmos |
| プロファイル editing | 興味分野リスト | 「retail よりも tech に関心」を明示変更 | Cosmos |

**A の「interface critical」要件への回答**: 単純 thumbs ではなく **自己評価 3 段階 + 明示プロファイル編集** が UX の核。これがあると「個人化が見える」demo になる。

---

## 8. Demo storyboard（3 分以内）

| 時刻 | シーン | 何を見せる |
|------|------|----------|
| 0:00-0:30 | ユーザーが朝、Web UI（or Teams DM）で「本日の朝刊」を開く | "本日のクイズ + 要約" を確認 |
| 0:30-1:30 | 配信内容 | (a) クイズ「retail 業界の典型 KPI は？」 4 択 + 出典 "過去 project XX の transcript より" / (b) 要約「先週 chat で議論された tech trend」 |
| 1:30-2:00 | 解答 | ユーザーが選択 → "正解 + 解説 + さらに詳しくは過去 doc YY" |
| 2:00-2:30 | **場面転換: 翌朝** | 配信が「あなたは tech に関心が高く retail KPI が弱い → tech 案件における retail KPI 設計事例」と個人化 |
| 2:30-3:00 | admin 視点（副次） | プロファイル全体ビュー、組織で誰がどの domain に強い / 弱いの heatmap |

**判定基準**: 「個人化が demo 内で見える」か（→ 翌朝の場面転換が肝）/ 「法人 固有 corpus が effective」と即理解できるか。

---

## 9. 6週ビルドリスク（R/Y/G）

| レイヤ | リスク | 理由 / 緩和 |
|------|------|-----------|
| Ingest pipeline | 🟢 G | managed |
| **合成 corpus（doc + transcript + chat）** | 🟡 Y | 量が要る（80 doc + 25 transcript + 100 chat）、内的整合性は A/C より緩い |
| 出題 LLM（4 択 + 解説 + 出典） | 🟡 Y | 品質と難易度調整 1 週間 |
| 要約 LLM | 🟢 G | bulk 処理、mini で十分 |
| 個人化ループ（profile update） | 🟡 Y | state 管理は MVP 簡素化（自動学習は Day 28） |
| Logic Apps スケジューリング | 🟢 G | managed |
| Web UI "朝刊" タブ | 🟢 G | Stretch: Teams webhook は Y |
| Feedback UI | 🟢 G | 単純 |
| Orchestrator | 🟢 G | flow 単純 |
| 認証 / 観測 | 🟢 G | scaffold 済 |

**ボトルネック**: 合成 corpus 量（Y）と出題品質（Y）。**Day 10 までに minimum viable corpus**（30 doc + 10 transcript + 50 chat）。

**特徴**: **D は全体的に最も build-friendly**（R 項目なし、Y 項目も C / A より少ない）。

---

## 10. Differentiation hook

> **「法人 固有 corpus × 個人化学習プロファイル × 毎朝 push」**
>
> 他社製品（McKinsey Lilli / 各社内 LLM RAG）は **pull 型 RAG**（聞かれたら答える）が中心。本案は **push 型 + 個人化ループ** で habit loop を形成する。domain-specialty prevalence 前提（domain-specialty prevalence）の最も直接的な instantiation。

**主張可能な独自性**:
1. **Push 型 + 個人化**: pull 型 RAG との構造差別化
2. **3 source 横断**（SPO + transcript + chat）: 単一文書 RAG との粒度差別化
3. **副次 admin heatmap**: 個人 → 組織への visibility 拡張

**他チームと被るリスク**: 学習エージェント自体は中レベルの被り → 上記 3 点 + 「**翌朝の場面転換で個人化が見える**」demo 構成で差別化。

---

## 11. このカードからの Open question

1. **Teams webhook 連携を MVP に含めるか or Web UI で代替** → Graph API 学習コストと pitch 価値の trade-off
2. **出題の難易度を「ユーザー毎」に変えるか、demo では固定で見せて差別化感を出すか** → 1 日 demo では time-evolution 見せにくい
3. **「学習効果」の demo 演出** → 翌朝の場面転換は事前録画でも OK か（リアルタイム不要）
4. **C との統合カードに合流させるか維持か** → 「単独 D」と「C+D 統合」を別カードで比較可能に
5. **個人プロファイルの自動学習を Day 28 で実装するか** → MVP は明示編集のみで十分か

---

## 12. テンプレ妥当性 review への問い

このカードを書いてみて分かった **テンプレ自体の課題**:

- ✅ **12 セクション機能**: D は「外部 system 連携なし」候補だが §5 が薄くなる以外問題なし
- ⚠️ **§5 が薄い候補への対応**: D のように mock 環境が少ない候補は §5 表が 4 行で済む → 「§5 lift 評価」+「§5 N/A 項目の明示」で見やすくすべき
- ⚠️ **§8 "time-evolution" の難しさ**: D は「翌朝の場面転換」が demo の核 → storyboard format は時刻軸で OK だが、`場面転換` の演出を強調する欄が欲しい
- 📌 **§3 topology で "stateful behavior" を独立項目化**: D の profile update / C の HITL feedback ループは agent 性論証の柱 → 各カード共通で抽出すべき

**review 後の next action**:
- C / A / D で format 共通化検証完了 → C+D 統合カード作成（最後）
- 修正あれば 3 カードに反映 → 再 review → 統合カード
