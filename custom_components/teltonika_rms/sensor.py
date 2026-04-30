"""Diagnostic sensors for Teltonika RMS."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity, is_poe_capable_series
from .models import NormalizedDevice

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika RMS sensor entities."""
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle
    known: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_entities: list[SensorEntity] = []

        for device_id, device_info in bundle.inventory.data.items():
            # 1. Standard Diagnostic Sensors
            if normalized := bundle.merged_device(device_id):
                _add_standard_sensors(bundle, device_id, normalized, known, new_entities)

            # 2. PoE Monitoring Sensors
            model = device_info.get("model", "UNKNOWN")
            if is_poe_capable_series(model):
                _add_poe_sensors(bundle, device_id, model, known, new_entities)

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(bundle.inventory.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.state.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.port_scan.async_add_listener(_add_new_entities))


def _add_standard_sensors(
    bundle: CoordinatorBundle,
    device_id: str,
    normalized: NormalizedDevice,
    known: set[str],
    new_entities: list[SensorEntity],
) -> None:
    """Add standard diagnostic sensors for a device."""
    standard_classes = (
        RmsModelSensor,
        RmsFirmwareSensor,
        RmsSerialSensor,
        RmsLastSeenSensor,
        RmsClientsCountSensor,
        RmsRouterUptimeSensor,
        RmsTemperatureSensor,
        RmsSignalStrengthSensor,
        RmsWanStateSensor,
        RmsConnectionStateSensor,
        RmsConnectionTypeSensor,
        RmsSimSlotSensor,
    )
    for entity_cls in standard_classes:
        if not entity_cls.should_create(normalized):
            continue
        unique = f"{device_id}_{entity_cls.entity_key}"
        if unique not in known:
            known.add(unique)
            new_entities.append(entity_cls(bundle, device_id))


def _add_poe_sensors(
    bundle: CoordinatorBundle,
    device_id: str,
    model: str,
    known: set[str],
    new_entities: list[SensorEntity],
) -> None:
    """Add PoE monitoring sensors for a device."""
    ports = _get_initial_ports(bundle, device_id, model)
    _apply_scan_results(bundle, device_id, ports)

    for port in ports.values():
        pid = str(port.get("id") or "").strip()
        if not pid or pid == "NIL":
            continue

        has_poe_data = any(port.get(k) is not None for k in ("PoE", "poe", "poe_enable", "PoE (W)"))
        if has_poe_data:
            unique_id = f"{device_id}_{pid}_poe_w"
            if unique_id not in known:
                known.add(unique_id)
                new_entities.append(RmsPoePowerSensor(bundle, device_id, pid))


def _get_initial_ports(
    bundle: CoordinatorBundle, device_id: str, model: str
) -> dict[str, dict[str, Any]]:
    """Initialize port mapping from configuration data."""
    ports = {
        str(p.get("id")): p
        for p in bundle.port_config.data.get(device_id, [])
        if p.get("id") and str(p.get("id")) != "NIL"
    }
    if (model.startswith("TSW") or model.startswith("SWM")) and not ports:
        for i in range(1, 9):
            ports[f"port{i}"] = {"id": f"port{i}"}
        for i in range(1, 3):
            ports[f"sfp{i}"] = {"id": f"sfp{i}"}
    return ports


def _apply_scan_results(
    bundle: CoordinatorBundle, device_id: str, ports: dict[str, dict[str, Any]]
) -> None:
    """Merge scanning results into the port mapping."""
    for scan_port in bundle.port_scan.data.get(device_id, []):
        name = str(scan_port.get("name") or "").strip()
        if not name or name == "NIL":
            continue
        if name not in ports:
            ports[name] = {"id": name}
        ports[name].update(scan_port)


