"""Device tracker entities for Teltonika RMS."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType  # type: ignore[attr-defined]
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity, async_setup_platform_helper
from .models import has_location_coordinates

PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Teltonika RMS device trackers."""
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle

    # Delegate discovery and setup to common helper
    async_setup_platform_helper(
        entry,
        bundle,
        async_add_entities,
        _discover_tracker_entities,
        [bundle.inventory, bundle.state],
    )


def _discover_tracker_entities(
    bundle: CoordinatorBundle, known: set[str]
) -> list[RmsDeviceTracker]:
    """Discover new tracker entities."""
    new_entities: list[RmsDeviceTracker] = []
    for device_id in bundle.inventory.data:
        normalized = bundle.merged_device(device_id)
        if not has_location_coordinates(normalized):
            continue
        unique = f"{device_id}_location"
        if unique in known:
            continue
        known.add(unique)
        new_entities.append(RmsDeviceTracker(bundle, device_id))
    return new_entities


class RmsDeviceTracker(TeltonikaRmsEntity, TrackerEntity):
    """GPS tracker from RMS location data when available."""

    _attr_translation_key = "location"
    _attr_icon = "mdi:crosshairs-gps"
    _attr_source_type = SourceType.GPS

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id)
        self._attr_unique_id = f"{device_id}_location"

    @property
    def available(self) -> bool:
        return has_location_coordinates(self._normalized)

    @property
    def latitude(self) -> float | None:
        normalized = self._normalized
        return normalized.latitude if normalized else None

    @property
    def longitude(self) -> float | None:
        normalized = self._normalized
        return normalized.longitude if normalized else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        normalized = self._normalized
        if normalized is None:
            return {}

        attrs: dict[str, Any] = {}
        if normalized.location_label:
            attrs["location_detail"] = normalized.location_label

        if normalized.latitude is not None and normalized.longitude is not None:
            coords = f"{normalized.latitude:.6f}, {normalized.longitude:.6f}"
            attrs["coordinates"] = coords
            attrs["google_maps_url"] = (
                f"https://maps.google.com/?q={normalized.latitude:.6f},{normalized.longitude:.6f}"
            )
        return attrs

    @property
    def location_accuracy(self) -> int:
        return 100
