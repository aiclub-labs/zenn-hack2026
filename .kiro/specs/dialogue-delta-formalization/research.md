# Research & Design Decisions

## Summary

- **Feature**: `dialogue-delta-formalization`
- **Discovery Scope**: Complex Integration（マルチエージェント + HITL + 暗黙知形式化 + Azure agent platform 新製品検証 + 通知 UX 設計）
- **Key Findings**:
  - **Foundry Agent Service + MAF 1.0 + BYO Cosmos のハイブリッド構成**が HITL / checkpoint / multi-agent orchestration を最小自前実装で実現できる（→ `azure-agent-platform-decision.md`）
  - 暗黙知形式化の正誤判定は **GraphCheck (atomic claim 分解 + KG path) を MVP、冷起動期は FactCheck の 3 LLM アンサンブル併用** が現状ベスト（→ `tacit-knowledge-ai-prior-art.md`）
  - 重み付けは **A (LLM 自己批評, Kunumi) × B (アノテータ信頼度, EffiARA) × C (時間減衰)** の 3 層積、MVP は A のみ
  - ヒアリングは **Kunumi 5-step に 5W1H を埋込み、ChatExtract follow-up confirmation で hallucination 抑制**
  - POC マス候補は 5 件評価済、**A (戦略×製造業 / 人材アサイン)** が議事録例示 + デモ強度 + corpus 作成負荷の 3 軸で最有力
  - **schema 更新通知は Discord webhook 単独配信**で AI Club 既存 bot と疎結合、業務ユーザー認識ズレを抑制（2026-05-25 追加）
  - **MVP 境界は spec-driven build → 機能レビュー → 改修サイクルで吸収**、spec 段階で want/must を先回り削減しない（2026-05-25 追加）

## Research Log

外部リサーチは独立ファイルに切り出し、本 `research.md` はインデックスと spec への結論橋渡しのみを担う。

### 暗黙知形式化システムの先行事例（2026-05-12 完了）

- **Context**: 「重み付け（フラグ / 多数決 / 公開情報照合の組合せ）」の具体仕様を想像で書かないため、AI を活用した暗黙知形式化システムの先行研究と既存製品を調査
- **Sources**: `../../../docs/research/tacit-knowledge-ai-prior-art.md` 内に全 URL あり（Kunumi, EffiARA, GraphCheck, FactCheck, ChatExtract, PKAI, 各社 enterprise 製品）
- **Findings**: requirements `### 設計ベースライン` 表 1-3 に要約
- **Implications**: Requirement 13 (重み付け) / 14 (正誤判定) / 5 (ヒアリング) の Acceptance Criteria を研究結論ベースで EARS 化

### Azure Agent Platform 選定（2026-05-12 完了）

- **Context**: Semantic Kernel 単体 / MAF / Foundry / Container Apps 直接デプロイのいずれが MVP の HITL + multi-agent + 6 週 / $200 制約で最適か判断
- **Sources**: `../../../docs/research/azure-agent-platform-decision.md`
- **Findings**: Foundry Workflow agent (preview) で HITL と orchestration を宣言的に書けるが preview 機能、MAF を Container Apps に直接デプロイすればコード変更なしで切替可能（converged runtime）
- **Implications**: Week 1 (2026-05-18) を flag day として Foundry Hosted agent の swedencentral 提供有無 / Free Trial enable 可否を実機検証してから最終確定

### POC セクター×ユニット候補（2026-05-12 完了）

- **Context**: 8 セクター × 10 ユニットのうち POC で扱う 1-2 マスを選定
- **Sources**: `../../../docs/research/sector-unit-candidates.md`
- **Findings**: 5 候補を 4 軸（暗黙知密度 / 差分顕在性 / corpus 作成しやすさ / デモ説得力）で評価。A=戦略×製造業 (人材アサイン) が議事録例示済で最有力
- **Implications**: 5/14 セッションで KPMG AI 部の実マトリクスとのマッピングを確認し最終確定

### Schema 更新通知 UX の設計（2026-05-25 追加）

