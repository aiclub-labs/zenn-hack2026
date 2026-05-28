# Interface Contracts (Implementation Freeze)

> 並列 worktree 実装の **唯一の真実源**。本書を読まずに型・API・collection 形状・event payload・KV シークレット名を作らないこと。
> 変更は本書を先に PR、合意後に各 worktree へ反映。spec.json language=ja。

---

## 0. 前提

- Python 3.11+ / Pydantic v2 / FastAPI 0.115+ / Microsoft Agent Framework (MAF) 1.0 Python SDK
- Foundry Workflow agent preview, swedencentral（flag day green）
- Cosmos DB Serverless / AI Search Basic / Container Apps / Key Vault `kv-hack2026-tyu3o4` / App Insights
- partition key 全 collection 共通: `pk = f"{sector}#{unit}"`
- 命名: snake_case (collections / fields) / PascalCase (Pydantic models) / SCREAMING_SNAKE_CASE (env / KV secret)
- 全 model に `model_config = ConfigDict(extra="forbid", frozen=True)`（DTO 不変）

---

## 1. 共通 Pydantic 型

```python
# app/contracts/common.py
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

PK = str  # f"{sector}#{unit}"

class Tenant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sector: str
    unit: str

    @property
    def pk(self) -> PK:
        return f"{self.sector}#{self.unit}"

ExpectedValueType = Literal["string", "number", "enum", "structured"]
Shareability = Literal["private", "unit", "public"]
ChangeType = Literal["create", "update", "deactivate", "reactivate"]
ReviewDecision = Literal["approve", "edit", "reject"]
ConflictDecision = Literal["adopt_new", "keep_existing", "coexist"]
TJVerdict = Literal["supported", "novel", "conflict"]
QueueStatus = Literal["pending_review", "in_review", "approved", "rejected", "expired", "conflict_pending"]
HearoutOutcome = Literal["completed", "skipped", "expired"]
DeltaPattern = Literal["input-time", "activation-time"]
```

---

## 2. Cosmos collections（12 種, design §5.1 と一致）

```python
# app/contracts/cosmos.py
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from .common import *

# --- 2.1 schemas ---
class SchemaField(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    sector: str
    unit: str
    pk: str
    field_name: str
    description: str
    expected_value_type: ExpectedValueType
    example: str
    ai_baseline_assumption: str
    is_active: bool = True
    revision_id: int
    updated_at: datetime
    updated_by: str

# --- 2.2 schema_audit_log ---
class SchemaAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    schema_field_id: str
    revision_id: int
    change_type: ChangeType
    diff: dict[str, dict[str, Any]]  # {field: {before, after}}
    reason: Optional[str] = None
    changed_by: str
    changed_at: datetime

# --- 2.3 schema_candidate_log ---
class SchemaCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    turn_id: str
    suggested_field_hint: str
    llm_reason: str
    occurrences: int
    last_seen_at: datetime

# --- 2.4 prompt_templates ---
class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    terminology: dict[str, str]
    industry_examples: list[str]
    scenario_prompts: dict[str, str]

# --- 2.5 dialogue_turns ---
class DialogueTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    session_id: str
    turn_id: str
    role: Literal["user", "assistant"]
    content: Optional[str] = None  # redact=true なら None
    self_critic_score: Optional[float] = None  # 0-10
    self_critic_reason: Optional[str] = None
    redact: bool = False
    timestamp: datetime
    schema_revision_seen_at: Optional[datetime] = None
    schema_revision_id_seen: Optional[int] = None

# --- 2.6 delta_events ---
class DeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    turn_id: str
    schema_field_id: Optional[str]  # None = out-of-schema
    self_critic: float
    distance: float
    gap_detected: bool
    cooldown_until: Optional[datetime] = None
    matched_reason: str

# --- 2.7 hearout_records ---
class HearoutRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    gap_event_id: str
    session_id: str
    transcript: list[dict[str, str]]  # [{turn, q, a}]
    who: Optional[str] = None
    what: Optional[str] = None
    when: Optional[str] = None
    where: Optional[str] = None
    why: Optional[str] = None
    how: Optional[str] = None
    outcome: HearoutOutcome
    turn_count: int

# --- 2.8 formalization_queue ---
class FormalizationTicket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    hearout_id: str
    weight_a: float
    weight_b: float = 1.0  # MVP fixed
    weight_c: float = 1.0  # MVP fixed
    weight_final: float
    tj_verdict: Optional[TJVerdict] = None
    status: QueueStatus
    locked_by: Optional[str] = None
    lock_expires_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    decision: Optional[ReviewDecision] = None
    conflict_decision: Optional[ConflictDecision] = None
    edit_diff: Optional[dict[str, Any]] = None
    expired_at: Optional[datetime] = None
    created_at: datetime

# --- 2.9 truth_judgment_logs ---
class TruthJudgmentLog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    record_id: str
    atomic_claims: list[str]
    evidence_score: float
    ensemble_votes: list[dict[str, Any]]  # [{model, vote, reason}]
    verdict: TJVerdict
    pattern: DeltaPattern

# --- 2.10 corpus_meta ---
class CorpusMeta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    record_id: str
    schema_field_id: str
    referenced_count: int = 0
    last_referenced_at: Optional[datetime] = None
    shareability: Shareability = "private"
    is_active: bool = True
    superseded_by: Optional[str] = None
    coexisting_views: Optional[list[str]] = None

# --- 2.11 citation_audit_log ---
class CitationAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    old_record_id: str
    new_record_id: str
    transition: Literal["superseded", "coexists"]
    occurred_at: datetime

# --- 2.12 error_logs ---
class ErrorLog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    pk: str
    ts: datetime
    agent: str
    stack: str
    last_turn_meta: dict[str, Any]  # content は含めない（redact 時）
```

