# Framework-based Self-Assessment — dialogue-delta-formalization

> 作成: 2026-05-27 / 対象: Microsoft Agent Hackathon Japan 2026 提出 (締切 2026-05-30)
> スコープ: `scaffold/` 全体 (spec / 実装コード / Bicep / UAT)
> 用法: チーム自己評価 + 審査員からの突っ込み想定リスト。pitch / README 構築の素材に流用可。

---

## 0. Executive Summary

5 フレームワーク (Azure WAF AI Workload / AWS WAF GenAI Lens / 主要 Trusted AI 10 / Microsoft RAI Standard v2 / NIST AI RMF) を当てた総合評価:

| Framework | Grade (初版 → 2026-05-28) | 一言 |
|-----------|-------|------|
| **Azure WAF (AI Workload)** | **B-** → **B** | T1 で Evaluation harness 着手、SLO は依然 Phase 2 |
| **AWS WAF GenAI Lens** | **C+** → **B-** | T4 で Continuous iteration KQL 文書化、T5 で Sustainability 明示 |
| **主要 Trusted AI 10** | **C+** → **B-** | T3 Fairness proxy KQL、T6 Transparency footer で Explainability 補強 |
| **MS RAI Standard v2** | **C** → **B-** | T2 Impact Assessment + T6 disclosure footer で Transparency / Inclusiveness を底上げ |
| **NIST AI RMF (G/M/M/M)** | **C** → **B-** | Map (Impact Assessment) と Measure (golden set) が着地 |

