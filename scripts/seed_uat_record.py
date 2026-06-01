"""One-shot UAT seed: insert a substantive surface-treatment record for
manufacturing-s8b/line-A so Delta Detector has a citable neighbor.

LOCAL DEVELOPMENT BOOTSTRAP ONLY. Production runtime uses Managed Identity
(see app/util/aisearch.py, Req 17.1 / Issue #40). This script uses admin keys
purely because it's a one-shot seed run from an operator workstation that
may not yet have RBAC role assignments propagated.

Reads AOAI key from env AOAI_API_KEY, AISEARCH key from AISEARCH_ADMIN_KEY.
Reads endpoints from azd env.

Usage:
  AOAI_API_KEY=... AISEARCH_ADMIN_KEY=... python scripts/seed_uat_record.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

AOAI_ENDPOINT = "https://aoai-hack2026.openai.azure.com"
AOAI_DEPLOY = "text-embedding-3-small"
AOAI_KEY = os.environ["AOAI_API_KEY"]

SEARCH_EP = "https://srch-hack2026-dev-ytzykj.search.windows.net"
SEARCH_KEY = os.environ["AISEARCH_ADMIN_KEY"]
INDEX = "corpus-dev"

CONTENT = (
    "ライン A の表面処理プロセス: 脱脂 → 酸洗 → 化成皮膜 (りん酸亜鉛) → "
    "電着塗装 (ED) → 焼付乾燥 170℃ × 20 分。塗装膜厚は 18-22 μm が目標。"
    "焼付温度が 165℃ を下回ると密着不良 (クロスカット試験で剥離)、"
    "175℃ を超えると黄変・脆化リスクが上がる。"
    "工程間搬送はオーバーヘッドコンベア、滞留時間は最大 8 分まで。"
)
ATOMIC_CLAIMS = [
    "焼付温度 170℃ × 20 分が標準",
    "膜厚目標 18-22 μm",
    "165℃ 未満で密着不良",
    "175℃ 超で黄変・脆化",
]


def embed(text: str) -> list[float]:
    req = urllib.request.Request(
        f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_DEPLOY}/embeddings?api-version=2024-08-01-preview",
        data=json.dumps({"input": text}).encode("utf-8"),
        headers={"api-key": AOAI_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    return body["data"][0]["embedding"]


def upload(doc: dict) -> None:
    payload = {"value": [{"@search.action": "mergeOrUpload", **doc}]}
    req = urllib.request.Request(
        f"{SEARCH_EP}/indexes/{INDEX}/docs/index?api-version=2024-07-01",
        data=json.dumps(payload).encode("utf-8"),
        headers={"api-key": SEARCH_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        print(r.status, r.read().decode("utf-8"))


def main() -> int:
    vector = embed(CONTENT)
    print(f"embedded {len(vector)}-dim")
    doc = {
        "id": "uat-seed-surface-treatment",
        "sector": "manufacturing-s8b",
        "unit": "line-A",
        "pk": "manufacturing-s8b#line-A",
        "schema_field_id": "sf_surface_treatment",
        "content": CONTENT,
        "atomic_claims": ATOMIC_CLAIMS,
        "weight_final": 0.8,
        "shareability": "unit",
        "is_active": True,
        "superseded_by": "",
        "created_at": "2026-05-28T06:00:00Z",
        "vector": vector,
    }
    upload(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
