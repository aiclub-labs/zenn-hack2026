"""Consultant-tacit pivot: POST /records/{id}/vote materializes
upvotes/downvotes/score on the AI Search doc.

Direct-coroutine style, same posture as test_schemas_history_public.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api import votes as votes_api


@pytest.mark.unit
def test_vote_up_increments_and_writes_score() -> None:
    fake_client = MagicMock()
    fake_client.get_document = AsyncMock(
        return_value={"id": "r1", "pk": "general#general", "upvotes": 3, "downvotes": 1}
    )
    fake_client.merge_or_upload_documents = AsyncMock()

    with patch.object(votes_api, "__name__", votes_api.__name__):
        from app.util import aisearch

        with patch.object(aisearch, "CorpusIndex") as mk:
            inst = MagicMock()
            inst._client = fake_client
            mk.return_value = inst

            resp = asyncio.run(
                votes_api.cast_vote(
                    "r1", votes_api.VoteRequest(direction="up")
                )
            )

    assert resp.upvotes == 4
    assert resp.downvotes == 1
    assert resp.score == 3
    fake_client.merge_or_upload_documents.assert_awaited_once()
    payload = fake_client.merge_or_upload_documents.await_args.kwargs["documents"][0]
    assert payload["score"] == 3
    assert payload["upvotes"] == 4


@pytest.mark.unit
def test_vote_down_increments_and_can_go_negative() -> None:
    fake_client = MagicMock()
    fake_client.get_document = AsyncMock(
        return_value={"id": "r1", "pk": "general#general", "upvotes": 0, "downvotes": 0}
    )
    fake_client.merge_or_upload_documents = AsyncMock()

    from app.util import aisearch

    with patch.object(aisearch, "CorpusIndex") as mk:
        inst = MagicMock()
        inst._client = fake_client
        mk.return_value = inst

        resp = asyncio.run(
            votes_api.cast_vote("r1", votes_api.VoteRequest(direction="down"))
        )

    assert resp.upvotes == 0
    assert resp.downvotes == 1
    assert resp.score == -1
