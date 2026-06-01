# idea-f — 対話差分監視による暗黙知形式化エージェント（Architecture Card v1）

> **目的**: 採択された方向性を 12 セクション format で確定する正本カード。
> 中核アプローチ:
> - 暗黙知ソース: **AI×人間の対話ライブ監視**
> - HITL: **5W1H 差分ヒアリング**
> - 出口: **形式化ループ自体に集中、出口は後段**

作成日: 2026-05-12 / ステータス: チーム承認待ち

---

## 0. 30 秒サマリー

**問題**: 業界 × 領域特化の暗黙知（人間関係 / 顧客固有の意思決定癖 / 過去案件の red-flag パターン等）は個人の頭に閉じ込められ組織知化されない。汎用 LLM では埋められず、「業務価値は domain-specific な暗黙知に宿る」前提に立てば、これが組織 knowledge の最大のロス。

**提案**: 特定セクター × ユニットの業務対話を agent が監視し、**事前定義「欲しいデータ項目」スキーマと、AI 出力 / 人間入力の差分**を暗黙知として検知 → **5W1H ヒアリングループ**で形式知化 → 重み付き corpus に蓄積 → 次回対話で参照。

**核となるアプローチ**: 「文書から暗黙知を抽出する」のではなく「**対話の最中に暗黙知が発生した瞬間を捕まえる**」。事前定義スキーマで対話の暴走を防ぎ、重み付き形式化で人間入力の盲信を避ける。

**期待されるインパクト**:
- 暗黙知が文書化を待たず**発生時点で形式化**される
- 次回以降の同種対話で **AI 応答に蓄積知識が反映**、属人化リセット
- セクター × ユニット単位で**組織知の階層 corpus** が育ち、多マス展開時に水平移植可能

---

## 1. As-Is → To-Be

### As-Is

> ⚠️ **本テーブルは現時点で暫定記述**。「PM / 営業が業務対話の中で日常的に AI に判断を聞く」という前提が、デプロイ対象組織の実態（M365 Copilot 導入状況 / PM-AI 対話の日常性 等）と整合するか未確認。
>
> **視点の明示**: 本 As-Is は **対象組織の As-Is** を記述する（ハッカソン参加チーム視点ではない）。
>
> 実態確認後に本テーブルを書き換え、admin 視点の行追加、Copilot との overlap を踏まえた pain 再記述、§11 Differentiation hook 反映を併せて実施する。

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| 業務対話 | PM / 営業が **既存社内システム（M365 Copilot / 社内ナレッジ検索 / 営業支援 AI 等）** に判断を聞く → 汎用知識 + 公開ドキュメント範囲で回答 | クライアント固有暗黙知が反映されない |
| 判断分岐 | システム回答と人間判断が食い違う → 人間がオーバーライドして終わり | 「なぜ違ったか」が記録されず属人化 |
| 次回対話 | 同じパターンでシステムが同じ汎用回答 | 暗黙知が組織知化されない |

**共通の根**: 既存システム×人間の判断差分そのものが暗黙知の在りかなのに、捕まえていない。

### To-Be

| 段階 | 何が起きるか（PM 視点） | 解決される痛み |
|------|---------------------|--------------|
| 業務対話 | PM が **既存システム（Copilot 等）に重ねた本 agent layer** に聞く → 既存システムの汎用回答 + **過去 corpus 内の同種暗黙知 record の引用**を返す | クライアント固有暗黙知が反映され始める（corpus 蓄積が進むほど強化）|
| 判断分岐 | PM の判断が応答と食い違うと、その場で **5W1H ヒアリング modal が起動 → 形式化 → corpus に追加** | 「なぜ違ったか」が形式知化、属人化リセット |
| 次回対話 | 同じ PM / 別 PM が類似質問 → **既存システム + 更新済 corpus** を引用 | 暗黙知が組織知化される（一人の経験が組織の応答に反映）|

