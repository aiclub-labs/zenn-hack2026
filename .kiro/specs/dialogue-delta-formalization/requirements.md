# Requirements Document

> 本ドキュメントは [`personas-stories.md`](./personas-stories.md) の Persona × User Story を**起点**として導出された要件定義書である。各 Requirement は `Source Story:` フィールドで導出元を明示する。

## Project Description (Input)

特定セクター×ユニットの業務対話を **Microsoft Agent Framework 1.0**（2026-04-03 GA、Semantic Kernel + AutoGen 統合後継）ベースの multi-agent が監視し、admin が事前定義した「欲しいデータ項目」スキーマと、人間の入力 / AI の出力の差分を暗黙知として検知する。差分閾値超で 5W1H ヒアリングループを起動し、自由回答を構造化 record に形式化、重み付け（自己批評スコア / アノテータ信頼度 / 公開情報照合の組合せ）で正誤判定したうえで Azure AI Search の corpus に登録する。次回対話では蓄積済 record を参照して AI 応答に反映する。

**MVP スコープ**:
- 必達: Delta Detector + Hearout Agent (5W1H) + Formalization HITL + 次回対話での参照
- nice-to-have: 検索 SPA
- 削除: push 朝刊配信

**対象ドメイン**:
- 8 セクター × 10 ユニットのマトリクスから 1-2 マスを POC スコープに選定
- アーキは多マス展開対応設計（partition key で水平展開）
- 業務フローの具体絞り込みは design 段階で再判断（2026-05-20 meeting 決定）

**Azure 構成**:
- **Microsoft Foundry Agent Service**（Workflow agent preview） — 4 agent fan-out + HITL を宣言的記述
- **Microsoft Agent Framework 1.0** — agent SDK、`RequestInfoEvent` / `ToolApprovalRequestContent` で HITL 標準実装
- AOAI: gpt-4o (Hearout / 形式化) + gpt-4o-mini (差分スコアリング)、swedencentral 流用
- AI Search Basic（corpus index 1 本）
- Cosmos DB Serverless（BYO conversation state / スキーマ / HITL ログ / corpus メタデータ）
- Container Apps（既存環境、custom tool / MCP webhook ホスト、3 SPA shell 同居）
- App Insights / Entra ID + Managed Identity

**予算**: 6 週で $143 / $200（バッファ $57）

**チーム制約**: 全ドキュメント日本語、3-phase 承認ワークフロー（Requirements → Design → Tasks → Implementation）

**参照**:
- Persona × User Story: [`personas-stories.md`](./personas-stories.md)
- リスク台帳: [`../../../docs/risks.md`](../../../docs/risks.md)
- アーキカード: [`../../../docs/architecture-cards/idea-f-dialogue-monitoring.md`](../../../docs/architecture-cards/idea-f-dialogue-monitoring.md)
- 採用基準リサーチ: [`../../../docs/research/tacit-knowledge-ai-prior-art.md`](../../../docs/research/tacit-knowledge-ai-prior-art.md), [`../../../docs/research/azure-agent-platform-decision.md`](../../../docs/research/azure-agent-platform-decision.md)

## 設計ベースライン

requirements の EARS 化・design 段階で具体仕様に展開するための先行事例ベースライン。

### 正誤判定方式

