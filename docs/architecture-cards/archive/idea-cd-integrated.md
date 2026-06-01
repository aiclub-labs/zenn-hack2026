# C+D 統合 — 知見アーカイブ × ドメイン学習 デュアル出力エージェント（Architecture Card）

> **目的**: 新案C / D / A カードと同じ 12 セクション format で並置。本カードは **kickoff 後の operator + チーム提案** = C を主軸とし D と統合する構成（problem-statement §4 選択肢 Z 相当）。
>
> 関連: [idea-c-knowledge-archive.md](./idea-c-knowledge-archive.md) · [idea-d-domain-learning.md](./idea-d-domain-learning.md) · [.html 版](./idea-cd-integrated.html)

作成日: 2026-05-11 / ステータス: チーム review 用 draft（5/11 決定で **本構成を採用するか単独 C に戻すかを決定**）

---

## 0. 30 秒サマリー

> **同一 corpus（SPO + 契約書 + transcript + chat）上で、2 つの出力モードを提供**:
> - **C path（pull）**: PM がプロジェクト完了時に契約書 AI 判断 + curation → 新規提案時に共有可な範囲だけが検索可能
> - **D path（push）**: コンサル個人に毎朝、同じ corpus から個人化学習配信
>
> **核**: 「1 corpus × 2 出力モード」の lifecycle 訴求 + Sotaro テーゼ（domain-specialty prevalence）の **組織化（C）+ 個人化（D）の同時実装**。

---

## 1. As-Is → To-Be

### As-Is

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| プロジェクト完了 | SPO graveyard / curation なし / 守秘判断は kill switch | reuse 率低い |
| 新規提案 | ad-hoc な ex-PM ping | 属人探索 |
| 個人のドメイン学習 | 過去素材があるのに死蔵 / 動機続かない | habit 化されない |
| **共通の根**: corpus は存在するが **lifecycle がない**（蓄積 → 多面活用 がデザインされていない） |  |  |

### To-Be

| 段階 | 何が起きるか | 解決される痛み |
|------|------------|--------------|
| プロジェクト完了 | PM が contract-aware curation → corpus 充実（C path） | reuse 基盤確立 |
| 新規提案時 | 共有可な範囲が pull 検索（C path） | 属人探索 解消 |
| 個人の朝の学習 | 同じ corpus から毎朝 push（D path） | habit loop 形成 |
| **共通の効用**: corpus が **lifecycle を持つ**（curated → multi-mode consumed） |  |  |

### 埋まるギャップ（3 点）

1. **corpus lifecycle**: 蓄積 → 多面活用（pull + push）
2. **contract-aware が D 側にも効く**: 個人配信も share-safe で安全
3. **組織化 + 個人化の同時実装**: Sotaro テーゼの構造的応答

---

## 2. Azure サービス（具体 SKU）

| レイヤ | サービス | SKU | 月額（概算） | 採用根拠 |
|------|---------|-----|------------|--------|
| 文書解析 | Azure AI Document Intelligence | Standard S0 | 〜$15 | 契約書 + SPO + transcript |
| LLM | Azure OpenAI | 4.1 + mini | 〜$45 | C 判断 + D 出題の両方 |
| 検索 | Azure AI Search | Basic | 〜$75 | **1 サービスで複数 index** |
| ホスト | Azure Container Apps | Consumption | 〜$15 | 両 UI（PM 用 + 朝刊用） |
| ストレージ | Blob | Hot LRS | 〜$5 | 全 corpus |
| 状態 | Cosmos DB | Serverless | 〜$8 | HITL + プロファイル |
| スケジューリング | Logic Apps | Consumption | 〜$5 | 毎朝 push |
| 観測 | App Insights | Basic | 〜$5 | scaffold 済 |
| 認証 | Entra ID | included | $0 | scaffold 済 |

**6週合計見込み: 〜$173 / $200**（バッファ $27、**タイト**）。AI Search 1 service 共有で予算節約効くが、開発工数が単独 1.5x。

---

## 3. Agent topology

```
                ┌─────────────────────┐
                │  Orchestrator agent │
                └─────────────────────┘
                  │                  │
            C path                D path
                  │                  │
   ┌──────────────┼──────────────┐   │
   ▼              ▼              ▼   ▼
┌─────────┐  ┌─────────┐   ┌──────────┐  ┌──────────┐
│Contract │  │Retrieval│   │Generator │  │Feedback  │
│Analyzer │  │agent    │   │(quiz +   │  │(profile  │
│+Curator │  │(pull)   │   │ summary) │  │ update)  │
└─────────┘  └─────────┘   └──────────┘  └──────────┘
   │              │              │              │
   ▼              │              │              │
[HITL clause]     │              │              │
   │              │              │              │
   ▼              ▼              ▼              ▼
        ┌────────────────────────────┐
        │   Shared AI Search index   │
        │  (contracts / knowledge /  │
        │   learning_profile)        │
        └────────────────────────────┘
                    ▲
                    │
        ┌──────────────────────┐
        │ Ingest agent         │
        │ (SPO + transcript +  │
        │  chat + contracts)   │
        └──────────────────────┘
```

