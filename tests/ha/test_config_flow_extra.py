"""Extra tests for Teltonika RMS config flow to ensure high coverage."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.teltonika_rms.config_flow import OAuth2FlowHandler, TeltonikaRmsOptionsFlow
from custom_components.teltonika_rms.const import (
    AUTH_MODE_PAT,
    CONF_AUTH_MODE,
    CONF_PAT_TOKEN,
)


@pytest.mark.asyncio
async def test_flow_user_step(hass: HomeAssistant) -> None:
    """Test the user step shows a menu."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    result = await handler.async_step_user()
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_flow_pat_step_validation(hass: HomeAssistant) -> None:
    """Test PAT step validation logic."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler.context = {}

    # Test empty input
    result = await handler.async_step_pat(user_input={CONF_PAT_TOKEN: ""})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_pat"}

    # Test valid input
    with (
        patch(
            "custom_components.teltonika_rms.config_flow._token_fingerprint", return_value="hash"
        ),
        patch.object(hass.config_entries, "async_entry_for_domain_unique_id", return_value=None),
    ):
        result = await handler.async_step_pat(user_input={CONF_PAT_TOKEN: "valid-token"})
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_PAT_TOKEN] == "valid-token"
        assert result["data"][CONF_AUTH_MODE] == AUTH_MODE_PAT


@pytest.mark.asyncio
async def test_flow_reauth_oauth(hass: HomeAssistant) -> None:
    """Test reauth flow for OAuth2."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler.context = {"entry_id": "test-entry"}

    mock_entry = MagicMock()
    mock_entry.data = {CONF_AUTH_MODE: "oauth2"}

    with (
        patch.object(hass.config_entries, "async_get_entry", return_value=mock_entry),
        patch.object(
            handler, "async_step_pick_implementation", return_value={"type": "form"}
        ) as mock_pick,
    ):
        await handler.async_step_reauth({})
        mock_pick.assert_called_once()


@pytest.mark.asyncio
async def test_flow_reauth_pat(hass: HomeAssistant) -> None:
    """Test reauth flow for PAT."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler.context = {"entry_id": "test-entry"}

    mock_entry = MagicMock()
    mock_entry.data = {CONF_AUTH_MODE: AUTH_MODE_PAT}

    with patch.object(hass.config_entries, "async_get_entry", return_value=mock_entry):
        result = await handler.async_step_reauth({})
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_pat"


@pytest.mark.asyncio
async def test_flow_reauth_pat_submission(hass: HomeAssistant) -> None:
    """Test PAT reauth submission."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler._reauth_entry = MagicMock()
    handler.context = {}

    # Test valid submission
    with patch.object(
        handler, "async_update_reload_and_abort", return_value={"type": "abort"}
    ) as mock_abort:
        await handler.async_step_reauth_pat(user_input={CONF_PAT_TOKEN: "new-token"})
        mock_abort.assert_called_once()


