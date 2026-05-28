# 新案C — プロジェクト知見アーカイブ・横展開エージェント（Architecture Card）

> **目的**: このカードは「概念だけで議論を続けると solid criteria が立たない」という問題への対処として、各候補を **同じ 12 セクション** で並置し、5/11 のテーマ確定を table-read 化する artifact。本カードは新案C（kickoff 提示の 4 候補のうち、保険 → C+D 統合主軸候補に格上げ検討中）の見本。
>
> **このカードを見れば分かること**: ① 何を実装するか / ② アプリがどう見えるか / ③ As-Is と To-Be のギャップがどう埋まるか / ④ 6週・$200 で本当に作れるか
>
> 関連: [problem-statement.md §2 候補マトリクス](../../problem-statement.md#候補のマトリクスkickoff-後4-候補で再構成) · [§4 統合シナリオ](../../problem-statement.md#統合シナリオの選択肢511-で決定)

作成日: 2026-05-11 / ステータス: **テンプレ妥当性検証用サンプル**（チーム review 後に A / D / C+D を同フォーマットで clone）

---

## 0. 30 秒サマリー

> プロジェクト完了時に PM が **契約書を agent に読ませて「共有可否を clause 単位で判断」** させ、共有可な範囲だけを構造化アーカイブ。新規案件提案時は、提案担当が案件概要を入力 → past project から **共有可な部分だけ** が根拠付きで surfaces。
>
> **核**: 契約書 AI 判断レイヤ — 多くのナレッジ MS は守秘を無視するか手動 redact だが、本案は **agent が clause-by-clause で判断 + PM が HITL で承認** する。これがハッカソン submission の独自性。

---

## 1. As-Is → To-Be（現状と理想のギャップ）

### As-Is（現状）

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| プロジェクト完了 | PM が SharePoint に成果物を放り込んで終了 → SPO が graveyard 化 | 構造化されないため後で誰も見つけられない |
| 新規提案ニーズ発生 | manager / 提案担当が Teams で ex-PM を ping「過去に似た案件あった？」 | ad-hoc・属人的・タイミング次第で空振り |
| 共有可否判断 | 「契約上どこまで共有できるか」を PM が個別判断 → 不確実なら **kill switch（共有しない）** | 共有可能な知見も死蔵 / 提案精度が向上しない |
| 結果 | プロジェクト知見の reuse 率は低位安定 / 同様案件で毎回ゼロから | 提案 win-rate / 提案 lead-time が改善せず |

### To-Be（理想）

| 段階 | 何が起きるか | 解決される痛み |
|------|------------|--------------|
| プロジェクト完了 | PM が agent を起動 → **30 分で contract-aware curation** → 構造化された知見エントリが KB に登録 | graveyard 化を防ぐ / curation の負荷を下げる |
| 共有可否判断 | agent が **契約書を clause 単位で読み**「共有可 / 要 redact / 共有不可」を理由付きで提示 → PM が HITL で承認・修正 | 一回限りの判断で済む（毎回再判断 → 一括判断） / 判断コストの圧縮 |
| 新規提案ニーズ発生 | 提案担当が案件概要入力 → 5 秒で **共有可な範囲だけ** の past project が relevance スコア + 出典 clause 付きで surfaces | 属人探索 → semantic search / 守秘リスク bounded |
| 結果 | reuse がデフォルト化 / 守秘リスクは契約書ベースで explicit に bounded | win-rate / lead-time に直接効く |

### 埋まるギャップ（3点）

1. **discovery cost**: 手動 ping → semantic search
2. **confidentiality decision cost**: per-提案 ad-hoc 判断 → 完了時 1 回の clause-by-clause 判断
3. **institutional knowledge decay**: SPO folder graveyard → searchable + tagged corpus

---

## 2. Azure サービス（具体 SKU）

| レイヤ | サービス | SKU | 月額（概算） | 採用根拠 |
|------|---------|-----|------------|--------|
| 文書解析 | Azure AI Document Intelligence | Standard S0 | 〜$15（1500 page 換算） | 契約書 clause 抽出 + project doc 取り込み |
| LLM | Azure OpenAI | GPT-4.1（判断系）+ GPT-4.1-mini（分類・要約） | 〜$40（prompt cache 効かせる前提） | clause judgment は 4.1、bulk 要約は mini |
| 検索 | Azure AI Search | Basic | 〜$75 | **予算最大の variable**。共有可否 metadata + chunk-level vector を 1 index |
| ホスト | Azure Container Apps | Consumption（scale-to-zero） | 〜$10（demo 専用） | Web UI + agent backend |
| ストレージ | Blob Storage | Hot LRS | 〜$5 | 契約書 PDF + project artifact |
| 状態 | Cosmos DB | Serverless | 〜$5 | 共有可否判断ログ + agent state |
| 観測 | Application Insights / Log Analytics | Basic | 〜$5 | M4 deploy で bootstrap 済 |
| 認証 | Entra ID + Managed Identity | included | $0 | scaffold/infra で構築済 |

**6週合計見込み: 〜$165 / $200**（バッファ $35）。AI Search Basic が予算最大の単一 risk。Free tier (50MB / 3 index) は demo 規模では不足。

---

## 3. Agent topology

```
[ Web UI (Container Apps) ]
            │
            ▼
   ┌─────────────────────┐
   │  Orchestrator agent │  (router: archival flow / retrieval flow)
   └─────────────────────┘
       │              │
  archival flow   retrieval flow
       │              │
       ▼              ▼
┌──────────────┐  ┌──────────────┐
│ Contract     │  │ Retrieval    │
│ Analyzer     │  │ agent        │
│ (DocIntel +  │  │ (vector +    │
│  LLM 判断)   │  │  metadata    │
└──────────────┘  │  filter)     │
       │          └──────────────┘
       ▼
┌──────────────┐
│ HITL UI      │  ← PM が clause 単位で承認・修正・拒否
│ (clause-by-  │
│  clause)     │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Knowledge    │
│ Curator      │  (summary + tag + AI Search index 化)
└──────────────┘
```

**MVP 構成**: Orchestrator + Contract Analyzer + Retrieval の 3 agent。Curator は MVP では Contract Analyzer と統合（Day 28 以降に分離）。

**「agent である必要」の論証**: (a) Contract Analyzer は DocIntel → clause 抽出 → LLM 分類 → citation 付き返却 の **multi-step**、(b) Orchestrator は archival / retrieval を意図解釈で振り分け、(c) HITL feedback を Retrieval スコアリングに反映する **state を持つ** 動作。LLM 1-shot では不可能。

---

## 4. Tool / MCP インベントリ

| Tool | 種別 | 用途 |
|------|-----|------|
| `document_intelligence.analyze_contract` | Azure AI wrapper | 契約書 PDF → clause 配列 |
| `document_intelligence.extract_artifact` | Azure AI wrapper | PPT / Word → 構造テキスト |
| `ai_search.query_knowledge` | AI Search query | metadata filter + vector search |
| `ai_search.upsert_entry` | AI Search index | curation 結果の登録 |
| `mock_sharepoint.list_project_files` | カスタム（FastAPI） | 擬似 SPO の project folder 列挙 |
| `mock_sharepoint.read_file` | カスタム | 擬似 SPO のファイル content 取得 |
| `llm.classify_clause_shareability` | structured output | clause → {shareable / redact / exclude} + 理由 |
| `llm.draft_redaction` | structured output | redact 対象の sanitized 版生成 |
| `cosmos.log_decision` | Cosmos SDK | HITL 判断ログ |

**MCP 化方針**: Phase 1 は Agent Service の function calling で直接実装（MCP server 化は overhead）。Day 28 で CRM trigger 連携を入れるなら MCP 化検討。

---

## 5. 擬似コーポレートシステム

| 実環境 | 擬似実装 | 構築コスト |
|------|---------|----------|
| SharePoint プロジェクト folder | **Blob Storage + Web UI（SPO 風 mock）** — folder/file ツリーを Container Apps 上のフロントで表示 | 中（React tree view 5 日） |
| 契約書 repo | Blob Storage（mock SPO の `/contracts/` 配下） | 小（フロント込で 1 日） |
| CRM 新案件 trigger | **シンプル Web フォーム** — 「新規提案: 業界 / 内容 / 想定規模」入力 → retrieval flow 起動 | 小（半日） |
| 認証 / 権限 | Entra ID + roles（PM / 提案担当 / viewer） | 小（managed） |

**alternative**: SharePoint dev tenant を立てる選択肢もある（operator action item に記載）。立てられれば「実 SPO 連携」として pitch 価値↑。立たなければ Blob + mock UI で代替。**MVP は mock UI で確定**、SPO dev tenant が間に合えば Day 28 で swap。

**合成データの NDA 安全性**: 全データは AOAI 生成。実 KPMG 案件の固有名詞・数値は一切含めない。「業界 + 案件タイプ + 一般的契約パターン」の組み合わせで 15-20 種類生成。Submission 公開時に reviewable な corpus サンプルとして同梱。

---

## 6. Corpus（データソース・合成量・index）

### 合成契約書（最大の build risk）

- **15-20 件 = 3-5 アーキタイプ × 各 3-5 バリエーション**
- アーキタイプ例: 厳格 NDA / 標準コンサル契約 / 限定共有許諾 / publish-friendly / カスタム免責
- 各 5-15 ページ、clause 30-60 個
- 生成: AOAI で「実在の英文 NDA テンプレ + 想定パラメータ」→ 出力 → 弁護士的観点での sanity check（チームメンバー 1 名）
- 生成プロンプトはリポジトリに含める（再現性）

### 合成プロジェクト知見

- **30-50 案件 × 各 ~2 ページサマリ + 1-2 artifact（PPT or Word）**
- 業界 5-7 種 / 案件タイプ 4-5 種で組み合わせ
- 各案件に紐づく契約書（上記 15-20 のいずれか）を assign
- 生成: AOAI structured output → human sanity check

### AI Search index 設計

| index | 内容 | metadata | vector |
|------|-----|---------|-------|
| `contracts` | clause 単位 chunk | `contract_id`, `clause_id`, `shareability`（HITL 後）, `redaction_template` | clause text embedding |
| `knowledge` | プロジェクト知見の chunk（800 token） | `project_id`, `industry`, `case_type`, `contract_id`, `shareable_only`（boolean） | chunk embedding |

**filter logic**: retrieval flow は `shareable_only=true` の chunk のみ返却 → 守秘リスクが index レイヤで bounded。

---

## 7. HITL surface（人間が判断する場所）

| ステップ | UI | 人間がやること | feedback 保存先 |
|--------|-----|--------------|---------------|
| 契約書 clause 判断 | clause-by-clause table（30-60 行） | 各 clause の agent 判断（shareable / redact / exclude）を 承認・修正・拒否 + 理由を 1 行 | Cosmos: 次案件の判断 prompt に few-shot として入る |
| 知見エントリ pre-publish | agent 生成 summary + tags の preview | tag 修正 / summary 微修正 / publish 承認 | Cosmos |
| Retrieval 結果 relevance | 結果カード横の thumbs up/down | 提案担当が relevance フィードバック | retrieval ranking re-weight |

**A の「interface critical」要件への回答**: 単純承認/却下ではなく、**clause 単位の修正提案**（agent: shareable / 人: redact w/ template X）が UX の核。これがないと HITL が機能しない。

---

## 8. Demo storyboard（3 分以内）

| 時刻 | シーン | 何を見せる |
|------|------|----------|
| 0:00-0:30 | PM 視点：プロジェクト完了 | mock SPO で完了 project folder を選択 → 「Archive with Agent」ボタン |
| 0:30-1:30 | Contract Analyzer 動作 | agent が契約書を読み込み、clause-by-clause table を表示。各行: clause 抜粋 / 判断 / 理由 / 推奨 redaction template。PM が 8/10 を承認、2 件を修正 |
| 1:30-2:00 | Knowledge Curator 動作 | agent が共有可な範囲のみで summary + tags 生成 → PM 承認 → AI Search に index |
| 2:00-2:30 | 場面転換：6 ヶ月後の別 PM | 新規提案フォーム入力「業界: retail / 内容: AI 戦略策定」→ 検索 |
| 2:30-3:00 | Retrieval 結果 | 過去 3 案件が relevance スコア + **共有可 clause への citation** 付きで表示。1 件をクリック → 「契約書のこの clause で共有可と判断済」と表示 |

**判定基準**: 観客が「KPMG じゃなくても自社で動かしたい」と思えるか / 「contract-aware が独自」と即理解できるか。

---

## 9. 6週ビルドリスク（R/Y/G）

| レイヤ | リスク | 理由 / 緩和 |
|------|------|-----------|
| Document Intelligence pipeline | 🟢 G | managed・実績多数 |
| Contract shareability LLM 判断 | 🟡 Y | prompt 設計 + 合成契約書で iteration 必要、3-5 日確保 |
| **合成契約書 corpus（15-20 件）** | 🔴 R | **最大変数**。"realistic enough" な phrasing 設計に 1 週間。daichi がリードする想定 |
| 合成プロジェクト知見 corpus | 🟡 Y | 量 × tag consistency。AOAI structured output で量産可だが sanity check に時間 |
| AI Search 設計 + indexing | 🟢 G | well-trodden、Bicep に追加するだけ |
| HITL UI（clause-by-clause table） | 🟡 Y | カスタム React + 修正 UX が demo の見せ場 → 削れない、3-5 日 |
| mock SharePoint UI | 🟡 Y | ツリービュー + ファイルプレビュー、3 日 |
| Orchestrator + Retrieval agent | 🟢 G | Agent Service function calling で素直に書ける |
| 認証・観測性 | 🟢 G | scaffold 済 |

**ボトルネック**: 合成契約書 corpus (R) → MVP 最初の 1 週間で確定させないと後段が全停止。**Day 7 までに 5 件の最小 corpus + sanity check** を mandatory milestone に置く。

---

## 10. Differentiation hook（差別化の支柱）

> **「Contract-aware knowledge sharing」**
>
> 多くの enterprise knowledge agent（Glean / Microsoft Copilot / Notion AI 等）は守秘判断を **人間に丸投げ** するか、**organization-level の access control** で粗く処理する。本案は **個別契約 clause × 個別 chunk** の granularity で agent が判断 + HITL 承認するため、共有可否が **契約書由来で explicit traceable**。

**主張可能な独自性**:
1. clause-level の judgment + citation back（"contract X の clause Y より shareable" と画面に出る）
2. HITL が単純承認ではなく **clause 単位の修正提案** UX
3. retrieval 時に shareable_only filter が **index レイヤで** 効く（漏洩リスクが query 時に消える）

**他チームと被るリスク**: 「ナレッジ RAG」自体は確実に被る → 上記 3 点を pitch で 30 秒以内に伝える台本が要る（外向け 1-liner で一発）。

---

## 11. このカードからの Open question

1. **6週で合成契約書 15-20 件を realistic に作れるか** → daichi の sample data 検討と紐づき。Day 7 までに 5 件試作を mandatory に
2. **AI Search Basic ($75/mo) を Day 1 から走らせるか、Day 14 開始で半額に抑えるか** → MVP 開発初期は in-memory FAISS で代替する選択肢あり
3. **clause-level の判断精度は何 % で許容か** → 契約 review の世界では 95%+ 期待されるが、demo では 80% + HITL でカバーで成立。pitch でどう語るか
4. **新案D との統合をこのカードに含めるか、別カードに切るか** → 含めるなら corpus 共有設計（mock SPO + transcript / chat）を §6 に追加し、push 配信機構を §3 topology に追加。**推奨: C+D 統合カードを別途作成し、本カードは C 単独として維持**（変数を分離）

---

## 12. テンプレ妥当性 review への問い（チーム討議用）

このカードを書いてみて分かった **テンプレ自体の課題**:

- ✅ **12 セクションは過不足なし**: 各セクションが具体的判断を引き出した（特に §5 擬似システム / §9 R/Y/G が効いた）
- ⚠️ **§1 As-Is → To-Be が長め**: 1 ページに収めるなら表 2 つに圧縮版テンプレを用意すべき
- ⚠️ **§9 リスクと §11 Open question が重複しがち**: §11 は「カード書く前は気付かなかった問い」のみに限定するルール追加
- 📌 **追加検討**: 各候補の "agent である必要" を §3 内に独立項目化（LLM 1-shot で済む案を機械的に弾けるよう）

**review 後の next action**:
- このカード形式で OK なら → **A / D / C+D を 30 分ずつで clone**（5/11 中に揃える）
- 形式に修正があれば → 本カードに反映して再 review → そのあと clone
