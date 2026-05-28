"""PII scrubbing — pure regex masking. No I/O.

Applied immediately before any external emission (Req 16.6).
Patterns:
  - email addresses
  - phone numbers (JP / intl)
  - numeric IDs >= 6 digits
  - JP-style full names (姓 + space + 名, simple heuristic)
"""
from __future__ import annotations

import re
from typing import Any

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone: must have either a + prefix, parens, or an internal separator.
# Bare digit runs (e.g. "123456") fall through to _NUMERIC_ID_RE.
_PHONE_RE = re.compile(
    r"(?<!\d)(?:"
    r"\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{2,4}[-\s]?\d{2,4}"
    r"|\(?\d{2,4}\)?[-\s]\d{2,4}[-\s]\d{3,4}"
    r"|\d{2,4}[-\s]\d{3,4}[-\s]?\d{0,4}"
    r"|0\d{9,10}"
    r")(?!\d)"
)
_NUMERIC_ID_RE = re.compile(r"(?<!\d)\d{6,}(?!\d)")
# Heuristic JP name: 2-4 kanji/kana surname + space + 2-4 kanji/kana given.
_JP_NAME_RE = re.compile(
    r"[\u4e00-\u9fff\u30a0-\u30ff\u3040-\u309f]{1,4}[\s　]"
    r"[\u4e00-\u9fff\u30a0-\u30ff\u3040-\u309f]{1,4}"
)

_MASK_EMAIL = "[REDACTED_EMAIL]"
_MASK_PHONE = "[REDACTED_PHONE]"
_MASK_ID = "[REDACTED_ID]"
_MASK_NAME = "[REDACTED_NAME]"


def _scrub_text(text: str) -> str:
    text = _EMAIL_RE.sub(_MASK_EMAIL, text)
    text = _PHONE_RE.sub(_MASK_PHONE, text)
    text = _NUMERIC_ID_RE.sub(_MASK_ID, text)
    text = _JP_NAME_RE.sub(_MASK_NAME, text)
    return text


def _scrub_value(value: Any) -> Any:
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, dict):
        return {k: _scrub_value(v) for k, v in value.items()}  # type: ignore[misc]
    if isinstance(value, list):
        return [_scrub_value(v) for v in value]  # type: ignore[misc]
    if isinstance(value, tuple):
        return tuple(_scrub_value(v) for v in value)  # type: ignore[misc]
    return value


def scrub(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-scrubbed copy of `payload`. Pure function."""
    result = _scrub_value(payload)
    # _scrub_value preserves dict shape for dict input.
    return result  # type: ignore[no-any-return]
