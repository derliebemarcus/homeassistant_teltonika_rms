"""Action buttons for Teltonika RMS."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TeltonikaRmsRuntime
from .coordinator import CoordinatorBundle
from .entity import TeltonikaRmsEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika RMS action buttons."""
    runtime: TeltonikaRmsRuntime = entry.runtime_data
    bundle: CoordinatorBundle = runtime.bundle
    async_add_entities(RmsRebootButton(bundle, device_id) for device_id in bundle.inventory.data)


class RmsRebootButton(TeltonikaRmsEntity, ButtonEntity):
    """Button that triggers an RMS reboot action."""

    _attr_name = "Reboot"
    _attr_icon = "mdi:restart"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, bundle: CoordinatorBundle, device_id: str) -> None:
        super().__init__(bundle, device_id)
        self._attr_unique_id = f"{device_id}_reboot"

    def press(self) -> None:
        """Handle the button press."""
        raise NotImplementedError()

    async def async_press(self) -> None:
        """Request a reboot for the device."""
        try:
            await self._bundle.api.async_reboot_device(self.device_id)
        except ConfigEntryAuthFailed as err:
            raise HomeAssistantError(
                "RMS reboot requires device_actions:write permissions. "
                "Reauthenticate and try again."
            ) from err
        await self._bundle.state.async_request_refresh()
