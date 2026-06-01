"""App Insights wrapper using azure-monitor-opentelemetry. Lazy init.

Metric names follow design.md §7.
"""
from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any, Optional

logger = logging.getLogger(__name__)

_initialized = False
_init_lock = Lock()
_meter: Any = None
_metrics_cache: dict[str, Any] = {}


def _ensure_initialized() -> None:
    global _initialized, _meter
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        conn = os.environ.get(
            "APPLICATIONINSIGHTS_CONNECTION_STRING"
        ) or os.environ.get("APPINSIGHTS_CONNECTION_STRING")
        if not conn:
            logger.info("App Insights connection string not set; telemetry no-op")
            _initialized = True
            return
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            from opentelemetry import metrics

            configure_azure_monitor(connection_string=conn)
            _meter = metrics.get_meter("dialogue-delta-formalization")
        except Exception as exc:  # pragma: no cover - degraded mode
            logger.warning("Telemetry init failed: %s", exc)
        _initialized = True


def emit_metric(
    name: str, value: float, properties: Optional[dict[str, Any]] = None
) -> None:
    """Record a metric observation. Silent no-op if telemetry not configured."""
    _ensure_initialized()
    if _meter is None:
        logger.debug("metric %s=%s props=%s (no-op)", name, value, properties)
        return
    try:
        counter = _metrics_cache.get(name)
        if counter is None:
            counter = _meter.create_counter(name)
            _metrics_cache[name] = counter
        counter.add(value, attributes=properties or {})
    except Exception as exc:  # pragma: no cover - degraded mode
        logger.warning("emit_metric failed for %s: %s", name, exc)