> **既存システムとの関係**: 本 agent は既存システム（Copilot 等）の代替ではなく、**「差分捕捉 + 暗黙知 corpus」レイヤを上に重ねる**位置付け。既存システムは汎用知識を、本 agent は組織特化暗黙知を担当する役割分担。

### ギャップを埋める主たるメカニズム

ギャップを埋めているのは **「差分発生時点で捕捉 → 重み付き形式化 → 次回 retrieval」のループ全体**。3 要素の役割:

1. **corpus 蓄積 + 次回 retrieval（主因）**: クライアント固有暗黙知が AI 応答に反映されるのは、過去 record の引用による。これが「汎用回答しか出てこない」痛みへの直接の解。
2. **発生時点で捕捉（タイミング）**: 文書化を待たず、対話の判断分岐フェーズで形式化が走る。「あとでまとめる」を不要にする。
3. **事前定義スキーマ（ガードレール）**: 「どこを見るか」を絞り、ヒアリング起動の暴走を防ぐ。**gap 解決の主因ではなく precision を守る制約**。
4. **重み付き正誤判定（信頼担保）**: 人間入力を 100% 信頼しない（自己批評スコア + 多数決 + フラグ）。corpus の質を時間的に維持する。

---

## 1.5. Persona & User Story

> **スコープ**: 要件詳細（Acceptance Criteria / KPI）は requirements 段階の責務。本節は **「誰が / 何を / なぜ」** の 3 要素 + 1 本のシナリオまで。

### Personas

### スコープ業界・ドメイン

> 本 POC のスコープは **M&A Advisory × Due Diligence（DD）業務、TMT（テクノロジー / メディア / 通信）セクター**。consulting / FA（ファイナンシャル・アドバイザリー）チームを対象組織と想定し、target 企業評価における「業界 × deal 構造 × 経営者」固有の暗黙知を扱う。

| 役割 | ペルソナ | プロファイル | 関わり |
|------|--------|------------|--------|
| **Primary（demo 主役）** | **M&A PM 田中** | TMT セクター担当の M&A advisory PM、deal lead 経験 5 年。DD で target 企業の財務 / 法務 / 事業リスクを評価。M365 Copilot を日常利用。過去案件の **経営者の癖 / 業界特有の post-merger 統合 red-flag / 同業 deal 構造リスク** を頭で抱えており、共有手段がない | 業務対話で本 agent layer に問い、差分発生時に 5W1H ヒアリングに応答、形式化レビューを承認 |
| **Secondary（運用主役）** | **admin 役** | TMT セクターのナレッジマネジメント担当 / シニアマネージャー相当。DD 観点スキーマ定義 + corpus 監督 + 重み調整方針を持つ | DD 観点スキーマ事前定義（経営者リスク / 業界 deal 構造リスク / post-merger 統合リスク 等）、矛盾検知フラグの裁定、Phase 2 以降のアノテータ信頼度運用 |

### User Story（JTBD 形式）

> **When** M&A PM が DD 業務の中で target 企業評価を既存システム（Copilot 等）に問おうとする時、
> **I want** AI が組織固有の暗黙知（過去案件の経営者の癖 / 業界特有の red-flag / 同業 deal の落とし穴）を踏まえて回答してほしい、
> **so I can** ベテラン PM 個人の頭にあった DD 判断ロジックを組織で再利用でき、判断時間短縮 + 後続 PM の deal 立ち上がり加速 + 案件横断で見落としていたリスクの組織的捕捉ができる。

### Scenario 1 本（業務対話 → 形式化 → 次回参照の 3-act）

> 詳細な分秒は §9 Demo storyboard 参照。本シナリオはペルソナ × ユーザーストーリーの **動作確認** が主目的。

**Act 1 — 業務対話**: 田中が TMT セクターの SaaS スタートアップ買収案件 X の DD で「target X、財務 KPI 健全、シナジー試算 positive。買収 GO で問題ない？」と既存システムに聞く。Copilot は「財務指標は業界平均上位、シナジー仮説も妥当」と汎用回答。agent layer が裏で過去 corpus を query → 類似 record があれば inline で引用、なければ素のまま通す。

