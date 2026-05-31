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

TENANT_PK = "general#general"
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
            {
                "role": "ai",
                "content": "Power Query の日付テキスト揺れ正規化、どの場面で書きました?",
            },
            {
                "role": "user",
                "content": "先週の 提案案件、月次集計の前処理。日付列が '2026/5/1', '2026-05-01', 'May 1 2026' が混在",
            },
            {"role": "ai", "content": "どんな関数で揃えました?"},
            {
                "role": "user",
                "content": "Table.TransformColumns で Text.Replace 二段 + Date.From、その後 try ... otherwise null でガード",
            },
            {"role": "ai", "content": "気をつけたポイントは?"},
            {
                "role": "user",
                "content": "ロケール依存になりがちなので Date.FromText に明示的に 'en-US' を渡す。あと null を残すと downstream で SUM が落ちるので 0 fallback を別列で",
            },
        ],
        "who": USER_ID,
        "what": "Power Query で日付テキスト揺れを Table.TransformColumns + try で正規化する自分のレシピ",
        "when": "2026 年 5 月 提案案件 月次集計フェーズ",
        "where": "Power Query M / Excel データ取得",
        "why": "日付列のロケール / 区切り混在で Date.FromText が随所で落ちるため",
        "how": "Text.Replace 二段で区切り正規化 → Date.FromText with 'en-US' → try otherwise null → 0 fallback 別列",
        "outcome": "completed",
        "turn_count": 3,
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