**MVP 構成**: C path は完全実装、D path は **Generator のみ実装、Profile / Feedback は static demo**（個人化ループは "翌朝の場面転換" で演出のみ）。

**「agent である必要」の論証**:
- (a) C と D が **同一 retrieval 基盤を共有** = 統合の物理的接点が存在
- (b) `shareable_only` filter が D 側にも効く（contract-aware push）= **データ層の cross-cutting**
- (c) 双方が **multi-step + stateful**（C: HITL clause / D: profile）

---

## 4. Tool / MCP インベントリ

C カード §4 + D カード §4 の **和集合**（重複: `document_intelligence.*`, `ai_search.*`）。Tool 数は単独 9 → 統合 14 程度。

新規 / 共通化:
| Tool | 用途 |
|------|------|
| `ai_search.query_with_share_filter` | C 検索 + D 配信両方で `shareable_only=true` を必須適用 |
| `cosmos.cross_log` | C HITL 履歴 + D 反応履歴を統合 schema で記録 |

---

## 5. 擬似コーポレートシステム

| 実環境 | 擬似実装 | lift |
|------|---------|------|
| SharePoint（C+D 共通） | Blob + Web UI mock | 中 |
| 契約書 repo（C 専用） | Blob + Web UI | 小 |
| transcript + chat（D 専用） | Blob + Cosmos + Web UI | 小 |
| CRM 新案件 trigger（C 専用） | Web フォーム | 小 |
| 朝刊配信（D 専用） | Web UI タブ + Logic Apps | 小 |
| 認証 | Entra ID | 小 |

**lift 評価**: 単独 C の mock 環境 + D の mock 環境を **同じ UI shell に統合** することで C 単独 lift × 1.3x 程度で済む（× 2x 回避）。

---

## 6. Corpus

### 共通 corpus（最大の build risk）

| 種類 | 量 | 用途 |
|------|----|------|
| SPO doc | 50-80 件 | C: curation 対象 / D: 学習素材 |
| 契約書 | 15-20 件 | C: shareability 判断 / **D: share-safe filter** |
| 会議 transcript | 20-30 件 | D: 学習素材 / C: project knowledge 補強 |
| Teams / Slack chat | 100+ messages | D: 学習素材 |

### 統合 schema

- 全 doc / chunk に **`contract_id` を紐付け**（C path で判断された shareable / redact 状態が D path でも効く）
- 学習プロファイル `domain_weights` は C の curation tag（`industry`, `case_type`）と vocabulary 共有

### AI Search index（3 本）

| index | 内容 | metadata 共通 | 利用 path |
|------|-----|------------|----------|
| `contracts` | clause | `contract_id`, `shareability` | C |
| `knowledge` | doc/transcript/chat chunk | `domain`, `case_type`, `contract_id`, **`shareable_only`** | **C + D 両方** |
| `learning_profile` | user state | `user_id`, `domain_weights` | D |

**統合の物理的接点**: `knowledge` index に `shareable_only` フィールドがあり、**C path（提案検索）も D path（朝刊配信）も同じ filter を共有**。

---

## 7. HITL surface

| ステップ | path | UI | 人間がやること |
|--------|------|-----|--------------|
| 契約書 clause 判断 | C | clause-by-clause table | 承認 / 修正 / 拒否 |
| 知見エントリ pre-publish | C | summary + tags | 承認 |
| Retrieval relevance | C | 結果 thumbs | 評価 |
| 出題への解答 | D | 4 択 + 自己評価 | 解答 |
| 要約への反応 | D | thumbs | 関心評価 |
| プロファイル editing | D | 興味リスト | 明示変更 |

**統合の効果**: C 側 HITL の `shareability` 判断が **D 側配信にも cascade**（C で「共有不可」と判断された clause は D 側で出題されない）→ 守秘リスクが両 path で同時 bounded。

---

## 8. Demo storyboard（3 分以内）

| 時刻 | シーン | 何を見せる |
|------|------|----------|
| 0:00-0:30 | PM 視点: プロジェクト完了 | Archive with Agent 起動 |
| 0:30-1:00 | C path 圧縮: Contract Analyzer + Curator | clause-by-clause 判断 + curation を **30 秒に圧縮**（要点のみ） |
| 1:00-1:30 | **場面転換 1**: 6 ヶ月後の別 PM 提案検索 | 新規案件入力 → 共有可な過去案件 surfaces（C path 完成形） |
| 1:30-2:00 | **場面転換 2**: ジュニアコンサル朝の Web UI | 「本日の朝刊」→ 同じ過去 project から個人化クイズ |
| 2:00-2:30 | ジュニアが解答 → 解説 | "詳しくは過去 project XX の curated entry（**clause Y で共有可と判断済**）" — **C → D の接続を明示** |
| 2:30-3:00 | admin 視点: lifecycle ビュー | 1 corpus が 2 modes で活用される heatmap + 「contract-aware が D 側にも効く」を 1 行で訴求 |

