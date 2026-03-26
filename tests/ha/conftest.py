"""Home Assistant specific pytest fixtures for Teltonika RMS tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from homeassistant.config_entries import ConfigEntriesFlowManager, ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.teltonika_rms.const import DOMAIN
from custom_components.teltonika_rms.coordinator import CoordinatorBundle

pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture(autouse=True)
def auto_enable_patching() -> str:
    """Set the default asyncio backend for pytest-asyncio."""
    # This is necessary to avoid issues with Home Assistant's event loop management
    return "asyncio"


@pytest.fixture
def hass(mock_coordinator_bundle: CoordinatorBundle) -> Generator[HomeAssistant]:
    """Mock HomeAssistant fixture."""
    _hass = AsyncMock(spec=HomeAssistant)
    mock_config_entry = AsyncMock(spec=ConfigEntry)
    mock_config_entry.domain = DOMAIN
    mock_config_entry.runtime_data = mock_coordinator_bundle

    _hass.config_entries = AsyncMock(spec=ConfigEntriesFlowManager)
    _hass.config_entries.async_entries = AsyncMock(return_value=[mock_config_entry])
    _hass.bus = AsyncMock()
    _hass.bus.async_listen_once = AsyncMock()
    _hass.services = AsyncMock()
    _hass.services.has_service.return_value = False
    _hass.services.async_register = AsyncMock()
    _hass.services.async_remove = AsyncMock()
    with patch(
        "custom_components.teltonika_rms.PLATFORMS",
        ["binary_sensor", "sensor", "device_tracker"],
    ):
        yield _hass


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
