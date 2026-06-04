"""Tests for OAuth application credential wiring."""

from __future__ import annotations

import asyncio

import pytest
from homeassistant.components.application_credentials import ClientCredential
from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2ImplementationWithPkce,
)

from custom_components.teltonika_rms.application_credentials import (
    async_get_auth_implementation,
    async_get_authorization_server,
    async_get_description_placeholders,
    async_get_local_oauth_show_setup,
)
from custom_components.teltonika_rms.const import AUTHORIZE_URL, TOKEN_URL

pytestmark = pytest.mark.ha


def test_async_get_local_oauth_show_setup_returns_true() -> None:
    assert asyncio.run(async_get_local_oauth_show_setup(object())) is True  # type: ignore[arg-type]


def test_async_get_auth_implementation_uses_correct_pkce_argument_order() -> None:
    implementation = asyncio.run(
        async_get_auth_implementation(
            hass=object(),  # type: ignore[arg-type]
            auth_domain="custom_components.teltonika_rms.test",
            credential=ClientCredential(
                client_id="client-id",
                client_secret="client-secret",
            ),
        )
    )

    assert isinstance(implementation, LocalOAuth2ImplementationWithPkce)
    assert implementation.domain == "custom_components.teltonika_rms.test"
    assert implementation.client_id == "client-id"
    assert implementation.client_secret == "client-secret"
    assert implementation.authorize_url == AUTHORIZE_URL
    assert implementation.token_url == TOKEN_URL


def test_authorization_server_and_placeholders_use_expected_urls() -> None:
    server = asyncio.run(async_get_authorization_server(object()))  # type: ignore[arg-type]
    placeholders = asyncio.run(
        async_get_description_placeholders(object())  # type: ignore[arg-type]
    )

    assert server.authorize_url == AUTHORIZE_URL
    assert server.token_url == TOKEN_URL
    assert placeholders == {"console_url": "https://rms.teltonika-networks.com/"}
