"""Cost cron stub. Daily AOAI token aggregation + threshold check.

Thresholds per contracts.md §5 / design.md §7: $120 warn, $150 hard.
Full App Insights query wiring is WT-D scope; this module owns the
threshold logic + event emission shape.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from app.contracts.common import utcnow
from app.contracts.events import CostAlertEvent

WARN_THRESHOLD_USD: float = 120.0
HARD_THRESHOLD_USD: float = 150.0


async def aggregate_aoai_tokens_daily() -> float:
    """Return cumulative AOAI cost (USD) for the current rolling period.

    Stub: real implementation queries App Insights `customMetrics` for
    `agent.*.tokens` and multiplies by per-deployment rate cards.
    """
    # TODO(WT-D): wire App Insights Kusto query + price table
    return 0.0


def check_thresholds(cumulative: float) -> Optional[CostAlertEvent]:
    """Return a CostAlertEvent if cumulative exceeds warn/hard threshold, else None.

    Caller decides whether to dispatch (avoid duplicate alerts per period).
    """
    if cumulative < WARN_THRESHOLD_USD:
        return None
    threshold = HARD_THRESHOLD_USD if cumulative >= HARD_THRESHOLD_USD else WARN_THRESHOLD_USD
    now = utcnow()
    return CostAlertEvent(
        threshold_usd=threshold,
        cumulative_usd=cumulative,
        period_start=now - timedelta(days=1),
        period_end=now,
    )
