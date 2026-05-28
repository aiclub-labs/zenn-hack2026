# 新案A — 案件立ち上げ人材マッチングエージェント（Architecture Card）

> **目的**: 新案C カード（[idea-c-knowledge-archive.md](./idea-c-knowledge-archive.md)）と同じ 12 セクション format で並置し、5/11 のテーマ確定を table-read 化する。本カードは新案A（kickoff 暫定主軸候補）。
>
> 関連: [problem-statement.md §2](../../problem-statement.md#候補のマトリクスkickoff-後4-候補で再構成) · [.html 版](./idea-a-personnel-matching.html)

作成日: 2026-05-11 / ステータス: チーム review 用 draft

---

## 0. 30 秒サマリー

> PM が案件要件（業界 / 必要スキル / 期間 / 働き方）を入力 → agent が **KC Bridge データ + CV PPT + GPDR 評価** を 3 軸で並列分析 → 理由付きランキング + 打診メッセージドラフト。ジュニア側 use-case では自分のマッチ率を見て自己 awareness を形成（双方向）。
>
> **核**: 3 軸スコアリング（**スキル / キャリア志向 / GPDR**）+ 双方向 UI + multi-system 横断。LLM 1-shot では到達不能な agent 性。

---

## 1. As-Is → To-Be

### As-Is

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| 案件立ち上げ | PM が KC Bridge で手動検索（スキル一覧 → 絞り込み → 候補リスト） | キャリア志向まで加味できず時間がかかる |
| 候補打診 | PM が個別 Teams ping → 興味確認 → CV 確認 | 1 案件 2-3 時間の overhead |
| ジュニア視点 | 自分がどの案件にマッチしうるか不明 / 自己 PR の updates が反映されているか不明 | キャリア形成の能動性が育たない |
| 結果 | ミスマッチアサイン → 早期離脱 / モチベ低下 | 離職率と project velocity に影響 |

### To-Be

| 段階 | 何が起きるか | 解決される痛み |
|------|------------|--------------|
| 案件立ち上げ | PM が要件入力 → **数分で 3 軸ランキング + 理由 + 打診ドラフト** | 数時間 → 数分 |
| 候補打診 | PM が ranking 上位を承認・編集 → agent が打診メッセージ送信 | overhead 圧縮 |
| ジュニア視点 | 自分のマッチ率と "上げるには XX スキル" を確認 | 能動的キャリア形成 |
| 結果 | スキル + キャリア整合のあるアサイン / 双方向 visibility | 離職率改善 / project velocity 向上 |

### 埋まるギャップ（3 点）

1. **マッチング時間**: 数時間 → 数分
2. **キャリア志向の加味**: 暗黙判断 → 明示 3 軸スコア
3. **双方向 visibility**: PM 側単独 → PM + ジュニア両側

---

## 2. Azure サービス（具体 SKU）

| レイヤ | サービス | SKU | 月額（概算） | 採用根拠 |
|------|---------|-----|------------|--------|
| 文書解析 | Azure AI Document Intelligence | Standard S0 | 〜$10 | CV PPT → スキル / 経歴抽出 |
| LLM | Azure OpenAI | GPT-4.1（説明）+ mini（分類） | 〜$35 | 3 軸スコアリング判断 + 打診ドラフト |
| 検索 | Azure AI Search | Basic | 〜$75 | members / projects index、vector + filter |
| ホスト | Azure Container Apps | Consumption | 〜$10 | UI + agent backend |
| ストレージ | Blob Storage | Hot LRS | 〜$5 | CV PPT / 案件サマリ |
| 状態 | Cosmos DB | Serverless | 〜$5 | プロファイル / HITL 履歴 |
| 観測 | App Insights | Basic | 〜$5 | scaffold 済 |
| 認証 | Entra ID | included | $0 | scaffold 済 |

**6週合計見込み: 〜$145 / $200**（バッファ $55、C より緩い）。

---

## 3. Agent topology

```
[ PM UI ]  [ ジュニア UI ]
       │         │
       ▼         ▼
   ┌─────────────────────┐
   │  Orchestrator agent │  (role-aware routing: PM / junior)
   └─────────────────────┘
            │
   ┌────────┴────────┐
   ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Search agent │  │ Self-aware   │
│ (KC Bridge + │  │ agent        │
│  CV + GPDR   │  │ (junior 側)  │
│  vector +    │  └──────────────┘
│  filter)     │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Scoring      │  3 軸: スキル / キャリア / GPDR + sub
│ agent        │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Explanation  │  理由付け + 打診ドラフト
│ agent        │
└──────────────┘
       │
       ▼
[ HITL: PM が "もっと X 重視で" 調整指示 ]
```

**MVP 構成**: Search + Scoring を 1 agent 統合、Explanation 別、Self-aware は Day 21 以降。

**「agent である必要」の論証**:
- (a) KC Bridge + CV + GPDR + 過去案件 の **multi-system 横断**
- (b) PM / ジュニアで role-aware に振る舞いを切り替える **state**
- (c) HITL の調整指示（「もっとキャリア重視」）を **意図解釈して re-rank** する multi-step。LLM 1-shot では不可能。

---

## 4. Tool / MCP インベントリ

| Tool | 種別 | 用途 |
|------|-----|------|
| `kc_bridge.query_members` | mock API | 擬似 KC Bridge へのスキル / 業界クエリ |
| `document_intelligence.extract_cv` | Azure AI wrapper | CV PPT → 構造化 |
| `gpdr.fetch_scores` | mock API | 9 項目 × 5 段階のスコア取得 |
| `ai_search.query_members` | AI Search | vector + filter |
| `ai_search.query_projects` | AI Search | 過去参画案件履歴 |
| `llm.score_3axis` | structured output | スキル / キャリア / GPDR の重み付け |
| `llm.explain_match` | structured output | ランキング各候補の理由付け |
| `llm.draft_outreach` | structured output | 打診メッセージ生成 |
| `cosmos.log_decision` | Cosmos SDK | HITL 履歴 |

---

## 5. 擬似コーポレートシステム

| 実環境 | 擬似実装 | 構築コスト |
|------|---------|----------|
| KC Bridge（Power Automate） | **Web UI mock**（メンバー検索画面風 React） | 中（5 日） |
| GPDR 評価 backend | Cosmos に 9 項目 × 5 段階を格納、REST API で返却 | 小（2 日） |
| CV PPT store | Blob + thumbnail 表示 UI | 小（2 日） |
| 個人ページ（キャリア志向自己申告） | Web フォーム + Cosmos | 小（1 日） |
| 認証 / 権限 | Entra ID + roles（PM / consultant / viewer） | 小（managed） |

**lift 評価**: KC Bridge mock UI が中、それ以外は低。**合成データの "内的整合性"** が最大の隠れコスト（スキル / 経歴 / キャリア志向 / GPDR が矛盾しないように）。

---

## 6. Corpus

### メンバープロファイル（最大の build risk）

- **60-80 名 = 業界 5 種 × スキル 10 種 × 経験レベル 3 段階**
- 各メンバー: スキル配列 / 業界経験 / キャリア志向（自己申告テキスト 200-400 字）/ GPDR スコア / 直近 3-5 件参画案件
- 生成: AOAI structured output → 「内的整合性チェック」（スキル ↔ 経歴 ↔ GPDR ↔ 志向が矛盾しないか）

### CV PPT

- **10-15 件サンプル**、テンプレ統一（実 KPMG 形式風）
- AOAI 生成テキスト → PPT に流し込み（python-pptx）

### 過去案件サマリ

- **30-50 件**、業界 / 案件タイプ / 期間 / role / 成果
- 各メンバーの参画履歴と紐付け

### AI Search index 設計

| index | 内容 | metadata | vector |
|------|-----|---------|-------|
| `members` | プロファイル chunk | `skills[]`, `industries[]`, `career_intent`, `gpdr_scores` | スキル + キャリア志向 embedding |
| `projects` | 案件サマリ chunk | `industry`, `case_type`, `members[]` | サマリ embedding |

---

## 7. HITL surface

| ステップ | UI | 人間がやること | feedback 保存先 |
|--------|-----|--------------|---------------|
| ランキング review | 候補 5 名カード + レーダーチャート + 理由 | "もっとスキル重視で" / "キャリア志向を強く" を自由文で指示 → re-rank | Cosmos: 次回 prompt few-shot |
| 打診メッセージ承認 | agent ドラフト textarea | 編集 / 承認 / 送信 | Cosmos |
| ジュニア self-edit | プロファイル画面 | キャリア志向テキスト修正 → 次回マッチに反映 | Cosmos |

**A の「interface critical」要件への回答**: 単純承認/却下ではなく、**自由文で重み調整指示**（「もっと X 重視で」）が UX の核。これがないと HITL が機能しない。

---

## 8. Demo storyboard（3 分以内）

| 時刻 | シーン | 何を見せる |
|------|------|----------|
| 0:00-0:30 | PM 視点：案件要件入力 | フォーム「業界: retail / 必要スキル: AI 戦略 + データ分析 / 期間: 3 ヶ月 / 働き方: hybrid」→ 「Find Match」 |
| 0:30-1:30 | Agent 動作 | 候補 5 名表示。各候補に **3 軸レーダーチャート**（skill / career / GPDR）+ 理由 1 行 + "過去 retail 案件参画" タグ |
| 1:30-2:00 | HITL 調整 | PM が「もっとキャリア志向を見て」と入力 → re-rank → 別の候補が浮上 |
| 2:00-2:30 | 打診ドラフト | agent が打診メッセージ生成 → PM が編集 → 送信 |
| 2:30-3:00 | 場面転換: ジュニア視点 | 自分のプロファイル画面で「**マッチ率 60% — 上げるには XX スキル**」を表示。双方向性を演出 |

**判定基準**: 観客が「3 軸スコアリング + 双方向」が独自と即理解できるか / KPMG 文脈なしでも汎用 talent matching agent として動くか。

---

## 9. 6週ビルドリスク（R/Y/G）

| レイヤ | リスク | 理由 / 緩和 |
|------|------|-----------|
| DocIntel CV parsing | 🟢 G | managed |
| 3 軸スコアリング LLM | 🟡 Y | prompt 設計と重み調整、3-5 日 |
| **メンバーデータ合成（内的整合性）** | 🔴 R | **最大変数**。60-80 名 × multi-attribute の矛盾なし設計。Day 7 までに 20 名 core |
| CV PPT 合成（10-15 件） | 🟡 Y | テンプレ + AOAI で量産可、リアルさ要 sanity check |
| 過去案件サマリ | 🟡 Y | 量と業界 mix |
| AI Search vector + filter | 🟢 G | well-trodden |
| KC Bridge mock UI | 🟡 Y | Power Automate 風表現 5 日 |
| HITL UI（自由文調整） | 🟡 Y | "もっと X 重視で" を re-rank に翻訳する prompt 設計が肝 |
| 双方向 UI（ジュニア側） | 🟡 Y | MVP では simplified、Day 28 で本格化 |
| Orchestrator | 🟢 G | role-aware routing は素直 |

**ボトルネック**: メンバーデータの内的整合性 (R)。**Day 7 までに 20 名 core dataset** を mandatory。

---

## 10. Differentiation hook

> **「3 軸スコアリング + 双方向 talent matching」**
>
> 多くの talent matching プロダクト（LinkedIn Talent Insights / Workday Skills Cloud 等）は **スキル単独** が中心。本案は **スキル + キャリア志向 + GPDR（客観評価）** の 3 軸 + **双方向 UI（PM とジュニア両側で agent が振る舞う）**。

**主張可能な独自性**:
1. 3 軸スコアリング（スキル / キャリア / GPDR）+ レーダーチャート可視化
2. **自由文での重み調整 HITL**（「もっとキャリア重視で」→ 即 re-rank）
3. 双方向 use-case（ジュニア側の self-awareness UI）

**他チームと被るリスク**: talent matching は被る確率中 → 上記 3 点 + KPMG 固有（KC Bridge + GPDR）で diff を出す。

---

## 11. このカードからの Open question

1. **メンバー 60-80 名で "内的整合性" を保てるか** → Day 7 までに 20 名で feasibility 確認
2. **ジュニア側 use-case は MVP 必須か Day 28 拡張か** → demo 双方向性が独自性の柱なら MVP 必須
3. **GPDR 9 項目を全部 demo に出すか subset か** → 認知負荷 vs 厚み
4. **KC Bridge mock UI の "Power Automate 風" の lift 度合い** → 5 日かけるか簡易版で済ますか
5. **C / D との統合をこのカードに含めるか** → 別カード（C+D 統合カード）と切り分ける

---

## 12. テンプレ妥当性 review への問い

このカードを書いてみて分かった **テンプレ自体の課題**:

- ✅ **12 セクション機能**: C と同じ format で書ける、テンプレが pattern-agnostic
- ⚠️ **§5 に "lift 評価" 列が欲しい**: 各 mock 環境の構築 lift（高 / 中 / 低）を §5 内に明示すべき → format 改訂候補
- ⚠️ **§8 storyboard が "双方向" だと複雑**: A は 2 つの persona を 3 分に押し込む → "場面転換" の演出が必須
- 📌 **追加検討**: §3 topology の "role-aware behavior" を明示する欄を独立化（agent 性論証の差別化に効く）

**review 後の next action**:
- この format で OK なら D / C+D も同型 clone（5/11 中）
- 修正あれば C+A 双方に反映 → 再 review
