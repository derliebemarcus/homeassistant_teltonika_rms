"""Switch entities for Teltonika RMS."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika RMS switch entities."""
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle
    known: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_entities: list[SwitchEntity] = []
        for device_id, device_info in bundle.inventory.data.items():
            model = device_info.get("model", "UNKNOWN")
            is_switch_device = model.startswith("TSW") or model.startswith("SWM")

            port_configs = {
                str(p.get("id")): p
                for p in bundle.port_config.data.get(device_id, [])
                if p.get("id")
            }

            if is_switch_device and not port_configs:
                for i in range(1, 9):
                    port_configs[f"port{i}"] = {"id": f"port{i}"}
                for i in range(1, 3):
                    port_configs[f"sfp{i}"] = {"id": f"sfp{i}"}

            for scan_port in bundle.port_scan.data.get(device_id, []):
                port_name = str(scan_port.get("name") or "").strip()
                if port_name and port_name not in port_configs:
                    port_configs[port_name] = {"id": port_name}

            ports = list(port_configs.values())

            LOGGER.debug(
                "Device detected: %s (Model: %s, Is Switch: %s). Found %d port configurations.",
                device_id,
                model,
                is_switch_device,
                len(ports),
            )

            for port in ports:
                LOGGER.debug("Device %s configuring port: %s", device_id, port)
                port_id = str(port.get("id") or "").strip()
                if not port_id:
                    continue

                if _supports_poe(port):
                    unique_poe = f"{device_id}_{port_id}_poe"
                    if unique_poe not in known:
                        known.add(unique_poe)
                        new_entities.append(RmsPoeSwitch(bundle, device_id, port_id))

                if _supports_port(port) or is_switch_device:
                    unique_port = f"{device_id}_{port_id}_port"
                    if unique_port not in known:
                        known.add(unique_port)
                        new_entities.append(RmsPortSwitch(bundle, device_id, port_id))

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(bundle.inventory.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.port_config.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.port_scan.async_add_listener(_add_new_entities))


class RmsPoeSwitch(TeltonikaRmsEntity, SwitchEntity):
    """Switch that controls PoE on one RMS switch port."""

    _attr_icon = "mdi:power-plug"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, bundle: CoordinatorBundle, device_id: str, port_id: str) -> None:
        super().__init__(bundle, device_id, coordinator=bundle.port_config)
        self._port_id = port_id
        self._attr_unique_id = f"{device_id}_{port_id}_poe"
        self._attr_name = f"{port_id.upper()} PoE"

    @property
    def available(self) -> bool:
        return super().available and self._port is not None and _supports_poe(self._port)

    @property
    def is_on(self) -> bool:
        port = self._port
        return port is not None and str(port.get("poe_enable")) == "1"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        port = self._port or {}
        return {
            "port_id": self._port_id,
            "description": port.get("description"),
            "enabled": port.get("enabled"),
            "autoneg": port.get("autoneg"),
            "isolated": port.get("isolated"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_poe(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_poe(False)

    async def _async_set_poe(self, enabled: bool) -> None:
        try:
            await self._bundle.api.async_set_device_port_poe(self.device_id, self._port_id, enabled)
        except ConfigEntryAuthFailed as err:
            raise HomeAssistantError(
                "RMS PoE control requires device_configurations:write permissions. "
                "Reauthenticate and try again."
            ) from err
        await self._bundle.port_config.async_request_refresh()

    @property
    def _port(self) -> dict[str, Any] | None:
        for port in self._bundle.port_config.data.get(self.device_id, []):
            if str(port.get("id")) == self._port_id:
                return port
        return None


class RmsPortSwitch(TeltonikaRmsEntity, SwitchEntity):
    """Switch that controls port enabled state on one RMS switch port."""

    _attr_icon = "mdi:ethernet"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, bundle: CoordinatorBundle, device_id: str, port_id: str) -> None:
        super().__init__(bundle, device_id, coordinator=bundle.port_config)
        self._port_id = port_id
        self._attr_unique_id = f"{device_id}_{port_id}_port"
        self._attr_name = f"{port_id.upper()}"

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        model = self._bundle.inventory.data.get(self.device_id, {}).get("model", "")
        is_switch_device = model.startswith("TSW") or model.startswith("SWM")
        if self._port is None:
            return is_switch_device
        return _supports_port(self._port) or is_switch_device

    @property
    def is_on(self) -> bool | None:
        port = self._port
        if port is None:
            return False

        val = port.get("enabled")
        if val is not None:
            return str(val) == "1"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        port = self._port or {}
        return {
            "port_id": self._port_id,
            "description": port.get("description"),
            "poe_enable": port.get("poe_enable"),
            "autoneg": port.get("autoneg"),
            "isolated": port.get("isolated"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_port(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_port(False)

    async def _async_set_port(self, enabled: bool) -> None:
        try:
            await self._bundle.api.async_set_device_port_enabled(
                self.device_id, self._port_id, enabled
            )
        except ConfigEntryAuthFailed as err:
            raise HomeAssistantError(
                "RMS port control failed. This requires device_configurations:write permissions "
                "and the device model must support RMS port configuration."
            ) from err
        await self._bundle.port_config.async_request_refresh()

    @property
    def _port(self) -> dict[str, Any] | None:
        port_data: dict[str, Any] | None = None
        for port in self._bundle.port_config.data.get(self.device_id, []):
            if str(port.get("id")) == self._port_id:
                port_data = port.copy()
                break

        for scan_port in self._bundle.port_scan.data.get(self.device_id, []):
            if str(scan_port.get("name") or "").strip() == self._port_id:
                if port_data is None:
                    port_data = {"id": self._port_id}
                if "state" not in port_data:
                    port_data["state"] = scan_port.get("state")
                break

        return port_data


def _supports_poe(port: dict[str, Any]) -> bool:
    return "poe_enable" in port


def _supports_port(port: dict[str, Any]) -> bool:
    return "enabled" in port
