"""watch_cosmos.py — E2E スモーク中に主要 container の doc 件数を 5s ごとに print。

使い方:
    COSMOS_ENDPOINT=https://cdb-hack2026-...documents.azure.com:443/ \
    COSMOS_DB=hackdb \
    python scripts/watch_cosmos.py

Auth: DefaultAzureCredential (Managed Identity / az login どちらでも)。
contracts.md §2 の 12 container を順に SELECT VALUE COUNT(1) で叩く。
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

CONTAINERS = [
    "schemas",
    "schema_audit_log",
    "dialogue_turns",
    "delta_events",
    "hearout_records",
    "formalization_queue",
    "corpus_meta",
    "citation_audit_log",
    "truth_judgment_logs",
    "conflicts",
    "cost_ledger",
    "error_logs",
]


async def snapshot(client: CosmosClient, db_name: str) -> dict[str, int | str]:
    db = client.get_database_client(db_name)
    out: dict[str, int | str] = {}
    for name in CONTAINERS:
        try:
            cont = db.get_container_client(name)
            items = cont.query_items(query="SELECT VALUE COUNT(1) FROM c")
            total = 0
            async for v in items:
                total = int(v)
                break
            out[name] = total
        except Exception as exc:
            out[name] = f"ERR:{type(exc).__name__}"
    return out


async def main() -> int:
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    db_name = os.environ.get("COSMOS_DB", "hackdb")
    interval = float(os.environ.get("WATCH_INTERVAL", "5"))
    if not endpoint:
        print("ERR: COSMOS_ENDPOINT not set", file=sys.stderr)
        return 1

    cred = DefaultAzureCredential()
    async with CosmosClient(endpoint, credential=cred) as client:
        prev: dict[str, int | str] = {}
        while True:
            cur = await snapshot(client, db_name)
            ts = datetime.now().strftime("%H:%M:%S")
            line = " | ".join(
                f"{k}={cur[k]}{'*' if prev.get(k) != cur[k] else ''}" for k in CONTAINERS
            )
            print(f"[{ts}] {line}", flush=True)
            prev = cur
            time.sleep(interval)


if __name__ == "__main__":
    import asyncio

    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(0)
