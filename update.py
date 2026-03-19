"""Firmware update entities for Teltonika RMS."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity
from .models import NormalizedDevice

PARALLEL_UPDATES = 0


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
        new_entities: list[RmsFirmwareUpdateEntity] = []
        for device_id in bundle.inventory.data:
            normalized = bundle.merged_device(device_id)
            if not RmsFirmwareUpdateEntity.should_create(normalized):
                continue
            unique = f"{device_id}_firmware_update"
            if unique in known:
                continue
            known.add(unique)
            new_entities.append(RmsFirmwareUpdateEntity(bundle, device_id))
        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(bundle.inventory.async_add_listener(_add_new_entities))
    entry.async_on_unload(bundle.state.async_add_listener(_add_new_entities))


class RmsFirmwareUpdateEntity(TeltonikaRmsEntity, UpdateEntity):
    """Read-only firmware update view backed by RMS device metadata."""

    _attr_name = "Firmware Update"
    _attr_icon = "mdi:update"

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id, coordinator=bundle.inventory)
        self._attr_unique_id = f"{device_id}_firmware_update"

    @classmethod
    def should_create(cls, normalized: NormalizedDevice | None) -> bool:
        return normalized is not None and (
            normalized.latest_firmware is not None or normalized.stable_firmware is not None
        )

    @property
    def installed_version(self) -> str | None:
        normalized = self._normalized
        return normalized.firmware if normalized else None

    @property
    def latest_version(self) -> str | None:
        normalized = self._normalized
        if normalized is None:
            return None
        return normalized.stable_firmware

    @property
    def release_summary(self) -> str | None:
        normalized = self._normalized
        if normalized is None:
            return None
        latest = normalized.latest_firmware
        stable = normalized.stable_firmware
        if latest and stable and latest != stable:
            return f"Latest: {latest}; Stable: {stable}"
        return None
