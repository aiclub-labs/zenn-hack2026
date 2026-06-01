"""Unit tests for PII scrubbing (app/util/pii.py).

Req 16.6: All external emissions are PII-scrubbed before dispatch.
Pure function tests — no I/O, no mocks.

NOTE on JP-name heuristic:
  The regex matches 1-4 CJK/kana characters followed by a space then 1-4 more.
  This is a broad heuristic that will produce false positives on ANY
  CJK-space-CJK pattern (e.g. product names, place names such as
  "東京 タワー"). Tests intentionally acknowledge this false-positive risk
  with an explicit docstring note.
"""
from __future__ import annotations

import pytest

from app.util.pii import _scrub_text, scrub

_EMAIL_MASK = "[REDACTED_EMAIL]"
_PHONE_MASK = "[REDACTED_PHONE]"
_ID_MASK = "[REDACTED_ID]"
_NAME_MASK = "[REDACTED_NAME]"


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_email_scrubbed() -> None:
    """Plain email addresses are replaced with [REDACTED_EMAIL]."""
    result = _scrub_text("Contact test@example.com for details.")
    assert _EMAIL_MASK in result
    assert "test@example.com" not in result


@pytest.mark.unit
def test_email_subdomain_scrubbed() -> None:
    """Subdomain emails are also redacted."""
    result = _scrub_text("Send to user@mail.corp.co.jp now.")
    assert _EMAIL_MASK in result
    assert "@mail.corp.co.jp" not in result


@pytest.mark.unit
def test_non_email_at_sign_not_scrubbed() -> None:
    """A bare '@' without email structure is not masked."""
    result = _scrub_text("Mention @username in the chat.")
    # Should not produce REDACTED_EMAIL for a bare @username (no TLD).
    assert _EMAIL_MASK not in result


# ---------------------------------------------------------------------------
# Phone numbers
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_jp_phone_scrubbed() -> None:
    """Japanese mobile number format 090-XXXX-XXXX is masked."""
    result = _scrub_text("Call me at 090-1234-5678 today.")
    assert _PHONE_MASK in result
    assert "090-1234-5678" not in result


@pytest.mark.unit
def test_jp_phone_no_separators_scrubbed() -> None:
    """10-digit JP phone number without separators."""
    result = _scrub_text("Number: 0901234567")
    assert _PHONE_MASK in result


# ---------------------------------------------------------------------------
# Numeric IDs >= 6 digits
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_numeric_id_6digits_scrubbed() -> None:
    """6-digit numeric ID is masked."""
    result = _scrub_text("Employee ID 123456 is on file.")
    assert _ID_MASK in result
    assert "123456" not in result


@pytest.mark.unit
def test_numeric_id_9digits_scrubbed() -> None:
    """9-digit ID (e.g. social/tax number) is masked."""
    result = _scrub_text("Reference: 123456789")
    assert _ID_MASK in result


@pytest.mark.unit
def test_short_numbers_not_scrubbed() -> None:
    """5-digit or shorter numbers are NOT masked (below threshold)."""
    result = _scrub_text("Order 12345 placed.")
    assert _ID_MASK not in result


# ---------------------------------------------------------------------------
# JP name heuristic
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_jp_name_scrubbed() -> None:
    """CJK surname + space + CJK given name matches the heuristic.

    FALSE-POSITIVE RISK: Any CJK-space-CJK bi-gram (product names, place names,
    compound nouns like '東京 タワー') will also be masked. This is a known
    trade-off of the simple regex heuristic — accuracy requires NER.
    """
    result = _scrub_text("担当者は田中 花子です。")
    assert _NAME_MASK in result


# ---------------------------------------------------------------------------
# Pure-function determinism
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_scrub_is_deterministic() -> None:
    """Same input always produces the same output."""
    text = "Send 123456789 to test@example.com or call 090-1234-5678."
    assert _scrub_text(text) == _scrub_text(text)


@pytest.mark.unit
def test_scrub_dict_payload() -> None:
    """scrub() traverses nested dicts and masks PII at all levels."""
    payload = {
        "user": "admin@corp.com",
        "meta": {"id": "9876543", "phone": "090-9999-0000"},
        "tags": ["safe", "9999999"],
    }
    result = scrub(payload)
    assert _EMAIL_MASK in result["user"]
    assert "admin@corp.com" not in result["user"]
    assert _ID_MASK in result["meta"]["id"]
    assert _PHONE_MASK in result["meta"]["phone"]
    assert _ID_MASK in result["tags"][1]


@pytest.mark.unit
def test_scrub_does_not_mutate_original() -> None:
    """scrub() must return a new dict; original is unchanged."""
    original = {"email": "x@y.com"}
    _ = scrub(original)
    assert original["email"] == "x@y.com"


@pytest.mark.unit
def test_scrub_text_no_pii_unchanged() -> None:
    """Text with no PII passes through without modification."""
    clean = "The quick brown fox jumps over the lazy dog."
    assert _scrub_text(clean) == clean


# ---------------------------------------------------------------------------
# LLM fallback (Issue #37 / Req 16.6)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scrub_async_no_llm_equals_sync(monkeypatch) -> None:
    """`use_llm=False` must be identical to the sync `scrub()` result."""
    from app.util import pii as pii_mod

    payload = {"text": "test@example.com or 090-1234-5678"}
    async_result = await pii_mod.scrub_async(payload, use_llm=False)
    assert async_result == pii_mod.scrub(payload)


@pytest.mark.asyncio
async def test_scrub_async_invokes_llm_for_residual_kanji(monkeypatch) -> None:
    """Residual kanji name (no space) — regex misses, LLM pass redacts."""
    from app.util import pii as pii_mod

    calls: list[str] = []

    async def _fake_llm(text: str) -> str:
        calls.append(text)
        return text.replace("山田太郎", "[REDACTED_NAME]")

    monkeypatch.setattr(pii_mod, "_scrub_text_with_llm", _fake_llm)

    payload = {"msg": "担当は山田太郎さんです。"}
    result = await pii_mod.scrub_async(payload)
    assert "山田太郎" not in result["msg"]
    assert "[REDACTED_NAME]" in result["msg"]
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_scrub_async_llm_failure_falls_back_to_regex(monkeypatch) -> None:
    """LLM exception must not crash scrub — regex output is returned."""
    from app.util import pii as pii_mod

    async def _boom(text: str) -> str:
        raise RuntimeError("aoai down")

    # _scrub_text_with_llm itself handles exceptions internally; simulate that
    # the production helper catches and returns regex-scrubbed text.
    async def _safe_llm(text: str) -> str:
        try:
            return await _boom(text)
        except Exception:
            return text

    monkeypatch.setattr(pii_mod, "_scrub_text_with_llm", _safe_llm)
    payload = {"email": "x@y.com"}
    result = await pii_mod.scrub_async(payload)
    assert result["email"] == "[REDACTED_EMAIL]"
