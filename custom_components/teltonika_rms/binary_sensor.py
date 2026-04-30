"""Binary sensors for Teltonika RMS."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika RMS binary sensor entities."""
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle
    known: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_entities: list[BinarySensorEntity] = []

        for device_id, device_info in bundle.inventory.data.items():
            # 1. Device Online State
            online_unique = f"{device_id}_online"
            if online_unique not in known:
                known.add(online_unique)
                new_entities.append(RmsOnlineBinarySensor(bundle, device_id))

            # 2. Port Link States
            port_ids = _collect_device_port_ids(device_id, device_info, bundle)
            for port_id in sorted(port_ids):
                unique_port = f"{device_id}_{port_id}_link"
                if unique_port not in known:
                    known.add(unique_port)
                    new_entities.append(RmsPortLinkBinarySensor(bundle, device_id, port_id))

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(bundle.inventory.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.port_scan.async_add_listener(_add_new_entities))


def _collect_device_port_ids(
    device_id: str, device_info: dict[str, Any], bundle: CoordinatorBundle
) -> set[str]:
    """Collect all relevant port identifiers for a device."""
    port_ids: set[str] = set()

    # 1. From port configuration data
    for port in bundle.port_config.data.get(device_id, []):
        pid = str(port.get("id") or "").strip()
        if pid and pid != "NIL":
            if pid.startswith("switch_"):
                pid = pid[7:]
            port_ids.add(pid)

    # 2. Default switch ports for specific models
    model = device_info.get("model", "UNKNOWN")
    if model.startswith(("TSW", "SWM")):
        port_ids.update(f"port{i}" for i in range(1, 9))
        port_ids.update(f"sfp{i}" for i in range(1, 3))

    # 3. From scanning results
    for scan_port in bundle.port_scan.data.get(device_id, []):
        pid = str(scan_port.get("name") or "").strip()
        if pid and pid != "NIL":
            port_ids.add(pid)

    return port_ids


class RmsOnlineBinarySensor(TeltonikaRmsEntity, BinarySensorEntity):
    """Connectivity state for an RMS device."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:router-network"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id)
        self._attr_unique_id = f"{device_id}_online"

    @property
    def is_on(self) -> bool | None:
        normalized = self._normalized
        return normalized.online if normalized else None


class RmsPortLinkBinarySensor(TeltonikaRmsEntity, BinarySensorEntity):
    """Link state for an ethernet port."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:ethernet-cable"

    def __init__(self, bundle: CoordinatorBundle, device_id: str, port_id: str) -> None:
        super().__init__(bundle, device_id, coordinator=bundle.port_scan)
        self._port_id = port_id
        self._attr_unique_id = f"{device_id}_{port_id}_link"
        self._attr_name = f"{port_id.upper()} Link"

    @property
    def _port(self) -> dict[str, Any] | None:
        for port in self._bundle.port_scan.data.get(self.device_id, []):
            if str(port.get("name") or "").strip() == self._port_id:
                return port
        return None

    @property
    def available(self) -> bool:
        return super().available

    @property
    def is_on(self) -> bool | None:
        port = self._port
        if port is None:
            return False
        state = port.get("state")
        if state is not None:
            return str(state).lower() == "up"
        return True