- **Context**: 2026-05-25 Daichi review で「**スキーマ更新が業務側に通知されず認識ズレ → ヒアリング過剰 → 業務離脱**」リスクが指摘され、Req 2 に AC #5 (通知配信) / #6 (変更履歴 view) / #7 (最新スキーマ確認済フラグ) が追加された。本リサーチは通知チャネルの選定と Delta Detector pipeline 内の flag 配置を決める。
- **Options Considered**:
  1. **Discord webhook（既存 bot に乗らず webhook 単独）** — AI Club は `personal-hub/ai-club/discord-bot` で bot を運用中だが、本 spec の通知は **bot を経由せず webhook 単独**で送る。bot 障害との疎結合 + 一方向依存 + Key Vault で URL 管理。チャネル名は `#hack-schema-updates` を新規想定（既存通知チャネル再利用も可、ID はハードコードせず config 化）。
  2. Microsoft Teams Adaptive Card — KPMG が Teams 主体である点で本命候補だが、ハッカソン期間中の Graph API 認可整備コストが大きく、proxy 組織での実装としては overspec。Follow-up で検討。
  3. Polling（Chat UI 側で定期的に `GET /schemas/history` を叩く） — webhook 設定不要だが、通知の即時性に欠け、ヒアリング過剰の抑制効果が弱い。AC #7 の banner と組み合わせる二段構えにすると却って複雑化。
- **Recommendation**: **Option 1（Discord webhook 単独）**。さらに AC #7 の最新スキーマ確認済フラグを Delta Detector pipeline の直前（Schema Revision Gate）に配置し、`dialogue_turns.schema_revision_seen_at` / `schemas.revision_id` の照合 + banner ack 受信で `schema_revision_seen_at` を更新する設計を採用（design.md §4.6）。
- **Sources / 確認**:
  - Discord Webhook 仕様（同期 POST、Rate limit 30 req/min/channel） — 本通知量（schema 更新 1 マス当たり週数件想定）で余裕
  - 既存 bot コードと干渉しないことは `personal-hub/ai-club/discord-bot` の channel handler を読まずとも、webhook URL を独立分離するだけで担保可能
  - PII scrubbing は Req 16.6 で AC 化済、通知 payload にも適用
- **Implications**:
  - Req 17.2 に Discord webhook URL を Key Vault 管理対象として明記済
  - design.md に `Notification Dispatcher` component を新設、Schema Manager Agent の `schema.updated` event を subscribe する設計に統合
  - tasks.md 起票時、webhook URL 4 種（schema_updates / pending_review / expired / cost_alert）をすべて config item として扱う
- **TODO（low-priority）**: Teams Adaptive Card オプションは Follow-up 列に置き、reviewer feedback で「Discord だと業務ユーザーが見ない」judgment が出たら昇格判定

### MVP 境界の決定 — Sotaro 承認 caveat への応答（2026-05-25 追加）

- **Context**: 2026-05-25 Sotaro 承認時のコメント「**want/must が要件に混在している。spec-driven の build → review → adjust サイクルで吸収するのが良い**」。本リサーチはこの caveat を design に落とし込む方針を決める。
- **Options Considered**:
  1. **Spec 段階で want/must を先回りに削る**（要件を Must / Should / Could で再ラベル付け） — 危険。persona-driven v2 で苦労して導出した独立要件（B5 / C4 / Persona A JTBD / R2 AC #5-7）を「Could」に降格すると、再昇格時に design 再生成コストが嵩む。Daichi が close した review session の合意基盤も壊す。
  2. **MVP 境界を design に明示する「今回ビルド」vs「Follow-up」表で吸収**（採用） — spec の構造を保ったまま design 上で line を引く。機能レビュー時にメトリクスを根拠に Follow-up 列を昇格／降格でき、Sotaro 提案の「build → review → adjust」サイクルそのもの。
  3. spec を MVP 用と Phase 2 用に分割 — `umbrella spec を作らない`（structure.md What NOT to do）に反する。
- **Recommendation**: **Option 2**。design.md §1「MVP 境界」表に「今回ビルド = M2-M8」「Follow-up = M9-M12 機能レビュー後判定」の二列で全主要レイヤーを並べる。Follow-up 列の項目は tasks.md 起票時に **チケットとして起票するが MVP マイルストーンに入れない** 運用ルールも明記。
- **Implications**:
  - design.md §1 が新規追加
  - tasks.md 生成時に「MVP マイルストーン」と「Follow-up backlog」のラベル分離が必要
  - decisions.md D1（検索 SPA）/ D2（2nd spec）は MVP 境界表に取り込まれた（Follow-up 列に明示）

### MAF 1.0 GA / Foundry Workflow agent preview 状況確認（2026-05-25、部分検証）

