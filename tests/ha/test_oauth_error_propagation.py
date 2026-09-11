"""Regression contract for Home Assistant OAuth2 setup error propagation."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from homeassistant.helpers import config_entry_oauth2_flow

import custom_components.teltonika_rms as integration
from custom_components.teltonika_rms.const import AUTH_MODE_OAUTH2, CONF_AUTH_MODE, DOMAIN

pytestmark = pytest.mark.ha


def _entry() -> Any:
    return SimpleNamespace(
        data={
            CONF_AUTH_MODE: AUTH_MODE_OAUTH2,
            "auth_implementation": "test",
            "token": {
                "access_token": "test-token",
                "refresh_token": "test-refresh",
                "expires_at": 0,
            },
        },
        options={},
        runtime_data=None,
        entry_id="entry-149",
        add_update_listener=MagicMock(),
        async_on_unload=MagicMock(),
    )


def _hass() -> Any:
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(return_value=MagicMock())
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock()
    hass.services = MagicMock()
    hass.services.has_service.return_value = False
    hass.async_create_task = MagicMock()
    return hass


def _token_error(error_type: type[Exception], status: int) -> Exception:
    request_info = MagicMock()
    request_info.real_url = "https://example.invalid/oauth/token"
    return error_type(
        request_info=request_info,
        history=(),
        status=status,
        message="oauth failure",
        headers=None,
        domain=DOMAIN,
    )


async def _setup_with_validation_error(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> tuple[Any, Any]:
    hass = _hass()
    entry = _entry()
    api = MagicMock()
    api.async_validate_connection = AsyncMock(side_effect=error)
    api.set_status_channel_manager = MagicMock()

    monkeypatch.setattr(
        integration.config_entry_oauth2_flow,
        "async_get_config_entry_implementation",
        AsyncMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        integration.config_entry_oauth2_flow,
        "OAuth2Session",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        integration,
        "SpecCompatibleRmsApiClient",
        MagicMock(return_value=api),
    )
    monkeypatch.setattr(
        integration.status_channel,
        "RmsStatusChannelManager",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(integration, "_initialize_bundle", MagicMock(return_value=MagicMock()))

    await integration.async_setup_entry(hass, entry)
    return hass, entry


@pytest.mark.asyncio
async def test_native_implementation_unavailable_is_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the HA 2026.10 not-ready exception and translated message intact."""

    class NativeImplementationUnavailable(
        config_entry_oauth2_flow.ImplementationUnavailableError,
        ConfigEntryNotReady,
    ):
        pass

    error = NativeImplementationUnavailable("implementation unavailable")
    hass = _hass()
    entry = _entry()
    monkeypatch.setattr(
        integration.config_entry_oauth2_flow,
        "async_get_config_entry_implementation",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(ConfigEntryNotReady) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value is error
    entry.add_update_listener.assert_not_called()
    hass.config_entries.async_reload.assert_not_called()


@pytest.mark.asyncio
async def test_legacy_unknown_implementation_becomes_auth_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Map the pre-2026.10 ValueError contract onto reauthentication semantics."""
    hass = _hass()
    entry = _entry()
    error = ValueError("Implementation not available")
    monkeypatch.setattr(
        integration.config_entry_oauth2_flow,
        "async_get_config_entry_implementation",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(ConfigEntryAuthFailed) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value.__cause__ is error
    entry.add_update_listener.assert_not_called()
    hass.config_entries.async_reload.assert_not_called()


@pytest.mark.asyncio
async def test_native_transient_token_refresh_error_is_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the HA 2026.10 token-refresh not-ready exception intact."""

    class NativeTransientTokenError(
        OAuth2TokenRequestTransientError,
        ConfigEntryNotReady,
    ):
        pass

    error = _token_error(NativeTransientTokenError, 503)

    with pytest.raises(ConfigEntryNotReady) as raised:
        await _setup_with_validation_error(monkeypatch, error)

    assert raised.value is error


@pytest.mark.asyncio
async def test_legacy_token_refresh_reauth_error_becomes_auth_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve reauth semantics for Home Assistant versions before 2026.10."""
    error = _token_error(OAuth2TokenRequestReauthError, 400)

    with pytest.raises(ConfigEntryAuthFailed) as raised:
        await _setup_with_validation_error(monkeypatch, error)

    assert raised.value.__cause__ is error