class RmsPoePowerSensor(TeltonikaRmsEntity, SensorEntity):
    """PoE port power usage in watts."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:lightning-bolt"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, bundle: CoordinatorBundle, device_id: str, port_id: str) -> None:
        super().__init__(bundle, device_id, coordinator=bundle.port_scan)
        self._port_id = port_id
        self._attr_unique_id = f"{device_id}_{port_id}_poe_w"
        self._attr_name = f"{port_id.upper()} PoE Power"

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
    def native_value(self) -> float | None:
        port = self._port
        if port is None:
            return None
        val = port.get("PoE (W)")
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None


class _BaseDiagnosticSensor(TeltonikaRmsEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    entity_key: ClassVar[str]

    def __init__(self, bundle: CoordinatorBundle, device_id: str, key: str) -> None:
        super().__init__(bundle, device_id)
        self._key = key
        self._attr_unique_id = f"{device_id}_{key}"

    @classmethod
    def should_create(cls, normalized: NormalizedDevice | None) -> bool:
        return True

    @property
    def native_value(self) -> Any:
        normalized = self._normalized
        if normalized is None:
            return None
        return getattr(normalized, self._key)


class RmsModelSensor(_BaseDiagnosticSensor):
    """Model sensor."""

    entity_key = "model"
    _attr_translation_key = "model"
    _attr_icon = "mdi:chip"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, "model")


class RmsFirmwareSensor(_BaseDiagnosticSensor):
    """Firmware sensor."""

    entity_key = "firmware"
    _attr_translation_key = "firmware"
    _attr_icon = "mdi:update"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, "firmware")


class RmsSerialSensor(_BaseDiagnosticSensor):
    """Serial number sensor."""

    entity_key = "serial"
    _attr_translation_key = "serial"
    _attr_icon = "mdi:identifier"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, "serial")


class RmsLastSeenSensor(TeltonikaRmsEntity, SensorEntity):
    """Last update timestamp from RMS."""

    _attr_translation_key = "last_seen"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    entity_key = "last_seen"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id)
        self._attr_unique_id = f"{device_id}_last_seen"

    @classmethod
    def should_create(cls, normalized: NormalizedDevice | None) -> bool:
        return normalized is not None and normalized.last_seen is not None

    @property
    def native_value(self) -> datetime | None:
        normalized = self._normalized
        return normalized.last_seen if normalized else None


class _OptionalDiagnosticSensor(_BaseDiagnosticSensor):
    """Diagnostic sensor that exists only when RMS provides the value."""

    @classmethod
    def should_create(cls, normalized: NormalizedDevice | None) -> bool:
        return normalized is not None and getattr(normalized, cls.entity_key) is not None

    @property
    def available(self) -> bool:
        normalized = self._normalized
        return normalized is not None and getattr(normalized, self._key) is not None


class RmsClientsCountSensor(_OptionalDiagnosticSensor):
    """Clients count sensor."""

    entity_key = "clients_count"
    _attr_name = "Clients Count"
    _attr_icon = "mdi:account-multiple"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsRouterUptimeSensor(_OptionalDiagnosticSensor):
    """Router uptime sensor."""

    entity_key = "router_uptime"
    _attr_name = "Router Uptime"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)

    @property
    def native_value(self) -> float | None:
        normalized = self._normalized
        if normalized is None or normalized.router_uptime is None:
            return None
        return round(normalized.router_uptime / 86400, 2)


class RmsTemperatureSensor(_OptionalDiagnosticSensor):
    """Temperature sensor."""

    entity_key = "temperature"
    _attr_name = "Temperature"
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)

    @property
    def native_value(self) -> float | None:
        normalized = self._normalized
        if normalized is None or normalized.temperature is None:
            return None
        return float(normalized.temperature)


class RmsSignalStrengthSensor(_OptionalDiagnosticSensor):
    """Signal strength sensor."""

    entity_key = "signal_strength"
    _attr_name = "Signal Strength"
    _attr_icon = "mdi:signal"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "dBm"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsWanStateSensor(_OptionalDiagnosticSensor):
    """WAN state sensor."""

    entity_key = "wan_state"
    _attr_name = "WAN State"
    _attr_icon = "mdi:wan"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsConnectionStateSensor(_OptionalDiagnosticSensor):
    """Connection state sensor."""

    entity_key = "connection_state"
    _attr_name = "Connection State"
    _attr_icon = "mdi:network-outline"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsConnectionTypeSensor(_OptionalDiagnosticSensor):
    """Connection type sensor."""

    entity_key = "connection_type"
    _attr_name = "Connection Type"
    _attr_icon = "mdi:radio-tower"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsSimSlotSensor(_OptionalDiagnosticSensor):
    """SIM slot sensor."""

    entity_key = "sim_slot"
    _attr_name = "SIM Slot"
    _attr_icon = "mdi:sim"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)

    @property
    def native_value(self) -> int | None:
        normalized = self._normalized
        if normalized is None or normalized.sim_slot is None:
            return None
        return int(normalized.sim_slot)