- **Context**: design.md の technology stack で「MAF 1.0 GA (2026-04-03)」「Foundry Workflow agent preview」「swedencentral リージョン提供」を前提に置いている。Sotaro 承認後、これらが正しく一次資料で裏取りできるかを再確認する。
- **Verification attempted**:
  - **MAF 1.0 GA**: `azure-agent-platform-decision.md` 内で 2026-04-03 GA を一次資料引用済。本 research では再検証せず既存リサーチを参照。
  - **Foundry Workflow agent preview のリージョン**: Week 1 flag day (2026-05-18) で実機検証する D4 の主題。本日（2026-05-25）時点で flag day 結果が `decisions.md` の Closed Decisions に反映されていないため、**「TODO: 2026-05-18 flag day 結果を decisions.md D4 に追記、それを本 research に取り込む」** とする。
  - **WebFetch/WebSearch 検証**: 本日のリサーチ枠ではツール起動コストと cache 影響を勘案し、上記 2 点はリンク先既存ドキュメントの再読で代替。reviewer feedback で「最新の preview status を踏まえた区分が必要」と出たら別 session で WebFetch を回す。
- **Implications**:
  - design.md §2.4 の Notes 列に「swedencentral 提供状況は research.md 2026-05-25 ログ参照」と記載
  - tasks.md でも `D4` の状態を確認する task を tech stack 確定の prerequisite に置く

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Semantic Kernel 単体 + Container Apps | SK Process Framework で orchestration、HITL は自前 | 既知の枠組み | MAF 1.0 リリースで継続性に疑問、HITL 自前実装コスト高 | 却下 |
| MAF 1.0 単体 + Container Apps | SK + AutoGen 統合後継、`RequestInfoEvent` で HITL | 単一 SDK で記述、Foundry 無しで完結 | orchestration の宣言性が低い、checkpoint 機構を自前実装 | バックアップ案 |
| **Foundry Workflow + MAF + BYO Cosmos** | Foundry が orchestration / HITL / checkpoint を提供、MAF は SDK | HITL pause-resume と長期 thread 永続化が標準、token + tool のみ課金 | Workflow agent / Hosted agent は preview、swedencentral 提供は flag day 確認 | **採用** |
| AWS Bedrock 移植 | 比較対照のみ | – | hackathon Azure 縛りで非該当 | 却下 |

## Design Decisions

### Decision: Foundry Workflow agent (preview) を MVP の orchestration に採用、MAF を SDK 層に据える

- **Context**: HITL pause-resume / 長期 thread 永続化 / 4 agent + Notification Dispatcher orchestration / 6 週 / $200 / agent tracing を全て満たす必要
- **Alternatives Considered**: (1) SK 単体 + 自前 HITL、(2) MAF + Container Apps 直接、(3) Foundry + MAF + BYO Cosmos
- **Selected Approach**: (3)
- **Rationale**: Foundry は本体無料で token + tool のみ課金、BYO Cosmos で conversation state を可視化可能、per-agent Entra identity / App Insights tracing 標準。MAF コードは Container Apps へ移植可能なため preview リスクヘッジ可
- **Trade-offs**: preview 機能依存（breaking change リスク）↔ 自前実装の工数削減
- **Follow-up**: Week 1 (2026-05-18) flag day 結果を decisions.md D4 に反映、本 research に取り込む（TODO）

### Decision: 正誤判定は GraphCheck 型 MVP、冷起動期は FactCheck 型 3 LLM 投票で補強

- **Context**: 冷起動期は corpus がほぼ空のため atomic claim 整合性照合が機能しない
- **Selected Approach**: GraphCheck メイン + FactCheck (corpus < 30 件時のみ) 併用
- **Rationale**: corpus 規模で自動的に判定方式を切替えればコストと精度のバランスが取れる
- **Trade-offs**: ロジック複雑化 ↔ 冷起動失敗回避
- **Follow-up**: 閾値 30 件は実測でキャリブレーション

### Decision: 重み付けは MVP では LLM 自己批評 (A) のみ、B/C は Phase 2/3 段階導入

- **Selected Approach**: 段階導入
- **Rationale**: MVP で空回りせず実装範囲を絞れる
- **Follow-up**: Phase 2 で EffiARA 試行、Phase 3 で β(t) 減衰の γ を環境変数化

### Decision: 多マス対応は partition key `{sector}#{unit}` 単一設計、AI Search index は 1 本

- **Selected Approach**: Cosmos / AI Search ともに 1 リソースで sector + unit を filter
- **Rationale**: マス追加時 schema 投入のみで稼働

### Decision: ヒアリングは Kunumi 5-step に 5W1H を埋込み、ChatExtract で confirmation

