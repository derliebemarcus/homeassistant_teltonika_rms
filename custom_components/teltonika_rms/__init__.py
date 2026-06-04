"""Teltonika RMS integration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from homeassistant.helpers.typing import ConfigType

from . import api as api_mod
from . import coordinator as coordinator_mod
from . import endpoint_matrix, status_channel
from .const import (
    AUTH_MODE_OAUTH2,
    AUTH_MODE_PAT,
    CONF_AUTH_MODE,
    CONF_PAT_TOKEN,
    CONF_SPEC_PATH,
    DEFAULT_OPTIONS,
    DEFAULT_SPEC_PATH,
    DOMAIN,
    SERVICE_GET_DEVICE_HISTORY,
    SERVICE_REFRESH,
)
from .exceptions import RmsApiError
from .models import TeltonikaRmsRuntime

__all__ = [
    "DOMAIN",
    "SERVICE_GET_DEVICE_HISTORY",
    "TeltonikaRmsRuntime",
]

if TYPE_CHECKING:
    pass

LOGGER = logging.getLogger(__name__)

PLATFORMS: tuple[Platform, ...] = (
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.UPDATE,
)


async def async_setup(_hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up Teltonika RMS."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Teltonika RMS from config entry."""

    auth_mode = str(entry.data.get(CONF_AUTH_MODE, AUTH_MODE_OAUTH2))
    auth_client: api_mod.RmsAuthClient
    if auth_mode == AUTH_MODE_PAT:
        pat_token = str(entry.data.get(CONF_PAT_TOKEN, "")).strip()
        if not pat_token:
            raise ConfigEntryNotReady("PAT token missing")
        auth_client = api_mod.PatRmsAuthClient(
            aiohttp_client.async_get_clientsession(hass), pat_token
        )
    else:
        try:
            implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        except config_entry_oauth2_flow.ImplementationUnavailableError as err:
            raise ConfigEntryNotReady(f"OAuth implementation unavailable: {err}") from err
        oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
        auth_client = api_mod.OAuth2RmsAuthClient(oauth_session)

    spec_path = str(entry.options.get(CONF_SPEC_PATH, DEFAULT_SPEC_PATH))
    matrix = await hass.async_add_executor_job(endpoint_matrix.load_endpoint_matrix, spec_path)

    api = api_mod.RmsApiClient(
        auth=auth_client,
        endpoint_matrix=matrix,
    )
    status_manager = status_channel.RmsStatusChannelManager(api)
    api.set_status_channel_manager(status_manager)

    bundle = _initialize_bundle(hass, api, entry, status_manager)
    entry.runtime_data = TeltonikaRmsRuntime(bundle=bundle)

    try:
        await api.async_validate_connection()
        await bundle.inventory.async_config_entry_first_refresh()
        await bundle.state.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except RmsApiError as err:
        raise ConfigEntryNotReady(f"Failed to connect to Teltonika RMS: {err}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Unexpected error during initialization: {err}") from err

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    hass.async_create_task(
        _async_refresh_optional_coordinator("ethernet port scan", bundle.port_scan)
    )
    hass.async_create_task(
        _async_refresh_optional_coordinator("port configuration", bundle.port_config)
    )

    _register_services(hass)

    return True


def _initialize_bundle(
    hass: HomeAssistant,
    api: api_mod.RmsApiClient,
    entry: ConfigEntry,
    status_manager: status_channel.RmsStatusChannelManager,
) -> coordinator_mod.CoordinatorBundle:
    """Initialize all coordinators and wrap them in a bundle."""
    inventory = coordinator_mod.InventoryCoordinator(hass, api, _merged_options(entry), entry)
    state = coordinator_mod.StateCoordinator(
        hass, api, inventory, {"options": _merged_options(entry), "entry": entry}
    )
    port_scan = coordinator_mod.PortScanCoordinator(hass, api, inventory, entry)
    port_config = coordinator_mod.PortConfigCoordinator(hass, api, inventory, entry)

    return coordinator_mod.CoordinatorBundle(
        inventory=inventory,
        state=state,
        port_scan=port_scan,
        port_config=port_config,
        status_channels=status_manager,
        api=api,
    )