### Cosmos container provisioning

```
Database: dialogue_delta
Containers (all partition_key="/pk"):
  schemas, schema_audit_log, schema_candidate_log, prompt_templates,
  dialogue_turns, delta_events, hearout_records, formalization_queue,
  truth_judgment_logs, corpus_meta, citation_audit_log, error_logs
Throughput: serverless
```

---

## 3. AI Search index

```
Index name: corpus-{env}  (env=dev/prod)
Partition: filter on sector+unit
Vector field: text-embedding-3-small, dim=1536
Fields:
  id          Edm.String       key
  sector      Edm.String       filterable
  unit        Edm.String       filterable
  pk          Edm.String       filterable
  schema_field_id  Edm.String  filterable
  content     Edm.String       searchable
  atomic_claims  Collection(Edm.String)  searchable
  weight_final  Edm.Double     sortable, filterable
  shareability  Edm.String     filterable
  is_active   Edm.Boolean      filterable
  superseded_by  Edm.String    filterable
  created_at  Edm.DateTimeOffset  sortable, filterable
  vector      Collection(Edm.Single)  vector, dim=1536
```

---

## 4. Agent interfaces (MAF 1.0 Python)

```python
# app/contracts/agents.py
from typing import Protocol, Optional
from .cosmos import *
from .events import *

class SchemaManagerAgentI(Protocol):
    async def upsert(self, field: SchemaField, reason: Optional[str] = None) -> tuple[SchemaField, SchemaAuditEntry]: ...
    async def set_active(self, field_id: str, pk: str, is_active: bool, reason: Optional[str] = None) -> SchemaAuditEntry: ...
    async def bulk_import(self, source: Tenant, target: Tenant) -> list[SchemaField]: ...
    async def get_history(self, tenant: Tenant, limit: int = 50, since: Optional[datetime] = None) -> list[SchemaAuditEntry]: ...

class DeltaDetectorAgentI(Protocol):
    async def detect(self, turn: DialogueTurn) -> list[DeltaEvent]: ...

class HearoutAgentI(Protocol):
    async def start(self, gap_event_id: str, user_id: str, tenant: Tenant) -> "HearoutTurn": ...
    async def respond(self, session_id: str, answer: str) -> "HearoutTurn": ...
    async def skip(self, session_id: str) -> HearoutRecord: ...

class HearoutTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    session_id: str
    status: Literal["in_progress", "completed", "skipped", "expired"]
    next_question: Optional[str] = None
    final_record: Optional[HearoutRecord] = None
    turn_count: int

class FormalizationAgentI(Protocol):
    async def weight(self, record: HearoutRecord) -> tuple[float, float, float, float]:  # (a, b, c, final)
        ...
    async def submit_for_review(self, record: HearoutRecord, weights: tuple[float, float, float, float], tj_verdict: Optional[TJVerdict]) -> FormalizationTicket: ...
    async def on_review_decision(self, ticket_id: str, pk: str, decision: ReviewDecision, edited: Optional[HearoutRecord] = None) -> "CorpusUpsertResult": ...
    async def on_conflict_decision(self, ticket_id: str, pk: str, decision: ConflictDecision) -> "ConflictResolution": ...

class TruthJudgmentI(Protocol):
    async def judge(self, record: HearoutRecord) -> TruthJudgmentLog: ...

class NotificationDispatcherI(Protocol):
    async def emit(self, event: "NotificationEvent") -> None: ...

class CorpusUpsertResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: str
    corpus_meta_id: str

class ConflictResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    ticket_id: str
    decision: ConflictDecision
    affected_record_ids: list[str]
```