- **Selected Approach**: Kunumi 5-step の「質問」ステップで 5W1H を生成、回答後 ChatExtract 型「この理解で合っていますか?」を 1 回挟む
- **Rationale**: hallucination 抑制（Nature 2024）、Kunumi の self-critic でヒアリング継続/切替を自動判定
- **Follow-up**: 5 ターン上限の妥当性は実測

### Decision: Schema 更新通知は Discord webhook 単独配信（2026-05-25）

- **Context**: Req 2 AC #5/#6/#7 追加に伴う通知チャネル選定
- **Alternatives Considered**: (1) Discord webhook 単独、(2) Teams Adaptive Card、(3) Polling のみ
- **Selected Approach**: (1)
- **Rationale**: AI Club 既存 bot との疎結合、認可整備不要、即時配信、Key Vault で URL 管理しハードコード回避
- **Trade-offs**: KPMG 本番想定の Teams 主流とは乖離（Follow-up で Teams 化検討） ↔ ハッカソン期間内の実装容易性
- **Follow-up**: reviewer feedback で「業務ユーザーが Discord を見ない」judgment が出たら Teams 移行

### Decision: MVP 境界は design.md §1 表で明示、spec 段階で want/must を先回り削減しない（2026-05-25）

- **Context**: Sotaro 承認 caveat「want/must 混在は spec-driven build → review → adjust サイクルで吸収」
- **Alternatives Considered**: (1) spec で先回り削減、(2) design の MVP 境界表で吸収、(3) spec を MVP/Phase 2 に分割
- **Selected Approach**: (2)
- **Rationale**: persona-driven v2 で苦労して導出した独立要件を spec で降格すると再昇格時のコストが大きい。design 上で「今回ビルド」と「Follow-up」を線引きする方が改修サイクルに乗りやすい
- **Trade-offs**: design.md が長くなる ↔ spec 構造保持 + Sotaro caveat への直接応答
- **Follow-up**: 機能レビュー後（M9-M12）に Follow-up 列のメトリクスを基に昇格／降格判定

## Risks & Mitigations

- **Foundry Workflow agent preview の breaking change** — MAF を Container Apps に直接デプロイするバックアップ案、コード移植可能
- **swedencentral リージョンで Foundry Hosted agent 未提供** — Container Apps 直接デプロイにフォールバック、AOAI のみ swedencentral 流用。Week 1 flag day で確定
- **Schema 更新通知が業務ユーザーに届かず認識ズレ（Daichi 5/24 review、2026-05-25 新規）** — Discord webhook + Hearout 起動前 banner の二段構え（design.md §4.6）。reviewer feedback で「弱い」judgment が出たら Teams 移行
- **LLM 自己批評の過大評価** — Phase 2 で複数 LLM 平均化を検討、reviewer による補正でカバー
- **冷起動期 corpus 不在で正誤判定が機能しない** — FactCheck 3 LLM 投票 + 人手 seed corpus
- **5/14 後の POC マス変更** — partition key 設計でマス変更時の影響を schema 再投入に限定
- **予算 $200 超過** — `sector-unit-candidates.md` の Tier A-F 削減候補と App Insights alert で段階縮退
- **want/must 混在の解消遅延** — MVP 境界表 + 改修サイクルで吸収（Sotaro caveat 2026-05-25）

## References

- [Microsoft Agent Framework 1.0 GA Announcement](https://devblogs.microsoft.com/foundry/) — 2026-04-03 GA（azure-agent-platform-decision.md 内に詳細）
- [Microsoft Foundry Agent Service docs](https://learn.microsoft.com/azure/ai-services/agents/) — Workflow / Prompt / Hosted agent 区分
- [Discord Webhooks documentation](https://discord.com/developers/docs/resources/webhook) — 通知配信仕様
- [Kunumi arXiv 2507.03811](https://arxiv.org/abs/2507.03811) — self-critique + 5-step protocol
- [EffiARA arXiv 2410.14515](https://arxiv.org/html/2410.14515v1) — annotator reliability
- [GraphCheck PMC12360635](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360635/) — atomic claim + KG path
- [FactCheck SIGIR 2025](https://www.dei.unipd.it/~silvello/papers/2025-SIGIR_Demo_LLM.pdf) — 3 LLM ensemble
- [ChatExtract Nature 2024](https://www.nature.com/articles/s41467-024-45914-8) — follow-up confirmation
- PKAI (BISE 2025) — SECI multi-agent 19 design requirements（本文精読 TODO）
