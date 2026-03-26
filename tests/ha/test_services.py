"""High-value runtime tests for the Teltonika RMS Home Assistant services."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.teltonika_rms import DOMAIN, SERVICE_GET_DEVICE_HISTORY
from custom_components.teltonika_rms.__init__ import (
    _build_history_handler,
)  # Import the handler directly
from custom_components.teltonika_rms.coordinator import CoordinatorBundle

pytestmark = pytest.mark.ha


@pytest.mark.asyncio
async def test_get_device_history_service_calls_api_and_fires_event(
    hass: HomeAssistant,
    mock_rms_api_client: AsyncMock,
    mock_coordinator_bundle: CoordinatorBundle,
) -> None:
    """Test that the get_device_history service calls the API and fires an event."""
    mock_rms_api_client.async_get_device_history.return_value = [
        {"timestamp": "2026-01-01T00:00:00Z", "value": 10}
    ]

    mock_config_entry = AsyncMock()
    mock_config_entry.domain = DOMAIN
    mock_config_entry.runtime_data = AsyncMock(bundle=mock_coordinator_bundle)
    hass.config_entries._entries = [mock_config_entry]

    events = []
    await hass.bus.async_listen_once(f"{DOMAIN}_device_history", lambda e: events.append(e))

    # Directly call the service handler with mocked call data
    handler = _build_history_handler(hass)
    await handler(
        AsyncMock(
            data={
                "device_id": "test-device-id",
                "from_time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
                "to_time": datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat(),
                "interval": "1h",
                "config_id": 123,
            }
        )
    )

    mock_rms_api_client.async_get_device_history.assert_awaited_once_with(
        device_id="test-device-id",
        from_time=datetime.fromisoformat(
            datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
        ).replace(tzinfo=UTC),
        to_time=datetime.fromisoformat(
            datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat()
        ).replace(tzinfo=UTC),
        interval="1h",
        config_id=123,
        keys=None,
    )

    assert len(events) == 1
    event_data = events[0].data
    assert event_data["device_id"] == "test-device-id"
    assert event_data["config_id"] == 123
    assert event_data["data"] == [{"timestamp": "2026-01-01T00:00:00Z", "value": 10}]


@pytest.mark.asyncio
async def test_get_device_history_service_handles_keys_param(
    hass: HomeAssistant,
    mock_rms_api_client: AsyncMock,
    mock_coordinator_bundle: CoordinatorBundle,
) -> None:
    """Test that the get_device_history service correctly passes keys to the API."""
    mock_rms_api_client.async_get_device_history.return_value = [
        {"timestamp": "2026-01-01T00:00:00Z", "temp": 25}
    ]

    mock_config_entry = AsyncMock()
    mock_config_entry.domain = DOMAIN
    mock_config_entry.runtime_data = AsyncMock(bundle=mock_coordinator_bundle)
    hass.config_entries._entries = [mock_config_entry]

    events = []
    await hass.bus.async_listen_once(f"{DOMAIN}_device_history", lambda e: events.append(e))

    handler = _build_history_handler(hass)
    await handler(
        AsyncMock(
            data={
                "device_id": "test-device-id-2",
                "from_time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
                "to_time": datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat(),
                "interval": "1h",
                "keys": "temperature,humidity",
            }
        )
    )

    mock_rms_api_client.async_get_device_history.assert_awaited_once_with(
        device_id="test-device-id-2",
        from_time=datetime.fromisoformat(
            datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
        ).replace(tzinfo=UTC),
        to_time=datetime.fromisoformat(
            datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat()
        ).replace(tzinfo=UTC),
        interval="1h",
        config_id=None,
        keys=["temperature", "humidity"],
    )
    assert len(events) == 1


@pytest.mark.asyncio
async def test_get_device_history_service_fires_error_event_on_api_failure(
    hass: HomeAssistant,
    mock_rms_api_client: AsyncMock,
    mock_coordinator_bundle: CoordinatorBundle,
) -> None:
    """Test that the get_device_history service fires an error event on API failure."""
    mock_rms_api_client.async_get_device_history.side_effect = Exception("API down")

    mock_config_entry = AsyncMock()
    mock_config_entry.domain = DOMAIN
    mock_config_entry.runtime_data = AsyncMock(bundle=mock_coordinator_bundle)
    hass.config_entries._entries = [mock_config_entry]

    error_events = []
    await hass.bus.async_listen_once(
        f"{DOMAIN}_device_history_error", lambda e: error_events.append(e)
    )

    handler = _build_history_handler(hass)
    await handler(
        AsyncMock(
            data={
                "device_id": "test-device-id-error",
                "from_time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
                "to_time": datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat(),
                "interval": "1h",
                "keys": "temp",
            }
        )
    )

    assert len(error_events) == 1
    assert error_events[0].data["device_id"] == "test-device-id-error"
    assert "API down" in error_events[0].data["error"]


@pytest.mark.asyncio
async def test_get_device_history_service_invalid_input_no_api_call(
    hass: HomeAssistant,
    mock_rms_api_client: AsyncMock,
    mock_coordinator_bundle: CoordinatorBundle,
) -> None:
    """Test that the service does not call the API with invalid input."""
    mock_config_entry = AsyncMock()
    mock_config_entry.domain = DOMAIN
    mock_config_entry.runtime_data = AsyncMock(bundle=mock_coordinator_bundle)
    hass.config_entries._entries = [mock_config_entry]

    # Missing device_id
    with patch("custom_components.teltonika_rms.__init__.LOGGER.error") as mock_logger_error:
        handler = _build_history_handler(hass)
        await handler(
            AsyncMock(
                data={
                    "from_time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
                    "to_time": datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat(),
                    "interval": "1h",
                    "keys": "temp",
                }
            )
        )
        mock_logger_error.assert_called_once()

    mock_rms_api_client.async_get_device_history.assert_not_awaited()

    # Missing config_id and keys
    mock_rms_api_client.async_get_device_history.reset_mock()
    with patch("custom_components.teltonika_rms.__init__.LOGGER.error") as mock_logger_error:
        handler = _build_history_handler(hass)
        await handler(
            AsyncMock(
                data={
                    "device_id": "test-device-id-no-params",
                    "from_time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
                    "to_time": datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC).isoformat(),
                    "interval": "1h",
                }
            )
        )
        mock_logger_error.assert_called_once()
    mock_rms_api_client.async_get_device_history.assert_not_awaited()


@pytest.mark.asyncio
async def test_unload_removes_history_service(hass: HomeAssistant) -> None:
    """Test that the get_device_history service is removed on unload."""
    # Assume service is registered
    await hass.services.async_register(DOMAIN, SERVICE_GET_DEVICE_HISTORY, AsyncMock())
    # Mock _merged_options to avoid dependency issues during unload test
    with patch("custom_components.teltonika_rms.__init__._merged_options", return_value={}):
        hass.config_entries.async_unload_platforms.return_value = True
        result = await hass.config_entries.async_unload_platforms(
            AsyncMock(), []
        )  # Pass an empty list for platforms if you don't care about them
        assert result is True

        # Verify service is removed if no other entries exist
        hass.config_entries._entries = []  # Simulate no other entries
        await hass.config_entries.async_unload_entry(
            AsyncMock(domain=DOMAIN, runtime_data=AsyncMock())
        )
        assert not await hass.services.has_service(DOMAIN, SERVICE_GET_DEVICE_HISTORY)
