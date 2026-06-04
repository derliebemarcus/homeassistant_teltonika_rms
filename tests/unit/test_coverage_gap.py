from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.teltonika_rms.api import (
    _coerce_list,
    _coerce_state_map,
    _validate_contract_payload,
)
from custom_components.teltonika_rms.exceptions import RmsApiError
from custom_components.teltonika_rms.models_api import DeviceDetailResponse
from custom_components.teltonika_rms.status_channel import _is_device_grouped_terminal


def test_validate_contract_payload_error() -> None:
    """Test that ValidationError raises RmsApiError."""
    # Missing required 'data' or malformed
    invalid_payload = {"something": "else"}
    with pytest.raises(RmsApiError, match="RMS schema changed"):
        _validate_contract_payload(invalid_payload, "test_endpoint", DeviceDetailResponse)


def test_coerce_list_edge_cases() -> None:
    """Test _coerce_list with non-standard inputs."""
    assert _coerce_list(None) == []
    assert _coerce_list("not a list") == []

    # Dict with no matching keys
    assert _coerce_list({"unknown": [1, 2]}) == []

    # Dict with matching key but not a list
    assert _coerce_list({"items": "not a list"}) == []


def test_coerce_state_map_nested_devices() -> None:
    """Test _coerce_state_map with nested devices key."""
    data = {"devices": [{"id": "dev1", "status": "online"}, {"id": "dev2", "status": "offline"}]}
    result = _coerce_state_map(data)
    assert "dev1" in result
    assert "dev2" in result
    assert result["dev1"]["status"] == "online"


def test_coerce_state_map_missing_id() -> None:
    """Test _coerce_state_map skips items without ID."""
    data = [{"id": "dev1"}, {"no_id": "here"}, {"device_id": "dev2"}]
    result = _coerce_state_map(data)
    assert "dev1" in result
    assert "dev2" in result
    assert len(result) == 2


def test_is_device_grouped_terminal_non_list_value() -> None:
    """Test that _is_device_grouped_terminal returns False if a value is not a list."""
    # A payload that looks like a device map but contains a non-list value for a numeric key
    payload = {"123": "not a list"}
    assert _is_device_grouped_terminal(payload) is False


@pytest.mark.asyncio
async def test_coordinator_wireless_error_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test coordinator wireless enrichment error handlers."""
    from homeassistant.exceptions import ConfigEntryAuthFailed

    from custom_components.teltonika_rms.coordinator import StateCoordinator
    from custom_components.teltonika_rms.exceptions import RmsApiError

    api = MagicMock()
    # StateCoordinator(hass, api, inventory, options, entry)
    coordinator = StateCoordinator(MagicMock(), api, MagicMock(), {})

    # 1. Test ConfigEntryAuthFailed
    api.async_get_device_wireless = AsyncMock(side_effect=ConfigEntryAuthFailed)
    results: dict[str, dict[str, Any]] = {"dev1": {}}
    await coordinator._async_enrich_wireless(results, ["dev1"], max_per_cycle=1)
    assert "clients_count" not in results["dev1"].get("state", {})

    # 2. Test RmsApiError
    api.async_get_device_wireless = AsyncMock(side_effect=RmsApiError)
    await coordinator._async_enrich_wireless(results, ["dev1"], max_per_cycle=1)
    assert "clients_count" not in results["dev1"].get("state", {})
