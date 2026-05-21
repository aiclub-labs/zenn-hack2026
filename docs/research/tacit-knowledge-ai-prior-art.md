# 暗黙知形式化 × AI 活用 — 先行事例リサーチ

> 作成日: 2026-05-12 / 用途: dialogue-delta-formalization spec の design フェーズ前補完
> 関連: ../architecture-cards/idea-f-dialogue-monitoring.md, ../../.kiro/specs/dialogue-delta-formalization/
> 調査者: Claude (Opus 4.7) / タイムボックス 20 分

## TL;DR (3 行)

- LLM による暗黙知抽出は既に学術領域で確立しており、特に Kunumi 社の arXiv 2507.03811 が「LLM エージェントによる反復対話 + 自己批評スコア (0-10) + 列単位の暗黙知をエピデミックモデルで追跡」という直接転用可能なパターンを提示している。spec の **正誤判定 = LLM-as-judge + 構造化 KG 照合のハイブリッド**、**重み付け = 自己批評スコア + アノテータ信頼度 (EffiARA 系) + provenance 減衰** の三層を推奨。
- Fact verification 系は GraphCheck (atomic claim 分解 → KG パスでスコア) と FactCheck (RAG + LLM アンサンブル投票) の二系統が主流。本プロジェクトの「入力 vs corpus」差分判定は GraphCheck 型の atomic decomposition、人間入力の信頼度集約は FactCheck 型のアンサンブルが適合。
- 5W1H ヒアリングは Kunukmi 論文の「rapport → 質問 → 応答処理 → 自己批評 → 続行/切替」5-step プロトコルが現実的に最もシンプル。SECI Externalization の AI 実装としては PKAI (Springer BISE 2025) が socialization → externalization の多エージェント構成を提示。

---

## 1. AI-driven dialogue delta detection

