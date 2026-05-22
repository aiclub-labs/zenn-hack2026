# Research & Design Decisions

## Summary

- **Feature**: `dialogue-delta-formalization`
- **Discovery Scope**: Complex Integration（マルチエージェント + HITL + 暗黙知形式化 + Azure agent platform 新製品検証）
- **Key Findings**:
  - **Foundry Agent Service + MAF 1.0 + BYO Cosmos のハイブリッド構成**が HITL / checkpoint / multi-agent orchestration を最小自前実装で実現できる（→ `azure-agent-platform-decision.md`）
  - 暗黙知形式化の正誤判定は **GraphCheck (atomic claim 分解 + KG path) を MVP、冷起動期は FactCheck の 3 LLM アンサンブル併用** が現状ベスト（→ `tacit-knowledge-ai-prior-art.md`）
  - 重み付けは **A (LLM 自己批評, Kunumi) × B (アノテータ信頼度, EffiARA) × C (時間減衰)** の 3 層積、MVP は A のみ
  - ヒアリングは **Kunumi 5-step に 5W1H を埋込み、ChatExtract follow-up confirmation で hallucination 抑制**
  - POC マス候補は 5 件評価済、**A (戦略×製造業 / 人材アサイン)** が議事録例示 + デモ強度 + corpus 作成負荷の 3 軸で最有力

## Research Log

外部リサーチは独立ファイルに切り出し、本 `research.md` はインデックスと spec への結論橋渡しのみを担う。

### 暗黙知形式化システムの先行事例（2026-05-12 完了）

- **Context**: 「重み付け（フラグ / 多数決 / 公開情報照合の組合せ）」の具体仕様を想像で書かないため、AI を活用した暗黙知形式化システムの先行研究と既存製品を調査
- **Sources**: `../../../docs/research/tacit-knowledge-ai-prior-art.md` 内に全 URL あり（Kunumi, EffiARA, GraphCheck, FactCheck, ChatExtract, PKAI, 各社 enterprise 製品）
- **Findings**: requirements `### リサーチ結論を踏まえた設計ベースライン` 表 1-3 に要約
- **Implications**: Requirement 5 (重み付け) / 7 (正誤判定) / 4 (ヒアリング) の Acceptance Criteria を研究結論ベースで EARS 化

### Azure Agent Platform 選定（2026-05-12 完了）

- **Context**: Semantic Kernel 単体 / MAF / Foundry / Container Apps 直接デプロイのいずれが MVP の HITL + multi-agent + 6 週 / $200 制約で最適か判断
- **Sources**: `../../../docs/research/azure-agent-platform-decision.md`
- **Findings**: Foundry Workflow agent (preview) で HITL と orchestration を宣言的に書けるが preview 機能、MAF を Container Apps に直接デプロイすればコード変更なしで切替可能（converged runtime）
- **Implications**: Week 1 (2026-05-18) を flag day として Foundry Hosted agent の swedencentral 提供有無 / Free Trial enable 可否を実機検証してから最終確定

### POC セクター×ユニット候補（2026-05-12 完了）

- **Context**: 8 セクター × 10 ユニットのうち POC で扱う 1-2 マスを選定
- **Sources**: `../../../docs/research/sector-unit-candidates.md`
- **Findings**: 5 候補を 4 軸（暗黙知密度 / 差分顕在性 / corpus 作成しやすさ / デモ説得力）で評価。A=戦略×製造業 (人材アサイン) が議事録例示済で最有力
- **Implications**: 5/14 セッションで KPMG AI 部の実マトリクスとのマッピングを確認し最終確定。requirements は最終マス未確定でも記述可能（partition key 設計で多マス対応のため）

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Semantic Kernel 単体 + Container Apps | SK Process Framework で orchestration、HITL は自前 | 既知の枠組み | MAF 1.0 リリースで継続性に疑問、HITL 自前実装コスト高 | 却下 |
| MAF 1.0 単体 + Container Apps | SK + AutoGen 統合後継、`RequestInfoEvent` で HITL | 単一 SDK で記述、Foundry 無しで完結 | orchestration の宣言性が低い、checkpoint 機構を自前実装 | バックアップ案 |
| **Foundry Workflow + MAF + BYO Cosmos** | Foundry が orchestration / HITL / checkpoint を提供、MAF は SDK | HITL pause-resume と長期 thread 永続化が標準、token + tool のみ課金 | Workflow agent / Hosted agent は preview、swedencentral 提供未確認 | **採用候補** |
| AWS Bedrock 移植 | 比較対照のみ | – | hackathon Azure 縛りで非該当 | 却下 |

## Design Decisions

### Decision: Foundry Workflow agent (preview) を MVP の orchestration に採用、MAF を SDK 層に据える

- **Context**: HITL pause-resume / 長期 thread 永続化 / 4 agent orchestration / 6 週 / $200 / agent tracing を全て満たす必要
- **Alternatives Considered**:
  1. SK 単体 + 自前 HITL — 工数が膨らむ
  2. MAF + Container Apps 直接 — orchestration の宣言性なし
  3. **Foundry + MAF + BYO Cosmos** — preview リスクあるが標準機能で網羅