def _register_services(hass: HomeAssistant) -> None:
    """Register custom services for the integration."""
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _build_refresh_handler(hass))

    if not hass.services.has_service(DOMAIN, SERVICE_GET_DEVICE_HISTORY):
        hass.services.async_register(
            DOMAIN, SERVICE_GET_DEVICE_HISTORY, _build_history_handler(hass)
        )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Teltonika RMS entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    if not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
        hass.services.async_remove(DOMAIN, SERVICE_GET_DEVICE_HISTORY)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _build_refresh_handler(hass: HomeAssistant) -> Callable[[Any], Coroutine[Any, Any, None]]:
    """Build the refresh service handler."""
    from .coordinator import async_refresh_all

    async def _async_handle_refresh(call: Any) -> None:
        entries = hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            runtime: TeltonikaRmsRuntime | None = getattr(entry, "runtime_data", None)
            if runtime is None:
                continue
            await async_refresh_all(runtime.bundle)

    return _async_handle_refresh


def _parse_datetime_string(value: str) -> datetime:
    """Parse ISO-formatted datetime strings from service calls."""
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError as err:
        raise vol.Invalid(f"Invalid datetime format: {value}") from err


def _get_history_schema() -> Any:
    return vol.Schema(
        {
            vol.Required("device_id"): str,
            vol.Required("from_time"): _parse_datetime_string,
            vol.Required("to_time"): _parse_datetime_string,
            vol.Required("interval"): str,
            vol.Optional("config_id", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Optional("keys"): vol.All(str, lambda v: [k.strip() for k in v.split(",")]),
        }
    )


def _build_history_handler(hass: HomeAssistant) -> Callable[[Any], Coroutine[Any, Any, None]]:
    history_schema = _get_history_schema()

    async def _async_handle_get_device_history(call: Any) -> None:
        try:
            validated_data = history_schema(call.data)
        except vol.Invalid as err:
            LOGGER.error("Invalid service call data for get_device_history: %s", err)
            return

        device_id = validated_data["device_id"]
        from_time = validated_data["from_time"]
        to_time = validated_data["to_time"]
        interval = validated_data["interval"]
        config_id = validated_data.get("config_id")
        keys = validated_data.get("keys")

        if config_id == 0:
            config_id = None

        if not config_id and not keys:
            LOGGER.error(
                "Service get_device_history requires either 'config_id' or 'keys' to be provided."
            )
            return

        for entry in hass.config_entries.async_entries(DOMAIN):
            runtime: TeltonikaRmsRuntime | None = getattr(entry, "runtime_data", None)
            if runtime is None:
                continue
            api: api_mod.RmsApiClient = runtime.bundle.api

            try:
                history_data = await api.async_get_device_history(
                    device_id,
                    from_time=from_time,
                    to_time=to_time,
                    interval=interval,
                    config_id=config_id,
                    keys=keys,
                )
                hass.bus.async_fire(
                    f"{DOMAIN}_device_history",
                    {
                        "device_id": device_id,
                        "from_time": from_time.isoformat(),
                        "to_time": to_time.isoformat(),
                        "interval": interval,
                        "config_id": config_id,
                        "keys": keys,
                        "data": history_data,
                    },
                )
                LOGGER.debug(
                    "Published %s_device_history event for device %s with %s records.",
                    DOMAIN,
                    device_id,
                    len(history_data),
                )
            except Exception as err:  # pylint: disable=broad-except-clause
                LOGGER.error("Failed to fetch device history for %s: %s", device_id, err)
                hass.bus.async_fire(
                    f"{DOMAIN}_device_history_error",
                    {
                        "device_id": device_id,
                        "error": str(err),
                    },
                )
                return

    return _async_handle_get_device_history


def _merged_options(entry: Any) -> dict[str, Any]:
    merged = dict(DEFAULT_OPTIONS)
    merged.update(entry.options)
    return merged


async def _async_refresh_optional_coordinator(name: str, coordinator: Any) -> None:
    """Refresh optional data sources without blocking config-entry setup."""
    try:
        await coordinator.async_request_refresh()
    except Exception as err:  # pragma: no cover - defensive background guard
        LOGGER.debug("Optional Teltonika RMS %s refresh failed after setup: %s", name, err)