**Act 2 — 差分発生 → 形式化**: 田中が「いや、創業者が前職の被買収時に主要 eng を引き連れて辞めた前例ある。post-merger で同じパターン踏むリスク高い」と入力。agent が schema「経営者リスク（post-merger 行動パターン）」field との一致を検知 → 5W1H modal 起動。田中が回答 → 形式化候補 record 生成 → HITL レビューで自己批評スコア (0-10) と共に提示 → 田中が承認 → corpus 登録。

**Act 3 — 次回対話で参照**: 翌月、別 PM（鈴木）が別の TMT SaaS 買収案件 Y の DD で「target Y の創業者、財務は OK だけど…」と既存システムに問う。agent layer が corpus query → Act 2 で蓄積した record（経営者の post-merger 行動パターン）を引用 → 鈴木は最初から「同パターンが Y にも当てはまるか」を踏まえた DD 観点で深掘りできる。**ここでループが閉じる**。

---

## 2. 入出力インターフェース（I/O）

### モード一覧（MVP）

| モード | 起点 | 入力 | 出力 | 受け取り画面 |
|------|------|-----|------|------------|
| **スキーマ定義** | admin が事前設定 | 暗黙知データ項目（例: M&A DD なら「経営者リスク」「業界 deal 構造リスク」「post-merger 統合リスク」） | スキーマ JSON | admin UI |
| **Retrieval** | ユーザーが業務対話開始 | ユーザー質問 | 関連 corpus record 引用 | 既存システム応答に inline で挿入 |
| **対話監視** | ユーザーが業務対話開始 | ユーザー自然文 + 既存システム応答（+ 引用 record） | 差分検知ログ（裏）| 通常チャット UI |
| **差分ヒアリング** | 差分閾値超で agent 起動 | 5W1H 質問への自由回答 | 形式化候補 record | チャット UI 内で modal 展開 |
| **形式化承認 (HITL)** | ヒアリング完了後 | 候補 record + 自己批評スコア (0-10) 表示 | 承認/修正/拒否 → corpus 登録 | レビュー UI |

### スコープ削減後の出口（出口は後段に集中）

| 出口 | MVP 含めるか | 理由 |
|------|------------|------|
| **次回対話での参照** | ✅ 必達 | 形式化ループのクローズ条件 |
| **検索 SPA (pull)** | 🟡 nice-to-have | MVP の差別化は形式化ループ自体 |
| **朝刊 (push)** | ❌ 削除 | アウトプット過多で重い、デモ尺も食う |

### 画面イメージ（差分ヒアリング modal）

```
┌─ 業務対話 (Copilot + agent layer) ─────────────────────┐
│ User:    target X (SaaS) 買収、財務 OK、GO で問題ない？  │
│ Copilot: 財務指標は業界平均上位、シナジー仮説も妥当。     │
│ agent:   (過去 record 引用) TMT SaaS 買収では創業者の    │
│          前職被買収時の行動パターンを確認推奨            │
│ User:    いや、創業者が前職被買収時に主要 eng を引き連れ │
│          て辞めた前例ある。post-merger 同パターン懸念    │
│                                                       │
│ ⚠️ 差分検知: スキーマ「経営者リスク」と一致            │
│ ┌─ 5W1H ヒアリング ───────────────────────────────┐   │
│ │ Why:  なぜそう行動したと推測されるか?              │   │
│ │ When: 前職の被買収はいつ / どの deal か?           │   │
│ │ Who:  対象となった eng はどの role / 何人か?       │   │
│ │ How:  当時 acquirer はどう対応 / 結果どうなったか?  │   │
│ │ [回答する] [スキップ]                              │   │
│ └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 3. Agent topology + 実装部位

```
     ┌─────────────────────────────────────────────────┐
     │  Orchestrator (Foundry Workflow + MAF 1.0)      │  ← Container Apps / FastAPI
     └─────────────────────────────────────────────────┘
        │          │           │          │          │
   ┌────▼───┐ ┌────▼────┐ ┌────▼───┐ ┌────▼─────┐ ┌──▼──────┐
   │Schema  │ │ Delta   │ │Hearout │ │Retriever │ │  対話   │
   │Manager │ │Detector │ │ Agent  │ │(対話開始 │ │  UI     │
   │(admin) │ │ (live)  │ │(5W1H)  │ │ corpus Q)│ │(chat)   │
   └────────┘ └─────────┘ └────────┘ └──────────┘ └─────────┘
        │          │           │          ▲
        └──────────┼───────────┘          │
                   ▼                       │
       ┌──────────────────────────┐        │
       │  Formalization + HITL    │        │
       │  (重み付け + 正誤判定)    │        │
       └──────────────────────────┘        │
                   │                       │
                   ▼                       │
       ┌──────────────────────────┐        │
       │ Knowledge corpus index   │────────┘
       │ (AI Search + Cosmos)     │
       └──────────────────────────┘
