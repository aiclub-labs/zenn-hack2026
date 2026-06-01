# Requirements Document

## Project Description (Input)

特定セクター×ユニットの業務対話を **Microsoft Agent Framework 1.0**（2026-04-03 GA、
Semantic Kernel + AutoGen 統合後継）ベースの multi-agent が監視し、admin が事前定義した
「欲しいデータ項目」スキーマと、人間の入力 / AI の出力の差分を暗黙知として検知する。
差分閾値超で 5W1H ヒアリングループを起動し、自由回答を構造化 record に形式化、
重み付け（自己批評スコア / アノテータ信頼度 / 公開情報照合の組合せ）で正誤判定したうえで
Azure AI Search の corpus に登録する。次回対話では蓄積済 record を参照して AI 応答に反映する。

**MVP スコープ**:
- 必達: Delta Detector + Hearout Agent (5W1H) + Formalization HITL + 次回対話での参照
- nice-to-have: 検索 SPA
- 削除: push 朝刊配信

**対象ドメイン（セクター × ユニット マトリクス前提）**:
- 想定組織: 8 セクター（業界軸: 製造 / 金融 / 公共 等）× 10 ユニット（領域軸: 戦略 / ビジネスイノベーション / テクノロジー / サステナビリティ 等）
- ハッカソン POC スコープ: マトリクスから **1-2 マス** をピックアップして実装（例: 「戦略ユニット × 特定セクター」での人材マッチング）
- アーキテクチャ要件: **将来の多マス展開（組織全体ロールアウト）に対応する設計**とする。MVP では 1-2 マスのみ稼働だが、スキーマ管理 / corpus index / agent orchestration はマス単位で水平展開可能な構造にする
- 対象マスの最終確定: 5/14 セッション以降

**Azure 構成（想定、リサーチ #2 反映）**:
- **Microsoft Foundry Agent Service** — agent runtime（本体無料、token + tool 課金のみ）。Workflow agent (preview) で 4 agent orchestration + HITL を宣言的に記述
- **Microsoft Agent Framework 1.0** — agent SDK。Foundry 不採用時のバックアップは MAF を Container Apps に直接デプロイ
- AOAI: gpt-4o (Hearout/形式化) + gpt-4o-mini (差分スコアリング)、既存 swedencentral リソース流用
- AI Search Basic（corpus index 1 本）
- Cosmos DB Serverless（**BYO conversation state** / スキーマ / HITL ログ / corpus メタデータ）
- Container Apps（既存環境、**custom tool / MCP webhook ホスト**として活用、3 SPA shell も同居）
- App Insights / Entra ID（scaffold 済、agent tracing + per-agent identity に直結）

**予算**: 6 週で $143 / $200（バッファ $57）

**前提カード**: `../../../docs/architecture-cards/idea-f-dialogue-monitoring.md`

**チーム制約**:
- 全ドキュメント日本語生成（チームメンバーの一部が英語に不慣れ）
- 3-phase 承認ワークフロー（Requirements → Design → Tasks → Implementation）に従う

## 確認ポイント（requirements 生成前に揉む / design 前に潰す）

1. **Agent orchestration プラットフォーム**（2026-05-12 リサーチ #2 完了）:
   **Microsoft Foundry Agent Service (Workflow agent, preview) + MAF 1.0 + BYO Cosmos DB のハイブリッド構成**
   を採用候補に確定。バックアップは **MAF を Container Apps 直接デプロイ + Prompt agent のみ Foundry 利用**。
   **Week 1 終了時点 (2026-05-18) で flag day を設け、Hosted agent (preview) の挙動を実機検証してから最終判断**。
   詳細は `../../../docs/research/azure-agent-platform-decision.md`。
2. **正誤判定方式の具体仕様**: フラグ / 多数決 / 公開情報照合の組合せをどう設計するかは、
   **暗黙知形式化システムにおける AI 活用の先行事例リサーチ**を完了してから決定する。
   requirements 段階では「複数ソースの重み付き集約」程度の抽象度に留め、具体方式は design フェーズで確定。
   想像ベースの spec 化は禁止。
3. **次回対話参照のスコープ**: 同一ユーザーのみ参照 / 同一マス内全ユーザー参照 / マス横断参照 のどれを採るか、プライバシー・NDA cascade との関係で要決定（design 前）。

## リサーチ TODO（design フェーズ前に完了させる）