**初版時の Top 3 リスク** (2026-05-27 提起):
1. **Evaluation harness の欠如** → **✅ T1 完了** (`tests/test_tj_golden.py`, `tests/fixtures/tj_golden.json` 10/10 match)
2. **Hearout エージェントの倫理性** → **部分対応** (T6 で AI 関与の常時 disclosure + 言語/accessibility scope 開示、本格 fairness audit は Phase 2)
3. **PII Scrubbing の脆弱性** → **未着手** (gap #2 / P1 残)。提出時は `requirements.md:375` の AC を Phase 2 と整合させる差分が必要

**残課題** (提出後の優先順位):
- PII scrubber の LLM fallback (gap #2 / P1)
- Latency / availability SLO (gap #7 / P3)
- Adversarial red-team / Prompt injection 評価 (§7.3 K)
- WCAG accessibility audit (§7.3 L)

**閉じた gap (2026-05-28 まで)**: #1 (T1) / #3 (T3) / #4 (T2) / #5 (T5) / #6 (T6) / #8 (T6 部分) / Continuous evaluation (T4) — 6/8 gaps + 2 deferred-with-justification

---

## 1. Microsoft Azure Well-Architected Framework — AI Workload

ソース: [Azure WAF AI](https://learn.microsoft.com/en-us/azure/well-architected/ai/) / 5 pillar (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency) + AI 固有ガイダンス (Model selection / Grounding / Evaluation / Responsible AI 統合)。

### 1.1 Pillar 評価

| Pillar | 状態 | 根拠 (file:line / framework reference) | 突っ込まれ時の答え |
|--------|------|----------------------------------------|---------------------|
| **Reliability** | 🟡 部分的 | Foundry checkpoint で HITL pause/resume (`design.md:117-127`)、24h SLA + 5min lock TTL (`requirements.md:251-256`)。一方 SLO は cold-start ≤ 3 秒 (`requirements.md:402`) のみで availability / 5xx 率は未定義 | 「HITL 部分は Foundry preview の checkpoint で耐性を持たせている。可用性目標はハッカソンスコープでは個別 SLO 未定義」 |
| **Security** | ✅ 強い | Managed Identity 全面 (`containerapps.bicep:4`)、Key Vault `kv-hack2026-tyu3o4` で 4 Discord webhook + AOAI + Cosmos secret 管理 (`contracts.md:466-473`)、per-agent Entra identity (`requirements.md:385`)、reviewer RBAC scope (`requirements.md:389`)、`enablePurgeProtection=true` (STATUS.md 2026-04-29 ログ) | 「全 6 サービス MI 経由、API キー直接利用は KV 経由のフォールバック 1 種類のみ」 |
| **Cost Optimization** | 🟡 部分的 | $200 上限 / 想定 $143 / バッファ $57 (`requirements.md:36`)、累積 $120 / $150 で `cost.alert.fired` (`requirements.md:371`)、Tier A/C 縮退 (`requirements.md:396-398`)、Budget bicep 80%/100%/forecast100% notification (`budget.bicep:17-42`)、scale-to-zero (`containerapps.bicep:3`)。一方で 250k TPM × gpt-4o の **実消費レート計測は未実装** (STATUS.md は gpt-4o-mini のみ provisioned 状態) | 「forecast budget + 2-tier alert + scale-to-zero。実消費は M8 タスク 8.4 で着手予定」 |
| **Operational Excellence** | 🟡 部分的 | App Insights + Log Analytics、customMetrics リスト (`design.md:550`)、PII scrubber emit 直前 (`requirements.md:375`)、GitHub Actions lint/typecheck/Bicep what-if (`tasks.md:18`)。Agent tracing は MAF 自動 export (`requirements.md:370`) に依存しており、構造化 trace の自分側設計は希薄 | 「telemetry は MAF + App Insights に任せ、business metric (`hearout.intervention.count`, `self_approval_rate.weekly` 等) を customMetrics で補強」 |
| **Performance Efficiency** | 🟡 部分的 | cold-start ≤ 3 秒 SLO、業務時間帯 min_replicas=1 (`containerapps.bicep:4`)、partition key `{sector}#{unit}` で水平展開 (`requirements.md:357`)、Cosmos Serverless + AI Search Basic。一方で **Hearout 1 セッション平均 < 2000 token は design.md:577 でターゲット化のみ**、実測なし | 「ハッカソンスコープでは partition 設計 + serverless 採用が主、本番負荷試験は UAT 非スコープ (`handoff-uat.md:60`)」 |

### 1.2 AI 固有ガイダンス

| 観点 | 状態 | 根拠 |
|------|------|------|
| **Model selection** | ✅ 強い | gpt-4o = Hearout/Formalization、gpt-4o-mini = Delta scoring/Truth assist、`text-embedding-3-small` 固定 (`design.md:136`)。Tier A/C で gpt-4o → gpt-4o-mini fallback 設計 (`requirements.md:398`)。embedding 切替は index 全再構築コストで Phase 2 化 (`requirements.md:400-401`) — 根拠付きの判断 |
| **Grounding** | 🟡 部分的 | GraphCheck atomic claim 分解 + AI Search corpus 検索 (`requirements.md:337-340`)、冷起動期は FactCheck 3-LLM ensemble (`requirements.md:339`)。**Web/KG hybrid (Bing/Wikipedia) は Phase 2 行き** (`tasks.md:103`) |
| **Evaluation** | 🔴 不足 | golden set 20 件は `contracts.md:543` に「明日着手」と書かれたまま。Self-critic / Truth Judgment の precision/recall 測定計画なし。RAG retrieval recall@k 等の番号もなし |
| **Responsible AI 統合** | 🔴 不足 | §4 RAI で詳述 |

### 1.3 Pitch 用言い回し

> 「Azure WAF Security pillar に沿って、全サービスを Managed Identity + Key Vault + per-agent Entra identity で構成。secret は KV `kv-hack2026-tyu3o4` の 7 種で集約管理し、コード上に直接配置していない (`contracts.md:466-473`)。」

---

## 2. AWS Well-Architected — Generative AI Lens (2025-12 更新版)

ソース: [AWS GenAI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/) / 6 pillar (Operational Excellence / Security / Reliability / Performance Efficiency / Cost Optimization / Sustainability) + 6 phase (Impact scoping → Model selection → Customization → Integration → Deployment → Continuous iteration)。

> 注: AWS だが「cross-cloud rigor」目的でフレームワークだけ参照。Azure 実装に対し「同等概念がどう満たされているか」を見る。

| Pillar | 状態 | 根拠 / Gap |
|--------|------|------------|
| Operational Excellence | 🟡 | App Insights + GitHub Actions 程度。**A/B prompt experimentation framework なし**。`prompt_templates` collection (`requirements.md:361`) は sector×unit 別 inject に限定 |
| Security | ✅ | §1 Security pillar と同じ |
| Reliability | 🟡 | HITL fallback (`requirements.md:282`)、`pending_review` 救済 (`requirements.md:325`)、SLA expired 再投入 (`requirements.md:288`)。一方 **Foundry preview 障害時は MAF 直 Container Apps へ降格** (`design.md:120`) — Plan B は明示済みだが Test 未実施 |
| Performance Efficiency | 🟡 | Cosmos partition + AI Search filter で Tenant isolation。Latency SLO は cold-start のみ |
| Cost Optimization | ✅ | §1 と同様、forecast budget + Tier 縮退の組合せは AWS Lens の "graceful degradation" にマップ可 |
| **Sustainability** | 🔴 | Carbon footprint / model efficiency の議論なし。**唯一の救い**は scale-to-zero + serverless 採用 |
| Responsible AI (cross-pillar) | 🟡 | §4 |

### Lifecycle phase coverage

| Phase | 状態 |
|-------|------|
| Impact scoping | 🟡 — `personas-stories.md` で 3 persona + リスク台帳は揃うが、対象組織 (例: AI 推進部門)全体への bias / 業務阻害 impact は形式 assessment 化されていない |
| Model selection | ✅ — `design.md:136` |
| Customization | 🟡 — `prompt_templates` のみ、Fine-tune / DPO 等は考慮外 (ハッカソンスケール妥当) |
| Integration | ✅ — MAF + Foundry Workflow + BYO Cosmos の三層 |
| Deployment | ✅ — Container Apps + Bicep + budget |
| **Continuous iteration** | 🔴 — 観測指標は `customMetrics` の宣言まで、loop 化された prompt/threshold 更新フローは未設計 |

---

## 3. Trusted AI Framework — 10 Pillars

ソース: [Trusted AI](https://example.com/trusted-ai/en/what-we-do/services/ai/trusted-ai-framework.html) 10 ethical pillars。AI 部が 対象組織配下である以上、本フレームワークが審査員 の自然な評価軸になりやすい。

| Pillar | 状態 | 根拠 / Gap | 説明責任シナリオ |
|--------|------|------------|--------------------|
| **Reliability** | 🟡 | 自己批評スコア (Kunumi) + GraphCheck/FactCheck ensemble (`requirements.md:42-48`)、HITL 3 段 (Hearout → Formalization → Reviewer)、TJ 編集後の再実行 (`requirements.md:342`)。一方 model decay / drift 監視なし | 「3 段 HITL でハッカソン版の reliability を担保、運用 drift は Phase 2 issue」 |
| **Security** | ✅ | §1 Security と同じ。`enablePurgeProtection=true`、`nodelete-shared` lock、policy.bicep `deny-storage-public` (STATUS.md デプロイ済リソース表) | 「MI + KV + RG lock + deny-public storage policy で多層」 |
| **Safety** | 🟡 | Hearout 5 ターン上限 / skip 自由 (`requirements.md:189-192`)、SLA expired 後の業務ユーザー「諦める」選択肢 (`requirements.md:286`)。一方 **AI 応答に critical action 抑止の guardrail なし** (回答内容の有害性チェックは Truth Judgment が「事実性」だけを見る) | 「業務阻害 = 安全リスクとして 5 ターン上限 / opt-out で対応。回答有害性は Foundry の content filter に委譲」 |
| **Privacy** | 🟡 | redact フラグ (`requirements.md:215-219`)、論理削除 + 引用先連鎖 (`requirements.md:387`)、PII scrubber (`scaffold/app/util/pii.py:38-44`)。**Gap**: scrubber が regex のみで LLM scrubbing 未実装 — requirements 16.6 文言と乖離 | 「redact + 論理削除 + scrubber の三層。LLM scrubbing は Phase 2」 |
| **Sustainability** | 🔴 | 言及ゼロ。`text-embedding-3-small` 採用 + scale-to-zero が偶発的に効くのみ | 「ハッカソンスコープでは個別の sustainability 目標なし。serverless + scale-to-zero で間接最小化」 |
| **Explainability** | 🟡 | 重み breakdown tooltip (A×B×C、`requirements.md:252`)、TJ verdict バッジ (supported/novel/conflict、`requirements.md:247`)、Citation ID で出典 turn 表示 (`requirements.md:206`)。**Gap**: なぜその AI 応答が出たかの自己批評理由 (`self_critic_reason`) は contracts に field 定義 (`contracts.md:120`) はあるが、Chat UI 上で利用者に提示するかは未確定 | 「3 層 explainability (breakdown / verdict バッジ / citation)。応答理由の UI 露出は次タスク」 |
| **Integrity (Data)** | ✅ | partition key `{sector}#{unit}` 全 collection 統一 (`requirements.md:357`)、frozen Pydantic model (`contracts.md:14`)、`schema_audit_log` 物理削除禁止 invariant (`tasks.md:35`)、Truth Judgment で corpus 整合性チェック (`requirements.md:337-343`) | 「schema は revision + audit log で改竄不可、record は TJ で投入前検証」 |
| **Transparency** | 🟡 | Schema 変更履歴 view (Req 2.6) + 業務ユーザー向け banner (Req 2.7) は **同期通知 design** (`design.md:447-471`) で強化済。**Gap**: AI agent が自動推論していること自体を Persona B に明示する UI が無い (常時 disclosure) | 「schema 更新の Push transparency は実装、AI 関与の常時 disclosure は次サイクル」 |
| **Fairness** | 🔴 | Bias test なし。sector×unit を跨いだ承認率/拒否率の差分監視なし。Reviewer の自己承認率 > 30% warning (`requirements.md:254`) は最も近い | 「自己承認率 KPI が唯一の fairness proxy。本格的 bias audit は Phase 2」 |
| **Accountability** | ✅ | 3 段 HITL (Hearout → HITL approve → TJ verdict)、`schema_audit_log` (`tasks.md:36`)、`citation_audit_log` (`requirements.md:273`)、reviewer scope (`requirements.md:389`)、`allow_self_approval` env-flag (`requirements.md:253`) | 「人の判断を必ず通過、誰がいつ承認したかは audit log で trace 可能」 |

**法人 視点 Top Risk**: Fairness 監査の不在。デモ後に「sector A の reject 率と sector B の reject 率に有意差があった場合どう検知するか」と聞かれて答えられない。

---

## 4. Microsoft Responsible AI Standard v2 (6 goals / 14 sub-goals)

ソース: [MS RAI Standard v2](https://www.microsoft.com/en-us/ai/responsible-ai)。Microsoft Hackathon 提出物としては最低限のフィット感が必要。

| Goal | 状態 | 根拠 / Gap |
|------|------|------------|
| **Accountability** | 🟡 | Audit log 2 種 + HITL 3 段 + spec の 3-phase approval は強い。一方 **Impact Assessment (template に基づく) は未実施** — RAI Standard が GA 後に最も重視するもの。`personas-stories.md` がそれに最も近い |
| **Transparency** | 🟡 | 法人 §Transparency と同。**Gap**: AI が応答生成していることの常時 notice (chat UI 上に「AI が自己批評スコアを付けています」等) |
| **Fairness** | 🔴 | 法人 §Fairness と同 |
| **Reliability & Safety** | 🟡 | §1.1 Reliability + §3 Safety と同。Adversarial / red-teaming は未実施 |
| **Privacy & Security** | ✅ / 🟡 | Security は強。Privacy は scrubber 弱点 (§3 参照) |
| **Inclusiveness** | 🔴 | 言語 = ja 固定 (`spec.json`, `handoff-uat.md:108`)、accessibility (WCAG / スクリーンリーダー) は未検証。3 persona は社内ロールベースで demographic 多様性は議論外 |

**判定**: 6 goal のうち 2 完成 / 3 部分 / 2 不足。**Impact Assessment template を 1 枚に圧縮した付録**を提出前に作っておくと、審査員質問への耐久力が一段上がる。

---

## 5. NIST AI RMF 1.0 (Govern / Map / Measure / Manage)

ソース: NIST AI RMF 1.0 (2023-01)、現状 enterprise governance の de-facto。

| Function | 状態 | 根拠 |
|----------|------|------|
| **Govern** | 🟡 | CLAUDE.md の 3-phase approval (Requirements → Design → Tasks → Implementation)、Kiro spec workflow、`personas-stories.md`、`risks.md`、`decisions.md`、3 名 collaborator + reviewer scope。**Gap**: 第三者 audit / model card / system card がない |
| **Map** | ✅ | `personas-stories.md` (3 persona JTBD)、`risks.md` (R-01〜R-07)、`scope-candidates.md`、`impact-d1/d2/d3-*.md` (3 業界 impact 分析)、`research.md` (prior art baseline) — 文書化レベルとしてはハッカソン基準では高い |
| **Measure** | 🔴 | customMetrics 宣言はあるが収集データなし、golden set 未作成、operational target は requirements に書かれた数字 (skip 率 ≤ 50%, expired 率 ≤ 10%, self-approval > 30% warning) が大半 |
| **Manage** | 🟡 | Tier A/C 縮退、cost alert、SLA expired 再投入、conflict 3 択 (adopt_new / keep_existing / coexist) は manage に該当。**Gap**: 重大インシデント escalation runbook なし |

---

## 6. Cross-framework Gap Matrix — 共通指摘の優先度付け

> 複数 framework が同じ穴を指摘した場合、それは pitch で必ず突かれる。優先度 P1 = 提出 72h で潰す、P2 = pitch で「Phase 2」と明言、P3 = 提出後。

| # | Gap | 指摘 framework | Priority | 根拠 |
|---|-----|----------------|----------|------|
| 1 | ~~**Evaluation harness 不在**~~ ✅ **2026-05-27 着手 (T1)** — TJ golden 10 件 + pytest harness (`tests/test_tj_golden.py`, `tests/fixtures/tj_golden.json`)。10/10 match、aggregation 決定論を担保。real-LLM eval は Phase 2 | Azure WAF (AI eval) / AWS GenAI / NIST (Measure) / 法人 (Reliability) | **P1 ✅** | aggregation/cold-start/hot-path 3 経路をカバー |
| 2 | **PII scrubber が regex のみ** (Req 16.6 の "LLM scrubbing" と乖離) | 法人 (Privacy) / MS RAI (Privacy & Security) / Azure WAF (Security) | **P1** | `app/util/pii.py:14-31` 漢字氏名ヒューリスティックは false negative 多発。最低 1 段の LLM scrubbing pass を Phase 2 と明示するか、要件 16.6 を MVP では正規表現のみと書き換える整合作業必要 |
| 3 | ~~**Fairness / Bias audit 不在**~~ ✅ **2026-05-28 着手 (T3)** — `docs/observability-kql.md` §1 で reviewer × sector × decision 別の approve/reject 比率 KQL を 3 本提供。`app/api/reviews.py` の `/decision` endpoint で `review.decision` customMetric を emit するよう instrument | 法人 (Fairness) / MS RAI (Fairness) / AWS GenAI (Responsible AI) | **P2 ✅** | proxy として fairness dashboard 化。本格 bias audit は Phase 2 |
| 4 | ~~**Impact Assessment 文書なし**~~ ✅ **2026-05-28 完了 (T2)** — `scaffold/docs/impact-assessment.md` (12 harm × mitigation × file:line 出典、out-of-scope 利用明記、残存リスク 5 件開示) | MS RAI / 法人 / NIST | **P1 ✅** | MS RAI v2 Impact Assessment 構造に準拠 |
| 5 | ~~**Sustainability に対する明示的設計判断なし**~~ ✅ **2026-05-28 完了 (T5)** — `README.md` Sustainability セクション + `app/util/cost.py:19` `aggregate_aoai_tokens_daily` で AOAI token を customMetric として日次集計。scale-to-zero + serverless + gpt-4o-mini routing + max_completion_tokens 上限を明示化 | AWS GenAI / 法人 | **P3 ✅** | carbon 計測そのものは Phase 2 だが、設計判断を文書化 |
| 6 | ~~**AI 関与の常時 disclosure UI なし**~~ ✅ **2026-05-28 完了 (T6)** — `ui/chat/src/shell/AppShell.tsx` に persistent disclosure footer 追加（全 surface = Chat/Admin/Review でカバー）+ ChatWindow per-message self-critic スコアバッジは既存 | MS RAI (Transparency) / 法人 (Transparency) | **P2 ✅** | 言語 ja-JP + accessibility Phase 2 も同 footer で開示 |
| 7 | **Cold start 以外の latency / availability SLO 未定義** | Azure WAF (Reliability/Performance) / AWS GenAI (Reliability) | **P3** | ハッカソンスコープでは UAT で機能性が通れば OK。pitch で問われたら「次フェーズ」 |
| 8 | ~~**Hearout 介入の Inclusiveness / accessibility 未検証**~~ ✅ **2026-05-28 部分対応 (T6)** — AppShell footer に「言語: 日本語 (ja-JP) 固定、accessibility は Phase 2」を明示開示。WCAG audit 本体は Phase 2 | MS RAI (Inclusiveness) | **P3 ✅** | scope 制限の transparency で対応 |

---

## 7. ハッカソン現実主義による Recommendations

> 5/30 提出まで wall-clock 約 72h。「やる / 言及で逃げる / 切る」を分類。

### 7.1 やるべき (提出までに) — Priority P1

| # | Item | コスト | 審査インパクト | 担当推奨 |
|---|------|--------|---------------|----------|
| ~~A~~ ✅ | **Eval harness 最小版** — **完了 2026-05-27**。`tests/fixtures/tj_golden.json` (10 件: 5 supported / 3 novel / 2 conflict, 製造ライン domain) + `tests/test_tj_golden.py` (verdict ≥ 80% assert + hot-path retrieval heuristic test)。**結果 10/10 match**。スクリプト LLM 応答上での aggregation 決定論を担保 (real-LLM 品質評価は Phase 2) | M | Hi | dev メンバー |
| ~~B~~ ✅ | **Impact Assessment 1 pager** — **完了 2026-05-28**。`scaffold/docs/impact-assessment.md` (12 harm × mitigation table + 意図利用 / out-of-scope / 残存リスク 5 件 / フレームワーク対応表)。MS RAI v2 + 法人 Accountability + NIST Map を解消 | S | Hi | オペレータ |
| C | **PII scrubber の現状を要件に整合**: `requirements.md:375` の「LLM scrubbing」を MVP 行きにせず Phase 2 に降格させる差分 PR、もしくは LLM fallback を 1 関数追加 | S | Mid | dev メンバー |
| ~~D~~ ✅ | **Chat UI に AI disclosure footer 1 行** — **完了 2026-05-28**。`AppShell.tsx` に persistent footer 追加 (T6) | S | Mid | dev メンバー |
| ~~E~~ ✅ | **本書 (framework-review.md) を README から link** — **完了 2026-05-28**。README の Sustainability/RAI セクションから link (T5) | S | Mid | オペレータ |

### 7.2 諦めて pitch で言及して逃げる — Priority P2

| # | Item | pitch 言い回し例 |
|---|------|-------------------|
| F | Fairness / Bias audit | 「ハッカソンスコープでは自己承認率 > 30% warning が fairness proxy。本格 bias audit は運用フェーズ」 |
| G | Web/KG hybrid grounding | 「冷起動期は FactCheck 3-LLM ensemble、定常期は GraphCheck + corpus。Web grounding は Phase 2」 |
| ~~H~~ ✅ | Continuous evaluation loop — **完了 2026-05-28 (T4)**。`docs/observability-kql.md` §2 に weekly customMetrics workbook 用 KQL 5 本 (token / TJ verdict / Hearout outcome / self-critic / review duration) + alert ルール 4 件を文書化。Workbook bicep 化は Phase 2 |
| I | Multi-tenant 横断検索 | 「同一 sector×unit 内に閉じる設計、横断は Phase 2 (`requirements.md:202`)」 |
| J | Sustainability | (pitch では触れない。聞かれたら「scale-to-zero + serverless」で 1 行返す) |

### 7.3 完全に切る — Priority P3

| # | Item | 理由 |
|---|------|------|
| K | Adversarial red-team / Prompt injection 評価 | スコープ過大、ハッカソン基準では誰も実施しない |
| L | Accessibility / WCAG | 言語固定 + persona 限定で正当化、UAT 非スコープ |
| M | Model card / System card 形式の提出 | MS RAI で重要だがハッカソン審査では空気感、Impact Assessment (B) で代替 |
| N | Foundry preview 代替経路 (Container Apps 直 MAF) の実地検証 | flag day で green であれば走らせない |

---

## 8. Pitch で credibly 主張できる言い回し集

> 各 1 文。pitch スクリプト / README / Zenn 記事から再利用可。

1. **Security**: 「Azure WAF の Security pillar に沿って、全 5 サービスを Managed Identity + Key Vault (`kv-hack2026-tyu3o4`) + per-agent Entra identity + RG `CanNotDelete` lock + `deny-storage-public` policy assignment で多層化した (`infra/main.bicep:75-101`)。」
2. **Accountability**: 「Trusted AI の Accountability pillar に対応し、Hearout → Formalization HITL → Truth Judgment → Reviewer の 4 段で人間判断を強制、`schema_audit_log` + `citation_audit_log` + `truth_judgment_logs` の 3 audit log で trace 可能 (`design.md:489-499`)。」
3. **Privacy**: 「Persona B の redact フラグ + 論理削除 (`is_active=false`) + 引用先連鎖 (`superseded_by`) + emit 直前 PII scrubbing の 4 段で privacy by design (`requirements.md:215-219, 387-388, 375`)。」
4. **Cost**: 「$200 上限に対し forecast budget 100% 通知 + 累積 $120/$150 で Tier A/C 縮退提案 + scale-to-zero (idle 5min) で予算ガードレールを多層化 (`budget.bicep:17-42`, `requirements.md:396-398`)。」
5. **Explainability**: 「重み breakdown (A×B×C) tooltip + TJ verdict バッジ (supported / novel / conflict) + Citation ID クリックで出典 turn 表示 (`requirements.md:247-252, 206`) — レビュアーが「なぜこの record か」を 1 画面で判断可能。」
6. **Data Integrity**: 「全 12 Cosmos collection で partition key `{sector}#{unit}` を強制 (`contracts.md:228`)、Pydantic `frozen=True, extra="forbid"` で DTO 不変性、`schema_audit_log` 物理削除禁止 invariant により data tampering を遮断。」
7. **Operational rigor**: 「Kiro 3-phase spec workflow (Requirements → Design → Tasks → Implementation)、EARS 18 Requirements × 100+ AC × Traceability matrix で要求と実装を双方向 trace。」

---

## 9. Post-hack TODO (提出後)

| Priority | Item | 関連 framework |
|----------|------|----------------|
| H | Truth Judgment golden set 100 件まで拡張 + precision/recall/F1 ダッシュボード | Azure WAF (Eval) / NIST (Measure) |
| H | PII scrubber に LLM fallback pass 実装 (requirements 16.6 と完全整合) | 法人 / MS RAI Privacy |
| H | Fairness audit framework: sector × user dimension で reject/approval 率の差分検知 | 法人 / MS RAI Fairness |
| M | Impact Assessment を MS RAI v2 template 準拠で再構成 (model card 兼用) | MS RAI |
| M | Adversarial red-team (prompt injection / data exfiltration) シナリオ 5 件 | MS RAI Safety |
| M | Continuous iteration loop: 閾値 (`response_self_critic_low/mid`, `embedding_distance_threshold`) を週次 hit-rate から自動提案 | AWS GenAI Continuous iteration |
| M | Chat UI に AI 関与 disclosure を全 turn 表示 | MS RAI Transparency |
| L | Sustainability: AOAI token consumption から推定 CO2e を customMetrics に追加 | AWS GenAI / 法人 |
| L | Accessibility: WCAG 2.1 AA 相当の audit を Chat UI に実施 | MS RAI Inclusiveness |
| L | Foundry preview 障害時の Container Apps 直 MAF 切替を chaos test で実証 | Azure WAF Reliability |

---

## 10. 参考 (Framework 公式 URL — 最新版)

- [Azure Well-Architected Framework — AI Workloads](https://learn.microsoft.com/en-us/azure/well-architected/ai/) (2026 update)
- [AWS Well-Architected Generative AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html) (2025-12 更新)
- [Trusted AI Framework](https://example.com/trusted-ai/en/what-we-do/services/ai/trusted-ai-framework.html) (10 pillars)
- [Microsoft Responsible AI Standard v2](https://www.microsoft.com/en-us/ai/responsible-ai) (6 goals / 14 sub-goals)
- [NIST AI Risk Management Framework 1.0](https://www.nist.gov/itl/ai-risk-management-framework) (Govern / Map / Measure / Manage)

---

**End of framework-review.md** — 7.1 のアクション A〜E を 24h 以内に着手することを推奨。
