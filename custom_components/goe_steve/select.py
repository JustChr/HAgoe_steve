"""Select platform: charging mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import GoeSteveConfigEntry
from .engine import PHASE1_MODES, ChargingMode
from .entity import GoeSteveEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ChargingModeSelect(entry.runtime_data)])


class ChargingModeSelect(GoeSteveEntity, RestoreEntity, SelectEntity):
    """The headline control: pick how the car should charge."""

    _attr_icon = "mdi:ev-station"
    _attr_options = [mode.value for mode in PHASE1_MODES]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging_mode")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            if last.state in self._attr_options:
                self.coordinator.settings.mode = ChargingMode(last.state)

    @property
    def current_option(self) -> str:
        return self.coordinator.settings.mode.value

    async def async_select_option(self, option: str) -> None:
        self.coordinator.settings.mode = ChargingMode(option)
        self.async_write_ha_state()
        self.coordinator.request_apply()
