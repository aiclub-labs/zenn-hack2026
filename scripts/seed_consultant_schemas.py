"""Seed: 5 schema fields for general#general (consultant tacit pivot).

Pair with seed_consultant_tacit.py — that script writes records whose
``schema_field_id`` points at these 5 fields. This script writes the
schema docs themselves directly into the Cosmos ``schemas`` container,
plus a matching ``schema_audit_log`` create entry.

Usage:
  COSMOS_ENDPOINT=https://cdb-hack2026-...documents.azure.com:443/ \
  COSMOS_DB=dialogue_delta \
  python scripts/seed_consultant_schemas.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

PK = "general#general"
SECTOR, UNIT = "general", "general"
ACTOR = "seed-consultant-tacit"

FIELDS = [
    {
        "id": "sf_excel_formula_technique",
        "field_name": "Excel 数式テクニック",
        "description": (
            "LET / LAMBDA / 配列数式など、保守可能な Excel 数式の書き方ノウハウ。"
            "後任引継ぎと提案フェーズの再利用性を上げる目的。"
        ),
        "expected_value_type": "string",
        "example": "LET で中間値に名前を付け、ネスト 5 階の INDEX/MATCH を上から読める形に分解する。",
        "ai_baseline_assumption": (
            "クライアント提出物は Excel 中心。VBA は環境制約で使えないことが多く、"
            "365 関数 (LET/LAMBDA/XLOOKUP) を疑似スクリプトとして使う。"
        ),
    },
    {
        "id": "sf_power_query_recipe",
        "field_name": "Power Query レシピ",
        "description": (
            "M 言語ベースの前処理レシピ。日付・通貨・ピボット展開など、"
            "クライアント生データ → 集計可能形までの繰り返し変換を再利用する。"
        ),
        "expected_value_type": "string",
        "example": "日付文字列 'R7.4.1' → Date 型化 を Table.TransformColumns で 1 ステップに圧縮。",
        "ai_baseline_assumption": (
            "前処理は Power Query で行い、ピボット集計は Excel/Power Pivot に渡す。"
            "提案フェーズでクライアントから貰う生データのフォーマットは案件ごとに揺れる。"
        ),
    },
    {
        "id": "sf_office_scripts_macro",
        "field_name": "Office Scripts マクロ",
        "description": (
            "M365 ネイティブの TypeScript ベース自動化。VBA 代替として "
            "Power Automate から呼べる粒度で書く。"
        ),
        "expected_value_type": "string",
        "example": "テーブル → JSON 化スクリプトを Power Automate Flow から callMacro で叩く。",
        "ai_baseline_assumption": (
            "クライアント環境で VBA が禁止されているケースが増加。"
            "Office Scripts は M365 標準で動き、Power Automate 連携が前提。"
        ),
    },
    {
        "id": "sf_copilot_prompt_pattern",
        "field_name": "Copilot プロンプトパターン",
        "description": (
            "M365 Copilot (Word / Excel / PowerPoint / Teams) で再利用する"
            "プロンプト雛形。役割定義 + 出力フォーマット指定の二段構成が基本。"
        ),
        "expected_value_type": "string",
        "example": "議事録: 役割=書記 / 出力=「結論・決定・Next Action」3 ブロック固定。",
        "ai_baseline_assumption": (
            "Copilot は社内導入が進む一方、業務ユーザーは zero-shot 投入になりがち。"
            "プロンプト構造のテンプレ化で出力の安定性を担保する。"
        ),
    },
    {
        "id": "sf_power_automate_flow",
        "field_name": "Power Automate フロー",
        "description": (
            "Forms / Teams / Outlook / Excel 間を繋ぐローコードフロー。"
            "通知配信や SLA トラッキングを Excel + Flow の最小構成で組む。"
        ),
        "expected_value_type": "string",
        "example": "Forms 回答 → Teams 通知 + Excel テーブル追記の 2-アクション構成。",
        "ai_baseline_assumption": (
            "サーバーレス基盤を立てるほどではない業務自動化の主戦場。"
            "コネクタ制限 (per-user/per-flow) を踏まえて設計する。"
        ),
    },
]


async def seed(endpoint: str, db_name: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    credential = DefaultAzureCredential()
    async with CosmosClient(endpoint, credential=credential) as client:
        db = client.get_database_client(db_name)
        schemas = db.get_container_client("schemas")
        audit = db.get_container_client("schema_audit_log")
        for f in FIELDS:
            doc = {
                "id": f["id"],
                "pk": PK,
                "sector": SECTOR,
                "unit": UNIT,
                "field_name": f["field_name"],
                "description": f["description"],
                "expected_value_type": f["expected_value_type"],
                "example": f["example"],
                "ai_baseline_assumption": f["ai_baseline_assumption"],
                "is_active": True,
                "revision_id": 1,
                "updated_at": now,
                "updated_by": ACTOR,
            }
            await schemas.upsert_item(doc)
            audit_doc = {
                "id": str(uuid.uuid4()),
                "pk": PK,
                "schema_field_id": f["id"],
                "revision_id": 1,
                "change_type": "create",
                "diff": {
                    "field_name": {"before": None, "after": f["field_name"]},
                    "description": {"before": None, "after": f["description"]},
                },
                "reason": "consultant tacit pivot seed",
                "changed_by": ACTOR,
                "changed_at": now,
            }
            await audit.upsert_item(audit_doc)
            print(f"  upserted {f['id']}")
    await credential.close()
    return 0


def main() -> int:
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    db_name = os.environ.get("COSMOS_DB", "dialogue_delta")
    if not endpoint:
        print("ERROR: COSMOS_ENDPOINT env var required", file=sys.stderr)
        return 2
    print(f"seeding {len(FIELDS)} schema fields into {db_name} (pk={PK})")
    return asyncio.run(seed(endpoint, db_name))


if __name__ == "__main__":
    raise SystemExit(main())
