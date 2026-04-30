"""Base entity for Teltonika RMS."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
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