```

### 実装部位

| Agent | 実装場所 | 主要処理 | 使う Azure / ライブラリ |
|------|---------|---------|-----------------------|
| **Orchestrator** | `app/orchestrator/` | request 振り分け / agent workflow / state | **Foundry Workflow agent (preview) + MAF 1.0**、Container Apps |
| **Schema Manager** | `app/agents/schema.py` | 「欲しいデータ項目」CRUD | Cosmos DB |
| **Delta Detector** | `app/agents/delta.py` | 入出力 stream を監視、スキーマ照合、差分スコア計算 | AOAI gpt-4o-mini（embedding 比較 + LLM 判定）|
| **Hearout Agent** | `app/agents/hearout.py` | 5W1H 質問生成 → 回答収集 → record 候補化 | AOAI gpt-4o |
| **Retriever** | `app/agents/retriever.py` | 対話開始時に corpus を query → 関連 record を AI 応答に augment | AI Search, AOAI gpt-4o-mini |
| **Formalization + HITL** | `app/agents/formalize.py` + `web/hitl/` | 重み付け / 正誤判定 / 承認 | AOAI gpt-4o-mini, Cosmos, AI Search upsert |
| **対話 UI** | `web/chat/` | チャット + 差分 modal | Container Apps SPA |

### 「agent である必要」の論証

- (a) **multi-step**: 検索 → 監視 → 検知 → ヒアリング → 形式化 → 承認の 6 step
- (b) **function calling**: `lookup_schema`, `score_delta`, `generate_5w1h`, `weight_record`, `corpus.query` 等を tool 化
- (c) **stateful**: ヒアリングセッション状態 + スキーマ + corpus
- (d) **MCP 相当**: AOAI / AI Search / Cosmos を統一 wrapper

---

## 4. Azure サービス（具体 SKU + AWS 比較）

| レイヤ | Azure サービス | SKU | 月額（概算） | AWS 等価 | Azure 採用根拠 |
|------|---------|-----|------------|---------|--------------|
| LLM | Azure OpenAI | GPT-4o + mini | ~$40 | Bedrock | gpt-4o-mini は provisioned 済、gpt-4o は採否判断中 |
| Agent orchestration | **Foundry Agent Service (本体無料) + MAF 1.0** | $0（token / tool 課金は AOAI に内包） | Bedrock Agents | Foundry Workflow agent (preview) + MAF 1.0 + BYO Cosmos のハイブリッド。Week 1 flag day で実機検証後に Foundry / Container Apps 直載せの最終判断 |
| 検索 | Azure AI Search | Basic | ~$75 | Bedrock Knowledge Bases | corpus index 1 本に縮減（profile index 削除）|
| 状態 | Cosmos DB | Serverless | ~$8 | DynamoDB | スキーマ / ヒアリングセッション / 重み |
| 文書解析 | （MVP では不要、後段で AI Document Intelligence） | — | $0 | Textract | 対話入力中心のため、初期は文書 OCR 不要 |
| 観測 | App Insights | Basic | ~$5 | CloudWatch | scaffold 済 |
| 認証 | Entra ID | included | $0 | Cognito | scaffold 済 |
| スケジューリング | 不要（push 出口削除のため） | — | $0 | — | — |

**6週合計見込み: 〜$128 / $200**（バッファ $72）。Foundry 本体無料 + Document Intelligence / Logic Apps / push 関連 index 不採用でコスト圧縮。

**Foundry / MAF 採用ポイント**:
- Foundry Agent Service Runtime / Prompt agents = **GA**、Workflow / Hosted agents / Multi-Agent Workflows = preview
- MAF 1.0 GA (2026-04-03) で SK + AutoGen 統合、**HITL は標準機能**（RequestInfoEvent / ToolApprovalRequestContent）
- BYO Cosmos for conversation state が公式パターン、既存リソース全部活用可
- AWS Bedrock との機能パリティはほぼ取れている、Memory tool のみ preview 制約あり（BYO Cosmos でカバー）

---

## 5. Tool / MCP インベントリ（コアのみ）

| Tool | 用途 | 利用 agent |
|------|------|-----------|
| `schema.get` / `schema.upsert` | スキーマ CRUD | Schema Manager |
| `dialogue.stream_intercept` | 対話 stream の入出力捕捉 | Delta Detector |
| `aoai.score_delta` | スキーマと入出力の embedding 距離 + LLM 判定 | Delta Detector |
| `aoai.generate_5w1h` | スキーマに沿った 5W1H 質問生成 | Hearout Agent |
| `aoai.formalize_record` | ヒアリング結果を構造化 record に | Formalization |
| `weight.compute` | 重み付け（信頼度スコア） | Formalization |
| `truth.verify_public` | 公開情報との論理整合（**要否は open**） | Formalization |
| `corpus.upsert` | AI Search に登録 | Formalization |
| `corpus.query` | 対話開始時の関連 record 検索（`{sector}#{unit}` パーティション内）| Retriever |
| `aoai.augment_with_records` | 検索された record を AI 応答プロンプトに注入 | Retriever |
| `cosmos.hitl_log` | 承認履歴 | HITL UI |

