"""Switch entities for Teltonika RMS."""

from __future__ import annotations

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
        for device_id in bundle.inventory.data:
            for port in bundle.port_config.data.get(device_id, []):
                port_id = str(port.get("id") or "").strip()
                if not port_id:
                    continue

                if _supports_poe(port):
                    unique_poe = f"{device_id}_{port_id}_poe"
                    if unique_poe not in known:
                        known.add(unique_poe)
                        new_entities.append(RmsPoeSwitch(bundle, device_id, port_id))

                if _supports_port(port):
                    unique_port = f"{device_id}_{port_id}_port"
                    if unique_port not in known:
                        known.add(unique_port)
                        new_entities.append(RmsPortSwitch(bundle, device_id, port_id))

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(bundle.inventory.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.port_config.async_add_listener(_add_new_entities))


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
        return super().available and self._port is not None and _supports_port(self._port)

    @property
    def is_on(self) -> bool:
        port = self._port
        return port is not None and str(port.get("enabled")) == "1"

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
            await self._bundle.api.async_set_device_port_enabled(self.device_id, self._port_id, enabled)
        except ConfigEntryAuthFailed as err:
            raise HomeAssistantError(
                "RMS port control requires device_configurations:write permissions. "
                "Reauthenticate and try again."
            ) from err
        await self._bundle.port_config.async_request_refresh()

    @property
    def _port(self) -> dict[str, Any] | None:
        for port in self._bundle.port_config.data.get(self.device_id, []):
            if str(port.get("id")) == self._port_id:
                return port
        return None


def _supports_poe(port: dict[str, Any]) -> bool:
    return "poe_enable" in port


def _supports_port(port: dict[str, Any]) -> bool:
    return "enabled" in port
