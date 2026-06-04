"""Switch entities for Teltonika RMS."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity, async_setup_platform_helper, is_poe_capable_series

LOGGER = logging.getLogger(__name__)


PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure Teltonika RMS switches."""
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle

    # Platform-specific entity discovery via common helper
    async_setup_platform_helper(
        entry,
        bundle,
        async_add_entities,
        _discover_new_entities,
        [bundle.inventory, bundle.port_config, bundle.port_scan],
    )


def _discover_new_entities(bundle: CoordinatorBundle, known: set[str]) -> list[SwitchEntity]:
    """Find and return new switch entities not yet in 'known'."""
    new_entities: list[SwitchEntity] = []
    for device_id, device_info in bundle.inventory.data.items():
        model = device_info.get("model", "UNKNOWN")
        if not is_poe_capable_series(model):
            continue

        port_configs = _get_device_port_configs(device_id, model, bundle)

        for port_id, port in port_configs.items():
            if _supports_poe(port):
                unique_poe = f"{device_id}_{port_id}_poe"
                if unique_poe not in known:
                    known.add(unique_poe)
                    new_entities.append(RmsPoeSwitch(bundle, device_id, port_id))

    return new_entities


def _get_device_port_configs(
    device_id: str, model: str, bundle: CoordinatorBundle
) -> dict[str, dict[str, Any]]:
    """Get port configurations for a specific device."""
    port_configs: dict[str, dict[str, Any]] = {
        str(p.get("id")): p
        for p in bundle.port_config.data.get(device_id, [])
        if p.get("id") and str(p.get("id")) != "NIL"
    }

    is_switch_device = model.startswith("TSW") or model.startswith("SWM")
    if is_switch_device and not port_configs:
        # Default ports for switch devices if no config is available yet
        for i in range(1, 9):
            port_configs[f"port{i}"] = {"id": f"port{i}"}
        for i in range(1, 3):
            port_configs[f"sfp{i}"] = {"id": f"sfp{i}"}

    # Supplement with scanned ports
    for scan_port in bundle.port_scan.data.get(device_id, []):
        port_name = str(scan_port.get("name") or "").strip()
        if port_name and port_name != "NIL" and port_name not in port_configs:
            port_configs[port_name] = {"id": port_name}

    return port_configs


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
        if port is None:
            return False

        val = port.get("poe_enable")
        if val is not None:
            return str(val) in ("1", "true", "True")

        val_poe = port.get("PoE")
        if val_poe is None:
            val_poe = port.get("poe")
        if val_poe is not None:
            return str(val_poe) in ("1", "true", "True")

        val_poe_w = port.get("PoE (W)")
        if val_poe_w is not None:
            try:
                return float(val_poe_w) > 0.0
            except (TypeError, ValueError):
                return False

        return False

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

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        raise NotImplementedError()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        raise NotImplementedError()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_poe(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_poe(False)

    async def _async_set_poe(self, enabled: bool) -> None:
        try:
            await self._bundle.api.async_set_device_port_poe(self.device_id, self._port_id, enabled)
        except ConfigEntryAuthFailed as err:
            raise HomeAssistantError(
                "RMS PoE control failed. The device model may not support RMS remote PoE "
                "configuration, or you may need to reauthenticate your Home Assistant "
                "integration to activate the device_configurations:write permission."
            ) from err
        await self._bundle.port_config.async_request_refresh()

    @property
    def _port(self) -> dict[str, Any] | None:
        for port in self._bundle.port_config.data.get(self.device_id, []):
            if str(port.get("id")) == self._port_id:
                return port
        return None


def _supports_poe(port: dict[str, Any]) -> bool:
    return (
        "poe_enable" in port
        or port.get("PoE") is not None
        or port.get("poe") is not None
        or port.get("PoE (W)") is not None
    )
