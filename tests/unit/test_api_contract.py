"""Contract tests for Teltonika RMS API models."""

from __future__ import annotations

from typing import cast

import pytest
from pydantic import ValidationError

from custom_components.teltonika_rms.models_api import (
    DeviceDetailResponse,
    DeviceListResponse,
    DeviceState,
    DeviceStateResponse,
)


def test_device_list_response_valid() -> None:
    """Test parsing a device-list response matching the current RMS OpenAPI schema."""
    data = [
        {
            "id": 1,
            "name": "Router 1",
            "serial": "123456",
            "mac": "00:11:22:33:44:55",
            "model": "RUT955",
            "status": 1,
            "extra_field": "ignore me",
        }
    ]
    response = DeviceListResponse.model_validate({"data": data})
    assert len(response.data) == 1
    assert response.data[0].id == 1
    assert response.data[0].model_name == "RUT955"
    assert response.data[0].status == 1


def test_device_list_response_accepts_optional_id_and_nullable_status() -> None:
    """Accept an ID-less RMS record when another stable identifier is present."""
    response = DeviceListResponse.model_validate(
        {
            "data": [
                {
                    "name": "Pending inventory record",
                    "serial": "SER-1",
                    "status": None,
                }
            ]
        }
    )
    assert response.data[0].id is None
    assert response.data[0].serial == "SER-1"
    assert response.data[0].status is None


def test_device_list_response_accepts_legacy_string_status() -> None:
    """Keep compatibility with older RMS responses using textual statuses."""
    response = DeviceListResponse.model_validate({"data": [{"id": "1", "status": "online"}]})
    assert response.data[0].status == "online"


def test_device_list_response_rejects_unidentified_record() -> None:
    """Reject rows that cannot produce a persistent Home Assistant device ID."""
    with pytest.raises(ValidationError, match="stable identifier"):
        DeviceListResponse.model_validate({"data": [{"name": "Missing identifier"}]})


def test_device_detail_response_valid() -> None:
    """Test parsing a valid device detail response."""
    data = {
        "id": 1,
        "serial": "123456",
        "mac": "AA:BB:CC:DD:EE:FF",
        "model": "RUT240",
        "status": 0,
    }
    response = DeviceDetailResponse.model_validate({"data": data})
    assert response.data.id == 1
    assert response.data.serial == "123456"
    assert response.data.status == 0


def test_device_state_response_valid() -> None:
    """Test parsing a valid device state response."""
    data = {
        "id": "1",
        "online": True,
        "wan_ip": "1.2.3.4",
    }
    response = DeviceStateResponse.model_validate({"data": data})
    state = cast(DeviceState, response.data)
    assert state.id == "1"
