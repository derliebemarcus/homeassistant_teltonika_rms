"""Application credentials support for Teltonika RMS OAuth2."""

import asyncio

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2Implementation,
    LocalOAuth2ImplementationWithPkce,
)

from .const import AUTHORIZE_URL, TOKEN_URL


async def async_get_local_oauth_show_setup(_hass: HomeAssistant) -> bool:
    """Return whether to show setup in local oauth."""
    await asyncio.sleep(0)
    return True


async def async_get_authorization_server(_hass: HomeAssistant) -> AuthorizationServer:
    """Return OAuth2 authorization server metadata."""
    await asyncio.sleep(0)
    return AuthorizationServer(
        authorize_url=AUTHORIZE_URL,
        token_url=TOKEN_URL,
    )


async def async_get_auth_implementation(
    hass: HomeAssistant,
    auth_domain: str,
    credential: ClientCredential,
) -> AbstractOAuth2Implementation:
    """Build a PKCE OAuth2 implementation."""
    await asyncio.sleep(0)
    return LocalOAuth2ImplementationWithPkce(
        hass,
        auth_domain,
        credential.client_id,
        AUTHORIZE_URL,
        TOKEN_URL,
        credential.client_secret,
    )


async def async_get_description_placeholders(_hass: HomeAssistant) -> dict[str, str]:
    """Add dynamic placeholders for credentials form."""
    await asyncio.sleep(0)
    return {
        "console_url": "https://rms.teltonika-networks.com/",
    }
