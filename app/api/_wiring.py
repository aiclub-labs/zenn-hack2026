"""End-of-day merge wiring: instantiate real WT-B/C/D classes and register
them via `app.api._deps.set_*`. Called from `app.main` lifespan.

M-1 (resolved): SchemaGateAdapter no longer holds in-process state. The
session's acked-revision watermark lives in ``dialogue_turns`` and is
read/written via ``DialogueTurnsRepo``.
M-6 (resolved): ``DialogueTurnsRepo`` is registered on _deps so turn.py
can append USER + ASSISTANT turn docs.
"""
from __future__ import annotations

from typing import Optional

from app.api import _deps
from app.config import settings
from app.contracts.common import Tenant, utcnow
from app.contracts.http import SchemaUpdateBanner


# ---- Adapter: WT-B SchemaRevisionGate -> WT-E SchemaRevisionGateI -----------
#
# WT-B class is session-centric:    check(session_id, tenant, current_seen_revision)
# WT-E protocol is now session-aware: banner_for(user_id, tenant, session_id)
# and acknowledge(user_id, tenant, session_id, turn_id).
#
# Adapter responsibilities:
#   * forward (session_id, tenant) to the real gate
#   * read the session's last acked revision from dialogue_turns (NOT in-proc)
#   * stamp the specific turn_id on ack — not the latest turn — so ack is
#     tied to the turn that displayed the banner

class SchemaGateAdapter:
    def __init__(self, real_gate, schemas_repo, turns_repo) -> None:  # type: ignore[no-untyped-def]
        self._gate = real_gate
        self._schemas = schemas_repo
        self._turns = turns_repo
        # Per-session banner cache used only to recover unseen_revision_ids
        # on ack. Safe because banner re-derives from store on every check().
        self._banner_cache: dict[tuple[str, str], SchemaUpdateBanner] = {}

    async def banner_for(
        self, user_id: str, tenant: Tenant, session_id: str
    ) -> Optional[SchemaUpdateBanner]:
        last_seen = await self._turns.get_latest_acked_revision(
            session_id, tenant.pk
        )
        banner = await self._gate.check(session_id, tenant, last_seen)
        if banner is not None:
            self._banner_cache[(session_id, tenant.pk)] = banner
        return banner

    async def acknowledge(
        self,
        user_id: str,
        tenant: Tenant,
        session_id: str,
        turn_id: str,
    ) -> None:
        banner = self._banner_cache.pop((session_id, tenant.pk), None)
        if banner is None or not banner.unseen_revision_ids:
            # Fallback: ack to the tenant's current latest.
            latest = await self._schemas.latest_revision_for_tenant(tenant.pk)
            if latest == 0:
                return
            revision_id = latest
        else:
            revision_id = max(banner.unseen_revision_ids)
        await self._turns.set_revision_seen(
            session_id=session_id,
            pk=tenant.pk,
            turn_id=turn_id,
            revision_id=revision_id,
            ts=utcnow(),
        )

    async def is_acked(
        self, user_id: str, tenant: Tenant, session_id: str
    ) -> bool:
        last_seen = await self._turns.get_latest_acked_revision(
            session_id, tenant.pk
        )
        latest = await self._schemas.latest_revision_for_tenant(tenant.pk)
        return last_seen >= latest


