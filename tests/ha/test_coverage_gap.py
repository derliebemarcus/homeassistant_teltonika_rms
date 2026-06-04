"""Tests to close coverage gaps in the Teltonika RMS integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.teltonika_rms.api import (
    PatRmsAuthClient,
    RmsApiClient,
)
from custom_components.teltonika_rms.endpoint_matrix import (
    EndpointMatrix,
    EndpointSpec,
)


@pytest.mark.asyncio
async def test_pat_auth_client_get_access_token() -> None:
    """Test async_get_access_token in PatRmsAuthClient."""
    session = MagicMock()
    client = PatRmsAuthClient(session, "test-token")
    token = await client.async_get_access_token()
    assert token == "test-token"


@pytest.mark.asyncio
async def test_api_client_get_device_history_time_range_tuple() -> None:
    """Test async_get_device_history with time_range as a tuple (backward compatibility)."""
    auth = MagicMock()
    mock_response = MagicMock(status=200)
    mock_response.json = AsyncMock(return_value={"success": True, "data": [], "meta": {}})
    auth.async_request = AsyncMock(return_value=mock_response)

    matrix = EndpointMatrix("test", {})
    matrix.endpoints["device_history"] = EndpointSpec("/devices/{id}/history", tuple(), "safe")

    client = RmsApiClient(auth, matrix)

    from_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    to_time = datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC)

    # This should trigger the 'if not from_time or not to_time' branch for time_range
    history = await client.async_get_device_history("test-id", time_range=(from_time, to_time))

    assert history == []
    # No from_time/to_time and no time_range
    history = await client.async_get_device_history("test-id")
    assert history == []


@pytest.mark.asyncio
async def test_config_flow_properties() -> None:
    """Test OAuth2FlowHandler properties for coverage."""
    from custom_components.teltonika_rms.config_flow import OAuth2FlowHandler

    handler = OAuth2FlowHandler()
    assert handler.logger is not None
    assert "scope" in handler.extra_authorize_data
    assert handler.is_matching({"some": "info"}) is False


@pytest.mark.asyncio
async def test_config_flow_reauth_failure() -> None:
    """Test reauth failure branches for coverage."""
    from custom_components.teltonika_rms.config_flow import OAuth2FlowHandler

    handler = OAuth2FlowHandler()
    handler.hass = MagicMock()
    handler.context = {"entry_id": "test-entry"}
    handler._reauth_entry = None

    # Coverage for line 101
    handler.hass.config_entries.async_get_entry.return_value = None
    with patch.object(handler, "async_abort") as mock_abort:
        await handler.async_step_reauth({})
        mock_abort.assert_called_with(reason="reauth_failed")

    # Coverage for line 117
    with patch.object(handler, "async_abort") as mock_abort:
        await handler.async_step_reauth_pat({"pat_token": "valid-format"})
        mock_abort.assert_called_with(reason="reauth_failed")


@pytest.mark.asyncio
async def test_config_flow_reauth_pat_empty() -> None:
    """Test reauth PAT with empty token for coverage."""
    from custom_components.teltonika_rms.config_flow import OAuth2FlowHandler

    handler = OAuth2FlowHandler()
    handler.hass = MagicMock()

    # Coverage for line 115
    with patch.object(handler, "async_show_form") as mock_show:
        await handler.async_step_reauth_pat({"pat_token": "  "})
        args, kwargs = mock_show.call_args
        assert kwargs["errors"]["base"] == "invalid_pat"


@pytest.mark.asyncio
async def test_models_has_location_none() -> None:
    """Test has_location_coordinates with None for coverage."""
    from custom_components.teltonika_rms.models import has_location_coordinates

    assert has_location_coordinates(None) is False


@pytest.mark.asyncio
async def test_button_press_error() -> None:
    """Test button.press raises NotImplementedError for coverage."""
    from custom_components.teltonika_rms.button import RmsRebootButton

    button = RmsRebootButton(MagicMock(), "test-id")
    with pytest.raises(NotImplementedError):
        button.press()


def test_models_parse_rms_timestamp_invalid() -> None:
    """Test parse_rms_timestamp with invalid data."""
    from custom_components.teltonika_rms.models import parse_rms_timestamp

    assert parse_rms_timestamp(None) is None
    assert parse_rms_timestamp("") is None
    assert parse_rms_timestamp("invalid") is None


def test_models_parse_online_varied() -> None:
    """Test parse_online with various inputs."""
    from custom_components.teltonika_rms.models import parse_online

    assert parse_online(None) is None
    assert parse_online(True) is True
    assert parse_online(1) is True
    assert parse_online("online") is True
    assert parse_online("up") is True
    assert parse_online("connected") is True
    assert parse_online("true") is True
    assert parse_online("1") is True
    assert parse_online("offline") is False
    assert parse_online("down") is False
    assert parse_online("disconnected") is False
    assert parse_online("false") is False
    assert parse_online("0") is False
    assert parse_online("unknown") is None


def test_models_parse_numeric_invalid() -> None:
    """Test numeric parsers with invalid data."""
    from custom_components.teltonika_rms.models import parse_float, parse_int

    assert parse_float(None) is None
    assert parse_float("abc") is None
    assert parse_int(None) is None
    assert parse_int("abc") is None


def test_models_parse_coordinate_pair() -> None:
    """Test _parse_coordinate_pair with various formats."""
    from custom_components.teltonika_rms.models import _parse_coordinate_pair

    assert _parse_coordinate_pair([12.3, 45.6]) == (45.6, 12.3)
    assert _parse_coordinate_pair("12.3, 45.6") == (45.6, 12.3)
    assert _parse_coordinate_pair("invalid") == (None, None)


def test_entity_is_poe_capable_none() -> None:
    """Test is_poe_capable_series with None."""
    from custom_components.teltonika_rms.entity import is_poe_capable_series

    assert is_poe_capable_series(None) is False
    assert is_poe_capable_series("") is False


def test_entity_port_entity_name_mismatch() -> None:
    """Test RmsPortEntity._port with name mismatch."""
    from custom_components.teltonika_rms.entity import RmsPortEntity

    bundle = MagicMock()
    bundle.port_scan.data = {"dev-1": [{"name": "Port1"}]}
    entity = RmsPortEntity(bundle, "dev-1", "Port2")
    assert entity._port is None


def test_device_tracker_none_device() -> None:
    """Test RmsDeviceTracker with missing normalized device."""
    from custom_components.teltonika_rms.device_tracker import RmsDeviceTracker

    bundle = MagicMock()
    bundle.merged_device.return_value = None
    tracker = RmsDeviceTracker(bundle, "dev-1")
    assert tracker.latitude is None
    assert tracker.longitude is None


@pytest.mark.asyncio
async def test_coordinator_enrich_location_disabled() -> None:
    """Test location enrichment is skipped when disabled."""
    from custom_components.teltonika_rms.coordinator import StateCoordinator

    api = MagicMock()
    api.async_get_states_for_devices = AsyncMock(return_value={})
    inventory = MagicMock()
    inventory.data = {}
    config = {"options": {"enable_location": False}}
    coord = StateCoordinator(MagicMock(), api, inventory, config)
    # This should cover the 'if not self._enable_location' branch implicitly or explicitly
    with patch.object(coord, "_async_enrich_locations") as mock_enrich:
        await coord._async_update_data()
        mock_enrich.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_enrich_location_real() -> None:
    """Test real location enrichment logic."""
    from custom_components.teltonika_rms.coordinator import StateCoordinator

    api = MagicMock()
    api.async_get_device_location = AsyncMock(return_value={"latitude": 1.0, "longitude": 2.0})
    inventory = MagicMock()
    inventory.data = {"dev-1": {}}
    config = {"options": {"enable_location": True}}
    coord = StateCoordinator(MagicMock(), api, inventory, config)
    results: dict[str, Any] = {"dev-1": {}}
    await coord._async_enrich_locations(results, ["dev-1"], max_per_cycle=10)
    assert results["dev-1"]["location"]["latitude"] == 1.0


def test_device_tracker_discovery() -> None:
    """Test device tracker entity discovery."""
    from custom_components.teltonika_rms.device_tracker import _discover_tracker_entities

    bundle = MagicMock()
    # Happy path
    bundle.inventory.data = {"dev-1": {}}
    bundle.merged_device.return_value = MagicMock(latitude=1.0, longitude=2.0)
    known: set[str] = set()
    entities = _discover_tracker_entities(bundle, known)
    assert len(entities) == 1
    assert "dev-1_location" in known

    # Edge case: No coordinates
    bundle.merged_device.return_value = MagicMock(latitude=None, longitude=None)
    known.clear()
    entities = _discover_tracker_entities(bundle, known)
    assert len(entities) == 0

    # Edge case: Already known
    bundle.merged_device.return_value = MagicMock(latitude=1.0, longitude=2.0)
    known = {"dev-1_location"}
    entities = _discover_tracker_entities(bundle, known)
    assert len(entities) == 0


def test_switch_and_update_fallbacks() -> None:
    """Test is_on fallbacks when data is missing for coverage."""
    from custom_components.teltonika_rms.switch import RmsPoeSwitch
    from custom_components.teltonika_rms.update import RmsFirmwareUpdateEntity

    bundle = MagicMock()
    bundle.port_scan.data = {}
    sw = RmsPoeSwitch(bundle, "dev-1", "Port1")
    assert sw.is_on is False

    bundle.merged_device.return_value = None
    upd = RmsFirmwareUpdateEntity(bundle, "dev-1")
    assert upd.in_progress is False


def test_status_channel_terminal_edge_cases() -> None:
    """Test terminal state detection edge cases for coverage."""
    from custom_components.teltonika_rms.status_channel import _is_device_grouped_terminal

    # Line 167: not is_device_map
    assert _is_device_grouped_terminal({"not_a_device_id": "not_a_list"}) is False