---

## 5. Event payloads（pub/sub & Notification Dispatcher）

```python
# app/contracts/events.py
from typing import Literal, Union
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class SchemaUpdatedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_type: Literal["schema.updated"] = "schema.updated"
    sector: str
    unit: str
    revision_id: int
    change_type: str
    field_name: str
    diff_summary: str
    history_url: str
    changed_by: str
    changed_at: datetime

class PendingReviewEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_type: Literal["record.pending_review"] = "record.pending_review"
    ticket_id: str
    sector: str
    unit: str
    user_id: str
    weight_final: float
    reason: str

class ExpiredEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_type: Literal["record.expired"] = "record.expired"
    ticket_id: str
    sector: str
    unit: str
    reviewer_id: str
    user_id: str
    expired_at: datetime

class CostAlertEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_type: Literal["cost.alert.fired"] = "cost.alert.fired"
    threshold_usd: float
    cumulative_usd: float
    period_start: datetime
    period_end: datetime

NotificationEvent = Union[SchemaUpdatedEvent, PendingReviewEvent, ExpiredEvent, CostAlertEvent]
```

### Discord webhook payload contract

各 event → Discord embed の 1:1 マッピング。

```python
def to_discord_payload(event: NotificationEvent) -> dict:
    # 共通: title = event_type, color = severity, fields = event の全プロパティ
    # PII Scrubber 適用後に POST
    ...
```

---

## 6. FastAPI endpoints

```
POST   /turn                       -> TurnResponse                        # Req 4, 2.7
DELETE /turn/{turn_id}             -> {ok: true}                          # Req 7
GET    /schemas                    -> list[SchemaFieldDoc]                # Req 1, 2 (M-7)
POST   /schemas                    -> SchemaField                         # Req 1
PATCH  /schemas/{id}               -> SchemaField                         # Req 2
POST   /schemas/{id}/active        -> SchemaAuditEntry                    # Req 2 (M-8)
POST   /schemas/bulk-import        -> list[SchemaField]                   # Req 3
GET    /schemas/history            -> list[SchemaAuditEntry]              # Req 2.6
GET    /retrieve                   -> RetrieveResponse                    # Req 6
GET    /citations/{id}             -> CitationDetail                      # Req 6.5
GET    /reviews                    -> list[FormalizationTicket]           # Req 9
GET    /reviews/conflict           -> list[FormalizationTicket]           # Req 10
POST   /reviews/{id}/lock          -> {locked_until}                      # Req 9.10
POST   /reviews/{id}/decision      -> CorpusUpsertResult                  # Req 9
POST   /reviews/{id}/conflict      -> ConflictResolution                  # Req 10
POST   /hearout/{session}/respond  -> HearoutTurn                         # Req 5
POST   /hearout/{session}/skip     -> HearoutRecord                       # Req 5.7
GET    /healthz                    -> {ok: true}
```

```python
# app/contracts/http.py
class TurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    user_id: str
    sector: str
    unit: str
    session_id: str
    user_content: str
    redact: bool = False

class CitationRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: str
    schema_field_id: str
    weight: float
    superseded_by: Optional[str] = None

class SchemaUpdateBanner(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    unseen_revision_ids: list[int]
    changed_fields_summary: str
    history_url: str

class TurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    turn_id: str
    ai_response: str
    self_critic_score: float
    citations: list[CitationRef]
    schema_update_banner: Optional[SchemaUpdateBanner] = None
    gap_detected: bool

class RetrieveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    records: list[CitationRef]
    conflicts: list[dict]  # [{schema_field_id, alt_count}]

# --- M-7: GET /schemas list -------------------------------------------------
# Query: ?sector=<s>&unit=<u>&active_only=true (default)
# Auth:  require_admin_role (header stub today → Entra OIDC)
# Returns: list[SchemaFieldDoc] sorted by field_name. Replaces the prior
# Admin-UI workaround of replaying /schemas/history to derive current state.

# --- M-8: POST /schemas/{id}/active formalized ------------------------------
# Query: ?pk=<sector#unit>      (REQUIRED — partition key for direct lookup)
# Body:
class SetActiveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    is_active: bool
    reason: Optional[str] = None
# Returns: SchemaAuditEntry stamped with revision_id + before/after diff.
```