- [x] **暗黙知形式化システムの先行事例**（2026-05-12 完了） → `../../../docs/research/tacit-knowledge-ai-prior-art.md`
- [x] **Azure Agent Platform 選定**（2026-05-12 完了） → `../../../docs/research/azure-agent-platform-decision.md`。Foundry + MAF ハイブリッド推奨、Week 1 flag day で最終確定
- [ ] PKAI 論文本文（19 件の design requirement）の精読 — ヒアリング設計の網羅性チェック（design フェーズ前）
- [ ] エンタープライズ製品（Microsoft Copilot for Knowledge / Notion AI / Guru / Bloomfire）の暗黙知扱いの一次資料調査 — 差別化ストーリー強度の検証
- [ ] Foundry Hosted agent の swedencentral リージョン提供状況確認（Week 1 実機検証で潰す）
- [ ] Free Trial 下での Hosted agent enable 可否確認（5/26 PAYG 移行前の制約整理）

## リサーチ結論を踏まえた設計ベースライン（2026-05-12）

先行事例リサーチ（[research/tacit-knowledge-ai-prior-art.md](../../../docs/research/tacit-knowledge-ai-prior-art.md)）の結論を spec 補完用ベースラインとして記録。**requirements EARS 化と design 段階で具体仕様に展開**する。

### 正誤判定方式

