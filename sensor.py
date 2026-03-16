"""Diagnostic sensors for Teltonika RMS."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity
from .models import NormalizedDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle
    known: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_entities: list[SensorEntity] = []
        for device_id in bundle.inventory.data:
            normalized = bundle.merged_device(device_id)
            for entity_cls in (
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
            ):
                if not entity_cls.should_create(normalized):
                    continue
                unique = f"{device_id}_{entity_cls.entity_key}"
                if unique in known:
                    continue
                known.add(unique)
                new_entities.append(entity_cls(bundle, device_id))
        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(bundle.inventory.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.state.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.port_scan.async_add_listener(_add_new_entities))


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
    entity_key = "model"
    _attr_translation_key = "model"
    _attr_icon = "mdi:chip"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, "model")


class RmsFirmwareSensor(_BaseDiagnosticSensor):
    entity_key = "firmware"
    _attr_translation_key = "firmware"
    _attr_icon = "mdi:update"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, "firmware")


class RmsSerialSensor(_BaseDiagnosticSensor):
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
    entity_key = "clients_count"
    _attr_name = "Clients Count"
    _attr_icon = "mdi:account-multiple"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsRouterUptimeSensor(_OptionalDiagnosticSensor):
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
    entity_key = "signal_strength"
    _attr_name = "Signal Strength"
    _attr_icon = "mdi:signal"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "dBm"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsWanStateSensor(_OptionalDiagnosticSensor):
    entity_key = "wan_state"
    _attr_name = "WAN State"
    _attr_icon = "mdi:wan"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsConnectionStateSensor(_OptionalDiagnosticSensor):
    entity_key = "connection_state"
    _attr_name = "Connection State"
    _attr_icon = "mdi:network-outline"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsConnectionTypeSensor(_OptionalDiagnosticSensor):
    entity_key = "connection_type"
    _attr_name = "Connection Type"
    _attr_icon = "mdi:radio-tower"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, self.entity_key)


class RmsSimSlotSensor(_OptionalDiagnosticSensor):
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