@pytest.mark.asyncio
async def test_async_oauth_create_entry_reauth_mismatch(hass: HomeAssistant) -> None:
    """Test OAuth entry creation fails on unique_id mismatch during reauth."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler.context = {}

    # Mock token with different sub
    data = {"token": {"access_token": "header.eyJzdWIiOiAibmV3LWlkIn0.sig"}}  # gitleaks:allow

    with patch.object(OAuth2FlowHandler, "source", "reauth"):
        handler._reauth_entry = MagicMock()
        handler._reauth_entry.unique_id = "original-id"
        result = await handler.async_oauth_create_entry(data)
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "wrong_account"


@pytest.mark.asyncio
async def test_options_flow_budget_exceeded(hass: HomeAssistant) -> None:
    """Test options flow blocks on budget excess."""
    mock_entry = MagicMock()
    mock_entry.options = {}
    flow = TeltonikaRmsOptionsFlow(mock_entry)
    flow.hass = hass

    user_input = {
        "inventory_interval": 60,
        "state_interval": 60,
        "estimated_devices": 500,
        "tags": "",
        "spec_path": "",
        "enable_location": True,
        "device_status": "online",
    }

    # Create a future for async_add_executor_job
    future: asyncio.Future[Any] = asyncio.Future()
    mock_matrix = MagicMock()
    mock_matrix.path_for.return_value = None
    future.set_result(mock_matrix)

    with (
        patch.object(hass, "async_add_executor_job", return_value=future),
        patch(
            "custom_components.teltonika_rms.config_flow.estimate_monthly_requests",
            return_value=9999999,
        ),
    ):
        result = await flow.async_step_init(user_input=user_input)
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "request_budget_exceeded"}


@pytest.mark.asyncio
async def test_options_flow_success(hass: HomeAssistant) -> None:
    """Test options flow success path."""
    mock_entry = MagicMock()
    mock_entry.options = {}
    flow = TeltonikaRmsOptionsFlow(mock_entry)
    flow.hass = hass

    user_input = {
        "inventory_interval": 60,
        "state_interval": 60,
        "estimated_devices": 10,
        "tags": "tag1",
        "spec_path": "custom.yaml",
        "enable_location": True,
    }

    future: asyncio.Future[Any] = asyncio.Future()
    mock_matrix = MagicMock()
    mock_matrix.path_for.return_value = None
    future.set_result(mock_matrix)

    with (
        patch.object(hass, "async_add_executor_job", return_value=future),
        patch(
            "custom_components.teltonika_rms.config_flow.estimate_monthly_requests",
            return_value=100,
        ),
        patch.object(
            flow, "async_create_entry", return_value={"type": "create_entry"}
        ) as mock_create,
    ):
        await flow.async_step_init(user_input=user_input)
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_oauth_create_entry_new(hass: HomeAssistant) -> None:
    """Test standard OAuth entry creation."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler.context = {}

    data = {"token": {"access_token": "header.eyJzdWIiOiAibmV3LXVzZXIifQ.sig"}}  # gitleaks:allow
    with patch.object(hass.config_entries, "async_entry_for_domain_unique_id", return_value=None):
        result = await handler.async_oauth_create_entry(data)
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Teltonika RMS"


@pytest.mark.asyncio
async def test_oauth_create_entry_reauth_success(hass: HomeAssistant) -> None:
    """Test OAuth reauth success."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    handler.context = {}

    data = {"token": {"access_token": "header.eyJzdWIiOiAidXNlci0xMjMifQ.sig"}}  # gitleaks:allow

    with (
        patch.object(OAuth2FlowHandler, "source", "reauth"),
        patch.object(
            handler, "async_update_reload_and_abort", return_value={"type": "abort"}
        ) as mock_abort,
    ):
        handler._reauth_entry = MagicMock()
        handler._reauth_entry.unique_id = "user-123"
        await handler.async_oauth_create_entry(data)
        mock_abort.assert_called_once()


@pytest.mark.asyncio
async def test_flow_user_step_submit(hass: HomeAssistant) -> None:
    """Test user step submission."""
    handler = OAuth2FlowHandler()
    handler.hass = hass

    # Test choosing PAT
    result = await handler.async_step_user(user_input={"next_step_id": "pat"})
    assert result["type"] == FlowResultType.MENU


@pytest.mark.asyncio
async def test_async_step_oauth2(hass: HomeAssistant) -> None:
    """Test OAuth2 step."""
    handler = OAuth2FlowHandler()
    handler.hass = hass
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.AbstractOAuth2FlowHandler.async_step_user",
        return_value={"type": "external_step"},
    ):
        result = await handler.async_step_oauth2()
        assert result["type"] == "external_step"


def test_extract_subject_errors() -> None:
    """Test token extraction error cases."""
    from custom_components.teltonika_rms.config_flow import _extract_subject_from_token

    assert _extract_subject_from_token({}) is None
    assert _extract_subject_from_token({"token": "not-a-dict"}) is None
    assert _extract_subject_from_token({"token": {"access_token": 123}}) is None
    assert _extract_subject_from_token({"token": {"access_token": "short"}}) is None
    assert _extract_subject_from_token({"token": {"access_token": "header.bad-json.sig"}}) is None