def build_and_register() -> None:
    """Construct real instances and register via _deps setters.

    Falls back silently to the no-op stubs from _deps.py if any optional
    Azure SDK dep is not installed locally (so dev boot still works).
    """
    try:
        import httpx

        from app.agents.notification.dispatcher import NotificationDispatcher
        from app.agents.schema_gate.gate import SchemaRevisionGate
        from app.repos._base import InMemoryContainer
        from app.repos.dialogue_turns import DialogueTurnsRepo
        from app.repos.error_logs import ErrorLogsRepo
        from app.repos.schemas import SchemasRepo
        from app.util.kv import KeyVaultClient
        from app.util.cosmos import get_container as _cosmos_container
    except Exception as exc:  # pragma: no cover
        import logging

        logging.getLogger("wiring").warning(
            "Wiring deferred — optional deps missing: %s. Stubs remain active.",
            exc,
        )
        return

    def _container(name: str):  # type: ignore[no-untyped-def]
        c = _cosmos_container(name)
        if c is None:
            import logging

            logging.getLogger("wiring").info(
                "cosmos.%s unavailable — falling back to InMemory", name
            )
            return InMemoryContainer()
        return c

    schemas_container = _container("schemas")
    turns_container = _container("dialogue_turns")
    error_container = _container("error_logs")

    schemas_repo = SchemasRepo(schemas_container)
    turns_repo = DialogueTurnsRepo(turns_container)
    error_repo = ErrorLogsRepo(error_container)

    # M-6: register dialogue_turns repo so turn.py can append.
    _deps.set_dialogue_turns_repo(turns_repo)

    # M-7: expose SchemasRepo to GET /schemas (list) endpoint.
    _deps.set_schemas_repo(schemas_repo)

    kv = KeyVaultClient(settings.key_vault_uri) if getattr(settings, "key_vault_uri", None) else None
    http = httpx.AsyncClient(timeout=10.0)

    # WT-D: ErrorLog repo wired (was TODO in WT-B)
    notifier = NotificationDispatcher(
        kv=kv,
        http_client=http,
        error_logs_repo=error_repo,
        admin_pk="hack#admin",
    )

    real_gate = SchemaRevisionGate(
        schemas_repo=schemas_repo,
        dialogue_turns_repo=turns_repo,
        history_url_template="/admin/schemas/history?sector={sector}&unit={unit}",
    )
    _deps.set_schema_gate(SchemaGateAdapter(real_gate, schemas_repo, turns_repo))

    # ---- WT-C: SchemaManagerAgent — override app.api.schemas.get_agent -----
    try:
        from app.agents.schema_manager.agent import SchemaManagerAgent
        from app.api import schemas as schemas_api
        from app.repos.schema_audit_log import SchemaAuditLogRepo

        audit_repo = SchemaAuditLogRepo(_container("schema_audit_log"))
        schema_agent = SchemaManagerAgent(
            schemas=schemas_repo, audit=audit_repo, dispatcher=notifier
        )
        schemas_api.set_agent(schema_agent)
    except Exception as exc:  # pragma: no cover
        import logging

        logging.getLogger("wiring").warning(
            "SchemaManagerAgent not wired: %s", exc
        )

    # ---- WT-D agents: try-import, register if available ----
    try:
        from app.agents.formalization.agent import FormalizationAgent
        from app.agents.hearout.agent import HearoutAgent
        from app.agents.truth_judgment.module import TruthJudgmentModule
        from app.repos.citation_audit_log import CitationAuditLogRepo
        from app.repos.corpus_meta import CorpusMetaRepo
        from app.repos.delta_events import DeltaEventsRepo
        from app.repos.formalization_queue import FormalizationQueueRepo
        from app.repos.hearout_records import HearoutRecordsRepo
        from app.repos.truth_judgment_logs import TruthJudgmentLogsRepo
        from app.util.aisearch import CorpusIndex

        hearout_repo = HearoutRecordsRepo(_container("hearout_records"))
        queue_repo = FormalizationQueueRepo(_container("formalization_queue"))
        corpus_meta = CorpusMetaRepo(_container("corpus_meta"))
        citation_audit = CitationAuditLogRepo(_container("citation_audit_log"))
        delta_events_repo = DeltaEventsRepo(_container("delta_events"))
        tj_log = TruthJudgmentLogsRepo(_container("truth_judgment_logs"))
        corpus = CorpusIndex()

        try:
            from app.util.aoai_chat import chat_client as _aoai
            llm = _aoai()
        except Exception:  # pragma: no cover
            llm = None

        tj_module = TruthJudgmentModule(tj_log_repo=tj_log, corpus=corpus, llm_client=llm)
        hearout_agent = HearoutAgent(hearout_repo=hearout_repo, llm_client=llm)

        # ---- M-3: gap_event_id -> user_id resolver --------------------------
        # DialogueTurn lacks an explicit user_id field; we use ``session_id``
        # as the originating-user proxy (1 session ↔ 1 signed-in user in our
        # UX). When the contract gains a real user_id field, swap the return.
        async def _resolve_user(gap_event_id: str, pk: str) -> str:
            delta = await delta_events_repo.get(gap_event_id, pk)
            if delta is None:
                return gap_event_id
            turn = await turns_repo.get(delta.turn_id, pk)
            if turn is None:
                return gap_event_id
            return turn.session_id  # user proxy — see note above

        # ---- M-4: gap_event_id -> schema_field_id resolver ------------------
        async def _resolve_schema_field(gap_event_id: str, pk: str) -> str:
            delta = await delta_events_repo.get(gap_event_id, pk)
            if delta is None or delta.schema_field_id is None:
                return ""
            return delta.schema_field_id

        formalization_agent = FormalizationAgent(
            queue_repo=queue_repo,
            hearout_repo=hearout_repo,
            corpus_meta_repo=corpus_meta,
            citation_audit_repo=citation_audit,
            delta_events_repo=delta_events_repo,
            corpus=corpus,
            truth_judgment=tj_module,
            notifier=notifier,
            user_resolver=_resolve_user,
            schema_field_resolver=_resolve_schema_field,
        )
        _deps.set_hearout_agent(hearout_agent)
        _deps.set_formalization_agent(formalization_agent)
        _deps.set_formalization_queue_repo(queue_repo)

        # ---- M-5: DeltaDetectorAgent with bound repo callables --------------
        try:
            from app.agents.delta_detector.agent import DeltaDetectorAgent
            from app.repos.schema_candidate_log import SchemaCandidateLogRepo

            schema_candidates = SchemaCandidateLogRepo(_container("schema_candidate_log"))

            async def _load_active(pk: str):  # type: ignore[no-untyped-def]
                return await schemas_repo.list_active(pk)

            async def _recent_turn_ids(pk: str, session_id: str, limit: int):  # type: ignore[no-untyped-def]
                # Detector calls (pk, session_id, limit); repo expects
                # (session_id, pk, limit). Rebind explicitly.
                return await turns_repo.recent_session_turn_ids(
                    session_id, pk, limit
                )

            delta_detector = DeltaDetectorAgent(
                delta_events_repo=delta_events_repo,
                schema_candidate_repo=schema_candidates,
                load_active_schemas=_load_active,
                recent_session_turn_ids=_recent_turn_ids,
                llm_client=llm,
            )
            _deps.set_delta_detector(delta_detector)
        except Exception as exc:  # pragma: no cover
            import logging

            logging.getLogger("wiring").warning(
                "DeltaDetectorAgent not wired: %s", exc
            )
    except Exception as exc:  # pragma: no cover
        import logging

        logging.getLogger("wiring").warning(
            "WT-D agents not wired (deferred until azure SDKs present): %s",
            exc,
        )
