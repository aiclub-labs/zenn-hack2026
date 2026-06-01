"""PII scrubbing — regex masking + optional LLM fallback (Req 16.6 / Issue #37).

Applied immediately before any external emission.
Patterns:
  - email addresses
  - phone numbers (JP / intl)
  - numeric IDs >= 6 digits
  - JP-style full names (姓 + space + 名, simple heuristic)

`scrub()` is the pure regex pass — safe to call from sync code.
`scrub_async()` adds an LLM pass over residual text (catches kanji names
without space, romaji names, customer/case codes the regex misses).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# LLM fallback pass (Req 16.6 / Issue #37)
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LLM_SCRUB_SYSTEM_PROMPT = (
    "あなたは PII redactor です。入力テキストに含まれる以下を [REDACTED_NAME] / "
    "[REDACTED_ID] / [REDACTED_EMAIL] / [REDACTED_PHONE] のいずれかで置換してください:\n"
    "- 個人氏名 (漢字/カナ/ローマ字、スペース有無問わず)\n"
    "- 顧客名・案件コード (例: ABC-12345, 案件#789)\n"
    "- メールアドレス・電話番号・6桁以上の数値ID\n"
    "業務用語・製品名・地名・部署名・一般名詞は置換しないこと。\n"
    'JSON で {"scrubbed_text": "..."} のみ返答。'
)

# Skip LLM when text is too short/long to be cost-worthy or PII-bearing.
_LLM_MIN_CHARS = 8
_LLM_MAX_CHARS = 4000


async def _scrub_text_with_llm(text: str) -> str:
    if not text or len(text) < _LLM_MIN_CHARS or len(text) > _LLM_MAX_CHARS:
        return text
    # Already-fully-masked strings: no signal left for LLM.
    if "[REDACTED" in text and not _CJK_RE.search(text):
        return text

    from app.util.aoai_chat import chat_client, deployment_small

    try:
        client = chat_client()
        resp = await client.chat.completions.create(
            model=deployment_small(),
            messages=[
                {"role": "system", "content": _LLM_SCRUB_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            max_completion_tokens=min(800, len(text) + 100),
            response_format={"type": "json_object"},
        )
        parsed = json.loads(resp.choices[0].message.content or "{}")
        scrubbed = parsed.get("scrubbed_text")
        if isinstance(scrubbed, str) and scrubbed:
            return scrubbed
    except Exception as exc:  # noqa: BLE001
        logger.debug("LLM PII scrub failed, falling back to regex-only: %s", exc)
    return text


async def _scrub_value_async(value: Any) -> Any:
    if isinstance(value, str):
        return await _scrub_text_with_llm(value)
    if isinstance(value, dict):
        return {k: await _scrub_value_async(v) for k, v in value.items()}  # type: ignore[misc]
    if isinstance(value, list):
        return [await _scrub_value_async(v) for v in value]  # type: ignore[misc]
    if isinstance(value, tuple):
        return tuple([await _scrub_value_async(v) for v in value])  # type: ignore[misc]
    return value


async def scrub_async(
    payload: dict[str, Any], *, use_llm: bool = True
) -> dict[str, Any]:
    """Two-pass scrub: regex (sync) → optional LLM pass over residual strings.

    `use_llm=False` makes this equivalent to ``scrub()`` (no network I/O).
    LLM call uses ``deployment_small`` (gpt-4o-mini) at temperature 0 and is
    best-effort: on any failure the regex-only result is returned.
    """
    base = scrub(payload)
    if not use_llm:
        return base
    result = await _scrub_value_async(base)
    return result  # type: ignore[no-any-return]