---

## 5b. スコープ削減ラダー（優先順位 TBD、チーム合意後に確定）

| Tier | 候補 | 切った場合の影響 |
|------|------|---------------|
| **A** | 公開情報照合 (`truth.verify_public`) を削除 | 正誤判定が「フラグ + 多数決」のみ、論理整合性低下 |
| **B** | 重み付けを binary（信頼 / 不信）に粗化 | 多数決の解像度低下 |
| **C** | 5W1H を 3W に絞る (Why / Who / How) | ヒアリング粒度低下、形式化品質低下 |
| **D** | HITL を句単位 → record 単位に粗化 | 形式化解像度低下 |
| **E** | 検索 SPA (nice-to-have) を実装しない | 「次回対話で参照」のみで demo 成立 |
| **F** | スキーマ事前定義 UI を JSON 手書きに | admin UX 低下、デモ尺は短縮 |

**「絶対切らない 2 つ」候補**: Delta Detector / Hearout Agent（コアループの 2 軸）

---

## 6. 擬似コーポレートシステム

| 実環境 | 擬似実装 | lift |
|------|---------|------|
| 業務チャット | チャット SPA | 中 |
| スキーマ管理画面 | admin UI（簡易表） | 小 |
| 過去案件知識（参照用） | AI Search index 50-80 record（合成） | 中 |
| 認証 | Entra ID | 小 |
| HITL レビュー | レビュー UI | 中 |

**統合 UI shell** で「チャット / admin / HITL」3 画面を 1 React app で実装。

---

## 7. Corpus

| 種類 | 量 | 用途 |
|------|----|------|
| スキーマ定義（合成） | 5-10 件 | 1 セクター×ユニット分 |
| 過去 record（合成、seed corpus） | 50-80 件 | 検知時の比較ベース + nice-to-have 検索結果 |
| 対話 sample（合成、デモ用） | 10-20 セッション | デモ動画の素材 |

