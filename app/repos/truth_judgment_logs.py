"""Cosmos repo for `truth_judgment_logs` (Req 8, 14)."""
from __future__ import annotations

from typing import Any

from azure.cosmos.aio import ContainerProxy

from app.contracts.cosmos import TruthJudgmentLog


class TruthJudgmentLogsRepo:
    container_name = "truth_judgment_logs"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def append(self, log: TruthJudgmentLog) -> TruthJudgmentLog:
        await self._c.upsert_item(log.model_dump(mode="json"))
        return log

    async def get_for_record(
        self, pk: str, record_id: str, limit: int = 10
    ) -> list[TruthJudgmentLog]:
        query = (
            f"SELECT TOP {int(limit)} * FROM c WHERE c.pk = @pk "
            "AND c.record_id = @rid ORDER BY c._ts DESC"
        )
        params: list[dict[str, Any]] = [
            {"name": "@pk", "value": pk},
            {"name": "@rid", "value": record_id},
        ]
        out: list[TruthJudgmentLog] = []
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            out.append(TruthJudgmentLog.model_validate(it))
        return out
