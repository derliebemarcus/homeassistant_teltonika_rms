"""Home Assistant specific pytest fixtures for Teltonika RMS tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.teltonika_rms import TeltonikaRmsRuntime
from custom_components.teltonika_rms.const import DOMAIN
from custom_components.teltonika_rms.coordinator import CoordinatorBundle


@pytest.fixture
def hass(mock_coordinator_bundle: CoordinatorBundle) -> Generator[HomeAssistant]:
    """Mock HomeAssistant fixture."""
    _hass = AsyncMock(spec=HomeAssistant)
    _hass.data = {}
    _hass.async_add_executor_job = AsyncMock()

    # Track listeners for events
    _listeners: dict[str, Any] = {}

    def async_listen_once(event_type: str, listener: Any) -> Any:
        _listeners[event_type] = listener
        return lambda: _listeners.pop(event_type, None)

    def async_fire(event_type: str, event_data: Any) -> None:
        if event_type in _listeners:
            listener = _listeners.pop(event_type)
            listener(MagicMock(data=event_data))

    mock_config_entry = AsyncMock(spec=ConfigEntry)
    mock_config_entry.domain = DOMAIN
    mock_config_entry.runtime_data = TeltonikaRmsRuntime(bundle=mock_coordinator_bundle)

    _hass.config_entries = MagicMock()
    _hass.config_entries._entries = [mock_config_entry]
    _hass.config_entries.async_forward_entry_setups = AsyncMock()
    _hass.config_entries.async_unload_platforms = AsyncMock()
    _hass.config_entries.async_entries = MagicMock(
        side_effect=lambda domain=None: [
            e
            for e in _hass.config_entries._entries
            if domain is None or getattr(e, "domain", None) == domain
        ]
    )
    _hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    _hass.config_entries.async_unload_entry = AsyncMock(return_value=True)
    _hass.config_entries.flow = MagicMock()
    _hass.config_entries.flow.async_progress_by_handler = MagicMock(return_value=[])
    _hass.bus = MagicMock()
    _hass.bus.async_fire = MagicMock(side_effect=async_fire)
    _hass.bus.async_listen_once = MagicMock(side_effect=async_listen_once)
    _hass.async_create_task = MagicMock()
    _hass.services = MagicMock()
    _hass.services.has_service.return_value = False
    _hass.services.async_register = MagicMock()
    _hass.services.async_remove = MagicMock()
    with patch(
        "custom_components.teltonika_rms.PLATFORMS",
        ["binary_sensor", "sensor", "device_tracker"],
    ):
        yield cast(HomeAssistant, _hass)


@pytest.fixture
def mock_rms_api_client() -> Generator[AsyncMock]:
    """Mock RmsApiClient fixture."""
    with patch(
        "custom_components.teltonika_rms.api.RmsApiClient", autospec=True
    ) as mock_api_client:
        yield mock_api_client.return_value


@pytest.fixture
def mock_coordinator_bundle(
    mock_rms_api_client: AsyncMock,
) -> Generator[CoordinatorBundle]:
    """Mock CoordinatorBundle fixture."""
    with (
        patch(
            "custom_components.teltonika_rms.coordinator.InventoryCoordinator", autospec=True
        ) as mock_inventory_coordinator,
        patch(
            "custom_components.teltonika_rms.coordinator.StateCoordinator", autospec=True
        ) as mock_state_coordinator,
        patch(
            "custom_components.teltonika_rms.coordinator.PortScanCoordinator", autospec=True
        ) as mock_port_scan_coordinator,
        patch(
            "custom_components.teltonika_rms.coordinator.PortConfigCoordinator", autospec=True
        ) as mock_port_config_coordinator,
        patch(
            "custom_components.teltonika_rms.status_channel.RmsStatusChannelManager", autospec=True
        ) as mock_status_channel_manager,
    ):
        bundle = CoordinatorBundle(
            inventory=mock_inventory_coordinator.return_value,
            state=mock_state_coordinator.return_value,
            port_scan=mock_port_scan_coordinator.return_value,
            port_config=mock_port_config_coordinator.return_value,
            status_channels=mock_status_channel_manager.return_value,
            api=mock_rms_api_client,
        )
        yield bundle
