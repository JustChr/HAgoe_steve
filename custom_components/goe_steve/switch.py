"""Switch platform: master enable for smart control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import GoeSteveConfigEntry
from .entity import GoeSteveEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [SmartControlSwitch(coordinator), AutoPhaseSwitch(coordinator)]
    )


class SmartControlSwitch(GoeSteveEntity, RestoreEntity, SwitchEntity):
    """When off, the brain never writes the charger — manual control wins."""

    _attr_icon = "mdi:brain"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "smart_control")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.settings.smart_enabled = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.settings.smart_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.settings.smart_enabled = True
        self.async_write_ha_state()
        self.coordinator.request_apply()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.settings.smart_enabled = False
        self.async_write_ha_state()
        self.coordinator.request_apply()


class AutoPhaseSwitch(GoeSteveEntity, RestoreEntity, SwitchEntity):
    """When on, the brain switches 1↔3 phases to follow the solar surplus."""

    _attr_icon = "mdi:sine-wave"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "auto_phase")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.settings.auto_phase = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.settings.auto_phase

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.settings.auto_phase = True
        self.async_write_ha_state()
        self.coordinator.request_apply()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.settings.auto_phase = False
        self.async_write_ha_state()
        self.coordinator.request_apply()
