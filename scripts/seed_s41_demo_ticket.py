"""Seed 1 hearout record + 1 formalization ticket for S4.1 demo path.

Bypasses the gap-detector flow when self-critic stays too high to trigger
hearout automatically. Use to demo C1 (review) → B3 (citation) end-to-end.

Tenant: manufacturing-s8b / line-A / haruka@example.com
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

ENDPOINT = os.environ.get(
    "COSMOS_ENDPOINT",
    "https://cosmos-hack2026-dev-ytzykj.documents.azure.com:443/",
)
DATABASE = os.environ.get("COSMOS_DATABASE", "dialogue_delta")

TENANT_PK = "manufacturing-s8b#line-A"
USER_ID = "haruka@example.com"


async def main() -> int:
    credential = DefaultAzureCredential()
    client = CosmosClient(ENDPOINT, credential=credential)
    db = client.get_database_client(DATABASE)
    hearout_c = db.get_container_client("hearout_records")
    queue_c = db.get_container_client("formalization_queue")

    now = datetime.now(timezone.utc)
    hearout_id = f"hr-{uuid.uuid4().hex[:8]}"
    ticket_id = f"fq-{uuid.uuid4().hex[:8]}"
    gap_event_id = f"de-{uuid.uuid4().hex[:8]}"

    hearout_doc = {
        "id": hearout_id,
        "pk": TENANT_PK,
        "gap_event_id": gap_event_id,
        "session_id": hearout_id,
        "transcript": [
            {"role": "ai", "content": "5/22 ライン A クラック、いつ気付いた?"},
            {"role": "user", "content": "朝のシフト切替直後、08:15 ごろ"},
            {"role": "ai", "content": "どの工程で発見した?"},
            {
                "role": "user",
                "content": "表面処理後の目視検査ライン (拡大鏡使用)",
            },
            {"role": "ai", "content": "原因として何を疑った?"},
            {"role": "user", "content": "焼付温度ドリフト (165℃ 付近で密着不良)"},
            {"role": "ai", "content": "暫定対応は何を決めた?"},
            {
                "role": "user",
                "content": "焼付温度を 172℃ に上げ、膜厚再測定を全数実施",
            },
        ],
        "who": USER_ID,
        "what": "ライン A 表面処理後クラック、焼付温度ドリフト疑い",
        "when": "2026-05-22 08:15",
        "where": "ライン A 目視検査 (拡大鏡)",
        "why": "焼付温度 165℃ 付近で密着不良",
        "how": "焼付 172℃ 上げ + 全数膜厚再測定",
        "outcome": "completed",
        "turn_count": 4,
        "created_at": now.isoformat(),
    }

    ticket_doc = {
        "id": ticket_id,
        "pk": TENANT_PK,
        "hearout_id": hearout_id,
        "weight_a": 0.82,
        "weight_b": 1.0,
        "weight_c": 1.0,
        "weight_final": 0.82,
        "status": "pending_review",
        "created_at": now.isoformat(),
    }

    await hearout_c.upsert_item(hearout_doc)
    await queue_c.upsert_item(ticket_doc)
    print(f"seeded hearout={hearout_id} ticket={ticket_id} pk={TENANT_PK}")
    await client.close()
    await credential.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