| 段階 | 方式 | 出典 |
|------|------|------|
| MVP | **GraphCheck 型**: 入力を atomic claim に分解 → corpus との一致をスコア化 | [GraphCheck PMC12360635](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360635/) |
| 冷起動期併用 | **FactCheck 型**: 3 LLM アンサンブル投票で合議 | [FactCheck SIGIR 2025](https://www.dei.unipd.it/~silvello/papers/2025-SIGIR_Demo_LLM.pdf) |
| 将来オプション | **Web/KG ハイブリッド**: Wikipedia / Bing grounding にフォールバック | [arXiv 2511.03217](https://arxiv.org/html/2511.03217) |

### 重み付け方式（3 層積）

| 層 | 方式 | 投入段階 | 出典 |
|----|------|----------|------|
| A | **LLM 自己批評スコア (0-10)**: 入力の確信度を LLM 自身に採点 | MVP 必達 | [Kunumi arXiv 2507.03811](https://arxiv.org/abs/2507.03811) |
| B | **アノテータ信頼度 (EffiARA)**: ユーザー × topic の過去 agreement から信頼度 | Phase 2（複数人入力蓄積後） | [EffiARA arXiv 2410.14515](https://arxiv.org/html/2410.14515v1) |
| C | **Provenance 時間減衰**: β(t) = β₀ e^(-γt) で古い知識を減衰 | Phase 3（鮮度管理要件化後） | Kunumi 論文 |

最終重み = A × B × C の積。MVP は A のみ。

### 閾値設計のたたき台

- 暗黙知ギャップ検知: AI 出力の self-critic score < **5** でヒアリングトリガ
- 形式化採用（corpus 投入）: 重み付き合成スコア ≥ **0.7**
- 正誤判定で reject: atomic claim 整合性スコア < **0.4**
- すべてキャリブレーション前提（実測しながら調整）

### ヒアリングプロトコル

**Kunumi 5-step**（rapport → 質問 → 応答処理 → 自己批評 → 続行/切替）の「質問」ステップに
**5W1H を埋め込む**形を採用。抽出後は **ChatExtract 型の follow-up confirmation**
（[Nature 2024](https://www.nature.com/articles/s41467-024-45914-8)）で hallucination 抑制。

### Agent 構成の理論的根拠 + プラットフォーム実装

**理論面**: PKAI (BISE 2025) の SECI 各フェーズに専門エージェントを割当てる multi-agent 構成と整合。本 spec の「Schema Manager / Delta Detector / Hearout Agent / Formalization HITL」分離は PKAI 系譜（19 件の design requirement 本文は要精読）。

**プラットフォーム面**（リサーチ #2 結論）:
- **Foundry Agent Service Workflow agent (preview)** で 4 agent fan-out + HITL を YAML / graph で宣言的に記述
- **MAF 1.0 の `RequestInfoEvent` / `ToolApprovalRequestContent`** が 5W1H ヒアリング / 形式化承認の pause-resume を標準機能でカバー → HITL の自前実装不要
- **チェックポイント機構**: pending request を含む `AgentThread` を JSON で Cosmos に永続化 → 長期対話セッションの中断・再開が標準対応
- **per-agent Microsoft Entra identity** で agent ごとに分離した認証 / 監査が可能
- **App Insights 連携** で agent tracing が標準 dashboard で見える
- バックアップ: Foundry preview 機能が詰まったら、同じ MAF コードを Container Apps に載せ替え可能（converged runtime のため）

### 差別化ストーリー

Glean 等のエンタープライズ製品は **explicit knowledge の検索 / 集約が主軸**で、
対話差分からの暗黙知抽出層は明確に埋められていない（公開資料ベース）。
本プロジェクトの差別化ポイントは「対話差分検知 + 5W1H ヒアリングによる externalization の自動化」自体。

### 既知リスク

- **LLM 自己批評の過大評価**: 複数 LLM での self-critic 平均で軽減検討（design 段階で詰める）
- **冷起動期の閾値ぶれ**: 初期 corpus 不在で正誤判定が機能しにくい → FactCheck 型併用と人手 seed corpus でカバー
- **5W1H 専用 LLM プロンプト研究の不在**: Kunumi 5-step に埋め込む方針で進めるが、独自 follow-up rule の必要性は design 段階で判断

## Introduction

本 spec は、特定セクター×ユニットに属する業務対話を AI agent が監視し、
人間の入力と AI の出力の差分から暗黙知を抽出して形式知化する MVP の要件を定義する。
Microsoft Agent Hackathon 2026 提出物として 6 週間で実装し、
対象組織 (例: AI 推進部門)の組織的暗黙知活用の POC として位置付ける。
Microsoft Agent Framework 1.0 と Foundry Agent Service Workflow agent を採用し、
HITL ループを標準機能で構成する。
先行事例（Kunumi arXiv 2507.03811 / EffiARA / GraphCheck）の手法を採用基準として援用する。

## Requirements

### Requirement 1: 暗黙知スキーマの事前定義

**Objective:** As an admin (対象組織 (例: AI 推進部門)の知識管理担当), I want セクター×ユニット単位で「捕捉したい暗黙知データ項目」を事前定義する, so that 対話監視中のエージェントが暴走せずスキーマに沿った差分のみ検出できる

#### Acceptance Criteria
1. When admin がスキーマ定義 UI から新規 schema field を登録する, the system shall `{field_name, description, sector, unit, expected_value_type, example, ai_baseline_assumption}` を Cosmos DB に upsert する
2. When schema field が更新される, the system shall `updated_at` と `revision_id` を増分し、過去 revision は監査ログとして保持する
3. The system shall 1 セクター×ユニットあたり最低 5 件、上限 30 件の schema field を登録できる
4. If schema field が `is_active = false` でマークされる, then the system shall Delta Detector の照合対象から自動的に除外する
5. Where セクター×ユニット を切替える, the system shall そのマスに紐づく schema field のみを画面に表示する

### Requirement 2: 業務対話の監視とログ取得

**Objective:** As a 業務ユーザー (PM / 営業), I want AI との対話が裏で監視・ログ化される, so that 後段の差分検知エージェントが入出力ペアを参照できる

#### Acceptance Criteria
1. When ユーザーがチャット UI から入力を送信する, the system shall `{user_id, sector, unit, turn_id, timestamp, role: "user", content}` を Cosmos の `dialogue_turns` コレクションに append する
2. When AI が応答を生成する, the system shall 同 turn 内に `role: "assistant", content, self_critic_score (0-10)` を記録する
3. The system shall すべての対話ターンに `session_id` を付与し、同一セッション内ターンを時系列で取得可能にする
4. If ユーザーがプライバシーフラグ `redact = true` を立てた turn を送信する, then the system shall その turn の content を Cosmos に保存せずメタデータのみ保持する
5. While 対話が進行中, the system shall App Insights に `dialogue.turn.recorded` メトリクスを emit する

### Requirement 3: 入出力差分の検知（Delta Detector）

**Objective:** As a system, I want 各対話ターンを schema と照合し、暗黙知候補となる差分を自動検知する, so that 後段のヒアリングを必要な場面でのみ起動する

#### Acceptance Criteria
1. When 新規 turn が記録される, the Delta Detector shall 該当セクター×ユニットの active schema fields すべてに対し差分スコアを計算する
2. The Delta Detector shall AI 応答の self-critic score (Kunumi 型 0-10) と user input の意味的距離（embedding cosine similarity）を組み合わせて差分スコアを算出する
3. When self-critic score < 5 かつ意味的距離が閾値（初期 0.4）を超える, the system shall 該当 schema field を「暗黙知ギャップ候補」としてマークし Hearout Agent にイベント emit する
4. If 同一 session 内で同一 schema field が連続 3 ターン以上ギャップ判定される, then the system shall 重複検知を抑制し最初のギャップのみヒアリング対象にする
5. The Delta Detector shall 検知判定根拠（self-critic score, distance, matched schema field id）を `delta_events` コレクションに保存する

### Requirement 4: 5W1H ヒアリングループ（Hearout Agent）

**Objective:** As a 業務ユーザー, I want AI から構造化された 5W1H 質問で暗黙知を引き出される, so that 頭の中の判断ロジックを言語化して残せる

#### Acceptance Criteria
1. When Delta Detector からギャップ通知を受ける, the Hearout Agent shall Kunumi 5-step protocol（rapport → 質問 → 応答処理 → 自己批評 → 続行/切替）に沿って対話を開始する
2. The Hearout Agent shall 質問ステップで schema field の `expected_value_type` に応じた 5W1H 質問（Why / When / Who / What / Where / How）を生成する
3. When ユーザー回答を受領する, the Hearout Agent shall ChatExtract 型 follow-up confirmation（「この理解で合っていますか?」）を 1 回挟んで hallucination を抑制する
4. If ユーザーが「スキップ」を選択する, then the Hearout Agent shall `outcome: skipped` を記録しヒアリングを終了する
5. The Hearout Agent shall 1 ヒアリングセッションで最大 5 ターンで打ち切り、回収済 5W1H 要素を `hearout_records` に保存する
6. While ヒアリングが進行中, the system shall 通常の業務対話 UI から modal で分離表示する

### Requirement 5: 重み付き形式化（Formalization）

**Objective:** As a system, I want ヒアリング結果を構造化 record に変換し信頼度重みを付与する, so that corpus 投入時の品質を担保する

#### Acceptance Criteria
1. When Hearout Agent が record 候補を出力する, the Formalization Agent shall LLM 自己批評スコア A (0-10) を必ず計算する
2. Where Phase 2 以降, the system shall アノテータ信頼度 B（EffiARA 系、ユーザー × topic の過去 agreement から sigmoid 化）を計算する
3. Where Phase 3 以降, the system shall Provenance 時間減衰 C（β(t) = β₀ e^(-γt)、γ は環境変数）を計算する
4. The system shall 最終重み = A × B × C の積で算出する。MVP は A のみ（B = C = 1.0）
5. If 最終重みが閾値 0.7 未満, then the system shall record を `pending_review` ステータスで保留する
6. When 最終重みが 0.7 以上, the system shall record を HITL レビュー queue に投入する

### Requirement 6: HITL レビューと承認

**Objective:** As a レビュアー (PM 自身 or 知識管理担当), I want record 候補を承認・修正・拒否できる, so that corpus の品質を最終ゲートでコントロールできる

#### Acceptance Criteria
1. When レビューキュー に新規 record が入る, the system shall MAF の `RequestInfoEvent` で workflow を pause しレビュー UI に通知する
2. The レビュー UI shall record の `{5W1H 要素, schema field, 重み breakdown (A/B/C), 正誤判定スコア, 関連 dialogue turns}` を一覧表示する
3. When レビュアーが「承認」を選ぶ, the system shall record を `approved` にして corpus.upsert を発火する
4. When レビュアーが「修正」を選び編集する, the system shall 編集後の content を保存し、`reviewer_id, edited_at, edit_diff` を監査ログに記録する
5. When レビュアーが「拒否」を選ぶ, the system shall record を `rejected` にして `delta_events` の該当 field を 7 日間 cooldown する（同一ギャップの再ヒアリング防止）
6. If 24 時間以内にレビューが完了しない, then the system shall 該当 record を `expired` にし、レビュアーに Discord 通知を送る

### Requirement 7: 正誤判定（Truth Judgment）

**Objective:** As a system, I want 蓄積される暗黙知 record の論理整合性を corpus 全体に対して検証する, so that 矛盾や誤情報が形式知化されないようにする

#### Acceptance Criteria
1. When record が `approved` になる前段で, the system shall record 内容を atomic claim に分解する（GraphCheck 型）
2. The system shall 各 atomic claim に対し既存 corpus 内の類似 record を AI Search で検索し evidence path score を算出する
3. If atomic claim 整合性スコア < 0.4, then the system shall record を `conflict_detected` フラグ付きでレビュー UI に提示し人間判断を仰ぐ
4. Where corpus が薄い冷起動期（record 件数 < 30）, the system shall FactCheck 型の 3 LLM アンサンブル投票（gpt-4o / gpt-4o-mini / 同 gpt-4o 別 prompt）で補助判定を行う
5. The system shall 矛盾検知時の判定根拠（参照した既存 record id 群、各 LLM の判定）を `truth_judgment_logs` に保存する

### Requirement 8: 次回対話での corpus 参照

**Objective:** As a 業務ユーザー, I want 過去の暗黙知 record が次回以降の AI 応答に自然に反映される, so that 同じ暗黙知を毎回ヒアリングで取り直さなくて済む

#### Acceptance Criteria
1. When 業務ユーザーが新規対話ターンを送信する, the AI shall 該当セクター×ユニットの corpus から関連 record を AI Search で retrieval し回答コンテキストに注入する
2. The system shall retrieval されたレコードの引用 ID を AI 応答に明示する
3. Where ユーザー権限が schema field の `shareability` ラベルを満たさない, the system shall 該当 record を retrieval 対象から除外する
4. If 同一マス内で複数 record が同一 schema field に対し矛盾する, then the AI shall 重みが最も高い record を優先し、ユーザーに「他に N 件の異なる見解あり」と明示する
5. The system shall 各 retrieval イベントを App Insights に記録し、`record_referenced_count` 指標を corpus メタデータに反映する（利用度トラッキング）

### Requirement 9: 多マス対応設計（POC スコープ 1-2 マス）

**Objective:** As an architect (オペレータ), I want アーキテクチャがマス単位で水平展開できる, so that ハッカソン後の組織展開でも同コード資産を再利用できる

#### Acceptance Criteria
1. The system shall すべての永続化リソース（Cosmos collections、AI Search index）を `sector` + `unit` の複合キーで partition する
2. The system shall MAF agent 起動時に `target_sectors`, `target_units` を環境変数 / config で指定可能にする
3. When 新規マスを追加する, the system shall infra コード変更なく schema fields の Cosmos 投入のみで運用開始できる
4. Where ハッカソン MVP は 1-2 マスのみ稼働, the system shall 単一 Foundry workflow 定義で全マスを処理できる（マスごとの workflow 分岐は不要）

### Requirement 10: 観測性とテレメトリ

**Objective:** As an operator, I want agent 動作とコスト消費を可視化する, so that 予算 $200 の枯渇前にスコープ調整できる

#### Acceptance Criteria
1. The system shall MAF / Foundry の agent tracing を App Insights に自動 export する
2. The system shall 1 日 1 回 AOAI token 消費を集計し、累積 $120 (M8 burn-rate gate) と $150 (warning) でアラートする
3. While 各 agent が実行中, the system shall agent 名 / 経過時間 / トークン消費を App Insights `customMetrics` に emit する
4. If エラーが発生する, then the system shall stack trace + 直前の dialogue turn を Cosmos の `error_logs` に保存する

### Requirement 11: セキュリティと認証

**Objective:** As a 組織管理者, I want クライアント機密データが漏れない構造である, so that 合成 corpus とはいえ運用パターン上の脆弱性が残らない

#### Acceptance Criteria
1. The system shall すべての agent と Container Apps の認証を Entra ID + Managed Identity で行う（API キー直接利用は禁止）
2. The system shall AOAI / Cosmos / AI Search への接続文字列を Key Vault `kv-hack2026-tyu3o4` で管理する
3. Where ユーザーが `redact = true` フラグを立てる, the system shall 該当 turn の content を保存せずメタデータのみ保持する
4. The system shall Foundry Agent Service の per-agent Microsoft Entra identity 機能で、各 agent ごとに最小権限スコープを割当てる
5. If 認証エラーが発生する, then the system shall ユーザーに具体的なエラー詳細を返さず、汎用 5xx と内部ログのみ詳細化する

### Requirement 12: 予算管理と段階的スコープ

**Objective:** As an operator, I want 予算 $200 を超えないよう段階的にスコープ縮退できる, so that M13 teardown ゲートまで稼働を維持できる

#### Acceptance Criteria
1. The system shall 累積コスト消費を週次でレポートし、`../../../docs/research/sector-unit-candidates.md` の Tier A-F 削減候補と対応付けて閾値超過時に提案する
2. When 累積 $120 を超える, the system shall Tier A（公開情報照合カット）を operator に推奨する
3. When 累積 $150 を超える, the system shall Tier C（5W1H を 3W に縮退）+ Hearout Agent モデルを gpt-4o → gpt-4o-mini に切替提案する
4. The system shall Foundry Hosted agent の scale-to-zero 状態を idle 5 分で発動するよう設定する
