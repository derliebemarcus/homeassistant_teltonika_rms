"""Base entity for Teltonika RMS."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import CoordinatorBundle
from .models import NormalizedDevice


class TeltonikaRmsEntity(CoordinatorEntity):
    """Base coordinator entity bound to one RMS device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        bundle: CoordinatorBundle,
        device_id: str,
        *,
        coordinator: DataUpdateCoordinator | None = None,
    ) -> None:
        super().__init__(coordinator or bundle.state)
        self._bundle = bundle
        self._device_id = device_id

    @property
    def device_id(self) -> str:
        """RMS device identifier."""
        return self._device_id

    @property
    def _normalized(self) -> NormalizedDevice | None:
        return self._bundle.merged_device(self._device_id)

    @property
    def available(self) -> bool:
        return self._normalized is not None

    @property
    def device_info(self) -> DeviceInfo | None:
        normalized = self._normalized
        if normalized is None:
            return None
        info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Teltonika",
            name=normalized.name,
            model=normalized.model,
            sw_version=normalized.firmware,
            serial_number=normalized.serial,
        )
        return info


def is_poe_capable_series(model: str | None) -> bool:
    """Check if the device model series is potentially PoE capable."""
    if not model:
        return False
    return model.startswith(("OTD", "SWM", "TSW")) or (
        model.startswith("RUT") and not model.startswith(("RUTX", "RUTM"))
    )


class RmsPortEntity(TeltonikaRmsEntity):
    """Base for entities bound to a specific port of an RMS device."""

    def __init__(self, bundle: CoordinatorBundle, device_id: str, port_id: str) -> None:
        """Initialize the port entity."""
        super().__init__(bundle, device_id, coordinator=bundle.port_scan)
        self._port_id = port_id

    @property
    def _port(self) -> dict[str, Any] | None:
        """Return the port information from the latest scan."""
        for port in self._bundle.port_scan.data.get(self.device_id, []):
            if str(port.get("name") or "").strip() == self._port_id:
                return port
        return None


def async_setup_platform_helper(
    entry: ConfigEntry,
    bundle: CoordinatorBundle,
    async_add_entities: AddEntitiesCallback,
    discover_func: Callable[[CoordinatorBundle, set[str]], list[Any]],
    listeners: list[DataUpdateCoordinator],
) -> None:
    """Standardized setup helper for platform discovery and entity tracking."""
    known: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_entities = discover_func(bundle, known)
        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    for listener in listeners:
        entry.async_on_unload(listener.async_add_listener(_add_new_entities))