### AI Search index（1 本に削減）

| index | 内容 | 主要 metadata |
|------|-----|------------|
| `tacit_records` | 形式化済暗黙知 record（chunk 単位） | `sector`, `unit`, `schema_field`, `weight`, `source_user`, `verified_flag` |

> **パーティション設計**: Cosmos DB 側の partition key は **`{sector}#{unit}`** を採用（POC 1-2 マス前提でも、多マス展開時に水平スケール可能）。AI Search 側は `sector`, `unit` を filterable facet として保持し、Retriever の `corpus.query` は同一 `{sector}#{unit}` スコープで検索する。

---

## 8. HITL surface

| ステップ | UI | 人間がやること |
|--------|-----|--------------|
| スキーマ定義 | admin 表 | 「欲しいデータ項目」を入力（または既存テンプレ選択） |
| 差分ヒアリング | チャット内 modal | 5W1H に自由回答 / スキップ |
| 形式化レビュー | レビュー UI（record + 重み slider） | 承認 / 修正 / 拒否 / 重み調整 |
| 多数決 / 矛盾検知 | レビュー UI 一覧 | 同一スキーマ field の矛盾 record にフラグ立て |

---

## 9. Demo storyboard（3 分以内）

| 時刻 | シーン | 何を見せる |
|------|------|----------|
| 0:00-0:20 | 場面: TMT M&A DD 業務 | admin が DD 観点スキーマ（経営者リスク / 業界 deal 構造 / post-merger 統合）を見せる |
| 0:20-1:00 | PM × 既存システム対話 | 田中が target X (SaaS) 買収判断を Copilot に問う → 財務 OK の汎用回答、PM が「創業者が前職で…」と暗黙知発露 |
| 1:00-1:40 | **差分検知 + 5W1H ヒアリング起動** | チャット内 modal で Why/When/Who/How を聞く（経営者リスク field） |
| 1:40-2:10 | HITL レビュー | record 候補 + 自己批評スコア表示、PM が承認 |
| 2:10-2:40 | **2 回目の対話（翌月、別 PM 鈴木）** | 別 TMT SaaS 買収 Y で類似質問 → agent が Act 2 record を引用 → 鈴木は最初から経営者リスク観点で DD 深掘り可能 |
| 2:40-3:00 | admin 視点 | corpus 蓄積ビュー（TMT × M&A DD record 数）/ 矛盾検知フラグ |

**判定基準**: 観客が「対話の差分が発生した瞬間を捕まえて、次回に活きる」と即理解できるか。

---

## 10. 6週ビルドリスク（R/Y/G）+ 工数試算

### リスク

| レイヤ | リスク | 理由 / 緩和 |
|------|------|-----------|
| **対話 stream 監視の実装** | 🟡 Y | Semantic Kernel での hook パターン要 PoC、Day 7 までに spike |
| Delta Detector の閾値調整 | 🔴 R | 偽陽性多すぎ / 少なすぎの両極、Day 14-21 で調整 |
| 5W1H 質問品質 | 🟡 Y | prompt 試行錯誤、スキーマに応じた質問生成 |
| 重み付け / 正誤判定 | 🟡 Y | 多数決と論理整合の組合せ、design 決定 |
| **Azure Foundry Agent Service の GA 状況** | 🟡 Y | Workflow agent は preview。Week 1 flag day で swedencentral 実機検証 → 不可なら MAF on Container Apps へ即フォールバック可能（コード変更不要、converged runtime）|
| 統合 UI shell | 🟡 Y | 3 画面 1 app |
| 予算 ($128 / $200) | 🟢 G | バッファ $72 |
| 認証 / 観測 | 🟢 G | scaffold 済 |

### 工数試算（AI-driven 前提 = wall-clock + human review 二軸）

