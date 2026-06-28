"""Tests for current RMS device-list schema and pagination behavior."""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.teltonika_rms.api import RmsApiClient, RmsAuthClient
from custom_components.teltonika_rms.api_devices import (
    SpecCompatibleRmsApiClient,
    _has_next_offset_page,
    _normalize_device_record,
)
from custom_components.teltonika_rms.endpoint_matrix import EndpointMatrix, EndpointSpec


def _client() -> SpecCompatibleRmsApiClient:
    matrix = EndpointMatrix(
        source="test",
        endpoints={"devices_list": EndpointSpec("/devices", tuple(), "safe")},
    )
    return SpecCompatibleRmsApiClient(
        cast(RmsAuthClient, MagicMock()),
        matrix,
    )


@pytest.mark.asyncio
async def test_device_list_uses_limit_offset_and_meta_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The current RMS specification uses offset pagination and meta.total."""
    client = _client()
    request = AsyncMock(
        side_effect=[
            ([{"id": 1, "status": 1}, {"id": 2, "status": 2}], {"total": 3}),
            ([{"id": 3, "status": 0}], {"total": 3}),
        ]
    )
    monkeypatch.setattr(client, "async_request", request)

    devices = await client.async_list_devices(page_size=2)

    assert devices == [
        {"id": 1, "status": "online"},
        {"id": 2, "status": "pending"},
        {"id": 3, "status": "offline"},
    ]
    assert request.await_count == 2
    assert request.await_args_list[0].kwargs["params"] == {"limit": 2, "offset": 0}
    assert request.await_args_list[1].kwargs["params"] == {"limit": 2, "offset": 2}


@pytest.mark.asyncio
async def test_device_list_is_not_truncated_after_twenty_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default path follows meta.total instead of imposing the old 20-page cap."""
    client = _client()
    total = 21
    request = AsyncMock(
        side_effect=[([{"id": index, "status": 1}], {"total": total}) for index in range(total)]
    )
    monkeypatch.setattr(client, "async_request", request)

    devices = await client.async_list_devices(page_size=1)

    assert len(devices) == total
    assert request.await_count == total
    assert request.await_args_list[-1].kwargs["params"] == {"limit": 1, "offset": 20}


@pytest.mark.asyncio
async def test_device_list_stops_when_server_repeats_a_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A server ignoring offset cannot cause duplicate pages or an endless loop."""
    client = _client()
    repeated_page = [{"id": 1, "status": 1}]
    request = AsyncMock(side_effect=[(repeated_page, {}), (repeated_page, {})])
    monkeypatch.setattr(client, "async_request", request)

    devices = await client.async_list_devices(page_size=1)

    assert devices == [{"id": 1, "status": "online"}]
    assert request.await_count == 2


@pytest.mark.asyncio
async def test_device_list_respects_explicit_page_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connection validation can still request only one page explicitly."""
    client = _client()
    request = AsyncMock(return_value=([{"id": 1, "status": 1}], {"total": 10}))
    monkeypatch.setattr(client, "async_request", request)

    devices = await client.async_list_devices(page_size=1, max_pages=1)

    assert devices == [{"id": 1, "status": "online"}]
    assert request.await_count == 1


@pytest.mark.asyncio
async def test_device_detail_status_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Detail fallback cannot interpret pending status code 2 as online."""
    client = _client()
    parent_call = AsyncMock(return_value={"id": 1, "status": 2})
    monkeypatch.setattr(RmsApiClient, "async_get_device_state", parent_call)

    result = await client.async_get_device_state("1")

    assert result == {"id": 1, "status": "pending"}


@pytest.mark.asyncio
async def test_device_list_preserves_existing_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing status and tag options remain attached to the corrected request."""
    client = _client()
    request = AsyncMock(return_value=([{"id": 1, "status": 1}], {"total": 1}))
    monkeypatch.setattr(client, "async_request", request)

    await client.async_list_devices(tags=["ber", "zrh"], device_status="online")

    awaited_call = request.await_args
    assert awaited_call is not None
    assert awaited_call.kwargs["params"] == {
        "limit": 50,
        "offset": 0,
        "tags": "ber,zrh",
        "status": "online",
    }


def test_status_normalization_matches_openapi_semantics() -> None:
    """Normalize documented numeric/null values and retain unknown future codes."""
    assert _normalize_device_record({"status": None})["status"] == "offline"
    assert _normalize_device_record({"status": 0})["status"] == "offline"
    assert _normalize_device_record({"status": 1})["status"] == "online"
    assert _normalize_device_record({"status": 2})["status"] == "pending"
    assert _normalize_device_record({"status": 7})["status"] == 7
    assert _normalize_device_record({"id": 1}) == {"id": 1}


def test_offset_page_fallback_uses_short_page_detection() -> None:
    """Without meta.total, a short page terminates pagination safely."""
    assert _has_next_offset_page(2, {}, 0, 2) is True
    assert _has_next_offset_page(1, {}, 0, 2) is False
    assert _has_next_offset_page(0, {"total": 10}, 0, 2) is False
    assert _has_next_offset_page(2, {"total": 3}, 0, 2) is True
    assert _has_next_offset_page(1, {"total": 3}, 2, 2) is False
