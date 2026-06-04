from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import ImplementationUnavailableError

from custom_components.teltonika_rms import async_setup_entry, async_unload_entry
from custom_components.teltonika_rms.const import (
    AUTH_MODE_PAT,
    CONF_AUTH_MODE,
    CONF_PAT_TOKEN,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_async_setup_entry_pat_missing_token(hass: HomeAssistant) -> None:
    """Test setup failure when PAT token is missing."""
    mock_entry = MagicMock()
    mock_entry.data = {CONF_AUTH_MODE: AUTH_MODE_PAT, CONF_PAT_TOKEN: ""}
    mock_entry.options = {}

    with pytest.raises(ConfigEntryNotReady, match="PAT token missing"):
        await async_setup_entry(hass, mock_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_oauth_failure(hass: HomeAssistant) -> None:
    """Test setup failure when OAuth implementation is unavailable."""
    mock_entry = MagicMock()
    mock_entry.data = {CONF_AUTH_MODE: "oauth2"}
    mock_entry.options = {}

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError("OAuth fail"),
    ):
        with pytest.raises(ConfigEntryNotReady, match="OAuth implementation unavailable"):
            await async_setup_entry(hass, mock_entry)


@pytest.mark.asyncio
async def test_async_setup_entry_api_failure(hass: HomeAssistant) -> None:
    """Test setup failure when API connection validation fails."""
    mock_entry = MagicMock()
    mock_entry.data = {CONF_AUTH_MODE: AUTH_MODE_PAT, CONF_PAT_TOKEN: "token"}
    mock_entry.options = {}

    # Patch the RmsApiClient class itself to control its instance methods
    with (
        patch("custom_components.teltonika_rms.api.PatRmsAuthClient"),
        patch("custom_components.teltonika_rms.api.RmsApiClient") as mock_api_class,
        patch("custom_components.teltonika_rms.endpoint_matrix.load_endpoint_matrix"),
        patch("homeassistant.helpers.aiohttp_client.async_get_clientsession"),
    ):
        mock_api = mock_api_class.return_value
        mock_api.async_validate_connection = AsyncMock(side_effect=Exception("API failure"))

        with pytest.raises(ConfigEntryNotReady, match="Unexpected error during initialization"):
            await async_setup_entry(hass, mock_entry)


@pytest.mark.asyncio
async def test_async_unload_entry_multiple_entries(hass: HomeAssistant) -> None:
    """Test unloading when multiple entries exist (services should not be removed)."""
    mock_entry = MagicMock()
    mock_entry.domain = DOMAIN

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[mock_entry, MagicMock()]),
        patch.object(hass.config_entries, "async_unload_platforms", return_value=True),
        patch.object(hass.services, "async_remove") as mock_remove,
    ):
        result = await async_unload_entry(hass, mock_entry)
        assert result is True
        mock_remove.assert_not_called()