> 本プロジェクトは Claude Code / Codex + Discord bot 経由 async 実行で実装する。
> 「純実装 h」は AI が回すため**時間制約ではない**。人間ボトルネックは **review + 構想 + async 決定 + 演出**のみ。
> 以下は AI-driven 換算（旧 195-250h 純実装 → wall-clock 5-6w + human review 30-50h）。

| 部位 | Wall-clock | Human review | 構想/演出 主体 |
|------|-----------|--------------|----------------|
| スキーマ + 合成 corpus 整備 | 3-4 day | 3-5h（ドメイン妥当性 + サンプル QC） | ドメインエキスパート |
| Delta Detector + 対話 hook | 1 week | 5-8h（閾値判断 + 偽陽性 review） | member-a |
| Hearout Agent + Formalization | 1 week | 5-8h（5W1H プロンプト品質 + 重み付け review） | member-a |
| HITL UI + 統合 shell | 3-4 day | 3-5h（UX flow review） | UI 担当 |
| Orchestrator + Container Apps | 2-3 day | 2-4h（IaC / deploy review） | maumau |
| Demo / 動画収録 | 1 week 最終 | 8-12h（ナラティブ + 演出 + 撮影） | 全員 |
| **合計** | **5-6 週 wall-clock** | **26-42h human review** | バッファ wall-clock 0-1w / review 8-14h |

**真のボトルネック**: ① Azure $200 予算、② wall-clock 6 週（Azure 提供期限）、③ 人間 review 帯域、④ async 決定速度、⑤ Foundry preview の region 提供（flag day）。

→ **Tier 削減判断**は wall-clock 残量 + Azure コストで行う（人時を理由に追加スコープを却下しない）。

---

## 11. Differentiation hook

> **「対話の差分発生瞬間を捕まえる agent」**
>
> 他チームは「文書から RAG」「議事録から要約」を出してくる可能性が高い。本案は **対話の最中にスキーマ × 差分で暗黙知を捕捉**し、**5W1H ヒアリングループ**で形式化する。「文書からの事後抽出」ではなく「対話の瞬間捕捉」が本業性を強める。

**主張可能な独自性**:
1. **発生時点捕捉**: 文書化を待たない
2. **事前定義スキーマで暴走防止**: ガードレール = 差別化要素
3. **5W1H ヒアリング**: 過去案件で実証された質問パターン
4. **重み付き正誤判定**: 人間入力を 100% 信頼しない設計

---

## 12. Open question（要件定義段階で決定）

1. **対象セクター×ユニット 1 マス選定** — 暫定: TMT × M&A DD（§1.5 参照）。確定はチーム合意要
2. **公開情報照合の MVP 含有可否** — Tier A 削減候補との関係
3. ~~**重み付け方式**~~ → ✅ **close**: MVP = A. LLM 自己批評スコア (0-10) のみ。Phase 2 で B. アノテータ信頼度、Phase 3 で C. Provenance 時間減衰。最終重み = A × B × C。閾値: 検知 score<5、形式化採用 合成≥0.7
4. ~~**Azure Foundry Agent Service 採用可否**~~ → ✅ **close**: Foundry Workflow agent (preview) + MAF 1.0 + BYO Cosmos のハイブリッド採用。Week 1 flag day で実機検証 → 不可なら Container Apps 直載せフォールバック
5. **スキーマ事前定義のテンプレ提供範囲** — 5-10 件のサンプル、ドメイン特化テンプレを何個用意するか
6. **スキーマ外入力 (out-of-schema) の取扱い** — 事前定義スキーマに該当しない暗黙知シグナル（人間が「揉めてた」と発言したが該当 schema_field なし、等）を ① 破棄 / ② 別 bucket に保留 / ③ 動的にスキーマ拡張提案 のいずれにするか。MVP は ① か ② に倒すのが現実的

---

## レビューチェックリスト（オフライン用）

> **スコープ絞り込み (2026-05-15)**: 本レビューパスは **spec の上流 input** を確定する目的に絞る。Requirements / Design phase に進む際の正本となる「§0 / §1 / §1.5 / §3 ラフ / 全体整合」のみを対象。§2 以降の詳細は **次のレビューパスに deferred**（末尾参照）。
>
> 各項目で「OK / NG（コメント）」を inline で書き込む用。マークダウン崩さず `<!-- review: ... -->` で囲っても良い。

