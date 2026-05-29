# GenAI アプリ ベストプラクティス (責務単位)

`personal-hub/study/` の AWS AIP-C01 / AIF-C01 / MLA-C01 + Azure AI-102 から、サービス名でなく**責務 (responsibility)** 単位で抽出した実装観点。各項目に scaffold (Dialogue Delta, sweden central dev) 現状を 3 値マーク。

| 記号 | 意味 |
|---|---|
| ✅ | scaffold が既に満たしている |
| 🟡 | 浅い (動くが本番想定では不足) |
| ⬜ | 未対応 (デモ後タスク候補) |

出典は AWS 教材の filename 略記 (`d1-task5` 等)。Azure サービス対応は責務マップ末尾に併記。

---

## 1. Grounding & retrieval policy

- ✅ **Hybrid search (BM25 + vector) を named entity 質問に使う** — Azure AI Search の hybrid query で対応済 (`app/retrieval/search.py`)。 (d1-task5)
- 🟡 **チャンク戦略は文書構造に追従** — scaffold は固定チャンク。schema_field 単位の semantic chunk になっておらず、長文 record の中段が落ちる可能性。 (d1-task5)
- 🟡 **Retrieval precision vs recall の症状別診断** — 現状 precision/recall を分離計測していない。"なんとなく citations が薄い" を体系的に切り分ける手順が無い。 (d2-task1)
- ⬜ **Freshness アーキテクチャ** — Cosmos → AI Search 同期は手動 reindex。「分オーダー」で必要なら event-driven (Cosmos change feed → Function → index) に移行。デモは秒オーダー不要 OK。 (d2-task1)
- ⬜ **Multi-source RRF / weighted merge** — 単一 index しか引かない。複数テナント / 信頼度違うソースを統合する仕組みなし。デモ未要件。 (d1-task5)
- ⬜ **長文プロンプトプレフィックスのキャッシュ最適化** — AOAI prompt caching 未使用。system prompt が安定したら ≥1024 token prefix を caching 対象に。 (aif-detailed)

## 2. Citation binding & traceability

- ✅ **回答 ↔ 出典の明示バインド** — `citation_id` + `schema_field_id` + `weight` で取れている (`app/contracts/http.py`)。 (d3-task4)
- ✅ **RAG ≠ hallucination ゼロ** を前提に self-critic を後段に持つ — `_aoai_complete` の critic 段がこの責務 (`app/api/turn.py:113-152`)。 (d2-task1)
- 🟡 **Contextual grounding を出力後ガードとして単独評価** — critic は事実性を判定するが、source span との overlap を測る grounding score が別途無い。critic に embed されている。 (d1-task6)
- 🟡 **Citation precision + coverage の対計測** — 「引用先が関連しているか」「主張のうち何 % が裏付けられたか」を分離計測していない。今は self-critic 単一指標。 (d5-task1)
- ⬜ **Agent trace を retrieval/generation 別レイヤで保存** — Cosmos turns に retrieval_ctx と ai_response が混ざる。デバッグ時に「検索が悪いのか生成が悪いのか」を 1 record で切れない。 (d3-task4)

## 3. Refusal / safety / responsible AI

- ✅ **PII redaction (LLM ベース)** — `app/util/pii.py` で NAME/ID/EMAIL/PHONE。Req 7 の redact flag と直結。 (aif-detailed)
- 🟡 **Defense in depth は層** — 現状: PII redact のみ。AOAI content filter (Azure 既定) + Prompt Shields + 出力フィルタ の 3 層構成にはなっていない。AOAI 側のデフォルト content filter は効いているが明示利用していない。 (d3-task1)
- ⬜ **Prompt injection 防御 (direct + indirect)** — direct: ユーザ入力を critic に通すが prompt shield 未使用。indirect: KB ingestion 時の sanitization なし (record 本文に指示文を混ぜられたら通る)。 (d3-task1)
- ⬜ **Refusal trigger の明示ポリシー** — "個人 recall 質問なら score≤2" は critic 採点軸にあるが、その時の **拒否文言**・**Hearout 起動以外の代替動線**が定義されていない。 (d3-task4)
- ⬜ **Bias / fairness 計測** — demographic parity / equal opportunity の metric なし。tacit-knowledge ドメインは tenant ベース、ユーザ属性差別の表面化リスクは低いがログには無い。 (d3-task4)

