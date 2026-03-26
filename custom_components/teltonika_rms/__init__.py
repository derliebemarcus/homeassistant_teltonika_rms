"""Teltonika RMS integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC
from typing import TYPE_CHECKING, Any, cast

from .const import (
    AUTH_MODE_OAUTH2,
    AUTH_MODE_PAT,
    CONF_AUTH_MODE,
    CONF_PAT_TOKEN,
    CONF_SPEC_PATH,
    DEFAULT_OPTIONS,
    DEFAULT_SPEC_PATH,
    DOMAIN,
    SERVICE_REFRESH,
)

SERVICE_GET_DEVICE_HISTORY = "get_device_history"

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.const import Platform

    PLATFORMS: tuple[str, ...] = (
        Platform.BINARY_SENSOR,
        Platform.SENSOR,
        Platform.DEVICE_TRACKER,
        Platform.BUTTON,
        Platform.SWITCH,
        Platform.UPDATE,
    )
except ModuleNotFoundError:
    PLATFORMS = ("binary_sensor", "sensor", "device_tracker", "button", "switch", "update")


@dataclass(slots=True)
class TeltonikaRmsRuntime:
    """Runtime data attached to config entry."""

    bundle: Any
    remove_service_listener: Callable[[], None] | None = None


async def async_setup_entry(hass: HomeAssistant, entry: Any) -> bool:
    """Set up Teltonika RMS from config entry."""
    from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
    from homeassistant.helpers import config_entry_oauth2_flow
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .api import OAuth2RmsAuthClient, PatRmsAuthClient, RmsApiClient, RmsAuthClient
    from .coordinator import (
        CoordinatorBundle,
        InventoryCoordinator,
        PortConfigCoordinator,
        PortScanCoordinator,
        StateCoordinator,
    )
    from .endpoint_matrix import load_endpoint_matrix
    from .status_channel import RmsStatusChannelManager

    auth_mode = str(entry.data.get(CONF_AUTH_MODE, AUTH_MODE_OAUTH2))
    auth_client: RmsAuthClient
    if auth_mode == AUTH_MODE_PAT:
        pat_token = str(entry.data.get(CONF_PAT_TOKEN, "")).strip()
        if not pat_token:
            raise ConfigEntryNotReady("PAT token missing")
        auth_client = PatRmsAuthClient(async_get_clientsession(hass), pat_token)
    else:
        try:
            implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        except config_entry_oauth2_flow.ImplementationUnavailableError as err:
            raise ConfigEntryNotReady(f"OAuth implementation unavailable: {err}") from err
        oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
        auth_client = OAuth2RmsAuthClient(oauth_session)

    spec_path = str(entry.options.get(CONF_SPEC_PATH, DEFAULT_SPEC_PATH))
    endpoint_matrix = await hass.async_add_executor_job(load_endpoint_matrix, spec_path)

    api = RmsApiClient(
        auth=auth_client,
        endpoint_matrix=endpoint_matrix,
    )
    status_manager = RmsStatusChannelManager(api)
    api.set_status_channel_manager(status_manager)

    inventory = InventoryCoordinator(hass, api, _merged_options(entry))
    state = StateCoordinator(hass, api, inventory, _merged_options(entry))
    port_scan = PortScanCoordinator(hass, api, inventory)
    port_config = PortConfigCoordinator(hass, api, inventory)
    bundle = CoordinatorBundle(
        inventory=inventory,
        state=state,
        port_scan=port_scan,
        port_config=port_config,
        status_channels=status_manager,
        api=api,
    )

    entry.runtime_data = TeltonikaRmsRuntime(bundle=bundle)

    try:
        await api.async_validate_connection()
        await inventory.async_config_entry_first_refresh()
        await state.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        raise ConfigEntryNotReady(f"Failed to initialize Teltonika RMS: {err}") from err

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    hass.async_create_task(_async_refresh_optional_coordinator("ethernet port scan", port_scan))
    hass.async_create_task(_async_refresh_optional_coordinator("port configuration", port_config))

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _build_refresh_handler(hass))

    if not hass.services.has_service(DOMAIN, SERVICE_GET_DEVICE_HISTORY):
        hass.services.async_register(
            DOMAIN, SERVICE_GET_DEVICE_HISTORY, _build_history_handler(hass)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: Any) -> bool:
    """Unload Teltonika RMS entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    if not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
        hass.services.async_remove(DOMAIN, SERVICE_GET_DEVICE_HISTORY)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: Any) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _build_refresh_handler(hass: HomeAssistant):
    from .coordinator import async_refresh_all

    async def _async_handle_refresh(call: Any) -> None:
        entries = hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            runtime: TeltonikaRmsRuntime | None = getattr(entry, "runtime_data", None)
            if runtime is None:
                continue
            await async_refresh_all(runtime.bundle)

    return _async_handle_refresh


def _build_history_handler(hass: HomeAssistant):
    from datetime import datetime

    import voluptuous as vol

    from .api import RmsApiClient

    # Helper to parse ISO-formatted datetime strings from service calls
    def parse_datetime_string(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value).replace(tzinfo=UTC)
        except ValueError as err:
            raise vol.Invalid(f"Invalid datetime format: {value}") from err

    # Validate input types for the service call
    HISTORY_SCHEMA = vol.Schema(
        {
            vol.Required("device_id"): str,
            vol.Required("from_time"): parse_datetime_string,
            vol.Required("to_time"): parse_datetime_string,
            vol.Required("interval"): str,
            vol.Optional("config_id", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Optional("keys"): vol.All(str, lambda v: [k.strip() for k in v.split(",")]),
        }
    )

    async def _async_handle_get_device_history(call: Any) -> None:
        try:
            validated_data = HISTORY_SCHEMA(call.data)
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

        for entry in await hass.config_entries.async_entries(DOMAIN):
            runtime: TeltonikaRmsRuntime | None = cast(
                TeltonikaRmsRuntime, getattr(entry, "runtime_data", None)
            )
            if runtime is None:
                continue
            api: RmsApiClient = runtime.bundle.api

            try:
                history_data = await api.async_get_device_history(
                    device_id=device_id,
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
