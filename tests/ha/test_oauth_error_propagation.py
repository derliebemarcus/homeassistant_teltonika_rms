"""Regression contract for Home Assistant OAuth2 setup error propagation."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    OAuth2TokenRequestError,
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


def _prepare_setup_with_validation_error(
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
    monkeypatch.setattr(
        integration,
        "_initialize_bundle",
        MagicMock(return_value=MagicMock()),
    )

    return hass, entry


def _assert_failed_setup_has_no_listener_or_reload(hass: Any, entry: Any) -> None:
    entry.add_update_listener.assert_not_called()
    hass.config_entries.async_reload.assert_not_called()


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
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


@pytest.mark.asyncio
async def test_legacy_implementation_unavailable_becomes_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retain pre-2026.10 setup-retry semantics without increasing the HA minimum."""
    error = config_entry_oauth2_flow.ImplementationUnavailableError(
        "implementation unavailable"
    )
    hass = _hass()
    entry = _entry()
    monkeypatch.setattr(
        integration.config_entry_oauth2_flow,
        "async_get_config_entry_implementation",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(ConfigEntryNotReady) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value.__cause__ is error
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


@pytest.mark.asyncio
async def test_native_unknown_implementation_is_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep HA 2026.10 auth-failed semantics ahead of ValueError compatibility."""

    class NativeUnknownImplementation(ConfigEntryAuthFailed, ValueError):
        pass

    error = NativeUnknownImplementation("implementation not available")
    hass = _hass()
    entry = _entry()
    monkeypatch.setattr(
        integration.config_entry_oauth2_flow,
        "async_get_config_entry_implementation",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(ConfigEntryAuthFailed) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value is error
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


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
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


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
    hass, entry = _prepare_setup_with_validation_error(monkeypatch, error)

    with pytest.raises(ConfigEntryNotReady) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value is error
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


@pytest.mark.asyncio
async def test_native_token_refresh_reauth_error_is_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the HA 2026.10 token-refresh authentication failure intact."""

    class NativeReauthTokenError(
        OAuth2TokenRequestReauthError,
        ConfigEntryAuthFailed,
    ):
        pass

    error = _token_error(NativeReauthTokenError, 400)
    hass, entry = _prepare_setup_with_validation_error(monkeypatch, error)

    with pytest.raises(ConfigEntryAuthFailed) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value is error
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


@pytest.mark.asyncio
async def test_legacy_token_refresh_reauth_error_becomes_auth_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve reauth semantics for Home Assistant versions before 2026.10."""
    error = _token_error(OAuth2TokenRequestReauthError, 400)
    hass, entry = _prepare_setup_with_validation_error(monkeypatch, error)

    with pytest.raises(ConfigEntryAuthFailed) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value.__cause__ is error
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


@pytest.mark.asyncio
async def test_legacy_token_refresh_error_becomes_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Map generic pre-2026.10 OAuth token failures onto setup retry semantics."""
    error = _token_error(OAuth2TokenRequestError, 503)
    hass, entry = _prepare_setup_with_validation_error(monkeypatch, error)

    with pytest.raises(ConfigEntryNotReady) as raised:
        await integration.async_setup_entry(hass, entry)

    assert raised.value.__cause__ is error
    _assert_failed_setup_has_no_listener_or_reload(hass, entry)


@pytest.mark.asyncio
async def test_oauth_session_token_validation_error_propagates_unchanged() -> None:
    """Do not intercept an error raised directly by OAuth2Session token validation."""
    error = _token_error(OAuth2TokenRequestTransientError, 503)
    oauth_session = MagicMock()
    oauth_session.async_ensure_token_valid = AsyncMock(side_effect=error)
    oauth_session.token = {"access_token": "test-token"}
    auth_client = integration.api_mod.OAuth2RmsAuthClient(oauth_session)

    with pytest.raises(OAuth2TokenRequestTransientError) as raised:
        await auth_client.async_get_access_token()

    assert raised.value is error
    oauth_session.async_ensure_token_valid.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_rms_transport_does_not_retry_or_wrap_oauth_token_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep OAuth token failures out of the generic RMS ClientError retry wrapper."""
    error = _token_error(OAuth2TokenRequestError, 503)
    auth_client = MagicMock()
    auth_client.async_request = AsyncMock(side_effect=error)
    api = integration.api_mod.RmsApiClient(auth=auth_client, endpoint_matrix=MagicMock())
    sleep = AsyncMock()
    monkeypatch.setattr(integration.api_mod.asyncio, "sleep", sleep)

    with pytest.raises(OAuth2TokenRequestError) as raised:
        await api.async_request("GET", "/devices")

    assert raised.value is error
    auth_client.async_request.assert_awaited_once()
    sleep.assert_not_awaited()