---

## 7. Configuration / Key Vault secrets

```
# Key Vault secrets (kv-hack2026-tyu3o4)
DISCORD_WEBHOOK_URL_SCHEMA_UPDATES
DISCORD_WEBHOOK_URL_PENDING_REVIEW
DISCORD_WEBHOOK_URL_EXPIRED
DISCORD_WEBHOOK_URL_COST_ALERT
COSMOS_CONNECTION_STRING
AISEARCH_ADMIN_KEY
AOAI_API_KEY  # MI 優先、fallback only

# Env vars (Container Apps)
AOAI_ENDPOINT, AOAI_DEPLOYMENT_GPT4O, AOAI_DEPLOYMENT_GPT4OMINI, AOAI_DEPLOYMENT_EMBED
COSMOS_ENDPOINT, COSMOS_DATABASE=dialogue_delta
AISEARCH_ENDPOINT, AISEARCH_INDEX=corpus-{env}
FOUNDRY_WORKFLOW_ID, FOUNDRY_PROJECT
APPINSIGHTS_CONNECTION_STRING
KEY_VAULT_URI=https://kv-hack2026-tyu3o4.vault.azure.net/
ENV=dev|prod
```

---

## 8. Folder layout（worktree merge を考慮）

```
scaffold/
  app/
    contracts/        # ★ 本書の Python 実体 (本書 freeze 後すぐ実装)
      common.py
      cosmos.py
      agents.py
      events.py
      http.py
    repos/            # Cosmos CRUD per collection
      schemas.py, schema_audit_log.py, ...
    agents/
      schema_manager/   # WT-C
      delta_detector/   # WT-D
      hearout/          # WT-D
      formalization/    # WT-D
      truth_judgment/   # WT-D
      notification/     # WT-B
      schema_gate/      # WT-B
    api/                # WT-E
      turn.py, schemas.py, reviews.py, retrieval.py, citations.py, hearout.py
    util/
      pii.py, cost.py, telemetry.py, kv.py, embedding.py
    main.py             # FastAPI bootstrap (既存)
  ui/
    admin/              # WT-C  (React Vite SPA)
    chat/               # WT-E
    review/             # WT-E
  infra/
    modules/
      cosmos.bicep      # WT-A
      aisearch.bicep    # WT-A
      keyvault-secrets.bicep  # WT-A
      containerapps.bicep     # WT-A
      foundry.bicep           # WT-A
    main.bicep
  tests/                # 明日着手（today: skip）
```

### 衝突回避ルール

- `app/contracts/` は本書直後に **mainline 単独 commit**。各 WT は read-only として import。
- `app/main.py` への route 追加は `app/api/{name}.py` を作って `app.include_router()`。各 WT が `main.py` を編集しないこと。
- `infra/main.bicep` への module 参照追加は WT-A 単独。他 WT は `infra/modules/*` を作るだけにする。
- `pyproject.toml` / `package.json` の依存追加は WT-A が一括反映（他 WT は変更リスト .md で申告）。
- 共通 util (`pii`, `cost`, `kv`) は WT-B が先行実装、他 WT は import only。

---

## 9. TDD/EDD policy（今日は no-test 実装、明日 TDD 着手）

| 領域 | 明日の TDD 対象 | EDD 対象 |
|------|----------------|---------|
| weight calc, cooldown, gate, partition filter, redact mask, webhook retry | ★ 単体テスト | – |
| schema CRUD / audit | ★ Cosmos in-memory fake で I/O テスト | – |
| Delta gap threshold | ★ ルール部分 | prompt 部分 |
| Hearout 5W1H, Formalization narrative | – | 対人 eyeball + capture-replay |
| Truth Judgment ensemble | golden set 20 件 | – |
| UI flow | – | Playwright smoke + 目視 |
| MAF / Foundry integration | – | integration-test driven |

---

## 10. Definition of Done (今日 = 5/25 中)

- ✅ contracts.md merged
- ✅ `app/contracts/*.py` 実装（本書の Python 化）
- ✅ WT-A infra Bicep modules 全て差分プラン green
- ✅ WT-B Notification Dispatcher + Schema Gate のコード一式（テストなし）
- ✅ WT-C Schema Manager + Admin UI のコード一式（テストなし）
- ✅ WT-D Delta + Hearout + Formalization + TJ のコード一式（テストなし）
- ✅ WT-E Chat UI + Retrieval + Review UI のコード一式（テストなし）

明日（5/26）: TDD layer 着手 + integration E2E + EDD prompt 調整 + demo dry run。