**判定基準**: 観客が「1 corpus が 2 modes で活きる」と即理解できるか / 統合の "薄さ" が見えないか（pitch の最大リスク）。

---

## 9. 6週ビルドリスク（R/Y/G）

| レイヤ | リスク | 理由 / 緩和 |
|------|------|-----------|
| **全 corpus 量（契約書 + SPO + transcript + chat）** | 🔴 R | **単独 C より 1.7x の合成負荷**。Day 7 までに C の最小 5 件 + D の最小 30 doc を **並行整備** |
| C path 完全実装 | 🟡 Y | 単独 C と同じ |
| D path simplified 実装 | 🟡 Y | Generator のみ、Profile / Feedback は static demo |
| 共通 ingest pipeline | 🟡 Y | orchestration 設計が増える、3 日 |
| 統合 demo storyboard | 🟡 Y | 3 分に 2 path を押し込む脚本、リハ込みで 2-3 日 |
| **予算 ($173 / $200)** | 🟡 Y | バッファ $27 はタイト → Day 28 で再見積もり mandatory |
| HITL UI（C + D） | 🟡 Y | 共通 shell で実装すれば lift 削減 |
| Logic Apps | 🟢 G | managed |
| Orchestrator | 🟢 G | flow 増えるが各々素直 |
| 認証 / 観測 | 🟢 G | scaffold 済 |

**ボトルネック**: ① corpus 量（R）= 単独 C より重い、② 統合 demo storyboard（Y）= "薄さ" が見えると逆効果。

**実装量の現実**: 単独 C 比で **1.5-1.7x**。6週で 2 path を回し切る prerequisite は (a) Day 7 corpus 50% / (b) Day 14 で C path MVP / (c) Day 21 で D Generator / (d) Day 28 で統合 demo リハ。

---

## 10. Differentiation hook

> **「1 corpus × 2 出力モード」の lifecycle 訴求**
>
> 他チームは「単機能 agent」を出してくる可能性が高い。本案は **同じ knowledge corpus が pull（C 提案検索）と push（D 朝刊配信）の両モードで活きる lifecycle 設計** を構造的差別化として提示。Sotaro テーゼ（domain-specialty prevalence）の **組織化（C）+ 個人化（D）の同時実装**。

**主張可能な独自性**:
1. **「1 corpus × 2 出力モード」**: lifecycle 訴求（他チームの単機能 agent との構造差別化）
2. **Contract-aware が D 側にも効く**: share-safe push 配信（C 単独 / D 単独では出ない強み）
3. **組織化 + 個人化の同時実装**: テーゼに対する 2 角形の応答

**リスク**: 統合の "**薄さ**" が見えると逆効果（「無理やり繋げた感」）→ pitch で **30 秒以内に「同じ corpus が両側で活きる具体例」** を示せないとマイナス。

---

## 11. このカードからの Open question

1. **6週 + $200 で本当に 2 path 動かせるか** → 単独 C カード比 1.5-1.7x の現実性。Day 7 / Day 14 / Day 21 / Day 28 の milestone gate を mandatory に
2. **D path の simplification 度合い** → どこまで切ると "demo only" に見えないか。Profile update を Day 28 で活性化するか諦めるか
3. **C → D 統合 demo 脚本の説得力** → 「同じ project が両側で…」を 30 秒で見せられるか。リハ 2-3 日確保
4. **主軸 C 単独 + D pitch hook（選択肢 Y）との比較** → 統合本実装と pitch hook 訴求のどちらが pitch 強いか
5. **予算バッファ $27 で 6週走り切れるか** → Day 28 で再見積もり、超過時の縮退プラン（D path を pitch hook に縮退 = 選択肢 Y に着地）

---

## 12. テンプレ妥当性 review への問い

このカードを書いてみて分かった **テンプレ自体の課題**:

- ✅ **12 セクション機能**: 統合カードでも format 維持可能
- ⚠️ **統合カードは §2 / §5 / §6 の量が単独 1.5x**: 1 ページに圧縮し切るのが難しい → 折りたたみ表記か別ファイル参照を許容するルール追加
- 📌 **統合カードに「単独カードとの diff サマリ」セクションを追加**: 新規読者が「何が C 単独 / D 単独と違うのか」を 30 秒で把握できる欄
- 📌 **§9 R/Y/G に "実装量 multiplier" 列を追加**: 統合カードは単独 1.5-1.7x、これを明示する欄

**review 後の next action**:
- 4 カード（C / A / D / C+D）出揃った → チーム alignment
- 5/11 決定: 単独 C / 単独 A / C+D 統合 / 単独 D のいずれかを採択 → §5 problem-statement.md「backbone for dev」に最初の entry を書く
- 修正あれば 4 カードに反映 → 採択カードを implementation スペックの起点に