### §0 サマリー
- [ ] 「業務価値は domain-specific な暗黙知に宿る」前提が外部 reviewer に通る言葉になっているか
- [ ] 「発生時点捕捉」のフックが 30 秒以内に伝わるか
- [ ] 4 段構造（問題 / 提案 / 核 / インパクト）の分量バランス

### §1 As-Is → To-Be
- [ ] As-Is の暫定 callout は今レビューでは保留扱いで OK か（対象組織実態確認後に書き換え前提）
- [ ] 「既存システム（Copilot 等）」例示の粒度（M365 Copilot だけで足りるか）
- [ ] To-Be 表「PM 視点 × ループ各段階」軸統一は機能しているか
- [ ] 「ギャップを埋める主たるメカニズム」4 要素の優先順位（主因=corpus / タイミング / ガードレール / 信頼担保）

### §1.5 Personas & User Story
- [ ] スコープ業界・ドメイン = TMT × M&A DD の選択が hackathon demo 強度 + 対象組織想定（FA / advisory）と整合しているか
- [ ] Primary persona = M&A PM 田中の解像度（deal lead 5 年目 / TMT セクター / Copilot 日常利用）は requirements の Stakeholders 導出に足りるか
- [ ] Secondary persona = admin 役の責任範囲（DD 観点スキーマ定義 / 矛盾裁定 / 重み運用）が MVP と Phase 2 で混ざっていないか
- [ ] User Story (JTBD) の **so I can** 節（判断時間短縮 + 後続 PM deal 立ち上がり加速 + 案件横断リスク捕捉）が組織レベルの価値主張として成立しているか
- [ ] Scenario 3-act の M&A DD context（SaaS 買収 / 創業者 post-merger 行動パターン）が §9 Demo storyboard と二重 source になっていないか

### §3 ラフ・アーキテクチャ（粒度: 大枠のみ）
- [ ] 5 agent (Schema / Delta / Hearout / Retriever / Formalization) で **暗黙知ループの閉じ**が成立するか過不足の判断
- [ ] Retriever を独立 agent にする vs Orchestrator 内ロジックに埋め込む — 独立にする方が user story の「Act 1 で AI が corpus 引用」フローが説明しやすい、で OK か
- [ ] 「agent である必要」4 軸 (multi-step / function calling / stateful / MCP 相当) が hackathon 審査向けに十分か

### 全体整合
- [ ] §0 problem → §1 To-Be → §1.5 user story → §3 architecture のナラティブが一本道で繋がっているか
- [ ] 差別化 (§11) の主張「既存システム = 汎用 / 本 agent = 組織特化暗黙知 layer」が persona + user story から自然に導出できるか

---

### Deferred — 次のレビューパス（要件定義着手後 or 別セッション）

> 以下は本レビューパスのスコープ外。spec input が確定してから順次。

- §2 I/O（Mode 5 つの粒度 / Retrieval 実装現実性 / 画面イメージ / 出口削減妥当性）
- §4 Azure サービス（$128/$200 内訳 / AWS 等価列 / Foundry/MAF 採用ポイント / 文書解析 MVP 不要判断）
- §5 / §5b（Tool 11 個粒度 / Tier 優先順 / 死守 2 候補）
- §6-§9（擬似実装 / Corpus / HITL / Demo storyboard）
- §10 リスク + 工数（R/Y/G キャリブレーション / 工数試算 / ボトルネック順）
- §11 Differentiation hook（他チーム想定 / Copilot overlap / 独自性 4 点配分）
- §12 Open question（残 4 件の期限主体 / #6 out-of-schema MVP 結論 / #2 公開情報照合方針）

---

> **オフライン review 完了後の合流**: コメントを inline で書き込んだまま push or screenshot で共有 → 編集再開時に上から順に潰す。