| 段階 | 方式 | 出典 |
|------|------|------|
| MVP | **GraphCheck 型**: 入力を atomic claim に分解 → corpus との一致をスコア化 | [GraphCheck PMC12360635](https://pmc.ncbi.nlm.nih.gov/articles/PMC12360635/) |
| 冷起動期併用 | **FactCheck 型**: 3 LLM アンサンブル投票で合議 | [FactCheck SIGIR 2025](https://www.dei.unipd.it/~silvello/papers/2025-SIGIR_Demo_LLM.pdf) |
| 将来オプション | **Web/KG ハイブリッド**: Wikipedia / Bing grounding にフォールバック | [arXiv 2511.03217](https://arxiv.org/html/2511.03217) |

### 重み付け方式（3 層積）

| 層 | 方式 | 投入段階 | 出典 |
|----|------|----------|------|
| A | **LLM 自己批評スコア (0-10)** | MVP 必達 | [Kunumi arXiv 2507.03811](https://arxiv.org/abs/2507.03811) |
| B | **アノテータ信頼度 (EffiARA)** | Phase 2 | [EffiARA arXiv 2410.14515](https://arxiv.org/html/2410.14515v1) |
| C | **Provenance 時間減衰** β(t) = β₀ e^(-γt) | Phase 3 | Kunumi 論文 |

最終重み = A × B × C の積。MVP は A のみ（B = C = 1.0）。

### 閾値設計（キャリブレーション前提）

- 暗黙知ギャップ検知: AI 出力の self-critic score < **5** でヒアリングトリガ
- 形式化採用（corpus 投入）: 重み付き合成スコア ≥ **0.7**
- 正誤判定で reject: atomic claim 整合性スコア < **0.4**

### ヒアリングプロトコル

**Kunumi 5-step**（rapport → 質問 → 応答処理 → 自己批評 → 続行/切替）の「質問」ステップに **5W1H を埋め込む**。抽出後は **ChatExtract 型 follow-up confirmation** ([Nature 2024](https://www.nature.com/articles/s41467-024-45914-8)) で hallucination 抑制。

---

## Introduction

本 spec は、特定セクター × ユニットに属する業務対話を AI agent が監視し、人間入力と AI 出力の差分から暗黙知を抽出して形式知化する MVP の要件を定義する。Microsoft Agent Hackathon 2026 提出物として 6 週間で実装し、KPMG AI 部の組織的暗黙知活用の POC として位置付ける。

### 用語: 暗黙知の定義（2026-05-20 meeting 決定）

「**自分の中で言語化できていないもの**」「**形式化されていない状態**」を本 spec における暗黙知と定義する。
- 言語化されていない判断パターン / 経験則 / 文脈依存の意思決定
- 「言語化はできるが普段していない（制約があって出ていない）」も含む
- 「世界中の誰も言語化していない」レベルではなく、**個人レベルで未形式化**の状態を主対象とする

### Persona 構成（[`personas-stories.md`](./personas-stories.md) §1 より）

| Persona | 役割 | 担当 Requirement 章 |
|---|---|---|
| **A: 知識管理者** (シゲル) | 暗黙知を**形式化したい人** | §A |
| **B: 業務ユーザー** (ハルカ) | 暗黙知を**借りる / 活用する人**（5W1H ヒアリング協力者でもある） | §B |
| **C: レビュアー** (タケシ) | C1-C3 はレビュー action のバリエーション（承認 / 編集 / 拒否）、**C4 は矛盾検知を担う人間** | §C |

### Requirement 構成

- **§A / §B / §C**: 各 persona の User Story から直接導出される **ユーザー対面要件**
- **§D 支援システム要件**: 複数 story を成立させるための **内部 agent / 処理** 要件（Delta Detector / Formalization / Truth Judgment 等）。`Supports:` で関連 story を明示
- **§E 横断 / 非機能要件**: 多マス対応 / 観測性 / セキュリティ / 予算

### リスク台帳との連動

[`../../../docs/risks.md`](../../../docs/risks.md) を参照。各 Requirement は緩和対象リスクを `関連リスク:` で明示する。

### 用語表（同名異義の symbol 分離）

| Symbol | 意味 | 参照 |
|---|---|---|
| `response_self_critic_score` | AI 応答に対する自己批評スコア (0-10) | Req 4 AC2, Req 12 AC2-5 |
| `record_self_critic_score` | Hearout 出力 record に対する自己批評スコア (0-10, = 重み層 A) | Req 13 AC1 |
| `embedding_distance_threshold` | user input embedding cosine 距離の閾値 (= 0.4) | Req 12 AC5, AC10 |
| `claim_consistency_threshold` | Truth Judgment の atomic claim 整合性スコア閾値 (= 0.4) | Req 14 AC4 |
| `response_self_critic_low / mid` | Delta Detector 2段判定の閾値 (3 / 5) | Req 12 AC4-5, AC10 |

---

## Requirements

# §A. Persona A（知識管理者 シゲル）の要件

### Requirement 1: 暗黙知スキーマの初期定義

**Source Story:** A1 (マス開設時のスキーマ初期定義)
**Objective:** As an admin (知識管理者), I want セクター×ユニット単位で「捕捉したい暗黙知データ項目」を事前定義する, so that 対話監視中の agent が暴走せずスキーマに沿った差分のみ検出できる
**関連リスク:** R-02（重み付け）, R-07（業務フロー絞り込み）

#### Acceptance Criteria

1. When admin が Admin UI から新規 schema field を登録する, the system shall `{field_name, description, sector, unit, expected_value_type, example, ai_baseline_assumption}` を Cosmos DB の `schemas` collection に upsert する
2. The system shall 1 セクター×ユニットあたり最低 5 件、上限 30 件の schema field を登録できる
3. Where セクター×ユニットを切替える, the system shall そのマスに紐づく schema field のみを画面に表示する
4. When schema field が登録 / 更新される, the system shall `revision_id` を増分し、Delta Detector が次 turn から照合対象に含める
5. The Admin UI shall schema field 登録中に業務側対話を**停止せず**動作する（Persona A JTBD「業務を止めずに定義・更新したい」を満たす）

### Requirement 2: スキーマの段階的調整と監査

**Source Story:** A2 (スキーマの段階的調整)
**Objective:** As an admin, I want 既存 schema field を業務側フィードバックに応じて段階的に調整する, so that 過剰検知や検知漏れを運用しながら是正できる
**関連リスク:** R-02

#### Acceptance Criteria

1. When admin が schema field を編集する, the system shall 新 `revision_id` で upsert し、過去 revision を **監査ログとして保持** する（削除不可）
2. If admin が `is_active = false` に設定する, then the system shall 次 turn から Delta Detector の照合対象から自動的に除外し、reject 率指標を停止状態として更新する
3. The system shall 各 schema field の reject 率 / 検知回数を Admin UI に表示し、過剰検知の判定材料を提供する
4. When admin が is_active 状態を再度切替える, the system shall 切替時刻と理由（任意入力）を `schema_audit_log` に記録する

### Requirement 3: 横展開（新マス追加）

**Source Story:** A3 (マス追加 = 横展開)
**Objective:** As an admin, I want POC 成功マスの仕組みを別ユニットに即日展開する, so that 組織全体への段階的ロールアウトを工数最小で実現できる
**関連リスク:** R-07

#### Acceptance Criteria

1. When admin が新マス（新 sector×unit ペア）の schema を Cosmos に投入する, the system shall **infra 変更なし**で Day-1 から運用開始する（partition key 自動分離 / agent 設定のみで稼働）
2. The system shall 単一 Foundry workflow 定義で全マスを処理する（マスごとの workflow 分岐は不要）
3. Where 既存マスの schema を新マスに複製する, the Admin UI shall 一括 import 機能を提供する
4. The system shall マス間で record / corpus が混在しないことを partition key で保証する

---

# §B. Persona B（業務ユーザー ハルカ）の要件

### Requirement 4: 業務対話の通常実行とログ取得

**Source Story:** B1 (通常対話 / gap なし)
**Objective:** As a 業務ユーザー, I want AI チャットを通常通り利用しつつ裏で対話が記録される, so that 後段の暗黙知抽出と次回参照が成立する
**関連リスク:** R-06（無意識利用 vs 意識協力）

#### Acceptance Criteria

1. When 業務ユーザーが Chat UI から入力を送信する, the system shall `{user_id, sector, unit, turn_id, timestamp, role: "user", content}` を `dialogue_turns` collection に append する
2. When AI が応答を生成する, the system shall 同 turn に `role: "assistant", content, self_critic_score (0-10)` を記録する
3. The system shall すべての対話ターンに `session_id` を付与し、同セッション内ターンを時系列で取得可能にする
4. While 通常対話が継続する, the system shall ユーザー側の UI 操作 / レイテンシに**業務阻害となる介入**を追加しない（無意識利用を担保）
5. The system shall App Insights に `dialogue.turn.recorded` メトリクスを emit する

### Requirement 5: 5W1H ヒアリング介入

**Source Story:** B2 (暗黙知ヒアリング介入)
**Objective:** As a 業務ユーザー, I want AI 応答が弱い turn でのみ 5W1H 質問を受け、業務リズムを崩さず暗黙知を形式化される, so that 自分の経験を AI に教える手間が最小化される
**関連リスク:** R-01（供給側インセンティブ）, R-06

#### Acceptance Criteria

1. When 該当 turn が「暗黙知ギャップ候補」と判定される（Req 12 参照）, the Hearout Agent shall Kunumi 5-step protocol（rapport → 質問 → 応答処理 → 自己批評 → 続行/切替）で modal を起動する
2. The Hearout Agent shall 質問ステップで schema field の `expected_value_type` に応じた 5W1H 質問（Why / When / Who / What / Where / How）を生成する
3. When ユーザー回答を受領する, the Hearout Agent shall ChatExtract 型 follow-up confirmation（「この理解で合っていますか?」）を 1 回挟む
4. If ユーザーが「スキップ」を選択する, then the Hearout Agent shall `outcome: skipped` を記録しヒアリングを終了する（**業務阻害ゼロを担保**）
5. The Hearout Agent shall 1 ヒアリングセッションを **最大 5 ターンで打ち切り**、回収済 5W1H 要素を `hearout_records` に保存する
6. While ヒアリング modal 表示中, the system shall 元の業務対話 UI を見える状態で残し、文脈を切らない
7. The system shall ヒアリング介入頻度を **1 日 1-3 回 / skip 率 ≤ 50%** を運用ターゲットとし、超過時は Delta Detector の閾値再キャリブレーション候補としてメトリクス記録する

### Requirement 6: 過去暗黙知の自然な参照

**Source Story:** B3 (過去暗黙知の自然な参照)
**Objective:** As a 業務ユーザー, I want 以前自分が形式化した record が次回対話で AI 応答に自然に反映される, so that 同じ説明を何度もしなくて済む
**関連リスク:** R-01

#### Acceptance Criteria

1. When 業務ユーザーが新規 turn を送信する, the AI shall 該当 sector×unit の corpus から関連 record を AI Search で retrieval し、回答コンテキストに注入する。**retrieval スコープは「同一 sector×unit 内」に限定し、マス横断検索は MVP では行わない**（Phase 2 で検討 / 確認ポイント #1 結論）
2. The AI 応答 shall retrieval された record の **引用 ID を明示**する（「前回△△と話したように」形式）
3. Where ユーザー権限が record の `shareability` ラベル（`private`: 本人のみ / `unit`: 同マス内全ユーザー / `public`: 同マス内全ユーザー、Phase 2 でマス横断候補）を満たさない, the system shall 該当 record を retrieval 対象から除外する
4. The system shall 各 retrieval イベントで `record_referenced_count` を corpus メタデータに加算する（**供給側への評価フィードバック = R-01 緩和**）
5. The system shall 引用 ID をクリックで dialogue turn 出典が確認できる UI を提供する

### Requirement 7: 機密案件の redact

**Source Story:** B4 (機密案件の redact)
**Objective:** As a 業務ユーザー, I want 守秘度の高い顧客名 / 案件コードを含む turn を redact できる, so that 機密情報が形式化対象にならない
**関連リスク:** (Persona B embed リスク 2 / 機密 turn redact 忘れ)

#### Acceptance Criteria

1. When ユーザーが redact フラグ `redact = true` を ON にして送信する, the system shall 該当 turn の `content` を Cosmos に保存せず**メタデータのみ**保持する
2. While redact = true の turn, the Delta Detector shall 当該 turn を照合対象から自動的に除外する
3. The system shall redact 状態を turn 単位で明示し、後から redact 解除はできない（誤投入を防ぐ不可逆設計）
4. If ユーザーが redact 忘れを後から発見する, then the system shall 該当 turn を retrospective に `redact = true` に変更でき、content を物理削除する（ベストエフォート、引用先 record があれば一緒に削除する）

### Requirement 8: 活用時の矛盾検知通知（B5 独立要件）

**Source Story:** B5 (矛盾検知時のユーザー通知)
**Objective:** As a 業務ユーザー, I want 同じ schema field に対し過去 record が複数の異なる見解を持つ場合に AI 応答内で明示される, so that 自分が情報源の揺れを認識して判断できる
**関連リスク:** R-03 (活用時の矛盾検知 = (b) パターン)

#### Acceptance Criteria

1. When AI が retrieval した record 集合に同 schema field で異なる見解が複数 (≥ 2) 含まれる, the AI 応答 shall **重みが最も高い record を優先**しつつ「他に N 件の異なる見解あり」と明示する
2. When ユーザーが「他の見解を見る」を選択する, the system shall 矛盾する record を並列表示し、それぞれの出典 turn / 重み / 投稿日時を表示する
3. The system shall 活用時矛盾検知イベントを `truth_judgment_logs` に `pattern: "activation-time"` で記録する（Req 14 の入力時矛盾検知と区別）
4. Where ユーザーが矛盾を解消する目的で追加情報を入力する, the system shall その turn を新規ヒアリング対象として扱う（Req 5 の連動）

---

# §C. Persona C（レビュアー タケシ）の要件

### Requirement 9: レビュー action（承認 / 編集 / 拒否）

**Source Story:** C1, C2, C3（**いずれか 1 つを選択するバリエーション**、2026-05-20 meeting 決定）
**Objective:** As a レビュアー, I want record 候補に対し 1 record あたり 2 分以内に承認 / 編集 / 拒否のいずれかを選択する, so that 組織資産化に品質ゲートが入る
**関連リスク:** (Persona C embed リスク 1 / 重み breakdown 不可解 → 全件承認)

#### Acceptance Criteria

1. When レビューキューに新規 record が入る, the system shall MAF `RequestInfoEvent` で workflow を pause しレビュー UI に通知する
2. The レビュー UI shall record の **{5W1H 要素 / 重み breakdown (A × B × C) / 関連 dialogue turns / Truth Judgment 結果バッジ (`supported`=緑 / `novel`=黄 / `conflict`=赤)}** を 1 画面で表示する
3. When レビュアーが「**承認**」(C1) を選ぶ, the system shall record を `approved` にして corpus.upsert を発火する（Truth Judgment は Req 14 で**前段実行済**）。`conflict` バッジ付き record は本 AC ではなく Req 10 の専用フローに従う
4. When レビュアーが「**編集**」(C2) を選び content を修正する, the system shall `{reviewer_id, edited_at, edit_diff}` を監査ログに記録し、編集後 record を Req 14 Truth Judgment に**再投入**して新バッジを得てから本 Req 9 のループに戻す
5. When レビュアーが「**拒否**」(C3) を選ぶ, the system shall record を `rejected` にし、該当 **schema field × user ペア**に対し **7 日 cooldown** を設定する（再ヒアリング防止）
6. The レビュー UI shall 各 record の処理時間を計測し、**中央値 ≤ 2 分** を運用ターゲットとして表示する
7. The 重み breakdown UI shall 各層 (A/B/C) の数値と意味を tooltip 表示する（**重み不可解で全件承認するリスク緩和**）
8. The system shall `allow_self_approval` フラグを sector×unit 単位で持つ。MVP/デモ環境は **`false`**（自己生成 record の自己承認禁止、別 reviewer pool へ自動 routing）、運用環境は **`true`** だが `self-critic ≥ 8` かつ Truth Judgment バッジが `supported` の場合のみ自己承認を許す
9. The system shall **「自己承認率」を週次 dashboard に表示し、> 30% で warning** を出す（案D / 確認ポイント #2 結論）
10. When レビュアーが record をレビュー UI で開く, the system shall record に **`locked_by, lock_expires_at (= 取得時刻 + 5 分)`** を設定する。他レビュアーには grey out 表示。TTL 経過で自動解放、解放後の取得は先勝ち
11. If レビュー処理時間の週次中央値が **3 分** を超える, then the system shall reviewer UI を「優先 3 件のみ表示」モードに自動切替し、admin に warning を出す

### Requirement 10: 矛盾検知時の人間判断（C4 独立要件）

**Source Story:** C4 (矛盾検知時の人間判断)
**Objective:** As a レビュアー, I want 入力時に矛盾フラグが立った record について、矛盾相手の既存 record と並列表示で比較判断する, so that 組織として整合性のある corpus を維持できる
**関連リスク:** R-03 (入力時の矛盾検知 = (a) パターン)

#### Acceptance Criteria

1. When Truth Judgment (Req 14) が atomic claim 整合性スコア < 0.4 を返す, the system shall record を `conflict_detected` フラグ付きで **専用 review queue** に提示する（通常 review queue と区別）
2. The レビュー UI shall `conflict_detected` record と矛盾相手の既存 corpus record を **並列比較表示** する
3. When レビュアーが「新規 record を採用」を選ぶ, the system shall 既存 record を `superseded_by: {new_record_id}` でマークし、新 record を corpus に投入する
4. When レビュアーが「既存を維持」を選ぶ, the system shall 新 record を `rejected_due_to_conflict` にする
5. When レビュアーが「両方残す」を選ぶ, the system shall 両 record を `coexisting_views` 関係で紐付けて corpus 投入し、Req 8 (B5) の活用時通知の対象にする
6. The system shall 各 conflict resolution を `truth_judgment_logs` に `pattern: "input-time"` で記録する
7. The system shall conflict resolution 率 **≥ 80%（直近 30 日窓）** を運用ターゲットとし、未解決の `conflict_detected` 件数を Admin UI に表示する
8. When AC3 (`superseded_by`) または AC4 (`rejected_due_to_conflict`) で record 状態が変わる, the system shall `citation_audit_log` に新旧 record の対応を記録する。Req 6 AC5 で過去 AI 応答の引用 ID をクリックされたとき、superseded された record は **「この見解は更新されています → 最新 record にリンク」バナー** で誘導する

### Requirement 11: SLA 期限切れ運用

**Source Story:** C5 (SLA expired 通知)
**Objective:** As an operator (Persona A 兼任可), I want レビュー queue で 24h 放置された record の状態を可視化し再投入の判断ができる, so that 業務側 redo 負担を最小化できる
**関連リスク:** (Persona C embed リスク 2 / 24h SLA 超過 → expired → redo 負担)

#### Acceptance Criteria

1. The system shall レビュー queue 内の各 record に **24h SLA タイマー** を表示する
2. If record がレビュー queue で 24h 経過する, then the system shall 状態を `expired` にする。`expired` は以下を意味する: **(a) reviewer の通常 queue から除外 (b) corpus.upsert しない (c) 該当 schema field × user ペアに 7 日 cooldown を設定する** (Req 9 AC5 と整合)
3. When record が `expired` になる, the system shall レビュアーと該当業務ユーザーに **Discord 通知** を送る
4. The 業務ユーザー向け通知 shall 「再ヒアリングが必要」または「諦める」の選択肢を提示する
5. The system shall expired 率 **≤ 10%** を運用ターゲットとして週次レポートに含める
6. The system shall `expired` record を admin が手動で `pending_review` に再投入可能とする。Discord 通知で業務ユーザーが「再ヒアリングが必要」を選んだ場合は、当該 turn を新規対象として **Req 5 の 5W1H ヒアリングループを再起動**する

---

# §D. 支援システム要件（複数 story を成立させる内部処理）

### Requirement 12: 暗黙知ギャップ検知（Delta Detector）

**Supports:** B2（Req 5 のトリガ）
**Objective:** As a system, I want 各対話 turn を schema と照合し暗黙知候補となる差分を自動検知する, so that ヒアリングを必要場面でのみ起動できる
**関連リスク:** R-02, R-05（ローカルモデル精度）

#### Acceptance Criteria

1. When 新規 turn が記録される, the Delta Detector shall 該当 sector×unit の active schema fields すべてに対し差分スコアを計算する
2. The system shall AI 応答の self-critic score (0-10) を **応答生成と同一 LLM 呼び出し内で構造化出力として併出**させる（例: function calling で `{response, self_critic_score, self_critic_reason}`）。MVP では critic agent を分離しない（Req 4 AC2 連動）
3. The Delta Detector shall AI 応答の **self-critic score (0-10)** と user input の **意味的距離（embedding cosine similarity）** を組み合わせて差分スコアを算出する
4. When **self-critic score < 3**（低信頼確定）, the Delta Detector shall 距離スコアに関わらず該当 schema field を「暗黙知ギャップ候補」としてマークし Hearout Agent にイベント emit する
5. When self-critic score が **3 以上 5 未満** かつ意味的距離が閾値（初期 0.4）を超える, the Delta Detector shall 同様にマークしイベント emit する
6. If **同一 session かつ直近 30 分以内** に同一 schema field が連続 3 turn 以上ギャップ判定される, then the system shall 重複検知を抑制し最初のギャップのみヒアリング対象にする。session 終了（idle 30 分 or 明示 close）で抑制カウンタをリセットする
7. The Delta Detector shall 検知判定根拠（self-critic / distance / matched schema field id）を `delta_events` collection に保存する
8. Where redact = true の turn, the Delta Detector shall 当該 turn を照合対象から自動的に除外する（Req 7 連動）
9. Where turn が active schema fields のいずれにもマッチしない（out-of-schema）, the Delta Detector shall 当該 turn を `schema_candidate_log` collection に蓄積し、Admin UI に **「schema 追加候補」レポート**として提示する（Req 2 連動 / B-2 結論 = 案R 採用）
10. The system shall 閾値 `response_self_critic_low (= 3)` / `response_self_critic_mid (= 5)` / `embedding_distance_threshold (= 0.4)` を **環境変数化**し、週次 dashboard で各閾値の hit 率を表示、admin が config 更新で再キャリブレーション可能とする

### Requirement 13: 重み付き形式化（Formalization Agent）

**Supports:** B2 → C1/C2 のブリッジ（Req 5 出力を Req 9 入力に変換）
**Objective:** As a system, I want ヒアリング結果を構造化 record に変換し信頼度重みを付与する, so that レビュー queue 投入時の品質を担保する
**関連リスク:** R-02

#### Acceptance Criteria

1. When Hearout Agent が record 候補を出力する, the Formalization Agent shall **record 自己批評スコア `record_self_critic_score` (= 重み層 A, 0-10)** を必ず計算する（Req 12 の `response_self_critic_score` とは別物 / 用語表参照）
2. Where Phase 2 以降, the system shall **アノテータ信頼度 B**（EffiARA 系、ユーザー × topic の過去 agreement から sigmoid 化）を計算する
3. Where Phase 3 以降, the system shall **Provenance 時間減衰 C**（β(t) = β₀ e^(-γt)、γ は環境変数）を計算する
4. The system shall 最終重み = A × B × C の積で算出する（MVP は B = C = 1.0）
5. If 最終重み < **0.5**（MVP）/ < **0.7**（Phase 2 以降、B 層投入後）, then the system shall record を `pending_review` で保留し、**当該業務ユーザー本人に Discord 通知** + Admin UI の「保留中 record」一覧に表示する（reviewer queue には入れない）
6. When 最終重み ≥ **0.5**（MVP）/ ≥ **0.7**（Phase 2 以降）, the system shall record を §C のレビュー queue（Req 9）に投入する
7. The system shall 各層スコアと最終重みを record メタデータに保存し、Req 9 の UI で breakdown 表示可能にする

### Requirement 14: 入力時の正誤判定（Truth Judgment）

**Supports:** C4（Req 10 の起動トリガ）
**Objective:** As a system, I want corpus 投入直前の record の論理整合性を corpus 全体に対して検証する, so that 矛盾や誤情報が形式知化されないようにする
**関連リスク:** R-02, R-03(a)

#### Acceptance Criteria

1. When Formalization Agent (Req 13) が record を queue に投入する直前, the system shall **Req 9 のレビューより前段で** Truth Judgment を起動し、record 内容を **atomic claim に分解**する（GraphCheck 型）
2. The system shall 各 atomic claim に対し既存 corpus 内の類似 record を AI Search で検索し evidence path score を算出し、record を **3値分類**（`supported` / `novel` / `conflict`）する
3. Where 該当 sector×unit の corpus 内 active record 件数 < **30**（冷起動期）, the system shall AC1-2 の GraphCheck path をスキップし、**AC5 の FactCheck 3 LLM アンサンブル投票のみで分類する**。アンサンブル多数決が「conflict なし」を返した場合は `novel` として Req 9 の通常 queue に投入する
4. When 分類が `conflict`（atomic claim 整合性スコア < `claim_consistency_threshold` (= **0.4**, 環境変数化、Req 12 の `embedding_distance_threshold` とは別 symbol / 用語表参照）, the system shall record を `conflict_detected` フラグ付きで **Req 10 の専用 review queue** に提示する。それ以外（`supported` / `novel`）は **Req 9 の通常 review queue** にバッジ付きで投入する
5. Where 冷起動期、または `conflict` 判定の確証強化が必要な場合, the system shall **FactCheck 型の 3 LLM アンサンブル投票** (gpt-4o / gpt-4o-mini / gpt-4o 別 prompt) で補助判定を行う
6. When Req 9 の「編集」(AC4) で record content が修正された, the system shall 編集後 record に対し本 Truth Judgment を**再実行**し新バッジを返す
7. The system shall 判定根拠（参照した既存 record id 群、3値分類、各 LLM の判定）を `truth_judgment_logs` に `pattern: "input-time"` で保存する

---

# §E. 横断 / 非機能要件

### Requirement 15: 多マス対応アーキテクチャ

**Supports:** A3（Req 3）+ ハッカソン後の組織展開
**Objective:** As an architect, I want アーキテクチャがマス単位で水平展開できる, so that ハッカソン後の組織展開で同コード資産を再利用できる
**関連リスク:** R-07

#### Acceptance Criteria

1. The system shall すべての永続化リソース（Cosmos collections / AI Search index）を **`sector` + `unit` の複合キー** で partition する
2. The system shall MAF agent 起動時に `target_sectors`, `target_units` を環境変数 / config で指定可能にする
3. Where ハッカソン MVP は 1-2 マスのみ稼働, the system shall 単一 Foundry workflow 定義で全マスを処理できる（マスごとの workflow 分岐は不要）
4. The system shall マスを跨いで record / corpus / dialogue turn が混在しないことを partition key と AI Search filter で保証する
5. The system shall Cosmos の `prompt_templates` collection を持ち、sector×unit ごとに **agent prompt の用語辞書 / 業界用語例 / 想定対話シナリオ** を格納する。MAF agent 起動時に partition key で読み込み system prompt に inject する（マスごとの prompt 分岐を実現しつつ workflow 定義は単一を維持）

### Requirement 16: 観測性とテレメトリ

**Objective:** As an operator, I want agent 動作とコスト消費を可視化する, so that 予算 $200 の枯渇前にスコープ調整できる
**関連リスク:** R-04, R-05

#### Acceptance Criteria

1. The system shall MAF / Foundry の agent tracing を App Insights に自動 export する
2. The system shall 1 日 1 回 AOAI token 消費を集計し、累積 **$120** / **$150** で `cost.alert.fired` イベントを emit する（**emit 責務のみ。Tier 削減等の action 責務は Req 18 AC2/3 が subscribe して担う**）
3. While 各 agent が実行中, the system shall agent 名 / 経過時間 / トークン消費を App Insights `customMetrics` に emit する
4. If エラーが発生する, then the system shall stack trace + 直前の dialogue turn を Cosmos の `error_logs` に保存する。**当該 turn の `redact` が true の場合は content を除外し、`{turn_id, role, timestamp, redact: true}` のメタデータのみ保存する**（Req 7 連動）
5. The system shall Req 5 (ヒアリング介入頻度), Req 9 (レビュー処理時間 / 自己承認率), Req 10 (conflict resolution 率), Req 11 (expired 率) の各運用ターゲットを週次 dashboard で可視化する
6. The system shall App Insights / `customMetrics` に emit するすべての payload から PII 候補（顧客名 / 案件コード / メールアドレス）を **正規表現 + LLM scrubbing** で除去する

### Requirement 17: セキュリティと認証

**Objective:** As an org admin, I want クライアント機密データが漏れない構造である, so that 合成 corpus とはいえ運用パターン上の脆弱性が残らない

#### Acceptance Criteria

1. The system shall すべての agent と Container Apps の認証を **Entra ID + Managed Identity** で行う（API キー直接利用禁止）
2. The system shall AOAI / Cosmos / AI Search への接続文字列、および **Discord webhook URL**（Req 11 AC3 / Req 13 AC5 連動）を **Key Vault `kv-hack2026-tyu3o4`** で管理する
3. The system shall **Foundry Agent Service の per-agent Microsoft Entra identity** で各 agent に最小権限スコープを割当てる
4. Where ユーザーが redact = true フラグを立てる, the system shall Req 7 に従い content を保存しない
5. If 認証エラーが発生する, then the system shall ユーザーに具体エラー詳細を返さず、汎用 5xx と内部ログのみ詳細化する
6. When ユーザーが record の削除を申請する（退職 / 撤回希望）, the system shall **論理削除（案T）** を行う: record の `is_active = false` を設定し、retrieval (Req 6) / Truth Judgment (Req 14) の参照対象から除外する。**物理削除はしない**（監査ログ要件と引用先連鎖の安全のため）。Req 7 AC4 の retroactive redact と同じ手法で content を物理削除する場合のみ例外
7. The system shall reviewer に **`reviewer_scope: [sector×unit list]`** を Entra ID group claim で持たせ、scope 外の record はレビュー queue に表示しない。Foundry per-agent identity（AC3）で強制する

**Objective:** As an operator, I want 予算 $200 を超えないよう段階的にスコープ縮退できる, so that M13 teardown ゲートまで稼働を維持できる
**関連リスク:** R-04（高精度モデル可否）

#### Acceptance Criteria

1. The system shall 累積コスト消費を週次でレポートし、[`../../../docs/research/sector-unit-candidates.md`](../../../docs/research/sector-unit-candidates.md) の Tier A-F 削減候補と対応付けて閾値超過時に提案する
2. When 累積 **$120** を超える, the system shall Tier A（公開情報照合カット）を operator に推奨する
3. When 累積 **$150** を超える, the system shall Tier C（5W1H を 3W に縮退）+ Hearout Agent モデルを gpt-4o → gpt-4o-mini に切替提案する
4. The system shall Foundry Hosted agent の **scale-to-zero** 状態を idle 5 分で発動するよう設定する
5. The system shall モデル選択（クラウド高精度 / ローカル）を **設定で切替可能**にする（R-04 緩和）。**ただし切替対象は生成系 LLM (gpt-4o ↔ gpt-4o-mini ↔ ローカル LLM) に限定し、embedding モデル (`text-embedding-3-small`) は MVP 期間中固定とする**
6. The system shall embedding モデル変更は AI Search index 全再構築コスト（record 数 × 再 embed 料金）を伴うため、**Phase 2 以降の運用判断**とし MVP では実施しない
7. The system shall Hearout Agent の **cold start latency ≤ 3 秒** を SLO とする。実現のため Foundry の `min_replicas = 1` を **業務時間帯（平日 9-19 JST）のみ維持**、夜間/休日のみ scale-to-zero を有効化する（Req 5 ヒアリング介入 UX 阻害を防ぐ / AC4 と整合）

---

## 確認ポイント（design 前に潰す）

1. ✅ **次回対話参照のスコープ** (Req 6) — **決定 (2026-05-22): 同一 sector×unit 内に限定、shareability ラベル ({private/unit/public}) で粒度制御。マス横断は Phase 2**
2. ✅ **B = C 兼任の MVP 許容** (Req 9) — **決定 (2026-05-22): 案D 採用。`allow_self_approval` フラグで環境別制御 (MVP/デモは禁止、運用は条件付き許可)、自己承認率 KPI を週次 dashboard 化**
3. **業務フロー絞り込みのタイミング** (R-07): 本 requirements は汎用設計、design 前に critical path 用の絞り込みを team 合意
4. **Phase 2/3 (重み層 B/C / Provenance 時間減衰) を MVP 外明示** (Req 13): tasks 段階で誤って実装されないよう scope を明文化
5. **`conflict_detected` 専用 review queue を独立 UI で実装するか** (Req 10): UI 数の増加と HITL 設計の複雑度のトレードオフ

### 2026-05-22 review session 反映 (🔴 11件 close)

| # | Req | 変更点 |
|---|-----|--------|
| 1 | Req 9 AC3 | TJ 前段移動に伴い「< 0.4 で Req 10 へ」を AC3/AC4 で明示 |
| 2 | Req 9 AC8/9 | 案D (環境別 + 自己承認率 KPI > 30% warning) を新規追加 |
| 3 | Req 14, Req 9 | 案C 採用: Truth Judgment を Req 9 前段に移動、3値分類 (supported/novel/conflict) で全件 HITL 維持 |
| 4 | Req 11 AC2/AC6 | `expired` 意味論明文化 + admin による再投入経路追加 |
| 5 | Req 12 AC4/5 | AND 条件を 2段判定 (self-critic < 3 で即発火 / 3-5 + 距離超で複合発火) に変更 |
| 6 | Req 12 AC2 | self-critic は応答生成と同一 LLM 呼び出しで併出 (critic agent 分離せず) を明示 |
| 7 | Req 13 AC5/6 | MVP 閾値を 0.7 → **0.5** に緩和、Phase 2 で 0.7 に戻す |
| 8 | Req 14 AC3 | 冷起動期 (corpus < 30) は GraphCheck スキップ、FactCheck アンサンブルのみで分類 |
| 9 | Req 6 AC1/3 | 案Y 採用: 同一 sector×unit スコープを明示、shareability セマンティクス確定 |
| 10 | Req 16 AC4/AC6 | redact=true 連動、PII scrubbing AC を新規追加 |
| 11 | Req 18 AC5/AC6 | embedding モデルは MVP 固定 (LLM のみ切替可)、index 全再構築を Phase 2 へ |

### 2026-05-22 review session 反映 (🟡 15 件 close)

| # | Req | 変更点 |
|---|-----|--------|
| a | Req 9 AC10 | 並行レビュー lock TTL = 5 分 |
| b | Req 9 AC11 | レビュー中央値 > 3 分で「優先 3 件表示」モード自動切替 |
| c | Req 10 AC8 | superseded record の引用先整合 (`citation_audit_log` + 更新バナー) |
| d | Req 10 AC7 | conflict resolution 率の窓 = 直近 30 日 |
| e | Req 17 AC2 | Discord webhook URL も Key Vault 管理対象 |
| f | Req 12 AC9 | out-of-schema → 案R 採用 (`schema_candidate_log` + admin レポート) |
| g | Req 12 AC10 | 閾値環境変数化 (`response_self_critic_low/mid`, `embedding_distance_threshold`) |
| h | Req 12 AC6 | 連続抑制境界 = 同一 session かつ直近 30 分以内、idle 30 分でリセット |
| i | Req 13 AC5 | `pending_review` 宛先 = ユーザー本人 Discord + Admin UI 保留一覧 |
| j | Req 13 AC1 / 用語表 | self-critic 命名分離 (`response_*` / `record_*`) |
| k | Req 14 AC4 / 用語表 | 0.4 symbol 分離 (`embedding_distance_threshold` / `claim_consistency_threshold`) |
| l | Req 15 AC5 | `prompt_templates` collection (sector×unit ごとに用語辞書 inject) |
| m | Req 16 AC2 | コスト alert: emit 責務に限定、action は Req 18 が subscribe |
| n | Req 17 AC6 | record retention = 案T 採用 (論理削除 `is_active=false`、物理削除しない) |
| o | Req 17 AC7 | reviewer RBAC (`reviewer_scope` Entra group claim、scope 外非表示) |
| p | Req 18 AC7 | cold start SLO ≤ 3 秒、`min_replicas=1` を業務時間帯のみ維持 |

## リサーチ TODO（design フェーズ前に完了させる）

- [x] **暗黙知形式化システムの先行事例** (2026-05-12 完了) → [`../../../docs/research/tacit-knowledge-ai-prior-art.md`](../../../docs/research/tacit-knowledge-ai-prior-art.md)
- [x] **Azure Agent Platform 選定** (2026-05-12 完了) → [`../../../docs/research/azure-agent-platform-decision.md`](../../../docs/research/azure-agent-platform-decision.md)
- [ ] PKAI 論文本文（19 件の design requirement）の精読 — ヒアリング設計の網羅性チェック
- [ ] エンタープライズ製品（Microsoft Copilot for Knowledge / Notion AI / Guru / Bloomfire）の暗黙知扱いの一次資料調査 — 差別化ストーリー強度の検証
- [ ] Foundry Hosted agent の swedencentral リージョン提供状況確認

---

design.md は v1 requirements から導出されているため、本 requirements に合わせて再生成または差分更新が必要。