## 4. Output structure & prompt engineering

- ✅ **System prompt + Guardrails contextual grounding** — system prompt 更新済 (2026-05-29)。生成エラーは prompt 起因が主、と切り分けている。 (d2-task1)
- 🟡 **Few-shot for format spec** — system prompt は instructional only。「結論 1 文 + hedge ルール」を **例示** で見せていない。LLM が指示違反したときの修正例が無い。 (aif-detailed)
- 🟡 **Temperature ≠ Top-P** の使い分け — `_aoai_complete` で temp=0.4 を直書き。critic は 0.0 (正しい)。`max_completion_tokens=400` も hard-coded。設定外出ししたい。 (d1-task6)
- ⬜ **Prompt 管理 (versioning + A/B)** — prompt が Python 文字列に直書き。git diff で履歴は追えるが、本番中の A/B + rollout 制御は無い。 (d1-task6)
- ⬜ **Chain-of-thought (zero-shot CoT)** — 多段推論質問でも "step by step" 誘導なし。tacit knowledge 引き出しに有効な可能性。 (aif-detailed)

## 5. Evaluation & telemetry

- 🟡 **LLM-as-a-Judge: 2 モデル分離** — critic は `deployment_small` で生成は `deployment_large`。原則は満たしているが、両方 AOAI 同系列。完全独立 (別 vendor) ではない。 (d5-task1)
- 🟡 **Quality gate = hallucination rate** — self-critic で間接計測。閾値 ≤5 で gap_detected を発火するロジックはある (delta_detector)。ただし**集計ダッシュボード**が無く、テナント別劣化を見れない。 (d5-task1)
- ⬜ **RAG 評価 4 軸** — retrieval relevance / citation precision / coverage / latency を golden set で定期回す仕組みなし。`tests/system/` は smoke のみ。 (d5-task1)
- ⬜ **Shadow deployment** — 新 prompt は dev に直 push。staging slot + traffic mirror で実トラフィック検証ができていない。 (d5-task1)
- ⬜ **User feedback の多次元化** — 👍/👎 のみ。理由カテゴリ (factual / tone / unhelpful) や free-text コメントの集約なし。 (d5-task1)
- ⬜ **Golden set + offline eval pipeline** — 本セッションで作った 7 件 pytest は black-box smoke。質問群を versioning した eval set として運用していない。 (d5-task1)

## 6. Cost & latency

- 🟡 **Token estimation を invoke 前に** — 現状なし。AOAI usage を CloudWatch (Azure Monitor) で受けているが**事前見積もり**は無い。デモ規模では無視可。 (d4-task1)
- 🟡 **Model cascading (small → large)** — critic は small で正しい配分。ただし**生成側の routing** (簡単な質問は small で済ます) はしていない。 (d4-task1)
- ⬜ **Prompt caching (≥1024 token prefix)** — AOAI 側 caching 利用なし。system prompt が安定しているので適用余地大。 (d1-task6)
- ⬜ **Semantic cache** — 類似質問の embedding cache なし。同一 sector で繰り返し質問されるドメインなので ROI 高い可能性。 (d2-task1)
- ⬜ **Provisioned throughput / batching** — Pay-as-you-go のみ。デモ規模では適切、本番化時に再評価。 (d4-task1)

## 7. Conversation & state management

- ✅ **Multi-turn session memory** — `dialogue_turns` container に role + content + turn_id 保持、session_id で纏まる。 (d3-task4)
- ✅ **Slot extraction (Hearout)** — Kunumi 5-step で 5W1H を毎ターン全文 transcript から再抽出 (`hearout/prompts.py`)。 (-)
- ✅ **Iterative re-query** — schema gate + conflict surfacing で「不足/競合」を inline で返す。明示的な再検索ループではないが UI 側で再質問動線あり。 (d2-task1)
- 🟡 **Agent 種別の使い分け** — Hearout = Agent (動的 5W1H 補完)、formalization = Flow (固定パイプ)。明示してドキュメント化されていないので、新人が混乱する余地。 (d1-task6)
- 🟡 **Conflict resolution semantics** — `/retrieve` の `conflicts[].alt_count` で alt 数は返るが、resolution UI は Review tab のみ。エンドユーザ側に "他 N 件の異なる見解" inline が出るのは○、選び方の根拠は薄い。 (d3-task4)

## 8. Schema / knowledge update management

