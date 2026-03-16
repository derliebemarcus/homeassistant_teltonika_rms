"""Config flow for Teltonika RMS."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow

from .api import estimate_monthly_requests, normalize_tags
from .const import (
    AUTH_MODE_OAUTH2,
    AUTH_MODE_PAT,
    CONF_AUTH_MODE,
    CONF_DEVICE_STATUS,
    CONF_ENABLE_LOCATION,
    CONF_ESTIMATED_DEVICES,
    CONF_INVENTORY_INTERVAL,
    CONF_PAT_TOKEN,
    CONF_SPEC_PATH,
    CONF_STATE_INTERVAL,
    CONF_TAGS,
    DEFAULT_OPTIONS,
    DEFAULT_SPEC_PATH,
    DOMAIN,
    MAX_MONTHLY_REQUESTS,
    OAUTH2_SCOPES,
    REQUEST_BUDGET_HEADROOM,
)
from .endpoint_matrix import load_endpoint_matrix

LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle OAuth2/PAT config flow for Teltonika RMS."""

    DOMAIN = DOMAIN
    VERSION = 1

    _reauth_entry: ConfigEntry | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return flow logger required by Home Assistant."""
        return LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Append OAuth scopes during authorize step."""
        return {"scope": " ".join(OAUTH2_SCOPES)}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Offer authentication mode selection."""
        return self.async_show_menu(step_id="user", menu_options=["oauth2", "pat"])

    async def async_step_oauth2(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Start OAuth2 authentication."""
        return await super().async_step_user(user_input)

    async def async_step_pat(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Create entry using PAT token authentication."""
        errors: dict[str, str] = {}
        if user_input is not None:
            token = str(user_input.get(CONF_PAT_TOKEN, "")).strip()
            if not token:
                errors["base"] = "invalid_pat"
            else:
                unique_id = f"pat_{_token_fingerprint(token)}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Teltonika RMS",
                    data={
                        CONF_AUTH_MODE: AUTH_MODE_PAT,
                        CONF_PAT_TOKEN: token,
                    },
                    options=dict(DEFAULT_OPTIONS),
                )

        schema = vol.Schema({vol.Required(CONF_PAT_TOKEN): str})
        return self.async_show_form(step_id="pat", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Begin reauthentication for the existing auth mode."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if self._reauth_entry is None:
            return self.async_abort(reason="reauth_failed")
        auth_mode = str(self._reauth_entry.data.get(CONF_AUTH_MODE, AUTH_MODE_OAUTH2))
        if auth_mode == AUTH_MODE_PAT:
            return await self.async_step_reauth_pat()
        return await self.async_step_pick_implementation()

    async def async_step_reauth_pat(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reauthenticate PAT by replacing the token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            token = str(user_input.get(CONF_PAT_TOKEN, "")).strip()
            if not token:
                errors["base"] = "invalid_pat"
            elif self._reauth_entry is None:
                return self.async_abort(reason="reauth_failed")
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data_updates={
                        CONF_AUTH_MODE: AUTH_MODE_PAT,
                        CONF_PAT_TOKEN: token,
                    },
                )

        schema = vol.Schema({vol.Required(CONF_PAT_TOKEN): str})
        return self.async_show_form(step_id="reauth_pat", data_schema=schema, errors=errors)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create (or update) entry once OAuth callback is complete."""
        unique_id = _extract_subject_from_token(data)
        if unique_id:
            await self.async_set_unique_id(unique_id)
            if self.source != "reauth":
                self._abort_if_unique_id_configured()

        oauth_data = dict(data)
        oauth_data[CONF_AUTH_MODE] = AUTH_MODE_OAUTH2

        if self.source == "reauth":
            if self._reauth_entry is not None:
                if (
                    unique_id
                    and self._reauth_entry.unique_id
                    and self._reauth_entry.unique_id != unique_id
                ):
                    return self.async_abort(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data_updates=oauth_data,
                )

        return self.async_create_entry(
            title="Teltonika RMS",
            data=oauth_data,
            options=dict(DEFAULT_OPTIONS),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return options flow handler."""
        return TeltonikaRmsOptionsFlow(config_entry)


class TeltonikaRmsOptionsFlow(OptionsFlow):
    """Options flow with request-budget safety checks."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized = dict(user_input)
            normalized[CONF_TAGS] = ",".join(normalize_tags(str(user_input.get(CONF_TAGS, ""))))

            inventory_interval = int(normalized[CONF_INVENTORY_INTERVAL])
            state_interval = int(normalized[CONF_STATE_INTERVAL])
            estimated_devices = int(normalized[CONF_ESTIMATED_DEVICES])
            spec_path = str(normalized[CONF_SPEC_PATH]).strip() or DEFAULT_SPEC_PATH

            matrix = await self.hass.async_add_executor_job(load_endpoint_matrix, spec_path)
            aggregate_supported = matrix.path_for("device_state_aggregate") is not None

            estimate = estimate_monthly_requests(
                inventory_interval=inventory_interval,
                state_interval=state_interval,
                estimated_devices=estimated_devices,
                aggregate_state_supported=aggregate_supported,
            )
            if estimate > int(MAX_MONTHLY_REQUESTS * REQUEST_BUDGET_HEADROOM):
                errors["base"] = "request_budget_exceeded"
            else:
                normalized[CONF_SPEC_PATH] = spec_path
                return self.async_create_entry(title="", data=normalized)

        merged = dict(DEFAULT_OPTIONS)
        merged.update(self._config_entry.options)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_INVENTORY_INTERVAL, default=merged[CONF_INVENTORY_INTERVAL]
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                vol.Required(CONF_STATE_INTERVAL, default=merged[CONF_STATE_INTERVAL]): vol.All(
                    vol.Coerce(int), vol.Range(min=60, max=3600)
                ),
                vol.Required(
                    CONF_ESTIMATED_DEVICES, default=merged[CONF_ESTIMATED_DEVICES]
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=500)),
                vol.Optional(CONF_TAGS, default=merged[CONF_TAGS]): str,
                vol.Optional(CONF_DEVICE_STATUS, default=merged[CONF_DEVICE_STATUS]): str,
                vol.Optional(CONF_SPEC_PATH, default=merged[CONF_SPEC_PATH]): str,
                vol.Required(CONF_ENABLE_LOCATION, default=merged[CONF_ENABLE_LOCATION]): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


def _extract_subject_from_token(data: dict[str, Any]) -> str | None:
    token = data.get("token", {})
    if not isinstance(token, dict):
        return None
    raw_access_token = token.get(CONF_ACCESS_TOKEN)
    if not isinstance(raw_access_token, str):
        return None
    parts = raw_access_token.split(".")
    if len(parts) < 2:
        return None
    payload_segment = parts[1]
    padded = payload_segment + "=" * (-len(payload_segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return None
    subject = payload.get("sub")
    return str(subject) if subject is not None else None


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
