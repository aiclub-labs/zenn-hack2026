"""reset_tenant.py — UAT 前にテナント単位で Cosmos の動的 doc を削除する。

使い方:
    COSMOS_ENDPOINT=https://cdb-hack2026-...documents.azure.com:443/ \
    COSMOS_DB=hackdb \
    python scripts/reset_tenant.py \
        --sector manufacturing-s8b --unit line-A --confirm

オプション:
    --include-schemas     schemas / schema_audit_log もリセット (baseline 破棄)
    --include-errors      error_logs もリセット
    --dry-run             削除せず件数だけ表示

Auth: DefaultAzureCredential (Managed Identity / az login どちらでも)。
partition key = f"{sector}#{unit}" でフィルタするため他テナントには触れない。
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Iterable

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

# 動的 doc — UAT ごとに必ず消す
DYNAMIC_CONTAINERS = [
    "dialogue_turns",
    "delta_events",
    "hearout_records",
    "formalization_queue",
    "corpus_meta",
    "citation_audit_log",
    "truth_judgment_logs",
    "schema_candidate_log",
]

# baseline — --include-schemas で消す
SCHEMA_CONTAINERS = [
    "schemas",
    "schema_audit_log",
]

ERROR_CONTAINERS = ["error_logs"]


async def wipe_partition(
    client: CosmosClient,
    db_name: str,
    container_name: str,
    pk: str,
    dry_run: bool,
) -> tuple[int, int]:
    db = client.get_database_client(db_name)
    try:
        c = db.get_container_client(container_name)
    except Exception as exc:
        print(f"  [SKIP] {container_name}: {exc}")
        return (0, 0)

    found = 0
    deleted = 0
    try:
        it = c.query_items(
            query="SELECT c.id FROM c WHERE c.pk = @pk",
            parameters=[{"name": "@pk", "value": pk}],
            partition_key=pk,
        )
        async for row in it:
            found += 1
            if dry_run:
                continue
            try:
                await c.delete_item(item=row["id"], partition_key=pk)
                deleted += 1
            except Exception as exc:
                print(f"  [WARN] {container_name}/{row['id']}: {exc}")
    except Exception as exc:
        print(f"  [ERROR] {container_name}: {exc}")
        return (found, deleted)
    return (found, deleted)


async def main(
    endpoint: str,
    db_name: str,
    sector: str,
    unit: str,
    containers: Iterable[str],
    dry_run: bool,
) -> int:
    pk = f"{sector}#{unit}"
    print(f"target: db={db_name} pk={pk} dry_run={dry_run}")
    print(f"containers: {', '.join(containers)}\n")

    credential = DefaultAzureCredential()
    async with CosmosClient(endpoint, credential=credential) as client:
        total_found = 0
        total_deleted = 0
        for name in containers:
            found, deleted = await wipe_partition(
                client, db_name, name, pk, dry_run
            )
            verb = "would delete" if dry_run else "deleted"
            print(f"  {name:24s} found={found:4d} {verb}={deleted:4d}")
            total_found += found
            total_deleted += deleted
        print(
            f"\ntotal: found={total_found} "
            f"{'would delete' if dry_run else 'deleted'}={total_deleted}"
        )
    await credential.close()
    return 0


def cli() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sector", required=True)
    p.add_argument("--unit", required=True)
    p.add_argument("--include-schemas", action="store_true")
    p.add_argument("--include-errors", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--confirm",
        action="store_true",
        help="必須: 削除実行時に明示的に指定 (dry-run 時は不要)",
    )
    args = p.parse_args()

    endpoint = os.environ.get("COSMOS_ENDPOINT")
    db_name = os.environ.get("COSMOS_DB", "dialogue_delta")
    if not endpoint:
        print("ERROR: COSMOS_ENDPOINT env var required", file=sys.stderr)
        return 2
    if not args.dry_run and not args.confirm:
        print("ERROR: --confirm required for destructive run", file=sys.stderr)
        return 2

    containers = list(DYNAMIC_CONTAINERS)
    if args.include_schemas:
        containers += SCHEMA_CONTAINERS
    if args.include_errors:
        containers += ERROR_CONTAINERS

    return asyncio.run(
        main(endpoint, db_name, args.sector, args.unit, containers, args.dry_run)
    )


if __name__ == "__main__":
    raise SystemExit(cli())