- **Kunumi: Leveraging LLMs for Tacit Knowledge Discovery in Organizational Contexts** ([arxiv.org/abs/2507.03811](https://arxiv.org/abs/2507.03811))
  - 手法: テーブル列を「fact」単位に分解し、LLM エージェントが従業員と反復対話。**stack-based に階層下位を優先**、新規担当者が言及されたら動的に再優先化。プロンプトチェイニングで部分観測 MDP として定式化。
  - 差分スコアリング: **自己批評スコア 0-10**。≥5 = 列名/意味/型を把握、≥8 = 暗黙知 (変数間相互作用) を含む。不確実 / 推測情報は自動減点。外部評価 (G-Eval, METEOR, full-knowledge recall) と相関 0.73。
  - **本 spec への含意**: 「AI 出力 vs 人間入力」の差分検出にそのまま流用可能。AI 出力の自己批評スコア < 閾値 → 暗黙知ギャップ候補、と定式化できる。
- **PKAI: LLMs for Process Knowledge Acquisition** (Springer BISE 2025, [link.springer.com/article/10.1007/s12599-025-00976-w](https://link.springer.com/article/10.1007/s12599-025-00976-w))
  - 手法: SECI の preparation / socialization / externalization 各フェーズを別の専門エージェントに割当てる multi-agent system。**19 件の design requirement** を知識獲得理論ベースで定義 (本文は要確認、abstract のみ確認)。
  - **本 spec への含意**: 「監視 / 検知 / ヒアリング / 形式化」を別エージェントに分離する構成の正当化材料になる。詳細は本文未確認。
- **Knowledge Sharing in Manufacturing using LLM-powered Tools** (PMC, [pmc.ncbi.nlm.nih.gov/articles/PMC11004332/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11004332/))
  - 手法: 製造業現場での LLM チャットボットによる適応的インタビュー。follow-up question と曖昧性解消が中心。要確認 (abstract のみ)。

## 2. Human input weighting / trust scoring

- **EffiARA: Efficient Annotator Reliability Assessment** ([arxiv.org/html/2410.14515v1](https://arxiv.org/html/2410.14515v1))
  - 手法: **inter- / intra-annotator agreement から worker reliability score を計算 → loss function のサンプル重みに反映**。soft-label training で判断の不確実性を保持。
  - **本 spec への含意**: 複数人が同一暗黙知に回答した場合の集約方法として直接採用可能。最低限「ユーザー × topic 単位の過去 agreement 率」を保持し sigmoid で重み化する設計が現実的。
- **Fleiss' kappa / Krippendorff's alpha** (古典、[Wikipedia 経由で確認可能](https://en.wikipedia.org/wiki/Fleiss%27_kappa))
  - 多人数アノテータ間の一致度を [-1, 1] / [0, 1] で測る指標。**カテゴリ / 順序 / 連続値混在 OK は Krippendorff** が唯一の選択肢。
  - **本 spec への含意**: トピック単位の信頼度 baseline 計算に流用。MVP 段階では Fleiss' kappa で十分。
- **Worker reliability re-weighting framework** (EffiARA 論文内で引用される一連の研究)
  - **本 spec への含意**: 投票による多数決ではなく、信頼度重み付き平均が標準。spec の「重み付き形式化」はこの系譜に位置付けられる。

## 3. Truth judgment in knowledge bases

- **GraphCheck: Extracted Knowledge Graph-Powered Fact-Checking** (PMC, [pmc.ncbi.nlm.nih.gov/articles/PMC12360635/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360635/))
  - 手法: 応答を **atomic claim に分解 → KG から evidence path を引き当てスコア化**。汎用 / 医療ベンチマークで +7.1%。
  - **本 spec への含意**: 「入力された暗黙知」を atomic claim に分割し、既存 corpus との照合で正誤を出す方式に流用可能。**spec の正誤判定方式 A** として提案。
- **FactCheck: Fact Verification in KGs Using LLMs** (SIGIR 2025 Demo, [dei.unipd.it/~silvello/papers/2025-SIGIR_Demo_LLM.pdf](https://www.dei.unipd.it/~silvello/papers/2025-SIGIR_Demo_LLM.pdf))
  - 手法: **RAG + LLM アンサンブル投票** で KG 内の fact を検証。複数 LLM の合議で信頼性を担保。
  - **本 spec への含意**: **spec の正誤判定方式 B**。corpus が薄い初期段階で external grounding なしに合議で動かせる利点。
- **Hybrid Fact-Checking (KG + LLM + Web search)** ([arxiv.org/html/2511.03217](https://arxiv.org/html/2511.03217))
  - 手法: KG-first / web-adaptive。KG ヒットなければ web 検索にフォールバック。
  - **本 spec への含意**: **spec の正誤判定方式 C** (中長期)。corpus + Wikipedia / Bing grounding のハイブリッド。

## 4. 5W1H / structured elicitation

- **5W1H 専用の LLM 研究は今回見つからず** (要確認: より深い検索が必要)。一般的な information extraction prompt engineering は [promptingguide.ai/prompts/information-extraction](https://www.promptingguide.ai/prompts/information-extraction) に集約されているが 5W1H 明示の事例は薄い。
- **ChatExtract** ([nature.com/articles/s41467-024-45914-8](https://www.nature.com/articles/s41467-024-45914-8))
  - 手法: 抽出 → **follow-up question で正誤を再確認** する 2 段プロンプト。材料科学論文から物性値を抽出。
  - **本 spec への含意**: 5W1H で抽出した後に「この理解で合っているか」を follow-up で確認する 2 段化で hallucination を下げられる。
- **Kunumi 論文の 5-step protocol** (1 と同じ): rapport → 質問 → 応答処理 → 自己批評 → 続行/切替。**5W1H をこの「質問」ステップに埋め込む形が最もシンプル**。

## 5. SECI モデルの AI 実装

- **PKAI** (前出 [Springer](https://link.springer.com/article/10.1007/s12599-025-00976-w)): SECI の socialization / externalization を multi-agent で実装。要確認。
- **古典理論レビュー**: SECI の externalization は「dialogue, metaphor, conceptualization」で tacit → explicit を実現する ([Frontiers in Psychology 2019](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.02730/full))。**本 spec の「5W1H ヒアリング」は externalization フェーズの dialogue 形式に該当**、と位置付けられる。
- ServiceNow blog ([servicenow.com/community/.../the-knowledge-creation-series-episode-1](https://www.servicenow.com/community/knowledge-management-blog/the-knowledge-creation-series-episode-1-the-seci-model-four/ba-p/3349445)): SECI を KM 製品で扱う際の整理。要確認 (理論寄り)。

## 6. エンタープライズ製品の知識管理

- **Glean** ([glean.com/solutions/knowledge-management](https://www.glean.com/solutions/knowledge-management))
  - 公開資料の範囲: 100+ SaaS 横断検索 + RAG。**暗黙知抽出は明示されておらず、explicit knowledge の検索/集約が主**。
  - **本 spec への含意**: Glean が埋めていない「暗黙知ヒアリング → corpus 化」レイヤーが本プロジェクトの差別化点になる、と整理可能。
- **Microsoft Copilot for Knowledge / Notion AI / Guru / Bloomfire**: 今回未深掘り (要確認)。いずれも公開資料ベースでは「既存ドキュメントの RAG / 要約」が主軸で、対話差分からの暗黙知抽出を明示する製品は確認できていない。

---

## 本 spec への落とし込み提案

### 正誤判定方式

| 案 | 内容 | 採用判断 |
|----|------|----------|
| A. atomic claim 分解 + corpus 照合 (GraphCheck 型) | 入力をユニット化し既存 corpus との一致をスコア化 | **MVP 推奨**。corpus が育つ前提で長期的にも生きる |
| B. LLM アンサンブル投票 (FactCheck 型) | 3 つの LLM で同入力を判定し合議 | corpus 不在の冷起動期に併用 |
| C. Web/KG ハイブリッド | Wikipedia / Bing grounding をフォールバック | 中長期、汎用知識領域に限定 |

**推奨: A をベース、冷起動期間のみ B を併用、C は将来オプション。**

### 重み付け方式

| 案 | 内容 | 採用判断 |
|----|------|----------|
| A. LLM 自己批評スコア (Kunumi 型 0-10) | 入力の確信度を LLM 自身に採点させる | **必須**。実装も軽い |
| B. アノテータ信頼度 (EffiARA 型) | ユーザー × topic 単位の過去 agreement から信頼度 | **MVP 第二段**。複数人入力が蓄積した段階で投入 |
| C. Provenance 時間減衰 (Kunumi のエピデミックモデル類似) | 古い知識は β(t) = β₀e^(-γt) で減衰 | 第三段。鮮度管理が要件化した段階で |

**推奨: 最終重み = A × B × C の積。MVP は A のみ、Phase 2 で B、Phase 3 で C。**

### 閾値設計のたたき台

- **暗黙知ギャップ検知**: AI 出力の self-critic score < **5** (Kunumi の「列の意味を把握」未満ライン) → ヒアリングトリガ。
- **形式化採用 (corpus 投入)**: 重み付き合成スコア ≥ **0.7** (A: ≥7/10、B: ≥0.6、C: 1.0 で初期 ≈ 0.42 → ヒアリング複数回で底上げ)。閾値は計測しながらキャリブレーション。
- **正誤判定で reject**: GraphCheck 型の atomic claim 整合性スコア < **0.4**。

---

## 開いている疑問

- PKAI 論文の本文 (19 件の design requirement) を読まないと、ヒアリング設計の網羅性チェックができない → **design フェーズ前に必読**。
- Microsoft Copilot for Knowledge / Notion AI 等のエンタープライズ製品が暗黙知をどう扱うかの一次資料は未確認。差別化ストーリーの強度に影響。
- 5W1H 専用の LLM プロンプト研究は今回見つけられず。Kunumi 5-step の「質問」ステップに埋め込む形で良いか、独自に follow-up rule を設計するかは spec 段階で判断必要。
- Krippendorff's alpha を Phase 1 から入れるか Phase 2 まで遅延させるかは、初期ユーザー数の見積もり次第。
- 自己批評スコアの hallucination リスク (LLM が自身の確信度を過大評価する既知問題) は別途軽減策が必要。複数 LLM での self-critic を平均、あたりが現実解か。