- **Selected Approach**: 3
- **Rationale**: Foundry は本体無料で token + tool のみ課金、BYO Cosmos で conversation state を可視化可能、per-agent Entra identity / App Insights tracing 標準。MAF コードは Container Apps へ移植可能なため preview リスクヘッジ可
- **Trade-offs**: preview 機能依存（breaking change リスク）↔ 自前実装の工数削減
- **Follow-up**: Week 1 (2026-05-18) flag day で swedencentral 提供 / Free Trial enable / Workflow agent の RequestInfoEvent 挙動を実機検証

### Decision: 正誤判定は GraphCheck 型 MVP、冷起動期は FactCheck 型 3 LLM 投票で補強

- **Context**: 冷起動期は corpus がほぼ空のため atomic claim 整合性照合が機能しない
- **Alternatives Considered**:
  1. GraphCheck のみ — 冷起動失敗
  2. FactCheck のみ — corpus 蓄積後も LLM コスト高
  3. **GraphCheck メイン + FactCheck (corpus < 30 件時のみ) 併用**
- **Selected Approach**: 3
- **Rationale**: corpus 規模で自動的に判定方式を切替えればコストと精度のバランスが取れる
- **Trade-offs**: ロジックがやや複雑化 ↔ 冷起動失敗回避
- **Follow-up**: 閾値 30 件は実測でキャリブレーション

### Decision: 重み付けは MVP では LLM 自己批評 (A) のみ、B/C は Phase 2/3 段階導入

- **Context**: EffiARA は複数アノテータ蓄積前提、時間減衰は鮮度管理要件確定後
- **Selected Approach**: 段階導入
- **Rationale**: MVP で空回りせず実装範囲を絞れる
- **Trade-offs**: 初期重みが LLM 自己評価バイアスを受ける ↔ 実装速度
- **Follow-up**: Phase 2 で EffiARA 試行、Phase 3 で β(t) 減衰の γ を環境変数化

### Decision: 多マス対応は partition key `{sector}#{unit}` 単一設計、AI Search index は 1 本

- **Context**: 多マス展開時のリソース増加と migration コストを最小化したい
- **Selected Approach**: Cosmos / AI Search ともに 1 リソースで sector + unit を filter
- **Rationale**: マス追加時 schema 投入のみで稼働できる
- **Trade-offs**: マス間データ分離が論理層のみ ↔ infra コスト最小
- **Follow-up**: マルチテナント要件発生時に index 分割を再評価

### Decision: ヒアリングは Kunumi 5-step に 5W1H を埋込み、ChatExtract で confirmation

- **Context**: 5W1H 専用 LLM プロンプト研究が乏しいため既存プロトコルの組合せで構成
- **Selected Approach**: Kunumi 5-step の「質問」ステップで 5W1H を生成、回答後 ChatExtract 型「この理解で合っていますか?」を 1 回挟む
- **Rationale**: hallucination 抑制 (Nature 2024 報告)、Kunumi の self-critic でヒアリング継続/切替を自動判定
- **Trade-offs**: ターン数が増える ↔ record 品質向上
- **Follow-up**: 5 ターン上限の妥当性は実測

## Risks & Mitigations

- **Foundry Workflow agent preview の breaking change** — MAF を Container Apps に直接デプロイするバックアップ案を Week 1 flag day で確定。コード移植可能（converged runtime）
- **swedencentral リージョンで Foundry Hosted agent 未提供** — Container Apps 直接デプロイにフォールバック、AOAI のみ swedencentral 流用
- **LLM 自己批評の過大評価** — Phase 2 で複数 LLM 平均化を検討、reviewer による補正でカバー
- **冷起動期 corpus 不在で正誤判定が機能しない** — FactCheck 3 LLM 投票 + 人手 seed corpus
- **5/14 後の POC マス変更** — partition key 設計でマス変更時の影響を schema 再投入に限定
- **予算 $200 超過** — `sector-unit-candidates.md` の Tier A-F 削減候補と App Insights alert で段階縮退

## References

- [Microsoft Agent Framework 1.0 GA Announcement](https://devblogs.microsoft.com/foundry/) — 2026-04-03 GA（azure-agent-platform-decision.md 内に詳細）
- [Microsoft Foundry Agent Service docs](https://learn.microsoft.com/azure/ai-services/agents/) — Workflow / Prompt / Hosted agent 区分
- [Kunumi arXiv 2507.03811](https://arxiv.org/abs/2507.03811) — self-critique + 5-step protocol
- [EffiARA arXiv 2410.14515](https://arxiv.org/html/2410.14515v1) — annotator reliability
- [GraphCheck PMC12360635](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360635/) — atomic claim + KG path
- [FactCheck SIGIR 2025](https://www.dei.unipd.it/~silvello/papers/2025-SIGIR_Demo_LLM.pdf) — 3 LLM ensemble
- [ChatExtract Nature 2024](https://www.nature.com/articles/s41467-024-45914-8) — follow-up confirmation
- PKAI (BISE 2025) — SECI multi-agent 19 design requirements（本文精読 TODO）