- ✅ **Versioning (schema rev)** — `unseen_revision_ids` + 各 schema_field に rev N。banner で差分を ack 制御。 (d5-task1)
- ✅ **Supersede semantics** — `superseded_by` + banner 文字列で「この見解は更新されています」を表示。chain 辿れる。 (d2-task1)
- ✅ **Change notification = ack 制御** — schema gate が session 内で 1 度だけ banner 出す → ack で抑止。 (d3-task4)
- 🟡 **Model Card 相当** — 「この AOAI deployment が何で訓練され、どの guardrail が掛かっているか」のドキュメントが README 散在。1 枚の Model Card に集約していない。 (aif-detailed)
- ⬜ **Automated quality gate + rollback** — prompt or schema 更新時に quality 劣化検知 → 自動 rollback の仕組みなし。CI で smoke pass のみ。 (d5-task1)

---

## 5 つの非自明な cross-cutting 原則

1. **診断は層分離が前提** — 「citations は良いのに答えが悪い」⇒ prompt or contextual grounding を疑う。「答えはもっともらしいが citations が貧弱」⇒ retrieval (chunk / hybrid weight) を疑う。scaffold ではこの 2 層を turn record で分離保存していない (§2 ⬜) → デバッグコスト増。
2. **Defense in depth は異種多層** — 同種スタック (例: PII redact を 2 段) は冗長で実質単層。scaffold は PII redact 1 層のみ、AOAI content filter は default 任せ。「明示的に 3 種の異なる層」(input shield / model guardrail / output validator) を意識すべき。
3. **多次元評価 + HITL が盲点を消す** — self-critic 単一指標は LLM 自身のバイアスを引き継ぐ。👍/👎 + 理由カテゴリ + golden set + 人手アノテの 4 系統が揃って初めて blind spot が消える (scaffold は 1.5 系統)。
4. **Freshness / latency / cost は同時設計** — semantic cache は cost ↓ + latency ↓ だが staleness ↑。provisioned throughput は latency 保証だが cost ↑。「3 つを別軸で順に最適化」してはいけない。scaffold はデモ規模で 3 軸とも未調整 OK だが、本番化時は同時に決める。
5. **Traceability はガバナンス全前提** — 出典バインド・bias 監査・incident response はすべて trace 上に立つ。Cosmos に retrieval_ctx / prompt_ctx を **明示 field** として残すか否かで、後から効く監査可能性が決まる (scaffold は ai_response field に prompt_ctx を mix している → §2 ⬜ 該当)。

---

## 責務 → Azure サービス対応マップ (参考)

| 責務 | AWS 教材想定 | Azure 等価 (scaffold) |
|---|---|---|
| RAG retrieval | Bedrock KB + OpenSearch | Azure AI Search (hybrid) |
| Vector store | Aurora pgvector / OpenSearch | AI Search vector field / Cosmos |
| Generation FM | Bedrock Claude/Titan | AOAI gpt-4o / 4-turbo |
| Critic FM | Bedrock model evaluation | AOAI gpt-4o-mini (`deployment_small`) |
| Guardrails | Bedrock Guardrails | AOAI Content Filter + Azure AI Content Safety + Prompt Shields |
| PII redact | Comprehend + Guardrails | LLM-based redactor (`app/util/pii.py`) |
| Telemetry | CloudWatch + Bedrock Eval | Azure Monitor / Application Insights |
| Prompt mgmt | Bedrock Prompt Management | (未対応) git + Python literal |
| Agent trace | Bedrock Agent Tracing | Cosmos `dialogue_turns` (粒度浅) |
| Cache | Bedrock Prompt Caching + OpenSearch semantic | (未対応) |

---

## 集計

| 状態 | 件数 |
|---|---|
| ✅ 満たしている | 12 |
| 🟡 浅い | 15 |
| ⬜ 未対応 | 18 |

**Gate 判定 (P1 → P2)**: 🟡15 + ⬜18 = 33 観点中、**デモ前に潰すべき**は §2 traceability 分離 / §3 Prompt Shields / §4 few-shot 例示の 3 点。残りはデモ後 P3 候補。価値あり → P2 (評価採点 + 検証) に進める。

出典: `personal-hub/study/aws-aip-c01/notes/` (D1-D5) / `aws-aif-c01-detailed-concepts.md` / `azure-ai-102/notes/` / `aws-mla-c01/notes/`.
