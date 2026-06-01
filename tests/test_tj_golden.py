"""Truth Judgment golden set evaluation (T1 of framework-review.md §7.1).

Loads 10 hand-curated cases from `tests/fixtures/tj_golden.json` and runs
each through `TruthJudgmentModule.judge` with scripted LLM + corpus stubs.
Asserts that aggregate verdict matches the expected label on ≥ 80% of cases.

Scope:
- Tests the deterministic aggregation pipeline (`_aggregate`, ensemble vote
  counting, cold-start fallback path) on scripted LLM responses.
- Does NOT exercise real AOAI / AI Search quality. Real-LLM evaluation
  requires a deployed inference endpoint + a seeded corpus and is tracked
  in `framework-review.md §9` as post-hack TODO.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agents.truth_judgment.module import TruthJudgmentModule
from app.contracts.cosmos import HearoutRecord

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tj_golden.json"
PASS_THRESHOLD = 0.80


@pytest.fixture
def golden_cases() -> list[dict[str, Any]]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == 10, f"expected 10 golden cases, got {len(cases)}"
    return cases


def _record_from_case(case: dict[str, Any]) -> HearoutRecord:
    r = case["record"]
    return HearoutRecord(
        id=f"hr_{case['case_id']}",
        pk="manufacturing-s8b#line-A",
        gap_event_id=f"ge_{case['case_id']}",
        session_id=f"sess_{case['case_id']}",
        transcript=[{"role": "user", "content": r.get("what", "")}],
        who=r.get("who"),
        what=r.get("what"),
        when=r.get("when"),
        where=r.get("where"),
        why=r.get("why"),
        how=r.get("how"),
        outcome="completed",
        turn_count=3,
    )


def _build_llm_stub(case: dict[str, Any]) -> AsyncMock:
    """Stub AsyncAzureOpenAI: graphcheck returns scripted claims; each
    subsequent factcheck call returns the next per-claim verdict.
    Cold-start path = each claim triggers 3 ensemble votes (all same verdict)."""
    claims = case["scripted_claims"]
    per_claim_verdicts = case["scripted_per_claim_verdicts"]
    assert len(claims) == len(per_claim_verdicts), case["case_id"]

    # Call sequence:
    #   1 graphcheck call (returns atomic_claims JSON)
    #   then for each claim: 3 factcheck calls (ensemble) — all same verdict
    responses: list[str] = [json.dumps({"atomic_claims": claims})]
    for v in per_claim_verdicts:
        for _ in range(3):  # 3-LLM ensemble
            responses.append(
                json.dumps({"verdict": v, "confidence": 0.9, "reason": f"scripted-{v}"})
            )

    call_iter = iter(responses)

    def _make_resp(content: str) -> Any:
        msg = type("M", (), {"content": content})
        choice = type("C", (), {"message": msg})
        return type("R", (), {"choices": [choice]})

    async def _create(**kwargs: Any) -> Any:
        return _make_resp(next(call_iter))

    client = AsyncMock()
    client.chat.completions.create = _create  # type: ignore[assignment]
    return client


def _build_corpus_stub() -> AsyncMock:
    """Corpus always returns 0 hits → forces cold-start FactCheck ensemble
    path, which is the deterministically testable branch. Hot-path (≥3 hits
    with superseded_by heuristic) is exercised separately in
    test_tj_hot_path_diverging."""
    corpus = AsyncMock()
    corpus.query = AsyncMock(return_value=[])
    return corpus


def _build_logs_stub() -> AsyncMock:
    repo = AsyncMock()
    repo.append = AsyncMock()
    return repo


def _build_embed_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_embed(text: str) -> list[float]:
        return [0.0] * 8

    monkeypatch.setattr("app.agents.truth_judgment.module.embed", _fake_embed)


@pytest.mark.asyncio
async def test_tj_golden_set_meets_threshold(
    golden_cases: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    _build_embed_stub(monkeypatch)
    results: list[tuple[str, str, str, bool]] = []  # (case_id, expected, actual, match)

    for case in golden_cases:
        module = TruthJudgmentModule(
            tj_log_repo=_build_logs_stub(),
            corpus=_build_corpus_stub(),
            llm_client=_build_llm_stub(case),
        )
        record = _record_from_case(case)
        log = await module.judge(record)
        expected = case["expected_verdict"]
        actual = log.verdict
        results.append((case["case_id"], expected, actual, expected == actual))

    match_count = sum(1 for *_, ok in results if ok)
    pass_rate = match_count / len(results)

    report_lines = [
        f"\nTJ golden-set evaluation: {match_count}/{len(results)} match "
        f"(threshold >= {PASS_THRESHOLD:.0%})"
    ]
    for case_id, expected, actual, ok in results:
        mark = "OK" if ok else "FAIL"
        report_lines.append(f"  [{mark}] {case_id}: expected={expected}, got={actual}")
    report = "\n".join(report_lines)
    print(report)

    assert pass_rate >= PASS_THRESHOLD, report


@pytest.mark.asyncio
async def test_tj_hot_path_diverging_yields_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When corpus returns ≥3 hits and ≥2 carry superseded_by/coexisting_views,
    the retrieval heuristic must yield 'conflict' without invoking ensemble."""
    _build_embed_stub(monkeypatch)
    diverging_hits = [
        {"id": "r1", "content": "x", "superseded_by": "r99"},
        {"id": "r2", "content": "y", "coexisting_views": ["r3"]},
        {"id": "r3", "content": "z"},
    ]

    corpus = AsyncMock()
    corpus.query = AsyncMock(return_value=diverging_hits)

    llm = AsyncMock()

    async def _create(**kwargs: Any) -> Any:
        # Only graphcheck should be called; ensemble path must NOT trigger
        # because retrieval path handles ≥ COLD_START_THRESHOLD hits.
        msg = type("M", (), {"content": json.dumps({"atomic_claims": ["c1"]})})
        choice = type("C", (), {"message": msg})
        return type("R", (), {"choices": [choice]})

    llm.chat.completions.create = _create  # type: ignore[assignment]

    module = TruthJudgmentModule(
        tj_log_repo=_build_logs_stub(),
        corpus=corpus,
        llm_client=llm,
    )
    record = HearoutRecord(
        id="hr_hot",
        pk="manufacturing-s8b#line-A",
        gap_event_id="ge_hot",
        session_id="sess_hot",
        transcript=[{"role": "user", "content": "x"}],
        what="x",
        outcome="completed",
        turn_count=1,
    )
    log = await module.judge(record)
    assert log.verdict == "conflict", log
    assert any(v.get("source") == "retrieval" for v in log.ensemble_votes)
